"""Sprite-Teile von OTIGO (48x48-Zelle): Koepfe als Raster, Jacke mit Kurvenschattierung, Chibi-Proportion. Farben nur aus style_lib.P."""
import math

import style_lib as S

P = S.P
HAIR_D, HAIR_B, HAIR_L = P['outline_dunkel'], P['outline_nacht'], P['erde_dunkel']
SKIN_L, SKIN_M, SKIN_K = P['haut_hell'], P['haut_mittel'], P['haut_schatten']
J_B, J_L, J_D, J_K = P['wald_mittel'], P['gras'], P['wald_dunkel'], P['outline_nacht']
SHIRT = P['wald_dunkel']
JEAN_B, JEAN_L, JEAN_D = P['nachtblau_mittel'], P['nachtblau_hell'], P['nachtblau_dunkel']
BOOT_D, BOOT_B, BOOT_L = P['erde_dunkel'], P['holz_dunkel'], P['holz_mittel']
LEA_D, LEA_B, LEA_L = P['holz_dunkel'], P['holz_mittel'], P['holz_hell']
METAL_L, METAL_M, GLOSS = P['stein_hell'], P['stein_mittel'], P['kerzenweiss']
LIP = P['haut_schatten']
LID = P['outline_dunkel']
EYE_BROWN = P['holz_mittel']

CMAP = {'H': HAIR_B, 'h': HAIR_L, 'D': HAIR_D, 'S': SKIN_L, 'M': SKIN_M, 'K': SKIN_K, 'e': LID, 'b': EYE_BROWN, 'r': LIP}

# Koepfe 18 breit, 17 hoch. Haar: nach hinten gestrichen, Volumen oben, kurze Seiten. Gesicht 10 breit.
# Zeilen 0-5 Haar, 6-7 Stirn, 8 Brauen, 9 frei, 10 Lid, 11 Iris, 12 Nase, 13 Oberlippenbart, 14 Mund, 15 Kinn (Stoppeln), 16 Hals.
HEAD_S = [
    "......hhHHHH......", ".....hhhHHHHHD....", "....hhhHHHHHHHD...", "...hhHHhHHHHHHD...", "...hHhHHHhHHHHD...", "...hHHHHHHHHHHD...",
    "...hHHHHHSSSSHD...", "...hHHSSSSSSSSD...", "...hSDDSSSDDSSD...", "...hSSSSSSSSSSD...", "...hSeeSSSeeSSD...", "...hSbbSSSbbSSD...",
    "...hSSSSMMSSSSD...", "....SSMMMMMMSS....", "....SMMMrrMMMS....", "....SMMMKKMMMS....", "......MKKKKM......"]
HEAD_SW = [
    "......hhHHHH......", ".....hhhHHHHHD....", "....hhhHHHHHHHD...", "...hhHHhHHHHHHD...", "...hHhHHHhHHHHD...", "...hHHHHHHHHHHD...",
    "...hHHHHHSSSHHD...", "...hHHSSSSSSSHD...", "...hSDDSDDSSSHD...", "...hSSSSSSSSMHD...", "...hSeeSeeSSMHD...", "...hSbbSbbSSMHD...",
    "...hSSMSSSSSMHD...", "....SMMMMMSMHH....", "....SMMrrMMMMH....", "....SMMMMKMMHH....", "......MKKKKM......"]
HEAD_B = [
    "......hhHHHH......", ".....hhhHHHHHD....", "....hhhHHHHHHHD...", "...hhHHhHHHHHHD...", "...hHhHHHhHHHHD...", "...hHHHHHHHHHHD...",
    "...hHHHHHHHHHHD...", "...hHHhHHHHHhHD...", "...hHHHHhHHHHHD...", "...hHHHHHHHHHHD...", "...hHHhHHHHhHHD...", "...hHHHHHHHHHHD...",
    "....HHHHHhHHHD....", "....HHHHHHHHHD....", "....SMHHHHHHMS....", "....SMMMMMMMMS....", "......MMKKMM......"]
HEAD_W = [
    "......hhHHHH......", ".....hhhHHHHHD....", "....hhhHHHHHHHD...", "...hhHHhHHHHHHD...", "...hHhHHHhHHHHD...", "...hHHHHHHHHHHD...",
    "...hHHHHHHHHHHD...", "...hHHSSSHHHHHD...", "...hSSSSDDHHHHD...", "...SSSSSMHHHHHD...", "...SSeeSMHHHHHD...", "...SSbbSMHHHHHD...",
    "..SSSSSSMHHHD.....", "..SSSSMMMHHD......", "...SSMrrMMHD......", "...SMMMKMMD.......", "......MKKM........"]
for _t in (HEAD_S, HEAD_SW, HEAD_B, HEAD_W):
    assert len(_t) == 17 and all(len(r) == 18 for r in _t), [(i, len(r)) for i, r in enumerate(_t) if len(r) != 18]


def blink(tpl):
    return [r.replace('ee', 'MM').replace('bb', 'MM') for r in tpl]


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


HW_FRONT = {20: 7.4, 23: 7.6, 28: 7.0, 32: 7.4}
HW_SIDE = {20: 5.0, 24: 5.2, 32: 5.4}
CX_FRONT, CX_SIDE = 23.5, 24.0
Y_TOP, Y_HEM = 20, 32


