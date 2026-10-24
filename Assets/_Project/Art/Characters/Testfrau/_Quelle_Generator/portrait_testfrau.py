"""Portrait der Testfrau (64x64) im Stil der anderen Charaktere (Elenora, Mara, Veronica): breites Ei-Gesicht, Haarkappe mit Seitenscheitel,
Seitenstraehnen enden am Kiefer, Schraffur-Schattierung (gezackte Kanten), Auge mit Lid, Weiss, blauer Iris, Pupille, Lichtpunkt.
Keine Glitzerpunkte. Nur Farben aus style_lib.P."""
import math

import style_lib as S

P = S.P
SKIN_L, SKIN_M, SKIN_D = P['haut_hell'], P['haut_mittel'], P['haut_schatten']
HAIR_D, HAIR_B, HAIR_L = P['erde_dunkel'], P['holz_dunkel'], P['holz_mittel']
COAT_D, COAT_B, COAT_L, COAT_K = P['nachtblau_mittel'], P['stoff_blau_gedaempft'], P['stoff_blau_hell'], P['nachtblau_dunkel']
SC_D, SC_L = P['stoff_rot_gedaempft'], P['akzent_rose']
LEA_D, LEA_B, LEA_L = P['holz_dunkel'], P['holz_mittel'], P['holz_hell']
WHITE, BTN, OUTL, MOUTH, ORANGE = P['zaehne_grinsen'], P['licht_warmgelb'], P['outline_dunkel'], P['outline_nacht'], P['laterne_orange']
IRIS_L, IRIS_D, GLOSS = P['stoff_blau_hell'], P['stoff_blau_gedaempft'], P['kerzenweiss']
CX = 31.5


def interp(table, y):
    ys = sorted(table)
    if y <= ys[0]:
        return table[ys[0]]
    if y >= ys[-1]:
        return table[ys[-1]]
    for a, b in zip(ys, ys[1:]):
        if a <= y <= b:
            return table[a] + (table[b] - table[a]) * (y - a) / (b - a)


FACE_HW = {15: 8.5, 17: 11.0, 20: 12.6, 24: 13.4, 30: 13.4, 34: 12.3, 37: 10.4, 40: 7.6, 42: 5.0, 44: 3.2}
HAIR_HW = {3: 8.0, 5: 13.5, 8: 18.0, 12: 20.0, 16: 21.2, 30: 21.8, 36: 20.6, 39: 18.8}
SHOULDER_HW = {49: 8, 51: 14, 53: 20, 55: 25, 57: 29, 59: 31, 61: 32}


def face_hw(y):
    return interp(FACE_HW, y)


