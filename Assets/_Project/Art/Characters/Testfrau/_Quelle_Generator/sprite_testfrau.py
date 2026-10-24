"""Sprite-Teile der Testfrau (48x48-Zelle): von Hand gezeichnete Koepfe (Raster), Mantel mit Rundungen und Kurvenschattierung,
kurze Beine (chibi, wie Mara/Sheriff). Farben nur aus style_lib.P."""
import math

import style_lib as S

P = S.P
HAIR_D, HAIR_B, HAIR_L, HAIR_A = P['erde_dunkel'], P['holz_dunkel'], P['holz_mittel'], P['stroh_sand']
SKIN_L, SKIN_M, SKIN_D = P['haut_hell'], P['haut_mittel'], P['haut_schatten']
C_B, C_L, C_D, C_K = P['stoff_blau_gedaempft'], P['stoff_blau_hell'], P['nachtblau_mittel'], P['nachtblau_dunkel']
SC_L, SC_D = P['akzent_rose'], P['stoff_rot_gedaempft']
LEA_D, LEA_B, LEA_L = P['holz_dunkel'], P['holz_mittel'], P['holz_hell']
PANT_B, PANT_D, PANT_L = P['holz_hell'], P['holz_mittel'], P['stroh_sand']
BOOT_D, BOOT_B, BOOT_L = P['erde_dunkel'], P['holz_dunkel'], P['holz_mittel']
BTN, ORANGE, WHITE, EYE = P['licht_warmgelb'], P['laterne_orange'], P['zaehne_grinsen'], P['outline_dunkel']

CMAP = {'b': P['stoff_blau_hell'], 'H': HAIR_B, 'h': HAIR_L, 'D': HAIR_D, 'S': SKIN_L, 'M': SKIN_M, 'K': SKIN_D, 'e': EYE, 'i': HAIR_B, 'r': SC_L, 'w': WHITE}

# ---- Koepfe (18 breit, 18 hoch): Haarkappe mit Seitenscheitel, Gesicht 10 breit, Seitenhaar endet am Kiefer mit kleiner Locke.
# Legende: H/h/D Haar Basis/Licht/Schatten, S/M/K Haut hell/mittel/tief, e Lidstrich, b blaue Iris, r Lippen
# (Zeilen 0-5 Kappe, 6-14 Gesicht, 15 Kiefer/Locke; 16 Zeilen) Kopf = Gesicht 10 + 1 Pixel Haar je Seite
HEAD_S = [
    "......hhHHHH......",
    ".....hhhHHHHHD....",
    "....hhhHHHHHHHD...",
    "...hhHHHHHHHHHD...",
    "...hHHHDHHHHHHD...",
    "...hHHHDDHHHHHD...",
    "...hSSSSSSHHHHD...",
    "...hSSSSSSSHHHD...",
    "...hSSSSSSSSHHD...",
    "...hSSSSSSSSSHD...",
    "...hSeeSSSeeSSD...",
    "...hSbbSSSbbSSD...",
    "...hSSSSMMSSSSD...",
    "...hSSSSrrSSSSD...",
    "...hHMSSSSSSMHD...",
    "...hhHHMKKMHHhh..."]
HEAD_SW = [
    "......hhHHHH......",
    ".....hhhHHHHHD....",
    "....hhhHHHHHHHD...",
    "...hhHHHHHHHHHD...",
    "...hHHHDHHHHHHD...",
    "...hHHHDDHHHHHD...",
    "...hSSSSSHHHHHD...",
    "...hSSSSSSHHHHD...",
    "...hSSSSSSSHHHD...",
    "...hSSSSSSSMHHD...",
    "...hSeeSeeSMHHD...",
    "...hSbbSbbSMHHD...",
    "...hSSMSSSSMHHD...",
    "...hSSrrSSSMHHD...",
    "...hHMSSSSMMHHD...",
    "...hhHHMKMHHHhh..."]
HEAD_B = [
    "......hhHHHH......",
    ".....hhhHHHHHD....",
    "....hhhHHHHHHHD...",
    "...hhHHHHHHHHHD...",
    "...hHHHDHHHHHHD...",
    "...hHHHDDHHHHHD...",
    "...hHHHHHDDHHHD...",
    "...hHHHHHHHDHHD...",
    "...hHHDHHHHDHHD...",
    "...hHHHHHHHHDHD...",
    "...hHDHHHHHHHDD...",
    "...hHHHHDHHHHHD...",
    "...hHHHHHHDHHHD...",
    "...hHHHHHHHHHDD...",
    "...hHHHHHHHHHHD...",
    "..hhHHHHhhHHHHhh.."]
