"""Doctor Veronica: Portraits 64x64 (Quelle laut NPC-Doku), nur Hex-Werte der Nightward-Palette.

Ausdruecke laut Doku: Ruhig (Standard), Mitfuehlend, Traurig, Entschlossen.
Dazu Blinzeln (calm mit geschlossenen Augen) und die Sprechmuender A, E, O (Basis: Ruhig), wie bei den anderen Figuren.

Aufruf:  python gen_doctor_veronica_portraits.py [Ausgabeordner]
"""
import math
import os
import sys

from PIL import Image

W = 64
PAL = set('#' + p for p in ('1a1526 2b2140 3d2e4a 4f3d5c 6b5a7a 1f2a3d 2c3e56 3f5570 e8e0f0 3b2a22 5c4033 7a5a43 9c7a5a b89a72 '
                            '1e3a2b 2f5a3c 4a7a4f 6e9a5e 9ab87a 4a4550 6e6a74 9a95a0 5e3d33 8c5f4d d19a7a 7a2e3a c4636b 3a4a7a '
                            '6b7fb8 ffd27a ffa550 e8733a fff1c9 6fd3e6 a8f0ff 2b6b8a f2ead8 d64a6a 8a1f3d').split())

K, K2 = '#1a1526', '#2b2140'
SL, SM, SD = '#d19a7a', '#8c5f4d', '#5e3d33'
HL, HB, HS, HD = '#e8e0f0', '#9a95a0', '#6e6a74', '#4a4550'   # graues Haar: Licht, Grund, Schatten, tief
HV = '#6b5a7a'                                                 # kuehles Violett im Haarschatten
CG = ('#b89a72', '#9c7a5a', '#7a5a43', '#5c4033')              # Strickjacke
KW = ('#e8e0f0', '#9a95a0', '#6b5a7a')                         # Kittel
WARM = '#fff1c9'
IRIS = '#5c4033'
LIP = '#c4636b'


class Pn:
    def __init__(s):
        s.b = [[None] * W for _ in range(W)]

    def P(s, x, y, c):
        if 0 <= x < W and 0 <= y < W:
            s.b[y][x] = c

    def R(s, x1, y1, x2, y2, c):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                s.P(x, y, c)

    def E(s, cx, cy, rx, ry, c):
        for y in range(W):
            for x in range(W):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    s.P(x, y, c)

    def inE(s, x, y, cx, cy, rx, ry):
        return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def sym(x):
    return 63 - x


