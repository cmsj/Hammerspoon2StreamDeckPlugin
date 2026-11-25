import {
    action,
    SingletonAction,
    type DialDownEvent,
    type DialRotateEvent,
    type DialUpEvent,
    type DidReceiveSettingsEvent,
    type PropertyInspectorDidAppearEvent,
    type TouchTapEvent,
    type WillAppearEvent,
    type WillDisappearEvent
} from "@elgato/streamdeck";

import { deck, type Settings } from "../deck";

/** A Stream Deck + dial and its touch-strip segment, controlled by Hammerspoon. */
@action({ UUID: "org.hammerspoon.hammerspoon2.dial" })
export class HammerspoonDial extends SingletonAction<Settings> {
    override onWillAppear(ev: WillAppearEvent<Settings>): void {
        deck.appear("dial", ev.action, ev.payload.settings);
    }

    override onWillDisappear(ev: WillDisappearEvent<Settings>): void {
        deck.disappear(ev.action.id);
    }

    override onDidReceiveSettings(ev: DidReceiveSettingsEvent<Settings>): void {
        deck.settingsChanged(ev.action.id, ev.payload.settings);
    }

    override onDialDown(ev: DialDownEvent<Settings>): void {
        deck.dialEvent({ type: "dialDown" }, ev.action.id);
    }

    override onDialUp(ev: DialUpEvent<Settings>): void {
        deck.dialEvent({ type: "dialUp" }, ev.action.id);
    }

    override onDialRotate(ev: DialRotateEvent<Settings>): void {
        deck.dialEvent({ type: "dialRotate", ticks: ev.payload.ticks, pressed: ev.payload.pressed }, ev.action.id);
    }

    override onTouchTap(ev: TouchTapEvent<Settings>): void {
        const [x, y] = ev.payload.tapPos;
        deck.dialEvent({ type: "touchTap", position: [x, y], hold: ev.payload.hold }, ev.action.id);
    }

    override onPropertyInspectorDidAppear(_ev: PropertyInspectorDidAppearEvent<Settings>): void {
        deck.updateInspector();
    }

    override onSendToPlugin(): void {
        deck.updateInspector();
    }
}
