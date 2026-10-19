"""Props 2: Moebel, Karren, Zelt, Schilder, Vogelscheuche ... + Animationen (Feuer, Wasser, Fahne)"""
import math
from props import *

NF = 6


# ------------------------------------------------------------------ Feuer
def flame(sp, cx, base, hgt, wd, f, nf=NF, seed=0, lick=True):
    ph = 2 * math.pi * f / nf
    hf = hgt * (0.90 + 0.14 * math.sin(ph * 1.0 + seed) + 0.06 * math.sin(ph * 2 + 1.3))
    top = int(base - hf)
    for y in range(base, top - 1, -1):
        t = (base - y) / max(1.0, hf)
        sx = math.sin(ph + t * 2.4 + seed) * t * 1.9
        half = wd / 2.0 * (1 - t ** 1.25) * (1 + 0.16 * math.sin(ph * 2 + y * 0.9 + seed))
        if half < 0.5 and t < 0.97:
            half = 0.5
        for x in range(int(cx - half - 2 + sx), int(cx + half + 3 + sx)):
            u = abs(x + .5 - (cx + sx)) / max(0.5, half)
            if u > 1.0:
                continue
            if t > 0.86:
                c = RED if u < 0.7 else WINE
            elif u < 0.34 and t < 0.42:
                c = CREAM if t < 0.2 else YELLOW
            elif u < 0.58 and t < 0.66:
                c = YELLOW if t < 0.3 else AMBER
            elif u < 0.82 and t < 0.84:
                c = AMBER if t < 0.4 else ORANGE
            else:
                c = ORANGE if t < 0.5 else RED
            sp.set(x, y, c)
    # seitliche Zungen
    if lick:
        k = f % nf
        for (dx, dh) in ((-1, 0.45), (1, 0.38)):
            lx = int(cx + dx * (wd / 2.0 + 0.5))
            ly = int(base - hgt * dh * (0.8 + 0.3 * math.sin(ph + dx)))
            if (f + dx) % 2 == 0:
                sp.set(lx, ly, ORANGE); sp.set(lx, ly + 1, RED)
            else:
                sp.set(lx, ly + 1, AMBER); sp.set(lx, ly + 2, ORANGE)
    # Funken
    for j in range(2):
        t = ((f + j * 3) % nf) / float(nf)
        yy = int(top - 1 - t * 8)
        xx = int(cx + (-3 if j else 3) * math.sin(ph + j) + (j * 2 - 1) * t * 3)
        if t < 0.8:
            sp.set(xx, yy, YELLOW if t < 0.4 else ORANGE)


def logs_base(sp, cx, y, seed=0, w=14):
    """zwei gekreuzte Holzscheite + Steinring"""
    for i in range(w):
        x = cx - w // 2 + i
        yy = y + int(round((i - w / 2) * 0.22))
        sp.set(x, yy, BROWN[3]); sp.set(x, yy + 1, BROWN[2]); sp.set(x, yy + 2, BROWN[1])
        if i < 3:
            sp.set(x, yy, BROWN[5]); sp.set(x, yy + 1, BROWN[4])
    for i in range(w):
        x = cx - w // 2 + i
        yy = y + int(round((w / 2 - i) * 0.22))
        sp.set(x, yy, BROWN[4] if i > w - 4 else BROWN[3]); sp.set(x, yy + 1, BROWN[2]); sp.set(x, yy + 2, BROWN[1])


def stones_ring(sp, cx, cy, rx, ry, n=9, seed=0):
    pts = []
    for i in range(n):
        a = i / n * 6.283
        pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry, a))
    for (x, y, a) in sorted(pts, key=lambda p: p[1]):
        lit(sp, [(x, y, 3.0, 2.4)], R_STONE_L, seed=seed + int(a * 10), noise=.12, gain=.95, bias=.05)


R_STONE_L = [STONE[0], STONE[1], STONE[2], STONE[3], STONE[4], STONE[5]]


