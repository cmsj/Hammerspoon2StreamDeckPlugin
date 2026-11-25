# Protocol between the plugin and the StreamDeckPlugin Spoon

The Spoon listens on a Unix domain socket at
`~/Library/Application Support/Hammerspoon2/streamdeck.sock`, and the plugin connects to it,
retrying about once a second while it can't. Each message is one JSON object on its own line,
with a `type` field. `src/protocol.ts` has the types.

## Connecting

1. The plugin connects and sends `hello`. The Spoon answers with its own `hello`.
2. If the two `protocol` numbers differ, both sides report which one needs updating and the
   connection stays open but idle. Reloading the Spoon closes it, and the next connection starts
   again from step 1.
3. Otherwise the plugin sends `snapshot`, and the Spoon answers with `state`.

```jsonc
// plugin -> Spoon
{"type":"hello","protocol":1,"plugin":"0.1.0.0","streamDeck":"7.6.1.23033","platform":"mac"}
// Spoon -> plugin
{"type":"hello","protocol":1,"spoon":"1.0.0"}
```

## Plugin to Spoon

| type | fields | when |
|---|---|---|
| `snapshot` | `devices`, `instances` | Once, after the hellos |
| `appear` / `disappear` | `instance` | A Hammerspoon action became visible or invisible: placed, deleted, or its page, folder or profile shown or hidden. Stream Deck doesn't say which. |
| `rename` | `instance`, `oldName` | Someone changed the name in the action's settings |
| `keyDown` / `keyUp` | `instance`, `userDesiredState`? | A key was pressed or released. `userDesiredState` is only there inside a multi-action. |
| `dialDown` / `dialUp` | `instance` | A dial was pushed or released |
| `dialRotate` | `instance`, `ticks`, `pressed` | A dial was turned (`ticks` is negative counterclockwise) |
| `touchTap` | `instance`, `position` `[x, y]`, `hold` | A touch-strip segment was tapped, or long-pressed (`hold`) |
| `deviceConnected` / `deviceDisconnected` / `deviceChanged` | `device` | |
| `error` | `message` | Something the Spoon asked for failed, e.g. an image file couldn't be read |

An **instance** is one placed key or dial:

```jsonc
{
  "id": "4b1b…",            // Elgato's id for the placed action (stable until it's deleted, moved or copied)
  "kind": "key",            // or "dial"
  "name": "mute",           // "" until it's given a name
  "device": "892e…",        // a device id
  "coordinates": {"row": 0, "column": 3},  // missing inside a multi-action
  "isInMultiAction": false,
  "state": 0                // keys only
}
```

A **device** is `{id, name, type, typeName, size: {rows, columns}, connected}`, where `type` is
Elgato's `DeviceType` number and `typeName` its name, e.g. `"StreamDeckXL"`.

## Spoon to plugin

| type | fields | |
|---|---|---|
| `state` | `names`, `ids`, `knownNames` | Everything to show: a visual for each name and each instance id that has one. It replaces whatever the plugin had cached, and every visible action is redrawn. |
| `update` | `target`, then any visual fields | Changes some fields of one name's or one id's visual |
| `alert` | `target`, `kind` (`"alert"` or `"ok"`) | Flashes a warning triangle or tick |
| `knownNames` | `names` | The names the config uses, offered in the actions' settings |

`target` is `{"name": "mute"}` or `{"id": "4b1b…"}`. A **visual** has any of these fields. In an
`update`, a field that's missing is left alone, and `null` puts it back to its default:

| field | |
|---|---|
| `image` | A `data:` URL, SVG markup, or the absolute path of an image file (png, jpg, gif, svg, webp, bmp), which the plugin reads |
| `title` | |
| `state` | Keys: 0 or 1 |
| `feedback` | Dials: values for the touch-strip layout's items, merged into those already set. Image items (`icon`, `icon1`, `icon2`, `full-canvas`, `canvas`) can be file paths too. |
| `layout` | Dials: `"$X1"`, `"$A0"`, `"$A1"`, `"$B1"` (the default), `"$B2"`, `"$C1"`, or a layout JSON path |
| `triggerDescription` | Dials: `{rotate, push, touch, longTouch}` |
| `deleteFiles` | Paths in this visual that are temporary files the plugin should delete once it has read them. Only files named `hs2-streamdeck-…` are deleted. |

What an action shows is its name's visual with its id's visual laid over it, field by field.

## What the plugin does on its own

- It caches every visual, and redraws an action whenever it appears, because Stream Deck doesn't
  keep images and titles set at runtime once an action goes off-screen.
- Messages from the Spoon are handled in order, one at a time, so a slow file read can't let a
  later update be overwritten by an earlier one.
- If the Spoon goes away for more than 5 seconds (longer than a config reload takes), it clears its
  cache and puts every action back to its defaults.
- A press while the Spoon isn't connected shows an alert on the key.
