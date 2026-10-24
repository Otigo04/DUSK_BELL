"""FELSLAND (Art/Welt/05_Felsland): Felsboden, Klippen-/Plateau-Autotile mit Vorderwand, Treppe, Hoehleneingang, Felsobjekte, Kristalle.

Tileset/  Boden_Fels.png             4 nahtlose Varianten (Geroell, Risse) 128x32
          Plateau.png                47er-Autotile (Ms=12): Innen = begehbare Hochflaeche, Sued-Rand zeigt 12 px hohe Felswand, Aussen = Felsboden
          Plateau_Moos.png           dasselbe mit Moos-/Grasbewuchs auf der Hochflaeche
Objekte/  Treppe_Fels_S (32x48), Hoehleneingang (64x64), Felsbrocken_A-D, Geroellhaufen, Stalagmit_A/B, Felssaeule, Erzader_Wand (32x32, statisch)
Animiert/ Kristall_A/B (32x40, 8f), Erzader_Glitzern (32x32, 8f), Tropfen (16x32, 8f, Hoehlen-Tropfstein)
Aufruf: python gen_felsland.py"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import sys

import numpy as np
from PIL import Image

import welt_lib as W
import welt_tiles as TL
from welt_draw import Cv, COL, strip, static_noise, ring_shadow, rot90
from welt_lib import H, hsh

N = 8
S0, S1, S2, S3, S4, S5 = (H(h) for h in ('3d3850', '5a566e', '7a7790', '9e9bb2', 'c4c1d2', 'e4e0ea'))
BR0, BR1, BR2 = (H(h) for h in ('3a2530', '5a3a3f', '7d5646'))
G1, G2, G3 = (H(h) for h in ('2f5444', '3f7347', '58903f'))
P0, P1 = H('1f1630'), H('2a1d3b')
_fn = {}


def floor_px(x, y, v):
    if v not in _fn:
        _fn[v] = (static_noise(6, 6, 700 + v), static_noise(12, 12, 740 + v), static_noise(3, 3, 780 + v))
    n1, n2, n3 = _fn[v]
    a, b, r = n1[y, x], n2[y, x], n3[y, x]
    h = hsh(x, y, v, 701)
    c = S1
    if a > 0.8:
        c = S2
    elif a < 0.3:
        c = S0
    if abs(r - 0.5) < 0.018 and a < 0.8:
        c = S0                                                          # Risse (Hoehenlinie des Rauschens)
    if h > 0.965:
        c = S2 if h < 0.99 else S3                                      # Kiesel
    elif h < 0.012:
        c = BR1
    return c


def plateau_inside(sh, x, y, t, moss=False):
    n = _fn.setdefault('pl', (static_noise(5, 5, 710), static_noise(11, 11, 711), static_noise(3, 3, 712)))
    a, b, r = n[0][y, x], n[1][y, x], n[2][y, x]
    h = hsh(x, y, 2, 713)
    d = sh.D[y, x]
    c = S3
    if a > 0.7:
        c = S4
    elif a < 0.28:
        c = S2
    if abs(r - 0.5) < 0.016:
        c = S2
    if h > 0.975:
        c = S4 if c != S4 else S5
    elif h < 0.012:
        c = S2
    if moss and a < 0.3 and b > 0.45 and (b > 0.8 or h > 0.93):
        c = G2 if b < 0.9 else G3
    if moss and a > 0.82 and b > 0.5:
        c = G2
    P = sh.P
    top = (not sh.ext[y - 1 + P, x + P]) or (not sh.ext[y - 2 + P, x + P] and hsh(x, y, 3, 714) < 0.5)
    left = not sh.ext[y + P, x - 1 + P]
    if d <= 1.5:
        if top or left:
            return S5 if hsh(x, y, 4, 715) < 0.6 else S4                # beleuchtete Kante oben/links
        return S2 if hsh(x, y, 5, 715) < 0.6 else S1                   # Schattenkante unten/rechts
    if d <= 2.6 and (top or left) and hsh(x, y, 6, 715) < 0.4:
        return S4
    return c


def plateau_outside(sh, x, y):
    od = sh.OD[y, x]
    k = sh.face_depth(x, y)
    h = hsh(x, y, 7, 716)
    if k:                                                                 # Vorderwand (Sued-Rand): heller als Boden, dunkler als Hochflaeche
        col = x // 3                                                      # senkrechte Schichten
        base = S2 if hsh(col, 0, 8, 717) > 0.4 else S3
        v = base
        if (y + (1 if hsh(col, 1, 8, 717) > 0.5 else 0)) % 4 == 0:
            v = S3 if base == S2 else S4                                  # Schichtfugen (Horizontal)
        if hsh(x, y // 3, 9, 718) > 0.94:
            v = S1                                                        # Risse
        if x % 3 == 2 and hsh(col, 2, 8, 717) > 0.55:
            v = S1 if v in (S2, S3) else v                                # Spalten zwischen den Bloecken
        if k <= 1:
            return S1
        if k <= 3:
            v = S1 if h < 0.55 else S2                                    # Schatten direkt unter dem Rand
        if k >= 11:
            return S0 if h < 0.75 else S1                                 # Wandfuss
        return v
    if od <= 1.0:
        return S0
    if od <= 3.0 and h < 0.9 - 0.2 * od:
        return S1                                                         # Seitenwand/Schatten an O/W/N
    return floor_px(x, y, 0)


# ============================================================ Objekte
def rock(w, h, seed, rx, ry, cx=None, cy=None):
    cv = Cv(w, h)
    cx = w / 2 if cx is None else cx
    cy = h / 2 + 1 if cy is None else cy

    def fn(dx, dy, x, y):
        lit = -0.55 * dx - 0.85 * dy
        n = hsh(x, y, seed, 3)
        wob = 0.12 * math.sin(math.atan2(dy, dx) * 3 + seed)
        lit += wob
        if lit > 0.5:
            return 's5' if n > 0.55 else 's4'
        if lit > 0.1:
            return 's4' if n > 0.8 else ('s3' if n > 0.1 else 's2')
        if lit > -0.3:
            return 's2' if n > 0.12 else 's3'
        if lit > -0.6:
            return 's1' if n > 0.1 else 's2'
        return 's0' if n > 0.6 else 's1'
    cv.ell(cx, cy, rx, ry, fn)
    for k in range(3):                                                    # Risse
        x0, y0 = cx - rx * 0.5 + hsh(k, seed, 1, 720) * rx, cy - ry * 0.4 + hsh(k, seed, 2, 720) * ry * 0.6
        for i in range(5):
            if cv.solid(int(x0 + i * 0.7), int(y0 + i * 0.9)):
                cv.set(x0 + i * 0.7, y0 + i * 0.9, 's0')
    cv.outline('s0')
    ring_shadow(cv, cx, cy, rx, ry, 's0')
    return cv


def boulders():
    return {'Felsbrocken_A': rock(32, 32, 1, 10, 8).img(), 'Felsbrocken_B': rock(32, 32, 2, 7, 5.5).img(),
            'Felsbrocken_C': rock(48, 32, 3, 18, 10).img(), 'Felsbrocken_D': rock(32, 32, 4, 12, 11).img()}


def rubble():
    cv = Cv(32, 32)
    for k in range(9):
        x, y = 6 + hsh(k, 1, 1, 730) * 20, 10 + hsh(k, 2, 1, 730) * 14
        r = 1.5 + hsh(k, 3, 1, 730) * 3
        cv.ell(x, y, r, r * 0.75, lambda dx, dy, X, Y: 's4' if (-0.5 * dx - 0.8 * dy) > 0.3 else ('s2' if (-0.5 * dx - 0.8 * dy) > -0.3 else 's1'))
    cv.outline('s0')
    ring_shadow(cv, 16, 19, 12, 7, 's0')
    return cv.img()


def stalagmite(k):
    cv = Cv(32, 48)
    hgt = [34, 26][k]
    wd = [7, 6][k]
    for y in range(44 - hgt, 45):
        f = (y - (44 - hgt)) / float(hgt)
        half = max(0.5, wd * f ** 0.8)
        for x in range(int(16 - half - 1), int(16 + half + 2)):
            d = (x + 0.5 - 16) / max(half, 0.5)
            if abs(d) > 1:
                continue
            n = hsh(x, y, k, 740)
            cv.set(x, y, ('s4' if d < -0.4 else ('s3' if d < 0.2 else ('s2' if d < 0.65 else 's1'))) if n > 0.12 else 's1')
    cv.outline('s0')
    ring_shadow(cv, 16, 44, wd + 2, 3, 's0')
    return cv.img()


def pillar():
    cv = Cv(32, 64)
    for y in range(6, 60):
        f = y / 60.0
        half = 6 + int(3 * math.sin(f * 9) * 0.6) + (3 if y > 52 else 0) + (2 if y < 12 else 0)
        for x in range(16 - half, 16 + half + 1):
            d = (x - 16) / float(half)
            n = hsh(x, y // 2, 3, 750)
            c = 's4' if d < -0.45 else ('s3' if d < 0.1 else ('s2' if d < 0.6 else 's1'))
            if y % 9 == 0:
                c = 's1' if c != 's1' else 's0'
            if n > 0.93:
                c = 's0'
            cv.set(x, y, c)
    for x in range(8, 24):
        for y in range(2, 7):
            if hsh(x, y, 4, 751) < 0.7 and cv.solid(x, y + 1):
                cv.set(x, y, 's3')
    cv.outline('s0')
    ring_shadow(cv, 16, 59, 12, 4, 's0')
    return cv.img()


def stairs():
    """Treppe in die Felswand (Blick von oben/vorn): 4 Stufen, seitliche Mauern, oben Kantenstueck."""
    cv = Cv(32, 48)
    for y in range(0, 48):                                                 # seitliche Waende
        for x in list(range(0, 5)) + list(range(27, 32)):
            e = (4 - x) if x < 5 else (x - 27)
            cv.set(x, y, 's2' if e >= 2 else ('s1' if e >= 1 else 's0'))
            if hsh(x, y, 1, 760) > 0.85:
                cv.set(x, y, 's3')
    steps = 5
    sh_ = 48 // steps
    for i in range(steps):
        y0 = i * sh_ + (48 - steps * sh_)
        for y in range(y0, y0 + sh_):
            for x in range(5, 27):
                if y - y0 < 3:
                    c = 's4' if hsh(x, y, 2, 761) > 0.15 else 's3'              # Trittflaeche (hell)
                elif y - y0 < sh_ - 1:
                    c = 's1' if hsh(x, y, 3, 761) > 0.2 else 's2'               # Setzstufe (dunkler)
                else:
                    c = 's0'                                                    # Schattenlinie
                cv.set(x, y, c)
    return cv.img()


def cave():
    cv = Cv(64, 64)
    # Felsumrahmung (Bogen)
    for y in range(0, 64):
        for x in range(0, 64):
            dx, dy = (x + 0.5 - 32) / 29.0, (y + 0.5 - 40) / 36.0
            r = dx * dx + dy * dy
            if r <= 1.0 and not (y > 40 and abs(x - 32) > 29):
                n = hsh(x, y, 5, 770)
                lit = -0.4 * dx - 0.6 * dy
                c = 's2' if lit > 0 else 's1'
                if n > 0.9:
                    c = 's3'
                elif n < 0.08:
                    c = 's0'
                if (y // 5) % 2 == 0 and hsh(x // 4, y // 5, 6, 770) > 0.55:
                    c = 's1' if c != 's1' else 's2'
                cv.set(x, y, c)
    for y in range(64):                                                    # untere Kante gerade
        for x in range(64):
            if y > 61:
                cv.a[y, x] = (0, 0, 0, 0)
    # Oeffnung
    for y in range(14, 62):
        for x in range(14, 50):
            dx, dy = (x + 0.5 - 32) / 17.0, (y + 0.5 - 46) / 31.0
            if dx * dx + dy * dy <= 1.0 and not (y > 46 and False):
                d = math.hypot(dx, dy)
                cv.set(x, y, 'p0' if False else ('ink' if d < 0.8 else 'purp'))
    for y in range(40, 62):                                                # Boden im Eingang (etwas heller, nach innen dunkler)
        for x in range(16, 48):
            dx = (x + 0.5 - 32) / 16.0
            if cv.get(x, y)[:3] in (COL['ink'][:3], COL['purp'][:3]) and y > 52 + 4 * dx * dx:
                cv.set(x, y, 's1' if hsh(x, y, 8, 771) > 0.3 else 's0')
    # Stalaktiten
    for x in range(18, 47, 4):
        L = 3 + int(hsh(x, 1, 7, 772) * 6)
        for j in range(L):
            hw = max(0, (L - j) // 4)
            for w in range(-hw, hw + 1):
                if cv.get(x + w, 15 + j)[:3] in (COL['ink'][:3], COL['purp'][:3]):
                    cv.set(x + w, 15 + j, 's2' if w <= 0 else 's1')
    cv.outline('s0')
    for x in range(10, 54, 3):                                             # Moos oben
        if cv.solid(x, 6) and hsh(x, 6, 3, 773) > 0.5:
            cv.set(x, 6, 'g2')
            cv.set(x + 1, 7, 'g3')
    return cv.img()


def ore_wall():
    cv = Cv(32, 32)
    for y in range(32):
        for x in range(32):
            n = hsh(x // 2, y // 3, 1, 780)
            c = 's1' if n > 0.4 else 's2'
            if (y % 4 == 0):
                c = 's2' if c == 's1' else 's1'
            if hsh(x, y, 2, 780) > 0.94:
                c = 's0'
            cv.set(x, y, c)
    veins = [(5, 8, 12, 14), (12, 14, 18, 12), (18, 12, 24, 20), (9, 22, 20, 26)]
    for (x0, y0, x1, y1) in veins:
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            cv.set(x, y, 'yel')
            cv.set(x + 1, y, 'or1')
            cv.set(x, y + 1, 'br2')
    return cv


def ore_anim():
    base = ore_wall()
    frames = []
    spots = [(8, 10), (16, 13), (21, 16), (14, 24), (6, 9), (23, 22)]
    for t in range(N):
        cv = Cv(32, 32)
        cv.a[:] = base.a
        for k, (x, y) in enumerate(spots):
            ph = (t + k * 3) % N
            if ph == 0:
                cv.set(x, y, 'cream')
            elif ph == 1:
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    cv.set(x + dx, y + dy, 'cream' if dx == 0 and dy == 0 else 'yel')
            elif ph == 2:
                cv.set(x, y, 'cream')
        frames.append(cv.img())
    return frames


def crystal(k):
    frames = []
    spec = [[(10, 34, 5, 20, 0.0), (17, 36, 6, 28, 0.3), (24, 34, 4, 16, -0.25)], [(8, 36, 5, 14, -0.3), (15, 37, 6, 30, 0.0), (22, 36, 5, 22, 0.25), (27, 37, 3, 10, 0.4)]][k]
    for t in range(N):
        cv = Cv(32, 40)
        glow = 0.5 + 0.5 * math.sin(2 * math.pi * t / N)
        for y in range(40):                                                 # Schein
            for x in range(32):
                d = math.hypot(x + .5 - 16, (y + .5 - 28) * 1.1)
                if d < 15 and hsh(x, y, t % 4, 790) < (1 - d / 15.0) * (0.12 + 0.18 * glow):
                    cv.set(x, y, 'b4' if hsh(x, y, 2, 791) > 0.4 else 'violet')
        for (bx, by, w, h, lean) in spec:
            for y in range(by - h, by + 1):
                f = (by - y) / float(h)
                half = w * (1 - f ** 1.6) / 2.0 + 0.5
                cx = bx + lean * (by - y)
                for x in range(int(cx - half - 1), int(cx + half + 2)):
                    d = (x + 0.5 - cx) / max(half, 0.5)
                    if abs(d) > 1:
                        continue
                    c = 'b5' if d < -0.5 else ('b4' if d < 0.1 else ('b3' if d < 0.6 else 'b2'))
                    if f > 0.88:
                        c = 'b5'
                    cv.set(x, y, c)
        for (bx, by, w, h, lean) in spec:                                      # Funkeln wandert die Kante entlang
            ph = (t + int(bx)) % N
            if ph < 3:
                yy = by - int(h * (0.2 + 0.2 * ph))
                cv.set(bx + lean * (by - yy) - 1, yy, 'cream')
        cv.outline('b0')
        cv.under(lambda x, y: 's0' if 36 <= y <= 39 and hsh(x, y, 1, 792) < 0.6 and ((x - 16) / 14.0) ** 2 + ((y - 38) / 2.5) ** 2 <= 1 else None)
        frames.append(cv.img())
    return frames


def drip():
    frames = []
    for t in range(N):
        cv = Cv(16, 32)
        for y in range(0, 6):                                               # Tropfstein oben
            hw = max(0, (6 - y) // 2)
            for x in range(8 - hw - 1, 8 + hw + 2):
                cv.set(x, y, 's2' if x <= 8 else 's1')
        cv.set(8, 6, 's2')
        if t < 3:                                                           # Tropfen waechst
            cv.set(8, 7, 'b4')
            if t == 2:
                cv.set(8, 8, 'b4')
        elif t < 7:                                                         # faellt
            y = 8 + (t - 3) * 5
            cv.set(8, y, 'b5')
            cv.set(8, y + 1, 'b4')
        else:                                                               # Aufschlag
            for dx in (-2, -1, 1, 2):
                cv.set(8 + dx, 29, 'b4')
            cv.set(8, 28, 'b5')
        frames.append(cv.img())
    return frames


def main():
    td = W.zone_dir('felsland', 'Tileset')
    od = W.zone_dir('felsland', 'Objekte')
    ad = W.zone_dir('felsland', 'Animiert')
    errs = []

    def chk(im, name):
        errs.extend(W.check_palette(im, name))
    fl = TL.floor_set(td + '/Boden_Fels.png', floor_px, 4)
    chk(fl, 'Boden_Fels')
    pl = TL.build_blob(td + '/Plateau.png', lambda sh, x, y, t: plateau_inside(sh, x, y, t, False), plateau_outside, M=6, Ms=12, R=8, amp=1.0)
    chk(pl, 'Plateau')
    pm = TL.build_blob(td + '/Plateau_Moos.png', lambda sh, x, y, t: plateau_inside(sh, x, y, t, True), plateau_outside, M=6, Ms=12, R=8, amp=1.0)
    chk(pm, 'Plateau_Moos')
    TL.layout_json(td + '/_Layout_Felsland.json', 'Felsland', 1, {
        'ms': 12, 'hinweis': 'Ms=12: untere Kante zeigt 12 px hohe Felswand (Vorderwand). Plateau-Zellen NACH OBEN setzen, Wand entsteht automatisch unter der Hochflaeche. Zeile darunter = Felsboden-Zelle (Wand ragt 12 px in sie hinein).',
        'sheets': {'Plateau.png': 'Innen = Hochflaeche (Fels)', 'Plateau_Moos.png': 'Innen = Hochflaeche mit Moos', 'Boden_Fels.png': '4 Bodenvarianten'}})
    mp = ["..........~~~.......", "..........~~~~......", "..~~~~~...~~~.......", "..~~~~~~~~~~~~......", "..~~~~~~~~~~~~..~~..", "..~~~~~~~~..~~..~~..", "....~~~~....~~~~~~..", "..........~~~~~~~~..", "....................", "...................."]
    TL.preview_blob(pl, 'Felsland_Plateau', TL.split_floor(fl), mp)
    TL.preview_blob(pm, 'Felsland_PlateauMoos', TL.split_floor(fl), mp)
    objs = {'Treppe_Fels_S': stairs(), 'Hoehleneingang': cave(), 'Geroellhaufen': rubble(), 'Stalagmit_A': stalagmite(0), 'Stalagmit_B': stalagmite(1),
            'Felssaeule': pillar(), 'Erzader_Wand': ore_wall().img()}
    objs.update(boulders())
    for n, im in objs.items():
        im.save('%s/%s.png' % (od, n))
        chk(im, n)
    for n, fr in (('Kristall_A', crystal(0)), ('Kristall_B', crystal(1)), ('Erzader_Glitzern', ore_anim()), ('Tropfen', drip())):
        im = strip(fr)
        im.save('%s/%s.png' % (ad, n))
        chk(im, n)
        errs += W.check_loop(fr, n)
    print('Naht Plateau (Mittel, 95%%, Formfehler): %.2f %.2f %d' % TL.seam_ok(pl, M=6, Ms=12, R=8))
    if errs:
        print('\n'.join(errs))
        sys.exit(1)
    print('ok Felsland')


if __name__ == '__main__':
    main()