def campfire_frame(f, seed=0, big=False):
    w = 64 if big else 32
    sp = Spr(w, 32)
    cx = w // 2
    stones_ring(sp, cx, 25, 10 if not big else 14, 4.2, 9 if not big else 12, seed)
    logs_base(sp, cx, 22, seed, 14 if not big else 20)
    # Glut am Boden
    for x in range(cx - 5, cx + 6):
        if (x + f) % 3 == 0:
            sp.set(x, 23, ORANGE if (x + f) % 2 else AMBER)
    flame(sp, cx, 24, 17 if not big else 24, 12 if not big else 20, f, seed=seed)
    if big:
        flame(sp, cx - 10, 24, 11, 8, (f + 2) % NF, seed=seed + 1)
        flame(sp, cx + 10, 24, 12, 8, (f + 4) % NF, seed=seed + 2)
    thick_outline(sp)
    # Outline soll Flamme nicht umranden: Flammenpixel behalten, Rand nur unten
    return sp


def campfire_frame_clean(f, seed=0, big=False):
    """Lagerfeuer ohne Umriss um die Flamme (Umriss nur um Steine/Holz)"""
    w = 64 if big else 32
    base = Spr(w, 32)
    cx = w // 2
    stones_ring(base, cx, 25, 10 if not big else 14, 4.2, 9 if not big else 12, seed)
    logs_base(base, cx, 22, seed, 14 if not big else 20)
    thick_outline(base)
    # Glut
    for x in range(cx - 5, cx + 6):
        if (x + f) % 3 == 0:
            base.set(x, 23, ORANGE if (x + f) % 2 else AMBER)
    flame(base, cx, 24, 17 if not big else 24, 12 if not big else 20, f, seed=seed)
    if big:
        flame(base, cx - 10, 24, 11, 8, (f + 2) % NF, seed=seed + 1)
        flame(base, cx + 10, 24, 12, 8, (f + 4) % NF, seed=seed + 2)
    return base


def cookfire_frame(f):
    sp = Spr(32, 40)
    cx = 16
    stones_ring(sp, cx, 34, 10, 4, 9, 7)
    logs_base(sp, cx, 31, 3, 14)
    thick_outline(sp)
    flame(sp, cx, 33, 13, 11, f, seed=2)
    # Dreibein + Topf
    for (x0, x1) in ((5, 12), (27, 20)):
        sp.line(x0, 6, x1, 33, BROWN[2])
        sp.line(x0 + 1, 6, x1 + 1, 33, BROWN[1])
    sp.rect(6, 5, 26, 6, BROWN[3])
    # Topf
    pot = Spr(32, 40)
    lit(pot, [(16, 20, 8.5, 7.5)], [PURP[0], STONE[0], STONE[1], STONE[2], STONE[3], STONE[4]], seed=3, noise=.1, gain=.95)
    for x in range(8, 25):
        for y in range(11, 14):
            if pot.solid(x, y):
                pot.set(x, y, STONE[1] if y > 11 else STONE[3])
    for x in range(9, 24):
        pot.set(x, 12, STONE[3]) if pot.solid(x, 12) else None
    # Suppe oben
    for x in range(10, 23):
        pot.set(x, 13, AMBER if (x + f) % 3 else YELLOW)
    thick_outline(pot)
    sp.paste(pot, 0, -2)
    # Dampf
    for j in range(3):
        t = ((f + j * 2) % NF) / float(NF)
        sp.set(int(13 + j * 3 + math.sin(t * 6 + j) * 1.5), int(8 - t * 7), STONE[5] if t < .6 else STONE[4])
    return sp


