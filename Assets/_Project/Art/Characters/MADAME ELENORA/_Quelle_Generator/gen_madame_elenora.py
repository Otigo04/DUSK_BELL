"""Madame Elenora: Idle (6), Walk (8), Run (8) und Invite (8, Einladungsgeste) in 8 Richtungen, 56x56-Raster.

Gleiches Raster, gleiche Zeilenreihenfolge (S, SW, W, NW, N, NE, E, SE) und gleiche Beinmechanik wie Hauptfiguren, Doctor Veronica und
Baker Mara (gen_doctor_veronica.py wird als Bibliothek genutzt). Nur Hex-Werte der Nightward-Palette.
Aussehen laut NPC-Doku: Ende 30, schwarze Haare hochgesteckt, rotes Kleid (Stoff Rot gedaempft #7a2e3a, Akzent #c4636b), schwarze Handschuhe.
Figur: hochgewachsen und aufrecht, Etuikleid mit Guertel, kurze Aermel, lange Handschuhe, dunkle Struempfe, Pumps.
Haltung: eisig und kontrolliert. Idle: Haende vor dem Koerper gefaltet, Gehen: kleine Schritte (enger Rock), kaum Armschwung.
Schwarz = die dunklen Violett-Toene der Palette (#2b2140, #3d2e4a, #4f3d5c), nie #1a1526 (das ist die Outline).
NE/E/SE sind gespiegelte NW/W/SW.

Aufruf:  python gen_madame_elenora.py [Ausgabeordner]
"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
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
DR = ('#c4636b', '#7a2e3a', '#3d2e4a')               # Kleid: Licht (Akzent Rose), Grund, Schatten (Violett)
DRD = '#2b2140'                                      # Kleid: tiefste Falte
GL = ('#4f3d5c', '#3d2e4a', '#2b2140')               # Handschuh: Licht, Grund, Schatten
HK = ('#6b5a7a', '#4f3d5c', '#3d2e4a', '#2b2140')    # Haar (schwarz): Glanz, Licht, Grund, Schatten
LIP = '#7a2e3a'
ROSE = '#c4636b'
IRIS = '#6b7fb8'                                     # eisblaue Iris (Palette: Stoff Blau hell)
GOLD, GOLD2 = '#ffd27a', '#ffa550'

# Struempfe und Pumps ueber die Bein-Palette der Hauptfiguren (leg() liest G.LEGPAL)
G.LEGPAL.update(
    pants=('#3d2e4a', '#4f3d5c', '#6b5a7a'), pants_dark=('#2b2140', '#3d2e4a', '#4f3d5c'),
    boot=('#2b2140', '#3d2e4a', '#2b2140'), boot_dark=('#1a1526', '#2b2140', '#1a1526'),
    sole='#1a1526', sole_dark='#1a1526', edge='#1a1526', edge_dark='#1a1526')


# ---------------------------------------------------------------- Arme (lange Handschuhe)
def sleeve_front(cv, x1, x2, y_end, left):
    """Kurzer Kleidaermel (y 19-20), darunter Handschuh bis y_end."""
    cv.R(x1, 19, x2, 20, DR[1])
    cv.P(x2 if left else x1, 19, DR[2])
    cv.P(x1 if left else x2, 19, DR[0])
    cv.P(x2 if left else x1, 20, DR[2])
    for y in range(21, y_end + 1):
        cv.R(x1, y, x2, y, GL[1])
        cv.P(x2 if left else x1, y, GL[2])
        cv.P(x1 if left else x2, y, GL[0] if y < y_end - 1 else GL[1])


def glove_hand(cv, x, y):
    cv.R(x, y, x + 1, y + 2, GL[1])
    cv.P(x, y, GL[0])
    cv.P(x + 1, y + 2, GL[2])
    cv.P(x, y + 2, GL[2])


def forearm(cv, x0, y0, x1, y1, col):
    """2 px breiter Unterarm entlang einer Linie (waagrecht -> 2 hoch, steil -> 2 breit). col = (Licht, Grund, Schatten)."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    flat = abs(x1 - x0) > abs(y1 - y0)
    for i in range(n + 1):
        x, y = rnd(x0 + (x1 - x0) * i / n), rnd(y0 + (y1 - y0) * i / n)
        if flat:
            cv.R(x, y, x, y + 1, col[1])
            cv.P(x, y, col[0])
            cv.P(x, y + 1, col[2])
        else:
            cv.R(x, y, x + 1, y, col[1])
            cv.P(x, y, col[0] if x1 < x0 else col[1])
            cv.P(x + 1, y, col[2])


