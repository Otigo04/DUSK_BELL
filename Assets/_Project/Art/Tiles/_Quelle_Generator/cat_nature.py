"""Katalog: Buesche, Pflanzen, Steine -> dict name -> Spr (und Animationen: name -> ([Spr,...], ms))"""
from bushes import *

OBJ = {}
ANIM = {}


def fit(sp, W=32, Hh=32):
    """Sprite kleiner zeichnen und unten mittig in Zielgroesse setzen"""
    out = Spr(W, Hh)
    pts = [(x, y) for y in range(sp.h) for x in range(sp.w) if sp.solid(x, y)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y1 = min(xs), max(xs), max(ys)
    ox = (W - (x1 - x0 + 1)) // 2 - x0
    oy = (Hh - 1) - y1
    for (x, y) in pts:
        out.set(x + ox, y + oy, sp.p[x, y])
    return out


def twigs(w, h, seed, n=7):
    """kahle Zweige (toter Busch)"""
    sp = Spr(w, h)
    cols = [BROWN[1], BROWN[2], BROWN[3]]

    def branch(x, y, ang, ln, depth):
        for i in range(ln):
            xx = int(round(x + math.cos(ang) * i))
            yy = int(round(y - math.sin(ang) * i))
            sp.set(xx, yy, cols[2 if (i + depth) % 5 == 0 else 1])
            if depth == 0 and i < ln * 0.5:
                sp.set(xx + 1, yy, cols[0])
            if depth < 2 and i > 2 and hsh(xx, yy, seed + depth) < 0.22:
                branch(xx, yy, ang + (0.7 if hsh(xx, yy, seed + 9) < .5 else -0.7), max(2, int(ln * 0.45)), depth + 1)
    for i in range(n):
        t = (i + .5) / n
        branch(w / 2 + (t - .5) * 6, h - 3, math.pi * (0.2 + 0.6 * t) + (hsh(seed, i) - .5) * .3,
               int(h * (0.55 + 0.3 * hsh(seed, i, 2))), 0)
    thick_outline(sp, bottom=False)
    return sp


def lavender(w, h, seed, n=9):
    sp = Spr(w, h)
    for i in range(n):
        t = (i + .5) / n
        x = int(4 + t * (w - 8))
        top = int(h * (0.25 + 0.35 * hsh(seed, i)))
        lean = (t - .5) * 3
        for y in range(top, h - 3):
            xx = int(round(x + lean * (h - 3 - y) / (h - 3 - top + 1)))
            sp.set(xx, y, GREEN[2] if (y + i) % 3 else GREEN[3])
        tx = int(round(x + lean))
        for y in range(top - 5, top + 3):
            c = VIOLET if (y + i) % 2 else MAUVE
            sp.set(tx, y, c)
            if (y + i) % 3 == 0:
                sp.set(tx + 1, y, VIOLET)
            if (y + i) % 3 == 1:
                sp.set(tx - 1, y, MAUVE)
        sp.set(tx, top - 5, PINK if hsh(seed, i, 3) < .3 else CREAM)
    thick_outline(sp, bottom=False)
    return sp


def tuft(w, h, seed, n=9, ramp=None, wd=1.6, tall=0.7):
    ramp = ramp or R_GREEN
    sp = Spr(w, h)
    order = sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2))
    for i in order:
        t = (i + .5) / n
        ang = math.pi * (0.5 + (0.5 - t) * 0.9) + (hsh(seed, i) - .5) * .3
        L = int(h * tall * (0.65 + 0.35 * math.sin(math.pi * t)) * (0.85 + 0.3 * hsh(seed, i, 4)))
        leaf(sp, w / 2 + (t - .5) * (w * 0.45), h - 3, ang, L, wd, ramp, droop=(t - .5) * 3.0)
    thick_outline(sp, bottom=False)
    return sp


def crystal_shape(sp, cx, base, hgt, wd, ramp):
    """sechskantiger Kristall: links hell, rechts dunkel, Spitze oben"""
    top = base - hgt
    half = wd // 2
    for y in range(top, base + 1):
        t = (y - top) / max(1, hgt)
        w2 = int(half * (t / 0.25) + 0.5) if t < 0.25 else half
        for x in range(cx - w2, cx + w2 + 1):
            u = (x - (cx - half)) / max(1, wd - 1)
            if x == cx - w2:
                c = ramp[4]
            elif u < 0.38:
                c = ramp[3]
            elif u < 0.62:
                c = ramp[2]
            else:
                c = ramp[1]
            if t < 0.12:
                c = ramp[4] if x <= cx else ramp[3]
            sp.set(x, y, c)
    gy = top + int(hgt * 0.35)
    sp.set(cx - half + 1, gy, ramp[5])
    sp.set(cx - half + 1, gy + 1, ramp[5])
    sp.set(cx - half + 1, gy + 2, ramp[4])


