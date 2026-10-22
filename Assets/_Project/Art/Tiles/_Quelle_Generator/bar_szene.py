"""Ilhans Bar - Szenen-Layout (Hauptgebaeude, aussen + innen).
Erzeugt Art/Tiles/Baukasten/Szene_IlhansBar.json (wird von Editor/IlhansBarBuilder.cs gelesen) und
Art/Tiles/Baukasten/Vorschau_IlhansBar.png. Gleiche Daten = gleiches Bild in Unity.
Aufruf:  python bar_szene.py   (vorher einmal python bk_build.py)

Tile-Referenzen:  BA:r:c / BI:r:c   Zellen aus Tileset_Bar_Aussen / Tileset_Bar_Innen
                  BKO:Name          Baukasten-Objekt (Anker links unten)
                  OBJ:Name          Objekt aus Art/Tiles/Objekte (Anker links unten), ANI:Name = animierte Variante
                  RT:Art:material   Baukasten-RuleTile (Boden, Innenwand, Krone), BKI:r:c Baukasten-Innen-Zelle
                  T:r:c             Terrain-Zelle, TRT:Name RuleTile aus TileAssets/RuleTiles
"""
import json, os
from PIL import Image
from bk_lib import *
import bk_build as BB
import bk_innen as BI_

TI = TILES
OUT = BK + '/Szene_IlhansBar.json'
INNEN_X = 60          # Innenraum liegt rechts neben dem Aussenbereich in derselben Szene

E = []                # (layer, ref, x, y, dx, dy)
LIGHTS = []           # (x, y, farbe, radius, intensitaet, nachtlicht)
DOORS = []            # (x, y, richtung) Klapptueren: Zelle des Durchgangs, richtung +1 = klappt nach rechts auf, -1 nach links
COLL = set()          # (layer_root, x, y)  Kollisionszellen
WARM, FIRE, CYAN = 'warm', 'feuer', 'talisman'


def put(layer, ref, x, y, dx=0, dy=0):
    E.append((layer, ref, x, y, dx, dy))


def piece(layer, sheet, sc, sr, w, h, x, y, solid=None):
    """Mehrzelliges Bar-Teil: Sheet-Zelle (sc, sr) links oben, Groesse w x h, Unity-Position (x, y) = links unten."""
    for i in range(w):
        for j in range(h):
            if _empty(sheet, sr + j, sc + i):
                continue          # leere Sheet-Zelle (z. B. obere Haelfte der Theke) hat kein Sprite
            put(layer, f'{sheet}:{sr + j}:{sc + i}', x + i, y + (h - 1 - j))
    if solid:
        for i in range(w):
            COLL.add((solid, x + i, y))       # nur die Fusszeile blockiert (hohe Teile ragen optisch nach oben)


def _empty(sheet, r, c):
    im = _sheet(TI + ('/Tileset_Bar_Aussen.png' if sheet == 'BA' else '/Tileset_Bar_Innen.png'))
    return im.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32)).getchannel('A').getbbox() is None


# ====================================================================== AUSSEN (Unity-Koordinaten, y nach oben)
AW, ROOF_TOP = 20, 6


