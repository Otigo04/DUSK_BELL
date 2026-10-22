"""Hauptfiguren Mann/Frau: Essen (eat) und Trinken (drink), 8 Richtungen x 8 Frames, 56x56.

Nutzt die Pose-Engine aus gen_hauptfiguren_combat.py: rechte Hand fuehrt Brot bzw. Flasche zum Mund, linke Hand haengt.
Aufruf: python gen_eatdrink.py [Ausgabeordner]  -> <Ordner>/<Name>/<name>_<eat|drink>.png  und eatdrink_dauer.json
"""
import json
import os
import sys

from PIL import Image

import gen_hauptfiguren_combat as C
from gen_hauptfiguren import CELL, ORDER, SPECS, to_img

LH = (0.5, -4.0, -7.5)


def seq_eat():
    # (Hand rechts, Hoehe des Koerpers dy, Dauer, Stufe des Essens oder None)
    spec = [
        ((1.5, 3.8, -6.0), 0, 0.10, 2),
        ((3.2, 2.4, -0.5), 0, 0.09, 2),
        ((4.6, 1.2, 4.2), 0, 0.12, 2),     # an den Mund
        ((4.8, 1.2, 4.6), 1, 0.11, 1),     # beissen, kauen
        ((4.6, 1.2, 4.2), 0, 0.11, 1),
        ((4.8, 1.2, 4.6), 1, 0.11, 0),
        ((3.2, 2.4, -0.5), 0, 0.09, None),
        ((1.5, 3.8, -6.0), 0, 0.10, None),
    ]
    seq = []
    for rh, dy, du, st in spec:
        fx = [('prop', 'R', 'food', st)] if st is not None else []
        seq.append(dict(rh=rh, lh=LH, dy=dy, dur=du, fx=fx))
    return seq


def seq_drink():
    spec = [
        ((1.5, 3.8, -6.0), 0, 0.10, 0),
        ((3.2, 2.6, -0.5), 0, 0.09, 0),
        ((4.2, 1.6, 3.4), 0, 0.10, 1),     # Flasche kippen
        ((4.3, 1.5, 4.2), 0, 0.14, 2),     # trinken
        ((4.3, 1.5, 4.2), 1, 0.12, 2),     # Schluck
        ((4.2, 1.6, 3.6), 0, 0.10, 1),
        ((3.2, 2.6, -0.5), 0, 0.09, 0),
        ((1.5, 3.8, -6.0), 0, 0.10, None),
    ]
    seq = []
    for rh, dy, du, t in spec:
        fx = [('prop', 'R', 'bottle', t)] if t is not None else []
        seq.append(dict(rh=rh, lh=LH, dy=dy, dur=du, fx=fx))
    return seq


ANIMS = {'eat': seq_eat, 'drink': seq_drink}


def build(name, outdir):
    spec = SPECS[name]
    os.makedirs(outdir, exist_ok=True)
    durs = {}
    for an, fn in ANIMS.items():
        seq = fn()
        sheet = Image.new('RGBA', (len(seq) * CELL, 8 * CELL))
        for r, v in enumerate(ORDER):
            for c, pose in enumerate(seq):
                sheet.paste(to_img(C.render_pose(spec, v, pose)), (c * CELL, r * CELL))
        sheet.save(os.path.join(outdir, '%s_%s.png' % (name.lower(), an)))
        durs[an] = [p['dur'] for p in seq]
    return durs


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    res = {}
    for n in SPECS:
        res = build(n, os.path.join(base, n))
        print('ok', n)
    json.dump(res, open(os.path.join(base, 'eatdrink_dauer.json'), 'w'))
