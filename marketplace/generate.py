#!/usr/bin/env python3
"""Generates the Marketplace thumbnail and gallery images (1920x960 PNG).

Needs rsvg-convert (brew install librsvg) and the icon at build/icon-512.png.
Run from anywhere: python3 marketplace/generate.py
"""
import base64
import html
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
W, H = 1920, 960

ICON = "data:image/png;base64," + base64.b64encode((BUILD / "icon-512.png").read_bytes()).decode()

SANS = "SF Pro Display, Helvetica Neue, sans-serif"
TEXT = "SF Pro Text, Helvetica Neue, sans-serif"
MONO = "Menlo, monospace"

GOLD_1, GOLD_2 = "#FDF5A9", "#DB9D39"
INK = "#F4EEE2"
MUTED = "#A79E8E"


def esc(s):
    return html.escape(s, quote=True)


# --- Keys: each returns SVG drawn in a 144x144 box ---------------------------------------------

def title(t, y=130, size=19, color="#fff"):
    return (f'<text x="72" y="{y}" font-family="{TEXT}" font-size="{size}" font-weight="600" '
            f'fill="{color}" text-anchor="middle" style="paint-order:stroke" stroke="#000" '
            f'stroke-opacity="0.35" stroke-width="3">{esc(t)}</text>')


def bg(fill):
    return f'<rect width="144" height="144" fill="{fill}"/>'


def grad(id_, c1, c2):
    return (f'<defs><linearGradient id="{id_}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>')


def k_mic(uid):
    return (grad(uid, "#ff5a4e", "#c4231b") + bg(f"url(#{uid})") +
            '<rect x="56" y="24" width="32" height="56" rx="16" fill="#fff"/>'
            '<path d="M42 62 a30 30 0 0 0 60 0" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"/>'
            '<line x1="72" y1="92" x2="72" y2="104" stroke="#fff" stroke-width="7" stroke-linecap="round"/>'
            + title("LIVE"))


def k_clock(uid):
    return (bg("#0b0b0c") +
            f'<text x="72" y="74" font-family="{MONO}" font-size="40" font-weight="bold" fill="#ffb000" text-anchor="middle">14:32</text>'
            f'<text x="72" y="104" font-family="{MONO}" font-size="22" fill="#a06f00" text-anchor="middle">:07</text>')


def k_toggle(uid):
    return (bg("#121212") +
            '<circle cx="72" cy="60" r="34" fill="#36c24a"/><circle cx="72" cy="60" r="34" fill="none" stroke="#7ef08c" stroke-width="3" opacity="0.6"/>'
            f'<text x="72" y="128" font-family="{TEXT}" font-size="24" font-weight="700" fill="#fff" text-anchor="middle">ON</text>')


def k_counter(uid):
    return (grad(uid, "#4c8cf5", "#1f56c9") + bg(f"url(#{uid})") +
            f'<text x="72" y="92" font-family="{SANS}" font-size="64" font-weight="700" fill="#fff" text-anchor="middle">42</text>'
            + title("Count", 128, 17))


def k_hs(uid):
    return (grad(uid, GOLD_1, GOLD_2) + bg(f"url(#{uid})") +
            f'<image href="{ICON}" x="14" y="6" width="116" height="116"/>' + title("Reload", 132, 18, "#2a1d05").replace('stroke="#000"', 'stroke="#fff"'))


def k_volume(uid):
    return (bg("#1d2430") +
            '<path d="M34 58 h18 l24 -20 v68 l-24 -20 h-18 z" fill="#e8eef8"/>'
            '<path d="M88 52 q12 20 0 40 M98 42 q22 30 0 60" fill="none" stroke="#e8eef8" stroke-width="6" stroke-linecap="round"/>'
            '<rect x="22" y="118" width="100" height="8" rx="4" fill="#3a4658"/><rect x="22" y="118" width="64" height="8" rx="4" fill="#5fb4ff"/>')


def k_battery(uid):
    return (bg("#101412") +
            '<rect x="26" y="40" width="84" height="44" rx="9" fill="none" stroke="#dfe6df" stroke-width="5"/>'
            '<rect x="112" y="53" width="8" height="18" rx="3" fill="#dfe6df"/>'
            '<rect x="33" y="47" width="61" height="30" rx="4" fill="#3ed65a"/>'
            + title("87%", 124, 24))