def build_aussen():
    # Boden: Gras ueberall, Pflasterplatz vor dem Eingang
    for x in range(-8, AW + 8):
        for y in range(-10, ROOF_TOP + 4):
            put('a_boden', 'T:4:%d' % int(hsh(x + 50, y + 50, 7) * 8), x, y)
    for x in range(5, 15):
        for y in range(-10, -2):
            put('a_weg', 'TRT:RT_Pflaster', x, y)
    for x in range(-8, AW + 8):
        for y in (-9, -10):
            put('a_weg', 'TRT:RT_Pflaster', x, y)
    # Fassade (2 Zeilen), Fenster + Pendeltuer
    cols = {0: 1, AW - 1: 2}
    win = {2: 3, 4: 3, 6: 3, 13: 3, 15: 5, 17: 3}
    for x in range(AW):
        if x in (9, 10):
            continue
        sc = win.get(x, cols.get(x, 0))
        piece('a_wand', 'BA', sc, 1, 1, 2, x, 0)
        if sc == 3:
            LIGHTS.append((x + 0.5, 1.0, WARM, 2.4, 0.8, True))
    piece('a_wand', 'BA', 6, 1, 2, 2, 9, 0)                 # Pendeltuer zu
    LIGHTS.append((10.0, 0.9, WARM, 2.6, 0.7, True))
    # Dach: Traufe y2, Flaeche y3-5, First y6
    for x in range(AW):
        lmr = 0 if x == 0 else (2 if x == AW - 1 else 1)
        put('a_dach', 'BA:0:%d' % (6 + lmr), x, 2)
        for y in (3, 4, 5):
            put('a_dach', 'BA:0:%d' % (3 + lmr), x, y)
        put('a_dach', 'BA:0:%d' % (0 + lmr), x, ROOF_TOP)
    # Dach-Deko: Schild, Gauben, Schornsteine mit Rauch
    piece('a_deko', 'BA', 0, 3, 4, 1, 8, 4)                 # ILHANS BAR
    for x, lit in ((3, True), (6, False), (13, True), (16, True)):
        put('a_deko', 'BA:0:%d' % (12 if lit else 13), x, 4)
        if lit:
            LIGHTS.append((x + 0.5, 4.5, WARM, 1.8, 0.6, True))
    for x in (5, 15):
        piece('a_deko', 'BA', 15, 0, 1, 2, x, ROOF_TOP)
    # Fassaden-Deko
    put('a_deko', 'BA:3:11', 8, 1)                          # Wandlaternen neben der Tuer
    put('a_deko', 'BA:3:11', 11, 1)
    LIGHTS.append((8.5, 1.5, FIRE, 3.0, 0.9, True))
    LIGHTS.append((11.5, 1.5, FIRE, 3.0, 0.9, True))
    piece('a_deko', 'BA', 0, 4, 1, 2, 18, 0)                # Ausleger Krug
    piece('a_deko', 'BA', 1, 4, 1, 2, 1, 0)                 # Ausleger Glas
    put('a_deko', 'BA:3:9', 8, 0)                           # Schild OFFEN
    # Veranda
    for x in range(AW):
        put('a_veranda', 'BA:3:%d' % (13 if x == 0 else (15 if x == AW - 1 else 14)), x, -1)
    for i, x in enumerate(range(8, 12)):
        put('a_veranda', 'BA:5:%d' % (5 if i == 0 else (7 if i == 3 else 6)), x, -2)
    # Veranda-Moebel / Vorplatz (Kollision)
    piece('a_vorne', 'BA', 8, 4, 2, 1, 2, -1, 'a')          # Bank
    piece('a_vorne', 'BA', 8, 4, 2, 1, 15, -1, 'a')
    put('a_vorne', 'BA:4:14', 5, -1); COLL.add(('a', 5, -1))        # Stehfass mit Krug
    put('a_vorne', 'BA:4:15', 18, -1); COLL.add(('a', 18, -1))      # Faesserstapel
    put('a_vorne', 'BA:5:8', 13, -1); COLL.add(('a', 13, -1))       # Flaschenkiste
    put('a_vorne', 'BA:5:9', 0, -1); COLL.add(('a', 0, -1))         # Bierfass
    for x in (7, 12):
        piece('a_vorne', 'BA', 3, 4, 1, 2, x, -3, 'a')     # Laternenpfosten
        LIGHTS.append((x + 0.5, -1.6, FIRE, 3.5, 1.0, True))
    piece('a_vorne', 'BA', 2, 4, 1, 2, 14, -4, 'a')         # Kreidetafel TODAY
    piece('a_vorne', 'BA', 10, 5, 4, 1, 0, -4, 'a')         # Schild ILHANS BAR am Platz
    piece('a_vorne', 'BA', 10, 5, 4, 1, 16, -8, 'a')        # zweites Schild an der Strasse
    piece('a_vorne', 'BA', 10, 4, 2, 1, 22, -1, 'a')        # Anbindebalken
    piece('a_vorne', 'BA', 12, 4, 2, 1, 22, -3, 'a')        # Trog
    # Pflanzen + Brunnen
    for (n, x, y) in (('Busch_Gruen_A', -2, 0), ('Busch_Blueten_Rosa', -1, -1), ('Busch_Gruen_C', 21, 1),
                      ('Busch_Blueten_Weiss', 20, -1), ('Busch_Rund', -3, 3), ('Busch_Gruen_B', 23, 3),
                      ('Busch_Klein_A', 4, -3), ('Busch_Klein_B', 15, -3)):
        put('a_obj', f'ANI:{n}_Wind_v{int(hsh(x, y, 3) * 4)}|OBJ:{n}', x, y)
        COLL.add(('a', x, y))
    put('a_obj', 'ANI:Brunnen_Anim_v0|OBJ:Brunnen', 18, -7)
    for c in ((18, -7), (19, -7)):
        COLL.add(('a', c[0], c[1]))
    put('a_obj', 'ANI:Laterne_Anim_v1|OBJ:Laterne', 1, -6)
    LIGHTS.append((1.5, -5.2, FIRE, 4.0, 1.0, True))
    COLL.add(('a', 1, -6))


