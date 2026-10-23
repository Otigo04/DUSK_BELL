"""TUERSPION: Blick durch den Spion der Haustuer bei Nacht (Regelwerk: "Taeuschung am Tuerspion: Silhouetten, zitternde Haende,
2 bis 3 Pixel breites Grinsen in #f2ead8. Gegensprech: echte Bewohner flehen um Asyl, Monster-Klone wiederholen starr Phrasen.").
Rundes Bild 128x128 (Kreis r=60 um die Mitte) mit Messingring. Aufbau von hinten nach vorn:
  Tuerspion_Hintergrund_Nacht  Veranda mit Laterne links (warmes Rimlicht auf allem, was davor steht)
  Tuerspion_Hintergrund_Dunkel Laterne aus - nur Mondblau (Lichtinsel fehlt, Besucher kaum zu sehen)
  Tuerspion_Gast / _Gast_Grinsen / _Gast_Enthuellt            Mantel beige, Schal dunkelrot, Haende zu ruhig gefaltet, Kopf zu hoch und schmal
  Tuerspion_Hausfrau / _Hausfrau_Grinsen / _Hausfrau_Enthuellt  Kopftuch rot, Kleid dunkelblau, Schuerze braun, Tablett mit Brot, Haende zu lang
  Tuerspion_Mensch_Mann / _Mensch_Frau   echte Bewohner: Gesicht sichtbar, weit offene Augen, Haende zittern (4 Frames, *_Anim.png)
  Tuerspion_Rahmen             Messingring + schwarze Ecken + Randverdunkelung (oberste Ebene)
Monster sind reine Silhouetten (Kopf/Koerper in Outline-Farbe, nur Rimlicht links): nur Grinsen (Zaehne #f2ead8) und Augen
(Monsterauge #d64a6a, nur bei Enthuellung) tragen die Monsterfarben (Style-Bibel). Menschen haben sichtbare Augen (Creme) - der Unterschied.
Einsatz: Layer in dieser Reihenfolge uebereinander, Point-Filter, keine Skalierung ausser ganzzahlig (2x). Ausgabe: Art/UI/Tuerspion.
Aufruf: python tuerspion.py   (schreibt auch Vorschau_Tuerspion.png)"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from bk_lib import *

OUTDIR = ART + '/UI/Tuerspion'
CX = CY = 64
RV = 60            # Sichtkreis
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


# ====================================================================== Helfer
def inside(px, py, pts):
    c = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi:
            c = not c
        j = i
    return c


def poly(s, pts, col):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        for x in range(int(min(xs)), int(max(xs)) + 1):
            if inside(x + 0.5, y + 0.5, pts):
                s.set(x, y, col)


def circ_dist(x, y):
    return math.hypot(x + 0.5 - CX, y + 0.5 - CY)


def clip(s, r=RV):
    for y in range(s.h):
        for x in range(s.w):
            if circ_dist(x, y) > r:
                s.set(x, y, (0, 0, 0, 0))
    return s


def rim_left(s, col=ORA):
    """Laternenlicht von links: erste solide Pixel jeder Zeile (linke Kante) bekommen Rimlicht."""
    add = []
    for y in range(s.h):
        for x in range(s.w):
            if s.solid(x, y) and not s.solid(x - 1, y) and s.get(x, y) != col:
                add.append((x, y))
    for x, y in add:
        s.set(x, y, col)
    return s


def glow(s, cx, cy, r, steps=2):
    """Lichtschein: heller werden (Palette-Rampe lt) mit Bayer-Dither, nahe der Quelle staerker."""
    for y in range(max(0, int(cy - r)), min(s.h, int(cy + r) + 1)):
        for x in range(max(0, int(cx - r)), min(s.w, int(cx + r) + 1)):
            d = math.hypot(x - cx, y - cy)
            if d > r or not s.solid(x, y):
                continue
            t = 1.0 - d / r
            lvl = t * 20.0
            c = s.get(x, y)
            if BAYER[y % 4][x % 4] < lvl:
                c = lt(c)
                if t > 0.55 and BAYER[(y + 1) % 4][(x + 2) % 4] < lvl - 8:
                    c = lt(c)
                s.set(x, y, c)


# ====================================================================== Hintergruende
def background(lit):
    s = Spr(128, 128)
    for y in range(128):
        for x in range(128):
            if circ_dist(x, y) > RV:
                continue
            if y < 92:                                           # Hauswand: senkrechte Bretter
                k = (x // 14) % 2
                c = SV_D if k == 0 else OL2
                if x % 14 == 0:
                    c = OL1
            else:                                                # Veranda-Dielen
                c = EARTH if ((y - 92) // 9) % 2 == 0 else WOOD_D
                if (y - 92) % 9 == 0:
                    c = OL1
                c = dk(c) if not lit else c
            if not lit:
                c = dk(c) if c not in (OL1,) else c
            s.set(x, y, c)
    for y in range(40, 100):                                     # Verandapfosten rechts
        for x in range(101, 111):
            if circ_dist(x, y) <= RV:
                s.set(x, y, WOOD_D if x < 106 else EARTH)
        if circ_dist(100, y) <= RV:
            s.set(100, y, OL1)
        if circ_dist(111, y) <= RV:
            s.set(111, y, OL1)
    if lit:                                                      # Laterne links oben
        for y in range(8, 24):
            s.set(25, y, ST_D)                                   # Kette
        s.rect(20, 24, 30, 38, OL1)
        s.rect(21, 25, 29, 37, ST_D)
        s.rect(22, 27, 28, 35, YEL)
        s.rect(23, 29, 27, 35, ORA)
        s.rect(24, 31, 26, 34, CREAM)
        hline(s, 20, 30, 24, OL1)
        for x in range(21, 30):
            s.set(x, 23, ST_M)
        glow(s, 25, 31, 52, 2)
    else:                                                        # Laterne aus
        for y in range(8, 24):
            s.set(25, y, ST_D)
        s.rect(20, 24, 30, 38, OL1)
        s.rect(21, 25, 29, 37, ST_D)
        s.rect(22, 27, 28, 35, NB_D)
        s.set(23, 28, NB_M)
    return clip(s)


def ring():
    s = Spr(128, 128)
    for y in range(128):
        for x in range(128):
            d = circ_dist(x, y)
            if d > 63.5:
                s.set(x, y, OL1)                                 # schwarze Ecken
            elif d > RV:
                ang = math.atan2(y + 0.5 - CY, x + 0.5 - CX)      # Messingring, Licht oben links
                u = (math.cos(ang - math.radians(225)) + 1) / 2
                s.set(x, y, ST_L if u > 0.82 else (YEL if u > 0.7 else (ST_M if u > 0.3 else ST_D)))
            elif d > 54:                                         # Randverdunkelung (Dither)
                lvl = (d - 54) / (RV - 54) * 16
                if BAYER[y % 4][x % 4] < lvl:
                    s.set(x, y, OL1)
    for a in range(0, 360, 45):                                  # Nieten
        x = int(CX + math.cos(math.radians(a)) * 61.5)
        y = int(CY + math.sin(math.radians(a)) * 61.5)
        s.set(x, y, OL1)
    for a in range(205, 250, 5):                                 # Glanzbogen im Glas
        x = int(CX + math.cos(math.radians(a)) * 50)
        y = int(CY + math.sin(math.radians(a)) * 50)
        s.set(x, y, MOON)
    return s


# ====================================================================== Gesichtsdetails
def grin(s, cx, cy, wide=6, big=False):
    """Das Grinsen: Mundlinie mit hochgezogenen Winkeln, Zaehne in #f2ead8 (6x2; Enthuellung 12x3 mit Luecken)."""
    w = 14 if not big else 20
    for x in range(cx - w // 2, cx + w // 2):
        s.set(x, cy, OL2)
    s.set(cx - w // 2 - 1, cy - 1, OL2)
    s.set(cx + w // 2, cy - 1, OL2)
    tw = wide if not big else 12
    th = 2 if not big else 3
    for y in range(cy, cy + th):
        for x in range(cx - tw // 2, cx + tw // 2):
            s.set(x, y, TEETH)
    if big:
        for x in range(cx - tw // 2 + 2, cx + tw // 2, 3):       # Zahnluecken
            for y in range(cy, cy + th):
                s.set(x, y, OL2)
    for x in range(cx - tw // 2 - 1, cx + tw // 2 + 1):
        s.set(x, cy + th, OL1)


def eyes_monster(s, y):
    for x0 in (56, 69):
        s.rect(x0, y, x0 + 2, y + 1, MON_EYE)
        s.set(x0 - 1, y + 2, OL2)
        s.set(x0 + 3, y + 2, OL2)


# ====================================================================== Besucher
def monster_gast(state):
    s = Spr(128, 128)
    coat = dk(WOOD_L, 2)                                         # beige Mantel, im Schatten
    poly(s, [(30, 128), (30, 102), (38, 87), (54, 77), (74, 77), (90, 87), (98, 102), (98, 128)], coat)   # schmale, gerade Schultern
    for k in range(0, 40):                                                                                 # Revers als zwei feine Linien
        s.set(60 + k // 7, 80 + k, OL1)
        s.set(68 - k // 7, 80 + k, OL1)
    for y in (100, 108, 116):                                                                              # Knoepfe
        s.set(64, y, ST_D)
        s.set(63, y, ST_L)
    for x in range(60, 68):                                       # Hals
        for y in range(60, 72):
            s.set(x, y, OL1)
    poly(s, [(50, 70), (78, 70), (82, 80), (64, 90), (46, 80)], RED_D)                # Schal dunkelrot (markantes Merkmal)
    s.rect(66, 84, 72, 106, RED_D)
    vline(s, 67, 84, 106, SK_S)
    for y in range(104, 110):
        s.set(66 + (y % 3) * 2, y, OL1)                           # Fransen
    s.ellipse(64, 40, 10.5, 17, OL1)                              # Kopf: zu hoch und zu schmal
    s.ellipse(64, 28, 10, 8, dk(EARTH) if False else EARTH)       # kurzes Haar
    s.ellipse(63, 44, 9, 14, OL1)
    s.ellipse(52, 44, 2, 4, OL1)                                  # Ohren
    s.ellipse(76, 44, 2, 4, OL1)
    for x0, c in ((54, SK_S), (65, SK_M)):                        # Haende zu ruhig vor dem Bauch gefaltet, kein Zucken
        s.rect(x0, 112, x0 + 9, 120, OL1)
        s.rect(x0 + 1, 113, x0 + 8, 119, c)
        for x in (x0 + 3, x0 + 6):
            s.set(x, 119, OL1)
    hline(s, 56, 74, 116, OL1)
    rim_left(s)
    if state in ('grinsen', 'enthuellt'):
        grin(s, 64, 54, big=(state == 'enthuellt'))
    if state == 'enthuellt':
        eyes_monster(s, 40)
    return clip(s, 58)


def monster_hausfrau(state):
    s = Spr(128, 128)
    poly(s, [(32, 128), (36, 98), (46, 84), (58, 76), (70, 76), (82, 84), (92, 98), (96, 128)], dk(BLUE_D))      # Kleid
    poly(s, [(46, 96), (82, 96), (86, 128), (42, 128)], WOOD_D)                                                  # Schuerze
    for x0 in (50, 76):                                           # Traeger
        poly(s, [(x0, 84), (x0 + 3, 84), (x0 + 3, 96), (x0 - 1, 96)], WOOD_D)
    for x in range(60, 68):
        for y in range(62, 78):
            s.set(x, y, OL1)
    s.ellipse(64, 46, 15, 16, RED_D)                              # Kopftuch (rot, markantes Merkmal)
    s.ellipse(64, 53, 9.5, 11, OL1)                               # Gesicht im Schatten
    poly(s, [(58, 62), (70, 62), (64, 72)], RED_D)                # Knoten unter dem Kinn
    hline(s, 52, 58, 36, SK_S)                                    # Falten im Tuch
    hline(s, 70, 76, 38, SK_S)
    # Tablett mit Brot
    s.rect(34, 100, 94, 106, OL1)
    s.rect(35, 101, 93, 105, WOOD_M)
    hline(s, 35, 93, 101, WOOD_L)
    hline(s, 35, 93, 105, WOOD_D)
    s.ellipse(64, 96, 12, 8, OL1)
    s.ellipse(64, 96, 11, 7, SAND)
    for x in (58, 63, 68):
        s.set(x, 92, WOOD_M)
        s.set(x + 1, 93, WOOD_M)
    s.ellipse(61, 94, 3, 2, CREAM)
    for x0 in (30, 82):                                           # Aermel zu kurz, Haende zu lang: Finger greifen ueber den Tablettrand
        s.rect(x0, 90, x0 + 12, 99, dk(BLUE_D))
        hline(s, x0, x0 + 12, 99, OL1)
        for k in range(4):
            x = x0 + 1 + k * 3
            s.rect(x, 100, x + 1, 112, SK_S)                       # Finger 12 px lang
            s.set(x, 100, SK_M)
            s.set(x + 1, 106, OL1)                                  # Gelenk
            s.set(x + 1, 113, OL1)
            s.set(x - 1, 101, OL1)
        s.rect(x0 + 1, 98, x0 + 11, 100, SK_S)                    # Handruecken
    rim_left(s)
    if state in ('grinsen', 'enthuellt'):
        grin(s, 64, 58, big=(state == 'enthuellt'))
    if state == 'enthuellt':
        eyes_monster(s, 46)
    return clip(s, 58)


def mensch(kind, f):
    """Echte Bewohner flehen: Gesicht sichtbar, Augen weit offen, Haende zittern (f = Frame 0..3)."""
    s = Spr(128, 128)
    jit = [(0, 0), (1, 0), (0, 1), (-1, 0)][f % 4]
    hj = [(0, 0), (-1, 1), (1, 0), (0, -1)][f % 4]
    if kind == 'mann':
        poly(s, [(26, 128), (30, 98), (42, 84), (56, 76), (72, 76), (86, 84), (98, 98), (102, 128)], WOOD_M)     # Wollpullover
        for x in range(34, 96, 6):                                # Zopfmuster
            for y in range(92, 124, 4):
                s.set(x, y, WOOD_D)
                s.set(x + 1, y + 1, WOOD_D)
        s.rect(59, 62, 69, 76, SK_S)
        s.ellipse(64, 46, 12, 15, SK_S)
        s.ellipse(60, 46, 7, 13, SK_M)
        s.ellipse(64, 30, 13, 9, EARTH)                           # strubbelige Haare
        for x in (53, 57, 62, 67, 72, 75):
            s.set(x, 20, EARTH)
            s.set(x + 1, 21, EARTH)
        glasses = True
    else:
        poly(s, [(30, 128), (34, 98), (46, 84), (58, 76), (70, 76), (82, 84), (94, 98), (98, 128)], dk(SV_M))   # Schultertuch
        poly(s, [(52, 76), (76, 76), (80, 90), (64, 98), (48, 90)], SV_M)
        s.rect(59, 62, 69, 76, SK_S)
        s.ellipse(64, 47, 11, 14, SK_S)
        s.ellipse(60, 47, 6, 12, SK_M)
        s.ellipse(64, 33, 13, 8, EARTH)                           # Haar
        s.ellipse(64, 24, 6, 5, EARTH)                            # Knoten
        glasses = False
    for x0 in (55, 69):                                           # weit aufgerissene Augen
        s.rect(x0 + jit[0] // 1, 43, x0 + 4 + jit[0], 47, CREAM)
        s.rect(x0 + 1 + jit[0], 44, x0 + 2 + jit[0], 46, OL1)
        s.set(x0 + 1 + jit[0], 44, MOON)
        hline(s, x0 - 1, x0 + 5, 41, OL2)                          # hochgezogene Brauen
    if glasses:
        for x0 in (53, 67):
            for a in range(0, 360, 30):
                s.set(int(x0 + 3.5 + math.cos(math.radians(a)) * 5), int(45 + math.sin(math.radians(a)) * 4.5), ST_L)
        hline(s, 62, 66, 45, ST_L)
    s.ellipse(64 + jit[0], 58, 3, 2, OL1)                          # Mund leicht offen
    s.set(63 + jit[0], 57, SK_L)
    # gefaltete / vor den Mund gedrueckte Haende, zittern
    hx, hy = (64 + hj[0], 102 + hj[1]) if kind == 'mann' else (64 + hj[0], 82 + hj[1])
    poly(s, [(hx - 5, hy + 10), (hx - 5, hy - 1), (hx - 1, hy - 11), (hx + 1, hy - 11), (hx + 5, hy - 1), (hx + 5, hy + 10)], OL1)
    poly(s, [(hx - 4, hy + 10), (hx - 4, hy - 1), (hx - 1, hy - 10), (hx, hy - 10), (hx, hy + 10)], SK_M)      # linke Hand
    poly(s, [(hx + 1, hy - 10), (hx + 4, hy - 1), (hx + 4, hy + 10), (hx + 1, hy + 10)], SK_L)                # rechte Hand
    vline(s, hx, hy - 10, hy + 10, OL1)                            # Fuge zwischen den Handflaechen
    for dy in (-5, -1, 3):                                         # Fingerglieder
        s.set(hx - 3, hy + dy, SK_S)
        s.set(hx + 2, hy + dy, SK_M)
    s.rect(hx - 6, hy + 10, hx + 5, hy + 14, SK_S)                # Handgelenke
    rim_left(s)
    return clip(s, 58)


# ====================================================================== Ausgabe
def save(sp, name):
    os.makedirs(OUTDIR, exist_ok=True)
    sp.save(os.path.join(OUTDIR, name + '.png'))


def save_anim(frames, name):
    save(frames[0], name)
    strip = Image.new('RGBA', (128 * len(frames), 128), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(f.im, (i * 128, 0))
    strip.save(os.path.join(OUTDIR, name + '_Anim.png'))


def compose(bg, vis, rg):
    out = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    for layer in (bg, vis, rg):
        if layer is not None:
            out.alpha_composite(layer.im)
    return out


if __name__ == '__main__':
    bg_n, bg_d, rg = background(True), background(False), ring()
    save(bg_n, 'Tuerspion_Hintergrund_Nacht')
    save(bg_d, 'Tuerspion_Hintergrund_Dunkel')
    save(rg, 'Tuerspion_Rahmen')
    vis = {}
    for st, suf in (('normal', ''), ('grinsen', '_Grinsen'), ('enthuellt', '_Enthuellt')):
        vis['Gast' + suf] = monster_gast(st)
        vis['Hausfrau' + suf] = monster_hausfrau(st)
    for n, sp in vis.items():
        save(sp, 'Tuerspion_' + n)
    for kind, nm in (('mann', 'Mensch_Mann'), ('frau', 'Mensch_Frau')):
        fr = [mensch(kind, f) for f in range(4)]
        save_anim(fr, 'Tuerspion_' + nm)
        vis[nm] = fr[0]
    lines = ['# Tuerspion (128x128, Kreis r=60) - Layer: Hintergrund < Besucher < Rahmen. Erzeugt von tuerspion.py',
             'Tuerspion_Hintergrund_Nacht', 'Tuerspion_Hintergrund_Dunkel', 'Tuerspion_Rahmen'] + ['Tuerspion_' + n for n in vis] + \
            ['Tuerspion_Mensch_Mann_Anim (4 Frames, Zittern)', 'Tuerspion_Mensch_Frau_Anim (4 Frames, Zittern)']
    open(OUTDIR + '/_Liste.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    # Vorschau 2x: Nacht-Szenen + eine dunkle
    S = 2
    order = [('Gast', bg_n), ('Gast_Grinsen', bg_n), ('Gast_Enthuellt', bg_n), ('Hausfrau', bg_n), ('Hausfrau_Grinsen', bg_n),
             ('Hausfrau_Enthuellt', bg_n), ('Mensch_Mann', bg_n), ('Mensch_Frau', bg_n), ('Gast_Grinsen', bg_d)]
    sh = Image.new('RGBA', (3 * 128 * S + 4 * 8, 3 * 128 * S + 4 * 8), (70, 60, 80, 255))
    for i, (n, bg) in enumerate(order):
        im = compose(bg, vis[n], rg).resize((128 * S, 128 * S), Image.NEAREST)
        sh.alpha_composite(im, (8 + (i % 3) * (128 * S + 8), 8 + (i // 3) * (128 * S + 8)))
    sh.save(OUTDIR + '/Vorschau_Tuerspion.png')
    print('Tuerspion:', len(vis) + 3, 'Dateien ->', OUTDIR)
