"""Pastor David: Idle (6), Walk (8), Run (8) und Pray (8, Beten mit gefalteten Haenden und gesenktem Kopf) in 8 Richtungen, 56x56-Raster.

Gleiches Raster, gleiche Zeilenreihenfolge (S, SW, W, NW, N, NE, E, SE) und gleiche Beinmechanik wie Hauptfiguren, Doctor Veronica und Baker Mara
(gen_doctor_veronica.py wird als Bibliothek genutzt). Nur Hex-Werte der Nightward-Palette.
Aussehen laut NPC-Doku: glatt rasiert, Brille, Priesterkragen (Erkennungsmerkmal, auch im Dunkeln hell), Strickweste, 50 Jahre.
NE/E/SE sind gespiegelte NW/W/SW.

Aufruf:  python gen_pastor_david.py [Ausgabeordner]
"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
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
SHIRT = ('#6b5a7a', '#3d2e4a', '#2b2140')      # schwarzes Priesterhemd (Violett-Schwarz): Licht, Grund, Schatten
VEST = ('#4a7a4f', '#2f5a3c', '#1e3a2b')       # Strickweste in Waldgruen: Licht, Grund, Schatten
TAB, TABL = '#e8e0f0', '#fff1c9'               # Krageneinsatz
HB, HL, HS = '#5c4033', '#9a95a0', '#3b2a22'   # Haar: braun mit grauen Schlaefen
FRAME, GLINT = '#4a4550', '#e8e0f0'            # Brille
BTN = '#b89a72'


# ---------------------------------------------------------------- Arme
def sleeve(cv, x1, x2, y_end, left):
    """Langer Hemdaermel mit Manschette; Hand folgt unter y_end."""
    for y in range(19, y_end + 1):
        cv.R(x1, y, x2, y, SHIRT[1])
        cv.P(x1 if left else x2, y, SHIRT[0])
        cv.P(x2 if left else x1, y, SHIRT[2])
    cv.R(x1, y_end, x2, y_end, SHIRT[2])


def hand(cv, x, y):
    cv.R(x, y, x + 1, y + 2, SL)
    cv.P(x, y, SM)
    cv.P(x, y + 1, SM)


# ---------------------------------------------------------------- Rumpf
def torso_front(cv, turn=0):
    """Hemd mit Priesterkragen, Strickweste mit V-Ausschnitt und senkrechten Rippen."""
    rows = {18: (17, 30)}
    cv.R(17, 18, 30, 18, SHIRT[1])
    for y in range(19, 28):
        cv.R(19, y, 28, y, VEST[1])
        cv.P(19, y, VEST[2])
        cv.P(28, y, VEST[0] if y < 24 else VEST[1])
    cv.R(19, 27, 28, 27, VEST[2])
    cv.R(20, 28, 27, 28, SHIRT[2])                      # Hemdzipfel unter der Weste
    for p in ((27, 18), (28, 18), (29, 18), (30, 19)):
        cv.P(p[0], p[1], SHIRT[0])
    # Rippen
    for y in range(20, 27):
        if y % 2 == 0:
            cv.P(20, y, VEST[2])
            cv.P(21, y, VEST[0] if y < 24 else VEST[1])
            cv.P(26, y, VEST[2])
            cv.P(27, y, VEST[0] if y < 24 else VEST[1])
    # V-Ausschnitt: Hemd darunter
    for y in range(19, 24):
        hw = 2 - (y - 19) // 2
        cv.R(24 - 1 - hw, y, 23 + hw, y, SHIRT[1])
    cv.P(23, 23, SHIRT[2])
    cv.P(24, 23, SHIRT[2])
    for y in (25, 26):
        cv.P(23, y, BTN)
        cv.P(24, y, BTN)
    # Hals und Priesterkragen: schwarzes Band mit hellem Einsatz
    cv.R(22, 17, 25, 17, SM)
    cv.R(21, 18, 26, 18, SHIRT[2])
    cv.R(23, 18, 24, 20, TAB)
    cv.P(23, 18, TABL)
    cv.P(23, 19, TABL)
    cv.P(22, 18, SHIRT[1])
    cv.P(25, 18, SHIRT[1])


def torso_back(cv):
    cv.R(17, 18, 30, 18, SHIRT[1])
    for y in range(19, 28):
        cv.R(19, y, 28, y, VEST[1])
        cv.P(19, y, VEST[2])
        cv.P(28, y, VEST[0] if y < 24 else VEST[1])
    cv.R(19, 27, 28, 27, VEST[2])
    cv.R(20, 28, 27, 28, SHIRT[2])
    for y in range(20, 27, 2):                          # Rippen und Mittelnaht
        cv.P(21, y, VEST[2])
        cv.P(26, y, VEST[2])
    for y in range(20, 27):
        cv.P(23, y, VEST[2])
    for p in ((27, 18), (28, 18), (29, 18), (30, 19)):
        cv.P(p[0], p[1], SHIRT[0])
    cv.R(22, 17, 25, 17, SM)
    cv.R(21, 17, 26, 17, TAB)                           # heller Kragenring im Nacken
    cv.P(21, 17, TABL)
    cv.R(22, 18, 25, 18, SHIRT[2])


# ---------------------------------------------------------------- Kopf
def head_front(cv, turn, closed=False):
    sx = -1 if turn else 0
    # Haarkappe, graue Schlaefen
    cv.R(21, 5, 26, 5, HB)
    cv.R(20, 6, 27, 6, HB)
    cv.R(19, 7, 28, 8, HB)
    cv.R(21, 6, 22, 6, HL)
    cv.P(24, 5, HL)
    cv.P(19, 8, HL)
    cv.P(28, 8, HL)
    cv.P(19, 9, HL)
    cv.P(28, 9, HL)
    cv.P(23, 6, HS)
    # Gesicht
    cv.R(20, 9, 27, 15, SL)
    cv.R(21, 16, 26, 16, SL)
    cv.R(22, 17, 25, 17, SM)
    for y in range(9, 16):
        cv.P(20, y, SM)
    cv.R(21, 16, 22, 16, SM)
    cv.P(19, 11, SM)                                    # Ohren
    cv.P(19, 12, SM)
    cv.P(28, 11, SL)
    cv.P(28, 12, SL)
    cv.R(20, 9, 21, 9, HB)                              # Stirnansatz
    cv.R(26, 9, 27, 9, HB)
    if turn:
        cv.R(26, 8, 28, 12, HB)
        cv.P(27, 9, HL)
        cv.P(19, 12, SL)
    # Brille: zwei runde Glaeser (3x3 Ring um das Auge), Steg auf Augenhoehe, Buegel zu den Ohren
    for x0 in (20, 25):
        x0 += sx
        cv.R(x0, 10, x0 + 2, 10, FRAME)
        cv.R(x0, 12, x0 + 2, 12, FRAME)
        cv.P(x0, 11, FRAME)
        cv.P(x0 + 2, 11, FRAME)
    cv.R(23 + sx, 11, 24 + sx, 11, FRAME)
    cv.P(19 + sx, 11, FRAME)
    cv.P(28 + sx, 11, FRAME)
    # Augen hinter den Glaesern (bei geschlossenen Augen nur Lidstrich)
    ec = SM if closed else K
    cv.P(21 + sx, 11, ec)
    cv.P(26 + sx, 11, ec)
    cv.P(21 + sx, 12, SM) if closed else None
    # Nase, ruhiger Mund
    cv.P(23 + sx, 13, SM)
    cv.P(24 + sx, 13, SM)
    cv.R(23 + sx, 14, 24 + sx, 14, SD)
    cv.P(22 + sx, 14, SM)


def head_back(cv, turn):
    cv.R(21, 5, 26, 5, HB)
    cv.R(20, 6, 27, 6, HB)
    cv.R(19, 7, 28, 15, HB)
    cv.R(20, 16, 27, 16, HB)
    for y in range(6, 15):                              # nach hinten gekaemmte Straehnen
        cv.P(22, y, HL if y < 10 else HB)
        cv.P(25, y, HS)
    cv.R(21, 5, 22, 5, HL)
    cv.P(20, 10, HL)
    cv.P(27, 10, HL)
    cv.P(23, 15, HS)
    cv.P(24, 15, HS)
    cv.P(18, 11, SM)
    cv.P(18, 12, SM)
    cv.P(29, 11, SL)
    cv.P(29, 12, SL)
    cv.R(22, 17, 25, 17, SM)
    if turn:
        cv.P(19, 11, SL)
        cv.P(19, 12, SL)
        cv.P(19, 13, SL)


def head_side(cv, closed=False):
    """Profil nach links."""
    cv.R(21, 5, 26, 5, HB)
    cv.R(20, 6, 27, 6, HB)
    cv.R(20, 7, 28, 7, HB)
    cv.R(24, 8, 28, 14, HB)
    cv.R(20, 8, 23, 8, HB)
    for p in ((22, 6), (24, 5), (26, 7), (25, 9), (27, 11)):
        cv.P(p[0], p[1], HL)
    for p in ((26, 10), (25, 13), (27, 13)):
        cv.P(p[0], p[1], HS)
    cv.R(20, 9, 23, 9, SL)
    cv.R(20, 10, 24, 15, SL)
    cv.R(19, 11, 19, 14, SL)
    cv.R(20, 16, 24, 16, SL)
    for y in range(10, 16):
        cv.P(24, y, SM)
    cv.R(20, 16, 22, 16, SM)
    cv.P(18, 12, SL)                                    # Nase
    cv.P(18, 13, SM)
    # Brille im Profil: Glas vorn, Buegel zum Ohr
    cv.R(19, 10, 22, 10, FRAME)
    cv.R(19, 12, 22, 12, FRAME)
    cv.P(19, 11, FRAME)
    cv.P(22, 11, FRAME)
    cv.R(23, 10, 25, 10, FRAME)
    ec = SM if closed else K
    cv.P(20, 11, ec)
    cv.P(21, 11, SL if not closed else SM)
    cv.P(19, 14, SD)
    cv.P(20, 14, SD)
    cv.P(24, 12, SM)                                    # Ohr
    cv.R(22, 17, 25, 17, SM)
    cv.R(22, 18, 24, 18, SM)


# ---------------------------------------------------------------- Oberkoerper je Ansicht
def upper_front(cv, swing, turn, run=False, pray=None):
    sl, sr = swing, -swing
    if pray is not None:
        # Oberarme hinter dem Koerper, Unterarme kommen nach dem Rumpf davor
        sleeve(cv, 16, 18, 23, True)
        sleeve(cv, 29, 31, 23, False)
    elif run:
        ln = 5
        sleeve(cv, 16, 18, 19 + ln + sl * 2, True)
        hand(cv, 16, 20 + ln + sl * 2)
        sleeve(cv, 29, 31, 19 + ln + sr * 2, False)
        hand(cv, 30, 20 + ln + sr * 2)
    else:
        sleeve(cv, 16, 18, 25 + sl, True)
        hand(cv, 16, 26 + sl)
        sleeve(cv, 29, 31, 25 + sr, False)
        hand(cv, 30, 26 + sr)
    torso_front(cv, turn)
    dip = 0
    if pray is not None:
        t = pray
        lift = (0, 0, 0, 1, 1, 0, 0, 0)[t]
        limb(cv, [(17, 23), (21, 23 + lift)], SHIRT[1], SHIRT[2], SHIRT[0])
        limb(cv, [(30, 23), (26, 23 + lift)], SHIRT[1], SHIRT[0], SHIRT[2])
        cv.R(22, 22 + lift, 25, 24 + lift, SL)           # gefaltete Haende vor der Brust
        cv.R(22, 24 + lift, 25, 24 + lift, SM)
        cv.P(23, 23 + lift, SM)
        cv.P(25, 22 + lift, SM)
        cv.R(20, 22 + lift, 21, 24 + lift, SHIRT[2])    # Manschetten
        cv.R(26, 22 + lift, 27, 24 + lift, SHIRT[2])
        dip = (0, 1, 2, 2, 2, 2, 1, 0)[t]
    cv.dy += dip
    head_front(cv, turn, closed=pray is not None and dip >= 1)
    cv.dy -= dip


def upper_back(cv, swing, turn, run=False, pray=None):
    sl, sr = swing, -swing
    if pray is not None:
        sleeve(cv, 16, 18, 23, True)
        sleeve(cv, 29, 31, 23, False)
    elif run:
        ln = 5
        sleeve(cv, 16, 18, 19 + ln + sl * 2, True)
        hand(cv, 16, 20 + ln + sl * 2)
        sleeve(cv, 29, 31, 19 + ln + sr * 2, False)
        hand(cv, 30, 20 + ln + sr * 2)
    else:
        sleeve(cv, 16, 18, 25 + sl, True)
        hand(cv, 16, 26 + sl)
        sleeve(cv, 29, 31, 25 + sr, False)
        hand(cv, 30, 26 + sr)
    torso_back(cv)
    dip = 0
    if pray is not None:
        dip = (0, 1, 2, 2, 2, 2, 1, 0)[pray]
    cv.dy += dip
    head_back(cv, turn)
    cv.dy -= dip


def upper_side(cv, swing_a, run=False, pray=None):
    """Seitenansicht nach links (W)."""
    end = 25 if run else 27
    if pray is None:
        far_hx = 24 + rnd(-swing_a * (5 if run else 3))
        for y in range(19, end + 1):
            x = rnd(24 + (far_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, SHIRT[2])
        cv.R(far_hx - 1, end, far_hx, end + 2, SM)
    # Rumpf: Weste, Hemd
    cv.R(21, 18, 26, 18, SHIRT[1])
    for y in range(19, 28):
        cv.R(20, y, 27, y, VEST[1])
        cv.P(20, y, VEST[2])
        cv.P(26, y, VEST[0] if y < 23 else VEST[1])
        cv.P(27, y, VEST[2])
    cv.R(20, 27, 27, 27, VEST[2])
    cv.R(21, 28, 26, 28, SHIRT[2])
    for y in range(20, 27, 2):
        cv.P(22, y, VEST[2])
        cv.P(23, y + 1, VEST[2])
    cv.P(25, 18, SHIRT[0])
    cv.P(26, 18, SHIRT[0])
    cv.P(20, 25, BTN)
    cv.P(20, 23, BTN)
    # Kragen: Einsatz vorn
    cv.R(22, 17, 25, 17, SM)
    cv.R(21, 18, 24, 18, SHIRT[2])
    cv.R(21, 18, 22, 19, TAB)
    cv.P(21, 18, TABL)
    dip = 0
    if pray is None:
        near_hx = 24 + rnd(swing_a * (5 if run else 3))
        for y in range(19, end + 1):
            x = rnd(24 + (near_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, SHIRT[1])
            cv.P(x - 1, y, SHIRT[2])
            cv.P(x + 1, y, SHIRT[0])
        cv.R(near_hx - 1, end - 1, near_hx + 1, end - 1, SHIRT[2])
        cv.R(near_hx - 1, end, near_hx, end + 2, SL)
        cv.P(near_hx - 1, end, SM)
        cv.P(near_hx - 1, end + 1, SM)
    else:
        t = pray
        lift = (0, 0, 0, 1, 1, 0, 0, 0)[t]
        limb(cv, [(24, 19), (23, 23), (20, 23 + lift)], SHIRT[1], SHIRT[2], SHIRT[0])
        cv.R(19, 22 + lift, 20, 24 + lift, SHIRT[2])    # Manschette
        cv.R(17, 21 + lift, 19, 24 + lift, SL)           # gefaltete Haende vor der Brust
        cv.R(17, 24 + lift, 19, 24 + lift, SM)
        cv.P(18, 22 + lift, SM)
        cv.P(17, 21 + lift, SM)
        dip = (0, 1, 2, 2, 2, 2, 1, 0)[t]
    cv.dy += dip
    head_side(cv, closed=pray is not None and dip >= 1)
    cv.dy -= dip


# ---------------------------------------------------------------- Zusammenbau
def render(view, phase, bob, mode, pray=None):
    """mode: idle, walk, run, pray. Ein Frame als Pixel-Raster."""
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
        if real in ('W', 'SW'):
            cv.dx = -1
    if real == 'W':
        upper_side(cv, swing, run, pray)
    elif real in ('S', 'SW'):
        upper_front(cv, rnd(swing), 1 if real == 'SW' else 0, run, pray)
    else:
        upper_back(cv, rnd(swing), 1 if real == 'NW' else 0, run, pray)
    buf = outline(cv.b)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return buf


IDLE_BOB = [0, 0, 0, 1, 1, 0]
WALK_BOB = [0, 1, 1, 0, 0, 1, 1, 0]
RUN_BOB = [0, 2, 1, 0, 0, 2, 1, 0]
PRAY_BOB = [0, 0, 0, 1, 1, 1, 0, 0]


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    stand = Image.new('RGBA', (8 * CELL, CELL))
    idle = Image.new('RGBA', (6 * CELL, 8 * CELL))
    walk = Image.new('RGBA', (8 * CELL, 8 * CELL))
    run = Image.new('RGBA', (8 * CELL, 8 * CELL))
    pray = Image.new('RGBA', (8 * CELL, 8 * CELL))
    for r, v in enumerate(ORDER):
        stand.paste(to_img(render(v, None, 0, 'idle')), (r * CELL, 0))
        for c, b in enumerate(IDLE_BOB):
            idle.paste(to_img(render(v, None, b, 'idle')), (c * CELL, r * CELL))
        for c, b in enumerate(WALK_BOB):
            walk.paste(to_img(render(v, c / 8.0, b, 'walk')), (c * CELL, r * CELL))
        for c, b in enumerate(RUN_BOB):
            run.paste(to_img(render(v, c / 8.0, b, 'run')), (c * CELL, r * CELL))
        for c in range(8):
            pray.paste(to_img(render(v, None, PRAY_BOB[c], 'pray', pray=c)), (c * CELL, r * CELL))
    stand.save(os.path.join(outdir, 'pastor_david_stand_8dir.png'))
    idle.save(os.path.join(outdir, 'pastor_david_idle_sheet.png'))
    walk.save(os.path.join(outdir, 'pastor_david_walk_sheet.png'))
    run.save(os.path.join(outdir, 'pastor_david_run_sheet.png'))
    pray.save(os.path.join(outdir, 'pastor_david_pray_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'ANIMATIONS_8DIR')
    build(out)
    print('ok', os.path.abspath(out))
