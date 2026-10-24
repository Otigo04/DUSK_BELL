"""Baut die Zusatz-Sprites fuer den NPC-Dialog: Namensschild und Beziehungsleiste.
Aufruf: python build_dialog.py

Panels/Namensschild_Grund.png   9-Slice 16x16 (Border 5), weisse Flaeche -> im UI mit #1a1526 eingefaerbt
Panels/Namensschild_Rahmen.png  9-Slice 16x16 (Border 5), weisser Rahmen -> im UI mit der Namensfarbe des NPCs eingefaerbt
HUD/Beziehung_Leiste.png        108x14: 21 Segmente (4x8) (-10 .. +10) rot -> neutral -> gruen, Striche an den Stufengrenzen
HUD/Beziehung_Marker.png        8x5: Dreieck ueber dem aktuellen Segment
HUD/Beziehung_Segment.png       4x8: weisses Segment fuer das Aufblitzen bei Aenderungen

Weiss ist nur Tint-Vorlage und erscheint nie ungefaerbt im Spiel.
"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import os

from nwui import ALLOWED, rgb, new, put, rect, used_colors, scaled

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
WHITE = (255, 255, 255)


def save(im, sub, name, tint_template=False):
    allowed = ALLOWED | {WHITE} if tint_template else ALLOWED
    assert used_colors(im) <= allowed, (name, used_colors(im) - allowed)
    im.save(os.path.join(OUT, sub, name))


def white(im, x, y):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), (255, 255, 255, 255))


# ------------------------------------------------------------------ Namensschild
def plate_fill(w=16, h=16):
    """Flaeche mit angeschnittenen Ecken (wie die Panels)."""
    im = new(w, h)
    for y in range(h):
        for x in range(w):
            corner = (x in (0, w - 1)) and (y in (0, h - 1))
            if not corner:
                white(im, x, y)
    return im


def plate_frame(w=16, h=16):
    """1px Rahmen mit angeschnittenen Ecken und Nieten, alles weiss (Tint = Namensfarbe)."""
    im = new(w, h)
    for x in range(1, w - 1):
        white(im, x, 0); white(im, x, h - 1)
    for y in range(1, h - 1):
        white(im, 0, y); white(im, w - 1, y)
    for (cx, cy) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        white(im, cx, cy)
    # Nieten in den Ecken (liegen im 9-Slice-Rand, werden also nie gestreckt)
    for (cx, cy) in ((3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)):
        white(im, cx, cy)
    return im


# ------------------------------------------------------------------ Beziehungsleiste
# Wert -> (Licht, Grund, Schatten). Extreme dunkler und satter, Mitte neutral (Stroh).
SEGMENTS = (
    [("eye", "blood", "od")] * 2 +        # -10, -9  feindselig
    [("pink", "eye", "blood")] * 2 +      # -8, -7
    [("lo", "fire", "rd")] * 2 +          # -6, -5   misstrauisch
    [("ly", "lo", "fire")] * 2 +          # -4, -3
    [("candle", "straw", "wh")] * 5 +     # -2 .. +2 neutral
    [("candle", "leaf", "gh")] * 2 +      # +3, +4   freundlich
    [("leaf", "gh", "g")] * 3 +           # +5 .. +7 guter Freund
    [("gh", "g", "fm")] * 3               # +8 .. +10 bester Freund
)
assert len(SEGMENTS) == 21
SEG_W, SEG_H, GAP, BORDER = 4, 8, 1, 2
# Stufengrenze liegt zwischen diesen Werten (links davon endet eine Stufe)
TIER_ENDS = (-7, -3, 2, 4, 7)


def bar():
    w = BORDER * 2 + 21 * SEG_W + 20 * GAP
    h = BORDER * 2 + SEG_H + 2
    im = new(w, h)
    # Aussenkontur dunkel, Rahmen violett
    rect(im, 0, 0, w - 1, BORDER * 2 + SEG_H - 1, "od")
    for x in range(1, w - 1):
        put(im, x, 1, "sv3"); put(im, x, BORDER + SEG_H, "sv2")
    put(im, 1, BORDER + SEG_H, "sv3")
    for y in range(1, BORDER + SEG_H + 1):
        put(im, 1, y, "sv3"); put(im, w - 2, y, "sv2")
    for i, (hi, base, sh) in enumerate(SEGMENTS):
        x0 = BORDER + i * (SEG_W + GAP)
        rect(im, x0, BORDER, x0 + SEG_W - 1, BORDER + SEG_H - 1, base)
        for x in range(x0, x0 + SEG_W):
            put(im, x, BORDER, hi)
            put(im, x, BORDER + SEG_H - 1, sh)
        value = i - 10
        if value in TIER_ENDS:
            gx = x0 + SEG_W   # Trennfuge rechts vom Segment
            for y in range(BORDER * 2 + SEG_H - 1, h):
                put(im, gx, y, "sv3")
    # Nullpunkt: Strich unter der Mitte
    mx = BORDER + 10 * (SEG_W + GAP) + 1   # 4 px breites Segment: Strich links der Mitte
    for y in range(BORDER * 2 + SEG_H - 1, h):
        put(im, mx + 1, y, "candle")
    for y in range(BORDER * 2 + SEG_H - 1, h):
        put(im, mx, y, "candle")
    return im


def marker():
    rows = [
        "oooooooo",
        "occcccco",
        ".occcco.",
        "..occo..",
        "...oo...",
    ]
    im = new(8, 5)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "o":
                put(im, x, y, "od")
            elif ch == "c":
                put(im, x, y, "candle")
    return im


def segment_flash():
    im = new(SEG_W, SEG_H)
    for y in range(SEG_H):
        for x in range(SEG_W):
            white(im, x, y)
    return im


if __name__ == "__main__":
    save(plate_fill(), "Panels", "Namensschild_Grund.png", tint_template=True)
    save(plate_frame(), "Panels", "Namensschild_Rahmen.png", tint_template=True)
    b = bar()
    save(b, "HUD", "Beziehung_Leiste.png")
    save(marker(), "HUD", "Beziehung_Marker.png")
    save(segment_flash(), "HUD", "Beziehung_Segment.png", tint_template=True)
    # Optional: 4x-Vorschau ausserhalb des Projekts, z. B. NW_PREVIEW=C:/temp/vorschau.png
    if os.environ.get("NW_PREVIEW"):
        prev = new(b.width + 4, b.height + 12)
        prev.alpha_composite(b, (2, 8))
        prev.alpha_composite(marker(), (2 + BORDER + 10 * (SEG_W + GAP) - 2, 3))
        scaled(prev, 4).save(os.environ["NW_PREVIEW"])
    print("Dialog-Sprites gebaut:", b.size)
