"""SUMPF (Art/Welt/04_Sumpf): Moorboden, Moorwasser (animiert, 47er-Autotile), Bohlenweg (16er-Wegtile), Objekte, Frosch, Irrlicht.

Tileset/  Boden_Sumpf.png            4 nahtlose Bodenvarianten (Schlamm, Moos, Pfuetzen) 128x32
          Moorwasser.png             47er-Autotile, 8 Frames (Zeilen), Innen = truebes Wasser mit Algen/Entengruetze, Aussen = Schlammufer -> Boden
          Bohlenweg.png              16 Wegstuecke (Maske N1 O2 S4 W8 = Spalte), transparent, liegt ueber Boden/Wasser
Objekte/  Mangrove (64x80), Totholz (32x48), Entengruetze_A-C, Moorfund_Schaedel, Moorfund_Rippen
Animiert/ Frosch_Sitzen (8f), Frosch_Huepfen_S/W/N/E (8f), Irrlicht (32x48, 8f), Blasen (32x32, 8f)
Aufruf: python gen_sumpf.py"""
import math
import sys

import numpy as np
from PIL import Image

import welt_lib as W
import welt_tiles as TL
from welt_draw import Cv, COL, strip, static_noise, ring_shadow, rot90
from welt_lib import H, hsh

N = 8
G0, G1, G2, G3, G4, G5 = (H(h) for h in ('243b3f', '2f5444', '3f7347', '58903f', '7bac45', 'a4c654'))
BR0, BR1, BR2, BR3, BR4 = (H(h) for h in ('3a2530', '5a3a3f', '7d5646', 'a37a56', 'c9a26a'))
B0, B1 = H('23336b'), H('2f4f8f')
S3, S4 = H('9e9bb2'), H('c4c1d2')
_fn = {}


def floor_px(x, y, v):
    if v not in _fn:
        _fn[v] = (static_noise(6, 6, 600 + v), static_noise(12, 12, 640 + v))
    n1, n2 = _fn[v]
    a, b = n1[y, x], n2[y, x]
    h = hsh(x, y, v, 601)
    c = G1
    if a < 0.3:
        c = BR1 if b < 0.6 else BR0                                   # Schlamm
    elif a < 0.42 and b < 0.4:
        c = BR1
    elif a > 0.72:
        c = G2
    if a > 0.58 and b > 0.84:
        c = G3
    if 0.3 <= a < 0.34 and b > 0.5:
        c = G0                                                        # dunkle Pfuetze am Rand
    if h > 0.965:
        c = G3 if c in (G1, G2) else BR2
    elif h < 0.012:
        c = G0
    elif h > 0.9945:
        c = G4
    return c


_water_f = {}


def water_fields():
    if not _water_f:
        _water_f['slow'] = W.noise_field(6, 6, 4, N, 610)
        _water_f['alg'] = W.noise_field(9, 4, 0, N, 611, sx=0, sy=0)
        _water_f['weed'] = W.noise_field(18, 18, 0, N, 612, sx=4)
        _water_f['sp'] = W.noise_field(20, 20, 4, N, 613)
    return _water_f