# ====================================================================== INNEN (ASCII, oben = Norden)
MAP = [
    "##################################",
    "#kkkkkkk#wwwwwwwwwwwwwwwww#hhhhhh#",
    "#kkkkkkk#wwwwwwwwwwwwwwwww#hhhhhh#",
    "#fffffff#:::::::::::::::::#pppppp#",
    "#fffffff::::::::::::::::::#pppppp#",
    "#fffffff#:::::::::::::::::#pppppp#",
    "#fffffff#.................#pppppp#",
    "#fffffff#.................#pppppp#",
    "#fffffff#.................#pppppp#",
    "#fffffff#..................pppppp#",
    "#########.................#pppppp#",
    "#wwwwwwww.................#pppppp#",
    "#wwwwwwww.................########",
    "#.........................#hhhhhh#",
    "#.........................#hhhhhh#",
    "#.........................#llllll#",
    "#.........................#llllll#",
    "#.........................#llllll#",
    "#..........................llllll#",
    "#.........................#llllll#",
    "#.........................#llllll#",
    "#################E################",
]
ROWS = len(MAP)
assert all(len(r) == 34 for r in MAP), [len(r) for r in MAP]
FLOOR = {'.': 'hall', ':': 'bar', 'f': 'kueche', 'p': 'hinter', 'l': 'lager', 'E': 'hall'}
WALLS = {'w': 'bar', 'k': 'kalk', 'h': 'holz'}


def U(col, row):
    """ASCII (Spalte, Zeile) -> Unity (x, y) inkl. Versatz des Innenraums."""
    return INNEN_X + col, ROWS - 1 - row


def ch(c, r):
    if 0 <= r < ROWS and 0 <= c < 34:
        return MAP[r][c]
    return ' '


def iput(layer, ref, col, row, dx=0, dy=0):
    x, y = U(col, row)
    put(layer, ref, x, y, dx, dy)


def ipiece(layer, sheet, sc, sr, w, h, col, row, solid=False):
    """Bar-Teil mit linker UNTERER Zelle bei ASCII (col, row)."""
    x, y = U(col, row)
    piece(layer, sheet, sc, sr, w, h, x, y, 'i' if solid else None)


def bko(layer, name, col, row, w=1, fuss=1, solid=True):
    """Baukasten-Objekt, Ankerzelle (links unten) bei ASCII (col, row)."""
    iput(layer, 'BKO:' + name, col, row)
    if solid:
        for i in range(w):
            for j in range(fuss):
                x, y = U(col + i, row - j)
                COLL.add(('i', x, y))


def ilight(col, row, kind, radius, inten, dx=0.5, dy=0.5):
    x, y = U(col, row)
    LIGHTS.append((x + dx, y + dy, kind, radius, inten, False))


