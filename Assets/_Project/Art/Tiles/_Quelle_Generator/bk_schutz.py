"""Haus-Baukasten SCHUTZ: Barrikade, Fensterlaeden, Riegel, Talisman-Zustaende. Wird von bk_build.py registriert.

Regelwerk: Hauptschutz ist die Barrikade (Tuer schliessen, schwerer Holzbalken, zwei Fensterlaeden mit Eisengriffen), ohne sie laesst
sich nicht schlafen. Talisman = Zusatzschutz (Feld ums Haus gegen Fenster-Eindringen), "verbraucht"/zerbricht.
Alle Teile passen 1:1 auf die vorhandenen Innen-Tueren/-Fenster (gleiche 32x64-Zelle, gleiche Rahmen), damit man sie per Tile-Tausch
zwischen den Zustaenden umschalten kann:

  Tuer  innen   Tuer_Innen_Zu (vorhanden) -> Tuer_Innen_Riegel -> Tuer_Innen_Halter (bereit) -> Tuer_Innen_Barrikade
  Fenster innen Fenster_Innen_Nacht (vorhanden, Glas) -> Fenster_Innen_Laeden_Offen -> Fenster_Innen_Laeden_Spalt (Warnstufe 2: offene Stelle)
                -> Fenster_Innen_Laeden_Zu
  Talisman      Wand_Talisman / Talisman_Tuer / Talisman_Fenster (aktiv, pulsiert) -> *_Aus (verbraucht) -> *_Bruch (zerbricht, 6 Frames)
  Balken_Lehnt  der Holzbalken steht bereit neben der Tuer (Moebel)
"""
from bk_lib import *
import bk_moebel as M
import bk_fassade as F

TALSET = (TAL, TAL_D, TAL_H)


# ====================================================================== Eisen und Holz
def iron_plate(s, x0, y0, x1, y1, rivets=True):
    box(s, x0, y0, x1, y1, ST_M, hi=ST_L, lo=ST_D)
    if rivets and x1 - x0 >= 3 and y1 - y0 >= 3:
        for (x, y) in ((x0 + 1, y0 + 1), (x1 - 1, y1 - 1)):
            s.set(x, y, ST_L)


def beam_h(s, x0, x1, y0, h=8):
    """Schwerer Holzbalken, waagrecht: Lichtkante oben, Maserung, Astloch, Schattenkante unten, Hirnholz an den Enden."""
    s.rect(x0, y0, x1, y0 + h + 1, OL1)
    for y in range(y0 + 1, y0 + h + 1):
        t = (y - y0 - 1) / max(1, h - 1)
        base = WOOD_L if t < 0.15 else (WOOD_M if t < 0.65 else WOOD_D)
        for x in range(x0 + 1, x1):
            s.set(x, y, base)
    hline(s, x0 + 1, x1 - 1, y0 + 1, SAND)
    for k in range(7):                                        # Maserung: kurze dunkle/helle Striche
        y = y0 + 2 + int(hsh(k, 3, 5) * (h - 3))
        xa = x0 + 3 + int(hsh(k, 7, 9) * (x1 - x0 - 12))
        ln = 3 + int(hsh(k, 1, 4) * 5)
        for x in range(xa, min(xa + ln, x1 - 1)):
            s.set(x, y, WOOD_D if y > y0 + 3 else WOOD_L)
    kx = x0 + (x1 - x0) // 2 + 3
    s.rect(kx, y0 + 3, kx + 2, y0 + 5, EARTH)                 # Astloch
    s.set(kx + 1, y0 + 4, OL2)
    vline(s, x0 + 1, y0 + 1, y0 + h, WOOD_D)                 # Hirnholz
    vline(s, x1 - 1, y0 + 1, y0 + h, EARTH)


def door_base():
    return M.inner_door('zu')


# ====================================================================== Tuer
def tuer_riegel():
    """Eisenriegel unter der Klinke vorgeschoben."""
    s = door_base()
    iron_plate(s, 9, 44, 12, 52)                              # Fuehrung links
    iron_plate(s, 21, 44, 24, 52)                             # Schliessblech rechts
    s.rect(13, 47, 23, 50, OL1)                               # Stange
    hline(s, 13, 22, 48, ST_L)
    hline(s, 13, 22, 49, ST_M)
    hline(s, 13, 22, 50, ST_D)
    box(s, 6, 46, 9, 51, ST_M, hi=ST_L, lo=ST_D)              # Knauf
    s.set(7, 48, ST_L)
    return s


