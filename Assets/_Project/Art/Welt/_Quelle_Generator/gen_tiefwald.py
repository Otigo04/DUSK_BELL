"""TIEFWALD (Art/Welt/02_Tiefwald): dunkler Waldboden, Uebergang Gras -> Tiefwald, undurchdringliches Dickicht (Autotile) + Objekte.

Tileset/  Boden_Tiefwald.png        4 nahtlose Varianten (A-D) nebeneinander, 128x32
          Uebergang_Gras_Tiefwald   47er-Autotile: Innen = Waldboden, Aussen = Gras (Weg ins Dunkel)
          Dickicht                  47er-Autotile: Innen = Dornen-/Buschwand (nicht begehbar), Aussen = Waldboden
Objekte/  Riesenbaum (96x112), Toter_Baum (48x80), Baumstumpf_A/B, Baumstamm_H (64x32)/_V (32x64), Farn_A-C, Pilze_A/B, Wurzeln
Animiert/ Pilzring_Leuchten (48x48), Spinnennetz (32x32), Gluehwuermchen (64x64), Nebel (96x32) - je 8 Frames nebeneinander
Aufruf: python gen_tiefwald.py"""
import math
import sys

import numpy as np
from PIL import Image

import welt_lib as W
import welt_tiles as TL
from welt_draw import Cv, COL, strip, static_noise, ring_shadow
from welt_lib import H, hsh

N = 8
G0, G1, G2, G3, G4, G5 = (H(h) for h in ('243b3f', '2f5444', '3f7347', '58903f', '7bac45', 'a4c654'))
BR0, BR1, BR2, BR3, BR4 = (H(h) for h in ('3a2530', '5a3a3f', '7d5646', 'a37a56', 'c9a26a'))
S1, S2, S3 = (H(h) for h in ('5a566e', '7a7790', '9e9bb2'))
RED = H('c04b3f')
Z = (0, 0, 0, 0)

_floor_noise = {}


def floor_px(x, y, v):
    """Waldboden: dunkles Moos-/Laubgemisch, nur periodische Eingaben -> nahtlos."""
    if v not in _floor_noise:
        _floor_noise[v] = (static_noise(7, 7, 400 + v), static_noise(13, 13, 440 + v))
    n1, n2 = _floor_noise[v]
    a, b = n1[y, x], n2[y, x]
    h = hsh(x, y, v, 401)
    c = G1
    if a < 0.2 + 0.06 * b:
        c = G0
    elif a > 0.74:
        c = G2 if b > 0.45 else G1
    if b > 0.9 and c != G0:
        c = G2
    if h > 0.955:
        c = BR1 if h < 0.985 else BR2                                 # Laub
    elif h < 0.02:
        c = G0
    elif h < 0.035 and a > 0.5:
        c = G3                                                        # Moosspitzen
    elif h > 0.9935:
        c = S1                                                        # Kiesel
    return c


def grass_bg():
    return TL.terrain_grass(0).load()


def trans_inside(sh, x, y, t):
    c = floor_px(x, y, 0)
    d = sh.D[y, x]
    if d <= 2.2:                                                      # dunkler Saum am Waldrand
        if hsh(x, y, 5, 411) < 0.75 - 0.2 * (d - 0.5):
            return G0 if d <= 1.2 else (G1 if c != G0 else G0)
    return c


_gp = None


def trans_outside(sh, x, y):
    global _gp
    if _gp is None:
        _gp = grass_bg()
    od = sh.OD[y, x]
    if od <= 3.2 and hsh(x, y, 6, 412) < 0.8 - 0.22 * od:
        return G2 if hsh(x, y, 7, 413) > 0.5 else G1                 # Moos/Unterholz franst ins Gras
    return tuple(_gp[x, y])


_thick_n = {}