def build_innen():
    # ---------------- Boden, Waende, Kronen
    for r in range(ROWS):
        for c in range(34):
            k = MAP[r][c]
            if k in FLOOR:
                kind = FLOOR[k]
                if kind == 'hall':
                    iput('i_boden', 'BI:0:%d' % (1 if hsh(c, r, 5) < 0.07 else 0), c, r)
                elif kind == 'bar':
                    iput('i_boden', 'BI:0:3', c, r)
                elif kind == 'kueche':
                    iput('i_boden', 'RT:Boden:fliesen_blau', c, r)
                elif kind == 'hinter':
                    iput('i_boden', 'RT:Boden:parkett', c, r)
                else:
                    iput('i_boden', 'RT:Boden:bohlen', c, r)
                # Schatten
                up, lf, rt = ch(c, r - 1), ch(c - 1, r), ch(c + 1, r)
                if up in WALLS:
                    nm = 'schatten_ecke_links' if lf == '#' else ('schatten_ecke_rechts' if rt == '#' else 'schatten_oben')
                    iput('i_schatten', 'BKI:13:%d' % BB.OVERLAYS.index(nm), c, r)
                elif lf == '#' and k != 'E':
                    iput('i_schatten', 'BKI:13:%d' % BB.OVERLAYS.index('schatten_links'), c, r)
                elif rt == '#' and k != 'E':
                    iput('i_schatten', 'BKI:13:%d' % BB.OVERLAYS.index('schatten_rechts'), c, r)
            elif k == '#':
                iput('i_krone', 'RT:Krone:holz', c, r)
                x, y = U(c, r)
                COLL.add(('i', x, y))
            elif k in ('k', 'h'):
                iput('i_wand', 'RT:Innenwand:' + WALLS[k], c, r)
                if ch(c, r + 1) not in ('k', 'h'):
                    x, y = U(c, r)
                    COLL.add(('i', x, y))
    iput('i_schatten', 'BKI:13:%d' % BB.OVERLAYS.index('schwelle'), 17, 21)
    for (c, r, d) in ((8, 4, -1), (26, 9, 1), (26, 18, 1)):   # Klapptueren (oeffnen nach innen in Kueche/Hinterzimmer/Lager)
        DOORS.append(U(c, r) + (d,))
    for (c, r) in ((8, 4), (26, 9), (26, 18)):                # Seitentueren: Rahmen auf den Kronen ober-/unterhalb
        iput('i_rahmen', 'BKO:Tuerrahmen_SeiteOben', c, r - 1)
        iput('i_rahmen', 'BKO:Tuerrahmen_SeiteUnten', c, r + 1)
        iput('i_schatten', 'BKI:13:%d' % BB.OVERLAYS.index('schwelle'), c, r)
    iput('i_rahmen', 'BKO:Tuerrahmen_UntenLinks', 16, 21)    # Ausgang
    iput('i_rahmen', 'BKO:Tuerrahmen_UntenRechts', 18, 21)
    iput('i_bodendeko', 'BI:0:7', 17, 20)                   # Fussmatte
    # ---------------- Schankraum: Rueckwand mit Spirituosen
    back = [(9, 14, 1, 1, 2), (10, 0, 3, 2, 2), (12, 2, 3, 2, 2), (14, 0, 1, 1, 2), (15, 0, 1, 1, 2), (16, 0, 1, 1, 2),
            (17, 0, 1, 1, 2), (18, 0, 1, 1, 2), (19, 0, 1, 1, 2), (20, 4, 3, 2, 2), (22, 6, 3, 2, 2), (24, 0, 1, 1, 2),
            (25, 15, 1, 1, 2)]
    for col, sc, sr, w, h in back:
        ipiece('i_wand', 'BI', sc, sr, w, h, col, 2)
    for c in range(9, 26):
        x, y = U(c, 2)
        COLL.add(('i', x, y))
    ipiece('i_wanddeko', 'BI', 6, 10, 4, 1, 15, 1)          # Schild ILHANS BAR ueber der Theke
    ilight(16, 1, WARM, 3.0, 0.8, 1.0, 0.5)
    ipiece('i_wanddeko', 'BI', 10, 3, 2, 1, 16, 2)          # Glashalter
    iput('i_wanddeko', 'BI:10:4', 14, 1)                    # Plakat NO CREDIT
    iput('i_wanddeko', 'BI:3:15', 19, 1)                    # Kalender
    # Linke Wand des Schankraums (unter der Kueche)
    for c in range(1, 9):
        sc = 14 if c == 1 else (15 if c == 8 else 0)
        ipiece('i_wand', 'BI', sc, 1, 1, 2, c, 12)
        x, y = U(c, 12)
        COLL.add(('i', x, y))
    ipiece('i_wanddeko', 'BI', 0, 10, 4, 1, 5, 11)          # Preistafel
    iput('i_wanddeko', 'BI:3:12', 1, 11)                    # Dartscheibe
    iput('i_wanddeko', 'BI:3:14', 2, 11)                    # Wanduhr
    # ---------------- Theke (Zeilen 5-6) mit Aufbauten
    counter = [1, 3, 4, 5, 0, 6, 7, 9, 5, 8, 0, 12, 13, 14, 2]
    for i, sc in enumerate(counter):
        ipiece('i_moebel', 'BI', sc, 5, 1, 2, 10 + i, 6, solid=True)
    ilight(16, 5, WARM, 2.2, 0.7, 0.5, 0.2)                 # Kerze auf der Theke
    for c in range(11, 25, 2):
        iput('i_moebel', 'BI:5:15', c, 7)                   # Barhocker
    # ---------------- Tische mit Stuehlen
    def round_table(c, r, gedeckt=True):
        iput('i_moebel', 'BI:7:%d' % (1 if gedeckt else 0), c, r)
        x, y = U(c, r)
        COLL.add(('i', x, y))
        iput('i_moebel', 'BI:7:8', c - 1, r, 9, 0)          # Stuhl links
        iput('i_moebel', 'BI:7:9', c + 1, r, -9, 0)         # Stuhl rechts
        iput('i_moebel', 'BI:7:6', c, r - 1, 0, -10)        # Stuhl hinter dem Tisch (Sitz zum Betrachter)
        iput('i_moebel', 'BI:7:7', c, r + 1, 0, 8)          # Stuhl vor dem Tisch (Lehne zum Betrachter)
    for c in (12, 16, 20):
        round_table(c, 10, c != 16)
        round_table(c, 15, c == 16)
    # Sitznischen links (je Bank, Tisch, Bank)
    for c in (1, 5):
        for r0 in (15, 18):
            ipiece('i_moebel', 'BI', 10, 7, 2, 1, c, r0, solid=True)
            ipiece('i_moebel', 'BI', 2, 7, 2, 1, c, r0 + 1, solid=True)
            ipiece('i_moebel', 'BI', 10, 7, 2, 1, c, r0 + 2, solid=True)
    bko('i_obj', 'Kamin_Stein', 3, 13, 2)
    ilight(3, 13, FIRE, 5.0, 1.1, 1.0, 0.8)
    iput('i_moebel', 'BI:7:15', 5, 13); COLL.add(('i',) + U(5, 13))   # Holzstapel
    iput('i_moebel', 'BI:7:12', 9, 12)                      # Spucknapf
    # Versammlungstafel rechts unten
    for c in (21, 23):
        bko('i_obj', 'Tisch_Lang_Decke', c, 18, 2)
        for k in range(2):
            iput('i_moebel', 'BI:7:6', c + k, 17, 0, -10)
            iput('i_moebel', 'BI:7:7', c + k, 19, 0, 8)
    ipiece('i_moebel', 'BI', 0, 8, 2, 2, 24, 14, solid=True)   # Klavier
    ipiece('i_moebel', 'BI', 3, 8, 1, 2, 15, 20, solid=True)   # Garderobe
    bko('i_obj', 'Topfpflanze_Gross', 25, 11)
    iput('i_moebel', 'BI:7:13', 25, 20)                     # Besen + Eimer
    # Kronleuchter ueber den Tischen (haengen von der Decke)
    for c in (12, 16, 20):
        for r in (8, 13):
            ipiece('i_decke', 'BI', 4, 8, 1, 2, c, r)
            ilight(c, r, WARM, 5.5, 1.0, 0.5, 0.3)
    # Zusaetzliche Lichter: dritte Reihe Kronleuchter, Laternen ueber den Nischen und der Theke, Kerzen auf allen Tischen
    for c in (12, 20):
        ipiece('i_decke', 'BI', 4, 8, 1, 2, c, 18)
        ilight(c, 18, WARM, 5.5, 1.0, 0.5, 0.3)
    for (c, r) in ((3, 16), (3, 19), (7, 15), (7, 19)):
        iput('i_decke', 'BI:8:6', c, r)
        ilight(c, r, FIRE, 4.5, 1.0)
    for c in (12, 17, 22):
        iput('i_decke', 'BI:8:6', c, 3)
        ilight(c, 3, FIRE, 4.5, 1.0)
    for c in (12, 16, 20):
        for r in (10, 15):
            ilight(c, r, WARM, 2.2, 0.6)
    for c in (21, 23):
        ilight(c, 18, WARM, 2.5, 0.7, 1.0)
    for c in (9, 25):
        iput('i_wanddeko', 'BI:8:5', c, 1)                  # Wandleuchten an den Enden der Rueckwand
        ilight(c, 1, WARM, 3.5, 0.9)
    for (c, r) in ((25, 13), (9, 17), (25, 17), (1, 13)):
        ilight(c, r, WARM, 3.5, 0.6)                        # weiche Fuelllichter in den Ecken
    # Kueche, Hinterzimmer, Lager
    iput('i_decke', 'BI:8:6', 4, 5); ilight(4, 5, FIRE, 4.5, 1.0)
    iput('i_decke', 'BI:8:6', 4, 8); ilight(4, 8, FIRE, 4.0, 0.9)
    iput('i_decke', 'BI:8:6', 30, 4); ilight(30, 4, FIRE, 4.0, 0.9)
    iput('i_decke', 'BI:8:6', 28, 10); ilight(28, 10, FIRE, 4.0, 0.9)
    iput('i_decke', 'BI:8:6', 29, 16); ilight(29, 16, FIRE, 4.0, 0.9)
    iput('i_decke', 'BI:8:6', 29, 19); ilight(29, 19, FIRE, 4.0, 0.9)

    # Kleinkram am Boden
    for (sc, c, r) in ((12, 14, 12), (14, 18, 8), (15, 22, 12), (13, 8, 14), (15, 10, 17)):
        iput('i_bodendeko', 'BI:0:%d' % sc, c, r)
    # ---------------- Kueche
    bko('i_obj', 'Herd_Eisen', 1, 3, 2)
    ilight(1, 3, FIRE, 4.0, 1.0, 1.0, 0.6)
    bko('i_obj', 'Kuechenschrank', 3, 3)
    bko('i_obj', 'Backofen', 5, 3, 2)
    ilight(5, 3, FIRE, 4.0, 1.0, 1.0, 0.6)
    bko('i_obj', 'Fass_Wasser', 7, 3)
    bko('i_obj', 'Arbeitstisch_Brot', 3, 6, 2)
    bko('i_obj', 'Tisch_Lang', 5, 6, 2)
    bko('i_obj', 'Spuelstein', 1, 9, 2)
    bko('i_obj', 'Sack_Mehl', 5, 9)
    bko('i_obj', 'Sack_Kartoffeln', 6, 9)
    bko('i_obj', 'Fass_Korn', 7, 9)
    bko('i_wandobj', 'Wand_Pfannen', 3, 1, solid=False)
    bko('i_wandobj', 'Wand_Kraeuter', 4, 1, solid=False)
    bko('i_wandobj', 'Fenster_Innen_Nacht', 7, 2, solid=False)
    # ---------------- Hinterzimmer (Versammlung, Poker)
    bko('i_wandobj', 'Wand_BildPortrait', 28, 1, solid=False)
    bko('i_wandobj', 'Wand_Kerzenleuchter', 29, 1, solid=False)
    ilight(29, 1, WARM, 2.4, 0.7)
    bko('i_wandobj', 'Fenster_Innen_Vorhang', 30, 2, solid=False)
    bko('i_wandobj', 'Wand_Talisman', 31, 1, solid=False)
    ilight(31, 1, CYAN, 1.6, 0.8)
    bko('i_wandobj', 'Wand_Uhr', 32, 1, solid=False)
    bko('i_obj', 'Buecherregal_Schmal', 27, 3)
    bko('i_obj', 'Sofa_Rot', 28, 3, 2)
    bko('i_obj', 'Sessel_Rot', 30, 3)
    ipiece('i_moebel', 'BI', 2, 8, 1, 2, 32, 4, solid=True)    # Kanonenofen
    ilight(32, 4, FIRE, 3.0, 0.9)
    bko('i_teppich', 'Teppich_Rot_Gross', 27, 7, solid=False)
    ipiece('i_moebel', 'BI', 4, 7, 2, 1, 28, 6, solid=True)    # Pokertisch
    iput('i_moebel', 'BI:7:8', 27, 6, 9, 0)
    iput('i_moebel', 'BI:7:9', 30, 6, -9, 0)
    for c in (28, 29):
        iput('i_moebel', 'BI:7:6', c, 5, 0, -10)
        iput('i_moebel', 'BI:7:7', c, 7, 0, 8)
    bko('i_obj', 'Tisch_Lang_Decke', 29, 10, 2)
    for c in (29, 30):
        iput('i_moebel', 'BI:7:6', c, 9, 0, -10)
        iput('i_moebel', 'BI:7:7', c, 11, 0, 8)
    bko('i_obj', 'Kommode', 31, 8, 2)
    ipiece('i_decke', 'BI', 6, 8, 1, 1, 29, 8)              # Haengelaterne
    ilight(29, 8, FIRE, 3.5, 0.9)
    # ---------------- Lager
    ipiece('i_wanddeko', 'BI', 8, 3, 2, 2, 28, 14)          # Fassregal an der Wand
    iput('i_wanddeko', 'BI:8:7', 31, 13)                    # Wandlaterne
    ilight(31, 13, FIRE, 3.0, 0.8)
    ipiece('i_bodendeko', 'BI', 8, 8, 2, 1, 29, 18)         # Kellerluke
    for (n, c, r) in (('Holzkorb', 27, 15), ('Kistenstapel', 31, 15), ('Fass_Korn', 32, 15), ('Fass_Aepfel', 32, 17),
                      ('Sack_Kartoffeln', 27, 20), ('Kistenstapel', 31, 20), ('Fass_Wasser', 32, 20), ('Sack_Mehl', 28, 20)):
        bko('i_obj', n, c, r)


