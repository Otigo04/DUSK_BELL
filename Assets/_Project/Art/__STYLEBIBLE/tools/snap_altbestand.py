#!/usr/bin/env python3
"""Altbestand auf die Master-Palette snappen (in place, nur Dateien mit Verstoessen).

    python3 snap_altbestand.py [--pool allgemein|wasser|sumpf|alle] [--apply] <Ordner> ...

Ohne --apply nur Trockenlauf. Aendert nur Farben/Alpha, nie die Groesse. Dateien ohne Verstoss bleiben unberuehrt.
Achtung: Generatoren (build_welt.py, bk_build.py ...) schreiben die alten Farben beim naechsten Lauf wieder zurueck.
"""
import argparse, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_lib as S


def needs_snap(im):
    for k, c in im.getcolors(1 << 24) or []:
        if c[3] and (c[3] != 255 or c[:3] not in S.MASTER_RGB):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--pool", default="allgemein", choices=sorted(S.POOLS))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    todo = changed = 0
    for root in a.paths:
        for r, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in S.SKIP_DIRS and not d.startswith("_Backup")]
            for n in sorted(files):
                if not n.lower().endswith(".png") or any(k in n for k in S.SKIP_NAMES):
                    continue
                p = os.path.join(r, n)
                im = Image.open(p).convert("RGBA")
                if not needs_snap(im):
                    continue
                todo += 1
                if a.apply:
                    S.snap_image(im, a.pool).save(p)
                    changed += 1
    print(f"{todo} Dateien mit Verstoessen; {'geschrieben: %d' % changed if a.apply else 'Trockenlauf, nichts geschrieben'} (Pool {a.pool})")


if __name__ == "__main__":
    main()
