"""Hauptfiguren Mann/Frau: Run, Boxen (punch1-3), Messer (knife1/2), Baseballschlaeger (bat), Pistole (shoot).

Baut auf gen_hauptfiguren.py auf (gleiches 56x56-Raster, gleiche Palette, gleiche 8 Richtungen S, SW, W, NW, N, NE, E, SE).
Der Koerper kommt aus render-Funktionen des Basis-Skripts mit noarms=True, die Arme (2-Segment-IK), Waffen und
Effekte werden hier ueber eine kleine 3D->Bildschirm-Projektion gezeichnet. NE/E/SE sind gespiegelte NW/W/SW,
dabei werden rechte/linke Hand getauscht, damit die Haendigkeit stimmt.

Aufruf:  python gen_hauptfiguren_combat.py [Ausgabeordner]   -> <Ordner>/<Name>/<name>_<anim>.png (8 Zeilen x N Frames)
"""
import math
import os
import sys

from PIL import Image

import gen_hauptfiguren as G
from gen_hauptfiguren import (CELL, OX, OY, K, K2, ST, ST2, CR, SL, SM, SD, W1, W2, W3, SAND, HR, V1, V2, V3, PAL, PALSET,
                              SPECS, VIEWS, ORDER, MIRROR, Cv, legs_pose, outline, to_img, rnd)

YS = 0.45            # Foreshortening der Bodentiefe auf dem Bildschirm
LATX = 1.6           # seitlicher Versatz wird in x gestreckt (Schulterbreite)
CX, CY = 23.5, 20.0  # Koerpermitte auf Schulterhoehe (Koerperkoordinaten, vor OX/OY)
L1, L2 = 5.0, 5.5    # Oberarm, Unterarm

# Schulter-Anker (rechter, linker Arm der Figur) je Basisansicht
SHOULDER = {
    'S': ((17, 20), (30, 20)),
    'SW': ((17, 20), (29, 20)),
    'W': ((24, 20), (24, 20)),
    'NW': ((30, 20), (17, 20)),
    'N': ((30, 20), (17, 20)),
}

FLASH_Y, FLASH_O, FLASH_W = '#ffd27a', '#ffa550', '#fff1c9'
SPARK_W, SPARK_Y = '#fff1c9', '#ffd27a'
TRAIL, TRAIL2 = '#f2ead8', '#9a95a0'
BAT_L, BAT_M, BAT_D = '#9c7a5a', '#7a5a43', '#5c4033'
GUN_M, GUN_H, GUN_D = '#2b2140', '#6e6a74', '#1a1526'


# ---------------------------------------------------------------- Projektion
def right_of(f):
    return (-f[1], f[0])


def project(f, p, anchor_c=(CX, CY)):
    """p=(d vorwaerts, r seitlich rechts, z Hoehe ueber Schulter) -> Bildschirm (x, y) in Koerperkoordinaten."""
    d, r, z = p
    rx, ry = right_of(f)
    gx = f[0] * d + rx * r * LATX
    gy = f[1] * d + ry * r
    return (anchor_c[0] + gx, anchor_c[1] + gy * YS - z)


def depth_of(f, p):
    d, r, _ = p
    return f[1] * d + f[0] * r


# ---------------------------------------------------------------- Pixel-Ebenen
class Layer:
    def __init__(s):
        s.px = {}

    def dot(s, x, y, c):
        s.px[(int(math.floor(x + 0.5)), int(math.floor(y + 0.5)))] = c

    def thick_line(s, a, b, w, c):
        n = max(1, int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2))
        for i in range(n + 1):
            t = i / float(n)
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            if w == 1:
                s.dot(x, y, c)
            elif w == 2:
                for dx in (0, 1):
                    for dy in (0, 1):
                        s.dot(x + dx - .5, y + dy - .5, c)
            else:
                hw = w // 2
                for dx in range(-hw, hw + 1):
                    for dy in range(-hw, hw + 1):
                        s.dot(x + dx, y + dy, c)

    def shade(s, hi=None, lo=None, left=None, right=None):
        """Randpixel einfaerben: oben hi, unten lo, links left, rechts right (nur wo Nachbar fehlt)."""
        out = dict(s.px)
        for (x, y), c in s.px.items():
            if hi and (x, y - 1) not in s.px:
                out[(x, y)] = hi
            if right and (x + 1, y) not in s.px:
                out[(x, y)] = right
            if left and (x - 1, y) not in s.px:
                out[(x, y)] = left
            if lo and (x, y + 1) not in s.px:
                out[(x, y)] = lo
        s.px = out

    def stamp(s, cv, outline_over=None):
        """Auf Cv schreiben. outline_over: Farbe fuer 1px Kontur dort, wo schon Koerper-Pixel liegen."""
        if outline_over:
            ring = set()
            for (x, y) in s.px:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in s.px:
                        ring.add(q)
            for (x, y) in ring:
                X, Y = x + OX + cv.dx, y + OY + cv.dy
                if 0 <= X < CELL and 0 <= Y < CELL and cv.b[Y][X] is not None:
                    cv.b[Y][X] = outline_over
        for (x, y), c in s.px.items():
            cv.P(x, y, c)


# ---------------------------------------------------------------- Arm / Hand
def ik_elbow(sh, hd, flare=0.4):
    dx, dy = hd[0] - sh[0], hd[1] - sh[1]
    dist = math.hypot(dx, dy)
    mx = L1 + L2
    if dist > mx - 0.01:
        k = (mx - 0.01) / dist
        hd = (sh[0] + dx * k, sh[1] + dy * k)
        dx, dy, dist = dx * k, dy * k, mx - 0.01
    dist = max(dist, 1.5)
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(0.0, L1 * L1 - a * a))
    ux, uy = dx / dist, dy / dist
    mxp, myp = sh[0] + ux * a, sh[1] + uy * a
    c1 = (mxp - uy * h, myp + ux * h)
    c2 = (mxp + uy * h, myp - ux * h)

    def score(c):
        return c[1] + flare * abs(c[0] - CX)

    return (c1 if score(c1) >= score(c2) else c2), hd


def draw_arm(cv, spec, sh, hd, front, role, hand_big=False, skin=True, elbow_flare=0.4):
    hl, base, shd, dk = spec['J']
    el, hd = ik_elbow(sh, hd, elbow_flare)
    lay = Layer()
    lay.thick_line(sh, el, 3, base)
    lay.thick_line(el, hd, 3, base)
    lay.shade(hi=None, lo=shd, left=shd, right=(hl if role == 'R' else None))
    stamp_over = K if front else None
    lay.stamp(cv, outline_over=stamp_over)
    return hd


def draw_fist(cv, hd, front, big=False):
    lay = Layer()
    x, y = hd
    size = 4 if big else 3
    h0 = size // 2
    for dx in range(size):
        for dy in range(size):
            lay.dot(x - h0 + dx, y - h0 + dy, SL)
    lay.shade(lo=SM, left=SM)
    lay.stamp(cv, outline_over=K if front else None)


# ---------------------------------------------------------------- Waffen
def draw_bat(cv, f, rh, vec, front, extra=None):
    g = rh
    base = project(f, (g[0] - 1.5 * vec[0], g[1] - 1.5 * vec[1], g[2] - 1.5 * vec[2]))
    tip = project(f, (g[0] + 13.5 * vec[0], g[1] + 13.5 * vec[1], g[2] + 13.5 * vec[2]))
    lay = Layer()
    n = 24
    for i in range(n + 1):
        t = i / float(n)
        x = base[0] + (tip[0] - base[0]) * t
        y = base[1] + (tip[1] - base[1]) * t
        w = 1 if t < 0.3 else (2 if t < 0.62 else 3)
        c = BAT_M
        sub = Layer()
        sub.thick_line((x, y), (x, y), w, c)
        lay.px.update(sub.px)
    lay.shade(hi=BAT_L, lo=BAT_D, left=None)
    # Kappe am Ende
    lay.stamp(cv, outline_over=K)
    return tip