# ====================================================================== Pruefung
def check():
    err = []
    # 1) Erreichbarkeit innen: alle Bodenfelder vom Eingang aus (Kollision = blockiert)
    blocked = {(x, y) for (l, x, y) in COLL if l == 'i'}
    floor = set()
    for r in range(ROWS):
        for c in range(34):
            if MAP[r][c] in FLOOR:
                floor.add(U(c, r))
    start = U(17, 21)
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n in floor and n not in blocked and n not in seen:
                seen.add(n)
                todo.append(n)
    free = floor - blocked
    lost = free - seen
    if lost:
        err.append('Innen: %d Bodenfelder nicht erreichbar: %s' % (len(lost), sorted(lost)[:8]))
    for need, nm in ((U(17, 20), 'Eingang'), (U(8, 4), 'Kuechentuer'), (U(26, 9), 'Tuer Hinterzimmer'), (U(26, 18), 'Tuer Lager'),
                     (U(9, 5), 'Thekendurchgang links'), (U(25, 5), 'Thekendurchgang rechts')):
        if need not in seen:
            err.append('Innen: %s nicht erreichbar %s' % (nm, need))
    # 2) Moebel nicht auf Wand/Krone
    for (l, ref, x, y, dx, dy) in E:
        if l in ('i_moebel', 'i_obj'):
            c, r = x - INNEN_X, ROWS - 1 - y
            if ch(c, r) not in FLOOR:
                err.append(f'Innen: {ref} bei ASCII ({c},{r}) steht nicht auf Boden')
    # 3) keine doppelt belegten Zellen je Ebene (Ausnahme: Stuehle mit Versatz)
    seenc = {}
    for (l, ref, x, y, dx, dy) in E:
        if l in ('a_boden', 'a_weg', 'i_boden', 'i_schatten'):
            continue
        k = (l, x, y)
        if k in seenc:
            err.append(f'{l}: {ref} und {seenc[k]} auf derselben Zelle ({x},{y})')
        seenc[k] = ref
    # 4) Aussen: Weg vom Platz zur Tuer frei
    ablk = {(x, y) for (l, x, y) in COLL if l == 'a'}
    for c in ((9, -1), (10, -1), (9, -2), (10, -2), (9, -5), (10, -5)):
        if c in ablk:
            err.append(f'Aussen: Zugang zur Tuer blockiert bei {c}')
    return err