def thicket_inside(sh, x, y, t):
    if 'n' not in _thick_n:
        _thick_n['n'] = (static_noise(6, 6, 450), static_noise(13, 13, 451))
    n1, n2 = _thick_n['n']
    a, b = 0.5 * n1[y, x] + 0.5 * n2[y, x], n2[y, x]
    d = sh.D[y, x]
    h = hsh(x, y, 3, 452)
    c = G1
    if a > 0.5:
        c = G2
    if a > 0.78:
        c = G3
    if b > 0.85 and a > 0.5:
        c = G4 if h > 0.5 else G3
    if b < 0.2:
        c = G0
    # Licht von oben links: Kanten nach oben/links heller, unten/rechts dunkler
    if d <= 1.6:
        up = (not sh.ext[y - 1 + sh.P, x + sh.P]) or (not sh.ext[y + sh.P, x - 1 + sh.P])
        c = G0 if not up or h < 0.4 else G1
    elif d <= 2.8 and h < 0.35:
        c = G0
    if h > 0.972:
        return BR3                                                    # Dornen
    if h > 0.9935:
        return RED                                                    # Beeren
    if b > 0.9 and h > 0.3:
        return G5
    return c


def thicket_outside(sh, x, y):
    c = floor_px(x, y, 1)
    od = sh.OD[y, x]
    shadow = False
    P = sh.P
    for k in (1, 2, 3):                                              # Schlagschatten nach unten/rechts
        if sh.ext[y - k + P, x + P] or sh.ext[y + P, x - k + P]:
            shadow = True
            break
    if shadow and hsh(x, y, 8, 453) < 0.8:
        return G0
    if od <= 4.0 and hsh(x, y, 9, 454) < 0.18:
        return G0
    return c


# ============================================================ Objekte
def blob_ell(cv, cx, cy, rx, ry, seed, dark='g0', mid='g1', light='g2', hi='g3', sp=0.1):
    def fn(dx, dy, x, y):
        lit = -0.55 * dx - 0.8 * dy
        n = hsh(x, y, seed, 3)
        if lit > 0.5:
            return hi if n > sp else light
        if lit > 0.0:
            return light if n > sp else mid
        if lit > -0.5:
            return mid if n > sp else dark
        return dark
    cv.ell(cx, cy, rx, ry, fn)


