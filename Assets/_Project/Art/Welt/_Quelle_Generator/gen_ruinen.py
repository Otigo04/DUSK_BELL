"""RUINEN (Art/Welt/06_Ruinen): Steinplatten-Boden, Mauer-Autotile (mit Ziegel-Vorderwand), Saeulen, Torbogen, Statue, Brunnen, Grabsteine, Altar,
Fackel, zerrissene Fahne und die Muehle mit animiertem Wasserrad.

Tileset/  Boden_Ruinen.png           4 nahtlose Plattenboeden (A-D) 128x32
          Mauer.png / Mauer_Verfallen.png   47er-Autotile (Ms=12): Innen = Mauerkrone, Sued-Rand = 12 px hohe Ziegelwand, Aussen = Plattenboden
Objekte/  Saeule_ganz (32x64), Saeule_gebrochen (32x48), Saeulenfuss, Torbogen (96x64), Statue (32x64), Brunnen_Ruine (64x64), Schutt_A-C,
          Ranken (32x32, Overlay), Grabstein_A-C (32x48), Altar (64x48), Muehle_Ruine (96x96, ohne Rad)
Animiert/ Wasserrad (64x64, 8 Frames = 22.5 Grad, Schleife nahtlos), Fackel (16x32), Fahne_zerrissen (32x48) - je 8 Frames
Aufruf: python gen_ruinen.py"""
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


