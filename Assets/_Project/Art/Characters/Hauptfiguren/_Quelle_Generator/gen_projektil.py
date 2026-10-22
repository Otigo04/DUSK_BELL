"""Projektil (Pistole) und Treffer-Funken: 16x16-Zellen, Palette wie die Hauptfiguren.

projektil_pistole.png : 8 Zeilen (S, SW, W, NW, N, NE, E, SE) x 3 Frames (Flug-Loop, Spitze/Schweif flackert), Mitte = Spitze
projektil_treffer.png : 1 Zeile x 5 Frames (Einschlag, kein Loop)
Aufruf: python gen_projektil.py [Ausgabeordner]
"""
import math
import os
import sys

from PIL import Image

CELL = 16
W, Y, O, R = '#fff1c9', '#ffd27a', '#ffa550', '#e8733a'
DIRS = {'S': (0, 1), 'SW': (-.7, .7), 'W': (-1, 0), 'NW': (-.7, -.7), 'N': (0, -1), 'NE': (.7, -.7), 'E': (1, 0), 'SE': (.7, .7)}
ORDER = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE']
YS = 0.45


def hexrgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def sdir(d):
    x, y = d[0], d[1] * YS
    n = math.hypot(x, y)
    return x / n, y / n


def put(im, x, y, c):
    X, Y = int(math.floor(x + 0.5)), int(math.floor(y + 0.5))
    if 0 <= X < CELL and 0 <= Y < CELL:
        im.putpixel((X, Y), hexrgb(c))


def bullet(d, frame):
    im = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    ux, uy = sdir(d)
    hx, hy = 8 + ux * 2.5, 8 + uy * 2.5
    ln = [5, 7, 6][frame]
    for dx in (0, 1):
        for dy in (0, 1):
            put(im, hx + dx - 0.5, hy + dy - 0.5, W)
    cols = [Y, Y, O, O, R, R, R]
    for i in range(1, ln + 1):
        put(im, hx - ux * (i + 0.7), hy - uy * (i + 0.7), cols[min(i - 1, len(cols) - 1)])
    k = [3, 6, 4][frame]
    put(im, hx - ux * k - uy * 1.6, hy - uy * k + ux * 1.6, O)
    return im


def impact(frame):
    im = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    c = 8
    if frame == 0:
        for a in range(-1, 2):
            for b in range(-1, 2):
                put(im, c + a, c + b, W)
    elif frame == 1:
        for a in range(-1, 2):
            for b in range(-1, 2):
                put(im, c + a, c + b, Y)
        put(im, c, c, W)
        for i in (2, 3):
            for ox, oy in ((i, 0), (-i, 0), (0, i), (0, -i)):
                put(im, c + ox, c + oy, W if i == 2 else Y)
    elif frame == 2:
        for ox, oy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            put(im, c + ox, c + oy, Y)
        for i in (3, 4):
            for ox, oy in ((i, 0), (-i, 0), (0, i), (0, -i)):
                put(im, c + ox, c + oy, O)
        for ox, oy in ((2, 2), (-2, 2), (2, -2), (-2, -2), (3, 3), (-3, 3), (3, -3), (-3, -3)):
            put(im, c + ox, c + oy, Y if abs(ox) == 2 else O)
    elif frame == 3:
        for ox, oy in ((4, 1), (-4, -1), (1, 4), (-1, -4), (3, 3), (-3, 3), (3, -3), (-3, -3), (5, 0), (-5, 0), (0, 5), (0, -5)):
            put(im, c + ox, c + oy, O)
        put(im, c, c, R)
    else:
        for ox, oy in ((5, 2), (-5, -2), (2, 5), (-2, -5), (4, 4), (-4, 4), (6, 0), (-6, 1)):
            put(im, c + ox, c + oy, R)
    return im


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    sheet = Image.new('RGBA', (3 * CELL, 8 * CELL))
    for r, n in enumerate(ORDER):
        for f in range(3):
            sheet.paste(bullet(DIRS[n], f), (f * CELL, r * CELL))
    sheet.save(os.path.join(outdir, 'projektil_pistole.png'))
    hit = Image.new('RGBA', (5 * CELL, CELL))
    for f in range(5):
        hit.paste(impact(f), (f * CELL, 0))
    hit.save(os.path.join(outdir, 'projektil_treffer.png'))


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else '.')
    print('ok')
