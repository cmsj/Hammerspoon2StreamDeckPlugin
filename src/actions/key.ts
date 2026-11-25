import {
    action,
    SingletonAction,
    type DidReceiveSettingsEvent,
    type KeyDownEvent,
    type KeyUpEvent,
    type PropertyInspectorDidAppearEvent,
    type WillAppearEvent,
    type WillDisappearEvent
} from "@elgato/streamdeck";

import { deck, type Settings } from "../deck";

/** A key whose image, title and state Hammerspoon controls, and whose presses it receives. */
@action({ UUID: "org.hammerspoon.hammerspoon2.key" })
export class HammerspoonKey extends SingletonAction<Settings> {
    override onWillAppear(ev: WillAppearEvent<Settings>): void {
        deck.appear("key", ev.action, ev.payload.settings, ev.payload.state);
    }

    override onWillDisappear(ev: WillDisappearEvent<Settings>): void {
        deck.disappear(ev.action.id);
    }

    override onDidReceiveSettings(ev: DidReceiveSettingsEvent<Settings>): void {
        deck.settingsChanged(ev.action.id, ev.payload.settings);
    }

    override onKeyDown(ev: KeyDownEvent<Settings>): void {
        const payload = ev.payload;
        deck.keyEvent("keyDown", ev.action.id, payload.state, "userDesiredState" in payload ? payload.userDesiredState : undefined);
    }

    override onKeyUp(ev: KeyUpEvent<Settings>): void {
        const payload = ev.payload;
        deck.keyEvent("keyUp", ev.action.id, payload.state, "userDesiredState" in payload ? payload.userDesiredState : undefined);
    }

    override onPropertyInspectorDidAppear(_ev: PropertyInspectorDidAppearEvent<Settings>): void {
        deck.updateInspector();
    }

    override onSendToPlugin(): void {
        // The only thing the property inspector asks for is its status, when it loads
        deck.updateInspector();
    }
}
