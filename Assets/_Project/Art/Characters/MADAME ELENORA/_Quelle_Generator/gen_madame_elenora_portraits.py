"""Madame Elenora: Portraits 64x64, nur Hex-Werte der Nightward-Palette.

Ausdruecke laut Doku: Ruhig (Standard), Kalt, Falsch laechelnd (nie Zaehne, die gehoeren dem Monster-Grinsen).
Dazu Blinzeln (Ruhig mit geschlossenen Augen) und die Sprechmuender A, E, O (Basis: Ruhig, ohne Zaehne), wie bei den anderen Figuren.
Der Villa-Hintergrund (#3d2e4a) kommt aus der UI, die PNGs sind wie bei den anderen Figuren transparent.

Aussehen: schmales Gesicht mit hohen Wangenknochen und spitzem Kinn, schwarzes Haar glatt nach hinten zum hohen Dutt, dunkelrote Lippen,
eisblaue Augen, Samtband am Hals, goldene Ohrringe, rotes Kleid mit eckigem Ausschnitt und Rose-Kante, goldene Brosche.
Schwarz = dunkle Violett-Toene der Palette (nie #1a1526, das ist die Outline).

Aufruf:  python gen_madame_elenora_portraits.py [Ausgabeordner]
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'DOCTOR VERONICA', '_Quelle_Generator'))

from gen_doctor_veronica_portraits import Pn, outline, to_img, sym, W, K, K2, SL, SM, SD, WARM  # noqa: E402

HK = ('#6b5a7a', '#4f3d5c', '#2b2140', '#1a1526')    # Haar: Glanz, Licht, Grund, Schatten (Grund dunkler als der Villa-Hintergrund #3d2e4a)
DR = ('#c4636b', '#7a2e3a', '#2b2140')               # Kleid: Rose-Licht, Grund, Schatten
LIPD, LIPL = '#7a2e3a', '#c4636b'
IRIS, IRIS2 = '#3f5570', '#6b7fb8'                   # eisblau, Glanz
SCL = '#e8e0f0'
GOLD, GOLD2 = '#ffd27a', '#ffa550'
VELV = ('#4f3d5c', '#2b2140')                        # Samtband: Licht, Grund


def hw_face(y):
    """Halbe Gesichtsbreite je Zeile: hohe Schlaefen, schlanke Wangen, spitzes Kinn."""
    if y < 12 or y > 45:
        return 0.0
    if y <= 30:
        t = (30 - y) / 18.0
        return 12.6 * math.sqrt(max(0.0, 1.0 - t * t * 0.9))
    return 12.6 - (y - 30) * 0.60 - ((y - 30) / 15.0) ** 2 * 1.2


def in_face(x, y):
    h = hw_face(y)
    return h > 0 and abs(x + 0.5 - 32) <= h


# ---------------------------------------------------------------- Koerper
def bust(p):
    base, lt, dk = DR[1], DR[0], DR[2]
    # Schultern: breit und gerade, Kleid mit weitem eckigen Ausschnitt
    for y in range(50, W):
        hw = 19 + (y - 50) * 1.9
        x1, x2 = int(round(32 - hw)), int(round(31 + hw))
        for x in range(max(0, x1), min(W - 1, x2) + 1):
            c = base
            if x >= 50:
                c = dk
            elif x >= 46 and (x + y) % 2 == 0:
                c = dk
            if x - x1 < 2 and y < 56:
                c = lt
            p.P(x, y, c)
        p.P(max(0, x1), y, lt if y < 58 else base)
    # Hals: schlank und lang, Schatten unter dem Kinn
    p.R(28, 40, 36, 52, SL)
    p.R(28, 40, 28, 52, SM)
    p.R(34, 40, 36, 52, SM)
    p.R(28, 44, 36, 47, SM)
    for x in range(29, 34):
        p.P(x, 44, SM)
    # Ausschnitt: weites U bis y 58, Haut mit Schluesselbein, Rose-Kante folgt dem Rand
    depth = 8.0
    for y in range(50, 59):
        hw = 10.5 * math.sqrt(max(0.0, 1.0 - ((y - 50) / depth) ** 2))
        x1, x2 = int(round(32 - hw)), int(round(31 + hw))
        for x in range(x1, x2 + 1):
            p.P(x, y, SL if x < 36 else SM)
        p.P(x1 - 1, y, lt)
        p.P(x2 + 1, y, lt)
        if y >= 55:
            p.R(x1, y, x2, y, lt)
    p.R(22, 49, 41, 49, lt) if False else None
    for x in (25, 26, 27, 37, 38, 39):                              # Schluesselbeine
        p.P(x, 52, SM)
    p.R(28, 52, 30, 52, SD)
    p.R(34, 52, 36, 52, SD)
    # Brosche am tiefsten Punkt des Ausschnitts
    p.R(31, 58, 33, 59, GOLD)
    p.P(33, 59, GOLD2)
    p.P(32, 60, GOLD2)
    p.P(31, 58, WARM)
    # Samtband am Hals mit goldener Schliesse
    p.R(28, 48, 36, 49, VELV[1])
    p.R(28, 48, 36, 48, VELV[0])
    p.R(31, 48, 33, 49, GOLD)
    p.P(33, 49, GOLD2)
    p.P(32, 48, WARM)


# ---------------------------------------------------------------- Kopf und Haare
def hairline(x):
    """Haaransatz: glatt zurueckgekaemmt, seitlicher Scheitel links (x 26), Schlaefen hoeher als bei Veronica."""
    d = (x + 0.5 - 32) / 13.0
    base = 15.5 + 5.5 * d * d
    if x <= 26:
        base += 0.4 * (26 - x)                                      # Scheitel: links tiefer gekaemmt
    return base


def head(p):
    # Haar hinten, eng am Kopf; hoher Dutt oben rechts der Mitte
    p.E(32, 22, 15.2, 16.5, HK[2])
    p.E(35, 6.5, 7.2, 5.8, HK[2])
    p.R(29, 9, 38, 13, HK[2])
    # Gesicht
    for y in range(W):
        for x in range(W):
            if in_face(x, y):
                c = SL
                if x >= 40:
                    c = SM
                elif x >= 38 and (x + y) % 2 == 0:
                    c = SM
                p.P(x, y, c)
    # Kinnkante etwas dunkler
    for x in range(26, 38):
        if in_face(x, 44):
            p.P(x, 44, SM)
    # Haar vorn: Stirnkappe und schmale Schlaefen, Ohren frei
    for y in range(W):
        for x in range(W):
            if not in_face(x, y):
                continue
            side = abs(x + 0.5 - 32) >= 11.2 and y <= 26
            if y < hairline(x) or side:
                p.P(x, y, HK[2])
    # Struktur: Straehnen laufen glatt zum Dutt, Glanzband quer ueber dem Oberkopf
    for y in range(W):
        for x in range(W):
            if p.b[y][x] != HK[2]:
                continue
            inside = p.inE(x, y, 32, 22, 15.2, 16.5) or p.inE(x, y, 35, 6.5, 7.2, 5.8) or (29 <= x <= 38 and 9 <= y <= 13)
            if not inside:
                continue
            k = int(math.atan2(y + 0.5 - 8, x + 0.5 - 35) * 11)
            if x >= 41:
                p.P(x, y, HK[3])
            elif k % 3 == 0:
                p.P(x, y, '#3d2e4a')
                if k % 6 == 0:
                    p.P(x, y, HK[1])
            elif k % 7 == 1 and y > 16:
                p.P(x, y, HK[3])
    for y in range(12, 17):                                         # Glanzband
        for x in range(23, 41):
            if p.b[y][x] in (HK[2], HK[1]) and abs((y - 13.5) - 0.12 * (x - 32) ** 2 / 12.0 * -1) < 1.1 and (x + y) % 2 == 0:
                p.P(x, y, HK[0])
    for p_ in ((26, 13), (27, 12), (28, 12), (36, 12), (37, 13), (24, 15), (39, 15)):
        p.P(p_[0], p_[1], HK[0])
    # Scheitel
    for y in range(11, 18):
        p.P(26 - (y - 11) // 3, y, HK[3])
    # Dutt: Wicklung als Boegen, Licht oben links, Schatten rechts unten, goldene Haarnadel
    for y in range(0, 14):
        for x in range(26, 44):
            if p.inE(x, y, 35, 6.5, 7.2, 5.8):
                d = ((x + 0.5 - 35) / 7.2) ** 2 + ((y + 0.5 - 6.5) / 5.8) ** 2
                c = HK[2]
                if x < 33 and y < 6:
                    c = HK[1]
                if x >= 38 or y >= 9:
                    c = HK[3]
                if int(d * 6) % 2 == 1 and d > 0.15:
                    c = HK[3] if c != HK[1] else HK[2]
                p.P(x, y, c)
    p.P(31, 2, HK[0])
    p.P(32, 1, HK[0])
    p.P(33, 2, HK[0])
    for i in range(5):                                              # Haarnadel quer durch den Dutt
        p.P(33 + i, 7 - i // 2, GOLD if i % 2 == 0 else GOLD2)
    # Ohren und goldene Ohrringe (Tropfen)
    p.R(18, 29, 19, 33, SM)
    p.R(44, 29, 45, 33, SD)
    p.P(18, 34, SM)
    p.P(45, 34, SD)
    for x in (18, 45):
        p.P(x, 35, GOLD)
        p.P(x, 36, GOLD2)
        p.P(x, 37, GOLD)


# ---------------------------------------------------------------- Gesichtszuege
def eye(p, left, mode):
    """mode: open, cold, flat, closed. Linkes Auge x 22..28, rechtes gespiegelt."""
    y0 = 27

    def X(x):
        return x if left else sym(x)

    xs = list(range(22, 28))
    if mode == 'closed':
        for x in xs:
            p.P(X(x), y0 + 1, K2)
        p.P(X(21), y0, K2)                                          # Wimpernschwung
        p.P(X(22), y0 + 2, K2)
        p.P(X(27), y0 + 2, K2)
        for x in xs[1:-1]:
            p.P(X(x), y0 + 2, SM)
        return
    # Oberlid: dicker Lidstrich mit Fluegel nach aussen oben
    p.R(X(22), y0 - 1, X(27), y0 - 1, K)
    p.P(X(21), y0 - 1, K)
    p.P(X(20), y0 - 2, K)
    p.P(X(23), y0 - 2, K2)
    h = 3 if mode == 'open' else 2
    rows = list(range(y0, y0 + h))
    for y in rows:
        for x in xs:
            p.P(X(x), y, SCL)
    # Iris: 3 breit, eisblau, Pupille und Glanzpunkt
    ix = (23, 24, 25)
    for y in rows:
        for x in ix:
            p.P(X(x), y, IRIS)
    p.P(X(24), y0 + 1, K)
    if mode == 'open':
        p.P(X(23), y0, IRIS2)
        p.P(X(25), y0, K2)
        p.P(X(25), y0 + 2, K2)
    elif mode == 'cold':
        p.R(X(22), y0, X(27), y0, SM)                               # Lid haengt halb ueber das Auge
        for x in ix:
            p.P(X(x), y0, K2)
        p.P(X(23), y0 + 1, IRIS2)
    else:                                                           # flat: Laecheln erreicht die Augen nicht
        p.R(X(22), y0, X(27), y0, SM)
        for x in ix:
            p.P(X(x), y0, K2)
        p.P(X(23), y0 + 1, IRIS2)
    for x in xs:
        p.P(X(x), y0 + h, SM)                                       # Unterlid
    p.P(X(21), y0 + 1, SM)


def brows(p, ys, thick=1, raise_left=0):
    """ys: y je Spalte der linken Braue (x 21..29, aussen -> innen), rechte gespiegelt. Duenn und scharf gewoelbt."""
    for left in (True, False):
        off = raise_left if left else 0
        for i, x in enumerate(range(21, 30)):
            y = ys[i] - off
            X = x if left else sym(x)
            for k in range(thick):
                p.P(X, y + k, HK[3] if k == 0 else HK[2])
            if i in (0, 1):
                p.P(X, y + thick, HK[2]) if False else None


def nose(p):
    for y in range(29, 34):
        p.P(34, y, SM)
    p.P(31, 30, WARM)
    p.R(30, 34, 33, 34, SD)
    p.P(29, 34, SM)
    p.P(34, 34, SM)
    p.P(30, 35, SD)
    p.P(33, 35, SD)


def cheeks(p):
    """Hohe Wangenknochen: eine schraege Konturlinie unter dem Wangenknochen, kein Punktmuster."""
    for (x, y) in ((22, 33), (23, 34), (24, 35), (25, 36)):
        p.P(x, y, SM)
    for (x, y) in ((sym(22), 33), (sym(23), 34), (sym(24), 35), (sym(25), 36)):
        p.P(x, y, SD)
    p.R(27, 17, 28, 17, SM)                                          # Stirnschatten unter dem Haaransatz
    p.R(35, 17, 36, 17, SM)


def mouth(p, kind):
    y = 39
    if kind == 'calm':
        p.R(29, y - 1, 35, y - 1, LIPD)
        p.P(31, y - 2, LIPD)
        p.P(33, y - 2, LIPD)
        p.R(30, y, 34, y, LIPL)
        p.P(28, y - 1, SM)
        p.P(36, y - 1, SM)
        p.R(31, y + 1, 33, y + 1, SM)
    elif kind == 'cold':
        p.R(28, y - 1, 36, y - 1, LIPD)
        p.R(29, y, 35, y, LIPD)
        p.P(27, y, SD)
        p.P(37, y, SD)
        p.R(31, y + 1, 33, y + 1, SM)
    elif kind == 'fake':
        p.R(29, y - 1, 35, y - 1, LIPD)
        p.R(30, y, 34, y, LIPL)
        p.P(28, y - 2, LIPD)
        p.P(27, y - 3, LIPD)
        p.P(36, y - 2, LIPD)
        p.P(37, y - 3, LIPD)
        p.P(28, y - 1, LIPD)
        p.P(36, y - 1, LIPD)
        p.R(31, y + 1, 33, y + 1, SM)
    elif kind == 'A':
        p.R(29, y - 2, 35, y - 2, LIPD)
        p.P(31, y - 3, LIPD)
        p.P(33, y - 3, LIPD)
        p.R(28, y - 1, 36, y + 2, K2)
        p.R(29, y + 3, 35, y + 3, K2)
        p.R(30, y + 2, 34, y + 2, LIPD)                             # Zunge
        p.R(29, y + 4, 35, y + 4, LIPL)
        p.R(31, y + 5, 33, y + 5, SM)
    elif kind == 'E':
        p.R(29, y - 2, 35, y - 2, LIPD)
        p.R(28, y - 1, 36, y, K2)
        p.R(29, y + 1, 35, y + 1, LIPL)
        p.R(31, y + 2, 33, y + 2, SM)
    elif kind == 'O':
        p.R(30, y - 2, 34, y - 2, LIPD)
        p.R(29, y - 1, 35, y + 2, K2)
        p.R(31, y + 3, 33, y + 3, K2)
        p.R(29, y - 1, 29, y + 1, LIPD)
        p.R(35, y - 1, 35, y + 1, LIPD)
        p.R(31, y + 4, 33, y + 4, LIPL)
        p.R(31, y + 5, 33, y + 5, SM)


# Brauen je Ausdruck (y je Spalte x 21..29, aussen -> innen)
BR_CALM = (24, 23, 22, 22, 22, 22, 23, 23, 24)
BR_COLD = (23, 23, 23, 23, 24, 24, 24, 25, 25)         # flach, innen tiefer: streng
BR_FAKE = (25, 24, 23, 22, 22, 22, 23, 24, 24)         # hohe Wölbung, freundlich nach aussen, Augen bleiben kalt

EXPR = {
    'calm':       dict(eye='open',   brows=BR_CALM, mouth='calm'),
    'cold':       dict(eye='cold',   brows=BR_COLD, mouth='cold'),
    'fake_smile': dict(eye='flat',   brows=BR_FAKE, mouth='fake', raise_left=1),
    'blink':      dict(eye='closed', brows=BR_CALM, mouth='calm'),
    'talk_A':     dict(eye='open',   brows=BR_CALM, mouth='A'),
    'talk_E':     dict(eye='open',   brows=BR_CALM, mouth='E'),
    'talk_O':     dict(eye='open',   brows=BR_CALM, mouth='O'),
}
ORDER = ['calm', 'cold', 'fake_smile', 'blink', 'talk_A', 'talk_E', 'talk_O']


def render(name):
    e = EXPR[name]
    p = Pn()
    bust(p)
    head(p)
    cheeks(p)
    brows(p, e['brows'], 1, e.get('raise_left', 0))
    eye(p, True, e['eye'])
    eye(p, False, e['eye'])
    nose(p)
    mouth(p, e['mouth'])
    return outline(p)


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    sheet = Image.new('RGBA', (len(ORDER) * W, W))
    for i, n in enumerate(ORDER):
        im = to_img(render(n))
        im.save(os.path.join(outdir, 'elenora_%s.png' % n))
        sheet.paste(im, (i * W, 0))
    sheet.save(os.path.join(outdir, '..', 'portrait_sheet.png'))


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'portraits')
    build(out)
    print('ok', os.path.abspath(out))
