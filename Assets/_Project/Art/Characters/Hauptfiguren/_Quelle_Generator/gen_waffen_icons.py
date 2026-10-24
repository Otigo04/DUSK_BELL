"""Item-Icons der Waffen Baseballschlaeger, Brecheisen, Jagdgewehr (32x32, Palette wie die anderen Waffen-Icons).
Aufruf: python gen_waffen_icons.py <Ordner Art/Items/Waffen>"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import os
import sys

from PIL import Image

K = (0x1a, 0x15, 0x26)


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


WOOD_L, WOOD_M, WOOD_D = hx('#b89a72'), hx('#9c7a5a'), hx('#7a5a43')
ST_H, ST_L, ST_M, ST_D = hx('#e8e0f0'), hx('#9a95a0'), hx('#6e6a74'), hx('#4a4550')
TAPE, TAPE_D = hx('#3a4a7a'), hx('#2c3e56')
GUN, GUN_H, GUN_D = hx('#2b2140'), hx('#6e6a74'), hx('#1a1526')


class Icon:
    def __init__(s):
        s.px = {}

    def dot(s, x, y, c):
        s.px[(int(round(x)), int(round(y)))] = c

    def line(s, a, b, w, cols):
        """Dicke Linie a->b. cols = (hell, mittel, dunkel): hell an der oberen Kante, dunkel unten."""
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 3) + 1
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        for i in range(n + 1):
            u = i / float(n)
            ww = w(u) if callable(w) else w
            for k in range(-int(ww), int(ww) + 1):
                if abs(k) > ww / 2.0 + 0.01:
                    continue
                x, y = a[0] + dx * u + nx * k, a[1] + dy * u + ny * k
                edge = k / (ww / 2.0 + 0.001)
                c = cols[0] if edge < -0.45 else (cols[2] if edge > 0.45 else cols[1])
                s.dot(x, y, c)

    def save(s, path):
        im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        out = set()
        for (x, y) in s.px:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + ox, y + oy)
                if q not in s.px:
                    out.add(q)
        for (x, y) in out:
            if 0 <= x < 32 and 0 <= y < 32:
                im.putpixel((x, y), K + (255,))
        for (x, y), c in s.px.items():
            if 0 <= x < 32 and 0 <= y < 32:
                im.putpixel((x, y), c + (255,))
        im.save(path)


def bat():
    i = Icon()
    a, b = (5.0, 26.5), (25.5, 6.0)
    i.line(a, b, lambda u: 2 if u < 0.35 else (3 + 3 * (u - 0.35) / 0.65 if u < 0.85 else 6 - 3 * (u - 0.85) / 0.15 * 0.6), (WOOD_L, WOOD_M, WOOD_D))
    # Griffband und Knauf
    i.line((6.0, 25.5), (10.0, 21.5), 2, (TAPE, TAPE, TAPE_D))
    i.line((3.6, 28.4), (4.6, 27.4), 3, (WOOD_M, WOOD_D, WOOD_D))
    return i


def crowbar():
    i = Icon()
    i.line((6.0, 26.0), (23.0, 9.0), 2, (ST_L, ST_M, ST_D))
    i.line((23.0, 9.0), (26.5, 5.5), 2, (ST_L, ST_M, ST_D))
    i.line((26.5, 5.5), (28.5, 6.5), 2, (ST_L, ST_M, ST_D))    # Haken
    i.line((28.5, 6.5), (29.0, 9.5), 2, (ST_M, ST_D, ST_D))
    i.line((4.0, 28.0), (6.5, 25.5), 2, (ST_L, ST_M, ST_D))     # Klaue unten
    i.line((3.0, 26.0), (5.0, 28.0), 2, (ST_M, ST_D, ST_D))
    for t in (0.35, 0.5):                                       # Glanz
        i.dot(6 + 17 * t, 26 - 17 * t - 1, ST_H)
    return i


def rifle():
    i = Icon()
    i.line((3.0, 28.0), (13.0, 20.0), lambda u: 4.4 - 1.6 * u, (WOOD_L, WOOD_M, WOOD_D))     # Schaft
    i.line((2.0, 29.2), (4.5, 27.2), 4, (GUN_H, GUN, GUN_D))                                  # Kolbenkappe
    i.line((13.0, 20.0), (17.5, 15.5), 3, (GUN_H, GUN, GUN_D))                                # Verschluss
    i.line((17.5, 15.5), (29.0, 4.0), 2, (GUN_H, GUN, GUN_D))                                 # Lauf
    i.line((18.5, 17.5), (25.0, 11.0), 2, (WOOD_L, WOOD_M, WOOD_D))                           # Vorderschaft
    i.line((13.5, 23.0), (16.0, 21.0), 2, (GUN, GUN, GUN_D))                                  # Abzugsbuegel
    i.dot(29.5, 3.0, GUN_H)                                                                   # Korn
    i.dot(16.0, 13.5, GUN_H)                                                                  # Kimme
    return i


if __name__ == '__main__':
    out = sys.argv[1]
    for name, fn in (('Item_Baseballschlaeger.png', bat), ('Item_Brecheisen.png', crowbar), ('Item_Jagdgewehr.png', rifle)):
        fn().save(os.path.join(out, name))
        print('ok', name)
