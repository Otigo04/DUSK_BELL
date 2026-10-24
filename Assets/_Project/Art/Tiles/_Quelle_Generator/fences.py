"""Zaun-/Mauer-/Hecken-Autotile (Kanten-Set N1 E2 S4 W8, wie die anderen Autotiles)."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
from nwlib import *

N, E, S, W = 1, 2, 4, 8
SH = G_MD


def wood(ramp):
    return ramp


STY = {
    'holz':   dict(c=[BROWN[1], BROWN[2], BROWN[3], BROWN[4], BROWN[5]]),
    'dunkel': dict(c=[BROWN[0], BROWN[1], BROWN[2], BROWN[3], BROWN[4]]),
    'weiss':  dict(c=[STONE[2], STONE[3], STONE[4], STONE[5], CREAM]),
}


def post(sp, x0, top, bot, c):
    for y in range(top, bot + 1):
        sp.set(x0, y, c[3])
        sp.set(x0 + 1, y, c[2])
        sp.set(x0 + 2, y, c[2])
        sp.set(x0 + 3, y, c[1])
    sp.rect(x0, top, x0 + 3, top, c[4])      # Kappe hell
    sp.set(x0 + 3, top, c[2])
    sp.set(x0, top + 1, c[4])


def hrail(sp, x0, x1, y, c, seed=0):
    for x in range(x0, x1 + 1):
        sp.set(x, y, c[3])
        sp.set(x, y + 1, c[2])
        sp.set(x, y + 2, c[1])
        if hsh(x, y, seed) < 0.06:
            sp.set(x, y + 1, c[1])          # Astloch / Maserung
        if hsh(x, y, seed + 1) < 0.05:
            sp.set(x, y, c[4])


def vrail(sp, y0, y1, x, c, seed=0):
    for y in range(y0, y1 + 1):
        sp.set(x, y, c[3])
        sp.set(x + 1, y, c[2])
        sp.set(x + 2, y, c[1])
        if hsh(x, y, seed + 3) < 0.06:
            sp.set(x + 1, y, c[1])


def fence_wood(mask, style='holz', var=0):
    c = STY[style]['c']
    sp = Spr(32, 32)
    px = 14
    # Rails hinten (N) -> Pfosten -> Rails seitlich -> vorne (S)
    if mask & N:
        vrail(sp, 0, 14, 15, c, var)
    if mask & W:
        hrail(sp, 0, 15, 11, c, var)
        hrail(sp, 0, 15, 18, c, var + 7)
    if mask & E:
        hrail(sp, 16, 31, 11, c, var)
        hrail(sp, 16, 31, 18, c, var + 7)
    post(sp, px, 7, 27, c)
    if mask & S:
        vrail(sp, 16, 31, 15, c, var)
    # Bodenschatten
    base = Spr(32, 32)
    for x in range(12, 20):
        base.set(x, 28, SH)
    if mask & W:
        for x in range(0, 12):
            if x % 2 == 0:
                base.set(x, 24, SH)
    if mask & E:
        for x in range(20, 32):
            if x % 2 == 1:
                base.set(x, 24, SH)
    sp.outline(OUT)
    out = Spr(32, 32)
    out.paste(base, 0, 0)
    out.paste(sp, 0, 0)
    return out


def fence_picket(mask, style='weiss', var=0):
    """Lattenzaun: senkrechte Latten, Querbalken hinten, Pfosten mit Kugel."""
    c = STY[style]['c']
    sp = Spr(32, 32)
    # Querbalken
    def pickets(x0, x1):
        for x in range(x0, x1 + 1):
            if (x - x0) % 4 in (0, 1, 2):
                col = c[3] if (x - x0) % 4 == 0 else c[2]
                top = 11 + (1 if (x // 4 + var) % 3 == 0 else 0)
                for y in range(top, 27):
                    sp.set(x, y, col if (x - x0) % 4 != 2 else c[1])
                sp.set(x, top, c[4])
    if mask & W:
        pickets(0, 13)
    if mask & E:
        pickets(18, 31)
    if mask & N:
        vrail(sp, 0, 12, 15, c, var)
    if mask & W:
        hrail(sp, 0, 13, 14, c, var)
        hrail(sp, 0, 13, 21, c, var + 4)
    if mask & E:
        hrail(sp, 18, 31, 14, c, var)
        hrail(sp, 18, 31, 21, c, var + 4)
    post(sp, 14, 7, 27, c)
    sp.set(15, 5, c[4]); sp.set(16, 5, c[3]); sp.set(15, 6, c[3]); sp.set(16, 6, c[2])  # Knauf
    if mask & S:
        vrail(sp, 16, 31, 15, c, var)
    base = Spr(32, 32)
    for x in range(12, 20):
        base.set(x, 28, SH)
    sp.outline(OUT)
    out = Spr(32, 32)
    out.paste(base, 0, 0)
    out.paste(sp, 0, 0)
    return out


def wall_stone(mask, var=0):
    """niedrige Steinmauer (Trockenmauer) mit Deckplatte."""
    sp = Spr(32, 32)
    c = STONE
    def seg(x0, x1, y0=12, y1=26):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                row = (y - y0) // 5
                off = 4 if row % 2 else 0
                bx = (x + off) % 8
                by = (y - y0) % 5
                if by == 4 or bx == 7:
                    col = c[0]
                else:
                    h = hsh((x + off) // 8, row, 600 + var)
                    base = 3 if h < 0.5 else (2 if h < 0.8 else 4)
                    if by == 0:
                        base += 1
                    if bx == 6 or by == 3:
                        base -= 1
                    col = c[max(1, min(5, base))]
                sp.set(x, y, col)
        # Deckplatte
        for x in range(x0, x1 + 1):
            sp.set(x, y0 - 2, c[5])
            sp.set(x, y0 - 1, c[4])
            sp.set(x, y0, c[3])
    x0 = 10 if not (mask & W) else 0
    x1 = 21 if not (mask & E) else 31
    if mask & N:
        for y in range(0, 11):
            for x in range(10, 22):
                col = c[4]
                if y % 6 == 5:
                    col = c[2]
                if x == 10: col = c[5]
                if x >= 20: col = c[3]
                sp.set(x, y, col)
    seg(x0, x1)
    if mask & S:
        for y in range(27, 32):
            for x in range(10, 22):
                col = c[4]
                if y % 6 == 1: col = c[2]
                if x == 10: col = c[5]
                if x >= 20: col = c[3]
                sp.set(x, y, col)
    # Moos
    for y in range(32):
        for x in range(32):
            if sp.solid(x, y) and sp.get(x, y) != c[0] and y < 15 and hsh(x, y, 650 + var) < 0.10:
                sp.set(x, y, G_BASE)
    sp.outline(OUT)
    base = Spr(32, 32)
    for x in range(x0, x1 + 1):
        if x % 2 == 0:
            base.set(x, 28, SH)
    out = Spr(32, 32)
    out.paste(base, 0, 0)
    out.paste(sp, 0, 0)
    return out


def hedge(mask, var=0):
    """Heckenband: Klumpen in der Mitte, Arme in Richtung der Nachbarn (organisch schattiert)."""
    m = set()
    cx, cy = 15.5, 16.5
    for y in range(32):
        for x in range(32):
            if ((x + .5 - 16) / 11.0) ** 2 + ((y + .5 - 17) / 11.0) ** 2 <= 1.0:
                m.add((x, y))
    def arm(horiz, neg):
        for t in range(0, 16):
            tt = t if neg else 31 - t
            w = 1.3 * noise1(tt * 0.5, var * 3 + (1 if horiz else 2) + (5 if neg else 0))
            w *= min(1.0, (tt if neg else 31 - tt) / 6.0)
            lo = int(round(6 + w))
            hi = int(round(26 + w * 0.8))
            for u in range(lo, hi + 1):
                m.add((tt, u) if horiz else (u, tt))
    if mask & W: arm(True, True)
    if mask & E: arm(True, False)
    if mask & N: arm(False, True)
    if mask & S: arm(False, False)
    sp = Spr(32, 32)
    shade_mask(sp, m, [GREEN[0], GREEN[1], GREEN[2], GREEN[3], GREEN[4], GREEN[5]], seed=var + 40, base=3, clump=2)
    sp.outline(OUT)
    return sp