def brazier_frame(f):
    sp = Spr(32, 40)
    cx = 16
    # Beine
    for (x0, x1) in ((10, 8), (22, 24), (16, 16)):
        sp.line(x0, 25, x1, 36, IRON[3]); sp.line(x0 + 1, 25, x1 + 1, 36, IRON[2])
    # Schale
    lit(sp, [(cx, 22, 10, 6.5)], IRON, seed=5, noise=.1, gain=.95)
    for y in range(0, 22):
        pass
    for x in range(cx - 10, cx + 10):
        sp.set(x, 18, IRON[4]); sp.set(x, 19, IRON[3]) if sp.solid(x, 19) else None
    # Glut
    for x in range(cx - 8, cx + 8):
        for y in (17, 18):
            sp.set(x, y, ORANGE if (x + f + y) % 3 else AMBER)
    thick_outline(sp)
    flame(sp, cx, 18, 15, 11, f, seed=1)
    return sp


def torch_frame(f):
    sp = Spr(32, 56)
    # Pfahl
    for y in range(22, 54):
        sp.set(15, y, WOOD[4]); sp.set(16, y, WOOD[3]); sp.set(17, y, WOOD[2]); sp.set(18, y, WOOD[1])
    # Kopf Stoff/Pech
    for y in range(17, 24):
        for x in range(13, 21):
            sp.set(x, y, BROWN[1] if x > 17 else BROWN[2] if x > 15 else BROWN[3])
    for x in range(13, 21):
        sp.set(x, 20, IRON[2])
    # Fuss
    for x in range(11, 23):
        sp.set(x, 52, BROWN[1]); sp.set(x, 53, BROWN[0])
    for x in range(12, 22):
        sp.set(x, 51, BROWN[2])
    thick_outline(sp)
    flame(sp, 16.5, 18, 13, 8, f, seed=3)
    return sp


