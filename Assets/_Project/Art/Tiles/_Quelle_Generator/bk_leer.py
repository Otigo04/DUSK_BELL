"""Haus-Baukasten LEERES HAUS: verlassene Fassade und verstaubte Einrichtung. Wird von bk_build.py registriert.
Monster-Bibel: Die Hausfrau schlaeft in einem "leer stehenden Haus am Dorfrand, Tuer nie abgeschlossen". Geweckt bringt sie tagsueber Brot
zu Haushalten, die sie beobachtet hat. Das Haus muss leer, aber bewohnt wirken: verwittert, Spinnweben, Laken ueber den Moebeln - und
Spuren, dass doch jemand schlaeft (zerwuehltes Bett, Nest aus Decken, altes Brot auf dem Tisch).
  aussen   Tuer_Verwittert, Tuer_Verwittert_Angelehnt (Tuer nie abgeschlossen), Fenster_Laeden_Schief_Blau, Fenster_Zerbrochen,
           Spinnweben_Aussen_Links/Rechts
  innen    Spinnweben_Ecke_Links/Rechts, Laken_Sofa, Laken_Sessel, Stuhl_Umgekippt, Bett_Zerwuehlt, Nest_Decken, Tisch_Staub, Kerzenstumpf"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
from bk_lib import *
import bk_fassade as F
import bk_moebel as M
import bk_spalt as SP


# ====================================================================== Verfall
def weather(s, seed=1, moss=True):
    """Verwittern: ungleichmaessig abdunkeln, senkrechte Regenstreifen, Moos am Fuss, Rostspuren unter Eisenteilen."""
    for y in range(s.h):
        for x in range(s.w):
            c = s.get(x, y)
            if not c[3]:
                continue
            if hsh(x, y, seed) < 0.10:
                s.set(x, y, dk(c))
            elif hsh(x, y, seed + 7) < 0.04:
                s.set(x, y, lt(c))
    for x in range(s.w):                                       # Regenstreifen
        if hsh(x, 3, seed + 3) < 0.22:
            y0 = int(hsh(x, 5, seed) * s.h * 0.5)
            for y in range(y0, min(s.h, y0 + 6 + int(hsh(x, 9, seed) * 18))):
                c = s.get(x, y)
                if c[3] and c not in (OL1, OL2):
                    s.set(x, y, dk(c))
    if moss:
        for y in range(s.h - 9, s.h):
            for x in range(s.w):
                c = s.get(x, y)
                if c[3] and c not in (OL1, OL2) and hsh(x, y, seed + 11) < 0.22 + (y - (s.h - 9)) * 0.02:
                    s.set(x, y, FOR_M if hsh(x, y, seed + 13) < 0.6 else FOR_D)
    return s


# ====================================================================== AUSSEN
def tuer_verwittert():
    s = F.door('dunkel', 'zu')
    weather(s, 21)
    for y in range(30, 46):                                    # fehlendes Brett: dunkler Schlitz
        s.set(11, y, OL2)
        s.set(12, y, OL1 if y % 3 else OL2)
    for yb in (20, 55):                                        # Rostfahnen unter den Beschlaegen
        for k in range(1, 5):
            s.set(8 + (k % 2), yb + k, SK_S if k < 3 else EARTH)
    for (x, y) in ((17, 24), (19, 25), (15, 50), (18, 52)):    # abgeplatzter Anstrich
        s.set(x, y, WOOD_L)
        s.set(x + 1, y, WOOD_M)
    return s


def tuer_angelehnt():
    """Tuer nie abgeschlossen: steht einen Spalt breit offen, dunkel dahinter."""
    s = tuer_verwittert()
    for y in range(14, 64):
        for x in range(22, 26):
            s.set(x, y, [OL1, OL2, NB_D, NB_M if y % 5 else NB_D][x - 22])
        s.set(21, y, OL1)
        s.set(20, y, WOOD_D)
    s.rect(17, 40, 19, 41, ST_L)                               # Klinke wandert mit dem Blatt
    s.set(18, 40, YEL)
    return s


def fenster_laeden_schief():
    """Linker Laden haengt schief an einem Scharnier und ist unten abgebrochen, rechts fehlen Latten; Glas dunkel."""
    s = F.window('dunkel', 'blau')
    for y in range(3, 27):                                     # linken Laden entfernen
        for x in range(2, 8):
            s.set(x, y, (0, 0, 0, 0))
    b, hi, lo = F.SHUT['blau']
    for y in range(3, 21):                                     # schief haengender Rest (Scherung nach links)
        sh = int((y - 3) * 0.28)
        for x in range(2, 8):
            xx = x - sh
            c = b if x not in (2, 7) else lo
            if (y - 3) % 3 == 0:
                c = lo
            if x == 3:
                c = hi
            s.set(xx, y, c)
    for k in range(4):                                         # abgebrochene, ausgefranste Kante
        s.set(2 - 5 + k, 20 + (k % 2), OL1)
    for y in (9, 15):                                          # fehlende Latten rechts
        for x in range(25, 29):
            s.set(x, y, OL2)
            s.set(x, y + 1, NB_D)
    s.set(24, 7, ST_D)
    return s


def fenster_zerbrochen():
    """Ein Stein ist durch die Scheibe: feines Sprungnetz um den Einschlag, unten rechts fehlt Glas, Scherben auf der Bank."""
    s = F.window('dunkel', None)
    for (x1, y1) in ((9, 8), (21, 7), (10, 20), (19, 22)):    # kurze, duenne Risse vom Einschlag (13,13)
        n = max(abs(x1 - 13), abs(y1 - 13))
        for i in range(1, n + 1):
            x = 13 + (x1 - 13) * i // n
            y = 13 + (y1 - 13) * i // n
            if hsh(x, y, 4) < 0.8:
                s.set(x, y, ST_L if i % 3 else NB_L)
    for (x, y) in ((12, 12), (14, 12), (13, 14), (12, 14), (14, 14)):                  # Einschlagloch
        s.set(x, y, OL1)
    for y in range(17, 25):                                    # fehlende Scheibe unten rechts, gezackte Kante
        for x in range(18, 23):
            if x + (y - 17) % 3 >= 19:
                s.set(x, y, OL1)
    for x in (11, 14, 19):                                     # Scherben auf der Fensterbank
        s.set(x, 26, ST_L)
    s.set(16, 27, NB_L)
    return s


def web(side='links'):
    """Spinnwebe in einer Ecke (32x32): Radialfaeden, Bogenfaeden, zerrissen, einzelne Faeden haengen herab."""
    s = Spr(32, 32)
    import math
    angs = [8, 24, 40, 56, 72, 86]
    pts = {}
    for k, a in enumerate(angs):
        for r in range(2, 24):
            x = int(r * math.cos(math.radians(a)))
            y = int(r * math.sin(math.radians(a)))
            if hsh(k, r, 5) < 0.93:
                s.set(x, y, ST_L if r % 7 else MOON)
            pts[(k, r)] = (x, y)
    for r in (6, 12, 18):
        for k in range(len(angs) - 1):
            if hsh(k, r, 8) < 0.7:
                (x0, y0), (x1, y1) = pts[(k, r)], pts[(k + 1, r)]
                n = max(abs(x1 - x0), abs(y1 - y0), 1)
                for i in range(n + 1):
                    s.set(x0 + (x1 - x0) * i // n, y0 + (y1 - y0) * i // n + (1 if i % 2 else 0), ST_M)
    for (x, y, ln) in ((18, 15, 5), (7, 19, 4), (13, 20, 6)):
        for k in range(ln):
            s.set(x, y + k, ST_M if k < ln - 1 else MOON)
    if side == 'rechts':
        out = Spr(32, 32)
        for y in range(32):
            for x in range(32):
                c = s.get(x, y)
                if c[3]:
                    out.set(31 - x, y, c)
        return out
    return s


# ====================================================================== INNEN
def dust(s, x0, y0, x1, y1, dens=0.25, seed=3):
    """Staub: einzelne Pixel eine Stufe heller, oben dichter."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c = s.get(x, y)
            if c[3] and c not in (OL1, OL2) and hsh(x, y, seed) < dens * (1.2 - (y - y0) / max(1, y1 - y0)):
                s.set(x, y, lt(c))