def floor_px(x, y, v):
    """Steinplatten 16x16 (Periode 16 teilt 32), Fugen, Risse, Moos, Unkraut."""
    sx, sy = x % 16, y % 16
    slab = ((x // 16) * 2 + (y // 16) + v) % 4
    h = hsh(x, y, v, 801)
    base = [S2, S2, S3, S2][int(hsh(x // 16, y // 16, v, 802) * 4) % 4] if True else S2
    if sx == 0 or sy == 0:
        return S0 if hsh(x, y, 1, 803) < 0.8 else S1                    # Fuge
    c = base
    if sx == 1 or sy == 1:
        c = S3 if base == S2 else S4                                     # Lichtkante oben/links
    elif sx == 15 or sy == 15:
        c = S1                                                           # Schatten unten/rechts
    # Riss pro Platte
    cx = int(hsh(x // 16, y // 16, v, 804) * 8) + 4
    cy = int(hsh(x // 16, y // 16, v, 805) * 8) + 4
    if hsh(x // 16, y // 16, v, 806) > 0.55 and abs((sx - cx) - (sy - cy) * 0.7) < 0.7 and 2 < sy < 13:
        c = S0
    if h > 0.975:
        c = S1 if base == S2 else S2                                     # Sprenkel
    # Moos in Fugen/Ecken
    if (sx < 4 or sy < 4) and hsh(x // 16, y // 16, v, 807) > 0.5 and hsh(x, y, v, 808) > 0.55:
        c = G2 if hsh(x, y, v, 809) > 0.4 else G3
    return c


def wall_inside(sh, x, y, t, ruined=False):
    """Mauerkrone: Steinplatten-Deckflaeche mit hellem Rand oben/links."""
    h = hsh(x, y, 2, 810)
    d = sh.D[y, x]
    sx, sy = x % 8, y % 8
    c = S4 if hsh(x // 8, y // 8, 3, 811) > 0.4 else S3
    if sx == 0 or sy == 0:
        c = S2                                                           # Fugen
    if h > 0.97:
        c = S2
    if ruined and hsh(x // 6, y // 6, 5, 812) > 0.85:
        c = G2 if hsh(x, y, 6, 812) > 0.3 else G3                         # bewachsen
    P = sh.P
    top = (not sh.ext[y - 1 + P, x + P])
    left = (not sh.ext[y + P, x - 1 + P])
    if d <= 1.5:
        if top or left:
            return S5
        return S2 if hsh(x, y, 5, 813) < 0.7 else S1
    return c


def wall_outside(sh, x, y, ruined=False):
    od = sh.OD[y, x]
    k = sh.face_depth(x, y)
    h = hsh(x, y, 7, 814)
    if k:                                                               # Ziegelwand
        row = y // 4
        off = 4 if row % 2 else 0
        bxi = ((x + off) // 8) % 4
        bx = (x + off) % 8
        if y % 4 == 0 or bx == 0:
            c = S1                                                       # Moertel
        else:
            r = hsh(bxi, row, 3, 815)
            c = S3 if r > 0.6 else (S2 if r > 0.2 else S3)
            if bx == 1 or y % 4 == 1:
                c = S4 if c == S3 else S3                                 # Lichtkante
            if hsh(bxi, row, 4, 815) > 0.93:
                c = S1                                                   # dunkler Stein
        if ruined and hsh(bxi, row, 6, 816) > 0.9 and k > 4:
            c = S0                                                       # herausgebrochen
        if k <= 1:
            return S1
        if k <= 3 and h < 0.6:
            c = S1                                                       # Schatten unter der Krone
        if k >= 8 and ruined and hsh(x // 3, y // 2, 7, 817) > 0.72:
            c = G2 if h > 0.3 else G3                                    # Moos am Fuss
        if k >= 11:
            return S0 if h < 0.75 else S1
        return c
    if od <= 1.0:
        return S0
    if od <= 3.0 and h < 0.9 - 0.2 * od:
        return S1
    return floor_px(x, y, 0)


# ============================================================ Objekte
def column(h_, broken):
    cv = Cv(32, 64 if not broken else 48)
    H_ = cv.h
    top = 8 if not broken else 18
    for y in range(top, H_ - 4):
        half = 6 + (3 if y > H_ - 12 else 0)
        for x in range(16 - half, 16 + half + 1):
            d = (x - 16) / float(half)
            if broken and y < top + 5 and hsh(x, y, 1, 820) < (top + 5 - y) / 6.0 * (0.9 if x > 16 else 0.2):
                continue
            c = 's5' if d < -0.55 else ('s4' if d < -0.1 else ('s3' if d < 0.4 else ('s2' if d < 0.75 else 's1')))
            if (x - 16) % 4 == 0 and abs(d) < 0.9:
                c = 's2' if c in ('s3', 's4', 's5') else 's1'          # Kannelur
            if y % 14 == 0:
                c = 's1'
            cv.set(x, y, c)
    if not broken:
        for y in range(3, 9):                                                # Kapitell
            for x in range(6, 27):
                cv.set(x, y, 's4' if y < 5 else 's3')
        for x in range(6, 27):
            cv.set(x, 8, 's1')
    for y in range(H_ - 6, H_ - 3):                                          # Basis
        for x in range(7, 26):
            cv.set(x, y, 's3' if y == H_ - 6 else 's2')
    for x in range(12, 21):                                                  # Moos
        for y in range(H_ - 12, H_ - 5):
            if cv.solid(x, y) and hsh(x, y, 2, 821) > 0.78:
                cv.set(x, y, 'g2')
    cv.outline('s0')
    ring_shadow(cv, 16, H_ - 4, 12, 3, 's0')
    return cv.img()


def column_base():
    cv = Cv(32, 32)
    cv.ell(16, 18, 11, 7, lambda dx, dy, x, y: 's4' if (-0.5 * dx - 0.8 * dy) > 0.2 else ('s3' if (-0.5 * dx - 0.8 * dy) > -0.4 else 's2'))
    cv.ell(16, 15, 7, 4.5, lambda dx, dy, x, y: 's3' if dx * dx + dy * dy > 0.4 else 's4')
    for j in range(5):
        x, y = 8 + hsh(j, 1, 1, 822) * 16, 14 + hsh(j, 2, 1, 822) * 8
        if cv.solid(int(x), int(y)):
            cv.set(x, y, 's1')
    cv.outline('s0')
    ring_shadow(cv, 16, 18, 11, 7, 's0')
    return cv.img()


def archway():
    cv = Cv(96, 64)
    for px in (6, 70):                                                       # zwei Pfeiler
        for y in range(10, 62):
            for x in range(px, px + 20):
                d = (x - px - 10) / 10.0
                c = 's4' if d < -0.5 else ('s3' if d < 0.1 else ('s2' if d < 0.6 else 's1'))
                if y % 6 == 0 or (x - px) % 10 == 0 and (y // 6) % 2 == 0:
                    c = 's1'
                cv.set(x, y, c)
    for y in range(4, 24):                                                   # Bogen
        for x in range(10, 86):
            dx, dy = (x + 0.5 - 48) / 38.0, (y + 0.5 - 28) / 24.0
            r = math.hypot(dx, dy)
            if 0.64 <= r <= 1.0 and y < 30:
                ang = math.atan2(dy, dx)
                if hsh(int(ang * 12), 1, 1, 830) > 0.9 and ang > -1.8 and ang < -1.0:
                    continue                                                  # herausgebrochene Steine
                c = 's4' if -2.3 < ang < -1.2 else ('s3' if r < 0.84 else 's2')
                if int(ang * 14) % 2 == 0:
                    c = 's2' if c == 's3' else ('s3' if c == 's2' else c)
                cv.set(x, y, c)
    for x in range(44, 53):                                                  # Schlussstein
        for y in range(2, 10):
            cv.set(x, y, 's5' if y < 4 else 's3')
    for x in range(8, 90, 4):                                                # Efeu
        if cv.solid(x, 14) and hsh(x, 1, 2, 831) > 0.6:
            for j in range(3 + int(hsh(x, 2, 2, 831) * 6)):
                cv.set(x + j % 2, 14 + j, 'g2' if j % 2 else 'g3')
    cv.outline('s0')
    ring_shadow(cv, 48, 60, 40, 3, 's0')
    return cv.img()


def statue():
    cv = Cv(32, 64)
    for y in range(54, 62):                                                  # Sockel
        for x in range(5, 27):
            cv.set(x, y, 's3' if y < 56 else ('s2' if x < 20 else 's1'))
    for y in range(24, 54):                                                  # Koerper (Gewand)
        f = (y - 24) / 30.0
        half = 5 + int(5 * f)
        for x in range(16 - half, 16 + half + 1):
            d = (x - 16) / float(half)
            c = 's4' if d < -0.4 else ('s3' if d < 0.2 else ('s2' if d < 0.65 else 's1'))
            if (x + y // 3) % 5 == 0:
                c = 's2' if c in ('s3', 's4') else 's1'
            cv.set(x, y, c)
    cv.ell(16, 17, 5, 6, lambda dx, dy, x, y: 's4' if (-0.5 * dx - 0.8 * dy) > 0 else 's3')       # Kopf
    for (x, y) in ((14, 17), (18, 17)):
        cv.set(x, y, 's1')
    for y in range(28, 44):                                                  # erhobener Arm links, rechts abgebrochen
        cv.set(8 - (y - 28) // 6, y, 's3')
        cv.set(9 - (y - 28) // 6, y, 's2')
    for x in range(10, 22):
        for y in range(36, 52):
            if cv.solid(x, y) and hsh(x, y, 3, 840) > 0.88:
                cv.set(x, y, 'g2')
    cv.outline('s0')
    ring_shadow(cv, 16, 60, 13, 3, 's0')
    return cv.img()


def well():
    cv = Cv(64, 64)
    cx, cy = 32, 36
    cv.ell(cx, cy + 6, 26, 14, lambda dx, dy, x, y: 's1' if (y // 4) % 2 == 0 else 's2')              # Mantel
    cv.ell(cx, cy, 26, 14, lambda dx, dy, x, y: 's4' if (-0.5 * dx - 0.8 * dy) > 0.1 else 's3')       # Rand
    cv.ell(cx, cy, 19, 9.5, lambda dx, dy, x, y: 'ink' if dx * dx + dy * dy < 0.8 else 'purp')        # Schacht (trocken)
    for a in range(0, 24):                                                   # Steinfugen am Rand
        ang = a / 24.0 * 6.283
        x, y = cx + 22.5 * math.cos(ang), cy + 12 * math.sin(ang)
        cv.set(x, y, 's2')
    for j in range(16):
        a = hsh(j, 1, 1, 850) * 6.28
        cv.set(cx + 22 * math.cos(a), cy + 11.5 * math.sin(a), 'g2' if j % 2 else 'g3')
    cv.outline('s0')
    ring_shadow(cv, cx, cy + 6, 26, 14, 's0')
    return cv.img()


def debris(k):
    cv = Cv(32, 32)
    for j in range(7 + 2 * k):
        x, y = 5 + hsh(j, k, 1, 860) * 22, 10 + hsh(j, k, 2, 860) * 14
        w, h = 2 + hsh(j, k, 3, 860) * 5, 1.5 + hsh(j, k, 4, 860) * 3
        cv.ell(x, y, w, h, lambda dx, dy, X, Y: 's4' if (-0.5 * dx - 0.8 * dy) > 0.3 else ('s2' if (-0.5 * dx - 0.8 * dy) > -0.3 else 's1'))
    for j in range(3):
        x, y = 8 + hsh(j, k, 5, 860) * 16, 13 + hsh(j, k, 6, 860) * 10
        if cv.solid(x, y):
            cv.set(x, y, 'g3')
    cv.outline('s0')
    ring_shadow(cv, 16, 18, 13, 7, 's0')
    return cv.img()


def vines():
    cv = Cv(32, 32)
    for k in range(3):
        x0 = 6 + k * 9
        for y in range(0, 28):
            x = x0 + 3 * math.sin(y * 0.35 + k * 1.7)
            cv.set(x, y, 'g2')
            cv.set(x + 1, y, 'g1')
            if y % 5 == 2 + k % 2:
                side = 1 if (y // 5 + k) % 2 else -1
                for j in range(1, 4):
                    cv.set(x + side * j, y + (1 if j > 1 else 0), 'g3' if j < 3 else 'g4')
                cv.set(x + side * 2, y - 1, 'g3')
        if k == 1:
            cv.set(x0 + 3, 26, 'pk')
            cv.set(x0 + 2, 26, 'cream')
    return cv.img()


def gravestone(k):
    cv = Cv(32, 48)
    wd = [10, 9, 11][k]
    hgt = [26, 22, 30][k]
    top = 44 - hgt
    for y in range(top, 44):
        for x in range(16 - wd, 16 + wd + 1):
            dx = (x - 16) / float(wd)
            if k == 0 and y < top + 6 and (dx * dx + ((y - top - 6) / 6.0) ** 2) > 1:
                continue                                                   # Rundbogen
            if k == 1 and y < top + (abs(dx) * 6):
                continue                                                   # Spitze
            c = 's4' if dx < -0.5 else ('s3' if dx < 0.2 else ('s2' if dx < 0.7 else 's1'))
            if hsh(x, y, k, 870) > 0.93:
                c = 's1'
            cv.set(x, y, c)
    if k == 2:                                                               # Kreuz
        for y in range(top + 4, top + 18):
            cv.rect(15, y, 16, y, 's1')
        cv.rect(11, top + 8, 20, top + 9, 's1')
    else:
        for y in range(top + 9, top + 12):
            cv.rect(12, y, 20, y, 's1')
        for y in range(top + 14, top + 16):
            cv.rect(13, y, 19, y, 's1')
    for x in range(6, 27):
        for y in range(top, 44):
            if cv.solid(x, y) and y > 38 and hsh(x, y, 1, 871) > 0.55:
                cv.set(x, y, 'g2' if hsh(x, y, 2, 871) > 0.3 else 'g3')
    cv.outline('s0')
    ring_shadow(cv, 16, 43, wd + 2, 3, 's0')
    return cv.img()


def altar():
    cv = Cv(64, 48)
    for y in range(22, 44):                                                  # Block
        for x in range(8, 56):
            dx = (x - 8) / 48.0
            c = 's4' if y < 25 else ('s3' if dx < 0.7 else 's2')
            if y >= 25 and ((y - 25) // 6 + x // 12) % 2 == 0 and (x % 12 == 0 or (y - 25) % 6 == 0):
                c = 's1'
            cv.set(x, y, c)
    for x in range(14, 50):                                                  # Reliefband
        cv.set(x, 36, 's4')
        cv.set(x, 37, 's1')
    for x in range(4, 60):
        for y in range(18, 22):
            cv.set(x, y, 's5' if y == 18 else 's4')
    for y in range(14, 18):                                                   # Kerzenstummel
        for x in (20, 21, 42, 43):
            cv.set(x, y, 'cream')
    cv.set(20, 12, 'yel')
    cv.set(42, 12, 'yel')
    cv.outline('s0')
    for y in range(44, 47):
        for x in range(8, 56):
            if not cv.solid(x, y) and hsh(x, y, 1, 880) < 0.7:
                cv.set(x, y, 's0')
    return cv.img()


def mill_ruin():
    cv = Cv(96, 96)
    for y in range(40, 92):                                                  # Mauerwerk (Ziegel)
        for x in range(12, 84):
            row = y // 4
            off = 4 if row % 2 else 0
            bx = (x + off) % 8
            if y % 4 == 0 or bx == 0:
                c = 's1'
            else:
                r = hsh(((x + off) // 8) % 12, row, 3, 890)
                c = 's3' if r > 0.5 else 's2'
                if bx == 1 or y % 4 == 1:
                    c = 's4' if c == 's3' else 's3'
            # Verfall oben: zackige Oberkante
            top = 40 + int(8 * (0.5 + 0.5 * math.sin(x * 0.23)) + 6 * hsh(x // 3, 1, 1, 891))
            if y < top:
                continue
            cv.set(x, y, c)
    for (x0, y0, w, h) in ((22, 52, 10, 14), (58, 52, 10, 14)):              # Fensteroeffnungen
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                cv.set(x, y, 'ink' if y > y0 + 1 else 'purp')
        for x in range(x0 - 1, x0 + w + 1):
            cv.set(x, y0 - 1, 's5')
    for y in range(66, 92):                                                  # Tuer
        for x in range(38, 54):
            dx, dy = (x - 46) / 8.0, (y - 74) / 8.0
            if (y > 74 or dx * dx + dy * dy <= 1):
                cv.set(x, y, 'ink' if x not in (38, 53) else 'br0')
    for x in range(12, 84):                                                  # Moos
        for y in range(40, 92):
            if cv.solid(x, y) and hsh(x // 2, y // 2, 4, 892) > 0.93:
                cv.set(x, y, 'g2')
    # Dachreste (Sparren)
    for i, x in enumerate(range(14, 82, 11)):
        for j in range(14):
            cv.set(x + j // 3, 38 - j + (4 if i % 2 else 0), 'br2')
            cv.set(x + 1 + j // 3, 38 - j + (4 if i % 2 else 0), 'br1')
    cv.outline('s0')
    ring_shadow(cv, 48, 90, 38, 4, 's0')
    return cv.img()


# ============================================================ Animiert
def wheel():
    frames = []
    cx, cy = 32, 30
    for t in range(N):
        th = math.radians(t * 22.5 / N)
        cv = Cv(64, 64)
        for Y in range(64):
            for X in range(64):
                dx, dy = X + 0.5 - cx, Y + 0.5 - cy
                r = math.hypot(dx, dy)
                if r > 30:
                    continue
                ph = math.atan2(dy, dx) - th
                lit = (-0.5 * dx - 0.8 * dy) / max(r, 1)
                c = None
                spoke_d = abs(((ph * 4 / math.pi) % 1.0) - 0.5) * 2         # 8 Speichen: 0 in Speichenmitte -> 1 dazwischen? (umgedreht unten)
                spoke_c = abs(((ph * 8 / (2 * math.pi) + 0.5) % 1.0) - 0.5)  # Abstand zur naechsten Speichenmitte (0..0.5), 8 Speichen
                paddle_c = abs(((ph * 16 / (2 * math.pi) + 0.5) % 1.0) - 0.5)   # 16 Schaufeln
                if r < 4.2:
                    c = 's3' if lit > 0 else 's1'
                    if r < 1.6:
                        c = 's0'
                elif 21.5 <= r < 24.5:
                    c = 'br3' if lit > 0.2 else ('br2' if lit > -0.4 else 'br1')
                elif 17.5 <= r < 19.2:
                    c = 'br2' if lit > 0 else 'br1'
                elif r < 21.5 and spoke_c * r < 1.5:
                    c = 'br3' if lit > 0 else 'br2'
                elif 24.5 <= r < 30 and paddle_c * r < 2.6:
                    c = 'br4' if (lit > 0 and r < 27) else ('br3' if r < 29 else 'br2')
                    if r >= 29.2:
                        c = 'br1'
                if c:
                    cv.set(X, Y, c)
        cv.outline('br0')
        # Spritzer unten: Tropfen springen vom Wasser
        for k in range(5):
            ph_ = ((t + k * 2) % N) / float(N)
            x = 22 + k * 5 + 2 * math.sin(k + t)
            y = 58 - 12 * math.sin(math.pi * ph_) - 0
            if 0.05 < ph_ < 0.95:
                cv.set(x, y, 'b5' if ph_ < 0.6 else 'b4')
        for x in range(8, 57):                                                # Gischt am Wasserspiegel
            if hsh(x, t, 1, 895) > 0.55 and abs(x - 32) < 24:
                cv.set(x, 59 + (x + t) % 2, 'b4' if hsh(x, t, 2, 895) > 0.4 else 'b5')
        frames.append(cv.img())
    return frames


def torch():
    frames = []
    for t in range(N):
        cv = Cv(16, 32)
        for y in range(16, 30):                                              # Halter/Stab
            cv.set(7, y, 'br2')
            cv.set(8, y, 'br1')
        for x in range(5, 11):
            cv.set(x, 16, 'br3' if x < 8 else 'br1')
            cv.set(x, 15, 'br2')
        # Flamme
        ph = 2 * math.pi * t / N
        for y in range(2, 16):
            f = (15 - y) / 13.0
            hw = 3.2 * (1 - f ** 1.4) + 0.4
            cxf = 7.5 + 1.3 * math.sin(ph + f * 3.0) * f
            for x in range(int(cxf - hw - 1), int(cxf + hw + 2)):
                d = abs(x + 0.5 - cxf) / max(hw, 0.4)
                if d <= 1:
                    c = 'yel' if (d < 0.45 and f < 0.55) else ('or2' if d < 0.75 and f < 0.8 else ('or1' if f < 0.9 else 'red'))
                    cv.set(x, y, c)
        for k in range(2):                                                    # Funken
            yy = 10 - ((t * 2 + k * 5) % 10)
            if 0 <= yy < 12 and hsh(k, t, 1, 896) > 0.3:
                cv.set(7 + 2 * math.sin(k * 3 + t), yy, 'yel')
        frames.append(cv.img())
    return frames


def flag():
    frames = []
    for t in range(N):
        cv = Cv(32, 48)
        for y in range(4, 46):                                                # Fahnenstange (schief, abgebrochen oben)
            cv.set(6, y, 'br2')
            cv.set(7, y, 'br1')
        cv.set(6, 3, 'br4')
        for x in range(8, 28):                                                # Tuch, zerfetzt, wellt
            f = (x - 8) / 19.0
            wave = 2.5 * math.sin(2 * math.pi * (t / N) - f * 5.0) * f
            hh = 14 - int(5 * f) + int(2 * math.sin(f * 17 + 1))
            for y in range(6, 6 + hh):
                yy = y + wave
                if x > 22 and (y - 6) % 5 > 2 and hsh(x, y, 1, 897) > 0.3:
                    continue                                                    # ausgefranst
                c = 'wine' if (y - 6) % 7 < 4 else 'red'
                if f < 0.1:
                    c = 'wine'
                cv.set(x, yy, c)
            if f > 0.05:
                cv.set(x, 6 + wave, 'pk' if hsh(x, 1, 2, 897) > 0.6 else 'red')
        frames.append(cv.img())
    return frames


def main():
    td = W.zone_dir('ruinen', 'Tileset')
    od = W.zone_dir('ruinen', 'Objekte')
    ad = W.zone_dir('ruinen', 'Animiert')
    errs = []

    def chk(im, name):
        errs.extend(W.check_palette(im, name))
    fl = TL.floor_set(td + '/Boden_Ruinen.png', floor_px, 4)
    chk(fl, 'Boden_Ruinen')
    mw = TL.build_blob(td + '/Mauer.png', lambda sh, x, y, t: wall_inside(sh, x, y, t, False), lambda sh, x, y: wall_outside(sh, x, y, False), M=6, Ms=12, R=3, amp=0.6)
    chk(mw, 'Mauer')
    mv = TL.build_blob(td + '/Mauer_Verfallen.png', lambda sh, x, y, t: wall_inside(sh, x, y, t, True), lambda sh, x, y: wall_outside(sh, x, y, True), M=6, Ms=12, R=3, amp=1.8)
    chk(mv, 'Mauer_Verfallen')
    TL.layout_json(td + '/_Layout_Ruinen.json', 'Ruinen', 1, {
        'ms': 12, 'hinweis': 'Wie Felsland/Plateau: Mauer-Zellen setzen, die 12 px hohe Ziegelwand erscheint unter der Mauerkrone (ragt in die Zelle darunter).',
        'sheets': {'Mauer.png': 'Mauerkrone + Ziegelwand', 'Mauer_Verfallen.png': 'zerfallen, bemoost, herausgebrochene Ziegel', 'Boden_Ruinen.png': '4 nahtlose Plattenboeden'}})
    mp = ["....................", "..~~~~~~~~~~~.......", "..~.........~.......", "..~.........~.......", "..~~~~..~~~~~.......", "....................", "...~~~~~~~~~~~~~~...", "....................", "...................."]
    TL.preview_blob(mw, 'Ruinen_Mauer', TL.split_floor(fl), mp)
    TL.preview_blob(mv, 'Ruinen_MauerVerfallen', TL.split_floor(fl), mp)
    objs = {'Saeule_ganz': column(0, False), 'Saeule_gebrochen': column(0, True), 'Saeulenfuss': column_base(), 'Torbogen': archway(), 'Statue': statue(),
            'Brunnen_Ruine': well(), 'Schutt_A': debris(0), 'Schutt_B': debris(1), 'Schutt_C': debris(2), 'Ranken': vines(), 'Grabstein_A': gravestone(0),
            'Grabstein_B': gravestone(1), 'Grabstein_C': gravestone(2), 'Altar': altar(), 'Muehle_Ruine': mill_ruin()}
    for n, im in objs.items():
        im.save('%s/%s.png' % (od, n))
        chk(im, n)
    for n, fr in (('Wasserrad', wheel()), ('Fackel', torch()), ('Fahne_zerrissen', flag())):
        im = strip(fr)
        im.save('%s/%s.png' % (ad, n))
        chk(im, n)
        errs += W.check_loop(fr, n)
    print('Naht Mauer (Mittel, 95%%, Formfehler): %.2f %.2f %d' % TL.seam_ok(mw, M=6, Ms=12, R=3, amp=0.6))
    print('Naht Mauer_Verfallen: %.2f %.2f %d' % TL.seam_ok(mv, M=6, Ms=12, R=3, amp=1.8))
    if errs:
        print('\n'.join(errs))
        sys.exit(1)
    print('ok Ruinen')


if __name__ == '__main__':
    main()
