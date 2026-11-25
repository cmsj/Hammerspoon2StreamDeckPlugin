import streamDeck, { DeviceType, type Action, type DialAction, type KeyAction, type Size } from "@elgato/streamdeck";

import { Bridge, type BridgeStatus } from "./bridge";
import { deleteFiles, resolveFeedback, resolveImage } from "./images";
import {
    PROTOCOL_VERSION,
    type DeviceInfo,
    type InstanceInfo,
    type Kind,
    type PluginMessage,
    type SpoonMessage,
    type Target,
    type Visual
} from "./protocol";

export type Settings = { name?: string };

/** The touch-strip layout dials use until the Spoon picks another; it has title, icon, value and indicator items. */
export const DEFAULT_LAYOUT = "$B1";
/** How long to keep showing what Hammerspoon last set after losing it, in case it's only reloading. */
const RESET_DELAY_MS = 5000;

type VisualField = "image" | "title" | "state" | "feedback" | "layout" | "triggerDescription";
const VISUAL_FIELDS: VisualField[] = ["image", "title", "state", "feedback", "layout", "triggerDescription"];

type Instance = { info: InstanceInfo; action: Action<Settings> };

type DeviceLike = { id: string; name: string; type: DeviceType; size: Size; isConnected: boolean };

function deviceInfo(device: DeviceLike): DeviceInfo {
    return {
        id: device.id,
        name: device.name,
        type: device.type,
        typeName: DeviceType[device.type] ?? `Unknown${device.type}`,
        size: { rows: device.size.rows, columns: device.size.columns },
        connected: device.isConnected
    };
}

function showAlert(action: Action<Settings>): void {
    if (action.isKey() || action.isDial()) action.showAlert().catch(() => {});
}

function normalizeName(name: unknown): string {
    return typeof name === "string" ? name.trim() : "";
}

/**
 * Tracks every visible Hammerspoon action, caches what Hammerspoon wants each name (or single
 * action) to show, and restores it whenever an action appears, since Stream Deck forgets images and
 * titles set at runtime when an action goes off-screen.
 */
class Deck {
    readonly #instances = new Map<string, Instance>();
    #names = new Map<string, Visual>();
    #ids = new Map<string, Visual>();
    #knownNames: string[] = [];
    #resetTimer: NodeJS.Timeout | null = null;
    /** Messages from the Spoon are handled one at a time, so a slow image read can't reorder updates. */
    #queue: Promise<void> = Promise.resolve();

    readonly bridge = new Bridge(
        {
            onConnect: () => this.#connected(),
            onMessage: (message) => {
                this.#queue = this.#queue.then(() => this.#handle(message)).catch((err) => this.#reportError(String(err)));
            },
            onDisconnect: () => this.#disconnected(),
            onStatus: (status) => this.#statusChanged(status)
        },
        () => ({
            type: "hello",
            protocol: PROTOCOL_VERSION,
            plugin: streamDeck.info.plugin.version,
            streamDeck: streamDeck.info.application.version,
            platform: streamDeck.info.application.platform
        })
    );