def halter_on(s):
    """Zwei Eisenhalter am Rahmen (auf beliebiger Tuer-Basis)."""
    for x0 in (1, 25):
        iron_plate(s, x0, 31, x0 + 5, 44)
        s.rect(x0 + 1, 35, x0 + 4, 39, OL1)                   # Aufnahme fuer den Balken
        hline(s, x0 + 1, x0 + 4, 39, ST_D)
        hline(s, x0 + 1, x0 + 4, 35, OL2)
    return s


def barrikade_on(s):
    """Balken in den Haltern + Eisenbaender + Schatten auf dem Tuerblatt."""
    beam_h(s, 2, 29, 33, 8)
    dither_dark(s, 7, 42, 24, 46, 10)
    for x0 in (3, 25):                                        # Eisenbaender um den Balken
        s.rect(x0, 31, x0 + 3, 43, OL1)
        s.rect(x0 + 1, 32, x0 + 2, 42, ST_M)
        vline(s, x0 + 1, 32, 42, ST_L)
        vline(s, x0 + 2, 32, 42, ST_D)
        s.set(x0 + 1, 35, ST_L)
        s.set(x0 + 1, 40, ST_L)
    return s


def tuer_halter():
    """Tuer zu, zwei leere Eisenhalter am Rahmen - bereit fuer den Balken."""
    return halter_on(door_base())


def tuer_barrikade():
    """Balken liegt in beiden Haltern quer vor der Tuer, wirft Schatten auf das Tuerblatt."""
    return barrikade_on(tuer_halter())


