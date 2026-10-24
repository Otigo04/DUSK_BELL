"""TIERE: Hund, Huhn, Pferd - 8 Richtungen (S, SW, W, NW, N, NE, E, SE; NE/E/SE gespiegelt), Idle (4), Walk (4) und eine Sonderaktion (4).
Zu den Gebaeuden im Dorf (Stall, Scheune, Bauernkate, Karren/Schubkarre) und zur Katze (32x32, 4 Frames, gleiche Palette und Beleuchtung: Licht oben links,
kuehle Schatten, Outline #1a1526). Nur Hex-Werte der Nightward-Palette.

  Hund   32x32-Raster   Idle (steht, Schwanz wedelt, atmet) | Walk | Sleep (eingerollt, 2 Zeilen: W und E)
  Huhn   32x32-Raster   Idle (Kopf ruckt) | Walk | Peck (pickt, 8 Zeilen)
  Pferd  64x64-Raster   Idle (Ohr zuckt, Schweif) | Walk | Graze (Kopf unten, 8 Zeilen)

Ansichten: S (von vorn), W (Seite), N (von hinten) sind eigene Zeichnungen. SW = Seitenkoerper mit frontal gedrehtem Kopf, NW = Seitenkoerper mit abgewandtem Kopf.
Ausgabe je Tier (Tiere/<Name>/): <name>_stand_8dir.png, <name>_idle_sheet.png, <name>_walk_sheet.png, <name>_<aktion>_sheet.png (Zellen nebeneinander = Frames, Zeilen = Richtungen).
Aufruf:  python gen_tiere.py [Ausgabeordner]     (schreibt auch Vorschau_Tiere.png)
"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE']
MIRROR = {'NE': 'NW', 'E': 'W', 'SE': 'SW'}
PAL = ['1a1526', '2b2140', '3d2e4a', '4f3d5c', '6b5a7a', '1f2a3d', '2c3e56', '3f5570', 'e8e0f0', '3b2a22', '5c4033',
       '7a5a43', '9c7a5a', 'b89a72', '1e3a2b', '2f5a3c', '4a7a4f', '6e9a5e', '9ab87a', '4a4550', '6e6a74', '9a95a0',
       '5e3d33', '8c5f4d', 'd19a7a', '7a2e3a', 'c4636b', '3a4a7a', '6b7fb8', 'ffd27a', 'ffa550', 'e8733a', 'fff1c9',
       '6fd3e6', 'a8f0ff', '2b6b8a', 'f2ead8', 'd64a6a', '8a1f3d']
PALSET = set('#' + p for p in PAL)
K, K2, V1 = '#1a1526', '#2b2140', '#3d2e4a'
HR, W1, W2, W3, SAND = '#3b2a22', '#5c4033', '#7a5a43', '#9c7a5a', '#b89a72'
CR, MOON, ST, ST2 = '#fff1c9', '#e8e0f0', '#9a95a0', '#6e6a74'
RD, ROSE, YEL, ORA = '#7a2e3a', '#c4636b', '#ffd27a', '#ffa550'
SD, SM, SL = '#5e3d33', '#8c5f4d', '#d19a7a'


class Cv:
    def __init__(s, cell):
        s.n = cell
        s.b = [[None] * cell for _ in range(cell)]

    def P(s, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < s.n and 0 <= y < s.n:
            s.b[y][x] = c

    def R(s, x1, y1, x2, y2, c):
        for y in range(int(round(y1)), int(round(y2)) + 1):
            for x in range(int(round(x1)), int(round(x2)) + 1):
                s.P(x, y, c)

    def blob(s, cx, cy, rx, ry, pal, light=(-0.6, -0.8)):
        """Beleuchtete Ellipse: pal = (Licht, Grund, Schatten)."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
                d = nx * nx + ny * ny
                if d > 1.0:
                    continue
                lam = nx * light[0] + ny * light[1]
                s.P(x, y, pal[0] if lam > 0.42 else (pal[2] if lam < -0.38 else pal[1]))

    def line(s, x0, y0, x1, y1, c, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0), 1) * 2)
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            y = y0 + (y1 - y0) * i / n
            for dx in range(w):
                for dy in range(w):
                    s.P(x + dx - (w - 1) // 2, y + dy - (w - 1) // 2, c)


def outline(cv):
    n = cv.n
    out = [row[:] for row in cv.b]
    for y in range(n):
        for x in range(n):
            if cv.b[y][x] is None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < n and 0 <= Y < n and cv.b[Y][X] is not None:
                        out[y][x] = K
                        break
    return out


def to_img(buf, n):
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    for y in range(n):
        for x in range(n):
            c = buf[y][x]
            if c:
                if c not in PALSET:
                    raise SystemExit('Farbe nicht in Palette: ' + c)
                im.putpixel((x, y), tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return im


def gait(phase, i, amp, lift_h):
    """Fuss-Offset und Hub fuer Bein i (0..3): diagonale Paare (VL+HR, VR+HL)."""
    off = (0.0, 0.5, 0.5, 0.0)[i]
    if phase is None:
        return 0.0, 0
    s_ = math.sin(2 * math.pi * (phase + off))
    c_ = math.cos(2 * math.pi * (phase + off))
    return s_ * amp, int(round(max(0.0, c_) * lift_h))


# ============================================================================ HUND
DOG = (CR, '#b89a72', '#9c7a5a')           # Fell: hell, Grund, Schatten (sandfarben)
DOGD = ('#7a5a43', '#5c4033', '#3b2a22')   # dunkle Abzeichen: Sattel, Ohren


def dog_leg(cv, x, y0, y1, w, foot_dx, lift, dark):
    pal = DOGD if dark else DOG
    for y in range(y0, y1 - lift + 1):
        cv.R(x, y, x + w - 1, y, pal[1])
        cv.P(x, y, pal[0] if not dark else pal[1])
    cv.R(x + foot_dx - 1, y1 - lift, x + w - 1 + foot_dx + 1, y1 - lift, '#5c4033' if dark else '#7a5a43')


def dog_head_front(cv, cx, cy, down=0):
    cv.blob(cx, cy, 4.5, 4.5, DOG)
    cv.R(cx - 2, cy + 1, cx + 1, cy + 4, CR)                           # Schnauze hell
    cv.R(cx - 1, cy + 3, cx, cy + 3, K)                                # Nase
    cv.P(cx - 2, cy - 1, K)
    cv.P(cx + 1, cy - 1, K)
    cv.P(cx - 2, cy - 2, CR)
    cv.R(cx - 6, cy - 2, cx - 4, cy + 3, DOGD[1])                      # Schlappohren
    cv.R(cx + 4, cy - 2, cx + 6, cy + 3, DOGD[1])
    cv.P(cx - 6, cy - 2, DOGD[0])
    cv.P(cx + 4, cy - 2, DOGD[0])


def dog_side(cv, phase, bob, t, mode='walk', head='side'):
    cv.n  # 32
    by = bob
    # ferne Beine (dunkel)
    for i, x in ((1, 9), (3, 21)):
        fo, lf = gait(phase, i, 3, 2)
        dog_leg(cv, x, 21 + by, 28, 2, int(round(fo)), lf, True)
    cv.blob(14, 18 + by, 8.5, 5.3, DOG)
    cv.R(5, 18 + by, 8, 22 + by, CR)                                    # heller Brustlatz
    cv.blob(15, 15 + by, 5.5, 2, DOGD)                                  # Sattel
    for i, x in ((0, 11), (2, 19)):
        fo, lf = gait(phase, i, 3, 2)
        dog_leg(cv, x, 21 + by, 28, 2, int(round(fo)), lf, False)
    # Schwanz
    wag = (0, 1, 2, 1)[t % 4] if mode == 'idle' else 1
    cv.line(22, 16 + by, 25 + wag // 2, 11 + by - wag // 2, DOG[1], 2)
    cv.P(25 + wag // 2, 10 + by - wag // 2, CR)
    if head == 'side':
        cv.blob(5, 14 + by, 4, 3.8, DOG)
        cv.R(0, 15 + by, 2, 17 + by, CR)
        cv.P(0, 15 + by, K)
        cv.P(4, 13 + by, K)
        cv.R(5, 12 + by, 7, 16 + by, DOGD[1])
        cv.P(5, 12 + by, DOGD[0])
    elif head == 'front':
        dog_head_front(cv, 5, 14 + by)
    else:
        cv.blob(5, 14 + by, 4, 3.8, DOG)
        cv.R(4, 11 + by, 7, 14 + by, DOGD[1])


def dog_front(cv, phase, bob, t, mode='walk'):
    by = bob
    for i, x in ((0, 12), (1, 18)):
        fo, lf = gait(phase, 0 if i == 0 else 1, 0, 2)
        dog_leg(cv, x, 22 + by, 28, 2, 0, lf, False)
    cv.blob(16, 20 + by, 6.5, 5, DOG)
    cv.R(14, 19 + by, 17, 24 + by, CR)
    dog_head_front(cv, 16, 13 + by)


def dog_back(cv, phase, bob, t, mode='walk'):
    by = bob
    for i, x in ((2, 12), (3, 18)):
        fo, lf = gait(phase, 3 if i == 2 else 2, 0, 2)
        dog_leg(cv, x, 22 + by, 28, 2, 0, lf, False)
    cv.blob(16, 19 + by, 6.8, 6, DOG)
    cv.blob(16, 17 + by, 4.5, 3, DOGD)
    wag = (0, 1, 0, -1)[t % 4] if mode == 'idle' else 0
    cv.line(16 + wag, 14 + by, 16 + wag * 2, 8 + by, DOG[1], 2)
    cv.P(16 + wag * 2, 7 + by, CR)
    cv.blob(16, 11 + by, 4, 3, DOGD)
    cv.R(10, 10 + by, 12, 14 + by, DOGD[1])
    cv.R(20, 10 + by, 22, 14 + by, DOGD[1])


def dog_sleep(cv, t, facing_left=True):
    by = (0, 0, 1, 0)[t % 4]
    cv.blob(15, 23 + by, 9, 4, DOG)
    cv.blob(15, 21 + by, 6, 2, DOGD)
    cv.blob(6, 24 + by, 3.6, 3.2, DOG)
    cv.R(1, 25 + by, 3, 26 + by, CR)
    cv.P(1, 25 + by, K)
    cv.R(5, 22 + by, 8, 25 + by, DOGD[1])
    cv.P(4, 23 + by, K)
    cv.R(4, 27 + by, 9, 28, DOG[2])                                    # Vorderpfoten
    cv.line(23, 23 + by, 26, 26 + by, DOG[1], 2)                       # Schwanz um den Koerper
    cv.R(20, 28, 24, 28, DOG[2])
    if t % 4 in (2, 3):
        cv.P(9, 18 + by, ST)
        cv.P(10, 16 + by, ST)


# ============================================================================ HUHN
HEN = (SAND, W3, W2)                       # braunes Huhn: Licht, Grund, Schatten
HEND = (W2, W1, HR)
COMB = (ROSE, RD, '#8a1f3d')


def hen_legs(cv, phase, side, by):
    for i, x in ((0, 14), (1, 17)):
        fo, lf = gait(phase, 0 if i == 0 else 1, 2.5 if side else 0, 2)
        x0 = x + int(round(fo))
        cv.R(x0, 24 + by, x0, 27 - lf, '#b89a72')
        cv.R(x0 - 1, 27 - lf, x0 + 1, 27 - lf, '#b89a72')
        cv.P(x0 + (-2 if side else 0), 27 - lf, '#b89a72')


def hen_side(cv, phase, t, mode='walk', head='side'):
    by = 0
    bob = {'walk': (0, 1, 0, 1), 'idle': (0, 0, 1, 0), 'peck': (0, 0, 0, 0)}[mode][t % 4]
    hen_legs(cv, phase, True, 0)
    # Schwanzfedern
    cv.blob(22, 17, 3, 5, HEND)
    cv.R(22, 11, 24, 15, HEND[2])
    cv.P(24, 11, HEND[0])
    cv.blob(15, 20, 7, 5.2, HEN)
    cv.blob(16, 21, 4, 2.5, HEND)                                      # Fluegel
    cv.R(15, 22, 18, 22, HEND[2])
    # Hals und Kopf
    peck = (0, 3, 6, 3)[t % 4] if mode == 'peck' else 0
    jerk = (0, 1, 0, -1)[t % 4] if mode in ('walk', 'idle') else 0
    hx, hy = 8 + jerk - peck // 3, 13 + peck + (bob if mode != 'peck' else 0)
    cv.line(10, 17, hx + 1, hy + 2, HEN[1], 3)
    cv.blob(hx, hy, 2.8, 2.8, (CR, SAND, W3))
    cv.R(hx - 4, hy, hx - 2, hy + 1, YEL)                              # Schnabel
    cv.P(hx - 4, hy, ORA)
    cv.P(hx - 1, hy - 1, K)
    cv.R(hx - 1, hy - 4, hx + 2, hy - 3, COMB[1])                      # Kamm
    cv.P(hx, hy - 5, COMB[0])
    cv.P(hx + 1, hy - 5, COMB[1])
    cv.R(hx - 3, hy + 2, hx - 2, hy + 3, COMB[1])                      # Kehllappen


def hen_front(cv, phase, t, mode='walk'):
    hen_legs(cv, phase, False, 0)
    cv.blob(16, 20, 6.5, 5.5, HEN)
    cv.R(14, 20, 18, 24, CR)
    peck = (0, 3, 6, 3)[t % 4] if mode == 'peck' else 0
    hy = 12 + peck // 2
    cv.blob(16, hy, 3, 3, (CR, SAND, W3))
    cv.R(15, hy + 1, 16, hy + 2, YEL)
    cv.P(14, hy - 1, K)
    cv.P(17, hy - 1, K)
    cv.R(15, hy - 4, 17, hy - 3, COMB[1])
    cv.P(16, hy - 5, COMB[0])
    cv.R(15, hy + 3, 16, hy + 4, COMB[1])


def hen_back(cv, phase, t, mode='walk'):
    hen_legs(cv, phase, False, 0)
    cv.blob(16, 21, 6.5, 5.5, HEN)
    cv.blob(16, 14, 4.5, 6, HEND)                                      # Schwanzfedern
    cv.R(14, 8, 18, 10, HEND[2])
    cv.P(16, 8, HEND[0])
    peck = (0, 3, 6, 3)[t % 4] if mode == 'peck' else 0
    cv.blob(16, 14 + peck // 2, 2.5, 2.5, HEND)
    cv.R(15, 10 + peck // 2, 17, 11 + peck // 2, COMB[1])


# ============================================================================ PFERD
HORSE = ('#9c7a5a', '#7a5a43', '#5c4033')   # Braune: Licht, Grund, Schatten
HORSED = ('#5c4033', '#3b2a22', '#2b2140')   # Maehne, Schweif, Beine unten


def horse_leg(cv, x, y0, y1, fo, lf, dark):
    """Gegliedertes Pferdebein: Oberschenkel breit, Fesselgelenk, Huf."""
    pal = HORSE if not dark else (HORSE[2], HORSE[2], HORSED[0])
    n = y1 - y0
    for y in range(y0, y1 - lf + 1):
        u = (y - y0) / max(1.0, float(n))
        w = 4 if u < 0.45 else 3
        xo = x + int(round(fo * u))
        kb = -1 if (u > 0.4 and u < 0.7 and lf) else 0
        cv.R(xo + kb, y, xo + w - 1 + kb, y, pal[1])
        cv.P(xo + kb, y, pal[0] if not dark else pal[1])
        if u > 0.55:
            cv.R(xo + kb, y, xo + w - 1 + kb, y, HORSED[0] if not dark else HORSED[1])
    xo = x + int(round(fo))
    cv.R(xo - 1, y1 - lf, xo + 3, y1 - lf, K2)                          # Huf


def horse_head_side(cv, px, py):
    """Pferdekopf von der Seite (Schnauze links): haengt vom Genick (px,py) nach vorn unten, etwa 50 Grad."""
    mx, my = px - 9, py + 10                                             # Maulspitze
    cv.line(px, py, mx, my, HORSE[1], 6)
    cv.blob(px - 4, py + 4, 4.2, 3.6, HORSE)                             # Backe
    cv.blob(mx, my, 3.3, 3.0, HORSE)                                     # Maul
    cv.R(mx - 3, my + 1, mx - 1, my + 3, HORSED[1])                      # Maul dunkel
    cv.P(mx - 1, my - 1, K2)                                             # Nuestern
    cv.P(px - 3, py + 2, K)                                              # Auge
    cv.P(px - 4, py + 2, CR)
    cv.line(px - 2, py - 1, mx + 1, my - 3, CR, 1)                       # Blesse
    cv.R(px + 1, py - 5, px + 3, py - 1, HORSE[1])                       # Ohr
    cv.P(px + 2, py - 6, HORSED[1])
    cv.line(px + 3, py, px + 9, py + 10, HORSED[1], 2)                   # Maehne entlang des Halses


def horse_side(cv, phase, bob, t, mode='walk', head='side', graze=False):
    by = bob
    for i, x in ((1, 15), (3, 42)):
        fo, lf = gait(phase, i, 5, 3)
        horse_leg(cv, x, 40 + by, 59, fo, lf, True)
    cv.blob(30, 34 + by, 18, 8.5, HORSE)
    cv.blob(30, 40 + by, 14, 3, (HORSE[1], HORSE[2], HORSED[1]))        # Bauch
    for i, x in ((0, 18), (2, 45)):
        fo, lf = gait(phase, i, 5, 3)
        horse_leg(cv, x, 40 + by, 59, fo, lf, False)
    # Hals: vom Widerrist nach vorn oben, Kopf haengt am Genick
    down = 11 if graze else 0
    px, py = 14 - (4 if graze else 0), 14 + by + down
    cv.line(21, 30 + by, px + 2, py + 3, HORSE[1], 9)
    # Schweif
    sw = (0, 1, 2, 1)[t % 4]
    cv.line(47, 30 + by, 52 + sw, 40 + by, HORSED[1], 3)
    cv.line(52 + sw, 40 + by, 51 + sw, 50 + by, HORSED[1], 2)
    if head == 'side':
        horse_head_side(cv, px, py)
    elif head == 'front':
        horse_head_front(cv, px - 4, py + 6)
    else:
        cv.blob(px - 3, py + 5, 4, 5, HORSE)
        cv.R(px - 5, py - 1, px - 3, py + 2, HORSE[1])


def horse_head_front(cv, cx, cy, down=0):
    cv.blob(cx, cy, 4, 6, HORSE)
    cv.R(cx - 1, cy - 5, cx, cy + 3, CR)
    cv.R(cx - 2, cy + 3, cx + 2, cy + 6, HORSED[1])
    cv.P(cx - 1, cy + 4, K2)
    cv.P(cx + 1, cy + 4, K2)
    cv.P(cx - 3, cy - 1, K)
    cv.P(cx + 3, cy - 1, K)
    cv.R(cx - 4, cy - 8, cx - 3, cy - 5, HORSE[1])
    cv.R(cx + 3, cy - 8, cx + 4, cy - 5, HORSE[1])


def horse_front(cv, phase, bob, t, mode='walk', graze=False):
    by = bob
    for i, x in ((0, 24), (1, 36)):
        fo, lf = gait(phase, 0 if i == 0 else 1, 0, 3)
        horse_leg(cv, x, 40 + by, 59, 0, lf, False)
    cv.blob(32, 33 + by, 12, 10, HORSE)
    cv.R(26, 30 + by, 38, 45 + by, HORSE[1])
    cv.line(32, 30 + by, 32, 18 + by, HORSE[1], 9)
    cv.line(32, 26 + by, 32, 14 + by, HORSED[1], 3)
    horse_head_front(cv, 32, 14 + by + (10 if graze else 0))


def horse_back(cv, phase, bob, t, mode='walk', graze=False):
    by = bob
    for i, x in ((2, 24), (3, 36)):
        fo, lf = gait(phase, 3 if i == 2 else 2, 0, 3)
        horse_leg(cv, x, 40 + by, 59, 0, lf, False)
    cv.blob(32, 33 + by, 13, 10, HORSE)
    sw = (0, 1, 0, -1)[t % 4]
    cv.line(32, 26 + by, 32 + sw, 50 + by, HORSED[1], 5)
    cv.R(30 + sw, 48 + by, 34 + sw, 52 + by, HORSED[0])
    cv.blob(32, 20 + by, 5, 6, HORSE)
    cv.R(28, 12 + by, 29, 16 + by, HORSE[1])
    cv.R(35, 12 + by, 36, 16 + by, HORSE[1])


# ============================================================================ Zusammenbau
IDLE_BOB = (0, 0, 1, 0)
WALK_BOB = (0, 1, 0, 1)


def draw(species, view, mode, frame):
    real = MIRROR.get(view, view)
    t = frame
    phase = frame / 4.0 if mode == 'walk' else None
    cv = Cv(64 if species == 'Pferd' else 32)
    bob = (WALK_BOB if mode == 'walk' else IDLE_BOB)[frame % 4]
    if species == 'Hund':
        if mode == 'sleep':
            dog_sleep(cv, t)
        elif real in ('W', 'SW', 'NW'):
            dog_side(cv, phase, bob, t, 'idle' if mode != 'walk' else 'walk', {'W': 'side', 'SW': 'front', 'NW': 'back'}[real])
        elif real == 'S':
            dog_front(cv, phase, bob, t, mode)
        else:
            dog_back(cv, phase, bob, t, mode)
    elif species == 'Huhn':
        if real in ('W', 'SW', 'NW'):
            hen_side(cv, phase, t, mode, 'side')
        elif real == 'S':
            hen_front(cv, phase, t, mode)
        else:
            hen_back(cv, phase, t, mode)
    else:
        graze = mode == 'graze'
        if real in ('W', 'SW', 'NW'):
            horse_side(cv, phase, bob, t, mode, {'W': 'side', 'SW': 'side', 'NW': 'back'}[real], graze)
        elif real == 'S':
            horse_front(cv, phase, bob, t, mode, graze)
        else:
            horse_back(cv, phase, bob, t, mode, graze)
    buf = outline(cv)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return to_img(buf, cv.n), cv.n


ACTIONS = {'Hund': 'sleep', 'Huhn': 'peck', 'Pferd': 'graze'}


def build(species, outdir):
    os.makedirs(outdir, exist_ok=True)
    n = 64 if species == 'Pferd' else 32
    low = species.lower()
    sheets = {}
    for mode in ('idle', 'walk', ACTIONS[species]):
        rows = 2 if mode == 'sleep' else 8
        sh = Image.new('RGBA', (4 * n, rows * n))
        for r in range(rows):
            view = ORDER[r] if mode != 'sleep' else ('W', 'E')[r]
            for f in range(4):
                im, _ = draw(species, view, mode, f)
                sh.paste(im, (f * n, r * n))
        sh.save(os.path.join(outdir, '%s_%s_sheet.png' % (low, mode)))
        sheets[mode] = sh
    stand = Image.new('RGBA', (8 * n, n))
    for r, v in enumerate(ORDER):
        stand.paste(draw(species, v, 'idle', 0)[0], (r * n, 0))
    stand.save(os.path.join(outdir, low + '_stand_8dir.png'))
    return stand, sheets


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..')
    S = 3
    prev = []
    for sp in ('Hund', 'Huhn', 'Pferd'):
        st, shs = build(sp, os.path.join(base, sp))
        prev.append((sp, st, shs))
        print('ok', sp)
    W = max(st.width for _, st, _ in prev) * S + 20
    H = sum((st.height + shs['walk'].height // 4 + 4) * S for _, st, shs in prev) + 40
    sh = Image.new('RGBA', (W, H), (74, 94, 74, 255))
    y = 10
    for sp, st, shs in prev:
        sh.alpha_composite(st.resize((st.width * S, st.height * S), Image.NEAREST), (10, y))
        y += st.height * S + 4
        walk = shs['walk']
        n = walk.width // 4
        strip = walk.crop((0, 2 * n, walk.width, 3 * n))
        sh.alpha_composite(strip.resize((strip.width * S, strip.height * S), Image.NEAREST), (10, y))
        y += n * S + 8
    sh.crop((0, 0, W, y + 10)).save(os.path.join(HERE, 'Vorschau_Tiere.png'))