def palm_hand(cv, x, y, left=True):
    """Handschuh-Hand mit Handflaeche nach oben (flache Geste): helle Handflaeche oben, Daumen angedeutet. (x, y) = Handwurzel."""
    d = -1 if left else 1                              # Richtung, in die die Finger zeigen
    for i in range(3):
        cv.P(x + d * i, y, GL[0])
        cv.P(x + d * i, y + 1, GL[1])
    cv.P(x + d * 3, y, GL[0])
    cv.P(x + d * 1, y + 2, GL[2])
    cv.P(x + d * 2, y + 2, GL[2])
    cv.P(x, y - 1, GL[1])                              # Daumen


# ---------------------------------------------------------------- Kleid
# Rumpf und Rock von vorn/hinten: schmale Taille (y 25-28), Hueften, nach unten ausgestellter Saum (y 38)
ROWS = {18: (18, 29), 19: (18, 29), 20: (18, 29), 21: (18, 29), 22: (18, 29), 23: (18, 29), 24: (19, 28),
        25: (20, 27), 26: (20, 27), 27: (20, 27), 28: (20, 27),
        29: (19, 28), 30: (18, 29), 31: (18, 29), 32: (18, 29), 33: (18, 29), 34: (18, 29), 35: (18, 29),
        36: (17, 30), 37: (17, 30), 38: (17, 30)}


def lit_band(cv, a, b):
    """Seidenglanz: rechte Seite von Oberteil und Rock im Rose-Akzent, damit das Kleid als Rot und nicht als Braun liest."""
    lt = DR[0]
    for y in range(19, 24):
        cv.P(b - 1, y, lt)
    for y in range(30, 36):
        cv.P(b - 1, y, lt)
        cv.P(b, y, lt)
    for y in range(36, 38):
        cv.P(b, y, lt)

def dress_front(cv):
    """Taillierter Oberteil mit eckigem Ausschnitt, Guertel, enger Rock bis unter das Knie, Mittelnaht, Rosenaht."""
    base, lt, dk = DR[1], DR[0], DR[2]
    rows = ROWS
    for y, (a, b) in rows.items():
        cv.R(a, y, b, y, base)
        cv.P(a, y, dk)
        cv.P(b, y, lt if y < 24 or y > 29 else base)
    # Ausschnitt: eckig, Hals und Schluesselbein, Rosekante
    cv.R(21, 18, 26, 18, SM)
    cv.R(22, 19, 25, 19, SL)
    cv.R(22, 20, 25, 20, SL)
    cv.P(21, 19, lt)
    cv.P(26, 19, lt)
    cv.P(21, 20, lt)
    cv.P(26, 20, lt)
    cv.R(22, 21, 25, 21, lt)
    cv.P(22, 19, SM)
    cv.P(25, 19, SM)
    cv.R(23, 20, 24, 20, SM)
    # Brustabnaeher und Schatten unter der Brust
    for p in ((20, 22), (21, 22), (26, 22), (27, 22)):
        cv.P(p[0], p[1], lt)
    for x in list(range(19, 23)) + list(range(25, 29)):
        cv.P(x, 24, dk)
    cv.P(22, 23, dk)
    cv.P(25, 23, dk)
    # Guertel mit Goldschnalle
    cv.R(20, 27, 27, 28, GL[1])
    cv.R(20, 28, 27, 28, GL[2])
    cv.R(23, 27, 24, 28, GOLD)
    cv.P(24, 28, GOLD2)
    cv.P(20, 27, GL[0])
    # Rock: Hueftlicht, Mittelnaht, Saum
    for y in range(30, 38):
        cv.P(23, y, dk)
        cv.P(24, y, base)
    for y in (31, 33, 35):
        cv.P(19, y, lt)
    cv.R(17, 38, 30, 38, dk)
    cv.R(18, 39, 29, 39, DRD)
    cv.P(30, 38, lt)
    lit_band(cv, 18, 29)
    # Brosche am Ausschnitt
    cv.P(23, 21, GOLD)
    cv.P(24, 21, GOLD2)


