"""Baker Mara: Portraits 64x64, nur Hex-Werte der Nightward-Palette.

Ausdruecke laut Doku: Ruhe (Standard), Warm (wird auf Mitfuehlend abgebildet -> Datei 'compassionate'), Misstrauisch, Veraengstigt.
Dazu Blinzeln (Ruhe mit geschlossenen Augen) und die Sprechmuender A, E, O (Basis: Ruhe), wie bei den anderen Figuren.

Aufruf:  python gen_baker_mara_portraits.py [Ausgabeordner]
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'DOCTOR VERONICA', '_Quelle_Generator'))

import gen_doctor_veronica_portraits as VP  # noqa: E402
from gen_doctor_veronica_portraits import Pn, outline, to_img, sym, W, K, K2, SL, SM, SD, WARM, HL as GRAYL  # noqa: E402,F401

HW, HY, HB, HS, HD = '#fff1c9', '#ffd27a', '#b89a72', '#9c7a5a', '#7a5a43'   # Blond: Glanz, warmgelbes Licht, Grund, Schatten, tief
SR, SRD = '#c4636b', '#7a2e3a'                                                # Tuch und Lippen: Grund, Schatten
TOP = ('#6b7fb8', '#3a4a7a', '#2c3e56', '#1f2a3d')                            # Oberteil
IRIS = '#3f5570'
GOLD, GOLD2 = '#ffd27a', '#ffa550'


# ---------------------------------------------------------------- Haare
def hair_mass(p):
    """Volumen hinter dem Kopf, Straehnen laufen vom Scheitel nach aussen."""
    p.E(32, 25, 19.5, 20.0, HB)
    for y in range(W):
        for x in range(W):
            if p.b[y][x] != HB:
                continue
            k = int(math.atan2(y + 0.5 - 6, x + 0.5 - 32) * 9)
            right = x >= 38
            if right:
                p.P(x, y, HS if x >= 41 else HB)
                if k % 3 == 0:
                    p.P(x, y, HB if x >= 41 else HY)
            else:
                if k % 3 == 0:
                    p.P(x, y, HY)
                elif k % 3 == 1 and y > 24:
                    p.P(x, y, HS)


def locks(p):
    """Lange Locken, vorn ueber die Schultern fallend; Hals und Ausschnitt bleiben frei."""
    for y in range(27, 58):
        wob = int(round(1.4 * math.sin(y / 5.0)))
        x1 = 14 + wob + (y - 27) // 12
        x2 = 21
        for x in range(x1, x2 + 1):
            band = ((x - x1) // 2 + y // 8) % 3
            c = (HY, HB, HS)[band] if band != 2 else HB
            if band == 2 and (x - x1) % 2 == 1:
                c = HS
            p.P(x, y, c)
            p.P(sym(x), y, c if band != 0 else HB)
        p.P(x2, y, HD)
        p.P(sym(x2), y, HD)
        p.P(x1, y, HS)
        p.P(sym(x1), y, HD)
    # Spitzen laufen zu einer Locke zusammen
    for i, y in enumerate(range(58, 62)):
        for x in range(16 + i, 22 - i // 2):
            p.P(x, y, HB if (x + y) % 3 else HS)
            p.P(sym(x), y, HS if (x + y) % 3 else HD)
    for y in range(30, 58, 7):
        p.P(17 + int(round(1.4 * math.sin(y / 5.0))) + (y - 27) // 12, y, HW)


# ---------------------------------------------------------------- Koerper
def bust(p):
    t = TOP
    for y in range(49, W):
        hw = 16 + (y - 49) * 1.8
        for x in range(max(0, int(32 - hw)), min(W, int(32 + hw) + 1)):
            c = t[1]
            if x >= 44:
                c = t[2]
            elif x >= 41 and (x + y) % 2 == 0:
                c = t[2]
            p.P(x, y, c)
    # tiefer V-Ausschnitt mit Haut; Brueste als zwei Waelbungen mit Licht an der Innenkante
    for y in range(48, W):
        hw = max(1.5, 9.0 - (y - 48) * 0.5)
        for x in range(int(round(32 - hw)), int(round(32 + hw))):
            p.P(x, y, SL if x < 33 else SM)
        if y >= 54:
            lx = int(round(32 - hw))
            rx = int(round(32 + hw)) - 1
            p.P(lx - 1, y, t[0])
            p.P(lx - 2, y, t[0] if y % 2 == 0 else t[1])
            p.P(rx + 1, y, t[1])
            p.P(rx + 2, y, t[2])
    for y in range(57, W):
        p.P(31, y, SD)
        p.P(32, y, SD)
    for x in range(14, 26):                                      # Oberkante der Waelbungen
        yy = 59 + int(round(2.0 * ((x - 20) / 6.0) ** 2))
        p.P(x, yy, t[0])
    for x in range(39, 50):
        yy = 59 + int(round(2.0 * ((x - 43.5) / 6.0) ** 2))
        p.P(x, yy, t[2])
    # Hals mit Kinnschatten
    p.R(27, 40, 36, 50, SL)
    p.R(27, 40, 27, 50, SM)
    p.R(34, 40, 36, 50, SM)
    p.R(27, 44, 36, 46, SM)
    for x in range(28, 34):
        p.P(x, 44, SM)
    for x in (23, 24, 25, 26):                                   # Schluesselbeine
        p.P(x, 51, SM)
    for x in (37, 38, 39, 40):
        p.P(x, 51, SD)
    # Goldkette mit Anhaenger
    for x in range(26, 38):
        yy = 49 + int(round(5.0 * (1 - ((x - 31.5) / 6.0) ** 2)))
        p.P(x, yy, GOLD)
    p.P(31, 55, GOLD)
    p.P(32, 55, GOLD)
    p.P(31, 56, GOLD2)
    p.P(32, 56, GOLD2)


# ---------------------------------------------------------------- Kopf
def head(p):
    p.E(32, 30, 12.6, 15.2, SL)
    for y in range(W):
        for x in range(W):
            if p.inE(x, y, 32, 30, 12.6, 15.2):
                if x >= 41:
                    p.P(x, y, SM)
                elif x >= 39 and (x + y) % 2 == 0:
                    p.P(x, y, SM)
    for x in range(26, 38):                                      # Kinnschatten
        if p.inE(x, 44, 32, 30, 12.6, 15.2):
            p.P(x, 44, SM)
    # Wangenroete
    for (x, y) in ((22, 35), (24, 35), (23, 36), (40, 35), (38, 35), (39, 36)):
        if (x + y) % 2 == 1 or y == 36:
            p.P(x, y, SR if x < 33 else SM)


def bangs(p):
    """Seitlich gescheiteltes Pony, vom Tuch ueber die Stirn nach rechts fallend."""
    for x in range(19, 38):
        ymax = 22 - int((x - 19) * 0.30)
        for y in range(15, ymax + 1):
            if p.inE(x, y, 32, 30, 13.2, 15.6) or y <= 18:
                p.P(x, y, HB)
                if (x + y) % 5 == 0:
                    p.P(x, y, HY)
                elif (x - y) % 7 == 3:
                    p.P(x, y, HS)
    # Haarstraehne seitlich am Gesicht
    for y in range(20, 38):
        for x in (19, 20):
            if p.inE(x, y, 32, 30, 13.4, 15.6):
                p.P(x, y, HB if (y // 3) % 2 else HY)
        for x in (44, 45):
            if p.inE(x, y, 32, 30, 13.4, 15.6):
                p.P(x, y, HS if (y // 3) % 2 else HB)


def scarf(p):
    """Rotes Tuch als Band quer ueber den Kopf, Knoten links mit herabhaengenden Enden."""
    for x in range(14, 50):
        yc = 12.5 + 5.5 * ((x + 0.5 - 32) / 17.5) ** 2
        for k in range(-2, 3):
            y = int(round(yc)) + k
            c = SR
            if k >= 1:
                c = SRD
            if k == -2 and x < 30:
                c = HW if (x % 3 == 0) else SR
            p.P(x, y, c)
    # Knoten: zwei Schlaufen und Mitte
    p.E(13.5, 13.5, 4.2, 3.6, SR)
    p.E(18.0, 15.5, 3.6, 3.2, SR)
    p.E(15.5, 14.5, 2.2, 2.0, SRD)
    p.P(12, 12, HW)
    p.P(13, 11, HW)
    p.P(17, 14, HW)
    p.R(11, 16, 12, 16, SRD)
    # Enden
    for i, y in enumerate(range(18, 31)):
        p.P(15, y, SR if i % 2 == 0 else SRD)
        p.P(16, y, SRD if i % 2 == 0 else SR)
    for i, y in enumerate(range(18, 25)):
        p.P(12, y, SRD if i % 2 == 0 else SR)
        p.P(13, y, SR if i % 2 == 0 else SRD)
    p.P(15, 31, SRD)
    p.P(12, 25, SRD)


# ---------------------------------------------------------------- Zuege
def brows(p, ys_left, ys_right):
    for i, x in enumerate(range(20, 29)):
        p.P(x, ys_left[i], HS)
        p.P(sym(x), ys_right[i], HS)
    p.P(20, ys_left[0] + 1, HB)
    p.P(sym(20), ys_right[0] + 1, HB)
    for i in (3, 4, 5):
        p.P(20 + i, ys_left[i] + 1, HD)
        p.P(sym(20 + i), ys_right[i] + 1, HD)


def eye(p, left, mode):
    """Auge mit Wimpernkranz. Linkes Auge x 21..27, rechtes gespiegelt."""
    X = (lambda x: x) if left else sym
    xs = range(21, 28)
    y0 = 28
    if mode == 'closed':
        for x in xs:
            p.P(X(x), y0 + 1, K2)
        p.P(X(20), y0 + 2, K2)
        p.P(X(21), y0 + 2, K2)
        for x in range(22, 27):
            p.P(X(x), y0 + 2, SM)
        return
    top = y0 - 1 if mode != 'wide' else y0 - 2
    p.R(X(21), top, X(27), top, K2) if left else p.R(X(27), top, X(21), top, K2)
    p.P(X(20), top + 1, K2)
    p.P(X(20), top, K2)
    p.P(X(27), top - 1, K2) if mode == 'wide' else None
    rows = {'open': range(y0, y0 + 3), 'soft': range(y0, y0 + 3), 'side': range(y0, y0 + 3), 'narrow': range(y0, y0 + 3),
            'wide': range(y0 - 1, y0 + 4)}[mode]
    for y in rows:
        for x in xs:
            p.P(X(x), y, GRAYL)
    if mode in ('side', 'narrow'):
        for x in xs:
            p.P(X(x), y0, SL)                                    # schweres Lid
    if mode == 'soft':
        for x in xs:
            p.P(X(x), y0 + 2, SL)                                # Lachaugen: Unterlid hoch
    # Iris 3x3 (Blick geradeaus), bei 'side' zur Seite
    ix = {'side': 25, 'open': 23, 'soft': 23, 'narrow': 23, 'wide': 24}[mode]
    isz = 3 if mode != 'wide' else 2
    for dx in range(isz):
        for dy in range(isz):
            yy = y0 + dy + (0 if mode != 'wide' else 0)
            if mode in ('side', 'narrow') and yy == y0:
                continue
            p.P(X(ix + dx), yy, IRIS)
    p.P(X(ix + 1), y0 + 1 if isz == 3 else y0, K)               # Pupille
    p.P(X(ix), y0 + (1 if mode in ('side', 'narrow') else 0), WARM)   # Glanzpunkt
    for x in range(22, 27):
        p.P(X(x), (y0 + 3 if mode != 'wide' else y0 + 4), SM)    # Unterlid


def nose(p):
    for y in range(31, 35):
        p.P(33, y, SM)
    p.P(31, 33, WARM)
    p.R(31, 35, 33, 35, SM)
    p.P(30, 35, SD)
    p.P(34, 35, SD)


def mouth(p, kind):
    if kind == 'calm':
        p.P(30, 37, SR)
        p.P(34, 37, SR)
        p.R(28, 38, 36, 38, SR)
        p.R(28, 39, 36, 39, SRD)
        p.R(29, 40, 35, 40, SR)
        p.R(30, 41, 34, 41, SR)
        p.R(31, 40, 32, 40, WARM)
        p.R(31, 42, 33, 42, SM)
    elif kind == 'warm':
        p.P(30, 37, SR)
        p.P(34, 37, SR)
        p.R(28, 38, 36, 38, SR)
        p.R(29, 39, 35, 39, SRD)
        p.P(27, 38, SRD)
        p.P(37, 38, SRD)
        p.R(29, 40, 35, 40, SR)
        p.R(30, 41, 34, 41, SR)
        p.R(31, 40, 33, 40, WARM)
        p.R(31, 42, 33, 42, SM)
        p.P(26, 37, SM)
        p.P(38, 37, SM)
    elif kind == 'smirk':                                       # misstrauisch: Mundwinkel schief
        p.P(30, 38, SR)
        p.R(29, 39, 35, 39, SR)
        p.R(28, 40, 33, 40, SRD)
        p.P(34, 39, SRD)
        p.R(35, 38, 36, 38, SRD)
        p.P(37, 37, SRD)
        p.R(30, 41, 33, 41, SR)
        p.P(31, 41, WARM)
        p.R(31, 42, 33, 42, SM)
        p.P(38, 36, SM)
    elif kind == 'scared':
        p.R(29, 37, 35, 37, SR)
        p.R(30, 38, 34, 40, K2)
        p.R(31, 40, 33, 40, SD)
        p.R(29, 38, 29, 40, SR)
        p.R(35, 38, 35, 40, SRD)
        p.R(30, 41, 34, 41, SR)
        p.R(31, 42, 33, 42, SM)
    elif kind == 'A':
        p.R(28, 37, 36, 37, SR)
        p.R(29, 38, 35, 41, K2)
        p.R(30, 40, 34, 41, SD)
        p.R(28, 38, 28, 40, SR)
        p.R(36, 38, 36, 40, SRD)
        p.R(30, 42, 34, 42, SR)
        p.R(31, 43, 33, 43, SM)
    elif kind == 'E':
        p.R(28, 37, 36, 37, SR)
        p.R(28, 38, 36, 39, K2)
        p.R(27, 38, 27, 39, SR)
        p.R(37, 38, 37, 39, SRD)
        p.R(29, 40, 35, 40, SR)
        p.R(30, 41, 34, 41, SM)
    elif kind == 'O':
        p.R(30, 37, 34, 37, SR)
        p.R(31, 38, 33, 41, K2)
        p.R(30, 39, 30, 40, SR)
        p.R(34, 39, 34, 40, SRD)
        p.R(31, 42, 33, 42, SR)
        p.R(31, 43, 33, 43, SM)


def earrings(p):
    for X in (lambda x: x, sym):
        p.P(X(19), 36, GOLD)
        p.P(X(19), 37, GOLD2)
        p.P(X(19), 38, GOLD)


EXPR = {
    'calm':          dict(eye='open',   mouth='calm',  bl=[24, 23, 23, 22, 22, 22, 23, 23, 24], br=[24, 23, 23, 22, 22, 22, 23, 23, 24]),
    'compassionate': dict(eye='soft',   mouth='warm',  bl=[25, 24, 24, 23, 23, 22, 22, 21, 21], br=[25, 24, 24, 23, 23, 22, 22, 21, 21]),
    'suspicious':    dict(eye='side',   mouth='smirk', bl=[23, 22, 21, 20, 20, 21, 22, 22, 23], br=[25, 25, 26, 26, 26, 27, 27, 27, 28]),
    'scared':        dict(eye='wide',   mouth='scared', bl=[22, 21, 21, 20, 19, 19, 18, 18, 17], br=[22, 21, 21, 20, 19, 19, 18, 18, 17]),
    'blink':         dict(eye='closed', mouth='calm',  bl=[24, 23, 23, 22, 22, 22, 23, 23, 24], br=[24, 23, 23, 22, 22, 22, 23, 23, 24]),
    'talk_A':        dict(eye='open',   mouth='A',     bl=[24, 23, 23, 22, 22, 22, 23, 23, 24], br=[24, 23, 23, 22, 22, 22, 23, 23, 24]),
    'talk_E':        dict(eye='open',   mouth='E',     bl=[24, 23, 23, 22, 22, 22, 23, 23, 24], br=[24, 23, 23, 22, 22, 22, 23, 23, 24]),
    'talk_O':        dict(eye='open',   mouth='O',     bl=[24, 23, 23, 22, 22, 22, 23, 23, 24], br=[24, 23, 23, 22, 22, 22, 23, 23, 24]),
}
ORDER = ['calm', 'compassionate', 'suspicious', 'scared', 'blink', 'talk_A', 'talk_E', 'talk_O']


def render(name):
    e = EXPR[name]
    p = Pn()
    hair_mass(p)
    bust(p)
    head(p)
    bangs(p)
    scarf(p)
    brows(p, e['bl'], e['br'])
    eye(p, True, e['eye'])
    eye(p, False, e['eye'])
    nose(p)
    mouth(p, e['mouth'])
    locks(p)
    earrings(p)
    return outline(p)


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    sheet = Image.new('RGBA', (len(ORDER) * W, W))
    for i, n in enumerate(ORDER):
        im = to_img(render(n))
        im.save(os.path.join(outdir, 'mara_%s.png' % n))
        sheet.paste(im, (i * W, 0))
    sheet.save(os.path.join(outdir, '..', 'portrait_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'portraits')
    build(out)
    print('ok', os.path.abspath(out))
