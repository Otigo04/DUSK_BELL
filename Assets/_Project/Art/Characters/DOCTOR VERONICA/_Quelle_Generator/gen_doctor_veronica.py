"""Doctor Veronica: Idle (6), Walk (8), Run (8) in 8 Richtungen und Treat (6) im 56x56-Raster.

Gleiches Raster, gleiche Zeilenreihenfolge (S, SW, W, NW, N, NE, E, SE) und gleiche Beinmechanik wie die
Hauptfiguren (gen_hauptfiguren.py wird als Bibliothek genutzt). Nur Hex-Werte der Nightward-Palette.
Aussehen laut NPC-Doku: grauer Dutt, Strickjacke ueber weissem Kittel, Schluesselbund am Guertel.
NE/E/SE sind gespiegelte NW/W/SW (alle Anbauteile sitzen mittig).

Aufruf:  python gen_doctor_veronica.py [Ausgabeordner]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'Hauptfiguren', '_Quelle_Generator'))

from PIL import Image  # noqa: E402

import gen_hauptfiguren as G  # noqa: E402
from gen_hauptfiguren import CELL, OX, OY, ORDER, MIRROR, VIEWS, K, K2, SM, SL, SD, rnd, outline, to_img, leg  # noqa: E402

# ---------------------------------------------------------------- Farben
KW = ('#e8e0f0', '#9a95a0', '#6b5a7a')            # Kittel: Grund, Schatten, tief
KWL = '#fff1c9'                                    # Kittel: warmes Licht
CG = ('#b89a72', '#9c7a5a', '#7a5a43', '#5c4033')  # Strickjacke: Licht, Grund, Schatten, tief
HA = ('#e8e0f0', '#9a95a0', '#6e6a74', '#4a4550')  # graues Haar: Licht, Grund, Schatten, tief
BRASS, BRASS2 = '#ffd27a', '#ffa550'
RING, RING2 = '#9a95a0', '#6e6a74'
LIP = '#8c5f4d'


class Cv(G.Cv):
    def __init__(s):
        super().__init__()
        s.dx = 0

    def P(s, x, y, c):
        X, Y = int(x) + OX + s.dx, int(y) + OY + s.dy
        if 0 <= X < CELL and 0 <= Y < CELL:
            s.b[Y][X] = c


# ---------------------------------------------------------------- Beine (wie Hauptfiguren, Schrittweite einstellbar)
def legs_pose(cv, view, phase, ampx=5.0, ampy=1.4, lift_h=2.4):
    fx, fy = VIEWS[view]
    side = abs(fx) == 1
    idle = phase is None
    specs = []
    for idx, off in enumerate((0.0, 0.5)):
        if idle:
            s_, c_ = 0.0, 0.0
        else:
            s_ = math.sin(2 * math.pi * (phase + off))
            c_ = math.cos(2 * math.pi * (phase + off))
        lift = 0 if idle else max(0.0, c_) * lift_h
        if side:
            sgn = 1 if fx > 0 else -1
            hx, w, dark = 23.5, 5, idx == 1
            ax = hx + s_ * ampx * sgn
            kb = sgn * (0.7 + lift * 0.4)
            ay = 42 - rnd(lift)
            toe = sgn
            depth = 0 if idx == 0 else -1
        else:
            hx = 21.0 if idx == 0 else 26.0
            w, dark, toe, kb = 4, False, 0, 0.0
            ax = hx + s_ * ampx * fx * 0.7
            ay = 42 + rnd(s_ * ampy * fy) - rnd(lift * 0.8)
            depth = s_ * fy
        specs.append((depth, dict(hx=hx, hy=33, ax=ax, ay=ay, w=w, kb=kb, dark=dark, toe=toe)))
    specs.sort(key=lambda t: t[0])
    for _, sp in specs:
        leg(cv, sp['hx'], sp['hy'], sp['ax'], sp['ay'], sp['w'], sp['kb'], sp['dark'], sp['toe'])
    x1, x2 = (20, 27) if side else (19, 28)
    cv.R(x1, 29, x2, 34, G.B2)
    for y in range(29, 35):
        cv.P(x1, y, G.B1)
        cv.P(x2, y, G.B3)


# ---------------------------------------------------------------- Kittel (Saum ueber den Oberschenkeln)
def coat_hem_front(cv, swing=0):
    """Weisser Kittel ab Taille bis knapp ueber das Knie, leicht ausgestellt, mit Mittelnaht, Taschen, Knoepfen."""
    base, sh, dp = KW
    for y in range(29, 35):
        flare = 1 if y >= 33 else 0
        x1, x2 = 19 - flare, 28 + flare
        cv.R(x1, y, x2, y, base)
        cv.P(x1, y, sh)
        cv.P(x2, y, KWL if y < 32 else base)
    cv.R(18, 35, 29, 35, sh)                          # Saumschatten
    cv.R(18, 36, 29, 36, dp)
    for y in range(29, 36):                           # Mittelnaht und Knoepfe
        cv.P(23, y, sh)
        cv.P(24, y, base)
    for y in (30, 33):
        cv.P(23, y, dp)
    cv.R(25, 32, 27, 32, sh)                          # Tasche rechts (vom Betrachter)


def coat_hem_side(cv):
    base, sh, dp = KW
    for y in range(29, 35):
        flare = 1 if y >= 33 else 0
        cv.R(20 - flare, y, 27 + flare, y, base)
        cv.P(20 - flare, y, sh)
        cv.P(27 + flare, y, sh)
        cv.P(26, y, KWL if y < 32 else base)
    cv.R(19, 35, 28, 35, sh)
    cv.R(19, 36, 28, 36, dp)
    cv.R(22, 32, 25, 32, sh)                          # Tasche


def keys_front(cv, side_sign=-1):
    """Schluesselbund am Kittel, links vom Betrachter (Hueftseite): Ring mit Loch, zwei Messingschluessel."""
    x = 20 if side_sign < 0 else 26
    cv.R(x, 31, x + 2, 31, RING)
    cv.P(x, 32, RING2)
    cv.P(x + 2, 32, RING2)
    cv.P(x, 33, BRASS)
    cv.P(x, 34, BRASS)
    cv.P(x, 35, BRASS2)
    cv.P(x + 1, 35, BRASS2)
    cv.P(x + 2, 33, BRASS2)
    cv.P(x + 2, 34, BRASS)
    cv.P(x + 2, 35, BRASS)


def keys_side(cv):
    cv.R(19, 31, 20, 31, RING)
    cv.P(19, 32, RING2)
    cv.P(18, 33, BRASS)
    cv.P(19, 33, BRASS)
    cv.P(18, 34, BRASS2)
    cv.P(19, 34, BRASS)
    cv.P(19, 35, BRASS2)
    cv.P(20, 33, BRASS2)


# ---------------------------------------------------------------- Haare
def bun(cv, x, y):
    """Dutt, 4 Pixel breit, Licht oben rechts, Schatten unten links."""
    hl, base, sh, dp = HA
    cv.R(x + 1, y, x + 2, y, base)
    cv.R(x, y + 1, x + 3, y + 2, base)
    cv.R(x + 1, y + 3, x + 2, y + 3, sh)
    cv.P(x + 2, y, hl)
    cv.P(x + 3, y + 1, hl)
    cv.P(x, y + 2, sh)
    cv.P(x + 1, y + 2, sh)
    cv.P(x + 3, y + 2, sh)
    cv.P(x + 1, y + 1, sh)


def hand(cv, x, y):
    cv.R(x, y, x + 1, y + 2, SL)
    cv.P(x, y, SM)
    cv.P(x, y + 1, SM)


# ---------------------------------------------------------------- Kopf
def head_front(cv, turn, down=0):
    hl, hb, hs, hd = HA
    sx = -1 if turn else 0
    # Dutt
    bun(cv, 23 if turn else 22, 2)
    # Haarkappe
    cv.R(21, 6, 26, 6, hb)
    cv.R(20, 7, 27, 7, hb)
    cv.R(19, 8, 28, 8, hb)
    cv.R(19, 9, 20, 9, hb)
    cv.R(27, 9, 28, 9, hb)
    for p in ((22, 6), (23, 6), (21, 7), (25, 7), (26, 7)):
        cv.P(p[0], p[1], hl)
    for p in ((20, 8), (27, 8), (24, 7)):
        cv.P(p[0], p[1], hs)
    # Gesicht
    cv.R(21, 9, 26, 9, SL)
    cv.R(20, 10, 27, 15, SL)
    cv.R(21, 16, 26, 16, SL)
    cv.R(22, 17, 25, 17, SM)
    for y in range(10, 16):
        cv.P(20, y, SM)
    cv.R(21, 16, 22, 16, SM)
    # Haar seitlich ueber den Ohren
    cv.R(19, 10, 19, 13, hb)
    cv.R(28, 10, 28, 13, hb)
    cv.P(19, 12, hs)
    cv.P(28, 12, hs)
    cv.P(19, 11, hl)
    if turn:
        cv.R(26, 8, 28, 13, hb)
        cv.R(26, 9, 26, 11, hs)
        cv.P(27, 8, hl)
        cv.P(19, 12, SL)
        cv.P(19, 11, SL)
        cv.P(19, 13, SL)
    # Augenbrauen, Augen (bei Treat nach unten), Nase, Mund
    e = 11 + down
    cv.R(21 + sx, e - 1, 22 + sx, e - 1, SM)          # Brauen in Hautschatten: weicher Blick
    cv.R(25 + sx, e - 1, 26 + sx, e - 1, SM)
    cv.R(21 + sx, e, 22 + sx, e, K)
    cv.R(25 + sx, e, 26 + sx, e, K)
    cv.P(23 + sx, 13, SM)
    cv.P(24 + sx, 13, SM)
    cv.R(23 + sx, 14, 24 + sx, 14, LIP)
    cv.P(22 + sx, 13, SD)                             # Lachfalte, ruhige Ausstrahlung
    cv.P(25 + sx, 13, SD)
    cv.P(20 + sx, 14, SM)


def head_back(cv, turn):
    hl, hb, hs, hd = HA
    bun(cv, 23 if turn else 22, 2)
    cv.R(21, 6, 26, 6, hb)
    cv.R(20, 7, 27, 7, hb)
    cv.R(19, 8, 28, 15, hb)
    cv.R(20, 16, 27, 16, hb)
    cv.R(21, 17, 26, 17, hs)
    for p in ((22, 6), (23, 6), (21, 7), (25, 7), (26, 7)):
        cv.P(p[0], p[1], hl)
    for y in range(9, 15):                            # Straehnen nach hinten gekaemmt
        cv.P(22, y, hl if y < 12 else hb)
        cv.P(25, y, hs)
    for y in range(8, 16):
        cv.P(20, y, hs)
        cv.P(27, y, hs)
    cv.P(23, 15, hs)
    cv.P(24, 15, hs)
    cv.R(22, 17, 25, 18, SM)
    cv.R(22, 16, 25, 16, hs)
    if turn:
        cv.P(19, 11, SL)
        cv.P(19, 12, SL)
        cv.P(19, 13, SL)


def head_side(cv, down=0):
    """Profil nach links."""
    hl, hb, hs, hd = HA
    # Dutt hinten oben (rechts)
    bun(cv, 26, 3)
    cv.R(21, 6, 27, 6, hb)
    cv.R(20, 7, 28, 7, hb)
    cv.R(24, 8, 28, 15, hb)
    cv.R(20, 8, 23, 8, hb)
    for p in ((22, 6), (23, 6), (21, 7), (26, 7)):
        cv.P(p[0], p[1], hl)
    for y in range(9, 15):
        cv.P(25, y, hl if y < 12 else hb)
        cv.P(27, y, hs)
    cv.P(24, 8, hs)
    cv.P(28, 8, hs)
    # Gesicht
    cv.R(20, 9, 23, 9, SL)
    cv.R(20, 10, 24, 15, SL)
    cv.R(19, 11, 19, 14, SL)
    cv.R(20, 16, 24, 16, SL)
    for y in range(10, 16):
        cv.P(24, y, SM)
    cv.R(20, 16, 22, 16, SM)
    cv.P(18, 12, SL)                                   # Nase
    cv.P(18, 13, SM)
    e = 11 + down
    cv.R(20, e - 1, 21, e - 1, hs)
    cv.P(21, e, K)
    cv.P(22, e, K)
    cv.P(19, 14, LIP)
    cv.P(20, 14, LIP)
    cv.P(21, 13, SD)
    cv.R(22, 17, 25, 17, SM)
    cv.R(22, 18, 24, 18, SM)


# ---------------------------------------------------------------- Oberkoerper
def limb(cv, pts, base, sh, hl):
    """Dicker Arm entlang eines Linienzugs (3 px breit bei steilen, 3 px hoch bei flachen Stuecken)."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        steep = abs(y1 - y0) >= abs(x1 - x0)
        for i in range(n + 1):
            x, y = rnd(x0 + (x1 - x0) * i / n), rnd(y0 + (y1 - y0) * i / n)
            if steep:
                cv.R(x - 1, y, x + 1, y, base)
                cv.P(x - 1, y, sh)
                cv.P(x + 1, y, hl)
            else:
                cv.R(x, y - 1, x, y + 1, base)
                cv.P(x, y - 1, hl)
                cv.P(x, y + 1, sh)


