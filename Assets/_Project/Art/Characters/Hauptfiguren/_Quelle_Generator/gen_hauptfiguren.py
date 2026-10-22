"""Hauptfiguren Mann/Frau: 8 Richtungen, Idle (6 Frames) und Walk (8 Frames) im 56x56-Raster.

Alles wird aus Rechtecken gezeichnet, nur Hex-Werte der Nightward-Palette. Kopf und Oberkoerper sind in jedem
Frame identisch (nur Bob/Atmung/Armschwung), die Beine sind gegliedert (Oberschenkel, Knie, Wade, Stiefel).
Zeilen wie die NPC-Sheets: S, SW, W, NW, N, NE, E, SE. NE/E/SE sind gespiegelte NW/W/SW (alle Anbauteile sitzen mittig).

Aufruf:  python gen_hauptfiguren.py [Ausgabeordner]
"""
import math
import os
import sys

from PIL import Image

CELL, OX, OY = 56, 4, 7
PAL = ['1a1526', '2b2140', '3d2e4a', '4f3d5c', '6b5a7a', '1f2a3d', '2c3e56', '3f5570', 'e8e0f0', '3b2a22', '5c4033',
       '7a5a43', '9c7a5a', 'b89a72', '1e3a2b', '2f5a3c', '4a7a4f', '6e9a5e', '9ab87a', '4a4550', '6e6a74', '9a95a0',
       '5e3d33', '8c5f4d', 'd19a7a', '7a2e3a', 'c4636b', '3a4a7a', '6b7fb8', 'ffd27a', 'ffa550', 'e8733a', 'fff1c9',
       '6fd3e6', 'a8f0ff', '2b6b8a', 'f2ead8', 'd64a6a', '8a1f3d']
PALSET = set('#' + p for p in PAL)

K, K2, V1, V2, V3 = '#1a1526', '#2b2140', '#3d2e4a', '#4f3d5c', '#6b5a7a'
B1, B2, B3 = '#1f2a3d', '#2c3e56', '#3f5570'
HR, W1, W2, W3, SAND = '#3b2a22', '#5c4033', '#7a5a43', '#9c7a5a', '#b89a72'
SD, SM, SL = '#5e3d33', '#8c5f4d', '#d19a7a'
ROSE, RD = '#c4636b', '#7a2e3a'
CR, ST, ST2 = '#fff1c9', '#9a95a0', '#6e6a74'
G1, G2, G3 = '#1e3a2b', '#2f5a3c', '#4a7a4f'

# Jacke: Licht, Grund, Schatten, Tief. Senfgold: Orange als Grund, Warmgelb als Licht, Schatten ins Braun
JACKET = ('#ffd27a', '#ffa550', '#9c7a5a', '#7a5a43')

SPECS = {
    'Mann': dict(female=False, J=JACKET, bag=(W2, W1, W3), hair=(HR, W1)),
    'Frau': dict(female=True, J=JACKET, bag=(G2, G1, G3), hair=(HR, W1), cap=(ROSE, RD, CR)),
}

# Beine und Schuhe: eigene Palette, damit der Masken-Modus sie von Rucksack und Haaren unterscheiden kann (gleiche Braun-Toene).
LEGPAL = dict(pants=(B1, B2, B3), pants_dark=(B1, B1, B2), boot=(W1, W2, W3), boot_dark=(HR, HR, W1), sole=HR, sole_dark=K2, edge=HR, edge_dark=K2)

