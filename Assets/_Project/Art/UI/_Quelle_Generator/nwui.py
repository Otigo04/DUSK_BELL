"""Nightward UI: gemeinsame Palette + Helfer. Nur Farben aus der Style-Bibel."""
from PIL import Image

PAL = {
    "od": "#1a1526", "on": "#2b2140", "sv1": "#3d2e4a", "sv2": "#4f3d5c", "sv3": "#6b5a7a",
    "nb1": "#1f2a3d", "nb2": "#2c3e56", "nb3": "#3f5570", "moon": "#e8e0f0",
    "ed": "#3b2a22", "wd": "#5c4033", "wm": "#7a5a43", "wh": "#9c7a5a", "straw": "#b89a72",
    "fd": "#1e3a2b", "fm": "#2f5a3c", "g": "#4a7a4f", "gh": "#6e9a5e", "leaf": "#9ab87a",
    "s1": "#4a4550", "s2": "#6e6a74", "s3": "#9a95a0",
    "k1": "#5e3d33", "k2": "#8c5f4d", "k3": "#d19a7a",
    "rd": "#7a2e3a", "pink": "#c4636b", "bl": "#3a4a7a", "blh": "#6b7fb8",
    "ly": "#ffd27a", "lo": "#ffa550", "fire": "#e8733a", "candle": "#fff1c9",
    "tal": "#6fd3e6", "talh": "#a8f0ff", "tald": "#2b6b8a",
    "teeth": "#f2ead8", "eye": "#d64a6a", "blood": "#8a1f3d",
}


def rgb(name):
    h = PAL.get(name, name)
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)


def new(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(im, x, y, name, alpha=255):
    if 0 <= x < im.width and 0 <= y < im.height:
        c = rgb(name)
        im.putpixel((x, y), (c[0], c[1], c[2], alpha))


def rect(im, x0, y0, x1, y1, name, alpha=255):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(im, x, y, name, alpha)


def from_ascii(rows, cmap):
    h, w = len(rows), len(rows[0])
    im = new(w, h)
    for y, row in enumerate(rows):
        assert len(row) == w, f"Zeile {y} hat Laenge {len(row)} statt {w}: {row!r}"
        for x, ch in enumerate(row):
            if ch != ".":
                put(im, x, y, cmap[ch])
    return im


def outline(im, name="od"):
    """1px Aussenkontur (4er-Nachbarschaft) um alle nicht-transparenten Pixel."""
    src = im.copy()
    for y in range(src.height):
        for x in range(src.width):
            if src.getpixel((x, y))[3] > 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < src.width and 0 <= ny < src.height and src.getpixel((nx, ny))[3] > 0:
                    put(im, x, y, name)
                    break
    return im


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def used_colors(im):
    s = set()
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 0:
                s.add(p[:3])
    return s


ALLOWED = {rgb(k)[:3] for k in PAL}