R_CRY = [BLUE[0], BLUE[1], BLUE[2], BLUE[3], BLUE[4], BLUE[5]]


def mossify(sp, y_from, y_to, seed, k=0.04):
    for y in range(y_from, y_to):
        for x in range(sp.w):
            if sp.solid(x, y) and sp.get(x, y) != OUT and hsh(x, y, seed) < (y - y_from + 2) * k:
                sp.set(x, y, R_MOSS[2 + (x + y) % 2])


def build():
    # ---------------- Buesche ----------------
    for i, nm in enumerate('ABCD'):
        OBJ['Busch_Gruen_' + nm] = bush(32, 32, 10 + i, 3 + (i % 2))
    for i, nm in enumerate('ABC'):
        OBJ['Busch_Klein_' + nm] = fit(bush(28, 24, 20 + i, 3, hscale=0.62, rmin=.2, rmax=.3))
    OBJ['Busch_Rund'] = bush(32, 32, 31, 1, hscale=0.95)
    OBJ['Busch_Gross_A'] = bush(64, 40, 32, 5, rmin=.15, rmax=.24)
    OBJ['Busch_Gross_B'] = bush(64, 40, 33, 6, rmin=.13, rmax=.22)
    OBJ['Busch_Riesig'] = bush(64, 64, 34, 5, rmin=.2, rmax=.3, hscale=1.15)
    OBJ['Busch_Beeren_Rot_A'] = bush(32, 32, 41, 3, deco=d_berries(RED, CREAM, 8, WINE))
    OBJ['Busch_Beeren_Rot_B'] = bush(32, 32, 42, 4, deco=d_berries(RED, PINK, 10, WINE))
    OBJ['Busch_Beeren_Blau'] = bush(32, 32, 43, 3, ramp=R_DARK, deco=d_berries(BLUE[2], BLUE[4], 9, BLUE[0]))
    OBJ['Busch_Beeren_Gelb'] = bush(32, 32, 44, 3, deco=d_berries(YELLOW, CREAM, 8, ORANGE))
    OBJ['Busch_Beeren_Schwarz'] = bush(32, 32, 45, 4, ramp=R_DARK, deco=d_berries(PURP[2], VIOLET, 10, PURP[0]))
    for nm, col, ctr in (('Rosa', PINK, YELLOW), ('Weiss', CREAM, YELLOW), ('Gelb', YELLOW, ORANGE),
                         ('Violett', VIOLET, CREAM), ('Rot', RED, YELLOW), ('Blau', BLUE[3], CREAM)):
        OBJ['Busch_Blueten_' + nm] = bush(32, 32, 50 + len(nm), 3,
                                          deco=d_flowers(col, ctr, 11, hi=CREAM if col != CREAM else None))
    OBJ['Busch_Blueten_Gross'] = bush(64, 40, 57, 5, rmin=.15, rmax=.24, deco=d_flowers(PINK, YELLOW, 22, hi=CREAM))
    for i, nm in enumerate('ABC'):
        OBJ['Busch_Dunkel_' + nm] = bush(32, 32, 60 + i, 3 + (i % 2), ramp=R_DARK)
    OBJ['Busch_Dunkel_Gross'] = bush(64, 40, 63, 5, rmin=.15, rmax=.24, ramp=R_DARK)
    for nm, rp, sd in (('Rot', R_AUT, 70), ('Orange', R_AUT2, 71),
                       ('Gelb', [BROWN[2], BROWN[3], AMBER, YELLOW, SAND, CREAM], 72)):
        OBJ['Busch_Herbst_' + nm] = bush(32, 32, sd, 3, ramp=rp)
    OBJ['Busch_Herbst_Gross'] = bush(64, 40, 73, 5, rmin=.15, rmax=.24, ramp=R_AUT2)
    OBJ['Busch_Tot_A'] = twigs(32, 32, 80, 7)
    OBJ['Busch_Tot_B'] = twigs(32, 32, 81, 9)
    OBJ['Busch_Tot_C'] = twigs(32, 32, 82, 5)

    def d_thorn(sp, m, seed):
        for (x, y) in sorted(m, key=lambda p: hsh(p[0], p[1], seed))[:14]:
            if sp.get(x, y) != OUT and y > 4:
                sp.set(x, y, WINE)
                sp.set(x, y - 1, RED)
    OBJ['Busch_Dornen'] = bush(32, 32, 90, 4, ramp=R_DARK, deco=d_thorn)
    OBJ['Brombeerbusch_A'] = bush(32, 32, 91, 4, ramp=R_DARK, deco=d_berries(PURP[2], VIOLET, 11, PURP[0]))
    # ---------------- Pflanzen ----------------
    OBJ['Farn_A'] = fern_big(32, 32, 1, n=8, wd=1.6)
    OBJ['Farn_B'] = fern_big(32, 32, 2, n=7, wd=1.8)
    OBJ['Farn_C'] = fern_big(32, 32, 3, n=9, wd=1.5, spread=.9)
    OBJ['Farn_Dunkel'] = fern_big(32, 32, 4, n=8, ramp=R_DARK, wd=1.7)
    OBJ['Farn_Gross_A'] = fern_big(64, 48, 5, n=11, wd=2.2, ln=34)
    OBJ['Farn_Gross_B'] = fern_big(64, 48, 6, n=10, ramp=R_DARK, wd=2.2, ln=34)
    OBJ['Lavendel_A'] = lavender(32, 32, 1, 9)
    OBJ['Lavendel_B'] = lavender(32, 32, 2, 7)
    OBJ['Grasbusch_A'] = tuft(32, 32, 1, 9)
    OBJ['Grasbusch_B'] = tuft(32, 32, 2, 11, wd=1.4, tall=0.85)
    OBJ['Grasbusch_C'] = tuft(32, 32, 3, 8, ramp=[GREEN[1], GREEN[2], GREEN[4], GREEN[5], GREEN[5], GREEN[6]], tall=0.6)
    OBJ['Grasbusch_Gross'] = tuft(64, 40, 4, 16, wd=2.0, tall=0.85)
    OBJ['Grasbusch_Dunkel'] = tuft(32, 32, 5, 10, ramp=R_DARK, tall=0.8)
    OBJ['Grasbusch_Trocken'] = tuft(32, 32, 6, 9, ramp=[BROWN[1], BROWN[2], BROWN[3], BROWN[4], SAND, CREAM], tall=0.8)
    for i in range(2):
        sp = bush(26, 16, 100 + i, 3, ramp=R_DARK, hscale=0.9)
        mm = {(x, y) for y in range(sp.h) for x in range(sp.w) if sp.solid(x, y)}
        d_flowers(VIOLET, PINK, 10, hi=MAUVE)(sp, mm, 100 + i)
        OBJ['Heidekraut_' + 'AB'[i]] = fit(sp)
    # ---------------- Steine ----------------
    for i in range(10):
        OBJ['Stein_Klein_' + 'DEFGHIJKLM'[i]] = fit(
            rock_poly(22, 18, 100 + i, verts=6 + i % 3, sx=.42, sy=.34 + .02 * (i % 4), cracks=i % 2))
    for i in range(8):
        OBJ['Stein_Mittel_' + 'ABCDEFGH'[i]] = rock_poly(
            32, 32, 130 + i, verts=7 + i % 3, sx=.44, sy=.32 + .03 * (i % 4), cracks=1 + i % 2,
            moss=0.35 if i in (2, 5) else 0)
    for i, nm in enumerate('ABC'):
        OBJ['Stein_Gross_' + nm] = rock_poly(64, 48 + 8 * (i % 2), 150 + i, verts=9 + i, sx=.44, sy=.42, cracks=3)
    OBJ['Stein_Gross_Moos_A'] = rock_poly(64, 48, 160, verts=9, sx=.44, sy=.42, moss=.5, cracks=2)
    OBJ['Stein_Gross_Moos_B'] = rock_poly(64, 56, 161, verts=10, sx=.44, sy=.44, moss=.4, cracks=3)
    OBJ['Stein_Findling'] = rock_poly(64, 64, 22, verts=10, sx=.44, sy=.44, cracks=3)
    for i, nm in enumerate('ABC'):
        OBJ['Stein_Sand_' + nm] = rock_poly(32 + 16 * (i % 2), 32 if i < 2 else 40, 170 + i, verts=7 + i,
                                            sx=.44, sy=.32 + .03 * i, ramp=R_WARM, cracks=1)
    for i, nm in enumerate('AB'):
        OBJ['Stein_Dunkel_' + nm] = rock_poly(32 + 16 * i, 32, 180 + i, verts=8, sx=.44, sy=.34,
                                              ramp=[PURP[0], PURP[1], PURP[2], PURP[3], STONE[1], STONE[2]])
    for i, nm in enumerate('ABC'):
        sp = Spr(32, 32)
        parts = [(8, 22, 14, 11), (21, 23, 13, 10), (14, 14, 14, 11), (24, 12, 10, 9)][: 3 + (i % 2)]
        for j, (cx, cy, w, h) in enumerate(parts):
            r = rock_poly(w + 2, h + 2, 190 + i * 7 + j, verts=6 + j % 3, sx=.46, sy=.4, cracks=0)
            sp.paste(r, cx - (w + 2) // 2, cy - (h + 2) // 2 + 2)
        OBJ['Steinhaufen_' + nm] = sp
    # Kiesel-Streu: kleine Steinchen ohne Rand
    for i in range(4):
        sp = Spr(32, 32)
        pts = []
        for j in range(60):
            x = 3 + int(hsh(200 + i, j, 1) * 25)
            y = 6 + int(hsh(200 + i, j, 2) * 20)
            if all(abs(x - a) + abs(y - b) > 6 for a, b in pts):
                pts.append((x, y))
                big = hsh(x, y, 5) < 0.45
                sp.set(x, y, STONE[4]); sp.set(x + 1, y, STONE[3]); sp.set(x, y + 1, STONE[2]); sp.set(x + 1, y + 1, STONE[1])
                if big:
                    sp.set(x + 2, y + 1, STONE[1]); sp.set(x + 2, y, STONE[2]); sp.set(x, y + 2, PURP[1]); sp.set(x + 1, y + 2, PURP[1])
            if len(pts) >= 5 + i:
                break
        OBJ['Kiesel_Streu_' + 'ABCD'[i]] = sp
    # Trittsteine / Platten (flach)
    for i, nm in enumerate('ABCD'):
        sp = Spr(32, 32)
        lobes = [(16, 18, 13 - (i % 2) * 2, 8 + (i % 3))]
        if i >= 2:
            lobes = [(10, 17, 8, 6), (23, 19, 8, 7)]
        lit(sp, lobes, R_STONE, seed=210 + i, noise=.18, gain=.9, bias=.12, light=(-.3, -.6))
        thick_outline(sp)
        OBJ['Trittstein_' + nm] = sp
    # Menhir
    for i in range(2):
        sp = Spr(32, 64)
        tall = 46 - i * 8
        top = 64 - 3 - tall
        for y in range(top, 62):
            t = (y - top) / tall
            half = int(5 + 5 * min(1, t * 1.6) - 3 * (1 - min(1, t * 6)) + (hsh(y, i) - .5) * 1.5)
            for x in range(16 - half, 16 + half):
                u = (x - (16 - half)) / max(1, 2 * half)
                v = 0.78 - u * 0.6 + (hsh(x, y, 40 + i) - .5) * .25 + (BAYER[y % 4][x % 4] / 16 - .5) * .12
                sp.set(x, y, R_STONE[int(max(0, min(5, round(v * 5))))])
        for k in range(3):
            xx = 12 + int(hsh(i, k) * 8)
            for y in range(top + 10 + k * 6, 56):
                if sp.solid(xx, y) and hsh(y, k, i) < .75:
                    sp.set(xx, y, R_STONE[1])
        mossify(sp, 50, 62, 77 + i, 0.035)
        thick_outline(sp)
        OBJ['Menhir_' + 'AB'[i]] = sp
    # Grabsteine
    for i, kind in enumerate(('rund', 'kreuz', 'schief')):
        sp = Spr(32, 32)
        cx = 16
        if kind == 'kreuz':
            for y in range(6, 28):
                for x in range(14, 19):
                    sp.set(x, y, R_STONE[4 if x == 14 else 3 if x < 17 else 2])
            for y in range(11, 15):
                for x in range(8, 25):
                    sp.set(x, y, R_STONE[4 if y == 11 else 3 if y < 14 else 2])
        else:
            off = 0 if kind == 'rund' else 3
            for y in range(7, 28):
                half = 7 if y > 11 else int(7 - (11 - y) * 0.9)
                o = off if y < 20 else 0
                for x in range(cx - half + o, cx + half + o):
                    u = (x - (cx - half + o)) / (2 * half)
                    sp.set(x, y, R_STONE[int(max(1, min(5, round((0.85 - u * 0.5 + (hsh(x, y, 5) - .5) * .2) * 5))))])
            for y in range(13, 19):
                sp.set(cx + (off if y < 20 else 0), y, R_STONE[1])
            for x in range(cx - 2 + off, cx + 3 + off):
                sp.set(x, 15, R_STONE[1])
        for x in range(8, 25):
            for y in range(24, 28):
                if sp.solid(x, y) and hsh(x, y, 9 + i) < .25:
                    sp.set(x, y, R_MOSS[3])
        thick_outline(sp)
        for x in range(9, 24):
            if not sp.solid(x, 28):
                sp.set(x, 28, BROWN[2])
        OBJ['Grabstein_' + 'ABC'[i]] = sp
    # ---------------- animiert: Talisman-Kristalle / Runenstein ----------------
    frames = []
    for f in range(4):
        sp = Spr(32, 32)
        crystal_shape(sp, 10, 27, 11, 5, R_CRY)
        crystal_shape(sp, 22, 27, 14, 6, R_CRY)
        crystal_shape(sp, 16, 28, 19, 7, R_CRY)
        pulse = [BLUE[3], BLUE[4], BLUE[5], BLUE[4]][f]
        for y in range(10, 28):
            for x in range(32):
                if sp.get(x, y) == BLUE[4] and (x + y + f) % 4 == 0:
                    sp.set(x, y, pulse)
        sp.set(14 + f % 2, 12 + f, BLUE[5])
        sp.set(22 + (f % 3), 9 + (f * 2) % 5, BLUE[5])
        thick_outline(sp)
        frames.append(sp)
    ANIM['Kristall_Talisman_A'] = (frames, 220)
    frames = []
    for f in range(4):
        sp = Spr(32, 32)
        crystal_shape(sp, 12, 27, 15, 6, R_CRY)
        crystal_shape(sp, 21, 27, 9, 5, R_CRY)
        sp.set(10 + f, 12 + (f * 3) % 7, BLUE[5])
        thick_outline(sp)
        frames.append(sp)
    ANIM['Kristall_Talisman_B'] = (frames, 260)
    frames = []
    for f in range(6):
        sp = Spr(32, 48)
        for y in range(8, 45):
            half = 8 if y > 14 else 8 - (14 - y) // 2
            for x in range(16 - half, 16 + half):
                u = (x - (16 - half)) / (2 * half)
                v = .78 - u * .55 + (hsh(x, y, 66) - .5) * .22 + (BAYER[y % 4][x % 4] / 16 - .5) * .12
                sp.set(x, y, R_STONE[int(max(0, min(4, round(v * 5))))])
        glow = [BLUE[3], BLUE[4], BLUE[5], BLUE[4], BLUE[3], BLUE[2]][f]
        runes = [(13, 16, 'v'), (17, 16, 'h'), (14, 23, 'x'), (18, 25, 'v'), (13, 31, 'h'), (17, 33, 'x')]
        for (rx, ry, k) in runes:
            if k == 'v':
                for t in range(4):
                    sp.set(rx, ry + t, glow)
                sp.set(rx + 1, ry + 1, glow)
            elif k == 'h':
                for t in range(4):
                    sp.set(rx + t - 1, ry + 1, glow)
                sp.set(rx, ry, glow)
            else:
                for (a, b) in ((0, 0), (1, 1), (2, 2), (2, 0), (0, 2)):
                    sp.set(rx + a, ry + b, glow)
        mossify(sp, 38, 46, 78, 0.04)
        thick_outline(sp)
        frames.append(sp)
    ANIM['Runenstein_A'] = (frames, 200)
    return OBJ, ANIM


if __name__ == '__main__':
    build()
    names = list(OBJ)
    print(len(names), len(ANIM))
    preview('cat_nat.png', [OBJ[n].im for n in names], scale=3, bg=(88, 144, 63, 255), maxw=1900)
    preview('cat_nat_anim.png', [f.im for n, (fr, ms) in ANIM.items() for f in fr], scale=4, bg=(60, 80, 60, 255), maxw=1900)
