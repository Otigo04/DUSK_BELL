"""Props 3: Moebel, Karren, Schilder, Zelt, Vogelscheuche, Werkzeug"""
import math
from props2 import *


def leg(sp, x, y0, y1, w=3, wood=WOOD):
    for y in range(y0, y1 + 1):
        sp.set(x, y, wood[4]); sp.set(x + 1, y, wood[3])
        if w > 2:
            sp.set(x + 2, y, wood[2])
        if w > 3:
            sp.set(x + 3, y, wood[1])


def table(seed=0, W=64, items=False, wood=WOOD):
    sp = Spr(W, 40)
    x0, x1 = 4, W - 5
    # Beine (hinten schmaler, vorne)
    leg(sp, x0 + 2, 26, 36, 3, wood)
    leg(sp, x1 - 4, 26, 36, 3, wood)
    # Zargen
    for x in range(x0 + 1, x1):
        sp.set(x, 25, wood[2]); sp.set(x, 26, wood[1])
    # Platte (Draufsicht-Anteil)
    for y in range(14, 25):
        t = (y - 14) / 10.0
        for x in range(x0, x1 + 1):
            k = (y - 14) // 3
            c = wood[4] if t < .15 else wood[3] if k % 2 == 0 else wood[3]
            if hsh(x // 4 + k * 3, y, seed) < .08:
                c = wood[2]
            if (y - 14) % 3 == 2 and 2 < y - 14 < 10:
                c = wood[2]
            sp.set(x, y, c)
    for x in range(x0, x1 + 1):
        sp.set(x, 23, wood[2]); sp.set(x, 24, wood[1])
        sp.set(x, 14, wood[5])
    if items:
        # Teller, Krug, Brot, Kerze
        for (px, py) in ((16, 18), (30, 19), (44, 18)):
            lit(sp, [(px, py, 4.5, 1.9)], [STONE[2], STONE[3], STONE[4], STONE[5], CREAM], seed=px, noise=.05, gain=.9, bias=.2)
        lit(sp, [(31, 16.5, 3, 2)], [BROWN[1], BROWN[2], BROWN[3], BROWN[4], AMBER], seed=3)
        # Krug
        sp.rect(x0 + 6, 9, x0 + 9, 17, BROWN[3]); sp.rect(x0 + 6, 9, x0 + 6, 17, BROWN[4]); sp.rect(x0 + 9, 9, x0 + 9, 17, BROWN[1])
        sp.rect(x0 + 6, 9, x0 + 9, 9, BROWN[5]); sp.set(x0 + 10, 11, BROWN[2]); sp.set(x0 + 10, 12, BROWN[2]); sp.set(x0 + 11, 11, BROWN[2])
        # Kerze
        sp.rect(W - 16, 10, W - 14, 17, CREAM); sp.rect(W - 14, 10, W - 14, 17, STONE[4]); sp.set(W - 15, 9, AMBER); sp.set(W - 15, 8, YELLOW)
    thick_outline(sp)
    return sp


def bench(seed=0, W=64, back=False, wood=WOOD):
    sp = Spr(W, 40 if back else 32)
    H = sp.h
    x0, x1 = 4, W - 5
    base = H - 3
    for x in (x0 + 3, x1 - 5):
        leg(sp, x, base - 9, base, 3, wood)
    for y in range(base - 14, base - 8):
        for x in range(x0, x1 + 1):
            t = (y - (base - 14)) / 5.0
            sp.set(x, y, wood[4] if t < .2 else wood[3] if t < .7 else wood[2])
    for x in range(x0, x1 + 1):
        sp.set(x, base - 9, wood[1])
        sp.set(x, base - 14, wood[5])
    if back:
        for x in (x0 + 3, x1 - 5):
            for y in range(base - 24, base - 13):
                sp.set(x, y, wood[3]); sp.set(x + 1, y, wood[2]); sp.set(x + 2, y, wood[1])
        for y in range(base - 24, base - 18):
            for x in range(x0 + 1, x1):
                sp.set(x, y, wood[4] if y == base - 24 else wood[3] if y < base - 21 else wood[2])
        for x in range(x0 + 1, x1):
            sp.set(x, base - 19, wood[1])
    thick_outline(sp)
    return sp


def stool(seed=0, wood=WOOD):
    sp = Spr(32, 32)
    for x in (10, 20):
        leg(sp, x, 20, 28, 3, wood)
    lit(sp, [(16, 19, 9, 3.5)], [wood[1], wood[2], wood[3], wood[4], wood[5]], seed=seed, noise=.1, gain=.9, bias=.15)
    for x in range(8, 25):
        sp.set(x, 21, wood[1]) if sp.solid(x, 21) else None
    thick_outline(sp)
    return sp


def chair(seed=0, wood=WOOD):
    sp = Spr(32, 40)
    for x in (9, 20):
        leg(sp, x, 24, 36, 3, wood)
    for x in (9, 20):
        for y in range(8, 24):
            sp.set(x + 1, y, wood[3]); sp.set(x + 2, y, wood[2])
    for y in range(9, 18):
        for x in range(11, 21):
            sp.set(x, y, wood[3] if (y - 9) % 4 else wood[1])
    for x in range(8, 24):
        sp.set(x, 8, wood[5]); sp.set(x, 7, wood[4])
    lit(sp, [(16, 24, 9, 3.4)], [wood[1], wood[2], wood[3], wood[4], wood[5]], seed=seed, noise=.1, gain=.9, bias=.15)
    thick_outline(sp)
    return sp


def wheel(sp, cx, cy, r, seed=0, rim=None):
    rim = rim or WOOD
    for a in range(0, 360, 6):
        ar = math.radians(a)
        for rr in (r, r - 1):
            x = int(round(cx + math.cos(ar) * rr))
            y = int(round(cy + math.sin(ar) * rr))
            sp.set(x, y, IRON[3] if rr == r else rim[3])
    for k in range(8):
        ar = k * math.pi / 4 + 0.2
        for rr in range(1, r - 1):
            sp.set(int(round(cx + math.cos(ar) * rr)), int(round(cy + math.sin(ar) * rr)), rim[2] if k % 2 else rim[3])
    sp.rect(cx - 1, cy - 1, cx + 1, cy + 1, IRON[2]); sp.set(cx - 1, cy - 1, IRON[4])


def cart(seed=0, loaded=None):
    sp = Spr(64, 48)
    # Ladebett
    for y in range(20, 34):
        for x in range(10, 54):
            t = (y - 20) / 13.0
            sp.set(x, y, ramp_at(WOOD, 0.9 - t * .55 + (hsh(x // 3, y // 3, seed) - .5) * .2, x, y, .3))
    for x in range(10, 54):
        sp.set(x, 20, WOOD[5]); sp.set(x, 21, WOOD[4]); sp.set(x, 33, WOOD[1])
    for k in range(4):
        sp.rect(10 + k * 14, 21, 10 + k * 14, 33, WOOD[1])
    # Deichsel
    sp.line(52, 30, 63, 38, WOOD[3]); sp.line(52, 31, 63, 39, WOOD[2]); sp.line(52, 29, 62, 37, WOOD[4])
    wheel(sp, 22, 36, 8, seed)
    wheel(sp, 42, 36, 8, seed + 1)
    if loaded == 'heu':
        lit(sp, [(32, 17, 19, 8)], [BROWN[2], BROWN[3], BROWN[4], AMBER, SAND, CREAM], seed=seed, noise=.3, gain=.85, bias=.08)
        for k in range(10):
            sp.set(14 + int(hsh(k, seed) * 36), 8 + int(hsh(k, seed, 2) * 3), YELLOW)
    elif loaded == 'kisten':
        sp.paste(crate(18, 12, 'zu', seed, base=29, top_h=4), 6, -8)
        sp.paste(crate(18, 12, 'zu', seed + 1, base=29, top_h=4), 26, -8)
    elif loaded == 'faesser':
        sp.paste(barrel(seed, 'zu', w=7, h=16), 4, -3)
        sp.paste(barrel(seed + 1, 'zu', w=7, h=16), 26, -3)
    thick_outline(sp)
    return sp


def wheelbarrow(seed=0, loaded=False):
    sp = Spr(32, 32)
    # Mulde
    for y in range(12, 22):
        t = (y - 12) / 9.0
        half = int(11 - t * 4)
        for x in range(15 - half, 15 + half + 1):
            sp.set(x, y, ramp_at(WOOD, 0.9 - t * .5 + (hsh(x, y, seed) - .5) * .2, x, y, .3))
    for x in range(4, 27):
        sp.set(x, 12, WOOD[5]) if sp.solid(x, 12) else None
    # Griffe
    sp.line(22, 20, 31, 24, WOOD[3]); sp.line(22, 21, 31, 25, WOOD[2])
    sp.line(10, 22, 6, 27, WOOD[2]); sp.line(20, 22, 24, 27, WOOD[2])
    wheel(sp, 6, 23, 5, seed)
    if loaded:
        lit(sp, [(14, 11, 9, 4)], [BROWN[1], BROWN[2], BROWN[3], BROWN[4], SAND], seed=seed, noise=.3)
    thick_outline(sp)
    return sp


def signpost(kind='wegweiser', seed=0):
    sp = Spr(32, 48)
    for y in range(6, 46):
        sp.set(14, y, WOOD[4]); sp.set(15, y, WOOD[3]); sp.set(16, y, WOOD[3]); sp.set(17, y, WOOD[2]); sp.set(18, y, WOOD[1])
    for x in range(11, 22):
        sp.set(x, 45, BROWN[1])
    if kind == 'wegweiser':
        for (y0, dirn) in ((8, 1), (17, -1)):
            for y in range(y0, y0 + 8):
                for x in range(4, 29):
                    t = (y - y0) / 7.0
                    sp.set(x, y, WOOD[4] if t < .15 else WOOD[3] if t < .8 else WOOD[2])
            # Spitze
            if dirn == 1:
                for k in range(4):
                    for y in range(y0 + k, y0 + 8 - k):
                        sp.set(28 + k, y, WOOD[3])
                sp.rect(6, y0 + 3, 21, y0 + 4, BROWN[0]); sp.set(22, y0 + 2, BROWN[0]); sp.set(22, y0 + 5, BROWN[0]); sp.set(23, y0 + 3, BROWN[0])
            else:
                for k in range(4):
                    for y in range(y0 + k, y0 + 8 - k):
                        sp.set(3 - k, y, WOOD[3])
                sp.rect(10, y0 + 3, 25, y0 + 4, BROWN[0]); sp.set(9, y0 + 2, BROWN[0]); sp.set(9, y0 + 5, BROWN[0]); sp.set(8, y0 + 3, BROWN[0])
    elif kind == 'tafel':
        for y in range(8, 24):
            for x in range(5, 28):
                t = (y - 8) / 15.0
                sp.set(x, y, WOOD[4] if t < .1 else WOOD[3] if t < .8 else WOOD[2])
        for y in (11, 15, 19):
            for x in range(8, 25 - (y % 3) * 2):
                sp.set(x, y, BROWN[0])
        for (x, y) in ((6, 9), (26, 9), (6, 22), (26, 22)):
            sp.set(x, y, IRON[4])
    elif kind == 'warnung':
        for y in range(8, 24):
            for x in range(5, 28):
                sp.set(x, y, WOOD[3] if y > 8 else WOOD[4])
        # roter Totenkopf-ish Punkt: zwei Augen + Zaehne
        sp.rect(11, 12, 13, 14, RED); sp.rect(19, 12, 21, 14, RED)
        sp.rect(13, 17, 19, 18, CREAM)
        for x in range(13, 20, 2):
            sp.set(x, 18, WOOD[1])
        for x in range(6, 27):
            sp.set(x, 9, WINE) if False else None
    thick_outline(sp)
    return sp


def hanging_sign(kind='schmied', seed=0):
    sp = Spr(32, 48)
    for y in range(4, 46):
        sp.set(6, y, WOOD[4]); sp.set(7, y, WOOD[3]); sp.set(8, y, WOOD[2])
    for x in range(6, 28):
        sp.set(x, 5, WOOD[4]); sp.set(x, 6, WOOD[3]); sp.set(x, 7, WOOD[1])
    sp.line(8, 14, 14, 7, WOOD[3])
    # Schild haengt
    for y in range(12, 28):
        for x in range(13, 28):
            sp.set(x, y, WOOD[3] if y > 12 else WOOD[4])
    for y in range(12, 28):
        sp.set(13, y, WOOD[4]); sp.set(27, y, WOOD[1])
    for x in range(13, 28):
        sp.set(x, 27, WOOD[1])
    sp.set(14, 8, IRON[3]); sp.set(14, 9, IRON[3]); sp.set(26, 8, IRON[3]); sp.set(26, 9, IRON[3])
    if kind == 'schmied':
        sp.rect(16, 17, 24, 18, IRON[1]); sp.rect(19, 19, 21, 23, IRON[1]); sp.rect(16, 16, 18, 16, IRON[1])
    elif kind == 'taverne':
        sp.rect(17, 15, 23, 21, AMBER); sp.rect(17, 15, 23, 16, CREAM); sp.rect(24, 17, 25, 19, BROWN[1]); sp.rect(17, 22, 23, 23, BROWN[1])
    elif kind == 'laden':
        disc(sp, 20, 20, 4, 4, [ORANGE, AMBER, YELLOW, YELLOW, CREAM], seed=1)
        sp.set(20, 15, GREEN[3])
    for x in range(6, 10):
        sp.set(x, 45, BROWN[1])
    thick_outline(sp)
    return sp


def mailbox(seed=0, col=None):
    sp = Spr(32, 48)
    col = col or [PURP[0], WINE, RED, PINK, PINK]
    for y in range(24, 46):
        sp.set(15, y, WOOD[4]); sp.set(16, y, WOOD[3]); sp.set(17, y, WOOD[2])
    for x in range(12, 21):
        sp.set(x, 45, BROWN[1])
    lit(sp, [(16, 16, 9, 7)], col, seed=seed, noise=.1, gain=.95)
    for y in range(16, 23):
        for x in range(7, 26):
            if not sp.solid(x, y) or True:
                u = (x - 7) / 18.0
                if ((x + .5 - 16) / 9.0) ** 2 + ((y + .5 - 16) / 7.0) ** 2 <= 1 or y >= 16:
                    sp.set(x, y, ramp_at(col, 0.9 - abs(u - .3) * 1.1 - (y - 16) / 14.0, x, y, .3))
    sp.rect(11, 15, 21, 16, IRON[1]) if False else None
    sp.rect(12, 18, 20, 19, PURP[0])
    # Fahne
    sp.rect(26, 11, 26, 18, IRON[3]); sp.rect(27, 11, 29, 13, YELLOW); sp.set(27, 11, CREAM)
    thick_outline(sp)
    return sp


def scarecrow(seed=0):
    sp = Spr(32, 64)
    # Pfahl
    for y in range(18, 62):
        sp.set(15, y, WOOD[4]); sp.set(16, y, WOOD[3]); sp.set(17, y, WOOD[2])
    # Querbalken
    for x in range(3, 30):
        sp.set(x, 25, WOOD[4]); sp.set(x, 26, WOOD[3]); sp.set(x, 27, WOOD[1])
    # Kleidung (Hemd)
    cloth = [PURP[1], MAUVE, VIOLET, STONE[3], STONE[4]]
    for y in range(24, 44):
        t = (y - 24) / 19.0
        half = int(5 + t * 2 - (1 if y > 36 else 0))
        for x in range(16 - half, 16 + half + 1):
            sp.set(x, y, ramp_at([BROWN[1], BROWN[2], RED, WINE, PINK] if False else [WINE, RED, PINK, SAND, CREAM], 0.5 + (hsh(x, y, seed) - .5) * .25 - abs(x - 14) * .03, x, y, .3))
    # Aermel
    for x in list(range(3, 11)) + list(range(22, 30)):
        for y in range(24, 29 + (x % 3 == 0)):
            sp.set(x, y, RED if (x + y) % 3 else WINE)
    # Flicken
    sp.rect(14, 33, 17, 36, BLUE[2]); sp.rect(14, 33, 17, 33, BLUE[3])
    # Stroh an den Enden
    for (x, y) in ((2, 28), (3, 29), (30, 28), (29, 29), (13, 44), (17, 45), (15, 46), (19, 44)):
        sp.set(x, y, YELLOW); sp.set(x - 1, y + 1, AMBER)
    # Kopf (Sack) + Hut
    lit(sp, [(16, 16, 6, 6)], [BROWN[1], BROWN[2], BROWN[3], BROWN[4], SAND], seed=seed, noise=.18, gain=.95)
    sp.set(14, 15, BROWN[0]); sp.set(18, 15, BROWN[0]); sp.set(14, 16, BROWN[0]); sp.set(18, 16, BROWN[0])
    for x in range(14, 19):
        sp.set(x, 19, BROWN[0]) if x % 2 else None
    # Hut
    for x in range(7, 26):
        sp.set(x, 11, BROWN[3] if x < 16 else BROWN[2]); sp.set(x, 10, BROWN[4] if x < 16 else BROWN[3])
    for y in range(3, 10):
        for x in range(12, 21):
            sp.set(x, y, BROWN[4] if x < 14 else BROWN[3] if x < 18 else BROWN[2])
    for x in range(12, 21):
        sp.set(x, 8, WINE)
    thick_outline(sp)
    return sp


def tent(seed=0, col=None, W=64, H=64):
    sp = Spr(W, H)
    col = col or [BROWN[1], BROWN[2], BROWN[3], SAND, CREAM]
    cx = W // 2
    top = 6
    base = H - 6
    for y in range(top, base + 1):
        t = (y - top) / float(base - top)
        half = int(2 + t * (W // 2 - 6))
        for x in range(cx - half, cx + half + 1):
            u = (x - (cx - half)) / max(1, 2 * half)
            v = 0.88 - abs(u - .3) * .9 - t * .08 + (hsh(x, y, seed) - .5) * .08
            sp.set(x, y, ramp_at(col, v, x, y, .25))
        # Streifen
    for y in range(top + 6, base + 1):
        t = (y - top) / float(base - top)
        half = int(2 + t * (W // 2 - 6))
        for x in range(cx - half, cx + half + 1):
            if (x - cx + W) % 14 < 4 and sp.solid(x, y):
                ramp = [WINE, RED, PINK]
                sp.set(x, y, ramp[0 if x > cx else 1])
    # Eingang
    for y in range(base - 22, base + 1):
        t = (y - (base - 22)) / 22.0
        half = int(2 + t * 7)
        for x in range(cx - half, cx + half + 1):
            sp.set(x, y, PURP[1] if abs(x - cx) < half - 1 else PURP[3])
    # Mittelnaht
    for y in range(top, base - 22):
        sp.set(cx, y, col[1])
    # Spitze + Fahne
    sp.rect(cx, top - 5, cx, top, BROWN[2]); sp.rect(cx + 1, top - 5, cx + 3, top - 3, RED)
    # Heringe
    for (x, y) in ((cx - W // 2 + 4, base), (cx + W // 2 - 5, base)):
        sp.set(x, y, WOOD[3]); sp.set(x, y + 1, WOOD[2])
    thick_outline(sp)
    return sp


def chopping_block(seed=0):
    sp = Spr(32, 32)
    lit(sp, [(16, 22, 9.5, 5.5)], [BROWN[1], BROWN[2], BROWN[3], BROWN[4], SAND], seed=seed, noise=.1, gain=.9, bias=.15)
    for y in range(22, 29):
        for x in range(7, 26):
            if ((x + .5 - 16) / 9.5) ** 2 + ((y + .5 - 22) / 5.5) ** 2 <= 1 or True:
                if y > 22 and (x > 6 and x < 26):
                    half = 9.5 - (y - 22) * 0.05
                    if abs(x + .5 - 16) < half:
                        u = (x - 7) / 18.0
                        sp.set(x, y, ramp_at([BROWN[0], BROWN[1], BROWN[2], BROWN[3]], .85 - abs(u - .25) * 1.2, x, y, .3))
    # Ringe oben
    for rr in (1.8, 3.8, 5.8):
        for a in range(0, 40):
            ar = a / 40.0 * 6.283
            x = int(16 + math.cos(ar) * rr * 1.6); y = int(21 + math.sin(ar) * rr * 0.9)
            if sp.solid(x, y):
                sp.set(x, y, BROWN[2])
    # Axt (Stiel schraeg, Kopf)
    for i in range(14):
        sp.set(19 + int(i * 0.5), 20 - i, WOOD[3]); sp.set(20 + int(i * 0.5), 20 - i, WOOD[2])
    sp.rect(14, 5, 22, 9, IRON[3]); sp.rect(14, 5, 22, 5, IRON[5]); sp.rect(14, 9, 22, 9, IRON[1]); sp.rect(12, 6, 13, 9, IRON[4])
    sp.set(12, 6, IRON[5])
    thick_outline(sp)
    return sp


def anvil(seed=0):
    sp = Spr(32, 32)
    # Block
    for y in range(22, 29):
        for x in range(9, 23):
            sp.set(x, y, ramp_at([BROWN[1], BROWN[2], BROWN[3], BROWN[4]], .8 - (y - 22) / 7.0 * .5, x, y, .3))
    # Amboss
    ramp = IRON
    for y in range(11, 22):
        t = (y - 11) / 10.0
        x0 = 6 if y < 15 else 10
        x1 = 27 if y < 15 else 21
        if y >= 18:
            x0, x1 = 11, 20
        for x in range(x0, x1 + 1):
            u = (x - x0) / max(1, x1 - x0)
            sp.set(x, y, ramp_at(ramp, .9 - abs(u - .25) * 1.1 - t * .25 + (hsh(x, y, seed) - .5) * .1, x, y, .3))
    for x in range(6, 28):
        sp.set(x, 11, IRON[5]) if sp.solid(x, 11) else None
    # Horn
    for i in range(5):
        sp.set(6 - i, 12 + (i // 3), IRON[3]); sp.set(6 - i, 13, IRON[2])
    thick_outline(sp)
    return sp


def beehive(seed=0):
    sp = Spr(32, 32)
    # Strohkorb aus Ringen
    rings = [(8, 7), (11, 9), (14, 11), (17, 12), (20, 13), (23, 13), (26, 12)]
    for (y, half) in rings:
        for yy in range(y - 1, y + 2):
            for x in range(16 - half, 16 + half + 1):
                u = (x - (16 - half)) / max(1, 2 * half)
                v = .9 - abs(u - .3) * 1.15 + (.12 if yy == y - 1 else -.15 if yy == y + 1 else 0)
                sp.set(x, yy, ramp_at([BROWN[1], BROWN[2], BROWN[3], BROWN[4], AMBER, YELLOW], v, x, yy, .3))
    sp.rect(14, 3, 17, 5, BROWN[3])
    sp.rect(12, 21, 18, 23, PURP[0])        # Einflugloch
    # Bienchen
    sp.set(24, 16, YELLOW); sp.set(25, 16, BROWN[0]); sp.set(5, 12, YELLOW); sp.set(4, 12, BROWN[0])
    thick_outline(sp)
    return sp


def rowboat(seed=0):
    sp = Spr(64, 32)
    for y in range(14, 26):
        t = (y - 14) / 11.0
        for x in range(4, 60):
            u = (x - 4) / 55.0
            edge = 6 * (1 - math.sin(math.pi * u) ** 0.6)
            if y >= 14 + edge * 0.5 and y <= 26 - edge * 0.4:
                sp.set(x, y, ramp_at(WOOD, .88 - t * .55 + (hsh(x // 3, y // 3, seed) - .5) * .2, x, y, .3))
    for x in range(6, 58):
        yy = 14 + int(3 * (1 - math.sin(math.pi * (x - 4) / 55.0) ** 0.6))
        sp.set(x, yy, WOOD[5]); sp.set(x, yy + 1, WOOD[4])
    # Sitzbretter
    for x in (22, 38):
        sp.rect(x, 15, x + 2, 24, WOOD[4]); sp.rect(x + 2, 15, x + 2, 24, WOOD[1])
    # Ruder
    sp.line(10, 9, 30, 22, WOOD[3]); sp.line(11, 9, 31, 22, WOOD[2])
    sp.rect(7, 6, 11, 9, WOOD[4]); sp.rect(7, 9, 11, 9, WOOD[2])
    thick_outline(sp)
    return sp