    constructor() {
        streamDeck.devices.onDeviceDidConnect((ev) => this.#send({ type: "deviceConnected", device: deviceInfo(ev.device) }));
        streamDeck.devices.onDeviceDidDisconnect((ev) => this.#send({ type: "deviceDisconnected", device: deviceInfo(ev.device) }));
        streamDeck.devices.onDeviceDidChange((ev) => this.#send({ type: "deviceChanged", device: deviceInfo(ev.device) }));
    }

    // Events from Stream Deck

    appear(kind: Kind, action: Action<Settings>, settings: Settings, state?: number): void {
        const info: InstanceInfo = {
            id: action.id,
            kind,
            name: normalizeName(settings.name),
            device: action.device.id,
            isInMultiAction: action.isKey() ? action.isInMultiAction() : false
        };
        const coordinates = action.coordinates;
        if (coordinates) info.coordinates = { row: coordinates.row, column: coordinates.column };
        if (kind === "key") info.state = state ?? 0;

        this.#instances.set(info.id, { info, action });
        this.#apply(info.id, new Set(VISUAL_FIELDS));
        this.#send({ type: "appear", instance: info });
    }

    disappear(id: string): void {
        const instance = this.#instances.get(id);
        if (!instance) return;
        this.#instances.delete(id);
        this.#send({ type: "disappear", instance: instance.info });
    }

    settingsChanged(id: string, settings: Settings): void {
        const instance = this.#instances.get(id);
        if (!instance) return;
        const name = normalizeName(settings.name);
        if (name === instance.info.name) return;
        const oldName = instance.info.name;
        instance.info.name = name;
        this.#apply(id, new Set(VISUAL_FIELDS));
        this.#send({ type: "rename", instance: instance.info, oldName });
    }

    keyEvent(type: "keyDown" | "keyUp", id: string, state?: number, userDesiredState?: number): void {
        const instance = this.#instances.get(id);
        if (!instance) return;
        if (state !== undefined) instance.info.state = state;
        if (!this.#interactive(instance)) return;
        const message: PluginMessage = { type, instance: instance.info };
        if (userDesiredState !== undefined) message.userDesiredState = userDesiredState;
        this.#send(message);
    }

    dialEvent(message: { type: "dialDown" | "dialUp" } | { type: "dialRotate"; ticks: number; pressed: boolean } | { type: "touchTap"; position: [number, number]; hold: boolean }, id: string): void {
        const instance = this.#instances.get(id);
        if (!instance || !this.#interactive(instance)) return;
        this.#send({ ...message, instance: instance.info } as PluginMessage);
    }

    // The property inspector

    /** Sends the property inspector that's open (if any) what it shows: connection status and the names the config uses. */
    updateInspector(): void {
        const action = streamDeck.ui.action;
        if (!action) return;
        const status = this.bridge.status;
        streamDeck.ui
            .sendToPropertyInspector({
                status: status as unknown as Record<string, string | number>,
                knownNames: this.#knownNames,
                id: action.id,
                socketPath: this.bridge.socketPath,
                pluginProtocol: PROTOCOL_VERSION
            })
            .catch(() => {});
    }

    // The connection to Hammerspoon

    #send(message: PluginMessage): void {
        if (this.bridge.isReady) this.bridge.send(message);
    }

    /** Whether a press can do anything; if Hammerspoon isn't there, the action shows an alert instead. */
    #interactive(instance: Instance): boolean {
        if (this.bridge.isReady) return true;
        showAlert(instance.action);
        return false;
    }

    #reportError(message: string): void {
        streamDeck.logger.error(message);
        this.#send({ type: "error", message });
    }

    #connected(): void {
        if (this.#resetTimer) {
            clearTimeout(this.#resetTimer);
            this.#resetTimer = null;
        }
        this.bridge.send({
            type: "snapshot",
            devices: [...streamDeck.devices].map(deviceInfo),
            instances: [...this.#instances.values()].map((instance) => instance.info)
        });
    }

    #disconnected(): void {
        if (this.#resetTimer) clearTimeout(this.#resetTimer);
        this.#resetTimer = setTimeout(() => {
            this.#resetTimer = null;
            this.#names = new Map();
            this.#ids = new Map();
            for (const id of this.#instances.keys()) this.#apply(id, new Set(VISUAL_FIELDS));
        }, RESET_DELAY_MS);
    }

    #statusChanged(_status: BridgeStatus): void {
        this.updateInspector();
    }

    async #handle(message: SpoonMessage): Promise<void> {
        switch (message.type) {
            case "state": {
                const names = new Map<string, Visual>();
                const ids = new Map<string, Visual>();
                for (const [name, visual] of Object.entries(message.names ?? {})) {
                    names.set(name, await this.#merge({}, visual));
                }
                for (const [id, visual] of Object.entries(message.ids ?? {})) {
                    ids.set(id, await this.#merge({}, visual));
                }
                this.#names = names;
                this.#ids = ids;
                this.#setKnownNames(message.knownNames);
                for (const id of this.#instances.keys()) this.#apply(id, new Set(VISUAL_FIELDS));
                break;
            }
            case "update": {
                const { target } = message;
                const cache = "id" in target ? this.#ids : this.#names;
                const key = "id" in target ? target.id : normalizeName(target.name);
                const merged = await this.#merge(cache.get(key) ?? {}, message);
                if (Object.keys(merged).length) cache.set(key, merged);
                else cache.delete(key);

                const fields = new Set(VISUAL_FIELDS.filter((field) => field in message));
                for (const instance of this.#targets(target)) this.#apply(instance.info.id, fields);
                break;
            }
            case "alert":
                for (const instance of this.#targets(message.target)) {
                    const action = instance.action;
                    if (message.kind === "ok" && action.isKey()) action.showOk().catch(() => {});
                    else showAlert(action);
                }
                break;
            case "knownNames":
                this.#setKnownNames(message.names);
                break;
        }
    }

    #setKnownNames(names: unknown): void {
        this.#knownNames = Array.isArray(names) ? names.filter((name) => typeof name === "string").sort() : [];
        this.updateInspector();
    }

    #targets(target: Target): Instance[] {
        if ("id" in target) {
            const instance = this.#instances.get(target.id);
            return instance ? [instance] : [];
        }
        const name = normalizeName(target.name);
        return [...this.#instances.values()].filter((instance) => instance.info.name === name);
    }

    /**
     * Merges an update into a cached visual, resolving its images, and returns the result. A `null`
     * field removes it from the cache, and feedback is merged item by item, as Stream Deck does.
     */
    async #merge(cached: Visual, update: Visual): Promise<Visual> {
        const result: Visual = { ...cached };
        try {
            for (const field of VISUAL_FIELDS) {
                if (!(field in update)) continue;
                const value = update[field];
                if (value === null || value === undefined) {
                    delete result[field];
                } else if (field === "image") {
                    result.image = await resolveImage(value as string);
                } else if (field === "feedback") {
                    const feedback = await resolveFeedback(value as Record<string, unknown>);
                    result.feedback = { ...(result.feedback ?? {}), ...feedback };
                } else {
                    (result as Record<string, unknown>)[field] = value;
                }
            }
        } finally {
            await deleteFiles(update.deleteFiles);
        }
        return result;
    }

    /** What an action should show: its name's visual, with anything set for its id taking precedence. */
    #effective(info: InstanceInfo): Visual {
        const byName = info.name ? this.#names.get(info.name) ?? {} : {};
        const byId = this.#ids.get(info.id) ?? {};
        const result: Visual = { ...byName, ...byId };
        if (byName.feedback && byId.feedback) result.feedback = { ...byName.feedback, ...byId.feedback };
        return result;
    }

    /** Pushes the given fields of an instance's effective visual to Stream Deck, resetting any that aren't set. */
    #apply(id: string, fields: Set<VisualField>): void {
        const instance = this.#instances.get(id);
        if (!instance || fields.size === 0) return;
        const visual = this.#effective(instance.info);
        const { action } = instance;
        const fail = (what: string) => (err: unknown) => streamDeck.logger.warn(`${what} failed for ${id}: ${err}`);

        if (action.isKey()) {
            this.#applyKey(action, visual, fields, fail);
            if (fields.has("state") && typeof visual.state === "number") instance.info.state = visual.state;
        } else if (action.isDial()) {
            this.#applyDial(action, visual, fields, fail);
        }
    }

