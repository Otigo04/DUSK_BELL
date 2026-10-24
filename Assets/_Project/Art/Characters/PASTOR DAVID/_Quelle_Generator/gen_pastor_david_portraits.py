"""Pastor David: Portraits 64x64, nur Hex-Werte der Nightward-Palette.

Ausdruecke laut Doku: Ruhe (Standard), Warm (Zuordnung offen -> wie bei Mara und Veronica als 'compassionate' abgelegt),
Misstrauisch, Veraengstigt. Dazu Blinzeln (Ruhe mit geschlossenen Augen) und die Sprechmuender A, E, O.

Aufruf:  python gen_pastor_david_portraits.py [Ausgabeordner]
"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'DOCTOR VERONICA', '_Quelle_Generator'))

import gen_doctor_veronica_portraits as VP  # noqa: E402
from gen_doctor_veronica_portraits import Pn, outline, to_img, sym, W, K, K2, SL, SM, SD, WARM  # noqa: E402

SHIRT = ('#6b5a7a', '#3d2e4a', '#2b2140')       # Priesterhemd: Licht, Grund, Schatten
VEST = ('#4a7a4f', '#2f5a3c', '#1e3a2b')        # Strickweste
TAB, TABL = '#e8e0f0', '#fff1c9'
HB, HL, HS, HD = '#5c4033', '#9a95a0', '#3b2a22', '#1a1526'   # Haar: braun, graue Schlaefen, dunkel
FRAME = '#2b2140'
GLINT = '#e8e0f0'
IRIS = '#5c4033'
BTN = '#b89a72'
WHITE = '#e8e0f0'


# ---------------------------------------------------------------- Koerper
def bust(p):
    for y in range(49, W):
        hw = 15 + (y - 49) * 1.7
        for x in range(max(0, int(32 - hw)), min(W, int(32 + hw) + 1)):
            c = SHIRT[1]
            if x >= 44:
                c = SHIRT[2]
            elif x <= 14:
                c = SHIRT[0] if (x + y) % 2 == 0 else SHIRT[1]
            p.P(x, y, c)
    # Strickweste mit V-Ausschnitt in der Mitte
    for y in range(54, W):
        hw = 14 + (y - 54) * 0.9
        for x in range(int(round(32 - hw)), int(round(32 + hw))):
            c = VEST[1]
            if x >= 38:
                c = VEST[2] if (x + y) % 2 == 0 or x >= 42 else VEST[1]
            elif x <= 26 and (x + y) % 2 == 0:
                c = VEST[0]
            p.P(x, y, c)
        vh = max(1.5, 5.0 - (y - 54) * 0.4)
        for x in range(int(round(32 - vh)), int(round(32 + vh))):
            p.P(x, y, SHIRT[1] if x < 33 else SHIRT[2])
    # Rippen
    for y in range(56, W):
        for x in (20, 23, 26, 37, 40, 43):
            if (y // 2) % 2 == 0 and VEST[1] == '#2f5a3c':
                if p.b[y][x] in (VEST[1], VEST[0]):
                    p.P(x, y, VEST[2])
    for y in (60, 63):
        p.R(31, y, 32, y, BTN)
    # Hals
    p.R(27, 40, 36, 49, SL)
    p.R(27, 40, 27, 49, SM)
    p.R(34, 40, 36, 49, SM)
    p.R(27, 44, 36, 46, SM)
    for x in range(28, 34):
        p.P(x, 44, SM)
    # Priesterkragen: schwarzes Band mit hellem Einsatz
    p.R(24, 47, 39, 50, SHIRT[2])
    p.R(24, 47, 24, 48, SHIRT[1])
    p.R(30, 48, 33, 53, TAB)
    p.R(30, 48, 31, 53, TABL)
    p.R(33, 50, 33, 53, '#9a95a0')


# ---------------------------------------------------------------- Kopf
def head(p):
    # Ohren
    p.E(18.0, 31, 2.4, 3.4, SL)
    p.E(46.0, 31, 2.4, 3.4, SM)
    p.P(18, 31, SM)
    p.P(18, 32, SM)
    # Gesicht, kantiger Kiefer
    p.E(32, 28.5, 13.6, 16.3, SL)
    p.E(32, 34, 13.0, 11.5, SL)
    for y in range(W):
        for x in range(W):
            if p.b[y][x] == SL and 18.5 < x < 45.5:
                if x >= 41:
                    p.P(x, y, SM)
                elif x >= 39 and (x + y) % 2 == 0:
                    p.P(x, y, SM)
    for x in range(24, 41):                                      # Kinnschatten
        p.P(x, 44, SM)
    # Lachfalten und Nasolabialfalten (50 Jahre)
    for (x, y) in ((26, 36), (25, 37), (25, 38), (24, 39)):
        p.P(x, y, SM)
    for (x, y) in ((sym(26), 36), (sym(25), 37), (sym(25), 38), (sym(24), 39)):
        p.P(x, y, SD)


def hair(p):
    """Kurzes Haar, seitlich gescheitelt, graue Schlaefen."""
    def hairline(x):
        d = (x + 0.5 - 32) / 14.0
        return 15.0 + 6.0 * d * d
    for y in range(W):
        for x in range(W):
            if p.inE(x, y, 32, 22, 16.2, 15.0) and (y < hairline(x) or (abs(x + 0.5 - 32) >= 12.4 and y <= 27)):
                k = int(math.atan2(y + 0.5 - 6, x + 0.5 - 24) * 8)
                c = HB
                if k % 3 == 0:
                    c = HS
                if abs(x + 0.5 - 32) >= 11 and y >= 17:
                    c = HL if (x + y) % 2 == 0 or y >= 22 else HB   # graue Schlaefen
                p.P(x, y, c)
    for y in range(11, 17):                                      # Scheitel
        p.P(23, y, HL)


def glasses(p):
    """Runde Brille: zwei Ringe, Steg, Buegel. Eine Zeile Glanz im Glas."""
    for cx in (24.5, 39.5):
        for y in range(W):
            for x in range(W):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - 28.5)
                if 4.3 <= d <= 5.5:
                    p.P(x, y, FRAME)
        p.P(int(cx) - 2, 25, GLINT)
        p.P(int(cx) - 1, 25 - 1 + 1, GLINT) if False else None
    p.R(30, 27, 33, 27, FRAME)                                  # Steg
    p.R(19, 27, 20, 27, FRAME)                                  # Buegel
    p.P(18, 28, FRAME)
    p.R(43, 27, 44, 27, FRAME)
    p.P(45, 28, FRAME)


def brows(p, ys_left, ys_right):
    for i, x in enumerate(range(20, 29)):
        p.P(x, ys_left[i], HB)
        p.P(x, ys_left[i] - 1, HD)
        p.P(sym(x), ys_right[i], HB)
        p.P(sym(x), ys_right[i] - 1, HD)


def eye(p, left, mode):
    """Auge hinter dem Glas. Linkes Auge um x 24.5, rechtes gespiegelt."""
    X = (lambda x: x) if left else sym
    y0 = 28
    xs = range(22, 27)
    if mode == 'closed':
        for x in xs:
            p.P(X(x), y0 + 1, K2)
        for x in range(23, 26):
            p.P(X(x), y0 + 2, SM)
        return
    rows = {'open': (y0 - 1, y0, y0 + 1), 'soft': (y0, y0 + 1), 'side': (y0, y0 + 1), 'wide': (y0 - 2, y0 - 1, y0, y0 + 1, y0 + 2)}[mode]
    for y in rows:
        for x in xs:
            p.P(X(x), y, WHITE)
    if mode == 'soft':
        for x in xs:
            p.P(X(x), y0 + 1, SL)                               # Lachaugen: Unterlid hoch
        rows = (y0,)
    ix = {'open': 23, 'soft': 23, 'side': 25, 'wide': 24}[mode]
    n = 2
    for dx in range(n):
        for y in rows:
            if mode == 'wide' and y in (rows[0], rows[-1]):
                continue
            p.P(X(ix + dx), y, IRIS)
    mid = rows[len(rows) // 2]
    p.P(X(ix + 1), mid, K)
    p.P(X(ix), rows[0] if mode != 'wide' else rows[1], WARM)
    top = rows[0] - 1
    for x in xs:
        p.P(X(x), top, SM if mode != 'side' else FRAME)         # Oberlid; bei 'side' schweres Lid


def nose(p):
    for y in range(29, 36):
        p.P(33, y, SM)
    p.P(31, 33, WARM)
    p.R(30, 36, 33, 36, SM)
    p.P(29, 36, SD)
    p.P(34, 36, SD)
    p.P(30, 37, SD)
    p.P(33, 37, SD)


def mouth(p, kind):
    y = 40
    if kind == 'calm':
        p.R(28, y, 36, y, SD)
        p.R(29, y + 1, 35, y + 1, SM)
        p.R(30, y + 2, 34, y + 2, SM)
        p.P(27, y - 1, SM)
        p.P(37, y - 1, SM)
    elif kind == 'warm':
        p.R(29, y, 35, y, SD)
        p.R(27, y - 1, 28, y - 1, SD)
        p.R(36, y - 1, 37, y - 1, SD)
        p.R(29, y + 1, 35, y + 1, SM)
        p.R(30, y + 2, 34, y + 2, SM)
        p.P(26, y - 2, SM)
        p.P(38, y - 2, SM)
        p.P(20, 31, SM)                                         # Krähenfüße
        p.P(44, 31, SD)
    elif kind == 'pressed':                                     # misstrauisch: Lippen schmal und schief
        p.R(29, y, 35, y, SD)
        p.P(28, y + 1, SD)
        p.R(36, y - 1, 37, y - 1, SD)
        p.R(30, y + 1, 34, y + 1, SM)
        p.P(38, y - 2, SM)
    elif kind == 'scared':
        p.R(29, y - 1, 35, y - 1, SD)
        p.R(30, y, 34, y + 2, K2)
        p.R(31, y + 2, 33, y + 2, SD)
        p.R(30, y + 3, 34, y + 3, SM)
    elif kind == 'A':
        p.R(28, y - 1, 36, y - 1, SD)
        p.R(29, y, 35, y + 3, K2)
        p.R(30, y + 2, 34, y + 3, SD)
        p.R(30, y + 4, 34, y + 4, SM)
    elif kind == 'E':
        p.R(28, y - 1, 36, y - 1, SD)
        p.R(28, y, 36, y + 1, K2)
        p.R(29, y + 2, 35, y + 2, SM)
        p.R(30, y + 3, 34, y + 3, SM)
    elif kind == 'O':
        p.R(30, y - 1, 34, y - 1, SD)
        p.R(30, y, 34, y + 3, K2)
        p.R(31, y + 4, 33, y + 4, K2)
        p.R(29, y + 1, 29, y + 2, SM)
        p.R(35, y + 1, 35, y + 2, SD)
        p.R(31, y + 5, 33, y + 5, SM)


EXPR = {
    'calm':          dict(eye='open',   mouth='calm',    bl=[23, 22, 22, 21, 21, 21, 22, 22, 23], br=[23, 22, 22, 21, 21, 21, 22, 22, 23]),
    'compassionate': dict(eye='soft',   mouth='warm',    bl=[24, 23, 23, 22, 22, 21, 21, 20, 20], br=[24, 23, 23, 22, 22, 21, 21, 20, 20]),
    'suspicious':    dict(eye='side',   mouth='pressed', bl=[22, 21, 20, 19, 19, 20, 21, 21, 22], br=[24, 24, 25, 25, 25, 26, 26, 26, 27]),
    'scared':        dict(eye='wide',   mouth='scared',  bl=[21, 20, 20, 19, 18, 18, 17, 17, 16], br=[21, 20, 20, 19, 18, 18, 17, 17, 16]),
    'blink':         dict(eye='closed', mouth='calm',    bl=[23, 22, 22, 21, 21, 21, 22, 22, 23], br=[23, 22, 22, 21, 21, 21, 22, 22, 23]),
    'talk_A':        dict(eye='open',   mouth='A',       bl=[23, 22, 22, 21, 21, 21, 22, 22, 23], br=[23, 22, 22, 21, 21, 21, 22, 22, 23]),
    'talk_E':        dict(eye='open',   mouth='E',       bl=[23, 22, 22, 21, 21, 21, 22, 22, 23], br=[23, 22, 22, 21, 21, 21, 22, 22, 23]),
    'talk_O':        dict(eye='open',   mouth='O',       bl=[23, 22, 22, 21, 21, 21, 22, 22, 23], br=[23, 22, 22, 21, 21, 21, 22, 22, 23]),
}
ORDER = ['calm', 'compassionate', 'suspicious', 'scared', 'blink', 'talk_A', 'talk_E', 'talk_O']


def render(name):
    e = EXPR[name]
    p = Pn()
    bust(p)
    head(p)
    hair(p)
    eye(p, True, e['eye'])
    eye(p, False, e['eye'])
    glasses(p)
    brows(p, e['bl'], e['br'])
    nose(p)
    mouth(p, e['mouth'])
    return outline(p)


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    sheet = Image.new('RGBA', (len(ORDER) * W, W))
    for i, n in enumerate(ORDER):
        im = to_img(render(n))
        im.save(os.path.join(outdir, 'david_%s.png' % n))
        sheet.paste(im, (i * W, 0))
    sheet.save(os.path.join(outdir, '..', 'portrait_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'portraits')
    build(out)
    print('ok', os.path.abspath(out))