def draw_knife(cv, f, rh, vec, front, extra=None):
    g = rh
    grip_b = project(f, g)
    grip_e = project(f, (g[0] + 2 * vec[0], g[1] + 2 * vec[1], g[2] + 2 * vec[2]))
    tip = project(f, (g[0] + 8 * vec[0], g[1] + 8 * vec[1], g[2] + 8 * vec[2]))
    blade_b = grip_e
    lay = Layer()
    lay.thick_line(grip_b, grip_e, 2, HR)
    lay.stamp(cv, outline_over=K)
    bl = Layer()
    bl.thick_line(blade_b, tip, 2, ST)
    bl.shade(hi=CR, lo=ST2)
    bl.dot(tip[0], tip[1], CR)
    bl.stamp(cv, outline_over=K)
    # Parierstange
    cg = Layer()
    cg.thick_line(grip_e, grip_e, 2, SAND)
    cg.stamp(cv)
    return tip


def draw_gun(cv, f, rh, vec, front, extra=None):
    g = rh
    ln = 6.0
    rear = project(f, (g[0] - 1 * vec[0], g[1] - 1 * vec[1], g[2] - 1 * vec[2]))
    muz = project(f, (g[0] + ln * vec[0], g[1] + ln * vec[1], g[2] + ln * vec[2]))
    lay = Layer()
    lay.thick_line(rear, muz, 2, GUN_M)
    # Griff nach unten (Schulterkoordinaten: z kleiner)
    gb = project(f, (g[0] - 0.5 * vec[0], g[1] - 0.5 * vec[1], g[2] - 3.5))
    lay.thick_line(project(f, (g[0], g[1], g[2] - .5)), gb, 2, GUN_M)
    lay.shade(hi=GUN_H, lo=GUN_D)
    lay.stamp(cv, outline_over=K)
    # Schlitten-Details: heller Streifen
    dl = Layer()
    dl.dot(muz[0], muz[1], ST2)
    dl.stamp(cv)
    return muz


# ---------------------------------------------------------------- weitere Waffen
def at(g, v, t):
    """Punkt t Einheiten vom Griff g entlang v (Koerperkoordinaten d, r, z)."""
    return (g[0] + v[0] * t, g[1] + v[1] * t, g[2] + v[2] * t)


def stick(cv, f, g, vec, t0, t1, width, color, hi=None, lo=None, outline=K):
    """Gerader Stab entlang vec von t0 bis t1 ab Griff g. width: Zahl oder Funktion u(0..1) -> Breite. Gibt (Anfang, Ende) auf dem Bildschirm zurueck."""
    a = project(f, at(g, vec, t0))
    b = project(f, at(g, vec, t1))
    lay = Layer()
    n = max(2, int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2))
    for i in range(n + 1):
        u = i / float(n)
        w = width(u) if callable(width) else width
        sub = Layer()
        sub.thick_line((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), w, color)
        lay.px.update(sub.px)
    lay.shade(hi=hi, lo=lo)
    lay.stamp(cv, outline_over=outline)
    return a, b


def draw_machete(cv, f, rh, vec, front, extra=None):
    stick(cv, f, rh, vec, -1.0, 2.5, 2, HR)
    _, tip = stick(cv, f, rh, vec, 2.5, 12.0, 2, ST, hi=CR, lo=ST2)
    cg = Layer()
    p = project(f, at(rh, vec, 2.5))
    cg.thick_line(p, p, 2, SAND)
    cg.stamp(cv)
    return tip


def draw_axe(cv, f, rh, vec, front, extra=None):
    stick(cv, f, rh, vec, -1.5, 11.0, 2, BAT_M, hi=BAT_L, lo=BAT_D)
    sd = screen_dir(f, vec)
    nx, ny = -sd[1], sd[0]
    fw = screen_dir(f, (1.0, 0.0, 0.0))
    if nx * fw[0] + ny * fw[1] < 0:      # Schneide zeigt nach vorn
        nx, ny = -nx, -ny
    c = project(f, at(rh, vec, 9.5))
    head = Layer()
    for i in range(-1, 2):               # entlang des Stiels
        for j in range(-1, 4):           # quer: -1 Ruecken, 3 Schneide
            col = ST2 if j <= 0 else (CR if j == 3 else ST)
            head.dot(c[0] + sd[0] * i + nx * j, c[1] + sd[1] * i + ny * j, col)
    head.stamp(cv, outline_over=K)
    return project(f, at(rh, vec, 11.0))


def draw_club(cv, f, rh, vec, front, extra=None):
    _, tip = stick(cv, f, rh, vec, -1.5, 12.0, lambda u: 1 if u < 0.3 else (2 if u < 0.58 else 3), BAT_M, hi=BAT_L, lo=BAT_D)
    st = Layer()
    for t in (9.0, 10.5, 11.5):          # Eisennaegel im Kopf
        q = project(f, at(rh, vec, t))
        st.dot(q[0], q[1], ST)
    st.stamp(cv)
    return tip


def draw_crowbar(cv, f, rh, vec, front, extra=None):
    _, tip = stick(cv, f, rh, vec, -1.5, 12.0, 2, ST, hi=CR, lo=ST2)
    sd = screen_dir(f, vec)
    nx, ny = -sd[1], sd[0]
    hk = Layer()
    for k, (a, b) in enumerate(((1.4, -0.5), (2.4, -1.4), (2.6, -2.6))):   # Haken am Ende
        hk.dot(tip[0] + nx * a + sd[0] * b, tip[1] + ny * a + sd[1] * b, ST2 if k == 2 else ST)
    hk.stamp(cv, outline_over=K)
    return tip


def draw_flail(cv, f, rh, vec, front, extra=None):
    """extra = Richtung der Kette (Kopf haengt nach). Stiel 8 Einheiten, Kette 3,5, Kopf mit Stacheln."""
    stick(cv, f, rh, vec, -1.5, 8.0, 2, BAT_M, hi=BAT_L, lo=BAT_D)
    hv = extra if extra else vec
    p0 = at(rh, vec, 8.0)
    c0 = project(f, p0)
    c1 = project(f, at(p0, hv, 3.5))
    ch = Layer()
    ch.thick_line(c0, c1, 1, ST2)
    ch.stamp(cv)
    hc = project(f, at(p0, hv, 5.5))
    head = Layer()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            head.dot(hc[0] + dx, hc[1] + dy, BAT_M)
    head.shade(hi=BAT_L, lo=BAT_D)
    for ox, oy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        head.dot(hc[0] + ox, hc[1] + oy, ST)
    head.stamp(cv, outline_over=K)
    return hc


def draw_rifle(cv, f, rh, vec, front, extra=None):
    stick(cv, f, rh, vec, -4.5, 2.5, 2, BAT_M, hi=BAT_L, lo=BAT_D)          # Schaft
    stick(cv, f, rh, vec, 2.5, 7.0, 2, GUN_M, hi=GUN_H, lo=GUN_D)           # Verschluss
    _, tip = stick(cv, f, rh, vec, 7.0, 13.5, 1, GUN_M, hi=GUN_H, lo=GUN_D)  # Lauf
    return tip


