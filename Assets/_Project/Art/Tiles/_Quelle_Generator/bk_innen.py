"""Haus-Baukasten INNEN: Boeden (nahtlos, 3 Varianten), Wandflaechen (Autotile N1 E2 S4 W8), Mauerkronen
(Autotile + Innenecken), Schatten-Overlays. Ansicht 3/4 von vorne, Licht oben links."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
from bk_lib import *

FLOORS = ['dielen_hell', 'dielen_dunkel', 'dielen_rot', 'parkett', 'steinplatten', 'pflaster', 'lehm', 'stroh',
          'fliesen_schach', 'fliesen_blau', 'bohlen', 'kirchenstein']
IWALLS = ['putz', 'tapete_rot', 'tapete_blau', 'tapete_gruen', 'holz', 'stein', 'backstein', 'kalk']
CROWNS = ['violett', 'holz', 'stein']


# ====================================================================== Boeden
def floor_px(kind, x, y, var):
    sd = 500 + var * 11
    if kind in ('dielen_hell', 'dielen_dunkel', 'dielen_rot'):
        pal = {'dielen_hell': (WOOD_L, SAND, WOOD_M, WOOD_D), 'dielen_dunkel': (WOOD_M, WOOD_L, WOOD_D, EARTH),
               'dielen_rot': (SK_S, SK_M, EARTH, OL2)}[kind]
        b, hi, lo, seam = pal
        row, v = divmod(y, 8)
        joint = int(hsh(row, var, sd) * 30) + 1
        if v == 7:
            return seam
        if (x - joint) % 32 == 0:
            return seam
        c = b
        if v == 0:
            c = hi
        elif v == 6:
            c = lo
        r = ph(x, y, sd)
        if v in (2, 3, 4) and ((x + row * 7) % 13 < 3 and v == 3):
            c = lo
        if r < 0.04:
            c = lo
        if (x - joint) % 32 in (2, 29) and v == 3 and var != 2:
            c = ST_D       # Nagel
        return c
    if kind == 'parkett':
        bx, by = x // 8, y // 8
        u, v = x % 8, y % 8
        horiz = (bx + by) % 2 == 0
        k = v if horiz else u
        c = [WOOD_L, WOOD_M, WOOD_M, WOOD_D][(k // 2) % 4] if False else (WOOD_M if k % 4 else WOOD_D)
        if k % 4 == 1:
            c = WOOD_L
        if ph(x, y, sd) < 0.04:
            c = WOOD_D
        if u == 0 and not horiz or v == 0 and horiz:
            pass
        return c
    if kind == 'steinplatten':
        row, v = divmod(y, 16)
        off = (row % 2) * 8
        u = (x + off) % 16
        if v == 15 or u == 15:
            return ST_D
        t = hsh(((x + off) % 32) // 16, row, sd)
        b = ST_M if t < 0.75 else ST_L
        c = b
        if v == 0 or u == 0:
            c = lt(b)
        elif v == 14 or u == 14:
            c = dk(b)
        if ph(x, y, sd) < 0.05:
            c = dk(b)
        return c
    if kind == 'pflaster':
        pts = []
        for gy in range(4):
            for gx in range(4):
                pts.append((gx * 8 + 4 + (hsh(gx, gy, 7) - .5) * 4, gy * 8 + 4 + (hsh(gx, gy, 8) - .5) * 3, gx, gy))
        best = [(1e9, None), (1e9, None)]
        for px, py, gx, gy in pts:
            for wx in (-32, 0, 32):
                for wy in (-32, 0, 32):
                    d = math.hypot(x + .5 - px - wx, y + .5 - py - wy)
                    if d < best[0][0]:
                        best = [(d, (px + wx, py + wy, gx, gy)), best[0]]
                    elif d < best[1][0]:
                        best[1] = (d, None)
        if best[1][0] - best[0][0] < 1.2:
            return OL2
        p = best[0][1]
        b = [ST_M, ST_M, ST_L, ST_D][int(hsh(p[2], p[3], sd) * 4)]
        dx, dy = x + .5 - p[0], y + .5 - p[1]
        return lt(b) if dx + dy < -2.5 else (dk(b) if dx + dy > 2.5 else b)
    if kind == 'lehm':
        r = hsh(x // 3, y // 2, sd)
        c = WOOD_M if r < 0.6 else (WOOD_L if r < 0.85 else WOOD_D)
        if ph(x, y, sd + 1) < 0.03:
            c = SAND
        return c
    if kind == 'stroh':
        k = (x * 3 + y * 7) % 11
        r = ph(x, y, sd)
        c = SAND if r < 0.4 else (WOOD_L if r < 0.85 else WOOD_M)
        if (x + int(hsh(y // 2, 1, sd) * 6)) % 5 == 0:
            c = WOOD_M
        if r > 0.97:
            c = CREAM
        return c
    if kind == 'fliesen_schach':
        u, v = x % 16, y % 16
        dark = ((x // 16) + (y // 16)) % 2
        b = SK_M if dark else SAND
        if u == 15 or v == 15:
            return WOOD_D
        c = b
        if u == 0 or v == 0:
            c = lt(b) if not dark else SK_L
        elif u == 14 or v == 14:
            c = dk(b)
        if ph(x, y, sd) < 0.03:
            c = dk(b)
        return c
    if kind == 'fliesen_blau':
        u, v = x % 16, y % 16
        if u == 15 or v == 15:
            return ST_M
        c = MOON
        # blaues Ornament
        du, dv = abs(u - 7), abs(v - 7)
        if du + dv in (5, 6) or (du == 0 and dv < 3) or (dv == 0 and du < 3):
            c = BLUE_D
        if du + dv == 0:
            c = BLUE_L
        if u == 0 or v == 0:
            c = ST_L if c == MOON else c
        return c
    if kind == 'bohlen':
        col, u = divmod(x, 16)
        joint = int(hsh(col, var, sd) * 30)
        if u == 15:
            return EARTH
        if (y - joint) % 32 == 0:
            return EARTH
        c = WOOD_M
        if u == 0:
            c = WOOD_L
        elif u == 14:
            c = WOOD_D
        if (u + y // 5) % 7 == 0 and u not in (0, 14):
            c = WOOD_D
        if ph(x, y, sd) < 0.04:
            c = WOOD_L
        if u in (3, 11) and (y - joint) % 32 in (3, 28):
            c = OL2
        return c
    if kind == 'kirchenstein':
        u, v = x % 32, y % 16
        off = ((y // 16) % 2) * 16
        u = (x + off) % 32
        if v == 15 or u == 31:
            return ST_M
        c = ST_L
        if v == 0 or u == 0:
            c = MOON
        if ph(x, y, sd) < 0.05:
            c = ST_M
        return c
    raise ValueError(kind)


def floor_tile(kind, var):
    return tex_tile(lambda x, y, sd: floor_px(kind, x, y, var), var)


# ====================================================================== Wandflaechen
IW = {
    'putz': (SAND, WOOD_L, CREAM), 'tapete_rot': (RED_D, SK_S, ROSE), 'tapete_blau': (BLUE_D, NB_M, BLUE_L),
    'tapete_gruen': (FOR_M, FOR_D, GRASS), 'holz': (WOOD_M, WOOD_D, WOOD_L), 'stein': (ST_M, ST_D, ST_L),
    'backstein': (RED_D, SK_S, ROSE), 'kalk': (MOON, ST_L, CREAM),
}


def iwall_px(mat, x, y, var):
    b, lo, hi = IW[mat]
    sd = 700 + var * 5
    if mat == 'putz':
        r = ph(x, y, sd)
        return WOOD_L if r < 0.05 else (CREAM if r > 0.97 else SAND)
    if mat == 'kalk':
        r = ph(x, y, sd)
        return ST_L if r < 0.04 else MOON
    if mat.startswith('tapete'):
        # Streifen + Medaillon-Muster (periodisch 8/16)
        u, v = x % 8, y % 16
        c = b
        if u == 0:
            c = lo
        if mat == 'tapete_rot':
            if (u, v) in ((4, 4), (3, 5), (5, 5), (4, 6), (4, 12)):
                c = hi
        elif mat == 'tapete_blau':
            if u in (3, 5) and v % 4 == 0 or (u == 4 and v % 4 == 2):
                c = hi
        else:
            if u == 4 and v in (2, 3, 4, 10, 11, 12) or (v in (3, 11) and u in (3, 5)):
                c = hi if v < 8 else GRASS_L
        return c
    if mat == 'holz':
        u = x % 8
        return [EARTH, WOOD_L, WOOD_M, WOOD_M, WOOD_M, WOOD_M, WOOD_M, WOOD_D][u] if ph(x, y, sd) > 0.05 else WOOD_D
    if mat == 'stein':
        row, v = divmod(y, 8)
        u = (x + (row % 2) * 8) % 16
        if v == 7 or u == 0:
            return SV_D
        c = ST_M if hsh(((x + (row % 2) * 8) % 32) // 16, row, sd) < 0.7 else ST_D
        if v == 0:
            c = lt(c)
        return c
    if mat == 'backstein':
        row, v = divmod(y, 4)
        u = (x + (row % 2) * 4) % 8
        if v == 3 or u == 0:
            return ST_M
        c = RED_D if hsh(((x + (row % 2) * 4) % 32) // 8, row, sd) < 0.8 else SK_S
        if v == 0 and u in (2, 3, 4):
            c = ROSE if c == RED_D else c
        return c
    raise ValueError(mat)


def iwall_tile(mat, mask, var=0):
    s = tex_tile(lambda x, y, sd: iwall_px(mat, x, y, var), var)
    n, e, so, w = bool(mask & N), bool(mask & E), bool(mask & S), bool(mask & W)
    if not so:
        # Lambris unten (Holz-Vertaefelung) + Fussleiste, nur bei Tapete/Putz/Kalk
        if mat in ('putz', 'tapete_rot', 'tapete_blau', 'tapete_gruen', 'kalk'):
            hline(s, 0, 31, 9, OL1)
            hline(s, 0, 31, 10, WOOD_L)
            hline(s, 0, 31, 11, WOOD_M)
            hline(s, 0, 31, 12, WOOD_D)
            for y in range(13, 28):
                for x in range(32):
                    u = x % 16
                    c = WOOD_M
                    if u in (1, 14) or y in (15, 25):
                        c = WOOD_D if u == 14 or y == 25 else WOOD_L
                    if u in (0, 15):
                        c = EARTH
                    if 2 <= u <= 13 and 16 <= y <= 24:
                        c = WOOD_M if (u + y) % 9 else WOOD_D
                    s.set(x, y, c)
        hline(s, 0, 31, 27, OL1)
        for y in (28, 29, 30):
            hline(s, 0, 31, y, [WOOD_L, WOOD_M, WOOD_D][y - 28])
        hline(s, 0, 31, 31, OL1)
    if not n:
        # Deckenleiste + Schatten von der Mauerkrone
        hline(s, 0, 31, 0, OL1)
        hline(s, 0, 31, 1, WOOD_D)
        hline(s, 0, 31, 2, WOOD_M)
        hline(s, 0, 31, 3, EARTH)
        darken_rect(s, 0, 4, 31, 5, 1)
    if not w:
        vline(s, 0, 0, 31, OL1)
        darken_rect(s, 1, 0, 2, 31, 1)
    if not e:
        vline(s, 31, 0, 31, OL1)
        darken_rect(s, 28, 0, 30, 31, 1)
    if var == 3:
        # Risse / Fleck (manuell)
        for (x, y) in ((8, 6), (9, 7), (9, 8), (10, 9), (11, 9), (12, 10), (12, 11), (21, 4), (22, 5), (22, 6)):
            s.set(x, y, dk(s.get(x, y), 2))
    return s


# ====================================================================== Mauerkronen (Raumrand von oben)
CR = {'violett': (SV_D, SV_M, OL2, SV_L), 'holz': (WOOD_D, WOOD_M, EARTH, WOOD_L), 'stein': (ST_D, ST_M, SV_D, ST_L)}


def crown_tile(mat, mask, inner=None):
    b, hi, lo, hl = CR[mat]
    s = Spr(32, 32)
    for y in range(32):
        for x in range(32):
            row, v = divmod(y, 8)
            u = (x + (row % 2) * 8) % 16
            c = b
            if v == 7 or u == 0:
                c = lo
            elif v == 0:
                c = hi
            s.set(x, y, c)
    n, e, so, w = bool(mask & N), bool(mask & E), bool(mask & S), bool(mask & W)
    if not n:
        hline(s, 0, 31, 0, OL1)
        hline(s, 0, 31, 1, hl)
        hline(s, 0, 31, 2, hi)
    if not so:
        hline(s, 0, 31, 31, OL1)
        hline(s, 0, 31, 30, lo)
    if not w:
        vline(s, 0, 0, 31, OL1)
        vline(s, 1, 0 if n else 0, 31, hi)
    if not e:
        vline(s, 31, 0, 31, OL1)
        vline(s, 30, 0, 31, lo)
    # Ecken sauber
    if not n and not w:
        s.set(1, 1, OL1)
    if not n and not e:
        s.set(30, 1, OL1)
    if not so and not w:
        s.set(1, 30, OL1)
    if not so and not e:
        s.set(30, 30, OL1)
    if inner:
        # Innenecke: diagonal fehlender Nachbar -> 2x2 Eck-Kante
        cx, cy = {'NO': (31, 0), 'SO': (31, 31), 'SW': (0, 31), 'NW': (0, 0)}[inner]
        dx = -1 if cx else 1
        dy = -1 if cy else 1
        for i in range(3):
            s.set(cx + dx * i, cy, OL1 if i == 0 else s.get(cx + dx * i, cy))
            s.set(cx, cy + dy * i, OL1 if i == 0 else s.get(cx, cy + dy * i))
        s.set(cx, cy, OL1)
        s.set(cx + dx, cy, OL1)
        s.set(cx, cy + dy, OL1)
    return s


def crown_set(mat):
    t = [crown_tile(mat, m) for m in range(16)]
    t += [crown_tile(mat, 15, k) for k in ('NO', 'SO', 'SW', 'NW')]
    return t


# ====================================================================== Schatten-Overlays (Boden)
def shade(kind):
    s = Spr(32, 32)
    for y in range(32):
        for x in range(32):
            if kind == 'oben':
                lv = 10 if y < 4 else (6 if y < 8 else (3 if y < 12 else 0))
            elif kind == 'links':
                lv = 10 if x < 3 else (5 if x < 6 else 0)
            elif kind == 'rechts':
                lv = 10 if x > 28 else (5 if x > 25 else 0)
            elif kind == 'ecke_links':
                lv = max(10 if y < 4 else (6 if y < 8 else (3 if y < 12 else 0)), 10 if x < 3 else (5 if x < 6 else 0))
            else:
                lv = max(10 if y < 4 else (6 if y < 8 else (3 if y < 12 else 0)), 10 if x > 28 else (5 if x > 25 else 0))
            B = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
            if B[y % 4][x % 4] < lv:
                s.set(x, y, OL2)
    return s


def threshold():
    s = Spr(32, 32)
    box(s, 2, 22, 29, 31, WOOD_L, hi=SAND, lo=WOOD_D)
    hline(s, 3, 28, 26, WOOD_M)
    return s


def doormat(c=RED_D):
    s = Spr(32, 32)
    box(s, 3, 8, 28, 24, c, hi=lt(c), lo=dk(c))
    for x in range(5, 27, 2):
        vline(s, x, 10, 22, dk(c))
    for x in range(3, 29, 2):
        s.set(x, 7, SAND)
        s.set(x, 25, SAND)
    return s