def k_cpu(uid):
    pts = "18,96 32,90 44,94 56,70 68,78 80,52 92,64 104,46 116,58 126,40"
    return (bg("#0f1116") +
            f'<polyline points="{pts} 126,112 18,112" fill="#2ee6a8" fill-opacity="0.18" stroke="none"/>'
            f'<polyline points="{pts}" fill="none" stroke="#2ee6a8" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>'
            + title("CPU 23%", 136, 17))


def k_calendar(uid):
    return (bg("#f6f3ee") +
            '<rect width="144" height="40" fill="#e8443a"/>'
            f'<text x="72" y="29" font-family="{TEXT}" font-size="20" font-weight="700" fill="#fff" text-anchor="middle">WED</text>'
            f'<text x="72" y="106" font-family="{SANS}" font-size="62" font-weight="300" fill="#1d1d1f" text-anchor="middle">25</text>'
            f'<text x="72" y="133" font-family="{TEXT}" font-size="15" fill="#6b6b6b" text-anchor="middle">10:30 Standup</text>')


def k_layout(uid):
    return (grad(uid, "#1f8a84", "#0f5753") + bg(f"url(#{uid})") +
            '<rect x="24" y="22" width="46" height="80" rx="7" fill="#fff" opacity="0.95"/>'
            '<rect x="76" y="22" width="44" height="37" rx="7" fill="#fff" opacity="0.7"/>'
            '<rect x="76" y="65" width="44" height="37" rx="7" fill="#fff" opacity="0.7"/>'
            + title("Tile", 132))


def k_coffee(uid):
    return (grad(uid, "#8a5a3b", "#4c2f1d") + bg(f"url(#{uid})") +
            '<path d="M34 50 h62 v30 a26 26 0 0 1 -26 26 h-10 a26 26 0 0 1 -26 -26 z" fill="#fff"/>'
            '<path d="M96 58 h6 a12 12 0 0 1 0 24 h-8" fill="none" stroke="#fff" stroke-width="6"/>'
            '<path d="M54 40 c-8 -6 8 -12 0 -20 M68 40 c-8 -7 8 -14 0 -24 M82 40 c-8 -6 8 -12 0 -20" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity="0.7"/>'
            + title("Awake", 132))


def k_play(uid):
    return (grad(uid, "#a24cf0", "#5b1fb0") + bg(f"url(#{uid})") +
            '<path d="M56 34 L104 64 L56 94 Z" fill="#fff" stroke="#fff" stroke-width="8" stroke-linejoin="round"/>'
            + title("Now Playing", 130, 16))


def k_vpn(uid):
    return (bg("#11251a") +
            '<path d="M50 62 v-12 a22 22 0 0 1 44 0 v12" fill="none" stroke="#5ee38a" stroke-width="8"/>'
            '<rect x="40" y="60" width="64" height="46" rx="9" fill="#5ee38a"/>'
            '<circle cx="72" cy="80" r="6" fill="#11251a"/><rect x="69" y="82" width="6" height="12" rx="2" fill="#11251a"/>'
            + title("VPN", 134))


def k_shot(uid):
    c = "#f2f2f2"
    return (bg("#26262a") +
            f'<path d="M30 52 v-20 h20 M94 32 h20 v20 M114 84 v20 h-20 M50 104 h-20 v-20" fill="none" stroke="{c}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
            '<circle cx="72" cy="68" r="14" fill="#ff9f0a"/>' + title("Capture", 134, 17))


def k_build(uid):
    return (bg("#0f1a12") +
            '<circle cx="72" cy="60" r="34" fill="#29b34a"/>'
            '<path d="M55 61 l12 12 l23 -25" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
            + title("Build", 128))


def k_dnd(uid):
    return (grad(uid, "#5856d6", "#2f2d8f") + bg(f"url(#{uid})") +
            '<path d="M86 30 a36 36 0 1 0 28 54 a30 30 0 0 1 -28 -54 z" fill="#fff"/>' + title("Focus", 132))


def k_empty(uid):
    return bg("#0a0a0b")