def draw_shotgun(cv, f, rh, vec, front, extra=None):
    """Pumpgun: Holzschaft, Verschluss, Doppelrohr-Optik aus Lauf plus Magazinrohr, Vorderschaft aus Holz."""
    stick(cv, f, rh, vec, -4.5, 2.5, 2, BAT_M, hi=BAT_L, lo=BAT_D)
    low = (rh[0], rh[1], rh[2] - 1.0)
    stick(cv, f, low, vec, 6.5, 10.5, 2, BAT_M, hi=BAT_L, lo=BAT_D)         # Vorderschaft (Pumpe)
    stick(cv, f, rh, vec, 2.5, 6.5, 2, GUN_M, hi=GUN_H, lo=GUN_D)
    _, tip = stick(cv, f, rh, vec, 6.5, 14.0, 2, GUN_M, hi=GUN_H, lo=GUN_D)
    return tip


def draw_assault(cv, f, rh, vec, front, extra=None):
    """Sturmgewehr: kurzer schwarzer Schaft, Gehaeuse, Magazin nach unten, duenner Lauf."""
    stick(cv, f, rh, vec, -3.5, 1.0, 2, GUN_D, hi=GUN_M, lo=GUN_D)
    stick(cv, f, at(rh, vec, 5.5), (0.0, 0.0, -1.0), 0.0, 3.5, 2, GUN_D, hi=GUN_M, lo=GUN_D)   # Magazin
    stick(cv, f, rh, vec, 1.0, 9.0, 2, GUN_M, hi=GUN_H, lo=GUN_D)
    _, tip = stick(cv, f, rh, vec, 9.0, 14.0, 1, GUN_H, hi=ST, lo=GUN_D)
    return tip


def draw_sniper(cv, f, rh, vec, front, extra=None):
    """Repetierbuechse (Kar98): Holzschaft, langer Lauf, Zielfernrohr obenauf."""
    stick(cv, f, rh, vec, -4.5, 3.0, 2, BAT_M, hi=BAT_L, lo=BAT_D)
    stick(cv, f, rh, vec, 3.0, 8.0, 2, GUN_M, hi=GUN_H, lo=GUN_D)
    _, tip = stick(cv, f, rh, vec, 8.0, 17.5, 1, GUN_M, hi=GUN_H, lo=GUN_D)
    up = (rh[0], rh[1], rh[2] + 1.6)
    stick(cv, f, up, vec, 4.0, 10.0, 1, GUN_H, hi=ST, lo=GUN_D)                 # Zielfernrohr
    return tip


DRAWERS = {'rifle': draw_rifle, 'shotgun': draw_shotgun, 'assault': draw_assault, 'sniper': draw_sniper, 'bat': draw_bat, 'knife': draw_knife, 'gun': draw_gun, 'machete': draw_machete, 'axe': draw_axe, 'club': draw_club,
           'crowbar': draw_crowbar, 'flail': draw_flail}
TRAIL_LEN = {'bat': 13.5, 'club': 12.5, 'crowbar': 12.5, 'axe': 11.5, 'machete': 12.0, 'flail': 13.0}


# ---------------------------------------------------------------- Effekte (nach der Kontur, ohne Outline)
def put(buf, x, y, c, dx, dy):
    X, Y = int(math.floor(x + 0.5)) + OX + dx, int(math.floor(y + 0.5)) + OY + dy
    if 0 <= X < CELL and 0 <= Y < CELL:
        buf[Y][X] = c


FOOD_Y, FOOD_O, FOOD_D = '#ffd27a', '#ffa550', '#7a5a43'
GLASS, GLASS_H, GLASS_D, CORK = '#6b7fb8', '#e8e0f0', '#3a4a7a', '#9c7a5a'


def fx_food(buf, p, dx, dy, stage):
    """Essen in der Hand (Brotstueck): stage 2 ganz, 1 angebissen, 0 nur Kruemel."""
    x, y = p
    shapes = {
        2: {(-2, -1): FOOD_D, (-1, -2): FOOD_D, (0, -2): FOOD_D, (1, -2): FOOD_D, (2, -1): FOOD_D, (-1, 0): FOOD_D, (0, 0): FOOD_D, (1, 0): FOOD_D,
            (-1, -1): FOOD_Y, (0, -1): FOOD_Y, (1, -1): FOOD_O},
        1: {(-1, -1): FOOD_D, (0, -2): FOOD_D, (1, -2): FOOD_D, (2, -1): FOOD_D, (0, 0): FOOD_D, (1, 0): FOOD_D,
            (0, -1): FOOD_Y, (1, -1): FOOD_O},
        0: {(0, -1): FOOD_O, (1, 0): FOOD_Y},
    }[stage]
    for (ox, oy), c in shapes.items():
        put(buf, x + ox, y + oy - 1, c, dx, dy)


def fx_bottle(buf, p, face, dx, dy, tilt):
    """Flasche in der Hand. tilt 0 = aufrecht getragen (Hals oben), 1-2 = an den Mund gekippt (Hals zeigt zum Gesicht)."""
    x, y = p
    if tilt == 0:
        ux, uy = 0.0, 1.0                  # Boden liegt unter dem Hals
    else:
        ax, ay = x - face[0], y - face[1]  # vom Gesicht weg
        n = math.hypot(ax, ay) or 1.0
        ax, ay = ax / n, ay / n
        ay -= 0.55 * (tilt - 1) + 0.25     # mit mehr Kippen zeigt der Boden nach oben
        n = math.hypot(ax, ay) or 1.0
        ux, uy = ax / n, ay / n
    # Hals zeigt in Richtung -u; die Hand haelt die Flasche etwa in der Mitte
    nx0, ny0 = x - ux * 3.5, y - uy * 3.5
    for i in range(0, 8):
        cx, cy = nx0 + ux * i, ny0 + uy * i
        if i == 0:
            put(buf, cx, cy, CORK, dx, dy)
        elif i <= 2:
            put(buf, cx, cy, GLASS_D, dx, dy)
        else:
            px, py = -uy, ux                # quer zur Achse
            for o in (-1, 0, 1):
                c = GLASS_D if o == -1 else (GLASS_H if o == 0 and i == 4 else GLASS)
                put(buf, cx + px * o, cy + py * o, c, dx, dy)


def fx_spark(buf, p, dx, dy, size):
    x, y = p
    cols = [SPARK_W, SPARK_Y, FLASH_O]
    put(buf, x, y, SPARK_W, dx, dy)
    for i in range(1, size + 1):
        c = cols[min(i - 1, 2)]
        for ox, oy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            put(buf, x + ox, y + oy, c, dx, dy)
    if size >= 2:
        for ox, oy in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
            put(buf, x + ox, y + oy, FLASH_O, dx, dy)


def fx_flash(buf, p, sdir, dx, dy, size):
    """Muendungsfeuer an Bildschirmpunkt p, sdir = Bildschirmrichtung (normiert)."""
    x, y = p
    ux, uy = sdir
    for a in range(-1, 2):
        for b in range(-1, 2):
            put(buf, x + a, y + b, FLASH_W, dx, dy)
    for i in range(2, 2 + size):
        c = FLASH_Y if i < 2 + size - 1 else FLASH_O
        put(buf, x + ux * i, y + uy * i, c, dx, dy)
        put(buf, x + ux * i + uy, y + uy * i - ux, c if i < 3 else FLASH_O, dx, dy) if i < 4 else None
        put(buf, x + ux * i - uy, y + uy * i + ux, c if i < 3 else FLASH_O, dx, dy) if i < 4 else None
    for s_ in (1, -1):
        for i in range(2, 4):
            put(buf, x - uy * i * s_ * 1.0, y + ux * i * s_ * 1.0, FLASH_Y if i == 2 else FLASH_O, dx, dy)
    put(buf, x - ux * 2, y - uy * 2, FLASH_O, dx, dy)


