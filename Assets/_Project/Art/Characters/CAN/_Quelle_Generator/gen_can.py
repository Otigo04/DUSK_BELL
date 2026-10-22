"""Can: Idle (6), Walk (8), Run (8) und Feed (8, Monster fuettern: Brot aus dem Beutel, tief und vorsichtig hinhalten) in 8 Richtungen, 56x56-Raster.

Gleiches Raster, gleiche Zeilenreihenfolge (S, SW, W, NW, N, NE, E, SE) und gleiche Beinmechanik wie Hauptfiguren, Doctor Veronica, Mara und Pastor David
(gen_doctor_veronica.py wird als Bibliothek genutzt). Nur Hex-Werte der Nightward-Palette.
Aussehen laut NPC-Doku: Mitte 30, strubbelige Haare, grosse Hornbrille (Erkennungsmerkmal), Wollpullover; frueher Pfleger in einer Psychiatrie.
Figur: schlaksig und leicht gebeugt, ueberlanger Pullover mit Rippenbuendchen, Aermel decken die Haende fast ab, Brotbeutel an einem Umhaengegurt,
weisse Klinik-Clogs. Er redet mit Monstern, nicht mit Menschen: Haltung zerstreut, Blick eher an allem vorbei.
NE/E/SE sind gespiegelte NW/W/SW.

Aufruf:  python gen_can.py [Ausgabeordner]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'DOCTOR VERONICA', '_Quelle_Generator'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'Hauptfiguren', '_Quelle_Generator'))

from PIL import Image  # noqa: E402

import gen_hauptfiguren as G  # noqa: E402
import gen_doctor_veronica as V  # noqa: E402
from gen_hauptfiguren import CELL, ORDER, MIRROR, K, K2, SM, SL, SD, rnd, outline, to_img  # noqa: E402

Cv = V.Cv
legs_pose = V.legs_pose
limb = V.limb

# ---------------------------------------------------------------- Farben
SW = ('#9a95a0', '#6e6a74', '#4a4550')              # Wollpullover (Mondlila-Grau): Licht, Grund, Schatten
SWH = '#e8e0f0'                                      # Maschenlicht
RIB = '#4a4550'                                      # Rippenbuendchen
RIB2 = '#2b2140'
HB, HL, HS = '#5c4033', '#7a5a43', '#3b2a22'         # Strubbelhaar: Grund, Licht, Schatten
FR, FRL = '#3b2a22', '#5c4033'                       # Hornbrille: dunkles Horn, Licht oben
GLINT = '#e8e0f0'
STRAP = ('#9c7a5a', '#7a5a43')                       # Umhaengegurt
BAG = ('#b89a72', '#9c7a5a', '#7a5a43')              # Brotbeutel: Licht, Grund, Schatten
BREAD = ('#fff1c9', '#d19a7a', '#9c7a5a')            # Brot: Krume, Kruste hell, Kruste dunkel

G.B1, G.B2, G.B3 = '#5c4033', '#7a5a43', '#9c7a5a'   # Becken (legs_pose zeichnet es mit B1..B3)

# Hose (braune Cordhose) und weisse Klinik-Clogs ueber die Bein-Palette der Hauptfiguren (leg() liest G.LEGPAL)
G.LEGPAL.update(
    pants=('#5c4033', '#7a5a43', '#9c7a5a'), pants_dark=('#3b2a22', '#5c4033', '#7a5a43'),
    boot=('#e8e0f0', '#fff1c9', '#9a95a0'), boot_dark=('#9a95a0', '#9a95a0', '#6e6a74'),
    sole='#4a4550', sole_dark='#2b2140', edge='#9a95a0', edge_dark='#6e6a74')


# ---------------------------------------------------------------- Arme
def sleeve(cv, x1, x2, y_end, left):
    """Ueberlanger Wollaermel, am Handgelenk gestaut (Rippenbuendchen); Hand folgt unter y_end."""
    for y in range(19, y_end + 1):
        cv.R(x1, y, x2, y, SW[1])
        cv.P(x1 if left else x2, y, SW[0] if y < y_end - 2 else SW[1])
        cv.P(x2 if left else x1, y, SW[2])
    for y in range(21, y_end - 1, 3):                  # Staufalten
        cv.R(x1, y, x2, y, SW[2])
    cv.R(x1, y_end - 1, x2, y_end, RIB)
    cv.P(x1 + 1, y_end - 1, RIB2)


def hand(cv, x, y):
    """Nur Fingerspitzen schauen aus dem Aermel."""
    cv.R(x, y, x + 1, y + 1, SL)
    cv.P(x, y, SM)


# ---------------------------------------------------------------- Rumpf, Beutel
def torso_front(cv):
    """Boxiger, zu langer Pullover mit haengenden Schultern, Zopfmuster und Rundhals."""
    cv.R(18, 18, 29, 18, SW[1])
    for y in range(19, 32):
        cv.R(18, y, 29, y, SW[1])
        cv.P(18, y, SW[2])
        cv.P(29, y, SW[0] if y < 26 else SW[1])
    for y in range(20, 31):                            # Zopfmuster: zwei Maschenreihen links und rechts
        if y % 2 == 0:
            cv.P(20, y, SW[2])
            cv.P(21, y, SWH if y < 25 else SW[0])
            cv.P(26, y, SW[2])
            cv.P(27, y, SWH if y < 25 else SW[0])
        else:
            cv.P(21, y, SW[2])
            cv.P(20, y, SW[0])
            cv.P(27, y, SW[2])
            cv.P(26, y, SW[0])
    cv.R(17, 31, 30, 32, RIB)                          # Saumrippen
    for x in range(18, 30, 2):
        cv.P(x, 31, RIB2)
        cv.P(x, 32, RIB2)
    # Rundhals: dicker Kragen, Haut darueber
    cv.R(21, 18, 26, 19, RIB)
    cv.P(21, 19, RIB2)
    cv.P(26, 19, RIB2)
    cv.R(22, 17, 25, 17, SM)
    cv.R(23, 18, 24, 18, SM)


def torso_back(cv):
    cv.R(18, 18, 29, 18, SW[1])
    for y in range(19, 32):
        cv.R(18, y, 29, y, SW[1])
        cv.P(18, y, SW[2])
        cv.P(29, y, SW[0] if y < 26 else SW[1])
    for y in range(20, 31, 2):
        cv.P(20, y, SW[2])
        cv.P(21, y, SW[0])
        cv.P(26, y, SW[2])
        cv.P(27, y, SW[0])
    for y in range(20, 31):                            # Mittelnaht
        cv.P(23, y, SW[2])
    cv.R(18, 31, 29, 32, RIB)
    for x in range(19, 29, 2):
        cv.P(x, 31, RIB2)
        cv.P(x, 32, RIB2)
    cv.R(21, 18, 26, 18, RIB)
    cv.R(22, 17, 25, 17, SM)


def strap_front(cv, flip=False):
    """Umhaengegurt quer ueber die Brust (von der linken Schulter im Bild zur rechten Huefte)."""
    for y in range(19, 31):
        x = 20 + rnd((y - 19) * 0.72)
        if flip:
            x = 27 - rnd((y - 19) * 0.72)
        cv.P(x, y, STRAP[0])
        cv.P(x + 1, y, STRAP[1])


def bag_front(cv, left=False, open_=0):
    """Brotbeutel an der Huefte: Leinenbeutel mit Klappe, Brotkante schaut oben heraus."""
    x1, x2 = (17, 21) if left else (26, 30)
    cv.R(x1, 28, x2, 34, BAG[1])
    cv.R(x1, 28, x2, 29, BAG[0])
    cv.R(x1, 30, x2, 30, BAG[2])                       # Klappenkante
    cv.P(x1, 31, BAG[0])
    cv.R(x1, 34, x2, 34, BAG[2])
    cv.P(x2 if not left else x1, 31, BAG[2])
    cv.P((x1 + x2) // 2, 31, STRAP[1])                 # Verschluss
    if open_ == 0:
        cv.R(x1 + 1, 27, x1 + 3, 27, BREAD[1])         # Brot ragt oben heraus
        cv.P(x1 + 1, 27, BREAD[0])


def bag_side(cv):
    cv.R(21, 28, 26, 34, BAG[1])
    cv.R(21, 28, 26, 29, BAG[0])
    cv.R(21, 30, 26, 30, BAG[2])
    cv.R(21, 34, 26, 34, BAG[2])
    cv.P(26, 31, BAG[2])
    cv.P(22, 31, BAG[0])
    cv.R(22, 27, 24, 27, BREAD[1])
    cv.P(22, 27, BREAD[0])
    for y in range(19, 28):                            # Gurt schraeg ueber den Koerper
        cv.P(23 + rnd((y - 19) * 0.1), y, STRAP[0])
        cv.P(24 + rnd((y - 19) * 0.1), y, STRAP[1])


# ---------------------------------------------------------------- Kopf
def head_front(cv, turn, down=0):
    sx = -1 if turn else 0
    # Strubbelhaar: unregelmaessige Spitzen ueber der Kappe, Wirbel rechts
    cv.R(21, 4, 26, 4, HB)
    cv.R(20, 5, 27, 5, HB)
    cv.R(19, 6, 28, 8, HB)
    for p in ((22, 3), (23, 2), (25, 3), (26, 2), (27, 3), (20, 4), (28, 5)):
        cv.P(p[0], p[1], HB)
    for p in ((23, 3), (24, 3), (26, 3), (21, 4), (24, 5), (21, 6)):
        cv.P(p[0], p[1], HL)
    for p in ((23, 2), (22, 5), (26, 5), (20, 7), (27, 7), (24, 7)):
        cv.P(p[0], p[1], HS)
    cv.P(19, 9, HB)                                    # Haar ueber den Ohren
    cv.P(28, 9, HB)
    cv.P(19, 10, HS)
    # Gesicht, muede: Augenringe, Bartschatten
    cv.R(20, 9, 27, 15, SL)
    cv.R(21, 16, 26, 16, SL)
    cv.R(22, 17, 25, 17, SM)
    for y in range(9, 16):
        cv.P(20, y, SM)
    cv.R(21, 16, 22, 16, SM)
    cv.R(20, 9, 21, 9, HB)
    cv.R(26, 9, 27, 9, HB)
    cv.P(24, 9, HB)                                    # Stirnfransen
    cv.P(23, 9, HS)
    if turn:
        cv.R(26, 8, 28, 12, HB)
        cv.P(27, 9, HL)
        cv.P(19, 11, SL)
        cv.P(19, 12, SL)
    # grosse Hornbrille: zwei breite Glaeser (4x3), dicker Rahmen, Steg, Buegel
    for x0 in (19, 25):
        x0 += sx
        cv.R(x0, 10, x0 + 3, 10, FR)
        cv.R(x0, 12, x0 + 3, 12, FR)
        cv.P(x0, 11, FR)
        cv.P(x0 + 3, 11, FR)
        cv.P(x0 + 1, 10, FRL)
    cv.R(23 + sx, 11, 24 + sx, 11, FR)
    cv.P(18 + sx, 11, FR)
    cv.P(29 + sx, 11, FR)
    cv.P(21 + sx, 11, K)                               # Augen hinter den Glaesern
    cv.P(26 + sx, 11, K)
    cv.P(20 + sx, 11, GLINT)                           # Glanz im Glas
    cv.P(27 + sx, 11, GLINT)
    cv.P(21 + sx, 13 + down, SM)                       # Augenringe
    cv.P(26 + sx, 13 + down, SM)
    # Nase, kleiner schiefer Mund, Bartstoppeln
    cv.P(23 + sx, 13, SM)
    cv.P(24 + sx, 13, SM)
    cv.R(23 + sx, 14, 24 + sx, 14, SD)
    cv.P(22 + sx, 15, SM)
    cv.P(25 + sx, 15, SM)
    cv.P(23 + sx, 16, SM)
    cv.P(24 + sx, 16, SM)


def head_back(cv, turn):
    cv.R(21, 4, 26, 4, HB)
    cv.R(20, 5, 27, 5, HB)
    cv.R(19, 6, 28, 15, HB)
    cv.R(20, 16, 27, 16, HB)
    for p in ((22, 3), (23, 2), (25, 3), (26, 2), (27, 3), (20, 4), (28, 5)):
        cv.P(p[0], p[1], HB)
    for p in ((23, 3), (24, 3), (26, 3), (21, 5), (22, 8), (26, 9), (23, 15)):
        cv.P(p[0], p[1], HL)
    for p in ((23, 2), (22, 6), (27, 6), (24, 9), (27, 12), (22, 14)):
        cv.P(p[0], p[1], HS)
    for y in range(9, 16):                              # Strubbel: Straehnen unregelmaessig
        cv.P(21 + (y * 3) % 5, y, HL if y % 2 else HS)
    cv.P(18, 11, FR)                                   # Buegel der Brille
    cv.P(29, 11, FR)
    cv.P(18, 12, SM)
    cv.P(29, 12, SL)
    cv.R(22, 17, 25, 17, SM)
    if turn:
        cv.P(19, 11, SL)
        cv.P(19, 12, SL)
        cv.P(19, 13, SL)


def head_side(cv, down=0):
    """Profil nach links."""
    cv.R(21, 4, 26, 4, HB)
    cv.R(20, 5, 27, 5, HB)
    cv.R(20, 6, 28, 7, HB)
    cv.R(24, 8, 28, 14, HB)
    cv.R(20, 8, 23, 8, HB)
    for p in ((22, 3), (23, 2), (25, 3), (26, 2), (27, 3), (29, 6)):
        cv.P(p[0], p[1], HB)
    for p in ((23, 3), (24, 3), (22, 5), (25, 7), (27, 10), (26, 12)):
        cv.P(p[0], p[1], HL)
    for p in ((23, 2), (24, 6), (26, 9), (25, 13), (27, 13), (28, 9)):
        cv.P(p[0], p[1], HS)
    cv.R(20, 9, 23, 9, SL)
    cv.R(20, 10, 24, 15, SL)
    cv.R(19, 11, 19, 14, SL)
    cv.R(20, 16, 24, 16, SL)
    for y in range(10, 16):
        cv.P(24, y, SM)
    cv.R(20, 16, 22, 16, SM)
    cv.P(18, 12, SL)                                   # Nase
    cv.P(18, 13, SM)
    # Hornbrille im Profil: breites Glas vorn, dicker Buegel zum Ohr
    cv.R(18, 10, 22, 10, FR)
    cv.R(18, 12, 22, 12, FR)
    cv.P(18, 11, FR)
    cv.P(22, 11, FR)
    cv.R(23, 10, 26, 10, FR)
    cv.P(19, 10, FRL)
    cv.P(20, 11, GLINT)
    cv.P(21, 11, K)
    cv.P(21, 13 + down, SM)                            # Augenring
    cv.P(19, 14, SD)
    cv.P(20, 14, SD)
    cv.P(20, 15, SM)
    cv.P(22, 15, SM)
    cv.P(24, 12, SM)                                   # Ohr
    cv.R(22, 17, 25, 17, SM)
    cv.R(22, 18, 24, 18, SM)


# ---------------------------------------------------------------- Brot
def bread(cv, x, y, left=True):
    """Brotstueck (4x3) in der Hand: helle Krume vorn, Kruste oben und unten."""
    d = -1 if left else 1
    for i in range(4):
        cv.P(x + d * i, y, BREAD[1])
        cv.P(x + d * i, y + 1, BREAD[0] if i < 3 else BREAD[1])
        cv.P(x + d * i, y + 2, BREAD[2])
    cv.P(x, y + 1, BREAD[2])


def crumbs(cv, x, y, n):
    pts = ((0, 0), (2, 1), (-1, 2), (1, 3), (3, 3), (-2, 4))
    for i in range(min(n, len(pts))):
        cv.P(x + pts[i][0], y + pts[i][1], BREAD[0] if i % 2 == 0 else BREAD[1])


# Feed: Reichweite des Arms (0 = Beutel, 1 = ganz vorgestreckt und tief), Beugung, Beutelgriff, Brot sichtbar, Kruemel
FEED_REACH = [0.0, 0.0, 0.25, 0.7, 1.0, 1.0, 0.5, 0.1]
FEED_DIP = [0, 0, 1, 2, 3, 3, 1, 0]
FEED_BAG = [0, 1, 1, 0, 0, 0, 0, 0]
FEED_BREAD = [0, 0, 1, 1, 1, 1, 1, 0]
FEED_CRUMBS = [0, 0, 0, 0, 2, 4, 6, 0]


# ---------------------------------------------------------------- Oberkoerper je Ansicht
def upper_front(cv, swing, turn, mode='rest', down=0, ft=None):
    """mode: rest, run, feed. Der Beutel haengt an der rechten Hueftseite (im Bild), die rechte Hand ist die Fuetterungshand."""
    sl, sr = swing, -swing
    reach = FEED_REACH[ft] if ft is not None else 0.0
    if mode == 'run':
        ln = 5
        sleeve(cv, 15, 17, 19 + ln + sl * 2, True)
        hand(cv, 15, 20 + ln + sl * 2)
        sleeve(cv, 30, 32, 19 + ln + sr * 2, False)
        hand(cv, 31, 20 + ln + sr * 2)
    elif mode == 'feed':
        sleeve(cv, 15, 17, 25, True)
        hand(cv, 15, 26)
        if FEED_BAG[ft]:                               # Hand im Beutel
            sleeve(cv, 30, 32, 24, False)
        else:
            o = rnd(2 * reach)
            ye = 25 + rnd(6 * reach)
            sleeve(cv, 30 + o, 32 + o, ye, False)
    else:
        sleeve(cv, 15, 17, 25 + sl, True)
        hand(cv, 15, 26 + sl)
        sleeve(cv, 30, 32, 25 + sr, False)
        hand(cv, 31, 26 + sr)
    torso_front(cv)
    strap_front(cv)
    bag_front(cv, False, FEED_BAG[ft] if ft is not None else 0)
    if mode == 'feed':
        if FEED_BAG[ft]:
            hand(cv, 30, 26)
            cv.R(28, 27, 30, 29, SL)                   # Hand taucht in den Beutel
            cv.P(28, 27, SM)
        else:
            o = rnd(2 * reach)
            ye = 25 + rnd(6 * reach)
            hand(cv, 31 + o, ye + 1)
            if FEED_BREAD[ft]:
                bread(cv, 33 + o, ye + 2, False)
            if FEED_CRUMBS[ft]:
                crumbs(cv, 33 + o, ye + 6, FEED_CRUMBS[ft])
    head_front(cv, turn, down)


def upper_back(cv, swing, turn, mode='rest', ft=None):
    """Beutel haengt hinten links im Bild (Gegenseite zur Vorderansicht)."""
    sl, sr = swing, -swing
    reach = FEED_REACH[ft] if ft is not None else 0.0
    if mode == 'run':
        ln = 5
        sleeve(cv, 15, 17, 19 + ln + sl * 2, True)
        hand(cv, 15, 20 + ln + sl * 2)
        sleeve(cv, 30, 32, 19 + ln + sr * 2, False)
        hand(cv, 31, 20 + ln + sr * 2)
    elif mode == 'feed':
        sleeve(cv, 30, 32, 25, False)
        hand(cv, 31, 26)
        o = rnd(2 * reach)
        ye = 25 + rnd(5 * reach)
        sleeve(cv, 15 - o, 17 - o, ye, True)
        hand(cv, 15 - o, ye + 1)
    else:
        sleeve(cv, 15, 17, 25 + sl, True)
        hand(cv, 15, 26 + sl)
        sleeve(cv, 30, 32, 25 + sr, False)
        hand(cv, 31, 26 + sr)
    torso_back(cv)
    strap_front(cv, True)
    bag_front(cv, True, 1)
    if mode == 'feed' and FEED_BREAD[ft] and reach > 0.3:
        o = rnd(2 * reach)
        ye = 25 + rnd(5 * reach)
        bread(cv, 14 - o, ye + 2, True)
    head_back(cv, turn)


def upper_side(cv, swing_a, mode='rest', down=0, ft=None):
    """Seitenansicht nach links (W)."""
    run = mode == 'run'
    end = 25 if run else 27
    reach = FEED_REACH[ft] if ft is not None else 0.0
    if mode != 'feed':
        far_hx = 24 + rnd(-swing_a * (5 if run else 3))
        for y in range(19, end + 1):
            x = rnd(24 + (far_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, SW[2])
        cv.R(far_hx - 1, end, far_hx, end + 1, SM)
    else:
        for y in range(19, 27):
            cv.R(23, y, 25, y, SW[2])
        cv.R(23, 26, 24, 27, SM)
    # Rumpf
    cv.R(21, 18, 26, 18, SW[1])
    for y in range(19, 32):
        cv.R(20, y, 27, y, SW[1])
        cv.P(20, y, SW[0] if y < 26 else SW[1])
        cv.P(27, y, SW[2])
        cv.P(26, y, SW[2] if y > 22 else SW[1])
    for y in range(20, 31, 2):
        cv.P(22, y, SW[2])
        cv.P(23, y + 1, SW[0])
    cv.R(20, 31, 27, 32, RIB)
    for x in range(21, 27, 2):
        cv.P(x, 31, RIB2)
        cv.P(x, 32, RIB2)
    cv.R(21, 18, 25, 19, RIB)
    cv.R(22, 17, 25, 17, SM)
    bag_side(cv)
    # naher Arm
    if mode == 'feed':
        ex, ey = rnd(23 - 2 * reach), rnd(23 + 1 * reach)
        hx, hy = rnd(22 - 8 * reach), rnd(26 + 4 * reach)
        limb(cv, [(24, 19), (ex, ey), (hx, hy)], SW[1], SW[2], SW[0])
        cv.R(hx - 1, hy - 1, hx + 1, hy + 1, RIB)
        if FEED_BAG[ft]:
            cv.R(21, 27, 23, 29, SL)
        else:
            cv.R(hx - 2, hy, hx - 1, hy + 1, SL)
            if FEED_BREAD[ft]:
                bread(cv, hx - 3, hy, True)
            if FEED_CRUMBS[ft]:
                crumbs(cv, hx - 5, hy + 4, FEED_CRUMBS[ft])
    else:
        near_hx = 24 + rnd(swing_a * (5 if run else 3))
        for y in range(19, end + 1):
            x = rnd(24 + (near_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, SW[1])
            cv.P(x - 1, y, SW[2])
            cv.P(x + 1, y, SW[0])
        cv.R(near_hx - 1, end - 1, near_hx + 1, end, RIB)
        cv.R(near_hx - 1, end + 1, near_hx, end + 2, SL)
        cv.P(near_hx - 1, end + 1, SM)
    head_side(cv, down)


# ---------------------------------------------------------------- Zusammenbau
def render(view, phase, bob, mode, ft=None):
    """mode: idle, walk, run, feed (ft = Bildnummer 0..7). Ein Frame als Pixel-Raster."""
    real = MIRROR.get(view, view)
    cv = Cv()
    run = mode == 'run'
    if run:
        legs_pose(cv, real, phase, ampx=7.0, ampy=2.2, lift_h=3.6)
    else:
        legs_pose(cv, real, phase)
    cv.dy = bob + (FEED_DIP[ft] if mode == 'feed' else 0)
    swing = 0 if phase is None else math.sin(2 * math.pi * phase)
    if run:
        swing = 1.0 if swing > 0.35 else (-1.0 if swing < -0.35 else 0.0)
        if real in ('W', 'SW'):
            cv.dx = -1
    arm = 'run' if run else ('feed' if mode == 'feed' else 'rest')
    if real == 'W':
        upper_side(cv, swing, arm, 0, ft)
    elif real in ('S', 'SW'):
        upper_front(cv, rnd(swing), 1 if real == 'SW' else 0, arm, 0, ft)
    else:
        upper_back(cv, rnd(swing), 1 if real == 'NW' else 0, arm, ft)
    buf = outline(cv.b)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return buf


IDLE_BOB = [0, 0, 0, 1, 1, 0]
WALK_BOB = [0, 1, 1, 0, 0, 1, 1, 0]
RUN_BOB = [0, 2, 1, 0, 0, 2, 1, 0]
FEED_BOB = [0, 0, 0, 0, 0, 0, 0, 0]


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    stand = Image.new('RGBA', (8 * CELL, CELL))
    idle = Image.new('RGBA', (6 * CELL, 8 * CELL))
    walk = Image.new('RGBA', (8 * CELL, 8 * CELL))
    run = Image.new('RGBA', (8 * CELL, 8 * CELL))
    feed = Image.new('RGBA', (8 * CELL, 8 * CELL))
    for r, v in enumerate(ORDER):
        stand.paste(to_img(render(v, None, 0, 'idle')), (r * CELL, 0))
        for c, b in enumerate(IDLE_BOB):
            idle.paste(to_img(render(v, None, b, 'idle')), (c * CELL, r * CELL))
        for c, b in enumerate(WALK_BOB):
            walk.paste(to_img(render(v, c / 8.0, b, 'walk')), (c * CELL, r * CELL))
        for c, b in enumerate(RUN_BOB):
            run.paste(to_img(render(v, c / 8.0, b, 'run')), (c * CELL, r * CELL))
        for c in range(8):
            feed.paste(to_img(render(v, None, FEED_BOB[c], 'feed', c)), (c * CELL, r * CELL))
    stand.save(os.path.join(outdir, 'can_stand_8dir.png'))
    idle.save(os.path.join(outdir, 'can_idle_sheet.png'))
    walk.save(os.path.join(outdir, 'can_walk_sheet.png'))
    run.save(os.path.join(outdir, 'can_run_sheet.png'))
    feed.save(os.path.join(outdir, 'can_feed_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'ANIMATIONS_8DIR')
    build(out)
    print('ok', os.path.abspath(out))
