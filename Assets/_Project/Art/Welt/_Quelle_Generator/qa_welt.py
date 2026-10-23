"""QA fuer alles unter Art/Welt (ohne _Vorschau): Palette, Alpha, Rastermasse, Frames, Schleifen, leere Dateien, Layout-JSONs.
Aufruf: python qa_welt.py        Rueckgabe 0 = alles gut, 1 = Fehler (werden aufgelistet)
Ergebnis liefert zusaetzlich die Datenbasis fuer _Liste.txt / _Assets.json (siehe build_welt.py)."""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

import welt_lib as W

FRAMES16 = {'Fisch_Forelle_Sprung', 'Fisch_Karpfen_Sprung'}
NO_LOOP_CHECK = FRAMES16                                  # Sprung-Sheets enthalten leere Anfangs-/Endframes (Absicht)
GRID_SHEETS = {'Fisch_': (8, 4)}                          # Schwimm-Sheets: 8 Frames x 4 Richtungen


def classify(path):
    rel = os.path.relpath(path, W.WELT).replace('\\', '/')
    zone, sub = rel.split('/')[0], rel.split('/')[1]
    return rel, zone, sub, os.path.basename(path)[:-4]


def collect():
    items = []
    for p in sorted(glob.glob(W.WELT + '/*/*/*.png')):
        rel, zone, sub, name = classify(p)
        if zone.startswith('_'):
            continue
        items.append((p, rel, zone, sub, name))
    return items