def sleeve_front(cv, x1, x2, y_end, hl_on_right):
    hl, base, sh, dk = CG
    cv.R(x1, 19, x2, y_end, base)
    for y in range(19, y_end + 1):
        cv.P(x1, y, hl if hl_on_right is False else sh)
        cv.P(x2, y, hl if hl_on_right else sh)
    cv.R(x1, y_end, x2, y_end, dk)                    # Strickbuendchen
    cv.R(x1, y_end - 1, x2, y_end - 1, sh)


def upper_front(cv, swing, turn, run=False, down=0):
    hl, base, sh, dk = CG
    kb, ks, kd = KW
    # Arme (Strickjackenaermel mit Kittelaermel-Rand), bei Run gebeugt und angehoben
    sl, sr = swing, -swing
    if run:
        ln = 5
        sleeve_front(cv, 16, 18, 19 + ln + sl * 2, False)
        hand(cv, 16, 20 + ln + sl * 2)
        if turn:
            sleeve_front(cv, 28, 30, 18 + ln + sr * 2, True)
            hand(cv, 29, 19 + ln + sr * 2)
        else:
            sleeve_front(cv, 29, 31, 19 + ln + sr * 2, True)
            hand(cv, 30, 20 + ln + sr * 2)
    else:
        sleeve_front(cv, 16, 18, 24 + sl, False)
        cv.R(16, 25 + sl, 18, 25 + sl, kb)            # Kittelmanschette
        cv.P(16, 25 + sl, ks)
        hand(cv, 16, 26 + sl)
        if turn:
            sleeve_front(cv, 28, 30, 23 + sr, True)
            cv.R(28, 24 + sr, 30, 24 + sr, kb)
            hand(cv, 29, 25 + sr)
        else:
            sleeve_front(cv, 29, 31, 24 + sr, True)
            cv.R(29, 25 + sr, 31, 25 + sr, kb)
            cv.P(31, 25 + sr, ks)
            hand(cv, 30, 26 + sr)
    # Kittel unten
    coat_hem_front(cv)
    # Strickjacke: offene Front, Kittel in der Mitte sichtbar
    cv.R(17, 18, 30, 18, base)
    cv.R(19, 19, 28, 28, base)
    for y in range(19, 29):
        cv.P(19, y, sh)
        cv.P(28, y, hl if y < 24 else base)
    cv.R(19, 28, 28, 28, sh)                          # Saum der Strickjacke
    cv.R(20, 29, 27, 29, dk)
    # Kittel-Streifen in der Mitte
    for y in range(19, 29):
        cv.R(22, y, 25, y, kb)
        cv.P(22, y, ks)
        cv.P(25, y, KWL if y < 22 else kb)
    cv.P(23, 24, ks)
    cv.P(24, 26, ks)
    # Strickmuster: senkrechte Rippen neben dem Kittelstreifen
    for y in range(20, 28, 2):
        cv.P(20, y, sh)
        cv.P(21, y + 1, sh)
        cv.P(27, y, sh)
        cv.P(26, y + 1, sh)
    # Schulterlicht
    for p in ((27, 18), (28, 18), (29, 18), (30, 19)):
        cv.P(p[0], p[1], hl)
    # Hals und Kragen
    cv.R(22, 18, 25, 18, SM)
    cv.R(23, 19, 24, 19, SM)
    cv.P(21, 18, kb)
    cv.P(26, 18, kb)
    cv.P(22, 19, ks)
    cv.P(25, 19, ks)
    keys_front(cv, -1)
    head_front(cv, turn, down)


