"""Portrait von OTIGO (64x64) im Familien-Stil: breites Gesicht, nach hinten gestrichenes Haar mit Volumen, kraeftige Brauen, braune Augen,
Stoppelbart als Schraffur, gruene Jacke, Kette. Keine Glitzerpunkte. Nur Farben aus style_lib.P."""
import style_lib as S

P = S.P
SKIN_L, SKIN_M, SKIN_K = P['haut_hell'], P['haut_mittel'], P['haut_schatten']
HAIR_D, HAIR_B, HAIR_L = P['outline_dunkel'], P['outline_nacht'], P['erde_dunkel']
J_B, J_L, J_D, J_K = P['wald_mittel'], P['gras'], P['wald_dunkel'], P['outline_nacht']
TEE = P['wald_dunkel']
METAL_L, METAL_M, GLOSS = P['stein_hell'], P['stein_mittel'], P['kerzenweiss']
WHITE, OUTL, LID = P['zaehne_grinsen'], P['outline_dunkel'], P['outline_dunkel']
IRIS_L, IRIS_D = P['holz_mittel'], P['holz_dunkel']
LIP, LIP_L, MOUTH = P['haut_schatten'], P['haut_mittel'], P['outline_nacht']
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


FACE_HW = {14: 10.5, 17: 13.0, 21: 14.4, 28: 14.6, 34: 14.2, 38: 13.2, 41: 11.4, 44: 8.4, 46: 5.6}
HAIR_HW = {3: 6.5, 5: 11.5, 8: 14.8, 12: 16.3, 16: 16.6}
SHOULDER_HW = {47: 8, 49: 15, 51: 21, 53: 26, 55: 29, 57: 31, 59: 32}