def line(p, x0, y0, x1, y1, c, th=1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = int(round(x0 + (x1 - x0) * i / n))
        y = int(round(y0 + (y1 - y0) * i / n))
        for t in range(th):
            p.P(x, y + t, c)


# ---------------------------------------------------------------- Koerper
def bust(p):
    base, mid, sh, dk = CG[1], CG[1], CG[2], CG[3]
    for y in range(49, W):
        hw = 17 + (y - 49) * 1.6
        x1, x2 = int(round(32 - hw)), int(round(31 + hw))
        for x in range(max(0, x1), min(W - 1, x2) + 1):
            c = base
            if x >= 44:
                c = sh                                              # kuehler Schatten rechts
            elif x >= 41 and (x + y) % 2 == 0:
                c = sh                                              # Dither zur Mitte
            if x - x1 < 2 and y < 54:
                c = CG[0]                                           # Schulterlicht links oben
            p.P(x, y, c)
        p.P(max(0, x1), y, CG[0] if y < 56 else base)
    # Strickrippen links und rechts vom Kittel
    for y in range(54, W):
        for x in list(range(8, 24, 3)) + list(range(41, 58, 3)):
            if (y // 2) % 2 == 0:
                p.P(x, y, sh)
    # Kittel: V-Ausschnitt mit Kragen
    for y in range(48, 60):
        hw = 9 - (y - 48) * 0.75
        if hw < 1.5:
            hw = 1.5
        for x in range(int(round(32 - hw)), int(round(32 + hw))):
            p.P(x, y, KW[0])
        p.P(int(round(32 - hw)), y, KW[1])
        p.P(int(round(31 + hw)), y, KW[1] if y > 49 else KW[0])
    p.R(30, 59, 33, W - 1, KW[0])
    p.R(30, 59, 30, W - 1, KW[1])
    p.R(33, 59, 33, W - 1, KW[1])
    for y in range(60, W, 4):
        p.P(31, y, KW[2])                                           # Knoepfe
        p.P(32, y, KW[2])
    # Hals mit Hautschatten unter dem Kinn
    p.R(26, 40, 37, 50, SL)
    p.R(26, 40, 26, 50, SM)
    p.R(34, 40, 37, 50, SM)
    p.R(26, 44, 37, 47, SM)                                         # Kinnschatten
    for x in range(27, 34):
        p.P(x, 44, SM)
    # V-Hautfeld
    for y in range(49, 55):
        hw = 4.5 - (y - 49) * 0.9
        for x in range(int(round(32 - hw)), int(round(32 + hw))):
            p.P(x, y, SL if x < 33 else SM)
    # Kittelkragen-Spitzen neben dem Hals
    for y in range(46, 52):
        p.R(23 + (y - 46) // 2, y, 26, y, KW[0])
        p.R(37, y, 40 - (y - 46) // 2, y, KW[0] if y < 50 else KW[1])
    p.R(23, 46, 25, 47, KW[0])
    p.R(38, 46, 40, 47, KW[1])


# ---------------------------------------------------------------- Kopf
def hairline(x):
    """Haaransatz-Hoehe an Spalte x: mittig geteilt, zu den Schlaefen hin tiefer."""
    d = (x + 0.5 - 32) / 14.0
    return 17.5 + 7.0 * d * d


def head(p):
    # Haarmasse hinten + Dutt
    p.E(32, 23, 18, 18.5, HB)
    p.E(32, 5.5, 6.5, 5.0, HB)
    p.R(27, 8, 36, 12, HB)
    # Gesicht
    p.E(32, 28.5, 13.7, 16.5, SL)
    for y in range(W):
        for x in range(W):
            if p.inE(x, y, 32, 28.5, 13.7, 16.5):
                if x >= 41:
                    p.P(x, y, SM)                                   # Schatten rechts
                elif x >= 39 and (x + y) % 2 == 0:
                    p.P(x, y, SM)                                   # Dither zum Licht
    # Kinn-Unterkante etwas dunkler
    for x in range(24, 41):
        if p.inE(x, 44, 32, 28.5, 13.7, 16.5):
            p.P(x, 44, SM)
    # Haar vorn: Stirn-Kappe und Koteletten
    for y in range(W):
        for x in range(W):
            if not p.inE(x, y, 32, 28.5, 13.7, 16.5):
                continue
            side = abs(x + 0.5 - 32) >= 12.2 and y <= 33
            if y < hairline(x) or side:
                p.P(x, y, HB)
    # Haarstruktur: Straehnen laufen vom Scheitel nach hinten
    for y in range(W):
        for x in range(W):
            if p.b[y][x] not in (HB,):
                continue
            inside_hair = p.inE(x, y, 32, 23, 18, 18.5) or p.inE(x, y, 32, 5.5, 6.5, 5.0) or (27 <= x <= 36 and 8 <= y <= 12)
            if not inside_hair:
                continue
            right = x >= 38
            k = int(math.atan2(y + 0.5 - 7, x + 0.5 - 32) * 9)    # Straehnen laufen strahlenfoermig zum Dutt
            if right:
                p.P(x, y, HS if x >= 41 else HB)                    # Haarschatten rechts
                if k % 3 == 0:
                    p.P(x, y, HB if x >= 41 else HL)
                elif k % 4 == 2 and x >= 41:
                    p.P(x, y, HD)
            else:
                if k % 3 == 0:
                    p.P(x, y, HL)                                   # helle Straehne, nach oben gekaemmt
                elif k % 3 == 1 and y > 20:
                    p.P(x, y, HS)
    # Scheitel
    for y in range(11, 17):
        p.P(31, y, HS)
        p.P(32, y, HS)
    # Dutt: Licht links oben, Schatten rechts unten, Wicklung als Bogen
    for y in range(0, 11):
        for x in range(24, 41):
            if p.inE(x, y, 32, 5.5, 6.5, 5.0):
                d = ((x + 0.5 - 32) / 6.5) ** 2 + ((y + 0.5 - 5.5) / 5.0) ** 2
                c = HB
                if x < 31 and y < 5:
                    c = HL
                if x >= 35 or y >= 8:
                    c = HS
                if int(d * 6) % 2 == 1 and d > 0.15:
                    c = HS if c != HL else HB                       # Wicklung
                p.P(x, y, c)
    p.P(28, 2, HL)
    p.P(29, 1, HL)
    # Ohr-Andeutung unter dem Haar (Laeppchen)
    p.P(18, 35, SM)
    p.P(45, 35, SM)


# ---------------------------------------------------------------- Gesichtszuege
def eye(p, left, mode):
    """mode: open, sad, narrow, closed. Linkes Auge x 22..27, rechtes gespiegelt (x 36..41)."""
    xs = list(range(22, 28))
    iris = (24, 25)
    y0 = 27

    def X(x):
        return x if left else sym(x)

    if mode == 'closed':
        for x in xs:
            p.P(X(x), y0 + 1, K2)
        for x in xs[1:-1]:
            p.P(X(x), y0 + 2, SM)
        return
    p.R(X(22), y0 - 1, X(27), y0 - 1, K2)                      # Oberlid
    if left:
        p.P(21, y0 - 1, K2)
    else:
        p.P(42, y0 - 1, K2)
    h = 3 if mode in ('open',) else 2
    rows = list(range(y0, y0 + h))
    for y in rows:
        for x in xs:
            p.P(X(x), y, HL)
    if mode == 'sad':                                           # schweres Lid, feuchter Glanz
        for x in xs:
            p.P(X(x), y0, SL)
        for x in iris:
            p.P(X(x), y0 + 1, IRIS)
        p.P(X(25), y0 + 1, WARM)
        for x in xs:
            p.P(X(x), y0 + 2, SM)
        for x in xs[1:-1]:
            p.P(X(x), y0 + 3, SM)                               # Traenensack
        return
    if mode == 'narrow':                                       # Lid schraeg nach innen unten
        p.R(X(22), y0, X(27), y0, SL)
        for x in iris:
            p.P(X(x), y0 + 1, IRIS)
        for x in xs:
            p.P(X(x), y0 + 2, SM)
        return
    for x in iris:
        p.P(X(x), y0, K)
        p.P(X(x), y0 + 1, IRIS)
    p.P(X(24 if left else 25), y0, K2)
    for x in xs:
        p.P(X(x), y0 + 2, SM)                                   # Unterlid
    p.P(X(26), y0 + 1, HL)


def brows(p, outer, inner, thick=2):
    """outer/inner: y der Braue aussen bzw. innen. Linke Braue x 21..28, rechte gespiegelt."""
    for left in (True, False):
        pts = []
        for i, x in enumerate(range(21, 29)):
            t = i / 7.0
            y = outer + (inner - outer) * t
            pts.append((x, int(round(y))))
        for x, y in pts:
            X = x if left else sym(x)
            for k in range(thick):
                c = HS if k == 0 else HD
                p.P(X, y + k, c)
        # Brauenende duenn auslaufen lassen
        X0 = 21 if left else sym(21)
        p.P(X0, pts[0][1] + thick - 1, SL) if thick > 1 and False else None


def nose(p):
    for y in range(29, 34):
        p.P(33, y, SM)
    p.P(31, 31, WARM)
    p.R(30, 34, 33, 34, SD)
    p.P(29, 34, SM)
    p.P(34, 34, SM)
    p.P(30, 35, SD)
    p.P(33, 35, SD)


def age_lines(p, heavy=False):
    for dx in (0, 1):
        pass
    p.P(20, 27, SM)
    p.P(19, 28, SM)
    p.P(20, 29, SM)
    p.P(sym(20), 27, SM)
    p.P(sym(19), 28, SM)
    p.P(sym(20), 29, SM)
    for (x, y) in ((27, 35), (26, 36), (26, 37), (25, 38)):
        p.P(x, y, SM)
    for (x, y) in ((sym(27), 35), (sym(26), 36), (sym(26), 37), (sym(25), 38)):
        p.P(x, y, SD)
    if heavy:
        p.R(23, 31, 26, 31, SM)
        p.R(37, 31, 40, 31, SM)
    p.R(27, 18, 28, 18, SM)                                     # Stirnfalte unter dem Haar
    p.R(35, 18, 36, 18, SM)


def mouth(p, kind):
    y = 39
    if kind == 'calm':
        p.R(29, y, 35, y, SD)
        p.P(28, y - 1, SM)
        p.P(36, y - 1, SM)
        p.R(30, y + 1, 34, y + 1, SM)
        p.R(31, y + 2, 33, y + 2, SL)
    elif kind == 'warm':
        p.R(29, y, 35, y, SD)
        p.R(27, y - 1, 28, y - 1, SD)
        p.R(36, y - 1, 37, y - 1, SD)
        p.R(30, y + 1, 34, y + 1, LIP)
        p.R(31, y + 2, 33, y + 2, SL)
        p.P(26, y - 2, SM)
        p.P(38, y - 2, SM)
    elif kind == 'sad':
        p.R(29, y, 35, y, SD)
        p.P(28, y + 1, SD)
        p.P(36, y + 1, SD)
        p.R(30, y + 1, 34, y + 1, SM)
        p.R(31, y + 2, 33, y + 2, SM)
        p.P(27, y + 2, SM)
        p.P(37, y + 2, SM)
    elif kind == 'firm':
        p.R(27, y, 37, y, SD)
        p.R(28, y + 1, 36, y + 1, SM)
        p.R(31, y + 2, 33, y + 2, SM)
        p.P(22, 36, SM)                                         # Kiefermuskel
        p.P(23, 37, SM)
        p.P(41, 36, SD)
        p.P(40, 37, SD)
    elif kind == 'A':
        p.R(29, y - 1, 35, y - 1, SD)
        p.R(28, y, 36, y + 3, K2)
        p.R(29, y + 4, 35, y + 4, K2)
        p.R(30, y + 3, 34, y + 3, SD)                            # Zunge
        p.R(30, y + 5, 34, y + 5, SM)
    elif kind == 'E':
        p.R(29, y - 1, 35, y - 1, SD)
        p.R(28, y, 36, y + 1, K2)
        p.R(29, y + 2, 35, y + 2, SD)
        p.R(30, y + 3, 34, y + 3, SM)
    elif kind == 'O':
        p.R(30, y - 1, 34, y - 1, SD)
        p.R(30, y, 34, y + 3, K2)
        p.R(31, y + 4, 33, y + 4, K2)
        p.R(29, y + 1, 29, y + 2, SM)
        p.R(35, y + 1, 35, y + 2, SD)
        p.R(31, y + 5, 33, y + 5, SM)


def outline(p):
    out = [row[:] for row in p.b]
    for y in range(W):
        for x in range(W):
            if p.b[y][x] is None:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < W and 0 <= Y < W and p.b[Y][X] is not None:
                        out[y][x] = K
                        break
    return out


EXPR = {
    'calm':          dict(eye='open',   brows=(23, 23, 2), mouth='calm', heavy=False),
    'compassionate': dict(eye='open',   brows=(24, 22, 2), mouth='warm', heavy=False),
    'sad':           dict(eye='sad',    brows=(25, 21, 2), mouth='sad',  heavy=True),
    'determined':    dict(eye='narrow', brows=(22, 25, 2), mouth='firm', heavy=False),
    'blink':         dict(eye='closed', brows=(23, 23, 2), mouth='calm', heavy=False),
    'talk_A':        dict(eye='open',   brows=(23, 23, 2), mouth='A',    heavy=False),
    'talk_E':        dict(eye='open',   brows=(23, 23, 2), mouth='E',    heavy=False),
    'talk_O':        dict(eye='open',   brows=(23, 23, 2), mouth='O',    heavy=False),
}
ORDER = ['calm', 'compassionate', 'sad', 'determined', 'blink', 'talk_A', 'talk_E', 'talk_O']


def render(name):
    e = EXPR[name]
    p = Pn()
    bust(p)
    head(p)
    age_lines(p, e['heavy'])
    brows(p, *e['brows'])
    eye(p, True, e['eye'])
    eye(p, False, e['eye'])
    nose(p)
    mouth(p, e['mouth'])
    return outline(p)


def to_img(buf):
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    for y in range(W):
        for x in range(W):
            c = buf[y][x]
            if c:
                if c not in PAL:
                    raise SystemExit('Farbe nicht in Palette: %s (%d,%d)' % (c, x, y))
                im.putpixel((x, y), tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    return im


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    sheet = Image.new('RGBA', (len(ORDER) * W, W))
    for i, n in enumerate(ORDER):
        im = to_img(render(n))
        im.save(os.path.join(outdir, 'veronica_%s.png' % n))
        sheet.paste(im, (i * W, 0))
    sheet.save(os.path.join(outdir, '..', 'portrait_sheet.png'))


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'portraits')
    build(out)
    print('ok', os.path.abspath(out))
