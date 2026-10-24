"""Nightward Bar-Lib: Style-Bibel-Palette (Art/Palette.gpl), Schrift, Helfer.
Alle Farben stammen aus der Style-Bibel (39 Farben). Keine Fremdfarben, kein Alpha ausser 0/255."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nwlib import Spr, hsh  # Sprite-Klasse + deterministischer Hash

ART = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')).replace('\\', '/')   # Art/ relativ zu diesem Ordner (laeuft auf Mac und Windows)
TILES = ART + '/Tiles'


def H(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


OL1, OL2 = H('1a1526'), H('2b2140')
SV_D, SV_M, SV_L = H('3d2e4a'), H('4f3d5c'), H('6b5a7a')
NB_D, NB_M, NB_L, MOON = H('1f2a3d'), H('2c3e56'), H('3f5570'), H('e8e0f0')
EARTH, WOOD_D, WOOD_M, WOOD_L, SAND = H('3b2a22'), H('5c4033'), H('7a5a43'), H('9c7a5a'), H('b89a72')
FOR_D, FOR_M, GRASS, GRASS_L, LEAF = H('1e3a2b'), H('2f5a3c'), H('4a7a4f'), H('6e9a5e'), H('9ab87a')
ST_D, ST_M, ST_L = H('4a4550'), H('6e6a74'), H('9a95a0')
SK_S, SK_M, SK_L = H('5e3d33'), H('8c5f4d'), H('d19a7a')
RED_D, ROSE, BLUE_D, BLUE_L = H('7a2e3a'), H('c4636b'), H('3a4a7a'), H('6b7fb8')
YEL, ORA, GLOW, CREAM = H('ffd27a'), H('ffa550'), H('e8733a'), H('fff1c9')
CLEAR = (0, 0, 0, 0)

# ---------------------------------------------------------------- Schrift
_F57 = {
    'A': '01110 10001 10001 11111 10001 10001 10001',
    'B': '11110 10001 10001 11110 10001 10001 11110',
    'E': '11111 10000 10000 11110 10000 10000 11111',
    'H': '10001 10001 10001 11111 10001 10001 10001',
    'I': '01110 00100 00100 00100 00100 00100 01110',
    'L': '10000 10000 10000 10000 10000 10000 11111',
    'N': '10001 11001 10101 10011 10001 10001 10001',
    'O': '01110 10001 10001 10001 10001 10001 01110',
    'R': '11110 10001 10001 11110 10100 10010 10001',
    'S': '01111 10000 10000 01110 00001 00001 11110',
    'T': '11111 00100 00100 00100 00100 00100 00100',
}
_F35 = {
    'A': '010 101 111 101 101', 'B': '110 101 110 101 110', 'C': '011 100 100 100 011',
    'D': '110 101 101 101 110', 'E': '111 100 110 100 111', 'F': '111 100 110 100 100',
    'G': '011 100 101 101 011', 'H': '101 101 111 101 101', 'I': '111 010 010 010 111',
    'J': '001 001 001 101 010', 'K': '101 101 110 101 101', 'L': '100 100 100 100 111',
    'M': '101 111 111 101 101', 'N': '110 101 101 101 101', 'O': '010 101 101 101 010',
    'P': '110 101 110 100 100', 'Q': '010 101 101 110 011', 'R': '110 101 110 101 101',
    'S': '011 100 010 001 110', 'T': '111 010 010 010 010', 'U': '101 101 101 101 111',
    'V': '101 101 101 101 010', 'W': '101 111 111 111 101', 'X': '101 101 010 101 101',
    'Y': '101 101 010 010 010', 'Z': '111 001 010 100 111',
    '0': '111 101 101 101 111', '1': '010 110 010 010 111', '2': '110 001 010 100 111',
    '3': '110 001 010 001 110', '4': '101 101 111 001 001', '5': '111 100 110 001 110',
    '6': '011 100 110 101 010', '7': '111 001 010 010 010', '8': '010 101 010 101 010',
    '9': '010 101 011 001 110', '.': '000 000 000 000 010', '-': '000 000 111 000 000',
    ' ': '000 000 000 000 000', ':': '000 010 000 010 000', '!': '010 010 010 000 010',
}


def _glyphs(tbl):
    return {k: [r for r in v.split()] for k, v in tbl.items()}


G57, G35 = _glyphs(_F57), _glyphs(_F35)


def text_width(txt, font='5x7', scale=1, gap=1):
    g, w = (G57, 5) if font == '5x7' else (G35, 3)
    return sum((w if c != ' ' else w - 1) * scale + gap * scale for c in txt) - gap * scale


def draw_text(s, txt, x, y, col, font='5x7', scale=1, gap=1, shadow=None):
    g, w = (G57, 5) if font == '5x7' else (G35, 3)
    cx = x
    for ch in txt:
        rows = g.get(ch)
        cw = (w if ch != ' ' else w - 1)
        if rows:
            for ry, row in enumerate(rows):
                for rx, b in enumerate(row):
                    if b == '1':
                        for sy in range(scale):
                            for sx in range(scale):
                                if shadow:
                                    s.set(cx + rx * scale + sx + 1, y + ry * scale + sy + 1, shadow)
        if rows:
            for ry, row in enumerate(rows):
                for rx, b in enumerate(row):
                    if b == '1':
                        for sy in range(scale):
                            for sx in range(scale):
                                s.set(cx + rx * scale + sx, y + ry * scale + sy, col)
        cx += (cw + gap) * scale


# ---------------------------------------------------------------- Helfer
def darken(c):
    m = {WOOD_L: WOOD_M, WOOD_M: WOOD_D, WOOD_D: EARTH, SAND: WOOD_L, ST_L: ST_M, ST_M: ST_D, ST_D: OL2}
    return m.get(c, c)


def rect_o(s, x0, y0, x1, y1, fill, out=OL1):
    """Rechteck mit 1px Outline (Outline liegt innerhalb)."""
    s.rect(x0, y0, x1, y1, out)
    if x1 - x0 >= 2 and y1 - y0 >= 2:
        s.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill)


def planks(s, x0, y0, x1, y1, base=WOOD_M, lite=WOOD_L, dark=WOOD_D, seam=EARTH, vertical=True, seed=1):
    """Bretter. vertical: senkrechte Bretter, Breite 8 (nahtlos in X)."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if vertical:
                u, v = (x - x0) % 8, y - y0
            else:
                u, v = (y - y0) % 8, x - x0
            c = base
            if u == 0:
                c = seam
            elif u == 1:
                c = lite
            elif u == 7:
                c = dark
            r = hsh(x, y, seed)
            if u not in (0, 1, 7):
                if r < 0.05:
                    c = dark
                elif r > 0.97:
                    c = lite
            if vertical:
                if u == 4 and (y - y0) % 16 == 4:
                    c = ST_L
                if u == 4 and (y - y0) % 16 == 5:
                    c = ST_D
            s.set(x, y, c)