# ====================================================================== Vorschau (Python-Render)
_cache = {}


def img(ref):
    if ref in _cache:
        return _cache[ref]
    ref0 = ref.split('|')[-1] if ref.startswith('ANI:') else ref
    p = ref0.split(':')
    if p[0] in ('BA', 'BI'):
        sh = _sheet(TI + ('/Tileset_Bar_Aussen.png' if p[0] == 'BA' else '/Tileset_Bar_Innen.png'))
        r, c = int(p[1]), int(p[2])
        im = sh.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
    elif p[0] == 'BKI':
        sh = _sheet(BK + '/Tileset_BK_Innen.png')
        r, c = int(p[1]), int(p[2])
        im = sh.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
    elif p[0] == 'T':
        sh = _sheet(TI + '/Tileset_Terrain.png')
        r, c = int(p[1]), int(p[2])
        im = sh.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32))
    elif p[0] == 'BKO':
        im = Image.open(BK + '/Objekte/' + p[1] + '.png').convert('RGBA')
    elif p[0] == 'OBJ':
        im = Image.open(TI + '/Objekte/' + p[1] + '.png').convert('RGBA')
    else:
        raise ValueError(ref)
    _cache[ref] = im
    return im


def _sheet(path):
    if path not in _cache:
        _cache[path] = Image.open(path).convert('RGBA')
    return _cache[path]