HEAD_W = [
    "......hhHHHH......",
    ".....hhhHHHHHD....",
    "....hhhHHHHHHHD...",
    "...hhHHHHHHHHHD...",
    "...hHHHDHHHHHHD...",
    "...hHHHDDHHHHHD...",
    "...hSSSSHHHHHHD...",
    "...SSSSSMHHHHHD...",
    "...SSSSSMHHHHHD...",
    "...SSSSSMHHHHHD...",
    "...SSeeSMHHHHHD...",
    "...SSbbSMHHHHHD...",
    "..SSSSSSMHHHHHD...",
    "..SSSSSSMHHHHHD...",
    "...SSrrSMHHHHHD...",
    "...hSMMMMHHHHhh..."]
for _t in (HEAD_S, HEAD_SW, HEAD_B, HEAD_W):
    assert len(_t) == 16 and all(len(r) == 18 for r in _t), [(i, len(r)) for i, r in enumerate(_t) if len(r) != 18]


def _blink(tpl):
    out = []
    for r in tpl:
        r = r.replace('ee', 'MM').replace('ei', 'MM').replace('ie', 'MM').replace('bb', 'MM')
        out.append(r)
    return out


def blit(cv, tpl, x0, y0):
    for j, row in enumerate(tpl):
        for i, ch in enumerate(row):
            if ch != '.':
                cv.P(x0 + i, y0 + j, CMAP[ch])


def interp(table, y):
    ys = sorted(table)
    if y <= ys[0]:
        return table[ys[0]]
    if y >= ys[-1]:
        return table[ys[-1]]
    for a, b in zip(ys, ys[1:]):
        if a <= y <= b:
            return table[a] + (table[b] - table[a]) * (y - a) / (b - a)


# ---- Mantel (Halbbreite je Zeile): Schultern -> Taille -> ausgestellter Saum
HW_FRONT = {20: 6.6, 23: 7.0, 27: 6.0, 29: 5.6, 32: 6.8, 35: 8.0, 37: 8.6}
HW_SIDE = {20: 4.6, 24: 4.8, 29: 4.4, 32: 5.4, 35: 6.4, 37: 7.0}
CX_FRONT, CX_SIDE = 23.5, 24.0
Y_TOP, Y_HEM = 20, 37


def coat(cv, dy, cx, hwt, sway=0.0, tx=0):
    for y in range(Y_TOP, Y_HEM + 1):
        dyy = dy if y < 30 else 0                                    # Saum bewegt sich nicht mit dem Atmen
        yy = y + dyy
        hw = interp(hwt, y)
        off = sway * max(0.0, (y - 31) / 6.0) + tx
        for x in range(round(cx + off - hw + 0.5), round(cx + off + hw - 0.5) + 1):
            nx = (x - (cx + off)) / hw
            ny = (y - Y_TOP) / 17.0
            t = 0.7 * nx + 0.25 * ny
            c = C_B
            if nx < -0.70:
                c = C_L
            elif t > 0.62:
                c = C_D
            if y >= Y_HEM - 1:
                c = C_K if t > 0.1 else C_D
            cv.P(x, yy, c)
        # Falten im Rockteil: zwei Rillen mit Licht daneben
        if 31 <= y <= 36:
            for side in (-1, 1):
                gx = round(cx + off + side * (2.6 + (y - 31) * 0.35))
                cv.P(gx, yy, C_D)
                cv.P(gx - 1, yy, C_L) if (y % 2 == 0 and side == -1) else None


def belt(cv, dy, cx, hwt, tx=0, buckle=True):
    y = 28 + dy
    hw = interp(hwt, 28)
    for x in range(round(cx + tx - hw + 0.5), round(cx + tx + hw - 0.5) + 1):
        cv.P(x, y, LEA_B if (x + 1) % 3 else LEA_L)
        cv.P(x, y + 1, LEA_D)
    if buckle:
        cv.R(round(cx + tx) - 1, y, round(cx + tx), y, BTN)
        cv.P(round(cx + tx) - 1, y + 1, ORANGE)


def scarf(cv, dy, tx=0, side=False):
    if side:
        cv.R(20, 20 + dy, 27, 20 + dy, SC_L)
        cv.R(20, 21 + dy, 27, 21 + dy, SC_D)
        for dx in (22, 25):
            cv.P(dx, 21 + dy, WHITE)
        cv.R(27, 21 + dy, 29, 28 + dy, SC_L)
        cv.R(29, 22 + dy, 29, 28 + dy, SC_D)
        cv.P(28, 29 + dy, SC_D)
        cv.P(27, 24 + dy, WHITE)
        return
    cv.R(20 + tx, 20 + dy, 27 + tx, 20 + dy, SC_L)
    cv.R(20 + tx, 21 + dy, 27 + tx, 21 + dy, SC_D)
    for dx in (21, 24, 27):
        cv.P(dx + tx, 20 + dy, WHITE)
    cv.R(26 + tx, 21 + dy, 27 + tx, 22 + dy, SC_L)
    cv.R(26 + tx, 23 + dy, 26 + tx, 29 + dy, SC_L)
    cv.R(27 + tx, 23 + dy, 27 + tx, 29 + dy, SC_D)
    cv.P(26 + tx, 30 + dy, SC_D)
    cv.P(26 + tx, 26 + dy, WHITE)


