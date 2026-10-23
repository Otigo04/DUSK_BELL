"""Haus-Baukasten INNEN-SONDERSTUECKE fuer Revier und Aerztehaus. Wird von bk_build.py registriert.
(Backofen und Esse gab es schon: Baeckerei/Schmiede. Hier steht, was in den Dorfhaeusern laut Docs fehlte.)
Quellen:
  Revier (Ink "Sheriff Bulut: Erste Begegnung"): "village map on the wall, a shelf of old files, a handwritten list of names beside the window";
         Revier hat laut Dialogue Bible einen Talisman (Schrein/Wand vorhanden). Zelle: ein Dorf-Revier haelt Leute fest -> Zellengitter, -tuer, Pritsche.
  Aerztehaus (Doctor Veronica): "Ihr Schluesselbund oeffnet die Praxis und den Medikamentenschrank", "fuehrt heimlich Buch ueber alle Toten"
         -> Behandlungsliege (OP-Liege), Instrumententisch, Paravent, Anatomietafel, Pult mit dem Totenbuch.
  Revier   Zellengitter_Gerade, Zellentuer_Zu, Zellentuer_Offen, Zellenpritsche, Zelleneimer, Aktenregal, Wand_Dorfkarte, Wand_Namensliste
  Praxis   Behandlungsliege, Instrumententisch, Paravent, Wand_Anatomietafel, Pult_Totenbuch
3/4-Ansicht von vorn, Licht oben links, Anker links unten; Gitter sind durchsichtig (Luecken transparent), Teile mit Fuss-Zeilen sind solide."""
from bk_lib import *
import bk_moebel as M

WD = M.WD


# ====================================================================== Revier: Zelle
def bar(s, x, y0, y1):
    """Eisenstab, 2 px dick plus Outline: Licht links, Schatten rechts, vereinzelt Rost."""
    s.rect(x, y0, x + 3, y1, OL1)
    vline(s, x + 1, y0, y1, ST_L)
    vline(s, x + 2, y0, y1, ST_D)
    for y in range(y0 + 1, y1):
        if hsh(x, y, 7) < 0.07:
            s.set(x + 1, y, SK_S)