# Masken-Modus (NW_MASK=1): statt der Bilder entstehen Masken fuer die Kleidung (siehe PlayerOutfit in Unity). Jacke, Hose und Schuhe
# werden mit eindeutigen Farben gezeichnet; to_img schreibt daraus je Pixel R = Bereich (1 Oberteil, 2 Hose, 3 Schuhe), G = Stufe.
# Oberteil (wie JACKET): 0 Licht, 1 Grund, 2 Schatten, 3 Tief. Hose: 0 Dunkel, 1 Grund, 2 Licht. Schuhe: 0 Sohle, 1 Dunkel, 2 Grund, 3 Licht.
MASK = bool(os.environ.get('NW_MASK'))
MASK_TOP = ('#f00001', '#f00002', '#f00003', '#f00004')
MASK_LEG = ('#f01001', '#f01002', '#f01003')
MASK_SHOE = ('#f02000', '#f02001', '#f02002', '#f02003')
MASK_CODE = {}
for _i, _c in enumerate(MASK_TOP):
    MASK_CODE[_c] = (1, _i)
for _i, _c in enumerate(MASK_LEG):
    MASK_CODE[_c] = (2, _i)
for _i, _c in enumerate(MASK_SHOE):
    MASK_CODE[_c] = (3, _i)
if MASK:
    for _s in SPECS.values():
        _s['J'] = MASK_TOP
    LEGPAL = dict(pants=MASK_LEG, pants_dark=(MASK_LEG[0], MASK_LEG[0], MASK_LEG[1]), boot=MASK_SHOE[1:], boot_dark=(MASK_SHOE[0], MASK_SHOE[0], MASK_SHOE[1]),
                  sole=MASK_SHOE[0], sole_dark=MASK_SHOE[0], edge=MASK_SHOE[0], edge_dark=MASK_SHOE[0])

# Richtung: (fx, fy) Blickrichtung auf dem Bildschirm
VIEWS = {'S': (0, 1), 'SW': (-.7, .7), 'W': (-1, 0), 'NW': (-.7, -.7), 'N': (0, -1)}
ORDER = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE']
MIRROR = {'NE': 'NW', 'E': 'W', 'SE': 'SW'}


class Cv:
    def __init__(s):
        s.b = [[None] * CELL for _ in range(CELL)]
        s.dy = 0
        s.dx = 0

    def P(s, x, y, c):
        X, Y = int(x) + OX + s.dx, int(y) + OY + s.dy
        if 0 <= X < CELL and 0 <= Y < CELL:
            s.b[Y][X] = c

    def R(s, x1, y1, x2, y2, c):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                s.P(x, y, c)


def rnd(v):
    return int(math.floor(v + 0.5))


# ---------------------------------------------------------------- Beine
def leg(cv, hx, hy, ax, ay, w, kb, dark, toe):
    pants = LEGPAL['pants_dark'] if dark else LEGPAL['pants']
    boot = LEGPAL['boot_dark'] if dark else LEGPAL['boot']
    sole = LEGPAL['sole_dark'] if dark else LEGPAL['sole']
    edge = LEGPAL['edge_dark'] if dark else LEGPAL['edge']
    kx = (hx + ax) / 2.0 + kb
    n = max(1, ay - hy)
    for y in range(hy, ay + 1):
        u = (y - hy) / float(n)
        x = hx + (kx - hx) * u / 0.5 if u < 0.5 else kx + (ax - kx) * (u - 0.5) / 0.5
        wd = w if u < 0.55 else w - 1
        x0 = rnd(x - wd / 2.0 + 0.01)
        for i in range(wd):
            c = pants[1]
            if i == 0:
                c = pants[0]
            elif i == wd - 1 and wd >= 4:
                c = pants[2]
            cv.P(x0 + i, y, c)
    bw = w + 1
    x0 = rnd(ax - bw / 2.0 + 0.01)
    for k in range(4):
        y = ay + 1 + k
        for i in range(bw):
            c = boot[0]
            if k == 0:
                c = boot[1]
            elif i == 0:
                c = edge
            elif i == bw - 1 and k < 3:
                c = boot[2]
            if k == 3:
                c = sole
            cv.P(x0 + i, y, c)
        if toe and k >= 2:
            for d in range(2):
                xx = x0 + bw + d if toe > 0 else x0 - 1 - d
                cv.P(xx, y, sole if k == 3 else boot[0])