def dress_side(cv):
    base, lt, dk = DR[1], DR[0], DR[2]
    for y in range(18, 40):
        if y <= 23:
            a, b = (19, 27) if y >= 20 else (21, 26)
        elif y <= 28:
            a, b = (21, 26)
        elif y <= 31:
            a, b = (20, 28)
        elif y <= 35:
            a, b = (19, 29)
        else:
            a, b = (19, 29)
        cv.R(a, y, b, y, base)
        cv.P(a, y, dk if y > 23 else lt)
        cv.P(b, y, dk)
    cv.R(20, 19, 21, 19, lt)
    cv.P(19, 20, lt)
    cv.P(19, 21, lt)
    cv.P(20, 22, dk)
    cv.R(19, 24, 21, 24, dk)                           # Unterkante Brust
    cv.R(21, 27, 26, 28, GL[1])                        # Guertel
    cv.R(21, 28, 26, 28, GL[2])
    cv.P(21, 27, GOLD)
    cv.P(21, 28, GOLD2)
    for y in (31, 33, 35):
        cv.P(27, y, lt)
    cv.R(19, 38, 29, 38, dk)
    cv.R(20, 39, 28, 39, DRD)
    cv.P(22, 21, GOLD)


def dress_back(cv):
    base, lt, dk = DR[1], DR[0], DR[2]
    rows = ROWS
    for y, (a, b) in rows.items():
        cv.R(a, y, b, y, base)
        cv.P(a, y, dk)
        cv.P(b, y, lt if y < 24 or y > 29 else base)
    # tiefer Ruecken-V mit Haut, Reissverschluss bis zum Guertel
    cv.R(22, 18, 25, 18, SM)
    cv.R(22, 19, 25, 19, SL)
    cv.R(23, 20, 24, 20, SL)
    cv.P(23, 21, SM)
    cv.P(24, 21, SM)
    for y in range(22, 27):
        cv.P(23, y, dk)
        cv.P(24, y, base)
    cv.P(18, 20, lt)
    cv.P(29, 21, lt)
    cv.R(20, 27, 27, 28, GL[1])
    cv.R(20, 28, 27, 28, GL[2])
    cv.P(23, 27, GL[0])
    cv.P(24, 27, GL[0])
    for y in range(30, 38):
        cv.P(23, y, dk)
        cv.P(24, y, base)
    for y in (31, 33, 35):
        cv.P(29, y, lt)
    cv.R(17, 38, 30, 38, dk)
    cv.R(18, 39, 29, 39, DRD)
    cv.P(30, 38, lt)
    lit_band(cv, 18, 29)


# ---------------------------------------------------------------- Haare, Kopf
def bun(cv, x, y):
    """Hohes Chignon, 6 Pixel breit: Glanz oben rechts, Schatten unten links."""
    hl, lt, base, sh = HK
    cv.R(x + 1, y, x + 4, y, base)
    cv.R(x, y + 1, x + 5, y + 2, base)
    cv.R(x + 1, y + 3, x + 4, y + 3, sh)
    cv.P(x + 3, y, lt)
    cv.P(x + 4, y, lt)
    cv.P(x + 4, y + 1, hl)
    cv.P(x + 2, y + 1, lt)
    cv.P(x + 5, y + 2, lt)
    cv.P(x, y + 2, sh)
    cv.P(x + 1, y + 2, sh)
    cv.P(x + 3, y + 2, sh)
    cv.P(x + 1, y + 1, sh)


