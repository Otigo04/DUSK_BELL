"""Pickup (alter, verbeulter Farm-Truck) in 8 Richtungen, je 8 Bilder, 112x80-Raster.

Das Auto wird als Voxel-Modell gebaut (Karosserie, Fuehrerhaus mit Scheiben, Ladeflaeche mit Ladung, Raeder, Spiegel, Stossstangen,
Lichter) und per Strahlenverfolgung in der gleichen leicht von oben geneigten Seitenansicht gerendert wie die Spielfiguren. Pro Richtung entsteht
dadurch eine in sich stimmige Ansicht. Beleuchtung: flaches Licht von links oben, vier Stufen je Material (nur Hex-Werte im Palettenton),
dunkle Kontur, Schatten am Boden.

Blatt: Zeile = Richtung in der Reihenfolge E, NE, N, NW, W, SW, S, SE (Winkel 0, 45, ..., 315 Grad, 0 = nach rechts, 90 = nach oben/Norden).
Spalte 0-3 = Fahrt (Raeder drehen, Karosserie wippt leicht), Spalte 4-7 = dasselbe mit leuchtenden Bremslichtern.
Pivot: Mitte des Autos auf dem Boden (Pixel 56, 52 von 112x80).

Aufruf:  python gen_pickup.py [Ausgabeordner]     (Standard: Ordner darueber = Art/Vehicles)
Ausgabe: Auto_Pickup.png (Blatt) und Auto_Pickup.json (Raster und Pivot fuer den Import) im Ausgabeordner, Auto_Pickup_preview.png (4x, nur Ansicht) neben dem Skript
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(HERE, '..'))

CELL_W, CELL_H = 112, 80
PIVOT = (56, 52)                       # Bodenmitte des Autos im Rahmen
PS = 0.5                               # Pixelgroesse in Voxeln: 2 Pixel pro Voxel
EL = math.radians(30.0)                # Kamera-Neigung
DIRS = 8
FRAMES = 4


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


# ---------------------------------------------------------------- Materialien: je 4 Stufen (dunkel .. hell)
PAINT = ('#3b1f2b', '#6a2433', '#8f3447', '#bd5560')           # verblichenes Weinrot
UNDER = ('#0f0c18', '#1a1526', '#2b2140', '#3d2e4a')
GLASS = ('#14101f', '#1f2a3d', '#2c3e56', '#6b7fb8')
TIRE = ('#0f0c18', '#1a1526', '#2b2140', '#3d2e4a')
TREAD = ('#1a1526', '#2b2140', '#3d2e4a', '#4a4550')
HUB = ('#4a4550', '#6e6a74', '#9a95a0', '#e8e0f0')
CHROME = ('#3d2e4a', '#6e6a74', '#9a95a0', '#e8e0f0')
WOOD = ('#3b2a22', '#5c4033', '#7a5a43', '#9c7a5a')
RUST = ('#3b2a22', '#5c4033', '#8c5f4d', '#b07a58')
MUD = ('#2b2140', '#3b2a22', '#5c4033', '#7a5a43')
LAMP = ('#ffd27a', '#ffd27a', '#fff1c9', '#fff1c9')             # leuchtet selbst
TAIL = ('#8a1f3d', '#a8203f', '#d64a6a', '#d64a6a')
TAIL_BRAKE = ('#e8733a', '#ff8a4a', '#ffd27a', '#fff1c9')
LINER = ('#0f0c18', '#1a1526', '#2b2140', '#4a4550')
CASE = ('#2b2140', '#3b2a22', '#5c4033', '#7a5a43')
CAN = ('#7a3a1f', '#b8501f', '#e8733a', '#ffa550')
PLATE = ('#6e6a74', '#9a95a0', '#e8e0f0', '#f2ead8')
LUG = ('#9a95a0', '#9a95a0', '#e8e0f0', '#fff1c9')
SEAM = ('#14101f', '#1a1526', '#2b2140', '#3d2e4a')
TARP = ('#1e3a2b', '#2f5a3c', '#4a7a4f', '#6e9a5e')

(M_AIR, M_PAINT, M_UNDER, M_GLASS, M_TIRE, M_HUB, M_CHROME, M_WOOD, M_RUST, M_MUD, M_LAMP, M_TAIL, M_LINER,
 M_CASE, M_CAN, M_PLATE, M_LUG, M_TREAD, M_SEAM, M_TARP) = range(20)

RAMPS = {
    M_PAINT: PAINT, M_UNDER: UNDER, M_GLASS: GLASS, M_TIRE: TIRE, M_HUB: HUB, M_CHROME: CHROME, M_WOOD: WOOD,
    M_RUST: RUST, M_MUD: MUD, M_LAMP: LAMP, M_TAIL: TAIL, M_LINER: LINER, M_CASE: CASE, M_CAN: CAN,
    M_PLATE: PLATE, M_LUG: LUG, M_TREAD: TREAD, M_SEAM: SEAM, M_TARP: TARP,
}
EMISSIVE = {M_LAMP}
OUTLINE = hx('#1a1526')
SHADOW = hx('#0f0c18')

# ---------------------------------------------------------------- Modell
NX, NY, NZ = 56, 24, 24                # Voxelraum (mit Rand)
CX, CY = 28, 12                        # Mitte des Autos im Voxelraum
LEN, WID = 52, 18                      # Karosserie: x 2..53 (Laenge), y 3..20 (Breite)
X0, X1 = 2, 53                         # hinten, vorne (einschliesslich)
Y0, Y1 = 3, 20                         # rechts, links (einschliesslich)
WHEEL_Z = 4.6
WHEEL_R = 4.5
WHEELS = ((12.5, 'rear'), (41.5, 'front'))
CAB_X0, CAB_X1 = 17, 33                # Fuehrerhaus
HOOD_X0 = 33


def hash3(x, y, z, salt=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791) ^ (salt * 2654435761)) & 0xffff


def box(v, x0, x1, y0, y1, z0, z1, m):
    v[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = m


def hood_top(x):
    """Obere Kante der Motorhaube (z-Index der letzten Schicht): vorne zum Kuehler abfallend."""
    if x >= X1 - 1:
        return 9
    if x >= X1 - 3:
        return 10
    return 11


def cab_top(x):
    """Dach und Windschutzscheibe: Dach flach, vorne in 4 Schritten zur Motorhaube geneigt, hinten steil."""
    if x < CAB_X0 + 1:
        return 15
    if x <= 27:
        return 17
    return {28: 16, 29: 15, 30: 14, 31: 13, 32: 12}.get(x, 11)


def build_body(brake):
    v = np.zeros((NX, NY, NZ), np.uint8)

    # Unterboden und Rahmen
    box(v, X0, X1, Y0 + 2, Y1 - 2, 2, 4, M_UNDER)

    # Karosserie-Kern (Schalen aussen, dunkler Kern innen, damit Radkaesten nicht durchsichtig sind)
    box(v, X0, X1, Y0, Y1, 4, 8, M_PAINT)

    # Haube und Kotfluegel bis zur Kante
    for x in range(HOOD_X0, X1 + 1):
        for z in range(9, hood_top(x) + 1):
            v[x, Y0:Y1 + 1, z] = M_PAINT
    # Fuehrerhaus
HOOD_X0 = 33


def hash3(x, y, z, salt=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791) ^ (salt * 2654435761)) & 0xffff


def box(v, x0, x1, y0, y1, z0, z1, m):
    v[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = m


def hood_top(x):
    """Obere Kante der Motorhaube (z-Index der letzten Schicht): vorne zum Kuehler abfallend."""
    if x >= X1 - 1:
        return 9
    if x >= X1 - 3:
        return 10
    return 11


def cab_top(x):
    """Dach und Windschutzscheibe: Dach flach, vorne in 4 Schritten zur Motorhaube geneigt, hinten steil."""
    if x < CAB_X0 + 1:
        return 15
    if x <= 27:
        return 17
    return {28: 16, 29: 15, 30: 14, 31: 13, 32: 12}.get(x, 11)


def build_body(brake):
    v = np.zeros((NX, NY, NZ), np.uint8)

    # Unterboden und Rahmen
    box(v, X0, X1, Y0 + 2, Y1 - 2, 2, 4, M_UNDER)

    # Karosserie-Kern (Schalen aussen, dunkler Kern innen, damit Radkaesten nicht durchsichtig sind)
    box(v, X0, X1, Y0, Y1, 4, 8, M_PAINT)

    # Haube und Kotfluegel bis zur Kante
    for x in range(HOOD_X0, X1 + 1):
        for z in range(9, hood_top(x) + 1):
            v[x, Y0:Y1 + 1, z] = M_PAINT
    # Haubenwoelbung: Mitte eine Schicht hoeher bis kurz vor den Kuehler
    for x in range(HOOD_X0 + 1, X1 - 4):
        v[x, Y0 + 5:Y1 - 4, hood_top(x) + 1] = M_PAINT

    # Fuehrerhaus
    for x in range(CAB_X0, CAB_X1 + 1):
        for z in range(9, cab_top(x) + 1):
            v[x, Y0 + 1:Y1, z] = M_PAINT
    # Dachkanten abrunden
    for x in (CAB_X0 + 1, 27):
        v[x, Y0 + 1, 17] = M_AIR
        v[x, Y1 - 1, 17] = M_AIR
    for x in range(CAB_X0 + 1, 28):
        v[x, Y0 + 1, 17] = M_AIR
        v[x, Y1 - 1, 17] = M_AIR
    # Dachhimmel nur oben: etwas Verkleidung am Rand
    # Scheiben: Seitenfenster (aeussere Schicht), B-Saeule bei x 24-25, Front- und Heckscheibe
    for side_y in (Y0 + 1, Y1 - 1):
        for x in range(CAB_X0 + 2, 30):
            if x in (24, 25):
                continue
            top = min(cab_top(x) - 1, 16)
            for z in range(11, top + 1):
                if z <= 16:
                    v[x, side_y, z] = M_GLASS
    for x in range(28, 33):                              # Windschutzscheibe (Schraege)
        z = cab_top(x)
        for dz in (0, -1):
            if z + dz >= 11:
                v[x, Y0 + 2:Y1 - 1, z + dz] = M_GLASS
    for z in range(11, 16):                              # Heckscheibe
        v[CAB_X0, Y0 + 3:Y1 - 2, z] = M_GLASS
        v[CAB_X0 + 1, Y0 + 3:Y1 - 2, z] = M_GLASS
    # Heckscheibe sitzt in der Rueckwand der Kabine (Bett davor): Rahmenstreifen oben
    v[CAB_X0, Y0 + 3:Y1 - 2, 16] = M_PAINT

    # Tuerfugen und Griffe (seitlich)
    for side_y in (Y0, Y1):
        for z in range(5, 11):
            for sx in (CAB_X0 + 1, 24, 31):
                if v[sx, side_y, z] == M_PAINT:
                    v[sx, side_y, z] = M_SEAM
        for gx in (22, 23):
            v[gx, side_y, 9] = M_CHROME
        for gx in (29, 30):
            v[gx, side_y, 9] = M_CHROME

    # Ladeflaeche: Boden, Waende, Heckklappe, Radkaesten innen
    box(v, X0, CAB_X0 - 1, Y0 + 1, Y1 - 1, 4, 7, M_LINER)               # Boden (Oberkante z = 8)
    for z in range(8, 11):
        v[X0:CAB_X0, Y0, z] = M_PAINT                                    # rechte Wand
        v[X0:CAB_X0, Y1, z] = M_PAINT                                    # linke Wand
        v[X0, Y0:Y1 + 1, z] = M_PAINT                                    # Heckklappe
    v[X0:CAB_X0, Y0, 11] = M_CHROME                                      # Randleiste der Wand
    v[X0:CAB_X0, Y1, 11] = M_CHROME
    v[X0, Y0:Y1 + 1, 11] = M_CHROME
    v[X0 + 1, Y0 + 7:Y0 + 11, 9] = M_SEAM                                # Heckklappen-Griff
    for (a, b) in ((Y0 + 1, Y0 + 3), (Y1 - 3, Y1 - 1)):                  # Radkastenwoelbungen
        box(v, 8, 16, a, b, 8, 9, M_PAINT)
    # Ladung: Holzkiste, Koffer, Benzinkanister, aufgerolltes Segeltuch
    box(v, X0 + 2, X0 + 7, Y0 + 4, Y0 + 9, 8, 12, M_WOOD)
    box(v, X0 + 2, X0 + 7, Y0 + 4, Y0 + 4, 10, 10, M_UNDER)             # Latte
    box(v, X0 + 3, X0 + 9, Y0 + 11, Y0 + 15, 8, 11, M_CASE)
    box(v, X0 + 3, X0 + 9, Y0 + 13, Y0 + 13, 11, 11, M_CHROME)          # Koffer-Griff
    box(v, X0 + 10, X0 + 12, Y0 + 4, Y0 + 6, 8, 11, M_CAN)              # Kanister
    box(v, X0 + 9, X0 + 13, Y0 + 7, Y0 + 10, 8, 9, M_TARP)              # Segeltuch

    # Frontpartie: Kuehlergrill (dunkel mit Chromstreben), Scheinwerfer, Stossstange
    gx = X1
    box(v, gx, gx, Y0 + 4, Y1 - 4, 5, 9, M_UNDER)
    for z in (6, 8):
        box(v, gx, gx, Y0 + 4, Y1 - 4, z, z, M_CHROME)
    box(v, gx, gx, Y0 + 1, Y0 + 3, 6, 8, M_CHROME)                      # Scheinwerferfassung
    box(v, gx, gx, Y1 - 3, Y1 - 1, 6, 8, M_CHROME)
    box(v, gx, gx, Y0 + 2, Y0 + 2, 7, 7, M_LAMP)
    box(v, gx, gx, Y1 - 2, Y1 - 2, 7, 7, M_LAMP)
    box(v, gx, gx, Y0 + 1, Y0 + 3, 7, 7, M_LAMP)
    box(v, gx, gx, Y1 - 3, Y1 - 1, 7, 7, M_LAMP)
    box(v, gx + 1, gx + 1, Y0, Y1, 3, 5, M_CHROME)                      # Stossstange
    box(v, gx + 1, gx + 1, Y0 + 7, Y0 + 10, 4, 4, M_PLATE)               # Kennzeichen

    # Heck: Rueckleuchten, Stossstange, Auspuff
    rx = X0
    tail = M_TAIL
    box(v, rx, rx, Y0, Y0 + 2, 5, 7, tail)
    box(v, rx, rx, Y1 - 2, Y1, 5, 7, tail)
    box(v, rx - 1, rx - 1, Y0 + 1, Y1 - 1, 3, 5, M_CHROME)
    box(v, rx - 1, rx - 1, Y0 + 7, Y0 + 10, 4, 4, M_PLATE)
    box(v, rx - 2, rx - 1, Y1 - 3, Y1 - 3, 3, 3, M_CHROME)              # Auspuffende
    v[rx - 2, Y1 - 3, 3] = M_UNDER

    # Aussenspiegel: schwarze Arme mit Spiegel
    for sy, dy in ((Y0, -1), (Y1, 1)):
        v[31, sy + dy, 13] = M_UNDER
        v[31, sy + dy, 14] = M_UNDER
        v[30, sy + dy, 13] = M_UNDER
        v[30, sy + dy, 14] = M_UNDER

    # Schmutz und Rost (feste Zufallsmuster, damit alle Ansichten zusammenpassen)
    rng = np.random.RandomState(7)
    surf = np.argwhere(v == M_PAINT)
    for _ in range(9):
        x, y, z = surf[rng.randint(len(surf))]
        r = rng.choice([1, 1, 1, 2])
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    xx, yy, zz = x + dx, y + dy, z + dz
                    if 0 <= xx < NX and 0 <= yy < NY and 0 <= zz < NZ and v[xx, yy, zz] == M_PAINT and dx * dx + dy * dy + dz * dz <= r * r + 1:
                        v[xx, yy, zz] = M_RUST
    for x in range(X0, X1 + 1):                                         # Dreck an der Unterkante
        for y in (Y0, Y1, Y0 + 1, Y1 - 1):
            for z in (4, 5):
                if v[x, y, z] == M_PAINT and hash3(x, y, z, 3) % 4 == 0:
                    v[x, y, z] = M_MUD
    # Radkaesten ausschneiden (nur die Aussenschalen), Kern bleibt dunkel
    for xc, _ in WHEELS:
        for x in range(NX):
            for z in range(NZ):
                if (x + 0.5 - xc) ** 2 + (z + 0.5 - WHEEL_Z) ** 2 < 5.9 ** 2 and z <= 11:
                    for y in list(range(Y0, Y0 + 4)) + list(range(Y1 - 3, Y1 + 1)):
                        if v[x, y, z] in (M_PAINT, M_RUST, M_MUD, M_SEAM):
                            v[x, y, z] = M_UNDER
    return v


def add_wheels(v, phase):
    v = v.copy()
    rot = -phase * math.radians(18.0)
    for xc, _ in WHEELS:
        for side in ('r', 'l'):
            ys = range(Y0 - 1, Y0 + 3) if side == 'r' else range(Y1 - 2, Y1 + 2)
            outer = Y0 - 1 if side == 'r' else Y1 + 1
            for y in ys:
                for x in range(NX):
                    for z in range(NZ):
                        dx, dz = x + 0.5 - xc, z + 0.5 - WHEEL_Z
                        r = math.hypot(dx, dz)
                        if r > WHEEL_R:
                            continue
                        ang = math.atan2(dz, dx) - rot
                        if y == outer:                                    # Felge sichtbar
                            if r > 3.3:
                                m = M_TREAD if int(math.floor(ang / math.radians(30.0))) % 2 == 0 and r > 3.7 else M_TIRE
                            elif r < 1.2:
                                m = M_CHROME
                            else:
                                m = M_HUB
                                for k in range(5):
                                    d = abs(math.remainder(ang - k * math.radians(72.0), math.tau))
                                    if r > 1.7 and r < 2.9 and d < math.radians(15.0):
                                        m = M_LUG
                        else:
                            m = M_TIRE if r > 3.0 else M_UNDER
                        v[x, y, z] = m
    return v


def finish(v, brake):
    v = v.copy()
    if brake:
        v[v == M_TAIL] = M_TAIL   # Material bleibt, die Rampe wechselt im Renderer
    return v


# ---------------------------------------------------------------- Rendern
LIGHT = np.array([-0.453, -0.252, 0.855])
STEP = 0.2
TRANGE = 60.0


def occlusion(v):
    """Pro Voxel und Flaechenrichtung: wie viele der 8 Nachbarn in der Flaechenebene (eine Schicht davor) sind belegt."""
    solid = (v > 0).astype(np.int16)
    occ = {}
    axes = {'x': 0, 'y': 1, 'z': 2}
    for axis in range(3):
        for sign in (1, -1):
            shifted = np.roll(solid, -sign, axis=axis)     # Zelle direkt vor der Flaeche
            tan = [a for a in range(3) if a != axis]
            cnt = np.zeros_like(solid)
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    if da == 0 and db == 0:
                        continue
                    cnt += np.roll(np.roll(shifted, da, axis=tan[0]), db, axis=tan[1])
            occ[(axis, sign)] = cnt
    return occ


def render(v, occ, phi_deg, brake, bob):
    phi = math.radians(phi_deg)
    cphi, sphi = math.cos(phi), math.sin(phi)

    px = np.arange(CELL_W)
    py = np.arange(CELL_H)
    pxx, pyy = np.meshgrid(px, py)
    oy = PIVOT[1] + bob                       # Wippen: ganze Figur 1 px hoeher
    u = (pxx + 0.5 - PIVOT[0]) * PS
    vv = (oy - (pyy + 0.5)) * PS
    u, vv = u.ravel(), vv.ravel()
    n = u.size

    sinE, cosE = math.sin(EL), math.cos(EL)
    # Welt: R=(1,0,0), U=(0,sinE,cosE), d=(0,cosE,-sinE); P = R*u + U*v + d*t
    hit_t = np.full(n, np.inf)
    hit_m = np.zeros(n, np.uint8)
    hit_i = np.zeros((n, 3), np.int32)
    hit_n = np.zeros((n, 3), np.int8)
    prev_i = None
    done = np.zeros(n, bool)

    ts = np.arange(-TRANGE, TRANGE, STEP)
    prev_idx = None
    for t in ts:
        gx = u
        gy = vv * sinE + t * cosE
        gz = vv * cosE - t * sinE
        lx = gx * cphi + gy * sphi
        ly = -gx * sphi + gy * cphi
        ix = np.floor(lx + CX).astype(np.int32)
        iy = np.floor(ly + CY).astype(np.int32)
        iz = np.floor(gz).astype(np.int32)
        ok = (ix >= 0) & (ix < NX) & (iy >= 0) & (iy < NY) & (iz >= 0) & (iz < NZ)
        m = np.zeros(n, np.uint8)
        m[ok] = v[ix[ok], iy[ok], iz[ok]]
        newhit = (m > 0) & (~done)
        if newhit.any():
            hit_m[newhit] = m[newhit]
            hit_t[newhit] = t
            hit_i[newhit] = np.stack([ix[newhit], iy[newhit], iz[newhit]], 1)
            if prev_idx is not None:
                d = hit_i[newhit] - prev_idx[newhit]
                nrm = np.zeros((int(newhit.sum()), 3), np.int8)
                nrm = np.zeros((int(newhit.sum()), 3), np.int8)
                # Achse mit dem groessten Strahlanteil unter den geaenderten Achsen (Ecken eindeutig machen)
                ray_local = np.array([cosE * sphi, cosE * cphi, -sinE])
                diffs = d != 0
                weights = np.abs(ray_local)[None, :] * diffs
                axis = np.argmax(weights, 1)
                has = diffs.any(1)
                axis = np.where(has, axis, 2)
                for a in range(3):
                    sel = axis == a
                    if sel.any():
                        sign = np.sign(d[sel, a])
                        sign = np.where(sign == 0, 1, sign)
                        nrm[sel, a] = -sign
                hit_n[newhit] = nrm
            else:
                hit_n[newhit] = np.array([0, 0, 1], np.int8)
            done |= newhit
        prev_idx = np.stack([ix, iy, iz], 1)
        if done.all():
            break

    img = np.zeros((n, 4), np.uint8)
    depth = hit_t.copy()
    solid = done
    # Schattierung
    nl = hit_n.astype(np.float64)
    wx = nl[:, 0] * cphi - nl[:, 1] * sphi
    wy = nl[:, 0] * sphi + nl[:, 1] * cphi
    wz = nl[:, 2]
    dot = wx * LIGHT[0] + wy * LIGHT[1] + wz * LIGHT[2]
    level = np.where(dot > 0.65, 3, np.where(dot > 0.1, 2, np.where(dot > -0.35, 1, 0)))
    # Ambient Occlusion: eingeklemmte Flaechen eine Stufe dunkler
    ao = np.zeros(n, np.int16)
    for a in range(3):
        for s in (1, -1):
            sel = solid & (hit_n[:, a] == s)
            if sel.any():
                idx = hit_i[sel]
                ao[sel] = occ[(a, s)][idx[:, 0], idx[:, 1], idx[:, 2]]
    level = np.where(ao >= 3, level - 1, level)
    # Koernung: einzelne Voxelflaechen etwas heller/dunkler
    hsh = (hit_i[:, 0] * 73856093 ^ hit_i[:, 1] * 19349663 ^ hit_i[:, 2] * 83492791) & 0xffff
    grit = (hsh % 37 == 0)
    glint = (hsh % 31 == 1)
    level = np.where(grit & (level > 0), level - 1, level)
    level = np.where(glint & (level < 3) & ((hit_m == M_WOOD) | (hit_m == M_CASE) | (hit_m == M_HUB)), level + 1, level)
    # Scheiben: schraege Spiegelung
    glass = hit_m == M_GLASS
    streak = ((hit_i[:, 0] + hit_i[:, 2] * 2) % 9 == 0)
    level = np.where(glass & streak, 3, np.where(glass & (~streak), np.minimum(level, 1), level))
    level = np.clip(level, 0, 3)

    for m_id, ramp in RAMPS.items():
        sel = solid & (hit_m == m_id)
        if not sel.any():
            continue
        r = TAIL_BRAKE if (m_id == M_TAIL and brake) else ramp
        cols = np.array([hx(c) for c in r], np.uint8)
        lv = level[sel]
        if m_id in EMISSIVE:
            lv = np.full(lv.shape, 3)
        elif m_id == M_TAIL and brake:
            lv = np.full(lv.shape, 2)
        img[sel, :3] = cols[lv]
        img[sel, 3] = 255

    # Konturen: innere Kanten dort, wo ein deutlich naeherer Nachbar vorbeilaeuft
    im = img.reshape(CELL_H, CELL_W, 4)
    dp = depth.reshape(CELL_H, CELL_W)
    sol = solid.reshape(CELL_H, CELL_W)
    lvmap = level.reshape(CELL_H, CELL_W)
    mmap = hit_m.reshape(CELL_H, CELL_W)
    out = im.copy()
    dark = {m: np.array(hx(r[0]), np.uint8) for m, r in RAMPS.items()}
    for y in range(CELL_H):
        for x in range(CELL_W):
            if not sol[y, x]:
                continue
            for dy, dx in ((-1, 0), (0, -1), (1, 0), (0, 1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < CELL_H and 0 <= xx < CELL_W and sol[yy, xx] and dp[yy, xx] < dp[y, x] - 3.0:
                    # Nur an der oberen/linken Kante des Nachbarn, damit die Linien duenn bleiben
                    if mmap[y, x] not in EMISSIVE:
                        out[y, x, :3] = dark[mmap[y, x]]
                    break
    # Aeussere Kontur
    result = out.copy()
    for y in range(CELL_H):
        for x in range(CELL_W):
            if sol[y, x]:
                continue
            for dy, dx in ((-1, 0), (0, -1), (1, 0), (0, 1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < CELL_H and 0 <= xx < CELL_W and sol[yy, xx]:
                    result[y, x, :3] = OUTLINE
                    result[y, x, 3] = 255
                    break

    # Schatten auf dem Boden (nach rechts unten verschoben)
    gxs = u
    gys = vv / sinE
    lx = (gxs - 1.2) * cphi + (gys + 1.0) * sphi
    ly = -(gxs - 1.2) * sphi + (gys + 1.0) * cphi
    inside = (np.abs(lx / 27.0) ** 4 + np.abs(ly / 11.5) ** 4) < 1.0
    inside = inside.reshape(CELL_H, CELL_W) & (result[:, :, 3] == 0)
    result[inside, :3] = SHADOW
    result[inside, 3] = 90
    return result


def render_sheet():
    sheet = Image.new('RGBA', (CELL_W * 8, CELL_H * DIRS), (0, 0, 0, 0))
    body = build_body(False)
    for f in range(FRAMES):
        v = add_wheels(body, f)
        occ = occlusion(v)
        bob = 1 if f in (1, 3) else 0
        for d in range(DIRS):
            for brake in (0, 1):
                arr = render(v, occ, d * 45, brake, bob)
                im = Image.fromarray(arr)
                sheet.paste(im, ((f + (4 if brake else 0)) * CELL_W, d * CELL_H))
        print('Bild', f, 'fertig', flush=True)
    return sheet


def main():
    sheet = render_sheet()
    sheet.save(os.path.join(OUT, 'Auto_Pickup.png'))
    pv = Image.new('RGBA', (CELL_W * 4 * 4, CELL_H * 2 * 4), (46, 58, 46, 255))
    for d in range(DIRS):
        im = sheet.crop((0, d * CELL_H, CELL_W, (d + 1) * CELL_H)).resize((CELL_W * 4, CELL_H * 4), Image.NEAREST)
        pv.paste(im, ((d % 4) * CELL_W * 4, (d // 4) * CELL_H * 4), im)
    pv.save(os.path.join(HERE, 'Auto_Pickup_preview.png'))
    with open(os.path.join(OUT, 'Auto_Pickup.json'), 'w') as f:
        json.dump({'cell': [CELL_W, CELL_H], 'pivot': [PIVOT[0] / CELL_W, 1.0 - PIVOT[1] / CELL_H],
                   'dirs': ['E', 'NE', 'N', 'NW', 'W', 'SW', 'S', 'SE'], 'frames': 8}, f)


if __name__ == '__main__':
    main()
