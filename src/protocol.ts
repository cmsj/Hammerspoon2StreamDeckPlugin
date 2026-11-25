// The messages exchanged with the StreamDeckPlugin Spoon over the Unix domain socket: one JSON
// object per line, in each direction. PROTOCOL.md describes them in prose.

/**
 * Bumped whenever a change would break the other side. Each side sends its version in its hello,
 * and if they differ, both report which side needs updating, and nothing else is exchanged.
 */
export const PROTOCOL_VERSION = 1;

/** Where the Spoon listens, relative to the user's home directory. */
export const SOCKET_PATH = "Library/Application Support/Hammerspoon2/streamdeck.sock";

export type Kind = "key" | "dial";

/** A Stream Deck device, as the Spoon sees it. */
export type DeviceInfo = {
    id: string;
    name: string;
    /** Elgato's DeviceType number. */
    type: number;
    /** A readable name for `type`, e.g. "StreamDeckXL". */
    typeName: string;
    size: { rows: number; columns: number };
    connected: boolean;
};

/**
 * One placed Hammerspoon action that's currently visible: a key or dial on a device's current page,
 * or a step in a multi-action. `id` is Elgato's identifier for the placed action. It lasts as long
 * as the action stays where it is (including across restarts), and changes if it's deleted and
 * placed again, or copied.
 */
export type InstanceInfo = {
    id: string;
    kind: Kind;
    /** The name typed into the action's settings, or "" if it doesn't have one yet. */
    name: string;
    device: string;
    /** Absent for an action inside a multi-action. */
    coordinates?: { row: number; column: number };
    isInMultiAction: boolean;
    /** The key's current state (0 or 1), for keys. */
    state?: number;
};

/**
 * What a key or dial shows. In an update, a missing field is left alone and `null` puts it back to
 * its default. In the cache, only fields that are set are present.
 */
export type Visual = {
    /** An image: a data: URL, SVG markup, or the absolute path of an image file. */
    image?: string | null;
    title?: string | null;
    /** Keys only: 0 or 1. */
    state?: number | null;
    /** Dials only: values for the touch-strip layout's items, merged into what's already shown. */
    feedback?: Record<string, unknown> | null;
    /** Dials only: a built-in layout ("$A0", "$A1", "$B1", "$B2", "$C1", "$X1") or a layout JSON path. */
    layout?: string | null;
    /** Dials only: the descriptions Stream Deck shows for rotate, push, touch and long touch. */
    triggerDescription?: { rotate?: string; push?: string; touch?: string; longTouch?: string } | null;
    /** Paths in `image` and `feedback` that the plugin should delete once it has read them. */
    deleteFiles?: string[];
};

/** Which keys or dials a message from the Spoon applies to. */
export type Target = { name: string } | { id: string };

// Plugin to Spoon

export type PluginHello = {
    type: "hello";
    protocol: number;
    plugin: string;
    streamDeck: string;
    platform: string;
};
export type Snapshot = { type: "snapshot"; devices: DeviceInfo[]; instances: InstanceInfo[] };
export type InstanceMessage = { type: "appear" | "disappear"; instance: InstanceInfo };
export type RenameMessage = { type: "rename"; instance: InstanceInfo; oldName: string };
export type KeyMessage = { type: "keyDown" | "keyUp"; instance: InstanceInfo; userDesiredState?: number };
export type DialMessage = { type: "dialDown" | "dialUp"; instance: InstanceInfo };
export type RotateMessage = { type: "dialRotate"; instance: InstanceInfo; ticks: number; pressed: boolean };
export type TouchMessage = { type: "touchTap"; instance: InstanceInfo; position: [number, number]; hold: boolean };
export type DeviceMessage = { type: "deviceConnected" | "deviceDisconnected" | "deviceChanged"; device: DeviceInfo };
export type ErrorMessage = { type: "error"; message: string };

export type PluginMessage =
    | PluginHello
    | Snapshot
    | InstanceMessage
    | RenameMessage
    | KeyMessage
    | DialMessage
    | RotateMessage
    | TouchMessage
    | DeviceMessage
    | ErrorMessage;

// Spoon to plugin

export type SpoonHello = { type: "hello"; protocol: number; spoon: string };
/** Everything the Spoon wants shown, replacing whatever the plugin had cached. */
export type StateMessage = {
    type: "state";
    names: Record<string, Visual>;
    ids: Record<string, Visual>;
    knownNames: string[];
};
export type UpdateMessage = { type: "update"; target: Target } & Visual;
export type AlertMessage = { type: "alert"; target: Target; kind: "alert" | "ok" };
export type KnownNamesMessage = { type: "knownNames"; names: string[] };

export type SpoonMessage = SpoonHello | StateMessage | UpdateMessage | AlertMessage | KnownNamesMessage;