ORDER = ['a_boden', 'a_weg', 'a_veranda', 'a_wand', 'a_dach', 'a_deko', 'a_vorne', 'a_obj',
         'i_boden', 'i_schatten', 'i_bodendeko', 'i_teppich', 'i_wand', 'i_wanddeko', 'i_wandobj', 'i_moebel', 'i_obj',
         'i_decke', 'i_krone', 'i_rahmen']


def render(x0, y0, x1, y1, layers, TS, bg):
    W, H = (x1 - x0 + 1) * 32, (y1 - y0 + 1) * 32
    out = Image.new('RGBA', (W, H), bg)
    # RuleTiles vorab je Ebene sammeln
    rt_cells = {}
    for (l, ref, x, y, dx, dy) in E:
        if l in layers and (ref.startswith('RT:') or ref.startswith('TRT:')):
            rt_cells.setdefault((l, ref), set()).add((x, y))

    def blit(im, x, y, dx=0, dy=0):
        px = (x - x0) * 32 + dx
        py = (y1 - y + 1) * 32 - im.height - dy
        tmp = Image.new('RGBA', out.size, (0, 0, 0, 0))
        tmp.paste(im, (px, py))
        out.alpha_composite(tmp)

    terr = _sheet(TI + '/Tileset_Terrain.png')
    for l in ORDER:
        if l not in layers:
            continue
        items = [e for e in E if e[0] == l]
        if l in ('a_vorne', 'a_obj', 'i_moebel', 'i_obj'):
            items.sort(key=lambda e: -e[3])
        for (l_, ref, x, y, dx, dy) in items:
            if ref.startswith('RT:'):
                _, kind, mat = ref.split(':')
                cells = rt_cells[(l, ref)]
                if kind == 'Boden':
                    t = TS['boden_' + mat][BB.fill_pick(x, y)]
                elif kind == 'Innenwand':
                    m = BB.mask_at(cells, x, y)
                    t = TS['iwand_' + mat][m if m != 15 else 15]
                else:
                    m = BB.mask_at(cells, x, y)
                    t = TS['krone_' + mat][m] if m != 15 else TS['krone_' + mat][_inner(cells, x, y)]
                blit(t.im, x, y)
            elif ref.startswith('TRT:'):
                cells = rt_cells[(l, ref)]
                m = BB.mask_at(cells, x, y)
                c = m
                if m == 15:
                    c = _inner(cells, x, y)
                blit(terr.crop((c * 32, 32, c * 32 + 32, 64)), x, y)
            else:
                blit(img(ref), x, y, dx, dy)
    return out