def shingles(s, x0, y0, x1, y1, seed=3):
    """Holzschindeln: Reihen 8 hoch, Schindeln 8 breit, versetzt. Nahtlos in X (32er) und Y (8er)."""
    for y in range(y0, y1 + 1):
        course, cy = divmod(y - y0, 8)
        for x in range(x0, x1 + 1):
            xo = (x - x0 + (course % 2) * 4) % 8
            idx = (x - x0 + (course % 2) * 4) // 8
            cool = hsh(idx, course, seed) < 0.28
            base, hi, sh = (SV_D, SV_M, OL2) if cool else (WOOD_D, WOOD_M, EARTH)
            c = base
            if cy == 0:
                c = hi
            elif cy >= 6:
                c = sh
            if xo == 0 and cy > 0:
                c = sh
            elif xo == 1 and 0 < cy < 6 and hsh(x, y, seed + 9) < 0.35:
                c = hi
            s.set(x, y, c)


def barge(s, side, y0, y1):
    """Ortgangbrett (senkrecht) links 'L' oder rechts 'R', 6px breit."""
    xs = range(0, 6) if side == 'L' else range(31, 25, -1)
    cols = [OL1, WOOD_L, WOOD_M, WOOD_M, WOOD_D, OL1]
    for i, x in enumerate(xs):
        for y in range(y0, y1 + 1):
            s.set(x, y, cols[i])


def stone_base(s, x0, y0, x1, y1, seed=5):
    """Steinsockel, Blöcke 16x8 versetzt."""
    for y in range(y0, y1 + 1):
        course, cy = divmod(y - y0, 8)
        for x in range(x0, x1 + 1):
            xo = (x - x0 + (course % 2) * 8) % 16
            c = ST_M
            if cy == 0:
                c = ST_L
            elif cy == 7:
                c = ST_D
            if xo == 0:
                c = ST_D
            elif xo == 1 and cy not in (0, 7):
                c = ST_L
            elif hsh(x, y, seed) < 0.07 and cy not in (0, 7):
                c = ST_D
            s.set(x, y, c)


def ell_o(s, cx, cy, rx, ry, fill, out=OL1):
    s.ellipse(cx, cy, rx + 1, ry + 1, out)
    s.ellipse(cx, cy, rx, ry, fill)


def px_list(s, pts, col):
    for x, y in pts:
        s.set(x, y, col)


def crop(s, x, y, w, h):
    o = Spr(w, h)
    o.im.paste(s.im.crop((x, y, x + w, y + h)), (0, 0))
    o.p = o.im.load()
    return o


def load_item(name):
    from PIL import Image
    path = ART + '/Items/Getraenke/' + name + '.png'
    im = Image.open(path).convert('RGBA')
    o = Spr(im.width, im.height)
    o.im = im
    o.p = im.load()
    return o


class Sheet:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.spr = Spr(cols * 32, rows * 32)
        self.index = {}

    def put(self, name, col, row, piece):
        assert piece.w % 32 == 0 and piece.h % 32 == 0, (name, piece.w, piece.h)
        assert col * 32 + piece.w <= self.cols * 32 and row * 32 + piece.h <= self.rows * 32, name
        for yy in range(piece.h):
            for xx in range(piece.w):
                if self.spr.get(col * 32 + xx, row * 32 + yy)[3] and piece.p[xx, yy][3]:
                    pass
        self.spr.paste(piece, col * 32, row * 32)
        self.index[name] = (col, row, piece)

    def piece(self, name):
        return self.index[name][2]

    def save(self, path):
        self.spr.save(path)


def compose(canvas_w, canvas_h, bg, placements, sheet):
    """placements: (name, tx, ty[, dx, dy]) in Kachelkoordinaten -> Vorschaubild."""
    out = Spr(canvas_w * 32, canvas_h * 32)
    out.rect(0, 0, out.w - 1, out.h - 1, bg)
    for pl in placements:
        name, tx, ty = pl[0], pl[1], pl[2]
        dx, dy = (pl[3], pl[4]) if len(pl) > 3 else (0, 0)
        out.paste(sheet.piece(name), tx * 32 + dx, ty * 32 + dy)
    return out


def check_palette(path):
    from PIL import Image
    pal = set()
    for l in open(ART + '/Palette.gpl'):
        t = l.split()
        if len(t) >= 3 and t[0].isdigit():
            pal.add((int(t[0]), int(t[1]), int(t[2])))
    im = Image.open(path).convert('RGBA')
    bad = [c for _, c in im.getcolors(10 ** 7) if c[3] > 0 and (c[:3] not in pal or c[3] != 255)]
    return bad
