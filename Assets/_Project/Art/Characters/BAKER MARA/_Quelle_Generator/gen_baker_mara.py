"""Baker Mara: Idle (6), Walk (8), Run (8) und Bake (8, Teig kneten an einer unsichtbaren Theke) in 8 Richtungen, 56x56-Raster.

Gleiches Raster, gleiche Zeilenreihenfolge (S, SW, W, NW, N, NE, E, SE) und gleiche Beinmechanik wie Hauptfiguren und Doctor Veronica
(gen_doctor_veronica.py wird als Bibliothek genutzt). Nur Hex-Werte der Nightward-Palette.
Aussehen laut NPC-Doku: blonde Haare mit warmgelben Lichtern, rotes Tuch im Haar (Erkennungszeichen), ehemaliges Model.
Figur: Sanduhr mit schmaler Taille, Oberteil mit tiefem V-Ausschnitt, Schuerze, enge Hose, lange Haare.
NE/E/SE sind gespiegelte NW/W/SW.

Aufruf:  python gen_baker_mara.py [Ausgabeordner]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'DOCTOR VERONICA', '_Quelle_Generator'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'Hauptfiguren', '_Quelle_Generator'))

from PIL import Image  # noqa: E402

import gen_doctor_veronica as V  # noqa: E402
from gen_hauptfiguren import CELL, ORDER, MIRROR, K, K2, SM, SL, SD, rnd, outline, to_img  # noqa: E402

Cv = V.Cv
legs_pose = V.legs_pose
limb = V.limb

# ---------------------------------------------------------------- Farben
TOP = ('#6b7fb8', '#3a4a7a', '#2c3e56', '#1f2a3d')   # Oberteil: Licht, Grund, Schatten, tief
AP = ('#7a5a43', '#5c4033', '#3b2a22')               # Schuerze (Holz): Grund, Schatten, tief
APL = '#9c7a5a'                                      # Licht auf der Schuerze
HW, HY, HB, HS, HD = '#fff1c9', '#ffd27a', '#b89a72', '#9c7a5a', '#7a5a43'  # Blond: Glanz, warmgelbes Licht, Grund, Schatten, tief
SR, SRD = '#c4636b', '#7a2e3a'                       # rotes Tuch: Grund, Schatten
DOUGH = ('#fff1c9', '#b89a72', '#9c7a5a')            # Teig: Grund, Rand, Unterkante
FLOUR = '#e8e0f0'
GOLD = '#ffd27a'


def hair_x(cv, x, y, light):
    """Ein Haarpixel mit warmgelbem Licht je nach Muster."""
    cv.P(x, y, HY if light else HB)


# ---------------------------------------------------------------- Arme
def arm_front(cv, x1, x2, y_end, left):
    """Kurzarm-Oberteil, nackter Unterarm. y_end = letzte Armzeile (Hand folgt darunter)."""
    cv.R(x1, 19, x2, 20, TOP[1])
    cv.P(x2 if left else x1, 19, TOP[2])
    cv.P(x1 if left else x2, 19, TOP[0])
    for y in range(21, y_end + 1):
        cv.R(x1, y, x2, y, SL)
        cv.P(x2 if left else x1, y, SM)                  # Innenkante im Schatten


def hand(cv, x, y):
    cv.R(x, y, x + 1, y + 2, SL)
    cv.P(x, y, SM)
    cv.P(x, y + 1, SM)


# ---------------------------------------------------------------- Rumpf
def torso_front(cv):
    """Schmale Taille, grosse Brust (breiter als Schultern und Taille) mit tiefem V-Ausschnitt, Licht oben rechts."""
    t = TOP
    rows = {18: (17, 30), 19: (18, 29), 20: (17, 30), 21: (17, 30), 22: (17, 30), 23: (17, 30), 24: (18, 29),
            25: (20, 27), 26: (20, 27), 27: (20, 27), 28: (20, 27)}
    for y, (a, b) in rows.items():
        cv.R(a, y, b, y, t[1])
        cv.P(a, y, t[2])
        cv.P(b, y, t[0] if y < 24 else t[1])
    for x in list(range(18, 23)) + list(range(25, 30)):  # Unterkante der Brust
        cv.P(x, 24, t[2])
    for x in (20, 21, 26, 27):
        cv.P(x, 25, t[2])
    for p in ((18, 21), (19, 21), (19, 22), (20, 21), (21, 20), (26, 21), (28, 21), (28, 22), (27, 20), (29, 21)):
        cv.P(p[0], p[1], t[0])
    for p in ((17, 22), (17, 23), (30, 23)):
        cv.P(p[0], p[1], t[2])
    cv.P(22, 23, t[2])
    cv.P(25, 23, t[2])
    cv.R(23, 23, 24, 24, t[3])
    # Ausschnitt: Hals, V bis zur Brustmitte
    cv.R(22, 18, 25, 18, SM)
    cv.R(21, 19, 26, 19, SL)
    cv.P(21, 19, SM)
    cv.P(26, 19, SM)
    cv.R(22, 20, 25, 20, SL)
    cv.R(23, 21, 24, 21, SL)
    cv.R(23, 22, 24, 22, SM)
    cv.P(22, 20, SM)
    cv.P(25, 20, SM)


def apron_front(cv):
    """Halbschuerze ab der Taille, weitet sich zu den Hueften (Sanduhr), mit Bindeband und Tasche."""
    base, sh, dp = AP
    cv.R(19, 29, 28, 29, sh)                           # Bund
    cv.R(23, 29, 24, 29, dp)
    for y in range(30, 36):
        x1, x2 = (19, 28) if y < 32 else (17, 30)
        cv.R(x1, y, x2, y, base)
        cv.P(x1, y, sh)
        cv.P(x2, y, APL if y < 34 else base)
    cv.R(17, 36, 30, 36, sh)
    cv.R(18, 37, 29, 37, dp)
    cv.R(21, 32, 26, 35, sh)                           # Tasche
    cv.R(22, 33, 25, 35, base)
    for p in ((20, 31), (28, 34), (23, 36), (25, 30), (18, 33), (22, 34), (24, 33)):   # Mehlflecken
        cv.P(p[0], p[1], FLOUR)
    cv.P(18, 29, sh)                                   # Schleife seitlich
    cv.P(17, 30, base)
    cv.P(16, 31, sh)


def apron_side(cv):
    base, sh, dp = AP
    cv.R(20, 29, 28, 29, sh)
    for y in range(30, 36):
        x1, x2 = (20, 28) if y < 32 else (19, 30)
        cv.R(x1, y, x2, y, base)
        cv.P(x1, y, sh)
        cv.P(x2, y, sh)
        cv.P(27, y, APL if y < 34 else base)
    cv.R(19, 36, 30, 36, sh)
    cv.R(20, 37, 29, 37, dp)
    cv.R(21, 32, 25, 32, sh)
    cv.R(21, 32, 21, 34, sh)
    cv.R(21, 34, 25, 34, sh)
    for p in ((22, 31), (26, 34), (24, 35), (23, 33)):
        cv.P(p[0], p[1], FLOUR)
    cv.P(28, 29, dp)
    cv.P(29, 30, base)
    cv.P(30, 31, sh)


def apron_back(cv):
    base, sh, dp = AP
    cv.R(19, 29, 28, 29, sh)
    for y in range(30, 36):
        x1, x2 = (19, 28) if y < 32 else (17, 30)
        cv.R(x1, y, x2, y, base)
        cv.P(x1, y, sh)
        cv.P(x2, y, APL if y < 34 else base)
    cv.R(17, 36, 30, 36, sh)
    cv.R(18, 37, 29, 37, dp)
    # Schleife hinten mittig mit zwei Baendern
    cv.R(22, 28, 25, 29, sh)
    cv.P(23, 28, dp)
    cv.P(24, 28, dp)
    cv.P(21, 29, base)
    cv.P(26, 29, base)
    cv.P(22, 30, sh)
    cv.P(25, 30, sh)
    cv.P(22, 31, sh)
    cv.P(25, 31, sh)
    for p in ((21, 32), (27, 34), (23, 35), (20, 30), (18, 34)):
        cv.P(p[0], p[1], FLOUR)
    for y in range(32, 36):                            # Gesaessnaht
        cv.P(23, y, sh)
        cv.P(24, y, base)


# ---------------------------------------------------------------- Haare, Tuch, Kopf
def scarf_knot_front(cv, right=True):
    """Knoten oben rechts mit zwei herabhaengenden Enden."""
    xs = (28, 29, 30)
    cv.R(28, 6, 30, 8, SR)
    cv.P(30, 6, SRD)
    cv.P(28, 8, SRD)
    cv.P(29, 7, SRD)
    cv.P(28, 6, HW)
    # Enden
    for i, y in enumerate(range(9, 14)):
        cv.P(29, y, SR if i % 2 == 0 else SRD)
    for i, y in enumerate(range(9, 12)):
        cv.P(30, y, SRD if i % 2 == 0 else SR)
    cv.P(29, 14, SRD)


def head_front(cv, turn, down=0, sway=0):
    sx = -1 if turn else 0
    # Haarschopf ueber dem Tuch
    cv.R(21, 3, 26, 3, HB)
    cv.R(20, 4, 27, 4, HB)
    cv.R(19, 5, 28, 6, HB)
    for p in ((22, 3), (23, 3), (21, 4), (24, 4), (25, 5), (20, 5), (22, 5)):
        cv.P(p[0], p[1], HY)
    for p in ((22, 4), (27, 5), (26, 6)):
        cv.P(p[0], p[1], HW if p[0] == 22 else HS)
    # Tuch quer ueber die Stirn
    cv.R(19, 7, 28, 8, SR)
    cv.R(18, 9, 29, 9, SRD)
    cv.P(21, 7, HW)
    cv.P(22, 7, HW)
    for x in (19, 22, 25, 28):
        cv.P(x, 8, SRD)
    # Gesicht
    cv.R(20, 10, 27, 15, SL)
    cv.R(21, 16, 26, 16, SL)
    cv.R(22, 17, 25, 17, SM)
    for y in range(10, 16):
        cv.P(20, y, SM)
    cv.R(21, 16, 22, 16, SM)
    # Ponyfransen und Seitenhaar
    cv.R(20, 10, 24, 10, HB)
    cv.R(20, 11, 21, 11, HB)
    cv.P(22, 10, HY)
    cv.P(23, 10, HY)
    cv.R(19, 9, 19, 15, HB)
    cv.R(28, 9, 28, 15, HB)
    cv.P(19, 11, HY)
    cv.P(28, 12, HY)
    if turn:
        cv.R(26, 9, 28, 14, HB)
        cv.P(27, 11, HY)
        cv.P(19, 12, SL)
        cv.P(19, 13, SL)
    # Augen mit Wimpern, Nase, volle Lippen
    e = 12 + down
    cv.R(21 + sx, e, 22 + sx, e, K)
    cv.R(25 + sx, e, 26 + sx, e, K)
    cv.P(20 + sx, e - 1, K2)                           # Wimpernschwung aussen
    cv.P(27 + sx, e - 1, K2)
    cv.P(22 + sx, e - 1, K2)
    cv.P(25 + sx, e - 1, K2)
    cv.P(23 + sx, 13, SM)
    cv.P(24 + sx, 13, SM)
    cv.R(23 + sx, 14, 24 + sx, 14, SRD)
    cv.R(23 + sx, 15, 24 + sx, 15, SR)
    cv.P(23 + sx, 15, '#fff1c9')


def hair_front_long(cv, sway=0):
    """Lange Haare, schmal vorn ueber die Schultern fallend (Brust und Taille bleiben sichtbar)."""
    for y in range(11, 23):
        w = 2 if y < 20 else 1
        sw = sway if y >= 19 else 0
        cv.R(17 + sw, y, 17 + w + sw, y, HB) if False else None
        for i in range(w + 1):
            cv.P(17 + i + sw, y, HB)
            cv.P(30 - i + sw, y, HB)
        cv.P(17 + sw, y, HY if (y // 3) % 2 == 0 else HS)
        cv.P(30 + sw, y, HS if (y // 3) % 2 == 0 else HY)
    cv.P(17 + sway, 23, HS)
    cv.P(30 + sway, 23, HD)
    cv.P(18 + sway, 22, HD)
    cv.P(29 + sway, 22, HD)


def head_back(cv, turn, sway=0):
    cv.R(21, 3, 26, 3, HB)
    cv.R(20, 4, 27, 4, HB)
    cv.R(19, 5, 28, 6, HB)
    cv.R(19, 9, 28, 16, HB)
    cv.R(20, 16, 27, 17, HB)
    # Tuch quer, Knoten mittig mit Enden
    cv.R(19, 7, 28, 8, SR)
    cv.R(18, 9, 29, 9, SRD)
    cv.R(22, 5, 25, 7, SR)
    cv.P(22, 5, SRD)
    cv.P(25, 7, SRD)
    cv.P(23, 6, HW)
    for i, y in enumerate(range(10, 15)):
        cv.P(23, y, SR if i % 2 == 0 else SRD)
    for i, y in enumerate(range(10, 13)):
        cv.P(25, y, SRD if i % 2 == 0 else SR)
    for p in ((21, 4), (24, 3), (26, 5), (21, 11), (26, 12), (22, 14), (25, 16), (20, 13), (27, 15)):
        cv.P(p[0], p[1], HY)
    for p in ((23, 11), (27, 10), (21, 15), (24, 16)):
        cv.P(p[0], p[1], HS)
    if turn:
        cv.P(19, 11, SL)
        cv.P(19, 12, SL)
        cv.P(19, 13, SL)


def hair_back_long(cv, sway=0, turn=0):
    """Lange Haare ueber den Ruecken bis zu den Schulterblaettern, laufen nach unten spitz zu."""
    x1, x2 = (20, 28) if turn else (20, 27)
    for y in range(17, 27):
        t = (y - 17) / 9.0
        a = x1 + int(t * 1.5)
        b = x2 - int(t * 1.5)
        off = sway if y >= 22 else 0
        cv.R(a + off, y, b + off, y, HB)
        cv.P(a + off, y, HS)
        cv.P(b + off, y, HS if y > 20 else HB)
        for x in range(a + 1 + off, b + off):
            if x in (a + 2 + off, b - 2 + off) and (y // 3) % 2 == 0:
                cv.P(x, y, HY)                         # warmgelbe Straehne
            elif x == (a + b) // 2 + off and y % 2 == 0:
                cv.P(x, y, HS)
    cv.R(22 + sway, 27, 25 + sway, 27, HS)
    cv.R(23 + sway, 28, 24 + sway, 28, HD)


def head_side(cv, down=0, sway=0):
    """Profil nach links."""
    cv.R(21, 3, 26, 3, HB)
    cv.R(20, 4, 28, 4, HB)
    cv.R(20, 5, 29, 6, HB)
    for p in ((22, 3), (23, 3), (21, 4), (24, 5), (26, 4)):
        cv.P(p[0], p[1], HY)
    # Haare hinten, fallen ueber den Ruecken
    cv.R(24, 9, 29, 16, HB)
    for y in range(17, 26):
        t = (y - 17) / 8.0
        off = sway if y >= 21 else 0
        cv.R(25 + off, y, 29 - int(t) + off, y, HB)
        cv.P(25 + off, y, HS)
        cv.P(29 - int(t) + off, y, HD)
    for y in range(9, 25):
        if y % 3 == 0:
            cv.P(26, y, HY)
            cv.P(28, y + 1, HY)
        if y % 4 == 1:
            cv.P(27, y, HS)
    # Tuch quer ueber die Stirn, Knoten hinten
    cv.R(20, 7, 28, 8, SR)
    cv.R(19, 9, 25, 9, SRD)
    cv.P(22, 7, HW)
    cv.P(23, 7, HW)
    cv.R(28, 6, 30, 8, SR)
    cv.P(30, 6, SRD)
    cv.P(29, 7, SRD)
    for i, y in enumerate(range(9, 15)):
        cv.P(29, y, SR if i % 2 == 0 else SRD)
    for i, y in enumerate(range(9, 12)):
        cv.P(30, y, SRD if i % 2 == 0 else SR)
    # Gesicht
    cv.R(20, 10, 24, 15, SL)
    cv.R(19, 11, 19, 14, SL)
    cv.R(20, 16, 24, 16, SL)
    for y in range(10, 16):
        cv.P(24, y, SM)
    cv.R(20, 16, 22, 16, SM)
    cv.P(18, 12, SL)                                   # Nase
    cv.R(20, 10, 22, 10, HB)                           # Ponyfransen
    cv.P(21, 10, HY)
    e = 12 + down
    cv.P(21, e, K)
    cv.P(22, e, K)
    cv.P(20, e - 1, K2)
    cv.P(22, e - 1, K2)
    cv.P(19, 14, SRD)
    cv.P(20, 14, SR)
    cv.P(19, 15, SR)
    cv.P(20, 15, SR)
    cv.R(22, 17, 25, 17, SM)
    cv.R(22, 18, 24, 18, SM)


# ---------------------------------------------------------------- Oberkoerper je Ansicht
def upper_front(cv, swing, turn, run=False, down=0, sway=0, bake=None):
    sl, sr = swing, -swing
    if bake is not None:
        d, lift = bake
        # Arme: Oberarm senkrecht, Unterarm nach innen unten zum Teig
        limb(cv, [(16, 19), (16, 24), (21, 27 + d)], SL, SM, SL)
        limb(cv, [(31, 19), (31, 24), (26, 27 + d)], SL, SL, SM)
        cv.R(15, 19, 17, 20, TOP[1])
        cv.R(30, 19, 32, 20, TOP[1])
    elif run:
        ln = 5
        arm_front(cv, 15, 17, 19 + ln + sl * 2, True)
        hand(cv, 15, 20 + ln + sl * 2)
        arm_front(cv, 30, 32, 19 + ln + sr * 2, False)
        hand(cv, 31, 20 + ln + sr * 2)
    else:
        arm_front(cv, 15, 17, 25 + sl, True)
        hand(cv, 15, 26 + sl)
        arm_front(cv, 30, 32, 25 + sr, False)
        hand(cv, 31, 26 + sr)
    torso_front(cv)
    apron_front(cv)
    hair_front_long(cv, sway)
    if bake is not None:
        d, lift = bake
        bake_dough_front(cv, d)
    scarf_knot_front(cv)
    head_front(cv, turn, down, sway)


def bake_dough_front(cv, d):
    """Teigklumpen vor dem Bauch, wird beim Druecken breiter und flacher; Haende liegen oben auf."""
    w = (3, 4, 5)[d]
    h = (3, 3, 2)[d]
    x1, x2 = 24 - w, 23 + w
    y1 = 31 + (3 - h)
    cv.R(x1, y1, x2, y1 + h - 1, DOUGH[0])
    cv.R(x1, y1 + h - 1, x2, y1 + h - 1, DOUGH[1])
    cv.P(x1, y1, DOUGH[1])
    cv.P(x2, y1, DOUGH[1])
    cv.P(x1 + 1, y1, FLOUR)
    cv.P(x2 - 2, y1 + 1 if h > 2 else y1, DOUGH[1])
    hand(cv, 21, 28 + d)
    hand(cv, 25, 28 + d)


def upper_back(cv, swing, turn, run=False, sway=0, bake=None):
    sl, sr = swing, -swing
    if bake is not None:
        d, lift = bake
        arm_front(cv, 15, 17, 23 + d, True)
        arm_front(cv, 30, 32, 23 + d, False)
    elif run:
        ln = 5
        arm_front(cv, 15, 17, 19 + ln + sl * 2, True)
        hand(cv, 15, 20 + ln + sl * 2)
        arm_front(cv, 30, 32, 19 + ln + sr * 2, False)
        hand(cv, 31, 20 + ln + sr * 2)
    else:
        arm_front(cv, 15, 17, 25 + sl, True)
        hand(cv, 15, 26 + sl)
        arm_front(cv, 30, 32, 25 + sr, False)
        hand(cv, 31, 26 + sr)
    # Rumpf von hinten: Taille schmal, Brust nur seitlich angedeutet
    t = TOP
    rows = {18: (17, 30), 19: (18, 29), 20: (18, 29), 21: (18, 29), 22: (18, 29), 23: (18, 29), 24: (19, 28),
            25: (20, 27), 26: (20, 27), 27: (20, 27), 28: (20, 27)}
    for y, (a, b) in rows.items():
        cv.R(a, y, b, y, t[1])
        cv.P(a, y, t[2])
        cv.P(b, y, t[0] if y < 24 else t[1])
    for y in (21, 23, 25):                             # Schulterblatt-Falten
        cv.P(22, y, t[2])
        cv.P(25, y, t[2])
    cv.P(18, 21, t[0])
    cv.P(29, 21, t[0])
    cv.P(18, 24, t[2])
    cv.P(29, 24, t[2])
    cv.R(22, 18, 25, 18, SM)
    apron_back(cv)
    hair_back_long(cv, sway, turn)
    head_back(cv, turn, sway)


def upper_side(cv, swing_a, run=False, down=0, sway=0, bake=None):
    """Seitenansicht nach links (W)."""
    t = TOP
    end = 25 if run else 27
    lift = 0
    if bake is None:
        far_hx = 24 + rnd(-swing_a * (5 if run else 3))
        for y in range(19, end + 1):
            x = rnd(24 + (far_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, SM)
        cv.R(far_hx - 1, end, far_hx, end + 2, SM)
    else:
        d, lift = bake
        limb(cv, [(24, 19), (22, 23), (19, 26 + d)], SM, SM, SM)
        cv.R(17, 26 + d, 18, 28 + d, SM)
    # lange Haare hinter dem Koerper
    cv.R(25, 17, 29, 27, HB)
    # Rumpf: Brust vorn, schmale Taille
    for y in range(18, 28):
        if y <= 24:
            a, b = (18, 27) if 20 <= y <= 24 else (20, 27)
        else:
            a, b = 21, 26
        cv.R(a, y, b, y, t[1])
        cv.P(a, y, t[2] if y > 22 else t[0])
        cv.P(b, y, t[2])
    for p in ((19, 21), (19, 22), (20, 20), (20, 21)):
        cv.P(p[0], p[1], t[0])
    cv.R(18, 24, 21, 24, t[2])                         # Brustunterkante
    cv.R(19, 25, 20, 25, t[2])
    cv.R(21, 18, 26, 18, t[1])
    cv.P(25, 18, t[0])
    cv.R(22, 17, 25, 17, SM)
    cv.R(21, 19, 22, 19, SL)                           # Ausschnitt seitlich
    apron_side(cv)
    # naher Arm
    if bake is None:
        near_hx = 24 + rnd(swing_a * (5 if run else 3))
        cv.R(near_hx - 1, 19, near_hx + 1, 20, t[1])
        for y in range(21, end + 1):
            x = rnd(24 + (near_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, SL)
            cv.P(x + 1, y, SM)
        cv.R(near_hx - 1, end, near_hx, end + 2, SL)
        cv.P(near_hx - 1, end, SM)
    else:
        d, lift = bake
        limb(cv, [(24, 19), (23, 23), (20, 25 + d)], SL, SM, SL)
        cv.R(23, 19, 25, 20, t[1])
        cv.R(17, 25 + d, 19, 27 + d, SL)
        cv.P(17, 25 + d, SM)
        bake_dough_side(cv, d)
    head_side(cv, down, sway)


def bake_dough_side(cv, d):
    w = (3, 4, 5)[d]
    h = (3, 3, 2)[d]
    x2 = 17
    x1 = x2 - w
    y1 = 28 + d + (3 - h)
    cv.R(x1, y1, x2, y1 + h - 1, DOUGH[0])
    cv.R(x1, y1 + h - 1, x2, y1 + h - 1, DOUGH[1])
    cv.P(x1, y1, DOUGH[1])
    cv.P(x1 + 1, y1, FLOUR)


# ---------------------------------------------------------------- Zusammenbau
def render(view, phase, bob, mode, bake=None):
    """mode: idle, walk, run, bake. Ein Frame als Pixel-Raster."""
    real = MIRROR.get(view, view)
    cv = Cv()
    run = mode == 'run'
    if run:
        legs_pose(cv, real, phase, ampx=7.0, ampy=2.2, lift_h=3.6)
    else:
        legs_pose(cv, real, phase)
    cv.dy = bob
    swing = 0 if phase is None else math.sin(2 * math.pi * phase)
    sway = 0 if phase is None else rnd(math.cos(2 * math.pi * phase) * (1.0 if run else 0.7))
    if run:
        swing = 1.0 if swing > 0.35 else (-1.0 if swing < -0.35 else 0.0)
        if real in ('W', 'SW'):
            cv.dx = -1
    if real == 'W':
        upper_side(cv, swing, run, 0, sway, bake)
    elif real in ('S', 'SW'):
        upper_front(cv, rnd(swing), 1 if real == 'SW' else 0, run, 0, sway, bake)
    else:
        upper_back(cv, rnd(swing), 1 if real == 'NW' else 0, run, sway, bake)
    buf = outline(cv.b)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return buf


IDLE_BOB = [0, 0, 0, 1, 1, 0]
WALK_BOB = [0, 1, 1, 0, 0, 1, 1, 0]
RUN_BOB = [0, 2, 1, 0, 0, 2, 1, 0]
BAKE_D = [0, 1, 2, 1, 0, 1, 2, 1]          # Druecktiefe der Haende
BAKE_BOB = [0, 0, 1, 0, 0, 0, 1, 0]


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    stand = Image.new('RGBA', (8 * CELL, CELL))
    idle = Image.new('RGBA', (6 * CELL, 8 * CELL))
    walk = Image.new('RGBA', (8 * CELL, 8 * CELL))
    run = Image.new('RGBA', (8 * CELL, 8 * CELL))
    bake = Image.new('RGBA', (8 * CELL, 8 * CELL))
    for r, v in enumerate(ORDER):
        stand.paste(to_img(render(v, None, 0, 'idle')), (r * CELL, 0))
        for c, b in enumerate(IDLE_BOB):
            idle.paste(to_img(render(v, None, b, 'idle')), (c * CELL, r * CELL))
        for c, b in enumerate(WALK_BOB):
            walk.paste(to_img(render(v, c / 8.0, b, 'walk')), (c * CELL, r * CELL))
        for c, b in enumerate(RUN_BOB):
            run.paste(to_img(render(v, c / 8.0, b, 'run')), (c * CELL, r * CELL))
        for c in range(8):
            bake.paste(to_img(render(v, None, BAKE_BOB[c], 'bake', bake=(BAKE_D[c], 0))), (c * CELL, r * CELL))
    stand.save(os.path.join(outdir, 'baker_mara_stand_8dir.png'))
    idle.save(os.path.join(outdir, 'baker_mara_idle_sheet.png'))
    walk.save(os.path.join(outdir, 'baker_mara_walk_sheet.png'))
    run.save(os.path.join(outdir, 'baker_mara_run_sheet.png'))
    bake.save(os.path.join(outdir, 'baker_mara_bake_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'ANIMATIONS_8DIR')
    build(out)
    print('ok', os.path.abspath(out))
