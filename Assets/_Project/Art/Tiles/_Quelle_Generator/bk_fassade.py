"""Haus-Baukasten AUSSEN: Overlays fuer Fassade und Dach (transparent, passen auf jedes Wand-/Dachmaterial).
Jedes Teil ist ein ganzes Objekt (keine halben Tueren moeglich). Ankerzelle = links unten."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
from bk_lib import *

SHUT = {'blau': (BLUE_D, BLUE_L, NB_M), 'rot': (RED_D, ROSE, SK_S), 'gruen': (FOR_M, GRASS, FOR_D),
        'holz': (WOOD_M, WOOD_L, WOOD_D)}
DOOR = {'holz': (WOOD_M, WOOD_L, WOOD_D), 'rot': (RED_D, ROSE, SK_S), 'blau': (BLUE_D, BLUE_L, NB_M),
        'gruen': (FOR_M, GRASS, FOR_D), 'dunkel': (WOOD_D, WOOD_M, EARTH)}


# ====================================================================== Glas
def glass(s, x0, y0, x1, y1, lit, f=0, seed=0):
    """Scheibe. lit: warmes Licht (oben gelb, unten orange), sonst Nachtglas mit Mondreflex."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if lit:
                t = (y - y0) / max(1, y1 - y0)
                c = YEL if t < 0.55 else ORA
                if f and hsh(x, y, seed + f) < 0.10 and t > 0.4:
                    c = YEL if c == ORA else ORA
            else:
                c = NB_M if (y - y0) < (y1 - y0) // 2 else NB_D
            s.set(x, y, c)
    if lit:
        s.set(x0, y0, CREAM)
        s.set(x0 + 1, y0, CREAM)
        s.set(x0, y0 + 1, CREAM)
    else:
        for i in range(3):
            s.set(x1 - 1 - i, y0 + 1 + i, NB_L)
        s.set(x1 - 1, y0 + 1, MOON)