def fx_bullet(buf, p, sdir, dx, dy, length=3):
    """Projektil mit Leuchtspur: heller Kopf (2px), dahinter Schweif in Gelb/Orange."""
    x, y = p
    ux, uy = sdir
    cols = [FLASH_W, FLASH_W, FLASH_Y, FLASH_Y, FLASH_O, FLASH_O, '#e8733a']
    for i in range(length + 2):
        put(buf, x - ux * i, y - uy * i, cols[min(i, len(cols) - 1)], dx, dy)
        if i < 2:
            put(buf, x - ux * i - uy * 0.6, y - uy * i + ux * 0.6, FLASH_Y, dx, dy)


def fx_trail(buf, a, b, dx, dy, c=TRAIL):
    n = max(1, int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2))
    for i in range(n + 1):
        t = i / float(n)
        put(buf, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, c, dx, dy)


def fx_dust(buf, f, dx, dy, stage):
    """Staubwoelkchen hinter den Fuessen (stage 0 klein/hell bis 2 gross/blass), gegen die Laufrichtung."""
    bx = CX - f[0] * 9.0
    by = 45.0 - f[1] * 9.0 * YS
    if f[0] == 0 and f[1] < 0:
        by = 47.0
    if f[0] == 0 and f[1] > 0:
        by = 44.0
        bx = CX + 5.0
    pat = [
        [(0, 0, TRAIL), (1, 0, TRAIL), (0, -1, TRAIL)],
        [(-1, 0, TRAIL), (0, 0, TRAIL), (1, 0, TRAIL), (0, -1, TRAIL), (-1, -1, TRAIL2), (2, -1, TRAIL2)],
        [(-2, 0, TRAIL2), (-1, -1, TRAIL), (0, -2, TRAIL2), (1, -1, TRAIL2), (2, 0, TRAIL2), (3, -1, TRAIL2)],
    ][stage]
    for ox, oy, c in pat:
        put(buf, bx + ox, by + oy, c, dx, dy)


def screen_dir(f, vec):
    sx = vec[0] * f[0] + vec[1] * right_of(f)[0] * LATX
    sy = (vec[0] * f[1] + vec[1] * right_of(f)[1]) * YS - vec[2]
    n = math.hypot(sx, sy) or 1.0
    return (sx / n, sy / n)


# ---------------------------------------------------------------- Pose-Rendering
def composite(back, body):
    out = [row[:] for row in body]
    for y in range(CELL):
        for x in range(CELL):
            if out[y][x] is None and back[y][x] is not None:
                out[y][x] = back[y][x]
    return out


HANG_R = (0.0, 4.2, -8.0)
HANG_L = (0.0, -4.2, -8.0)


SIDE_SWAP_KINDS = ('gun', 'rifle', 'shotgun', 'assault', 'sniper', 'knife')
HEAD_X0, HEAD_X1 = 18.0, 29.0   # Kopfbreite in Koerperkoordinaten (Bildschirm-x)


def clear_head(f, h, side):
    """Haende, die hoeher als die Schulter und im Bild hinter dem Kopf liegen wuerden, seitlich (r) versetzen, bis sie neben dem Kopf frei sind."""
    d, r, z = h
    if d <= 0.5:
        return h
    for _ in range(14):
        x, y = project(f, (d, r, z))
        inside = HEAD_X0 - 2.0 <= x <= HEAD_X1 + 1.0
        if y > 19.0 or not inside:
            break
        r += side * 0.4
    return (d, r, z)