def upper_back(cv, swing, turn, run=False, treat=None):
    hl, base, sh, dk = CG
    kb, ks, kd = KW
    sl, sr = swing, -swing
    if treat is not None:
        # Arme zeigen nach vorn: von hinten nur Oberarme, die Ellbogen wandern mit dem Wickeln
        lift = (0, -1, -1, 0, 1, 1)[treat]
        sleeve_front(cv, 16, 18, 23 + lift, False)
        sleeve_front(cv, 29, 31, 23 - lift, True)
    elif run:
        ln = 5
        sleeve_front(cv, 16, 18, 19 + ln + sl * 2, False)
        hand(cv, 16, 20 + ln + sl * 2)
        sleeve_front(cv, 29, 31, 19 + ln + sr * 2, True)
        hand(cv, 30, 20 + ln + sr * 2)
    else:
        sleeve_front(cv, 16, 18, 24 + sl, False)
        cv.R(16, 25 + sl, 18, 25 + sl, kb)
        hand(cv, 16, 26 + sl)
        sleeve_front(cv, 29, 31, 24 + sr, True)
        cv.R(29, 25 + sr, 31, 25 + sr, kb)
        hand(cv, 30, 26 + sr)
    coat_hem_front(cv)
    # Rueckseite: Kittel nur als Saum, Strickjacke durchgehend
    cv.R(17, 18, 30, 18, base)
    cv.R(19, 19, 28, 28, base)
    for y in range(19, 29):
        cv.P(19, y, sh)
        cv.P(28, y, hl if y < 24 else base)
    cv.R(19, 28, 28, 28, sh)
    cv.R(20, 29, 27, 29, dk)
    for y in range(20, 28):                           # Mittelnaht der Strickjacke
        cv.P(23, y, sh)
    for y in range(20, 28, 2):                        # Rippen
        cv.P(21, y, sh)
        cv.P(22, y + 1, sh)
        cv.P(26, y, sh)
        cv.P(25, y + 1, sh)
    cv.R(21, 18, 26, 18, kb)                          # Kittelkragen im Nacken
    cv.P(21, 18, ks)
    # Naht und Knoepfe der Kittel-Rueckseite verdecken wir nicht: nur Mittelnaht
    for p in ((27, 18), (28, 18), (29, 18), (30, 19)):
        cv.P(p[0], p[1], hl)
    head_back(cv, turn)


