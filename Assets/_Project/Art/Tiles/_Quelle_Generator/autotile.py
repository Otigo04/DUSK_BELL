"""Nahtlose Autotile-Engine fuer Weg / Pflaster.
Kanten-Profile sind periodisch (32 px) und an den Kachelecken null -> Nachbarkacheln passen exakt."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
from PIL import Image
from nwlib import *

N, E, S, W = 1, 2, 4, 8
M = 6          # Randabstand zu nicht verbundenen Seiten
PH = {'N': 0.0, 'E': 1.7, 'S': 3.1, 'W': 4.6}


def wob(side, t, amp=1.0):
    a = 2 * math.pi * t / 32.0
    # nur ganze Frequenzen, sin(0)=0 -> Kachelgrenzen sind exakt M
    v = 1.3 * math.sin(a + 0) * math.cos(PH[side]) + 1.0 * math.sin(2 * a) * math.cos(PH[side] * 2) + \
        0.7 * math.sin(3 * a) * math.cos(PH[side] * 3)
    return int(round(v * amp))


def build_mask(mask, notch=None):
    """liefert 32x32 bool Raster 'innen' (Weg)"""
    con = {'N': bool(mask & N), 'E': bool(mask & E), 'S': bool(mask & S), 'W': bool(mask & W)}
    ins = [[True] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            ok = True
            if not con['N'] and y < M + wob('N', x):
                ok = False
            if not con['S'] and y > 31 - (M + wob('S', x)):
                ok = False
            if not con['W'] and x < M + wob('W', y):
                ok = False
            if not con['E'] and x > 31 - (M + wob('E', y)):
                ok = False
            # runde Ecken (beide Seiten offen)
            R = 8
            for (cn, cw, cx, cy, sx, sy) in (('N', 'W', 0, 0, 1, 1), ('N', 'E', 31, 0, -1, 1),
                                           ('S', 'W', 0, 31, 1, -1), ('S', 'E', 31, 31, -1, -1)):
                if not con[cn] and not con[cw]:
                    ox = x if sx == 1 else 31 - x
                    oy = y if sy == 1 else 31 - y
                    if ox < M + R and oy < M + R:
                        d = math.hypot(ox + .5 - (M + R), oy + .5 - (M + R))
                        if d > R:
                            ok = False
            # Innenecke: beide Seiten verbunden, Diagonale fehlt
            if notch:
                cx, cy = {'NE': (32, 0), 'SE': (32, 32), 'SW': (0, 32), 'NW': (0, 0)}[notch]
                if math.hypot(x + .5 - cx, y + .5 - cy) < M + 0.5 + 1.5 * (hsh(x, y, 3) < 0.0):
                    ok = False
            ins[y][x] = ok
    return ins, con


def render(mask, notch, tex, bgtile, edge, rim_dark, rim_lite, seed=0, over=(G_MD, G_BASE)):
    ins, con = build_mask(mask, notch)

    def inside(x, y):
        if 0 <= x < 32 and 0 <= y < 32:
            return ins[y][x]
        # ausserhalb der Kachel: nur wahr wenn diese Seite verbunden ist
        if y < 0:
            return con['N']
        if y > 31:
            return con['S']
        if x < 0:
            return con['W']
        return con['E']

    out = Image.new('RGBA', (32, 32))
    op = out.load()
    bp = bgtile.convert('RGBA').load()
    for y in range(32):
        for x in range(32):
            if ins[y][x]:
                nb = [inside(x + 1, y), inside(x - 1, y), inside(x, y + 1), inside(x, y - 1)]
                ring1 = not all(nb)
                c = tex(x, y)
                if ring1:
                    c = edge
                    if hsh(x, y, seed + 11) < 0.16:
                        c = over[int(hsh(x, y, seed + 12) * 2)]
                else:
                    # zweiter Ring: Licht von oben-links
                    d2 = [inside(x + 2, y), inside(x - 2, y), inside(x, y + 2), inside(x, y - 2)]
                    dg = [inside(x + 1, y + 1), inside(x - 1, y - 1), inside(x + 1, y - 1), inside(x - 1, y + 1)]
                    if not d2[0] or not d2[2] or not dg[0]:
                        c = rim_dark
                    elif not d2[1] or not d2[3] or not dg[1]:
                        c = rim_lite
                op[x, y] = c
            else:
                op[x, y] = bp[x, y]
    # Gras-Saum aussen: dunkler Rand und kleine Halme, die in den Weg ragen
    for y in range(32):
        for x in range(32):
            if not ins[y][x]:
                near = [inside(x + 1, y), inside(x - 1, y), inside(x, y + 1), inside(x, y - 1)]
                if any(near) and hsh(x, y, seed + 21) < 0.55:
                    op[x, y] = GREEN[2] if hsh(x, y, seed + 22) < 0.7 else GREEN[1]
    return out