SHEET = (CREAM, MOON, ST_L)            # Laken: Licht, Mitte, Schatten (kuehl)


def drape(w, h, hem_y, seed):
    """Laken ueber einem Moebel: weiche Kuppe, Falten, ausgefranster Saum."""
    s = Spr(w, 32)
    top = 32 - h - 2
    for y in range(top, hem_y + 1):
        t = (y - top) / max(1, hem_y - top)
        half = (w / 2.0 - 3) * (0.55 + 0.45 * math.sqrt(min(1.0, t * 1.4)))
        for x in range(int(w / 2 - half), int(w / 2 + half) + 1):
            u = (x - (w / 2 - half)) / max(1.0, 2 * half)
            c = SHEET[0] if (u < 0.28 and t < 0.6) else (SHEET[1] if u < 0.7 else SHEET[2])
            if t > 0.8 and (x + int(hsh(x, 1, seed) * 3)) % 4 == 0:
                c = SHEET[2]
            s.set(x, y, c)
    for k in range(3):                                         # Falten
        x = int(w * (0.3 + 0.2 * k) + hsh(k, 2, seed) * 3)
        for y in range(top + 4, hem_y - 1):
            if hsh(x, y, seed) < 0.9:
                s.set(x + int((y - top) * 0.04 * (k - 1)), y, ST_M)
    for x in range(int(w * 0.1), int(w * 0.9)):                # Saum mit Zipfeln
        if s.solid(x, hem_y) and hsh(x, 4, seed) < 0.4:
            s.set(x, hem_y + 1, ST_M)
    outline_obj(s)
    return s