def render_pose(spec, view, pose):
    """pose: dict(rh, lh, dy, lean, stance=(phase, amp, lift)|None, weapon=(kind, hand, vec)|None, fx=[...])."""
    base_view = MIRROR.get(view, view)
    mirrored = view in MIRROR
    f = VIEWS[base_view]
    sp = dict(spec)
    sp['noarms'] = True

    rh = pose.get('rh', HANG_R)
    lh = pose.get('lh', HANG_L)
    if callable(rh):   # Handposition haengt von der Ansicht ab (Run/Sprint: Arme von hinten/vorn anders als von der Seite)
        rh = rh(f)
    if callable(lh):
        lh = lh(f)
    wk = pose.get('weapon')
    vec = wk[2] if wk else None
    if mirrored:
        # Haendigkeit erhalten: gespiegelt tauscht die Figur-Rechte mit der Bildschirm-Basis-Linken
        rh, lh = (lh[0], -lh[1], lh[2]), (rh[0], -rh[1], rh[2])
        if wk:
            vec = (vec[0], -vec[1], vec[2])
            extra = (wk[3][0], -wk[3][1], wk[3][2]) if len(wk) > 3 else None
            wk = (wk[0], 'L' if wk[1] == 'R' else 'R', vec) + ((extra,) if extra else ())

    north = base_view in ('N', 'NW')
    flare = north and 'sort_north' not in pose
    if flare:
        # Rueckansicht: Waffen mit Schusshand auf der abgewandten Seite (NW: rechte Hand liegt auf der rechten Bildseite, gezielt wird
        # nach links) wuerden hinter Kopf und Koerper verschwinden: die Waffe wandert in die linke Hand (Pose gespiegelt).
        if base_view == 'NW' and wk and wk[0] in SIDE_SWAP_KINDS and wk[1] == 'R':
            rh, lh = (lh[0], -lh[1], lh[2]), (rh[0], -rh[1], rh[2])
            wk = (wk[0], 'L', (vec[0], -vec[1], vec[2])) + tuple(wk[3:])
            vec = wk[2]
        # Nach vorn (vom Betrachter weg) reichende Haende waeren hinter dem Kopf verdeckt: seitlich nur so weit versetzen, dass sie
        # neben dem Kopf frei liegen (nie auf dem Ruecken, nicht wie Fluegel abstehend).
        rh, lh = clear_head(f, rh, +1), clear_head(f, lh, -1)

    st = pose.get('stance')
    phase, amp, lift = ((tuple(st[:3]) + (2.4,))[:3] if st else (None, 5.0, 2.4))   # lift optional
    diag = st[3] if st and len(st) > 3 else 1.0   # <1: Beinausschlag in Schraegansichten verkleinern, damit die Beine sich nicht kreuzen
    kneek = st[4] if st and len(st) > 4 else 0.4  # Kniehub (Lauf: hoeher)
    env = st[5] if st and len(st) > 5 else 0.0    # Hubkurve des Schwungbeins (Lauf: breiter)

    cvb = Cv()   # hinter dem Koerper
    cv = Cv()
    cv.dy = pose.get('leg_dy', 0)   # Beine heben sich in der Flugphase vom Boden (Lauf)
    legs_pose(cv, base_view, phase, amp, lift, diag, kneek, env)
    adv = pose.get('adv', 0.0)   # Koerper um adv px in Blickrichtung nach vorn geschoben (Ausfallschritt)
    dy0 = pose.get('dy_n', pose.get('dy', 0)) if f[1] < 0 else pose.get('dy', 0)   # dy_n: eigener Wert fuer Rueckansichten
    cv.dy = dy0 + rnd(adv * f[1] * 0.8)
    lean = pose.get('lean', 0)
    cv.dx = rnd((lean + adv) * f[0] * 1.0) if f[0] else 0
    cvb.dy, cvb.dx = cv.dy, cv.dx
    if base_view == 'W':
        G.upper_side(cv, sp, 0)
    elif base_view in ('S', 'SW'):
        G.upper_front(cv, sp, 0, 1 if base_view == 'SW' else 0)
    else:
        G.upper_back(cv, sp, 0, 1 if base_view == 'NW' else 0)

    shR, shL = SHOULDER[base_view]
    hands = {'R': rh, 'L': lh}
    shoulders = {'R': shR, 'L': shL}

    sort_north = pose.get('sort_north', True)   # Rueckansicht: Haende nie auf den Ruecken legen, sondern nach Tiefe sortieren

    def is_front(h):
        return (north and not sort_north) or depth_of(f, h) > -0.5

    # Sortierung: Haende hinten zuerst
    order = sorted(('R', 'L'), key=lambda k: depth_of(f, hands[k]))
    hand_scr = {}
    for k in order:
        h = hands[k]
        front = is_front(h)
        tgt = project(f, h)
        target_cv = cv if front else cvb
        hand_scr[k] = draw_arm(target_cv, sp, shoulders[k], tgt, front, k, elbow_flare=-0.6 if flare else 0.4)   # Rueckansicht: Ellbogen zum Koerper, nicht als Fluegel
    hand_front = {k: is_front(hands[k]) for k in hands}

    # Waffe
    tip = None
    wkind = wk[0] if wk else None
    if wk:
        wh = wk[1]
        hp = hands[wh]
        wfront = hand_front[wh] or not north   # nur in der Rueckansicht kann die Waffe hinter dem Koerper liegen
        tcv = cv if wfront else cvb
        # Waffe haengt am (geklemmten) Handpunkt
        tip = DRAWERS[wkind](tcv, f, hp, vec, wfront, wk[3] if len(wk) > 3 else None)
    for k in order:
        h = hands[k]
        fr = hand_front[k]
        big = depth_of(f, h) > 6.5 and not wk
        draw_fist(cv if fr else cvb, hand_scr[k], fr, big)

    buf = outline(composite(cvb.b, cv.b))
    dx, dy = cv.dx, cv.dy

    # Effekte
    for e in pose.get('fx', []):
        kind = e[0]
        if kind == 'spark':           # ('spark', hand 'R'/'L', size)
            hk = e[1]
            if mirrored:
                hk = 'L' if hk == 'R' else 'R'
            sv = e[3] if len(e) > 3 else (1.0, 0.0, 0.0)
            sd = screen_dir(f, (sv[0], -sv[1] if mirrored else sv[1], sv[2]))
            hx_, hy_ = hand_scr[hk]
            fx_spark(buf, (hx_ + sd[0] * 3.0, hy_ + sd[1] * 3.0), dx, dy, e[2])
        elif kind == 'flash' and tip:
            sd = screen_dir(f, vec)
            fx_flash(buf, (tip[0] + sd[0] * 1.5, tip[1] + sd[1] * 1.5), sd, dx, dy, e[1])
        elif kind == 'bullet' and tip:
            sd = screen_dir(f, vec)
            dist = e[1]
            gx = vec[0]
            bx = tip[0] + sd[0] * dist
            by = tip[1] + sd[1] * dist
            fx_bullet(buf, (bx, by), sd, dx, dy, e[2] if len(e) > 2 else 3)
        elif kind == 'trail':         # ('trail', (theta0, phi0), (theta1, phi1)): Schwungbogen der Schlagerspitze
            hp = hands[wk[1]]
            (t0, p0), (t1, p1) = e[1], e[2]
            tl = TRAIL_LEN.get(wkind, 13.5)
            for ln, col in ((tl, TRAIL), (tl - 3.5, TRAIL2)):
                prev = None
                for i in range(0, 9):
                    u = i / 8.0
                    tv = t0 + (t1 - t0) * u
                    pv = p0 + (p1 - p0) * u
                    v = vec_dir(-tv if mirrored else tv, pv)
                    q = project(f, (hp[0] + (ln - 1.5) * v[0], hp[1] + (ln - 1.5) * v[1], hp[2] + (ln - 1.5) * v[2]))
                    if prev:
                        fx_trail(buf, prev, q, dx, dy, col)
                    prev = q
        elif kind == 'prop':          # ('prop', hand, 'food'|'bottle', stufe)
            hk = e[1]
            if mirrored:
                hk = 'L' if hk == 'R' else 'R'
            hp_ = hand_scr[hk]
            if e[2] == 'food':
                fx_food(buf, hp_, dx, dy, e[3])
            else:
                fx_bottle(buf, hp_, (23.5 + 2.0 * f[0], 13.0), dx, dy, e[3])
        elif kind == 'dust':
            fx_dust(buf, f, dx, dy, e[1])
        elif kind == 'stab_streak' and tip:
            sd = screen_dir(f, vec)
            for i in range(3, 9):
                put(buf, tip[0] - sd[0] * i, tip[1] - sd[1] * i + 1, TRAIL2 if i > 5 else TRAIL, dx, dy)

    if tip:
        mx = rnd(tip[0]) + OX + dx
        render_pose.muzzle = (CELL - 1 - mx if mirrored else mx, rnd(tip[1]) + OY + dy)
    else:
        render_pose.muzzle = None
    if mirrored:
        buf = [row[::-1] for row in buf]
    return buf


# ---------------------------------------------------------------- Posen-Definitionen
def vec_dir(theta, phi):
    """theta: Gierwinkel Grad (0 vorwaerts, +90 rechts), phi: Elevation Grad."""
    t, p = math.radians(theta), math.radians(phi)
    return (math.cos(t) * math.cos(p), math.sin(t) * math.cos(p), math.sin(p))


GUARD_R = (4.5, 4.5, -3.5)
GUARD_L = (6.0, -4.0, -2.0)


def seq_punch1():  # Jab links
    return [
        dict(lh=(3.0, -4.5, -3.0), rh=(4.5, 4.5, -3.5), stance=(0.75, 3.0), lean=-1, dy=1, dur=0.08),
        dict(lh=(8.0, -3.5, -0.5), rh=GUARD_R, stance=(0.25, 4.0, 0), lean=1, dy=1, dur=0.05),
        dict(lh=(10.5, -3.0, 0.5), rh=GUARD_R, stance=(0.25, 4.5, 0), lean=2, dy=1, dur=0.06, fx=[('spark', 'L', 2)]),
        dict(lh=(10.5, -3.0, 0.5), rh=GUARD_R, stance=(0.25, 4.5, 0), lean=2, dy=1, dur=0.10, fx=[('spark', 'L', 1)]),
        dict(lh=(7.0, -4.0, -1.5), rh=GUARD_R, stance=(0.25, 4.0, 0), lean=1, dy=0, dur=0.07),
        dict(lh=GUARD_L, rh=GUARD_R, stance=(0.25, 3.0), lean=0, dy=0, dur=0.07),
    ]


def seq_punch2():  # Gerade rechts
    return [
        dict(rh=(1.5, 5.0, -2.5), lh=GUARD_L, stance=(0.25, 3.0), lean=-2, dy=1, dur=0.08),
        dict(rh=(7.0, 4.0, -0.5), lh=GUARD_L, stance=(0.75, 4.0, 0), lean=0, dy=1, dur=0.05),
        dict(rh=(10.5, 2.5, 0.5), lh=(4.5, -4.5, -2.5), stance=(0.75, 5.0, 0), lean=2, dy=1, dur=0.06, fx=[('spark', 'R', 2)]),
        dict(rh=(10.5, 2.5, 0.5), lh=(4.5, -4.5, -2.5), stance=(0.75, 5.0, 0), lean=3, dy=1, dur=0.10, fx=[('spark', 'R', 1)]),
        dict(rh=(7.0, 4.0, -1.5), lh=GUARD_L, stance=(0.75, 4.0, 0), lean=1, dy=0, dur=0.07),
        dict(rh=GUARD_R, lh=GUARD_L, stance=(0.25, 3.0), lean=0, dy=0, dur=0.07),
    ]


