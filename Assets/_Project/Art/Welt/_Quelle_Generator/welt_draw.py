"""WELT-ZEICHENHILFEN: kleine Pixel-Zeichenflaeche (Cv), Palette-Farbnamen (COL), Streifen-Export, Schatten.
Alles nur Farben aus Palette.png, Alpha 0/255."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math

import numpy as np
from PIL import Image

from welt_lib import H, hsh

COL = {k: H(v) for k, v in dict(
    ink='1f1630', g0='243b3f', g1='2f5444', g2='3f7347', g3='58903f', g4='7bac45', g5='a4c654', br0='3a2530', br1='5a3a3f', br2='7d5646',
    br3='a37a56', br4='c9a26a', br5='e3c98c', s0='3d3850', s1='5a566e', s2='7a7790', s3='9e9bb2', s4='c4c1d2', s5='e4e0ea',
    b0='23336b', b1='2f4f8f', b2='3f72b0', b3='5b99c4', b4='8cc4d6', b5='cfeef0', pk='e07a9a', cream='efe7dd', yel='f6d34a', wine='8a3550', violet='7a6ad8', purp='6b4d8c', or1='e8863f', or2='f3a65a', red='c04b3f').items()}


class Cv:
    """Kleine Zeichenflaeche (RGBA, nur 0/255-Alpha)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)

    def set(self, x, y, c):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = COL[c] if isinstance(c, str) else c

    def get(self, x, y):
        x, y = int(math.floor(x)), int(math.floor(y))
        return tuple(self.a[y, x]) if 0 <= x < self.w and 0 <= y < self.h else (0, 0, 0, 0)

    def solid(self, x, y):
        x, y = int(math.floor(x)), int(math.floor(y))
        return 0 <= x < self.w and 0 <= y < self.h and self.a[y, x, 3] > 0

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def ell(self, cx, cy, rx, ry, fn):
        """fn(dx_norm, dy_norm, x, y) -> Farbname/None, fuer alle Pixel in der Ellipse."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    c = fn(dx, dy, x, y)
                    if c:
                        self.set(x, y, c)

    def outline(self, c, only_below=False):
        """1-px-Kontur um alle opaken Pixel (4er-Nachbarschaft)."""
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if not self.solid(x, y):
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if self.solid(x + dx, y + dy):
                            add.append((x, y))
                            break
        for x, y in add:
            self.set(x, y, c)

    def under(self, fn):
        """Pixel NUR dort setzen, wo noch leer (fuer Schatten/Wasser unter Objekten)."""
        for y in range(self.h):
            for x in range(self.w):
                if not self.solid(x, y):
                    c = fn(x, y)
                    if c:
                        self.set(x, y, c)

    def img(self):
        return Image.fromarray(self.a, 'RGBA')


def strip(frames):
    w, h = frames[0].size
    im = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.paste(f, (i * w, 0))
    return im


def ring_shadow(cv, cx, cy, rx, ry, c='b1'):
    """Dunkler Wasserschatten unter einem Objekt (nur wo leer), leicht nach unten rechts versetzt."""
    def fn(x, y):
        dx, dy = (x + 0.5 - cx - 1.5) / (rx + 1.8), (y + 0.5 - cy - 2) / (ry + 1.8)
        return c if dx * dx + dy * dy <= 1 else None
    cv.under(fn)




def static_noise(cx, cy, seed):
    """Periodisches Wertrauschen 32x32 (0..1), nahtlos kachelbar."""
    import welt_lib as W
    return W.noise_field(cx, cy, 0, 1, seed)[0]


def rot90(im):
    return im.transpose(Image.ROTATE_270)