def legs_pose(cv, view, phase, amp=5.0, lift_h=2.4, diag=1.0, kneek=0.4, env=0.0):
    fx, fy = VIEWS[view]
    side = abs(fx) == 1
    idle = phase is None
    AMPX, AMPY, LIFT = amp, 1.4 * amp / 5.0, lift_h
    specs = []
    for idx, off in enumerate((0.0, 0.5)):
        if idle:
            s_, c_ = 0.0, 0.0
        else:
            s_ = math.sin(2 * math.pi * (phase + off))
            c_ = math.cos(2 * math.pi * (phase + off))
        # env > 0 (Lauf): das Schwungbein hebt schon beim Abdruck ab und setzt erst spaet auf, dazwischen fliegt der Koerper
        lift = 0 if idle else (max(0.0, c_) * LIFT if env <= 0 else LIFT * max(0.0, min(1.0, (c_ + env) / (1.0 + env))))
        if side:
            sgn = 1 if fx > 0 else -1
            hx, w, dark = 23.5, 5, idx == 1
            ax = hx + s_ * AMPX * sgn
            kb = sgn * (0.7 + lift * kneek)   # kneek: wie weit das Knie des angehobenen Beins nach vorn geht (Lauf: hoeher)
            ay = 42 - rnd(lift)
            toe = sgn
            depth = 0 if idx == 0 else -1
        else:
            hx = 21.0 if idx == 0 else 26.0
            w, dark, toe, kb = 4, False, 0, 0.0
            ax = hx + s_ * AMPX * fx * 0.7 * diag
            ay = 42 + rnd(s_ * AMPY * fy) - rnd(lift * 0.8)
            depth = s_ * fy
        specs.append((depth, dict(hx=hx, hy=33, ax=ax, ay=ay, w=w, kb=kb, dark=dark, toe=toe)))
    specs.sort(key=lambda t: t[0])
    for _, sp in specs:
        leg(cv, sp['hx'], sp['hy'], sp['ax'], sp['ay'], sp['w'], sp['kb'], sp['dark'], sp['toe'])
    # Becken
    x1, x2 = (20, 27) if side else (19, 28)
    cv.R(x1, 29, x2, 34, LEGPAL['pants'][1])
    for y in range(29, 35):
        cv.P(x1, y, LEGPAL['pants'][0])
        cv.P(x2, y, LEGPAL['pants'][2])


# ---------------------------------------------------------------- Oberkoerper
def hand(cv, x, y):
    cv.R(x, y, x + 1, y + 2, SL)
    cv.P(x, y, SM)
    cv.P(x, y + 1, SM)
    cv.P(x, y + 2, SM)


def arms_front(cv, s, swing, narrow_right=False):
    if s.get('noarms'):
        return
    hl, base, sh, dk = s['J']
    sl, sr = swing, -swing
    cv.R(16, 19, 18, 26 + sl, base)
    for y in range(19, 27 + sl):
        cv.P(16, y, sh)
        cv.P(18, y, sh)
    hand(cv, 16, 27 + sl)
    if narrow_right:
        cv.R(28, 19, 30, 25 + sr, base)
        for y in range(19, 26 + sr):
            cv.P(30, y, sh)
        hand(cv, 29, 26 + sr)
    else:
        cv.R(29, 19, 31, 26 + sr, base)
        for y in range(19, 27 + sr):
            cv.P(29, y, sh)
            cv.P(31, y, hl)
        hand(cv, 30, 27 + sr)


def bust_front(cv, s):
    """Grosse Brust: zwei Waelbungen ueber den Armansatz hinaus, dunkle Unterkante, Licht oben rechts."""
    hl, base, sh, dk = s['J']
    rows = {20: (20, 22), 21: (19, 23), 22: (18, 23), 23: (18, 23), 24: (19, 22)}
    for y, (a, b) in rows.items():
        for x in range(a, b + 1):
            cv.P(x, y, base)
            cv.P(47 - x, y, base)
    for x in range(19, 24):
        cv.P(x, 25, dk)
        cv.P(47 - x, 25, dk)
    for x in range(18, 24):
        cv.P(x, 24, sh)
        cv.P(47 - x, 24, sh)
    cv.P(18, 22, sh)
    cv.P(18, 23, sh)
    cv.P(29, 23, sh)
    for p in ((22, 21), (23, 21), (27, 21), (28, 21), (27, 22), (29, 22)):
        cv.P(p[0], p[1], hl)
    for p in ((23, 22), (24, 22), (23, 23), (24, 23)):
        cv.P(p[0], p[1], dk if p[1] == 23 else sh)


