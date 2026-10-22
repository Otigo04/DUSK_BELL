"""Ilhans Bar - AUSSEN. Erzeugt Tileset_Bar_Aussen.png + Bar_Aussen_Vorschau.png."""
from bar_lib import *

PRICE_L = ['BEER', 'MEAD', 'WINE', 'SCHNAPPS']
PRICE_R = ['WHISKY', 'RUM', 'BOURBON', 'HOT STEW']


# ============================================================ DACH
def roof_first(side=None):
    s = Spr(32, 32)
    shingles(s, 0, 8, 31, 31)
    # Firstkappe
    s.rect(0, 0, 31, 0, OL1)
    s.rect(0, 1, 31, 2, WOOD_L)
    s.rect(0, 3, 31, 5, WOOD_M)
    s.rect(0, 6, 31, 6, WOOD_D)
    s.rect(0, 7, 31, 7, EARTH)
    for x in range(2, 32, 8):
        s.set(x, 4, WOOD_D)
    if side:
        barge(s, side, 0, 31)
    return s


def roof_area(side=None):
    s = Spr(32, 32)
    shingles(s, 0, 0, 31, 31)
    if side:
        barge(s, side, 0, 31)
    return s


def roof_eave(side=None):
    s = Spr(32, 32)
    shingles(s, 0, 0, 31, 15)
    s.rect(0, 16, 31, 16, WOOD_L)
    s.rect(0, 17, 31, 21, WOOD_M)
    s.rect(0, 22, 31, 22, WOOD_D)
    s.rect(0, 23, 31, 23, OL1)
    for x in range(3, 32, 8):
        s.set(x, 19, WOOD_D)
    # Schatten auf der Wand darunter
    planks(s, 0, 24, 31, 31)
    for y in range(24, 32):
        for x in range(32):
            s.set(x, y, darken(s.get(x, y)))
    if side:
        barge(s, side, 0, 31)
    return s


def chimney(smoke=False):
    s = Spr(32, 64)
    # Schaft
    for y in range(24, 64):
        course, cy = divmod(y - 24, 6)
        for x in range(8, 24):
            xo = (x - 8 + (course % 2) * 4) % 8
            c = ST_M
            if cy == 0:
                c = ST_L
            elif cy == 5:
                c = ST_D
            if xo == 0:
                c = ST_D
            if x == 8:
                c = OL1
            if x == 23:
                c = OL1
            if x in (9, 10) and cy not in (0, 5):
                c = ST_L if x == 9 else ST_M
            if x >= 21 and x < 23:
                c = ST_D
            s.set(x, y, c)
    # Kappe
    s.rect(6, 17, 25, 17, OL1)
    s.rect(6, 18, 25, 18, ST_L)
    s.rect(6, 19, 25, 22, ST_M)
    s.rect(6, 23, 25, 23, OL1)
    s.rect(6, 18, 6, 22, OL1)
    s.rect(25, 18, 25, 22, OL1)
    s.rect(9, 14, 22, 16, OL1)
    s.rect(10, 15, 21, 15, ST_D)
    if smoke:
        for i, (x, y, c) in enumerate([(14, 12, ST_L), (15, 11, MOON), (16, 9, ST_L), (15, 7, MOON), (17, 6, ST_L),
                                       (16, 4, MOON), (18, 3, ST_L), (17, 1, MOON), (14, 9, MOON), (19, 5, ST_L)]):
            s.set(x, y, c)
            s.set(x + 1, y, c)
    return s


def dormer(lit):
    s = Spr(32, 32)
    shingles(s, 0, 0, 31, 31)
    rect_o(s, 6, 4, 25, 27, WOOD_M)
    s.rect(7, 5, 24, 5, WOOD_L)
    gl = [YEL, YEL, ORA, ORA] if lit else [NB_L, NB_M, NB_M, NB_D]
    for i, y0 in enumerate((8, 17)):
        for j, x0 in enumerate((9, 17)):
            col = gl[i * 2 + j] if lit else gl[i * 2 + j]
            s.rect(x0, y0, x0 + 6, y0 + 7, OL1)
            s.rect(x0 + 1, y0 + 1, x0 + 5, y0 + 6, col)
            s.set(x0 + 1, y0 + 1, CREAM if lit else NB_L)
            s.set(x0 + 2, y0 + 1, CREAM if lit else MOON)
    s.rect(6, 25, 25, 27, WOOD_L)
    s.rect(6, 27, 25, 27, OL1)
    return s


# ============================================================ FASSADE (32x64 = oben+unten)
def facade(side=None, sockel=True):
    s = Spr(32, 64)
    planks(s, 0, 0, 31, 63)
    if sockel:
        stone_base(s, 0, 54, 31, 63)
        s.rect(0, 53, 31, 53, OL1)
    if side:
        # Eckpfosten
        xs = range(0, 6) if side == 'L' else range(31, 25, -1)
        cols = [OL1, WOOD_L, WOOD_M, WOOD_M, WOOD_D, OL1]
        for i, x in enumerate(xs):
            for y in range(0, 54):
                s.set(x, y, cols[i])
        if side == 'L':
            s.rect(0, 54, 1, 63, OL1)
        else:
            s.rect(30, 54, 31, 63, OL1)
    return s