def candle_frame(f):
    sp = Spr(32, 32)
    # Tellerchen
    disc(sp, 16, 27, 8, 2.4, IRON, seed=1)
    for (cx, h, w) in ((12, 9, 4), (19, 13, 5), (16, 6, 4)):
        for y in range(27 - h, 27):
            for x in range(cx - w // 2, cx + (w + 1) // 2):
                u = (x - (cx - w // 2)) / max(1, w - 1)
                sp.set(x, y, CREAM if u < .4 else SAND if u < .8 else STONE[4])
        sp.set(cx - w // 2, 27 - h, CREAM); sp.set(cx - w // 2 + 1, 27 - h, CREAM)
        # Wachstropfen
        sp.set(cx + w // 2 - 1, 27 - h + 2, CREAM)
        sp.set(cx, 27 - h - 1, BROWN[1])
    thick_outline(sp)
    for (cx, h, k) in ((12, 9, 0), (19, 13, 2), (16, 6, 4)):
        flame(sp, cx, 27 - h - 1, 5, 3.2, (f + k) % NF, seed=k, lick=False)
    return sp


def lantern_ground_frame(f):
    sp = Spr(32, 32)
    cx = 16
    # Rahmen
    for x in range(10, 23):
        sp.set(x, 27, IRON[2]); sp.set(x, 26, IRON[3])
    for y in range(11, 27):
        for x in (10, 11, 21, 22):
            sp.set(x, y, IRON[3] if x < 15 else IRON[1])
    for x in range(10, 23):
        sp.set(x, 10, IRON[4]); sp.set(x, 11, IRON[3])
    # Dach
    for y in range(5, 10):
        inset = (9 - y)
        for x in range(10 + inset - 1, 23 - inset + 1):
            sp.set(x, y, IRON[4] if x < 16 else IRON[2])
    sp.rect(15, 2, 17, 4, IRON[3])
    for x in range(14, 19):
        sp.set(x, 2, IRON[3]) if False else None
    # Glas/Licht
    glow = [AMBER, YELLOW, AMBER, ORANGE, YELLOW, CREAM][f % 6]
    for y in range(12, 26):
        for x in range(12, 21):
            u = abs(x - 16) / 5.0
            c = YELLOW if u < .4 else AMBER if u < .75 else ORANGE
            if y > 22:
                c = ORANGE
            if f % 3 == 1 and u < .3 and y < 20:
                c = CREAM
            sp.set(x, y, c)
    flame(sp, 16, 25, 8, 5, f, seed=2, lick=False)
    thick_outline(sp)
    return sp


# ------------------------------------------------------------------ Fahne
def flag_frame(f, cloth=None, emblem=True, nf=8):
    ramp = cloth or [WINE, RED, PINK]
    sp = Spr(32, 64)
    # Mast
    for y in range(4, 62):
        sp.set(6, y, WOOD[4]); sp.set(7, y, WOOD[3]); sp.set(8, y, WOOD[2])
    sp.rect(5, 2, 9, 3, YELLOW); sp.set(5, 2, CREAM); sp.set(9, 3, ORANGE)
    for x in range(3, 12):
        sp.set(x, 61, BROWN[1]); sp.set(x, 62, BROWN[0])
    ph = 2 * math.pi * f / nf
    w, h = 20, 18
    top = 6
    for x in range(9, 9 + w):
        t = (x - 9) / float(w - 1)
        off = int(round(math.sin(ph - t * 4.2) * 2.4 * t))
        taper = int(round(t * 3))      # Spitze (Schwalbenschwanz leicht)
        for y in range(top + off + (taper if t > .85 else 0), top + off + h - taper):
            v = 0.62 + (-(y - top - off) / float(h)) * 0.2 + math.cos(ph - t * 4.2) * 0.2 * (1 if t > 0 else 0)
            sp.set(x, y, ramp_at(ramp, v, x, y, .3))
        # Schatten/Saum
        sp.set(x, top + off, ramp[2]) if False else None
    # Wappen: Mond
    if emblem:
        for a in range(0, 360, 12):
            pass
        t = 0.45
        off = int(round(math.sin(ph - t * 4.2) * 2.4 * t))
        cx, cy = 9 + int(w * t), top + off + h // 2
        for y in range(-4, 5):
            for x in range(-4, 5):
                d1 = math.hypot(x, y)
                d2 = math.hypot(x - 1.8, y - 0.5)
                if d1 <= 3.9 and d2 > 3.2:
                    sp.set(cx + x, cy + y, YELLOW if x < 0 else AMBER)
    thick_outline(sp)
    return sp


# ------------------------------------------------------------------ Wasser
def water_fill(sp, mask_fn, f, nf=4, seed=0, base=None):
    base = base or [BLUE[0], BLUE[1], BLUE[2], BLUE[3], BLUE[4], BLUE[5]]
    for y in range(sp.h):
        for x in range(sp.w):
            if mask_fn(x, y):
                wave = math.sin((x + y * 0.6) * 0.55 + f * 2 * math.pi / nf)
                v = 0.5 + 0.16 * wave
                c = ramp_at(base, v, x, y, .25)
                sp.set(x, y, c)
    # Glitzer
    for k in range(3):
        x = int(3 + hsh(seed, k, 1) * (sp.w - 6) + f * 2 + k * 5) % sp.w
        y = int(3 + hsh(seed, k, 2) * (sp.h - 6))
        if mask_fn(x, y):
            sp.set(x, y, BLUE[5])


def well_frame(f):
    sp = Spr(64, 64)
    cx, cy = 32, 44
    # Steinring (Ellipse), vorderer Rand
    rx, ry = 22, 11
    # Ring
    lit(sp, [(cx, cy, rx, ry)], R_STONE_L, seed=9, noise=.2, gain=1.0, bias=.05)
    # Innen: Wasser (Ellipse kleiner)
    def inner(x, y):
        return ((x + .5 - cx) / (rx - 5.5)) ** 2 + ((y + .5 - (cy - 2.5)) / (ry - 4.5)) ** 2 <= 1
    water_fill(sp, inner, f, 4, 3)
    # Steinfugen am Ring
    for a in range(0, 360, 20):
        x = int(cx + math.cos(math.radians(a)) * (rx - 1.5))
        y = int(cy + math.sin(math.radians(a)) * (ry - 1))
        if sp.solid(x, y) and not inner(x, y):
            sp.set(x, y, STONE[1])
            sp.set(x, y + 1, STONE[1]) if a % 40 == 0 else None
    # Rand-Hoehe (Front)
    for x in range(cx - rx + 2, cx + rx - 1):
        yy = int(cy + ry * math.sqrt(max(0, 1 - ((x + .5 - cx) / rx) ** 2)))
        for k in range(1, 4):
            sp.set(x, yy - k, STONE[2] if k == 3 else STONE[1]) if not inner(x, yy - k) else None
    # Pfosten + Dach
    for px in (cx - rx + 4, cx + rx - 7):
        for y in range(14, 44):
            sp.set(px, y, WOOD[4]); sp.set(px + 1, y, WOOD[3]); sp.set(px + 2, y, WOOD[2]); sp.set(px + 3, y, WOOD[1])
    # Dach (Schindeln)
    for y in range(4, 16):
        t = (y - 4) / 11.0
        half = int(8 + t * 24)
        for x in range(cx - half, cx + half + 1):
            row = (y - 4) // 3
            c = BROWN[2] if (x + row * 3) % 6 < 3 else BROWN[1]
            if (y - 4) % 3 == 0:
                c = BROWN[4] if x < cx else BROWN[3]
            sp.set(x, y, c)
    # Rolle + Seil + Eimer
    sp.rect(cx - 1, 20, cx + 1, 22, IRON[3])
    for y in range(22, 36):
        sp.set(cx, y, SAND)
    bk = Spr(64, 64)
    vcyl(bk, cx - 4, cx + 3, 33, 40, WOOD, 4)
    hoop(bk, 35, cx - 5, cx + 4, IRON, h=1)
    bk.rect(cx - 4, 33, cx + 3, 33, WOOD_D[2])
    sp.paste(bk, 0, 0)
    thick_outline(sp)
    return sp


def trough_frame(f):
    sp = Spr(64, 32)
    # Holztrog
    for y in range(14, 28):
        for x in range(6, 58):
            sp.set(x, y, ramp_at(WOOD, 0.85 - (y - 14) / 14.0 * 0.5 + (hsh(x // 3, y, 2) - .5) * .2, x, y, .3))
    for x in (6, 7, 56, 57):
        for y in range(12, 29):
            sp.set(x, y, WOOD[4] if x < 10 else WOOD[1])
    for x in range(6, 58):
        sp.set(x, 14, WOOD[5]); sp.set(x, 13, WOOD[4])
    # Wasseroberflaeche
    def surf(x, y):
        return 9 <= x <= 54 and 15 <= y <= 18
    water_fill(sp, surf, f, 4, 4)
    for x in range(8, 56):
        sp.set(x, 14, WOOD[5] if x % 5 else WOOD[4])
    # Beine
    for x0 in (10, 48):
        sp.rect(x0, 27, x0 + 3, 30, WOOD[2]); sp.set(x0, 27, WOOD[4]); sp.rect(x0 + 3, 27, x0 + 3, 30, WOOD[1])
    thick_outline(sp)
    return sp


def barrel_water_frame(f):
    sp = barrel(3, 'wasser')
    # Wellen im Wasser (sichtbare Ellipse y 9..14)
    cx = 16
    for y in range(7, 14):
        for x in range(cx - 7, cx + 7):
            if sp.get(x, y) in (BLUE[2], BLUE[3], BLUE[4], BLUE[5]):
                v = 0.5 + 0.2 * math.sin((x + y) * 0.9 + f * 1.57)
                sp.set(x, y, ramp_at([BLUE[1], BLUE[2], BLUE[3], BLUE[4], BLUE[5]], v, x, y, .25))
    return sp
