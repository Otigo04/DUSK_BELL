"""WELT-TILE-ENGINE: 47er-Blob-Autotile-Sheets, nahtlose Bodenkacheln, Vorschau-Karten, Pruefungen.

build_blob(path, inside, outside, frames, M, Ms, R, amp)
    inside(sh, x, y, t)  -> RGBA   Pixel der "Innenflaeche" (Wasser/Boden/Plateau/Mauer), t = Frame
    outside(sh, x, y)    -> RGBA   Pixel ausserhalb (Ufer/Wand/Hintergrund), statisch
    Sheet: 48 Spalten (Blob-Index 0..46, Spalte 47 leer) x `frames` Zeilen; Reihenfolge siehe welt_lib.BLOB47 / _Layout_*.json
floor_set(path, fn, n)   n nahtlose 32x32-Bodenkacheln nebeneinander (fn(x, y, variante) -> RGBA, nur periodische Eingaben!)
preview_blob(...)        Testkarte aus einem Sheet (genau wie Unity-Autotile zusammengesetzt)
Pruefung: seam_ok(sheet)  vergleicht alle Nachbarpaare zufaelliger Karten (Farbsprung an der Naht <= 2x Pixel-zu-Pixel-Varianz im Inneren)
"""
import os
import random

import numpy as np
from PIL import Image

import welt_lib as W


def build_blob(path, inside, outside, frames=1, M=6, Ms=None, R=9, amp=1.0):
    sheet = np.zeros((frames * 32, 48 * 32, 4), np.uint8)
    for i, (m, n) in enumerate(W.BLOB47):
        sh = W.Shape(m, n, M=M, R=R, amp=amp, Ms=Ms)
        for t in range(frames):
            for y in range(32):
                for x in range(32):
                    c = inside(sh, x, y, t) if sh.ins[y, x] else outside(sh, x, y)
                    sheet[t * 32 + y, i * 32 + x] = c
    im = Image.fromarray(sheet, 'RGBA')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return im


def floor_set(path, fn, n=4):
    im = np.zeros((32, n * 32, 4), np.uint8)
    for v in range(n):
        for y in range(32):
            for x in range(32):
                im[y, v * 32 + x] = fn(x, y, v)
    out = Image.fromarray(im, 'RGBA')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path)
    return out


def split_floor(im, n=4):
    return [im.crop((i * 32, 0, i * 32 + 32, 32)) for i in range(n)]


def tile_at(sheet, mask, notch, frame=0):
    i = W.idx_of(mask, notch)
    return sheet.crop((i * 32, frame * 32, i * 32 + 32, frame * 32 + 32))


DEFAULT_MAP = [
    "..........~~~.......",
    "..........~~~~......",
    "...........~~.......",
    "....~~~~~..~~~......",
    "...~~~~~~~~~~.......",
    "...~~~~~~~~~~..~....",
    "....~~~~~~..~~~~~...",
    ".....~~~....~~~~~~..",
    "..........~~~~~~~~..",
    "..........~~~.......",
    "..........~~........",
    "..........~~~.......",
]


def render_map(sheet, mp, land, frame=0, face=None):
    """mp: Liste von Strings ('~' = Autotile-Zelle). land: 32x32-Bild (oder Liste, zufaellig gewaehlt) fuer Zellen ohne Autotile."""
    wet = {(x, y) for y, r in enumerate(mp) for x, c in enumerate(r) if c == '~'}
    Wd, Hd = len(mp[0]), len(mp)
    im = Image.new('RGBA', (Wd * 32, Hd * 32))
    lands = land if isinstance(land, list) else [land]
    for y in range(Hd):
        for x in range(Wd):
            if (x, y) in wet:
                m, n = W.mask_from_map(wet, x, y)
                im.paste(tile_at(sheet, m, n, frame), (x * 32, y * 32))
            else:
                im.paste(lands[int(W.hsh(x, y, 1, 7) * len(lands))], (x * 32, y * 32))
    return im


def preview_blob(sheet, name, land, mp=None, frames=(0,), scale=1):
    od = W.WELT + '/_Vorschau'
    os.makedirs(od, exist_ok=True)
    outs = []
    for f in frames:
        im = render_map(sheet, mp or DEFAULT_MAP, land, f)
        if scale != 1:
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        p = '%s/%s_f%d.png' % (od, name, f)
        im.save(p)
        outs.append(p)
    return outs


def seam_ok(sheet, frames=1, limit=2.2, M=6, Ms=None, trials=40, R=9, amp=1.0):
    """Nahttest: Farbsprung an Kachelgrenzen (nur Nachbarn, die beide Autotile sind) im Verhaeltnis zur Varianz im Inneren. True wenn Mittel <= 1.2 und Maximum <= limit*Mittel+...,
    genauer: gibt (Mittelverhaeltnis, 95%-Wert, Formfehler) zurueck."""
    random.seed(11)
    a = np.array(sheet.convert('RGB')).astype(int)
    rat, shape_err = [], 0
    for _ in range(trials):
        wet = {(x, y) for x in range(8) for y in range(8) if random.random() < 0.62}
        for (x, y) in wet:
            mi, ni = W.mask_from_map(wet, x, y)
            i = W.idx_of(mi, ni)
            for dx, dy in ((1, 0), (0, 1)):
                if (x + dx, y + dy) in wet:
                    mj, nj = W.mask_from_map(wet, x + dx, y + dy)
                    j = W.idx_of(mj, nj)
                    t = 0
                    A = a[t * 32:(t + 1) * 32, i * 32:(i + 1) * 32]
                    B = a[t * 32:(t + 1) * 32, j * 32:(j + 1) * 32]
                    d = np.abs(A[:, -1] - B[:, 0]).mean() if dx else np.abs(A[-1, :] - B[0, :]).mean()
                    ref = max(1e-6, np.abs(np.diff(A, axis=1 if dx else 0)).mean())
                    rat.append(d / ref)
                    sa = W.Shape(mi, ni, M=M, Ms=Ms, R=R, amp=amp).ins
                    sb = W.Shape(mj, nj, M=M, Ms=Ms, R=R, amp=amp).ins
                    if dx and not np.array_equal(sa[:, 31], sb[:, 0]):
                        shape_err += 1
                    if dy and not np.array_equal(sa[31, :], sb[0, :]):
                        shape_err += 1
    return float(np.mean(rat)), float(np.percentile(rat, 95)), shape_err


def terrain_grass(i=0):
    return W.terrain_grass(i)


def layout_json(path, name, frames, extra=None):
    obj = {'name': name, 'tileSize': 32, 'ppu': 32, 'frames': frames, 'columns': 48, 'rows': frames,
           'layout': 'Spalte = Blob-Index 0..46 (47 = leer), Zeile = Animationsframe',
           'masken': 'Bit N=1 O=2 S=4 W=8 (gesetzt = Innenflaeche setzt sich in diese Richtung fort); fehlendeEcken = Diagonalzelle ist Aussen',
           'tiles': [{'index': i, 'maske': m, 'fehlendeEcken': sorted(n), 'name': W.name_of(i)} for i, (m, n) in enumerate(W.BLOB47)]}
    if extra:
        obj.update(extra)
    W.dump_json(path, obj)
