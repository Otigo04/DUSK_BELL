"""WELT-BIBLIOTHEK: gemeinsame Bausteine fuer alle Biome jenseits Zone 1 (Art/Welt).

Palette: Art/Palette.png (40 Farben) - dieselbe wie Gelaende (Tileset_Terrain), Wald, Uebergang, Hohes Gras, Zaun und die Natur-Objekte,
damit Ufer, Boeden und Baeume nahtlos an die vorhandene Aussenwelt anschliessen. (Haus/Interieur/Baukasten nutzen dagegen die 39-Farben-Style-Bibel.)
Raster 32x32, Point-Filter, PPU 32, keine halbtransparenten Pixel. Weiche Uebergaenge nur per Dither.

Enthalten:
  Pfade/Zonen        zone_dir(zone, sub)           -> Art/Welt/<NN_Zone>/<Tileset|Objekte|Animiert|Tiere>
  Rauschen           noise_field(...)              periodisch in Raum (32 px) UND Zeit (T Frames) -> nahtlose Animationen
  Autotile (47er)    Blob47: Form, Distanzfelder, Index <-> Nachbarn, Regeln als JSON
  Pruefung           check_palette(), check_loop(), seam_report()
  Ausgabe            write_sheet(), Liste/JSON-Helfer
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WELT = os.path.normpath(os.path.join(HERE, '..')).replace('\\', '/')
ART = os.path.normpath(os.path.join(HERE, '..', '..')).replace('\\', '/')
sys.path.insert(0, ART + '/Tiles/_Quelle_Generator')

from nwlib import (Spr, H, hsh, GREEN, BROWN, STONE, PURP, BLUE, OUT, RED, ORANGE, YELLOW, PINK, VIOLET,  # noqa: E402,F401
                   CREAM, WINE, SAND, AMBER, MAUVE)

ZONEN = {'gemeinsam': '00_Gemeinsam', 'tiefwald': '02_Tiefwald', 'fluss': '03_Fluss', 'sumpf': '04_Sumpf',
         'felsland': '05_Felsland', 'ruinen': '06_Ruinen'}

_pal = Image.open(ART + '/Palette.png').convert('RGBA')
PALETTE = {c[:3] for _, c in _pal.getcolors(10 ** 6) if c[3] > 0}
assert len(PALETTE) == 40, 'Palette.png sollte 40 Farben haben'


def zone_dir(zone, sub):
    d = '%s/%s/%s' % (WELT, ZONEN[zone], sub)
    os.makedirs(d, exist_ok=True)
    return d


def C(rgba):
    """RGBA-Tuple -> Palette-Index-freier RGB-Tuple (fuer numpy-Vergleiche)."""
    return tuple(rgba[:3])


# ====================================================================== Rauschen (raum- und zeitperiodisch)
def _smooth(u):
    return u * u * (3.0 - 2.0 * u)


def noise_field(cx, cy, ct, T, seed, sx=0.0, sy=0.0, kx=1, ky=1):
    """Wertrauschen als Feld [T, 32, 32] mit Werten 0..1.
    cx, cy   Gitterzellen pro Kachel (vor Wiederholung); kx, ky Wiederholungen: Periode 32/kx bzw. 32/ky
    ct       Gitterzellen ueber die Schleife (0/1 = zeitlich konstant, nur verschoben)
    sx, sy   Verschiebung in Pixel pro Frame (Stroemung). Bedingung: sx*T ist ein Vielfaches der Periode, sonst schliesst die Schleife nicht.
    Das Feld ist in x/y mit Periode 32/kx bzw. 32/ky nahtlos und in t mit Periode T."""
    px, py = 32.0 / kx, 32.0 / ky
    if sx:
        assert abs((sx * T) / px - round((sx * T) / px)) < 1e-9, 'Schleife schliesst nicht (sx=%s, T=%s, Periode %s)' % (sx, T, px)
    if sy:
        assert abs((sy * T) / py - round((sy * T) / py)) < 1e-9, 'Schleife schliesst nicht (sy=%s, T=%s, Periode %s)' % (sy, T, py)
    ctc = max(1, ct)
    lat = np.zeros((ctc, cy, cx))
    for k in range(ctc):
        for j in range(cy):
            for i in range(cx):
                lat[k, j, i] = hsh(i, j, k, seed)
    if kx > 1 or ky > 1:
        pass                                                   # Wiederholung geschieht ueber die Koordinate (siehe unten)
    ys, xs = np.mgrid[0:32, 0:32].astype(float)
    out = np.zeros((T, 32, 32))
    for t in range(T):
        X = (xs - sx * t) % px
        Y = (ys - sy * t) % py
        u = X / px * cx
        v = Y / py * cy
        i0 = np.floor(u).astype(int)
        j0 = np.floor(v).astype(int)
        fu = _smooth(u - i0)
        fv = _smooth(v - j0)
        i1 = (i0 + 1) % cx
        j1 = (j0 + 1) % cy
        i0 %= cx
        j0 %= cy
        if ctc > 1:
            w = t / float(T) * ctc
            k0 = int(math.floor(w)) % ctc
            k1 = (k0 + 1) % ctc
            fw = _smooth(w - math.floor(w))
        else:
            k0 = k1 = 0
            fw = 0.0
        a = lat[k0][j0, i0] * (1 - fu) + lat[k0][j0, i1] * fu
        b = lat[k0][j1, i0] * (1 - fu) + lat[k0][j1, i1] * fu
        c0 = a * (1 - fv) + b * fv
        if ctc > 1:
            a = lat[k1][j0, i0] * (1 - fu) + lat[k1][j0, i1] * fu
            b = lat[k1][j1, i0] * (1 - fu) + lat[k1][j1, i1] * fu
            c1 = a * (1 - fv) + b * fv
            c0 = c0 * (1 - fw) + c1 * fw
        out[t] = c0
    return out


def hash_field(seed, salt=0):
    """Statisches 32x32-Feld aus Einzel-Hashes (0..1), periodisch trivial."""
    f = np.zeros((32, 32))
    for y in range(32):
        for x in range(32):
            f[y, x] = hsh(x, y, seed, salt)
    return f


# ====================================================================== Blob47-Autotile
def corners_of(mask):
    """Relevante Ecken (nur wenn beide angrenzenden Seiten verbunden sind): Liste von 'NE','SE','SW','NW'."""
    out = []
    if mask & 1 and mask & 2:
        out.append('NE')
    if mask & 2 and mask & 4:
        out.append('SE')
    if mask & 4 and mask & 8:
        out.append('SW')
    if mask & 8 and mask & 1:
        out.append('NW')
    return out


def build_blob47():
    """Alle 47 Kombinationen (mask N1 E2 S4 W8, fehlende Ecken als Menge) in fester Reihenfolge."""
    out = []
    for mask in range(16):
        cs = corners_of(mask)
        for sub in range(1 << len(cs)):
            out.append((mask, frozenset(c for k, c in enumerate(cs) if sub >> k & 1)))
    assert len(out) == 47
    return out


BLOB47 = build_blob47()
COLS47 = 12                       # Kacheln je Zeile im Sheet (4 Zeilen = 48 Plaetze je Frame)
ROWS47 = 4


def idx_of(mask, notches=frozenset()):
    return BLOB47.index((mask, frozenset(notches)))


def name_of(i):
    m, n = BLOB47[i]
    return 'm%02d%s' % (m, ('_n' + ''.join(sorted(n))) if n else '')


def mask_from_map(wet, x, y):
    """Maske und fehlende Ecken fuer Zelle (x, y) in einer Menge wet = {(x, y)} (y nach unten)."""
    m = 0
    if (x, y - 1) in wet:
        m |= 1
    if (x + 1, y) in wet:
        m |= 2
    if (x, y + 1) in wet:
        m |= 4
    if (x - 1, y) in wet:
        m |= 8
    notch = set()
    for c, (dx, dy) in {'NE': (1, -1), 'SE': (1, 1), 'SW': (-1, 1), 'NW': (-1, -1)}.items():
        if c in corners_of(m) and (x + dx, y + dy) not in wet:
            notch.add(c)
    return m, frozenset(notch)


def wob(side, t, amp=1.0):
    """Organische Uferlinie: ganze Halbwellen, an den Kachelenden (t=0 und t=31) exakt 0 -> Nachbarkacheln passen."""
    ph = {'N': 0.0, 'E': 1.7, 'S': 3.1, 'W': 4.6}[side]
    a = math.pi * t / 31.0                                   # sin(k*pi*t/31): exakt 0 bei t=0 und t=31
    v = 1.3 * math.sin(a) * math.cos(ph) + 1.0 * math.sin(2 * a) * math.cos(ph * 2) + 0.7 * math.sin(3 * a) * math.cos(ph * 3)
    return int(round(v * amp))


class Shape:
    """Form einer Blob47-Kachel: innen (Wasser/Boden), Verbindungen, Distanzfelder (gecacht).
    M = Uferbreite (N/O/W), Ms = Uferbreite Sued (Standard = M; fuer Klippen/Mauern mit sichtbarer Vorderwand, z. B. 12)."""
    _cache = {}

    def __init__(self, mask, notches, M=6, R=9, amp=1.0, Ms=None):
        Ms = M if Ms is None else Ms
        key = (mask, frozenset(notches), M, R, amp, Ms)
        if key in Shape._cache:
            self.__dict__ = Shape._cache[key].__dict__
            return
        self.mask, self.notches, self.M, self.Ms = mask, frozenset(notches), M, Ms
        con = {'N': bool(mask & 1), 'E': bool(mask & 2), 'S': bool(mask & 4), 'W': bool(mask & 8)}
        self.con = con
        mar = {'N': M, 'E': M, 'S': Ms, 'W': M}
        ins = np.ones((32, 32), bool)
        for y in range(32):
            for x in range(32):
                ok = True
                if not con['N'] and y < M + wob('N', x, amp):
                    ok = False
                if not con['S'] and y > 31 - (Ms + wob('S', x, amp)):
                    ok = False
                if not con['W'] and x < M + wob('W', y, amp):
                    ok = False
                if not con['E'] and x > 31 - (M + wob('E', y, amp)):
                    ok = False
                for (cn, cw, sx, sy) in (('N', 'W', 1, 1), ('N', 'E', -1, 1), ('S', 'W', 1, -1), ('S', 'E', -1, -1)):
                    if not con[cn] and not con[cw]:             # runde Aussenecke
                        mx, my = mar[cw], mar[cn]
                        ox = x if sx == 1 else 31 - x
                        oy = y if sy == 1 else 31 - y
                        if ox < mx + R and oy < my + R and math.hypot(ox + .5 - (mx + R), oy + .5 - (my + R)) > R:
                            ok = False
                for c in self.notches:                            # Innenecke: Kreis um die Kachelecke
                    cx, cy = {'NE': (32, 0), 'SE': (32, 32), 'SW': (0, 32), 'NW': (0, 0)}[c]
                    rx_, ry_ = M + 0.5, (Ms if c[0] == 'S' else M) + 0.5          # Ellipse: Breite = Ufer O/W, Hoehe = Ufer N bzw. S
                    if ((x + .5 - cx) / rx_) ** 2 + ((y + .5 - cy) / ry_) ** 2 < 1.0:
                        ok = False
                ins[y, x] = ok
        self.ins = ins
        P = 14
        # Aussenraum der Kachel: Randpixel werden fortgesetzt (Nachbarkachel hat an der Naht dieselbe Maske, siehe seam-Test)
        idx = np.clip(np.arange(-P, 32 + P), 0, 31)
        ext = ins[np.ix_(idx, idx)]
        self.ext, self.P = ext, P
        # Distanzen: innen -> naechstes "nicht innen", aussen -> naechstes "innen"
        out_pts = np.argwhere(~ext)
        in_pts = np.argwhere(ext)
        D = np.zeros((32, 32))
        OD = np.zeros((32, 32))
        for y in range(32):
            for x in range(32):
                p = np.array([y + P, x + P])
                if ins[y, x]:
                    D[y, x] = min(9.0, float(np.min(np.hypot(out_pts[:, 0] - p[0], out_pts[:, 1] - p[1]))) if len(out_pts) else 9.0)
                else:
                    OD[y, x] = min(14.0, float(np.min(np.hypot(in_pts[:, 0] - p[0], in_pts[:, 1] - p[1]))) if len(in_pts) else 14.0)
        self.D, self.OD = D, OD                                    # D: 0.5..9 innen, OD: 0.5..14 aussen
        Shape._cache[key] = self

    def face_depth(self, x, y):
        """Fuer Aussenpixel: Abstand (1..) zur naechsten Innenflaeche DIREKT darueber (Nordseite) - Vorderwand von Klippen/Mauern; 0 = keine."""
        if self.ins[y, x]:
            return 0
        for k in range(1, 16):
            yy = y - k + self.P
            if self.ext[yy, x + self.P]:
                return k
        return 0


# ====================================================================== Bild-Helfer
def to_img(grid):
    """grid[y][x] = RGBA-Tuple oder None -> 32x32 RGBA-Bild."""
    h, w = len(grid), len(grid[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            c = grid[y][x]
            if c is not None:
                px[x, y] = c
    return im


def terrain_grass(i=0):
    """Gras-Kachel aus dem bestehenden Tileset_Terrain (Zeile 4, Spalte 0-7), damit Ufer nahtlos an die Wiese passen."""
    ts = Image.open(ART + '/Tiles/Tileset_Terrain.png').convert('RGBA')
    return ts.crop((i * 32, 4 * 32, i * 32 + 32, 4 * 32 + 32))


def write_sheet(path, tiles, cols):
    """tiles: Liste von 32x32-Bildern (oder None) -> Sheet mit cols Spalten."""
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new('RGBA', (cols * 32, rows * 32), (0, 0, 0, 0))
    for i, t in enumerate(tiles):
        if t is not None:
            im.paste(t, ((i % cols) * 32, (i // cols) * 32))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return im


def write_strip(path, frames):
    w, h = frames[0].size
    im = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.paste(f, (i * w, 0))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return im


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write('\n')


# ====================================================================== Pruefungen
def check_palette(im, name=''):
    """Fehlermeldungen: Farben ausserhalb Palette.png oder halbtransparente Pixel."""
    im = im.convert('RGBA')
    errs = []
    bad = [c for _, c in im.getcolors(10 ** 7) if c[3] > 0 and (c[:3] not in PALETTE or c[3] != 255)]
    if bad:
        errs.append('%s: %d Fremdfarben/Halbalpha, z. B. %s' % (name, len(bad), ['%02x%02x%02x/%d' % (c[0], c[1], c[2], c[3]) for c in bad[:3]]))
    return errs


def check_loop(frames, name=''):
    """Schleifen-Pruefung: letzter Frame darf dem ersten nicht gleichen (sonst Ruckler), und es muss Bewegung geben."""
    errs = []
    a = [np.array(f.convert('RGBA')) for f in frames]
    if len(a) > 1 and all(np.array_equal(a[0], x) for x in a[1:]):
        errs.append('%s: Animation ohne Bewegung' % name)
    if len(a) > 2 and np.array_equal(a[0], a[-1]):
        errs.append('%s: letzter Frame == erster (doppelter Frame in der Schleife)' % name)
    return errs


def seam_report(cells, getter, name=''):
    """Naht-Test fuer ein Raster aus Kacheln. cells: {(x,y): Bild}. Misst die Farbdifferenz ueber Kachelgrenzen gegenueber der
    typischen Differenz benachbarter Pixelspalten/-zeilen innerhalb der Kacheln. Rueckgabe: (Verhaeltnis, schlechteste Stelle)."""
    inner, border = [], []
    for (x, y), im in cells.items():
        a = np.array(im.convert('RGB')).astype(int)
        inner.append(np.abs(np.diff(a, axis=1)).mean())
        inner.append(np.abs(np.diff(a, axis=0)).mean())
        if (x + 1, y) in cells:
            b = np.array(cells[(x + 1, y)].convert('RGB')).astype(int)
            border.append((np.abs(a[:, -1] - b[:, 0]).mean(), (x, y, 'E')))
        if (x, y + 1) in cells:
            b = np.array(cells[(x, y + 1)].convert('RGB')).astype(int)
            border.append((np.abs(a[-1, :] - b[0, :]).mean(), (x, y, 'S')))
    if not border:
        return 1.0, None
    typ = max(1e-6, float(np.mean(inner)))
    worst = max(border, key=lambda t: t[0])
    return worst[0] / typ, worst[1]
