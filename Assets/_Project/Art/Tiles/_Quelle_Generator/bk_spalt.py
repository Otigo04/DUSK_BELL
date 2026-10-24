"""Haus-Baukasten SPALT: Tuer und Fenster stehen einen Spalt offen, etwas greift hinein (Nachtbelagerung, Warnstufe 2-3).
Regelwerk: Warnstufe 2 = offene Stelle, 5-10 s Zeit sie zu sichern. Warnstufe 3 = bei Ignorieren schiebt sich eine Tatze oder Fratze
durch den Spalt -> Kampf oder Flucht. Monster-Bibel: Verkleidung hat "Haende zu lang fuer die Aermel" (Hausfrau), "Haende zu ruhig" (Gast);
der Spalt zeigt erst die Menschenhand (Verkleidung), dann die Klaue (Enthuellung, Krallen in Zaehne-Farbe #f2ead8, Augen #d64a6a).
Hausfrau-Schwaeche: reicht der Spieler ihr etwas durch den Spalt, zieht sie die Hand zurueck (Rueckzug-Animation).
Zustaende (Tile-Tausch, gleiche 32x64-Zelle wie Tuer_Innen_Zu / Fenster_Innen_*):
  Tuer    Tuer_Innen_Spalt -> _Spalt_Hand_Gast | _Spalt_Hand_Hausfrau | _Spalt_Hausfrau_Rueckzug | _Spalt_Klaue
  Tuer mit Balken   Tuer_Innen_Barrikade_Spalt -> _Spalt_Klaue (der Balken haelt, splittert aber)
  Fenster Fenster_Innen_Laeden_Spalt (vorhanden) -> Fenster_Innen_Spalt_Hand | _Spalt_Klaue | _Spalt_Fratze (nur ein Gesichtsausschnitt)
Dialogue Bible: nie Monster und Mensch in einer Szene - hier ist nur das Monster zu sehen, nie beide."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
from bk_lib import *
import bk_moebel as M
import bk_schutz as Z

MENSCH = (SK_L, SK_M, SK_S)            # Menschenhand: Licht oben, Schatten unten
KLAUE = (SK_M, SK_S, EARTH)            # dunkler, im Spalt kaum beleuchtet
AERMEL = {'gast': (WOOD_L, SAND, WOOD_M), 'hausfrau': (BLUE_D, BLUE_L, NB_M)}   # beiger Mantel / dunkelblaues Kleid


# ====================================================================== Spalt
def door_gap(s):
    """Tuer steht an der Klinkenseite einen Spalt offen: Blatt verkuerzt, dunkle Nacht im Spalt, Mondlicht am Rand."""
    for y in range(9, 64):
        panel = 12 <= y <= 32 or 36 <= y <= 59
        for x in range(21, 25):
            if x == 21:
                c = OL1
            elif x == 22:
                c = OL2
            elif x == 23:
                c = NB_D
            else:
                c = NB_M if y % 5 else NB_D                    # Mondstreifen, leicht unruhig
            s.set(x, y, c)
        s.set(20, y, OL1 if panel else WOOD_D)                # Blattkante liegt im Schatten
        if panel:
            s.set(19, y, WOOD_L if (12 < y < 32 or 36 < y < 59) else WOOD_M)
    s.set(17, 35, YEL)                                         # Klinke wandert mit dem Blatt
    s.set(18, 35, ORA)
    return s


def finger(s, xr, xl, y, skin=MENSCH, claw=False):
    """Waagrechter Finger vom Spalt (xr) nach links bis zur Spitze (xl): 2 px dick, Gelenkfalten, Nagel oder Kralle."""
    for x in range(xl, xr + 1):
        s.set(x, y - 1, OL1)
        s.set(x, y, skin[0])
        s.set(x, y + 1, skin[1])
        s.set(x, y + 2, OL1)
    for jx in range(xl + 3, xr - 1, 3):
        s.set(jx, y, skin[2])
        s.set(jx, y + 1, skin[2])
    if claw:
        for i, yy in ((1, y), (2, y), (3, y + 1)):             # Kralle, krumm nach unten
            s.set(xl - i, yy, TEETH)
        for i in (1, 2, 3):
            s.set(xl - i, y - 1 if i < 3 else y, OL1)
        s.set(xl - 4, y + 1, OL1)
        s.set(xl - 2, y + 1, OL1)
        s.set(xl - 3, y + 2, OL1)
    else:
        s.set(xl, y, SAND)                                     # Fingernagel
        s.set(xl - 1, y, OL1)
        s.set(xl - 1, y + 1, OL1)


def cuff(s, x0, x1, y0, y1, sleeve):
    base, hi, lo = sleeve
    s.rect(x0, y0, x1, y1, OL1)
    s.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, base)
    vline(s, x0 + 1, y0 + 1, y1 - 1, hi)
    hline(s, x0, x1, y1, OL1)
    hline(s, x0 + 1, x1 - 1, y1 - 1, lo)


def crawl(f, k):
    """Finger k tastet sich vor und zurueck (Wellenbewegung ueber die Finger)."""
    return (0, 1, 2, 1)[(f + k) % 4] - 1


def tuer_spalt():
    return door_gap(M.inner_door('zu'))


def tuer_hand(who, f):
    """Menschenhand haelt sich am Tuerblatt fest, 4 Frames. Hausfrau: Finger tasten, Aermel zu kurz (Haende zu lang).
    Gast: Haende zu ruhig - fast starr, nur der kleine Finger bewegt sich."""
    s = door_gap(M.inner_door('zu'))
    ys = (28, 33, 38, 43)
    lens = (6, 8, 9, 7) if who == 'gast' else (5, 7, 8, 6)
    for k, y in enumerate(ys):
        move = crawl(f, k) if (who == 'hausfrau' or k == 3) else 0
        finger(s, 23, 23 - lens[k] - move, y)
    cuff(s, 23, 24, ys[0] - 2, ys[-1] + 3, AERMEL[who])
    return s


def tuer_hausfrau_rueckzug(f):
    """Sie bekommt etwas durch den Spalt gereicht und zieht die Hand zurueck (5 Frames, nicht loopen): greift, haelt, ballt, weicht, weg."""
    s = door_gap(M.inner_door('zu'))
    scale = (1.0, 1.0, 0.7, 0.4, 0.0)[f]
    if scale == 0.0:
        return s
    ys = (28, 33, 38, 43)
    lens = (5, 7, 8, 6)
    for k, y in enumerate(ys):
        ln = max(1, int(round(lens[k] * scale)))
        if f == 2:                                             # Faust: Finger kurz und gebogen
            ln = max(2, ln - 1)
        finger(s, 23, 23 - ln, y)
    shift = 0 if f < 3 else 1
    cuff(s, 23 + shift, 24, ys[0] - 2, ys[-1] + 3, AERMEL['hausfrau'])
    return s


def tuer_klaue(f):
    """Enthuellung: dunkle Klaue mit Krallen in Zaehne-Farbe kratzt das Holz (4 Frames), Kratzspuren wachsen."""
    s = door_gap(M.inner_door('zu'))
    ys = (30, 37, 44)
    for k, y in enumerate(ys):
        xl = 23 - 11 - (crawl(f, k) if k != 1 else 0)
        finger(s, 23, xl, y, KLAUE, claw=True)
        ln = (f + 1) * 2
        hline(s, xl - 6 - ln, xl - 6, y + 1, OL2)               # Kratzspur im Holz
        if f >= 2:
            s.set(xl - 7 - ln, y, WOOD_L)                       # Span
    cuff(s, 23, 24, ys[0] - 2, ys[-1] + 3, (SK_S, SK_M, EARTH))
    return s


def tuer_barrikade_spalt():
    """Tuer wurde aufgedrueckt, der Balken haelt - Riss im Holz, Splitter, Spalt dahinter."""
    s = Z.halter_on(door_gap(M.inner_door('zu')))
    Z.barrikade_on(s)
    for k, y in enumerate(range(34, 42)):                       # Riss
        s.set(22 + (1 if k % 3 == 1 else 0) - (1 if k % 3 == 2 else 0), y, OL1)
    for x in (20, 21, 23):                                      # Splitter oben auf dem Balken
        s.set(x, 32, WOOD_L)
    s.set(22, 31, SAND)
    return s


def tuer_barrikade_klaue(f):
    s = tuer_barrikade_spalt()
    ys = (47, 52, 57)
    for k, y in enumerate(ys):
        xl = 23 - 10 - crawl(f, k)
        finger(s, 23, xl, y, KLAUE, claw=True)
        hline(s, xl - 6 - (f + 1) * 2, xl - 6, y + 1, OL2)
    cuff(s, 23, 24, ys[0] - 2, ys[-1] + 3, (SK_S, SK_M, EARTH))
    return s


# ====================================================================== Fenster
def fenster_hand(f, klaue=False):
    """Hand/Klaue greift hinter dem aufgeschwenkten Laden hervor ueber das Glas nach dem zweiten Laden."""
    s = Z.fenster_laeden_spalt()
    ys = (18, 24, 30)
    for k, y in enumerate(ys):
        xl = 21 - (4 if not klaue else 6) - crawl(f, k)
        finger(s, 21, xl, y, KLAUE if klaue else MENSCH, claw=klaue)
    s.rect(21, ys[0] - 1, 22, ys[-1] + 3, OL1)                  # Handruecken am Ladenrand
    s.rect(21, ys[0], 21, ys[-1] + 2, SK_S)
    return s


def fenster_fratze(f):
    """Nur ein senkrechter Ausschnitt eines Gesichts im Spalt: Augen (erst dunkel, dann Monsterauge #d64a6a), dann das Grinsen
    (3 px breit, #f2ead8). Sechs Frames: dunkel, dunkel, Augen, Augen+Grinsen, Augen+Grinsen, dunkel."""
    s = Z.fenster_laeden_spalt()
    glow = f in (2, 3, 4)
    grin = f in (3, 4)
    dim = f in (0, 1, 5)
    for y in range(13, 40):                                     # Gesichtsoval, im Spalt (x 16..20)
        for x in range(16, 21):
            nx = (x - 18.0) / 6.0
            ny = (y - 26.0) / 13.5
            if nx * nx + ny * ny <= 1.0:
                c = EARTH if dim else (SK_S if x <= 17 else EARTH)
                s.set(x, y, c)
    for x in range(16, 21):                                     # Brauenschatten
        s.set(x, 20, OL2)
    s.set(18, 24, SK_M if not dim else EARTH)                   # Nasenruecken
    s.set(18, 25, SK_M if not dim else EARTH)
    for (ex, hot) in ((16, 17), (19, 20)):                      # Augenhoehlen
        s.rect(ex, 22, ex + 1, 23, OL1)
        if glow:
            s.set(hot, 22, MON_EYE)
            s.set(hot, 23, MON_EYE)
    for x in range(16, 21):                                     # Mund
        s.set(x, 30, OL1)
    s.set(16, 29, OL1)
    s.set(20, 29, OL1)
    if grin:
        for x in (17, 18, 19):
            s.set(x, 30, TEETH)
            s.set(x, 31, TEETH)
        s.set(18, 31, SK_M)
        for x in range(16, 21):
            s.set(x, 32, OL1)
    return s


# ====================================================================== Register
def register(R):
    Wd = 'innen_wand'
    R.add('Tuer_Innen_Spalt', tuer_spalt(), Wd, fuss=0, solid=False)
    R.add_anim('Tuer_Innen_Spalt_Hand_Gast', [tuer_hand('gast', f) for f in range(4)], 200, Wd, fuss=0, solid=False)
    R.add_anim('Tuer_Innen_Spalt_Hand_Hausfrau', [tuer_hand('hausfrau', f) for f in range(4)], 200, Wd, fuss=0, solid=False)
    R.add_anim('Tuer_Innen_Spalt_Hausfrau_Rueckzug', [tuer_hausfrau_rueckzug(f) for f in range(5)], 220, Wd, fuss=0, solid=False)
    R.add_anim('Tuer_Innen_Spalt_Klaue', [tuer_klaue(f) for f in range(4)], 160, Wd, fuss=0, solid=False)
    R.add('Tuer_Innen_Barrikade_Spalt', tuer_barrikade_spalt(), Wd, fuss=0, solid=False)
    R.add_anim('Tuer_Innen_Barrikade_Spalt_Klaue', [tuer_barrikade_klaue(f) for f in range(4)], 160, Wd, fuss=0, solid=False)
    R.add_anim('Fenster_Innen_Spalt_Hand', [fenster_hand(f) for f in range(4)], 200, Wd, fuss=0, solid=False)
    R.add_anim('Fenster_Innen_Spalt_Klaue', [fenster_hand(f, True) for f in range(4)], 160, Wd, fuss=0, solid=False)
    R.add_anim('Fenster_Innen_Spalt_Fratze', [fenster_fratze(f) for f in range(6)], 280, Wd, fuss=0, solid=False)


if __name__ == '__main__':
    # Vorschau: python bk_spalt.py -> Baukasten/Vorschau_Spalt.png (alle Frames nebeneinander, 4x)
    from PIL import Image
    R = Reg()
    register(R)
    names = ['Tuer_Innen_Spalt', 'Tuer_Innen_Spalt_Hand_Gast', 'Tuer_Innen_Spalt_Hand_Hausfrau', 'Tuer_Innen_Spalt_Hausfrau_Rueckzug',
             'Tuer_Innen_Spalt_Klaue', 'Tuer_Innen_Barrikade_Spalt', 'Tuer_Innen_Barrikade_Spalt_Klaue',
             'Fenster_Innen_Spalt_Hand', 'Fenster_Innen_Spalt_Klaue', 'Fenster_Innen_Spalt_Fratze']
    S, GAP = 4, 8
    rows = []
    for n in names:
        fr = R.anim[n][0] if n in R.anim else [R.obj[n][0]]
        rows.append([f.im.resize((f.w * S, f.h * S), Image.NEAREST) for f in fr])
    groups = [rows[:5], rows[5:]]
    cols = []
    for grp in groups:
        w = max(sum(i.width + GAP for i in r) for r in grp) + GAP
        h = sum(r[0].height + GAP for r in grp) + GAP
        im = Image.new('RGBA', (w, h), (70, 60, 80, 255))
        y = GAP
        for r in grp:
            x = GAP
            for i in r:
                im.paste(i, (x, y), i)
                x += i.width + GAP
            y += r[0].height + GAP
        cols.append(im)
    out = Image.new('RGBA', (cols[0].width + cols[1].width, max(c.height for c in cols)), (70, 60, 80, 255))
    out.paste(cols[0], (0, 0))
    out.paste(cols[1], (cols[0].width, 0))
    out.save(BK + '/Vorschau_Spalt.png')
    print('Vorschau_Spalt.png', out.size)
