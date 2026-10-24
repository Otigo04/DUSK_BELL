"""Friedhof-Objekte fuer die Beerdigung am Dorfeingang (Pivot unten links, 32 px Raster):
Grab_Offen, Erdhaufen, Sarg_Leer, Toter_Weiss (in weisses Tuch gewickelt, auf der Bahre), Schaufel_Erde, Grabhuegel_Kreuz,
Grabhuegel_Blumen, Kreuz_Holz, Grabstein_D (Obelisk), Grabstein_E (flache Platte), Grabstein_F (Hochkreuz mit Ring).
Ausgabe: Art/Tiles/Dorf/Objekte/*.png.  Aufruf: python friedhof_objekte.py [ausgabeordner] [vorschau.png]"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nwlib import *

OUTLINE = H('1a1526')
EARTH = [H(x) for x in ('2b2140', '3b2a22', '5c4033', '7a5a43', '9c7a5a', 'b89a72')]
MOSS = [GREEN[1], GREEN[2], GREEN[3]]
CLOTH = [H(x) for x in ('6b5a7a', '9a95a0', 'c4c1d2', 'e4e0ea', 'efe7dd', 'fff1c9')]   # Leinentuch: kuehle Schatten -> warmes Licht


def earth_fill(sp, x0, y0, x1, y1, seed, lo=1, hi=4):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = lo + (hi - lo) * (0.35 + 0.5 * hsh(x, y, seed))
            sp.set(x, y, EARTH[int(round(v))])


def mound(sp, cx, cy, rx, ry, seed):
    """Lockere Erde: heller Kamm oben links, dunkel unten rechts, Klumpen."""
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = nx * nx + ny * ny
            if d > 1.0:
                continue
            lam = (-nx * 0.5 - ny * 0.85) * 0.5 + 0.55 - d * 0.35
            v = lam * 4.2 + (hsh(x, y, seed) - 0.5) * 1.3
            sp.set(x, y, EARTH[int(max(1, min(5, round(v))))])
    for k in range(int(rx * 1.2)):
        x = int(cx - rx + hsh(k, seed, 1) * rx * 2)
        y = int(cy + ry - hsh(k, seed, 2) * ry * 0.5)
        if sp.solid(x, y):
            sp.set(x, y, EARTH[5 if hsh(k, seed, 3) < .5 else 2])


def grab_offen():
    sp = Spr(64, 64)
    # Rand aus aufgeworfener Erde
    earth_fill(sp, 8, 14, 55, 54, 11, 3, 4)
    # Grube: hintere Wand (Erdschichten), dunkler Boden
    for y in range(20, 48):
        for x in range(12, 52):
            if y < 31:
                k = 2 + (1 if (y + int(hsh(x, 3, 4) * 3)) % 4 == 0 else 0)
                sp.set(x, y, EARTH[k] if x > 13 else EARTH[1])
            else:
                f = (y - 31) / 16.0
                sp.set(x, y, EARTH[0] if f > 0.15 or hsh(x, y, 8) < 0.5 else EARTH[1])
    for x in range(12, 52):
        sp.set(x, 20, EARTH[4])                       # Kante vorn/oben hell im Licht
        sp.set(x, 47, EARTH[3])
    for y in range(20, 48):
        sp.set(12, y, EARTH[4])
        sp.set(51, y, EARTH[2])
    # Wurzeln und Steinchen in der Wand
    for x, y in ((18, 24), (19, 25), (20, 25), (38, 27), (39, 28), (44, 23)):
        sp.set(x, y, EARTH[4] if (x + y) % 2 else EARTH[5])
    # Bretter/Stuetzen quer ueber der Grube (zum Ablassen des Sargs)
    for yy in (30, 38):
        for x in range(9, 55):
            sp.set(x, yy, BROWN[2]); sp.set(x, yy + 1, BROWN[1])
        for x in range(9, 55, 7):
            sp.set(x, yy, BROWN[3])
    for k in range(40):
        x, y = int(8 + hsh(k, 1, 2) * 48), int(16 + hsh(k, 2, 3) * 40)
        if 12 <= x <= 51 and 20 <= y <= 47:
            continue
        sp.set(x, y, EARTH[5] if hsh(k, 5, 6) < .3 else EARTH[2])
    thick_outline(sp)
    return sp


def erdhaufen():
    sp = Spr(64, 32)
    mound(sp, 32, 22, 26, 11, 21)
    mound(sp, 20, 24, 12, 6, 22)
    mound(sp, 47, 25, 11, 5, 23)
    thick_outline(sp)
    return sp


def sarg_leer():
    sp = Spr(64, 32)
    # Sechseck-Sarg von oben/vorn: Deckel liegt daneben, Kasten offen mit hellem Futter
    pts = [(2, 14), (10, 6), (54, 6), (62, 14), (54, 24), (10, 24)]
    def inside(x, y):
        # konvexes Polygon (Vorzeichen-Test)
        s = None
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            c = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
            if c == 0:
                continue
            if s is None:
                s = c > 0
            elif (c > 0) != s:
                return False
        return True
    for y in range(32):
        for x in range(64):
            if inside(x + .5, y + .5):
                t = hsh(x // 3, y, 31)
                sp.set(x, y, BROWN[2] if t < .6 else BROWN[1])
    # obere Kante hell (Licht), untere dunkel
    for x in range(10, 55):
        sp.set(x, 6, BROWN[4]); sp.set(x, 7, BROWN[3])
        sp.set(x, 23, BROWN[0]); sp.set(x, 24, BROWN[0])
    # Innenraum mit Leinenfutter (schmaler als der Rand)
    for y in range(10, 21):
        for x in range(9, 56):
            if inside(x + .5, y + .5) and (x - 9) > (4 - (y - 10) * 0.0) and abs(y - 15) < 6 - max(0, (7 - x) // 2) - max(0, (x - 51) // 2):
                sp.set(x, y, CLOTH[3] if y < 14 else CLOTH[2] if y < 18 else CLOTH[1])
    for x in range(12, 53, 6):
        sp.set(x, 12, CLOTH[4])
    # Griffe/Beschlaege
    for x in (18, 32, 46):
        sp.set(x, 23, STONE[3]); sp.set(x + 1, 23, STONE[2])
    thick_outline(sp)
    return sp


def toter_weiss():
    """Bahre aus zwei Balken, darauf der Tote, in weisses Leinentuch gewickelt (Kopf links), drei Baender."""
    sp = Spr(64, 32)
    # Balken der Bahre
    for y in (22, 23, 24):
        for x in range(2, 62):
            sp.set(x, y, BROWN[2] if y == 22 else BROWN[1] if y == 23 else BROWN[0])
    for x in (6, 7, 8, 9, 54, 55, 56, 57):
        for y in range(25, 29):
            sp.set(x, y, BROWN[1] if x in (6, 54) else BROWN[0])           # Fuesse
    # Koerper: laenglich, Kopf links dicker, zum Fuss hin schmaler (Pixelmaske)
    def half_height(x):
        if x < 6 or x > 58:
            return 0
        if x < 18:                       # Kopf
            t = (x - 6) / 12.0
            return 3.0 + 5.0 * (1 - (1 - t) ** 2) ** 0.5
        if x < 24:                       # Schulter
            return 8.0
        if x > 52:                       # Fuesse
            return 5.0 - (x - 52) * 0.35
        return 8.0 - (x - 24) * 0.075
    cy = 14
    for x in range(64):
        h = half_height(x)
        if h <= 0:
            continue
        for y in range(int(cy - h), int(cy + h) + 1):
            u = (y - (cy - h)) / (2 * h)                # 0 oben (Licht) .. 1 unten
            v = 0.9 - u * 0.75 + (hsh(x, y, 41) - 0.5) * 0.18
            sp.set(x, y, CLOTH[int(max(0, min(5, round(v * 5))))])
    # Falten laengs und Wickelbaender (grau-violett)
    for x in range(12, 56):
        if hsh(x, 7, 5) < 0.55:
            sp.set(x, 12, CLOTH[2]); sp.set(x, 17, CLOTH[1])
    for bx in (19, 33, 46):
        for y in range(int(cy - half_height(bx)) + 1, int(cy + half_height(bx))):
            sp.set(bx, y, CLOTH[1]); sp.set(bx + 1, y, CLOTH[2])
    # Gesichtstuch: Schatten an der Stirnkante
    for y in range(11, 18):
        sp.set(8, y, CLOTH[1])
    thick_outline(sp)
    return sp


def schaufel_erde():
    sp = Spr(32, 32)
    mound(sp, 15, 26, 11, 4, 51)
    for y in range(4, 24):                                 # Stiel
        sp.set(21, y, BROWN[3]); sp.set(22, y, BROWN[2])
    for x in range(19, 25):                                # Griff
        sp.set(x, 3, BROWN[2]); sp.set(x, 4, BROWN[1])
    for y in range(22, 29):                                # Blatt, halb in der Erde
        for x in range(19, 25):
            sp.set(x, y, STONE[3] if x < 22 else STONE[1])
    thick_outline(sp)
    return sp


def grabhuegel_kreuz():
    sp = Spr(32, 32)
    mound(sp, 16, 22, 12, 6, 61)
    for y in range(8, 24):                                 # Holzkreuz
        sp.set(15, y, BROWN[3]); sp.set(16, y, BROWN[2])
    for x in range(11, 21):
        sp.set(x, 12, BROWN[3]); sp.set(x, 13, BROWN[2])
    thick_outline(sp)
    return sp


def grabhuegel_blumen():
    sp = Spr(32, 32)
    mound(sp, 16, 21, 12, 6, 71)
    cols = (WINE, CREAM, YELLOW, MAUVE, CREAM)
    for k in range(12):
        x = 8 + int(hsh(k, 1, 7) * 16)
        y = 15 + int(hsh(k, 2, 7) * 6)
        c = cols[k % len(cols)]
        sp.set(x, y, c); sp.set(x + 1, y, c); sp.set(x, y + 1, GREEN[3])
    thick_outline(sp)
    return sp


def kreuz_holz():
    sp = Spr(32, 32)
    for y in range(4, 28):
        for x in range(14, 18):
            sp.set(x, y, BROWN[3] if x == 14 else BROWN[2] if x < 17 else BROWN[1])
    for x in range(8, 24):
        for y in range(10, 13):
            sp.set(x, y, BROWN[4] if y == 10 else BROWN[2] if y == 11 else BROWN[1])
    for x in range(10, 23):
        sp.set(x, 28, EARTH[2]); sp.set(x, 27 if x % 3 else 28, EARTH[3])
    thick_outline(sp)
    return sp


def stone_shade(u, x, y, seed):
    v = 0.85 - u * 0.5 + (hsh(x, y, seed) - .5) * .2
    return STONE[int(max(1, min(5, round(v * 5))))]


def moss(sp, x0, x1, y0, y1, seed, p):
    for x in range(x0, x1):
        for y in range(y0, y1):
            if sp.solid(x, y) and hsh(x, y, seed) < p:
                sp.set(x, y, MOSS[1 + int(hsh(x, y, seed + 1) * 2)])


def grabstein_d():
    """Obelisk auf Sockel (32x64)."""
    sp = Spr(32, 64)
    for y in range(52, 62):
        for x in range(6, 26):
            sp.set(x, y, stone_shade((x - 6) / 20, x, y, 81))
    for y in range(40, 52):
        for x in range(9, 23):
            sp.set(x, y, stone_shade((x - 9) / 14, x, y, 82))
    for y in range(6, 40):
        half = 5 - (1 if y < 30 else 0) - (1 if y < 14 else 0)
        for x in range(16 - half, 16 + half):
            sp.set(x, y, stone_shade((x - (16 - half)) / (2 * half), x, y, 83))
    for k, y in enumerate(range(0, 6)):
        w = 5 - k // 2
        for x in range(16 - w + 2, 16 + w - 2):
            sp.set(x, 6 + y - 6 + 3, stone_shade(0.2, x, y, 84)) if False else None
    for y in range(2, 6):
        half = max(1, (y - 1))
        for x in range(16 - half, 16 + half):
            sp.set(x, y, stone_shade(0.1, x, y, 85))
    for y in range(20, 30):
        sp.set(15, y, STONE[1]); sp.set(16, y, STONE[1]) if y % 3 else None   # Inschrift
    moss(sp, 6, 26, 48, 62, 86, 0.18)
    thick_outline(sp)
    return sp


def grabstein_e():
    """Flache, schraege Platte mit Kerze (32x32)."""
    sp = Spr(32, 32)
    for y in range(14, 27):
        for x in range(5, 27):
            sp.set(x, y, stone_shade(((y - 14) / 13.0) * 0.8 + (x - 5) / 80.0, x, y, 91))
    for y in range(16, 22):
        for x in range(9, 23):
            if hsh(x, y, 92) < 0.35:
                sp.set(x, y, STONE[1])
    for x in range(7, 25):
        sp.set(x, 14, STONE[5])
    for y in range(8, 14):                                  # Kerzenstummel
        sp.set(27, y, CREAM); sp.set(28, y, STONE[3])
    sp.set(27, 7, YELLOW); sp.set(27, 6, AMBER)
    moss(sp, 5, 27, 20, 27, 93, 0.2)
    thick_outline(sp)
    return sp


def grabstein_f():
    """Hochkreuz mit Ring (32x32)."""
    sp = Spr(32, 32)
    for y in range(4, 28):
        for x in range(14, 19):
            sp.set(x, y, STONE[4] if x == 14 else STONE[3] if x < 17 else STONE[2])
    for x in range(8, 25):
        for y in range(9, 13):
            sp.set(x, y, STONE[4] if y == 9 else STONE[3] if y < 12 else STONE[2])
    for y in range(3, 18):                                  # Ring
        for x in range(8, 25):
            r = ((x + .5 - 16) ** 2 + (y + .5 - 10.5) ** 2) ** .5
            if 5.2 <= r <= 7.0:
                sp.set(x, y, STONE[4] if (x < 16 and y < 11) else STONE[2])
    for x in range(10, 23):
        for y in range(25, 28):
            sp.set(x, y, STONE[3] if y == 25 else STONE[2])
    moss(sp, 8, 25, 18, 28, 97, 0.22)
    thick_outline(sp)
    return sp


OBJ = {
    'Grab_Offen': grab_offen, 'Erdhaufen': erdhaufen, 'Sarg_Leer': sarg_leer, 'Toter_Weiss': toter_weiss,
    'Schaufel_Erde': schaufel_erde, 'Grabhuegel_Kreuz': grabhuegel_kreuz, 'Grabhuegel_Blumen': grabhuegel_blumen,
    'Kreuz_Holz': kreuz_holz, 'Grabstein_D': grabstein_d, 'Grabstein_E': grabstein_e, 'Grabstein_F': grabstein_f,
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else TILES + '/Dorf/Objekte'
    imgs = []
    for name, fn in OBJ.items():
        sp = fn()
        sp.save(os.path.join(out, name + '.png'))
        imgs.append(sp.im)
    if len(sys.argv) > 2:
        preview(sys.argv[2], imgs, scale=4)
    print('geschrieben:', ', '.join(OBJ))
