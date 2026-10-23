"""FLUSS-OBJEKTE (Art/Welt/03_Fluss/Objekte = statisch, Art/Welt/03_Fluss/Animiert = 8-Frame-Streifen, Frames nebeneinander).

Statisch  : Findling_A-C, Furtstein_A-D, Pfahl, Steg_Mitte_H/V, Steg_Ende_H_L/R, Steg_Ende_V_O/U, Bruecke_Holz_Mitte_H, Bruecke_Holz_Bruch_L/R,
            Bruecke_Holz_Luecke, Bruecke_Pfeiler
Animiert  : Findling_Schaum_S/N/O/W (Stein mit Schaum), Furtstein_Schaum, Seerose_A-C, Schilf_A-C, Rohrkolben, Strudel, Treibholz,
            Pfahl_Wellen, Wasserfall_{Kante,Mitte,Fuss}_{L,M,R}
Alles liegt TRANSPARENT ueber dem Wasser-Tileset (ausser Wasserfall-Kacheln, die sind vollflaechig). Palette.png, Alpha 0/255, 8 Frames, Schleife nahtlos.
Aufruf: python gen_fluss_objekte.py"""
import math
import sys

import numpy as np
from PIL import Image

import welt_lib as W
from welt_lib import H, hsh

from welt_draw import Cv, COL, strip, ring_shadow, rot90

N = 8


# ================================================================ Steine
def stone(cv, cx, cy, rx, ry, seed, shape=0):
    def fn(dx, dy, x, y):
        lit = -0.55 * dx - 0.85 * dy
        n = hsh(x, y, seed, 3)
        if lit > 0.55:
            return 's4' if n > 0.2 else 's5'
        if lit > 0.12:
            return 's3' if n > 0.15 else 's4'
        if lit > -0.35:
            return 's2' if n > 0.12 else 's3'
        return 's1' if n > 0.15 else 's2'
    cv.ell(cx, cy, rx, ry, fn)
    for k in range(2 + shape):                                       # Risse / Moos
        x, y = int(cx - rx * 0.6 + hsh(k, seed, 5, 1) * rx * 1.2), int(cy - ry * 0.4 + hsh(k, seed, 6, 1) * ry * 0.9)
        if cv.solid(x, y):
            cv.set(x, y, 's1')
            if cv.solid(x + 1, y + 1):
                cv.set(x + 1, y + 1, 's1')
    if shape == 2:                                                    # Moos oben
        for x in range(int(cx - rx), int(cx + rx)):
            y = int(cy - ry * 0.75)
            if cv.solid(x, y) and hsh(x, 1, seed, 8) > 0.45:
                cv.set(x, y, 'g3')
                if hsh(x, 2, seed, 8) > 0.5:
                    cv.set(x, y + 1, 'g2')


def make_findling(k):
    cv = Cv(32, 32)
    r = [(10, 7.5), (12, 8.5), (8.5, 6.5)][k]
    stone(cv, 16, 17, r[0], r[1], 31 + k, shape=k)
    cv.outline('s0')
    ring_shadow(cv, 16, 17, r[0], r[1])
    return cv.img()


def make_furtstein(k):
    cv = Cv(32, 32)
    cx, cy, rx, ry = 16, 15, [11, 10, 12, 9][k], [7, 7, 7.5, 6][k]
    # Seitenwand (flach, 3 px) dann Deckflaeche
    cv.ell(cx, cy + 3, rx, ry, lambda dx, dy, x, y: 's1' if hsh(x, y, k, 11) > 0.2 else 's0')
    cv.ell(cx, cy, rx, ry, lambda dx, dy, x, y: ('s4' if (-0.5 * dx - 0.8 * dy) > 0.35 else ('s3' if hsh(x, y, k, 13) > 0.12 else 's4')) if (-0.5 * dx - 0.8 * dy) > -0.2 else ('s2' if hsh(x, y, k, 13) > 0.15 else 's3'))
    for j in range(3):
        x, y = int(cx - rx * .5 + hsh(j, k, 15, 1) * rx), int(cy - ry * .3 + hsh(j, k, 16, 1) * ry * .6)
        if cv.solid(x, y):
            cv.set(x, y, 's1')
    cv.outline('s0')
    ring_shadow(cv, cx, cy + 2, rx, ry)
    return cv.img()


# ================================================================ Schaum-Animationen
FLOW = {'S': (0, 1), 'N': (0, -1), 'O': (1, 0), 'W': (-1, 0)}