def seq_punch3():  # Uppercut
    return [
        dict(rh=(2.5, 3.5, -8.5), lh=(6.0, -3.5, -1.0), stance=(0.25, 3.0), lean=-1, dy=2, dur=0.09),
        dict(rh=(5.0, 3.0, -5.0), lh=(6.0, -3.5, -1.0), stance=(0.75, 4.0, 0), lean=0, dy=2, dur=0.05),
        dict(rh=(8.0, 1.8, 4.5), lh=(5.0, -4.0, -1.5), stance=(0.75, 5.0, 0), lean=2, dy=-1, dur=0.06, fx=[('spark', 'R', 2, (0, 0, 1))]),
        dict(rh=(7.0, 1.8, 7.5), lh=(5.0, -4.0, -1.5), stance=(0.75, 5.0, 0), lean=2, dy=-1, dur=0.10, fx=[('spark', 'R', 1, (0, 0, 1))]),
        dict(rh=(5.0, 2.5, 3.0), lh=GUARD_L, stance=(0.75, 4.0, 0), lean=1, dy=0, dur=0.07),
        dict(rh=GUARD_R, lh=GUARD_L, stance=(0.25, 3.0), lean=0, dy=0, dur=0.07),
    ]


def seq_knife1():  # Stich gerade
    kv = vec_dir(0, 0)
    seq = []
    spec = [
        ((1.5, 3.5, -3.5), -2, 1, (0.25, 3.0), 0.08, []),
        ((4.0, 3.0, -2.0), 0, 1, (0.75, 4.5, 0), 0.04, []),
        ((9.5, 2.0, -1.0), 2, 1, (0.75, 5.5, 0), 0.05, [('stab_streak',)]),
        ((9.5, 2.0, -1.0), 2, 1, (0.75, 5.5, 0), 0.10, [('spark', 'R', 1)]),
        ((6.0, 3.0, -2.0), 1, 0, (0.75, 4.5, 0), 0.08, []),
        ((3.5, 3.5, -3.0), 0, 0, (0.25, 3.0), 0.08, []),
    ]
    for rh, lean, dy, st, du, fx in spec:
        seq.append(dict(rh=rh, lh=(5.0, -4.0, -3.0), weapon=('knife', 'R', kv), stance=st, lean=lean, dy=dy, dur=du, fx=fx))
    return seq


def seq_knife2():  # Stich von oben-schraeg nach vorn (Kombo-Variante)
    seq = []
    spec = [
        ((2.0, 3.5, 3.0), vec_dir(5, -30), -2, 1, (0.75, 3.0), 0.09, []),
        ((4.0, 3.0, 4.5), vec_dir(0, -40), -1, 1, (0.25, 4.5, 0), 0.04, []),
        ((8.0, 2.0, 0.0), vec_dir(0, -30), 2, 1, (0.25, 5.5, 0), 0.05, [('stab_streak',)]),
        ((9.0, 2.0, -3.0), vec_dir(0, -15), 2, 1, (0.25, 5.5, 0), 0.10, [('spark', 'R', 1)]),
        ((6.0, 3.0, -2.5), vec_dir(0, -5), 1, 0, (0.25, 4.5, 0), 0.08, []),
        ((3.5, 3.5, -3.0), vec_dir(0, 0), 0, 0, (0.75, 3.0), 0.08, []),
    ]
    for rh, kv, lean, dy, st, du, fx in spec:
        seq.append(dict(rh=rh, lh=(4.5, -4.5, -3.0), weapon=('knife', 'R', kv), stance=st, lean=lean, dy=dy, dur=du, fx=fx))
    return seq


def seq_swing(kind, key, two_hand=True, trail=(3, 4), spark=3, guard_l=(4.5, -4.5, -3.0), hand_off=3.0, stance_split=3):
    """Schlagwaffe. key = [(Gier, Elevation, Griff(d, r, z), lean, dy, dur[, (Gier, Elevation) der Kette]), ...].
    Bei zwei Haenden greift die linke hand_off Einheiten weiter vorn am Stiel, sonst bleibt sie in der Deckung."""
    seq = []
    for i, k in enumerate(key):
        th, ph, g, lean, dy, du = k[:6]
        v = vec_dir(th, ph)
        lh = (g[0] + hand_off * v[0], g[1] + hand_off * v[1], g[2] + hand_off * v[2]) if two_hand else guard_l
        wk = (kind, 'R', v) + ((vec_dir(*k[6]),) if len(k) > 6 else ())
        d = dict(rh=g, lh=lh, weapon=wk, stance=(0.25 if i < stance_split else 0.75, 5.0, 0), lean=lean, dy=dy, dur=du, fx=[])
        if i in trail:
            d['fx'].append(('trail', (key[i - 1][0], key[i - 1][1]), (th, ph)))
        if i == spark:
            d['fx'].append(('spark', 'R', 2))
        seq.append(d)
    return seq


def seq_bat():
    return seq_swing('bat', [
        (105, 60, (3.0, 4.0, 1.0), -1, 0, 0.08),
        (135, 45, (1.5, 5.0, 2.0), -2, 1, 0.09),
        (70, 12, (4.0, 3.5, 0.5), 0, 1, 0.04),
        (15, 0, (6.0, 1.5, -0.5), 2, 1, 0.04),
        (-40, 0, (6.0, -1.0, -0.5), 3, 1, 0.07),
        (-80, 20, (4.5, -2.5, 0.5), 2, 0, 0.09),
        (-60, 55, (3.5, 0.0, 0.5), 0, 0, 0.09),
    ])


def seq_club():  # Knueppel: beidhaendiger Hieb von der Schulter, schwerer und langsamer
    return seq_swing('club', [
        (140, 62, (2.5, 4.0, 2.5), -1, 0, 0.09),
        (165, 48, (1.0, 5.0, 3.5), -2, 1, 0.10),
        (85, 22, (4.0, 3.5, 1.0), 0, 1, 0.04),
        (20, 0, (6.0, 1.5, -0.5), 2, 1, 0.04),
        (-35, -5, (6.0, -0.5, -1.0), 3, 2, 0.08),
        (-70, 15, (4.5, -2.0, 0.0), 2, 1, 0.09),
        (-50, 50, (3.5, 0.5, 0.5), 0, 0, 0.09),
    ])


def seq_crowbar():  # Brecheisen: einhaendig von oben schraeg nach vorn unten
    return seq_swing('crowbar', [
        (35, 95, (1.5, 4.0, 3.5), -1, 0, 0.08),
        (30, 120, (0.5, 3.6, 5.5), -2, 1, 0.09),
        (30, 50, (4.0, 3.0, 2.0), 0, 1, 0.04),
        (5, -10, (7.0, 2.0, -0.5), 2, 1, 0.04),
        (-15, -35, (7.0, 1.0, -2.5), 3, 2, 0.07),
        (-20, -10, (5.0, 1.0, -1.5), 2, 1, 0.09),
        (0, 35, (3.5, 3.0, -1.0), 0, 0, 0.09),
    ], two_hand=False)


