"""Ilhans Bar - INNEN. Erzeugt Tileset_Bar_Innen.png + Bar_Innen_Vorschau.png.
Ansicht 3/4 von vorne wie Tileset_Interieur. Licht oben links warm, Schatten kuehl-violett."""
from bar_lib import *
from bar_aussen import lantern, PRICE_L, PRICE_R, sign_main


# ============================================================ BODEN (32x32, nahtlos)
def floor_planks(kind='dunkel'):
    s = Spr(32, 32)
    for y in range(32):
        r, v = divmod(y, 8)
        for x in range(32):
            xo = (x + (r * 13) % 32) % 32
            c = WOOD_D
            if v == 0:
                c = EARTH
            elif v == 1:
                c = WOOD_M
            elif v == 7:
                c = EARTH if False else WOOD_D
            if xo in (0, 1) and v > 0:
                c = EARTH
            f = hsh(x, y, 11)
            if v not in (0, 1) and xo > 1:
                if f < 0.035:
                    c = EARTH
                elif f > 0.97:
                    c = WOOD_M
            if kind == 'abgewetzt':
                w = hsh(x // 3, y // 3, 5)
                if v not in (0,) and w > 0.72:
                    c = WOOD_M if c == WOOD_D else c
                if v not in (0,) and w < 0.14 and xo > 1:
                    c = EARTH
            s.set(x, y, c)
    return s


def floor_sawdust():
    s = floor_planks('dunkel')
    for y in range(32):
        for x in range(32):
            f = hsh(x, y, 21)
            if f < 0.10:
                s.set(x, y, SAND)
            elif f < 0.14:
                s.set(x, y, WOOD_L)
    return s


def floor_stone(checker=False):
    s = Spr(32, 32)
    for y in range(32):
        for x in range(32):
            tx, ty = x // 16, y // 16
            base = ST_M
            if checker:
                base = ST_M if (tx + ty) % 2 == 0 else ST_D
            else:
                base = ST_M if (tx + ty) % 2 == 0 else ST_L if False else ST_M
            u, v = x % 16, y % 16
            c = base
            if v == 0 or u == 0:
                c = OL2
            elif v == 1 or u == 1:
                c = ST_L if not checker or base == ST_M else ST_M
            elif hsh(x, y, 31) < 0.07:
                c = ST_D if base != ST_D else ST_M
            s.set(x, y, c)
    return s


def floor_vertical():
    s = Spr(32, 32)
    for y in range(32):
        for x in range(32):
            u = x % 8
            v = (y + (x // 8) * 9) % 32
            c = WOOD_D
            if u == 0:
                c = EARTH
            elif u == 1:
                c = WOOD_M
            f = hsh(x, y, 41)
            if u > 1 and f < 0.05:
                c = EARTH
            if v == 0:
                c = EARTH
            s.set(x, y, c)
    return s


def runner():
    s = Spr(32, 32)
    for y in range(32):
        for x in range(32):
            s.set(x, y, RED_D)
    s.rect(0, 0, 31, 0, OL1); s.rect(0, 31, 31, 31, OL1)
    s.rect(0, 0, 31, 2, SV_D); s.rect(0, 29, 31, 31, SV_D)
    s.rect(0, 1, 31, 1, YEL); s.rect(0, 30, 31, 30, YEL)
    for x in range(4, 32, 8):
        s.rect(x - 1, 14, x + 1, 14, ROSE); s.rect(x, 13, x, 15, ROSE); s.set(x, 14, YEL)
    return s


def doormat():
    s = Spr(32, 32)
    s.rect(2, 8, 29, 23, OL1)
    s.rect(3, 9, 28, 22, WOOD_M)
    for y in range(9, 23):
        for x in range(3, 29):
            if (x + y) % 3 == 0:
                s.set(x, y, WOOD_L)
            elif hsh(x, y, 3) < 0.25:
                s.set(x, y, WOOD_D)
    s.rect(5, 11, 26, 20, OL1) if False else None
    draw_text(s, 'BAR', 11, 13, CREAM, '3x5', 1, 1)
    return s


def shade_overlay(side):
    s = Spr(32, 32)
    for y in range(32):
        for x in range(32):
            d = y if side == 'T' else (x if side == 'L' else 31 - x)
            lim = (1.0, 0.75, 0.5, 0.25, 0.12)
            if d < 5:
                dens = lim[d]
                b = [[1, 0], [0, 1]]
                on = (x % 2 + y % 2) % 2 == 0
                if dens >= 1 or (dens >= 0.5 and on) or (dens == 0.75 and (on or (x % 2 == 0))) or (dens < 0.5 and on and hsh(x, y, 7) < dens * 2):
                    s.set(x, y, OL2 if d < 2 else SV_D)
    return s


def threshold():
    s = Spr(32, 32)
    s.rect(0, 12, 31, 19, OL1)
    s.rect(0, 13, 31, 18, WOOD_L)
    s.rect(0, 13, 31, 13, SAND)
    s.rect(0, 18, 31, 18, WOOD_D)
    for x in (4, 27):
        s.set(x, 15, ST_L); s.set(x, 16, ST_D)
    return s


def puddle():
    s = Spr(32, 32)
    pts = [(10, 14), (11, 14), (12, 14), (13, 14), (14, 14), (15, 14), (16, 14), (17, 14), (9, 15), (10, 15), (11, 15),
           (12, 15), (13, 15), (14, 15), (15, 15), (16, 15), (17, 15), (18, 15), (19, 15), (10, 16), (11, 16), (12, 16),
           (13, 16), (14, 16), (15, 16), (16, 16), (17, 16), (18, 16), (12, 17), (13, 17), (14, 17), (15, 17)]
    for x, y in pts:
        s.set(x, y, GLOW if (x + y) % 2 else ORA)
    for x, y in ((11, 15), (12, 15), (13, 14)):
        s.set(x, y, YEL)
    return s


def shards():
    s = Spr(32, 32)
    for x, y, c in ((10, 14, MOON), (11, 14, ST_L), (12, 15, MOON), (15, 16, ST_L), (16, 16, MOON), (17, 17, ST_L),
                    (20, 14, MOON), (21, 15, ST_L), (13, 19, MOON), (14, 19, ST_L), (22, 19, MOON), (8, 17, ST_L)):
        s.set(x, y, c)
    return s


def butts():
    s = Spr(32, 32)
    for x, y in ((8, 20), (19, 14), (23, 22), (13, 25)):
        s.rect(x, y, x + 3, y, CREAM)
        s.set(x, y, ORA)
        s.set(x + 4, y, ST_M)
    for x, y in ((9, 18), (21, 17), (15, 22)):
        s.set(x, y, ST_L); s.set(x + 1, y, ST_M)
    return s


def peanuts():
    s = Spr(32, 32)
    for x, y in ((6, 16), (11, 22), (17, 13), (23, 20), (26, 12), (14, 27), (4, 25), (20, 25)):
        s.rect(x, y, x + 1, y, SAND); s.set(x, y + 1, WOOD_L)
    return s


# ============================================================ WAENDE (32x64)
def wall(kind='rot'):
    s = Spr(32, 64)
    # Kranzleiste
    s.rect(0, 0, 31, 0, OL1); s.rect(0, 1, 31, 1, WOOD_L); s.rect(0, 2, 31, 2, WOOD_M); s.rect(0, 3, 31, 3, WOOD_D)
    # Tapete
    for y in range(4, 35):
        for x in range(32):
            if kind == 'rot':
                c = RED_D
                if x % 8 in (0, 7):
                    c = SV_D
                if x % 8 == 4 and y % 8 == 4:
                    c = ROSE
                if x % 8 in (3, 5) and y % 8 == 5:
                    c = ROSE
                if x % 8 == 4 and y % 8 == 6:
                    c = ROSE
            elif kind == 'gruen':
                c = FOR_M
                if x % 8 in (0, 7):
                    c = FOR_D
                if x % 8 == 4 and y % 8 == 4:
                    c = LEAF
                if x % 8 in (3, 5) and y % 8 == 5:
                    c = GRASS_L
            else:
                c = WOOD_D
                u = x % 8
                if u == 0:
                    c = EARTH
                elif u == 1:
                    c = WOOD_M
                if hsh(x, y, 13) < 0.05 and u > 1:
                    c = EARTH
            if y < 8 and kind != 'holz':
                if (x + y) % 2 == 0 and y > 5:
                    c = darken(c) if c in (WOOD_M, WOOD_D) else (SV_D if c == RED_D else c)
            s.set(x, y, c)
    # Schattenkante unter Kranzleiste (Dither)
    for x in range(32):
        if x % 2 == 0:
            s.set(x, 4, OL2)
    # Handlauf / Paneelkante
    s.rect(0, 35, 31, 35, WOOD_L); s.rect(0, 36, 31, 37, WOOD_M); s.rect(0, 38, 31, 38, WOOD_D); s.rect(0, 39, 31, 39, OL1)
    # Vertaefelung
    for y in range(40, 64):
        for x in range(32):
            c = WOOD_D
            u, v = x % 16, y - 40
            if u == 0:
                c = EARTH
            if 2 <= u <= 13 and 3 <= v <= 17:
                c = WOOD_M if (u in (2, 3) or v == 3) else WOOD_D
                if u == 13 or v == 17:
                    c = EARTH
            s.set(x, y, c)
    s.rect(0, 58, 31, 58, WOOD_L); s.rect(0, 59, 31, 62, WOOD_M); s.rect(0, 63, 31, 63, EARTH)
    return s


def window_wall(kind):
    s = wall('rot')
    rect_o(s, 5, 5, 26, 35, WOOD_L)
    s.rect(6, 6, 25, 6, SAND)
    # Glas
    for (x0, x1) in ((8, 15), (16, 23)):
        for y in range(8, 32):
            if kind == 'nacht':
                c = NB_M if y < 20 else NB_D
            elif kind == 'lit':
                c = YEL if y < 18 else ORA
            elif kind == 'tag':
                c = BLUE_L if y < 22 else LEAF
            else:
                c = YEL if y < 18 else ORA
            for x in range(x0, x1 + 1):
                s.set(x, y, c)
    if kind == 'nacht':
        for x, y in ((10, 12), (20, 10), (18, 16), (12, 22)):
            s.set(x, y, MOON)
        ell_o(s, 21, 13, 2, 2, MOON, MOON)
        s.set(22, 12, NB_M)
    if kind == 'tag':
        for x, y in ((10, 11), (11, 11), (12, 11), (11, 10), (19, 15), (20, 15), (21, 15), (20, 14)):
            s.set(x, y, CREAM)
        for x in range(8, 24):
            s.set(x, 26 + (1 if (x // 3) % 2 else 0), GRASS)
    if kind in ('lit', 'curtain'):
        s.set(9, 9, CREAM); s.set(10, 9, CREAM); s.set(9, 10, CREAM)
    s.rect(15, 7, 16, 32, WOOD_D)
    s.rect(8, 19, 23, 20, WOOD_D)
    s.rect(4, 33, 27, 36, WOOD_L); s.rect(4, 36, 27, 36, OL1); s.rect(4, 33, 27, 33, SAND)
    if kind == 'curtain':
        for x0, x1 in ((6, 11), (20, 25)):
            for y in range(6, 33):
                for x in range(x0, x1 + 1):
                    u = x - x0
                    c = RED_D if u % 3 else ROSE
                    if u == 0 or u == 5:
                        c = SV_D
                    s.set(x, y, c)
        s.rect(6, 5, 25, 6, YEL); s.rect(6, 6, 25, 6, ORA)
        s.rect(11, 20, 12, 21, YEL); s.rect(19, 20, 20, 21, YEL)
    return s


def swing_door_inside():
    s = Spr(64, 64)
    a = wall('rot'); b = wall('rot')
    s.paste(a, 0, 0); s.paste(b, 32, 0)
    s.rect(3, 4, 60, 63, OL1)
    s.rect(4, 5, 59, 63, WOOD_D)
    s.rect(4, 5, 59, 6, WOOD_L); s.rect(4, 7, 59, 8, WOOD_M)
    s.rect(4, 9, 6, 63, WOOD_L); s.rect(57, 9, 59, 63, WOOD_D)
    for y in range(10, 64):
        for x in range(7, 57):
            t = (y - 10) / 53
            c = NB_D if t < 0.4 else (NB_M if t < 0.7 else NB_L)
            if (x + y) % 3 == 0 and t > 0.5:
                c = NB_L
            s.set(x, y, c)
    ell_o(s, 46, 22, 3, 3, MOON, MOON)
    for x0, y0 in ((13, 18), (36, 24)):
        s.rect(x0, y0, x0 + 1, y0, YEL)
    def leaf(x0, x1):
        for y in range(27, 54):
            for x in range(x0, x1 + 1):
                v = y - 27
                c = WOOD_M if (v // 4) % 2 == 0 else WOOD_D
                if v % 4 == 0:
                    c = WOOD_L
                if x == x0 or x == x1:
                    c = OL1
                s.set(x, y, c)
        s.rect(x0, 27, x1, 27, OL1); s.rect(x0, 53, x1, 53, OL1)
    leaf(7, 31); leaf(32, 56)
    s.rect(5, 30, 7, 31, ST_L); s.rect(56, 30, 58, 31, ST_L); s.rect(5, 50, 7, 51, ST_L); s.rect(56, 50, 58, 51, ST_L)
    s.rect(7, 58, 56, 63, WOOD_L); s.rect(7, 58, 56, 58, SAND)
    return s


def inner_door(kind):
    s = wall('rot')
    rect_o(s, 4, 3, 27, 63, WOOD_L)
    if kind == 'offen':
        for y in range(5, 64):
            for x in range(6, 26):
                t = (y - 5) / 58
                s.set(x, y, OL2 if t < 0.6 else SV_D)
        for y in range(40, 64):
            for x in range(6, 26):
                if (x + y) % 3 == 0:
                    s.set(x, y, SV_M)
        return s
    if kind == 'keller':
        for y in range(8, 64):
            for x in range(6, 26):
                s.set(x, y, ST_D)
        ell_o(s, 16, 18, 10, 10, OL1, ST_L)
        for y in range(18, 64):
            for x in range(7, 25):
                s.set(x, y, OL1)
        planks(s, 8, 20, 23, 63, base=WOOD_D, lite=WOOD_M, dark=EARTH, seam=OL1)
        s.rect(8, 30, 23, 31, ST_M); s.rect(8, 48, 23, 49, ST_M)
        s.rect(21, 38, 22, 41, ST_L)
        return s
    planks(s, 6, 5, 25, 63, base=WOOD_M, lite=WOOD_L, dark=WOOD_D, seam=EARTH, seed=9)
    for y0, y1 in ((10, 28), (34, 56)):
        s.rect(9, y0, 22, y1, OL1)
        s.rect(10, y0 + 1, 21, y1 - 1, WOOD_D)
        s.rect(10, y0 + 1, 21, y0 + 1, WOOD_L)
    s.rect(21, 34, 22, 36, YEL)
    s.rect(21, 37, 22, 37, ORA)
    return s


def mirror_wall():
    """Spiegelwand hinter der Theke, 64x64."""
    s = Spr(64, 64)
    for i in range(2):
        s.paste(wall('holz'), i * 32, 0)
    rect_o(s, 4, 4, 59, 44, YEL)
    s.rect(5, 5, 58, 5, CREAM)
    s.rect(6, 6, 57, 6, GLOW) if False else None
    s.rect(7, 7, 56, 41, OL1)
    for y in range(8, 41):
        for x in range(8, 56):
            t = (y - 8) / 32
            c = NB_L if t < 0.5 else NB_M
            s.set(x, y, c)
    # Glanzstreifen (diagonal)
    for k in range(0, 14):
        s.set(14 + k, 36 - k, MOON) if False else None
    for dx in (0, 1):
        for k in range(26):
            x, y = 12 + k + dx, 38 - k
            if 8 <= x < 56 and 8 <= y < 41:
                s.set(x, y, MOON if dx == 0 else NB_L)
    for k in range(18):
        x, y = 32 + k, 38 - k
        if 8 <= x < 56 and 8 <= y < 41:
            s.set(x, y, MOON)
    # Ornament oben
    for x in range(8, 56, 8):
        s.set(x, 5, ORA); s.set(x + 1, 5, GLOW)
    s.rect(5, 43, 58, 43, GLOW) if False else None
    # Regal darunter
    s.rect(2, 46, 61, 48, WOOD_L); s.rect(2, 48, 61, 48, OL1); s.rect(2, 46, 61, 46, SAND)
    return s


def wall_end(side):
    s = wall('rot')
    xs = range(0, 6) if side == 'L' else range(31, 25, -1)
    cols = [OL1, SV_L, SV_M, SV_M, SV_D, OL1]
    for i, x in enumerate(xs):
        for y in range(0, 64):
            s.set(x, y, cols[i])
    return s


# ============================================================ KLEINE REQUISITEN
BOTTLES = {
    'whisky': (6, 15, 2, 5, ORA, YEL, WOOD_L, CREAM),
    'bourbon': (6, 15, 2, 4, GLOW, ORA, RED_D, WOOD_D),
    'bier': (4, 16, 2, 7, WOOD_D, WOOD_M, ST_L, SAND),
    'rot': (4, 17, 2, 8, FOR_D, FOR_M, RED_D, CREAM),
    'weiss': (4, 17, 2, 8, FOR_M, LEAF, YEL, CREAM),
    'rum': (6, 14, 2, 4, EARTH, WOOD_D, WOOD_L, ROSE),
    'schnaps': (4, 14, 2, 5, MOON, CREAM, WOOD_L, BLUE_D),
    'met': (6, 12, 2, 3, SAND, CREAM, WOOD_M, YEL),
}


def sbottle(s, x, yb, kind):
    w, h, nw, nh, body, hi, cap, label = BOTTLES[kind]
    t = Spr(w + 2, h + 3)
    ox = 1 + (w - nw) // 2
    bh = h - nh
    t.rect(ox, 1, ox + nw - 1, nh, body)           # Hals
    t.rect(1, 1 + nh, w, h, body)                   # Koerper
    t.rect(1, 1 + nh, 1, h, hi)
    t.rect(ox, 0, ox + nw - 1, 1, cap)              # Kappe
    ly0, ly1 = h - bh // 2 - 1, h - 2
    if bh >= 5:
        t.rect(2, ly0, w - 1, ly1, label)
    t.outline(OL1)
    s.paste(t, x - 1, yb - h - 1)


def sglass(s, x, yb, kind):
    sp = {'wein': (5, 8), 'tumbler': (5, 6), 'humpen': (7, 8), 'schnaps': (3, 5)}[kind]
    w, h = sp
    t = Spr(w + 2, h + 2)
    if kind == 'wein':
        t.rect(1, 1, w, 4, MOON)
        t.rect(2, 2, w - 1, 3, RED_D)
        t.rect(w // 2 + 1, 5, w // 2 + 1, h - 1, ST_L)
        t.rect(1, h, w, h, MOON)
    elif kind == 'humpen':
        t.rect(1, 1, w - 2, h, MOON)
        t.rect(2, 3, w - 3, h - 1, YEL)
        t.rect(1, 1, w - 2, 2, CREAM)
        t.rect(w - 1, 3, w, h - 2, ST_L)
    else:
        t.rect(1, 1, w, h, MOON)
        t.rect(2, 2 if kind == 'schnaps' else 3, w - 1, h - 1, ORA if kind == 'tumbler' else CREAM)
    t.outline(OL1)
    s.paste(t, x - 1, yb - h - 1)


# ============================================================ REGALE (64x64)
def shelf(levels):
    """levels: 3 Listen aus ('b', kind) / ('g', kind) / None."""
    s = Spr(64, 64)
    for i in range(2):
        s.paste(wall('holz'), i * 32, 0)
    s.rect(0, 0, 63, 63, CLEAR) if False else None
    # Rueckwand dunkler
    for y in range(4, 64):
        for x in range(64):
            s.set(x, y, darken(s.get(x, y)))
    boards = (21, 42, 63)
    for yb in boards:
        s.rect(0, yb - 2, 63, yb, WOOD_L)
        s.rect(0, yb - 2, 63, yb - 2, SAND)
        s.rect(0, yb, 63, yb, OL1)
        if yb < 63:
            s.rect(0, yb + 1, 63, yb + 1, OL2)
    s.rect(0, 0, 1, 63, OL1); s.rect(62, 0, 63, 63, OL1)
    for li, items in enumerate(levels):
        yb = boards[li] - 3
        for i, it in enumerate(items):
            if it:
                x = 5 + i * 8
                if it[0] == 'b':
                    sbottle(s, x, yb, it[1])
                else:
                    sglass(s, x, yb, it[1])
    return s


def B(k): return ('b', k)
def G(k): return ('g', k)


def shelf_A():
    return shelf([[B('whisky'), B('whisky'), B('bourbon'), B('bourbon'), B('whisky'), B('bourbon'), B('whisky')],
                  [B('rum'), B('rum'), B('schnaps'), B('schnaps'), B('rum'), B('schnaps'), None],
                  [B('bourbon'), B('whisky'), B('whisky'), B('bourbon'), B('rum'), B('rum'), B('bourbon')]])


def shelf_B():
    return shelf([[B('rot'), B('weiss'), B('rot'), B('weiss'), B('rot'), B('weiss'), B('rot')],
                  [B('bier')] * 7,
                  [B('weiss'), B('rot'), B('bier'), B('bier'), B('rot'), B('weiss'), None]])


def shelf_glass():
    return shelf([[G('wein')] * 7, [G('tumbler')] * 5 + [None, None], [G('humpen'), G('humpen'), G('humpen'), None, G('schnaps'), G('schnaps'), G('schnaps')]])


def shelf_mixed():
    return shelf([[B('met'), B('schnaps'), B('rum'), B('met'), B('whisky'), B('rot'), B('bier')],
                  [G('tumbler'), G('tumbler'), None, B('bourbon'), B('bourbon'), None, G('wein')],
                  [B('weiss'), B('rot'), B('bier'), B('met'), B('met'), B('schnaps'), B('rum')]])


def barrel_rack():
    s = Spr(64, 64)
    for i in range(2):
        s.paste(wall('holz'), i * 32, 0)
    for y in range(4, 64):
        for x in range(64):
            s.set(x, y, darken(s.get(x, y)))
    # Gestell
    s.rect(2, 4, 5, 63, OL1); s.rect(3, 4, 4, 63, WOOD_M)
    s.rect(58, 4, 61, 63, OL1); s.rect(59, 4, 60, 63, WOOD_M)
    for cy in (22, 49):
        s.rect(2, cy + 9, 61, cy + 12, OL1)
        s.rect(3, cy + 10, 60, cy + 11, WOOD_L)
        # liegendes Fass
        for x in range(8, 56):
            for y in range(cy - 8, cy + 9):
                t = (y - (cy - 8)) / 16
                c = WOOD_M
                if t < 0.2:
                    c = WOOD_L
                elif t > 0.75:
                    c = WOOD_D
                if x % 6 == 0:
                    c = WOOD_D
                s.set(x, y, c)
        s.rect(8, cy - 9, 55, cy - 9, OL1); s.rect(8, cy + 9, 55, cy + 9, OL1)
        s.rect(8, cy - 8, 8, cy + 8, OL1); s.rect(55, cy - 8, 55, cy + 8, OL1)
        for x0 in (13, 47):
            s.rect(x0, cy - 8, x0 + 2, cy + 8, ST_M); s.rect(x0, cy - 8, x0, cy + 8, ST_L)
        s.rect(30, cy - 1, 34, cy + 2, ST_D)
        s.rect(31, cy + 2, 33, cy + 5, YEL); s.rect(31, cy + 5, 33, cy + 5, ORA)
    return s


def glass_rack():
    s = Spr(64, 32)
    s.rect(2, 3, 61, 5, OL1); s.rect(3, 4, 60, 4, WOOD_L)
    s.rect(2, 3, 3, 28, OL1); s.rect(60, 3, 61, 28, OL1)
    s.rect(2, 26, 61, 28, OL1); s.rect(3, 27, 60, 27, WOOD_L)
    for x in range(8, 58, 9):
        s.rect(x, 6, x, 9, ST_L)
        s.rect(x - 3, 10, x + 3, 10, MOON)
        s.rect(x - 3, 11, x - 3, 15, MOON); s.rect(x + 3, 11, x + 3, 15, MOON)
        s.rect(x - 2, 11, x + 2, 15, NB_L)
        s.rect(x - 2, 11, x - 2, 13, MOON)
    return s


# ============================================================ WANDDEKO
def dartboard():
    s = Spr(32, 32)
    ell_o(s, 16, 16, 12, 12, WOOD_D, OL1)
    for r, c in ((10, RED_D), (8, CREAM), (6, FOR_M), (4, CREAM), (2, RED_D)):
        s.ellipse(16, 16, r, r, c)
    s.rect(16, 5, 16, 27, OL1) if False else None
    for k in range(8):
        a = k * math.pi / 4
        for r in range(3, 11):
            s.set(int(round(16 + r * math.cos(a))), int(round(16 + r * math.sin(a))), OL1)
    s.rect(15, 15, 16, 16, YEL)
    s.line(22, 10, 28, 4, ST_L); s.set(28, 4, RED_D); s.set(27, 4, RED_D)
    return s


def antlers():
    s = Spr(32, 32)
    s.rect(11, 22, 20, 29, OL1); s.rect(12, 23, 19, 28, WOOD_M); s.rect(12, 23, 19, 23, WOOD_L)
    for sx in (-1, 1):
        cx = 15.5
        pts = [(0, 22), (3, 17), (5, 12), (6, 6), (5, 3)]
        for (a, b) in zip(pts, pts[1:]):
            s.line(int(cx + sx * a[0]), a[1], int(cx + sx * b[0]), b[1], OL1)
        for (a, b) in zip(pts, pts[1:]):
            s.line(int(cx + sx * a[0]) + (0 if sx < 0 else 0), a[1], int(cx + sx * b[0]), b[1], SAND)
        s.line(int(cx + sx * 3), 17, int(cx + sx * 9), 14, SAND); s.set(int(cx + sx * 9), 14, WOOD_L)
        s.line(int(cx + sx * 5), 12, int(cx + sx * 11), 8, SAND)
    return s


def wall_clock():
    s = Spr(32, 32)
    ell_o(s, 16, 16, 11, 11, CREAM, OL1)
    s.ellipse(16, 16, 11, 11, WOOD_M)
    s.ellipse(16, 16, 9, 9, CREAM)
    for a in range(12):
        ang = a * math.pi / 6
        s.set(int(round(16 + 7 * math.cos(ang))), int(round(16 + 7 * math.sin(ang))), OL1)
    s.line(16, 16, 16, 10, OL1); s.line(16, 16, 20, 18, OL1)
    s.set(16, 16, RED_D)
    s.rect(15, 27, 16, 29, ORA) if False else None
    return s


def calendar():
    s = Spr(32, 32)
    rect_o(s, 6, 3, 25, 28, CREAM)
    s.rect(7, 4, 24, 10, RED_D)
    draw_text(s, 'OCT', 11, 5, CREAM, '3x5', 1, 1)
    draw_text(s, '19', 12, 14, OL1, '3x5', 1, 1)
    for x in (9, 15, 21):
        s.set(x, 22, ST_M); s.set(x + 1, 22, ST_M); s.set(x, 24, ST_M); s.set(x + 1, 24, ST_M)
    s.rect(14, 1, 17, 3, ST_L)
    return s


def photo():
    s = Spr(32, 32)
    rect_o(s, 7, 4, 24, 27, WOOD_L)
    s.rect(9, 6, 22, 25, OL1)
    s.rect(10, 7, 21, 24, SAND)
    ell_o(s, 16, 14, 3.2, 4, WOOD_M, WOOD_M)
    s.rect(11, 19, 20, 24, WOOD_M)
    s.rect(10, 7, 21, 7, CREAM)
    s.rect(12, 20, 19, 20, CREAM) if False else None
    s.rect(15, 18, 16, 20, RED_D)
    return s


def poster_credit():
    s = Spr(32, 32)
    rect_o(s, 3, 3, 28, 28, CREAM)
    s.rect(4, 4, 27, 5, RED_D)
    draw_text(s, 'NO', 3 + (26 - text_width('NO', '3x5', 1, 1)) // 2, 9, RED_D, '3x5', 1, 1)
    draw_text(s, 'CREDIT', 3 + (26 - text_width('CREDIT', '3x5', 1, 1)) // 2, 17, OL1, '3x5', 1, 1)
    s.rect(6, 25, 25, 25, ST_L)
    for x, y in ((5, 5), (26, 5), (5, 26), (26, 26)):
        s.set(x, y, ST_D)
    return s


def price_board_inner():
    s = Spr(128, 32)
    rect_o(s, 0, 2, 127, 29, WOOD_M)
    s.rect(1, 3, 126, 3, WOOD_L)
    s.rect(3, 5, 124, 26, OL1)
    s.rect(4, 6, 123, 25, FOR_D)
    cols = [(8, ['BEER', 'MEAD', 'WINE']), (44, ['SCHNAPPS', 'RUM', 'WHISKY']), (84, ['BOURBON', 'HOT STEW', 'BREAD'])]
    for x0, rows in cols:
        for i, tx in enumerate(rows):
            draw_text(s, tx, x0, 9 + i * 6, CREAM, '3x5', 1, 1)
    for x in (39, 79):
        for y in range(8, 24):
            if y % 2 == 0:
                s.set(x, y, FOR_M)
    return s


# ============================================================ THEKE (32x64)
SURF = 36  # Oberkante Platte


def counter_base(side=None):
    s = Spr(32, 64)
    # Platte
    s.rect(0, SURF, 31, SURF, OL1)
    s.rect(0, SURF + 1, 31, SURF + 1, SAND)
    s.rect(0, SURF + 2, 31, SURF + 5, WOOD_L)
    s.rect(0, SURF + 3, 31, SURF + 3, SAND)
    for x in range(0, 32, 6):
        s.set(x + 2, SURF + 4, WOOD_M)
    s.rect(0, SURF + 6, 31, SURF + 6, WOOD_M)
    s.rect(0, SURF + 7, 31, SURF + 7, OL1)
    # Front
    for y in range(SURF + 8, 64):
        for x in range(32):
            u, v = x % 16, y - (SURF + 8)
            c = WOOD_D
            if u == 0:
                c = EARTH
            if 2 <= u <= 13 and 2 <= v <= 14:
                c = WOOD_M if (u in (2, 3) or v == 2) else WOOD_D
                if u == 13 or v == 14:
                    c = EARTH
            s.set(x, y, c)
    # Fussleiste aus Messing
    s.rect(0, 59, 31, 60, YEL if False else ST_L)
    s.rect(0, 59, 31, 59, MOON)
    s.rect(0, 61, 31, 61, OL1)
    s.rect(0, 62, 31, 63, WOOD_D); s.rect(0, 63, 31, 63, EARTH)
    if side == 'L':
        s.rect(0, SURF, 3, 63, OL1)
        s.rect(1, SURF + 1, 2, 62, WOOD_L)
        s.rect(0, SURF, 0, SURF, CLEAR)
    if side == 'R':
        s.rect(28, SURF, 31, 63, OL1)
        s.rect(29, SURF + 1, 30, 62, WOOD_D)
        s.rect(31, SURF, 31, SURF, CLEAR)
    return s


def on_counter(fn, side=None):
    s = counter_base(side)
    fn(s)
    return s


def prop_glasses(s):
    for x in (6, 14, 22):
        sglass(s, x, SURF, 'tumbler' if x != 14 else 'wein')


def prop_bottles(s):
    for x, k in ((5, 'whisky'), (14, 'rum'), (22, 'bourbon')):
        sbottle(s, x, SURF, k)


def prop_tap(s):
    s.rect(9, 14, 22, 15, OL1); s.rect(10, 14, 21, 14, ST_L); s.rect(10, 15, 21, 15, ST_M)
    s.rect(13, 15, 18, SURF - 1, OL1); s.rect(14, 16, 17, SURF - 2, ST_M); s.rect(14, 16, 14, SURF - 2, ST_L)
    for x, c in ((11, RED_D), (20, BLUE_D)):
        s.rect(x, 7, x + 1, 14, OL1); s.rect(x, 8, x + 1, 13, c)
        s.set(x, 8, ROSE if c == RED_D else BLUE_L)
    s.rect(15, 22, 16, 26, GLOW if False else ORA)
    s.rect(8, SURF - 2, 23, SURF - 1, OL1)
    s.rect(9, SURF - 2, 22, SURF - 2, ST_D)
    s.rect(12, SURF - 5, 19, SURF - 3, OL1); s.rect(13, SURF - 4, 18, SURF - 4, ST_M)
    sglass(s, 7, SURF, 'humpen')


def prop_register(s):
    s.rect(7, 22, 25, SURF - 1, OL1)
    s.rect(8, 23, 24, SURF - 2, WOOD_D)
    s.rect(8, 23, 24, 23, WOOD_L)
    s.rect(9, 24, 23, 28, OL1); s.rect(10, 25, 22, 27, YEL); s.rect(10, 25, 22, 25, CREAM)
    for x in range(10, 22, 3):
        s.rect(x, 30, x + 1, 31, ST_L); s.rect(x, 33, x + 1, 33, ST_L)
    s.rect(9, 20, 23, 21, OL1); s.rect(10, 20, 22, 20, ST_L)
    s.rect(26, 28, 28, 29, OL1); s.set(27, 28, YEL)


def prop_candle(s):
    s.rect(11, SURF - 4, 20, SURF - 1, OL1); s.rect(12, SURF - 3, 19, SURF - 2, ST_L)
    s.rect(14, SURF - 13, 17, SURF - 4, OL1); s.rect(15, SURF - 12, 16, SURF - 5, CREAM)
    s.rect(15, SURF - 18, 16, SURF - 14, YEL); s.set(15, SURF - 17, ORA); s.set(15, SURF - 16, CREAM)
    s.set(16, SURF - 19, ORA)


def prop_tray(s):
    s.rect(4, SURF - 3, 27, SURF - 1, OL1); s.rect(5, SURF - 3, 26, SURF - 2, ST_L)
    sglass(s, 8, SURF - 2, 'humpen'); sglass(s, 16, SURF - 2, 'humpen'); sglass(s, 24, SURF - 2, 'wein')


def prop_whisky(s):
    sbottle(s, 9, SURF, 'whisky')
    sglass(s, 20, SURF, 'tumbler')
    s.set(21, SURF - 3, YEL)


def prop_cigar(s):
    s.rect(6, SURF - 8, 25, SURF - 1, OL1)
    s.rect(7, SURF - 7, 24, SURF - 2, WOOD_M)
    s.rect(7, SURF - 7, 24, SURF - 7, WOOD_L)
    s.rect(11, SURF - 6, 20, SURF - 5, CREAM)
    s.rect(14, SURF - 5, 17, SURF - 4, RED_D)
    s.rect(7, SURF - 3, 24, SURF - 3, WOOD_D)


def prop_gate_closed(s):
    s.rect(0, SURF - 3, 31, SURF - 1, OL1)
    s.rect(1, SURF - 2, 30, SURF - 2, WOOD_L)
    s.rect(14, SURF - 4, 17, SURF - 3, ST_L)


def prop_gate_open(s):
    s.rect(0, SURF + 1, 31, SURF + 7, CLEAR)
    for y in range(SURF, 64):
        for x in range(32):
            s.set(x, y, OL2 if (y < 58) else SV_D)
    s.rect(2, SURF - 22, 6, SURF + 8, OL1); s.rect(3, SURF - 21, 5, SURF + 7, WOOD_L)
    s.rect(3, SURF - 21, 3, SURF + 7, SAND)
    s.rect(2, SURF + 8, 6, SURF + 8, WOOD_D)
    s.rect(0, 62, 31, 63, WOOD_D)


def prop_keg(s):
    for y in range(SURF - 22, SURF):
        t = (y - (SURF - 22)) / 21
        hw = int(round(8 + 2 * math.sin(math.pi * t)))
        for x in range(16 - hw, 16 + hw):
            rel = (x - (16 - hw)) / (2 * hw)
            c = WOOD_M
            if rel < 0.2:
                c = WOOD_L
            elif rel > 0.78:
                c = WOOD_D
            if (x - (16 - hw)) % 5 == 0 and x != 16 - hw:
                c = WOOD_D
            s.set(x, y, c)
        s.set(16 - hw - 1, y, OL1); s.set(16 + hw, y, OL1)
    s.rect(6, SURF - 23, 25, SURF - 23, OL1)
    s.rect(7, SURF - 22, 24, SURF - 22, WOOD_L)
    for y0 in (SURF - 17, SURF - 7):
        s.rect(6, y0, 25, y0 + 1, ST_M); s.rect(6, y0, 25, y0, ST_L)
    s.rect(15, SURF - 12, 16, SURF - 9, ST_D)
    s.rect(15, SURF - 9, 16, SURF - 7, ORA)


def prop_paper(s):
    s.rect(5, SURF - 2, 26, SURF - 1, OL1)
    s.rect(6, SURF - 3, 25, SURF - 2, CREAM)
    s.rect(6, SURF - 3, 25, SURF - 3, MOON)
    for x in range(8, 24, 3):
        s.rect(x, SURF - 2, x + 1, SURF - 2, ST_L)
    sglass(s, 24, SURF - 3, 'schnaps')


def barstool(side=False):
    s = Spr(32, 32)
    if not side:
        ell_o(s, 16, 12, 8, 3.2, RED_D, OL1)
        s.ellipse(16, 12, 6, 1.8, ROSE)
        s.rect(8, 13, 23, 16, OL1)
        s.rect(9, 13, 22, 15, RED_D); s.rect(9, 13, 22, 13, ROSE)
        for x in (12, 20):
            s.set(x, 14, YEL)
        s.rect(15, 17, 16, 24, OL1); s.rect(15, 17, 16, 24, ST_M); s.rect(15, 17, 15, 24, ST_L)
        for x0, x1 in ((10, 14), (17, 22)):
            s.line(15 if x0 < 15 else 16, 24, x0, 30, OL1)
            s.line(16 if x0 < 15 else 17, 24, x1 if x0 > 15 else x0 + 1, 30, ST_M) if False else None
        s.rect(9, 30, 22, 31, OL1) if False else None
        s.rect(8, 29, 14, 30, ST_D); s.rect(17, 29, 23, 30, ST_D)
        s.rect(9, 22, 22, 22, ST_L)
    else:
        s.rect(10, 10, 21, 15, OL1)
        s.rect(11, 11, 20, 14, RED_D); s.rect(11, 11, 20, 11, ROSE)
        s.rect(15, 16, 16, 28, OL1); s.rect(15, 16, 16, 27, ST_M)
        s.rect(10, 28, 21, 30, OL1); s.rect(11, 29, 20, 29, ST_D)
        s.rect(11, 22, 20, 22, ST_L)
    return s


# ============================================================ MOEBEL
def round_table(set_=False):
    s = Spr(32, 32)
    s.rect(14, 18, 17, 28, OL1); s.rect(15, 18, 16, 28, WOOD_M); s.rect(15, 18, 15, 28, WOOD_L)
    s.rect(9, 28, 22, 30, OL1); s.rect(10, 29, 21, 29, WOOD_D)
    ell_o(s, 16, 15, 13, 6, WOOD_D, OL1)
    s.ellipse(16, 14, 13, 5.2, WOOD_L)
    s.ellipse(16, 14, 11, 4, SAND)
    for x in range(8, 24):
        if x % 4 == 0:
            s.set(x, 14, WOOD_L)
    s.rect(4, 17, 28, 18, WOOD_D)
    if set_:
        sglass(s, 9, 15, 'humpen')
        sglass(s, 22, 16, 'tumbler')
        s.rect(15, 8, 16, 13, CREAM); s.rect(15, 5, 16, 7, YEL); s.set(15, 6, ORA)
        s.rect(13, 13, 18, 14, OL1) if False else None
    return s


def long_table():
    s = Spr(64, 32)
    s.rect(2, 8, 61, 9, OL1)
    s.rect(3, 9, 60, 9, SAND)
    s.rect(3, 10, 60, 15, WOOD_L)
    for x in range(6, 60, 7):
        s.set(x, 12, WOOD_M)
    s.rect(2, 16, 61, 17, OL1)
    s.rect(3, 16, 60, 16, WOOD_M)
    s.rect(3, 17, 60, 17, WOOD_D)
    for x0 in (6, 54):
        s.rect(x0, 18, x0 + 3, 29, OL1)
        s.rect(x0 + 1, 18, x0 + 2, 28, WOOD_M)
        s.rect(x0 + 1, 18, x0 + 1, 28, WOOD_L)
    s.rect(6, 24, 57, 24, WOOD_D) if False else None
    return s


def poker_table():
    s = Spr(64, 32)
    ell_o(s, 32, 14, 29, 9, WOOD_D, OL1)
    s.ellipse(32, 14, 27, 7.5, FOR_D)
    s.ellipse(32, 14, 25.5, 6.5, FOR_M)
    for x in range(10, 54):
        if (x * 3) % 7 == 0:
            s.set(x, 12 + (x % 5) % 3, GRASS)
    # Karten
    for x, y, c in ((24, 11, CREAM), (28, 13, CREAM), (32, 11, CREAM), (36, 14, CREAM), (40, 11, CREAM)):
        s.rect(x, y, x + 2, y + 3, OL1)
        s.rect(x + 1, y + 1, x + 1, y + 2, c)
    s.set(25, 12, RED_D); s.set(33, 12, RED_D)
    # Chips
    for x, y, c in ((12, 14, RED_D), (13, 14, RED_D), (12, 13, YEL), (50, 15, BLUE_D), (51, 15, BLUE_D), (50, 14, YEL),
                    (31, 17, ST_L), (32, 17, ST_L), (31, 16, YEL)):
        s.set(x, y, c)
    s.rect(10, 22, 13, 30, OL1); s.rect(11, 22, 12, 29, WOOD_M)
    s.rect(50, 22, 53, 30, OL1); s.rect(51, 22, 52, 29, WOOD_M)
    s.rect(30, 23, 33, 28, OL1); s.rect(31, 23, 32, 28, WOOD_D)
    return s


def chair(view):
    s = Spr(32, 32)
    if view == 'vorne':
        for x in (9, 21):
            s.rect(x, 4, x + 2, 20, OL1); s.rect(x + 1, 4, x + 1, 19, WOOD_M)
        s.rect(9, 6, 23, 8, OL1); s.rect(10, 7, 22, 7, WOOD_L)
        s.rect(9, 12, 23, 13, OL1); s.rect(10, 12, 22, 12, WOOD_M)
        s.rect(8, 18, 24, 21, OL1); s.rect(9, 19, 23, 19, SAND); s.rect(9, 20, 23, 20, WOOD_L)
        for x in (9, 21):
            s.rect(x, 21, x + 2, 30, OL1); s.rect(x + 1, 22, x + 1, 29, WOOD_D)
    elif view == 'hinten':
        s.rect(8, 4, 24, 21, OL1); s.rect(9, 5, 23, 20, WOOD_M)
        s.rect(9, 5, 23, 5, WOOD_L)
        for x in range(12, 22, 3):
            s.rect(x, 7, x, 18, WOOD_D)
        s.rect(8, 20, 24, 22, OL1); s.rect(9, 21, 23, 21, WOOD_D)
        for x in (9, 21):
            s.rect(x, 22, x + 2, 30, OL1); s.rect(x + 1, 23, x + 1, 29, WOOD_D)
    else:
        flip = (view == 'rechts')
        def X(x): return 31 - x if flip else x
        s.rect(X(9), 4, X(11), 21, OL1) if not flip else s.rect(X(11), 4, X(9), 21, OL1)
        for y in range(5, 21):
            s.set(X(10), y, WOOD_M)
        s.rect(min(X(9), X(24)), 17, max(X(9), X(24)), 20, OL1)
        for x in range(min(X(10), X(23)), max(X(10), X(23)) + 1):
            s.set(x, 18, SAND); s.set(x, 19, WOOD_L)
        for xx in (10, 22):
            s.rect(min(X(xx) - 1, X(xx) + 1), 20, max(X(xx) - 1, X(xx) + 1), 30, OL1)
            s.rect(X(xx), 21, X(xx), 29, WOOD_D)
    return s


def booth():
    s = Spr(64, 32)
    rect_o(s, 2, 2, 61, 16, RED_D)
    s.rect(3, 3, 60, 3, ROSE)
    for x in range(8, 58, 10):
        s.set(x, 8, YEL); s.set(x, 9, ORA)
    s.rect(3, 12, 60, 13, SV_D)
    rect_o(s, 2, 16, 61, 22, WOOD_D)
    s.rect(3, 17, 60, 17, WOOD_L)
    rect_o(s, 4, 22, 59, 28, RED_D)
    s.rect(5, 23, 58, 23, ROSE)
    for x0 in (6, 54):
        s.rect(x0, 28, x0 + 3, 31, OL1); s.rect(x0 + 1, 28, x0 + 2, 30, WOOD_D)
    return s


def spittoon():
    s = Spr(32, 32)
    ell_o(s, 16, 17, 7, 3, YEL, OL1)
    s.ellipse(16, 17, 5, 1.6, WOOD_D)
    s.rect(9, 19, 22, 25, OL1)
    for y in range(19, 25):
        for x in range(10, 22):
            s.set(x, y, YEL if x < 14 else (SAND if x < 19 else WOOD_L))
    s.ellipse(16, 26, 8, 3, OL1)
    s.ellipse(16, 25.5, 7, 2.2, SAND)
    s.rect(13, 20, 14, 23, CREAM)
    return s


def piano():
    s = Spr(64, 64)
    # Koerper
    rect_o(s, 2, 8, 61, 54, WOOD_D)
    s.rect(3, 9, 60, 10, WOOD_L)
    s.rect(3, 11, 60, 11, WOOD_M)
    # Notenpult + Noten
    s.rect(10, 16, 53, 29, OL1)
    s.rect(11, 17, 52, 28, EARTH)
    s.rect(18, 18, 45, 27, CREAM)
    s.rect(18, 18, 45, 18, MOON)
    for y in (20, 23, 26):
        s.rect(20, y, 43, y, ST_M)
    for x in (23, 28, 33, 37, 41):
        s.rect(x, 21, x + 1, 22, OL1); s.set(x + 1, 24, OL1)
    # Kerzenhalter
    for x in (6, 54):
        s.rect(x, 14, x + 2, 18, OL1); s.rect(x + 1, 15, x + 1, 17, CREAM)
        s.set(x + 1, 12, YEL); s.set(x + 1, 13, ORA)
    # Tastatur
    s.rect(6, 36, 57, 37, OL1)
    s.rect(7, 38, 56, 47, OL1)
    s.rect(8, 38, 55, 46, CREAM)
    for x in range(8, 56, 4):
        s.rect(x, 38, x, 46, ST_L)
    for x in range(10, 54, 4):
        if ((x - 10) // 4) % 7 not in (2, 6):
            s.rect(x, 38, x + 2, 43, OL1)
    s.rect(7, 47, 56, 48, WOOD_M)
    s.rect(4, 55, 59, 58, OL1)
    s.rect(5, 55, 58, 56, WOOD_D)
    # Beine
    for x in (6, 52):
        s.rect(x, 54, x + 5, 63, OL1); s.rect(x + 1, 55, x + 4, 62, WOOD_D); s.rect(x + 1, 55, x + 1, 62, WOOD_M)
    s.rect(26, 57, 37, 59, OL1); s.rect(27, 57, 36, 58, YEL)
    return s


def stove():
    s = Spr(32, 64)
    s.rect(14, 0, 17, 26, OL1); s.rect(15, 0, 16, 26, ST_D); s.rect(15, 0, 15, 26, ST_M)
    s.rect(12, 0, 19, 2, OL1) if False else None
    for y0 in (6, 14):
        s.rect(13, y0, 18, y0 + 1, ST_L)
    ell_o(s, 16, 40, 10, 14, ST_D, OL1)
    for y in range(26, 54):
        for x in range(6, 26):
            dx = (x + 0.5 - 16) / 10
            dy = (y + 0.5 - 40) / 14
            if dx * dx + dy * dy <= 1:
                t = (dx + dy)
                s.set(x, y, ST_L if t < -0.8 else (ST_M if t < 0.3 else ST_D))
    s.rect(12, 36, 21, 47, OL1); s.rect(13, 37, 20, 46, OL2)
    s.rect(14, 41, 19, 45, ORA); s.rect(15, 43, 18, 45, YEL); s.rect(16, 42, 17, 42, GLOW)
    s.rect(14, 38, 19, 39, ST_D)
    s.rect(8, 54, 23, 56, OL1); s.rect(9, 54, 22, 55, ST_M)
    for x in (9, 20):
        s.rect(x, 56, x + 2, 62, OL1); s.rect(x + 1, 56, x + 1, 61, ST_D)
    s.rect(8, 62, 24, 63, OL1)
    return s


def coat_stand():
    s = Spr(32, 64)
    s.rect(15, 6, 16, 60, OL1); s.rect(15, 7, 16, 59, WOOD_M); s.rect(15, 7, 15, 59, WOOD_L)
    for y, (a, b) in ((10, (8, 23)), (16, (9, 22))):
        s.line(15, y + 3, a, y, OL1); s.line(16, y + 3, b, y, OL1)
        s.set(a, y - 1, YEL); s.set(b, y - 1, YEL)
    # Mantel
    for y in range(14, 46):
        w = 5 + (y - 14) // 5
        for x in range(16 - w, 16 + w + 1):
            c = BLUE_D if x < 16 else BLUE_D
            if x < 16 - w + 2:
                c = BLUE_L
            elif x > 16 + w - 2:
                c = NB_M
            s.set(x, y, c)
    s.rect(10, 14, 22, 14, OL1)
    s.rect(15, 16, 16, 40, NB_M)
    for y in (20, 26, 32):
        s.set(15, y, YEL) if False else s.set(17, y, YEL)
    # Hut
    s.rect(6, 5, 12, 7, OL1)
    s.rect(7, 6, 11, 6, WOOD_D)
    s.rect(7, 1, 11, 4, OL1); s.rect(8, 2, 10, 4, WOOD_D)
    s.rect(8, 3, 10, 3, RED_D)
    s.rect(11, 59, 20, 63, OL1); s.rect(12, 60, 19, 62, WOOD_D)
    s.rect(7, 62, 24, 63, OL1)
    return s


def broom_bucket():
    s = Spr(32, 32)
    # Besen
    s.line(9, 3, 12, 24, OL1); s.line(10, 3, 13, 24, WOOD_L)
    for k in range(-3, 4):
        s.line(12, 22, 12 + k, 29, OL1)
    for k in range(-2, 3):
        s.line(12, 22, 12 + k, 28, SAND)
    s.rect(10, 22, 15, 23, ST_M)
    # Eimer
    for y in range(16, 30):
        t = (y - 16) / 13
        hw = int(round(6 + 1.5 * t))
        for x in range(23 - hw, 23 + hw):
            s.set(x, y, ST_M if x > 23 - hw + 2 else ST_L)
            if x > 23 + hw - 3:
                s.set(x, y, ST_D)
        s.set(23 - hw - 1, y, OL1); s.set(23 + hw, y, OL1)
    s.rect(16, 15, 29, 15, OL1); s.rect(17, 16, 28, 16, NB_L)
    s.rect(16, 29, 30, 30, OL1)
    s.rect(17, 22, 29, 22, ST_D)
    return s


def washbasin():
    s = Spr(32, 32)
    rect_o(s, 3, 12, 28, 30, WOOD_M)
    s.rect(4, 13, 27, 14, WOOD_L)
    ell_o(s, 16, 12, 10, 3, ST_L, OL1)
    s.ellipse(16, 12, 8, 1.8, NB_L)
    s.rect(11, 12, 14, 12, MOON)
    s.rect(15, 3, 16, 9, OL1); s.rect(15, 4, 16, 9, ST_M)
    s.rect(15, 3, 21, 4, OL1); s.rect(16, 3, 20, 3, ST_L)
    s.rect(20, 5, 21, 6, ST_M)
    s.rect(7, 20, 24, 29, OL1); s.rect(8, 21, 23, 28, WOOD_D); s.rect(15, 21, 16, 28, EARTH)
    s.set(14, 25, YEL); s.set(17, 25, YEL)
    return s


def wood_stack():
    s = Spr(32, 32)
    for row, (n, y) in enumerate(((4, 24), (3, 14))):
        for i in range(n):
            cx = (16 - (n - 1) * 3.5) + i * 7 if False else (8 + i * 8 if n == 4 else 12 + i * 8)
            ell_o(s, cx, y + 3, 4.2, 4.2, WOOD_M, OL1)
            s.ellipse(cx, y + 3, 2.8, 2.8, SAND)
            s.ellipse(cx, y + 3, 1.2, 1.2, WOOD_L)
    s.rect(2, 30, 29, 31, OL1)
    return s


def chandelier():
    s = Spr(32, 64)
    s.rect(15, 0, 16, 20, ST_D); s.rect(14, 0, 14, 20, OL1) if False else None
    for y in range(0, 20, 2):
        s.set(15, y, ST_L); s.set(16, y + 1, ST_D)
    s.rect(4, 22, 27, 26, OL1)
    s.rect(5, 23, 26, 24, ST_M); s.rect(5, 23, 26, 23, ST_L)
    s.rect(14, 26, 17, 32, OL1); s.rect(15, 26, 16, 31, ST_M)
    for x in (6, 12, 19, 25):
        s.rect(x, 17, x + 1, 22, OL1); s.rect(x, 18, x + 1, 22, CREAM)
        s.rect(x, 13, x + 1, 17, YEL); s.set(x, 15, ORA); s.set(x, 14, CREAM)
        s.set(x + 1, 12, ORA)
    for x in (8, 23):
        s.line(x, 26, x + (1 if x < 16 else -1), 34, ST_L)
        s.set(x + (1 if x < 16 else -1), 35, MOON)
    return s


def sconce():
    s = Spr(32, 32)
    s.rect(14, 10, 17, 24, OL1); s.rect(15, 11, 16, 23, ST_M)
    s.rect(10, 22, 21, 25, OL1); s.rect(11, 23, 20, 24, ST_L)
    s.rect(13, 12, 18, 16, OL1) if False else None
    s.rect(14, 5, 17, 11, OL1); s.rect(15, 6, 16, 10, CREAM)
    s.rect(15, 1, 16, 5, YEL); s.set(15, 3, ORA); s.set(15, 2, CREAM); s.set(16, 0, ORA)
    return s


def cellar_hatch():
    s = Spr(64, 32)
    rect_o(s, 4, 6, 59, 28, WOOD_D)
    planks(s, 6, 8, 57, 26, base=WOOD_M, lite=WOOD_L, dark=WOOD_D, seam=EARTH, vertical=False)
    s.rect(6, 8, 57, 8, WOOD_L)
    for x0 in (10, 48):
        s.rect(x0, 8, x0 + 2, 26, ST_M); s.rect(x0, 8, x0, 26, ST_L)
    ell_o(s, 32, 17, 5, 4, ST_M, OL1)
    s.ellipse(32, 17, 2.5, 1.8, CLEAR)
    return s


# ============================================================ BAU
def build():
    sh = Sheet(16, 11)
    P = sh.put
    # R0 Boeden
    P('boden_dielen_dunkel', 0, 0, floor_planks()); P('boden_dielen_abgewetzt', 1, 0, floor_planks('abgewetzt'))
    P('boden_saegespaene', 2, 0, floor_sawdust()); P('boden_steinplatten', 3, 0, floor_stone())
    P('boden_schachbrett', 4, 0, floor_stone(True)); P('boden_dielen_senkrecht', 5, 0, floor_vertical())
    P('laeufer', 6, 0, runner()); P('fussmatte', 7, 0, doormat())
    P('wandschatten_oben', 8, 0, shade_overlay('T')); P('wandschatten_links', 9, 0, shade_overlay('L'))
    P('wandschatten_rechts', 10, 0, shade_overlay('R')); P('schwelle', 11, 0, threshold())
    P('bierlache', 12, 0, puddle()); P('scherben', 13, 0, shards()); P('kippen', 14, 0, butts()); P('erdnussschalen', 15, 0, peanuts())
    # R1-2 Waende
    P('wand_tapete_rot', 0, 1, wall('rot')); P('wand_tapete_gruen', 1, 1, wall('gruen')); P('wand_holz', 2, 1, wall('holz'))
    P('fenster_nacht', 3, 1, window_wall('nacht')); P('fenster_lit', 4, 1, window_wall('lit'))
    P('fenster_tag', 5, 1, window_wall('tag')); P('fenster_vorhang', 6, 1, window_wall('curtain'))
    P('pendeltuer_innen', 7, 1, swing_door_inside())
    P('hintertuer', 9, 1, inner_door('zu')); P('tuer_offen', 10, 1, inner_door('offen')); P('kellertuer', 11, 1, inner_door('keller'))
    P('spiegelwand', 12, 1, mirror_wall())
    P('wand_ende_L', 14, 1, wall_end('L')); P('wand_ende_R', 15, 1, wall_end('R'))
    # R3-4 Regale + Deko
    P('regal_whisky', 0, 3, shelf_A()); P('regal_wein_bier', 2, 3, shelf_B()); P('regal_glaeser', 4, 3, shelf_glass())
    P('regal_gemischt', 6, 3, shelf_mixed()); P('fassregal', 8, 3, barrel_rack())
    P('glashalter', 10, 3, glass_rack())
    P('foto', 10, 4, photo()); P('foto_b', 11, 4, photo()); P('dartscheibe', 12, 3, dartboard()); P('geweih', 13, 3, antlers())
    P('wanduhr', 14, 3, wall_clock()); P('kalender', 15, 3, calendar())
    P('preistafel', 0, 10, price_board_inner()); P('plakat_kein_kredit', 4, 10, poster_credit())
    P('schild_ilhans_bar', 6, 10, sign_main())
    # R5-6 Theke
    P('theke_M', 0, 5, counter_base()); P('theke_ende_L', 1, 5, counter_base('L')); P('theke_ende_R', 2, 5, counter_base('R'))
    P('theke_glaeser', 3, 5, on_counter(prop_glasses)); P('theke_flaschen', 4, 5, on_counter(prop_bottles))
    P('theke_zapfhahn', 5, 5, on_counter(prop_tap)); P('theke_kasse', 6, 5, on_counter(prop_register))
    P('theke_kerze', 7, 5, on_counter(prop_candle)); P('theke_tablett', 8, 5, on_counter(prop_tray))
    P('theke_whisky', 9, 5, on_counter(prop_whisky)); P('theke_klappe_zu', 10, 5, on_counter(prop_gate_closed))
    P('theke_klappe_offen', 11, 5, on_counter(prop_gate_open)); P('theke_zigarren', 12, 5, on_counter(prop_cigar))
    P('theke_fass', 13, 5, on_counter(prop_keg)); P('theke_zeitung', 14, 5, on_counter(prop_paper))
    P('barhocker_vorne', 15, 5, barstool()); P('barhocker_seite', 15, 6, barstool(True))
    # R7 Moebel
    P('tisch_rund', 0, 7, round_table()); P('tisch_rund_gedeckt', 1, 7, round_table(True))
    P('tisch_lang', 2, 7, long_table()); P('pokertisch', 4, 7, poker_table())
    P('stuhl_vorne', 6, 7, chair('vorne')); P('stuhl_hinten', 7, 7, chair('hinten'))
    P('stuhl_links', 8, 7, chair('links')); P('stuhl_rechts', 9, 7, chair('rechts'))
    P('sitznische', 10, 7, booth()); P('spucknapf', 12, 7, spittoon())
    P('besen_eimer', 13, 7, broom_bucket()); P('waschbecken', 14, 7, washbasin()); P('holzstapel', 15, 7, wood_stack())
    # R8-9 gross
    P('klavier', 0, 8, piano()); P('kanonenofen', 2, 8, stove()); P('garderobe', 3, 8, coat_stand())
    P('kronleuchter', 4, 8, chandelier()); P('wandleuchte', 5, 8, sconce())
    P('haengelaterne', 6, 8, lantern('hang')); P('wandlaterne', 7, 8, lantern('wand'))
    P('kellerluke', 8, 8, cellar_hatch())
    return sh


def tile_fill(pl, name, x0, x1, y):
    for x in range(x0, x1):
        pl.append((name, x, y))


def preview(sh):
    W, Hh = 14, 10
    pl = []
    # Boden
    for y in range(2, Hh):
        for x in range(1, W - 1):
            nm = 'boden_dielen_dunkel' if (x + y) % 5 else 'boden_dielen_abgewetzt'
            if y >= 7 and 2 <= x <= 5:
                nm = 'boden_saegespaene'
            pl.append((nm, x, y))
    for x in range(1, W - 1):
        pl.append(('wandschatten_oben', x, 2))
    for y in range(2, Hh):
        pl.append(('wandschatten_links', 1, y)); pl.append(('wandschatten_rechts', W - 2, y))
    # Hinter der Theke Steinplatten
    for x in range(5, 11):
        pl.append(('boden_steinplatten', x, 2))
    # Waende (Reihen 0-1)
    walls = [(0, 'wand_ende_L'), (1, 'fenster_nacht'), (2, 'pendeltuer_innen'), (4, 'fenster_lit'), (5, 'regal_whisky'),
             (7, 'spiegelwand'), (9, 'regal_wein_bier'), (11, 'fenster_vorhang'), (12, 'hintertuer'), (13, 'wand_ende_R')]
    for x, nm in walls:
        pl.append((nm, x, 0))
    # Deko an der Wand
    pl.append(('dartscheibe', 1, 1, 0, 6 if False else 12))
    pl.append(('preistafel', 2, 1, 0, 28)) if False else None
    # Theke (Reihe 3-4), Platte auf Hoehe von Reihe 4
    cx = [('theke_ende_L', 'x'), ('theke_glaeser', 'x'), ('theke_flaschen', 'x'), ('theke_zapfhahn', 'x'), ('theke_kasse', 'x'),
          ('theke_tablett', 'x'), ('theke_ende_R', 'x')]
    for i, (nm, _) in enumerate(cx):
        pl.append((nm, 4 + i, 3, 0, 0))
    for i in range(3):
        pl.append(('barhocker_vorne', 5 + i * 2, 5, 0, -4))
    # Moebel
    pl.append(('klavier', 1, 3)); pl.append(('kanonenofen', 12, 3)); pl.append(('garderobe', 3, 3))
    pl.append(('tisch_rund_gedeckt', 3, 6)); pl.append(('stuhl_links', 2, 6, 8, 0)); pl.append(('stuhl_rechts', 4, 6, -8, 0))
    pl.append(('stuhl_hinten', 3, 5, 0, 12))
    pl.append(('pokertisch', 8, 7)); pl.append(('stuhl_vorne', 8, 6, 0, 4)); pl.append(('stuhl_hinten', 9, 8, 0, 0))
    pl.append(('stuhl_links', 7, 7, 14, 0)); pl.append(('stuhl_rechts', 10, 7, -14, 0))
    pl.append(('sitznische', 11, 7, 0, 0)); pl.append(('fussmatte', 2, 9)); pl.append(('schwelle', 2, 9, 0, -12))
    pl.append(('bierlache', 7, 5)); pl.append(('kippen', 10, 5)); pl.append(('erdnussschalen', 6, 8))
    pl.append(('kronleuchter', 6, 2, 0, -12)) if False else None
    out = compose(W, Hh, OL2, [p for p in pl if p], sh)
    return out


if __name__ == '__main__':
    sh = build()
    out = TILES + '/Tileset_Bar_Innen.png'
    sh.save(out)
    prev = preview(sh)
    prev.save(TILES + '/Bar_Innen_Vorschau.png')
    print('Innen Fremdfarben:', check_palette(out)[:5])