def moor_inside(sh, x, y, t):
    f = water_fields()
    d = sh.D[y, x]
    s, al, wd, sp = f['slow'][t, y, x], f['alg'][t, y, x], f['weed'][t, y, x], f['sp'][t, y, x]
    c = G0
    if s > 0.62:
        c = G1
    if s < 0.18:
        c = B0                                                          # tiefe, blaustichige Stelle
    if al > 0.74 and s > 0.35:
        c = G1 if al < 0.86 else G2                                   # Algenschlieren
    if wd > 0.78:
        c = G3 if wd > 0.9 else G2                                      # Entengruetze
    if wd > 0.945:
        c = G4
    if sp > 0.985:
        c = G5 if sp > 0.993 else G3                                    # faulige Glitzer
    if d <= 1.5:                                                      # Uferkante: dunkel, mit Moosraender
        return G1 if hsh(x, y, t // 2, 614) > 0.55 else G0
    if d <= 2.4 and hsh(x, y, 4, 615) < 0.35:
        return G1
    return c


_bg = None


def moor_outside(sh, x, y):
    od = sh.OD[y, x]
    h = hsh(x, y, 8, 616)
    if od <= 1.0:
        return BR0 if h < 0.7 else BR1
    if od <= 2.2:
        return BR1 if h < 0.5 else BR2
    if od <= 3.6 and h < 0.7 - 0.12 * od:
        return G2 if h < 0.3 else G3
    return floor_px(x, y, 0)


def board_tile(mask):
    cv = Cv(32, 32)
    n, e, s, w = bool(mask & 1), bool(mask & 2), bool(mask & 4), bool(mask & 8)
    path = np.zeros((32, 32), bool)
    path[8:24, 8:24] = True
    if n:
        path[0:8, 8:24] = True
    if s:
        path[24:32, 8:24] = True
    if e:
        path[8:24, 24:32] = True
    if w:
        path[8:24, 0:8] = True
    horiz = (e or w) and not (n or s)                                             # Planken stehen quer zur Laufrichtung
    for y in range(32):
        for x in range(32):
            if not path[y, x]:
                continue
            in_arm_h = (y in range(8, 24)) and (x < 8 or x >= 24)
            in_arm_v = (x in range(8, 24)) and (y < 8 or y >= 24)
            vertical_planks = horiz if not (in_arm_h or in_arm_v) else in_arm_h
            if (in_arm_h and not in_arm_v) and True:
                vertical_planks = True
            elif in_arm_v and not in_arm_h:
                vertical_planks = False
            k = x if vertical_planks else y
            pi = k // 8
            gap = (k % 8 == 0)
            nz = hsh(x, y, pi + (0 if vertical_planks else 50), 620)
            c = 'br1' if gap else ('br3' if nz > 0.25 else 'br2')
            if not gap and (k % 8 == 1):
                c = 'br4' if nz > 0.3 else 'br3'                               # Lichtkante
            if not gap and (k % 8 == 7):
                c = 'br2'
            cv.set(x, y, c)
    # Naegel
    for y in range(32):
        for x in range(32):
            if path[y, x] and ((x % 8 == 3 and y % 16 == 11) if True else False) and cv.get(x, y)[:3] != COL['br1'][:3]:
                cv.set(x, y, 's2')
    # Randbalken und Schatten (nur wo nicht Weg)
    edge = []
    for y in range(32):
        for x in range(32):
            if path[y, x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 32 and 0 <= yy < 32 and not path[yy, xx]:
                        edge.append((x, y, dx, dy))
                        break
    for x, y, dx, dy in edge:
        cv.set(x, y, 'br1' if (dy == 1 or dx == 1) else 'br2')
    for y in range(32):
        for x in range(32):
            if not path[y, x]:
                below = any(0 <= y - k < 32 and path[y - k, x] for k in (1, 2, 3))
                right = any(0 <= x - k < 32 and path[y, x - k] for k in (1, 2))
                if (below or right) and hsh(x, y, 5, 621) < 0.75:
                    cv.set(x, y, 'g0')
    if not (n or e or s or w):                                                    # alleinstehende Plattform: Pfosten an den Ecken
        for (px, py) in ((8, 8), (22, 8), (8, 22), (22, 22)):
            cv.rect(px, py, px + 1, py + 1, 'br0')
    else:                                                                          # Pfosten an den freien Ecken
        for (cx_, cy_, ok) in ((8, 8, not (n or w)), (22, 8, not (n or e)), (8, 22, not (s or w)), (22, 22, not (s or e))):
            if ok:
                cv.rect(cx_, cy_, cx_ + 1, cy_ + 1, 'br0')
                cv.set(cx_, cy_, 'br2')
    return cv.img()


def board_sheet():
    im = Image.new('RGBA', (16 * 32, 32), (0, 0, 0, 0))
    for m in range(16):
        im.paste(board_tile(m), (m * 32, 0))
    return im


# ============================================================ Objekte
def mangrove():
    cv = Cv(64, 80)
    for y in range(66, 79):                                                      # Wasserschatten
        for x in range(4, 60):
            dx, dy = (x - 32) / 28.0, (y - 72) / 6.5
            if dx * dx + dy * dy <= 1 and hsh(x, y, 1, 640) < 0.75:
                cv.set(x, y, 'g0')
    # Stelzwurzeln
    def root(x0, y0, x1, y1, w):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            f = i / float(n)
            x = x0 + (x1 - x0) * f
            y = y0 + (y1 - y0) * f - 6 * math.sin(math.pi * f) * (1 if x1 != x0 else 0)
            ww = max(1, int(round(w * (1 - 0.5 * f))))
            for k in range(ww):
                cv.set(round(x) + k, round(y), 'br2' if k == 0 else 'br1')
    for (x1, w) in ((6, 3), (14, 3), (22, 2), (42, 2), (50, 3), (58, 3)):
        root(32, 46, x1, 76, w)
    for y in range(26, 56):                                                      # Stamm
        half = 5 - (y < 34) + (y > 48)
        for x in range(32 - half, 32 + half + 1):
            d = (x - 32) / float(half)
            nz = hsh(x, y, 3, 641)
            cv.set(x, y, ('br3' if d < -0.4 else ('br2' if d < 0.3 else 'br1')) if nz > 0.15 else 'br0')
    # Krone
    for k, (cx, cy, rx, ry) in enumerate([(32, 18, 28, 14), (16, 24, 14, 10), (48, 24, 14, 10), (32, 28, 22, 8)]):
        def fn(dx, dy, x, y, k=k):
            lit = -0.5 * dx - 0.8 * dy
            n_ = hsh(x, y, k, 642)
            c = 'g3' if lit > 0.4 else ('g2' if lit > -0.1 else ('g1' if lit > -0.5 else 'g0'))
            return 'g4' if (c == 'g3' and n_ > 0.8) else (c if n_ > 0.07 else 'g0')
        cv.ell(cx, cy, rx, ry, fn)
    for x in range(8, 58, 5):                                                    # haengendes Moos
        L = 4 + int(hsh(x, 1, 2, 643) * 8)
        for j in range(L):
            if hsh(x, j, 3, 643) > 0.12:
                cv.set(x + (j // 3) % 2, 28 + j, 'g3' if j % 3 else 'g2')
    cv.outline('g0')
    return cv.img()


def deadwood():
    cv = Cv(32, 48)
    for y in range(8, 44):
        half = 3 - (y < 14) + (y > 38)
        for x in range(16 - half, 16 + half + 1):
            d = (x - 16) / float(half)
            nz = hsh(x, y, 2, 650)
            cv.set(x, y, ('br3' if d < -0.3 else ('br2' if d < 0.4 else 'br1')) if nz > 0.12 else 'br0')
    for (x0, y0, x1, y1) in ((14, 14, 5, 6), (18, 20, 27, 13), (15, 26, 8, 22)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            cv.set(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, 'br2')
            cv.set(x0 + (x1 - x0) * i / n + 1, y0 + (y1 - y0) * i / n, 'br1')
    for x in range(11, 22):                                                      # Moos/Algen am Wasser
        for y in range(36, 42):
            if cv.solid(x, y) and hsh(x, y, 5, 651) > 0.55:
                cv.set(x, y, 'g2' if hsh(x, y, 6, 651) > 0.4 else 'g1')
    cv.outline('br0')
    ring_shadow(cv, 16, 43, 9, 3, 'g0')
    return cv.img()


def duckweed(k):
    cv = Cv(32, 32)
    for j in range(40 + 14 * k):
        a = hsh(j, k, 1, 660) * 6.28
        r = (hsh(j, k, 2, 660) ** 0.6) * (9 + 3 * k)
        x, y = 16 + r * math.cos(a), 16 + r * 0.75 * math.sin(a)
        cv.set(x, y, 'g3' if hsh(j, k, 3, 660) > 0.35 else 'g2')
        if hsh(j, k, 4, 660) > 0.7:
            cv.set(x + 1, y, 'g4')
    return cv.img()


def skull():
    cv = Cv(32, 32)
    cv.ell(16, 17, 8, 7, lambda dx, dy, x, y: 's5' if (-0.5 * dx - 0.8 * dy) > 0.1 else ('s4' if (-0.5 * dx - 0.8 * dy) > -0.5 else 's3'))
    for (x, y) in ((12, 17), (13, 17), (12, 18), (13, 18), (19, 17), (20, 17), (19, 18), (20, 18)):
        cv.set(x, y, 'ink')
    cv.rect(16, 20, 16, 21, 'ink')
    for x in range(12, 21, 2):
        cv.set(x, 22, 's4')
        cv.set(x, 23, 's3')
    for (x, y) in ((11, 11), (12, 11), (13, 10), (22, 12)):                              # Moos
        if cv.solid(x, y):
            cv.set(x, y, 'g3')
    cv.outline('s0')
    for y in range(22, 31):                                                              # halb im Schlamm
        for x in range(2, 31):
            dx, dy = (x - 16) / 14.0, (y - 26) / 4.0
            if not cv.solid(x, y) and dx * dx + dy * dy <= 1 and hsh(x, y, 1, 670) < 0.8:
                cv.set(x, y, 'br0' if hsh(x, y, 2, 670) < 0.6 else 'br1')
    return cv.img()


def ribs():
    cv = Cv(32, 32)
    for k in range(5):
        x0 = 6 + k * 5
        for i in range(12):
            y = 9 + i
            x = x0 + 4 * math.sin(i / 11.0 * math.pi * 0.9) * (1 if k % 2 else 1)
            cv.set(round(x), y, 's5' if i < 6 else 's4')
            cv.set(round(x) + 1, y, 's3')
    for y in range(8, 24):
        cv.set(3, y, 's3')
        cv.set(4, y, 's4')
    cv.outline('s0')
    for y in range(18, 28):
        for x in range(0, 32):
            dx, dy = (x - 16) / 15.0, (y - 23) / 4.0
            if not cv.solid(x, y) and dx * dx + dy * dy <= 1 and hsh(x, y, 1, 671) < 0.7:
                cv.set(x, y, 'br0' if hsh(x, y, 2, 671) < 0.6 else 'br1')
    return cv.img()


# ============================================================ Animiert
def frog_pose(pose, t=0):
    """Frosch von oben, Blick nach Osten (Pose: 'sit', 'crouch', 'leap')."""
    cv = Cv(32, 32)
    cx, cy = 15, 16
    ext = {'sit': 0, 'crouch': -1, 'leap': 4}[pose]
    # Hinterbeine
    for sd in (-1, 1):
        L = 5 + ext
        for i in range(L):
            cv.set(cx - 3 - i, cy + sd * (4 - min(i, 3) * 0 + (1 if i > 2 else 0) * (0 if pose == 'leap' else 1)) if pose != 'leap' else cy + sd * (3 + i // 3), 'g3' if i % 2 else 'g2')
        cv.rect(cx - 3 - L, cy + sd * (3 + (L // 3 if pose == 'leap' else 1)) - 0, cx - 2 - L, cy + sd * (3 + (L // 3 if pose == 'leap' else 1)), 'g4')
    cv.ell(cx, cy, 7 + (2 if pose == 'leap' else 0), 5 - (1 if pose == 'leap' else 0), lambda dx, dy, x, y: ('g4' if (-0.5 * dx - 0.8 * dy) > 0.45 else ('g3' if (-0.5 * dx - 0.8 * dy) > -0.2 else ('g2' if (-0.5 * dx - 0.8 * dy) > -0.6 else 'g1'))) if hsh(x, y, 1, 680) > 0.07 else 'g2')
    # Flecken
    for (x, y) in ((cx - 2, cy - 2), (cx, cy + 2), (cx - 4, cy + 1), (cx + 1, cy - 3)):
        if cv.solid(x, y):
            cv.set(x, y, 'g1')
    # Vorderbeine
    for sd in (-1, 1):
        cv.rect(cx + 5, cy + sd * 5 - (0 if sd > 0 else 0), cx + 7 + ext // 2, cy + sd * 5, 'g3')
    # Kopf-Augen
    for sd in (-1, 1):
        cv.rect(cx + 6, cy + sd * 3, cx + 7, cy + sd * 3, 'yel')
        cv.set(cx + 7, cy + sd * 3, 'ink')
    cv.outline('g0')
    return cv


def frog_sit():
    frames = []
    for t in range(N):
        cv = frog_pose('sit')
        # Kehlsack pulsiert, Blinzeln in Frame 5
        pulse = [0, 1, 2, 2, 1, 0, 0, 1][t]
        for dx in range(pulse):
            cv.set(22 + dx, 16, 'cream')
        if t == 5:
            for sd in (-1, 1):
                cv.set(21, 16 + sd * 3, 'g2')
                cv.set(22, 16 + sd * 3, 'g2')
        # Schatten
        cv.under(lambda x, y: 'g0' if ((x - 15) / 11.0) ** 2 + ((y - 19) / 7.0) ** 2 <= 1 and hsh(x, y, 1, 681) < 0.7 else None)
        frames.append(cv.img())
    return frames


def frog_hop(deg):
    seq = ['sit', 'crouch', 'crouch', 'leap', 'leap', 'leap', 'crouch', 'crouch']
    arc = [0, 0, 0, 5, 8, 5, 0, 0]
    frames = []
    for t in range(N):
        pose = frog_pose(seq[t]).img()
        # drehen: E = 0, S = 270 (ROTATE_270 = 90 Grad im Uhrzeigersinn)
        k = {'E': 0, 'S': 1, 'W': 2, 'N': 3}[deg]
        for _ in range(k):
            pose = rot90(pose)
        out = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        sh = Cv(32, 32)
        sh.under(lambda x, y: 'g0' if ((x - 15) / (11.0 - arc[t] * 0.5)) ** 2 + ((y - 19) / (7.0 - arc[t] * 0.3)) ** 2 <= 1 and hsh(x, y, 2, 682) < 0.7 else None)
        out.alpha_composite(sh.img())
        out.alpha_composite(pose, (0, -arc[t]))
        frames.append(out)
    return frames


def wisp():
    frames = []
    for t in range(N):
        cv = Cv(32, 48)
        ph = 2 * math.pi * t / N
        cx = 16 + 3 * math.sin(ph)
        cy = 22 + 2 * math.sin(2 * ph)
        sz = 1.0 + 0.4 * math.sin(ph * 2 + 1)
        for y in range(48):
            for x in range(32):
                dx, dy = x + .5 - cx, (y + .5 - cy) * 0.75
                d = math.hypot(dx, dy)
                if d < 9 and hsh(x, y, t % 4, 690) < (1 - d / 9.0) * 0.30:
                    cv.set(x, y, 'b4' if hsh(x, y, 5, 691) > 0.5 else 'violet')
        for y in range(48):                                                          # Flammenkern
            for x in range(32):
                dx, dy = (x + .5 - cx) / (2.2 * sz), (y + .5 - cy) / (3.4 * sz)
                tail = max(0.0, (y + .5 - cy) / 10.0)
                if dx * dx / (1 + tail * 0.8) + (dy + 0.25 * math.sin(ph + y * 0.4)) ** 2 <= 1 and y + .5 < cy + 7:
                    r_ = math.hypot(dx, dy)
                    cv.set(x, y, 'b5' if r_ < 0.45 else ('b4' if r_ < 0.8 else 'violet'))
        for k in range(3):                                                           # aufsteigende Funken
            yy = (cy - 4 - ((t * 3 + k * 8) % 20))
            xx = cx + 4 * math.sin(k * 2 + t * 0.5)
            if 2 < yy < 46 and hsh(k, t, 1, 692) > 0.2:
                cv.set(xx, yy, 'b4')
        frames.append(cv.img())
    return frames


def bubbles():
    frames = []
    spec = [(9, 0), (19, 3), (14, 5), (23, 1)]
    for t in range(N):
        cv = Cv(32, 32)
        for k, (x0, off) in enumerate(spec):
            u = ((t + off) % N) / float(N)
            y = 27 - u * 22
            x = x0 + 2 * math.sin(u * 6.28 + k)
            r = 1 + (1 if u > 0.4 else 0) + (1 if k % 2 and u > 0.7 else 0)
            if u > 0.92:                                                              # Platzen: Ring
                for a in range(8):
                    cv.set(x + 3 * math.cos(a * 0.785), y + 3 * math.sin(a * 0.785), 'b4')
                continue
            cv.ell(x, y, r, r, lambda dx, dy, X, Y: 'b4')
            cv.set(int(x - r * 0.3), int(y - r * 0.3), 'b5')
        frames.append(cv.img())
    return frames


def main():
    td = W.zone_dir('sumpf', 'Tileset')
    od = W.zone_dir('sumpf', 'Objekte')
    ad = W.zone_dir('sumpf', 'Animiert')
    errs = []

    def chk(im, name):
        errs.extend(W.check_palette(im, name))
    fl = TL.floor_set(td + '/Boden_Sumpf.png', floor_px, 4)
    chk(fl, 'Boden_Sumpf')
    mo = TL.build_blob(td + '/Moorwasser.png', moor_inside, moor_outside, frames=N, M=6, R=9, amp=1.3)
    chk(mo, 'Moorwasser')
    bw = board_sheet()
    bw.save(td + '/Bohlenweg.png')
    chk(bw, 'Bohlenweg')
    TL.layout_json(td + '/_Layout_Sumpf.json', 'Sumpf', N, {
        'fpsEmpfohlen': 4,
        'sheets': {'Moorwasser.png': '47er-Autotile, 8 Frames; Aussen = Schlammufer + Boden_Sumpf', 'Bohlenweg.png': '16 Wegstuecke, Spalte = Maske (N1 O2 S4 W8), transparent',
                   'Boden_Sumpf.png': '4 nahtlose Bodenvarianten nebeneinander'}})
    TL.preview_blob(mo, 'Sumpf_Moorwasser', TL.split_floor(fl), None, frames=(0, 4))
    # Vorschau Bohlenweg
    pm = ["......", ".####.", ".#..#.", ".#..##", ".####.", "......"]
    path = {(x, y) for y, r in enumerate(pm) for x, c in enumerate(r) if c == '#'}
    pv = Image.new('RGBA', (6 * 32, 6 * 32))
    fl4 = TL.split_floor(fl)
    for y in range(6):
        for x in range(6):
            pv.paste(fl4[(x + y) % 4], (x * 32, y * 32))
            if (x, y) in path:
                m, _ = W.mask_from_map(path, x, y)
                pv.alpha_composite(bw.crop((m * 32, 0, m * 32 + 32, 32)), (x * 32, y * 32))
    pv.resize((6 * 64, 6 * 64), Image.NEAREST).save(W.WELT + '/_Vorschau/Sumpf_Bohlenweg.png')
    objs = {'Mangrove': mangrove(), 'Totholz': deadwood(), 'Entengruetze_A': duckweed(0), 'Entengruetze_B': duckweed(1), 'Entengruetze_C': duckweed(2),
            'Moorfund_Schaedel': skull(), 'Moorfund_Rippen': ribs()}
    for n, im in objs.items():
        im.save('%s/%s.png' % (od, n))
        chk(im, n)
    anims = [('Frosch_Sitzen', frog_sit()), ('Irrlicht', wisp()), ('Blasen', bubbles())] + [('Frosch_Huepfen_' + d, frog_hop(d)) for d in 'SWNE']
    for n, fr in anims:
        im = strip(fr)
        im.save('%s/%s.png' % (ad, n))
        chk(im, n)
        errs += W.check_loop(fr, n)
    print('Naht Moorwasser (Mittel, 95%%, Formfehler): %.2f %.2f %d' % TL.seam_ok(mo, M=6, R=9, amp=1.3))
    if errs:
        print('\n'.join(errs))
        sys.exit(1)
    print('ok Sumpf')


if __name__ == '__main__':
    main()