def head_front(cv, s, turn):
    fem = s['female']
    hh, hh2 = s['hair']
    sx = -1 if turn else 0
    if fem:
        cv.R(20, 10, 27, 15, SL)
        cv.R(21, 16, 26, 16, SL)
        cv.R(22, 17, 25, 17, SM)
        for y in range(10, 16):
            cv.P(20, y, SM)
        cv.R(21, 16, 22, 16, SM)
        cv.R(19, 10, 19, 15, hh)
        cv.R(28, 10, 28, 15, hh)
        if turn:
            cv.R(26, 10, 28, 15, hh)
            cv.P(19, 11, SL)
            cv.P(19, 12, SL)
        cv.P(19, 12, hh2)
        cv.P(28, 12, hh2)
        rose, rd, cr = s['cap']
        cv.R(21, 5, 26, 5, rose)
        cv.R(20, 6, 27, 6, rose)
        cv.R(19, 7, 28, 8, rose)
        cv.R(18, 9, 29, 9, rd)
        if turn:
            cv.R(14, 9, 18, 9, rd)
            cv.R(15, 8, 19, 8, rose)
        cv.P(24, 6, cr)
        cv.P(25, 6, cr)
        cv.P(23, 5, cr)
        cv.R(20, 10, 27, 10, SM)
        cv.R(21 + sx, 11, 22 + sx, 11, K)
        cv.R(25 + sx, 11, 26 + sx, 11, K)
        cv.P(23 + sx, 13, SM)
        cv.P(24 + sx, 13, SM)
        cv.R(23 + sx, 14, 24 + sx, 14, ROSE)
        if turn:
            cv.P(19, 13, SL)
    else:
        cv.R(20, 9, 27, 9, SL)
        cv.R(19, 10, 28, 15, SL)
        cv.R(20, 16, 27, 16, SL)
        cv.R(22, 17, 25, 17, SM)
        for y in range(10, 16):
            cv.P(19, y, SM)
        cv.R(20, 16, 22, 16, SM)
        cv.R(21, 5, 26, 5, hh)
        cv.R(20, 6, 27, 6, hh)
        cv.R(19, 7, 28, 7, hh)
        for p in ((24, 6), (25, 6), (26, 5), (27, 7), (26, 7)):
            cv.P(p[0], p[1], hh2)
        cv.R(19, 8, 19, 9, hh)
        cv.R(28, 8, 28, 9, hh)
        if turn:
            cv.R(26, 8, 28, 13, hh)
            cv.P(27, 9, hh2)
        cv.R(20 + sx, 8, 22 + sx, 8, K2)
        cv.R(25 + sx, 8, 27 + sx, 8, K2)
        cv.P(23 + sx, 8, V2)
        cv.P(24 + sx, 8, V2)
        cv.P(21 + sx, 8, V3)
        cv.P(26 + sx, 8, V3)
        cv.R(21 + sx, 10, 22 + sx, 10, hh)
        cv.R(25 + sx, 10, 26 + sx, 10, hh)
        cv.R(21 + sx, 11, 22 + sx, 11, K)
        cv.R(25 + sx, 11, 26 + sx, 11, K)
        cv.P(23 + sx, 13, SM)
        cv.P(24 + sx, 13, SM)
        cv.R(23 + sx, 14, 24 + sx, 14, SD)
        if not turn:
            cv.P(18, 11, SM)
            cv.P(18, 12, SM)
            cv.P(29, 11, SL)
            cv.P(29, 12, SL)
        else:
            cv.P(29, 11, SM)
            cv.P(29, 12, SM)