def jacket(cv, dy, cx, hwt, tx=0):
    for y in range(Y_TOP, Y_HEM + 1):
        yy = y + dy
        hw = interp(hwt, y)
        for x in range(round(cx + tx - hw + 0.5), round(cx + tx + hw - 0.5) + 1):
            nx = (x - (cx + tx)) / hw
            ny = (y - Y_TOP) / 12.0
            t = 0.7 * nx + 0.25 * ny
            c = J_B
            if nx < -0.70:
                c = J_L
            elif t > 0.60:
                c = J_D
            if y == Y_HEM:
                c = J_K if t > 0.1 else J_D
            cv.P(x, yy, c)
        if 24 <= y <= 31 and y % 3 == 0:                             # Falten
            for side in (-1, 1):
                cv.P(round(cx + tx + side * 3.4), yy, J_D)


def belt(cv, tx=0, cx=CX_FRONT, hw=7.4, buckle=True):
    y = 33
    for x in range(round(cx + tx - hw + 0.5), round(cx + tx + hw - 0.5) + 1):
        cv.P(x, y, LEA_B if x % 3 else LEA_L)
    if buckle:
        cv.R(round(cx + tx) - 1, y, round(cx + tx), y, METAL_L)


def arm(cv, x, y, swing, left):
    y += swing
    cv.R(x, y, x + 1, y + 7, J_B)
    cv.R(x if left else x + 1, y, x if left else x + 1, y + 7, J_L if left else J_D)
    cv.R(x, y + 8, x + 1, y + 8, J_D)                                # Bund
    cv.R(x, y + 9, x + 1, y + 10, SKIN_L)
    cv.P(x + (1 if left else 0), y + 10, SKIN_M)
    if left:
        cv.R(x, y + 7, x + 1, y + 7, METAL_L)                        # Armbanduhr
        cv.P(x, y + 7, GLOSS)


def chain(cv, dy, tx=0):
    for dx, dyy in ((-2, 0), (-1, 1), (0, 2), (1, 2), (2, 1), (3, 0)):
        cv.P(22 + tx + dx + 1, 20 + dyy + dy, METAL_L)
    cv.P(23 + tx, 23 + dy, GLOSS)                                    # Anhaenger


def zipper(cv, dy, tx=0):
    for y in range(22, 32):
        cv.P(24 + tx, y + dy, METAL_M if y % 2 else J_K)
    cv.P(24 + tx, 31 + dy, METAL_L)
    cv.R(20 + tx, 20 + dy, 21 + tx, 21 + dy, J_L)                    # Kragen
    cv.R(26 + tx, 20 + dy, 27 + tx, 21 + dy, J_D)
    for sx in (-1, 1):                                               # Taschen
        x0 = 24 + tx + (-6 if sx < 0 else 3)
        cv.R(x0, 28 + dy, x0 + 2, 28 + dy, J_K)
        cv.R(x0, 27 + dy, x0 + 2, 27 + dy, J_L)


def pouch(cv, x, y):
    cv.R(x, y, x + 3, y + 4, LEA_B)
    cv.R(x, y, x, y + 4, LEA_L)
    cv.R(x + 3, y + 1, x + 3, y + 4, LEA_D)
    cv.R(x + 1, y + 4, x + 3, y + 4, LEA_D)
    cv.R(x, y + 1, x + 3, y + 1, LEA_D)
    cv.P(x + 1, y + 2, METAL_L)


def legs_front(cv, lx, rx, lifts, tx=0):
    for x1, lift in ((lx + tx, lifts[0]), (rx + tx, lifts[1])):
        cv.R(x1, 34, x1 + 3, 41 - lift, JEAN_B)
        cv.R(x1, 34, x1, 41 - lift, JEAN_L)
        cv.R(x1 + 3, 34, x1 + 3, 41 - lift, JEAN_D)
        cv.R(x1 + 1, 38 - lift, x1 + 2, 38 - lift, JEAN_D)           # Kniefalte
        cv.R(x1, 41 - lift, x1 + 3, 41 - lift, JEAN_D)               # Aufschlag
        cv.R(x1, 42 - lift, x1 + 3, 43 - lift, BOOT_B)
        cv.R(x1, 42 - lift, x1, 43 - lift, BOOT_L)
        cv.R(x1 - 1, 44 - lift, x1 + 3, 44 - lift, BOOT_B)
        cv.R(x1 - 1, 44 - lift, x1 - 1, 44 - lift, BOOT_L)
        cv.R(x1 - 1, 45 - lift, x1 + 3, 45 - lift, BOOT_D)


def leg_side(cv, ax, ay, dark):
    jb, jd = (JEAN_D, JEAN_D) if dark else (JEAN_B, JEAN_D)
    bb, bd, bl = (BOOT_D, BOOT_D, BOOT_B) if dark else (BOOT_B, BOOT_D, BOOT_L)
    top = 34
    for y in range(top, ay - 3):
        xc = round(24 + (ax - 24) * (y - top) / max(ay - 3 - top, 1))
        cv.R(xc - 1, y, xc + 1, y, jb)
        cv.P(xc + 1, y, jd)
    cv.R(ax - 1, ay - 4, ax + 2, ay - 3, bb)
    cv.R(ax - 3, ay - 2, ax + 2, ay - 1, bb)
    cv.R(ax - 3, ay - 2, ax - 3, ay - 1, bl)
    cv.R(ax - 3, ay, ax + 2, ay, bd)