import math  # noqa: E402


def laken_sessel():
    s = drape(32, 22, 27, 5)
    dust(s, 4, 8, 28, 26, 0.3)
    M.floor_shadow(s, 5, 26, 30)
    return s


def laken_sofa():
    s = drape(64, 20, 27, 9)
    dust(s, 4, 10, 60, 26, 0.3, 8)
    M.floor_shadow(s, 4, 59, 30)
    return s


def stuhl_umgekippt():
    s = Spr(32, 32)
    M.block(s, 9, 19, 12, 10, 24, M.WD)                        # Sitz kippt nach hinten (Seitenansicht)
    for y in (14, 22):                                         # Stuhlbeine ragen waagrecht heraus
        s.rect(19, y, 28, y + 1, OL1)
        hline(s, 20, 27, y, WOOD_M)
        hline(s, 20, 27, y + 1, WOOD_D)
    s.rect(3, 18, 9, 29, OL1)                                  # Lehne liegt am Boden
    s.rect(4, 19, 8, 28, WOOD_M)
    for x in (5, 7):
        vline(s, x, 20, 27, WOOD_D)
    hline(s, 4, 8, 19, WOOD_L)
    M.floor_shadow(s, 3, 28, 30)
    dust(s, 3, 12, 28, 29, 0.25)
    return s


