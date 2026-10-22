"""Dorf-Objekte (Pivot unten links, 32 px Raster): Wegweiser (Englisch), Kreuz-Schild, Laternen, Beete, Waescheleine, Kuebel, Talisman-Pfosten, Ortsschild.
Ausgabe: Art/Tiles/Dorf/Objekte/*.png + _Liste.txt.  Aufruf: python dorf_objekte.py [ausgabeordner] [vorschau.png]"""
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nwlib import *

OUTLINE = H('1a1526')
C = {
    'r': H('7a2e3a'), 'R': H('c4636b'), 'w': H('f2ead8'), 'W': H('fff1c9'), 'g': H('4a7a4f'), 'G': H('9ab87a'), 'y': H('ffd27a'),
    'o': H('ffa550'), 'b': H('7a5a43'), 'B': H('5c4033'), 's': H('9a95a0'), 'S': H('4a4550'), 'k': H('1a1526'), 'c': H('b89a72'),
    't': H('6fd3e6'), 'T': H('a8f0ff'), 'd': H('2b6b8a'), 'e': H('e8733a'), 'h': H('9c7a5a'), 'p': H('4f3d5c'), 'P': H('3d2e4a'),
}

FONT = {
    'A': '010101111101101', 'B': '110101110101110', 'C': '011100100100011', 'D': '110101101101110', 'E': '111100110100111',
    'F': '111100110100100', 'G': '011100101101011', 'H': '101101111101101', 'I': '111010010010111', 'K': '101101110101101',
    'L': '100100100100111', 'M': '101111111101101', 'N': '111101101101101', 'O': '010101101101010', 'P': '110101110100100',
    'R': '110101110101101', 'S': '011100010001110', 'T': '111010010010010', 'U': '101101101101111', 'V': '101101101101010',
    'Y': '101101010010010', ' ': '000000000000000',
}


WIDE = {'M': ['10001', '11011', '10101', '10001', '10001']}


