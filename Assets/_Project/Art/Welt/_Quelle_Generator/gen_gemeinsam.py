"""GEMEINSAM (Art/Welt/00_Gemeinsam): zonenuebergreifende Orientierungs- und Rastobjekte.

Objekte/  Wegweiser_Holz (32x48), Steinmaennchen (32x32)
Animiert/ Grenzstein_Rune (32x48, 8f, leuchtende Rune), Lagerfeuer_Rast (32x32, 8f)
Aufruf: python gen_gemeinsam.py"""
import math
import sys

import welt_lib as W
from welt_draw import Cv, strip, ring_shadow
from welt_lib import hsh

N = 8


def signpost():
    cv = Cv(32, 48)
    for y in range(8, 44):                                                   # Pfosten
        for x in range(14, 19):
            d = (x - 14) / 4.0
            cv.set(x, y, 'br3' if d < 0.3 else ('br2' if d < 0.75 else 'br1'))
    for (y0, x0, x1, left) in ((10, 3, 24, True), (20, 8, 29, False)):       # zwei Schilder
        for y in range(y0, y0 + 8):
            for x in range(x0, x1 + 1):
                tip = (left and x < x0 + 4 and abs(y - y0 - 3.5) > (x - x0) * 0.9 + 0.5) or ((not left) and x > x1 - 4 and abs(y - y0 - 3.5) > (x1 - x) * 0.9 + 0.5)
                if tip:
                    continue
                c = 'br4' if y == y0 else ('br3' if y < y0 + 6 else 'br2')
                if (x + y) % 7 == 0 and 0 < y - y0 < 7:
                    c = 'br2'
                cv.set(x, y, c)
        for k in range(3):                                                    # Schriftstriche
            xx = x0 + 6 + k * 4
            cv.rect(xx, y0 + 3, xx + 1, y0 + 4, 'br0')
    cv.outline('br0')
    ring_shadow(cv, 16, 44, 8, 2.5, 'g0')
    return cv.img()


def cairn():
    cv = Cv(32, 32)
    for (cx, cy, rx, ry) in ((16, 25, 10, 4.5), (16, 19, 7.5, 3.6), (16, 14, 5, 3), (16, 10, 3, 2.2)):
        cv.ell(cx, cy, rx, ry, lambda dx, dy, x, y: 's4' if (-0.5 * dx - 0.8 * dy) > 0.2 else ('s3' if (-0.5 * dx - 0.8 * dy) > -0.4 else 's2'))
    cv.outline('s0')
    ring_shadow(cv, 16, 25, 10, 4.5, 'g0')
    return cv.img()


def border_stone():
    frames = []
    for t in range(N):
        cv = Cv(32, 48)
        glow = 0.5 + 0.5 * math.sin(2 * math.pi * t / N)
        for y in range(6, 44):                                                # Stein
            f = (y - 6) / 38.0
            half = 7 + int(3 * f) - (2 if y < 12 else 0)
            for x in range(16 - half, 16 + half + 1):
                d = (x - 16) / float(half)
                c = 's4' if d < -0.45 else ('s3' if d < 0.15 else ('s2' if d < 0.6 else 's1'))
                if hsh(x, y // 2, 1, 900) > 0.93:
                    c = 's1'
                cv.set(x, y, c)
        # Rune (Glocke): leuchtet im Takt
        col = 'b5' if glow > 0.75 else ('b4' if glow > 0.35 else 'b3')
        for (x, y) in ((16, 16), (15, 17), (17, 17), (14, 18), (18, 18), (14, 19), (18, 19), (15, 20), (17, 20), (16, 21), (16, 22), (16, 24), (15, 25), (17, 25), (16, 26)):
            cv.set(x, y, col)
        for y in range(14, 29):                                               # Schein
            for x in range(8, 25):
                if not cv.solid(x, y) and hsh(x, y, t % 4, 901) < glow * 0.06:
                    cv.set(x, y, 'b4')
        cv.outline('s0')
        ring_shadow(cv, 16, 43, 12, 3, 'g0')
        frames.append(cv.img())
    return frames


def campfire():
    frames = []
    for t in range(N):
        cv = Cv(32, 32)
        for k in range(9):                                                     # Steinkranz
            a = k * math.pi * 2 / 9
            cv.ell(16 + 11 * math.cos(a), 20 + 6.5 * math.sin(a), 3, 2.2, lambda dx, dy, x, y: 's3' if (-0.5 * dx - 0.8 * dy) > 0 else 's1')
        for (x0, y0, x1, y1) in ((8, 22, 24, 16), (9, 16, 23, 23)):            # gekreuzte Scheite
            n = max(abs(x1 - x0), abs(y1 - y0))
            for i in range(n + 1):
                x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
                cv.set(x, y, 'br3')
                cv.set(x, y + 1, 'br1')
        cv.rect(12, 19, 20, 20, 'red')                                         # Glut
        ph = 2 * math.pi * t / N
        for y in range(3, 20):
            f = (19 - y) / 16.0
            hw = 5.5 * (1 - f ** 1.3) + 0.5
            cxf = 16 + 1.8 * math.sin(ph + f * 4.0) * f
            for x in range(int(cxf - hw - 1), int(cxf + hw + 2)):
                d = abs(x + 0.5 - cxf) / max(hw, 0.4)
                if d <= 1:
                    cv.set(x, y, 'yel' if (d < 0.4 and f < 0.5) else ('or2' if d < 0.7 and f < 0.75 else ('or1' if f < 0.9 else 'red')))
        for k in range(3):                                                     # Funken
            yy = 14 - ((t * 2 + k * 6) % 14)
            if hsh(k, t, 1, 902) > 0.25:
                cv.set(16 + 5 * math.sin(k * 2 + t * 0.7), yy, 'yel')
        cv.outline('br0') if False else None
        frames.append(cv.img())
    return frames


def main():
    od = W.zone_dir('gemeinsam', 'Objekte')
    ad = W.zone_dir('gemeinsam', 'Animiert')
    errs = []
    for n, im in (('Wegweiser_Holz', signpost()), ('Steinmaennchen', cairn())):
        im.save('%s/%s.png' % (od, n))
        errs += W.check_palette(im, n)
    for n, fr in (('Grenzstein_Rune', border_stone()), ('Lagerfeuer_Rast', campfire())):
        im = strip(fr)
        im.save('%s/%s.png' % (ad, n))
        errs += W.check_palette(im, n) + W.check_loop(fr, n)
    if errs:
        print('\n'.join(errs))
        sys.exit(1)
    print('ok Gemeinsam')


if __name__ == '__main__':
    main()
