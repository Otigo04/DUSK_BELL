"""ERDBAU: Schlafplatz des Gastes. Monster-Bibel: "Erdbau am Waldrand, unter der Wurzel der verkruepelten Birke. Geweckt jagt er zuerst,
weil er den Weg zur Veranda kennt." Wecklevel (Regelwerk): 0-2 Monster schlaeft, 3 Unruhe, 4 Tagesjagd, 5 Monster ist wach.
Objekte (Pivot unten links, 32 px Raster) -> Art/Tiles/Dorf/Objekte:
  Birke_Verkruppelt       64x128  gedrehter, kranker Stamm, kahle Aeste, wenige welke Blaetter, Wurzelbogen unten (= Zustand schlaeft)
  Erdbau_Eingang_Schlaeft 64x32   Ueberlagerung/Ersatz der unteren 32 Zeilen: Loch klein, Laub, Spinnfaeden, Moos (Wecklevel 0-2)
  Erdbau_Eingang_Unruhig  64x32   Loch groesser, frisch ausgeworfene Erde, Kratzspuren an den Wurzeln (Wecklevel 3-4)
  Erdbau_Eingang_Wach     64x32   weit offen, Erde weit verstreut, Wurzel gebrochen, tiefe Kratzer, zwei Augen im Dunkel (Wecklevel 5)
Anim: Erdbau_Eingang_Wach_Anim.png (4 Frames, Augen blinzeln) -> Art/Tiles/Dorf/Animiert (nicht von DorfBuilder gescannt).
Die unteren 32 Zeilen von Birke_Verkruppelt sind identisch mit Erdbau_Eingang_Schlaeft: die Eingaenge koennen 1:1 darueber getauscht werden.
Aufruf: python erdbau_objekte.py   (schreibt auch Vorschau_Erdbau.png)"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from nwlib import *

OUTLINE = H('1a1526')
OL2 = H('2b2140')
MOON = H('e8e0f0')
BARK = [H(x) for x in ('4f3d5c', '6e6a74', '9a95a0', 'e8e0f0')]      # Birkenrinde: dunkel -> hell (kuehl)
EARTH = [H(x) for x in ('2b2140', '3b2a22', '5c4033', '7a5a43', '9c7a5a', 'b89a72')]
MOSS = [H(x) for x in ('1e3a2b', '2f5a3c', '4a7a4f')]
LEAF = [H(x) for x in ('7a5a43', 'b89a72', 'ffd27a', 'ffa550')]      # sterbendes Laub: braun, strohgelb, gelb, orange
ROOT = [H(x) for x in ('3b2a22', '5c4033', '7a5a43', '9c7a5a')]
EYE = H('d64a6a')
CREAM = H('fff1c9')
NB_D = H('1f2a3d')
ST = [H(x) for x in ('4a4550', '6e6a74', '9a95a0')]
WLITE = H('9c7a5a')


def seg(sp, x0, y0, x1, y1, w0, w1, cols, seed=0):
    """Gebogener Ast/Wurzel: dicke Linie mit Verjuengung; cols = (dunkel, mittel, hell). Licht von links oben."""
    n = int(max(abs(x1 - x0), abs(y1 - y0), 1) * 1.5)
    for i in range(n + 1):
        t = i / n
        cx = x0 + (x1 - x0) * t
        cy = y0 + (y1 - y0) * t
        w = w0 + (w1 - w0) * t
        for dy in range(-int(w / 2) - 1, int(w / 2) + 2):
            for dx in range(-int(w / 2) - 1, int(w / 2) + 2):
                d = math.hypot(dx, dy)
                if d <= w / 2 + 0.3:
                    lam = (-dx * 0.7 - dy * 0.7) / max(1, w / 2)
                    c = cols[2] if lam > 0.35 else (cols[1] if lam > -0.35 else cols[0])
                    if hsh(int(cx) + dx, int(cy) + dy, seed) < 0.08:
                        c = cols[0]
                    sp.set(int(round(cx + dx)), int(round(cy + dy)), c)


def curve(pts, steps=24):
    """Catmull-Rom-aehnlich: weiche Kurve durch Punkte."""
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(len(pts) - 1, i + 2)]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


# ====================================================================== Baum
def bark_col(u):
    return BARK[3] if u < 0.18 else (BARK[2] if u < 0.55 else (BARK[1] if u < 0.85 else BARK[0]))


def tree_top():
    sp = Spr(64, 128)
    ctrl = [(36, 4), (30, 18), (37, 42), (27, 68), (34, 90), (32, 104)]      # gedrehter, schiefer Stamm
    path = curve(ctrl, 12)
    pys = [p[1] for p in path]
    pxs = [p[0] for p in path]
    for yy in range(int(ctrl[0][1]), 105):
        x = float(np.interp(yy, pys, pxs))
        w = 4 + 10 * (yy - ctrl[0][1]) / (104 - ctrl[0][1])
        for dx in range(-int(w / 2) - 1, int(w / 2) + 2):
            if abs(dx) > w / 2 + 0.4:
                continue
            u = (dx + w / 2) / max(1.0, w)
            sp.set(int(round(x + dx)), yy, bark_col(u))
    # Birkenmale: dunkle Querstriche, Moos, kranke Stellen
    for y in range(8, 104):
        row = [x for x in range(64) if sp.solid(x, y)]
        if not row:
            continue
        for x in row:
            if hsh(x, y // 2, 31) < 0.13 and hsh(x, y, 32) < 0.7:
                sp.set(x, y, BARK[0])
            if y > 60 and x > (row[0] + row[-1]) / 2 and hsh(x, y, 33) < 0.18:
                sp.set(x, y, MOSS[0] if hsh(x, y, 34) < 0.5 else MOSS[1])
            if 36 < y < 52 and hsh(x, y, 35) < 0.20:
                sp.set(x, y, EARTH[1])                                 # faule Stelle
    for (x, y) in ((28, 58), (29, 59), (33, 38)):                      # Spechtloecher
        sp.set(x, y, OUTLINE)
        sp.set(x + 1, y, OUTLINE)
    for k in range(4):                                                 # Baumpilz
        sp.set(37 + k, 72 + (k > 1), H('b89a72'))
        sp.set(37 + k, 73 + (k > 1), H('7a2e3a'))
    # Aeste: krumm, teils hakenfoermig, kahl
    limbs = [([(30, 66), (22, 54), (12, 46), (8, 56)], 5, 1),
             ([(36, 40), (46, 30), (54, 22), (58, 28)], 4, 1),
             ([(31, 24), (22, 16), (14, 12), (12, 20)], 3, 1),
             ([(35, 14), (42, 8), (50, 6)], 3, 1),
             ([(28, 82), (20, 80), (14, 86)], 3, 1)]
    for pts, w0, w1 in limbs:
        p = curve(pts, 8)
        for i in range(len(p) - 1):
            t = i / len(p)
            seg(sp, p[i][0], p[i][1], p[i + 1][0], p[i + 1][1], w0 + (w1 - w0) * t, w0 + (w1 - w0) * (t + 0.1), BARK[0:3][::1] if False else (BARK[0], BARK[1], BARK[2]), 40 + i)
    for (x0, y0, x1, y1) in ((12, 46, 6, 42), (8, 56, 3, 60), (58, 28, 62, 22), (54, 22, 60, 16), (14, 12, 8, 8), (12, 20, 6, 24),
                             (50, 6, 56, 4), (22, 54, 16, 60), (46, 30, 52, 38)):                # Zweige
        seg(sp, x0, y0, x1, y1, 2, 1, (BARK[0], BARK[0], BARK[1]), 77)
    # Laub: sehr wenig und welk
    for (cx, cy) in ((9, 52), (57, 26), (13, 14), (47, 8), (20, 56), (60, 20)):
        for k in range(9):
            x = cx + int((hsh(k, cx, 61) - 0.5) * 6)
            y = cy + int((hsh(k, cy, 62) - 0.5) * 5)
            sp.set(x, y, LEAF[int(hsh(x, y, 63) * 4)])
    sp.outline(OUTLINE)
    return sp


# ====================================================================== Wurzeln und Eingang
def hole(sp, cx, cy, rx, ry):
    """Dunkles Loch: Rand OL1, innen OL2, tief NB_D, Erde am oberen Lippenrand."""
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            d = nx * nx + ny * ny
            if d <= 1.0:
                sp.set(x, y, OL2 if d > 0.35 else (NB_D if d > 0.12 else OUTLINE))
            elif d <= 1.35:
                sp.set(x, y, OUTLINE)


def root(sp, pts, w0, w1, seed):
    p = curve(pts, 10)
    for i in range(len(p) - 1):
        t = i / len(p)
        seg(sp, p[i][0], p[i][1], p[i + 1][0], p[i + 1][1], w0 + (w1 - w0) * t, w0 + (w1 - w0) * (t + 0.08), (ROOT[0], ROOT[1], ROOT[2]), seed + i)
        if hsh(i, seed, 5) < 0.35:                                     # Moos auf der Wurzel
            sp.set(int(p[i][0]), int(p[i][1]) - 1, MOSS[1])


def base(state, f=0):
    sp = Spr(64, 32)
    # Erdlager
    big = {'schlaeft': 1.0, 'unruhig': 1.25, 'wach': 1.55}[state]
    for y in range(14, 31):
        for x in range(2, 62):
            nx, ny = (x + .5 - 32) / 30.0, (y + .5 - 22) / 9.5
            if nx * nx + ny * ny <= 1.0:
                v = 0.25 + 0.55 * hsh(x, y, 71) + (0.2 if ny < -0.2 else 0)
                sp.set(x, y, EARTH[1 + int(v * 3)])
    # Stammfuss
    for y in range(0, 15):
        w = 13 + y * 0.9
        xc = 32 + (1 if y < 3 else 0)
        for x in range(int(xc - w / 2), int(xc + w / 2) + 1):
            u = (x - (xc - w / 2)) / max(1.0, w)
            c = bark_col(u)
            if hsh(x, y // 2, 36) < 0.13 and hsh(x, y, 37) < 0.7:
                c = BARK[0]
            sp.set(x, y, c)
    # Wurzeln: vier kraeftige Wurzeln, vorn zwei, die den Bogen ueber dem Loch bilden
    root(sp, [(26, 10), (18, 14), (11, 20), (6, 27)], 6, 3, 100)
    root(sp, [(38, 10), (46, 14), (53, 20), (58, 28)], 6, 3, 110)
    root(sp, [(22, 8), (14, 8), (6, 12)], 4, 2, 120)
    root(sp, [(42, 8), (50, 8), (58, 12)], 4, 2, 130)
    # Eingang
    rx, ry = 6.5 * big, 5.5 * big
    cx, cy = 32, 20
    if state == 'wach':
        rx, ry = 10.5, 8.5
    hole(sp, cx, cy, rx, ry)
    # Rand: obere Wurzelbruecke ueber dem Loch (macht aus dem Loch einen Bau unter der Wurzel)
    root(sp, [(cx - rx - 3, cy - 1), (cx - rx * 0.5, cy - ry - 3), (cx + rx * 0.5, cy - ry - 3), (cx + rx + 3, cy - 1)], 4.5, 4.5, 140)
    # vordere Erdlippe
    for x in range(int(cx - rx - 3), int(cx + rx + 4)):
        yy = int(cy + ry * math.sqrt(max(0.0, 1 - ((x - cx) / (rx + 3)) ** 2))) + 2
        for k in range(3):
            sp.set(x, yy + k, EARTH[3 - k] if hsh(x, k, 81) < 0.7 else EARTH[2])
    if state == 'schlaeft':
        for k in range(26):                                            # welkes Laub im Eingang, Spinnfaeden
            x = int(cx - rx + hsh(k, 1, 91) * rx * 2)
            y = int(cy + (hsh(k, 2, 91) - 0.3) * ry)
            sp.set(x, y, LEAF[int(hsh(k, 3, 91) * 2)])
        for a in (10, 35, 60):                                         # Spinnwebe in der oberen linken Ecke des Lochs
            for r in range(2, 8):
                sp.set(int(cx - rx + 1 + r * math.cos(math.radians(a))), int(cy - ry + 2 + r * math.sin(math.radians(a))), ST[2] if r % 2 else ST[1])
        for (x, y) in ((cx - 12, 26), (cx + 12, 27)):                  # Pilze
            sp.set(x, y, H('b89a72'))
            sp.set(x, y - 1, H('f2ead8'))
    elif state == 'unruhig':
        for k in range(60):                                            # frisch ausgeworfene, helle Erde beidseitig
            a = (k % 2) * 2 - 1
            x = int(cx + a * (rx + 2 + hsh(k, 1, 92) * 12))
            y = int(cy + 5 + hsh(k, 2, 92) * 7)
            sp.set(x, y, EARTH[4 + int(hsh(k, 3, 92) * 2)])
        for k in range(3):                                             # Kratzer an der Wurzelbruecke
            sp.line(int(cx - 7 + k * 3), int(cy - ry - 5), int(cx - 6 + k * 3), int(cy - ry), WLITE)
        for k in range(16):
            x = int(8 + hsh(k, 4, 93) * 48)
            y = int(22 + hsh(k, 5, 93) * 8)
            sp.set(x, y, LEAF[int(hsh(k, 6, 93) * 2)])
    else:
        for k in range(110):                                           # Erde weit verstreut
            a = (k % 2) * 2 - 1
            x = int(cx + a * (rx + 1 + hsh(k, 1, 94) * 20))
            y = int(cy + 3 + hsh(k, 2, 94) * 10)
            sp.set(x, y, EARTH[4 + int(hsh(k, 3, 94) * 2)] if hsh(k, 7, 94) < 0.7 else EARTH[2])
        for k in range(4):                                             # tiefe Kratzer ueber die ganze Wurzelbruecke
            sp.line(int(cx - 10 + k * 5), int(cy - ry - 6), int(cx - 8 + k * 5), int(cy - ry + 1), WLITE)
            sp.line(int(cx - 10 + k * 5), int(cy - ry - 6), int(cx - 10 + k * 5), int(cy - ry - 5), CREAM)
        for (x, y) in ((cx + 14, cy - 3), (cx + 15, cy - 4), (cx + 16, cy - 2), (cx + 17, cy - 2)):     # gebrochene Wurzel, helles Holz
            sp.set(int(x), int(y), WLITE)
            sp.set(int(x) + 1, int(y), CREAM)
        # Augen im Dunkel (f: 0-2 offen, 3 blinzelt)
        for ex in (cx - 4, cx + 3):
            if f < 3:
                sp.rect(ex, cy - 1, ex + 1, cy, EYE)
                sp.set(ex, cy - 1, H('ff9aa9') if False else EYE)
            else:
                sp.rect(ex, cy, ex + 1, cy, EYE)
    sp.outline(OUTLINE) if False else None
    return sp


def tree_full():
    sp = tree_top()
    b = base('schlaeft')
    for y in range(32):
        for x in range(64):
            c = b.get(x, y)
            if c[3]:
                sp.set(x, 96 + y, c)
    return sp


OBJ = {
    'Birke_Verkruppelt': tree_full,
    'Erdbau_Eingang_Schlaeft': lambda: base('schlaeft'),
    'Erdbau_Eingang_Unruhig': lambda: base('unruhig'),
    'Erdbau_Eingang_Wach': lambda: base('wach', 0),
}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else TILES + '/Dorf/Objekte'
    imgs = []
    for name, fn in OBJ.items():
        sp = fn()
        sp.save(os.path.join(out, name + '.png'))
        imgs.append(sp.im)
    fr = [base('wach', f) for f in range(4)]
    adir = TILES + '/Dorf/Animiert'
    os.makedirs(adir, exist_ok=True)
    strip = Image.new('RGBA', (64 * 4, 32), (0, 0, 0, 0))
    for i, f in enumerate(fr):
        strip.paste(f.im, (i * 64, 0))
    strip.save(adir + '/Erdbau_Eingang_Wach_Anim.png')
    S = 4
    sh = Image.new('RGBA', (64 * S * 4 + 50, 128 * S + 20), (80, 100, 80, 255))
    x = 10
    for im in imgs:
        b = im.resize((im.width * S, im.height * S), Image.NEAREST)
        sh.alpha_composite(b, (x, 10 + (128 * S - b.height) if b.height < 128 * S else 10))
        x += b.width + 10
    sh.save(TILES + '/Dorf/Vorschau_Erdbau.png')
    print('geschrieben:', ', '.join(OBJ), '+ Anim')