def upper_side(cv, swing_a, run=False, down=0, treat=None):
    """Seitenansicht nach links (W)."""
    hl, base, sh, dk = CG
    kb, ks, kd = KW
    end = 25 if run else 27
    lift = 0 if treat is None else (0, -1, -1, 0, 1, 1)[treat]
    if treat is None:
        # ferner Arm
        far_hx = 24 + rnd(-swing_a * (5 if run else 3))
        for y in range(19, end + 1):
            x = rnd(24 + (far_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, sh)
        cv.R(far_hx - 1, end, far_hx, end + 2, SM)
    else:
        limb(cv, [(24, 19), (22, 23), (19, 25 - lift)], sh, sh, sh)
        cv.R(17, 24 - lift, 18, 26 - lift, SM)
    # Rumpf: Kittel unten, Strickjacke
    coat_hem_side(cv)
    cv.R(21, 18, 26, 18, base)
    cv.R(20, 19, 27, 28, base)
    for y in range(19, 29):
        cv.P(20, y, sh)
        cv.P(26, y, hl if y < 23 else base)
        cv.P(27, y, sh)
    cv.R(20, 28, 27, 28, sh)
    cv.R(20, 29, 27, 29, dk)
    cv.P(25, 18, hl)
    cv.P(26, 18, hl)
    # Rippen
    for y in range(20, 28, 2):
        cv.P(22, y, sh)
        cv.P(23, y + 1, sh)
    # Kittelkragen
    cv.R(21, 18, 24, 18, kb)
    cv.P(22, 19, ks)
    cv.P(23, 19, kb)
    # Hals
    cv.R(22, 17, 25, 17, SM)
    keys_side(cv)
    if treat is None:
        # naher Arm
        near_hx = 24 + rnd(swing_a * (5 if run else 3))
        for y in range(19, end + 1):
            x = rnd(24 + (near_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, base)
            cv.P(x - 1, y, sh)
            cv.P(x + 1, y, hl)
        cv.R(near_hx - 1, end - 1, near_hx + 1, end - 1, kb)
        cv.R(near_hx - 1, end, near_hx, end + 2, SL)
        cv.P(near_hx - 1, end, SM)
        cv.P(near_hx - 1, end + 1, SM)
    else:
        limb(cv, [(24, 19), (23, 23), (20, 24 + lift)], base, sh, hl)
        cv.R(19, 23 + lift, 20, 25 + lift, kb)             # Manschette
        cv.R(17, 23 + lift, 18, 25 + lift, SL)
        cv.P(17, 23 + lift, SM)
        # Verband vor den Haenden
        y0 = 23 + lift
        cv.R(14, y0, 16, y0, KW[2])
        cv.R(14, y0 + 1, 16, y0 + 2, KW[0])
        cv.P(14, y0 + 1, KWL)
        cv.P(15 + (treat % 2), y0 + 1, KW[1])
        cv.R(14, y0 + 3, 16, y0 + 3, KW[2])
        for i in range((1, 2, 3, 2, 1, 0)[treat]):
            cv.P(14 + (i % 2), y0 + 4 + i, KW[0] if i == 0 else KW[1])
    head_side(cv, down)


# ---------------------------------------------------------------- Treat (Blick nach unten, Verband wickeln)
def upper_treat(cv, t, turn=0):
    """t = 0..5. Beide Haende vor dem Bauch, rollen einen Verband; Kopf leicht gesenkt."""
    hl, base, sh, dk = CG
    kb, ks, kd = KW
    lift = (0, -1, -1, 0, 1, 1)[t]
    # Kittel unten, Strickjacke
    coat_hem_front(cv)
    cv.R(17, 18, 30, 18, base)
    cv.R(19, 19, 28, 28, base)
    for y in range(19, 29):
        cv.P(19, y, sh)
        cv.P(28, y, hl if y < 24 else base)
    cv.R(19, 28, 28, 28, sh)
    cv.R(20, 29, 27, 29, dk)
    for y in range(19, 29):
        cv.R(22, y, 25, y, kb)
        cv.P(22, y, ks)
        cv.P(25, y, KWL if y < 22 else kb)
    for y in (21, 23, 25, 27):
        cv.P(20, y, sh)
        cv.P(27, y, sh)
    for p in ((27, 18), (28, 18), (29, 18), (30, 19)):
        cv.P(p[0], p[1], hl)
    cv.R(22, 18, 25, 18, SM)
    cv.R(23, 19, 24, 19, SM)
    cv.P(21, 18, kb)
    cv.P(26, 18, kb)
    keys_front(cv, -1)
    # Arme: Oberarm senkrecht, Unterarm waagrecht nach innen zum Verband (Ellbogen aussen)
    lh, rh = 24 + lift, 24 - lift                     # Handhoehen, gegengleich
    cv.R(16, 19, 18, 23, base)
    for y in range(19, 24):
        cv.P(16, y, sh)
        cv.P(18, y, hl if y < 21 else base)
    cv.R(16, 23, 18, 24, base)
    cv.R(16, 24, 16, 24, sh)
    cv.R(17, 24 + lift, 19, 25 + lift, base)           # Unterarm links
    cv.R(17, 25 + lift, 19, 25 + lift, sh)
    cv.R(20, 24 + lift, 20, 25 + lift, kb)             # Manschette
    hand(cv, 21, 24 + lift)
    cv.R(29, 19, 31, 23, base)
    for y in range(19, 24):
        cv.P(29, y, hl if y < 21 else base)
        cv.P(31, y, sh)
    cv.R(29, 23, 31, 24, base)
    cv.P(31, 24, sh)
    cv.R(28, 24 - lift, 30, 25 - lift, base)           # Unterarm rechts
    cv.R(28, 25 - lift, 30, 25 - lift, sh)
    cv.R(27, 24 - lift, 27, 25 - lift, kb)
    hand(cv, 25, 24 - lift)
    # Verband zwischen den Haenden: Rolle dreht sich, Streifen haengt herab
    y0 = 24 + lift
    cv.R(23, y0, 24, y0, kd)                           # Rolle mit dunklem Rand, damit sie sich vom Kittel abhebt
    cv.R(23, y0 + 1, 24, y0 + 2, kb)
    cv.P(23, y0 + 1, KWL)
    cv.P(24, y0 + 1 + (t % 2), ks)                     # Wicklung dreht sich
    cv.R(23, y0 + 3, 24, y0 + 3, kd)
    tail = (1, 2, 3, 2, 1, 0)[t]
    for i in range(tail):
        cv.P(23 + (i % 2), y0 + 4 + i, kb if i == 0 else ks)
    head_front(cv, turn, down=1)


# ---------------------------------------------------------------- Zusammenbau
def render(view, phase, bob, mode):
    """mode: 'idle', 'walk', 'run'. Ein Frame als Pixel-Raster."""
    real = MIRROR.get(view, view)
    cv = Cv()
    run = mode == 'run'
    if run:
        legs_pose(cv, real, phase, ampx=7.0, ampy=2.2, lift_h=3.6)
    else:
        legs_pose(cv, real, phase)
    cv.dy = bob
    swing = 0 if phase is None else math.sin(2 * math.pi * phase)
    if run:
        swing = 1.0 if swing > 0.35 else (-1.0 if swing < -0.35 else 0.0)
        # Vorlehnen: seitlich nach vorn (W = links), frontal ueber zusaetzlichen Bob
        if real == 'W':
            cv.dx = -1
        elif real == 'SW':
            cv.dx = -1
    if real == 'W':
        upper_side(cv, swing, run)
    elif real in ('S', 'SW'):
        upper_front(cv, rnd(swing), 1 if real == 'SW' else 0, run)
    else:
        upper_back(cv, rnd(swing), 1 if real == 'NW' else 0, run)
    buf = outline(cv.b)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return buf


def render_treat(view, t):
    """Behandeln in einer der 8 Richtungen (NE/E/SE gespiegelt)."""
    real = MIRROR.get(view, view)
    cv = Cv()
    legs_pose(cv, real, None)
    cv.dy = (0, 0, 1, 1, 1, 0)[t]
    if real == 'W':
        upper_side(cv, 0, False, 1, treat=t)
    elif real in ('S', 'SW'):
        upper_treat(cv, t, 1 if real == 'SW' else 0)
    else:
        upper_back(cv, 0, 1 if real == 'NW' else 0, False, treat=t)
    buf = outline(cv.b)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return buf


IDLE_BOB = [0, 0, 0, 1, 1, 0]
WALK_BOB = [0, 1, 1, 0, 0, 1, 1, 0]
RUN_BOB = [0, 2, 1, 0, 0, 2, 1, 0]


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    stand = Image.new('RGBA', (8 * CELL, CELL))
    idle = Image.new('RGBA', (6 * CELL, 8 * CELL))
    walk = Image.new('RGBA', (8 * CELL, 8 * CELL))
    run = Image.new('RGBA', (8 * CELL, 8 * CELL))
    treat = Image.new('RGBA', (6 * CELL, 8 * CELL))
    for r, v in enumerate(ORDER):
        stand.paste(to_img(render(v, None, 0, 'idle')), (r * CELL, 0))
        for c, b in enumerate(IDLE_BOB):
            idle.paste(to_img(render(v, None, b, 'idle')), (c * CELL, r * CELL))
        for c, b in enumerate(WALK_BOB):
            walk.paste(to_img(render(v, c / 8.0, b, 'walk')), (c * CELL, r * CELL))
        for c, b in enumerate(RUN_BOB):
            run.paste(to_img(render(v, c / 8.0, b, 'run')), (c * CELL, r * CELL))
        for t in range(6):
            treat.paste(to_img(render_treat(v, t)), (t * CELL, r * CELL))
    stand.save(os.path.join(outdir, 'doctor_veronica_stand_8dir.png'))
    idle.save(os.path.join(outdir, 'doctor_veronica_idle_sheet.png'))
    walk.save(os.path.join(outdir, 'doctor_veronica_walk_sheet.png'))
    run.save(os.path.join(outdir, 'doctor_veronica_run_sheet.png'))
    treat.save(os.path.join(outdir, 'doctor_veronica_treat_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'ANIMATIONS_8DIR')
    build(out)
    print('ok', os.path.abspath(out))
