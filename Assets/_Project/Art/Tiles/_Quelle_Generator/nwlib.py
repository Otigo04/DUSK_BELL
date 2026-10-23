"""Nightward Pixel-Lib: Palette, Sprite-Helfer, Autotile-Engine.
Alle Farben stammen aus Art/Palette.png (40 Farben)."""
import math, os
from PIL import Image

ART = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')).replace('\\', '/')   # Art/ relativ zu diesem Ordner (laeuft auf Mac und Windows)
TILES = ART + '/Tiles'


def H(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# --- Rampen (dunkel -> hell) ---
GREEN = [H(x) for x in ('243b3f', '2f5444', '3f7347', '58903f', '7bac45', 'a4c654', 'cde06a')]
BROWN = [H(x) for x in ('3a2530', '5a3a3f', '7d5646', 'a37a56', 'c9a26a', 'e3c98c')]
STONE = [H(x) for x in ('3d3850', '5a566e', '7a7790', '9e9bb2', 'c4c1d2', 'e4e0ea')]
PURP = [H(x) for x in ('1f1630', '2a1d3b', '3a2a4f', '4b3a63', '5e4c7a')]
BLUE = [H(x) for x in ('23336b', '2f4f8f', '3f72b0', '5b99c4', '8cc4d6', 'cfeef0')]
OUT = H('2a1d3b')
RED, ORANGE, YELLOW, PINK, VIOLET, CREAM, WINE, SAND, AMBER, MAUVE = [
    H(x) for x in ('c04b3f', 'e8863f', 'f6d34a', 'e07a9a', '7a6ad8', 'efe7dd', '8a3550', 'e6d8b8', 'f3a65a', '6b4d8c')]
G_DK, G_MD, G_BASE, G_LT, G_HI, G_HI2 = GREEN[1], GREEN[2], GREEN[3], GREEN[4], GREEN[5], GREEN[6]


def hsh(*a):
    """deterministischer Hash 0..1"""
    n = 2166136261
    for v in a:
        n = ((n ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
        n ^= n >> 13
        n = (n * 1274126177) & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffff) / 65535.0


class Spr:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.p = self.im.load()

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[x, y] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[x, y]
        return (0, 0, 0, 0)

    def solid(self, x, y):
        return self.get(x, y)[3] > 0

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.set(int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)), c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0:
                    self.set(x, y, c)

    def paste(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = other.p[x, y]
                if c[3]:
                    self.set(x + ox, y + oy, c)

    def outline(self, col=OUT, diag=False):
        add = []
        for y in range(-1, self.h + 1):
            for x in range(-1, self.w + 1):
                if self.solid(x, y):
                    continue
                nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                if diag:
                    nb += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
                if any(self.solid(x + a, y + b) for a, b in nb):
                    add.append((x, y))
        for x, y in add:
            self.set(x, y, col)

    def shadow(self, col=(0x2f, 0x54, 0x44, 255), dx=0, dy=1):
        """flacher Bodenschatten unter dem Objekt (nur Pixel die noch leer sind)"""
        pass

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.im.save(path)


def blob(spr, cx, cy, rx, ry, ramp, seed=0, light=(-0.6, -0.8), speck=None, steps=None):
    """beleuchtete Kugel/Klumpen, ramp = Liste dunkel->hell (3-5 Farben)."""
    n = len(ramp)
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            nx = (x + .5 - cx) / rx
            ny = (y + .5 - cy) / ry
            d = nx * nx + ny * ny
            if d > 1.0:
                continue
            z = math.sqrt(max(0.0, 1 - d))
            lam = (nx * light[0] + ny * light[1]) * 0.6 + z * 0.55
            v = lam + (hsh(x, y, seed) - 0.5) * 0.22
            i = int(max(0, min(n - 1, round((v + 0.1) * (n - 1) * 0.95))))
            spr.set(x, y, ramp[i])
            if speck and hsh(x * 3, y * 7, seed + 5) < speck[0]:
                spr.set(x, y, speck[1])


def tile_from(im, col, row):
    return im.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))