KEYS_15 = [k_mic, k_clock, k_toggle, k_counter, k_hs,
           k_volume, k_battery, k_cpu, k_calendar, k_layout,
           k_coffee, k_play, k_vpn, k_shot, k_build]


# --- The device ---------------------------------------------------------------------------------

uid_n = 0


def uid():
    global uid_n
    uid_n += 1
    return f"u{uid_n}"


def key_at(fn, x, y, size, highlight=False):
    u = uid()
    s = size / 144
    out = (f'<clipPath id="c{u}"><rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{size * 0.13:.1f}"/></clipPath>'
           f'<g clip-path="url(#c{u})"><g transform="translate({x},{y}) scale({s:.4f})">{fn(u)}</g>'
           f'<rect x="{x}" y="{y}" width="{size}" height="{size * 0.5}" fill="url(#gloss)"/></g>'
           f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{size * 0.13:.1f}" fill="none" stroke="#000" stroke-opacity="0.6" stroke-width="2"/>')
    if highlight:
        out += (f'<rect x="{x - 9}" y="{y - 9}" width="{size + 18}" height="{size + 18}" rx="{size * 0.18:.1f}" '
                f'fill="none" stroke="{GOLD_2}" stroke-width="5"/>')
    return out


def device(x, y, cols, rows, size, gap, keys, pad=52, highlight=()):
    w = cols * size + (cols - 1) * gap + 2 * pad
    h = rows * size + (rows - 1) * gap + 2 * pad
    out = (f'<rect x="{x}" y="{y + 26}" width="{w}" height="{h}" rx="46" fill="#000" opacity="0.55" filter="url(#shadow)"/>'
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="46" fill="url(#body)"/>'
           f'<rect x="{x + 1.5}" y="{y + 1.5}" width="{w - 3}" height="{h - 3}" rx="45" fill="none" stroke="#fff" stroke-opacity="0.09" stroke-width="3"/>'
           f'<rect x="{x + pad - 16}" y="{y + pad - 16}" width="{w - 2 * pad + 32}" height="{h - 2 * pad + 32}" rx="30" fill="#070708"/>')
    for i, fn in enumerate(keys):
        r, c = divmod(i, cols)
        out += key_at(fn, x + pad + c * (size + gap), y + pad + r * (size + gap), size, i in highlight)
    return out, w, h


def key_xy(x, y, cols, size, gap, index, pad=52):
    r, c = divmod(index, cols)
    return x + pad + c * (size + gap), y + pad + r * (size + gap)


DEFS = f'''<defs>
  <radialGradient id="bgglow" cx="0.72" cy="0.5" r="0.62">
    <stop offset="0" stop-color="#3a2c12"/><stop offset="0.55" stop-color="#1a1510"/><stop offset="1" stop-color="#0d0b09"/>
  </radialGradient>
  <linearGradient id="body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2c2c2f"/><stop offset="1" stop-color="#151517"/></linearGradient>
  <linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.10"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <linearGradient id="goldtext" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{GOLD_1}"/><stop offset="1" stop-color="{GOLD_2}"/></linearGradient>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="28"/></filter>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter>
</defs>'''


def page(body, glow_x=0.72):
    bgdef = DEFS.replace('cx="0.72"', f'cx="{glow_x}"')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{bgdef}'
            f'<rect width="{W}" height="{H}" fill="url(#bgglow)"/>{body}</svg>')