def giant_tree():
    cv = Cv(96, 112)
    # Bodenschatten (gedithert)
    for y in range(86, 112):
        for x in range(10, 90):
            dx, dy = (x - 52) / 40.0, (y - 100) / 11.0
            if dx * dx + dy * dy <= 1 and hsh(x, y, 1, 501) < 0.72:
                cv.set(x, y, 'g0')
    # Stamm mit Wurzelanlauf
    for y in range(58, 108):
        f = (y - 58) / 50.0
        half = 7 + int(6 * f ** 3.0)
        for x in range(48 - half, 48 + half + 1):
            d = (x - 48) / float(half)
            n = hsh(x, y, 2, 502)
            c = 'br3' if d < -0.45 else ('br2' if d < 0.25 else ('br1' if d < 0.7 else 'br0'))
            if n > 0.86:
                c = 'br1' if c != 'br0' else 'br0'
            elif n < 0.08 and c != 'br3':
                c = 'br0'
            if x % 5 == 0 and hsh(x, y // 4, 3, 503) > 0.45:
                c = 'br1' if c in ('br2', 'br3') else 'br0'
            cv.set(x, y, c)
    for side in (-1, 1):                                                      # Wurzeln
        for k in range(14):
            cv.set(48 + side * (10 + k), 104 + (k // 4), 'br1')
            cv.set(48 + side * (10 + k), 103 + (k // 4), 'br2')
    # Krone: viele ueberlappende Ellipsen
    blobs = [(48, 36, 36, 26), (24, 46, 24, 20), (72, 46, 24, 20), (36, 24, 24, 18), (62, 24, 24, 18), (48, 52, 30, 14), (14, 56, 12, 10), (82, 56, 12, 10)]
    for k, (cx, cy, rx, ry) in enumerate(blobs):
        blob_ell(cv, cx, cy, rx, ry, 510 + k, sp=0.07)
    # Blattbueschel: kleine helle/dunkle Klumpen verteilen
    for k in range(70):
        x, y = int(8 + hsh(k, 1, 5, 520) * 80), int(8 + hsh(k, 2, 5, 520) * 58)
        if cv.solid(x, y):
            tone = hsh(k, 3, 5, 520)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 1)):
                if cv.solid(x + dx, y + dy):
                    cv.set(x + dx, y + dy, 'g4' if tone > 0.75 and dy == 0 else ('g3' if tone > 0.4 else 'g1'))
    cv.outline('g0')
    return cv.img()


def dead_tree():
    cv = Cv(48, 80)
    for y in range(34, 76):
        half = 3 + (y - 34) // 14
        for x in range(24 - half, 24 + half + 1):
            d = (x - 24) / float(half)
            n = hsh(x, y, 7, 530)
            cv.set(x, y, ('br3' if d < -0.3 else ('br2' if d < 0.4 else 'br1')) if n > 0.12 else 'br0')
    for y in range(74, 79):
        for x in range(14, 35):
            if hsh(x, y, 1, 531) < 0.5:
                cv.set(x, y, 'br0')

    def branch(x0, y0, x1, y1, w):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            ww = max(1, int(round(w * (1 - 0.75 * i / n))))
            for k in range(ww):
                cv.set(round(x) + k, round(y), 'br2' if k == 0 else 'br1')
    branch(24, 36, 10, 14, 3)
    branch(25, 38, 38, 8, 3)
    branch(24, 30, 24, 2, 3)
    branch(16, 22, 6, 24, 2)
    branch(33, 20, 43, 22, 2)
    branch(21, 44, 8, 38, 2)
    branch(27, 50, 41, 42, 2)
    cv.outline('br0')
    return cv.img()


def stump(k):
    cv = Cv(32, 32)
    cx, cy, rx, ry = 16, 15, [10.5, 8.5][k], [7.5, 6.0][k]
    cv.ell(cx, cy + 4, rx, ry, lambda dx, dy, x, y: 'br1' if (x + y // 2) % 4 else 'br2')
    cv.ell(cx, cy, rx, ry, lambda dx, dy, x, y: ('br5' if False else ('br4' if int(math.hypot(dx, dy) * 4.2) % 2 == 0 else 'br3')))
    cv.ell(cx, cy, 1.6, 1.2, lambda dx, dy, x, y: 'br2')
    for j in range(5 + 2 * k):                                                  # Moos
        a = hsh(j, k, 1, 540) * 6.28
        x, y = cx + (rx - 1.5) * math.cos(a) * 0.9, cy + (ry - 1) * math.sin(a) * 0.9
        cv.rect(int(x), int(y), int(x) + 1, int(y), 'g3' if j % 2 else 'g2')
    cv.outline('br0')
    ring_shadow(cv, cx, cy + 2, rx, ry, 'g0')
    return cv.img()


def log(vertical):
    cv = Cv(64, 32)
    for x in range(3, 61):
        yc = 17
        ht = 6.4 - (1.2 if x < 8 else 0) + 0.4 * math.sin(x * 0.3)
        for y in range(int(yc - ht - 1), int(yc + ht + 2)):
            d = (y + 0.5 - yc) / ht
            if abs(d) > 1:
                continue
            n = hsh(x, y, 4, 541)
            if d < -0.6:
                c = 'g3' if n > 0.35 else 'g2'                                  # Moos oben
            elif d < 0.15:
                c = 'br3' if n > 0.2 else 'br2'
            elif d < 0.65:
                c = 'br2' if n > 0.15 else 'br1'
            else:
                c = 'br1'
            if x % 11 == 5 and abs(d) < 0.85 and hsh(x, y, 5, 541) > 0.4:
                c = 'br0'
            cv.set(x, y, c)
    cv.ell(5, 17, 2.6, 5.6, lambda dx, dy, x, y: 'br4' if int(math.hypot(dx, dy) * 3) % 2 == 0 else 'br3')   # Hirnholz
    for x in range(52, 62):                                                       # zersplittertes Ende rechts
        for y in range(10, 25):
            if hsh(x, y, 6, 542) < (x - 52) / 10.0 * 0.9 and cv.solid(x, y):
                cv.a[y, x] = (0, 0, 0, 0)
    cv.outline('br0')
    ring_shadow(cv, 32, 17, 29, 6, 'g0')
    im = cv.img()
    return rot90_(im) if vertical else im


def rot90_(im):
    return im.transpose(Image.ROTATE_270)


def fern(k):
    """Farnwedel: gebogene Mittelrippe mit Fiederblaettchen, helle Spitzen; dunkler Schatten statt Kontur (liest sich auf Gras UND Waldboden)."""
    cv = Cv(32, 32)
    n = [7, 9, 6][k]
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2.0) * (math.pi * 0.9 / (n - 1)) + (hsh(i, k, 1, 550) - 0.5) * 0.2
        L = 12 + hsh(i, k, 2, 550) * 4
        for s in range(int(L * 2)):
            r = s / 2.0
            x = 16 + r * math.cos(a)
            y = 27 + r * math.sin(a) + 0.02 * r * r
            cv.set(round(x), round(y), 'g1' if r < L * 0.4 else 'g2')
            if int(r) % 2 == 1 and r > 2:
                nx, ny = -math.sin(a), math.cos(a)
                ln = max(1, int(round(3.4 * (1 - r / L)) + 1))
                for sd in (-1, 1):
                    for j in range(1, ln + 1):
                        c = 'g5' if (j == ln and r > L * 0.3) else ('g4' if j > 1 else 'g3')
                        cv.set(round(x + sd * nx * j), round(y + sd * ny * j + j * 0.4), c)
    for y in range(26, 31):
        for x in range(10, 23):
            if not cv.solid(x, y) and hsh(x, y, 3, 551) < 0.55 and ((x - 16) / 7.0) ** 2 + ((y - 28) / 2.4) ** 2 <= 1:
                cv.set(x, y, 'g0')
    return cv.img()


def mushrooms(k):
    cv = Cv(32, 32)
    spec = [[(10, 22, 6, 'red'), (20, 19, 8, 'red'), (16, 26, 4, 'red')], [(9, 21, 7, 'br'), (19, 22, 6, 'br'), (23, 15, 4, 'br')]][k]
    for (cx, cy, r, kind) in sorted(spec, key=lambda s: s[1]):
        for y in range(cy, cy + r // 2 + 3):                                         # Stiel
            for x in range(cx - 1, cx + 2):
                cv.set(x, y, 'cream' if x < cx + 1 else 's3')
        cv.ell(cx, cy, r * 0.7, r * 0.5, lambda dx, dy, x, y, kind=kind, cx=cx: (('red' if (-0.5 * dx - 0.8 * dy) > -0.1 else 'wine') if kind == 'red' else ('br4' if (-0.5 * dx - 0.8 * dy) > 0.1 else ('br3' if (-0.5 * dx - 0.8 * dy) > -0.3 else 'br2'))))
        if kind == 'red':
            for dx, dy in ((-2, -1), (1, -2), (2, 0)):
                if cv.solid(cx + dx, cy + dy):
                    cv.set(cx + dx, cy + dy, 'cream')
    cv.outline('br0')
    ring_shadow(cv, 16, 24, 11, 3, 'g0')
    return cv.img()


def roots():
    cv = Cv(32, 32)

    def twist(x0, y0, ang, L, w):
        for i in range(L):
            ang += 0.06 * math.sin(i * 0.5 + x0)
            x0 += math.cos(ang)
            y0 += math.sin(ang)
            ww = max(1, int(w * (1 - i / float(L)) + 0.5))
            for k in range(ww):
                cv.set(round(x0), round(y0) + k, 'br2' if k == 0 else 'br1')
    twist(4, 14, 0.1, 22, 4)
    twist(6, 17, 0.5, 22, 3)
    twist(5, 12, -0.4, 20, 3)
    twist(8, 20, 1.0, 16, 2)
    cv.outline('br0')
    ring_shadow(cv, 16, 17, 14, 7, 'g0')
    return cv.img()


# ---- Animiert
def mush_ring():
    frames = []
    cx0, cy0 = 24, 24
    for t in range(N):
        cv = Cv(48, 48)
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t / N)
        # Leuchtschein (gedithert, pulsiert)
        for y in range(48):
            for x in range(48):
                d = math.hypot(x + .5 - cx0, (y + .5 - cy0) * 1.25)
                if d < 15 + 2 * pulse and hsh(x, y, t % 4, 560) < (1 - d / 17.0) * 0.28 * (0.5 + pulse):
                    cv.set(x, y, 'b4' if hsh(x, y, 1, 561) > 0.5 else 'pk')
        for k in range(8):
            a = k * math.pi / 4 + 0.2
            mx, my = cx0 + 13 * math.cos(a), cy0 + 9.5 * math.sin(a)
            r = 2 + (k % 3)
            cv.rect(int(mx), int(my), int(mx), int(my) + 2, 'cream')
            cv.ell(mx, my - 0.5, r * 0.8 + 1, r * 0.55 + 0.6, lambda dx, dy, x, y, k=k: 'v1' if False else ('violet' if (-0.5 * dx - 0.8 * dy) > 0 else 'purp'))
            if (k + t) % 4 == 0:
                cv.set(int(mx), int(my) - 1, 'cream')
        cv.outline('ink')
        frames.append(cv.img())
    return frames


def web():
    frames = []
    for t in range(N):
        cv = Cv(32, 32)
        sway = int(round(1.2 * math.sin(2 * math.pi * t / N)))
        cx, cy = 16, 14
        spokes = 7
        for k in range(spokes):
            a = k * 2 * math.pi / spokes + 0.3
            for r in range(1, 15):
                x = cx + r * math.cos(a) + sway * (r / 14.0) * 1.2
                y = cy + r * math.sin(a) * 0.95
                cv.set(round(x), round(y), 's4' if r % 4 else 's3')
        for ring in (4, 8, 12):
            for q in range(120):
                a = q / 120.0 * 2 * math.pi
                x = cx + ring * math.cos(a) + sway * (ring / 14.0) * 1.2
                y = cy + ring * math.sin(a) * 0.95
                if hsh(q, ring, 2, 570) > 0.3:
                    cv.set(round(x), round(y), 's5')
        # Tautropfen funkeln
        for k in range(3):
            if (t + k * 3) % N < 2:
                cv.set(cx + (k - 1) * 5 + sway, cy + (k % 2) * 4 - 2, 'b5')
        # Faden nach oben
        for y in range(0, 4):
            cv.set(cx + sway // 2, y, 's4')
        frames.append(cv.img())
    return frames


def fireflies():
    frames = []
    pts = [(14, 20, 6, 0.0), (44, 14, 5, 1.7), (30, 38, 7, 3.1), (52, 46, 4, 0.9), (10, 50, 5, 2.4), (36, 8, 4, 4.2), (22, 56, 3, 5.0)]
    for t in range(N):
        cv = Cv(64, 64)
        for k, (x0, y0, r, ph) in enumerate(pts):
            a = 2 * math.pi * t / N + ph
            x, y = x0 + r * math.cos(a), y0 + r * 0.7 * math.sin(2 * a)
            on = (t + k * 3) % N not in (3, 4) if k % 2 else (t + k) % N != 6
            if on:
                cv.set(round(x), round(y), 'yel')
                if (t + k) % 2 == 0:
                    cv.set(round(x) + 1, round(y), 'g5')
                    cv.set(round(x) - 1, round(y), 'g5')
                    cv.set(round(x), round(y) + 1, 'g5')
            elif hsh(k, t, 1, 580) > 0.5:
                cv.set(round(x), round(y), 'g4')
        frames.append(cv.img())
    return frames


def fog():
    """Nebelschwaden: gedithertes Band, 96x32, wandert 4 px/Frame nach rechts (32-px-Periode, 3 Wiederholungen -> Schleife nahtlos)."""
    n1 = W.noise_field(5, 2, 0, N, 590, sx=4)
    n2 = W.noise_field(11, 4, 0, N, 591, sx=4)
    frames = []
    for t in range(N):
        cv = Cv(96, 32)
        for y in range(32):
            band = 1.0 - abs(y - 15.5) / 15.5
            for x in range(96):
                v = n1[t, y, x % 32] * 0.7 + n2[t, y, x % 32] * 0.3
                v = v * (0.45 + 0.8 * band)
                thr = 0.5
                if v > thr + 0.16:
                    if (x + y) % 2 == 0 or hsh(x, y, 1, 592) > 0.7:
                        cv.set(x, y, 's5' if v > thr + 0.26 else 's4')
                elif v > thr + 0.08:
                    if (x + 2 * y) % 3 == 0:
                        cv.set(x, y, 's4')
                elif v > thr and (x + y) % 2 == 0:
                    cv.set(x, y, 's4')
        frames.append(cv.img())
    return frames


def main():
    td = W.zone_dir('tiefwald', 'Tileset')
    od = W.zone_dir('tiefwald', 'Objekte')
    ad = W.zone_dir('tiefwald', 'Animiert')
    errs = []

    def chk(im, name):
        errs.extend(W.check_palette(im, name))

    fl = TL.floor_set(td + '/Boden_Tiefwald.png', lambda x, y, v: floor_px(x, y, v), 4)
    chk(fl, 'Boden_Tiefwald')
    tr = TL.build_blob(td + '/Uebergang_Gras_Tiefwald.png', trans_inside, trans_outside, M=5, R=7, amp=1.4)
    chk(tr, 'Uebergang_Gras_Tiefwald')
    th = TL.build_blob(td + '/Dickicht.png', thicket_inside, thicket_outside, M=3, R=7, amp=1.6)
    chk(th, 'Dickicht')
    TL.layout_json(td + '/_Layout_Tiefwald.json', 'Tiefwald', 1, {
        'sheets': {'Uebergang_Gras_Tiefwald.png': 'Innen = Waldboden, Aussen = Gras (M=5)', 'Dickicht.png': 'Innen = Dornenwand (nicht begehbar), Aussen = Waldboden (M=3)',
                   'Boden_Tiefwald.png': '4 nahtlose Bodenvarianten 32x32 nebeneinander (zufaellig streuen)'}})
    for nm, sh, land, mp in (('Tiefwald_Uebergang', tr, TL.terrain_grass(0), None), ('Tiefwald_Dickicht', th, TL.split_floor(fl), None)):
        TL.preview_blob(sh, nm, land, mp)
    objs = {'Riesenbaum': giant_tree(), 'Toter_Baum': dead_tree(), 'Baumstumpf_A': stump(0), 'Baumstumpf_B': stump(1), 'Baumstamm_H': log(False), 'Baumstamm_V': log(True),
            'Farn_A': fern(0), 'Farn_B': fern(1), 'Farn_C': fern(2), 'Pilze_A': mushrooms(0), 'Pilze_B': mushrooms(1), 'Wurzeln': roots()}
    for n, im in objs.items():
        im.save('%s/%s.png' % (od, n))
        chk(im, n)
    for n, fr in (('Pilzring_Leuchten', mush_ring()), ('Spinnennetz', web()), ('Gluehwuermchen', fireflies()), ('Nebel', fog())):
        im = strip(fr)
        im.save('%s/%s.png' % (ad, n))
        chk(im, n)
        errs += W.check_loop(fr, n)
    print('Naht Uebergang (Mittel, 95%%, Formfehler): %.2f %.2f %d' % TL.seam_ok(tr, M=5, R=7, amp=1.4))
    print('Naht Dickicht  (Mittel, 95%%, Formfehler): %.2f %.2f %d' % TL.seam_ok(th, M=3, R=7, amp=1.6))
    if errs:
        print('\n'.join(errs))
        sys.exit(1)
    print('ok Tiefwald')


if __name__ == '__main__':
    main()
