"""FLUSS-TILESET (Art/Welt/03_Fluss/Tileset): animiertes Wasser mit 47er-Blob-Autotile.

Ergebnis: 10 Sheets  Fluss_<Strom>_<Ufer>.png   Strom = S, N, O, W, Still   Ufer = Gras, Kies
  Sheet-Layout: Spalte = Blob-Index 0..46 (Spalte 47 leer), Zeile = Animationsframe 0..15  (48*32 x 16*32 px)
  Animation: 16 Frames, Schleife nahtlos (Muster wandern 2 px/Frame = 32 px pro Schleife; Funkeln/Schaum zeitperiodisch)
  Naht: Ufer-Wellen sind an den Kachelenden exakt 0 -> Nachbarkacheln schliessen lueckenlos (siehe welt_lib / seam-Test)
Zusaetzlich: _Layout_Fluss.json (Blob-Index -> Maske/Ecken, Frame-Anzahl, Tempo), Vorschau in Welt/_Vorschau.
Aufruf: python gen_fluss.py        (schreibt alles, prueft Palette/Alpha/Schleife/Nahte, Abbruch bei Fehler)"""
import math
import sys

import numpy as np
from PIL import Image

import welt_lib as W
from welt_lib import H, hsh

T = 16
STROEME = {'S': (0, 2), 'N': (0, -2), 'O': (2, 0), 'W': (-2, 0), 'Still': (0, 0)}
UFER = ['Gras', 'Kies']

# Farben (alle aus Palette.png)
B0, B1, B2, B3, B4, B5 = (H(h) for h in ('23336b', '2f4f8f', '3f72b0', '5b99c4', '8cc4d6', 'cfeef0'))
G0, G1, G2, G3, G4, G5 = (H(h) for h in ('243b3f', '2f5444', '3f7347', '58903f', '7bac45', 'a4c654'))
BR0, BR1, BR2, BR3, BR4, BR5 = (H(h) for h in ('3a2530', '5a3a3f', '7d5646', 'a37a56', 'c9a26a', 'e3c98c'))
S1, S2, S3, S4, S5 = (H(h) for h in ('5a566e', '7a7790', '9e9bb2', 'c4c1d2', 'e4e0ea'))
CREAM = H('e6d8b8')

_fields = {}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
NCREST = 11


def crests(stream):
    """Wellenkaemme: kurze helle Striche quer zur Stroemung. Liste (x, y, Laenge, Phase); Position wandert 2 px/Frame (32 px = 1 Schleife)."""
    out, taken = [], []
    k = 0
    while len(out) < NCREST and k < 200:
        k += 1
        x, y = int(hsh(k, 1, 51, 2) * 32), int(hsh(k, 2, 51, 2) * 32)
        if any(min(abs(x - a), 32 - abs(x - a)) < 9 and min(abs(y - b), 32 - abs(y - b)) < 7 for a, b in taken):
            continue
        taken.append((x, y))
        out.append((x, y, 3 + int(hsh(k, 3, 51, 2) * 6), int(hsh(k, 4, 51, 2) * T)))
    return out


def crest_layer(stream):
    """[T,32,32] mit 0 = nichts, 1 = Schatten (B1), 2 = Kamm (B3), 3 = Kammspitze (B4)."""
    sx, sy = STROEME[stream]
    lay = np.zeros((T, 32, 32), np.uint8)
    for (x0, y0, L, ph) in crests(stream):
        for t in range(T):
            if stream == 'Still':                          # Kamm waechst und vergeht an Ort und Stelle
                u = (t + ph) % T
                ln = int(round(L * math.sin(math.pi * u / T)))
                if ln < 2:
                    continue
                bx, by = x0, y0
                horiz = True
            else:
                ln = L
                bx, by = (x0 + sx * t) % 32, (y0 + sy * t) % 32
                horiz = sy != 0
            for k in range(ln):
                px_, py_ = ((bx + k) % 32, by) if horiz else (bx, (by + k) % 32)
                lay[t, py_, px_] = 3 if ln >= 4 and ln // 2 - 1 <= k <= ln // 2 else 2
                sp = (px_, (py_ + 1) % 32) if horiz else ((px_ + 1) % 32, py_)
                if lay[t, sp[1], sp[0]] == 0:
                    lay[t, sp[1], sp[0]] = 1
    return lay


def fields(stream):
    """Animierte Rauschfelder je Stroemung (gecacht): weiche Flecken, Schaum, Funkeln, Kaemme."""
    if stream in _fields:
        return _fields[stream]
    sx, sy = STROEME[stream]
    vertical = sy != 0 or stream == 'Still'
    ct = 4 if stream == 'Still' else 0
    patch = W.noise_field(*((6, 3) if vertical else (3, 6)), ct, T, 11, sx=sx, sy=sy)
    f = {'patch': patch, 'crest': crest_layer(stream)}
    if stream == 'Still':
        f['spark'] = W.noise_field(16, 16, 8, T, 37)
        f['foam'] = W.noise_field(8, 8, 4, T, 41)
    else:
        f['spark'] = W.noise_field(24, 24, 0, T, 37, sx=sx, sy=sy)
        f['foam'] = W.noise_field(*((14, 3) if vertical else (3, 14)), 0, T, 41, sx=sx, sy=sy)
    _fields[stream] = f
    return f


