"""Props: Fass, Kiste, Sack, Korb, Eimer, Truhe, Kuerbis ... (32px-Raster, Palette Art/Palette.png)"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
from nwlib import *

WOOD = [BROWN[0], BROWN[1], BROWN[2], BROWN[3], BROWN[4], BROWN[5]]
WOOD_D = [PURP[0], BROWN[0], BROWN[1], BROWN[2], BROWN[3], BROWN[4]]
IRON = [PURP[0], STONE[0], STONE[1], STONE[2], STONE[3], STONE[4]]
CLOTH = [BROWN[1], BROWN[2], BROWN[3], SAND, CREAM, CREAM]
GROUND = GREEN[1]


def ramp_at(ramp, v, x=0, y=0, dith=0.5):
    n = len(ramp)
    f = v * (n - 1) + (BAYER[y % 4][x % 4] / 16.0 - 0.5) * dith
    return ramp[int(max(0, min(n - 1, round(f))))]


def vcyl(sp, x0, x1, y0, y1, ramp, seed=0, bulge=0.0, lines=0):
    """senkrechter Zylinder (Fass/Eimer): Licht von links, optional Daubenlinien"""
    h = y1 - y0
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, h)
        b = int(round(bulge * math.sin(math.pi * t)))
        for x in range(x0 - b, x1 + b + 1):
            u = (x - (x0 - b)) / max(1, (x1 - x0 + 2 * b))
            v = 0.95 - abs(u - 0.28) * 1.55 + (hsh(x, y, seed) - .5) * .12
            c = ramp_at(ramp, v, x, y, 0.35)
            if lines and (x - x0) % lines == 0 and 0 < u < 1:
                c = ramp[max(0, ramp.index(c) - 1)] if c in ramp else c
            sp.set(x, y, c)


def hoop(sp, y, x0, x1, ramp=IRON, bulge=0, h=2):
    for dy in range(h):
        for x in range(x0, x1 + 1):
            u = (x - x0) / max(1, x1 - x0)
            c = ramp[4] if (u < .25 and dy == 0) else ramp[3] if u < .55 else ramp[2] if u < .85 else ramp[1]
            if dy == h - 1:
                c = ramp[max(1, ramp.index(c) - 1)]
            sp.set(x, y + dy, c)


def disc(sp, cx, cy, rx, ry, ramp, seed=0, lobe_light=(-0.4, -0.7)):
    lit(sp, [(cx, cy, rx, ry)], ramp, seed=seed, noise=0.1, light=lobe_light, gain=0.9, bias=0.18)


def planks_h(sp, x0, y0, x1, y1, ramp, seed=0, ph=4):
    """liegende Bretter (waagrecht) mit Lichtkante oben, dunkle Fuge unten"""
    for y in range(y0, y1 + 1):
        r = (y - y0) // ph
        k = (y - y0) % ph
        for x in range(x0, x1 + 1):
            base = 3 if hsh(r, seed, 5) < .5 else 2
            if k == 0:
                c = ramp[min(5, base + 1)]
            elif k == ph - 1:
                c = ramp[1]
            else:
                c = ramp[base]
            if hsh(x // 3 + r * 7, y, seed) < 0.06:
                c = ramp[max(1, base - 1)]
            sp.set(x, y, c)


def planks_v(sp, x0, y0, x1, y1, ramp, seed=0, pw=4):
    for x in range(x0, x1 + 1):
        r = (x - x0) // pw
        k = (x - x0) % pw
        for y in range(y0, y1 + 1):
            base = 3 if hsh(r, seed, 6) < .5 else 2
            if k == 0:
                c = ramp[min(5, base + 1)]
            elif k == pw - 1:
                c = ramp[1]
            else:
                c = ramp[base]
            if hsh(x, y // 3 + r * 5, seed) < 0.06:
                c = ramp[max(1, base - 1)]
            sp.set(x, y, c)


def sack(sp, cx, base, w, h, ramp=CLOTH, seed=0, tie=BROWN[2], top_open=None):
    """Sack: breiter Bauch, oben zusammengebunden, kleine Zipfel"""
    top = base - h
    for y in range(top + 3, base + 1):
        t = (y - (top + 3)) / max(1, h - 3)
        if t < 0.14:
            half = int(w * 0.18 + t * w * 0.8)
        else:
            e = min(1.0, (t - 0.14) / 0.45)
            half = int(w * 0.3 + w * 0.2 * (e ** 0.7))
            if t > 0.88:
                half -= int((t - 0.88) * 14)
        for x in range(cx - half, cx + half + 1):
            u = (x - (cx - half)) / max(1, 2 * half)
            v = 0.9 - abs(u - 0.28) * 1.25 + (hsh(x, y, seed) - .5) * .16 - (0.1 if t > .85 else 0)
            sp.set(x, y, ramp_at(ramp, v, x, y, 0.4))
    ty = top + 6
    for x in range(cx - 3, cx + 4):
        sp.set(x, ty, tie)
        sp.set(x, ty + 1, BROWN[1])
    # Zipfel oben
    for (dx, dy, k) in ((-2, 2, 3), (-1, 1, 4), (0, 1, 3), (1, 2, 2), (2, 3, 2), (-3, 3, 3), (3, 4, 2)):
        sp.set(cx + dx, top + dy, ramp[k])
    # Falten
    for k in range(2):
        fx = cx - 4 + k * 7
        for y in range(top + int(h * 0.5), base - 3):
            if hsh(fx, y, seed) < .6:
                sp.set(fx, y, ramp[1])


def apple(sp, x, y, c=RED, hi=PINK, dk=WINE):
    sp.set(x, y, hi); sp.set(x + 1, y, c); sp.set(x, y + 1, c); sp.set(x + 1, y + 1, dk)


# ============================================================ FAESSER
def barrel(seed=0, kind='zu', wood=WOOD, hoops=IRON, w=9, h=22):
    sp = Spr(32, 32)
    cx = 16
    y0, y1 = 32 - 3 - h, 28
    x0, x1 = cx - w, cx + w - 1
    vcyl(sp, x0 + 1, x1 - 1, y0 + 3, y1, wood, seed, bulge=1.6, lines=3)
    hoop(sp, y0 + 5, x0 - 1, x1 + 1, hoops, h=2)
    hoop(sp, y1 - 5, x0 - 1, x1 + 1, hoops, h=2)
    # Deckel
    if kind == 'zu':
        disc(sp, cx, y0 + 3, w - 0.5, 3.6, wood, seed + 1)
        for x in range(cx - w + 2, cx + w - 2, 4):
            sp.set(x, y0 + 3, wood[1])
        sp.set(cx - 2, y0 + 2, wood[5]); sp.set(cx - 3, y0 + 2, wood[5])
    else:
        # offen: Rand (Holz) und Inhalt
        disc(sp, cx, y0 + 3, w - 0.5, 3.6, wood, seed + 1)
        inner = {'leer': (WOOD_D[1], WOOD_D[2]), 'wasser': (BLUE[2], BLUE[3]), 'aepfel': (RED, RED),
                 'korn': (AMBER, YELLOW), 'fisch': (BLUE[2], STONE[3]), 'oel': (PURP[1], PURP[3]),
                 'kohle': (PURP[0], STONE[1])}[kind]
        for y in range(y0 + 1, y0 + 6):
            for x in range(cx - w + 2, cx + w - 1):
                if ((x + .5 - cx) / (w - 2.0)) ** 2 + ((y + .5 - (y0 + 3)) / 2.4) ** 2 <= 1:
                    sp.set(x, y, inner[0] if (x + y) % 3 else inner[1])
        if kind == 'aepfel':
            for (ax, ay) in ((cx - 5, y0 + 2), (cx - 1, y0 + 1), (cx + 3, y0 + 2), (cx - 3, y0 + 3), (cx + 1, y0 + 3)):
                apple(sp, ax, ay)
        elif kind == 'wasser':
            for x in range(cx - 4, cx - 1):
                sp.set(x, y0 + 2, BLUE[4])
            sp.set(cx + 2, y0 + 3, BLUE[5])
        elif kind == 'korn':
            for x in range(cx - 5, cx + 5, 2):
                sp.set(x, y0 + 2 + (x % 3 == 0), SAND)
        elif kind == 'fisch':
            for (ax, ay) in ((cx - 4, y0 + 2), (cx, y0 + 3), (cx + 3, y0 + 1)):
                sp.set(ax, ay, STONE[4]); sp.set(ax + 1, ay, STONE[3]); sp.set(ax + 2, ay, BLUE[3])
    thick_outline(sp)
    return sp


def barrel_lying(seed=0, wood=WOOD):
    sp = Spr(32, 32)
    x0, x1, y0, y1 = 4, 26, 12, 28
    for y in range(y0, y1 + 1):
        t = (y - y0) / (y1 - y0)
        for x in range(x0, x1 + 1):
            u = (x - x0) / (x1 - x0)
            bulge = int(round(2 * math.sin(math.pi * u)))
            if y0 - bulge * 0 <= y <= y1:
                pass
            v = 0.95 - abs(t - 0.28) * 1.5 + (hsh(x, y, seed) - .5) * .1
            sp.set(x, y, ramp_at(wood, v, x, y, .35))
    for x in range(x0, x1 + 1):
        u = (x - x0) / (x1 - x0)
        sp.set(x, y0 - int(round(1.2 * math.sin(math.pi * u))), wood[4])
    for x in (9, 21):
        for y in range(y0 - 1, y1 + 1):
            sp.set(x, y, IRON[4] if y < y0 + 4 else IRON[3] if y < y1 - 4 else IRON[2])
            sp.set(x + 1, y, IRON[2])
    # Stirnseite links (Deckel)
    disc(sp, 5, 20, 3.0, 8.2, WOOD, seed + 4)
    for y in range(14, 27, 3):
        sp.set(4, y, wood[1])
    thick_outline(sp)
    return sp


def barrel_broken(seed=0):
    """Fass mit abgebrochenen Dauben: rechte Seite eingebrochen, Splitter davor"""
    sp = barrel(seed, 'leer')
    for y in range(sp.h):
        for x in range(sp.w):
            if sp.get(x, y) == OUT:
                sp.set(x, y, (0, 0, 0, 0))
    cx = 16
    ys = [y for y in range(sp.h) for x in range(sp.w) if sp.solid(x, y)]
    y0 = min(ys)
    for k, x in enumerate(range(cx + 1, cx + 11)):
        cut = y0 + 3 + (k * 3) % 7 + (k // 4) * 3
        for y in range(y0 - 1, min(cut, 20)):
            sp.set(x, y, (0, 0, 0, 0))
    # Reifen hing durch
    for x in range(cx + 2, cx + 9):
        sp.set(x, 21, IRON[3]); sp.set(x, 22, IRON[1])
    # Bretter am Boden
    for (x, y, l) in ((20, 28, 7), (24, 26, 5)):
        for i in range(l):
            sp.set(x + i, y, WOOD[3]); sp.set(x + i, y + 1, WOOD[2])
    thick_outline(sp)
    return sp


def barrel_group(seed=0):
    sp = Spr(64, 40)
    for i, (ox, oy, k) in enumerate([(0, 8, 'zu'), (22, 8, 'aepfel'), (11, 0, 'zu')]):
        b = barrel(seed + i, k, w=8, h=20)
        sp.paste(b, ox, oy)
    return sp


def keg(seed=0, wood=WOOD):
    sp = Spr(32, 32)
    vcyl(sp, 11, 21, 15, 27, wood, seed, bulge=1.2, lines=3)
    hoop(sp, 18, 9, 23, IRON, h=1)
    hoop(sp, 24, 9, 23, IRON, h=1)
    disc(sp, 16, 15, 5.5, 2.6, wood, seed)
    sp.set(16, 15, WOOD[1])
    # Zapfhahn
    sp.rect(22, 21, 25, 22, IRON[3]); sp.set(25, 23, IRON[2]); sp.set(22, 21, IRON[4])
    thick_outline(sp)
    return sp


# ============================================================ KISTEN
def crate(w=22, h=18, kind='zu', seed=0, wood=WOOD, cx=16, base=29, top_h=6):
    """Kiste von vorn+oben: Frontflaeche + Deckelflaeche"""
    sp = Spr(32, 32)
    x0, x1 = cx - w // 2, cx + w // 2 - 1
    fy0, fy1 = base - h, base
    # Front
    planks_h(sp, x0, fy0, x1, fy1, wood, seed, ph=max(4, h // 3))
    # Rahmen/Leisten
    for y in range(fy0, fy1 + 1):
        for x in (x0, x0 + 1, x1 - 1, x1):
            sp.set(x, y, wood[4] if x in (x0, x0 + 1) and y > fy0 else wood[1] if x in (x1, x1 - 1) else wood[2])
    for x in range(x0, x1 + 1):
        for y in (fy0, fy0 + 1, fy1 - 1, fy1):
            sp.set(x, y, wood[4] if y in (fy0, fy0 + 1) else wood[1])
    # Kreuzstrebe
    n = min(w - 6, h - 4)
    for i in range(n):
        sp.set(x0 + 3 + int(i * (w - 7) / n), fy0 + 2 + int(i * (h - 5) / n), wood[2])
        sp.set(x1 - 3 - int(i * (w - 7) / n), fy0 + 2 + int(i * (h - 5) / n), wood[2])
        sp.set(x0 + 4 + int(i * (w - 7) / n), fy0 + 2 + int(i * (h - 5) / n), wood[4])
    # Deckel / Oberseite
    ty0 = fy0 - top_h
    for y in range(ty0, fy0):
        for x in range(x0 + 1, x1):
            if kind == 'zu':
                c = wood[4] if (y - ty0) % 3 else wood[3]
                if (x - x0) % 7 == 0:
                    c = wood[2]
            else:
                c = WOOD_D[2]
            sp.set(x, y, c)
    if kind != 'zu':
        # Inhalt
        cont = {'offen': None, 'aepfel': RED, 'karotten': ORANGE, 'fisch': BLUE[3], 'stroh': AMBER, 'kohl': G_LT,
                'flaschen': BLUE[2], 'kartoffeln': BROWN[4]}[kind]
        for y in range(ty0 + 1, fy0 + 1):
            for x in range(x0 + 2, x1 - 1):
                if cont is None:
                    sp.set(x, y, WOOD_D[1] if y < fy0 else wood[1])
                else:
                    sp.set(x, y, cont)
        if kind == 'aepfel':
            for k in range(0, w - 5, 4):
                apple(sp, x0 + 2 + k, ty0 - 1 + (k % 8 == 0) * 2)
                apple(sp, x0 + 4 + k, ty0 + 2)
        elif kind == 'karotten':
            for k in range(0, w - 4, 3):
                sp.set(x0 + 3 + k, ty0 - 2, G_LT); sp.set(x0 + 4 + k, ty0 - 3, G_HI); sp.set(x0 + 3 + k, ty0 - 1, G_BASE)
                sp.set(x0 + 3 + k, ty0, ORANGE); sp.set(x0 + 3 + k, ty0 + 1, AMBER)
        elif kind == 'fisch':
            for k in range(0, w - 5, 5):
                for dx in range(4):
                    sp.set(x0 + 3 + k + dx, ty0 + 1 + (k % 2), STONE[4 - (dx > 1)])
                sp.set(x0 + 6 + k, ty0 + 1 + (k % 2), BLUE[2])
        elif kind == 'stroh':
            for k in range(14):
                sx = x0 + 2 + int(hsh(k, seed, 1) * (w - 5))
                sp.set(sx, ty0 - 1 - int(hsh(k, seed, 2) * 2), YELLOW)
                sp.set(sx + 1, ty0 + int(hsh(k, seed, 3) * 3), SAND)
        elif kind == 'kohl':
            for k in range(0, w - 7, 7):
                disc(sp, x0 + 5 + k, ty0 + 1, 3.5, 3.0, [GREEN[1], GREEN[2], GREEN[3], GREEN[4], GREEN[5], GREEN[6]], seed + k)
        elif kind == 'flaschen':
            for k in range(0, w - 5, 4):
                sp.rect(x0 + 3 + k, ty0 - 3, x0 + 4 + k, ty0 + 1, BLUE[2])
                sp.set(x0 + 3 + k, ty0 - 3, BLUE[5]); sp.set(x0 + 3 + k, ty0 - 4, BROWN[3]); sp.set(x0 + 4 + k, ty0 - 4, BROWN[2])
        elif kind == 'kartoffeln':
            for k in range(0, w - 5, 4):
                disc(sp, x0 + 4 + k, ty0 + 1, 2.2, 2.0, [BROWN[1], BROWN[2], BROWN[3], BROWN[4], SAND], seed + k)
    thick_outline(sp)
    return sp


def crate_stack(seed=0, n=2):
    s = Spr(32, 48)
    s.paste(crate(24, 18, 'zu', seed, base=29, top_h=6), 0, 17)
    s.paste(crate(18, 14, 'zu', seed + 3, base=29, top_h=5), 1 if n == 2 else -1, 0)
    return s


def crate_broken(seed=0):
    sp = Spr(32, 32)
    planks_h(sp, 5, 22, 26, 28, WOOD, seed, ph=3)
    # Splitter / hochstehende Bretter
    for (x, y, l, ang) in ((7, 22, 8, 1.1), (20, 22, 7, 2.0), (13, 22, 6, 1.5)):
        for i in range(l):
            xx = int(round(x + math.cos(ang) * i))
            yy = int(round(y - math.sin(ang) * i))
            sp.set(xx, yy, WOOD[3]); sp.set(xx + 1, yy, WOOD[2])
        sp.set(int(x + math.cos(ang) * (l - 1)), int(y - math.sin(ang) * (l - 1)) - 1, WOOD[5])
    thick_outline(sp)
    return sp


# ============================================================ SAECKE, KOERBE, EIMER
def basket(kind='leer', seed=0, w=20, h=13):
    sp = Spr(32, 32)
    cx = 16
    base = 29
    y0 = base - h
    wick = [BROWN[0], BROWN[1], BROWN[2], BROWN[3], BROWN[4], SAND]
    # Inhalt zuerst (hinten)
    if kind == 'aepfel':
        for k, (dx, dy) in enumerate(((-6, -4), (-2, -6), (3, -5), (6, -3), (-4, -2), (1, -3))):
            apple(sp, cx + dx, y0 + dy + 1, RED, PINK, WINE) if k % 3 != 2 else apple(sp, cx + dx, y0 + dy + 1, YELLOW, CREAM, ORANGE)
    elif kind == 'pilze':
        for k, dx in enumerate((-6, -1, 4)):
            disc(sp, cx + dx, y0 - 1 - (k % 2), 3.2, 2.3, [BROWN[1], BROWN[2], BROWN[3], BROWN[4], SAND], seed + k)
            sp.rect(cx + dx - 1, y0, cx + dx + 1, y0 + 2, CREAM)
    elif kind == 'brot':
        for k, dx in enumerate((-6, 0, 5)):
            disc(sp, cx + dx, y0 - 1, 4.0, 2.6, [BROWN[1], BROWN[2], BROWN[3], BROWN[4], AMBER, SAND], seed + k)
            sp.set(cx + dx, y0 - 2, BROWN[2]); sp.set(cx + dx + 1, y0 - 1, BROWN[2])
    elif kind == 'beeren':
        for k in range(9):
            sp.set(cx - 7 + int(hsh(k, seed, 1) * 14), y0 - 2 + int(hsh(k, seed, 2) * 3), VIOLET if k % 2 else BLUE[3])
            sp.set(cx - 7 + int(hsh(k, seed, 1) * 14) + 1, y0 - 1 + int(hsh(k, seed, 2) * 3), BLUE[1])
    elif kind == 'wolle':
        disc(sp, cx, y0 - 2, 8, 4, [PURP[3], STONE[2], STONE[3], STONE[4], CREAM, CREAM], seed)
    # Korpus: Flechtmuster
    for y in range(y0, base + 1):
        t = (y - y0) / h
        half = int(w / 2 - 1 - t * -1.0 * 0 + (1 - t) * 1.5)
        half = int(w / 2 * (0.82 + 0.18 * (1 - t)))
        for x in range(cx - half, cx + half + 1):
            u = (x - (cx - half)) / max(1, 2 * half)
            wv = (x + y * 2) % 4 < 2 if (y // 2) % 2 == 0 else (x + y * 2 + 2) % 4 < 2
            v = 0.85 - abs(u - 0.3) * 1.2 + (0.1 if wv else -0.1) + (hsh(x, y, seed) - .5) * .1
            sp.set(x, y, ramp_at(wick, v, x, y, .2))
    # Rand oben
    for x in range(cx - w // 2, cx + w // 2 + 1):
        sp.set(x, y0, wick[5] if x < cx else wick[4])
        sp.set(x, y0 + 1, wick[3])
    thick_outline(sp)
    return sp


def bucket(kind='leer', seed=0, wood=WOOD):
    sp = Spr(32, 32)
    vcyl(sp, 11, 20, 15, 27, wood, seed, bulge=0.0, lines=3)
    hoop(sp, 17, 10, 21, IRON, h=1)
    hoop(sp, 24, 10, 21, IRON, h=1)
    disc(sp, 15.5, 15, 5.2, 2.2, wood, seed)
    inner = {'leer': WOOD_D[1], 'wasser': BLUE[2], 'milch': CREAM, 'farbe': RED, 'kohle': PURP[0]}[kind]
    for y in range(13, 17):
        for x in range(11, 21):
            if ((x + .5 - 15.5) / 4.5) ** 2 + ((y + .5 - 15) / 1.6) ** 2 <= 1:
                sp.set(x, y, inner)
    if kind == 'wasser':
        sp.set(13, 15, BLUE[4]); sp.set(14, 15, BLUE[5])
    if kind == 'milch':
        sp.set(13, 15, WHITE if False else CREAM); sp.set(14, 14, CREAM)
    # Henkel
    for a in range(0, 12):
        t = a / 11.0
        x = int(round(10 + 11 * t))
        y = int(round(15 - 6 * math.sin(math.pi * t)))
        sp.set(x, y, IRON[3] if a < 7 else IRON[2])
    thick_outline(sp)
    return sp


# ============================================================ TRUHEN
def chest(kind='zu', seed=0, wood=WOOD, metal=IRON, w=24, h=15):
    sp = Spr(32, 32)
    cx = 16
    x0, x1 = cx - w // 2, cx + w // 2 - 1
    base = 29
    fy0 = base - h + 5
    # Front unten
    planks_h(sp, x0, fy0, x1, base, wood, seed, ph=4)
    if kind == 'zu':
        # gewoelbter Deckel
        for y in range(fy0 - 7, fy0):
            t = (fy0 - y) / 7.0
            inset = int(round((t ** 2.2) * 5))
            for x in range(x0 + inset, x1 - inset + 1):
                u = (x - x0) / w
                c = ramp_at(wood, 0.92 - abs(u - .3) * 1.1 - (1 - t) * .15 + t * .1, x, y, .3)
                sp.set(x, y, c)
        # Metallbaender
        for bx in (x0 + 3, x1 - 5):
            for y in range(fy0 - 7, base + 1):
                if sp.solid(bx, y):
                    sp.set(bx, y, metal[4]); sp.set(bx + 1, y, metal[3]); sp.set(bx + 2, y, metal[2])
        for x in range(x0, x1 + 1):
            sp.set(x, fy0, metal[3]); sp.set(x, fy0 - 1, metal[4])
        # Schloss
        sp.rect(cx - 2, fy0 - 1, cx + 1, fy0 + 3, YELLOW); sp.set(cx - 2, fy0 - 1, CREAM); sp.rect(cx - 2, fy0 + 3, cx + 1, fy0 + 3, ORANGE)
        sp.set(cx - 1, fy0 + 1, BROWN[0]); sp.set(cx, fy0 + 1, BROWN[0])
    else:
        # offen: Deckel hochgeklappt (hinten), Inhalt Gold
        for y in range(fy0 - 12, fy0 - 3):
            for x in range(x0 + 2, x1 - 1):
                sp.set(x, y, wood[2] if (x + y) % 5 else wood[1])
        for y in range(fy0 - 12, fy0 - 3):
            sp.set(x0 + 2, y, wood[4]); sp.set(x1 - 2, y, wood[1])
        for x in range(x0 + 2, x1 - 1):
            sp.set(x, fy0 - 12, wood[4])
        for y in range(fy0 - 3, fy0 + 1):
            for x in range(x0 + 1, x1):
                sp.set(x, y, PURP[1] if kind == 'leer' else BROWN[1])
        if kind in ('gold', 'schatz'):
            for k in range(0, w - 3, 3):
                disc(sp, x0 + 3 + k, fy0 - 3 - (k % 2), 2.4, 2.0, [ORANGE, AMBER, YELLOW, YELLOW, CREAM, CREAM], seed + k)
            if kind == 'schatz':
                sp.set(cx - 3, fy0 - 6, BLUE[4]); sp.set(cx - 2, fy0 - 6, BLUE[5]); sp.set(cx - 3, fy0 - 5, BLUE[2])
                sp.set(cx + 4, fy0 - 5, PINK); sp.set(cx + 5, fy0 - 5, RED)
        for bx in (x0 + 3, x1 - 5):
            for y in range(fy0, base + 1):
                sp.set(bx, y, metal[4]); sp.set(bx + 1, y, metal[3]); sp.set(bx + 2, y, metal[2])
        for x in range(x0, x1 + 1):
            sp.set(x, fy0, metal[3])
    # Seitenrahmen
    for y in range(fy0, base + 1):
        sp.set(x0, y, wood[4]); sp.set(x0 + 1, y, wood[3]); sp.set(x1, y, wood[1]); sp.set(x1 - 1, y, wood[2])
    for x in range(x0, x1 + 1):
        sp.set(x, base, wood[1]) if False else None
    thick_outline(sp)
    return sp


# ============================================================ KUERBIS, HEU
def pumpkin(seed=0, r=8, col=None, face=False):
    sp = Spr(32, 32)
    ramp = col or [BROWN[1], WINE, RED, ORANGE, AMBER, YELLOW]
    cx, cy = 16, 29 - r * 0.9
    lobes = [(cx - r * 0.55, cy, r * 0.62, r * 0.88), (cx + r * 0.55, cy, r * 0.62, r * 0.88), (cx, cy - 0.5, r * 0.7, r * 0.95)]
    lit(sp, lobes, ramp, seed=seed, noise=.1, gain=1.05, bias=.02)
    # Furchen
    for i in (-1, 1):
        for y in range(int(cy - r * 0.8), int(cy + r * 0.8)):
            xx = int(cx + i * r * 0.3 + math.sin((y - cy) * 0.35) * 0.5)
            if sp.solid(xx, y):
                sp.set(xx, y, ramp[1])
    # Stiel
    sp.rect(int(cx) - 1, int(cy - r) - 2, int(cx) + 1, int(cy - r) + 1, GREEN[2])
    sp.set(int(cx) - 1, int(cy - r) - 2, GREEN[4]); sp.set(int(cx) + 1, int(cy - r) - 1, GREEN[1])
    sp.set(int(cx) + 2, int(cy - r), G_BASE)
    if face:
        for (fx, fy) in ((cx - 4, cy - 1), (cx + 3, cy - 1)):
            sp.set(int(fx), int(fy), BROWN[0]); sp.set(int(fx) + 1, int(fy), BROWN[0]); sp.set(int(fx) + 1, int(fy) - 1, BROWN[0])
        for dx in range(-4, 5):
            sp.set(int(cx) + dx, int(cy) + 4 + (abs(dx) < 3 and 0 or -1), BROWN[0])
        sp.set(int(cx) - 2, int(cy) + 5, BROWN[0]); sp.set(int(cx) + 2, int(cy) + 5, BROWN[0])
    thick_outline(sp)
    return sp


def pumpkin_group(seed=0):
    sp = Spr(64, 32)
    sp.paste(pumpkin(seed, 8), -2, 0)
    sp.paste(pumpkin(seed + 1, 6, col=[BROWN[1], BROWN[2], ORANGE, AMBER, YELLOW, SAND]), 22, 2)
    sp.paste(pumpkin(seed + 2, 5), 14, 6)
    return sp


def haybale(kind='rund', seed=0):
    sp = Spr(32, 32)
    hay = [BROWN[1], BROWN[2], BROWN[3], BROWN[4], AMBER, SAND]
    if kind == 'rund':
        lit(sp, [(16, 18, 11, 10)], hay, seed=seed, noise=.25, gain=.95, bias=.1)
        # Spiralringe
        for r in (3.5, 6.5, 9):
            for a in range(0, 64):
                ang = a / 64 * 6.283
                x = int(16 + math.cos(ang) * r)
                y = int(18 + math.sin(ang) * r * 0.9)
                if hsh(x, y, seed + 3) < .75 and sp.solid(x, y):
                    sp.set(x, y, hay[1])
        # Binder
        for x in range(6, 27):
            if ((x + .5 - 16) / 11) ** 2 < 1:
                yy = 12
                for y in (yy, yy + 1):
                    if sp.solid(x, y):
                        sp.set(x, y, BROWN[1] if y == yy else BROWN[2])
    else:
        # Rechteck
        for y in range(14, 28):
            for x in range(6, 26):
                t = (y - 14) / 14.0
                v = 0.9 - t * .5 + (hsh(x, y, seed) - .5) * .3
                sp.set(x, y, ramp_at(hay, v, x, y, .4))
        for y in range(8, 14):
            for x in range(7, 27):
                sp.set(x, y, ramp_at(hay, .95 + (hsh(x, y, seed + 3) - .5) * .3, x, y, .4))
        for bx in (11, 20):
            for y in range(8, 28):
                sp.set(bx, y, BROWN[1]); sp.set(bx + 1, y, BROWN[2])
        for k in range(14):
            sp.set(5 + int(hsh(k, seed, 1) * 22), 9 + int(hsh(k, seed, 2) * 18), SAND)
    # Halme
    for k in range(7):
        sx = 5 + int(hsh(k, seed, 9) * 22)
        sp.set(sx, 7 + int(hsh(k, seed, 8) * 2), YELLOW)
    thick_outline(sp)
    return sp


def woodstack(big=False, seed=0):
    """Brennholzstapel: Stirnseiten der Rundhoelzer"""
    w, h = (64, 40) if big else (32, 32)
    sp = Spr(w, h)
    rows = 4 if big else 3
    cols = 7 if big else 3
    for r in range(rows):
        for c in range(cols - (r % 2 if not big else r % 2)):
            cx = 6 + c * 8.8 + (4.4 if r % 2 else 0)
            cy = h - 7 - r * 7.2
            lit(sp, [(cx, cy, 4.4, 4.2)], [BROWN[1], BROWN[2], BROWN[3], BROWN[3], BROWN[4]], seed=seed + r * 9 + c, noise=.1, gain=.9, bias=.1, light=(-.3, -.5))
            # Jahresringe
            for (rr, col) in ((3.0, BROWN[2]), (1.6, BROWN[4])):
                for a in range(20):
                    ang = a / 20 * 6.283
                    sp.set(int(cx + math.cos(ang) * rr), int(cy + math.sin(ang) * rr), col)
            sp.set(int(cx), int(cy), BROWN[1])
    thick_outline(sp)
    return sp
