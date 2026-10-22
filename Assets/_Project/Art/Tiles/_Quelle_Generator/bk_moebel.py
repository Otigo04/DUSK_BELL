"""Haus-Baukasten INNEN: Moebel, Wanddeko, Teppiche. 3/4-Ansicht von vorne, Licht oben links.
Jedes Teil = ganzes Objekt, Ankerzelle links unten. fuss = belegte Bodenzeilen (fuer Kollision / Pruefung)."""
from bk_lib import *

WD = (WOOD_M, WOOD_L, WOOD_D)          # Holz: Grund, Licht, Schatten
WDD = (WOOD_D, WOOD_M, EARTH)
CLOTH = {'rot': (RED_D, ROSE, SK_S), 'blau': (BLUE_D, BLUE_L, NB_M), 'gruen': (FOR_M, GRASS, FOR_D),
         'sand': (SAND, CREAM, WOOD_L), 'violett': (SV_M, SV_L, SV_D)}


# ====================================================================== Grundformen
def block(s, x0, x1, ytop, depth, ybot, wood=WD, top=None, legs=False, out=OL1):
    """Moebelkoerper: Oberseite (depth hoch) + Front bis ybot."""
    b, hi, lo = wood
    tb, thi, tlo = top or (hi, lt(hi), b)
    s.rect(x0, ytop, x1, ybot, out)
    s.rect(x0 + 1, ytop + 1, x1 - 1, ytop + depth, tb)
    hline(s, x0 + 1, x1 - 1, ytop + 1, thi)
    hline(s, x0 + 1, x1 - 1, ytop + depth, tlo)
    hline(s, x0, x1, ytop + depth + 1, out)
    if legs:
        return
    s.rect(x0 + 1, ytop + depth + 2, x1 - 1, ybot - 1, b)
    vline(s, x0 + 1, ytop + depth + 2, ybot - 1, hi)
    vline(s, x1 - 1, ytop + depth + 2, ybot - 1, lo)
    hline(s, x0 + 1, x1 - 1, ybot - 1, lo)


def legs(s, xs, y0, y1, wood=WD):
    for x in xs:
        s.rect(x, y0, x + 1, y1, OL1)
        vline(s, x, y0, y1 - 1, wood[0])
        vline(s, x + 1, y0, y1 - 1, wood[2])


def floor_shadow(s, x0, x1, y):
    for x in range(x0, x1 + 1):
        if not s.solid(x, y) and (x + y) % 2 == 0:
            s.set(x, y, OL2)


