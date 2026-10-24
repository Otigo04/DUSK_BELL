"""Uebergangs-Autotiles Gras -> Wald (weich, gedithert) + Hohes Gras Overlays."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
from nwlib import *
from autotile import wob, M as _M

N, E, S, W = 1, 2, 4, 8
ts = Image.open(TILES + '/Tileset_Terrain.png').convert('RGBA')
GR = [tile_from(Image.open(TILES + '/Tileset_Terrain_Gras.png').convert('RGBA') if False else ts, c, 4) for c in range(8)]
BAND = 11.0


# ----------------------------------------------------------------- Boeden
def floor_hell(x, y, v=0):
    x %= 32; y %= 32
    h = hsh(x, y, 700 + v)
    c = GREEN[1]
    if h < 0.10: c = GREEN[0]
    elif h < 0.30: c = GREEN[2]
    elif h < 0.34: c = GREEN[3]
    elif h < 0.365: c = BROWN[2]
    elif h < 0.375: c = BROWN[3]
    # Laub-Klumpen
    if hsh(x // 4, y // 4, 710 + v) < 0.16 and h < 0.7: c = GREEN[0]
    return c


def floor_dunkel(x, y, v=0):
    x %= 32; y %= 32
    h = hsh(x, y, 720 + v)
    c = GREEN[1]
    if h < 0.10: c = GREEN[0]
    elif h < 0.17: c = PURP[2]
    elif h < 0.30: c = GREEN[2]
    elif h < 0.325: c = BROWN[1]
    elif h < 0.332: c = BLUE[1]
    if hsh(x // 4, y // 3, 730 + v) < 0.14 and h > 0.34: c = GREEN[0]
    return c


def floor_laub(x, y, v=0):
    x %= 32; y %= 32
    g = ts.getpixel(((x + v * 3) % 32 + (v % 8) * 32 if False else (x + (v % 8) * 32), 4 * 32 + y))
    c = g
    h = hsh(x // 2, y // 2, 740 + v)
    if h < 0.075:
        cols = (ORANGE, AMBER, RED, BROWN[3], YELLOW, BROWN[2])
        k = int(hsh(x, y, 741 + v) * 6)
        c = cols[k]
        if hsh(x, y, 742 + v) < 0.5 and (x % 2 == 1):
            c = cols[(k + 1) % 6]
    return c


def floor_nadel(x, y, v=0):
    x %= 32; y %= 32
    h = hsh(x, y, 750 + v)
    c = BROWN[1]
    if h < 0.10: c = BROWN[0]
    elif h < 0.24: c = BROWN[2]
    elif h < 0.50: c = GREEN[1]
    elif h < 0.56: c = GREEN[2]
    elif h < 0.59: c = BROWN[3]
    # Nadeln: kurze schraege Striche
    if hsh(x // 3, y // 3, 760 + v) < 0.18 and (x + y) % 3 == 0:
        c = BROWN[3]
    if hsh((x + 2) // 3, (y + 1) // 3, 761 + v) < 0.10 and (x - y) % 3 == 0:
        c = BROWN[0]
    return c


FLOORS = {'hell': floor_hell, 'dunkel': floor_dunkel, 'laub': floor_laub, 'nadel': floor_nadel}


# ----------------------------------------------------------------- Autotile
def depth_field(mask, notch):
    con = {'N': bool(mask & N), 'E': bool(mask & E), 'S': bool(mask & S), 'W': bool(mask & W)}
    m0 = 1.5
    D = [[99.0] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            d = 99.0
            if not con['N']: d = min(d, y + .5 - (m0 + wob('N', x)))
            if not con['S']: d = min(d, 31.5 - y - (m0 + wob('S', x)))
            if not con['W']: d = min(d, x + .5 - (m0 + wob('W', y)))
            if not con['E']: d = min(d, 31.5 - x - (m0 + wob('E', y)))
            R = 6.0
            for (cn, cw, ox, oy) in (('N', 'W', 0, 0), ('N', 'E', 1, 0), ('S', 'W', 0, 1), ('S', 'E', 1, 1)):
                if not con[cn] and not con[cw]:
                    px = x + .5 if not ox else 32 - (x + .5)
                    py = y + .5 if not oy else 32 - (y + .5)
                    if px < m0 + R and py < m0 + R:
                        d = min(d, R - math.hypot(px - (m0 + R), py - (m0 + R)))
            if notch:
                cx, cy = {'NE': (32, 0), 'SE': (32, 32), 'SW': (0, 32), 'NW': (0, 0)}[notch]
                d = min(d, math.hypot(x + .5 - cx, y + .5 - cy) - m0)
            D[y][x] = d
    return D


def render_trans(mask, notch, floor, v, seed, grass_idx, shadow=True):
    D = depth_field(mask, notch)
    out = Image.new('RGBA', (32, 32))
    op = out.load()
    gp = GR[grass_idx % 8].load()
    for y in range(32):
        for x in range(32):
            d = D[y][x]
            p = max(0.0, min(1.0, d / BAND))
            p = p * p * (3 - 2 * p)
            thr = 0.55 * (BAYER[y % 4][x % 4] / 16.0) + 0.45 * hsh(x, y, seed + 900)
            if p > thr and d > 0:
                c = floor(x, y, v)
                # helle Waldkante direkt am Rand weicher
            else:
                c = gp[x, y]
                # Schatten des Waldes auf dem Gras (naeher am Wald dunkler)
                if shadow and 0 < d + 4 and d < 3.5 and hsh(x, y, seed + 910) < 0.55:
                    c = GREEN[2] if hsh(x, y, seed + 911) < 0.75 else GREEN[1]
                elif d < 7 and hsh(x, y, seed + 912) < 0.12:
                    c = GREEN[2]
            op[x, y] = c
    return out


def trans_set(style, v=0):
    fl = FLOORS[style]
    out = {}
    base = {'hell': 0, 'dunkel': 100, 'laub': 200, 'nadel': 300}[style]
    for idx in range(16):
        out[idx] = render_trans(idx, None, fl, v, base + idx, idx, style != 'laub')
    for k, nt in enumerate(('NE', 'SE', 'SW', 'NW')):
        out[16 + k] = render_trans(15, nt, fl, v, base + 70 + k, k, style != 'laub')
    return out


def fills(style, n=4):
    fl = FLOORS[style]
    res = []
    for v in range(n):
        t = Image.new('RGBA', (32, 32))
        for y in range(32):
            for x in range(32):
                t.putpixel((x, y), fl(x, y, v))
        res.append(t)
    return res


# ----------------------------------------------------------------- Hohes Gras
import bushes


def blade(sp, x0, base, ht, lean, curve, ramp, fat=True):
    """einzelner Halm, nach oben spitz zulaufend, links hell / rechts dunkel"""
    for i in range(int(ht) + 1):
        t = i / max(1.0, ht)
        x = x0 + lean * t + curve * t * t
        y = base - i
        wide = fat and t < 0.55
        c_l = ramp[min(5, 2 + int(t * 3.5))]
        c_r = ramp[max(0, 1 + int(t * 2.5))]
        xi = int(round(x))
        sp.set(xi, y, c_l)
        if wide:
            sp.set(xi + 1, y, c_r)
        if t > 0.9:
            sp.set(xi, y, ramp[5])


def blade_field(seed, ramp, n=16, tmin=14, tmax=27, flowers=None, heads=None, wd=1.0, dens2=0.8):
    """Hohes-Gras-Overlay: drei Halm-Reihen, x-periodisch (wickelt um -> Kacheln passen aneinander)."""
    big = Spr(96, 32)
    rows = ((19, 7, 13, 0), (25, 10, 19, 1), (31, tmin, tmax, 2))
    for row, (base, hlo, hhi, lay) in enumerate(rows):
        cnt = int(n * (dens2 if row < 2 else 1.0))
        for i in range(cnt):
            x = (i + hsh(seed, row, i)) * 32.0 / cnt
            hh = hlo + hsh(seed, row, i, 7) * (hhi - hlo)
            lean = (hsh(seed, row, i, 3) - .5) * 7
            curve = (hsh(seed, row, i, 4) - .5) * 5
            r = [ramp[0], ramp[0], ramp[1], ramp[2], ramp[3], ramp[4]] if lay == 0 else                 [ramp[0], ramp[1], ramp[2], ramp[3], ramp[4], ramp[5]] if lay == 1 else ramp
            for off in (0, 32, 64):
                blade(big, x + off, base, hh, lean, curve, r)
    sp = Spr(32, 32)
    sp.im = big.im.crop((32, 0, 64, 32))
    sp.p = sp.im.load()
    if flowers:
        col, ctr = flowers
        for k in range(5):
            x = int(3 + hsh(seed, k, 21) * 26)
            for y in range(32):
                if sp.solid(x, y):
                    sp.set(x, y - 1, col); sp.set(x + 1, y - 1, col); sp.set(x - 1, y - 1, col)
                    sp.set(x, y - 2, col); sp.set(x, y, ctr)
                    break
    if heads:
        col, dk = heads
        for k in range(8):
            x = int(2 + hsh(seed, k, 22) * 28)
            for y in range(32):
                if sp.solid(x, y):
                    for t in range(5):
                        sp.set(x, y - 1 - t, col if t % 2 == 0 else dk)
                    sp.set(x + 1, y - 2, col); sp.set(x - 1, y - 3, col); sp.set(x + 1, y - 4, dk)
                    break
    return sp


R_FRESH = [GREEN[1], GREEN[2], GREEN[3], GREEN[4], GREEN[5], GREEN[6]]
R_DKG = [GREEN[0], GREEN[1], GREEN[2], GREEN[3], GREEN[4], GREEN[5]]
R_DRY = [BROWN[2], BROWN[3], BROWN[4], SAND, SAND, CREAM]
R_MEAD = [GREEN[2], GREEN[3], GREEN[4], GREEN[5], GREEN[5], YELLOW]
R_WHEAT = [BROWN[3], BROWN[4], AMBER, YELLOW, YELLOW, CREAM]


def tall_grass_variants():
    V = []
    V.append(blade_field(1, R_FRESH, 15))
    V.append(blade_field(2, R_FRESH, 19, tmax=30))
    V.append(blade_field(3, R_FRESH, 12, tmin=8, tmax=20, wd=1.7))
    V.append(blade_field(4, R_DKG, 16))
    V.append(blade_field(5, R_DKG, 20, tmax=30, wd=1.3))
    V.append(blade_field(6, R_DRY, 15))
    V.append(blade_field(7, R_DRY, 18, tmax=30))
    V.append(blade_field(8, R_MEAD, 16))
    V.append(blade_field(9, R_FRESH, 15, flowers=(CREAM, YELLOW)))
    V.append(blade_field(10, R_FRESH, 15, flowers=(RED, YELLOW)))
    V.append(blade_field(11, R_FRESH, 15, flowers=(VIOLET, CREAM)))
    V.append(blade_field(12, R_FRESH, 15, flowers=(PINK, YELLOW)))
    V.append(blade_field(13, R_FRESH, 15, flowers=(YELLOW, ORANGE)))
    V.append(blade_field(14, R_WHEAT, 17, tmax=30, heads=(YELLOW, AMBER)))
    V.append(blade_field(15, R_FRESH, 17, tmax=30, heads=(BROWN[4], BROWN[2])))
    V.append(blade_field(16, R_DKG, 15, flowers=(BLUE[3], CREAM)))
    return V