def window(kind):
    """kind: 'lit', 'dark', 'shut'. Rot-gestrichene Läden (Ilhans Farbe)."""
    s = facade(None)
    # Fensterrahmen
    rect_o(s, 6, 9, 25, 47, WOOD_L)
    s.rect(7, 10, 24, 10, SAND)
    if kind == 'shut':
        for x0, x1 in ((7, 15), (16, 24)):
            s.rect(x0, 11, x1, 44, RED_D)
            for y in range(11, 45):
                for x in range(x0, x1 + 1):
                    u = (x - x0)
                    if u == 0:
                        s.set(x, y, OL1)
                    elif u == 1:
                        s.set(x, y, ROSE)
                    elif u == 8 or u == 7:
                        s.set(x, y, SV_D)
            for y in (18, 26, 34):  # Licht in den Ritzen
                s.rect(8, y, 14, y, YEL)
                s.rect(17, y, 23, y, YEL)
            s.rect(15, 11, 16, 44, OL1)
    else:
        glass = (YEL, ORA) if kind == 'lit' else (NB_L, NB_D)
        for (x0, x1) in ((8, 15), (16, 23)):
            for y in range(12, 43):
                top = y < 24
                c = glass[0] if top else glass[1]
                if kind == 'dark':
                    c = NB_M if y < 30 else NB_D
                s.set(x0, y, OL1) if False else None
                for x in range(x0, x1 + 1):
                    s.set(x, y, c)
            if kind == 'lit':
                # Lichtverlauf + Glanz
                for x in range(x0, x1 + 1):
                    s.set(x, 24, ORA if (x + 1) % 2 else YEL)
                s.set(x0 + 1, 13, CREAM); s.set(x0 + 2, 13, CREAM); s.set(x0 + 1, 14, CREAM)
                s.set(x0 + 1, 28, YEL); s.set(x0 + 2, 28, YEL)
            else:
                s.set(x0 + 1, 13, NB_L); s.set(x0 + 2, 14, MOON); s.set(x0 + 1, 14, NB_L)
                s.set(x0 + 2, 13, MOON)
        # Kreuz
        s.rect(15, 11, 16, 43, WOOD_D)
        s.rect(8, 26, 23, 27, WOOD_D)
        s.rect(8, 25, 23, 25, WOOD_M)
        # Silhouette Gast am Tresen (nur beleuchtet)
        if kind == 'lit':
            ell_o(s, 19, 36, 2.2, 2.6, SV_D, SV_D)
            s.rect(16, 38, 22, 42, SV_D)
    if kind != 'shut':
        for x0, x1 in ((0, 4), (27, 31)):
            s.rect(x0, 11, x1, 46, RED_D)
            for y in range(11, 47):
                for x in range(x0, x1 + 1):
                    u = x - x0
                    if u == 0 or u == 4:
                        s.set(x, y, OL1 if (x0 == 0 and u == 4) or (x0 == 27 and u == 0) else RED_D)
                if y % 3 == 0:
                    s.rect(x0, y, x1, y, ROSE)
                elif y % 3 == 2:
                    s.rect(x0, y, x1, y, SV_D)
            s.rect(x0, 11, x1, 11, OL1)
            s.rect(x0, 46, x1, 46, OL1)
    # Fensterbank
    s.rect(4, 47, 27, 50, WOOD_L)
    s.rect(4, 50, 27, 50, OL1)
    s.rect(4, 47, 27, 47, SAND)
    s.rect(5, 51, 26, 52, darken(WOOD_M))
    return s