def head_front(cv, turn, down=0):
    hl, lt, base, sh = HK
    sx = -1 if turn else 0
    bun(cv, 22 if turn else 21, 1)
    # Haarkappe, glatt nach hinten gezogen, Mittelscheitel leicht versetzt
    cv.R(21, 5, 26, 5, base)
    cv.R(20, 6, 27, 6, base)
    cv.R(19, 7, 28, 8, base)
    cv.R(19, 9, 20, 9, base)
    cv.R(27, 9, 28, 9, base)
    for p in ((22, 5), (23, 5), (22, 6), (25, 6), (21, 7), (26, 7)):
        cv.P(p[0], p[1], lt)
    for p in ((23, 6), (23, 7)):
        cv.P(p[0], p[1], sh)
    for p in ((24, 5), (27, 7)):
        cv.P(p[0], p[1], hl)
    for p in ((20, 8), (27, 8), (24, 7)):
        cv.P(p[0], p[1], sh)
    # Gesicht, hohe Wangenknochen, spitzes Kinn
    cv.R(21, 9, 26, 9, SL)
    cv.R(20, 10, 27, 15, SL)
    cv.R(21, 16, 26, 16, SL)
    cv.R(22, 17, 25, 17, SM)
    for y in range(10, 16):
        cv.P(20, y, SM)
    cv.R(21, 16, 22, 16, SM)
    cv.R(19, 10, 19, 13, base)
    cv.R(28, 10, 28, 13, base)
    cv.P(19, 11, lt)
    cv.P(28, 12, sh)
    if turn:
        cv.R(26, 8, 28, 13, base)
        cv.P(27, 8, hl)
        cv.P(19, 11, SL)
        cv.P(19, 12, SL)
        cv.P(19, 13, SL)
    # scharfe Brauen, schmale Augen mit Lidstrich, Nase, duenne dunkelrote Lippen
    e = 12 + down
    cv.R(21 + sx, e - 2, 22 + sx, e - 2, K2)
    cv.R(25 + sx, e - 2, 26 + sx, e - 2, K2)
    cv.P(21 + sx, e, K)                                # Auge: Lidstrich aussen, eisblaue Iris innen
    cv.P(22 + sx, e, IRIS)
    cv.P(25 + sx, e, IRIS)
    cv.P(26 + sx, e, K)
    cv.P(20 + sx, e, K2)                               # Lidstrich nach aussen gezogen
    cv.P(27 + sx, e, K2)
    cv.P(20 + sx, e - 1, K2)                           # Fluegel
    cv.P(27 + sx, e - 1, K2)
    cv.P(21 + sx, e + 1, SM)                           # Unterlid
    cv.P(26 + sx, e + 1, SM)
    cv.P(23 + sx, 13, SM)
    cv.P(24 + sx, 13, SM)
    cv.P(24 + sx, 13, SM)                              # Nase: ein Schattenpixel
    cv.R(22 + sx, 15, 25 + sx, 15, LIP)                # schmale dunkelrote Lippen, geschlossen
    cv.P(23 + sx, 15, ROSE)


def head_back(cv, turn):
    hl, lt, base, sh = HK
    bun(cv, 22 if turn else 21, 1)
    cv.R(21, 5, 26, 5, base)
    cv.R(20, 6, 27, 6, base)
    cv.R(19, 7, 28, 15, base)
    cv.R(20, 16, 27, 16, base)
    cv.R(21, 17, 26, 17, sh)
    # Franzoesischer Zopf: Rolle senkrecht ueber den Hinterkopf, Straehnen diagonal
    for y in range(7, 17):
        cv.P(22, y, sh)
        cv.P(25, y, sh)
        cv.P(23, y, lt if y % 2 == 0 else base)
        cv.P(24, y, base if y % 2 == 0 else lt)
    for p in ((21, 6), (26, 6), (20, 9), (27, 9), (20, 12), (27, 12)):
        cv.P(p[0], p[1], lt)
    for p in ((24, 8), (23, 12), (24, 15)):
        cv.P(p[0], p[1], hl)
    for y in range(8, 16):
        cv.P(19, y, sh)
        cv.P(28, y, sh)
    cv.R(22, 17, 25, 18, SM)                           # Nacken
    cv.R(22, 16, 25, 16, sh)
    if turn:
        cv.P(19, 11, SL)
        cv.P(19, 12, SL)
        cv.P(19, 13, SL)