def balken_lehnt():
    """Der Balken lehnt an der Wand neben der Tuer (noch nicht eingelegt). 32x64, Fuss unten."""
    s = Spr(32, 64)
    top_x, bot_x, y_top, y_bot, wd = 22, 11, 6, 61, 10
    for y in range(y_top, y_bot + 1):
        t = (y - y_top) / (y_bot - y_top)
        cx = top_x + (bot_x - top_x) * t
        x0 = int(round(cx - wd / 2.0))
        x1 = x0 + wd
        for x in range(x0, x1):
            u = (x - x0) / max(1, (x1 - x0 - 1))
            c = WOOD_L if u < 0.2 else (WOOD_M if u < 0.7 else WOOD_D)
            if hsh(x, y // 3, 6) < 0.10:
                c = dk(c)
            s.set(x, y, c)
        s.set(x0 - 1, y, OL1)
        s.set(x1, y, OL1)
    for x in range(int(top_x - wd / 2) - 1, int(top_x + wd / 2) + 2):   # Hirnholz oben (schraege Schnittflaeche)
        s.set(x, y_top - 1, OL1)
        s.set(x, y_top, SAND)
    for x in range(int(bot_x - wd / 2) - 1, int(bot_x + wd / 2) + 2):
        s.set(x, y_bot + 1, OL1)
    for k in (0.28, 0.62):                                    # Eisenband quer zum Balken
        y = int(y_top + (y_bot - y_top) * k)
        t = (y - y_top) / (y_bot - y_top)
        cx = top_x + (bot_x - top_x) * t
        for x in range(int(cx - wd / 2), int(cx + wd / 2)):
            s.set(x, y, ST_D)
            s.set(x, y + 1, ST_M)
        s.set(int(cx - wd / 2), y + 1, ST_L)
    for x in range(bot_x - 6, bot_x + 8):                    # Bodenschatten
        if (x + 62) % 2 == 0:
            s.set(x, 62, OL2)
    return s


# ====================================================================== Fensterlaeden (innen gesehen, 32x64, Rahmen wie Fenster_Innen_*)
def leaf(s, x0, x1, y0, y1, grip_side, planks=2):
    """Ein Fensterladen-Fluegel: Bretter, Eisenbaender mit Scharnier, Eisengriff."""
    s.rect(x0, y0, x1, y1, OL1)
    w = x1 - x0 - 1
    for y in range(y0 + 1, y1):
        for x in range(x0 + 1, x1):
            u = (x - x0 - 1) * planks // max(1, w)
            c = WOOD_M
            if (x - x0 - 1) * planks % max(1, w) < 1 or x == x0 + 1:
                c = WOOD_L
            if hsh(x, y // 4, 3) < 0.1:
                c = WOOD_D
            s.set(x, y, c)
    for k in range(1, planks):                                # Fugen zwischen den Brettern
        vline(s, x0 + 1 + k * w // planks, y0 + 1, y1 - 1, WOOD_D)
    for yb in (y0 + 3, y1 - 5):                               # Eisenbaender
        hline(s, x0 + 1, x1 - 1, yb, ST_L)
        hline(s, x0 + 1, x1 - 1, yb + 1, ST_D)
    hinge = x1 - 1 if grip_side == 'l' else x0 + 1            # Scharnierseite gegenueber dem Griff
    for yb in (y0 + 3, y1 - 5):
        s.set(hinge, yb, ST_L)


def grip(s, x, y):
    """Eisengriff: kleiner senkrechter Bügel."""
    s.rect(x, y, x + 1, y + 5, OL1)
    s.rect(x, y + 1, x, y + 4, ST_L)
    s.rect(x + 1, y + 1, x + 1, y + 4, ST_D)
    s.set(x, y + 1, ST_L)


def fenster_laeden_offen():
    """Laeden aufgeklappt, flach an der Wand neben dem Fenster; Glas dahinter sichtbar."""
    s = M.inner_window('nacht')
    leaf(s, 0, 5, 9, 43, 'l', planks=2)
    leaf(s, 26, 31, 9, 43, 'r', planks=2)
    grip(s, 1, 22)
    grip(s, 29, 22)
    return s


def fenster_laeden_zu():
    """Beide Fluegel geschlossen, Eisengriffe, Querriegel ueber der Fuge."""
    s = M.inner_window('nacht')
    s.rect(8, 10, 23, 39, OL1)
    leaf(s, 8, 15, 10, 39, 'r', planks=2)
    leaf(s, 16, 23, 10, 39, 'l', planks=2)
    vline(s, 15, 11, 38, OL1)
    vline(s, 16, 11, 38, OL2)
    grip(s, 13, 21)
    grip(s, 18, 21)
    for x in range(11, 21):                                   # Querriegel
        s.set(x, 24, OL1)
        s.set(x, 25, ST_L)
        s.set(x, 26, ST_M)
        s.set(x, 27, OL1)
    s.rect(15, 24, 16, 27, ST_L)
    s.set(15, 25, ST_D)
    return s


def fenster_laeden_spalt():
    """Warnstufe 2: der rechte Laden steht offen - die Stelle, die gesichert werden muss. Dunkle Nacht im Spalt."""
    s = M.inner_window('nacht')
    s.rect(8, 10, 23, 39, OL1)
    leaf(s, 8, 15, 10, 39, 'r', planks=2)
    vline(s, 15, 11, 38, OL1)
    for y in range(10, 40):                                   # freie Glasflaeche rechts
        for x in range(16, 24):
            c = NB_M if y < 24 else NB_D
            s.set(x, y, c)
    s.set(21, 13, MOON)
    s.set(19, 18, NB_L)
    for y in range(10, 40):                                   # Schlagschatten des Ladens
        s.set(16, y, OL2)
    s.rect(21, 10, 24, 39, OL1)                               # Laden schraeg aufgeschwenkt (verkuerzt)
    for y in range(11, 39):
        s.set(22, y, WOOD_L)
        s.set(23, y, WOOD_M)
    hline(s, 22, 23, 13, ST_D)
    hline(s, 22, 23, 35, ST_D)
    s.set(22, 24, ST_L)                                        # Griff
    s.set(22, 25, ST_L)
    grip(s, 13, 21)
    return s


# ====================================================================== Talismane: Zustaende
def recolor(sp, mapping):
    out = Spr(sp.w, sp.h)
    for y in range(sp.h):
        for x in range(sp.w):
            c = sp.get(x, y)
            if c[3]:
                out.set(x, y, mapping.get(c, c))
    return out


GRAU = {TAL: ST_M, TAL_D: ST_D, TAL_H: ST_L}


def talisman_fenster(f):
    """Kleiner Talisman an der Fensterlaibung: Kristall an V-foermiger Schnur (wie Talisman_Tuer, nur kleiner), pulsiert ruhig (6 Frames)."""
    s = Spr(32, 32)
    hline(s, 11, 20, 2, OL1)
    s.set(12, 3, WOOD_D)
    s.set(19, 3, WOOD_D)
    for i in range(4):
        s.set(13 + i, 3 + i // 2 + (1 if i > 1 else 0), WOOD_M)
        s.set(18 - i, 3 + i // 2 + (1 if i > 1 else 0), WOOD_M)
    s.set(15, 6, ST_M)
    s.set(16, 6, ST_L)
    for y in range(7, 21):
        w = min(y - 6, 20 - y + 1, 4)
        for x in range(16 - w, 16 + w):
            c = TAL if x < 16 else TAL_D
            if x == 15 and y < 13:
                c = TAL_H
            s.set(x, y, c)
    outline_obj(s)
    lvl = [0, 1, 2, 2, 1, 0][f % 6]
    if lvl >= 1:
        s.set(14, 10, TAL_H)
        s.set(15, 9, TAL_H)
    if lvl >= 2:
        for (x, y) in ((11, 13), (20, 13), (16, 22), (16, 5)):
            s.set(x, y, TAL_H)
    sx, sy = [(10, 9), (22, 10), (11, 17), (21, 18), (16, 24), (9, 13)][f % 6]
    s.set(sx, sy, TAL_H)
    return s


def break_frames(base, mode):
    """Der Talisman zerbricht: Aufblitzen, Riss, Haelften klaffen, Scherben fallen, Staub, leer (6 Frames).
    mode 'schnur': Kristall haengt frei an Schnur (alles ab y>=ycut gehoert zum Kristall); 'platte': Kristall sitzt auf Holzplatte."""
    if mode == 'schnur':
        ycut = 9
        cry = [(x, y, base.get(x, y)) for y in range(ycut, base.h) for x in range(base.w) if base.get(x, y)[3]]
        rest = [(x, y, base.get(x, y)) for y in range(0, ycut) for x in range(base.w) if base.get(x, y)[3]]
    else:
        cry = [(x, y, base.get(x, y)) for y in range(base.h) for x in range(base.w) if base.get(x, y) in TALSET]
        rest = [(x, y, base.get(x, y)) for y in range(base.h) for x in range(base.w) if base.get(x, y)[3] and base.get(x, y) not in TALSET]
    xs = [p[0] for p in cry]
    ys = [p[1] for p in cry]
    cx = (min(xs) + max(xs)) / 2.0
    ylo, yhi = min(ys), max(ys)

    def canvas(parts):
        s = Spr(base.w, base.h)
        for part in parts:
            for x, y, c in part:
                s.set(x, y, c)
        return s

    def shifted(pts, dx, dy, col=None, keep=None):
        return [(x + dx, y + dy, col or c) for x, y, c in pts if keep is None or keep(x, y)]

    left = [p for p in cry if p[0] < cx]
    right = [p for p in cry if p[0] >= cx]
    frames = []
    frames.append(canvas([rest, [(x, y, TAL_H) for x, y, c in cry]]))                         # 0 Aufblitzen
    crack = []
    k = 0
    for y in range(ylo, yhi + 1):                                                              # 1 Riss
        x = int(round(cx)) + (1 if k % 3 == 1 else (-1 if k % 3 == 2 else 0))
        crack.append((x, y, OL1))
        k += 1
    pset = {(x, y) for x, y, _ in cry}
    frames.append(canvas([rest, cry, [(x, y, c) for x, y, c in crack if (x, y) in pset]]))
    frames.append(canvas([rest, shifted(left, -1, 0), shifted(right, 1, 1)]))                  # 2 klafft auf
    frames.append(canvas([rest, shifted(left, -2, 3, keep=lambda x, y: hsh(x, y, 1) < 0.92),
                          shifted(right, 2, 4, keep=lambda x, y: hsh(x, y, 2) < 0.92)]))       # 3 faellt auseinander
    fall = [(x + int((hsh(x, y, 3) - 0.5) * 6), y + 7 + int(hsh(x, y, 4) * 5), TAL_D) for x, y, c in cry if hsh(x, y, 5) < 0.35]
    frames.append(canvas([rest, fall]))                                                        # 4 Scherben
    crumbs = [(x, min(base.h - 2, yhi + 6 + int(hsh(x, y, 6) * 3)), ST_M) for x, y, c in cry if hsh(x, y, 7) < 0.12]
    frames.append(canvas([rest, crumbs]))                                                      # 5 Staub, leer
    return frames


# ====================================================================== Register
def register(R):
    Wd, A, MB = 'innen_wand', 'aussen_wand', 'innen_moebel'
    # Tuer
    R.add('Tuer_Innen_Riegel', tuer_riegel(), Wd, fuss=0, solid=False)
    R.add('Tuer_Innen_Halter', tuer_halter(), Wd, fuss=0, solid=False)
    R.add('Tuer_Innen_Barrikade', tuer_barrikade(), Wd, fuss=0, solid=False)
    R.add('Balken_Lehnt', balken_lehnt(), MB, fuss=1, solid=True)
    # Fensterlaeden innen
    R.add('Fenster_Innen_Laeden_Offen', fenster_laeden_offen(), Wd, fuss=0, solid=False)
    R.add('Fenster_Innen_Laeden_Spalt', fenster_laeden_spalt(), Wd, fuss=0, solid=False)
    R.add('Fenster_Innen_Laeden_Zu', fenster_laeden_zu(), Wd, fuss=0, solid=False)
    # Talisman Fenster (aussen) + Zustaende
    R.add_anim('Talisman_Fenster', [talisman_fenster(f) for f in range(6)], 220, A)
    R.add('Talisman_Fenster_Aus', recolor(talisman_fenster(0), GRAU), A)
    R.add_anim('Talisman_Fenster_Bruch', break_frames(talisman_fenster(2), 'schnur'), 120, A)
    R.add('Talisman_Tuer_Aus', recolor(F.talisman_door(0), GRAU), A)
    R.add_anim('Talisman_Tuer_Bruch', break_frames(F.talisman_door(2), 'schnur'), 120, A)
    # Talisman Wand (innen)
    R.add('Wand_Talisman_Aus', recolor(M.wall_small('talisman', 0), GRAU), Wd, fuss=0, solid=False)
    R.add_anim('Wand_Talisman_Bruch', break_frames(M.wall_small('talisman', 2), 'platte'), 120, Wd, fuss=0, solid=False)


if __name__ == '__main__':
    # Vorschaubogen: python bk_schutz.py  ->  Baukasten/Vorschau_Schutz.png (Zustaende nebeneinander, 5x)
    from PIL import Image
    R = Reg()
    register(R)
    rows = [
        ['Tuer_Innen_Zu*', 'Tuer_Innen_Riegel', 'Tuer_Innen_Halter', 'Tuer_Innen_Barrikade', 'Balken_Lehnt'],
        ['Fenster_Innen_Nacht*', 'Fenster_Innen_Laeden_Offen', 'Fenster_Innen_Laeden_Spalt', 'Fenster_Innen_Laeden_Zu'],
        ['Talisman_Fenster', 'Talisman_Fenster_Aus', 'Talisman_Tuer_Aus', 'Wand_Talisman_Aus'],
        ['Talisman_Fenster_Bruch', 'Talisman_Tuer_Bruch', 'Wand_Talisman_Bruch'],
    ]
    S, GAP = 5, 12
    strips = []
    for row in rows:
        ims = []
        for n in row:
            if n.endswith('*'):
                ims.append(M.inner_door('zu').im if 'Tuer' in n else M.inner_window('nacht').im)
            elif n in R.anim and n.endswith('Bruch'):
                fr = R.anim[n][0]
                strip = Image.new('RGBA', (fr[0].w * len(fr), fr[0].h), (0, 0, 0, 0))
                for i, f in enumerate(fr):
                    strip.paste(f.im, (i * f.w, 0))
                ims.append(strip)
            else:
                ims.append(R.obj[n][0].im)
        strips.append(ims)
    W = max(sum(i.width * S + GAP for i in r) for r in strips) + GAP
    H = sum(max(i.height for i in r) * S + GAP for r in strips) + GAP
    sh = Image.new('RGBA', (W, H), (70, 60, 80, 255))
    y = GAP
    for r in strips:
        x = GAP
        for i in r:
            b = i.resize((i.width * S, i.height * S), Image.NEAREST)
            sh.paste(b, (x, y), b)
            x += b.width + GAP
        y += max(i.height for i in r) * S + GAP
    sh.save(BK + '/Vorschau_Schutz.png')
    print('Vorschau_Schutz.png', sh.size)
