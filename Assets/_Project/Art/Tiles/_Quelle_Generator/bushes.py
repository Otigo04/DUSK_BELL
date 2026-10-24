"""Busch-/Stein-/Pflanzen-Generator (Objekte, transparent, Palette Art/Palette.png)."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
from nwlib import *

R_GREEN = [GREEN[0], GREEN[1], GREEN[2], GREEN[3], GREEN[4], GREEN[5]]
R_DARK = [PURP[0], GREEN[0], GREEN[1], GREEN[2], GREEN[3], GREEN[4]]
R_AUT = [BROWN[1], WINE, RED, ORANGE, AMBER, YELLOW]
R_AUT2 = [BROWN[1], BROWN[2], ORANGE, AMBER, YELLOW, SAND]
R_DEAD = [BROWN[0], BROWN[1], BROWN[2], BROWN[3], BROWN[4]]
R_MOSS = [GREEN[1], GREEN[2], GREEN[3], GREEN[4], GREEN[5], GREEN[6]]
R_STONE = [STONE[0], STONE[1], STONE[2], STONE[3], STONE[4], STONE[5]]
R_WARM = [PURP[2], PURP[4], STONE[2], BROWN[4], SAND, CREAM]   # sandiger Fels


def lobes_for(w, h, seed, n, rmin=0.26, rmax=0.40, hscale=1.0):
    """Klumpen: hinten/oben zuerst, vorne/unten zuletzt (wie bei Busch_Gruen)."""
    L = []
    base = h - 3
    if n == 1:
        r = w * 0.40
        return [(w / 2, base - r * 0.8 * hscale, r, r * 0.85 * hscale)]
    # Hauptklumpen oben mittig
    rm = w * (rmax + 0.04)
    L.append((w * (0.5 + (hsh(seed, 90) - .5) * .12), base - rm * 1.05 * hscale, rm, rm * 0.95 * hscale))
    for i in range(n - 1):
        t = (i + 0.5) / (n - 1)
        r = w * (rmin + (rmax - rmin) * hsh(seed, i, 2)) * (1.0 if n < 4 else 0.85)
        cx = w * (0.16 + 0.68 * t) + (hsh(seed, i, 1) - .5) * w * 0.10
        cy = base - r * 0.78 * hscale
        L.append((cx, cy, r, r * 0.82 * hscale))
    return L


def leaf_flecks(sp, lobes, ramp_hi, ramp_lo, seed, n=7):
    """kleine Blattstriche: helle oben-links, dunkle Punkte darunter."""
    cnt = 0
    for i in range(60):
        li = int(hsh(seed, i, 61) * len(lobes))
        cx, cy, rx, ry = lobes[li]
        a = hsh(seed, i, 62) * math.pi * 2
        rr = hsh(seed, i, 63) ** .6 * 0.8
        x = int(cx + math.cos(a) * rx * rr)
        y = int(cy + math.sin(a) * ry * rr)
        if not sp.solid(x, y) or sp.get(x, y) == OUT:
            continue
        up = (y - cy) < 0 and (x - cx) < rx * 0.3
        if up and cnt < n:
            sp.set(x, y, ramp_hi); sp.set(x + 1, y, ramp_hi); cnt += 1
        elif hsh(x, y, seed + 70) < 0.25:
            sp.set(x, y, ramp_lo)


def bush(w=32, h=32, seed=0, n=3, ramp=R_GREEN, deco=None, rmin=0.26, rmax=0.40, hscale=1.0, flecks=True):
    sp = Spr(w, h)
    lobes = lobes_for(w, h, seed, n, rmin, rmax, hscale)
    m = lit(sp, lobes, ramp, seed=seed + 100, noise=0.12, gain=1.05, bias=-0.02)
    if flecks:
        leaf_flecks(sp, lobes, ramp[-1], ramp[1], seed)
    if deco:
        deco(sp, m, seed)
    thick_outline(sp)
    return sp


def ground_shadow(sp, col=None):
    col = col or GREEN[1]
    ys = [y for y in range(sp.h) for x in range(sp.w) if sp.solid(x, y)]
    if not ys:
        return sp
    ymax = max(ys)
    out = Spr(sp.w, sp.h)
    xs = [x for y in range(sp.h) for x in range(sp.w) if sp.solid(x, y) and y >= ymax - 1]
    if xs:
        x0, x1 = min(xs), max(xs)
        for x in range(x0 + 1, x1):
            if ymax + 1 < sp.h:
                out.set(x, ymax + 1, col)
    out.paste(sp, 0, 0)
    return out


def d_berries(color, hi=CREAM, n=7, dark=WINE):
    def f(sp, m, seed):
        pts = sorted(m, key=lambda p: hsh(p[0], p[1], seed + 500))
        k = 0
        for (x, y) in pts:
            if k >= n:
                break
            if 3 < y < sp.h - 5 and sp.get(x + 1, y) != OUT and sp.get(x, y + 1) != OUT:
                sp.set(x, y, color)
                sp.set(x + 1, y, color)
                sp.set(x, y + 1, dark)
                sp.set(x + 1, y + 1, dark)
                sp.set(x, y, hi if hsh(x, y, seed) < .5 else color)
                k += 1
    return f


def d_flowers(color, center=YELLOW, n=8, hi=None):
    def f(sp, m, seed):
        pts = sorted(m, key=lambda p: hsh(p[0], p[1], seed + 600))
        k = 0
        for (x, y) in pts:
            if k >= n:
                break
            if 3 < y < sp.h - 6 and 2 < x < sp.w - 3:
                sp.set(x, y, color); sp.set(x + 1, y, color); sp.set(x, y + 1, color)
                if hi:
                    sp.set(x, y, hi)
                sp.set(x + 1, y + 1, center)
                k += 1
    return f


def frond(sp, x0, y0, ang, ln, curve, ramp, leaf=3, seed=0):
    """Farnwedel: gebogene Mittelrippe mit Fiedern."""
    pts = []
    x, y, a = float(x0), float(y0), ang
    for i in range(ln):
        pts.append((x, y, a))
        x += math.cos(a)
        y -= math.sin(a)
        a += curve
    for i, (x, y, a) in enumerate(pts):
        sp.set(int(round(x)), int(round(y)), ramp[2])
        t = i / max(1, ln - 1)
        if i > 1 and i % 2 == 0:
            L = max(1, int(round(leaf * (1 - t * 0.75))))
            for sgn in (-1, 1):
                for j in range(1, L + 1):
                    px = x + math.cos(a + sgn * 1.2) * j
                    py = y - math.sin(a + sgn * 1.2) * j + (0.4 * j)
                    sp.set(int(round(px)), int(round(py)), ramp[3 if j < L else 4] if sgn < 0 else ramp[2 if j < L else 3])


def fern(w=32, h=32, seed=0, n=7, ramp=None):
    ramp = ramp or R_GREEN
    sp = Spr(w, h)
    cx = w // 2
    for i in range(n):
        t = (i + 0.5) / n
        ang = math.pi * (0.12 + 0.76 * t)
        ln = int(h * (0.45 + 0.25 * math.sin(math.pi * t)) + hsh(seed, i) * 3)
        curve = (0.5 - t) * -0.12 if t != 0.5 else 0
        curve = (t - 0.5) * 0.12
        frond(sp, cx + (t - .5) * 3, h - 4, ang, ln, curve, ramp[1:], leaf=4, seed=seed + i)
    sp.outline(OUT, diag=False)
    return sp


# ------------------------------------------------------------- Steine
def rock(w=32, h=32, seed=0, rx=0.40, ry=0.30, ramp=None, cracks=2, moss=0.0, lobes=None, flat=0.0, gain=1.15):
    ramp = ramp or R_STONE
    sp = Spr(w, h)
    base = h - 3
    if lobes is None:
        lobes = [(w * 0.5, base - h * ry * 0.95, w * rx, h * ry)]
    m = lit(sp, lobes, ramp, seed=seed + 300, noise=0.20, gain=gain, bias=0.04)
    xs = [p[0] for p in m]; ys = [p[1] for p in m]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for f in range(cracks):
        px = int(x0 + (x1 - x0) * (0.30 + 0.45 * hsh(seed, f, 21)))
        py = int(y0 + (y1 - y0) * (0.15 + 0.2 * hsh(seed, f, 22)))
        ln = int((y1 - y0) * (0.35 + 0.3 * hsh(seed, f, 23)))
        dx = 1 if hsh(seed, f, 24) < .5 else -1
        for i in range(ln):
            if (px, py) in m:
                sp.set(px, py, ramp[1])
                if (px - 1, py) in m:
                    sp.set(px - 1, py, ramp[min(len(ramp) - 1, 4)])
            py += 1
            if hsh(px, py, seed) < 0.35:
                px += dx
    if moss:
        for (x, y) in m:
            lim = y0 + (y1 - y0) * (0.35 + 0.25 * hsh(x // 3, 0, seed))
            if y < lim and hsh(x, y, seed + 800) < moss:
                sp.set(x, y, R_MOSS[3 if hsh(x, y, seed + 2) < .6 else 4])
    thick_outline(sp)
    return sp


def rock_poly(w=32, h=32, seed=0, verts=7, ramp=None, sx=0.42, sy=0.34, moss=0.0, cracks=1, flatness=0.8, cx=None, base_pad=3):
    """kantiger Stein: Polygon, jede Flaeche bekommt eigenes Licht (oben-links hell)."""
    ramp = ramp or R_STONE
    sp = Spr(w, h)
    cx = w / 2 if cx is None else cx
    cy = h - base_pad - h * sy * flatness
    ry_ = h * sy
    rx_ = w * sx
    ang0 = hsh(seed, 1) * 0.6
    pts = []
    for i in range(verts):
        a = ang0 + 2 * math.pi * i / verts + (hsh(seed, i, 5) - .5) * 0.5
        r = 0.78 + 0.28 * hsh(seed, i, 6)
        pts.append((cx + math.cos(a) * rx_ * r, cy + math.sin(a) * ry_ * r * (1.0 if math.sin(a) < 0 else 0.8)))
    L = (-0.6, -0.8)
    m = set()
    n = len(ramp)
    for y in range(h):
        for x in range(w):
            px, py = x + .5, y + .5
            # Sektor bestimmen
            ang = math.atan2(py - cy, px - cx)
            best = None
            for i in range(verts):
                p0, p1 = pts[i], pts[(i + 1) % verts]
                # Punkt im Dreieck (center,p0,p1)?
                d = (p1[0] - p0[0]) * (cy - p0[1]) - (cx - p0[0]) * (p1[1] - p0[1])
                def side(a, b, c):
                    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
                s1 = side((cx, cy), p0, (px, py)); s2 = side(p0, p1, (px, py)); s3 = side(p1, (cx, cy), (px, py))
                if (s1 >= 0 and s2 >= 0 and s3 >= 0) or (s1 <= 0 and s2 <= 0 and s3 <= 0):
                    best = i
                    break
            if best is None:
                continue
            p0, p1 = pts[best], pts[(best + 1) % verts]
            ex, ey = p1[0] - p0[0], p1[1] - p0[1]
            nl = math.hypot(ex, ey) or 1
            nx, ny = ey / nl, -ex / nl            # Aussennormale
            # sicherstellen dass sie nach aussen zeigt
            mx, my = (p0[0] + p1[0]) / 2 - cx, (p0[1] + p1[1]) / 2 - cy
            if nx * mx + ny * my < 0:
                nx, ny = -nx, -ny
            face = nx * L[0] + ny * L[1]           # -1..1
            # radiale Position: nahe Rand dunkler/heller je nach Seite, Mitte = flache Oberseite
            dist = math.hypot(px - cx, py - cy) / (math.hypot(mx, my) or 1)
            v = 0.52 + 0.30 * face * min(1.0, dist * 1.3) + 0.22 * (-(py - cy) / ry_) * 0.5
            v += (hsh(x, y, seed + 40) - .5) * 0.14 + (BAYER[y % 4][x % 4] / 16.0 - .5) * 0.10
            sp.set(x, y, ramp[int(max(0, min(n - 1, round(v * (n - 1)))))])
            m.add((x, y))
    if not m:
        return sp
    ys = [p[1] for p in m]; xs = [p[0] for p in m]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    # Lichtkante oben-links
    for (x, y) in list(m):
        if (x, y - 1) not in m or (x - 1, y) not in m:
            if sp.get(x, y) != ramp[0] and hsh(x, y, seed + 9) < 0.9:
                sp.set(x, y, ramp[min(n - 1, n - 1 if v > 0.4 else n - 2)])
    for f in range(cracks):
        px = int(x0 + (x1 - x0) * (0.30 + 0.4 * hsh(seed, f, 21)))
        py = int(y0 + (y1 - y0) * 0.2)
        ln = int((y1 - y0) * (0.4 + 0.25 * hsh(seed, f, 23)))
        dx = 1 if hsh(seed, f, 24) < .5 else -1
        for i in range(ln):
            if (px, py) in m:
                sp.set(px, py, ramp[1])
            py += 1
            if hsh(px, py, seed) < 0.4:
                px += dx
    if moss:
        for (x, y) in m:
            lim = y0 + (y1 - y0) * (0.3 + 0.3 * hsh(x // 3, 0, seed))
            if y < lim and hsh(x, y, seed + 800) < moss:
                sp.set(x, y, R_MOSS[3 if hsh(x, y, seed + 2) < .6 else 4])
    thick_outline(sp)
    return sp


def leaf(sp, x0, y0, ang, ln, wd, ramp, seed=0, droop=0.0):
    """ein Blatt (Farn/Gras): rotierte Ellipse, Mittelrippe, linke Haelfte hell."""
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(int(ln * 2.4)):
        pass
    cells = {}
    for t in range(0, ln * 3):
        tt = t / (ln * 3.0)
        d = tt * ln
        bend = droop * d * d / max(1, ln)
        cx = x0 + ca * d
        cy = y0 - sa * d + bend
        half = wd * math.sin(math.pi * min(1.0, tt * 0.9 + 0.1)) ** 0.8
        for k in range(-int(half * 2 + 1), int(half * 2 + 2)):
            u = k / 2.0
            if abs(u) <= half:
                px = int(round(cx - sa * u))
                py = int(round(cy - ca * u))
                cells[(px, py)] = (u, tt)
    for (x, y), (u, tt) in cells.items():
        if abs(u) < 0.5:
            c = ramp[4]
        elif u > 0:
            c = ramp[3] if tt < 0.75 else ramp[4]
        else:
            c = ramp[2] if tt < 0.8 else ramp[3]
        sp.set(x, y, c)


def fern_big(w=32, h=32, seed=0, n=6, ramp=None, spread=1.0, ln=None, wd=2.2):
    ramp = ramp or R_GREEN
    sp = Spr(w, h)
    ln = ln or int(h * 0.62)
    order = sorted(range(n), key=lambda i: abs(i - (n - 1) / 2), reverse=True)
    for i in order:
        t = (i + 0.5) / n
        ang = math.pi * (0.5 + (0.5 - t) * 1.55 * spread)
        L = int(ln * (0.7 + 0.3 * math.sin(math.pi * t)) * (0.9 + 0.2 * hsh(seed, i)))
        leaf(sp, w / 2 + (t - .5) * 3, h - 4, ang, L, wd, ramp, seed=seed + i, droop=(t - .5) * 2.2)
    thick_outline(sp, bottom=False)
    return sp