def head_side(cv, down=0):
    """Profil nach links."""
    hl, lt, base, sh = HK
    bun(cv, 24, 2)
    cv.R(21, 5, 27, 5, base)
    cv.R(20, 6, 28, 6, base)
    cv.R(20, 7, 29, 8, base)
    cv.R(24, 9, 29, 16, base)
    for p in ((22, 5), (23, 5), (21, 6), (26, 6), (25, 8)):
        cv.P(p[0], p[1], lt)
    for p in ((27, 7), (26, 10), (27, 13)):
        cv.P(p[0], p[1], hl)
    for y in range(9, 17):
        cv.P(28, y, sh)
        if y % 2:
            cv.P(26, y, lt)
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
    e = 12 + down
    cv.R(20, e - 2, 21, e - 2, K2)                     # Braue
    cv.P(21, e, IRIS)
    cv.P(22, e, K)
    cv.P(22, e - 1, K2)
    cv.P(21, e + 1, SM)
    cv.P(19, 15, LIP)
    cv.P(20, 15, LIP)
    cv.R(22, 17, 25, 17, SM)
    cv.R(22, 18, 24, 18, SM)


# ---------------------------------------------------------------- Oberkoerper je Ansicht
def upper_front(cv, swing, turn, mode='rest', down=0, ext=0.0):
    sl, sr = swing, -swing
    if mode == 'invite':
        # rechter Arm der Figur (links im Bild) oeffnet sich zur Seite, Handflaeche oben; der andere Arm bleibt am Guertel
        sleeve_front(cv, 15, 17, 23, True)
        sleeve_front(cv, 30, 32, 23, False)
        for i in range(5):
            cv.R(31 - i, 24 + i, 32 - i, 24 + i, GL[1])
            cv.P(32 - i, 24 + i, GL[2])
        hx, hy = rnd(20 - 11 * ext), rnd(27 - 3 * ext)
        forearm(cv, 16, 24, hx, hy, (GL[0], GL[1], GL[2]))
    elif mode == 'fold':
        # Oberarme gerade, Unterarme (2 px breit) laufen schraeg nach innen, Haende gefaltet vor dem Guertel
        sleeve_front(cv, 15, 17, 23, True)
        sleeve_front(cv, 30, 32, 23, False)
        for i in range(5):
            cv.R(16 + i, 24 + i, 17 + i, 24 + i, GL[1])
            cv.P(16 + i, 24 + i, GL[0])
            cv.R(31 - i, 24 + i, 32 - i, 24 + i, GL[1])
            cv.P(32 - i, 24 + i, GL[2])
    elif mode == 'run':
        ln = 5
        sleeve_front(cv, 15, 17, 19 + ln + sl * 2, True)
        glove_hand(cv, 15, 20 + ln + sl * 2)
        sleeve_front(cv, 30, 32, 19 + ln + sr * 2, False)
        glove_hand(cv, 31, 20 + ln + sr * 2)
    else:
        sleeve_front(cv, 15, 17, 25 + sl, True)
        glove_hand(cv, 15, 26 + sl)
        sleeve_front(cv, 30, 32, 25 + sr, False)
        glove_hand(cv, 31, 26 + sr)
    dress_front(cv)
    if mode == 'invite':
        if ext < 0.2:
            cv.R(21, 28, 26, 30, GL[1])
            cv.R(21, 28, 26, 28, GL[0])
            cv.R(21, 30, 26, 30, GL[2])
            cv.P(23, 29, GL[2])
            cv.P(24, 29, GL[2])
        else:
            cv.R(24, 28, 26, 30, GL[1])                # die ruhende Hand liegt am Guertel
            cv.R(24, 28, 26, 28, GL[0])
            cv.R(24, 30, 26, 30, GL[2])
            palm_hand(cv, hx, hy, True)
    elif mode == 'fold':
        cv.R(21, 28, 26, 30, GL[1])                    # gefaltete Haende
        cv.R(21, 28, 26, 28, GL[0])
        cv.R(21, 30, 26, 30, GL[2])
        cv.P(23, 29, GL[2])
        cv.P(24, 29, GL[2])
    head_front(cv, turn, down)