def analyse(path, rel, zone, sub, name):
    """Gibt (Eintrag-dict, Fehlerliste) zurueck."""
    errs = []
    im = Image.open(path)
    if im.mode != 'RGBA':
        errs.append('%s: Modus %s (erwartet RGBA)' % (rel, im.mode))
    im = im.convert('RGBA')
    a = np.array(im)
    w, h = im.size
    errs += W.check_palette(im, rel)
    if not (a[:, :, 3] > 0).any():
        errs.append('%s: komplett transparent' % rel)
    entry = {'datei': rel, 'zone': zone, 'ordner': sub, 'groesse': [w, h]}
    if sub == 'Tileset':
        if name.startswith('Boden_'):
            entry.update(art='Boden', zellen=[32, 32], spalten=w // 32, zeilen=1)
            if (w, h) != (128, 32):
                errs.append('%s: Boden muss 128x32 sein (4 Varianten)' % rel)
            # nahtlos: Rand-Differenz je Variante gegen typische Nachbarpixel-Differenz
            rgb = a[:, :, :3].astype(int)
            for v in range(w // 32):
                t = rgb[:, v * 32:(v + 1) * 32]
                dx = np.abs(t[:, -1] - t[:, 0]).mean()
                dy = np.abs(t[-1] - t[0]).mean()
                ref = max(1e-6, (np.abs(np.diff(t, axis=1)).mean() + np.abs(np.diff(t, axis=0)).mean()) / 2)
                if dx / ref > 2.0 or dy / ref > 2.0:
                    errs.append('%s: Variante %d nicht nahtlos (Rand/innen x %.2f y %.2f)' % (rel, v, dx / ref, dy / ref))
        elif name == 'Bohlenweg':
            entry.update(art='Wegstuecke16', zellen=[32, 32], spalten=16, zeilen=1)
            if (w, h) != (512, 32):
                errs.append('%s: 512x32 erwartet' % rel)
        else:
            frames = h // 32
            entry.update(art='Autotile47', zellen=[32, 32], spalten=48, zeilen=frames, frames=frames)
            if w != 48 * 32 or h % 32:
                errs.append('%s: Autotile-Sheet muss 1536 px breit und Hoehe Vielfaches von 32 sein' % rel)
            else:
                filled = [(a[f * 32:(f + 1) * 32, i * 32:(i + 1) * 32, 3] > 0).any() for f in range(frames) for i in range(47)]
                if not all(filled):
                    errs.append('%s: leere Autotile-Kacheln' % rel)
                if (a[:, 47 * 32:, 3] > 0).any():
                    errs.append('%s: Spalte 47 muss leer sein' % rel)
                # Frame-Pruefung (animiert): Frames duerfen nicht alle gleich sein; letzter != erster (Fuellkachel idx 31)
                if frames > 1:
                    idx = W.idx_of(15)
                    fr = [a[f * 32:(f + 1) * 32, idx * 32:(idx + 1) * 32] for f in range(frames)]
                    if all(np.array_equal(fr[0], x) for x in fr[1:]):
                        errs.append('%s: Wasser bewegt sich nicht' % rel)
                    if np.array_equal(fr[0], fr[-1]):
                        errs.append('%s: letzter Frame == erster' % rel)
                    # Schleifenschluss: Sprung letzter->erster nicht groesser als der groesste Sprung sonst (+30%)
                    d = [np.abs(fr[i].astype(int) - fr[(i + 1) % frames].astype(int)).mean() for i in range(frames)]
                    if d[-1] > max(d[:-1]) * 1.3 + 1:
                        errs.append('%s: Schleifen-Sprung zu gross (%.1f vs max %.1f)' % (rel, d[-1], max(d[:-1])))
    elif sub in ('Animiert', 'Tiere', 'Objekte'):
        frames = 1
        if sub == 'Animiert':
            frames = 8
        if name in FRAMES16:
            frames = 16
        grid = None
        for pre, g in GRID_SHEETS.items():
            if name.startswith(pre) and 'Sprung' not in name and sub == 'Tiere':
                grid = g
                frames = g[0]
        if sub == 'Objekte':
            entry.update(art='Objekt', frames=1)
        elif sub == 'Tiere' and grid is None and name not in FRAMES16:
            frames = 1
            entry.update(art='Tier', frames=1)
        else:
            cw = w // frames
            if w % frames:
                errs.append('%s: Breite %d nicht durch %d Frames teilbar' % (rel, w, frames))
            rows = grid[1] if grid else 1
            ch = h // rows
            entry.update(art='Animation' if not grid else 'Tiere4Richtungen', zellen=[cw, ch], frames=frames, zeilen=rows)
            cells = [a[r * ch:(r + 1) * ch, f * cw:(f + 1) * cw] for r in range(rows) for f in range(frames)]
            for r in range(rows):
                row = [a[r * ch:(r + 1) * ch, f * cw:(f + 1) * cw] for f in range(frames)]
                if name not in NO_LOOP_CHECK:
                    if all(np.array_equal(row[0], x) for x in row[1:]):
                        errs.append('%s: Zeile %d ohne Bewegung' % (rel, r))
                    if frames > 2 and np.array_equal(row[0], row[-1]):
                        errs.append('%s: Zeile %d letzter Frame == erster' % (rel, r))
                empty = [i for i, c in enumerate(row) if not (c[:, :, 3] > 0).any()]
                if empty and name not in NO_LOOP_CHECK and 'Spritzer' not in name:
                    errs.append('%s: leere Frames %s' % (rel, empty))
            if grid:                                                                       # Fische duerfen den Zellrand nicht beruehren
                for i, c in enumerate(cells):
                    al = c[:, :, 3] > 0
                    if al[0].any() or al[-1].any() or al[:, 0].any() or al[:, -1].any():
                        if 'Elritzen' not in name:
                            errs.append('%s: Zelle %d beruehrt den Rand' % (rel, i))
    return entry, errs


def main(verbose=True):
    items = collect()
    entries, errs = [], []
    for p, rel, zone, sub, name in items:
        e, er = analyse(p, rel, zone, sub, name)
        entries.append(e)
        errs += er
    # Layout-JSONs
    for z in W.ZONEN.values():
        for js in glob.glob('%s/%s/Tileset/_Layout_*.json' % (W.WELT, z)):
            try:
                json.load(open(js, encoding='utf-8'))
            except Exception as ex:
                errs.append('%s: ungueltiges JSON (%s)' % (js, ex))
    if verbose:
        print('%d PNGs geprueft' % len(items))
        if errs:
            print('FEHLER (%d):' % len(errs))
            print('\n'.join(errs))
        else:
            print('QA: alles in Ordnung')
    return entries, errs


if __name__ == '__main__':
    sys.exit(1 if main()[1] else 0)
