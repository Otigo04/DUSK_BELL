#!/usr/bin/env python3
"""Nightward Pixel Law - Linter.

    python3 pixel_lint.py <Datei|Ordner> ...        pruefen (Exit 1 bei Fehlern)
    python3 pixel_lint.py --kind char <Datei>       Klasse erzwingen (tile nature object item char portrait ui vfx)
    python3 pixel_lint.py --summary <Ordner>        nur Zusammenfassung pro Ordner
    python3 pixel_lint.py --report out.txt <Ordner> volle Abweichungsliste schreiben

Regeln: ../ART_STYLE.md. Fehler (E_*) = Asset nicht fertig. Warnungen (W_*) = Review.
"""
import argparse, collections, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_lib as S


def iter_pngs(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for r, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in S.SKIP_DIRS and not d.startswith("_Backup")]
            for f in sorted(files):
                if f.lower().endswith(".png") and not any(k in f for k in S.SKIP_NAMES):
                    yield os.path.join(r, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--kind", choices=sorted(S.KINDS))
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    n = bad = warned = 0
    codes = collections.Counter()
    bydir = collections.defaultdict(lambda: [0, 0])
    lines = []
    for f in iter_pngs(a.paths):
        kind = a.kind or S.guess_kind(f)
        try:
            err, warn = S.check_image(Image.open(f), kind)
        except Exception as e:
            err, warn = [f"E_LESEN {e}"], []
        n += 1
        d = os.path.dirname(f)
        bydir[d][0] += 1
        if err:
            bad += 1
            bydir[d][1] += 1
        if warn:
            warned += 1
        for m in err + warn:
            codes[m.split()[0]] += 1
        if err or warn:
            lines.append(f"{f} [{kind}]")
            lines += ["   " + m for m in err + warn]
    out = lines if not a.summary else []
    if a.report:
        open(a.report, "w").write("\n".join(lines) + "\n")
    if out:
        print("\n".join(out))
    if a.summary:
        for d, (t, b) in sorted(bydir.items()):
            print(f"{b:4d}/{t:<4d} fehlerhaft  {d}")
    print(f"\n{n} PNGs: {n - bad} ok, {bad} mit Fehlern, {warned} mit Warnungen | " +
          ", ".join(f"{k}={v}" for k, v in sorted(codes.items())))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
