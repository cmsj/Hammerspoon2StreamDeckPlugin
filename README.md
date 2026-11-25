# Stream Deck plugin for Hammerspoon 2

This plugin lets your [Hammerspoon 2](https://github.com/Hammerspoon/Hammerspoon2) config control
keys and dials in the Elgato Stream Deck app. Your config can set their images and titles, and
react to key presses, dial turns and touch-strip taps.

Hammerspoon 2's `hs.streamdeck` module drives the hardware directly, so it can't run at the same
time as the Elgato app. This plugin works inside the Elgato app instead, so Hammerspoon's keys sit
in your normal profiles alongside everything else, and pages, folders and multi-actions all work.

## Using it

1. Install the plugin (`.streamDeckPlugin` from the releases page) and the
   [StreamDeckPlugin Spoon](https://github.com/cmsj/Spoons2/tree/main/StreamDeckPlugin.spoon2):

   ```js
   hs.spoons.use("StreamDeckPlugin", { source: "cmsj/Spoons2", start: true, fn: (deck) => {
       deck.key("mute")
           .setTitle("Live")
           .on("down", () => toggleMute())
   }})
   ```

2. In the Stream Deck app, drag **Hammerspoon Key** (or **Hammerspoon Dial**, on a Stream Deck +)
   onto your deck, and type a name such as `mute` into its settings. Once the Spoon is running, the
   field suggests the names your config uses.

That's all there is to configure in the plugin. The Spoon's documentation, at the top of its
`init.js`, covers the rest.

## Developing

You need Node.js 24 or later.

```sh
npm install
npm run build              # bundles src/ into org.hammerspoon.hammerspoon2.sdPlugin/bin/
npx streamdeck dev         # once: turns on the Stream Deck app's developer mode
npm run link               # once: links the plugin folder into the Stream Deck app
npm run watch              # rebuilds, and restarts the plugin, on every change
```

The plugin's logs are in `org.hammerspoon.hammerspoon2.sdPlugin/logs/`. Set the Spoon's `debug`
setting to `true` to log every message in Hammerspoon's Console.

`npm run validate` checks the manifest, and `npm run pack` builds
`dist/org.hammerspoon.hammerspoon2.streamDeckPlugin`.

To release, push a version tag such as `0.0.2`. GitHub Actions packs the plugin with that
version (as `0.0.2.0`, since Stream Deck wants four parts) and publishes it as a GitHub release.
Keep the `Version` in `manifest.json` in step with the tags.

[PROTOCOL.md](PROTOCOL.md) describes the messages that pass between the plugin and the Spoon.
If you change it in a way that would break the other side, bump `PROTOCOL_VERSION` in both
`src/protocol.ts` and the Spoon.