def draw(cv, mood):
    def put(x, y, c):
        cv.P(int(x), int(y), c)

    # ---- Schultern, Mantel
    for y in range(49, 64):
        hw = interp(SHOULDER_HW, y)
        x1, x2 = round(CX - hw + 0.5), round(CX + hw - 0.5)
        for x in range(max(x1, 0), min(x2, 63) + 1):
            t = (x - CX) / max(hw, 1)
            c = COAT_B
            edge = t + (0.06 if (x + y) % 2 else 0.0)                # gezackte Kante (Schraffur)
            if edge < -0.62:
                c = COAT_L
            elif edge > 0.52:
                c = COAT_D
            put(x, y, c)
    for y in range(53, 63, 3):                                       # Nahtstriche
        put(12 + (y - 53) // 3 * 2, y, COAT_D)
        put(51 - (y - 53) // 3 * 2, y, COAT_L)
    for y in range(51, 64):                                          # Knopfleiste, Knoepfe
        put(31, y, COAT_K)
        put(32, y, COAT_K)
    for by in (55, 59, 63):
        put(30, by, BTN)
    for k in range(6):                                               # Revers
        for x in range(24 - k, 28 - k):
            put(x, 49 + k, COAT_L)
        for x in range(36 + k, 40 + k):
            put(x, 49 + k, COAT_L if k < 3 else COAT_D)
    for k in range(0, 31):                                           # Riemen
        x, y = 15 + k, 52 + round(k * 11 / 30)
        put(x, y, LEA_B)
        put(x, y + 1, LEA_D)
        if k % 5 == 0:
            put(x, y, LEA_L)
    # ---- Hals mit Kinnschatten (Schraffur)
    for y in range(40, 51):
        hw = 4.6 if y < 46 else 5.6
        for x in range(round(CX - hw + .5), round(CX + hw - .5) + 1):
            c = SKIN_M
            if y < 43:
                c = SKIN_D if (x + y) % 2 == 0 else SKIN_M
            elif y < 45 and (x + y) % 2 == 0:
                c = SKIN_D
            put(x, y, c)
    # ---- Haare hinten: Kappe + Seitenstraehnen bis zum Kiefer
    for y in range(3, 41):
        hw = interp(HAIR_HW, y)
        if y <= 16:
            top = 8.0 * max(0.0, 1 - ((16 - y) / 13.0) ** 2) ** 0.5   # runde Kuppe
            hw = max(hw, 0) if y > 5 else hw
        x1, x2 = round(CX - hw), round(CX + hw - 1)
        fh = face_hw(y) if y >= 15 else 0
        for x in range(x1, x2 + 1):
            if y > 16 and abs(x - CX) < fh - 1.5:
                continue
            # Scallop-Ende der Straehnen am Kiefer (Locken)
            side_l = x < CX
            end = 38 + round(1.6 * math.sin(x * 1.1) + (1 if (x % 3 == 0) else 0))
            if y > 33 and y > end:
                continue
            dx = (x - CX) / max(hw, 1)
            c = HAIR_B
            if (dx < -0.55 and y < 22) or (side_l and x - x1 <= 1 and y < 30):
                c = HAIR_L
            elif dx > 0.35:
                c = HAIR_D if (x + y) % 2 == 0 or dx > 0.7 else HAIR_B
            else:
                if (x * 2 + y) % 6 == 0 and y > 14:
                    c = HAIR_D                                         # Straehnenrillen
                elif (x + y * 2) % 9 == 0 and dx < 0:
                    c = HAIR_L
            put(x, y, c)
    # Locken-Ringe an den Enden (Pixel-Kringel)
    for lx in (21, 24, 39, 42):
        put(lx, 36, HAIR_D)
        put(lx + 1, 37, HAIR_D)
    # ---- Gesicht
    for y in range(15, 45):
        hw = face_hw(y)
        x1, x2 = round(CX - hw + 0.5), round(CX + hw - 0.5)
        for x in range(x1, x2 + 1):
            nx = (x - CX) / max(hw, 1)
            ny = (y - 28) / 15.0
            t = 0.62 * nx + 0.28 * ny
            c = SKIN_L
            if t > 0.62:
                c = SKIN_M
            elif t > 0.52 and (x + y) % 2 == 0:
                c = SKIN_M                                             # gezackter Uebergang
            if t > 0.96:
                c = SKIN_D if (x + y) % 2 == 0 else SKIN_M
            if y >= 41 and (x + y) % 2 == 0:
                c = SKIN_M
            put(x, y, c)
    # ---- Seitenscheitel, Pony: Scheitel bei x=26
    for y in range(4, 24):
        for x in range(10, 54):
            if y < 12:
                continue
            ex = 15 + abs(x - 26) * (0.36 if x > 26 else 0.22) + (0 if x > 26 else 0)
            edge = ex + (1 if (x + y) % 3 == 0 else 0)
            fh = face_hw(y)
            if abs(x - CX) <= fh + 2 and y <= edge and y >= 12:
                dxx = (x - 26) / 14.0
                c = HAIR_B
                if x > 26 and y > edge - 2:
                    c = HAIR_D if (x + y) % 2 == 0 else HAIR_B      # Unterkante dunkler (Schraffur)
                elif x < 26:
                    c = HAIR_L if (x * 2 + y) % 5 else HAIR_B
                put(x, y, c)
    for k in range(13):                                              # Scheitellinie
        put(26 + round(-k * 0.15), 5 + k, HAIR_D)
        if k % 2 == 0:
            put(27 + round(-k * 0.15), 5 + k, HAIR_L)
    # ---- Augen (Elenora-Stil: Lid, Weiss, blaue Iris, Pupille, Lichtpunkt)
    for ex in (23, 35):
        for k in range(6):                                           # Braue
            put(ex + k, 22 - (1 if 1 <= k <= 4 else 0), HAIR_D)
        if mood == 'blink':
            for k in range(6):
                put(ex + k, 27 + (1 if k in (0, 5) else 0), SKIN_D)
            for k in range(1, 5):
                put(ex + k, 29, SKIN_M)
            continue
        for k in range(6):
            put(ex + k, 25, OUTL)                                    # Oberlid
        put(ex - 1 if ex < 30 else ex + 6, 26, OUTL)                 # Wimper
        for y in (26, 27, 28):
            for k in range(6):
                put(ex + k, y, WHITE)
        ix = ex + 1 if ex < 30 else ex + 2
        for y in (26, 27, 28):
            for k in range(3):
                put(ix + k, y, IRIS_L if y < 28 else IRIS_D)
        put(ix + 1, 27, MOUTH)                                       # Pupille
        put(ix + 1, 26, MOUTH)
        put(ix, 26, GLOSS)                                           # Lichtpunkt
        for k in range(6):
            put(ex + k, 29, SKIN_M)                                  # Unterlid
    # ---- Nase
    for y in range(26, 33):
        put(32 + (1 if y > 29 else 0), y, SKIN_M)
    put(30, 33, SKIN_D)
    put(33, 33, SKIN_D)
    put(31, 34, SKIN_M)
    put(32, 34, SKIN_M)
    # ---- Mund
    if mood in ('calm', 'blink'):
        for x in range(29, 35):
            put(x, 37, SC_D)
        for x in range(30, 34):
            put(x, 38, SC_L)
        put(28, 37, SKIN_M)
        put(35, 37, SKIN_M)
        for x in range(30, 34):
            put(x, 39, SKIN_M)
        put(31, 38, P['kerzenweiss'])
    elif mood == 'talk_A':
        for x in range(29, 35):
            put(x, 37, SC_D)
        for y in range(38, 41):
            for x in range(30, 34):
                put(x, y, MOUTH)
        for x in range(30, 34):
            put(x, 38, WHITE)
            put(x, 41, SC_L)
    elif mood == 'talk_E':
        for x in range(28, 36):
            put(x, 37, SC_D)
        for x in range(29, 35):
            put(x, 38, WHITE)
            put(x, 39, MOUTH)
        for x in range(30, 34):
            put(x, 40, SC_L)
    else:
        for x in range(30, 34):
            put(x, 36, SC_D)
        for y in range(37, 40):
            put(31, y, MOUTH)
            put(32, y, MOUTH)
            put(30, y, SC_L)
            put(33, y, SC_D)
        for x in range(30, 34):
            put(x, 40, SC_D)
    # ---- Schal (zweitonig, eine Falte) und kleine Haarspange, Ohrstecker
    for y in range(45, 52):
        hw = 11.4 - abs(y - 47) * 0.9
        for x in range(round(CX - hw), round(CX + hw)):
            t = (x - CX) / hw
            c = SC_L if (y < 49 and t < 0.5) else SC_D
            put(x, y, c)
    for x in range(24, 31):
        put(x, 49, SC_D)
    for y in range(50, 62):
        for x in range(36 + (1 if y > 56 else 0), 41 + (1 if y > 56 else 0)):
            put(x, y, SC_L if x < 39 else SC_D)
    put(38, 62, SC_D)
    put(39, 62, SC_D)
    put(27, 7, SC_L)
    put(28, 7, SC_L)
    for (ex_, ey_) in ((19, 41), (44, 41)):
        put(ex_, ey_, BTN)
        put(ex_, ey_ + 1, ORANGE)
