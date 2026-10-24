"""Maske fuer die interact-Sheets (kein Generator vorhanden): erkennt Jacke, Hose und Schuhe an den Farben.
Licht/Grund der Jacke und die Jeans sind eindeutig. Schatten/Tief der Jacke und die Schuhfarben teilen sich Braun-Toene mit dem Rucksack:
Jackenschatten zaehlt nur neben Jackenpixeln, Schuhe nur in den untersten Zeilen der Figur.
Aufruf: python mask_interact.py <Ausgabeordner>  -> <Ordner>/<Mann|Frau>/<name>_interact.png (Format wie NW_MASK=1)"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import os
import sys

from PIL import Image

import gen_hauptfiguren as G


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


JK = [rgb(c) for c in G.JACKET]                     # Licht, Grund, Schatten, Tief
PANTS = {rgb(G.B1): 0, rgb(G.B2): 1, rgb(G.B3): 2}
SHOE = {rgb(G.HR): 0, rgb(G.K2): 0, rgb(G.W1): 1, rgb(G.W2): 2, rgb(G.W3): 3}
CELL = 56


def mask_cell(im, cx, cy):
    px = im.load()
    pts = {(x, y): px[cx + x, cy + y][:3] for y in range(CELL) for x in range(CELL) if px[cx + x, cy + y][3] > 0}
    if not pts:
        return {}
    bottom = max(y for _, y in pts)
    core = {p for p, c in pts.items() if c in (JK[0], JK[1])}
    out = {}
    for (x, y), c in pts.items():
        if c == JK[0]:
            out[(x, y)] = (1, 0)
        elif c == JK[1]:
            out[(x, y)] = (1, 1)
        elif c in (JK[2], JK[3]):
            n = sum(1 for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and (x + dx, y + dy) in core)
            if n >= 2:
                out[(x, y)] = (1, 2 if c == JK[2] else 3)
        if (x, y) in out:
            continue
        if c in PANTS:
            out[(x, y)] = (2, PANTS[c])
        elif c in SHOE and y >= bottom - 5:
            out[(x, y)] = (3, SHOE[c])
    return out


def main(out_dir):
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    for who in ('Mann', 'Frau'):
        name = '%s_interact.png' % who.lower()
        im = Image.open(os.path.join(base, who, name)).convert('RGBA')
        mask = Image.new('RGBA', im.size, (0, 0, 0, 0))
        for cy in range(0, im.height, CELL):
            for cx in range(0, im.width, CELL):
                for (x, y), (reg, idx) in mask_cell(im, cx, cy).items():
                    mask.putpixel((cx + x, cy + y), (reg, idx, 0, 255))
        os.makedirs(os.path.join(out_dir, who), exist_ok=True)
        mask.save(os.path.join(out_dir, who, name))
        print('ok', name)


if __name__ == '__main__':
    main(sys.argv[1])
