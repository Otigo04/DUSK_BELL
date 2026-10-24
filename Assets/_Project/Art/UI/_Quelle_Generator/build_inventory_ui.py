"""Inventar-UI: Slot-Rahmen (34x34), Equipment-Silhouetten (32x32) und fehlende Item-Icons (32x32).
Nur Farben der Style-Bibel (nwui.PAL). Aufruf: python build_inventory_ui.py
Ausgabe: Art/UI/Inventory/*.png  und  Art/Items/Waffen/Item_*.png (Pistole, Munition, Machete, Dreschflegel)."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import os

from PIL import Image, ImageDraw

from nwui import ALLOWED, rgb, new, put, rect, outline, used_colors

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.abspath(os.path.join(HERE, ".."))
ART = os.path.abspath(os.path.join(UI, ".."))
OUT = os.path.join(UI, "Inventory")
os.makedirs(OUT, exist_ok=True)


def save(im, path):
    bad = used_colors(im) - ALLOWED
    assert not bad, (path, bad)
    im.save(path)


# ---------------------------------------------------------------- Slots
S = 34


def slot(border, inner="on", light="sv1", corner_dots=None, double=False):
    im = new(S, S)
    rect(im, 0, 0, S - 1, S - 1, border)
    rect(im, 1, 1, S - 2, S - 2, inner)
    if double:
        rect(im, 1, 1, S - 2, S - 2, border)
        rect(im, 2, 2, S - 3, S - 3, inner)
    for (x, y) in ((0, 0), (S - 1, 0), (0, S - 1), (S - 1, S - 1)):
        put(im, x, y, "od", 0)
    # Licht oben links, Schatten unten rechts (Innenkante)
    o = 2 if double else 1
    for x in range(o, S - o):
        put(im, x, o, light)
    for y in range(o, S - o):
        put(im, o, y, light)
    for x in range(o + 1, S - o):
        put(im, x, S - o - 1, "od")
    for y in range(o + 1, S - o):
        put(im, S - o - 1, y, "od")
    if corner_dots:
        for (x, y) in ((1, 1), (S - 2, 1), (1, S - 2), (S - 2, S - 2)):
            put(im, x, y, corner_dots)
    return im


save(slot("od"), os.path.join(OUT, "Slot_Normal.png"))
save(slot("ly", light="ly"), os.path.join(OUT, "Slot_Hover.png"))
save(slot("ly", inner="sv1", light="ly", double=True, corner_dots="lo"), os.path.join(OUT, "Slot_Selected.png"))
save(slot("od", inner="nb1", light="nb2"), os.path.join(OUT, "Slot_Equip.png"))
save(slot("sv3", inner="on", light="sv2"), os.path.join(OUT, "Slot_Container.png"))


# ---------------------------------------------------------------- Equipment-Silhouetten (gedaempft, 32x32)
def sil_lantern():
    im = new(32, 32)
    c = "sv2"
    rect(im, 14, 5, 17, 6, c)
    rect(im, 12, 8, 19, 9, c)
    rect(im, 11, 10, 20, 22, c)
    rect(im, 13, 12, 18, 20, "on")
    rect(im, 12, 23, 19, 25, c)
    for (x, y) in ((13, 4), (18, 4)):
        put(im, x, y, c)
    return im


def sil_talisman():
    im = new(32, 32)
    pts = []
    for i in range(10):
        a = math.pi * 2 * i / 10 - math.pi / 2
        r = 11 if i % 2 == 0 else 5
        pts.append((15.5 + r * math.cos(a), 16 + r * math.sin(a)))
    ImageDraw.Draw(im).polygon(pts, fill=rgb("sv2"))
    rect(im, 14, 14, 17, 17, "on")
    return im


def sil_coat():
    im = new(32, 32)
    c = "sv2"
    rect(im, 11, 6, 20, 26, c)
    rect(im, 6, 7, 10, 20, c)
    rect(im, 21, 7, 25, 20, c)
    rect(im, 14, 6, 17, 10, "on")
    rect(im, 15, 11, 16, 26, "on")
    return im


for nm, fn in (("Leer_Licht", sil_lantern), ("Leer_Talisman", sil_talisman), ("Leer_Kleidung", sil_coat)):
    im = fn()
    outline(im, "on")
    save(im, os.path.join(OUT, nm + ".png"))


# ---------------------------------------------------------------- Fehlende Item-Icons (32x32)
def line(im, x0, y0, x1, y1, name, w=1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        for dx in range(w):
            for dy in range(w):
                put(im, x + dx, y + dy, name)


def pistol():
    im = new(32, 32)
    rect(im, 5, 9, 25, 14, "s2")
    rect(im, 5, 9, 25, 9, "s3")
    rect(im, 5, 14, 25, 14, "s1")
    rect(im, 26, 10, 28, 13, "s1")
    rect(im, 3, 8, 5, 10, "s1")
    rect(im, 7, 15, 17, 17, "s1")
    for (x, y) in ((17, 18), (18, 19), (19, 19), (20, 18), (20, 17), (19, 16)):
        put(im, x, y, "s1")
    put(im, 16, 18, "s3")
    for i in range(10):
        x0 = 6 + i // 4
        rect(im, x0, 18 + i, x0 + 4, 18 + i, "wd")
        put(im, x0, 18 + i, "wh")
        put(im, x0 + 4, 18 + i, "ed")
    put(im, 9, 12, "s1")
    put(im, 10, 12, "s1")
    outline(im, "od")
    return im


def ammo():
    im = new(32, 32)
    rect(im, 7, 13, 24, 25, "wm")
    rect(im, 7, 13, 24, 14, "wh")
    rect(im, 7, 24, 24, 25, "wd")
    rect(im, 11, 17, 20, 21, "candle")
    for x in (12, 14, 16, 18):
        put(im, x, 19, "wd")
    for i, x in enumerate((9, 12, 15, 18, 21)):
        rect(im, x, 7, x + 1, 12, "ly" if i % 2 == 0 else "lo")
        rect(im, x, 6, x + 1, 6, "k1")
    outline(im, "od")
    return im


def machete():
    im = new(32, 32)
    for t in range(0, 16):
        x = 11 + t
        y = 21 - t
        rect(im, x, y - 1, x + 2, y + 1, "s3")
        put(im, x + 3, y, "s2")
        put(im, x + 2, y + 1, "s1")
    rect(im, 24, 5, 26, 7, "s3")
    line(im, 9, 23, 12, 20, "s1", 2)
    line(im, 5, 27, 10, 22, "wd", 3)
    line(im, 5, 27, 10, 22, "wh", 1)
    put(im, 4, 28, "ed")
    outline(im, "od")
    return im


def flail():
    im = new(32, 32)
    line(im, 5, 27, 17, 15, "wd", 3)
    line(im, 5, 26, 17, 14, "wh", 1)
    for (x, y) in ((18, 14), (19, 12), (21, 11), (22, 9)):
        put(im, x, y, "s2")
        put(im, x + 1, y, "s3")
    for y in range(32):
        for x in range(32):
            if math.hypot(x - 24.5, y - 6.5) <= 4.2:
                put(im, x, y, "wm")
    rect(im, 21, 4, 22, 5, "wh")
    for (x, y) in ((24, 1), (29, 6), (24, 12), (19, 6), (28, 2), (28, 11), (20, 2), (20, 11)):
        put(im, x, y, "s3")
    outline(im, "od")
    return im



def coat():
    """Wollmantel: dunkles Blau, Kragen, Knoepfe aus Holz."""
    im = new(32, 32)
    rect(im, 10, 6, 21, 27, "bl")
    rect(im, 5, 8, 9, 22, "bl")
    rect(im, 22, 8, 26, 22, "bl")
    rect(im, 10, 6, 21, 7, "blh")
    rect(im, 5, 8, 9, 9, "blh")
    rect(im, 22, 8, 26, 9, "blh")
    for y in range(8, 28):
        put(im, 21, y, "nb2")
        put(im, 9 if y > 22 else 9, y, "blh") if y > 9 else None
    rect(im, 5, 21, 9, 22, "nb2")
    rect(im, 22, 21, 26, 22, "nb2")
    rect(im, 13, 5, 18, 8, "sv3")           # Kragen
    rect(im, 14, 8, 17, 9, "sv2")
    rect(im, 15, 10, 16, 27, "nb2")         # Knopfleiste
    for y in (12, 16, 20, 24):
        put(im, 15, y, "wh"); put(im, 16, y, "wm")
    rect(im, 10, 26, 21, 27, "nb2")
    outline(im, "od")
    return im


os.makedirs(os.path.join(ART, "Items", "Kleidung"), exist_ok=True)
save(coat(), os.path.join(ART, "Items", "Kleidung", "Item_Wollmantel.png"))
print("mantel ok")

extras = []
for nm, fn in (("Item_Pistole", pistol), ("Item_Munition", ammo), ("Item_Machete", machete), ("Item_Dreschflegel", flail)):
    d = os.path.join(ART, "Items", "Waffen")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, nm + ".png")
    save(fn(), p)
    extras.append(p)

# Vorschau (2x/3x)
sheet = [os.path.join(OUT, n) for n in ("Slot_Normal.png", "Slot_Hover.png", "Slot_Selected.png", "Slot_Equip.png", "Slot_Container.png",
                                       "Leer_Licht.png", "Leer_Talisman.png", "Leer_Kleidung.png")] + extras
prev = Image.new("RGBA", (len(sheet) * 76 + 8, 84), (26, 21, 38, 255))
for i, p in enumerate(sheet):
    im = Image.open(p).convert("RGBA")
    prev.alpha_composite(im.resize((im.width * 2, im.height * 2), Image.NEAREST), (4 + i * 76, 4))
prev.save(os.path.join(OUT, "Vorschau_Inventar.png"))
print("ok")