def saloon_door(state):
    """64x64. state: 'zu', 'schwingt', 'offen'."""
    s = Spr(64, 64)
    planks(s, 0, 0, 63, 63)
    stone_base(s, 0, 54, 63, 63)
    s.rect(0, 53, 63, 53, OL1)
    # Rahmen
    s.rect(3, 4, 60, 63, OL1)
    s.rect(4, 5, 59, 63, WOOD_D)
    s.rect(4, 5, 59, 6, WOOD_L)
    s.rect(4, 7, 59, 8, WOOD_M)
    s.rect(4, 9, 59, 9, OL1)
    s.rect(4, 9, 6, 63, WOOD_L)
    s.rect(57, 9, 59, 63, WOOD_D)
    s.rect(4, 9, 4, 63, OL1)
    s.rect(59, 9, 59, 63, OL1)
    # Innenraum (warmes Licht)
    ix0, ix1, iy0, iy1 = 7, 56, 10, 63
    for y in range(iy0, iy1 + 1):
        for x in range(ix0, ix1 + 1):
            t = (y - iy0) / (iy1 - iy0)
            c = OL2 if t < 0.35 else (SV_D if t < 0.62 else SV_M)
            if t > 0.8 and (x + y) % 2 == 0:
                c = WOOD_D
            s.set(x, y, c)
    # Lichtinseln im Raum
    for x0 in (14, 40):
        s.rect(x0, 16, x0 + 2, 17, YEL)
        s.set(x0 + 1, 15, ORA); s.set(x0 + 1, 18, ORA)
    # Boden / Schwelle
    s.rect(ix0, 58, ix1, 60, WOOD_M)
    s.rect(ix0, 61, ix1, 63, WOOD_L)
    s.rect(ix0, 61, ix1, 61, SAND)
    if state == 'offen':
        # Lichtkegel auf die Schwelle
        for y in range(40, 58):
            for x in range(ix0 + 8, ix1 - 8):
                if (x + y) % 3 == 0:
                    s.set(x, y, ORA if y > 50 else SV_M)
        return s

    def leaf(x0, x1, tilt=0):
        for y in range(27, 54):
            for x in range(x0, x1 + 1):
                u, v = x - x0, y - 27
                c = WOOD_M if (v // 4) % 2 == 0 else WOOD_D
                if v % 4 == 0:
                    c = WOOD_L
                if u == 0 or x == x1:
                    c = OL1
                s.set(x, y, c)
        s.rect(x0, 27, x1, 27, OL1)
        s.rect(x0, 53, x1, 53, OL1)
        s.rect(x0 + 1, 28, x1 - 1, 29, WOOD_L)
    if state == 'zu':
        leaf(7, 31)
        leaf(32, 56)
    else:
        leaf(7, 24)
        leaf(39, 56)
        s.rect(25, 30, 38, 52, OL2)
        for y in range(30, 53):
            s.set(31, y, YEL) if y % 2 == 0 else None
            s.set(32, y, ORA) if y % 2 == 0 else None
    # Scharniere
    for y in (30, 50):
        s.rect(5, y, 7, y + 1, ST_L)
        s.rect(56, y, 58, y + 1, ST_L)
    return s


def back_door():
    s = facade(None)
    rect_o(s, 5, 8, 26, 63, WOOD_L)
    planks(s, 7, 10, 24, 63, base=WOOD_M, lite=WOOD_L, dark=WOOD_D, seam=EARTH, vertical=True, seed=8)
    for y0 in (16, 46):
        s.rect(7, y0, 24, y0 + 2, ST_M)
        s.rect(7, y0, 24, y0, ST_L)
        s.rect(7, y0 + 2, 24, y0 + 2, ST_D)
    for y in range(12, 63):  # Diagonalstrebe
        pass
    s.line(8, 44, 23, 20, EARTH)
    s.line(8, 45, 23, 21, WOOD_D)
    s.rect(21, 36, 22, 39, YEL)
    s.rect(21, 40, 22, 40, ORA)
    s.rect(5, 61, 26, 63, WOOD_L)
    return s


# ============================================================ SCHILDER
def sign_main():
    s = Spr(128, 32)
    rect_o(s, 0, 2, 127, 29, WOOD_D)
    s.rect(1, 3, 126, 4, WOOD_L)
    s.rect(1, 5, 126, 5, WOOD_M)
    s.rect(1, 27, 126, 28, EARTH)
    # Innenfläche dunkelrot (Ilhans Farbe)
    s.rect(4, 7, 123, 24, OL1)
    s.rect(5, 8, 122, 23, RED_D)
    s.rect(5, 8, 122, 8, ROSE)
    s.rect(5, 23, 122, 23, SV_D)
    w = text_width('ILHANS BAR', '5x7', 2, 1)
    draw_text(s, 'ILHANS BAR', (128 - w) // 2, 9, CREAM, '5x7', 2, 1, shadow=OL1)
    for x in (8, 119):
        s.set(x, 11, ST_L); s.set(x, 20, ST_L)
    # Ketten-Ösen
    for x in (14, 113):
        s.rect(x, 0, x + 1, 2, ST_M)
    return s


def sign_bar():
    s = Spr(64, 32)
    rect_o(s, 0, 4, 63, 27, WOOD_D)
    s.rect(1, 5, 62, 6, WOOD_L)
    s.rect(3, 9, 60, 23, OL1)
    s.rect(4, 10, 59, 22, RED_D)
    s.rect(4, 10, 59, 10, ROSE)
    w = text_width('BAR', '5x7', 2, 1)
    draw_text(s, 'BAR', (64 - w) // 2, 12, CREAM, '5x7', 2, 1, shadow=OL1)
    return s


def price_board():
    s = Spr(96, 32)
    rect_o(s, 0, 1, 95, 30, WOOD_L)
    s.rect(2, 3, 93, 28, OL1)
    s.rect(3, 4, 92, 27, FOR_D)
    for i, t in enumerate(PRICE_L):
        draw_text(s, t, 6, 5 + i * 6, CREAM, '3x5', 1, 1)
    for i, t in enumerate(PRICE_R):
        draw_text(s, t, 52, 5 + i * 6, CREAM, '3x5', 1, 1)
    for x in range(48, 50):
        for y in range(5, 26):
            if y % 2 == 0:
                s.set(x, y, FOR_M)
    return s


def sign_ground():
    """Schild ILHANS BAR auf zwei kurzen Pfosten (128x32), fuer den Platz vor der Bar."""
    s = Spr(128, 32)
    for x in (14, 110):
        s.rect(x, 24, x + 3, 31, OL1)
        s.rect(x + 1, 24, x + 2, 31, WOOD_M)
    rect_o(s, 0, 0, 127, 25, WOOD_D)
    s.rect(1, 1, 126, 2, WOOD_L)
    s.rect(4, 4, 123, 22, OL1)
    s.rect(5, 5, 122, 21, RED_D)
    s.rect(5, 5, 122, 5, ROSE)
    w = text_width('ILHANS BAR', '5x7', 2, 1)
    draw_text(s, 'ILHANS BAR', (128 - w) // 2, 6, CREAM, '5x7', 2, 1, shadow=OL1)
    return s


def awning(side=None):
    """Markise rot-weiß, 32x32 (unten transparent)."""
    s = Spr(32, 32)
    for y in range(0, 24):
        for x in range(32):
            band = (x // 8) % 2 == 0
            c = RED_D if band else CREAM
            if y < 3:
                c = (SV_D if band else MOON)
            elif y == 3:
                c = OL1
            if y > 18:  # Volant mit Zacken
                edge = 23 - (3 if (x % 8) in (3, 4) else (2 if (x % 8) in (2, 5) else (1 if (x % 8) in (1, 6) else 0)))
                if y > edge:
                    continue
                if y == edge:
                    c = OL1
            if y == 18:
                c = SV_D if band else ST_L
            s.set(x, y, c)
    if side == 'L':
        s.rect(0, 0, 1, 22, OL1)
    if side == 'R':
        s.rect(30, 0, 31, 22, OL1)
    return s


def hang_sign(icon):
    s = Spr(32, 64)
    # Wandhalterung + Arm
    s.rect(0, 0, 2, 20, ST_D)
    s.rect(0, 0, 0, 20, OL1)
    s.rect(2, 3, 30, 4, OL1)
    s.rect(2, 3, 30, 3, ST_M)
    s.rect(2, 4, 30, 4, ST_D)
    s.rect(2, 4, 4, 12, ST_D)  # Stütze
    s.line(3, 12, 11, 4, ST_D)
    s.set(30, 5, ST_M); s.set(30, 6, ST_L)
    # Ketten
    for x in (9, 26):
        for y in range(5, 14, 2):
            s.set(x, y, ST_L); s.set(x, y + 1, ST_D)
    # Schild
    rect_o(s, 5, 13, 30, 46, WOOD_M)
    s.rect(6, 14, 29, 15, WOOD_L)
    s.rect(7, 17, 28, 44, OL1)
    s.rect(8, 18, 27, 43, RED_D if icon != 'glas' else BLUE_D)
    s.rect(8, 18, 27, 18, ROSE if icon != 'glas' else BLUE_L)
    s.rect(5, 45, 30, 46, EARTH)
    if icon == 'krug':
        # Bierkrug
        s.rect(11, 23, 21, 38, OL1)
        s.rect(12, 24, 20, 37, YEL)
        s.rect(19, 24, 20, 37, ORA)
        s.rect(12, 30, 13, 36, CREAM) if False else None
        s.rect(11, 20, 22, 25, OL1)
        s.rect(12, 21, 21, 24, CREAM)
        s.rect(14, 19, 17, 20, CREAM)
        ell_o(s, 24, 30, 2.3, 4, ST_L, OL1)
        s.rect(23, 28, 24, 32, RED_D)
        s.rect(13, 27, 13, 35, CREAM)
    else:
        # Glas + Flasche
        s.rect(10, 28, 18, 39, OL1)
        s.rect(11, 29, 17, 38, MOON)
        s.rect(11, 31, 17, 38, ORA)
        s.rect(11, 31, 17, 31, YEL)
        s.rect(21, 22, 25, 39, OL1)
        s.rect(22, 25, 24, 38, ORA)
        s.rect(23, 20, 24, 24, OL1)
        s.rect(23, 21, 23, 23, CREAM)
        s.rect(22, 30, 24, 34, CREAM)
    return s


def chalk_sandwich():
    s = Spr(32, 64)
    # Beine (A-Form)
    s.line(5, 62, 9, 12, OL1); s.line(6, 62, 10, 12, WOOD_M)
    s.line(26, 62, 22, 12, OL1); s.line(25, 62, 21, 12, WOOD_M)
    rect_o(s, 4, 10, 27, 52, WOOD_L)
    s.rect(6, 12, 25, 50, OL1)
    s.rect(7, 13, 24, 49, FOR_D)
    for x in range(7, 25):
        if x % 3 == 0:
            s.set(x, 14, FOR_M)
    draw_text(s, 'TODAY', 6 + (20 - text_width('TODAY', '3x5', 1, 1)) // 2, 16, YEL, '3x5', 1, 1)
    s.rect(8, 23, 23, 23, ST_L)
    for i, t in enumerate(['BEER', 'WINE', 'STEW']):
        draw_text(s, t, 7 + (18 - text_width(t, '3x5', 1, 1)) // 2, 26 + i * 7, CREAM, '3x5', 1, 1)
    s.rect(7, 47, 24, 48, FOR_M)
    s.rect(4, 51, 27, 52, WOOD_D)
    return s


def plaque(txt, bg, fg):
    s = Spr(32, 32)
    s.line(16, 0, 16, 5, OL1)
    rect_o(s, 1, 6, 30, 25, bg)
    s.rect(2, 7, 29, 7, CREAM if bg != CREAM else MOON)
    w = text_width(txt, '3x5', 1, 1)
    draw_text(s, txt, 1 + (30 - w) // 2, 13, fg, '3x5', 1, 1)
    s.set(3, 9, ST_L); s.set(28, 9, ST_L); s.set(3, 23, ST_L); s.set(28, 23, ST_L)
    return s


def lantern(kind):
    s = Spr(32, 32)
    if kind == 'wand':
        s.rect(0, 6, 8, 7, ST_D); s.rect(0, 5, 8, 5, OL1); s.rect(0, 8, 8, 8, OL1)
        s.line(2, 8, 8, 13, ST_D)
        cx = 15
        top = 8
    else:
        s.rect(15, 0, 16, 5, ST_D); s.rect(14, 0, 14, 5, OL1); s.rect(17, 0, 17, 5, OL1)
        cx = 15
        top = 5
    s.rect(cx - 5, top + 4, cx + 6, top + 4, OL1)
    s.rect(cx - 4, top + 3, cx + 5, top + 3, ST_D)
    s.rect(cx - 3, top + 1, cx + 4, top + 2, ST_M)
    s.rect(cx - 6, top + 5, cx + 7, top + 5, ST_D)
    s.rect(cx - 6, top + 5, cx - 6, top + 21, OL1)
    s.rect(cx + 7, top + 5, cx + 7, top + 21, OL1)
    for y in range(top + 6, top + 20):
        for x in range(cx - 5, cx + 7):
            t = (y - top - 6) / 14
            s.set(x, y, YEL if t < 0.45 else ORA)
    s.rect(cx - 1, top + 8, cx, top + 16, GLOW)
    s.rect(cx - 1, top + 8, cx - 1, top + 11, CREAM)
    s.rect(cx - 5, top + 6, cx - 4, top + 8, CREAM)
    s.rect(cx + 3, top + 6, cx + 3, top + 19, ST_D)
    s.rect(cx - 6, top + 20, cx + 7, top + 21, ST_D)
    s.rect(cx - 5, top + 22, cx + 6, top + 22, OL1)
    return s


def lamp_post():
    s = Spr(32, 64)
    s.rect(14, 22, 17, 62, OL1)
    s.rect(15, 22, 16, 62, WOOD_M)
    s.rect(15, 22, 15, 62, WOOD_L)
    s.rect(12, 58, 19, 63, WOOD_D)
    s.rect(12, 58, 19, 58, OL1)
    s.rect(11, 63, 20, 63, OL1)
    s.rect(9, 20, 22, 21, ST_D)
    lant = lantern('hang')
    # Laterne klein: 20 px hoch, zentriert auf Pfosten
    s.paste(crop(lant, 8, 3, 16, 22), 8, 0)
    return s


# ============================================================ VERANDA
def porch_floor(side=None):
    s = Spr(32, 32)
    for y in range(32):
        r, v = divmod(y, 8)
        for x in range(32):
            xo = (x + (r % 2) * 11) % 32
            c = WOOD_M
            if v == 0:
                c = WOOD_L
            elif v >= 6:
                c = WOOD_D if v == 6 else EARTH
            if xo in (0, 1) and v > 0:
                c = EARTH
            if hsh(x, y, 4) < 0.05 and v in (2, 3, 4):
                c = WOOD_D
            s.set(x, y, c)
    s.rect(0, 28, 31, 31, WOOD_D)
    s.rect(0, 28, 31, 28, WOOD_L)
    s.rect(0, 31, 31, 31, OL1)
    if side == 'L':
        s.rect(0, 0, 0, 31, OL1)
    if side == 'R':
        s.rect(31, 0, 31, 31, OL1)
    return s


def railing(side=None):
    s = Spr(32, 32)
    s.rect(0, 6, 31, 9, OL1)
    s.rect(0, 7, 31, 8, WOOD_L)
    s.rect(0, 9, 31, 9, WOOD_D)
    s.rect(0, 22, 31, 24, OL1)
    s.rect(0, 23, 31, 23, WOOD_M)
    for x0 in (4, 12, 20, 28):
        if x0 == 28 and side != 'R' and side is not None:
            pass
        s.rect(x0, 10, x0 + 2, 21, OL1)
        s.rect(x0 + 1, 10, x0 + 1, 21, WOOD_M)
        s.rect(x0 + 1, 10, x0 + 1, 15, WOOD_L)
    if side == 'L':
        s.rect(0, 0, 5, 31, OL1)
        s.rect(1, 1, 4, 30, WOOD_M)
        s.rect(1, 1, 1, 30, WOOD_L)
        s.rect(4, 1, 4, 30, WOOD_D)
        s.rect(0, 0, 5, 0, OL1)
    if side == 'R':
        s.rect(26, 0, 31, 31, OL1)
        s.rect(27, 1, 30, 30, WOOD_M)
        s.rect(27, 1, 27, 30, WOOD_L)
        s.rect(30, 1, 30, 30, WOOD_D)
    return s


def post():
    s = Spr(32, 64)
    s.rect(11, 0, 20, 63, OL1)
    s.rect(12, 0, 19, 63, WOOD_M)
    s.rect(12, 0, 13, 63, WOOD_L)
    s.rect(18, 0, 19, 63, WOOD_D)
    s.rect(8, 0, 23, 6, OL1)
    s.rect(9, 1, 22, 5, WOOD_L)
    s.rect(9, 5, 22, 5, WOOD_D)
    s.rect(8, 58, 23, 63, OL1)
    s.rect(9, 59, 22, 62, WOOD_D)
    return s


def steps(side=None):
    s = Spr(32, 32)
    for i, (y0, y1) in enumerate(((6, 15), (16, 25))):
        x0, x1 = (0, 31)
        s.rect(x0, y0, x1, y0, OL1)
        s.rect(x0, y0 + 1, x1, y0 + 2, WOOD_L)
        s.rect(x0, y0 + 3, x1, y1 - 1, WOOD_M)
        s.rect(x0, y1 - 1, x1, y1 - 1, WOOD_D)
        s.rect(x0, y1, x1, y1, OL1)
        for x in range(3, 32, 8):
            s.set(x, y0 + 5, WOOD_D)
    s.rect(0, 26, 31, 29, WOOD_D)
    s.rect(0, 29, 31, 29, OL1)
    if side == 'L':
        s.rect(0, 6, 0, 29, OL1)
    if side == 'R':
        s.rect(31, 6, 31, 29, OL1)
    return s


def bench():
    s = Spr(64, 32)
    for y0 in (3, 9):
        rect_o(s, 4, y0, 59, y0 + 5, WOOD_M)
        s.rect(5, y0 + 1, 58, y0 + 1, WOOD_L)
    rect_o(s, 2, 16, 61, 21, WOOD_L)
    s.rect(3, 17, 60, 17, SAND)
    s.rect(3, 20, 60, 20, WOOD_D)
    for x0 in (6, 54):
        s.rect(x0, 22, x0 + 3, 30, OL1)
        s.rect(x0 + 1, 22, x0 + 2, 29, WOOD_D)
        s.rect(x0, 30, x0 + 3, 31, OL1)
    s.rect(6, 4, 8, 26, OL1) if False else None
    s.rect(6, 9, 7, 20, WOOD_D)
    s.rect(56, 9, 57, 20, WOOD_D)
    return s


def hitching():
    s = Spr(64, 32)
    for x0 in (6, 53):
        s.rect(x0, 6, x0 + 4, 31, OL1)
        s.rect(x0 + 1, 7, x0 + 3, 30, WOOD_M)
        s.rect(x0 + 1, 7, x0 + 1, 30, WOOD_L)
        s.rect(x0 + 3, 7, x0 + 3, 30, WOOD_D)
        s.rect(x0 - 1, 5, x0 + 5, 6, OL1)
        s.rect(x0, 5, x0 + 4, 5, WOOD_L)
    s.rect(10, 12, 53, 17, OL1)
    s.rect(10, 13, 53, 16, WOOD_M)
    s.rect(10, 13, 53, 13, WOOD_L)
    s.rect(10, 16, 53, 16, WOOD_D)
    ell_o(s, 31, 22, 3, 3.5, ST_M, OL1)
    s.ellipse(31, 22, 1.2, 2, CLEAR)
    s.rect(31, 17, 32, 18, ST_L)
    return s


def trough():
    s = Spr(64, 32)
    rect_o(s, 2, 12, 61, 28, WOOD_M)
    s.rect(3, 13, 60, 13, WOOD_L)
    s.rect(5, 15, 58, 17, OL1)
    s.rect(6, 16, 57, 17, NB_L)
    s.rect(6, 16, 57, 16, MOON)
    for x in range(9, 56, 11):
        s.rect(x, 17, x + 3, 17, NB_M)
    for x0 in (14, 31, 48):
        s.rect(x0, 18, x0, 27, WOOD_D)
    s.rect(3, 24, 60, 24, ST_M)
    s.rect(3, 25, 60, 25, ST_D)
    s.rect(6, 28, 12, 31, OL1); s.rect(52, 28, 58, 31, OL1)
    s.rect(7, 28, 11, 30, WOOD_D); s.rect(53, 28, 57, 30, WOOD_D)
    return s


def barrel_stand(mug=True):
    s = Spr(32, 32)
    # Körper
    for y in range(13, 31):
        t = (y - 13) / 17
        hw = int(round(8 + 2.2 * math.sin(math.pi * t)))
        for x in range(16 - hw, 16 + hw):
            rel = (x - (16 - hw)) / (2 * hw)
            c = WOOD_M
            if rel < 0.18:
                c = WOOD_L
            elif rel > 0.8:
                c = WOOD_D
            if (x - (16 - hw)) % 5 == 0 and x != 16 - hw:
                c = WOOD_D
            s.set(x, y, c)
        s.set(16 - hw - 1, y, OL1) if False else None
    # Reifen
    for y0 in (17, 26):
        s.rect(6, y0, 25, y0 + 1, ST_M)
        s.rect(6, y0, 25, y0, ST_L)
    # Deckel (Ellipse)
    ell_o(s, 16, 12.5, 9.4, 3.4, WOOD_L)
    s.ellipse(16, 12.5, 7.5, 2.2, WOOD_M)
    s.rect(9, 12, 22, 12, WOOD_L)
    s.rect(6, 30, 25, 31, OL1)
    s.rect(7, 29, 24, 29, WOOD_D)
    # Silhouette-Outline der Seiten
    for y in range(13, 30):
        t = (y - 13) / 17
        hw = int(round(8 + 2.2 * math.sin(math.pi * t)))
        s.set(16 - hw - 1, y, OL1)
        s.set(16 + hw, y, OL1)
    if mug:
        s.rect(11, 3, 18, 12, OL1)
        s.rect(12, 6, 17, 11, YEL)
        s.rect(17, 6, 17, 11, ORA)
        s.rect(11, 2, 18, 6, OL1)
        s.rect(12, 3, 17, 5, CREAM)
        s.rect(13, 1, 15, 2, CREAM)
        ell_o(s, 20, 8, 1.7, 2.6, ST_L, OL1)
        s.ellipse(20, 8, 0.6, 1.2, CLEAR)
    return s


def barrel_stack():
    s = Spr(32, 32)
    for cx, cy, flag in ((9, 24, 0), (23, 24, 1), (16, 11, 2)):
        for y in range(cy - 7, cy + 8):
            t = (y - (cy - 7)) / 14
            hw = int(round(6 + 1.6 * math.sin(math.pi * t)))
            for x in range(cx - hw, cx + hw):
                rel = (x - (cx - hw)) / (2 * hw)
                c = WOOD_M
                if rel < 0.2:
                    c = WOOD_L
                elif rel > 0.78:
                    c = WOOD_D
                if (x - (cx - hw)) % 4 == 0 and x != cx - hw:
                    c = WOOD_D
                s.set(x, y, c)
            s.set(cx - hw - 1, y, OL1)
            s.set(cx + hw, y, OL1)
        for y0 in (cy - 3, cy + 3):
            s.rect(cx - 7, y0, cx + 6, y0, ST_M)
        s.rect(cx - 7, cy - 8, cx + 6, cy - 8, OL1)
        s.rect(cx - 7, cy + 8, cx + 6, cy + 8, OL1)
        s.rect(cx - 6, cy - 7, cx + 5, cy - 7, WOOD_L)
    s.rect(3, 31, 28, 31, OL1)
    return s


def bottle_crate():
    s = Spr(32, 32)
    cols = [(FOR_D, FOR_M), (WOOD_D, WOOD_M), (MOON, ST_L), (FOR_D, FOR_M)]
    for i, x0 in enumerate((7, 12, 17, 22)):
        a, b = cols[i]
        s.rect(x0, 6, x0 + 2, 16, OL1)
        s.rect(x0 + 1, 8, x0 + 1, 16, a)
        s.set(x0 + 1, 7, ST_L if i != 2 else CREAM)
        s.set(x0 + 2, 9, OL1) if False else None
        s.rect(x0 + 1, 12, x0 + 1, 15, b)
    rect_o(s, 3, 16, 28, 30, WOOD_M)
    s.rect(4, 17, 27, 17, WOOD_L)
    s.rect(4, 22, 27, 22, WOOD_D)
    s.rect(4, 23, 27, 23, WOOD_L)
    s.rect(4, 28, 27, 29, WOOD_D)
    s.rect(8, 18, 9, 29, WOOD_D)
    s.rect(22, 18, 23, 29, WOOD_D)
    s.rect(11, 19, 20, 21, CREAM)
    s.rect(11, 19, 20, 19, MOON)
    s.rect(14, 20, 17, 20, RED_D)
    return s


def bar_barrel():
    s = Spr(32, 32)
    from PIL import Image
    it = load_item('Item_Bierfass')
    s.paste(it, 0, 0)
    return s


# ============================================================ BAU
def build():
    sh = Sheet(16, 6)
    P = sh.put
    # Reihe 0: Dach
    P('dach_first_L', 0, 0, roof_first('L')); P('dach_first_M', 1, 0, roof_first()); P('dach_first_R', 2, 0, roof_first('R'))
    P('dach_flaeche_L', 3, 0, roof_area('L')); P('dach_flaeche_M', 4, 0, roof_area()); P('dach_flaeche_R', 5, 0, roof_area('R'))
    P('dach_traufe_L', 6, 0, roof_eave('L')); P('dach_traufe_M', 7, 0, roof_eave()); P('dach_traufe_R', 8, 0, roof_eave('R'))
    P('vordach_L', 9, 0, awning('L')); P('vordach_M', 10, 0, awning()); P('vordach_R', 11, 0, awning('R'))
    P('gaube_lit', 12, 0, dormer(True)); P('gaube_dunkel', 13, 0, dormer(False))
    P('schornstein', 14, 0, chimney(False)); P('schornstein_rauch', 15, 0, chimney(True))
    # Reihe 1-2: Fassade
    P('fassade_M', 0, 1, facade()); P('fassade_L', 1, 1, facade('L')); P('fassade_R', 2, 1, facade('R'))
    P('fenster_lit', 3, 1, window('lit')); P('fenster_dunkel', 4, 1, window('dark')); P('fenster_laeden_zu', 5, 1, window('shut'))
    P('pendeltuer_zu', 6, 1, saloon_door('zu')); P('pendeltuer_schwingt', 8, 1, saloon_door('schwingt'))
    P('eingang_offen', 10, 1, saloon_door('offen')); P('hintertuer', 12, 1, back_door())
    # Reihe 3: Schilder
    P('schild_ilhans_bar', 0, 3, sign_main()); P('schild_bar', 4, 3, sign_bar()); P('preistafel', 6, 3, price_board())
    P('schild_offen', 9, 3, plaque('OPEN', SAND, FOR_D)); P('schild_zu', 10, 3, plaque('CLOSED', CREAM, RED_D))
    P('wandlaterne', 11, 3, lantern('wand')); P('haengelaterne', 12, 3, lantern('hang'))
    P('veranda_boden_L', 13, 3, porch_floor('L')); P('veranda_boden_M', 14, 3, porch_floor()); P('veranda_boden_R', 15, 3, porch_floor('R'))
    P('stufen_M', 6, 5, steps())
    # Reihe 4-5
    P('ausleger_krug', 0, 4, hang_sign('krug')); P('ausleger_glas', 1, 4, hang_sign('glas'))
    P('kreidetafel', 2, 4, chalk_sandwich()); P('laternenpfosten', 3, 4, lamp_post()); P('pfosten', 4, 4, post())
    P('gelaender_L', 5, 4, railing('L')); P('gelaender_M', 6, 4, railing()); P('gelaender_R', 7, 4, railing('R'))
    P('stufen_L', 5, 5, steps('L')); P('stufen_R', 7, 5, steps('R'))
    P('bank', 8, 4, bench()); P('anbindebalken', 10, 4, hitching()); P('trog', 12, 4, trough())
    P('stehfass', 14, 4, barrel_stand()); P('faesser_stapel', 15, 4, barrel_stack())
    P('flaschenkiste', 8, 5, bottle_crate()); P('bierfass_zapf', 9, 5, bar_barrel())
    P('schild_ilhans_boden', 10, 5, sign_ground())
    return sh


def preview(sh):
    pl = []
    W, Hh = 11, 8
    # Dach
    names = [('dach_first_L', 'dach_first_M', 'dach_first_R'), ('dach_flaeche_L', 'dach_flaeche_M', 'dach_flaeche_R'),
             ('dach_traufe_L', 'dach_traufe_M', 'dach_traufe_R')]
    x0, xs = 1, 8  # Haus: x0..x0+xs-1
    for r, (l, m, rr) in enumerate(names):
        for i in range(xs):
            pl.append((l if i == 0 else (rr if i == xs - 1 else m), x0 + i, 1 + r))
    pl.append(('schornstein_rauch', x0 + 5, 0, 0, -32 + 32))
    # Fassade
    cols = ['fassade_L', 'fenster_lit', 'fenster_dunkel', None, None, 'fenster_lit', 'fenster_lit', 'fassade_R']
    for i, nm in enumerate(cols):
        if nm:
            pl.append((nm, x0 + i, 4))
    pl.append(('pendeltuer_zu', x0 + 3, 4))
    pl.append(('schild_ilhans_bar', x0 + 2, 2, 0, 10))
    pl.append(('wandlaterne', x0 + 2, 4, -24, -8))
    pl.append(('haengelaterne', x0 + 5, 4, 0, -8))
    pl.append(('ausleger_krug', x0 + 7, 3, -4, 6))
    # Veranda
    for i in range(xs):
        pl.append((('veranda_boden_L' if i == 0 else ('veranda_boden_R' if i == xs - 1 else 'veranda_boden_M')), x0 + i, 6))
    pl.append(('stufen_M', x0 + 3, 7)); pl.append(('stufen_M', x0 + 4, 7))
    pl.append(('stehfass', x0, 6, 0, -8)); pl.append(('kreidetafel', x0 + 1, 5, 0, 8))
    pl.append(('bank', x0 + 5, 6, 0, -10)); pl.append(('faesser_stapel', x0 + 7, 6, 0, -4))
    out = compose(W, Hh, NB_D, pl, sh)
    return out


if __name__ == '__main__':
    sh = build()
    out = TILES + '/Tileset_Bar_Aussen.png'
    sh.save(out)
    prev = preview(sh)
    prev.save(TILES + '/Bar_Aussen_Vorschau.png')
    print('Aussen Fremdfarben:', check_palette(out)[:5])