def water_px(sh, f, t, x, y):
    """Farbe eines Wasserpixels (Kachelform sh, Frame t)."""
    d = sh.D[y, x]
    v = f['patch'][t, y, x]
    fo = f['foam'][t, y, x]
    P = sh.P
    # Uferschatten: Land im Norden/Westen wirft dunkle Kante ins Wasser (Licht von oben links)
    shadow = (not sh.ext[y - 1 + P, x + P]) or (not sh.ext[y + P, x - 1 + P])
    shadow2 = (not sh.ext[y - 2 + P, x + P]) or (not sh.ext[y + P, x - 2 + P])
    if d <= 1.5:                                  # Uferkante: Schaum
        if fo > 0.58:
            return B5 if fo > 0.84 else B4
        return B2 if shadow else B3
    if d <= 2.6:                                  # flaches Wasser
        if shadow or shadow2:
            return B2
        return B4 if v > 0.86 else (B2 if v < 0.22 else B3)
    cr = f['crest'][t, y, x]
    if d <= 6.5:                                  # mittleres Wasser
        c = B3 if v > 0.96 else (B1 if v < 0.12 else B2)
        lo = B1
    else:                                         # tiefes Wasser
        c = B2 if v > 0.78 else (B0 if v < 0.08 else B1)
        lo = B0
    if cr == 3:
        return B4 if d > 6.5 else B5
    if cr == 2:
        return B3 if d > 6.5 else B4
    if cr == 1:
        return lo
    if f['spark'][t, y, x] > 0.985:
        return B5
    return c


def grass_px(grass, x, y):
    return tuple(grass[x, y])


def bank_px(sh, kind, grass, x, y):
    """Landpixel am Ufer (statisch, in allen Frames gleich)."""
    od = sh.OD[y, x]
    base = grass_px(grass, x, y)
    n = hsh(x, y, 7, 3)
    if kind == 'Gras':
        if od <= 1.0:
            return BR1 if n < 0.55 else BR0                 # nasse Erde
        if od <= 2.0:
            return BR2 if n < 0.6 else BR3                   # Uferkante
        if od <= 3.0:
            return G4 if n < 0.5 else G3                     # frisches Gras am Rand
        return base
    # Kies
    if od <= 1.0:
        return S1 if n < 0.5 else S2                         # nasser Kies
    if od <= 2.5:
        return S3 if n < 0.45 else (S2 if n < 0.75 else S4)
    if od <= 4.0:
        v = hsh(x // 2, y // 2, 9, 5)
        return S4 if v < 0.35 else (CREAM if v < 0.6 else (S3 if v < 0.85 else S5))
    if od <= 5.0 and n < 0.45:                               # Auslaufen ins Gras (Dither)
        return S3 if n < 0.2 else CREAM
    return base


def render_tile(mask, notch, stream, kind, t, grass):
    sh = W.Shape(mask, notch)
    f = fields(stream)
    px = np.zeros((32, 32, 4), np.uint8)
    for y in range(32):
        for x in range(32):
            c = water_px(sh, f, t, x, y) if sh.ins[y, x] else bank_px(sh, kind, grass, x, y)
            px[y, x] = c
    return Image.fromarray(px, 'RGBA')


def build_sheet(stream, kind):
    ts = Image.open(W.ART + '/Tiles/Tileset_Terrain.png').convert('RGBA')
    gim = ts.crop((0, 4 * 32, 32, 5 * 32))
    grass = gim.load()
    sheet = Image.new('RGBA', (48 * 32, T * 32), (0, 0, 0, 0))
    frames_of = {i: [] for i in range(47)}
    for t in range(T):
        for i, (m, n) in enumerate(W.BLOB47):
            im = render_tile(m, n, stream, kind, t, grass)
            sheet.paste(im, (i * 32, t * 32))
            frames_of[i].append(im)
    return sheet, frames_of


def main():
    out = W.zone_dir('fluss', 'Tileset')
    errs = []
    for stream in STROEME:
        for kind in UFER:
            sheet, frames_of = build_sheet(stream, kind)
            name = 'Fluss_%s_%s' % (stream, kind)
            sheet.save('%s/%s.png' % (out, name))
            errs += W.check_palette(sheet, name)
            for i in (15, 0):                                  # Vollwasser und Insel muessen sich bewegen
                if stream != 'Still' or i == 15:
                    errs += W.check_loop(frames_of[i], '%s idx%d' % (name, i))
            print('ok', name)
    W.dump_json(out + '/_Layout_Fluss.json', {
        'tileSize': 32, 'ppu': 32, 'frames': T, 'fps': 8, 'columns': 48, 'rows': T,
        'layout': 'Spalte = Blob-Index, Zeile = Animationsframe',
        'masken': 'Bit N=1 O=2 S=4 W=8 (Bit gesetzt = Wasser setzt sich in dieser Richtung fort); notch = Wasser-Ecke fehlt',
        'tiles': [{'index': i, 'maske': m, 'fehlendeEcken': sorted(n), 'name': W.name_of(i)} for i, (m, n) in enumerate(W.BLOB47)],
        'stroeme': list(STROEME), 'ufer': UFER,
        'hinweis': 'Wasser fliesst im Bild in Richtung S/N/O/W; Still = Teich ohne Strom. Randpixel sind kachel-nahtfrei.'})
    if errs:
        print('\n'.join(errs))
        sys.exit(1)


if __name__ == '__main__':
    main()
