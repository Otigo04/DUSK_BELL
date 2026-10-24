"""Nightward Haus-Baukasten - Grundlagen.
Palette = Style-Bibel (bar_lib, 39 Farben). Alle Texturen sind in 32 px periodisch, damit Kacheln nahtlos sind.
Kanten-Schema wie im restlichen Projekt: Maske = N*1 + E*2 + S*4 + W*8 (Bit = dort geht dasselbe Material weiter)."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bar_lib import *          # Palette, Spr, hsh, rect_o, planks, shingles, stone_base ...
from nwlib import Spr, hsh

BK = TILES + '/Baukasten'
N, E, S, W = 1, 2, 4, 8

# Abdunkeln / Aufhellen innerhalb der Palette (max. 3 Stufen je Material, Schatten violett-kuehl)
_DARK = {
    MOON: ST_L, CREAM: SAND, ST_L: ST_M, ST_M: ST_D, ST_D: SV_D, SV_L: SV_M, SV_M: SV_D, SV_D: OL2, OL2: OL1,
    SAND: WOOD_L, WOOD_L: WOOD_M, WOOD_M: WOOD_D, WOOD_D: EARTH, EARTH: OL2,
    LEAF: GRASS_L, GRASS_L: GRASS, GRASS: FOR_M, FOR_M: FOR_D, FOR_D: OL2,
    ROSE: RED_D, RED_D: SK_S, SK_S: EARTH, SK_L: SK_M, SK_M: SK_S,
    BLUE_L: BLUE_D, BLUE_D: NB_M, NB_L: NB_M, NB_M: NB_D, NB_D: OL1,
    YEL: ORA, ORA: GLOW, GLOW: RED_D,
}
_LITE = {
    ST_D: ST_M, ST_M: ST_L, ST_L: MOON, SV_D: SV_M, SV_M: SV_L, OL2: SV_D,
    EARTH: WOOD_D, WOOD_D: WOOD_M, WOOD_M: WOOD_L, WOOD_L: SAND, SAND: CREAM,
    FOR_D: FOR_M, FOR_M: GRASS, GRASS: GRASS_L, GRASS_L: LEAF,
    SK_S: RED_D, RED_D: ROSE, NB_D: NB_M, NB_M: NB_L, BLUE_D: BLUE_L, NB_L: BLUE_L,
}


def dk(c, n=1):
    for _ in range(n):
        c = _DARK.get(c, c)
    return c


def lt(c, n=1):
    for _ in range(n):
        c = _LITE.get(c, c)
    return c


def ph(x, y, seed):
    """periodischer Hash (32er-Raster)"""
    return hsh(x % 32, y % 32, seed)


def tex_tile(fn, seed=0, w=32, h=32):
    s = Spr(w, h)
    for y in range(h):
        for x in range(w):
            c = fn(x, y, seed)
            if c:
                s.set(x, y, c)
    return s


def darken_rect(s, x0, y0, x1, y1, n=1):
    for y in range(max(0, y0), min(s.h - 1, y1) + 1):
        for x in range(max(0, x0), min(s.w - 1, x1) + 1):
            c = s.get(x, y)
            if c[3]:
                s.set(x, y, dk(c, n))


def lighten_rect(s, x0, y0, x1, y1, n=1):
    for y in range(max(0, y0), min(s.h - 1, y1) + 1):
        for x in range(max(0, x0), min(s.w - 1, x1) + 1):
            c = s.get(x, y)
            if c[3]:
                s.set(x, y, lt(c, n))


def dither_dark(s, x0, y0, x1, y1, level):
    """Schatten-Overlay mit Bayer-Dither (level 0..16) - nur fuer weiche Uebergaenge (Style-Bibel)."""
    B = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    for y in range(max(0, y0), min(s.h - 1, y1) + 1):
        for x in range(max(0, x0), min(s.w - 1, x1) + 1):
            if B[y % 4][x % 4] < level:
                c = s.get(x, y)
                if c[3]:
                    s.set(x, y, dk(c))


def outline_obj(s, col=OL1):
    """1px-Outline um alle undurchsichtigen Pixel (nur 4er-Nachbarschaft, keine Diagonalen)."""
    add = []
    for y in range(s.h):
        for x in range(s.w):
            if s.solid(x, y):
                continue
            if any(s.solid(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                add.append((x, y))
    for x, y in add:
        s.set(x, y, col)


def hline(s, x0, x1, y, c):
    for x in range(x0, x1 + 1):
        s.set(x, y, c)


def vline(s, x, y0, y1, c):
    for y in range(y0, y1 + 1):
        s.set(x, y, c)


def box(s, x0, y0, x1, y1, fill, out=OL1, hi=None, lo=None):
    """Kasten mit Outline, Lichtkante oben/links, Schattenkante unten/rechts."""
    s.rect(x0, y0, x1, y1, out)
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    s.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)
    hi = lt(fill) if hi is None else hi
    lo = dk(fill) if lo is None else lo
    hline(s, x0 + 1, x1 - 1, y0 + 1, hi)
    vline(s, x0 + 1, y0 + 1, y1 - 1, hi)
    hline(s, x0 + 1, x1 - 1, y1 - 1, lo)
    vline(s, x1 - 1, y0 + 2, y1 - 1, lo)


def flame(s, cx, yb, h, f, big=False):
    """kleine Kerzen-/Lampenflamme, f = Frame (0..3) - ruhiges Flackern."""
    sway = [0, 0, 1, 0, -1, 0][f % 6] if big else [0, 1, 0, -1][f % 4] * 0
    hh = h + [0, 1, 0, -1][f % 4]
    for i in range(hh):
        y = yb - i
        x = cx + (sway if i >= hh - 2 else 0)
        c = ORA if i == 0 else (YEL if i < hh - 1 else CREAM if f % 2 == 0 else YEL)
        s.set(x, y, c)
    s.set(cx, yb - 1, CREAM if hh > 2 else YEL)


class Reg:
    """Objekt-Register: name -> (Spr, kategorie, fuss-Zeilen). Animationen: name -> (frames, ms)."""
    def __init__(self):
        self.obj, self.anim = {}, {}

    def add(self, name, spr, kat, fuss=1, solid=True):
        assert spr.w % 32 == 0 and spr.h % 32 == 0, (name, spr.w, spr.h)
        assert name not in self.obj, 'doppelt: ' + name
        self.obj[name] = (spr, kat, fuss, solid)

    def add_anim(self, name, frames, ms, kat, fuss=1, solid=True):
        for f in frames:
            assert (f.w, f.h) == (frames[0].w, frames[0].h), name
        self.add(name, frames[0], kat, fuss, solid)
        self.anim[name] = (frames, ms)


TAL, TAL_H, TAL_D = H('6fd3e6'), H('a8f0ff'), H('2b6b8a')
MON_EYE, TEETH, BLOOD = H('d64a6a'), H('f2ead8'), H('8a1f3d')