def seq_chop():  # Axt: beidhaendig ueber den Kopf, senkrecht nach unten
    return seq_swing('axe', [
        (0, 70, (2.5, 3.0, 3.0), -1, 0, 0.09),
        (0, 110, (1.5, 2.8, 5.8), -2, 1, 0.10),
        (0, 128, (0.5, 2.5, 6.5), -2, 1, 0.08),
        (0, 50, (4.0, 2.2, 2.0), 0, 1, 0.04),
        (0, -8, (7.5, 1.5, -1.0), 3, 2, 0.04),
        (0, -38, (7.5, 1.5, -3.0), 3, 2, 0.09),
        (0, 5, (5.0, 2.5, -2.5), 1, 1, 0.09),
        (0, 55, (3.0, 3.5, -3.0), 0, 0, 0.09),
    ], trail=(3, 4), spark=4, hand_off=3.5, stance_split=4)


def seq_flail():  # Dreschflegel: Kopf haengt an der Kette nach, schwingt ueber dem Kopf
    return seq_swing('flail', [
        (0, 65, (2.5, 3.0, 3.0), -1, 0, 0.09, (0, 20)),
        (0, 108, (1.5, 2.8, 5.5), -2, 1, 0.10, (0, 70)),
        (0, 125, (0.5, 2.5, 6.5), -2, 1, 0.08, (0, 112)),
        (0, 60, (4.0, 2.2, 2.0), 0, 1, 0.04, (0, 112)),
        (0, 8, (7.0, 1.6, -0.5), 3, 2, 0.04, (0, 70)),
        (0, -25, (7.5, 1.5, -2.5), 3, 2, 0.09, (0, -5)),
        (0, -10, (5.5, 2.5, -2.5), 1, 1, 0.09, (0, -62)),
        (0, 35, (3.5, 3.5, -3.0), 0, 0, 0.09, (0, -75)),
    ], trail=(), spark=5, hand_off=3.0, stance_split=4)


def seq_slash(back):  # Machete: einhaendiger Hieb quer vor dem Koerper; slash1 von rechts nach links, slash2 zurueck
    fwd = [
        (115, 25, (2.0, 4.8, 1.0), -2, 1, 0.08),
        (80, 15, (3.5, 4.5, 0.5), -1, 1, 0.05),
        (25, 5, (6.5, 3.2, -0.3), 1, 1, 0.04),
        (-10, 0, (7.5, 1.5, -0.5), 3, 1, 0.05),
        (-55, 5, (6.0, -0.5, -0.5), 3, 1, 0.07),
        (-75, 15, (4.0, -1.0, -1.0), 1, 0, 0.09),
    ]
    bk = [
        (-75, 20, (2.5, -1.0, 0.5), -2, 1, 0.08),
        (-40, 10, (3.5, -0.5, 0.0), -1, 1, 0.05),
        (0, 0, (6.5, 1.5, -0.5), 1, 1, 0.04),
        (35, 0, (7.5, 3.0, -0.7), 3, 1, 0.05),
        (70, 10, (5.5, 4.5, -0.7), 3, 1, 0.07),
        (100, 20, (3.5, 5.0, 0.0), 1, 0, 0.09),
    ]
    return seq_swing('machete', bk if back else fwd, two_hand=False, trail=(2, 3), spark=3, stance_split=3)


def seq_shoot():
    gv0 = vec_dir(0, 0)
    seq = []
    spec = [
        # rh, vec, lean, dy, dur, fx
        ((5.0, 3.0, -4.0), vec_dir(0, 35), -1, 0, 0.07, []),
        ((8.5, 1.5, -0.5), vec_dir(0, 3), 0, 0, 0.07, []),
        ((8.0, 1.5, 0.5), vec_dir(0, 12), 0, 0, 0.04, [('flash', 3), ('bullet', 1.0, 2)]),
        ((7.0, 1.5, 1.5), vec_dir(0, 22), -1, 0, 0.05, [('flash', 2), ('bullet', 6.0, 4)]),
        ((7.5, 1.5, 0.8), vec_dir(0, 12), -1, 0, 0.06, [('bullet', 12.0, 5)]),
        ((8.5, 1.5, -0.5), vec_dir(0, 3), 0, 0, 0.08, []),
        ((6.0, 2.5, -3.0), vec_dir(0, 30), 0, 0, 0.09, []),
    ]
    for rh, v, lean, dy, du, fx in spec:
        lh = (rh[0] - 0.2, rh[1] - 3.0, rh[2] - 0.5)
        seq.append(dict(rh=rh, lh=lh, weapon=('gun', 'R', v), stance=(0.25, 3.5), lean=lean, dy=dy, dur=du, fx=fx))
    return seq


def seq_longgun(kind):
    """Langwaffe an der Schulter, linke Hand stuetzt den Lauf. Je Waffe eigener Nachlade-Takt: Pumpgun pumpt (linke Hand vor/zurueck),
    Repetierbuechse bedient den Kammerstengel (rechte Hand), Gewehr und Sturmgewehr bleiben im Anschlag.
    Eintrag: (rh, Elevation, lean, dy, dur, fx, Abstand linke Hand)."""
    R0, R1 = (4.2, 2.0, -1.5), (3.8, 1.8, 0.3)
    fire = [('flash', 4), ('bullet', 1.0, 2)]
    after = [('flash', 2), ('bullet', 6.0, 4)]
    fly = [('bullet', 12.0, 5)]
    base = [
        (R0, 12, -1, 0, 0.07, [], 6.5),
        (R1, 2, 0, 0, 0.07, [], 6.5),
        (R1, 7, 0, 0, 0.04, fire, 6.5),
        ((3.2, 1.8, 0.7), 13, -1, 0, 0.05, after, 6.5),
        ((3.5, 1.8, 0.4), 7, -1, 0, 0.06, fly, 6.5),
    ]
    if kind == 'shotgun':
        spec = base + [(R1, 5, 0, 0, 0.06, [], 3.5), (R1, 3, 0, 0, 0.06, [], 7.0), (R1, 2, 0, 0, 0.07, [], 6.5), ((4.5, 2.0, -1.8), 18, 0, 0, 0.09, [], 6.5)]
    elif kind == 'sniper':
        spec = base + [((3.8, 2.6, 1.4), 4, 0, 0, 0.06, [], 6.5), ((2.4, 2.4, 1.2), 4, 0, 0, 0.06, [], 6.5), ((3.8, 2.0, 0.5), 3, 0, 0, 0.06, [], 6.5),
                       (R1, 2, 0, 0, 0.07, [], 6.5), ((4.5, 2.0, -1.8), 18, 0, 0, 0.09, [], 6.5)]
    else:
        spec = base + [(R1, 2, 0, 0, 0.08, [], 6.5), ((4.5, 2.0, -1.8), 18, 0, 0, 0.09, [], 6.5)]
    seq = []
    for rh, el, lean, dy, du, fx, lo in spec:
        v = vec_dir(0, el)
        lh = (rh[0] + lo * v[0], rh[1] + lo * v[1] - 1.0, rh[2] + lo * v[2] - 0.6)
        seq.append(dict(rh=rh, lh=lh, weapon=(kind, 'R', v), stance=(0.25, 3.0), lean=lean, dy=dy, dur=du, fx=fx))
    return seq


def seq_rifle():
    return seq_longgun('rifle')