def text(sp, x, y, s, col):
    for ch in s:
        if ch in WIDE:
            for j, row in enumerate(WIDE[ch]):
                for i, bit in enumerate(row):
                    if bit == '1':
                        sp.set(x + i, y + j, col)
            x += 6
            continue
        g = FONT[ch]
        for i, bit in enumerate(g):
            if bit == '1':
                sp.set(x + i % 3, y + i // 3, col)
        x += 4
    return x


def text_w(s):
    return sum(6 if c in WIDE else 4 for c in s) - 1


ICONS = {
    'Doctor': ['.wwwwwww.', 'wwwrrrwww', 'wwwrrrwww', 'wrrrrrrrw', 'wrrrrrrrw', 'wrrrrrrrw', 'wwwrrrwww', 'wwwrrrwww', '.wwwwwww.'],
    'Bakery': ['.........', '..bbbbb..', '.bccWccb.', 'bcWccccWb', 'bccccWccb', 'bcccccccb', '.bbbbbbb.', '.........', '.........'],
    'Bar': ['.........', '.WWWWW...', '.wwwwwww.', '.yyyyyyyy', '.yyyyy..y', '.yyyyy..y', '.yyyyyyyy', '.ooooo...', '.........'],
    'Diner': ['.s.s.s.s.', '.s.s.s.s.', '.sssssss.', '...sss...', '...sss...', '...sss...', '...sss...', '...sss...', '.........'],
    'Sheriff': ['....y....', '....y....', 'yyyyyyyyy', '.yyyyyyy.', '..yyyyy..', '.yyyyyyy.', '.yyy.yyy.', '.yy...yy.', '.........'],
    'Pastor': ['....s....', '....s....', '..sssss..', '....s....', '....s....', '....s....', '....s....', '...sss...', '.........'],
    'Market': ['.....g...', '....gg...', '..RRrRR..', '.RRRRRRR.', 'RRWRRRRRr', 'RRRRRRRRr', '.RRRRRRr.', '..rRRRr..', '.........'],
    'Barn': ['....r....', '...rrr...', '..rrrrr..', '.rrrrrrr.', 'rrrrrrrrr', 'rwwwrwwwr', 'rwrwrwrwr', 'rwwwrwwwr', 'rrrrrrrrr'],
    'Graves': ['..sssss..', '.sssssss.', '.sssWsss.', '.ssWWWss.', '.sssWsss.', '.sssWsss.', '.sssssss.', 'ggggggggg', '.........'],
    'Smith': ['.SSSSSSS.', 'SSSSSSSSS', '.SSSSSS..', '...SSS...', '...SSS...', '..SSSSS..', '.SSSSSSS.', '.........', '.........'],
    'Villa': ['....y....', '...yyy...', '..yyyyy..', '..yyyyy..', '.yyyyyyy.', 'yyyyyyyyy', '....o....', '.........', '.........'],
    'Homes': ['....c....', '...ccc...', '..ccccc..', '.ccccccc.', '.bbbbbbb.', '.bwbbbwb.', '.bbbkbbb.', '.bbbkbbb.', '.........'],
    'Forest': ['....g....', '...ggg...', '..ggggg..', '...ggg...', '..ggggg..', '.ggggggg.', '....b....', '....b....', '.........'],
}
LABEL = {'Doctor': 'DOCTOR', 'Bakery': 'BAKERY', 'Bar': 'BAR', 'Diner': 'DINER', 'Sheriff': 'SHERIFF', 'Pastor': 'PASTOR',
         'Market': 'MARKET', 'Barn': 'BARN', 'Graves': 'GRAVES', 'Smith': 'SMITH', 'Villa': 'VILLA', 'Homes': 'HOMES', 'Forest': 'FOREST'}


def draw_icon(sp, x, y, key):
    for j, row in enumerate(ICONS[key]):
        for i, ch in enumerate(row):
            if ch != '.':
                sp.set(x + i, y + j, C[ch])


def wood_post(sp, x0, x1, y0, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c = BROWN[2]
            if x == x0:
                c = BROWN[3]
            elif x == x1:
                c = BROWN[1]
            if hsh(x, y, 5) < 0.10:
                c = BROWN[1] if c != BROWN[1] else BROWN[0]
            sp.set(x, y, c)


def grass_foot(sp, cx, y):
    for k, (dx, h, c) in enumerate(((-5, 2, GREEN[2]), (-3, 3, GREEN[3]), (-1, 2, GREEN[2]), (4, 3, GREEN[3]), (6, 2, GREEN[2]), (8, 2, GREEN[3]))):
        for i in range(h):
            sp.set(cx + dx, y - i, c)
    for dx in range(-7, 10):
        if hsh(dx, y, 77) < 0.4:
            sp.set(cx + dx, y + 1, STONE[1])


def wegweiser(key, direction):
    sp = Spr(64, 64)
    wood_post(sp, 29, 34, 24, 62)
    grass_foot(sp, 31, 62)
    label = LABEL[key]
    if direction == 'R':
        x0, x1, tip = 4, 52, (53, 60)
        ix = 7
        tx = 18
    else:
        x0, x1, tip = 11, 59, (3, 10)
        ix = 49
        tx = 15
    y0, y1 = 7, 26
    # Brett
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c = BROWN[1]
            if y == y0:
                c = BROWN[3]
            elif y == y0 + 1:
                c = BROWN[2]
            elif y == y1:
                c = BROWN[0]
            sp.set(x, y, c)
    # Spitze
    mid = (y0 + y1) / 2.0
    n = tip[1] - tip[0]
    for i in range(n + 1):
        px = tip[0] + i if direction == 'R' else tip[1] - i
        half = (y1 - y0) / 2.0 * (1 - i / (n + 0.5))
        for y in range(int(math.floor(mid - half)), int(math.ceil(mid + half)) + 1):
            c = BROWN[1]
            if y <= mid - half + 1:
                c = BROWN[3]
            elif y >= mid + half - 1:
                c = BROWN[0]
            sp.set(px, y, c)
    sp.set(x0 + 1, y0 + 2, STONE[4])
    sp.set(x1 - 1, y0 + 2, STONE[4]) if direction == 'L' else None
    sp.set(x0 + 1, y1 - 1, STONE[3])
    sp.set(x1 - 1, y1 - 1, STONE[3])
    # Inhalt
    draw_icon(sp, ix, y0 + 5, key)
    text(sp, tx, y0 + 8, label, C['W'])
    sp.outline(OUTLINE)
    return sp.im


def kreuz_schild():
    sp = Spr(32, 64)
    wood_post(sp, 5, 8, 8, 62)
    grass_foot(sp, 7, 62)
    # Ausleger
    for x in range(5, 27):
        sp.set(x, 8, BROWN[3])
        sp.set(x, 9, BROWN[2])
        sp.set(x, 10, BROWN[1])
    for i in range(5):
        sp.set(9 + i, 11 + i, BROWN[2])
    # Ketten + Schild 18x18
    for y in range(11, 14):
        sp.set(12, y, STONE[3])
        sp.set(23, y, STONE[3])
    x0, y0 = 8, 14
    for y in range(y0, y0 + 19):
        for x in range(x0, x0 + 20):
            edge = x in (x0, x0 + 19) or y in (y0, y0 + 18)
            sp.set(x, y, BROWN[1] if edge else C['W'])
    for y in range(y0 + 1, y0 + 18):
        sp.set(x0 + 1, y, BROWN[3])
        sp.set(x0 + 18, y, STONE[4])
    for y in range(y0 + 3, y0 + 16):
        for x in range(x0 + 7, x0 + 13):
            sp.set(x, y, C['r'])
    for y in range(y0 + 7, y0 + 12):
        for x in range(x0 + 3, x0 + 17):
            sp.set(x, y, C['r'])
    for x in range(x0 + 7, x0 + 13):
        sp.set(x, y0 + 3, C['R'])
    sp.outline(OUTLINE)
    return sp.im


def gartenlicht():
    sp = Spr(32, 48)
    for y in range(18, 46):
        sp.set(15, y, PURP[3])
        sp.set(16, y, PURP[2])
    # Sockel
    sp.rect(12, 42, 19, 46, STONE[2])
    sp.rect(12, 42, 19, 42, STONE[4])
    sp.rect(12, 46, 19, 46, STONE[0])
    # Laterne
    sp.rect(11, 8, 20, 18, PURP[2])
    sp.rect(12, 9, 19, 17, C['o'])
    sp.rect(13, 10, 18, 16, C['y'])
    sp.rect(14, 11, 17, 15, C['W'])
    for x in (11, 15, 16, 20):
        sp.rect(x, 8, x, 18, PURP[3])
    sp.rect(10, 6, 21, 7, PURP[3])
    sp.rect(12, 4, 19, 5, PURP[2])
    sp.rect(14, 2, 17, 3, PURP[3])
    sp.rect(10, 19, 21, 19, PURP[1])
    sp.set(15, 1, C['y'])
    sp.outline(OUTLINE)
    return sp.im


def laterne_doppel():
    sp = Spr(64, 64)
    for y in range(18, 62):
        sp.set(30, y, PURP[4])
        sp.set(31, y, PURP[3])
        sp.set(32, y, PURP[3])
        sp.set(33, y, PURP[2])
    sp.rect(26, 58, 37, 62, STONE[2])
    sp.rect(26, 58, 37, 58, STONE[4])
    sp.rect(24, 60, 39, 62, STONE[1])
    sp.rect(24, 60, 39, 60, STONE[3])
    # Querarm mit Bogen
    for x in range(10, 54):
        yy = 18 + int(round(2.2 * ((abs(x - 31.5) / 21.5) ** 2)))
        sp.set(x, yy, PURP[3])
        sp.set(x, yy + 1, PURP[2])
    sp.rect(29, 14, 34, 17, PURP[3])
    sp.rect(30, 12, 33, 13, PURP[4])
    sp.set(31, 10, C['y'])
    sp.set(32, 10, C['y'])

    def lantern(cx):
        x0 = cx - 4
        sp.rect(cx, 22, cx, 24, PURP[3])
        sp.rect(x0 - 1, 24, x0 + 9, 25, PURP[3])
        sp.rect(x0, 26, x0 + 8, 37, PURP[2])
        sp.rect(x0 + 1, 27, x0 + 7, 36, C['o'])
        sp.rect(x0 + 2, 28, x0 + 6, 35, C['y'])
        sp.rect(x0 + 3, 29, x0 + 5, 34, C['W'])
        for x in (x0, x0 + 4, x0 + 8):
            sp.rect(x, 26, x, 37, PURP[3])
        sp.rect(x0 + 1, 38, x0 + 7, 39, PURP[2])
        sp.rect(x0 + 3, 40, x0 + 5, 40, PURP[3])
        sp.rect(x0 + 2, 23, x0 + 6, 23, PURP[4])
    lantern(12)
    lantern(51)
    sp.outline(OUTLINE)
    return sp.im


def soil(sp, x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            h = hsh(x, y, 31)
            c = BROWN[1]
            if h < 0.15:
                c = BROWN[0]
            elif h > 0.88:
                c = BROWN[2]
            if (y - y0) % 5 == 3 and hsh(x, y, 2) < 0.8:
                c = BROWN[0]
            sp.set(x, y, c)


def bed_frame(sp):
    sp.rect(0, 14, 63, 31, BROWN[3])
    sp.rect(1, 15, 62, 30, BROWN[2])
    for x in range(1, 63):
        sp.set(x, 14, BROWN[4])
        sp.set(x, 31, BROWN[0])
    for x in (0, 62):
        for y in range(14, 32):
            sp.set(x, y, BROWN[1] if x == 62 else BROWN[3])
    soil(sp, 3, 16, 60, 28)
    for x in range(1, 63):
        if hsh(x, 3, 3) < 0.4:
            sp.set(x, 15, BROWN[3])
            sp.set(x, 29, BROWN[1])
            sp.set(x, 30, BROWN[1])


def beet(kind):
    sp = Spr(64, 32)
    bed_frame(sp)
    if kind == 'Kohl':
        for row, y in enumerate((20, 26)):
            for k in range(5):
                x = 7 + k * 11 + (4 if row else 0)
                blob(sp, x, y, 5.0, 4.5, [GREEN[1], GREEN[2], GREEN[3], GREEN[4], GREEN[5]], seed=k + row * 7)
                sp.set(x - 1, y - 1, GREEN[6])
                sp.set(x + 1, y + 1, GREEN[1])
    elif kind == 'Karotten':
        for row, y in enumerate((21, 27)):
            for k in range(8):
                x = 6 + k * 7 + (3 if row else 0)
                for i, (dx, dy) in enumerate(((0, -4), (-1, -3), (1, -3), (-2, -2), (2, -2))):
                    sp.set(x + dx, y + dy, GREEN[3] if i % 2 else GREEN[4])
                sp.set(x, y - 5, GREEN[5])
                sp.rect(x - 1, y - 1, x + 1, y, C['e'])
                sp.set(x, y - 1, C['o'])
    elif kind == 'Kraeuter':
        for row, y in enumerate((20, 26)):
            for k in range(6):
                x = 6 + k * 9 + (4 if row else 0)
                blob(sp, x, y, 4.0, 3.5, [GREEN[1], GREEN[2], GREEN[3], GREEN[4]], seed=k + row * 3)
                if (k + row) % 2 == 0:
                    sp.set(x, y - 4, VIOLET)
                    sp.set(x + 1, y - 3, VIOLET)
                    sp.set(x - 1, y - 3, PINK)
    elif kind == 'Blumen':
        cols = [PINK, YELLOW, CREAM, VIOLET, RED]
        for row, y in enumerate((22, 27)):
            for k in range(9):
                x = 5 + k * 6 + (3 if row else 0)
                for i in range(4):
                    sp.set(x, y - i, GREEN[3 if i % 2 else 2])
                c = cols[(k + row) % 5]
                sp.rect(x - 1, y - 6, x + 1, y - 4, c)
                sp.set(x, y - 5, YELLOW if c != YELLOW else ORANGE)
                sp.set(x, y - 7, c)
    elif kind == 'Kuerbis':
        for k, (x, y) in enumerate(((10, 24), (24, 22), (38, 25), (51, 22), (30, 27))):
            r = 5.0 if k != 4 else 3.5
            blob(sp, x, y, r + 1, r, [BROWN[2], C['e'], C['e'], C['o'], AMBER], seed=k)
            sp.rect(x - 1, y - int(r) - 1, x, y - int(r), GREEN[2])
            sp.set(x - 1, y, BROWN[1])
            sp.set(x + 1, y, BROWN[1])
        for x in range(5, 60, 2):
            sp.set(x, 19 + int(2 * math.sin(x * 0.5)), GREEN[3])
    sp.outline(OUTLINE) if False else None
    return sp.im


def waescheleine():
    sp = Spr(96, 64)
    wood_post(sp, 4, 7, 10, 62)
    wood_post(sp, 88, 91, 10, 62)
    grass_foot(sp, 5, 62)
    grass_foot(sp, 89, 62)
    # Leine mit Durchhang
    pts = []
    for x in range(6, 90):
        y = 12 + int(round(3 * math.sin(math.pi * (x - 6) / 83.0)))
        sp.set(x, y, STONE[3])
        pts.append((x, y))
    cloths = [(14, 14, 18, C['r']), (30, 12, 20, C['w']), (50, 15, 16, C['b'].__class__(H('3a4a7a'))), (66, 12, 14, C['c']), (80, 11, 11, H('6b7fb8'))]
    for (cx, w, h, col) in cloths:
        ly = 12 + int(round(3 * math.sin(math.pi * (cx - 6) / 83.0)))
        for y in range(ly + 1, ly + 1 + h):
            sway = int(round(1.0 * math.sin(y * 0.6 + cx)))
            for x in range(cx, cx + w - 4):
                c = col
                if y == ly + 1:
                    c = tuple(max(0, v - 40) for v in col[:3]) + (255,)
                elif (x - cx) % 6 == 5:
                    c = tuple(max(0, v - 25) for v in col[:3]) + (255,)
                elif y == ly + h:
                    c = tuple(max(0, v - 30) for v in col[:3]) + (255,)
                sp.set(x + sway, y, c)
        sp.set(cx + 2, ly, BROWN[3])
        sp.set(cx + w - 6, ly, BROWN[3])
    sp.outline(OUTLINE)
    return sp.im


def kuebel(col):
    sp = Spr(32, 32)
    # Bluten
    cols = {'Rosa': (PINK, H('c4636b'), CREAM), 'Gelb': (YELLOW, ORANGE, CREAM)}[col]
    blob(sp, 16, 11, 11, 8, [GREEN[1], GREEN[2], GREEN[3], GREEN[4]], seed=3)
    for k in range(9):
        x, y = 8 + int(hsh(k, 1, 7) * 17), 5 + int(hsh(k, 2, 7) * 9)
        sp.rect(x, y, x + 1, y + 1, cols[k % 3])
        sp.set(x, y, YELLOW if k % 3 == 2 else cols[(k + 1) % 3])
    # Kuebel
    for y in range(17, 30):
        for x in range(7, 25):
            inset = 0 if y < 27 else 1
            if x < 7 + inset or x > 24 - inset:
                continue
            c = BROWN[2] if (x - 7) % 4 else BROWN[1]
            if x < 10:
                c = BROWN[3]
            if x > 21:
                c = BROWN[1]
            sp.set(x, y, c)
    sp.rect(7, 19, 24, 19, PURP[3])
    sp.rect(7, 26, 24, 26, PURP[3])
    sp.rect(7, 17, 24, 17, BROWN[4])
    sp.rect(8, 30, 23, 30, BROWN[0])
    sp.outline(OUTLINE)
    return sp.im


def talisman_pfosten():
    sp = Spr(32, 64)
    wood_post(sp, 14, 17, 12, 62)
    grass_foot(sp, 15, 62)
    sp.rect(7, 10, 24, 12, BROWN[2])
    sp.rect(7, 10, 24, 10, BROWN[3])
    sp.rect(7, 12, 24, 12, BROWN[1])
    sp.rect(15, 5, 16, 9, BROWN[2])
    sp.rect(14, 4, 17, 4, BROWN[3])
    # Faden und Talisman (Raute)
    for y in range(13, 18):
        sp.set(15, y, STONE[3])
    cx, cy = 15, 25
    for y in range(-8, 9):
        w = 8 - abs(y)
        for x in range(-w, w + 1):
            d = abs(x) + abs(y) * 1.0
            c = C['t']
            if d >= 7:
                c = C['d']
            elif d <= 2:
                c = C['T']
            elif x < 0 and y < 0:
                c = C['T'] if d <= 4 else C['t']
            sp.set(cx + x, cy + y, c)
    sp.set(cx, cy, C['T'])
    for (x, y) in ((cx - 10, cy - 3), (cx + 10, cy + 2), (cx - 8, cy + 8), (cx + 8, cy - 8), (cx, cy + 12)):
        sp.set(x, y, C['T'])
    sp.outline(OUTLINE)
    # Leuchtpunkte auf dem Umriss nicht ueberschreiben
    return sp.im


def ortsschild():
    sp = Spr(64, 64)
    wood_post(sp, 5, 8, 20, 62)
    wood_post(sp, 55, 58, 20, 62)
    grass_foot(sp, 7, 62)
    grass_foot(sp, 57, 62)
    for y in range(8, 32):
        for x in range(2, 62):
            c = BROWN[1]
            if y in (8, 9):
                c = BROWN[3]
            elif y == 31:
                c = BROWN[0]
            elif x in (2, 61):
                c = BROWN[2]
            sp.set(x, y, c)
    for (x, y) in ((5, 11), (58, 11), (5, 28), (58, 28)):
        sp.set(x, y, STONE[4])
    # Glocke links
    draw_icon(sp, 8, 14, 'Villa')
    s = 'DUSK BELL'
    text(sp, 22, 17, s, C['y'])
    text(sp, 22, 24, 'WELCOME'.replace('W', 'V').replace('C', 'C'), BROWN[4]) if False else None
    sp.outline(OUTLINE)
    return sp.im


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    items = {}
    for key in LABEL:
        for d in ('L', 'R'):
            items[f'Wegweiser_{key}_{d}'] = wegweiser(key, d)
    items['Kreuz_Schild'] = kreuz_schild()
    items['Gartenlicht'] = gartenlicht()
    items['Laterne_Doppel'] = laterne_doppel()
    for k in ('Kohl', 'Karotten', 'Kraeuter', 'Blumen', 'Kuerbis'):
        items['Beet_' + k] = beet(k)
    items['Waescheleine'] = waescheleine()
    items['Blumenkuebel_Rosa'] = kuebel('Rosa')
    items['Blumenkuebel_Gelb'] = kuebel('Gelb')
    items['Talisman_Pfosten'] = talisman_pfosten()
    items['Ortsschild'] = ortsschild()
    lines = []
    for n, im in items.items():
        im.save(os.path.join(outdir, n + '.png'))
        lines.append(f'{n} | {im.width}x{im.height}')
    open(os.path.join(outdir, '_Liste.txt'), 'w', encoding='utf-8').write('Dorf-Objekte (Pivot unten links, 32 px Raster)\n' + '\n'.join(lines) + '\n')
    return items


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else TILES + '/Dorf/Objekte'
    items = build(out)
    if len(sys.argv) > 2:
        preview(sys.argv[2], list(items.values()), scale=3, bg=(74, 122, 79, 255), maxw=1900)
    print(len(items), 'Objekte ->', out)