def foam_frames(base_img, cx, cy, rx, ry, flow):
    """Stein/Pfeiler mit Schaum: oberstroemig ein Kranz, unterstroemig ziehen Wellenstriche ab (8-Frame-Schleife)."""
    fx, fy = FLOW[flow]
    frames = []
    for t in range(N):
        cv = Cv(32, 32)
        cv.a[:] = np.array(base_img)
        for y in range(32):
            for x in range(32):
                if cv.solid(x, y):
                    continue
                dx, dy = (x + 0.5 - cx), (y + 0.5 - cy)
                ex = math.hypot(dx / (rx + 0.8), dy / (ry + 0.8))
                if 1.0 < ex < 1.0 + 1.5 / min(rx, ry) + 0.12 * (1 if True else 0):
                    up = -(dx * fx + dy * fy) / max(1e-6, math.hypot(dx, dy))     # >0 = oberstroemig
                    if up > -0.15 and hsh(x, y, (t // 2) + 3, 71) > 0.3:
                        cv.set(x, y, 'b5' if hsh(x, y, t, 72) > 0.6 else 'b4')
        # Kielwasser: Striche hinter dem Stein, laufen mit 4 px/Frame weg (32 px Periode wird nicht gebraucht, sie verblassen)
        for k in range(3):
            lat = (k - 1) * 4 + 0.5
            for s in range(6):
                dist = (ry if fy else rx) + 3 + ((t * 2 + k * 3 + s * 5) % 16)
                px_ = cx + (fx * dist if fx else lat)
                py_ = cy + (fy * dist if fy else lat)
                if hsh(k, s, 5, 73) > 0.35 and not cv.solid(int(px_), int(py_)) and dist < 15:
                    cv.set(px_, py_, 'b4' if dist < 11 else 'b3')
        frames.append(cv.img())
    return frames


# ================================================================ Pflanzen
def lily(k):
    frames = []
    pad = {0: (9, 6.5, 'g3', False), 1: (8, 6, 'g2', True), 2: (10, 7, 'g3', True)}[k]
    notch = [0.5, 3.0, 5.2][k]
    for t in range(N):
        cv = Cv(32, 32)
        bob = int(round(0.7 * math.sin(2 * math.pi * t / N + k)))
        rx, ry, base, flower = pad
        cx, cy = 16, 17 + bob

        def fn(dx, dy, x, y):
            a = math.atan2(dy, dx)
            if abs(((a - notch + math.pi) % (2 * math.pi)) - math.pi) < 0.22 and math.hypot(dx, dy) > 0.18:
                return None                                                # Einschnitt
            lit = -0.5 * dx - 0.8 * dy
            if lit > 0.45:
                return 'g4'
            if lit < -0.55:
                return 'g1' if base == 'g3' else 'g0'
            return base
        cv.ell(cx, cy, rx, ry, fn)
        for j in range(5):                                                  # Adern
            a = notch + 0.6 + j * 1.15
            for r in range(2, int(rx * 0.9)):
                x, y = cx + r * math.cos(a), cy + r * math.sin(a) * ry / rx
                if cv.solid(int(x), int(y)):
                    cv.set(x, y, 'g2' if base == 'g3' else 'g1')
        if flower:
            fx, fy = cx - 2, cy - 2
            for a_ in range(6):
                ax = fx + 3 * math.cos(a_ * math.pi / 3)
                ay = fy + 2.2 * math.sin(a_ * math.pi / 3)
                cv.rect(int(ax), int(ay), int(ax) + 1, int(ay) + 1, 'pk' if a_ % 2 else 'cream')
            cv.rect(fx - 1, fy - 1, fx, fy, 'yel')
        cv.outline('g0')
        # Wasserring pulsiert um das Blatt
        ph = (t + k * 2) % N
        if ph < 5:
            def ring(x, y, ph=ph):
                dx, dy = (x + 0.5 - cx) / (rx + 2 + ph * 0.7), (y + 0.5 - cy) / (ry + 2 + ph * 0.5)
                d = dx * dx + dy * dy
                return ('b4' if ph < 3 else 'b3') if 0.82 <= d <= 1.0 and hsh(x, y, ph, 81) > 0.35 else None
            cv.under(ring)
        ring_shadow(cv, cx, cy, rx, ry, 'b1')
        frames.append(cv.img())
    return frames


def reed(k, cattail=False):
    """Schilf: Halme biegen sich im Wind (Spitzenversatz ~ Hoehe^2), 8-Frame-Schleife."""
    frames = []
    rng = [(7, 36, -2, 0), (10, 42, 1, 1.4), (13, 33, -1, 2.1), (17, 44, 2, 0.8), (20, 38, 0, 2.9), (24, 34, 2, 1.7), (15, 28, -3, 3.6)]
    use = [rng[:5], rng[2:], [rng[i] for i in (0, 3, 4, 5, 6)]][k] if not cattail else [rng[1], rng[3], rng[4], rng[5]]
    for t in range(N):
        cv = Cv(32, 48)
        ph = 2 * math.pi * t / N
        for idx, (xb, h, lean, p0) in enumerate(use):
            amp = 1.6 + 0.3 * (idx % 3)
            tipx = lean + amp * math.sin(ph + p0)
            ytop = 45 - h
            for y in range(45, ytop - 1, -1):
                f = (45 - y) / float(h)
                x = xb + lean * f + (tipx - lean) * f * f
                col = 'g3' if (idx + y // 6) % 3 else 'g4'
                if f > 0.9 and not cattail:
                    col = 'g5'
                cv.set(round(x), y, col)
                if f < 0.55:
                    cv.set(round(x) + 1, y, 'g2')
            if cattail and idx % 2 == 0:                                   # Kolben
                f0 = 0.74
                for y in range(ytop + 2, ytop + 9):
                    f = (45 - y) / float(h)
                    x = xb + lean * f + (tipx - lean) * f * f
                    cv.set(round(x), y, 'br2')
                    cv.set(round(x) + 1, y, 'br1')
                    cv.set(round(x) - 1, y, 'br2')
                cv.set(round(xb + lean + (tipx - lean)), ytop - 1, 'br3')
                cv.set(round(xb + lean + (tipx - lean)), ytop, 'br3')
            else:                                                          # Blattspitzen seitlich
                for side in (-1, 1):
                    yb = 45 - int(h * (0.42 + 0.1 * (idx % 3)))
                    f = (45 - yb) / float(h)
                    x0 = xb + lean * f + (tipx - lean) * f * f
                    for j in range(1, 6):
                        cv.set(round(x0) + side * j, yb - j // 2 - (1 if side * (1 if t % 2 else -1) > 0 and j > 3 else 0), 'g3' if j < 4 else 'g4')
        cv.outline('g0')
        # Wurzelschatten und Wasserring
        for x in range(4, 29):
            for y in range(44, 48):
                if not cv.solid(x, y):
                    dx, dy = (x - 16) / 13.0, (y - 46) / 2.4
                    if dx * dx + dy * dy <= 1:
                        cv.set(x, y, 'b1' if hsh(x, y, 5, 91) > 0.15 else 'b0')
        frames.append(cv.img())
    return frames


# ================================================================ Strudel / Treibholz
def whirl():
    frames = []
    for t in range(N):
        cv = Cv(32, 32)
        for y in range(32):
            for x in range(32):
                dx, dy = x + 0.5 - 16, y + 0.5 - 16
                r = math.hypot(dx, dy)
                if r > 15.2:
                    continue
                a = math.atan2(dy, dx)
                s = (a / (2 * math.pi) * 3 + r / 5.5 - t / float(N)) % 1.0
                if r < 2.6:
                    c = 'b0'
                elif s < 0.16:
                    c = 'b5'
                elif s < 0.36:
                    c = 'b4'
                elif s < 0.62:
                    c = 'b2'
                else:
                    c = 'b1'
                if r > 12.5 and hsh(x, y, 7, 95) < (r - 12.5) / 2.7:
                    continue
                if r > 12.5 and c in ('b1', 'b2'):                         # Rand nur Lichtarme, innen dunkel -> Silhouette fuer Wasser
                    continue
                cv.set(x, y, c)
        frames.append(cv.img())
    return frames


def driftwood():
    frames = []
    for t in range(N):
        cv = Cv(64, 32)
        bob = int(round(1.0 * math.sin(2 * math.pi * t / N)))
        tilt = 0.5 * math.sin(2 * math.pi * t / N + 1.0)
        for x in range(6, 58):
            yc = 17 + bob + tilt * (x - 32) / 26.0
            ht = 4.6 - (1.4 if x < 10 or x > 54 else 0) + 0.5 * math.sin(x * 0.4)
            for y in range(int(yc - ht - 1), int(yc + ht + 2)):
                d = (y + 0.5 - yc) / ht
                if abs(d) > 1:
                    continue
                n = hsh(x, y, 3, 97)
                if d < -0.55:
                    c = 'br4' if n > 0.3 else 'br3'
                elif d < 0.2:
                    c = 'br3' if n > 0.2 else 'br2'
                elif d < 0.7:
                    c = 'br2' if n > 0.15 else 'br1'
                else:
                    c = 'br1'
                if x % 9 == 4 and abs(d) < 0.8 and hsh(x, y, 4, 97) > 0.4:
                    c = 'br1'
                cv.set(x, y, c)
        for x, up in ((22, 6), (39, 5)):                                    # Aststuempfe
            yc = 17 + bob + tilt * (x - 32) / 26.0
            for j in range(up):
                cv.set(x, yc - 5 - j, 'br2')
                cv.set(x + 1, yc - 5 - j, 'br1')
            cv.set(x, yc - 5 - up, 'br4')
        e = int(17 + bob + tilt * (-26) / 26.0)                             # Hirnholz links
        cv.ell(7, e, 2.2, 4, lambda dx, dy, x, y: 'br5' if dx * dx + dy * dy > 0.25 else 'br4')
        cv.outline('br0')
        ring_shadow(cv, 32, 17 + bob, 25, 4.5)
        # Wellen um den Stamm
        for x in range(4, 61):
            yb = 23 + bob + int(round(1.0 * math.sin(2 * math.pi * (t / N) + x * 0.5)))
            if not cv.solid(x, yb) and hsh(x, 1, 2, 98) > 0.45:
                cv.set(x, yb, 'b4' if (x + t) % 4 else 'b5')
        frames.append(cv.img())
    return frames


def pfahl(static):
    frames = []
    for t in range(1 if static else N):
        cv = Cv(32, 32)
        cx, cy = 16, 16
        for y in range(9, 22):
            for x in range(cx - 4, cx + 5):
                d = (x + 0.5 - cx) / 4.0
                if y <= 12 and not (d * d + ((y + 0.5 - 12) / 3.0) ** 2) <= 1.0 and y < 12:
                    pass
                n = hsh(x, y, 4, 99)
                cv.set(x, y, 'br4' if d < -0.4 else ('br3' if d < 0.2 else ('br2' if d < 0.65 else 'br1')) if n > 0.18 else 'br2')
        cv.ell(cx, 9, 4.2, 2.6, lambda dx, dy, x, y: 'br5' if dx * dx + dy * dy < 0.5 else 'br4')
        cv.outline('br0')
        ring_shadow(cv, cx, 16, 4.5, 6)
        if not static:
            ph = t / float(N)
            for k in range(2):
                p = (ph + k * 0.5) % 1.0
                rr = 7 + p * 8

                def ring(x, y, rr=rr, p=p):
                    d = math.hypot((x + 0.5 - cx), (y + 0.5 - 21) * 1.5)
                    return ('b5' if p < 0.3 else ('b4' if p < 0.6 else 'b3')) if abs(d - rr) < 0.7 and hsh(x, y, int(p * 8), 100) > p * 0.9 else None
                cv.under(ring)
        frames.append(cv.img())
    return frames


# ================================================================ Wasserfall
def waterfall(part, side):
    """part Kante|Mitte|Fuss, side L|M|R. Vollflaechige 32x32-Kachel, 8 Frames; Streifen laufen 4 px/Frame nach unten (32 px = Schleife)."""
    streak = W.noise_field(13, 3, 0, N, 201 + {'Kante': 0, 'Mitte': 1, 'Fuss': 2}[part], sy=4)
    streak2 = W.noise_field(7, 2, 0, N, 211, sy=4)
    foam = W.noise_field(8, 8, 4, N, 221)
    frames = []
    for t in range(N):
        cv = Cv(32, 32)
        for y in range(32):
            for x in range(32):
                s, s2, fo = streak[t, y, x], streak2[t, y, x], foam[t, y, x]
                if part == 'Mitte':
                    c = 'b3'
                    if s > 0.62:
                        c = 'b5' if s > 0.8 else 'b4'
                    elif s < 0.3 or s2 < 0.18:
                        c = 'b2'
                    if s2 > 0.9:
                        c = 'b5'
                elif part == 'Kante':
                    f = y / 31.0                                           # oben ruhig, zur Kante hin schneller/heller
                    c = 'b2' if f < 0.4 else ('b3' if f < 0.75 else 'b4')
                    if s > 0.66 and f > 0.2:
                        c = 'b4' if f < 0.75 else 'b5'
                    elif s < 0.2:
                        c = 'b2' if f < 0.8 else 'b3'
                    if y >= 29:                                              # Kante: Gischt
                        c = 'b5' if hsh(x, y, t // 2, 5) > 0.35 else 'b4'
                else:                                                      # Fuss: Gischtbecken
                    d = y / 31.0
                    c = 'b4' if s > 0.55 else 'b3'
                    if fo > 0.58 - 0.25 * d:
                        c = 'b5' if fo > 0.76 - 0.25 * d else 'b4'
                    if d > 0.65:
                        c = 'b3' if fo < 0.62 else ('b4' if fo < 0.78 else 'b5')
                        if d > 0.85 and fo < 0.4:
                            c = 'b2'
                    if y < 5 and s < 0.5:
                        c = 'b3'
                cv.set(x, y, c)
        for y in range(32):                                                  # Felswaende
            for x in list(range(0, 5)) if side == 'L' else (list(range(27, 32)) if side == 'R' else []):
                e = (4 - x) if side == 'L' else (x - 27)
                n = hsh(x, y, 9, 231 + t * 0)
                c = 's1' if e <= 1 else ('s2' if e <= 3 else 's3')
                if n > 0.82:
                    c = 's0'
                elif n < 0.1:
                    c = 's3'
                if e == 0 and side == 'L':
                    c = 's3' if n > 0.5 else 's2'
                cv.set(x, y, c)
                if e == 4 - 4 and False:
                    pass
        if part == 'Kante':
            for x in range(32):                                              # Steinlippe
                if cv.get(x, 28)[:3] != COL['s1'][:3] and not (side == 'L' and x < 5) and not (side == 'R' and x > 26):
                    pass
        frames.append(cv.img())
    return frames


# ================================================================ Steg / Bruecke (statisch)
def deck(w, h, y0, y1, seed, broken=None, rails=False, plank=8):
    cv = Cv(w, h)
    for x in range(w):
        pi = x // plank
        for y in range(y0, y1 + 1):
            g = (x % plank == 0) or (x % plank == plank - 1 and False)
            n = hsh(x, y, seed + pi, 301)
            c = 'br1' if x % plank == 0 else ('br4' if y == y0 + 1 else ('br3' if n > 0.22 else 'br2'))
            if y == y0 or y == y1:
                c = 'br1'
            cv.set(x, y, c)
        for y in (y0 + 3, y1 - 3):                                           # Naegel
            if x % plank == 2:
                cv.set(x, y, 's2')
    if rails:
        for x in range(w):
            for y in (y0 - 5, y0 - 4):
                cv.set(x, y, 'br4' if y == y0 - 5 else 'br2')
            for y in (y1 + 3, y1 + 4):
                cv.set(x, y, 'br4' if y == y1 + 3 else 'br2')
        for x in (3, w - 4):
            for y in range(y0 - 6, y0 + 1):
                cv.set(x, y, 'br2')
                cv.set(x + 1, y, 'br1')
            for y in range(y1, y1 + 6):
                cv.set(x, y, 'br2')
                cv.set(x + 1, y, 'br1')
    if broken:
        for x in range(w):
            for y in range(h):
                if broken(x, y):
                    cv.a[y, x] = (0, 0, 0, 0)
    return cv


def steg_set():
    out = {}
    d = deck(32, 32, 7, 24, 5)
    d.outline('br0')
    d.under(lambda x, y: 'b1' if 25 <= y <= 28 else None)
    out['Steg_Mitte_H'] = d.img()
    out['Steg_Mitte_V'] = rot90(out['Steg_Mitte_H'])
    e = deck(32, 32, 7, 24, 7, broken=lambda x, y: x < 5)
    for y in range(6, 26):                                                    # Querbalken am Ende
        e.set(5, y, 'br1')
        e.set(6, y, 'br2')
    for y in (7, 23):                                                         # Pfosten
        for x in (6, 7):
            for yy in range(y - 2, y + 3):
                e.set(x, yy, 'br2')
    e.outline('br0')
    e.under(lambda x, y: 'b1' if 25 <= y <= 28 and x > 5 else None)
    out['Steg_Ende_H_L'] = e.img()
    out['Steg_Ende_H_R'] = out['Steg_Ende_H_L'].transpose(Image.FLIP_LEFT_RIGHT)
    out['Steg_Ende_V_O'] = rot90(out['Steg_Ende_H_L'])
    out['Steg_Ende_V_U'] = rot90(out['Steg_Ende_H_R'])
    return out


def bruecke_set():
    out = {}
    m = deck(32, 32, 9, 22, 11, rails=True)
    m.outline('br0')
    m.under(lambda x, y: 'b1' if 28 <= y <= 31 else None)
    out['Bruecke_Holz_Mitte_H'] = m.img()

    def jag(side):
        def f(x, y):
            xx = x if side == 'L' else 31 - x
            edge = 12 + int(5 * math.sin(y * 0.9) + 3 * hsh(y, 1, 3, 303))
            return xx < edge
        return f
    for side in ('L', 'R'):
        b = deck(32, 32, 9, 22, 13, rails=True, broken=jag(side))
        b.outline('br0')
        out['Bruecke_Holz_Bruch_' + side] = b.img()
    # einzelnes Brett haengt schraeg im Wasser
    l = Cv(32, 32)
    for i in range(18):
        x, y = 8 + i, 8 + int(i * 0.7)
        for k in range(4):
            l.set(x, y + k, 'br3' if k in (1, 2) else ('br2' if k == 3 else 'br4'))
    l.outline('br0')
    ring_shadow(l, 16, 17, 10, 6)
    out['Bruecke_Holz_Luecke'] = l.img()
    p = Cv(32, 32)
    p.rect(8, 4, 23, 26, 's2')
    for y in range(4, 27):
        for x in range(8, 24):
            n = hsh(x, y, 2, 305)
            p.set(x, y, 's3' if (x < 12 and n > 0.2) else ('s1' if x > 19 else ('s2' if n > 0.15 else 's3')))
    for y in range(4, 27, 5):
        for x in range(8, 24):
            p.set(x, y, 's1')
    for x in range(8, 24, 8):
        for y in range(4, 27):
            if (y // 5) % 2 == 0:
                p.set(x, y, 's1')
    p.outline('s0')
    for x in range(6, 26):
        if not p.solid(x, 27) and hsh(x, 1, 7, 306) > 0.3:
            p.set(x, 27, 'b4')
    out['Bruecke_Pfeiler'] = p.img()
    return out


# ================================================================ Ausgabe
def main():
    od = W.zone_dir('fluss', 'Objekte')
    ad = W.zone_dir('fluss', 'Animiert')
    errs = []
    names = []

    def save(path, im):
        im.save(path)
        errs.extend(W.check_palette(im, path.rsplit('/', 1)[1]))
        names.append(path.rsplit('/', 1)[1])

    for k in range(3):
        save('%s/Findling_%s.png' % (od, 'ABC'[k]), make_findling(k))
    for k in range(4):
        save('%s/Furtstein_%s.png' % (od, 'ABCD'[k]), make_furtstein(k))
    save('%s/Pfahl.png' % od, pfahl(True)[0])
    for n, im in {**steg_set(), **bruecke_set()}.items():
        save('%s/%s.png' % (od, n), im)
    # Animiert
    for fl in FLOW:
        save('%s/Findling_Schaum_%s.png' % (ad, fl), strip(foam_frames(make_findling(1), 16, 17, 12, 8.5, fl)))
    save('%s/Furtstein_Schaum.png' % ad, strip(foam_frames(make_furtstein(0), 16, 16, 11, 7, 'S')))
    for k in range(3):
        save('%s/Seerose_%s.png' % (ad, 'ABC'[k]), strip(lily(k)))
        save('%s/Schilf_%s.png' % (ad, 'ABC'[k]), strip(reed(k)))
    save('%s/Rohrkolben.png' % ad, strip(reed(0, cattail=True)))
    save('%s/Strudel.png' % ad, strip(whirl()))
    save('%s/Treibholz.png' % ad, strip(driftwood()))
    save('%s/Pfahl_Wellen.png' % ad, strip(pfahl(False)))
    for part in ('Kante', 'Mitte', 'Fuss'):
        for side in 'LMR':
            save('%s/Wasserfall_%s_%s.png' % (ad, part, side), strip(waterfall(part, side)))
    for n in names:
        print('ok', n)
    if errs:
        print('\n'.join(errs))
        sys.exit(1)


if __name__ == '__main__':
    main()