def draw(cv, mood):
    def put(x, y, c):
        cv.P(int(x), int(y), c)

    # ---- Schultern, Jacke (gruen), Kragen, Reissverschluss
    for y in range(47, 64):
        hw = interp(SHOULDER_HW, y)
        x1, x2 = round(CX - hw + 0.5), round(CX + hw - 0.5)
        for x in range(max(x1, 0), min(x2, 63) + 1):
            t = (x - CX) / max(hw, 1)
            c = J_B
            edge = t + (0.06 if (x + y) % 2 else 0.0)
            if edge < -0.60:
                c = J_L
            elif edge > 0.50:
                c = J_D
            put(x, y, c)
    for y in range(47, 56):                                          # dunkles Shirt im V-Ausschnitt
        w = 7 - (y - 47) * 0.6
        for x in range(round(CX - w), round(CX + w) + 1):
            put(x, y, TEE)
    for y in range(52, 64):                                          # Reissverschluss
        put(31, y, METAL_M if y % 2 else J_K)
        put(32, y, J_K)
    put(32, 63, METAL_L)
    for k in range(6):                                               # Kragenflaechen
        for x in range(21 - k, 26 - k):
            put(x, 47 + k, J_L)
        for x in range(38 + k, 43 + k):
            put(x, 47 + k, J_D if k > 1 else J_B)
    for y in range(56, 63, 3):                                       # Taschenkanten/Naehte
        put(14 + (y - 56) // 3 * 2, y, J_D)
        put(49 - (y - 56) // 3 * 2, y, J_L)
    # Kette mit Anhaenger
    for k in range(0, 9):
        put(24 + k, 47 + round(k * 0.9), METAL_L if k % 2 == 0 else METAL_M)
        put(39 - k, 47 + round(k * 0.9), METAL_L if k % 2 == 0 else METAL_M)
    put(31, 55, METAL_L)
    put(32, 55, METAL_L)
    put(31, 56, GLOSS)
    put(32, 56, METAL_M)
    # ---- Hals (breit, Kinnschatten)
    for y in range(41, 52):
        hw = 6.2 if y < 48 else 7.2
        for x in range(round(CX - hw + .5), round(CX + hw - .5) + 1):
            c = SKIN_M
            if y < 45 and (x + y) % 2 == 0:
                c = SKIN_K
            if y >= 48:
                c = SKIN_M if x > CX - 3 else SKIN_L
            put(x, y, c)
    # ---- Haare hinten: Kuppe mit Volumen, kurze Seiten
    for y in range(3, 23):
        hw = interp(HAIR_HW, y)
        x1, x2 = round(CX - hw), round(CX + hw - 1)
        for x in range(x1, x2 + 1):
            dx = (x - CX) / max(hw, 1)
            c = HAIR_B
            if dx < -0.40 and y < 16:
                c = HAIR_L
            elif dx > 0.45:
                c = HAIR_D if (x + y) % 2 == 0 or dx > 0.75 else HAIR_B
            put(x, y, c)
    # Straehnen: diagonal von vorne links nach hinten rechts (nach hinten gestrichen)
    for y in range(4, 17):
        for x in range(14, 50):
            if cv.px.get((x, y)) in (HAIR_B, HAIR_L, HAIR_D):
                v = (x * 2 - y * 3) % 7
                if v == 0:
                    put(x, y, HAIR_D)
                elif v == 3 and x < 34:
                    put(x, y, HAIR_L)
    # ---- Gesicht mit Kurvenschattierung und Stoppeln
    for y in range(14, 47):
        hw = interp(FACE_HW, y)
        x1, x2 = round(CX - hw + 0.5), round(CX + hw - 0.5)
        for x in range(x1, x2 + 1):
            nx = (x - CX) / max(hw, 1)
            ny = (y - 28) / 16.0
            t = 0.62 * nx + 0.28 * ny
            c = SKIN_L
            if t > 0.60:
                c = SKIN_M
            elif t > 0.50 and (x + y) % 2 == 0:
                c = SKIN_M
            if t > 0.96:
                c = SKIN_K if (x + y) % 2 == 0 else SKIN_M
            # Mundzone bleibt sauber, Stoppelbart = mittlerer Ton mit wenigen dunklen Punkten (kein Gitter)
            clean = 27 <= x <= 36 and 36 <= y <= 41
            beard = (y >= 36 and abs(nx) > 0.0) or (34 <= y <= 36 and abs(x - CX) <= 7.5)
            if clean:
                c = SKIN_M if t > 0.6 else SKIN_L
            elif beard:
                if y <= 36:
                    c = SKIN_M if (x + y) % 2 == 0 else c
                else:
                    h = ((x * 7919 + y * 104729) * 2654435761 % 4294967296 >> 8) % 100   # feste Zufallsverteilung
                    dens = 16 if y >= 41 else 9
                    if h < dens:
                        c = SKIN_K
                    elif h < 62:
                        c = SKIN_M
            put(x, y, c)
    # Haaransatz auf der Stirn (nach hinten gestrichen, Geheimratsecken)
    for y in range(12, 22):
        hw = interp(FACE_HW, y)
        for x in range(round(CX - hw - 1), round(CX + hw + 1)):
            hl = 16.5 + abs(x - CX) * 0.20 - (1.5 if abs(x - CX) < 5 else 0) + (1 if x < CX else 0) * 0.8
            if y <= hl and y >= 12:
                dxx = (x - CX) / 15.0
                c = HAIR_B
                if dxx < -0.35:
                    c = HAIR_L if (x * 2 - y * 3) % 7 else HAIR_B
                elif y > hl - 1.5:
                    c = HAIR_D if (x + y) % 2 == 0 else HAIR_B
                put(x, y, c)
    for y in range(17, 29):                                          # Koteletten
        hwf = interp(FACE_HW, y)
        for x in (round(CX - hwf), round(CX - hwf) + 1, round(CX + hwf) - 1, round(CX + hwf)):
            if y < 27 or (y < 29 and (x + y) % 2 == 0):
                put(x, y, HAIR_B if x < CX else HAIR_D)
    # ---- Brauen (kraeftig, 2 Zeilen)
    for ex, flip in ((21, 1), (36, -1)):
        for k in range(7):
            yb = 22 - (1 if 1 <= k <= 5 else 0)
            put(ex + k, yb, HAIR_D)
            put(ex + k, yb + 1, HAIR_B) if (flip == 1 and k >= 2) or (flip == -1 and k <= 4) else None
    # ---- Augen
    for ex in (23, 35):
        if mood == 'blink':
            for k in range(6):
                put(ex + k, 27 + (1 if k in (0, 5) else 0), SKIN_K)
            for k in range(1, 5):
                put(ex + k, 29, SKIN_M)
            continue
        for k in range(6):
            put(ex + k, 25, LID)
        put(ex - 1 if ex < 30 else ex + 6, 26, LID)
        for y in (26, 27, 28):
            for k in range(6):
                if y in (26, 28) and k in (0, 5):
                    continue
                put(ex + k, y, WHITE)
        ix = ex + 1 if ex < 30 else ex + 2
        for y in (26, 27, 28):
            for k in range(3):
                put(ix + k, y, IRIS_L if y < 28 else IRIS_D)
        put(ix + 1, 27, MOUTH)
        put(ix + 1, 26, MOUTH)
        put(ix, 26, GLOSS)
        for k in range(6):
            put(ex + k, 29, SKIN_M)
            if (ex + k) % 2 == 0:
                put(ex + k, 30, SKIN_M)                              # Traenensack
    # ---- Nase (kraeftig, gerade)
    for y in range(25, 34):
        put(33 if y > 27 else 32, y, SKIN_M)
    for y in range(29, 34):
        put(34, y, SKIN_M) if y > 30 else None
    put(29, 34, SKIN_K)
    put(30, 34, SKIN_K)
    put(33, 34, SKIN_K)
    put(34, 34, SKIN_K)
    put(31, 35, SKIN_M)
    put(32, 35, SKIN_M)
    put(31, 29, GLOSS) if False else None
    # ---- Mund (dunkle Linie, saubere Lippen)
    if mood in ('calm', 'blink'):
        for x in range(29, 35):
            put(x, 38, LIP)
        for x in range(30, 34):
            put(x, 39, SKIN_M)
        put(31, 39, SKIN_L)
        put(32, 39, SKIN_L)
        put(28, 38, SKIN_M)
        put(35, 38, SKIN_M)
    elif mood == 'talk_A':
        for x in range(29, 35):
            put(x, 37, LIP)
        for y in range(38, 41):
            for x in range(30, 34):
                put(x, y, MOUTH)
        for x in range(30, 34):
            put(x, 38, WHITE)
            put(x, 41, SKIN_M)
    elif mood == 'talk_E':
        for x in range(28, 36):
            put(x, 37, LIP)
        for x in range(29, 35):
            put(x, 38, WHITE)
            put(x, 39, MOUTH)
        for x in range(29, 35):
            put(x, 40, SKIN_M)
    else:
        for x in range(30, 34):
            put(x, 37, LIP)
        for y in range(38, 41):
            put(31, y, MOUTH)
            put(32, y, MOUTH)
            put(30, y, SKIN_M)
            put(33, y, SKIN_M)
        for x in range(30, 34):
            put(x, 41, SKIN_M)