def upper_front(cv, s, swing, turn):
    fem = s['female']
    hl, base, sh, dk = s['J']
    bag, bagd, bagl = s['bag']
    # Rucksack hinten
    if not turn:
        cv.R(14, 19, 15, 30, bag)
        cv.R(32, 19, 33, 30, bag)
        for y in range(19, 31):
            cv.P(14, y, bagd)
            cv.P(32, y, bagl)
        cv.R(14, 28, 15, 30, bagd)
        cv.R(32, 28, 33, 30, bagd)
        if not fem:
            cv.R(17, 17, 19, 17, bag)
            cv.R(28, 17, 30, 17, bag)
    else:
        cv.R(29, 18, 34, 30, bag)
        for y in range(18, 31):
            cv.P(34, y, bagd)
            cv.P(29, y, bagd)
        cv.R(30, 18, 33, 18, bagl)
        cv.R(30, 27, 33, 30, bagd)
    arms_front(cv, s, swing, narrow_right=bool(turn))
    # Rumpf
    cv.R(17, 18, 30, 18, base)
    if fem:
        cv.R(19, 19, 28, 24, base)
        cv.R(20, 25, 27, 26, base)
        for y in range(19, 25):
            cv.P(19, y, sh)
        cv.P(20, 25, sh)
        cv.P(20, 26, sh)
        bust_front(cv, s)
    else:
        cv.R(19, 19, 28, 27, base)
        for y in range(19, 28):
            cv.P(19, y, sh)
    for p in ((27, 18), (28, 18), (29, 18), (30, 19), (31, 19), (31, 20)):
        cv.P(p[0], p[1], hl)
    # Kragen und Hals
    cv.R(22, 18, 25, 18, SM)
    cv.R(23, 19, 24, 19, SM)
    for p in ((21, 18), (26, 18), (22, 19), (25, 19)):
        cv.P(p[0], p[1], sh)
    if not fem:
        for y in range(20, 28):
            cv.P(23, y, sh)
    # Rucksackgurte
    if fem:
        for y in (19, 20, 25, 26):
            cv.P(21, y, bag)
            cv.P(26, y, bag)
    else:
        for y in range(19, 28):
            cv.P(21, y, bag)
            cv.P(26, y, bag)
        cv.R(21, 22, 26, 22, bagd)
    # Guertel
    by = 27 if fem else 28
    x1, x2 = (20, 27) if fem else (19, 28)
    cv.R(x1, by, x2, by, HR)
    cv.P(23, by, SAND)
    cv.P(24, by, SAND)
    # Schluesselring vorn am Guertel
    cv.P(24, by + 1, ST)
    cv.P(25, by + 1, ST)
    cv.P(24, by + 2, ST2)
    cv.P(25, by + 2, ST2)
    cv.P(25, by + 3, ST)
    head_front(cv, s, turn)
    if fem:
        h0, h1 = s['hair']
        # Pferdeschwanz lugt rechts hinter dem Kopf hervor
        if not turn:
            cv.P(29, 10, h0)
            cv.P(29, 11, ROSE)
            cv.P(29, 12, h0)
            cv.R(30, 12, 31, 16, h0)
            cv.P(30, 17, h0)
            cv.P(31, 17, h0)
            for p in ((31, 12), (31, 13), (31, 14), (30, 15)):
                cv.P(p[0], p[1], h1)
        else:
            cv.P(29, 10, h0)
            cv.P(29, 11, ROSE)
            cv.R(29, 12, 30, 15, h0)
            cv.P(30, 16, h0)
            cv.P(30, 12, h1)


