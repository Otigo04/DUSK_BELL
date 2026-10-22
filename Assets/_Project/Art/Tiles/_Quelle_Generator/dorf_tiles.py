"""Tileset_Dorf.png: Overlay-Autotiles (Pflaster, Platten, Kies) mit transparentem Rand + Weg-Details.
Die Overlays liegen auf dem Erdboden: Kante = dunkler Rand, Moos, ausgefranste Kiesel -> sauberer Uebergang Erde/Pflaster/Kies.
Spalte 0-15 Autotile-Maske (N=1 E=2 S=4 W=8), 16-19 Innenecken (NO, SO, SW, NW), wie Tileset_Terrain.
Aufruf: python dorf_tiles.py   (schreibt Art/Tiles/Tileset_Dorf.png und Vorschau)"""
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nwlib import *
import autotile
import paths

COLS = 20
MOSS = [GREEN[1], GREEN[2], GREEN[3]]


# ----------------------------------------------------------------- Texturen (periodisch, 32 px)
def dim(c):
    """eine Stufe dunkler auf der Stein-Rampe (Moertel STONE[0] und Rand bleiben)"""
    for i in (5, 4, 3, 2):
        if c == STONE[i]:
            return STONE[i - 1]
    return c


def cobble_tex(v=0, moss=0.0, wet=False):
    def f(x, y):
        x %= 32
        y %= 32
        c = dim(paths.cobble(x, y, v))
        if moss > 0:
            cl = hsh(x // 4, y // 3, 900 + v)          # Moos waechst in Flecken
            if c == STONE[0] and cl < moss * 1.6 and hsh(x, y, 910 + v) < 0.8:
                c = MOSS[0] if hsh(x, y, 911 + v) < 0.6 else MOSS[1]
            elif c != STONE[0] and cl < moss and hsh(x, y, 912 + v) < 0.7:
                c = MOSS[1] if hsh(x, y, 913 + v) < 0.55 else (MOSS[2] if hsh(x, y, 914) < 0.7 else GREEN[4])
        if wet and c != STONE[0] and hsh(x // 5, y // 4, 920 + v) < 0.3 and c in (STONE[3], STONE[4], STONE[5]):
            c = STONE[2] if c == STONE[3] else STONE[3]
        return c
    return f


def slab_tex(v=0, moss=0.0):
    """grosse Platten (16 px breit, versetzt), Fugen dunkel"""
    def f(x, y):
        x %= 32
        y %= 32
        row = 0 if y < 16 else 1
        by = y - row * 16
        xx = (x + (8 if row else 0)) % 32
        bx = xx % 16
        bi = xx // 16
        if bx == 15 or by == 15:
            c = STONE[0] if hsh(x, y, 940 + v) > 0.12 else PURP[2]
            if moss and hsh(x // 3, y // 3, 941 + v) < moss * 1.5 and hsh(x, y, 942) < 0.8:
                c = MOSS[0]
            return c
        h = hsh(bi, row, 950 + v)
        base = 3 if h < 0.45 else (2 if h < 0.8 else 4)
        if by == 0 or bx == 0:
            base = min(4, base + 1)
        elif by == 14 or bx == 14:
            base = max(1, base - 1)
        # Sprung / Abplatzer
        if hsh(bi, row, 960 + v) < 0.35:
            cx, cy = 3 + int(hsh(bi, row, 961) * 9), 3 + int(hsh(bi, row, 962) * 9)
            if bx == cx and 2 <= by <= 9 and abs(by - cy) < 4:
                base = 1
        if hsh(x, y, 970 + v) < 0.05 and base > 1:
            base -= 1
        if hsh(x, y, 971 + v) < 0.03 and base < 4:
            base += 1
        c = STONE[base]
        if moss:
            cl = hsh(x // 4, y // 4, 972 + v)
            if cl < moss and hsh(x, y, 973 + v) < 0.7:
                c = MOSS[1] if hsh(x, y, 974) < 0.6 else MOSS[2]
        return c
    return f


def gravel_tex(v=0):
    def f(x, y):
        x %= 32
        y %= 32
        h = hsh(x, y, 1000 + v)
        c = BROWN[4]
        if h < 0.17:
            c = BROWN[5]
        elif h < 0.34:
            c = BROWN[3]
        elif h < 0.40:
            c = BROWN[2]
        elif h < 0.44:
            c = STONE[4]
        elif h < 0.465:
            c = STONE[2]
        if hsh(x // 2, y // 2, 1100 + v) < 0.06 and x % 2 == 0 and y % 2 == 0:
            c = STONE[3]
        if hsh(x // 3, y // 3, 1200 + v) < 0.07 and c == BROWN[4]:
            c = BROWN[3]
        return c
    return f


# ----------------------------------------------------------------- Overlay-Render
def render_overlay(mask, notch, tex, seed, edge=None, rd=None, rl=None, fringe=(), over=(G_MD, G_BASE), over_p=0.16, soft=None):
    ins, con = autotile.build_mask(mask, notch)

    def inside(x, y):
        if 0 <= x < 32 and 0 <= y < 32:
            return ins[y][x]
        if y < 0:
            return con['N']
        if y > 31:
            return con['S']
        if x < 0:
            return con['W']
        return con['E']

    out = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    op = out.load()
    for y in range(32):
        for x in range(32):
            if not ins[y][x]:
                continue
            nb = [inside(x + 1, y), inside(x - 1, y), inside(x, y + 1), inside(x, y - 1)]
            ring1 = not all(nb)
            c = tex(x, y)
            if ring1:
                if soft is not None:        # weicher Rand (Kies): kein harter Umriss
                    c = soft[0] if hsh(x, y, seed + 11) < 0.55 else soft[1]
                else:
                    c = edge
                    if hsh(x, y, seed + 11) < over_p:
                        c = over[int(hsh(x, y, seed + 12) * len(over))]
            elif rd is not None:
                d2 = [inside(x + 2, y), inside(x - 2, y), inside(x, y + 2), inside(x, y - 2)]
                dg = [inside(x + 1, y + 1), inside(x - 1, y - 1), inside(x + 1, y - 1), inside(x - 1, y + 1)]
                if not d2[0] or not d2[2] or not dg[0]:
                    c = rd
                elif not d2[1] or not d2[3] or not dg[1]:
                    c = rl
            op[x, y] = c
    # Saum ausserhalb: Kiesel, Moos, Erdkruemel -> Uebergang wirkt gewachsen statt abgeschnitten
    for y in range(32):
        for x in range(32):
            if ins[y][x]:
                continue
            d1 = any(inside(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            d2 = (not d1) and any(inside(x + a, y + b) for a, b in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, -1), (1, -1), (-1, 1)))
            if not (d1 or d2):
                continue
            r = hsh(x, y, seed + 21)
            acc = 0.0
            for col, p1, p2 in fringe:
                acc += p1 if d1 else p2
                if r < acc:
                    op[x, y] = col
                    break
    return out


def autoset(kind, variant):
    """liefert 20 Kacheln (0..15 Masken, 16..19 Innenecken)"""
    out = []
    for idx in range(20):
        mask, notch = (idx, None) if idx < 16 else (15, ['NE', 'SE', 'SW', 'NW'][idx - 16])
        seed = 100 * variant + idx + {'cobble': 0, 'slab': 400, 'gravel': 800}[kind]
        if kind == 'cobble':
            t = render_overlay(mask, notch, cobble_tex(variant, 0.08 + 0.10 * variant), seed, edge=PURP[2], rd=STONE[1], rl=STONE[4],
                               fringe=((STONE[2], .16, .06), (GREEN[2], .14, .05), (BROWN[2], .14, .05), (STONE[4], .05, .02)))
        elif kind == 'slab':
            t = render_overlay(mask, notch, slab_tex(variant, 0.04 + 0.08 * variant), seed, edge=PURP[2], rd=STONE[1], rl=STONE[5],
                               fringe=((STONE[2], .14, .05), (GREEN[2], .12, .05), (BROWN[2], .12, .04)), over_p=0.10)
        else:
            t = render_overlay(mask, notch, gravel_tex(variant), seed, soft=(BROWN[3], BROWN[2]),
                               fringe=((BROWN[4], .30, .10), (STONE[3], .12, .05), (BROWN[2], .14, .06), (STONE[1], .04, .02), (GREEN[2], .05, .02)))
        out.append(t)
    return out


# ----------------------------------------------------------------- Fuellkacheln
def fills(kind):
    res = []
    n = {'cobble': 12, 'slab': 10, 'gravel': 10}[kind]
    for i in range(n):
        if kind == 'cobble':
            m = [0.0, 0.0, 0.02, 0.10, 0.14, 0.2, 0.28, 0.36, 0.08, 0.1, 0.06, 0.04][i]
            tex = cobble_tex(i % 3, m, wet=(i == 10))
        elif kind == 'slab':
            m = [0, 0, 0.02, 0.1, 0.16, 0.24, 0.06, 0.04, 0.3, 0.1][i]
            tex = slab_tex(i % 3, m)
        else:
            tex = gravel_tex(i % 4)
        im = Image.new('RGBA', (32, 32))
        p = im.load()
        for y in range(32):
            for x in range(32):
                p[x, y] = tex(x, y)
        # Besonderheiten auf Fuellkacheln
        sp = Spr(32, 32)
        sp.im = im
        sp.p = im.load()
        if kind == 'cobble' and i == 8:       # Riss
            x0 = 6
            for k in range(22):
                sp.set(x0 + k, 14 + int(3 * math.sin(k * 0.5)), STONE[0])
                if k % 5 == 3:
                    sp.set(x0 + k, 15 + int(3 * math.sin(k * 0.5)), PURP[2])
        if kind == 'cobble' and i == 9:       # Grasbueschel in der Fuge
            for bx, by in ((9, 22), (23, 11)):
                for k, (dx, dy, c) in enumerate(((0, 0, GREEN[2]), (-1, -1, GREEN[3]), (1, -2, GREEN[4]), (0, -3, GREEN[4]), (-2, -3, GREEN[3]), (2, -4, GREEN[5]))):
                    sp.set(bx + dx, by + dy, c)
        if kind == 'cobble' and i == 10:      # Pfuetze
            sp.ellipse(16, 17, 9, 5, BLUE[1])
            sp.ellipse(15, 16, 7, 3.5, BLUE[2])
            for (x, y) in ((11, 15), (12, 15), (19, 17)):
                sp.set(x, y, BLUE[4])
        if kind == 'cobble' and i == 11:      # Laub
            for (x, y, c) in ((8, 10, ORANGE), (9, 10, AMBER), (22, 22, BROWN[2]), (23, 22, ORANGE), (14, 25, BROWN[3])):
                sp.set(x, y, c)
        if kind == 'slab' and i == 7:         # Unkraut in Fuge
            for bx, by in ((15, 15), (31, 15)):
                for (dx, dy, c) in ((0, 0, GREEN[2]), (-1, -1, GREEN[3]), (1, -2, GREEN[4]), (0, -3, GREEN[5])):
                    sp.set(bx + dx, by + dy, c)
        if kind == 'gravel' and i == 8:       # groesserer Stein
            sp.ellipse(20, 18, 3, 2, STONE[3])
            sp.set(19, 17, STONE[5])
            sp.set(22, 19, STONE[1])
        res.append(sp.im)
    return res


# ----------------------------------------------------------------- Dekor / Details (transparent)
def decal(draw, seed=0):
    sp = Spr(32, 32)
    draw(sp, seed)
    return sp.im


def rut_h(sp, s):
    # zwei Spurrillen, periodisch -> nahtlos
    for base in (9 + s % 2, 21 - s % 2):
        for x in range(32):
            off = int(round(1.0 * math.sin(2 * math.pi * x / 32.0 * (1 + s % 2))))
            y = base + off
            if hsh(x, base, 1300 + s) < 0.92:
                sp.set(x, y, BROWN[1])
                if hsh(x, y, 1301 + s) < 0.5:
                    sp.set(x, y + 1, BROWN[2])
            if hsh(x, base, 1302 + s) < 0.12:
                sp.set(x, y - 1, BROWN[5])


def rut_v(sp, s):
    tmp = Spr(32, 32)
    rut_h(tmp, s)
    for y in range(32):
        for x in range(32):
            c = tmp.get(x, y)
            if c[3]:
                sp.set(y, x, c)


def puddle(sp, s):
    cx, cy = 15 + (s % 2) * 2, 16
    night, mid, hi = H('2c3e56'), H('3f5570'), H('6b7fb8')
    sp.ellipse(cx, cy, 12 - s * 2, 6, BROWN[1])          # nasser, dunkler Rand
    sp.ellipse(cx, cy, 11 - s * 2, 5, night)
    sp.ellipse(cx - 1, cy - 1, 8 - s * 2, 3.2, mid)
    for (x, y) in ((cx - 5, cy - 2), (cx - 4, cy - 2), (cx + 3, cy), (cx + 4, cy)):
        sp.set(x, y, hi)
    sp.set(cx - 3, cy + 1, mid)
    for k in range(4):
        sp.set(cx - 10 + k * 6 + s, cy + 6, BROWN[2])


def tuft(sp, s):
    bx, by = 10 + s * 5, 22
    blades = [(0, 0, 4, GREEN[3]), (-2, 0, 3, GREEN[2]), (2, 0, 5, GREEN[4]), (4, 0, 3, GREEN[3]), (-4, 0, 2, GREEN[2])]
    for dx, _, h, c in blades:
        for k in range(h):
            sp.set(bx + dx + (k // 2) * (1 if dx > 0 else -1 if dx < 0 else 0), by - k, c)
    sp.set(bx, by - 5, GREEN[5])
    if s % 2:
        sp.set(bx + 3, by - 6, PINK)
        sp.set(bx + 3, by - 5, GREEN[3])


def stones(sp, s):
    for k in range(3 + s):
        x, y = 4 + int(hsh(k, s, 1400) * 22), 6 + int(hsh(k, s, 1401) * 20)
        sp.set(x, y, STONE[3])
        sp.set(x + 1, y, STONE[2])
        if k % 2:
            sp.set(x, y - 1, STONE[4])
            sp.set(x + 1, y + 1, STONE[1])


def leaves(sp, s):
    cols = [ORANGE, AMBER, BROWN[2], BROWN[3], RED if s else BROWN[1]]
    for k in range(6):
        x, y = 3 + int(hsh(k, s, 1500) * 26), 4 + int(hsh(k, s, 1501) * 24)
        c = cols[k % len(cols)]
        sp.set(x, y, c)
        sp.set(x + 1, y, c)
        if k % 2:
            sp.set(x, y + 1, BROWN[1])


def straw(sp, s):
    for k in range(7):
        x, y = 3 + int(hsh(k, s, 1600) * 22), 5 + int(hsh(k, s, 1601) * 22)
        ln = 3 + k % 3
        for i in range(ln):
            sp.set(x + i, y + (i // 3) * (1 if k % 2 else -1), SAND if i % 2 == 0 else BROWN[5])


def prints(sp, s):
    for (x, y) in ((8, 8), (14, 14), (20, 20), (11, 21), (23, 9)):
        sp.set(x, y, BROWN[1])
        sp.set(x + 1, y, BROWN[1])
        sp.set(x, y + 1, BROWN[2])
        sp.set(x + 1, y + 1, BROWN[2])
        sp.set(x + 2, y + 1, BROWN[1])


def moss_patch(sp, s):
    cx, cy = 14 + s * 2, 16 - s
    rr = [(8, 5), (6, 4), (9, 4), (7, 6)][s % 4]
    for y in range(32):
        for x in range(32):
            nx, ny = (x + .5 - cx) / rr[0], (y + .5 - cy) / rr[1]
            d = nx * nx + ny * ny + (hsh(x, y, 1700 + s) - 0.5) * 0.7
            if d < 1.0:
                c = GREEN[2] if d > 0.55 else (GREEN[3] if hsh(x, y, 1701) < 0.7 else GREEN[4])
                if d < 0.25 and hsh(x, y, 1702) < 0.4:
                    c = GREEN[5]
                sp.set(x, y, c)


def crack(sp, s):
    x, y = 3 + s * 2, 8 + s * 3
    for k in range(24):
        y += int(round(1.2 * math.sin(k * 0.6 + s)))
        sp.set(x + k, max(2, min(29, y)), STONE[0])
        if k % 6 == 3:
            sp.set(x + k, max(2, min(29, y)) + 1, PURP[2])
            sp.set(x + k + 1, max(2, min(29, y)) - 1, STONE[0])


def flowers(sp, s):
    cols = [(PINK, YELLOW), (CREAM, YELLOW), (VIOLET, PINK)][s % 3]
    for k in range(4):
        x, y = 5 + int(hsh(k, s, 1800) * 21), 8 + int(hsh(k, s, 1801) * 17)
        sp.set(x, y + 1, GREEN[3])
        sp.set(x, y + 2, GREEN[2])
        sp.set(x, y, cols[k % 2])
        sp.set(x - 1, y, cols[0]) if k % 2 == 0 else sp.set(x + 1, y, cols[1])


def mushroom(sp, s):
    x, y = 12 + s * 6, 21
    sp.rect(x, y - 2, x + 1, y, CREAM)
    sp.rect(x - 2, y - 5, x + 3, y - 3, RED if s == 0 else BROWN[3])
    sp.rect(x - 1, y - 6, x + 2, y - 6, RED if s == 0 else BROWN[3])
    sp.set(x - 1, y - 4, CREAM)
    sp.set(x + 2, y - 5, CREAM)
    sp.rect(x - 3, y - 3, x + 4, y - 3, PURP[1]) if False else None
    sp.set(x + 3, y, GREEN[3])
    sp.set(x - 2, y + 1, GREEN[2])


def pebble_line(sp, s):
    for k in range(10):
        x, y = int(hsh(k, s, 1900) * 30), int(hsh(k, s, 1901) * 30)
        sp.set(x, y, STONE[3 if k % 2 else 4])
        if k % 3 == 0:
            sp.set(x + 1, y, STONE[2])


def details():
    row1 = [decal(rut_h, 0), decal(rut_h, 1), decal(rut_h, 2),
            decal(rut_v, 0), decal(rut_v, 1), decal(rut_v, 2),
            decal(puddle, 0), decal(puddle, 1),
            decal(tuft, 0), decal(tuft, 1), decal(tuft, 2), decal(tuft, 3),
            decal(stones, 0), decal(stones, 1), decal(stones, 2),
            decal(leaves, 0), decal(leaves, 1),
            decal(straw, 0), decal(straw, 1),
            decal(prints, 0)]
    row2 = [decal(moss_patch, 0), decal(moss_patch, 1), decal(moss_patch, 2), decal(moss_patch, 3),
            decal(crack, 0), decal(crack, 1), decal(crack, 2), decal(crack, 3),
            decal(flowers, 0), decal(flowers, 1), decal(flowers, 2),
            decal(mushroom, 0), decal(mushroom, 1),
            decal(pebble_line, 0), decal(pebble_line, 1), decal(pebble_line, 2)]
    return row1, row2


def build():
    rows = []
    for kind in ('cobble', 'slab', 'gravel'):
        rows.append(autoset(kind, 0))
        rows.append(autoset(kind, 1))
        rows.append(fills(kind))
    d1, d2 = details()
    rows += [d1, d2]
    W, H = COLS * 32, len(rows) * 32
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for r, row in enumerate(rows):
        for c, t in enumerate(row):
            sh.paste(t, (c * 32, r * 32))
    return sh, rows


def mock_preview(sh, path):
    """kleine Testkarte: Wiese, Erdstrasse mit Pflasterstreifen, Kieswege, Plattenvorplatz, Platz"""
    ts = Image.open(TILES + '/Tileset_Terrain.png').convert('RGBA')
    gx, gy = 22, 13
    ground = [['g'] * gx for _ in range(gy)]
    ov = [[None] * gx for _ in range(gy)]
    for y in range(gy):
        for x in (5, 6, 7, 8):
            ground[y][x] = 'd'
        for x in (6, 7):
            ov[y][x] = 'c'
    for x in range(9, 15):
        for y in (9, 10):
            ground[y][x] = 'd'
            ov[y][x] = 'k'
    for x in range(14, 19):
        for y in range(5, 11):
            ground[y][x] = 'd'
            ov[y][x] = 's' if (x >= 15 and y <= 8) else ('k' if x == 14 or y > 8 else None)
    for x in range(1, 5):
        for y in (3, 4):
            ground[y][x] = 'd'
            ov[y][x] = 'k'
    for x in range(10, 16):
        for y in range(1, 4):
            ground[y][x] = 'd'
            ov[y][x] = 'c'

    def ids(grid, ch):
        return lambda x, y: 0 <= x < gx and 0 <= y < gy and grid[y][x] == ch

    def mask(f, x, y):
        n = f(x, y - 1); e = f(x + 1, y); s = f(x, y + 1); w = f(x - 1, y)
        idx = (1 if n else 0) | (2 if e else 0) | (4 if s else 0) | (8 if w else 0)
        corner = -1
        if idx == 15:
            if not f(x + 1, y - 1): corner = 16
            elif not f(x + 1, y + 1): corner = 17
            elif not f(x - 1, y + 1): corner = 18
            elif not f(x - 1, y - 1): corner = 19
        return idx, corner

    S = 2
    img = Image.new('RGBA', (gx * 32, gy * 32))
    # Boden: Gras (Zeile 4 Spalte 0..7), Erde (Zeile 0 autotile / Zeile 4 Spalte 8..10)
    def tile(col, row):
        return ts.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))
    for y in range(gy):
        for x in range(gx):
            if ground[y][x] == 'g':
                img.paste(tile(int(hsh(x, y, 5) * 7) if hsh(x, y, 6) > 0.5 else 0, 4), (x * 32, y * 32))
            else:
                f = ids(ground, 'd')
                idx, corner = mask(f, x, y)
                t = tile(idx, 0) if idx != 15 else (tile(corner, 0) if corner >= 0 else tile(8 + int(hsh(x, y, 9) * 3), 4))
                img.paste(t, (x * 32, y * 32))
    # Overlays
    rowmap = {'c': 0, 's': 3, 'k': 6}
    for y in range(gy):
        for x in range(gx):
            ch = ov[y][x]
            if not ch:
                continue
            f = ids(ov, ch) if ch != 'k' else (lambda xx, yy: 0 <= xx < gx and 0 <= yy < gy and ov[yy][xx] in ('k', 's'))
            if ch == 's':
                f = lambda xx, yy: 0 <= xx < gx and 0 <= yy < gy and ov[yy][xx] in ('s',)
            idx, corner = mask(f, x, y)
            r = rowmap[ch]
            if idx != 15:
                t = sh.crop((idx * 32, (r + (x + y) % 2) * 32, idx * 32 + 32, (r + (x + y) % 2) * 32 + 32))
            elif corner >= 0:
                t = sh.crop((corner * 32, r * 32, corner * 32 + 32, r * 32 + 32))
            else:
                n = {'c': 12, 's': 10, 'k': 10}[ch]
                k = int(hsh(x, y, 77) * n) if hsh(x, y, 78) < 0.4 else (0 if ch != 'k' else int(hsh(x, y, 79) * 4))
                t = sh.crop((k * 32, (r + 2) * 32, k * 32 + 32, (r + 2) * 32 + 32))
            img.alpha_composite(t, (x * 32, y * 32))
    # Details auf Erdstrasse
    dr = (9) * 32
    for y in range(gy):
        for x in (5, 8):
            if hsh(x, y, 31) < 0.5:
                k = 3 + int(hsh(x, y, 32) * 3)
                img.alpha_composite(sh.crop((k * 32, dr, k * 32 + 32, dr + 32)), (x * 32, y * 32))
    img = img.resize((gx * 32 * S, gy * 32 * S), Image.NEAREST)
    img.save(path)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else TILES + '/Tileset_Dorf.png'
    sh, rows = build()
    sh.save(out)
    prev = sys.argv[2] if len(sys.argv) > 2 else None
    if prev:
        preview(prev, [sh], scale=2, bg=(60, 80, 60, 255))
        mock_preview(sh, prev.replace('.png', '_karte.png'))
    print('geschrieben', out, sh.size)