def hair_tips(cv, dy, tx=0, back=False):
    for side, xs in ((-1, (16, 17)), (1, (30, 31))):
        for k, y in enumerate(range(20, 25 if not back else 27)):
            x0 = xs[0] + tx + (1 if (side == -1 and k > 3) else 0) - (1 if (side == 1 and k > 3) else 0)
            cv.P(x0, y + dy, HAIR_L if side == -1 else HAIR_B)
            cv.P(x0 + 1, y + dy, HAIR_B if side == -1 else HAIR_D)
        cv.P(xs[0] + tx + (0 if side == -1 else 1), 22 + dy, HAIR_A)


def arm(cv, x, y, swing, left):
    y += swing
    cv.R(x, y, x + 1, y + 6, C_B)
    cv.R(x if left else x + 1, y, x if left else x + 1, y + 6, C_L if left else C_D)
    cv.R(x, y + 7, x + 1, y + 7, C_L)                                # Manschette
    cv.R(x, y + 8, x + 1, y + 9, SKIN_L)
    cv.P(x + (1 if left else 0), y + 9, SKIN_M)


def strap(cv, x0, y0, x1, y1):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
        cv.P(x, y, LEA_L if i % 3 == 0 else LEA_B)


def bag(cv, x1, y1, sway=0):
    x1 += sway
    cv.R(x1, y1, x1 + 4, y1 + 7, LEA_B)
    cv.R(x1, y1, x1, y1 + 7, LEA_L)
    cv.R(x1 + 4, y1 + 1, x1 + 4, y1 + 7, LEA_D)
    cv.R(x1 + 1, y1 + 7, x1 + 4, y1 + 7, LEA_D)
    cv.R(x1, y1 + 2, x1 + 4, y1 + 2, LEA_D)                          # Klappenkante
    cv.P(x1 + 2, y1 + 3, BTN)                                        # Schnalle
    cv.P(x1 + 1, y1 + 5, LEA_L)
    cv.P(x1 + 3, y1 + 6, LEA_L)


# ---- Beine: kurz, dunkle Stiefel mit Schnalle
def legs_front(cv, lx, rx, lifts, tx=0):
    for x1, lift in ((lx + tx, lifts[0]), (rx + tx, lifts[1])):
        cv.R(x1 + 1, 38, x1 + 3, 40 - lift, PANT_B)
        cv.R(x1 + 1, 38, x1 + 1, 40 - lift, PANT_L)
        cv.R(x1 + 3, 38, x1 + 3, 40 - lift, PANT_D)
        cv.R(x1, 41 - lift, x1 + 3, 42 - lift, BOOT_B)               # Schaft
        cv.R(x1, 41 - lift, x1, 42 - lift, BOOT_L)
        cv.R(x1 + 3, 41 - lift, x1 + 3, 42 - lift, BOOT_D)
        cv.P(x1 + 1, 41 - lift, BTN)
        cv.R(x1 - 1, 43 - lift, x1 + 3, 44 - lift, BOOT_B)           # Fuss
        cv.R(x1 - 1, 43 - lift, x1 - 1, 44 - lift, BOOT_L)
        cv.R(x1 - 1, 45 - lift, x1 + 3, 45 - lift, BOOT_D)           # Sohle


def leg_side(cv, ax, ay, dark):
    pb, pd = (PANT_D, PANT_D) if dark else (PANT_B, PANT_D)
    bb, bd, bl = (BOOT_D, BOOT_D, BOOT_B) if dark else (BOOT_B, BOOT_D, BOOT_L)
    top = 38
    for y in range(top, ay - 3):
        xc = round(24 + (ax - 24) * (y - top) / max(ay - 3 - top, 1))
        cv.R(xc - 1, y, xc + 1, y, pb)
        cv.P(xc + 1, y, pd)
    cv.R(ax - 1, ay - 4, ax + 2, ay - 3, bb)
    cv.R(ax - 1, ay - 4, ax - 1, ay - 3, bl)
    cv.R(ax - 3, ay - 2, ax + 2, ay - 1, bb)
    cv.R(ax - 3, ay - 2, ax - 3, ay - 1, bl)
    cv.R(ax - 3, ay, ax + 2, ay, bd)
    if not dark:
        cv.P(ax, ay - 4, BTN)