def rail(s, y0, y1, x0=0, x1=31):
    s.rect(x0, y0, x1, y1, OL1)
    s.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, ST_M)
    hline(s, x0 + 1, x1 - 1, y0 + 1, ST_L)
    hline(s, x0 + 1, x1 - 1, y1 - 1, ST_D)
    for x in range(x0 + 3, x1 - 2, 8):
        s.set(x, (y0 + y1) // 2, ST_L)                        # Nieten


def zellengitter(kind):
    """32x64: oben und unten Querbalken, senkrechte Staebe mit Luecken. kind: gerade | tuer_zu | tuer_offen"""
    s = Spr(32, 64)
    rail(s, 4, 9)
    rail(s, 56, 60)
    if kind == 'gerade':
        for x in (2, 9, 16, 23):
            bar(s, x, 10, 55)
        rail(s, 30, 32)
    elif kind == 'tuer_zu':
        for x in (0, 28):                                      # Pfosten
            s.rect(x, 10, x + 3, 55, OL1)
            s.rect(x + 1, 11, x + 2, 54, ST_M)
            vline(s, x + 1, 11, 54, ST_L)
        for y in (14, 44):                                     # Scharniere links
            s.rect(4, y, 7, y + 5, OL1)
            s.rect(5, y + 1, 6, y + 4, ST_D)
        for x in (8, 14, 20):
            bar(s, x, 10, 55)
        rail(s, 30, 32, 4, 27)
        box(s, 22, 33, 28, 42, ST_D, hi=ST_L, lo=OL2)          # Schlosskasten
        s.rect(24, 36, 25, 39, OL1)                            # Schluesselloch
        s.set(24, 40, OL1)
        s.set(26, 35, YEL)                                     # Messing am Schloss
    else:                                                      # offen: Fluegel zur Seite geschwenkt (verkuerzt), Durchgang frei
        for x in (0, 28):
            s.rect(x, 10, x + 3, 55, OL1)
            s.rect(x + 1, 11, x + 2, 54, ST_M)
            vline(s, x + 1, 11, 54, ST_L)
        for x in (4, 7, 10):                                   # Tuerfluegel von der Seite: Staebe dicht
            bar(s, x, 12, 53)
        for y in (14, 44):
            s.rect(4, y, 12, y + 2, OL1)
            hline(s, 5, 11, y + 1, ST_D)
    M.floor_shadow(s, 2, 29, 62)
    return s


def zellenpritsche():
    s = Spr(64, 32)
    M.block(s, 2, 61, 10, 9, 22, WD, top=(SAND, CREAM, WOOD_L))
    M.legs(s, (4, 56), 23, 29, WD)
    for x in range(5, 60, 3):                                  # Stroh
        if hsh(x, 1, 11) < 0.6:
            s.set(x, 12 + int(hsh(x, 2, 11) * 6), WOOD_L)
    s.rect(6, 12, 17, 17, OL1)                                 # Kissen
    s.rect(7, 13, 16, 16, MOON)
    hline(s, 7, 16, 16, ST_L)
    for x in range(24, 60):                                    # graue Decke mit Faltenwurf
        for y in range(11, 19):
            c = ST_L if y < 16 else ST_M
            if y == 11:
                c = MOON
            s.set(x, y, c)
    vline(s, 24, 11, 18, OL1)
    for x in range(26, 59, 6):
        vline(s, x, 12, 17, ST_M)
    for x in range(25, 60, 2):                                 # Decke haengt vorne herab
        s.set(x, 19, ST_M if x % 4 else ST_L)
    M.floor_shadow(s, 3, 60, 30)
    return s


def zelleneimer():
    s = Spr(32, 32)
    for y in range(13, 27):
        w = 7 + (y - 13) // 5
        for x in range(16 - w, 16 + w):
            u = (x - (16 - w)) / (2.0 * w)
            s.set(x, y, ST_L if u < 0.25 else (ST_M if u < 0.7 else ST_D))
    s.ellipse(16, 13, 8, 2.5, OL1)
    s.ellipse(16, 13, 7, 1.8, OL2)
    for y in (17, 22):                                         # Reifen
        hline(s, 9, 23, y, ST_M)
    s.line(8, 14, 12, 7, OL1)                                  # Henkel
    s.line(12, 7, 20, 7, OL1)
    s.line(20, 7, 24, 14, OL1)
    outline_obj(s)
    M.floor_shadow(s, 8, 24, 28)
    return s


def aktenregal():
    """Regal voller alter Akten: Ordner mit Etiketten, liegende Stapel (Ink: 'a shelf of old files')."""
    def fill(s, x0, x1, yb, r):
        x = x0
        i = 0
        while x + 3 <= x1:
            w = 4 + int(hsh(i, r, 21) * 3)
            c = [ST_L, WOOD_M, SAND, ST_M, WOOD_L][int(hsh(i, r, 22) * 5)]
            h = 9 - int(hsh(i, r, 23) * 3)
            s.rect(x, yb - h + 1, x + w - 1, yb, OL1)
            s.rect(x + 1, yb - h + 2, x + w - 2, yb - 1, c)
            vline(s, x + 1, yb - h + 2, yb - 1, lt(c))
            s.rect(x + 1, yb - h + 4, x + w - 2, yb - h + 5, CREAM)       # Etikett
            x += w
            i += 1
            if hsh(i, r, 24) < 0.18:
                x += 1
        if r == 1:                                                         # liegender Aktenstapel
            s.rect(x1 - 12, yb - 3, x1 - 2, yb, OL1)
            s.rect(x1 - 11, yb - 2, x1 - 3, yb - 1, CREAM)
            hline(s, x1 - 11, x1 - 3, yb - 2, MOON)
    return M.shelf_unit(64, 64, 4, fill, M.WDD, 41)


def wand_dorfkarte():
    s = Spr(64, 32)
    s.rect(3, 3, 60, 28, OL1)
    s.rect(4, 4, 59, 27, SAND)
    hline(s, 4, 59, 4, CREAM)
    for x in range(4, 60):
        for y in range(4, 28):
            if hsh(x, y, 31) < 0.06:
                s.set(x, y, WOOD_L)
    for x in range(8, 24):                                     # Wald oben links
        for y in range(6, 12):
            if hsh(x, y, 32) < 0.55:
                s.set(x, y, FOR_M if hsh(x, y, 33) < 0.5 else FOR_D)
    for y in range(4, 28):                                     # Strasse nord-sued
        x = 31 + int(2 * math.sin(y / 4.0))
        s.set(x, y, WOOD_D)
        s.set(x + 1, y, WOOD_D)
    for x in range(10, 56):                                    # Querweg
        y = 17 + int(1.5 * math.sin(x / 5.0))
        s.set(x, y, WOOD_D)
    for (x, y, c) in ((24, 11, RED_D), (38, 9, ST_M), (26, 21, WOOD_D), (40, 14, RED_D), (46, 20, WOOD_D), (20, 15, ST_M), (44, 8, WOOD_D), (36, 23, RED_D)):
        s.rect(x, y, x + 3, y + 2, OL2)                       # Haeuser
        s.rect(x, y, x + 3, y, c)
        s.rect(x + 1, y + 1, x + 2, y + 2, CREAM)
    for x in (12, 15, 18):                                     # Friedhof, Kreuze unten links
        vline(s, x, 22, 25, ST_M)
        hline(s, x - 1, x + 1, 23, ST_M)
    for y in range(18, 27):                                    # Bach unten rechts
        s.set(50 + int((y - 18) * 0.8), y, BLUE_D)
    for (x, y) in ((5, 5), (58, 5), (5, 26), (58, 26)):        # Pinnadeln
        s.set(x, y, ST_L)
        s.set(x - 1, y, OL1)
    for (x, y) in ((32, 9), (25, 22), (47, 21)):               # rote Markierungen
        s.rect(x, y, x + 1, y + 1, RED_D)
        s.set(x, y, ROSE)
    s.set(52, 6, OL2)                                          # Kompass
    s.set(52, 5, OL2)
    s.set(52, 7, OL2)
    s.set(51, 6, OL2)
    s.set(53, 6, OL2)
    s.set(52, 4, RED_D)
    return s


import math  # noqa: E402


def wand_namensliste():
    """Handgeschriebene Liste der Toten (Ink: 'a handwritten list of names beside the window'), einzelne Zeilen durchgestrichen."""
    s = Spr(32, 32)
    s.rect(8, 3, 23, 28, OL1)
    s.rect(9, 4, 22, 27, CREAM)
    for k in range(9):                                         # eingerissene untere Kante
        s.set(9 + k * 2, 27, MOON if k % 2 else OL1)
    s.rect(11, 6, 20, 6, ST_M)                                  # Ueberschrift
    for k in range(8):
        y = 9 + k * 2
        ln = 5 + int(hsh(k, 1, 41) * 5)
        hline(s, 11, 11 + ln, y, ST_M)
        if k in (1, 4, 5):
            hline(s, 10, 12 + ln, y, RED_D)                    # durchgestrichen
    s.set(15, 3, ST_L)                                         # Nagel
    s.set(15, 2, OL1)
    return s


# ====================================================================== Praxis
def behandlungsliege():
    """OP-/Behandlungsliege: gepolstertes Leder auf Holzgestell, weisses Laken, erhoehtes Kopfteil, Lederriemen."""
    s = Spr(64, 32)
    M.block(s, 2, 61, 10, 9, 22, WD, top=(WOOD_M, WOOD_L, WOOD_D))
    M.legs(s, (5, 56), 23, 29, WD)
    s.rect(4, 6, 17, 13, OL1)                                  # Kopfpolster erhoeht
    s.rect(5, 7, 16, 12, WOOD_L)
    hline(s, 5, 16, 7, SAND)
    hline(s, 5, 16, 12, WOOD_M)
    for x in range(19, 59):                                    # Laken
        for y in range(11, 19):
            c = CREAM if y < 14 else (MOON if y < 17 else ST_L)
            if y == 11:
                c = MOON
            s.set(x, y, c)
    vline(s, 19, 11, 18, OL1)
    for x in range(21, 58, 5):                                 # Falten
        vline(s, x, 12, 17, ST_L)
    for x in range(20, 58):
        s.set(x, 19, ST_L if x % 3 else ST_M)
    for x in (24, 46):                                         # Lederriemen
        s.rect(x, 10, x + 1, 20, WOOD_D)
        s.rect(x - 1, 14, x + 2, 15, ST_L)
    M.floor_shadow(s, 4, 59, 30)
    return s


def instrumententisch():
    s = Spr(32, 32)
    M.block(s, 4, 27, 13, 6, 21, (ST_M, ST_L, ST_D), top=(ST_L, MOON, ST_M))
    M.legs(s, (5, 25), 22, 29, (ST_M, ST_L, ST_D))
    s.rect(7, 15, 24, 18, OL1)                                 # Tablett
    s.rect(8, 16, 23, 17, ST_L)
    hline(s, 8, 23, 16, MOON)
    s.line(9, 17, 14, 17, ST_M)                                 # Skalpell, Schere
    s.set(15, 17, OL1)
    s.set(10, 16, ST_L)
    s.line(17, 16, 20, 17, OL1)
    s.rect(21, 9, 23, 14, OL1)                                 # braunes Medizinflaeschchen
    s.rect(22, 10, 22, 14, WOOD_M)
    s.rect(21, 7, 23, 8, OL1)
    s.set(22, 8, SAND)
    s.rect(7, 12, 12, 15, OL1)                                 # Verbandsrolle
    s.rect(8, 13, 11, 14, CREAM)
    s.set(8, 13, MOON)
    M.floor_shadow(s, 5, 26, 30)
    return s


def paravent():
    """Dreiteiliger Wandschirm (Sichtschutz in der Praxis): dunkelgruener Stoff mit Rautenmuster, Holzrahmen."""
    s = Spr(64, 64)
    tops = (8, 11, 8)
    for k, x0 in enumerate((2, 22, 42)):
        x1 = x0 + 19
        y0 = tops[k]
        s.rect(x0, y0, x1, 57, OL1)
        s.rect(x0 + 1, y0 + 1, x1 - 1, 56, WOOD_M)
        s.rect(x0 + 3, y0 + 3, x1 - 3, 54, FOR_D)
        for y in range(y0 + 3, 55):
            for x in range(x0 + 3, x1 - 2):
                if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                    s.set(x, y, FOR_M)
        hline(s, x0 + 1, x1 - 1, y0 + 1, WOOD_L)
        vline(s, x0 + 1, y0 + 1, 56, WOOD_L)
        vline(s, x1 - 1, y0 + 1, 56, WOOD_D)
        s.rect(x0 + 1, 55, x1 - 1, 57, WOOD_D)
        if k:                                                    # Scharniere zwischen den Teilen
            for y in (y0 + 6, 30, 50):
                s.rect(x0 - 1, y, x0 + 1, y + 2, ST_D)
                s.set(x0, y, ST_L)
    for x in (6, 26, 46):
        s.rect(x, 58, x + 3, 60, OL1)
        s.rect(x + 1, 58, x + 2, 59, WOOD_D)
    M.floor_shadow(s, 4, 60, 62)
    return s


def wand_anatomietafel():
    s = Spr(32, 32)
    s.rect(6, 2, 25, 3, WOOD_D)
    s.rect(6, 27, 25, 28, WOOD_D)
    s.rect(7, 4, 24, 26, OL1)
    s.rect(8, 4, 23, 26, CREAM)
    s.ellipse(15.5, 8, 2.6, 2.6, OL2)                         # Kopf
    s.ellipse(15.5, 8, 1.8, 1.8, CREAM)
    for y in range(11, 22):                                    # Koerper
        w = 4 if y < 14 else (3 if y > 18 else 4)
        s.set(15 - w, y, OL2)
        s.set(16 + w, y, OL2)
    hline(s, 11, 20, 11, OL2)
    for y in range(22, 26):
        s.set(13, y, OL2)
        s.set(18, y, OL2)
    s.rect(14, 12, 16, 14, RED_D)                              # Herz
    s.set(14, 12, ROSE)
    s.rect(11, 12, 12, 15, ROSE)                               # Lungen
    s.rect(19, 12, 20, 15, ROSE)
    for k in range(4):                                         # Daerme
        s.rect(13 + (k % 2), 16 + k, 17 - (k % 2), 16 + k, SK_S)
    for (x0, x1, y) in ((9, 11, 6), (20, 22, 8), (9, 11, 19), (20, 22, 17)):   # Beschriftung
        hline(s, x0, x1, y, ST_M)
    return s


def pult_totenbuch():
    """Schreibpult mit aufgeschlagenem Totenbuch (Veronicas Geheimnis): Zeilen mit Namen, ein Name rot markiert."""
    s = Spr(32, 32)
    M.legs(s, (13,), 20, 29, WD)
    s.rect(9, 27, 22, 29, OL1)
    s.rect(10, 27, 21, 28, WOOD_D)
    poly = [(5, 19), (26, 19), (24, 11), (7, 11)]
    for y in range(11, 20):                                    # schraege Pultplatte
        for x in range(5, 27):
            t = (y - 11) / 8.0
            if 7 - t * 2 <= x <= 24 + t * 2:
                s.set(x, y, WOOD_L if y < 13 else WOOD_M)
    hline(s, 5, 26, 19, OL1)
    hline(s, 7, 24, 10, OL1)
    s.rect(8, 8, 23, 17, OL1)                                  # Buch
    s.rect(9, 9, 15, 16, CREAM)
    s.rect(16, 9, 22, 16, MOON)
    vline(s, 15, 8, 17, OL1)
    for k in range(6):
        y = 10 + k
        hline(s, 10, 13, y, ST_M)
        hline(s, 17, 20 - (k % 2), y, ST_M)
    hline(s, 17, 21, 13, RED_D)                                   # roter Eintrag
    s.set(21, 12, RED_D)
    s.rect(24, 12, 26, 17, OL1)                                # Tintenfass
    s.rect(25, 14, 25, 16, OL2)
    s.line(25, 11, 28, 6, MOON)                             # Feder
    s.set(25, 12, ST_L)
    M.floor_shadow(s, 9, 22, 30)
    return s


# ====================================================================== Register
def register(R):
    MB, Wd = 'innen_moebel', 'innen_wand'
    R.add('Zellengitter_Gerade', zellengitter('gerade'), MB, fuss=1)
    R.add('Zellentuer_Zu', zellengitter('tuer_zu'), MB, fuss=1)
    R.add('Zellentuer_Offen', zellengitter('tuer_offen'), MB, fuss=0, solid=False)
    R.add('Zellenpritsche', zellenpritsche(), MB)
    R.add('Zelleneimer', zelleneimer(), MB)
    R.add('Aktenregal', aktenregal(), MB)
    R.add('Wand_Dorfkarte', wand_dorfkarte(), Wd, fuss=0, solid=False)
    R.add('Wand_Namensliste', wand_namensliste(), Wd, fuss=0, solid=False)
    R.add('Behandlungsliege', behandlungsliege(), MB)
    R.add('Instrumententisch', instrumententisch(), MB)
    R.add('Paravent', paravent(), MB)
    R.add('Wand_Anatomietafel', wand_anatomietafel(), Wd, fuss=0, solid=False)
    R.add('Pult_Totenbuch', pult_totenbuch(), MB)


if __name__ == '__main__':
    # Vorschau: python bk_interieur.py -> Baukasten/Vorschau_Interieur.png (5x)
    from PIL import Image
    R = Reg()
    register(R)
    names = ['Zellengitter_Gerade', 'Zellentuer_Zu', 'Zellentuer_Offen', 'Zellenpritsche', 'Zelleneimer', 'Aktenregal', 'Wand_Dorfkarte',
             'Wand_Namensliste', 'Behandlungsliege', 'Instrumententisch', 'Paravent', 'Wand_Anatomietafel', 'Pult_Totenbuch']
    S, GAP = 5, 10
    ims = [R.obj[n][0].im.resize((R.obj[n][0].w * S, R.obj[n][0].h * S), Image.NEAREST) for n in names]
    rows = [ims[:6], ims[6:]]
    w = max(sum(i.width + GAP for i in r) for r in rows) + GAP
    h = sum(max(i.height for i in r) + GAP for r in rows) + GAP
    sh = Image.new('RGBA', (w, h), (70, 60, 80, 255))
    y = GAP
    for r in rows:
        x = GAP
        for i in r:
            sh.paste(i, (x, y), i)
            x += i.width + GAP
        y += max(i.height for i in r) + GAP
    sh.save(BK + '/Vorschau_Interieur.png')
    print('Vorschau_Interieur.png', sh.size)