def sheet(frames, cols, cw, ch):
    rows = (len(frames) + cols - 1) // cols
    s = Image.new('RGBA', (cols * cw, rows * ch), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, ((i % cols) * cw, (i // cols) * ch))
    return s


def preview(path, files_or_imgs, scale=4, bg=(90, 110, 90, 255), gap=6, maxw=2000):
    ims = []
    for f in files_or_imgs:
        ims.append(Image.open(f).convert('RGBA') if isinstance(f, str) else f)
    x = y = rowh = 0
    pos = []
    for i in ims:
        w, h = i.width * scale, i.height * scale
        if x + w > maxw:
            x = 0
            y += rowh + gap
            rowh = 0
        pos.append((x, y))
        x += w + gap
        rowh = max(rowh, h)
    W = max(p[0] + i.width * scale for p, i in zip(pos, ims))
    Hh = y + rowh
    sh = Image.new('RGBA', (W, Hh), bg)
    for p, i in zip(pos, ims):
        sh.alpha_composite(i.resize((i.width * scale, i.height * scale), Image.NEAREST), p)
    sh.save(path)
    return sh.size


def shade_mask(spr, mask, ramp, seed=0, base=None, clump=2, spk=0.0, spkcol=None, hi_boost=0):
    """Faerbt eine Pixelmenge (set von (x,y)) organisch ein: Licht von oben-links,
    Kantenabdunklung unten/rechts, kleine Blatt-Klumpen als Textur. ramp = dunkel->hell."""
    n = len(ramp)
    base = n // 2 if base is None else base

    def run(x, y, dx, dy, mx=6):
        k = 0
        while (x + dx * (k + 1), y + dy * (k + 1)) in mask and k < mx:
            k += 1
        return k

    for (x, y) in mask:
        up, dn = run(x, y, 0, -1), run(x, y, 0, 1)
        lf, rt = run(x, y, -1, 0), run(x, y, 1, 0)
        v = base
        if up <= 1: v += 2 + hi_boost
        elif up <= 3: v += 1
        if dn <= 1: v -= 2
        elif dn <= 3: v -= 1
        if lf <= 1: v += 1
        if rt <= 1: v -= 1
        r = hsh(x // clump, y // clump, seed)
        if r < 0.18: v -= 1
        elif r > 0.84: v += 1
        if hsh(x, y, seed + 7) < 0.06: v -= 1
        v = max(0, min(n - 1, v))
        spr.set(x, y, ramp[v])
        if spk and hsh(x, y, seed + 13) < spk:
            spr.set(x, y, spkcol)


def noise1(t, seed, k=3):
    """glatter 1D-Wert -1..1"""
    import math as m
    return sum(m.sin(t * (0.5 + i * 0.7) + hsh(seed, i) * 6.28) / (1 + i * .6) for i in range(k)) / 1.8


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def lit(spr, lobes, ramp, seed=0, noise=0.10, light=(-0.55, -0.85), gain=1.0, bias=0.0, dither=True):
    """mehrere Ellipsen (cx,cy,rx,ry) in Reihenfolge hinten->vorne mit eigener Kugel-Beleuchtung.
    Gibt die gefuellte Pixelmenge zurueck."""
    n = len(ramp)
    out = set()
    for (cx, cy, rx, ry) in lobes:
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                nx = (x + .5 - cx) / rx
                ny = (y + .5 - cy) / ry
                d = nx * nx + ny * ny
                if d > 1.0 or not (0 <= x < spr.w and 0 <= y < spr.h):
                    continue
                z = math.sqrt(max(0.0, 1 - d))
                lam = (nx * light[0] + ny * light[1]) * 0.55 + z * 0.62
                v = (lam * gain + bias) + (hsh(x, y, seed) - 0.5) * noise
                f = v * (n - 1)
                if dither:
                    f += (BAYER[y % 4][x % 4] / 16.0 - 0.5) * 0.9
                spr.set(x, y, ramp[int(max(0, min(n - 1, round(f))))])
                out.add((x, y))
    return out


def thick_outline(spr, col=OUT, bottom=True):
    spr.outline(col)
    if bottom:
        add = []
        for y in range(spr.h - 1):
            for x in range(spr.w):
                if spr.get(x, y) == col and not spr.solid(x, y + 1) and spr.solid(x, y - 1) and spr.get(x, y - 1) != col:
                    add.append((x, y + 1))
        for x, y in add:
            spr.set(x, y, col)