def _inner(cells, x, y):
    if (x + 1, y + 1) not in cells: return 16
    if (x + 1, y - 1) not in cells: return 17
    if (x - 1, y - 1) not in cells: return 18
    if (x - 1, y + 1) not in cells: return 19
    return 15


if __name__ == '__main__':
    build_aussen()
    build_innen()
    errs = check()
    data = {
        'innenX': INNEN_X,
        'eintraege': [{'l': l, 'r': r, 'x': x, 'y': y, 'dx': dx, 'dy': dy} for (l, r, x, y, dx, dy) in E],
        'lichter': [{'x': x, 'y': y, 'k': k, 'rad': rad, 'i': i, 'n': n} for (x, y, k, rad, i, n) in LIGHTS],
        'kollision': [{'l': l, 'x': x, 'y': y} for (l, x, y) in sorted(COLL)],
        'tueren': [{'x': x, 'y': y, 'd': d} for (x, y, d) in DOORS],
        'aussenBreite': AW, 'aussenWandHoehe': 2, 'aussenTuerX': 10.0, 'aussenSpawnX': 10.0, 'aussenSpawnY': -1.4,
        'innenAusgangX': INNEN_X + 17.5, 'innenSpawnX': INNEN_X + 17.5, 'innenSpawnY': 1.6, 'innenBreite': 34, 'innenHoehe': ROWS,
    }
    json.dump(data, open(OUT, 'w', encoding='utf-8', newline='\n'))
    _, SI = BB.sheet_innen()
    a = render(-8, -10, AW + 7, ROOF_TOP + 3, [l for l in ORDER if l.startswith('a_')], SI, NB_D)
    i = render(INNEN_X, 0, INNEN_X + 33, ROWS - 1, [l for l in ORDER if l.startswith('i_')], SI, OL1)
    sh = Image.new('RGBA', (a.width + i.width + 32, max(a.height, i.height)), OL1)
    sh.paste(a, (0, 0))
    sh.paste(i, (a.width + 32, 0))
    sh.save(BK + '/Vorschau_IlhansBar.png')
    print('Eintraege: %d, Lichter: %d, Kollision: %d' % (len(E), len(LIGHTS), len(COLL)))
    if errs:
        print('FEHLER:\n' + '\n'.join(errs))
        raise SystemExit(1)
    print('Pruefung ok')