def text(x, y, s, size, color=INK, weight=400, family=SANS, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')


def brand(x, y, scale=1.0):
    """Icon plus 'Hammerspoon 2 for Stream Deck', small, for gallery headers."""
    s = 72 * scale
    return (f'<image href="{ICON}" x="{x}" y="{y}" width="{s}" height="{s}"/>'
            + text(x + s + 20, y + s * 0.47, "Hammerspoon 2", 30 * scale, INK, 700)
            + text(x + s + 20, y + s * 0.88, "for Stream Deck", 22 * scale, GOLD_2, 500))


def bullets(x, y, items, size=30, line=46, gap=74, color=INK):
    out = ""
    yy = y
    for lines in items:
        out += f'<circle cx="{x + 8}" cy="{yy - size * 0.33:.0f}" r="7" fill="{GOLD_2}"/>'
        for j, l in enumerate(lines):
            out += text(x + 32, yy + j * line, l, size, color, 400, TEXT)
        yy += (len(lines) - 1) * line + gap
    return out


# --- Code panel ---------------------------------------------------------------------------------

TOKEN = re.compile(r'(?P<str>"[^"]*"|`[^`]*`)|(?P<kw>\b(?:const|let|true|false|return)\b|=>)'
                   r'|(?P<meth>(?<=\.)[A-Za-z_]+(?=\())|(?P<num>\b\d+\b)|(?P<cmt>//.*$)|(?P<other>.)')
COLORS = {"str": "#a5d68a", "kw": "#f08fb0", "meth": "#ffcb6b", "num": "#f7a66a", "cmt": "#7d7466", "other": "#e9e3d6"}


def connector(x1, y1, x2, y2, down=False):
    if down:
        d = f"M {x1} {y1} C {x1 + 300} {y1}, {x2} {y2 + 140}, {x2} {y2 + 14}"
    else:
        d = f"M {x1} {y1} C {x1 + 260} {y1}, {x2 - 200} {y2}, {x2} {y2}"
    return (f'<circle cx="{x1}" cy="{y1}" r="7" fill="{GOLD_2}"/>'
            f'<path d="{d}" fill="none" stroke="{GOLD_2}" stroke-width="4" stroke-dasharray="10 9"/>'
            f'<circle cx="{x2}" cy="{y2 + (14 if down else 0)}" r="8" fill="{GOLD_2}"/>')


def code_panel(x, y, w, lines, size=25, lh=40, header="init.js"):
    h = len(lines) * lh + 96
    out = (f'<rect x="{x}" y="{y + 18}" width="{w}" height="{h}" rx="22" fill="#000" opacity="0.5" filter="url(#soft)"/>'
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="#17140f" stroke="#fff" stroke-opacity="0.08" stroke-width="2"/>'
           f'<circle cx="{x + 32}" cy="{y + 30}" r="8" fill="#ff5f57"/><circle cx="{x + 58}" cy="{y + 30}" r="8" fill="#febc2e"/>'
           f'<circle cx="{x + 84}" cy="{y + 30}" r="8" fill="#28c840"/>'
           + text(x + w / 2, y + 37, header, 20, MUTED, 500, TEXT, "middle"))
    for i, line in enumerate(lines):
        spans = ""
        for m in TOKEN.finditer(line):
            kind = m.lastgroup
            spans += f'<tspan fill="{COLORS[kind]}">{esc(m.group())}</tspan>'
        out += (f'<text x="{x + 36}" y="{y + 92 + i * lh}" font-family="{MONO}" font-size="{size}" '
                f'xml:space="preserve">{spans}</text>')
    return out, h


# --- Images -------------------------------------------------------------------------------------

def thumbnail():
    dev, dw, dh = device(850, 0, 5, 3, 150, 30, KEYS_15)
    dy = (H - dh) // 2 - 10
    dev, _, _ = device(850, dy, 5, 3, 150, 30, KEYS_15)
    body = (f'<image href="{ICON}" x="120" y="196" width="168" height="168"/>'
            + text(120, 470, "Hammerspoon 2", 92, INK, 700)
            + text(120, 540, "for Stream Deck", 54, "url(#goldtext)", 600)
            + text(122, 640, "Script your keys and dials", 36, MUTED, 400, TEXT)
            + text(122, 690, "in JavaScript, from your", 36, MUTED, 400, TEXT)
            + text(122, 740, "Hammerspoon 2 config.", 36, MUTED, 400, TEXT)
            + dev)
    return page(body)


def gallery_code():
    lines = [
        'hs.spoons.use("StreamDeckPlugin", {',
        '  source: "cmsj/Spoons2", start: true,',
        '  fn: (deck) => {',
        '    deck.key("mic")',
        '      .setTitle("LIVE")',
        '      .setImage(micIcon)',
        '      .on("down", () => toggleMute())',
        '',
        '    deck.key("cpu")',
        '      .setImage(cpuGraphSVG())',
        '  }',
        '})',
    ]
    panel, ph = code_panel(110, 0, 780, lines)
    py = (H - ph) // 2 + 40
    panel, _ = code_panel(110, py, 780, lines)
    dx, dy = 975, 230
    dev, dw, dh = device(dx, dy, 5, 3, 140, 26, KEYS_15, pad=46, highlight=(0,))
    kx, ky = key_xy(dx, dy, 5, 140, 26, 0, pad=46)
    body = (brand(110, 64)
            + text(1810, 112, "Your keys. Your code.", 52, INK, 700, anchor="end")
            + text(1810, 160, "Set images, titles and states, and react to presses.", 28, MUTED, 400, TEXT, "end")
            + panel + dev
            + connector(470, py + 92 + 3 * 40 - 9, kx - 12, ky + 70)
            + text(dx + dw / 2, dy + dh + 80, "SVG, image files or HSImage. Updates are cached, and redrawn", 24, MUTED, 400, TEXT, "middle")
            + text(dx + dw / 2, dy + dh + 114, "whenever a key reappears.", 24, MUTED, 400, TEXT, "middle"))
    return page(body, 0.7)


def gallery_setup():
    # A settings panel in the style of the plugin's property inspector
    px, py, pw = 960, 250, 850
    rows = ""
    rows += text(px + 210, py + 132, "Name", 26, MUTED, 400, TEXT, "end")
    rows += (f'<rect x="{px + 236}" y="{py + 96}" width="{pw - 286}" height="52" rx="8" fill="#4a4a4a" stroke="{GOLD_2}" stroke-width="2"/>'
             + text(px + 256, py + 132, "mic", 26, INK, 400, TEXT)
             + f'<rect x="{px + 298}" y="{py + 108}" width="2" height="30" fill="{INK}"/>')
    # suggestions dropdown
    sy = py + 156
    sugg = ["mic", "clock", "cpu", "build", "volume"]
    rows += f'<rect x="{px + 236}" y="{sy}" width="{pw - 286}" height="{len(sugg) * 46 + 12}" rx="8" fill="#3a3a3a" stroke="#fff" stroke-opacity="0.08"/>'
    for i, s in enumerate(sugg):
        if i == 0:
            rows += f'<rect x="{px + 242}" y="{sy + 6}" width="{pw - 298}" height="46" rx="6" fill="#0a64d8"/>'
        rows += text(px + 258, sy + 38 + i * 46, s, 24, INK, 400, TEXT)
    ry = sy + len(sugg) * 46 + 70
    rows += text(px + 210, ry, "Hammerspoon", 26, MUTED, 400, TEXT, "end")
    rows += f'<circle cx="{px + 250}" cy="{ry - 9}" r="9" fill="#28c940"/>' + text(px + 274, ry, "Connected (StreamDeckPlugin 1.0.0)", 26, INK, 400, TEXT)
    rows += text(px + 236, ry + 46, "Pick a name your config uses, or type a new one.", 22, MUTED, 400, TEXT)
    ph = ry + 90 - py
    panel = (f'<rect x="{px}" y="{py + 18}" width="{pw}" height="{ph}" rx="20" fill="#000" opacity="0.5" filter="url(#soft)"/>'
             f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="20" fill="#2d2d2d" stroke="#fff" stroke-opacity="0.08" stroke-width="2"/>'
             f'<rect x="{px}" y="{py}" width="{pw}" height="64" rx="20" fill="#363636"/><rect x="{px}" y="{py + 44}" width="{pw}" height="20" fill="#363636"/>'
             + f'<image href="{ICON}" x="{px + 20}" y="{py + 12}" width="40" height="40"/>'
             + text(px + 80, py + 42, "Hammerspoon Key", 24, INK, 600, TEXT)
             + rows)
    body = (brand(110, 64)
            + text(110, 290, "One setting: a name.", 60, INK, 700)
            + bullets(116, 400, [
                ["Drag a Hammerspoon Key onto any page,", "folder, profile or multi-action."],
                ["Give it a name. The field suggests the", "names your config already uses."],
                ["Your config does the rest, and hears when", "keys appear, move or are renamed."],
            ])
            + text(116, 800, "Keys with the same name show the same thing,", 26, MUTED, 400, TEXT)
            + text(116, 838, "on any page or device.", 26, MUTED, 400, TEXT)
            + panel)
    return page(body, 0.75)


def strip_segment(x, y, w, h, label, value, pct, icon, color):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#0b0b0c"/>'
            + text(x + 14, y + 26, label, 18, "#cfcfcf", 600, TEXT)
            + f'<g transform="translate({x + 14},{y + 34})">{icon}</g>'
            + text(x + w - 14, y + 66, value, 26, "#fff", 600, TEXT, "end")
            + f'<rect x="{x + 14}" y="{y + h - 20}" width="{w - 28}" height="8" rx="4" fill="#333"/>'
            + f'<rect x="{x + 14}" y="{y + h - 20}" width="{(w - 28) * pct:.0f}" height="8" rx="4" fill="{color}"/>')