def upper_back(cv, swing, turn, mode='rest', ext=0.0):
    sl, sr = swing, -swing
    if mode == 'invite':
        sleeve_front(cv, 30, 32, 25, False)
        glove_hand(cv, 31, 26)
        sleeve_front(cv, 15, 17, 23, True)
        hx, hy = rnd(16 - 5 * ext), rnd(25 - 2 * ext)
        forearm(cv, 16, 24, hx, hy, (GL[0], GL[1], GL[2]))
        palm_hand(cv, hx, hy, True) if ext >= 0.2 else glove_hand(cv, 15, 24)
    elif mode == 'fold':
        sleeve_front(cv, 15, 17, 25, True)
        glove_hand(cv, 15, 26)
        sleeve_front(cv, 30, 32, 25, False)
        glove_hand(cv, 31, 26)
    elif mode == 'run':
        ln = 5
        sleeve_front(cv, 15, 17, 19 + ln + sl * 2, True)
        glove_hand(cv, 15, 20 + ln + sl * 2)
        sleeve_front(cv, 30, 32, 19 + ln + sr * 2, False)
        glove_hand(cv, 31, 20 + ln + sr * 2)
    else:
        sleeve_front(cv, 15, 17, 25 + sl, True)
        glove_hand(cv, 15, 26 + sl)
        sleeve_front(cv, 30, 32, 25 + sr, False)
        glove_hand(cv, 31, 26 + sr)
    dress_back(cv)
    head_back(cv, turn)


