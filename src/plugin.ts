import streamDeck from "@elgato/streamdeck";

import { HammerspoonDial } from "./actions/dial";
import { HammerspoonKey } from "./actions/key";
import { deck } from "./deck";

streamDeck.logger.setLevel("info");

streamDeck.actions.registerAction(new HammerspoonKey());
streamDeck.actions.registerAction(new HammerspoonDial());

streamDeck.connect().then(() => deck.bridge.start());
