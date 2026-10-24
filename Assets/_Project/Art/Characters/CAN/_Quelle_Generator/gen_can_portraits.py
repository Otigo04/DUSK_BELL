"""Can: Portraits 64x64, nur Hex-Werte der Nightward-Palette.

Ausdruecke laut Doku: Ruhe (Standard), Mitfuehlend, Veraengstigt, Entschlossen.
Dazu Blinzeln (Ruhe mit geschlossenen Augen) und die Sprechmuender A, E, O (Basis: Ruhe), wie bei den anderen Figuren.
Der Hintergrund kommt aus der UI, die PNGs sind transparent.

Aussehen: Mitte 30, muedes Gesicht mit Bartstoppeln und Augenringen, grosse dunkle Hornbrille (Erkennungsmerkmal), strubbelige braune Haare mit
abstehenden Straehnen, Blick meist leicht an allem vorbei (zerstreut), graues Wollpullover mit dickem Rundhals, Umhaengegurt des Brotbeutels.

Aufruf:  python gen_can_portraits.py [Ausgabeordner]
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

HB, HL, HS = '#5c4033', '#7a5a43', '#3b2a22'         # Haar: Grund, Licht, Schatten
FR, FRL = '#3b2a22', '#5c4033'                       # Hornbrille: Horn, Licht
SW = ('#9a95a0', '#6e6a74', '#4a4550')               # Pullover: Licht, Grund, Schatten
SWH = '#e8e0f0'
RIB, RIB2 = '#4a4550', '#2b2140'
STRAP = ('#9c7a5a', '#7a5a43')
IRIS = '#5c4033'
SCL = '#e8e0f0'


def hnoise(x, y, m):
    return ((x * 73856093) ^ (y * 19349663)) % m


# ---------------------------------------------------------------- Koerper
def bust(p):
    base, lt, dk = SW[1], SW[0], SW[2]
    for y in range(50, W):
        hw = 19 + (y - 50) * 1.7
        x1, x2 = int(round(32 - hw)), int(round(31 + hw))
        for x in range(max(0, x1), min(W - 1, x2) + 1):
            c = base
            if x >= 46:
                c = dk
            elif x >= 43 and (x + y) % 2 == 0:
                c = dk
            if x - x1 < 2 and y < 56:
                c = lt
            p.P(x, y, c)
        p.P(max(0, x1), y, lt if y < 58 else base)
    # Zopfmuster: senkrechte Maschenreihen
    for y in range(54, W):
        for x in (14, 18, 22, 41, 45, 49, 53):
            if (y // 2 + x) % 2 == 0:
                p.P(x, y, SWH if x < 32 else lt)
                p.P(x + 1, y, dk)
    # Hals
    p.R(27, 40, 36, 49, SL)
    p.R(27, 40, 27, 49, SM)
    p.R(34, 40, 36, 49, SM)
    p.R(27, 44, 36, 47, SM)
    for x in range(28, 34):
        p.P(x, 44, SM)
    # dicker Rundhals: Rippenband
    for y in range(47, 54):
        x1, x2 = 24 - max(0, y - 49), 39 + max(0, y - 49)
        p.R(x1, y, x2, y, RIB)
        if y % 2 == 0:
            for x in range(x1, x2 + 1, 2):
                p.P(x, y, RIB2)
    p.R(25, 47, 38, 47, SW[1])
    p.R(28, 47, 35, 48, SM)                                         # Hals ragt aus dem Kragen
    p.R(29, 48, 34, 48, SL)
    # Umhaengegurt ueber die linke Schulter im Bild
    for y in range(50, W):
        x = 9 + (y - 50) * 2
        if 0 <= x < W:
            p.P(x, y, STRAP[0])
            p.P(x + 1, y, STRAP[0])
            p.P(x + 2, y, STRAP[1])


# ---------------------------------------------------------------- Kopf und Haare
def hw_face(y):
    """Halbe Gesichtsbreite je Zeile: runder Schaedel, kantiges Kinn."""
    if y < 12 or y > 45:
        return 0.0
    if y <= 31:
        t = (31 - y) / 19.0
        return 13.8 * math.sqrt(max(0.0, 1.0 - t * t * 0.95))
    return 13.8 - (y - 31) * 0.52 - ((y - 31) / 14.0) ** 2 * 1.6


def in_face(x, y):
    h = hw_face(y)
    return h > 0 and abs(x + 0.5 - 32) <= h


def hairline(x):
    """Unregelmaessiger Haaransatz: Fransen in Straehnen, links tiefer."""
    d = (x + 0.5 - 32) / 14.0
    base = 17.0 + 5.0 * d * d
    base += (hnoise(x, 3, 5) - 2) * 0.9
    if 20 <= x <= 26:
        base += 2.5
    return base


def head(p):
    # Haarmasse, dazu abstehende Straehnen
    p.E(32, 22, 16.8, 16.3, HB)
    tufts = ((20, 11, 4, -1), (23, 8, 5, -1), (26, 6, 5, 0), (29, 5, 4, 1), (33, 5, 6, 0), (37, 6, 5, 1), (40, 8, 4, 1), (43, 11, 4, 1),
             (18, 15, 3, -1), (45, 15, 3, 1))
    for (x, y, h, lean) in tufts:
        for i in range(h):
            p.P(x + (lean * i) // 2, y - i, HB)
            if i < 2:
                p.P(x + 1 + (lean * i) // 2, y - i, HB)
    # Gesicht
    for y in range(W):
        for x in range(W):
            if in_face(x, y):
                c = SL
                if x >= 41:
                    c = SM
                elif x >= 39 and (x + y) % 2 == 0:
                    c = SM
                p.P(x, y, c)
    # Haar vorn: Stirnfransen und Koteletten
    for y in range(W):
        for x in range(W):
            if not in_face(x, y):
                continue
            side = abs(x + 0.5 - 32) >= 12.4 and y <= 28
            if y < hairline(x) or side:
                p.P(x, y, HB)
    # Struktur: Straehnen, Licht und Schatten unregelmaessig
    for y in range(0, 40):
        for x in range(10, 54):
            if p.b[y][x] != HB:
                continue
            n = hnoise(x, y, 11)
            if n in (0, 1):
                p.P(x, y, HL)
            elif n in (5, 6) and y > 9:
                p.P(x, y, HS)
    for y in range(8, 20):                                          # Wirbel rechts oben
        p.P(38 + (y % 3), y, HL if y % 2 else HS)
    # Ohren (teils unter Haar), Brillenbuegel
    p.R(17, 28, 18, 33, SM)
    p.R(45, 28, 46, 33, SD)
    p.P(17, 34, SM)
    p.P(46, 34, SD)


# ---------------------------------------------------------------- Gesichtszuege
def eye(p, left, mode, gaze):
    """mode: open, wide, narrow, closed. Linkes Auge x 23..28 (innen = 28), rechtes gespiegelt. gaze: +1 = Blick nach rechts im Bild."""
    y0 = 27
    sh = gaze if left else -gaze

    def X(x):
        return x if left else sym(x)

    xs = list(range(23, 29))
    if mode == 'closed':
        for x in xs:
            p.P(X(x), y0 + 1, K2)
        for x in xs[1:-1]:
            p.P(X(x), y0 + 2, SM)
        return
    h = {'open': 3, 'wide': 4, 'narrow': 2}[mode]
    rows = list(range(y0 if mode != 'wide' else y0 - 1, (y0 if mode != 'wide' else y0 - 1) + h))
    for y in rows:
        for x in xs:
            p.P(X(x), y, SCL)
    # Iris 2 breit, Pupille, Glanzpunkt
    ix = (25 + sh, 26 + sh)
    for y in rows:
        for x in ix:
            p.P(X(x), y, IRIS)
    if mode == 'wide':
        for y in rows:
            p.P(X(ix[0]), y, IRIS)
        p.P(X(ix[1]), rows[1], K)
        p.P(X(ix[0]), rows[1], K)
        p.P(X(ix[0]), rows[0], WARM)
    else:
        p.P(X(ix[1]), rows[min(1, h - 1)], K)
        p.P(X(ix[0]), rows[0], WARM)
    if mode == 'narrow':
        for x in xs:
            p.P(X(x), rows[0] - 1, SM)                                 # Oberlid druckt
    p.R(X(23), rows[-1] + 1, X(28), rows[-1] + 1, SM) if left else p.R(X(28), rows[-1] + 1, X(23), rows[-1] + 1, SM)


def glasses(p):
    """Grosse Hornbrille: breite Glaeser mit abgerundeten Ecken, dicker Brauensteg, Nasensteg, Buegel zu den Ohren."""
    for left in (True, False):
        def X(x):
            return x if left else sym(x)
        for x in range(21, 30):                                     # Oberkante, doppelt
            p.P(X(x), 23, FR)
            p.P(X(x), 24, FR)
        for x in range(21, 30):                                     # Unterkante
            p.P(X(x), 32, FR)
        for y in range(25, 32):                                     # Seiten
            p.P(X(20), y, FR)
            p.P(X(30), y, FR)
        p.P(X(20), 24, FR)
        p.P(X(30), 24, FR)
        p.P(X(21), 32, FR)
        p.P(X(29), 32, FR)
        p.P(X(22), 23, FRL)                                         # Lichtkante auf dem Horn
        p.P(X(23), 23, FRL)
        p.P(X(20), 27, FRL)
        # Glanz im Glas
        p.P(X(22), 26, SCL)
        p.P(X(22), 25, SCL)
        p.P(X(23), 25, SCL)
        # Buegel
        p.P(X(19), 26, FR)
        p.P(X(18), 26, FR)
        p.P(X(17), 27, FR)
    p.R(31, 26, 32, 27, FR)                                         # Steg
    p.P(31, 28, FRL)
    p.P(32, 28, FRL)


def brows(p, ys):
    """ys: y je Spalte x 20..30 (aussen -> innen); dicke, ungepflegte Brauen (2 hoch) ueber dem Brillenrand."""
    for left in (True, False):
        for i, x in enumerate(range(20, 31)):
            X = x if left else sym(x)
            y = ys[i]
            p.P(X, y, HS)
            p.P(X, y + 1, HB)
            if hnoise(x, y, 4) == 0:
                p.P(X, y - 1, HS)


def nose(p):
    for y in range(29, 35):
        p.P(34, y, SM)
    p.P(30, 31, WARM)
    p.R(30, 35, 33, 35, SD)
    p.P(29, 35, SM)
    p.P(34, 35, SM)
    p.P(30, 36, SD)
    p.P(33, 36, SD)


def tired(p, extra=False):
    """Augenringe unter dem Brillenrand, Bartstoppeln, Falten."""
    for x in range(21, 30):
        if (x + 33) % 2 == 0:
            p.P(x, 33, SM)
            p.P(sym(x), 33, SM)
    for y in range(36, 46):
        for x in range(21, 43):
            if not in_face(x, y):
                continue
            if y in (39, 40, 41) and 28 <= x <= 36:
                continue
            if y >= 38 and hnoise(x, y, 6) == 0:
                p.P(x, y, SM if x < 40 else SD)
    p.R(27, 19, 28, 19, SM) if False else None
    if extra:
        p.R(24, 22, 26, 22, SM)


def mouth(p, kind):
    y = 40
    if kind == 'calm':
        p.R(29, y, 34, y, SD)
        p.P(28, y + 1, SM)
        p.P(35, y, SM)
        p.R(30, y + 1, 33, y + 1, SM)
    elif kind == 'warm':
        p.R(29, y, 34, y, SD)
        p.P(28, y - 1, SD)
        p.P(35, y - 1, SD)
        p.R(30, y + 1, 33, y + 1, '#c4636b')
        p.P(27, y - 2, SM)
        p.P(36, y - 2, SM)
    elif kind == 'scared':
        p.R(30, y - 1, 33, y - 1, SD)
        p.R(29, y, 34, y + 2, K2)
        p.R(30, y + 3, 33, y + 3, K2)
        p.R(30, y + 2, 33, y + 2, SD)
        p.R(31, y + 4, 32, y + 4, SM)
        p.P(28, y + 1, SM)
        p.P(35, y + 1, SM)
    elif kind == 'firm':
        p.R(28, y, 35, y, SD)
        p.R(29, y + 1, 34, y + 1, SM)
        p.P(23, 39, SM)                                             # Kiefermuskel
        p.P(24, 40, SM)
        p.P(40, 39, SD)
        p.P(39, 40, SD)
    else:
        VP.mouth(p, kind)                                           # A, E, O wie bei den anderen Figuren


EXPR = {
    # brows: y je Spalte x 20..30 (aussen -> innen); gaze: Blick an allem vorbei (zerstreut)
    'calm':          dict(eye='open',   brows=(21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21), mouth='calm',   gaze=1),
    'compassionate': dict(eye='open',   brows=(21, 21, 21, 20, 20, 19, 19, 18, 18, 18, 18), mouth='warm',   gaze=1),
    'scared':        dict(eye='wide',   brows=(19, 19, 19, 18, 18, 17, 17, 16, 16, 16, 16), mouth='scared', gaze=0),
    'determined':    dict(eye='narrow', brows=(20, 20, 20, 21, 21, 21, 21, 21, 22, 22, 22), mouth='firm',   gaze=0),
    'blink':         dict(eye='closed', brows=(21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21), mouth='calm',   gaze=1),
    'talk_A':        dict(eye='open',   brows=(21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21), mouth='A',      gaze=1),
    'talk_E':        dict(eye='open',   brows=(21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21), mouth='E',      gaze=1),
    'talk_O':        dict(eye='open',   brows=(21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21), mouth='O',      gaze=1),
}
ORDER = ['calm', 'compassionate', 'scared', 'determined', 'blink', 'talk_A', 'talk_E', 'talk_O']


def render(name):
    e = EXPR[name]
    p = Pn()
    bust(p)
    head(p)
    eye(p, True, e['eye'], e['gaze'])
    eye(p, False, e['eye'], e['gaze'])
    glasses(p)
    brows(p, e['brows'])
    nose(p)
    tired(p, name == 'determined')
    mouth(p, e['mouth'])
    return outline(p)


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    sheet = Image.new('RGBA', (len(ORDER) * W, W))
    for i, n in enumerate(ORDER):
        im = to_img(render(n))
        im.save(os.path.join(outdir, 'can_%s.png' % n))
        sheet.paste(im, (i * W, 0))
    sheet.save(os.path.join(outdir, '..', 'portrait_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'portraits')
    build(out)
    print('ok', os.path.abspath(out))