def window(state='lit', shut='blau', f=0):
    """32x32. state: lit | dunkel | zu (Laeden geschlossen, Licht in den Ritzen) | zu_dunkel"""
    s = Spr(32, 32)
    fx0, fx1, fy0, fy1 = 8, 23, 4, 25
    if shut and state in ('lit', 'dunkel'):
        b, hi, lo = SHUT[shut]
        for x0 in (2, 24):
            box(s, x0, 3, x0 + 5, 26, b, hi=hi, lo=lo)
            for y in range(6, 25, 3):
                hline(s, x0 + 1, x0 + 4, y, lo)
            s.set(x0 + (5 if x0 == 2 else 0), 7, ST_D)
            s.set(x0 + (5 if x0 == 2 else 0), 22, ST_D)
    # Rahmen
    box(s, fx0 - 1, fy0 - 1, fx1 + 1, fy1 + 1, WOOD_L, hi=SAND, lo=WOOD_M)
    if state in ('lit', 'dunkel'):
        lit = state == 'lit'
        glass(s, fx0 + 1, fy0 + 1, fx1 - 1, fy1 - 1, lit, f, 3)
        vline(s, 15, fy0 + 1, fy1 - 1, WOOD_M)
        vline(s, 16, fy0 + 1, fy1 - 1, WOOD_D)
        hline(s, fx0 + 1, fx1 - 1, 14, WOOD_M)
        hline(s, fx0 + 1, fx1 - 1, 15, WOOD_D)
        if lit:
            # Gardine oben (Stoff)
            for x in range(fx0 + 1, fx1):
                if (x + 1) % 3 and x not in (15, 16):
                    s.set(x, fy0 + 1, CREAM)
            s.set(fx0 + 1, fy0 + 2, CREAM)
            s.set(fx1 - 1, fy0 + 2, CREAM)
    else:
        b, hi, lo = SHUT[shut or 'holz']
        for x0, x1 in ((fx0, 15), (16, fx1)):
            box(s, x0, fy0, x1, fy1, b, hi=hi, lo=lo)
            for y in range(fy0 + 3, fy1 - 1, 3):
                hline(s, x0 + 1, x1 - 1, y, lo)
                if state == 'zu':
                    hline(s, x0 + 2, x1 - 2, y, YEL if (y // 3) % 2 else ORA)
        s.set(15, 15, ST_L)
        s.set(16, 15, ST_D)
    # Fensterbank
    box(s, fx0 - 3, fy1 + 1, fx1 + 3, fy1 + 4, ST_L, hi=MOON, lo=ST_M)
    return s


def window_round(lit, f=0):
    s = Spr(32, 32)
    s.ellipse(16, 15, 11, 11, OL1)
    s.ellipse(16, 15, 10, 10, WOOD_L)
    s.ellipse(16, 15, 8, 8, OL1)
    tmp = Spr(32, 32)
    glass(tmp, 0, 7, 31, 23, lit, f, 5)
    for y in range(32):
        for x in range(32):
            if ((x + .5 - 16) ** 2 + (y + .5 - 15) ** 2) <= 7.3 ** 2:
                s.set(x, y, tmp.get(x, y))
    vline(s, 16, 7, 23, WOOD_D)
    hline(s, 8, 24, 15, WOOD_D)
    for a in range(0, 360, 45):
        x = int(round(16 + 10 * math.cos(math.radians(a))))
        y = int(round(15 + 10 * math.sin(math.radians(a))))
        s.set(x, y, WOOD_M)
    s.set(10, 8, SAND)
    s.set(11, 7, SAND)
    return s


def window_arch(kind, f=0):
    """32x64 Rundbogenfenster (Kapelle). kind: lit | dunkel | bunt"""
    s = Spr(32, 64)
    x0, x1, ytop, ybot = 6, 25, 6, 58
    cx = 15.5

    def inside(x, y, pad):
        if y < ytop + 10:
            r = (x1 - x0) / 2 - pad
            return (x + .5 - (cx + .5)) ** 2 + ((y + .5 - (ytop + 10)) * 1.0) ** 2 <= r * r and y >= ytop + pad
        return x0 + pad <= x <= x1 - pad and y <= ybot - pad
    for y in range(64):
        for x in range(32):
            if inside(x, y, 0):
                s.set(x, y, OL1)
            if inside(x, y, 1):
                s.set(x, y, ST_L if x < 16 else ST_M)
            if inside(x, y, 3):
                s.set(x, y, OL1)
            if inside(x, y, 4):
                if kind == 'bunt':
                    cell = (x // 4 + (y // 5) * 3 + f * 0) % 5
                    c = [ROSE, BLUE_L, YEL, LEAF, ORA][cell]
                    if (x % 4 == 0 or y % 5 == 0):
                        c = OL2
                    if f and hsh(x // 4, y // 5, f) < 0.2:
                        c = lt(c) if c not in (YEL, CREAM) else CREAM
                    s.set(x, y, c)
                else:
                    t = (y - ytop) / (ybot - ytop)
                    lit = kind == 'lit'
                    c = (YEL if t < 0.5 else ORA) if lit else (NB_M if t < 0.5 else NB_D)
                    if (x % 5 == 1 or y % 6 == 2):
                        c = OL2 if not lit else GLOW
                    s.set(x, y, c)
    box(s, 3, ybot + 1, 28, ybot + 4, ST_L, hi=MOON, lo=ST_M)
    return s


def boarded():
    s = window('dunkel', None)
    for y0, sl in ((7, 1), (14, -1), (20, 1)):
        for x in range(5, 27):
            y = y0 + (x - 16) * sl // 6
            for k, c in enumerate((OL1, WOOD_L, WOOD_M, WOOD_D, OL1)):
                s.set(x, y + k, c)
        s.set(7, y0 + 2 - sl * 2, ST_L)
        s.set(24, y0 + 2 + sl * 2, ST_L)
    return s


def stable_window():
    s = Spr(32, 32)
    box(s, 6, 6, 25, 22, WOOD_M, hi=WOOD_L, lo=WOOD_D)
    s.rect(8, 8, 23, 20, OL2)
    s.rect(8, 8, 23, 9, OL1)
    for x in (11, 15, 19):
        vline(s, x, 8, 20, WOOD_L)
        vline(s, x + 1, 8, 20, WOOD_D)
    # Heu schaut heraus
    for x in range(8, 24):
        if hsh(x, 1, 3) < 0.6:
            s.set(x, 20, SAND)
        if hsh(x, 2, 3) < 0.3:
            s.set(x, 19, WOOD_L)
    box(s, 4, 23, 27, 25, WOOD_L, hi=SAND, lo=WOOD_M)
    return s


def shop_window(goods, f=0):
    """64x32 Schaufenster, warm beleuchtet. goods: brot | waren | apotheke | stoff | buecher"""
    s = Spr(64, 32)
    box(s, 2, 2, 61, 27, WOOD_M, hi=WOOD_L, lo=WOOD_D)
    glass(s, 5, 5, 58, 22, True, f, 11)
    for x in (22, 41):
        vline(s, x, 5, 22, WOOD_D)
        vline(s, x + 1, 5, 22, WOOD_M)
    hline(s, 5, 58, 9, GLOW)
    # Auslage-Brett
    hline(s, 5, 58, 21, WOOD_D)
    hline(s, 5, 58, 22, EARTH)
    for i, x in enumerate(range(7, 57, 6)):
        if x in range(20, 26) or x in range(39, 45):
            continue
        if goods == 'brot':
            s.rect(x, 18, x + 3, 20, WOOD_M)
            hline(s, x, x + 3, 18, WOOD_L)
            s.set(x + 1, 18, SAND)
            if i % 2:
                s.rect(x + 1, 15, x + 3, 17, WOOD_L)
                s.set(x + 2, 15, SAND)
        elif goods == 'waren':
            c = [RED_D, BLUE_D, FOR_M, WOOD_L][i % 4]
            s.rect(x, 15, x + 3, 20, c)
            hline(s, x, x + 3, 15, lt(c))
            hline(s, x, x + 3, 17, CREAM)
        elif goods == 'apotheke':
            c = [FOR_M, BLUE_D, RED_D][i % 3]
            s.rect(x + 1, 13, x + 2, 14, OL2)
            s.rect(x, 15, x + 3, 20, c)
            s.set(x, 16, lt(c))
            hline(s, x, x + 3, 18, CREAM)
        elif goods == 'stoff':
            c = [ROSE, BLUE_L, LEAF, SAND, RED_D][i % 5]
            s.rect(x, 12, x + 4, 20, c)
            vline(s, x + 4, 12, 20, dk(c))
            vline(s, x, 12, 20, lt(c))
        elif goods == 'buecher':
            for k in range(4):
                c = [RED_D, NB_L, FOR_M, WOOD_D][(i + k) % 4]
                vline(s, x + k, 14 + (k % 2), 20, c)
    box(s, 0, 27, 63, 30, ST_L, hi=MOON, lo=ST_M)
    return s


# ====================================================================== Tueren
def _door_leaf(s, x0, y0, x1, y1, col, arch=False):
    b, hi, lo = col
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u = (x - x0) % 5
            c = b
            if u == 0:
                c = lo
            elif u == 1:
                c = hi if hsh(x, y, 4) < 0.6 else b
            s.set(x, y, c)
    vline(s, x0, y0, y1, hi)
    vline(s, x1, y0, y1, lo)


def door(color='holz', kind='zu', f=0):
    """32x64. kind: zu | oberlicht | offen | offen_dunkel | stall"""
    s = Spr(32, 64)
    col = DOOR[color]
    # Zarge (Stein)
    box(s, 3, 9, 28, 63, ST_M, hi=ST_L, lo=ST_D)
    hline(s, 2, 29, 9, OL1)
    s.rect(3, 10, 28, 12, ST_L)
    hline(s, 3, 28, 12, ST_M)
    hline(s, 2, 29, 9, OL1)
    x0, x1, y0, y1 = 6, 25, 14, 63
    s.rect(x0 - 1, y0 - 1, x1 + 1, y1, OL1)
    if kind in ('offen', 'offen_dunkel'):
        lit = kind == 'offen'
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t = (y - y0) / (y1 - y0)
                if lit:
                    c = GLOW if t < 0.25 else (ORA if t < 0.7 else YEL)
                    if y > y1 - 10:
                        c = YEL if (x + y) % 2 else ORA
                else:
                    c = OL2 if t < 0.6 else NB_D
                s.set(x, y, c)
        # Tuerblatt nach innen geklappt (schmal links)
        for y in range(y0, y1 + 1):
            for k, c in enumerate((col[1], col[0], col[2])):
                s.set(x0 + k, y, c)
        vline(s, x0 + 3, y0, y1, OL1)
        if lit:
            for y in range(y0 + 4, y1 - 4, 5):
                s.set(x0 + 9 + (y % 3), y, CREAM)
        return s
    _door_leaf(s, x0, y0, x1, y1, col)
    if kind == 'oberlicht':
        s.rect(x0 + 2, y0 + 2, x1 - 2, y0 + 9, OL1)
        glass(s, x0 + 3, y0 + 3, x1 - 3, y0 + 8, True, f, 21)
        vline(s, 15, y0 + 3, y0 + 8, col[2])
        vline(s, 16, y0 + 3, y0 + 8, col[0])
    if kind == 'stall':
        # obere Haelfte offen (dunkel), untere zu
        s.rect(x0, y0, x1, 37, OL2)
        s.rect(x0, y0, x1, y0 + 1, OL1)
        hline(s, x0 - 1, x1 + 1, 38, OL1)
        hline(s, x0, x1, 39, col[1])
        for x in range(x0 + 2, x1 - 1):
            s.set(x, 36, NB_D)
    # Beschlaege
    for yb in ((y0 + 6, y1 - 8) if kind != 'stall' else (44, y1 - 8)):
        hline(s, x0 + 1, x1 - 6, yb, OL2)
        hline(s, x0 + 1, x1 - 6, yb + 1, ST_D)
        s.set(x0 + 2, yb, ST_L)
    # Klinke
    s.set(x1 - 3, 41, OL1)
    s.set(x1 - 3, 40, YEL)
    s.set(x1 - 4, 41, ST_L)
    s.set(x1 - 2, 41, ST_D)
    return s


def door_double_shop(f=0):
    """64x64 Ladentuer: zwei Fluegel mit Glas, warm beleuchtet."""
    s = Spr(64, 64)
    box(s, 4, 6, 59, 63, ST_M, hi=ST_L, lo=ST_D)
    s.rect(5, 7, 58, 10, ST_L)
    x0, x1, y0 = 8, 55, 13
    s.rect(x0 - 1, y0 - 1, x1 + 1, 63, OL1)
    # Oberlicht
    glass(s, x0, y0, x1, y0 + 6, True, f, 31)
    for x in range(x0 + 6, x1, 8):
        vline(s, x, y0, y0 + 6, WOOD_D)
    hline(s, x0, x1, y0 + 7, OL1)
    for lx0, lx1 in ((x0, 31), (32, x1)):
        _door_leaf(s, lx0, y0 + 8, lx1, 63, DOOR['gruen'])
        s.rect(lx0 + 3, y0 + 11, lx1 - 3, y0 + 30, OL1)
        glass(s, lx0 + 4, y0 + 12, lx1 - 4, y0 + 29, True, f, 33 + lx0)
        vline(s, (lx0 + lx1) // 2, y0 + 12, y0 + 29, FOR_D)
        box(s, lx0 + 3, y0 + 34, lx1 - 3, 58, FOR_M, hi=GRASS, lo=FOR_D)
    vline(s, 31, y0 + 8, 63, OL1)
    s.set(29, 44, YEL)
    s.set(34, 44, YEL)
    return s


def barn_gate():
    s = Spr(64, 64)
    box(s, 2, 4, 61, 63, WOOD_D, hi=WOOD_M, lo=EARTH)
    for lx0, lx1 in ((5, 31), (32, 58)):
        _door_leaf(s, lx0, 7, lx1, 63, DOOR['rot'])
        # Rahmen + Andreaskreuz
        for (ax, ay, bx, by) in ((lx0, 8, lx1, 62), (lx1, 8, lx0, 62)):
            n = max(abs(bx - ax), abs(by - ay))
            for i in range(n + 1):
                x = ax + (bx - ax) * i // n
                y = ay + (by - ay) * i // n
                s.set(x, y, MOON)
                s.set(x + 1, y, ST_L)
                s.set(x - 1, y, SK_S)
        for y in (7, 8, 35, 36, 61, 62):
            hline(s, lx0, lx1, y, MOON if y in (7, 35, 61) else ST_L)
        vline(s, lx0, 7, 63, MOON)
        vline(s, lx1, 7, 63, ST_M)
    vline(s, 31, 7, 63, OL1)
    s.rect(29, 34, 34, 37, OL1)
    s.rect(30, 35, 33, 36, ST_D)
    return s


def chapel_portal():
    s = Spr(64, 64)
    cx, top = 32, 4

    def r_at(y, rad):
        if y >= top + rad:
            return rad
        dy = top + rad - y
        return math.sqrt(max(0, rad * rad - dy * dy))
    for y in range(top, 64):
        for x in range(64):
            d = abs(x + .5 - cx)
            if d <= r_at(y, 28):
                s.set(x, y, OL1)
            if d <= r_at(y, 27) and y > top:
                # Bogensteine
                ring = r_at(y, 27) - d < 5 or y < top + 6
                c = ST_L if x < cx else ST_M
                if ring and ((int(math.atan2(y - top - 27, x - cx) * 6)) % 2):
                    c = ST_M if x < cx else ST_D
                s.set(x, y, c)
            if d <= r_at(y, 21) and y > top + 6:
                s.set(x, y, OL1)
            if d <= r_at(y, 20) and y > top + 7:
                u = int(x - cx + 40) % 5
                c = [WOOD_D, WOOD_L, WOOD_M, WOOD_M, WOOD_M][u]
                s.set(x, y, c)
    vline(s, cx - 1, top + 8, 63, OL1)
    vline(s, cx, top + 8, 63, EARTH)
    for yb in (30, 50):
        hline(s, cx - 19, cx + 18, yb, OL2)
        hline(s, cx - 19, cx + 18, yb + 1, ST_D)
    for x in (cx - 4, cx + 3):
        s.rect(x, 39, x + 1, 42, OL1)
        s.set(x, 40, YEL)
    return s


def steps(kind='stein', wide=False):
    w = 64 if wide else 32
    s = Spr(w, 32)
    c = (ST_L, ST_M, ST_D) if kind == 'stein' else (WOOD_L, WOOD_M, WOOD_D)
    box(s, 1, 0, w - 2, 7, c[0], hi=lt(c[0]), lo=c[1])
    box(s, 0, 7, w - 1, 14, c[1], hi=c[0], lo=c[2])
    for x in range(4, w - 4, 9 if kind == 'stein' else 6):
        s.set(x, 4, c[1])
        s.set(x + 2, 11, c[2])
    hline(s, 0, w - 1, 15, OL2)
    return s


def awning(color, part):
    """Vordach, part: L | M | R | E (einzeln). 32x32, Dach oben, darunter frei."""
    s = Spr(32, 32)
    for y in range(0, 13):
        for x in range(32):
            if color == 'rot':
                c = RED_D if (x // 4) % 2 == 0 else CREAM
                if y < 3:
                    c = dk(c) if c == CREAM else SK_S
            else:
                c = [WOOD_L, WOOD_M, WOOD_M, WOOD_D][(x + y // 4) % 4 if False else x % 4]
                if y % 4 == 0:
                    c = WOOD_D
            if y >= 10:
                c = dk(c)
            s.set(x, y, c)
    # Volant / Kante
    for x in range(32):
        yb = 13 + (1 if (color == 'rot' and (x % 8) in (3, 4)) else 0)
        for y in range(13, yb + 1):
            s.set(x, y, RED_D if color == 'rot' else WOOD_D)
        s.set(x, yb + 1, OL1)
    hline(s, 0, 31, 0, OL1)
    if part in ('L', 'E'):
        vline(s, 0, 0, 14, OL1)
        _bracket(s, 2, 14, 1)
    if part in ('R', 'E'):
        vline(s, 31, 0, 14, OL1)
        _bracket(s, 29, 14, -1)
    return s


def _bracket(s, x, y, d):
    for i in range(7):
        s.set(x + (i if d > 0 else -i) * 0, y + i, OL1)
        s.set(x + (i if d > 0 else -i) // 2 + d, y + i, WOOD_D)
    for i in range(5):
        s.set(x + d * i, y + 6 - i, WOOD_M)


def flower_box(c1, c2):
    s = Spr(32, 32)
    for x in range(5, 27):
        h = 2 + int(hsh(x, 1, ord(str(c1[0])[0])) * 3)
        for y in range(6 - h, 6):
            s.set(x, y, FOR_M if (x + y) % 3 else GRASS)
        if hsh(x, 3, 7) < 0.45:
            s.set(x, 6 - h - 1, c1 if hsh(x, 4, 7) < 0.6 else c2)
            s.set(x, 6 - h, c1 if hsh(x, 5, 7) < 0.5 else (CREAM if c1 != CREAM else YEL))
    box(s, 4, 6, 27, 12, WOOD_M, hi=WOOD_L, lo=WOOD_D)
    hline(s, 5, 26, 9, WOOD_D)
    s.set(6, 13, OL1)
    s.set(25, 13, OL1)
    return s


def wall_lantern(f):
    s = Spr(32, 32)
    # Arm von links
    hline(s, 1, 14, 6, OL1)
    hline(s, 1, 13, 7, ST_D)
    vline(s, 1, 4, 12, OL1)
    for i in range(5):
        s.set(2 + i, 12 - i, ST_D)
    # Laterne
    vline(s, 14, 7, 9, OL1)
    s.rect(10, 10, 18, 11, OL1)
    s.rect(11, 9, 17, 9, OL1)
    s.rect(10, 12, 18, 22, OL1)
    s.rect(11, 13, 17, 21, YEL)
    vline(s, 14, 13, 21, ST_D)
    for y in (13, 14):
        hline(s, 11, 17, y, ORA)
    s.rect(9, 22, 19, 23, OL1)
    hline(s, 10, 18, 22, ST_D)
    s.set(14, 24, OL1)
    # Flamme
    hh = [4, 5, 4, 3][f % 4]
    for i in range(hh):
        s.set(13 + (1 if i < hh - 1 else [0, 1, 1, 0][f % 4]), 20 - i, CREAM if i in (1, 2) else ORA if i == 0 else YEL)
    s.set(15, 19, CREAM if f % 2 else YEL)
    s.set(11, 13, CREAM)
    return s


SIGN_ICONS = ['baecker', 'schmied', 'apotheke', 'laden', 'schneider', 'fischer', 'buch', 'kapelle', 'arzt', 'stube']


def _icon(s, kind, ox, oy):
    """Symbol auf 12x10 Feld ab (ox,oy)."""
    P = lambda pts, c: [s.set(ox + x, oy + y, c) for x, y in pts]
    if kind == 'baecker':  # Brezel
        for a in range(0, 360, 12):
            for (cx, cy) in ((3.5, 4), (8.5, 4)):
                x = cx + 3 * math.cos(math.radians(a))
                y = cy + 3 * math.sin(math.radians(a))
                s.set(ox + int(round(x)), oy + int(round(y)), WOOD_L)
        P([(6, 7), (5, 8), (7, 8), (4, 9), (8, 9)], WOOD_L)
        P([(3, 2), (8, 2)], SAND)
    elif kind == 'schmied':  # Amboss
        s.rect(ox + 1, oy + 2, ox + 10, oy + 4, ST_L)
        s.rect(ox + 4, oy + 5, ox + 7, oy + 7, ST_M)
        s.rect(ox + 2, oy + 8, ox + 9, oy + 9, ST_M)
        P([(0, 2), (0, 3)], ST_L)
        hline(s, ox + 1, ox + 10, oy + 2, MOON)
    elif kind == 'apotheke':  # Moerser + Kreuz
        s.rect(ox + 2, oy + 5, ox + 9, oy + 8, ST_L)
        hline(s, ox + 3, ox + 8, oy + 9, ST_M)
        hline(s, ox + 2, ox + 9, oy + 5, MOON)
        P([(8, 1), (7, 2), (6, 3), (5, 4)], WOOD_L)
        P([(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)], LEAF)
    elif kind == 'laden':  # Sack + Waage
        s.rect(ox + 3, oy + 3, ox + 8, oy + 9, SAND)
        hline(s, ox + 4, ox + 7, oy + 2, WOOD_L)
        P([(5, 1), (6, 1)], WOOD_M)
        P([(5, 5), (6, 6), (5, 7)], WOOD_M)
    elif kind == 'schneider':  # Schere
        for (cx, cy) in ((3, 7), (8, 7)):
            s.ellipse(ox + cx, oy + cy, 2, 2, ST_L)
            s.set(ox + cx, oy + cy, OL2 if False else s.get(ox + cx, oy + cy))
        P([(3, 7), (8, 7)], RED_D)
        for i in range(6):
            s.set(ox + 3 + i, oy + 5 - i * 0 - i // 1 + 0, MOON) if False else None
        P([(4, 5), (5, 4), (6, 3), (7, 2), (8, 1), (7, 5), (6, 4), (5, 3), (4, 2), (3, 1)], MOON)
    elif kind == 'fischer':
        s.ellipse(ox + 5, oy + 5, 4.5, 2.5, BLUE_L)
        P([(9, 3), (10, 2), (9, 5), (10, 6), (9, 4), (10, 4), (11, 3), (11, 5)], BLUE_L)
        hline(s, ox + 2, ox + 7, oy + 4, MOON)
        P([(2, 5)], OL1)
    elif kind == 'buch':
        s.rect(ox + 1, oy + 2, ox + 5, oy + 8, RED_D)
        s.rect(ox + 6, oy + 2, ox + 10, oy + 8, RED_D)
        vline(s, ox + 5, oy + 2, oy + 9, OL2)
        for y in range(oy + 3, oy + 8, 2):
            hline(s, ox + 2, ox + 4, y, CREAM)
            hline(s, ox + 7, ox + 9, y, CREAM)
    elif kind == 'kapelle':  # Kerze
        s.rect(ox + 4, oy + 4, ox + 7, oy + 9, CREAM)
        vline(s, ox + 7, oy + 4, oy + 9, SAND)
        P([(5, 1), (5, 2), (6, 2), (5, 3)], YEL)
        P([(5, 2)], CREAM)
    elif kind == 'arzt':  # Flasche
        s.rect(ox + 4, oy + 0, ox + 6, oy + 2, WOOD_L)
        s.rect(ox + 2, oy + 3, ox + 8, oy + 9, FOR_M)
        hline(s, ox + 3, ox + 7, oy + 6, CREAM)
        P([(3, 4), (3, 5)], GRASS_L)
    elif kind == 'stube':  # Krug
        s.rect(ox + 2, oy + 2, ox + 7, oy + 9, WOOD_L)
        hline(s, ox + 2, ox + 7, oy + 2, CREAM)
        hline(s, ox + 2, ox + 7, oy + 3, CREAM)
        P([(8, 4), (9, 4), (9, 5), (9, 6), (9, 7), (8, 7)], WOOD_L)
        hline(s, ox + 3, ox + 6, oy + 6, WOOD_M)


def hanging_sign(kind, f):
    s = Spr(32, 32)
    # Wandhalter + Ausleger
    s.rect(0, 1, 2, 6, OL1)
    s.rect(1, 2, 1, 5, ST_D)
    hline(s, 2, 28, 3, OL1)
    hline(s, 2, 27, 4, ST_D)
    s.rect(27, 2, 29, 5, OL1)
    for i in range(6):
        s.set(3 + i, 10 - i, ST_D)
    sw = [0, 1, 0, -1][f % 4]
    # Ketten
    for x in (9, 22):
        for y in range(5, 9):
            s.set(x + (sw if y > 6 else 0), y, ST_M if y % 2 else ST_D)
    bx0 = 5 + sw
    box(s, bx0, 9, bx0 + 21, 27, WOOD_M, hi=WOOD_L, lo=WOOD_D)
    s.rect(bx0 + 2, 11, bx0 + 19, 25, WOOD_D)
    s.rect(bx0 + 3, 12, bx0 + 18, 24, EARTH)
    _icon(s, kind, bx0 + 5, 13)
    return s


def downpipe(part):
    s = Spr(32, 32)
    x0 = 25
    if part == 'oben':
        hline(s, 18, 31, 0, OL1)
        s.rect(18, 1, 31, 3, ST_M)
        hline(s, 18, 31, 1, ST_L)
        hline(s, 18, 31, 4, OL1)
    y0 = 4 if part == 'oben' else 0
    y1 = 26 if part == 'unten' else 31
    for y in range(y0, y1 + 1):
        for k, c in enumerate((OL1, ST_L, ST_M, ST_D, OL1)):
            s.set(x0 + k, y, c)
    for y in range(y0 + 6, y1, 12):
        hline(s, x0 - 1, x0 + 5, y, OL1)
        hline(s, x0, x0 + 4, y + 1, ST_D)
    if part == 'unten':
        for i, (dx, dy) in enumerate(((0, 27), (-1, 28), (-2, 29), (-3, 29))):
            pass
        s.rect(x0 - 3, 26, x0 + 4, 28, ST_M)
        hline(s, x0 - 3, x0 + 4, 26, ST_L)
        hline(s, x0 - 4, x0 + 4, 29, OL1)
        vline(s, x0 - 4, 26, 28, OL1)
        s.set(x0 - 3, 30, NB_L)
    return s


def ivy(h, seed):
    s = Spr(32, h)
    import random
    rnd = random.Random(seed)
    stems = []
    for k in range(3):
        x = rnd.randint(4, 27)
        for y in range(h - 1, int(h * rnd.uniform(0.05, 0.4)), -1):
            x += rnd.choice((-1, 0, 0, 1)) if y % 3 == 0 else 0
            x = max(2, min(29, x))
            s.set(x, y, WOOD_D)
            stems.append((x, y))
    for (x, y) in stems[::2]:
        if rnd.random() < 0.55:
            dx = rnd.choice((-2, -1, 1, 2))
            for (a, b, c) in ((0, 0, FOR_M), (1, 0, GRASS), (0, -1, GRASS), (1, -1, GRASS_L), (-1, 0, FOR_D), (0, 1, FOR_D)):
                xx, yy = x + dx + a, y + b
                if 0 <= xx < 32 and 0 <= yy < h:
                    s.set(xx, yy, c)
    return s


def talisman_door(f):
    """Haus-Talisman ueber der Tuer: Kristall an Schnur, pulsiert ruhig (6 Frames)."""
    s = Spr(32, 32)
    hline(s, 9, 22, 2, OL1)
    s.set(10, 3, WOOD_D)
    s.set(21, 3, WOOD_D)
    for i in range(6):
        s.set(11 + i, 3 + i // 2, WOOD_M)
        s.set(20 - i, 3 + i // 2, WOOD_M)
    pts = [(16, 7), (15, 8), (16, 8), (17, 8)]
    lvl = [0, 1, 2, 2, 1, 0][f % 6]
    # Kristall
    shape = []
    for y in range(9, 22):
        w = min(y - 8, 21 - y + 1, 4)
        for x in range(16 - w, 16 + w):
            shape.append((x, y))
    for (x, y) in shape:
        c = TAL if x < 16 else TAL_D
        if x == 16 - 1 and y < 15:
            c = TAL_H
        s.set(x, y, c)
    outline_obj(s)
    if lvl >= 1:
        s.set(14, 12, TAL_H)
        s.set(15, 11, TAL_H)
    if lvl >= 2:
        for (x, y) in ((12, 15), (19, 15), (16, 23), (16, 6)):
            s.set(x, y, TAL_H if lvl == 2 else TAL)
    # Glitzer-Funken
    sp = [(11, 10), (21, 12), (12, 19), (20, 19), (16, 25), (10, 15)]
    x, y = sp[f % 6]
    s.set(x, y, TAL_H)
    return s


def rain_barrel():
    s = Spr(32, 32)
    for y in range(10, 30):
        w = 9 if y in (10, 29) else 10
        for x in range(16 - w, 16 + w):
            u = (x - 6) % 4
            c = [WOOD_L, WOOD_M, WOOD_M, WOOD_D][u]
            if x > 21:
                c = dk(c)
            s.set(x, y, c)
    for y in (13, 25):
        hline(s, 6, 25, y, ST_D)
        hline(s, 6, 25, y + 1, OL2)
    s.ellipse(16, 10, 9, 2.6, WOOD_D)
    s.ellipse(16, 10, 7.6, 1.8, NB_M)
    hline(s, 11, 18, 10, NB_L)
    outline_obj(s)
    return s


def woodpile_wall():
    s = Spr(64, 32)
    s.rect(4, 6, 59, 7, WOOD_D)
    for row in range(3):
        for k in range(9):
            cx = 9 + k * 6 + (3 if row % 2 else 0)
            cy = 26 - row * 6
            if cx > 57:
                continue
            s.ellipse(cx, cy, 3.2, 3.0, WOOD_M)
            s.ellipse(cx, cy, 2.0, 1.8, SAND)
            s.set(cx, cy, WOOD_L)
    hline(s, 3, 60, 30, WOOD_D)
    outline_obj(s)
    return s


def bench_wall():
    s = Spr(64, 32)
    box(s, 4, 16, 59, 20, WOOD_L, hi=SAND, lo=WOOD_M)
    for x in (8, 52):
        s.rect(x, 21, x + 3, 29, WOOD_D)
        vline(s, x, 21, 29, WOOD_M)
    box(s, 4, 6, 59, 10, WOOD_M, hi=WOOD_L, lo=WOOD_D)
    for x in (10, 53):
        vline(s, x, 11, 15, WOOD_D)
    outline_obj(s)
    return s


def ladder():
    s = Spr(32, 64)
    for x in (8, 22):
        vline(s, x, 2, 63, WOOD_L)
        vline(s, x + 1, 2, 63, WOOD_D)
    for y in range(6, 62, 7):
        hline(s, 9, 21, y, WOOD_M)
        hline(s, 9, 21, y + 1, WOOD_D)
    outline_obj(s)
    return s


def flower_pot(c):
    s = Spr(32, 32)
    for y in range(20, 30):
        w = 6 if y < 22 else 5
        hline(s, 16 - w, 15 + w, y, SK_M if y < 22 else SK_S)
    hline(s, 10, 21, 20, SK_L)
    for i in range(14):
        x = 16 + int((hsh(i, 1, 2) - 0.5) * 12)
        y = 19 - int(hsh(i, 2, 2) * 9)
        s.set(x, y, GRASS if i % 2 else FOR_M)
        s.set(x, y + 1, FOR_M)
    for i in range(5):
        x = 16 + int((hsh(i, 5, 2) - 0.5) * 10)
        y = 12 + int(hsh(i, 6, 2) * 4)
        s.set(x, y, c)
        s.set(x + 1, y, c)
        s.set(x, y - 1, lt(c) if lt(c) != c else CREAM)
    outline_obj(s)
    return s


def name_board():
    s = Spr(64, 32)
    box(s, 2, 8, 61, 24, WOOD_M, hi=WOOD_L, lo=WOOD_D)
    s.rect(4, 10, 59, 22, WOOD_D)
    s.rect(5, 11, 58, 21, WOOD_M)
    for x in (6, 57):
        s.set(x, 12, ST_L)
        s.set(x, 20, ST_L)
    return s


# ====================================================================== Dach-Overlays
def dormer(lit, f=0):
    s = Spr(32, 32)
    # Giebeldach
    for y in range(1, 11):
        half = int((y - 1) * 1.45) + 2
        for x in range(16 - half, 16 + half):
            c = WOOD_D if (x + y) % 4 else EARTH
            if y in (1, 2):
                c = WOOD_M
            s.set(x, y, c)
    # Wand
    s.rect(4, 11, 27, 28, WOOD_L)
    vline(s, 4, 11, 28, SAND)
    s.rect(24, 11, 27, 28, WOOD_M)
    hline(s, 4, 27, 11, EARTH)
    hline(s, 4, 27, 12, WOOD_D)
    s.rect(8, 14, 23, 26, OL1)
    glass(s, 9, 15, 22, 25, lit, f, 41)
    vline(s, 15, 15, 25, WOOD_D)
    vline(s, 16, 15, 25, WOOD_M)
    hline(s, 9, 22, 20, WOOD_D)
    hline(s, 3, 28, 28, ST_L)
    hline(s, 3, 28, 29, ST_M)
    outline_obj(s)
    # Giebelkante hell
    for y in range(1, 11):
        half = int((y - 1) * 1.45) + 2
        s.set(16 - half, y, WOOD_L)
        s.set(16 + half - 1, y, WOOD_M)
    return s


def skylight(lit, f=0):
    s = Spr(32, 32)
    box(s, 7, 8, 24, 25, ST_M, hi=ST_L, lo=ST_D)
    s.rect(9, 10, 22, 23, OL1)
    glass(s, 10, 11, 21, 22, lit, f, 51)
    vline(s, 15, 11, 22, ST_D)
    vline(s, 16, 11, 22, ST_M)
    hline(s, 6, 25, 26, OL2)
    return s


def chimney(mat, smoke_frame=None):
    """Schornstein 32x64 (ohne Rauch) oder 32x96 mit Rauch-Frame."""
    H = 96 if smoke_frame is not None else 64
    s = Spr(32, H)
    off = H - 64
    for y in range(off + 20, H):
        for x in range(9, 23):
            if mat == 'stein':
                row, cy = divmod(y - off, 6)
                xo = (x + (row % 2) * 4) % 8
                c = ST_M if cy not in (0, 5) else (ST_L if cy == 0 else ST_D)
                if xo == 0:
                    c = ST_D
            else:
                row, cy = divmod(y - off, 4)
                xo = (x + (row % 2) * 3) % 6
                c = RED_D if cy != 3 and xo else ST_M
                if cy == 0 and xo and hsh(x, row, 3) < 0.4:
                    c = ROSE
            if x >= 20:
                c = dk(c)
            if x == 10 and c not in (ST_D, ST_M):
                c = lt(c)
            s.set(x, y, c)
    # Kappe
    s.rect(7, off + 14, 24, off + 19, OL1)
    s.rect(8, off + 15, 23, off + 18, ST_M)
    hline(s, 8, 23, off + 15, ST_L)
    s.rect(10, off + 11, 21, off + 14, OL1)
    s.rect(11, off + 12, 20, off + 13, OL2)
    for y in range(off + 20, H):
        s.set(8, y, OL1)
        s.set(23, y, OL1)
    # Fuss: Schatten auf dem Dach
    hline(s, 8, 23, H - 1, OL1)
    if smoke_frame is not None:
        smoke(s, 16, off + 11, smoke_frame, 8)
    return s


def stovepipe(smoke_frame=None):
    H = 96 if smoke_frame is not None else 64
    s = Spr(32, H)
    off = H - 64
    for y in range(off + 18, H):
        for k, c in enumerate((OL1, ST_L, ST_M, ST_M, ST_D, OL1)):
            s.set(13 + k, y, c)
    for y in (off + 30, off + 46):
        hline(s, 12, 19, y, OL1)
        hline(s, 13, 18, y + 1, ST_D)
    # Hut
    for i, y in enumerate(range(off + 11, off + 16)):
        hline(s, 12 - i, 19 + i, y, ST_M if i else ST_L)
    hline(s, 7, 24, off + 16, OL1)
    s.rect(13, off + 17, 18, off + 17, OL2)
    outline_obj(s)
    if smoke_frame is not None:
        smoke(s, 16, off + 10, smoke_frame, 8)
    return s


def smoke(s, cx, ytop, f, nf):
    """Rauch steigt, treibt nach rechts, wird groesser und loest sich auf. Nahtlose Schleife ueber nf Frames."""
    puffs = 4
    for p in range(puffs):
        t = ((p + f / float(nf)) / puffs) % 1.0
        y = (ytop - 1) - t * (ytop - 3)
        x = cx + math.sin(t * 4.0 + 0.5) * 1.5 + t * 7
        r = 2.2 + t * 3.4
        for yy in range(int(y - r) - 1, int(y + r) + 2):
            for xx in range(int(x - r) - 1, int(x + r) + 2):
                d = math.sqrt((xx + .5 - x) ** 2 + ((yy + .5 - y) * 1.15) ** 2)
                if d > r or not (0 <= yy < ytop):
                    continue
                if t > 0.62 and BAYER4[yy % 4][xx % 4] < (t - 0.62) * 40:
                    continue          # loest sich auf (Dither nur fuer Rauch/Nebel, Style-Bibel)
                rel = ((xx + .5 - x) - (yy + .5 - y)) / max(r, 1)
                c = MOON if rel < -0.35 else (ST_L if rel < 0.45 else ST_M)
                if t > 0.5:
                    c = ST_L if c == MOON else (SV_L if c == ST_M else c)
                s.set(xx, yy, c)


BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def weathervane(f):
    s = Spr(32, 64)
    vline(s, 15, 14, 63, OL1)
    vline(s, 16, 14, 63, ST_D)
    s.rect(12, 58, 19, 63, OL1)
    s.rect(13, 59, 18, 62, ST_M)
    for x in range(10, 22):
        s.set(x, 30, ST_M)
    s.set(10, 30, OL1)
    s.set(21, 30, OL1)
    s.ellipse(16, 30, 1.5, 1.5, YEL)
    # Hahn: Breite je nach Drehung
    sc = [1.0, 0.45, -1.0, -0.45][f % 4]
    pts = [(-6, 0), (-5, -1), (-4, -2), (-3, -2), (-2, -1), (-1, -1), (0, -1), (1, -2), (2, -4), (3, -5), (4, -4), (4, -3),
           (5, -3), (3, -3), (2, -3), (1, -1), (2, 0), (1, 1), (0, 1), (-1, 1), (-2, 1), (-3, 1), (-4, 0), (-5, 0), (-6, -2),
           (-7, -3), (-6, -1), (-1, 0), (0, 0), (1, 0), (-2, 0), (-3, 0), (3, -4), (2, -2), (-4, -1), (-3, -1), (-5, -2)]
    for (x, y) in pts:
        xx = 16 + int(round(x * sc))
        s.set(xx, 20 + y, OL1 if (x, y) in ((4, -3), (5, -3)) else (ST_D if abs(sc) < 0.6 else OL2))
    s.set(16 + int(round(3 * sc)), 15, RED_D)
    s.set(16 + int(round(3 * sc)), 14, ROSE)
    for x in range(14, 19):
        s.set(x, 22, OL1)
    return s


def roof_turret():
    """Dachreiter mit Glocke (Kapelle), 32x64."""
    s = Spr(32, 64)
    # Spitzdach
    for y in range(2, 22):
        half = int((y - 1) * 0.55) + 1
        for x in range(16 - half, 16 + half):
            c = roof_c = SV_D if (x + y) % 3 else SV_M
            if x < 16 - half + 2:
                c = SV_M
            s.set(x, y, c)
    s.rect(15, 0, 16, 2, YEL)
    s.set(15, 0, CREAM)
    # Glockenstube
    s.rect(6, 22, 25, 44, WOOD_M)
    s.rect(9, 26, 22, 41, OL2)
    for y in range(26, 34):
        w = (y - 25) // 2 + 2
        hline(s, 16 - w, 15 + w, y + 4, YEL if y < 30 else ORA)
    s.set(15, 30, CREAM)
    s.rect(15, 26, 16, 29, ST_D)
    hline(s, 6, 25, 22, WOOD_L)
    vline(s, 6, 22, 44, WOOD_L)
    vline(s, 25, 22, 44, WOOD_D)
    # Unterbau
    s.rect(7, 45, 24, 63, WOOD_D)
    for y in range(47, 63, 4):
        hline(s, 8, 23, y, EARTH)
    hline(s, 7, 24, 45, WOOD_M)
    outline_obj(s)
    return s


# ====================================================================== Register
def register(R):
    A = 'aussen_wand'
    for st in ('lit', 'dunkel'):
        for sh in ('blau', 'rot', 'gruen', None):
            nm = 'Fenster_%s_%s' % ('Licht' if st == 'lit' else 'Dunkel', (sh or 'ohne').capitalize())
            if st == 'lit':
                R.add_anim(nm, [window(st, sh, f) for f in range(4)], 260, A)
            else:
                R.add(nm, window(st, sh), A)
    R.add('Fenster_Laeden_Zu_Licht', window('zu', 'blau'), A)
    R.add('Fenster_Laeden_Zu_Rot', window('zu_dunkel', 'rot'), A)
    R.add('Fenster_Laeden_Zu_Blau', window('zu_dunkel', 'blau'), A)
    R.add_anim('Fenster_Rund_Licht', [window_round(True, f) for f in range(4)], 260, A)
    R.add('Fenster_Rund_Dunkel', window_round(False), A)
    R.add_anim('Fenster_Bogen_Licht', [window_arch('lit', f) for f in range(4)], 260, A)
    R.add('Fenster_Bogen_Dunkel', window_arch('dunkel'), A)
    R.add_anim('Fenster_Bogen_Bunt', [window_arch('bunt', f) for f in range(4)], 320, A)
    R.add('Fenster_Vernagelt', boarded(), A)
    R.add('Fenster_Stall', stable_window(), A)
    for g in ('brot', 'waren', 'apotheke', 'stoff', 'buecher'):
        R.add_anim('Schaufenster_' + g.capitalize(), [shop_window(g, f) for f in range(4)], 280, A)
    for c in ('holz', 'rot', 'blau', 'gruen', 'dunkel'):
        R.add('Tuer_' + c.capitalize(), door(c, 'zu'), A)
    R.add_anim('Tuer_Oberlicht_Holz', [door('holz', 'oberlicht', f) for f in range(4)], 260, A)
    R.add_anim('Tuer_Oberlicht_Blau', [door('blau', 'oberlicht', f) for f in range(4)], 260, A)
    R.add('Tuer_Offen_Licht', door('holz', 'offen'), A)
    R.add('Tuer_Offen_Dunkel', door('holz', 'offen_dunkel'), A)
    R.add('Tuer_Stall', door('rot', 'stall'), A)
    R.add_anim('Tuer_Laden_Doppel', [door_double_shop(f) for f in range(4)], 280, A)
    R.add('Tor_Scheune', barn_gate(), A)
    R.add('Portal_Kapelle', chapel_portal(), A)
    for c in ('rot', 'holz'):
        for p in ('L', 'M', 'R', 'E'):
            R.add('Vordach_%s_%s' % (c.capitalize(), p), awning(c, p), A)
    for nm, c1, c2 in (('Rot', ROSE, RED_D), ('Blau', BLUE_L, MOON), ('Gelb', YEL, ORA), ('Weiss', CREAM, MOON)):
        R.add('Blumenkasten_' + nm, flower_box(c1, c2), A)
    R.add_anim('Wandlaterne', [wall_lantern(f) for f in range(4)], 170, A)
    for k in SIGN_ICONS:
        R.add_anim('Haengeschild_' + k.capitalize(), [hanging_sign(k, f) for f in range(4)], 420, A)
    for p in ('oben', 'mitte', 'unten'):
        R.add('Fallrohr_' + p.capitalize(), downpipe(p), A)
    R.add('Efeu_Gross_A', ivy(64, 3), A)
    R.add('Efeu_Gross_B', ivy(64, 8), A)
    R.add('Efeu_Klein', ivy(32, 5), A)
    R.add_anim('Talisman_Tuer', [talisman_door(f) for f in range(6)], 220, A)
    R.add('Schild_Brett', name_board(), A)
    R.add('Leiter_Wand', ladder(), A)
    G = 'aussen_boden'
    R.add('Stufe_Stein', steps('stein'), G, solid=False)
    R.add('Stufe_Holz', steps('holz'), G, solid=False)
    R.add('Stufe_Stein_Breit', steps('stein', True), G, solid=False)
    R.add('Regenfass', rain_barrel(), G)
    R.add('Holzstapel_Wand', woodpile_wall(), G)
    R.add('Bank_Wand', bench_wall(), G)
    for nm, c in (('Rot', ROSE), ('Blau', BLUE_L), ('Gelb', YEL)):
        R.add('Blumentopf_' + nm, flower_pot(c), G)
    D = 'aussen_dach'
    R.add_anim('Gaube_Licht', [dormer(True, f) for f in range(4)], 260, D)
    R.add('Gaube_Dunkel', dormer(False), D)
    R.add_anim('Dachfenster_Licht', [skylight(True, f) for f in range(4)], 260, D)
    R.add('Dachfenster_Dunkel', skylight(False), D)
    R.add('Schornstein_Stein', chimney('stein'), D)
    R.add('Schornstein_Backstein', chimney('backstein'), D)
    R.add_anim('Schornstein_Stein_Rauch', [chimney('stein', f) for f in range(8)], 140, D)
    R.add_anim('Schornstein_Backstein_Rauch', [chimney('backstein', f) for f in range(8)], 140, D)
    R.add('Ofenrohr', stovepipe(), D)
    R.add_anim('Ofenrohr_Rauch', [stovepipe(f) for f in range(8)], 140, D)
    R.add_anim('Wetterfahne', [weathervane(f) for f in range(4)], 700, D)
    R.add('Dachreiter_Glocke', roof_turret(), D)