def bett_zerwuehlt():
    s = M.bed('rot', 32)
    for y in range(27, 58):                                    # Decke zurueckgeschlagen und verdreht
        for x in range(3, 29):
            if hsh(x, y, 14) < 0.11:
                c = s.get(x, y)
                if c[3]:
                    s.set(x, y, dk(c) if hsh(x, y, 15) < 0.6 else lt(c))
    for k in range(5):                                         # grosse Faltenwuelste
        x0 = 4 + int(hsh(k, 1, 16) * 18)
        for i in range(10):
            s.set(x0 + i // 2, 30 + k * 5 + i % 3, SK_S)
            s.set(x0 + i // 2, 29 + k * 5 + i % 3, ROSE)
    s.rect(5, 15, 17, 23, OL1)                                 # Kissen verrutscht, mit Delle
    s.rect(6, 16, 16, 22, MOON)
    s.ellipse(11, 19, 3, 2, ST_L)
    for x in range(26, 31):                                    # Zipfel haengt ueber die Kante
        for y in range(46, 58 + (x % 2)):
            s.set(x, y, CREAM if y % 4 else ST_L)
    for y in range(46, 58):
        s.set(25, y, OL1)
    dust(s, 3, 13, 28, 57, 0.18, 17)
    return s


def nest_decken():
    """Schlafnest auf dem Boden: Ring aus alten Decken und Kissen, Mulde in der Mitte, ein Stueck rotes Tuch."""
    s = Spr(64, 32)
    cols = [SV_M, SV_D, SK_S, ST_D, SV_L]
    s.ellipse(32, 17, 28, 12, OL1)
    for k in range(34):                                        # Deckenwuelste
        a = k / 34.0 * 6.283
        cx, cy = 32 + math.cos(a) * 20, 17 + math.sin(a) * 8
        c = cols[int(hsh(k, 1, 19) * len(cols))]
        s.ellipse(cx, cy, 6 + hsh(k, 2, 19) * 3, 4 + hsh(k, 3, 19) * 2, OL1)
        s.ellipse(cx, cy, 5 + hsh(k, 2, 19) * 3, 3 + hsh(k, 3, 19) * 2, c)
        s.ellipse(cx - 1, cy - 1, 2, 1, lt(c))
    s.ellipse(32, 17, 15, 6, OL1)                              # Mulde
    s.ellipse(32, 17, 14, 5, OL2)
    s.ellipse(30, 16, 8, 3, SV_D)
    for x in range(22, 36):                                    # Abdruck eines Koerpers
        s.set(x, 16 + int(math.sin(x / 3.0)), SK_S)
    for (x, y) in ((28, 15), (37, 18), (42, 14), (20, 19)):    # Stroh
        s.set(x, y, SAND)
        s.set(x + 1, y + 1, SAND)
    s.rect(38, 13, 41, 15, RED_D)                              # rotes Tuch (Kopftuch?)
    s.set(41, 15, ROSE)
    M.floor_shadow(s, 6, 58, 30)
    dust(s, 6, 6, 58, 28, 0.15, 21)
    return s


def tisch_staub():
    s = M.table(64)
    for (x, c) in ((13, CREAM), (36, MOON)):                   # zwei Teller
        s.ellipse(x + 5, 12, 6, 2, OL1)
        s.ellipse(x + 5, 12, 5, 1.5, c)
    s.ellipse(18, 11, 4, 2, SAND)                              # altes Brot mit Schimmel
    s.set(16, 10, FOR_M)
    s.set(18, 10, GRASS_L)
    s.set(20, 11, FOR_M)
    s.set(19, 12, GRASS_L)
    s.rect(44, 8, 47, 12, OL1)                                 # umgekippter Becher
    s.rect(45, 9, 46, 11, ST_L)
    s.set(48, 12, ST_M)
    s.rect(28, 9, 30, 11, OL1)                                 # Kerzenstumpf mit Wachs
    s.rect(28, 10, 29, 11, CREAM)
    s.set(30, 12, SAND)
    dust(s, 3, 8, 60, 20, 0.30, 23)
    for x in range(8, 56, 7):                                  # Spinnfaden an der Tischkante
        if hsh(x, 1, 24) < 0.4:
            hline(s, x, x + 3, 19, ST_M)
    return s


def kerzenstumpf():
    s = Spr(32, 32)
    s.ellipse(16, 24, 9, 3, OL1)                               # Unterteller
    s.ellipse(16, 24, 8, 2, ST_L)
    s.ellipse(16, 23, 6, 1, ST_M)
    s.rect(13, 13, 18, 23, OL1)
    s.rect(14, 14, 17, 22, CREAM)
    vline(s, 14, 14, 22, MOON)
    vline(s, 17, 14, 22, SAND)
    for (x, y) in ((13, 18), (18, 20), (19, 23), (12, 22)):    # herabgelaufenes Wachs
        s.set(x, y, CREAM)
        s.set(x, y + 1, SAND)
    s.set(15, 12, OL1)                                          # kalter Docht
    s.set(16, 12, OL2)
    M.floor_shadow(s, 8, 24, 28)
    return s


# ====================================================================== Register
def register(R):
    A, Wd, MB = 'aussen_wand', 'innen_wand', 'innen_moebel'
    R.add('Tuer_Verwittert', tuer_verwittert(), A)
    R.add('Tuer_Verwittert_Angelehnt', tuer_angelehnt(), A)
    R.add('Fenster_Laeden_Schief_Blau', fenster_laeden_schief(), A)
    R.add('Fenster_Zerbrochen', fenster_zerbrochen(), A)
    R.add('Spinnweben_Aussen_Links', web('links'), A)
    R.add('Spinnweben_Aussen_Rechts', web('rechts'), A)
    R.add('Spinnweben_Ecke_Links', web('links'), Wd, fuss=0, solid=False)
    R.add('Spinnweben_Ecke_Rechts', web('rechts'), Wd, fuss=0, solid=False)
    R.add('Laken_Sofa', laken_sofa(), MB)
    R.add('Laken_Sessel', laken_sessel(), MB)
    R.add('Stuhl_Umgekippt', stuhl_umgekippt(), MB)
    R.add('Bett_Zerwuehlt', bett_zerwuehlt(), MB, fuss=2)
    R.add('Nest_Decken', nest_decken(), MB)
    R.add('Tisch_Staub', tisch_staub(), MB)
    R.add('Kerzenstumpf', kerzenstumpf(), MB)


if __name__ == '__main__':
    # Vorschau: python bk_leer.py -> Baukasten/Vorschau_LeeresHaus.png (5x)
    from PIL import Image
    R = Reg()
    register(R)
    names = ['Tuer_Verwittert', 'Tuer_Verwittert_Angelehnt', 'Fenster_Laeden_Schief_Blau', 'Fenster_Zerbrochen', 'Spinnweben_Aussen_Links',
             'Spinnweben_Aussen_Rechts', 'Laken_Sessel', 'Laken_Sofa', 'Stuhl_Umgekippt', 'Bett_Zerwuehlt', 'Nest_Decken', 'Tisch_Staub',
             'Kerzenstumpf']
    S, GAP = 5, 10
    ims = [R.obj[n][0].im.resize((R.obj[n][0].w * S, R.obj[n][0].h * S), Image.NEAREST) for n in names]
    row1, row2 = ims[:6], ims[6:]
    w = max(sum(i.width + GAP for i in r) for r in (row1, row2)) + GAP
    h = max(i.height for i in row1) + max(i.height for i in row2) + 3 * GAP
    sh = Image.new('RGBA', (w, h), (70, 60, 80, 255))
    y = GAP
    for r in (row1, row2):
        x = GAP
        for i in r:
            sh.paste(i, (x, y), i)
            x += i.width + GAP
        y += max(i.height for i in r) + GAP
    sh.save(BK + '/Vorschau_LeeresHaus.png')
    print('Vorschau_LeeresHaus.png', sh.size)
