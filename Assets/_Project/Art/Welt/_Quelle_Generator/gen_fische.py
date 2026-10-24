"""FISCHE (Art/Welt/03_Fluss/Tiere): Forelle, Karpfen, Elritzen-Schwarm, springender Fisch + Wasserringe/Spritzer (03_Fluss/Animiert).

Jede Art gibt es in zwei Varianten:
  *_Farbe     sichtbarer Fisch (klares/flaches Wasser, an Land gezogen, Angel-Minispiel)
  *_Schatten  dunkle Silhouette fuer Fische UNTER der Wasseroberflaeche (liegt als Sprite ueber dem Wasser, sieht aus wie unter dem Wasser)
Layout Schwimmen: Zeilen = Blickrichtung S, W, N, E (Unity y-nach-unten), Spalten = 8 Frames Schwanzschlag (Schleife).
Zellgroesse: Forelle/Karpfen 32x32, Schwarm 48x48, Sprung 48x48 (16 Frames, Wasserlinie bei y=34), Ringe 32/48.
Alle Fische sind prozedural (Form als Funktion) und werden fuer jede Richtung/Pose per Rotation abgetastet -> keine Spiegelungsfehler.
Aufruf: python gen_fische.py"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import sys

import numpy as np
from PIL import Image

import welt_lib as W
from welt_lib import H, hsh

F = 8                                    # Frames Schwanzschlag
DIRS = [('S', 90), ('W', 180), ('N', 270), ('E', 0)]

COL = {k: H(v) for k, v in dict(
    ink='1f1630', g0='243b3f', g2='3f7347', g3='58903f', g4='7bac45', br0='3a2530', br2='7d5646', br3='a37a56', br4='c9a26a',
    br5='e3c98c', cream='e6d8b8', or1='e8863f', or2='f3a65a', red='c04b3f', yel='f6d34a', s0='3d3850', s1='5a566e', s2='7a7790',
    s3='9e9bb2', s4='c4c1d2', s5='e4e0ea', b0='23336b', b1='2f4f8f', b2='3f72b0', b3='5b99c4', b4='8cc4d6', b5='cfeef0',
    pk='e07a9a', wine='8a3550').items()}

ART_ = {
    'Forelle': dict(a=8.0, Hh=3.0, fin=4.0, amp=1.5, back='g2', flank='br4', belly='cream', fins='or1', outline='g0', spots=True),
    'Karpfen': dict(a=10.0, Hh=4.4, fin=4.5, amp=1.8, back='br3', flank='or1', belly='or2', fins='red', outline='br0', scales=True),
    'Elritze': dict(a=3.6, Hh=1.7, fin=2.0, amp=0.8, back='s1', flank='s4', belly='s5', fins='s3', outline='s0', stripe=True),
}


def local(sp, u, v, ph):
    """Farbname oder None fuer Fischkoerper am lokalen Punkt (u nach vorn, v quer). ph = Schwanzschlag-Phase."""
    a, Hh, fin, amp = sp['a'], sp['Hh'], sp['fin'], sp['amp']
    s = max(0.0, min(1.0, (a - u) / (2.0 * a)))          # 0 Kopf .. 1 Schwanzende
    vv = v - amp * math.sin(ph - 2.6 * s) * (s ** 1.25) * (1.0 if u > -a else 1.0)
    # Schwanzflosse
    if -a - fin <= u < -a * 0.8:
        f = (-a * 0.8 - u) / (fin + 0.2 * a)             # 0 am Stiel .. 1 Ende
        half = 0.55 + f * Hh * 0.95
        if abs(vv) <= half and not (f > 0.55 and abs(vv) < (f - 0.5) * Hh * 0.9):
            return 'fins'
    if abs(u) > a + 0.01 and u > 0:
        return None
    if u < -a * 0.8 or u > a:
        return None
    t = (u + a) / (2.0 * a)                                # 0 Schwanz .. 1 Kopf
    hh = Hh * (math.sin(math.pi * min(t, 1.0) ** 0.8) ** 0.7)
    hh = max(hh, 0.6) if t > 0.02 else 0.0
    # Rueckenflosse
    if 0.36 <= t <= 0.58 and -hh - 1.6 * sp['Hh'] / 3.0 <= vv < -hh + 0.2 and abs(vv) > hh * 0.8:
        return 'fins'
    if abs(vv) > hh:
        return None
    z = vv / hh if hh else 0
    # Auge
    if 0.80 <= t <= 0.90 and -0.55 <= z <= -0.05 and sp['Hh'] >= 3:
        return 'ink'
    if sp['Hh'] < 3 and 0.78 <= t <= 0.90 and -0.5 <= z <= 0.0:
        return 'ink'
    # Brustflosse
    if 0.64 <= t <= 0.70 and 0.30 <= z <= 0.62 and sp['Hh'] >= 3:
        return 'fins'
    c = 'back' if z < -0.38 else ('belly' if z > 0.42 else 'flank')
    if sp.get('stripe') and -0.15 <= z <= 0.2 and t < 0.75:
        return 'stripe'
    if sp.get('spots') and c != 'belly' and hsh(int(round(u * 1.3)), int(round(vv * 1.3)), 17, 5) > 0.82 and 0.15 < t < 0.8:
        return 'spot'
    if sp.get('scales') and c == 'flank' and (int(round(u)) + int(round(vv))) % 3 == 0 and 0.2 < t < 0.85:
        return 'scale'
    return c


def render(spname, theta_deg, ph, size, cx, cy, shadow=False, clip_y=None, scale=1.0, tint=None):
    sp = ART_[spname]
    th = math.radians(theta_deg)
    ct, st = math.cos(th), math.sin(th)
    grid = [[None] * size for _ in range(size)]
    for Y in range(size):
        for X in range(size):
            if clip_y is not None and Y > clip_y:
                continue
            dx, dy = X + 0.5 - cx, Y + 0.5 - cy
            u = (ct * dx + st * dy) / scale
            v = (-st * dx + ct * dy) / scale
            c = local(sp, u, v, ph)
            if c is not None:
                grid[Y][X] = c
    return grid, sp


def colorize(grid, sp, shadow):
    size = len(grid)
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    px = im.load()

    def rgba(name):
        if shadow:
            return COL['b0'] if name in ('back', 'flank', 'belly', 'stripe', 'spot', 'scale', 'ink') else COL['b1']
        return COL[{'back': sp['back'], 'flank': sp['flank'], 'belly': sp['belly'], 'fins': sp['fins'], 'ink': 'ink',
                    'stripe': 's0', 'spot': 'red', 'scale': 'br5'}[name]]
    for y in range(size):
        for x in range(size):
            if grid[y][x] is not None:
                px[x, y] = rgba(grid[y][x])
    if not shadow:                                        # dunkle Kontur (4er-Nachbarschaft)
        out = COL[sp['outline']]
        for y in range(size):
            for x in range(size):
                if grid[y][x] is None:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < size and 0 <= yy < size and grid[yy][xx] is not None:
                            px[x, y] = out
                            break
    return im


def swim_sheet(spname, shadow, size=32):
    sheet = Image.new('RGBA', (F * size, 4 * size), (0, 0, 0, 0))
    c = size / 2.0
    shift = ART_[spname]['fin'] / 2.0                      # Fisch samt Schwanz mittig in der Zelle
    for r, (dn, deg) in enumerate(DIRS):
        th = math.radians(deg)
        for f in range(F):
            g, sp = render(spname, deg, 2 * math.pi * f / F, size, c + shift * math.cos(th), c + shift * math.sin(th))
            sheet.paste(colorize(g, sp, shadow), (f * size, r * size))
    return sheet


def school_sheet(shadow, size=48, n=6):
    """Elritzen-Schwarm: n Fische schwimmen als lockere Gruppe in dieselbe Richtung, jeder mit eigener Phase und Kreisbahn (Schleife schliesst)."""
    sp = ART_['Elritze']
    sheet = Image.new('RGBA', (F * size, 4 * size), (0, 0, 0, 0))
    base = [(-9, -6), (3, -9), (10, -1), (-4, 1), (6, 8), (-11, 8)][:n]
    for r, (dn, deg) in enumerate(DIRS):
        th = math.radians(deg)
        ct, st = math.cos(th), math.sin(th)
        for f in range(F):
            im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            for k, (bx, by) in enumerate(base):
                ang = 2 * math.pi * f / F + k * 1.1
                ox, oy = bx + 1.6 * math.cos(ang), by + 1.2 * math.sin(ang * 2)           # u/v relativ zur Schwarmrichtung
                px_, py_ = size / 2 + ct * ox - st * oy, size / 2 + st * ox + ct * oy
                jit = deg + 14 * math.sin(ang * 2 + k)
                g, _ = render('Elritze', jit, 2 * math.pi * f / F + k * 0.9, size, px_, py_)
                fi = colorize(g, sp, shadow)
                im.alpha_composite(fi)
            sheet.paste(im, (f * size, r * size))
    return sheet


JUMP_N = 16


def jump_sheet(spname='Forelle', shadow=False, size=48):
    """Springender Fisch: Bogen ueber die Wasserlinie (y=34); unter der Linie wird nichts gezeichnet (Wasser verdeckt)."""
    sp = ART_[spname]
    sheet = Image.new('RGBA', (JUMP_N * size, size), (0, 0, 0, 0))
    wl = 34
    for f in range(JUMP_N):
        u = (f - 2) / 11.0                                   # Sprung ueber Frames 2..13
        if u < 0 or u > 1:
            continue
        x = 8 + 32 * u
        y = wl + 2 - 4 * 25 * u * (1 - u)
        dxdt, dydt = 32.0, -4 * 25 * (1 - 2 * u)
        ang = math.degrees(math.atan2(dydt, dxdt))
        ph = 2 * math.pi * (f % 4) / 4 * 1.0 + 0.8 * math.sin(u * 6)
        g, sp_ = render(spname, ang, ph, size, x, y, clip_y=wl)
        sheet.paste(colorize(g, sp_, shadow), (f * size, 0))
    return sheet


# ---------------------------------------------------------------- Wasserringe / Spritzer
def circle_px(im, cx, cy, r, color, skip=None):
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if abs(d - r) < 0.62:
                if skip and skip(x, y):
                    continue
                px[x, y] = color


def rings_sheet(size, n=8, rmax=None):
    """Konzentrische Wellenringe, die sich ausbreiten und aufloesen (Dither)."""
    rmax = rmax or size / 2 - 1
    sheet = Image.new('RGBA', (n * size, size), (0, 0, 0, 0))
    for f in range(n):
        im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        u = f / float(n)
        for k, off in enumerate((0.0, 0.28)):
            uu = u - off
            if uu < 0:
                continue
            r = 1.5 + (rmax - 1.5) * (uu / (1.0 - 0.28 * (1 if off else 0)))
            if r > rmax:
                continue
            fade = uu / (1.0 - off)
            col = COL['b5'] if fade < 0.35 else (COL['b4'] if fade < 0.7 else COL['b3'])
            thr = max(0.0, (fade - 0.55) * 2.2)
            circle_px(im, size / 2, size / 2, r, col, skip=lambda x, y, thr=thr: hsh(x, y, f, 61) < thr)
        sheet.paste(im, (f * size, 0))
    return sheet


def splash_sheet(size=48, n=8):
    """Sprung-Spritzer: Tropfen fliegen auf und fallen, mit Eintauchring (Wasserlinie y=34)."""
    sheet = Image.new('RGBA', (n * size, size), (0, 0, 0, 0))
    wl = 34
    drops = [(-6, -9, 1), (-3, -13, 1), (0, -15, 2), (3, -12, 1), (6, -8, 1), (9, -5, 1)]
    for f in range(n):
        im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        px = im.load()
        u = f / float(n - 1)
        for (dx, vy, sz) in drops:
            x = 24 + dx * (0.4 + 0.9 * u)
            y = wl + vy * 3.4 * u + 14.0 * u * u * 3.2 * abs(vy) / 15.0 * 1.0
            if y >= wl - 0.5 or u < 0.05:
                continue
            for oy in range(sz):
                for ox in range(sz):
                    xx, yy = int(x) + ox, int(y) + oy
                    if 0 <= xx < size and 0 <= yy < size:
                        px[xx, yy] = COL['b5'] if u < 0.7 else COL['b4']
        rr = 2 + 11 * u
        circle_px(im, 24, wl, rr, COL['b4'] if u > 0.5 else COL['b5'], skip=lambda x, y: y > wl + 3 or hsh(x, y, f, 63) < max(0.0, u - 0.6) * 2)
        sheet.paste(im, (f * size, 0))
    return sheet


def main():
    errs = []
    td = W.zone_dir('fluss', 'Tiere')
    ad = W.zone_dir('fluss', 'Animiert')
    outs = []
    for name in ('Forelle', 'Karpfen'):
        for var, sh in (('Farbe', False), ('Schatten', True)):
            s = swim_sheet(name, sh)
            outs.append(('%s/Fisch_%s_%s.png' % (td, name, var), s))
    for var, sh in (('Farbe', False), ('Schatten', True)):
        outs.append(('%s/Fisch_Elritzenschwarm_%s.png' % (td, var), school_sheet(sh)))
    outs.append(('%s/Fisch_Forelle_Sprung.png' % td, jump_sheet('Forelle')))
    outs.append(('%s/Fisch_Karpfen_Sprung.png' % td, jump_sheet('Karpfen')))
    outs.append(('%s/Wasserring_klein.png' % ad, rings_sheet(32)))
    outs.append(('%s/Wasserring_gross.png' % ad, rings_sheet(48)))
    outs.append(('%s/Sprung_Spritzer.png' % ad, splash_sheet()))
    for p, im in outs:
        im.save(p)
        errs += W.check_palette(im, p.rsplit('/', 1)[1])
        print('ok', p.rsplit('/', 1)[1], im.size)
    if errs:
        print('\n'.join(errs))
        sys.exit(1)


if __name__ == '__main__':
    main()