def upper_back(cv, s, swing, turn):
    fem = s['female']
    hl, base, sh, dk = s['J']
    bag, bagd, bagl = s['bag']
    hh, hh2 = s['hair']
    sl, sr = swing, -swing
    if not s.get('noarms'):
        cv.R(16, 19, 18, 26 + sl, base)
        for y in range(19, 27 + sl):
            cv.P(16, y, sh)
            cv.P(18, y, sh)
        hand(cv, 16, 27 + sl)
        cv.R(29, 19, 31, 26 + sr, base)
        for y in range(19, 27 + sr):
            cv.P(29, y, sh)
            cv.P(31, y, hl)
        hand(cv, 30, 27 + sr)
    cv.R(17, 18, 30, 18, base)
    cv.R(19, 19, 28, 27, base)
    # Rucksack (Rueckseite)
    x1, x2 = (19, 30) if turn else (18, 29)
    cv.R(x1, 19, x2, 31, bag)
    cv.R(x1 + 1, 18, x2 - 1, 21, bagl)
    cv.R(x1, 22, x2, 22, bagd)
    cv.R(x1, 23, x1, 31, bagd)
    cv.R(x2, 23, x2, 31, bagd)
    cv.R(x1 + 1, 27, x1 + 2, 31, bagd)
    cv.R(x2 - 2, 27, x2 - 1, 31, bagd)
    cv.R(x1, 31, x2, 31, bagd)
    cv.P((x1 + x2) // 2, 22, SAND)
    cv.P((x1 + x2) // 2 + 1, 22, SAND)
    cv.R(x1 + 3, 24, x2 - 3, 25, bag)
    if turn:
        cv.R(17, 19, 18, 30, bagd)
    cv.R(22, 17, 25, 18, SM)
    # Kopf von hinten
    if fem:
        rose, rd, cr = s['cap']
        cv.R(20, 9, 27, 15, hh)
        cv.R(21, 16, 26, 16, hh)
        cv.R(21, 5, 26, 5, rose)
        cv.R(20, 6, 27, 6, rose)
        cv.R(19, 7, 28, 8, rose)
        cv.R(19, 9, 28, 9, rd)
        cv.P(23, 5, cr)
        cv.P(24, 6, cr)
        cv.P(25, 6, cr)
        for y in range(10, 15):
            cv.P(21, y, hh2)
            cv.P(26, y, hh2)
        # Pferdeschwanz hinten mittig
        cv.R(23, 10, 24, 10, ROSE)
        cv.R(22, 11, 25, 17, hh)
        cv.R(23, 18, 24, 23, hh)
        cv.P(25, 12, hh2)
        cv.P(25, 14, hh2)
        cv.P(24, 18, hh2)
        cv.P(24, 20, hh2)
        if turn:
            cv.P(19, 11, SL)
            cv.P(19, 12, SL)
    else:
        cv.R(21, 5, 26, 5, hh)
        cv.R(20, 6, 27, 6, hh)
        cv.R(19, 7, 28, 15, hh)
        cv.R(20, 16, 27, 16, hh)
        for p in ((22, 6), (24, 5), (25, 6), (23, 8), (26, 9), (21, 10), (24, 12), (27, 13), (22, 14)):
            cv.P(p[0], p[1], hh2)
        cv.P(18, 11, SM)
        cv.P(18, 12, SM)
        cv.P(29, 11, SL)
        cv.P(29, 12, SL)
        if turn:
            cv.P(19, 11, SL)
            cv.P(19, 12, SL)
            cv.P(19, 13, SL)


def upper_side(cv, s, swing_a):
    """Seitenansicht nach links (W). swing_a in -1..1: Hand vor/zurueck."""
    fem = s['female']
    hl, base, sh, dk = s['J']
    bag, bagd, bagl = s['bag']
    hh, hh2 = s['hair']
    # ferner Arm (hinter dem Koerper, dunkel)
    far_hx = 24 + rnd(-swing_a * 3)
    if not s.get('noarms'):
        for y in range(19, 28):
            x = rnd(24 + (far_hx - 24) * (y - 19) / 8.0)
            cv.R(x - 1, y, x + 1, y, sh)
        cv.R(far_hx - 1, 27, far_hx, 29, SM)
    # Rucksack
    cv.R(27, 18, 32, 31, bag)
    cv.R(27, 18, 32, 19, bagl)
    cv.R(32, 20, 32, 31, bagd)
    cv.R(27, 23, 32, 23, bagd)
    cv.R(28, 27, 31, 31, bagd)
    cv.P(32, 18, None)
    cv.P(32, 31, None)
    cv.R(29, 25, 31, 26, bag)
    # Rumpf
    cv.R(21, 18, 26, 18, base)
    cv.R(20, 19, 27, 27, base)
    for y in range(19, 28):
        cv.P(20, y, sh)
        cv.P(26, y, hl if y < 22 else base)
    cv.P(25, 18, hl)
    cv.P(26, 18, hl)
    if fem:
        cv.R(27, 25, 27, 27, None)
        cv.R(20, 25, 20, 27, None)
        cv.R(21, 25, 26, 27, base)
        cv.P(21, 25, sh)
        rows = {20: (19, 21), 21: (18, 21), 22: (18, 21), 23: (18, 21), 24: (19, 21)}
        for y, (a, b) in rows.items():
            cv.R(a, y, b, y, base)
        cv.R(19, 25, 21, 25, dk)
        cv.R(18, 23, 21, 23, sh)
        cv.R(19, 24, 21, 24, sh)
        cv.P(19, 21, hl)
        cv.P(20, 21, hl)
        cv.P(18, 22, sh)
        by, bx1, bx2 = 27, 21, 26
    else:
        by, bx1, bx2 = 28, 20, 27
    # Hals / Kragen
    cv.R(22, 17, 25, 17, SM)
    cv.R(22, 18, 24, 18, SM)
    cv.P(21, 18, sh)
    cv.P(25, 18, sh)
    # Rucksackgurt
    for p in ((25, 19), (24, 20), (23, 21), (23, 22), (23, 23), (23, 24)):
        cv.P(p[0], p[1], bag)
    # Guertel + Schluesselring vorn
    cv.R(bx1, by, bx2, by, HR)
    cv.P(bx1, by, SAND)
    cv.P(bx1 - 1, by + 1, ST)
    cv.P(bx1 - 1, by + 2, ST)
    cv.P(bx1, by + 1, ST2)
    cv.P(bx1, by + 2, ST2)
    cv.P(bx1 - 1, by + 3, ST2)
    # naher Arm
    near_hx = 24 + rnd(swing_a * 3)
    if not s.get('noarms'):
        for y in range(19, 28):
            x = rnd(24 + (near_hx - 24) * (y - 19) / 8.0)
            cv.R(x - 1, y, x + 1, y, base)
            cv.P(x - 1, y, sh)
            cv.P(x + 1, y, hl)
        cv.R(near_hx - 1, 28, near_hx, 30, SL)
        cv.P(near_hx - 1, 28, SM)
        cv.P(near_hx - 1, 29, SM)
    # Kopf im Profil, Blick nach links
    cv.R(20, 9, 24, 15, SL)
    cv.R(19, 10, 19, 14, SL)
    cv.R(20, 16, 24, 16, SL)
    cv.R(25, 9, 28, 15, hh)
    for y in range(10, 16):
        cv.P(24, y, SM)
    cv.R(20, 16, 22, 16, SM)
    cv.P(18, 12, SL)
    cv.P(21, 11, K)
    cv.P(22, 11, K)
    if fem:
        rose, rd, cr = s['cap']
        cv.R(21, 5, 26, 5, rose)
        cv.R(20, 6, 27, 6, rose)
        cv.R(19, 7, 28, 8, rose)
        cv.R(14, 9, 25, 9, rd)
        cv.R(15, 8, 19, 8, rose)
        cv.R(24, 6, 25, 6, cr)
        cv.R(20, 10, 24, 10, SM)
        cv.R(25, 10, 28, 15, hh)
        cv.R(26, 16, 27, 16, hh)
        cv.P(19, 14, ROSE)
        cv.P(20, 14, ROSE)
        cv.P(28, 11, ROSE)
        cv.R(29, 11, 30, 11, hh)
        cv.R(29, 12, 30, 19, hh)
        cv.R(30, 20, 30, 21, hh)
        cv.P(29, 13, hh2)
        cv.P(29, 16, hh2)
        cv.P(27, 12, hh2)
    else:
        cv.R(21, 5, 26, 5, hh)
        cv.R(20, 6, 27, 6, hh)
        cv.R(20, 7, 28, 7, hh)
        cv.R(24, 8, 28, 9, hh)
        cv.R(26, 14, 28, 14, hh)
        for p in ((24, 6), (25, 6), (26, 5), (27, 7), (26, 9)):
            cv.P(p[0], p[1], hh2)
        # Sonnenbrille auf der Stirn
        cv.R(19, 8, 22, 8, K2)
        cv.R(23, 8, 24, 8, V2)
        cv.P(20, 8, V3)
        cv.R(20, 10, 22, 10, hh)
        cv.P(19, 13, SM)
        cv.P(20, 14, SD)
        cv.P(21, 14, SD)
        cv.P(25, 12, SM)
        cv.P(25, 13, SM)


# ---------------------------------------------------------------- Zusammenbau
def outline(buf):
    out = [row[:] for row in buf]
    for y in range(CELL):
        for x in range(CELL):
            if buf[y][x] is None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < CELL and 0 <= Y < CELL and buf[Y][X] is not None:
                        out[y][x] = K
                        break
    return out


def render(spec, view, phase, bob):
    """Ein Frame als Pixel-Raster. phase None = Idle."""
    real = MIRROR.get(view, view)
    cv = Cv()
    legs_pose(cv, real, phase)
    cv.dy = bob
    swing = 0 if phase is None else math.sin(2 * math.pi * phase)
    if real == 'W':
        upper_side(cv, spec, swing)
    elif real in ('S', 'SW'):
        upper_front(cv, spec, rnd(swing), 1 if real == 'SW' else 0)
    else:
        upper_back(cv, spec, rnd(swing), 1 if real == 'NW' else 0)
    buf = outline(cv.b)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return buf


def to_img(buf):
    im = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    for y in range(CELL):
        for x in range(CELL):
            c = buf[y][x]
            if MASK:
                if c in MASK_CODE:
                    im.putpixel((x, y), (MASK_CODE[c][0], MASK_CODE[c][1], 0, 255))
                continue
            if c:
                if c not in PALSET:
                    raise SystemExit('Farbe nicht in Palette: ' + c)
                im.putpixel((x, y), tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return im


IDLE_BOB = [0, 0, 0, 1, 1, 0]
WALK_BOB = [0, 1, 1, 0, 0, 1, 1, 0]


def build(name, outdir):
    spec = SPECS[name]
    os.makedirs(outdir, exist_ok=True)
    stand = Image.new('RGBA', (8 * CELL, CELL))
    idle = Image.new('RGBA', (6 * CELL, 8 * CELL))
    walk = Image.new('RGBA', (8 * CELL, 8 * CELL))
    for r, v in enumerate(ORDER):
        stand.paste(to_img(render(spec, v, None, 0)), (r * CELL, 0))
        for c, b in enumerate(IDLE_BOB):
            idle.paste(to_img(render(spec, v, None, b)), (c * CELL, r * CELL))
        for c, b in enumerate(WALK_BOB):
            walk.paste(to_img(render(spec, v, c / 8.0, b)), (c * CELL, r * CELL))
    stand.save(os.path.join(outdir, name.lower() + '_stand_8dir.png'))
    idle.save(os.path.join(outdir, name.lower() + '_idle.png'))
    walk.save(os.path.join(outdir, name.lower() + '_walk.png'))


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    for n in SPECS:
        build(n, os.path.join(base, n))
        print('ok', n)