def drawer(s, x0, y0, x1, y1, wood=WD):
    s.rect(x0, y0, x1, y1, OL1)
    s.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, wood[0])
    hline(s, x0 + 1, x1 - 1, y0 + 1, wood[1])
    cx = (x0 + x1) // 2
    s.set(cx, (y0 + y1) // 2, YEL)
    s.set(cx + 1, (y0 + y1) // 2, ORA)


def fire(s, x0, x1, yb, h, f, nf=6, seed=0):
    """Feuer in einem Kasten (Boden yb). Ruhige, nahtlose Schleife ueber nf Frames."""
    for x in range(x0, x1 + 1):
        ph_ = f / nf * 2 * math.pi
        k = hsh(x, 3, seed) * 6.28
        hh = h * (0.55 + 0.30 * math.sin(ph_ + k) + 0.15 * math.sin(2 * ph_ + k * 2))
        edge = min(x - x0, x1 - x) / max(1, (x1 - x0) / 2)
        hh *= 0.45 + 0.55 * min(1, edge * 1.6)
        for i in range(int(round(hh))):
            t = i / max(1, hh)
            c = GLOW if t < 0.3 else (ORA if t < 0.65 else YEL)
            if t > 0.85 and hh > 4:
                c = CREAM if (x + f) % 3 == 0 else YEL
            s.set(x, yb - i, c)
    # Glut
    for x in range(x0, x1 + 1):
        s.set(x, yb, ORA if (x + f) % 3 else YEL)
        s.set(x, yb + 1, GLOW if (x + f) % 2 else RED_D)


def candle(s, x, yb, f, h=4):
    s.rect(x, yb - h + 1, x + 1, yb, CREAM)
    s.set(x + 1, yb - h + 1, SAND)
    vline(s, x + 1, yb - h + 2, yb, SAND)
    fh = [3, 2, 3, 4][f % 4]
    for i in range(fh):
        s.set(x + (0 if i < fh - 1 else [0, 1, 0, 0][f % 4]), yb - h - i, ORA if i == 0 else (CREAM if i == 1 else YEL))


def books(s, x0, x1, yb, h, seed):
    x = x0
    i = 0
    while x <= x1:
        c = [RED_D, BLUE_D, FOR_M, WOOD_D, SV_M, SK_S, NB_L][int(hsh(i, seed, 3) * 7)]
        bh = h - int(hsh(i, seed, 4) * 3)
        bw = 2 if hsh(i, seed, 5) < 0.7 else 1
        for xx in range(x, min(x1, x + bw - 1) + 1):
            vline(s, xx, yb - bh + 1, yb, c)
            s.set(xx, yb - bh + 2, CREAM if (i % 3 == 0) else lt(c))
        x += bw
        if hsh(i, seed, 6) < 0.12:
            x += 1
        i += 1


def jars(s, x0, x1, yb, seed, cols=(FOR_M, BLUE_D, RED_D, SAND, SK_S)):
    x = x0
    i = 0
    while x + 2 <= x1:
        c = cols[int(hsh(i, seed, 1) * len(cols))]
        h = 4 + int(hsh(i, seed, 2) * 3)
        s.rect(x, yb - h + 1, x + 2, yb, c)
        s.set(x, yb - h + 2, lt(c) if lt(c) != c else CREAM)
        hline(s, x, x + 2, yb - h, WOOD_L if i % 2 else ST_L)
        x += 4
        i += 1


def shelf_unit(w, h, rows, filler, wood=WD, seed=0):
    """Wandregal / Schrank mit offenen Faechern. rows = Anzahl Faecher, filler(s, x0, x1, yb, row)"""
    s = Spr(w, h)
    top = 2
    block(s, 1, w - 2, top, 3, h - 2, wood)
    inner_top = top + 6
    fh = (h - 4 - inner_top) // rows
    for r in range(rows):
        y0 = inner_top + r * fh
        y1 = y0 + fh - 2
        s.rect(4, y0, w - 5, y1, OL2)
        hline(s, 4, w - 5, y0, OL1)
        filler(s, 5, w - 6, y1, r)
        hline(s, 3, w - 4, y1 + 1, wood[1])
    floor_shadow(s, 1, w - 2, h - 1)
    return s


# ====================================================================== Wohnen
def fireplace(f):
    s = Spr(64, 64)
    # Kaminmantel Stein
    for y in range(8, 62):
        for x in range(4, 60):
            row, v = divmod(y, 6)
            u = (x + (row % 2) * 5) % 10
            c = ST_M if v not in (0, 5) else (ST_L if v == 0 else ST_D)
            if u == 0:
                c = ST_D
            if x > 54:
                c = dk(c)
            s.set(x, y, c)
    s.rect(3, 7, 60, 7, OL1)
    vline(s, 3, 7, 62, OL1)
    vline(s, 60, 7, 62, OL1)
    # Sims
    block(s, 1, 62, 22, 3, 28, WD)
    candle(s, 8, 21, f)
    candle(s, 54, 21, (f + 2) % 6)
    s.rect(26, 15, 37, 21, OL1)
    s.rect(27, 16, 36, 20, WOOD_L)
    s.rect(29, 17, 34, 19, CREAM)
    s.set(31, 18, OL1)
    s.set(32, 17, OL1)
    # Feueroeffnung
    s.rect(14, 33, 49, 61, OL1)
    s.rect(15, 34, 48, 60, OL2)
    for y in range(34, 61):
        for x in range(15, 49):
            if (x + y) % 5 == 0:
                s.set(x, y, SV_D)
    fire(s, 18, 45, 56, 16, f, 6, 4)
    # Holzscheite
    for (x0, x1, y) in ((19, 34, 57), (29, 44, 58)):
        s.rect(x0, y, x1, y + 2, WOOD_D)
        hline(s, x0, x1, y, WOOD_M)
        s.set(x0, y + 1, SAND)
    hline(s, 15, 48, 60, EARTH)
    s.rect(10, 61, 53, 63, OL1)
    hline(s, 11, 52, 62, ST_L)
    return s


def sofa(col, w=64):
    b, hi, lo = CLOTH[col]
    s = Spr(w, 32)
    # Lehne
    s.rect(3, 4, w - 4, 18, OL1)
    s.rect(4, 5, w - 5, 17, b)
    hline(s, 4, w - 5, 5, hi)
    for x in range(12, w - 8, 14):
        s.set(x, 10, lo)
        s.set(x + 1, 11, lo)
    # Sitz
    s.rect(3, 18, w - 4, 27, OL1)
    s.rect(4, 19, w - 5, 26, b)
    hline(s, 4, w - 5, 19, hi)
    vline(s, w // 2, 19, 25, lo)
    hline(s, 4, w - 5, 26, lo)
    # Armlehnen
    for x0 in (1, w - 9):
        s.rect(x0, 10, x0 + 7, 28, OL1)
        s.rect(x0 + 1, 11, x0 + 6, 27, b)
        hline(s, x0 + 1, x0 + 6, 11, hi)
        vline(s, x0 + 6, 12, 27, lo)
    legs(s, (4, w - 6), 28, 30, WDD)
    return s


def armchair(col):
    b, hi, lo = CLOTH[col]
    s = Spr(32, 32)
    s.rect(6, 3, 25, 18, OL1)
    s.rect(7, 4, 24, 17, b)
    hline(s, 7, 24, 4, hi)
    s.rect(5, 17, 26, 27, OL1)
    s.rect(6, 18, 25, 26, b)
    hline(s, 6, 25, 18, hi)
    hline(s, 6, 25, 26, lo)
    for x0 in (3, 22):
        s.rect(x0, 10, x0 + 6, 27, OL1)
        s.rect(x0 + 1, 11, x0 + 5, 26, b)
        hline(s, x0 + 1, x0 + 5, 11, hi)
        vline(s, x0 + 5, 12, 26, lo)
    legs(s, (6, 24), 28, 30, WDD)
    return s


def table(w, cloth=None, items=None, round_=False):
    s = Spr(w, 32)
    if round_:
        s.ellipse(w / 2, 13, w / 2 - 3, 7, OL1)
        s.ellipse(w / 2, 13, w / 2 - 4, 6, WOOD_L if not cloth else CLOTH[cloth][0])
        s.ellipse(w / 2 - 1, 12, w / 2 - 7, 4, SAND if not cloth else CLOTH[cloth][1])
        s.rect(int(w / 2) - 2, 19, int(w / 2) + 1, 27, OL1)
        s.rect(int(w / 2) - 1, 19, int(w / 2), 26, WOOD_D)
        s.rect(int(w / 2) - 6, 27, int(w / 2) + 5, 29, OL1)
        hline(s, int(w / 2) - 5, int(w / 2) + 4, 28, WOOD_D)
    else:
        top = (CLOTH[cloth][0], CLOTH[cloth][1], CLOTH[cloth][2]) if cloth else None
        block(s, 2, w - 3, 8, 7, 19, WD, top)
        if cloth:
            b, hi, lo = CLOTH[cloth]
            for x in range(3, w - 3):
                for y in range(17, 21 + (x % 4 == 0)):
                    s.set(x, y, b if y < 20 else lo)
            for x in range(4, w - 4, 3):
                s.set(x, 18, CREAM)
        legs(s, (4, w - 6), 20, 29, WD)
        if w > 40:
            legs(s, (w // 2 - 1,), 20, 26, WD) if False else None
    floor_shadow(s, 3, w - 4, 30)
    if items:
        items(s)
    return s


def chair(view):
    s = Spr(32, 32)
    if view == 'vorne':
        # Lehne hinten (oben), Sitz vorne
        s.rect(9, 2, 22, 15, OL1)
        s.rect(10, 3, 21, 14, WOOD_M)
        for x in (12, 15, 18):
            vline(s, x, 5, 13, WOOD_D)
        hline(s, 10, 21, 3, WOOD_L)
        block(s, 8, 23, 14, 4, 20, WD)
        legs(s, (9, 21), 20, 29, WD)
    else:
        block(s, 8, 23, 8, 4, 14, WD)
        legs(s, (9, 21), 14, 27, WD)
        s.rect(9, 12, 22, 25, OL1)
        s.rect(10, 13, 21, 24, WOOD_M)
        hline(s, 10, 21, 13, WOOD_L)
        for x in (12, 15, 18):
            vline(s, x, 15, 23, WOOD_D)
    floor_shadow(s, 8, 23, 30)
    return s


def bookcase(w):
    def fill(s, x0, x1, yb, r):
        books(s, x0, x1, yb, 8 + (r % 2), 17 * w + r)
        if r == 2 and w > 40:
            s.rect(x1 - 6, yb - 4, x1 - 1, yb, ST_L)
            s.set(x1 - 5, yb - 4, MOON)
    return shelf_unit(w, 64, 4, fill, WDD, w)


def grandfather_clock(f):
    s = Spr(32, 64)
    block(s, 8, 23, 2, 2, 61, WDD)
    # Kopf
    s.rect(9, 6, 22, 19, OL1)
    s.ellipse(15.5, 12.5, 5.5, 5.5, CREAM)
    s.ellipse(15.5, 12.5, 4.0, 4.0, CREAM)
    s.set(15, 9, OL1)
    s.set(15, 10, OL1)
    s.set(15, 11, OL1)
    s.set(16, 12, OL1)
    s.set(17, 12, OL1)
    for (x, y) in ((15, 8), (20, 12), (15, 17), (11, 12)):
        s.set(x, y, WOOD_D)
    # Pendel-Fenster
    s.rect(11, 22, 20, 50, OL1)
    s.rect(12, 23, 19, 49, OL2)
    ang = [0, 2, 0, -2][f % 4]
    for i in range(16):
        s.set(15 + int(round(ang * i / 16)), 23 + i, ST_D)
    px = 15 + ang
    s.ellipse(px + 0.5, 42, 2.6, 2.6, YEL)
    s.set(px, 41, CREAM)
    s.set(px + 1, 43, ORA)
    hline(s, 12, 19, 46, YEL)
    hline(s, 12, 19, 47, ORA)
    floor_shadow(s, 8, 23, 62)
    return s


def rug(w, h, col, pattern):
    b, hi, lo = CLOTH[col]
    s = Spr(w, h)
    oval = pattern == 'rund'
    for y in range(2, h - 2):
        for x in range(2, w - 2):
            if oval and ((x + .5 - w / 2) / (w / 2 - 2)) ** 2 + ((y + .5 - h / 2) / (h / 2 - 2)) ** 2 > 1:
                continue
            c = b
            bx, by = min(x - 2, w - 3 - x), min(y - 2, h - 3 - y)
            if oval:
                d = ((x + .5 - w / 2) / (w / 2 - 2)) ** 2 + ((y + .5 - h / 2) / (h / 2 - 2)) ** 2
                if d > 0.78:
                    c = SAND if d < 0.86 else lo
                elif 0.4 < d < 0.48:
                    c = hi
            else:
                if bx in (1, 2) or by in (1, 2):
                    c = SAND
                elif bx == 0 or by == 0:
                    c = lo
                elif bx == 4 or by == 4:
                    c = hi
                else:
                    u, v = (x - 2) % 12, (y - 2) % 10
                    if abs(u - 6) + abs(v - 5) == 3:
                        c = hi if pattern == 'raute' else SAND
                    if pattern == 'raute' and abs(u - 6) + abs(v - 5) == 0:
                        c = CREAM
            s.set(x, y, c)
    if not oval:
        for x in range(3, w - 3, 2):
            s.set(x, 1, CREAM)
            s.set(x, h - 2, CREAM)
    return s


def runner(col):
    b, hi, lo = CLOTH[col]
    s = Spr(32, 64)
    for y in range(1, 63):
        for x in range(7, 25):
            c = b
            if x in (7, 24):
                c = lo
            elif x in (9, 22):
                c = SAND
            elif (y % 8 == 4) and 12 <= x <= 19:
                c = hi
            s.set(x, y, c)
    return s


def dresser(w=64):
    s = Spr(w, 32)
    block(s, 1, w - 2, 4, 4, 28, WD)
    for r in range(2):
        for k in range(2 if w > 40 else 1):
            x0 = 4 + k * ((w - 8) // 2)
            drawer(s, x0, 11 + r * 8, x0 + (w - 8) // (2 if w > 40 else 1) - 2, 17 + r * 8)
    legs(s, (2, w - 4), 28, 30, WDD)
    # Deko oben
    s.rect(8, 1, 11, 7, BLUE_D)
    s.set(8, 2, BLUE_L)
    s.set(9, 0, ROSE)
    s.set(10, 0, YEL)
    return s


def potted_plant(big=False):
    s = Spr(32, 64 if big else 32)
    H = s.h
    s.rect(10, H - 11, 21, H - 2, OL1)
    s.rect(11, H - 10, 20, H - 3, SK_M)
    hline(s, 11, 20, H - 10, SK_L)
    vline(s, 20, H - 9, H - 3, SK_S)
    hline(s, 9, 22, H - 12, OL1)
    import random
    rnd = random.Random(H)
    top = 6 if big else 4
    for i in range(70 if big else 35):
        a = rnd.uniform(-2.6, -0.5)
        ln = rnd.uniform(4, (H - 14 - top))
        x = 16 + math.cos(a) * ln * 0.7
        y = H - 13 + math.sin(a) * ln
        c = GRASS if rnd.random() < 0.5 else (FOR_M if rnd.random() < 0.6 else GRASS_L)
        s.set(int(x), int(y), c)
        s.set(int(x) + 1, int(y), FOR_M)
        s.set(int(x), int(y) + 1, FOR_D)
    outline_obj(s)
    return s


def chest(open_=False):
    s = Spr(32, 32)
    block(s, 4, 27, 10, 5, 28, WD)
    for x in (8, 23):
        vline(s, x, 11, 27, ST_D)
    hline(s, 5, 26, 17, ST_D)
    s.rect(14, 15, 17, 19, OL1)
    s.set(15, 17, YEL)
    s.set(16, 17, ORA)
    if open_:
        s.rect(4, 2, 27, 11, OL1)
        s.rect(5, 3, 26, 10, WOOD_D)
        s.rect(6, 12, 25, 15, OL2)
        for x in range(7, 25, 3):
            s.set(x, 13, YEL)
            s.set(x + 1, 14, ORA)
    floor_shadow(s, 4, 27, 29)
    return s


# ====================================================================== Kueche
def iron_stove(f):
    s = Spr(64, 64)
    # Ofenrohr nach oben
    for y in range(0, 26):
        for k, c in enumerate((OL1, ST_M, ST_D, OL2, OL2, OL1)):
            s.set(44 + k, y, c)
    hline(s, 43, 50, 12, OL1)
    block(s, 4, 59, 24, 6, 61, (OL2, SV_D, OL1), (ST_D, ST_M, OL2))
    # Herdplatten
    for cx in (16, 32):
        s.ellipse(cx, 28, 5, 2, OL1)
        s.ellipse(cx, 28, 4, 1.4, ST_D)
    # Topf mit Dampf
    s.rect(11, 20, 21, 28, OL1)
    s.rect(12, 21, 20, 27, ST_M)
    hline(s, 12, 20, 21, ST_L)
    hline(s, 10, 22, 20, OL1)
    for i in range(3):
        t = ((i + f / 6.0) / 3.0) % 1.0
        yy = int(18 - t * 16)
        xx = 15 + int(math.sin(t * 6 + i) * 2)
        if yy >= 0:
            s.set(xx, yy, ST_L if t < 0.6 else MOON)
            if t < 0.7:
                s.set(xx + 1, yy, ST_L)
    # Ofentuer mit Feuer
    s.rect(10, 37, 33, 54, OL1)
    s.rect(11, 38, 32, 53, OL2)
    fire(s, 13, 30, 50, 9, f, 6, 9)
    for x in range(11, 33, 3):
        vline(s, x, 38, 53, OL1)
    hline(s, 11, 32, 38, ST_D)
    # Backrohr
    s.rect(38, 37, 54, 54, OL1)
    s.rect(39, 38, 53, 53, ST_D)
    hline(s, 41, 51, 41, ST_M)
    s.rect(44, 44, 48, 45, YEL)
    legs(s, (6, 56), 61, 63, (ST_D, ST_M, OL2))
    return s


def sink(w=64):
    s = Spr(w, 32)
    block(s, 1, w - 2, 6, 6, 29, WD, (ST_L, MOON, ST_M))
    s.rect(8, 8, 30, 12, OL1)
    s.rect(9, 9, 29, 11, NB_M)
    hline(s, 10, 27, 9, NB_L)
    s.rect(36, 2, 38, 8, OL1)
    s.set(37, 3, ST_L)
    hline(s, 33, 38, 2, OL1)
    for k in range(3):
        drawer(s, 4 + k * 19, 15, 4 + k * 19 + 16, 26)
    # Teller
    for x in (44, 50):
        s.ellipse(x, 9, 3, 1.4, OL1)
        s.ellipse(x, 9, 2, 0.8, MOON)
    return s


def kitchen_cabinet():
    s = Spr(32, 64)
    block(s, 2, 29, 2, 3, 61, WD)
    s.rect(5, 8, 26, 32, OL2)
    for r, y in enumerate((14, 22, 30)):
        hline(s, 5, 26, y + 1, WOOD_L)
        for k in range(4):
            x = 6 + k * 5
            if r == 0:
                s.ellipse(x + 2, y - 3, 2, 3, BLUE_L)
                s.set(x + 2, y - 3, MOON)
            elif r == 1:
                s.rect(x, y - 3, x + 3, y, [CREAM, BLUE_L, CREAM, ROSE][k])
                hline(s, x, x + 3, y - 3, MOON)
            else:
                s.rect(x, y - 4, x + 3, y, [SK_M, ST_M, SK_M, FOR_M][k])
                s.set(x, y - 4, lt([SK_M, ST_M, SK_M, FOR_M][k]))
    for k in range(2):
        drawer(s, 5 + k * 11, 36, 15 + k * 11, 58)
    floor_shadow(s, 2, 29, 62)
    return s


def worktable_bread():
    def it(s):
        for x in (8, 18, 30):
            s.ellipse(x + 3, 10, 4, 2.2, WOOD_D)
            s.ellipse(x + 3, 9.5, 3.4, 1.6, WOOD_L)
            s.set(x + 2, 9, SAND)
        s.ellipse(46, 11, 6, 2.5, OL1)
        s.ellipse(46, 11, 5, 1.8, CREAM)
        s.rect(52, 6, 54, 12, WOOD_D)
    return table(64, None, it)


def barrel(kind='wasser'):
    s = Spr(32, 32)
    for y in range(8, 29):
        w = 9 if y in (8, 28) else 10
        for x in range(16 - w, 16 + w):
            u = (x - 6) % 4
            c = [WOOD_L, WOOD_M, WOOD_M, WOOD_D][u]
            if x > 21:
                c = dk(c)
            s.set(x, y, c)
    for y in (11, 24):
        hline(s, 6, 25, y, ST_D)
        hline(s, 6, 25, y + 1, OL2)
    s.ellipse(16, 8, 9, 2.6, WOOD_D)
    inner = {'wasser': NB_M, 'aepfel': RED_D, 'fisch': ST_L, 'kohle': OL2, 'korn': SAND}[kind]
    s.ellipse(16, 8, 7.6, 1.8, inner)
    if kind == 'wasser':
        hline(s, 11, 18, 8, NB_L)
    elif kind == 'aepfel':
        for x in range(10, 23, 3):
            s.set(x, 7, ROSE)
            s.set(x + 1, 8, LEAF if x % 2 else RED_D)
    elif kind == 'fisch':
        for x in range(10, 22, 4):
            hline(s, x, x + 2, 7, MOON)
            s.set(x + 3, 8, ST_M)
    elif kind == 'kohle':
        for x in range(10, 23, 2):
            s.set(x, 7 + x % 2, ST_D)
    elif kind == 'korn':
        for x in range(10, 23, 2):
            s.set(x, 8, WOOD_L)
    outline_obj(s)
    floor_shadow(s, 6, 26, 30)
    return s


def sack(col=SAND, label=None):
    s = Spr(32, 32)
    for y in range(9, 29):
        w = 6 + min(y - 9, 4) if y < 22 else 10 - max(0, y - 26)
        for x in range(16 - w, 16 + w):
            c = col
            if x < 16 - w + 2:
                c = lt(col) if lt(col) != col else CREAM
            elif x > 16 + w - 4:
                c = dk(col)
            if y > 25:
                c = dk(col)
            s.set(x, y, c)
    s.rect(13, 5, 18, 9, dk(col))
    hline(s, 12, 19, 9, WOOD_D)
    if label:
        s.rect(12, 15, 19, 20, label)
        hline(s, 12, 19, 15, lt(label))
    outline_obj(s)
    return s


def wall_rack(kind):
    """64x32 Wandbrett (Kategorie Wand): Toepfe | Geschirr | Werkzeug | Garn | Netz"""
    s = Spr(64, 32)
    if kind == 'netz':
        for y in range(4, 28):
            for x in range(4, 60):
                if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                    if ((x - 32) / 28) ** 2 + ((y - 12) / 18) ** 2 < 1:
                        s.set(x, y, SAND if (x // 6) % 2 else WOOD_L)
        for x in (6, 30, 56):
            s.rect(x, 3, x + 2, 5, OL1)
        for (x, y) in ((20, 18), (40, 10), (34, 22)):
            s.ellipse(x, y, 2.5, 2.5, ROSE)
            s.ellipse(x, y, 1.2, 1.2, CREAM)
        return s
    hline(s, 2, 61, 6, OL1)
    s.rect(2, 7, 61, 9, WOOD_M)
    hline(s, 2, 61, 7, WOOD_L)
    hline(s, 2, 61, 10, OL1)
    for x in (6, 56):
        for i in range(5):
            s.set(x + i, 11 + i, WOOD_D)
    if kind == 'toepfe':
        for k, x in enumerate(range(6, 58, 13)):
            s.rect(x + 4, 11, x + 5, 13, OL1)
            s.ellipse(x + 5, 19, 5, 5, OL1)
            s.ellipse(x + 5, 19, 4, 4, [SK_M, ST_M, SK_S, ST_D][k % 4])
            s.set(x + 3, 17, lt([SK_M, ST_M, SK_S, ST_D][k % 4]))
    elif kind == 'geschirr':
        for k, x in enumerate(range(5, 58, 7)):
            s.ellipse(x + 3, 3, 3, 3, OL1)
            s.ellipse(x + 3, 3, 2, 2, [MOON, BLUE_L, MOON, CREAM][k % 4])
            s.set(x + 3, 3, BLUE_D if k % 2 else ST_L)
        for k, x in enumerate(range(8, 58, 10)):
            s.rect(x, 13, x + 3, 17, CREAM)
            s.set(x + 4, 14, CREAM)
            s.set(x + 4, 15, CREAM)
    elif kind == 'werkzeug':
        # Zange, Hammer, Feile, Hufeisen
        for k, x in enumerate(range(8, 58, 12)):
            vline(s, x, 11, 13, OL1)
            if k % 4 == 0:
                vline(s, x, 13, 27, WOOD_M)
                s.rect(x - 3, 13, x + 3, 16, ST_M)
            elif k % 4 == 1:
                for i in range(14):
                    s.set(x - i // 5, 13 + i, ST_D)
                    s.set(x + i // 5, 13 + i, ST_M)
            elif k % 4 == 2:
                for a in range(0, 200, 15):
                    s.set(x + int(4 * math.cos(math.radians(a + 170))), 18 + int(4 * math.sin(math.radians(a + 170))), ST_L)
            else:
                vline(s, x, 13, 26, ST_L)
                vline(s, x + 1, 13, 26, ST_D)
                vline(s, x, 22, 26, WOOD_M)
        outline_obj(s)
    elif kind == 'garn':
        for k, x in enumerate(range(6, 58, 7)):
            c = [ROSE, BLUE_L, YEL, LEAF, CREAM, RED_D, SV_L, ORA][k % 8]
            s.rect(x, 1, x + 4, 5, c)
            hline(s, x, x + 4, 1, WOOD_L)
            hline(s, x, x + 4, 5, WOOD_L)
            s.set(x + 1, 3, lt(c) if lt(c) != c else CREAM)
    return s


def wall_small(kind, f=0):
    """32x32 Wandbehang (Kategorie Wand)."""
    s = Spr(32, 32)
    if kind == 'bild_landschaft':
        box(s, 5, 6, 26, 23, WOOD_D, hi=WOOD_M, lo=EARTH)
        s.rect(7, 8, 24, 21, NB_L)
        s.rect(7, 15, 24, 21, FOR_M)
        for x in range(7, 25):
            s.set(x, 15 - int(2 * math.sin(x / 3)), GRASS)
        s.ellipse(20, 11, 2, 2, YEL)
        s.set(10, 10, MOON)
    elif kind == 'bild_portrait':
        box(s, 8, 4, 23, 25, WOOD_L, hi=YEL, lo=WOOD_D)
        s.rect(10, 6, 21, 23, SV_D)
        s.ellipse(15.5, 13, 3.5, 4, SK_L)
        s.rect(11, 18, 20, 23, NB_M)
        hline(s, 12, 19, 9, OL2)
        s.set(14, 13, OL1)
        s.set(17, 13, OL1)
    elif kind == 'spiegel':
        s.ellipse(15.5, 15, 8, 11, OL1)
        s.ellipse(15.5, 15, 7, 10, YEL)
        s.ellipse(15.5, 15, 5.5, 8.5, NB_L)
        for i in range(5):
            s.set(12 + i, 10 + i, MOON)
    elif kind == 'kerzenleuchter':
        s.rect(14, 12, 17, 22, OL1)
        s.rect(15, 13, 16, 21, ST_L)
        hline(s, 7, 24, 20, OL1)
        hline(s, 8, 23, 19, YEL)
        for x in (8, 15, 22):
            candle(s, x, 18, (f + x) % 4, 4)
    elif kind == 'kraeuter':
        hline(s, 4, 27, 4, WOOD_D)
        for k, x in enumerate((7, 14, 21)):
            vline(s, x + 1, 5, 9, SAND)
            for y in range(9, 24):
                for dx in range(-2 + (y > 18), 3 - (y > 18)):
                    if hsh(x + dx, y, k) < 0.7:
                        s.set(x + 1 + dx, y, [FOR_M, GRASS, SV_L][k] if hsh(x, y, 2) < 0.6 else [GRASS, GRASS_L, SV_M][k])
            hline(s, x - 1, x + 3, 9, RED_D)
    elif kind == 'pfannen':
        hline(s, 3, 28, 3, WOOD_D)
        for k, x in enumerate((9, 21)):
            vline(s, x, 4, 13, OL1)
            s.ellipse(x, 20, 6 - k, 6 - k, OL1)
            s.ellipse(x, 20, 5 - k, 5 - k, ST_D)
            s.ellipse(x - 1, 19, 3 - k, 3 - k, ST_M)
    elif kind == 'talisman':
        lvl = [0, 1, 2, 1][f % 4]
        s.rect(9, 4, 22, 27, OL1)
        s.rect(10, 5, 21, 26, WOOD_D)
        hline(s, 10, 21, 5, WOOD_M)
        for y in range(9, 22):
            w = min(y - 8, 22 - y, 4)
            for x in range(16 - w, 16 + w):
                s.set(x, y, TAL if x < 16 else TAL_D)
        s.set(14, 12, TAL_H)
        if lvl:
            s.set(15, 11, TAL_H)
            s.set(13, 14, TAL_H)
        if lvl == 2:
            for (x, y) in ((11, 8), (20, 23), (11, 23), (20, 8)):
                s.set(x, y, TAL_H)
    elif kind == 'uhr':
        s.ellipse(15.5, 14, 8, 8, OL1)
        s.ellipse(15.5, 14, 7, 7, WOOD_M)
        s.ellipse(15.5, 14, 5, 5, CREAM)
        vline(s, 15, 10, 14, OL1)
        hline(s, 15, 18, 14, OL1)
        vline(s, 15, 22, 27, OL1)
        a = [-2, 0, 2, 0][f % 4]
        s.ellipse(15.5 + a, 27, 1.6, 1.6, YEL)
    elif kind == 'ruder':
        for i in range(28):
            s.set(6 + i * 2 // 3, 2 + i, WOOD_L)
            s.set(7 + i * 2 // 3, 2 + i, WOOD_D)
        s.ellipse(22, 25, 3.5, 5, WOOD_M)
        outline_obj(s)
    elif kind == 'hufeisen':
        for a in range(0, 210, 10):
            x = 16 + int(round(6 * math.cos(math.radians(a + 165))))
            y = 18 + int(round(6 * math.sin(math.radians(a + 165))))
            s.set(x, y, ST_L)
            s.set(x, y + 1, ST_M)
        outline_obj(s)
    elif kind == 'kranz':
        for a in range(0, 360, 8):
            x = 16 + int(round(8 * math.cos(math.radians(a))))
            y = 15 + int(round(8 * math.sin(math.radians(a))))
            s.set(x, y, GRASS if a % 16 else FOR_M)
            s.set(x + 1, y, FOR_M)
        for a in (30, 150, 270):
            s.set(16 + int(8 * math.cos(math.radians(a))), 15 + int(8 * math.sin(math.radians(a))), ROSE)
        s.rect(14, 22, 17, 25, RED_D)
    return s


def inner_window(kind, f=0):
    """32x64 Fenster in der Wandflaeche (Kategorie Wand): nacht | tag | licht(Mondnacht mit Kerze) | vorhang"""
    s = Spr(32, 64)
    box(s, 6, 8, 25, 41, WOOD_L, hi=SAND, lo=WOOD_M)
    for y in range(10, 40):
        for x in range(8, 24):
            t = (y - 10) / 30
            if kind == 'tag':
                c = BLUE_L if t < 0.6 else MOON
            else:
                c = NB_M if t < 0.5 else NB_D
            s.set(x, y, c)
    if kind != 'tag':
        s.ellipse(19, 15, 2, 2, MOON)
        s.set(10, 13, MOON)
        s.set(13, 20, NB_L)
    vline(s, 15, 10, 39, WOOD_M)
    vline(s, 16, 10, 39, WOOD_D)
    hline(s, 8, 23, 24, WOOD_D)
    box(s, 4, 41, 27, 44, ST_L, hi=MOON, lo=ST_M)
    if kind == 'vorhang':
        for x0, x1 in ((3, 10), (21, 28)):
            for y in range(5, 47):
                for x in range(x0, x1 + 1):
                    c = RED_D if (x - x0) % 3 else SK_S
                    if x == x0 + 1:
                        c = ROSE
                    s.set(x, y, c)
        hline(s, 2, 29, 5, WOOD_D)
        hline(s, 2, 29, 4, OL1)
    if kind == 'licht':
        candle(s, 20, 40, f, 4)
    return s


def inner_door(state):
    s = Spr(32, 64)
    box(s, 4, 6, 27, 63, WOOD_D, hi=WOOD_M, lo=EARTH)
    if state == 'offen':
        s.rect(7, 9, 24, 63, OL2)
        for y in range(9, 64):
            for x in range(7, 25):
                if y > 50 and (x + y) % 2:
                    s.set(x, y, NB_D)
        s.rect(7, 9, 9, 63, WOOD_M)
        vline(s, 7, 9, 63, WOOD_L)
        vline(s, 10, 9, 63, OL1)
        return s
    s.rect(7, 9, 24, 63, WOOD_M)
    for (y0, y1) in ((12, 32), (36, 59)):
        box(s, 9, y0, 22, y1, WOOD_M, hi=WOOD_D, lo=WOOD_L)
    s.set(21, 35, YEL)
    s.set(22, 35, ORA)
    return s


# ====================================================================== Schlafen
def bed(col, w=32):
    b, hi, lo = CLOTH[col]
    s = Spr(w, 64)
    # Kopfteil
    s.rect(1, 2, w - 2, 16, OL1)
    s.rect(2, 3, w - 3, 15, WOOD_D)
    hline(s, 2, w - 3, 3, WOOD_M)
    for x in range(5, w - 4, 5):
        vline(s, x, 5, 14, EARTH)
    # Matratze + Kissen + Decke
    s.rect(2, 12, w - 3, 58, OL1)
    s.rect(3, 13, w - 4, 57, CREAM)
    pw = (w - 10) // (2 if w > 40 else 1)
    for k in range(2 if w > 40 else 1):
        x0 = 5 + k * (pw + 1)
        s.rect(x0, 15, x0 + pw - 1, 23, OL1)
        s.rect(x0 + 1, 16, x0 + pw - 2, 22, MOON)
        hline(s, x0 + 1, x0 + pw - 2, 22, ST_L)
    for y in range(27, 58):
        for x in range(3, w - 3):
            c = b
            if y == 27:
                c = hi
            elif y == 28 or (y < 31 and x % 4 == 0):
                c = CREAM if y == 28 else hi
            elif (x + y) % 8 == 0 and y > 32:
                c = hi
            if x in (3, w - 4):
                c = lo
            s.set(x, y, c)
    hline(s, 2, w - 3, 26, OL1)
    # Fussteil
    s.rect(1, 52, w - 2, 61, OL1)
    s.rect(2, 53, w - 3, 60, WOOD_M)
    hline(s, 2, w - 3, 53, WOOD_L)
    hline(s, 2, w - 3, 60, WOOD_D)
    floor_shadow(s, 2, w - 3, 62)
    return s


def nightstand(f):
    s = Spr(32, 32)
    block(s, 7, 24, 12, 4, 28, WD)
    drawer(s, 9, 19, 22, 25)
    legs(s, (8, 22), 28, 30, WD)
    s.ellipse(12, 15, 3, 1, ST_L)
    candle(s, 11, 14, f, 5)
    s.rect(17, 11, 21, 15, RED_D)
    hline(s, 17, 21, 11, ROSE)
    return s


def wardrobe():
    s = Spr(32, 64)
    block(s, 2, 29, 1, 3, 61, WD)
    s.rect(1, 1, 30, 3, OL1)
    hline(s, 2, 29, 2, WOOD_L)
    for x0, x1 in ((5, 15), (16, 26)):
        box(s, x0, 9, x1, 56, WOOD_M, hi=WOOD_D, lo=WOOD_L)
        box(s, x0 + 2, 12, x1 - 2, 30, WOOD_M, hi=WOOD_D, lo=WOOD_L)
        box(s, x0 + 2, 34, x1 - 2, 53, WOOD_M, hi=WOOD_D, lo=WOOD_L)
    s.set(14, 33, YEL)
    s.set(17, 33, YEL)
    floor_shadow(s, 2, 29, 62)
    return s


def washstand():
    s = Spr(32, 32)
    block(s, 4, 27, 12, 5, 28, WD, (ST_L, MOON, ST_M))
    s.ellipse(14, 14, 7, 2.5, OL1)
    s.ellipse(14, 14, 6, 1.8, MOON)
    s.ellipse(14, 14, 4, 1.0, NB_L)
    # Krug
    s.rect(19, 3, 24, 13, OL1)
    s.rect(20, 4, 23, 12, MOON)
    vline(s, 23, 5, 12, ST_L)
    s.set(25, 6, OL1)
    s.set(25, 7, OL1)
    s.set(25, 8, OL1)
    s.set(19, 4, ST_L)
    drawer(s, 7, 20, 24, 25)
    legs(s, (5, 25), 28, 30, WD)
    return s


def cradle(f=0):
    s = Spr(32, 32)
    s.ellipse(16, 24, 13, 4, OL1)
    s.ellipse(16, 24, 12, 3, WOOD_D)
    s.rect(4, 10, 27, 22, OL1)
    s.rect(5, 11, 26, 21, WOOD_M)
    hline(s, 5, 26, 11, WOOD_L)
    s.rect(6, 12, 25, 15, CREAM)
    s.rect(6, 13, 20, 15, BLUE_L)
    hline(s, 6, 20, 13, MOON)
    for x in range(7, 26, 4):
        vline(s, x, 16, 21, WOOD_D)
    return s


# ====================================================================== Schmiede
def forge(f):
    s = Spr(64, 64)
    # Abzugshaube
    for y in range(0, 22):
        w = 10 + y
        for x in range(32 - w, 32 + w):
            row, v = divmod(y, 5)
            c = ST_M if v else ST_D
            if x > 32 + w - 4:
                c = dk(c)
            s.set(x, y, c)
    outline_obj(s)
    # Esse (gemauert)
    block(s, 6, 57, 24, 8, 61, (ST_M, ST_L, ST_D), (ST_D, ST_M, SV_D))
    s.rect(14, 26, 49, 32, OL1)
    s.rect(15, 27, 48, 31, OL2)
    # Kohlen + Glut (pulsiert)
    lv = [0, 1, 2, 1, 0, 1][f % 6]
    for x in range(15, 49):
        for y in range(28, 32):
            r = hsh(x, y, 5)
            c = OL2
            if r < 0.35 + lv * 0.1:
                c = GLOW
            if r < 0.15 + lv * 0.07:
                c = ORA
            if r < 0.05 + lv * 0.03:
                c = YEL
            s.set(x, y, c)
    fire(s, 20, 43, 27, 6 + lv, f, 6, 21)
    # Steine Front
    for y in range(34, 60):
        row, v = divmod(y - 34, 6)
        for x in range(7, 57):
            u = (x + row * 5) % 12
            if v == 5 or u == 0:
                s.set(x, y, ST_D)
    # Zange in der Glut
    for i in range(14):
        s.set(48 + i, 26 - i // 3, ST_D)
    return s


def anvil():
    s = Spr(32, 32)
    s.rect(4, 8, 27, 13, OL1)
    s.rect(5, 9, 26, 12, ST_M)
    hline(s, 5, 26, 9, MOON)
    hline(s, 5, 26, 12, ST_D)
    for i in range(4):
        s.set(1 + i, 10 + i // 2, ST_M)
    s.rect(11, 13, 20, 18, OL1)
    s.rect(12, 14, 19, 17, ST_D)
    s.rect(8, 18, 23, 28, OL1)
    s.rect(9, 19, 22, 27, WOOD_M)
    hline(s, 9, 22, 19, WOOD_L)
    vline(s, 22, 20, 27, WOOD_D)
    outline_obj(s)
    floor_shadow(s, 8, 23, 29)
    return s


def grindstone(f=0):
    s = Spr(32, 32)
    legs(s, (6, 24), 16, 29, WD)
    hline(s, 5, 26, 18, WOOD_D)
    s.ellipse(16, 14, 9, 9, OL1)
    s.ellipse(16, 14, 8, 8, ST_M)
    s.ellipse(15, 13, 5, 5, ST_L)
    s.ellipse(16, 14, 1.5, 1.5, WOOD_D)
    for i in range(6):
        s.set(25 + i // 2, 14 - i, WOOD_L)
    return s


def bellows():
    s = Spr(32, 32)
    for y in range(12, 26):
        w = 4 + (y - 12)
        hline(s, 4, 4 + w, y, WOOD_M if y % 3 else WOOD_D)
    s.rect(4, 12, 6, 27, WOOD_L)
    for y in range(14, 26, 3):
        hline(s, 5, 15 + (y - 12), y, SK_S)
    hline(s, 18, 28, 19, ST_D)
    hline(s, 18, 28, 20, ST_M)
    outline_obj(s)
    floor_shadow(s, 4, 28, 29)
    return s


# ====================================================================== Baeckerei
def bake_oven(f):
    s = Spr(64, 64)
    # Kuppel
    for y in range(4, 34):
        for x in range(2, 62):
            d = ((x + .5 - 32) / 29) ** 2 + ((y + .5 - 34) / 30) ** 2
            if d <= 1:
                row, v = divmod(y, 5)
                u = (x + row * 4) % 9
                c = SK_M if v else SK_S
                if u == 0:
                    c = SK_S
                if x < 20 and v:
                    c = SK_L if d > 0.8 else SK_M
                if x > 46:
                    c = dk(c)
                s.set(x, y, c)
    block(s, 2, 61, 32, 4, 61, (SK_S, SK_M, EARTH), (ST_M, ST_L, ST_D))
    # Ofenloch
    for y in range(18, 40):
        for x in range(18, 46):
            if ((x + .5 - 32) / 13) ** 2 + ((y + .5 - 40) / 21) ** 2 <= 1:
                s.set(x, y, OL1)
            if ((x + .5 - 32) / 12) ** 2 + ((y + .5 - 40) / 20) ** 2 <= 1:
                s.set(x, y, OL2)
    fire(s, 22, 41, 36, 9, f, 6, 33)
    # Brot im Ofen
    s.ellipse(28, 35, 3, 1.3, WOOD_L)
    s.ellipse(36, 35, 3, 1.3, WOOD_L)
    hline(s, 18, 45, 38, ST_L)
    # Holz darunter
    s.rect(14, 46, 49, 57, OL2)
    for row in range(2):
        for k in range(6):
            cx = 18 + k * 6 + row * 3
            if cx < 48:
                s.ellipse(cx, 55 - row * 5, 2.5, 2.3, WOOD_M)
                s.set(cx, 55 - row * 5, SAND)
    outline_obj(s)
    return s


def bread_rack():
    def fill(s, x0, x1, yb, r):
        for x in range(x0 + 1, x1 - 4, 6):
            if r % 2 == 0:
                s.ellipse(x + 2, yb - 2, 3, 2, WOOD_D)
                s.ellipse(x + 2, yb - 2.5, 2.5, 1.4, WOOD_L)
                s.set(x + 1, yb - 3, SAND)
            else:
                s.rect(x, yb - 5, x + 4, yb, WOOD_M)
                hline(s, x, x + 4, yb - 5, WOOD_L)
                s.set(x + 2, yb - 4, SAND)
    return shelf_unit(64, 64, 4, fill, WD, 3)


def counter(part, top=None, f=0):
    """Ladentheke 32x32: L | M | R; top = waage | kasse | glaeser | brot | flaschen | kerze"""
    s = Spr(32, 32)
    x0 = 1 if part == 'L' else 0
    x1 = 30 if part == 'R' else 31
    s.rect(x0, 10, x1, 30, OL1)
    s.rect(x0 + (1 if part == 'L' else 0), 11, x1 - (1 if part == 'R' else 0), 16, WOOD_L)
    hline(s, x0, x1, 11, SAND)
    hline(s, x0, x1, 17, OL1)
    s.rect(x0 + (1 if part == 'L' else 0), 18, x1 - (1 if part == 'R' else 0), 29, WOOD_M)
    for x in range(x0 + 2, x1, 8):
        box(s, x, 19, min(x + 6, x1 - 1), 28, WOOD_M, hi=WOOD_D, lo=WOOD_L)
    if part == 'L':
        vline(s, 2, 12, 29, WOOD_L)
    if part == 'R':
        vline(s, 29, 12, 29, WOOD_D)
    floor_shadow(s, x0, x1, 31)
    if top == 'waage':
        hline(s, 8, 23, 6, ST_D)
        vline(s, 15, 6, 12, ST_D)
        for x0_ in (6, 20):
            s.rect(x0_, 8, x0_ + 5, 9, YEL)
            hline(s, x0_, x0_ + 5, 10, ORA)
        s.rect(13, 12, 18, 13, ST_D)
    elif top == 'kasse':
        s.rect(9, 3, 22, 13, OL1)
        s.rect(10, 4, 21, 12, YEL)
        hline(s, 10, 21, 4, CREAM)
        for x in range(11, 21, 3):
            s.set(x, 7, OL2)
            s.set(x, 9, OL2)
        hline(s, 10, 21, 12, ORA)
    elif top == 'glaeser':
        jars(s, 5, 27, 13, 9, (FOR_M, RED_D, SAND, BLUE_D))
    elif top == 'brot':
        for x in (6, 15, 24):
            s.ellipse(x, 12, 4, 2.2, WOOD_D)
            s.ellipse(x, 11.5, 3.3, 1.5, WOOD_L)
            s.set(x - 1, 11, SAND)
    elif top == 'flaschen':
        for k, x in enumerate(range(6, 27, 4)):
            c = [FOR_M, BLUE_D, SK_S, FOR_D, RED_D, BLUE_L][k % 6]
            s.rect(x, 7, x + 2, 13, c)
            s.rect(x + 1, 4, x + 1, 6, c)
            s.set(x, 8, lt(c) if lt(c) != c else CREAM)
            hline(s, x, x + 2, 10, CREAM)
    elif top == 'kerze':
        candle(s, 15, 13, f, 5)
        s.ellipse(16, 14, 3, 1, ST_L)
    return s


# ====================================================================== Laden / Apotheke / Studierzimmer
def goods_shelf(kind):
    def fill(s, x0, x1, yb, r):
        if kind == 'waren':
            if r == 0:
                jars(s, x0, x1, yb, 41 + r)
            elif r == 1:
                for x in range(x0, x1 - 4, 7):
                    s.rect(x, yb - 6, x + 5, yb, [ST_M, RED_D, BLUE_D, FOR_M][(x // 7) % 4])
                    hline(s, x, x + 5, yb - 4, CREAM)
            elif r == 2:
                for x in range(x0, x1 - 6, 9):
                    s.rect(x, yb - 6, x + 7, yb, WOOD_L)
                    s.rect(x + 1, yb - 5, x + 6, yb - 1, SAND)
                    s.set(x + 3, yb - 3, RED_D)
            else:
                for x in range(x0, x1 - 5, 8):
                    sk = sack(SAND)
                    s.rect(x, yb - 7, x + 6, yb, SAND)
                    hline(s, x + 1, x + 5, yb - 8, WOOD_L)
                    vline(s, x + 6, yb - 7, yb, WOOD_L)
        elif kind == 'stoff':
            for x in range(x0, x1 - 3, 5):
                c = [ROSE, BLUE_L, LEAF, SAND, RED_D, SV_L, BLUE_D, CREAM][(x // 5 + r * 3) % 8]
                s.rect(x, yb - 7, x + 4, yb, c)
                vline(s, x + 4, yb - 7, yb, dk(c))
                hline(s, x, x + 4, yb - 7, lt(c) if lt(c) != c else CREAM)
        elif kind == 'apotheke':
            if r % 2 == 0:
                jars(s, x0, x1, yb, 51 + r, (FOR_M, BLUE_D, RED_D, SK_S, FOR_D))
            else:
                for x in range(x0, x1 - 3, 5):
                    c = [FOR_M, BLUE_D, SK_S][(x // 5) % 3]
                    s.rect(x + 1, yb - 8, x + 2, yb - 6, c)
                    s.rect(x, yb - 5, x + 3, yb, c)
                    s.set(x, yb - 4, CREAM)
        elif kind == 'buecher':
            books(s, x0, x1, yb, 8 + r % 2, 61 + r)
    return shelf_unit(64, 64, 4, fill, WDD if kind in ('buecher', 'apotheke') else WD, 7)


def apothecary_cabinet():
    s = Spr(64, 64)
    block(s, 1, 62, 2, 3, 61, WDD)
    for r in range(7):
        for c in range(6):
            x0 = 4 + c * 9
            y0 = 8 + r * 7
            s.rect(x0, y0, x0 + 8, y0 + 6, OL1)
            s.rect(x0 + 1, y0 + 1, x0 + 7, y0 + 5, WOOD_M)
            hline(s, x0 + 1, x0 + 7, y0 + 1, WOOD_L)
            s.rect(x0 + 3, y0 + 2, x0 + 5, y0 + 3, CREAM)
            s.set(x0 + 4, y0 + 4, YEL)
    floor_shadow(s, 1, 62, 62)
    return s


def mortar_table():
    def it(s):
        s.rect(9, 6, 16, 12, OL1)
        s.rect(10, 7, 15, 11, ST_L)
        hline(s, 10, 15, 7, MOON)
        for i in range(5):
            s.set(15 + i // 2, 6 - i, WOOD_L)
        for k, x in enumerate((20, 24)):
            s.rect(x, 7, x + 2, 12, [FOR_M, BLUE_D][k])
            s.set(x + 1, 6, WOOD_L)
    return table(32, None, it)


def distill(f):
    s = Spr(32, 64)
    # Tisch
    block(s, 2, 29, 40, 5, 48, WD)
    legs(s, (4, 26), 48, 61, WD)
    # Kolben mit Blasen
    s.ellipse(11, 34, 7, 7, OL1)
    s.ellipse(11, 34, 6, 6, FOR_M)
    s.ellipse(9, 32, 2, 2, GRASS_L)
    for i in range(3):
        t = ((i + f / 4.0) / 3.0) % 1.0
        s.set(10 + i * 2, int(38 - t * 9), LEAF)
    s.rect(10, 20, 12, 27, OL1)
    s.set(11, 21, ST_L)
    # Rohr zur Vorlage
    for i in range(14):
        s.set(12 + i, 20 + i // 2, ST_D)
    s.rect(22, 28, 28, 39, OL1)
    s.rect(23, 29, 27, 38, BLUE_D)
    hline(s, 23, 27, 35 - (f % 2), BLUE_L)
    # Flamme darunter
    candle(s, 10, 42, f, 1)
    return s


def desk(f):
    s = Spr(64, 32)
    block(s, 2, 61, 6, 6, 28, WDD)
    for k in range(2):
        drawer(s, 4 + k * 40, 15, 19 + k * 40, 25, WDD)
    s.rect(22, 15, 41, 27, OL2)
    # Papier, Feder, Kerze, Buch
    s.rect(18, 7, 30, 11, CREAM)
    hline(s, 19, 28, 9, ST_L)
    for i in range(5):
        s.set(31 + i, 10 - i, MOON)
    s.rect(42, 7, 52, 11, RED_D)
    hline(s, 42, 52, 7, ROSE)
    candle(s, 8, 10, f, 5)
    return s


def globe():
    s = Spr(32, 32)
    s.ellipse(16, 12, 8, 8, OL1)
    s.ellipse(16, 12, 7, 7, BLUE_D)
    for (x, y, w) in ((13, 8, 3), (18, 12, 4), (12, 14, 2)):
        hline(s, x, x + w, y, FOR_M)
        hline(s, x + 1, x + w - 1, y + 1, GRASS)
    s.set(12, 8, BLUE_L)
    for a in range(-60, 240, 12):
        s.set(16 + int(round(9.5 * math.cos(math.radians(a)))), 12 + int(round(9.5 * math.sin(math.radians(a)))), YEL)
    vline(s, 16, 21, 27, WOOD_D)
    s.rect(11, 27, 21, 29, OL1)
    hline(s, 12, 20, 28, WOOD_M)
    return s


def map_table():
    def it(s):
        s.rect(6, 7, 57, 14, SAND)
        for x in range(8, 56, 5):
            s.set(x, 9 + x % 3, WOOD_M)
        for i in range(12):
            s.set(16 + i * 2, 11 - i % 3, RED_D)
        s.ellipse(44, 10, 3, 2, BLUE_L)
    return table(64, None, it)


def telescope():
    s = Spr(32, 64)
    for (ax, ay, bx, by) in ((16, 40, 6, 62), (16, 40, 26, 62), (16, 40, 16, 62)):
        n = max(abs(bx - ax), abs(by - ay))
        for i in range(n + 1):
            s.set(ax + (bx - ax) * i // n, ay + (by - ay) * i // n, WOOD_D)
    for i in range(26):
        for k in range(4):
            c = [YEL, ORA, GLOW, RED_D][k]
            s.set(5 + i, 40 - i + k - 2, c)
    outline_obj(s)
    return s


# ====================================================================== Kapelle
def pew(w=64):
    s = Spr(w, 32)
    s.rect(1, 4, w - 2, 17, OL1)
    s.rect(2, 5, w - 3, 16, WOOD_M)
    hline(s, 2, w - 3, 5, WOOD_L)
    for x in range(8, w - 6, 8):
        vline(s, x, 7, 15, WOOD_D)
    block(s, 1, w - 2, 16, 3, 22, WD)
    for x0 in (1, w - 5):
        s.rect(x0, 2, x0 + 3, 28, OL1)
        s.rect(x0 + 1, 3, x0 + 2, 27, WOOD_D)
        s.set(x0 + 1, 3, WOOD_L)
    floor_shadow(s, 1, w - 2, 29)
    return s


def altar(f):
    s = Spr(64, 32)
    block(s, 4, 59, 10, 4, 29, (ST_L, MOON, ST_M), (CREAM, CREAM, SAND))
    # Tuch
    for y in range(15, 26):
        for x in range(20, 44):
            c = RED_D if (x - 20) % 8 else SK_S
            if y == 25 and x % 2:
                c = YEL
            s.set(x, y, c)
    for x in range(29, 35):
        s.set(x, 18, YEL)
    vline(s, 31, 16, 22, YEL)
    vline(s, 32, 16, 22, YEL)
    for k, x in enumerate((9, 15, 47, 53)):
        candle(s, x, 12, (f + k) % 4, 6)
    s.rect(28, 3, 35, 12, OL1)
    s.rect(29, 4, 34, 11, TAL_D)
    s.set(31, 6, TAL_H)
    s.set(32, 7, TAL)
    return s


def candelabra(f):
    s = Spr(32, 64)
    vline(s, 15, 18, 60, OL1)
    vline(s, 16, 18, 60, YEL)
    vline(s, 17, 18, 60, OL1)
    s.rect(9, 59, 23, 62, OL1)
    hline(s, 10, 22, 60, YEL)
    hline(s, 10, 22, 61, ORA)
    for i in range(6):
        s.set(9 + i, 24 - i // 2, YEL)
        s.set(22 - i, 24 - i // 2, YEL)
    for k, x in enumerate((7, 15, 23)):
        s.rect(x - 1, 19 + (k != 1) * 2, x + 2, 20 + (k != 1) * 2, ORA)
        candle(s, x, 18 + (k != 1) * 2, (f + k) % 4, 5)
    return s


def talisman_shrine(f):
    s = Spr(32, 64)
    # Saeule
    block(s, 7, 24, 36, 4, 61, (ST_M, ST_L, ST_D), (ST_L, MOON, ST_M))
    hline(s, 8, 23, 50, ST_D)
    # Kristall schwebt (auf/ab 1px)
    dy = [0, -1, -1, 0, 1, 1][f % 6]
    cy = 22 + dy
    for y in range(cy - 10, cy + 10):
        w = min(y - (cy - 11), (cy + 10) - y, 5)
        for x in range(16 - w, 16 + w):
            c = TAL if x < 16 else TAL_D
            if x == 16 - w and y < cy:
                c = TAL_H
            s.set(x, y, c)
    sh = Spr(32, 64)
    outline_obj(s)
    # Schimmer
    lv = [0, 1, 2, 2, 1, 0][f % 6]
    if lv:
        s.set(13, cy - 4, TAL_H)
        s.set(14, cy - 6, TAL_H)
    if lv == 2:
        for (x, y) in ((9, cy - 8), (23, cy - 2), (10, cy + 6), (22, cy + 8)):
            s.set(x, y, TAL_H)
    for x in range(10, 22, 2):
        s.set(x, 35, TAL if (x // 2 + f) % 3 == 0 else TAL_D)
    return s


# ====================================================================== Stall / Bauernhaus
def hay_pile():
    s = Spr(64, 32)
    for y in range(4, 30):
        for x in range(2, 62):
            d = ((x + .5 - 32) / 30) ** 2 + ((y + .5 - 30) / 25) ** 2
            if d <= 1:
                r = hsh(x, y, 4)
                c = SAND if r < 0.45 else (WOOD_L if r < 0.85 else WOOD_M)
                if (x + y * 2) % 7 == 0:
                    c = WOOD_M
                if y < 10 and r < 0.6:
                    c = CREAM if r < 0.1 else SAND
                if x > 50:
                    c = dk(c)
                s.set(x, y, c)
    outline_obj(s)
    return s


def trough():
    s = Spr(64, 32)
    block(s, 2, 61, 12, 6, 27, WD)
    s.rect(5, 14, 58, 17, OL2)
    for x in range(6, 58):
        if hsh(x, 1, 4) < 0.7:
            s.set(x, 14 + int(hsh(x, 2, 4) * 2), SAND if x % 3 else WOOD_L)
    legs(s, (4, 57), 27, 30, WD)
    return s


def butter_churn():
    s = Spr(32, 32)
    for y in range(10, 29):
        w = 6 + (y - 10) // 6
        for x in range(16 - w, 16 + w):
            u = (x - 10) % 4
            s.set(x, y, [WOOD_L, WOOD_M, WOOD_M, WOOD_D][u] if x < 16 + w - 2 else WOOD_D)
    for y in (13, 25):
        hline(s, 9, 22, y, ST_D)
    vline(s, 16, 1, 10, WOOD_L)
    vline(s, 17, 1, 10, WOOD_D)
    outline_obj(s)
    floor_shadow(s, 8, 24, 30)
    return s


def spinning_wheel(f=0):
    s = Spr(32, 32)
    s.ellipse(18, 12, 9, 9, OL1)
    s.ellipse(18, 12, 8, 8, WOOD_M)
    s.ellipse(18, 12, 6.5, 6.5, (0, 0, 0, 0))
    for a in range(0, 360, 45):
        a2 = a + f * 11
        for r in range(1, 7):
            s.set(18 + int(round(r * math.cos(math.radians(a2)))), 12 + int(round(r * math.sin(math.radians(a2)))), WOOD_L)
    s.ellipse(18, 12, 1.5, 1.5, WOOD_D)
    legs(s, (6, 24), 20, 29, WD)
    hline(s, 4, 27, 21, WOOD_D)
    s.rect(4, 14, 8, 20, CREAM)
    return s


# ====================================================================== Schneiderei / Fischer
def dress_form():
    s = Spr(32, 64)
    vline(s, 15, 40, 58, WOOD_D)
    vline(s, 16, 40, 58, WOOD_M)
    s.rect(9, 58, 22, 60, OL1)
    hline(s, 10, 21, 59, WOOD_D)
    for y in range(10, 42):
        w = 8 if y < 22 else (5 if y < 28 else 5 + (y - 28) // 3)
        for x in range(16 - w, 16 + w):
            c = ROSE if x < 16 + w - 3 else RED_D
            if x < 16 - w + 2:
                c = CREAM if y < 20 else ROSE
            s.set(x, y, c)
    s.rect(14, 5, 17, 9, WOOD_D)
    for y in range(12, 40, 4):
        s.set(16, y, YEL)
    outline_obj(s)
    return s


def sewing_table():
    def it(s):
        # Naehmaschine
        s.rect(14, 1, 34, 4, OL1)
        s.rect(15, 2, 33, 3, OL2)
        s.rect(30, 4, 34, 12, OL1)
        s.rect(31, 5, 33, 11, OL2)
        s.rect(14, 4, 17, 9, OL1)
        s.set(15, 2, YEL)
        s.rect(40, 7, 50, 12, ROSE)
        hline(s, 40, 50, 7, CREAM)
        for x in (8, 11):
            s.rect(x, 7, x + 2, 11, [BLUE_L, YEL][x % 2])
    return table(64, None, it)


def cloth_bolts():
    s = Spr(32, 32)
    for k, (x, y, c) in enumerate(((4, 16, ROSE), (14, 16, BLUE_L), (9, 8, LEAF), (20, 9, SAND))):
        cl = (c, lt(c) if lt(c) != c else CREAM, dk(c))
        s.rect(x, y, x + 9, y + 12, cl[0])
        hline(s, x, x + 9, y, cl[1])
        vline(s, x + 9, y, y + 12, cl[2])
        s.ellipse(x + 2, y + 6, 1.5, 5, cl[2])
    outline_obj(s)
    return s


def standing_mirror():
    s = Spr(32, 64)
    s.ellipse(16, 24, 9, 18, OL1)
    s.ellipse(16, 24, 8, 17, WOOD_M)
    s.ellipse(16, 24, 6, 15, NB_L)
    for i in range(10):
        s.set(12 + i // 2, 14 + i, MOON)
    legs(s, (8, 22), 42, 61, WD)
    hline(s, 6, 25, 61, OL1)
    return s


def fish_barrel():
    return barrel('fisch')


def eel_trap():
    s = Spr(32, 32)
    for y in range(10, 26):
        for x in range(4, 29):
            d = ((x + .5 - 16) / 12) ** 2 + ((y + .5 - 18) / 8) ** 2
            if d <= 1 and ((x % 4 == 0) or (y % 4 == 0)):
                s.set(x, y, WOOD_L if x < 20 else WOOD_M)
    s.ellipse(27, 18, 2, 5, WOOD_D)
    outline_obj(s)
    return s


# ====================================================================== Kram (Boden)
def crate_stack():
    s = Spr(32, 32)
    for (x0, y0, x1, y1) in ((3, 14, 18, 29), (14, 17, 29, 29), (7, 3, 22, 15)):
        block(s, x0, x1, y0, 2, y1, WD)
        for i in range(x1 - x0 - 3):
            s.set(x0 + 2 + i, y0 + 4 + i * (y1 - y0 - 6) // max(1, x1 - x0 - 3), WOOD_D)
    return s


def log_basket():
    s = Spr(32, 32)
    for k in range(5):
        cx = 9 + k * 3.5
        s.ellipse(cx, 13 - (k % 2) * 2, 2.5, 2.5, WOOD_M)
        s.set(int(cx), 13 - (k % 2) * 2, SAND)
    block(s, 5, 26, 14, 2, 28, (WOOD_L, SAND, WOOD_M))
    for x in range(7, 25, 3):
        vline(s, x, 18, 26, WOOD_M)
    return s


# ====================================================================== Tuerrahmen (liegen auf den Mauerkronen neben einer Tueroeffnung)
def _door_leaf_side(s, x0, x1, y0, y1):
    """offenes Tuerblatt, an die Mauer geklappt (Bretter, Beschlaege, Klinke)."""
    s.rect(x0, y0, x1, y1, OL1)
    for x in range(x0 + 1, x1):
        for y in range(y0 + 1, y1):
            u = (x - x0 - 1) % 4
            s.set(x, y, [WOOD_L, WOOD_M, WOOD_M, WOOD_D][u])
    for yb in (y0 + 4, y1 - 5):
        hline(s, x0 + 1, x1 - 1, yb, ST_D)
        s.set(x0 + 1, yb, ST_L)
    s.set(x1 - 2, (y0 + y1) // 2, YEL)


def door_frame(kind):
    """kind: seite_oben | seite_unten (Krone ueber/unter einer Seitentuer), unten_links | unten_rechts (Ausgang unten)."""
    s = Spr(32, 32)
    if kind == 'seite_oben':
        # Tuersturz an der Unterkante
        s.rect(0, 25, 31, 31, OL1)
        s.rect(1, 26, 30, 30, WOOD_M)
        hline(s, 1, 30, 26, WOOD_L)
        hline(s, 1, 30, 30, WOOD_D)
        for x in (3, 28):
            s.set(x, 28, ST_L)
    elif kind == 'seite_unten':
        s.rect(0, 0, 31, 6, OL1)
        s.rect(1, 1, 30, 5, WOOD_M)
        hline(s, 1, 30, 1, WOOD_L)
        hline(s, 1, 30, 5, WOOD_D)
        for x in (3, 28):
            s.set(x, 3, ST_L)
    else:
        right = kind == 'unten_links'          # Pfosten an der Seite zur Oeffnung
        px0 = 25 if right else 0
        s.rect(px0, 0, px0 + 6, 31, OL1)
        s.rect(px0 + 1, 0, px0 + 5, 31, WOOD_M)
        vline(s, px0 + 1, 0, 31, WOOD_L)
        vline(s, px0 + 5, 0, 31, WOOD_D)
        for y in (6, 24):
            s.set(px0 + 3, y, ST_L)
    return s


def klapptuer():
    """Klapptuer von oben gesehen: Brett 32 lang, 8 dick, Scharnier oben (Pivot oben Mitte).
    Zu = haengt senkrecht im Durchgang, offen = um 90 Grad in den Raum geklappt (Drehung im Spiel)."""
    s = Spr(32, 32)
    x0, x1 = 12, 19
    s.rect(x0, 0, x1, 31, OL1)
    for y in range(1, 31):
        for x in range(x0 + 1, x1):
            u = (x - x0 - 1) % 3
            c = [WOOD_L, WOOD_M, WOOD_D][u]
            if y % 10 == 0:
                c = WOOD_D
            s.set(x, y, c)
    vline(s, x0 + 1, 1, 30, WOOD_L)
    for y in (3, 4, 26, 27):                 # Beschlaege
        hline(s, x0 + 1, x1 - 1, y, ST_D)
    s.set(x0 + 1, 3, ST_L)
    s.set(x0 + 1, 26, ST_L)
    s.rect(14, 0, 17, 1, ST_M)               # Scharnier
    s.set(x1 - 1, 19, YEL)                   # Klinke
    s.set(x1 - 1, 20, ORA)
    return s


# ====================================================================== Register
def register(R):
    M, Wd, B = 'innen_moebel', 'innen_wand', 'innen_boden'
    # Wohnen
    R.add_anim('Kamin_Stein', [fireplace(f) for f in range(6)], 110, M, fuss=1)
    for c in ('gruen', 'rot', 'blau'):
        R.add('Sofa_' + c.capitalize(), sofa(c), M)
        R.add('Sessel_' + c.capitalize(), armchair(c), M)
    R.add('Tisch_Rund', table(32, round_=True), M)
    R.add('Tisch_Rund_Decke', table(32, 'sand', round_=True), M)
    R.add('Tisch_Lang', table(64), M)
    R.add('Tisch_Lang_Decke', table(64, 'rot'), M)
    R.add('Stuhl_Vorne', chair('vorne'), M)
    R.add('Stuhl_Hinten', chair('hinten'), M)
    R.add('Buecherregal_Schmal', bookcase(32), M)
    R.add('Buecherwand', bookcase(64), M)
    R.add_anim('Standuhr', [grandfather_clock(f) for f in range(4)], 500, M)
    R.add('Kommode', dresser(64), M)
    R.add('Topfpflanze', potted_plant(False), M)
    R.add('Topfpflanze_Gross', potted_plant(True), M)
    R.add('Truhe_Zu', chest(False), M)
    R.add('Truhe_Offen', chest(True), M)
    # Teppiche (Boden, begehbar)
    for c in ('rot', 'blau', 'gruen'):
        R.add('Teppich_%s_Gross' % c.capitalize(), rug(96, 64, c, 'raute'), B, fuss=0, solid=False)
        R.add('Teppich_%s' % c.capitalize(), rug(64, 32, c, 'streifen'), B, fuss=0, solid=False)
        R.add('Teppich_%s_Rund' % c.capitalize(), rug(64, 64, c, 'rund'), B, fuss=0, solid=False)
        R.add('Laeufer_%s' % c.capitalize(), runner(c), B, fuss=0, solid=False)
    # Kueche
    R.add_anim('Herd_Eisen', [iron_stove(f) for f in range(6)], 120, M)
    R.add('Spuelstein', sink(), M)
    R.add('Kuechenschrank', kitchen_cabinet(), M)
    R.add('Arbeitstisch_Brot', worktable_bread(), M)
    for k in ('wasser', 'aepfel', 'kohle', 'korn'):
        R.add('Fass_' + k.capitalize(), barrel(k), M)
    R.add('Sack_Mehl', sack(SAND), M)
    R.add('Sack_Kartoffeln', sack(WOOD_L), M)
    R.add('Sack_Korn', sack(SAND, RED_D), M)
    # Schlafen
    for c in ('rot', 'blau', 'gruen'):
        R.add('Bett_' + c.capitalize(), bed(c, 32), M, fuss=2)
    R.add('Bett_Doppel_Rot', bed('rot', 64), M, fuss=2)
    R.add('Bett_Doppel_Blau', bed('blau', 64), M, fuss=2)
    R.add_anim('Nachttisch_Kerze', [nightstand(f) for f in range(4)], 180, M)
    R.add('Kleiderschrank', wardrobe(), M)
    R.add('Waschtisch', washstand(), M)
    R.add('Wiege', cradle(), M)
    # Schmiede
    R.add_anim('Esse', [forge(f) for f in range(6)], 120, M)
    R.add('Amboss', anvil(), M)
    R.add('Schleifstein', grindstone(), M)
    R.add('Blasebalg', bellows(), M)
    # Baeckerei / Laden
    R.add_anim('Backofen', [bake_oven(f) for f in range(6)], 120, M)
    R.add('Brotregal', bread_rack(), M)
    for p in ('L', 'M', 'R'):
        R.add('Theke_' + p, counter(p), M)
    for t in ('waage', 'kasse', 'glaeser', 'brot', 'flaschen'):
        R.add('Theke_M_' + t.capitalize(), counter('M', t), M)
    R.add_anim('Theke_M_Kerze', [counter('M', 'kerze', f) for f in range(4)], 180, M)
    R.add('Warenregal', goods_shelf('waren'), M)
    R.add('Stoffregal', goods_shelf('stoff'), M)
    R.add('Kistenstapel', crate_stack(), M)
    # Apotheke / Studierzimmer
    R.add('Flaschenregal', goods_shelf('apotheke'), M)
    R.add('Apothekerschrank', apothecary_cabinet(), M)
    R.add('Moerser_Tisch', mortar_table(), M)
    R.add_anim('Destille', [distill(f) for f in range(4)], 200, M)
    R.add_anim('Schreibtisch_Kerze', [desk(f) for f in range(4)], 180, M)
    R.add('Globus', globe(), M)
    R.add('Kartentisch', map_table(), M)
    R.add('Fernrohr', telescope(), M)
    # Kapelle
    R.add('Kirchenbank', pew(64), M)
    R.add('Kirchenbank_Kurz', pew(32), M)
    R.add_anim('Altar', [altar(f) for f in range(4)], 180, M)
    R.add_anim('Kerzenstaender', [candelabra(f) for f in range(4)], 180, M)
    R.add_anim('Talisman_Schrein', [talisman_shrine(f) for f in range(6)], 200, M)
    # Stall / Bauernhaus
    R.add('Heuhaufen', hay_pile(), M)
    R.add('Futtertrog', trough(), M)
    R.add('Butterfass', butter_churn(), M)
    R.add_anim('Spinnrad', [spinning_wheel(f) for f in range(4)], 160, M)
    R.add('Holzkorb', log_basket(), M)
    # Schneiderei / Fischer
    R.add('Schneiderpuppe', dress_form(), M)
    R.add('Naehtisch', sewing_table(), M)
    R.add('Stoffballen', cloth_bolts(), M)
    R.add('Standspiegel', standing_mirror(), M)
    R.add('Fass_Fisch', fish_barrel(), M)
    R.add('Reuse', eel_trap(), M)
    # Wand
    for k in ('toepfe', 'geschirr', 'werkzeug', 'garn', 'netz'):
        R.add('Wandbrett_' + k.capitalize(), wall_rack(k), Wd, fuss=0, solid=False)
    for k in ('bild_landschaft', 'bild_portrait', 'spiegel', 'kraeuter', 'pfannen', 'ruder', 'hufeisen', 'kranz'):
        R.add('Wand_' + ''.join(p.capitalize() for p in k.split('_')), wall_small(k), Wd, fuss=0, solid=False)
    R.add_anim('Wand_Kerzenleuchter', [wall_small('kerzenleuchter', f) for f in range(4)], 180, Wd, fuss=0, solid=False)
    R.add_anim('Wand_Talisman', [wall_small('talisman', f) for f in range(4)], 260, Wd, fuss=0, solid=False)
    R.add_anim('Wand_Uhr', [wall_small('uhr', f) for f in range(4)], 500, Wd, fuss=0, solid=False)
    for k in ('nacht', 'tag', 'vorhang'):
        R.add('Fenster_Innen_' + k.capitalize(), inner_window(k), Wd, fuss=0, solid=False)
    R.add_anim('Fenster_Innen_Kerze', [inner_window('licht', f) for f in range(4)], 180, Wd, fuss=0, solid=False)
    R.add('Tuer_Innen_Zu', inner_door('zu'), Wd, fuss=0, solid=False)
    for k in ('seite_oben', 'seite_unten', 'unten_links', 'unten_rechts'):
        R.add('Tuerrahmen_' + ''.join(p.capitalize() for p in k.split('_')), door_frame(k), 'innen_rahmen', fuss=0, solid=False)
    R.add('Klapptuer', klapptuer(), 'innen_tuer', fuss=0, solid=True)
    R.add('Tuer_Innen_Offen', inner_door('offen'), Wd, fuss=0, solid=False)