def upper_side(cv, swing_a, mode='rest', down=0, ext=0.0):
    """Seitenansicht nach links (W)."""
    run = mode == 'run'
    end = 25 if run else 27
    if mode in ('fold', 'invite'):
        limb(cv, [(24, 19), (22, 23), (19, 27)], GL[2], GL[2], GL[2])
        cv.R(17, 27, 19, 29, GL[2])
    else:
        far_hx = 24 + rnd(-swing_a * (5 if run else 2))
        for y in range(19, end + 1):
            x = rnd(24 + (far_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, GL[2])
        cv.R(far_hx - 1, end, far_hx, end + 2, GL[2])
    dress_side(cv)
    if mode == 'invite':
        ex, ey = rnd(23 - 3 * ext), rnd(23 - 0 * ext)
        hx, hy = rnd(19 - 7 * ext), rnd(26 - 4 * ext)
        limb(cv, [(24, 19), (ex, ey), (hx + 1, hy)], GL[1], GL[2], GL[0])
        cv.R(23, 19, 25, 20, DR[1])
        if ext < 0.2:
            cv.R(17, 26, 19, 28, GL[1])
            cv.P(17, 26, GL[0])
            cv.R(18, 28, 19, 29, GL[2])
        else:
            palm_hand(cv, hx + 1, hy, True)
    elif mode == 'fold':
        limb(cv, [(24, 19), (23, 23), (20, 26)], GL[1], GL[2], GL[0])
        cv.R(23, 19, 25, 20, DR[1])
        cv.R(17, 26, 19, 28, GL[1])
        cv.P(17, 26, GL[0])
        cv.R(18, 28, 19, 29, GL[2])
    else:
        near_hx = 24 + rnd(swing_a * (5 if run else 2))
        cv.R(near_hx - 1, 19, near_hx + 1, 20, DR[1])
        cv.P(near_hx - 1, 19, DR[0])
        for y in range(21, end + 1):
            x = rnd(24 + (near_hx - 24) * (y - 19) / float(end - 19))
            cv.R(x - 1, y, x + 1, y, GL[1])
            cv.P(x + 1, y, GL[2])
            cv.P(x - 1, y, GL[0])
        cv.R(near_hx - 1, end, near_hx, end + 2, GL[1])
        cv.P(near_hx - 1, end, GL[0])
    head_side(cv, down)


# ---------------------------------------------------------------- Zusammenbau
def render(view, phase, bob, mode, ext=0.0):
    """mode: idle, walk, run, invite (ext = Oeffnung des Arms 0..1). Ein Frame als Pixel-Raster."""
    real = MIRROR.get(view, view)
    cv = Cv()
    run = mode == 'run'
    if run:
        legs_pose(cv, real, phase, ampx=6.0, ampy=2.0, lift_h=3.4)
    elif mode == 'walk':
        legs_pose(cv, real, phase, ampx=3.8, ampy=1.1, lift_h=1.8)   # enger Rock: kleine Schritte
    else:
        legs_pose(cv, real, phase)
    cv.dy = bob
    swing = 0 if phase is None else math.sin(2 * math.pi * phase)
    arm = 'run' if run else ('fold' if mode == 'idle' else ('invite' if mode == 'invite' else 'rest'))
    if mode == 'walk':
        swing = 0.0 if abs(swing) < 0.5 else (1.0 if swing > 0 else -1.0) * 0.5
    if run:
        swing = 1.0 if swing > 0.35 else (-1.0 if swing < -0.35 else 0.0)
        if real in ('W', 'SW'):
            cv.dx = -1
    if real == 'W':
        upper_side(cv, swing, arm, 0, ext)
    elif real in ('S', 'SW'):
        upper_front(cv, rnd(swing), 1 if real == 'SW' else 0, arm, 0, ext)
    else:
        upper_back(cv, rnd(swing), 1 if real == 'NW' else 0, arm, ext)
    buf = outline(cv.b)
    if view in MIRROR:
        buf = [row[::-1] for row in buf]
    return buf


IDLE_BOB = [0, 0, 0, 1, 1, 0]
WALK_BOB = [0, 1, 1, 0, 0, 1, 1, 0]
RUN_BOB = [0, 2, 1, 0, 0, 2, 1, 0]
INVITE_EXT = [0.0, 0.3, 0.7, 1.0, 1.0, 1.0, 0.55, 0.15]   # Arm oeffnet sich, haelt, schliesst sich
INVITE_BOB = [0, 0, 0, 1, 1, 0, 0, 0]                      # kurzes Nicken im Halten


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    stand = Image.new('RGBA', (8 * CELL, CELL))
    idle = Image.new('RGBA', (6 * CELL, 8 * CELL))
    walk = Image.new('RGBA', (8 * CELL, 8 * CELL))
    run = Image.new('RGBA', (8 * CELL, 8 * CELL))
    invite = Image.new('RGBA', (8 * CELL, 8 * CELL))
    for r, v in enumerate(ORDER):
        stand.paste(to_img(render(v, None, 0, 'idle')), (r * CELL, 0))
        for c, b in enumerate(IDLE_BOB):
            idle.paste(to_img(render(v, None, b, 'idle')), (c * CELL, r * CELL))
        for c, b in enumerate(WALK_BOB):
            walk.paste(to_img(render(v, c / 8.0, b, 'walk')), (c * CELL, r * CELL))
        for c, b in enumerate(RUN_BOB):
            run.paste(to_img(render(v, c / 8.0, b, 'run')), (c * CELL, r * CELL))
        for c in range(8):
            invite.paste(to_img(render(v, None, INVITE_BOB[c], 'invite', INVITE_EXT[c])), (c * CELL, r * CELL))
    stand.save(os.path.join(outdir, 'madame_elenora_stand_8dir.png'))
    idle.save(os.path.join(outdir, 'madame_elenora_idle_sheet.png'))
    walk.save(os.path.join(outdir, 'madame_elenora_walk_sheet.png'))
    run.save(os.path.join(outdir, 'madame_elenora_run_sheet.png'))
    invite.save(os.path.join(outdir, 'madame_elenora_invite_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'ANIMATIONS_8DIR')
    build(out)
    print('ok', os.path.abspath(out))