def dial(cx, cy, r):
    ticks = "".join(
        f'<line x1="{cx}" y1="{cy - r + 6}" x2="{cx}" y2="{cy - r + 14}" stroke="#555" stroke-width="3" transform="rotate({a} {cx} {cy})"/>'
        for a in range(0, 360, 15))
    return (f'<circle cx="{cx}" cy="{cy + 6}" r="{r}" fill="#000" opacity="0.6" filter="url(#soft)"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#2a2a2c" stroke="#3c3c3f" stroke-width="3"/>{ticks}'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.62}" fill="url(#body)" stroke="#000" stroke-opacity="0.5" stroke-width="2"/>')


def gallery_dials():
    keys8 = [k_mic, k_clock, k_toggle, k_hs, k_play, k_layout, k_dnd, k_build]
    x, y, size, gap, pad = 1000, 120, 150, 28, 48
    cols = 4
    inner_w = cols * size + (cols - 1) * gap
    strip_h = 100
    w = inner_w + 2 * pad
    h = pad + 2 * size + gap + 34 + strip_h + 40 + 150 + pad
    out = (f'<rect x="{x}" y="{y + 26}" width="{w}" height="{h}" rx="46" fill="#000" opacity="0.55" filter="url(#shadow)"/>'
           f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="46" fill="url(#body)"/>'
           f'<rect x="{x + 1.5}" y="{y + 1.5}" width="{w - 3}" height="{h - 3}" rx="45" fill="none" stroke="#fff" stroke-opacity="0.09" stroke-width="3"/>'
           f'<rect x="{x + pad - 14}" y="{y + pad - 14}" width="{inner_w + 28}" height="{2 * size + gap + 28}" rx="26" fill="#070708"/>')
    for i, fn in enumerate(keys8):
        r, c = divmod(i, cols)
        out += key_at(fn, x + pad + c * (size + gap), y + pad + r * (size + gap), size)
    sy = y + pad + 2 * size + gap + 34
    seg_w = inner_w / 4
    speaker = '<path d="M0 10 h10 l12 -10 v34 l-12 -10 h-10 z" fill="#fff"/>'
    sun = '<circle cx="16" cy="16" r="8" fill="#ffd23f"/>' + "".join(
        f'<line x1="16" y1="1" x2="16" y2="5" stroke="#ffd23f" stroke-width="3" transform="rotate({a} 16 16)"/>' for a in range(0, 360, 45))
    mic = '<rect x="9" y="0" width="12" height="22" rx="6" fill="#fff"/><path d="M3 16 a12 12 0 0 0 24 0" fill="none" stroke="#fff" stroke-width="3"/>'
    timer = '<circle cx="16" cy="18" r="14" fill="none" stroke="#fff" stroke-width="3"/><line x1="16" y1="18" x2="16" y2="9" stroke="#fff" stroke-width="3"/>'
    segs = [("Volume", "62%", 0.62, speaker, "#5fb4ff"), ("Display", "80%", 0.8, sun, "#ffd23f"),
            ("Mic gain", "45%", 0.45, mic, "#ff6a5f"), ("Timer", "04:12", 0.7, timer, "#36c24a")]
    out += f'<rect x="{x + pad - 6}" y="{sy - 6}" width="{inner_w + 12}" height="{strip_h + 12}" rx="14" fill="#070708"/>'
    out += f'<clipPath id="strip"><rect x="{x + pad}" y="{sy}" width="{inner_w}" height="{strip_h}" rx="9"/></clipPath><g clip-path="url(#strip)">'
    for i, (lab, val, pct, icon, col) in enumerate(segs):
        out += strip_segment(x + pad + i * seg_w, sy, seg_w, strip_h, lab, val, pct, icon, col)
        if i:
            out += f'<line x1="{x + pad + i * seg_w}" y1="{sy}" x2="{x + pad + i * seg_w}" y2="{sy + strip_h}" stroke="#222" stroke-width="2"/>'
    out += '</g>'
    dy = sy + strip_h + 40 + 75
    for i in range(4):
        out += dial(x + pad + seg_w * i + seg_w / 2, dy, 62)

    lines = [
        'deck.dial("volume")',
        '  .setFeedback({ value: "62%", indicator: 62 })',
        '  .on("rotate", (ev) => nudge(ev.ticks))',
        '  .on("touch", () => toggleMute())',
    ]
    panel, _ = code_panel(110, 610, 800, lines, 23, 38, "init.js")
    body = (brand(110, 64)
            + text(110, 290, "Keys, dials and touch strip.", 60, INK, 700)
            + text(112, 360, "On a Stream Deck +, a Hammerspoon Dial gets", 30, MUTED, 400, TEXT)
            + text(112, 404, "turns, presses and touches, and your config", 30, MUTED, 400, TEXT)
            + text(112, 448, "draws its touch-strip segment.", 30, MUTED, 400, TEXT)
            + text(112, 548, "down · up · rotate · touch · appear · disappear", 26, GOLD_2, 500, MONO)
            + panel + out)
    return page(body, 0.72)


def gallery_dynamic():
    # The same names on two devices, and the events the config hears
    keysA = [k_mic, k_clock, k_toggle, k_counter, k_hs,
             k_volume, k_battery, k_cpu, k_calendar, k_layout,
             k_coffee, k_play, k_vpn, k_shot, k_build]
    y0 = 290
    dev, dw, dh = device(110, y0, 5, 3, 112, 22, keysA, pad=40, highlight=(0, 7))
    keysB = [k_mic, k_cpu, k_dnd, k_empty, k_empty, k_empty]
    bx = 110 + dw + 70
    dev2, dw2, dh2 = device(bx, y0, 3, 2, 112, 22, keysB, pad=40, highlight=(0, 1))
    lx, lw = bx + dw2 + 70, 1810 - (bx + dw2 + 70)
    events = [("appear", 'mic  XL r0 c0'), ("appear", 'cpu  XL r1 c2'), ("appear", 'mic  Mini r0 c0'),
              ("rename", '"" -> "cpu"'), ("down", 'mic')]
    lp = (f'<rect x="{lx}" y="{y0}" width="{lw}" height="{dh}" rx="20" fill="#17140f" stroke="#fff" stroke-opacity="0.08" stroke-width="2"/>'
          + text(lx + 26, y0 + 46, "Events", 22, MUTED, 600, TEXT))
    for i, (ev, detail) in enumerate(events):
        yy = y0 + 100 + i * 66
        lp += text(lx + 26, yy, ev, 22, GOLD_2, 600, MONO) + text(lx + 26, yy + 28, detail, 20, INK, 400, MONO)
    body = (brand(110, 64)
            + text(110, 224, "Built for setups that change.", 60, INK, 700)
            + dev + dev2 + lp
            + text(110 + dw / 2, y0 + dh + 50, "The same names on any page or device", 24, MUTED, 400, TEXT, "middle")
            + text(bx + dw2 / 2, y0 + dh2 + 50, "Add, move or rename keys any time", 24, MUTED, 400, TEXT, "middle")
            + text(110, 880, "Your config hears where each key is, which device it's on, and when it appears, disappears or is renamed.", 26, MUTED, 400, TEXT))
    return page(body, 0.5)


def render(name, svg):
    src = BUILD / f"{name}.svg"
    src.write_text(svg)
    out = HERE / f"{name}.png"
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(out), str(src)], check=True)
    print(out)


if __name__ == "__main__":
    render("thumbnail", thumbnail())
    render("gallery-1-code", gallery_code())
    render("gallery-2-setup", gallery_setup())
    render("gallery-3-dials", gallery_dials())
    render("gallery-4-dynamic", gallery_dynamic())
