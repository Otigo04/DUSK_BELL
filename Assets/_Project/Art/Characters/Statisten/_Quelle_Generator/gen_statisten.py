"""STATISTEN: Trauergaeste, Mutter, Junge, Maedchen - 8 Richtungen, Idle (6 Frames) und Walk (8 Frames) im 56x56-Raster.
Gleiches Raster, gleiche Zeilenreihenfolge (S, SW, W, NW, N, NE, E, SE) und gleiche Beinmechanik wie Hauptfiguren, Veronica, Mara, David und Can
(gen_hauptfiguren.py wird als Bibliothek genutzt). NE/E/SE sind gespiegelte NW/W/SW. Nur Hex-Werte der Nightward-Palette.

Quellen: Opening Sequence Step 9 ("Menschen in dunkler Kleidung, frisch ausgehobenes Grab. Die Koepfe drehen sich mit dem Auto mit. Eine Frau
presst ein Tuch an den Mund. Ein Junge wird von seiner Mutter zurueckgezogen."), CrowdMember.cs (Trauergast: Idle in 8 Richtungen, Kopf dreht mit),
Style-Bibel (keine schwarzen Umrisse, "dunkle Kleidung" = Violett-/Nachtblau-Toene, jede Figur ein markantes Element: Hut, Tuch, Werkzeug).
Figuren (Ordner Statisten/<Name>/):
  Trauergast_Mann_A     schwarzer Anzug, Melone, graues Haar, Trauerflor am Arm
  Trauergast_Mann_B     langer dunkelblauer Mantel, helles Halstuch, dunkles Haar
  Trauergast_Frau_A     langes schwarzes Kleid, schwarzes Kopftuch
  Trauergast_Frau_B     dunkelgruener Mantel, Hut mit Trauerschleier
  Trauergast_Frau_Tuch  braunes Kleid, Haarknoten, presst ein weisses Tuch an den Mund (Hand dauerhaft oben)
  Mutter                schwarzes Kleid, violettes Schultertuch, Haarknoten
  Kind_Junge            Weste ueber weissem Hemd, Schiebermuetze, kurze Hosen mit Struempfen (Kind: ca. 3/4 Erwachsenengroesse)
  Kind_Maedchen         dunkles Kleid mit heller Schuerze, zwei Zoepfe
Ausgabe je Figur: <name>_stand_8dir.png (448x56), <name>_idle_sheet.png (336x448), <name>_walk_sheet.png (448x448).
Aufruf:  python gen_statisten.py [Ausgabeordner]     (schreibt auch Vorschau_Statisten.png)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'Hauptfiguren', '_Quelle_Generator'))

from PIL import Image  # noqa: E402

import gen_hauptfiguren as G  # noqa: E402
from gen_hauptfiguren import CELL, ORDER, MIRROR, K, K2, V1, V2, V3, HR, W1, W2, W3, SAND, SD, SM, SL, CR, ST, ST2, ROSE, RD, rnd, outline, to_img  # noqa: E402

MOON = '#e8e0f0'
NB1, NB2, NB3 = '#1f2a3d', '#2c3e56', '#3f5570'
GR1, GR2, GR3 = '#1e3a2b', '#2f5a3c', '#4a7a4f'

# Kleidung: Licht, Grund, Schatten, Tief
BLACK = (V2, V1, K2, K)
NAVY = (NB3, NB2, NB1, K)
DGREEN = (GR3, GR2, GR1, K)
BROWN = (W2, W1, HR, K2)
VIOLET = (V3, V2, V1, K2)
VEST = (ST2, '#4a4550', V1, K2)
SHIRT = (MOON, CR, ST, ST2)

SKIN = (SL, SM, SD)


def person(**kw):
    s = dict(kind='adult', female=False, coat=BLACK, sleeve=None, skirt=0, shawl=None, scarf=None, hair=(HR, W1), style='short',
             hat=None, hatc=(K2, V1, K), hanky=False, legs=(K2, K, V1), boots=(K2, K, V1), apron=None, armband=False, coatlong=0, skin=SKIN)
    s.update(kw)
    if s['kind'] == 'kid':
        s.update(t0=28, t1=35, x1=18, x2=29, hdy=10, ay2=33)
    else:
        s.update(t0=18, t1=31, x1=17, x2=30, hdy=0, ay2=28)
    return s


SPECS = {
    'Trauergast_Mann_A': person(coat=BLACK, hair=(ST, MOON), style='short', hat='bowler', hatc=(V1, K2, K), armband=True,
                                legs=(V1, K2, K), boots=(K, K, K2)),
    'Trauergast_Mann_B': person(coat=NAVY, hair=(HR, W1), style='short', scarf=(CR, SAND), coatlong=5, legs=(NB2, NB1, K), boots=(K2, K, V1)),
    'Trauergast_Frau_A': person(female=True, coat=BLACK, hair=(HR, W1), style='short', hat='scarf', hatc=(V1, K2, K), skirt=11),
    'Trauergast_Frau_B': person(female=True, coat=DGREEN, hair=(W1, W2), style='short', hat='veil', hatc=(K2, V1, K), skirt=9),
    'Trauergast_Frau_Tuch': person(female=True, coat=BROWN, hair=(HR, W1), style='bun', hanky=True, skirt=10),
    'Mutter': person(female=True, coat=BLACK, hair=(W1, W2), style='bun', shawl=VIOLET, skirt=11),
    'Kind_Junge': person(kind='kid', coat=VEST, sleeve=SHIRT, hair=(W1, W2), style='short', hat='kidcap', hatc=(ST2, ST, V1),
                         legs=(V1, K2, K), boots=(K2, K, V1)),
    'Kind_Maedchen': person(kind='kid', female=True, coat=BLACK, sleeve=BLACK, hair=(W2, W3), style='braids', apron=(MOON, CR, ST), skirt=6,
                            legs=(CR, MOON, ST), boots=(K2, K, V1)),
}


# ---------------------------------------------------------------- Zeichen-Helfer
def hl_(cv, x1, x2, y, c):
    cv.R(x1, y, x2, y, c)


def vl_(cv, x, y1, y2, c):
    cv.R(x, y1, x, y2, c)


def shaded(cv, x1, y1, x2, y2, pal):
    hl, base, sh, dk = pal
    cv.R(x1, y1, x2, y2, base)
    vl_(cv, x1, y1, y2, hl)
    vl_(cv, x2, y1, y2, sh)
    hl_(cv, x1, x2, y2, dk)


def legs_kid(cv, view, phase):
    """Kinderbeine: wie legs_pose, aber kuerzer (Huefte 36, Knoechel 42) und mit kleinerem Schritt."""
    fx, fy = G.VIEWS[view]
    side = abs(fx) == 1
    idle = phase is None
    AMPX, AMPY, LIFT = 3.6, 1.0, 1.8
    specs = []
    for idx, off in enumerate((0.0, 0.5)):
        s_ = 0.0 if idle else math.sin(2 * math.pi * (phase + off))
        c_ = 0.0 if idle else math.cos(2 * math.pi * (phase + off))
        lift = 0 if idle else max(0.0, c_) * LIFT
        if side:
            sgn = 1 if fx > 0 else -1
            hx, w, dark = 23.5, 4, idx == 1
            ax = hx + s_ * AMPX * sgn
            kb, ay, toe = sgn * (0.5 + lift * 0.4), 42 - rnd(lift), sgn
            depth = 0 if idx == 0 else -1
        else:
            hx = 21.5 if idx == 0 else 25.5
            w, dark, toe, kb = 3, False, 0, 0.0
            ax = hx + s_ * AMPX * fx * 0.7
            ay = 42 + rnd(s_ * AMPY * fy) - rnd(lift * 0.8)
            depth = s_ * fy
        specs.append((depth, dict(hx=hx, hy=36, ax=ax, ay=ay, w=w, kb=kb, dark=dark, toe=toe)))
    specs.sort(key=lambda t: t[0])
    for _, sp in specs:
        G.leg(cv, sp['hx'], sp['hy'], sp['ax'], sp['ay'], sp['w'], sp['kb'], sp['dark'], sp['toe'])
    x1, x2 = (21, 26) if side else (19, 28)
    cv.R(x1, 33, x2, 37, G.LEGPAL['pants'][1])
    for y in range(33, 38):
        cv.P(x1, y, G.LEGPAL['pants'][0])
        cv.P(x2, y, G.LEGPAL['pants'][2])


# ---------------------------------------------------------------- Kopf
def hair_front(cv, s, dy, turn):
    h, h2 = s['hair']
    st = s['style']
    cv.R(21, 5 + dy, 26, 5 + dy, h)
    cv.R(20, 6 + dy, 27, 6 + dy, h)
    cv.R(19, 7 + dy, 28, 7 + dy, h)
    cv.R(19, 8 + dy, 19, 9 + dy, h)
    cv.R(28, 8 + dy, 28, 9 + dy, h)
    for p in ((24, 6), (25, 6), (26, 5), (27, 7)):
        cv.P(p[0], p[1] + dy, h2)
    if turn:
        cv.R(26, 8 + dy, 28, 12 + dy, h)
    if st == 'bun':
        cv.R(22, 3 + dy, 25, 4 + dy, h)
        cv.P(23, 3 + dy, h2)
    elif st == 'braids':
        for y in range(9 + dy, 22 + dy):
            cv.P(18, y, h)
            cv.P(29, y, h)
            if y % 3 == 0:
                cv.P(18, y, h2)
                cv.P(29, y, h2)
        cv.R(17, 22 + dy, 19, 23 + dy, ROSE)
        cv.R(28, 22 + dy, 30, 23 + dy, ROSE)
    elif s['female'] and st == 'short':
        pass


def hat_front(cv, s, dy, turn):
    hat, (hc, hc2, hc3) = s['hat'], s['hatc']
    if hat == 'bowler':
        cv.R(21, 2 + dy, 26, 2 + dy, hc)
        cv.R(20, 3 + dy, 27, 6 + dy, hc2)
        cv.R(20, 3 + dy, 21, 5 + dy, hc)
        cv.R(17, 7 + dy, 30, 7 + dy, hc3)
        cv.R(18, 6 + dy, 29, 6 + dy, hc2)
        cv.R(20, 6 + dy, 27, 6 + dy, hc3)
    elif hat == 'scarf':
        cv.R(19, 5 + dy, 28, 9 + dy, hc2)
        cv.R(20, 4 + dy, 27, 4 + dy, hc2)
        cv.R(18, 8 + dy, 19, 17 + dy, hc2)
        cv.R(28, 8 + dy, 29, 17 + dy, hc2)
        cv.R(19, 5 + dy, 21, 6 + dy, hc)
        cv.R(20, 9 + dy, 27, 9 + dy, hc3)
        cv.R(22, 18 + dy, 25, 19 + dy, hc3)
    elif hat == 'veil':
        cv.R(20, 4 + dy, 27, 6 + dy, hc2)
        cv.R(18, 7 + dy, 29, 7 + dy, hc3)
        cv.R(21, 3 + dy, 25, 3 + dy, hc)
        for y in range(8 + dy, 14 + dy):                               # Schleier: Dither ueber Augen und Nase
            for x in range(19, 29):
                if (x + y) % 2 == 0:
                    cv.P(x, y, hc2)
    elif hat == 'kidcap':
        cv.R(19, 5 + dy, 28, 7 + dy, hc2)
        cv.R(20, 4 + dy, 27, 4 + dy, hc)
        cv.R(18, 8 + dy, 29, 8 + dy, hc3)
        cv.R(25, 8 + dy, 30, 9 + dy, hc3)


def head_front(cv, s, turn, back=False):
    dy = s['hdy']
    sl, sm, sd = s['skin']
    sx = -1 if turn else 0
    cv.R(20, 9 + dy, 27, 9 + dy, sl)
    cv.R(19, 10 + dy, 28, 15 + dy, sl)
    cv.R(20, 16 + dy, 27, 16 + dy, sl)
    cv.R(22, 17 + dy, 25, 17 + dy, sm)
    for y in range(10 + dy, 16 + dy):
        cv.P(19, y, sm)
    cv.R(20, 16 + dy, 22, 16 + dy, sm)
    hair_front(cv, s, dy, turn)
    cv.R(21 + sx, 11 + dy, 22 + sx, 11 + dy, K)
    cv.R(25 + sx, 11 + dy, 26 + sx, 11 + dy, K)
    cv.P(23 + sx, 13 + dy, sm)
    cv.P(24 + sx, 13 + dy, sm)
    cv.R(23 + sx, 14 + dy, 24 + sx, 14 + dy, sd)
    if s['hat']:
        hat_front(cv, s, dy, turn)


def head_back(cv, s, turn):
    dy = s['hdy']
    h, h2 = s['hair']
    sl, sm, sd = s['skin']
    cv.R(19, 6 + dy, 28, 15 + dy, h)
    cv.R(20, 5 + dy, 27, 5 + dy, h)
    cv.R(20, 16 + dy, 27, 16 + dy, h)
    cv.R(22, 17 + dy, 25, 18 + dy, sm)
    for p in ((22, 7), (25, 8), (21, 11), (26, 12), (23, 14)):
        cv.P(p[0], p[1] + dy, h2)
    if turn:
        cv.R(19, 10 + dy, 20, 14 + dy, sm)
    if s['style'] == 'bun':
        cv.R(22, 3 + dy, 25, 5 + dy, h)
        cv.P(23, 4 + dy, h2)
    elif s['style'] == 'braids':
        for y in range(9 + dy, 24 + dy):
            cv.P(21, y, h)
            cv.P(26, y, h)
        cv.R(20, 24 + dy, 22, 25 + dy, ROSE)
        cv.R(25, 24 + dy, 27, 25 + dy, ROSE)
    hat = s['hat']
    hc, hc2, hc3 = s['hatc']
    if hat == 'bowler':
        cv.R(21, 2 + dy, 26, 2 + dy, hc)
        cv.R(20, 3 + dy, 27, 6 + dy, hc2)
        cv.R(17, 7 + dy, 30, 7 + dy, hc3)
    elif hat == 'scarf':
        cv.R(19, 5 + dy, 28, 16 + dy, hc2)
        cv.R(20, 4 + dy, 27, 4 + dy, hc2)
        cv.R(22, 17 + dy, 25, 19 + dy, hc3)
        cv.R(21, 8 + dy, 23, 10 + dy, hc)
    elif hat == 'veil':
        cv.R(20, 4 + dy, 27, 7 + dy, hc2)
        cv.R(18, 8 + dy, 29, 8 + dy, hc3)
        cv.R(21, 3 + dy, 25, 3 + dy, hc)
    elif hat == 'kidcap':
        cv.R(19, 5 + dy, 28, 8 + dy, hc2)
        cv.R(20, 4 + dy, 27, 4 + dy, hc)
        cv.R(18, 9 + dy, 29, 9 + dy, hc3)


def head_side(cv, s):
    dy = s['hdy']
    h, h2 = s['hair']
    sl, sm, sd = s['skin']
    cv.R(19, 9 + dy, 27, 15 + dy, sl)
    cv.R(20, 16 + dy, 26, 16 + dy, sl)
    cv.R(22, 17 + dy, 25, 17 + dy, sm)
    cv.P(18, 12 + dy, sl)
    cv.P(18, 13 + dy, sl)
    cv.P(18, 14 + dy, sm)
    for y in range(10 + dy, 16 + dy):
        cv.P(27, y, sm)
    cv.R(22, 11 + dy, 22, 11 + dy, K)
    cv.R(20, 10 + dy, 22, 10 + dy, h)
    cv.R(20, 14 + dy, 21, 14 + dy, sd)
    cv.R(21, 5 + dy, 27, 5 + dy, h)
    cv.R(20, 6 + dy, 28, 7 + dy, h)
    cv.R(24, 8 + dy, 28, 15 + dy, h)
    cv.R(25, 16 + dy, 27, 17 + dy, h)
    for p in ((23, 6), (25, 5), (26, 9), (27, 13)):
        cv.P(p[0], p[1] + dy, h2)
    if s['style'] == 'bun':
        cv.R(26, 4 + dy, 29, 8 + dy, h)
        cv.P(27, 5 + dy, h2)
    elif s['style'] == 'braids':
        for y in range(10 + dy, 25 + dy):
            cv.P(27, y, h)
            cv.P(28, y, h)
        cv.R(26, 25 + dy, 29, 26 + dy, ROSE)
    hat = s['hat']
    hc, hc2, hc3 = s['hatc']
    if hat == 'bowler':
        cv.R(21, 2 + dy, 26, 2 + dy, hc)
        cv.R(20, 3 + dy, 27, 6 + dy, hc2)
        cv.R(17, 7 + dy, 29, 7 + dy, hc3)
    elif hat == 'scarf':
        cv.R(20, 4 + dy, 28, 9 + dy, hc2)
        cv.R(24, 10 + dy, 29, 17 + dy, hc2)
        cv.R(26, 17 + dy, 29, 19 + dy, hc3)
        cv.R(21, 5 + dy, 23, 6 + dy, hc)
    elif hat == 'veil':
        cv.R(20, 4 + dy, 28, 7 + dy, hc2)
        cv.R(17, 8 + dy, 28, 8 + dy, hc3)
        cv.R(21, 3 + dy, 25, 3 + dy, hc)
        for y in range(9 + dy, 14 + dy):
            for x in range(18, 24):
                if (x + y) % 2 == 0:
                    cv.P(x, y, hc2)
    elif hat == 'kidcap':
        cv.R(19, 5 + dy, 28, 8 + dy, hc2)
        cv.R(20, 4 + dy, 27, 4 + dy, hc)
        cv.R(16, 9 + dy, 22, 9 + dy, hc3)
        cv.R(17, 8 + dy, 21, 8 + dy, hc3)


# ---------------------------------------------------------------- Rumpf
def arm_pal(s):
    return s['sleeve'] or s['coat']


def arm_v(cv, x1, x2, y1, y2, pal, hand_dy=1):
    hl, base, sh, dk = pal
    cv.R(x1, y1, x2, y2, base)
    vl_(cv, x1, y1, y2, hl)
    vl_(cv, x2, y1, y2, sh)
    cv.R(x1, y2 + hand_dy, x1 + 1, y2 + hand_dy + 1, SL)
    cv.P(x1, y2 + hand_dy, SM)


def skirt(cv, s, x1, x2, view_side=False):
    n = s['skirt'] or s['coatlong']
    if not n:
        return
    hl, base, sh, dk = s['coat']
    t1 = s['t1']
    for k in range(1, n + 1):
        a = x1 - (k // 3) - (0 if view_side else 0)
        b = x2 + (k // 3)
        cv.R(a, t1 + k, b, t1 + k, base)
        cv.P(a, t1 + k, hl if k < n - 2 else base)
        cv.P(b, t1 + k, sh)
        if k % 4 == 3:
            cv.R(a + 2, t1 + k, b - 2, t1 + k, sh)
    cv.R(x1 - (n // 3), t1 + n, x2 + (n // 3), t1 + n, dk)
    if s['apron']:
        ah, ab, ash = s['apron'][0], s['apron'][1], s['apron'][2]
        cv.R(x1 + 2, s['t1'] - 2, x2 - 2, t1 + n - 1, ab)
        cv.R(x1 + 2, s['t1'] - 2, x1 + 2, t1 + n - 1, ah)
        cv.R(x2 - 2, s['t1'] - 2, x2 - 2, t1 + n - 1, ash)
        cv.R(x1 + 2, t1 + n - 1, x2 - 2, t1 + n - 1, ash)


def body_front(cv, s, swing, turn):
    x1, x2, t0, t1 = s['x1'], s['x2'], s['t0'], s['t1']
    ay2 = s['ay2']
    ap = arm_pal(s)
    hl, base, sh, dk = s['coat']
    # Arme (hinter dem Rumpf)
    arm_v(cv, x1 - 2, x1, t0 + 1, ay2 + swing, ap)
    if s['hanky']:
        arm_v(cv, x2, x2 + 2, t0 + 1, t0 + 6, ap, 0)                      # Oberarm (Unterarm + Tuch: hanky_front, nach dem Kopf)
    else:
        arm_v(cv, x2, x2 + 2, t0 + 1, ay2 - swing, ap)
    shaded(cv, x1, t0, x2, t1, s['coat'])
    hl_(cv, x1, x2, t0, hl)
    for y in range(t0 + 3, t1 - 1, 3):                                   # Knoepfe
        cv.P((x1 + x2) // 2, y, dk)
    if s['scarf']:
        cv.R(21, t0 - 1, 26, t0, s['scarf'][0])
        cv.R(22, t0 + 1, 23, t0 + 4, s['scarf'][1])
    if s['shawl']:
        sh_h, sh_b, sh_s, sh_d = s['shawl']
        for k in range(0, 9):
            a, b = x1 - 1 + k // 2, x2 + 1 - k // 2
            if a < b:
                cv.R(a, t0 + k - 1, b, t0 + k - 1, sh_b)
                cv.P(a, t0 + k - 1, sh_h)
                cv.P(b, t0 + k - 1, sh_s)
    if s['armband']:
        cv.R(x2, t0 + 3, x2 + 2, t0 + 4, CR)
    skirt(cv, s, x1, x2)


def hanky_front(cv, s, swing):
    """Unterarm nach oben, Hand und weisses Tuch am Mund - wird NACH dem Kopf gezeichnet, sonst verdeckt das Gesicht es."""
    if not s['hanky']:
        return
    x2, t0 = s['x2'], s['t0']
    ap = arm_pal(s)
    hold = 0 if swing >= 0 else 1
    cv.R(x2 - 3, t0 - 3 + hold, x2 - 1, t0 + 5, ap[1])
    vl_(cv, x2 - 3, t0 - 3 + hold, t0 + 5, ap[0])
    vl_(cv, x2 - 1, t0 - 3 + hold, t0 + 5, ap[2])
    cv.R(x2 - 4, t0 - 5 + hold, x2 - 1, t0 - 4 + hold, SL)                    # Hand
    cv.R(x2 - 8, t0 - 6 + hold, x2 - 3, t0 - 2 + hold, CR)                    # Tuch vor dem Mund
    cv.R(x2 - 8, t0 - 6 + hold, x2 - 8, t0 - 2 + hold, MOON)
    cv.P(x2 - 6, t0 - 4 + hold, ST)
    cv.P(x2 - 5, t0 - 3 + hold, ST)


def body_back(cv, s, swing, turn):
    x1, x2, t0, t1 = s['x1'], s['x2'], s['t0'], s['t1']
    ay2 = s['ay2']
    ap = arm_pal(s)
    hl, base, sh, dk = s['coat']
    arm_v(cv, x1 - 2, x1, t0 + 1, ay2 - swing, ap)
    arm_v(cv, x2, x2 + 2, t0 + 1, ay2 + swing, ap)
    shaded(cv, x1, t0, x2, t1, s['coat'])
    hl_(cv, x1, x2, t0, hl)
    vl_(cv, (x1 + x2) // 2, t0 + 2, t1 - 1, sh)
    if s['shawl']:
        sh_h, sh_b, sh_s, sh_d = s['shawl']
        for k in range(0, 8):
            cv.R(x1 - 1 + k // 3, t0 + k - 1, x2 + 1 - k // 3, t0 + k - 1, sh_b)
        cv.R(x1 - 1, t0 - 1, x2 + 1, t0 - 1, sh_h)
    if s['scarf']:
        cv.R(21, t0 - 1, 26, t0, s['scarf'][0])
    skirt(cv, s, x1, x2)


def body_side(cv, s, swing):
    t0, t1 = s['t0'], s['t1']
    x1, x2 = 20, 27
    ap = arm_pal(s)
    hl, base, sh, dk = s['coat']
    ay2 = s['ay2']
    far = rnd(-swing * 3)
    near = rnd(swing * 3)
    arm_v(cv, 22 + far, 24 + far, t0 + 1, ay2 - 1, (ap[2], ap[2], ap[3], ap[3]), 1)       # fernerer Arm, dunkel
    shaded(cv, x1, t0, x2, t1, s['coat'])
    hl_(cv, x1, x2, t0, hl)
    if s['shawl']:
        sh_h, sh_b, sh_s, sh_d = s['shawl']
        for k in range(0, 7):
            cv.R(x1 - 1, t0 + k - 1, x2 + 1 - k // 3, t0 + k - 1, sh_b)
        cv.R(x1 - 1, t0 - 1, x2 + 1, t0 - 1, sh_h)
    if s['scarf']:
        cv.R(20, t0 - 1, 26, t0, s['scarf'][0])
    if s['hanky']:
        cv.R(19, t0 + 1, 23, t0 + 4, ap[1])                                  # Oberarm vorn
        cv.R(17, t0 - 4, 20, t0 + 2, ap[1])                                  # Unterarm zum Mund
        cv.R(16, t0 - 8, 19, t0 - 4, SL)
        cv.R(13, t0 - 9, 17, t0 - 4, CR)
        cv.R(13, t0 - 9, 13, t0 - 4, MOON)
    else:
        arm_v(cv, 22 + near, 24 + near, t0 + 1, ay2, ap, 1)
    if s['armband']:
        cv.R(22 + near, t0 + 3, 24 + near, t0 + 4, CR)
    skirt(cv, s, x1, x2, True)


# ---------------------------------------------------------------- Zusammenbau
def set_legs(s):
    p, bt = s['legs'], s['boots']
    G.LEGPAL.update(pants=(p[2], p[0], p[1]) if False else (p[1], p[0], p[2]), pants_dark=(p[2], p[2], p[1]),
                    boot=(bt[1], bt[0], bt[2]), boot_dark=(bt[2], bt[2], bt[1]), sole=K, sole_dark=K2, edge=K2, edge_dark=K)
    G.B1, G.B2, G.B3 = p[1], p[0], p[2]


def render(s, view, phase, bob):
    real = MIRROR.get(view, view)
    set_legs(s)
    cv = G.Cv()
    if s['kind'] == 'kid':
        legs_kid(cv, real, phase)
    else:
        G.legs_pose(cv, real, phase)
    cv.dy = bob
    swing = 0 if phase is None else math.sin(2 * math.pi * phase)
    sw = rnd(swing)
    if real == 'W':
        body_side(cv, s, swing)
        head_side(cv, s)
    elif real in ('S', 'SW'):
        body_front(cv, s, sw, 1 if real == 'SW' else 0)
        head_front(cv, s, 1 if real == 'SW' else 0)
        hanky_front(cv, s, swing)
    else:
        body_back(cv, s, sw, 1 if real == 'NW' else 0)
        head_back(cv, s, 1 if real == 'NW' else 0)
    buf = outline(cv.b)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return buf


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
    low = name.lower()
    stand.save(os.path.join(outdir, low + '_stand_8dir.png'))
    idle.save(os.path.join(outdir, low + '_idle_sheet.png'))
    walk.save(os.path.join(outdir, low + '_walk_sheet.png'))
    return stand


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..')
    stands = []
    for n in SPECS:
        stands.append((n, build(n, os.path.join(base, n))))
        print('ok', n)
    S = 2
    sh = Image.new('RGBA', (8 * CELL * S + 20, len(stands) * (CELL * S + 6) + 20), (74, 94, 74, 255))
    for i, (n, st) in enumerate(stands):
        sh.alpha_composite(st.resize((st.width * S, st.height * S), Image.NEAREST), (10, 10 + i * (CELL * S + 6)))
    sh.save(os.path.join(HERE, 'Vorschau_Statisten.png'))
