"""Haus-Baukasten AUSSEN: Wandmaterialien + Dachmaterialien als Autotile-Saetze (Maske N1 E2 S4 W8).
Jedes Material: 16 Kanten-Kacheln + 4 Fuell-Varianten (Spalte 16-19; 16/17 kommen zufaellig in die Mitte)."""
from bk_lib import *

WALLS = ['fachwerk', 'holz', 'blockhaus', 'stein', 'backstein', 'kalk', 'blau', 'bruch']
ROOFS = ['schiefer', 'schindel', 'stroh', 'ziegel', 'moos', 'blech']


# ====================================================================== Wand-Texturen (32x32, periodisch)
def _vor_points(seed, cell=8, jit=0.8):
    pts = []
    for gy in range(32 // cell):
        for gx in range(32 // cell):
            ox = (hsh(gx, gy, seed) - 0.5) * jit * cell
            oy = (hsh(gx, gy, seed + 1) - 0.5) * jit * cell * 0.7
            pts.append((gx * cell + cell / 2 + ox, gy * cell + cell / 2 + oy, gx, gy))
    return pts


def _voronoi(x, y, pts):
    best = [(1e9, None), (1e9, None)]
    for px, py, gx, gy in pts:
        for wx in (-32, 0, 32):
            for wy in (-32, 0, 32):
                dx = (x + .5) - (px + wx)
                dy = ((y + .5) - (py + wy)) * 1.25
                d = math.sqrt(dx * dx + dy * dy)
                if d < best[0][0]:
                    best = [(d, (px + wx, py + wy, gx, gy)), best[0]]
                elif d < best[1][0]:
                    best[1] = (d, (px + wx, py + wy, gx, gy))
    return best


def wall_tex(mat, x, y, var):
    sd = 100 + var * 17
    if mat == 'holz':
        u, k = x % 8, x // 8
        joint = int(hsh(k, var, 4) * 26) + 3
        c = [EARTH, WOOD_L, WOOD_M, WOOD_M, WOOD_M, WOOD_M, WOOD_M, WOOD_D][u]
        if u in (2, 3, 4, 5, 6):
            r = ph(x, y, sd)
            if r < 0.06 or (u == 5 and (y + k * 5) % 11 < 3):
                c = WOOD_D
            elif r > 0.975:
                c = WOOD_L
        if y == joint and u != 0:
            c = EARTH
        if y == joint + 1 and u not in (0, 7):
            c = WOOD_L
        if u == 4 and y in (joint - 3, joint + 4) and var != 3:
            c = ST_L if y == joint - 3 else ST_D
        return c
    if mat == 'blockhaus':
        v = y % 8
        c = [OL2, WOOD_L, WOOD_L, WOOD_M, WOOD_M, WOOD_M, WOOD_D, EARTH][v]
        row = y // 8
        if v in (3, 4, 5):
            # Maserung: kurze Striche
            st = int(hsh(row, var, 9) * 32)
            if (x - st) % 13 < 4 and v == 4:
                c = WOOD_D
            if ph(x, y, sd) < 0.04:
                c = WOOD_D
        if v == 2 and ph(x, y, sd + 3) < 0.12:
            c = WOOD_M
        return c
    if mat == 'stein':
        row, cy = divmod(y, 8)
        off = (row % 2) * 8 + (4 if row == 2 else 0)
        xo = (x + off) % 16
        bi = ((x + off) % 32) // 16
        tone = hsh(bi, row, sd)
        base = ST_M if tone < 0.62 else (ST_L if tone < 0.9 else SV_L)
        if xo == 0 or cy == 7:
            return SV_D
        c = base
        if cy == 0:
            c = lt(base)
        elif cy == 6:
            c = dk(base)
        elif xo == 1:
            c = lt(base)
        elif xo == 15:
            c = dk(base)
        elif ph(x, y, sd) < 0.07:
            c = dk(base)
        return c
    if mat == 'backstein':
        row, cy = divmod(y, 4)
        off = (row % 2) * 4
        xo = (x + off) % 8
        bi = ((x + off) % 32) // 8
        if cy == 3 or xo == 0:
            return ST_M if ph(x, y, sd) > 0.1 else ST_D
        tone = hsh(bi, row, sd)
        base = RED_D if tone < 0.8 else SK_S
        c = base
        if cy == 0 and 1 <= xo <= 6:
            c = ROSE if (base == RED_D and hsh(bi, row, sd + 1) < 0.45) else base
        if cy == 2 or xo == 7:
            c = dk(base)
        return c
    if mat == 'kalk':
        c = MOON
        r = ph(x, y, sd)
        if r < 0.035:
            c = ST_L
        elif r > 0.992:
            c = SV_L
        # leichte Putzwellen
        if (y + int(hsh(x // 8, var, sd) * 6)) % 16 == 0 and ph(x, y, sd + 2) < 0.5:
            c = ST_L
        return c
    if mat == 'blau':
        v = y % 8
        c = [BLUE_L, BLUE_D, BLUE_D, BLUE_D, BLUE_D, BLUE_D, NB_M, OL2][v]
        if v in (2, 3, 4) and ph(x, y, sd) < 0.035:
            c = WOOD_M        # abgeblaetterte Farbe
        if v == 1 and ph(x, y, sd + 2) < 0.15:
            c = BLUE_L
        return c
    if mat == 'fachwerk':
        # Lehmputz mit Holzstaender (x 0-3) und Riegel (y 13-16)
        if x <= 3:
            return [EARTH, WOOD_M, WOOD_D, EARTH][x]
        if 13 <= y <= 16:
            return [EARTH, WOOD_M, WOOD_D, EARTH][y - 13]
        r = ph(x, y, sd)
        c = SAND
        if r < 0.05:
            c = WOOD_L
        elif r > 0.96:
            c = CREAM
        if x == 4 or y == 17:
            c = WOOD_L
        return c
    if mat == 'bruch':
        pts = _vor_points(77 + var * 0, 8, 0.9)
        (d1, p1), (d2, p2) = _voronoi(x, y, pts)
        if d2 - d1 < 1.1:
            return OL2
        tone = hsh(p1[2], p1[3], 31)
        base = ST_D if tone < 0.45 else (ST_M if tone < 0.8 else SV_M)
        dx, dy = (x + .5) - p1[0], (y + .5) - p1[1]
        c = base
        if dx + dy < -3.2:
            c = lt(base)
        elif dx + dy > 3.0:
            c = dk(base)
        if hsh(p1[2], p1[3], 50 + var) < 0.22 and dy < -1.5 and ph(x, y, sd) < 0.55:
            c = FOR_M if ph(x, y, sd + 1) < 0.6 else GRASS
        return c
    raise ValueError(mat)


def _fachwerk_strebe(s, kind):
    """Fuell-Variante: Strebe / Andreaskreuz im Fachwerk."""
    def beam(x0, y0, x1, y1):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i // n
            y = y0 + (y1 - y0) * i // n
            for k, c in enumerate((EARTH, WOOD_M, WOOD_D, EARTH)):
                s.set(x + k - 1, y, c)
    if kind == 1:
        beam(5, 12, 29, 0)
    elif kind == 2:
        beam(5, 31, 29, 18)
        beam(29, 31, 5, 18)


def wall_tile(mat, mask, var=0):
    s = tex_tile(lambda x, y, sd: wall_tex(mat, x, y, var), var)
    if mat == 'fachwerk' and var in (1, 2):
        _fachwerk_strebe(s, var)
        # Pfosten/Riegel wieder obenauf
        for y in range(32):
            for x in range(4):
                s.set(x, y, [EARTH, WOOD_M, WOOD_D, EARTH][x])
        for x in range(4, 32):
            for y in range(13, 17):
                s.set(x, y, [EARTH, WOOD_M, WOOD_D, EARTH][y - 13])
    if var == 3:
        _weather(s, mat)
    n, e, so, w = bool(mask & N), bool(mask & E), bool(mask & S), bool(mask & W)
    # ---------- Ecken (Seiten)
    for side, has in (('W', w), ('E', e)):
        if has:
            continue
        _corner(s, mat, side)
    # ---------- Sockel unten
    if not so:
        stone_base(s, 0, 24, 31, 31, seed=9)
        if mat in ('stein', 'bruch', 'backstein'):
            darken_rect(s, 0, 24, 31, 31)
        hline(s, 0, 31, 23, OL1)
        hline(s, 0, 31, 31, OL2)
        if not w:
            vline(s, 0, 23, 31, OL1)
        if not e:
            vline(s, 31, 23, 31, OL1)
            darken_rect(s, 28, 24, 30, 30)
    # ---------- Traufschatten oben
    if not n:
        if mat == 'fachwerk':
            for y in range(0, 5):
                hline(s, 0, 31, y, [EARTH, WOOD_M, WOOD_M, WOOD_D, EARTH][y])
        darken_rect(s, 0, 0, 31, 1, 2)
        darken_rect(s, 0, 2, 31, 3, 1)
    return s


def _weather(s, mat):
    """Fuell-Variante 4: verwittert (Risse, Moos, Flecken) - manuell setzen, nicht zufaellig."""
    pts = [(9, 6), (10, 7), (10, 8), (11, 9), (11, 10), (12, 11), (13, 11), (13, 12), (14, 13), (22, 20), (23, 21), (23, 22),
           (24, 23)]
    for x, y in pts:
        c = s.get(x, y)
        s.set(x, y, dk(c, 2))
    for x in range(3, 29):
        for y in range(24, 32):
            if hsh(x, y, 444) < (y - 22) * 0.06:
                s.set(x, y, FOR_M if hsh(x, y, 445) < 0.5 else GRASS)


def _corner(s, mat, side):
    xs = list(range(0, 8)) if side == 'W' else list(range(31, 23, -1))
    shade = 0 if side == 'W' else 1

    def put(i, y, c):
        s.set(xs[i], y, dk(c, shade))

    if mat in ('holz', 'blau', 'fachwerk'):
        cols = {'holz': [WOOD_L, WOOD_M, WOOD_M, WOOD_D], 'blau': [MOON, ST_L, ST_L, ST_M],
                'fachwerk': [WOOD_M, WOOD_D, WOOD_D, WOOD_D]}[mat]
        for y in range(32):
            for i, c in enumerate(cols):
                put(i + 1, y, c)
            put(5, y, EARTH if mat != 'blau' else NB_M)
    elif mat == 'blockhaus':
        for row in range(4):
            y0 = row * 8
            for yy in range(7):
                for i in range(1, 8):
                    dx, dy = i - 4, yy - 3
                    d = dx * dx + dy * dy * 1.3
                    if d <= 12:
                        c = SAND if d < 3 else (WOOD_L if d < 7 else WOOD_M)
                        if 4 <= d <= 5:
                            c = WOOD_M
                        if d > 9:
                            c = WOOD_D
                        put(i, y0 + yy, c)
            put(4, y0 + 3, WOOD_M)
    else:
        # Eckquader: abwechselnd lang/kurz
        base = {'stein': ST_L, 'backstein': ST_M, 'kalk': ST_L, 'bruch': ST_M}[mat]
        for row in range(4):
            y0 = row * 8
            ln = 7 if row % 2 == 0 else 5
            for yy in range(8):
                for i in range(1, ln + 1):
                    c = base
                    if yy == 0:
                        c = lt(base)
                    elif yy >= 6:
                        c = dk(base)
                    if i == ln:
                        c = dk(base, 2)
                    if yy == 7:
                        c = SV_D
                    put(i, y0 + yy, c)
    s.set(xs[0], 0, OL1)
    for y in range(32):
        s.set(xs[0], y, OL1)


# ====================================================================== Dach-Texturen
def roof_tex(mat, x, y, var):
    sd = 300 + var * 13
    if mat == 'schiefer':
        row, cy = divmod(y, 8)
        off = (row % 2) * 4
        xo = (x + off) % 8
        bi = ((x + off) % 32) // 8
        t = hsh(bi, row, sd)
        base = SV_D if t < 0.7 else (SV_M if t < 0.93 else NB_M)
        if cy == 7 or xo == 0:
            return OL2
        c = base
        if cy == 0:
            c = lt(base)
        elif cy == 6:
            c = dk(base)
        if xo == 7 and cy < 6:
            c = dk(base)
        return c
    if mat == 'schindel':
        row, cy = divmod(y, 8)
        xo = (x + (row % 2) * 4) % 8
        idx = ((x + (row % 2) * 4) % 32) // 8
        warm = hsh(idx, row, sd) < 0.9
        base, hi, sh = (WOOD_D, WOOD_M, EARTH) if warm else (SV_D, SV_M, OL2)
        c = base
        if cy == 0:
            c = hi
        elif cy >= 6:
            c = sh
        if xo == 0 and cy > 0:
            c = sh
        elif xo == 1 and 0 < cy < 6 and ph(x, y, sd + 9) < 0.35:
            c = hi
        return c
    if mat == 'stroh':
        row, cy = divmod(y, 8)
        k = (x + row * 3) % 32
        strand = hsh(k, row, sd)
        c = SAND if strand < 0.35 else (WOOD_L if strand < 0.8 else WOOD_M)
        if cy >= 6:
            c = dk(c)
        if cy == 7:
            c = WOOD_D if ph(x, y, sd) < 0.6 else WOOD_M
        if cy == 0 and ph(x, y, sd + 1) < 0.5:
            c = SAND
        if ph(x, y, sd + 3) < 0.03:
            c = CREAM
        return c
    if mat == 'ziegel':
        # Biberschwanz: Spalten 8 breit, Reihen 8 hoch, versetzt, runde Unterkante
        row, cy = divmod(y, 8)
        xo = (x + (row % 2) * 4) % 8
        bi = ((x + (row % 2) * 4) % 32) // 8
        t = hsh(bi, row, sd)
        base = RED_D if t < 0.7 else SK_S
        cut = cy == 7 and xo in (0, 1, 6, 7)
        if xo == 0 or cut:
            return EARTH
        c = base
        if cy == 7:
            c = dk(base)
        elif xo == 1 or cy == 0:
            c = ROSE if base == RED_D and cy < 4 else lt(base)
        elif xo == 7:
            c = dk(base)
        return c
    if mat == 'moos':
        c = roof_tex('schindel', x, y, var)
        m = 0.0
        for k in range(2):
            cx = hsh(k, var, sd + 40) * 32
            cy = hsh(k, var, sd + 41) * 32
            dx = min(abs(x - cx), 32 - abs(x - cx)) / (4 + 2 * hsh(k, 2, sd))
            dy = min(abs(y - cy), 32 - abs(y - cy)) / (2.5 + 1.5 * hsh(k, 3, sd))
            m = max(m, 1 - (dx * dx + dy * dy))
        m += (ph(x, y, sd + 42) - 0.5) * 0.7
        if m > 0.35:
            c = FOR_M if m < 0.7 else (GRASS if m < 0.9 else GRASS_L)
            if (y % 8) >= 6 and m < 0.5:
                c = FOR_D
        return c
    if mat == 'blech':
        u = x % 8
        c = [NB_L, NB_M, NB_M, NB_M, NB_M, NB_M, NB_D, OL2][u]
        if u == 0 and ph(x, y, sd) < 0.15:
            c = BLUE_L
        if u in (2, 3) and (y + x // 8 * 7) % 23 == 0:
            c = NB_L
        if u == 4 and hsh(x // 8, y // 10, sd + 2) < 0.12 and (y % 10) < 4:
            c = SK_S   # Rostlaeufer
        return c
    raise ValueError(mat)


RIDGE = {
    'schiefer': [OL1, ST_L, ST_M, ST_M, ST_D, OL2],
    'schindel': [OL1, WOOD_L, WOOD_M, WOOD_M, WOOD_D, EARTH],
    'stroh': [OL1, SAND, WOOD_L, WOOD_L, WOOD_M, WOOD_D, WOOD_D, EARTH],
    'ziegel': [OL1, ROSE, RED_D, RED_D, SK_S, EARTH],
    'moos': [OL1, WOOD_L, WOOD_M, WOOD_M, WOOD_D, EARTH],
    'blech': [OL1, MOON, NB_L, NB_L, NB_M, OL2],
}


def roof_tile(mat, mask, var=0):
    s = tex_tile(lambda x, y, sd: roof_tex(mat, x, y, var), var)
    if var == 3:
        # Flicken / Moosfleck (manuell)
        for y in range(9, 22):
            for x in range(10, 23):
                if (x - 16) ** 2 / 36 + (y - 15) ** 2 / 30 < 1:
                    c = s.get(x, y)
                    s.set(x, y, FOR_M if hsh(x, y, 9) < 0.5 else (GRASS if mat != 'blech' else SK_S))
    n, e, so, w = bool(mask & N), bool(mask & E), bool(mask & S), bool(mask & W)
    if not n:
        cols = RIDGE[mat]
        for y, c in enumerate(cols):
            hline(s, 0, 31, y, c)
        L = len(cols)
        if mat == 'ziegel':
            for x in range(0, 32, 8):
                for y in range(1, L - 1):
                    s.set(x, y, EARTH)
                s.set(x + 1, 1, CREAM if x % 16 == 0 else ROSE)
        elif mat == 'stroh':
            for x in range(4, 32, 8):
                for y in range(1, L - 1):
                    s.set(x, y, WOOD_D)
                    s.set(x + 1, y, EARTH)
        elif mat == 'blech':
            for x in range(0, 32, 4):
                s.set(x, 2, NB_M)
        else:
            for x in range(3, 32, 8):
                s.set(x, L - 3, dk(cols[3]))
        darken_rect(s, 0, L, 31, L, 1)
    if not so:
        if mat == 'stroh':
            # zottelige Strohkante, darunter Schatten
            for x in range(32):
                ln = 25 + int(hsh(x // 2, 7, 3) * 3)
                for y in range(22, 32):
                    if y <= ln:
                        c = s.get(x, y)
                        if y >= ln - 1:
                            c = WOOD_D
                        s.set(x, y, c)
                    else:
                        s.set(x, y, OL2 if y < 30 else OL1)
                s.set(x, ln + 1, OL1)
        else:
            hline(s, 0, 31, 21, dk(s.get(0, 21)))
            fas = [WOOD_L, WOOD_M, WOOD_M, WOOD_D, EARTH] if mat != 'blech' else [ST_L, NB_L, NB_M, NB_M, NB_D]
            hline(s, 0, 31, 22, OL1)
            for i, c in enumerate(fas):
                hline(s, 0, 31, 23 + i, c)
            if mat == 'blech':
                for x in range(6, 32, 16):
                    s.set(x, 24, MOON)
            else:
                for x in range(4, 32, 8):
                    s.set(x, 25, WOOD_D)
            hline(s, 0, 31, 28, OL1)
            for y in (29, 30, 31):
                hline(s, 0, 31, y, OL2 if y < 31 else OL1)
            for x in range(1, 32, 4):
                s.set(x, 29, SV_D)      # Sparrenkoepfe im Schatten
                s.set(x + 1, 29, SV_D)
    for side, has in (('W', w), ('E', e)):
        if has:
            continue
        xs = list(range(0, 6)) if side == 'W' else list(range(31, 25, -1))
        if mat == 'stroh':
            for y in range(32):
                s.set(xs[0], y, OL1)
                s.set(xs[1], y, dk(s.get(xs[1], y), 2 if side == 'E' else 1))
                s.set(xs[2], y, dk(s.get(xs[2], y), 1))
            continue
        if mat == 'blech':
            cols = [OL1, MOON, NB_L, NB_M, OL2, OL1] if side == 'W' else [OL1, NB_L, NB_M, NB_D, OL2, OL1]
        else:
            cols = [OL1, WOOD_L, WOOD_M, WOOD_M, WOOD_D, OL1] if side == 'W' else [OL1, WOOD_M, WOOD_D, WOOD_D, EARTH, OL1]
        ytop = 0
        ybot = 31 if so else 28
        for i, c in enumerate(cols):
            for y in range(ytop, ybot + 1):
                s.set(xs[i], y, c)
        if not so:
            for y in range(29, 32):
                s.set(xs[0], y, OL1)
        for y in range(ytop + 4, ybot, 9):
            s.set(xs[3], y, dk(cols[3]))
    return s


EDGE_VAR = (11, 14, 10)   # lange Kanten-Laeufe (oben, unten, einzeilig) bekommen je 2 Zufallsvarianten


def autotile_set(fn, mat):
    """26 Kacheln: 0-15 Maske, 16/17 = Fuellung Var 1/2 (zufaellig), 18 = verwittert (manuell), 19 = Fuellung Var 4,
    20/21 = Maske 11 Var 1/2, 22/23 = Maske 14 Var 1/2, 24/25 = Maske 10 Var 1/2 (alle zufaellig in der RuleTile)."""
    tiles = [fn(mat, m, 0) for m in range(16)]
    tiles += [fn(mat, 15, 1), fn(mat, 15, 2), fn(mat, 15, 3), fn(mat, 15, 4)]
    for m in EDGE_VAR:
        tiles += [fn(mat, m, 1), fn(mat, m, 2)]
    return tiles