    #applyKey(action: KeyAction<Settings>, visual: Visual, fields: Set<VisualField>, fail: (what: string) => (err: unknown) => void): void {
        // State first, since an image or title applies to the state that's current
        if (fields.has("state") && typeof visual.state === "number") action.setState(visual.state).catch(fail("setState"));
        if (fields.has("image")) action.setImage(visual.image ?? undefined).catch(fail("setImage"));
        if (fields.has("title")) action.setTitle(visual.title ?? undefined).catch(fail("setTitle"));
    }

    #applyDial(action: DialAction<Settings>, visual: Visual, fields: Set<VisualField>, fail: (what: string) => (err: unknown) => void): void {
        if (fields.has("layout")) {
            action.setFeedbackLayout(visual.layout ?? DEFAULT_LAYOUT).catch(fail("setFeedbackLayout"));
            fields.add("feedback"); // a new layout starts out empty
        }
        if (fields.has("image")) action.setImage(visual.image ?? undefined).catch(fail("setImage"));
        if (fields.has("title")) action.setTitle(visual.title as string).catch(fail("setTitle"));
        if (fields.has("feedback")) {
            const feedback = visual.feedback ?? (visual.layout ? null : { value: "", indicator: 0 });
            if (feedback) action.setFeedback(feedback as Parameters<typeof action.setFeedback>[0]).catch(fail("setFeedback"));
        }
        if (fields.has("triggerDescription")) {
            const description = visual.triggerDescription;
            action
                .setTriggerDescription(
                    description
                        ? { rotate: description.rotate, push: description.push, touch: description.touch, longTouch: description.longTouch }
                        : undefined
                )
                .catch(fail("setTriggerDescription"));
        }
    }
}

export const deck = new Deck();