def run_hand(side, s, d0, damp, lat, z0, zamp, alt=None):
    """Handposition im Lauf als Funktion der Ansicht. Von der Seite pendelt die Hand nach vorn/hinten (d);
    von vorn/hinten sieht man das kaum, dort bleibt der Arm am Koerper (z: kleiner Ausschlag, Hand vorn etwas hoeher)
    und die Hand ruecken nach innen, damit der Ellbogen nicht wie ein Fluegel absteht.
    side = +1 (rechte Hand) / -1 (linke Hand), s = Sinus der Phase (+1: Hand ganz hinten).
    alt = (d0, damp, lat, z0, zamp) fuer alle Ansichten ausser der reinen Seitenansicht (dort sind die Werte oben)."""
    def fn(f):
        d0_, damp_, lat_, z0_, zamp_ = (d0, damp, lat, z0, zamp) if (f[1] == 0 or alt is None) else alt
        k = abs(f[1])                    # 0 = Seitenansicht, 1 = von vorn/hinten
        k2 = k * k
        d = d0_ - damp_ * s
        r = side * (lat_ - 1.1 * k2)
        if f[1] < 0:                     # von hinten: Arme seitlich am Koerper vorbei, nicht ueber den Ruecken
            r = side * (lat_ + 0.9 * k2 - 3.2 * k * max(0.0, -s) + 10.0 * k * (1.0 - k) * max(0.0, s))   # Hand vorn (hinter dem Koerper) rueckt nach innen, ragt sonst als Fluegel heraus
            d = d0_ - damp_ * s * (1.0 - 0.55 * k2)
            d = max(-6.0, min(d, 2.5))                   # nach vorn gependelt wandert die Hand in Schraegansicht sonst seitlich ueber die Silhouette
            z = z0_ - 5.0 * k2 - zamp_ * s * (1.0 - k2)   # Arm fast gestreckt: sonst knickt der Ellbogen als Fluegel ab
            return (d, r, z)
        z = z0_ - 3.0 * k2 - zamp_ * s
        z -= 1.0 * k2 * (1.0 - abs(s))   # in der Mitte der Pendelbewegung hangt der Arm tiefer als an den Umkehrpunkten
        dg = 2.0 * abs(f[0] * f[1])      # 1 in den Schraegansichten: die Hand wuerde sonst ueber die Brust zur anderen Seite pendeln (wirkt wie verschraenkte Arme)
        d = d0_ * (1.0 - dg) - damp_ * s * (1.0 - 0.8 * dg)
        r += side * 2.2 * dg
        z -= 2.5 * dg
        return (d, r, z)
    return fn


def seq_run():
    """Lauf: Kniehub, Flugphase (Beine heben ab, wenn sie weit auseinander sind), Oberkoerper nach vorn, Arme abgewinkelt im Gegentakt.
    Phase p: bei s = sin(2 pi p) = 0 steht ein Bein unter dem Koerper (tiefster Punkt), bei |s| = 1 sind die Beine gespreizt (Flug, hoechster Punkt)."""
    seq = []
    for c in range(8):
        p = c / 8.0
        s = math.sin(2 * math.pi * p)
        rh = run_hand(+1, s, 1.0, 6.0, 4.5, -4.2, 4.2, alt=(1.0, 7.5, 4.5, -5.5, 3.0))
        lh = run_hand(-1, -s, 1.0, 6.0, 4.5, -4.2, 4.2, alt=(1.0, 7.5, 4.5, -5.5, 3.0))
        flight = abs(s)
        dy = 1 - rnd(2 * flight)            # s=0: +1 (tief), |s|=1: -1 (hoch)
        seq.append(dict(rh=rh, lh=lh, stance=(p, 8.5, 6.5, 0.55, 1.0, 0.45), lean=3, dy=dy, dy_n=dy, leg_dy=-1 if flight > 0.9 else 0, dur=0.075, sort_north=True))
    return seq


def seq_sprint():
    """Sprint: schneller als Run, tiefer Vorlehnen, grosse Schritte, hoher Kniehub, Arme eng angewinkelt."""
    seq = []
    for c in range(8):
        p = c / 8.0
        s = math.sin(2 * math.pi * p)
        rh = run_hand(+1, s, 1.5, 6.5, 3.4, -3.8, 4.6, alt=(1.5, 8.0, 3.4, -5.0, 3.5))
        lh = run_hand(-1, -s, 1.5, 6.5, 3.4, -3.8, 4.6, alt=(1.5, 8.0, 3.4, -5.0, 3.5))
        flight = abs(s)
        dy = 1 - rnd(3 * flight)
        seq.append(dict(rh=rh, lh=lh, stance=(p, 10.0, 7.5, 0.5, 1.2, 0.5), lean=4, dy=dy, dy_n=dy, leg_dy=-2 if flight > 0.9 else (-1 if flight > 0.6 else 0), dur=0.06, sort_north=True))
    return seq


def seq_dodge():
    """Ausweichen/Dash: Hocke, kraeftiger Abstoss, ein grosser Ausfallschritt nach vorn, Landung, Aufrichten.
    Der Koerper wandert nur wenige Pixel (die Strecke legt Unity zurueck), die Beine spannen weit, Oberkoerper lehnt vor."""
    # (adv, lean, dy, Beinweite, Hubhoehe, Armausschlag, dur)
    key = [
        (0.0, -1, 1, 2.5, 0.0, 2.0, 0.06),     # Ausholen: Hocke, Oberkoerper leicht zurueck
        (1.0, 2, 1, 6.0, 0.0, 5.0, 0.05),      # Abstoss: Standbein streckt sich nach hinten
        (2.0, 4, 1, 10.0, 0.0, 8.0, 0.06),     # Ausfallschritt: weite Beine, Arme gegenlaeufig
        (3.0, 4, 2, 10.5, 0.0, 8.5, 0.07),     # tiefster Punkt, vorderes Knie gebeugt
        (2.0, 3, 2, 8.0, 0.0, 6.0, 0.07),      # Landung abfedern
        (0.0, 1, 1, 4.0, 0.0, 3.0, 0.07),      # Aufrichten
    ]
    seq = []
    for adv, lean, dy, amp, lift, arm, du in key:
        rh = run_hand(+1, 1.0, 1.0, arm, 3.4, -5.0, 2.0)
        lh = run_hand(-1, -1.0, 1.0, arm, 3.4, -5.0, 2.0)
        seq.append(dict(rh=rh, lh=lh, stance=(0.25, amp, lift, 0.5), lean=lean, adv=adv, dy=dy, dy_n=max(0, dy - 2), dur=du, sort_north=True))
    return seq


ANIMS = {
    'dodge': seq_dodge,
    'run': seq_run,
    'sprint': seq_sprint,
    'punch1': seq_punch1,
    'punch2': seq_punch2,
    'punch3': seq_punch3,
    'knife1': seq_knife1,
    'knife2': seq_knife2,
    'bat': seq_bat,
    'shoot': seq_shoot,
    'club': seq_club,
    'crowbar': seq_crowbar,
    'chop': seq_chop,
    'flail': seq_flail,
    'machete1': lambda: seq_slash(False),
    'machete2': lambda: seq_slash(True),
    'rifle': seq_rifle,
    'shotgun': lambda: seq_longgun('shotgun'),
    'assault': lambda: seq_longgun('assault'),
    'sniper': lambda: seq_longgun('sniper'),
}

# Das Standbein im Run nutzt die Lauf-Legs (phase), alle anderen Posen ihr Stance-Tuple.


def build(name, outdir, only=None):
    spec = SPECS[name]
    os.makedirs(outdir, exist_ok=True)
    durs = {}
    for an, fn in ANIMS.items():
        if only and an not in only:
            continue
        seq = fn()
        sheet = Image.new('RGBA', (len(seq) * CELL, 8 * CELL))
        for r, v in enumerate(ORDER):
            for c, pose in enumerate(seq):
                sheet.paste(to_img(render_pose(spec, v, pose)), (c * CELL, r * CELL))
        sheet.save(os.path.join(outdir, '%s_%s.png' % (name.lower(), an)))
        durs[an] = [p['dur'] for p in seq]
    return durs


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    for n in SPECS:
        build(n, os.path.join(base, n), only)
        print('ok', n)
