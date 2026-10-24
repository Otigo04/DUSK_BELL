"""HUD-Paket (Neu): gemeinsame Helfer. Nur Farben der Style-Bibel (nwui.PAL), keine Anti-Aliasing-Kanten.
Wird von build_hud_neu.py benutzt."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import os

from PIL import Image, ImageDraw, ImageFont

from nwui import PAL, ALLOWED, rgb, new, put, rect, from_ascii, outline, scaled, used_colors

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(UI, "HUD_Neu")
FONT_PATH = os.path.join(UI, "Font", "Nightward_Pixel.ttf")

GROUPS = ("Plates", "Vitals", "Clock", "Needs", "Quest", "Wake", "Banner", "Events")
for g in GROUPS:
    os.makedirs(os.path.join(OUT, g), exist_ok=True)
os.makedirs(os.path.join(OUT, "Preview"), exist_ok=True)

MANIFEST = {}          # Gruppe -> [(Name, Bild)]  fuer die Aseprite-Dateien


def save(im, group, name):
    bad = used_colors(im) - ALLOWED
    assert not bad, (group, name, bad)
    im.save(os.path.join(OUT, group, name + ".png"))
    MANIFEST.setdefault(group, []).append((name, im))
    return im


# ---------------------------------------------------------------- Zeichen-Helfer
def disc(im, cx, cy, r, name, alpha=255):
    for y in range(im.height):
        for x in range(im.width):
            if math.hypot(x - cx, y - cy) <= r:
                put(im, x, y, name, alpha)


def line(im, x0, y0, x1, y1, name, alpha=255):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        put(im, int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)), name, alpha)


def poly(im, pts, name):
    d = ImageDraw.Draw(im)
    d.polygon(pts, fill=rgb(name))


def icon_from(core_w, core_h, fn, size, pad=None):
    """fn(im) zeichnet auf eine core_w x core_h Flaeche; wird mit 1 px Kontur zentriert in size x size gesetzt."""
    core = new(core_w, core_h)
    fn(core)
    full = new(size, size)
    ox = (size - core_w) // 2 if pad is None else pad[0]
    oy = (size - core_h) // 2 if pad is None else pad[1]
    full.paste(core, (ox, oy))
    return outline(full)


def shaded(im, light="candle", dark=None, mid=None):
    """Hilfsfunktion fuer gleichmaessige Diagonal-Schattierung: nichts, wird bei Bedarf pro Icon gemacht."""
    return im


# ---------------------------------------------------------------- Text
def text(im, x, y, s, color, size=8, shadow=True):
    f = ImageFont.truetype(FONT_PATH, size)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    if shadow:
        d.text((x + 1, y + 1), s, font=f, fill=rgb("od"))
    d.text((x, y), s, font=f, fill=rgb(color))


def text_w(s, size=8):
    return len(s) * 6 * (size // 8)


# ---------------------------------------------------------------- 9-Slice (Vorschau)
def nine(src, border, w, h):
    l, t, r, b = border
    out = new(w, h)
    sw, sh = src.size
    parts = {
        "tl": (0, 0, l, t, 0, 0, l, t), "tr": (sw - r, 0, sw, t, w - r, 0, w, t),
        "bl": (0, sh - b, l, sh, 0, h - b, l, h), "br": (sw - r, sh - b, sw, sh, w - r, h - b, w, h),
        "t": (l, 0, sw - r, t, l, 0, w - r, t), "b": (l, sh - b, sw - r, sh, l, h - b, w - r, h),
        "l": (0, t, l, sh - b, 0, t, l, h - b), "r": (sw - r, t, sw, sh - b, w - r, t, w, h - b),
        "c": (l, t, sw - r, sh - b, l, t, w - r, h - b),
    }
    for _, (x0, y0, x1, y1, dx0, dy0, dx1, dy1) in parts.items():
        if x1 <= x0 or y1 <= y0 or dx1 <= dx0 or dy1 <= dy0:
            continue
        piece = src.crop((x0, y0, x1, y1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
        out.alpha_composite(piece, (dx0, dy0))
    return out


def frame(w, h, bg, bg_alpha, fr, hi=None, corner=1):
    """Rahmen mit 1 px Kante, angeschnittenen Ecken, Licht oben links (gleiche Logik wie das Dialog-Panel)."""
    im = new(w, h)
    rect(im, 1, 1, w - 2, h - 2, bg, bg_alpha)
    for x in range(1, w - 1):
        put(im, x, 0, fr)
        put(im, x, h - 1, fr)
    for y in range(1, h - 1):
        put(im, 0, y, fr)
        put(im, w - 1, y, fr)
    for (cx, cy) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        put(im, cx, cy, fr)
    if hi:
        for x in range(2, w - 2):
            put(im, x, 1, hi)
        for y in range(2, h - 2):
            put(im, 1, y, hi)
        put(im, 1, 1, hi)
    return im


def over(base, im, x, y):
    base.alpha_composite(im, (x, y))
    return base
