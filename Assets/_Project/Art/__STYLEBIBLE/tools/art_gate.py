#!/usr/bin/env python3
"""Gate fuer geaenderte PNGs unter Art/ (Git-Hook und Claude-Hook).

    art_gate.py --staged     gestagte PNGs (pre-commit), Exit 1 bei Verstoss
    art_gate.py --worktree   geaenderte/neue PNGs im Arbeitsverzeichnis, Exit 2 bei Verstoss (Claude-Hook)
Regel: Datei in style_baseline.txt -> ignoriert. Sonst muss pixel_lint E_-fehlerfrei sein.
"""
import json, os, subprocess, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import style_lib as S
import pixel_guard as G


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=G.ART).stdout


def changed(mode):
    top = git("rev-parse", "--show-toplevel").strip()
    if mode == "staged":
        out = git("diff", "--cached", "--name-only", "--diff-filter=AM", "-z").split("\0")
    else:
        out = [l[3:].strip('"') for l in git("status", "--porcelain", "-uall").splitlines() if l[:2].strip() != "D"]
    return [os.path.join(top, p) for p in out if p.lower().endswith(".png")]


CACHE = os.path.join(HERE, ".gate_cache.json")   # nur Worktree-Modus: bereits bestandene Dateien nicht erneut pruefen


def main():
    mode = "staged" if "--staged" in sys.argv else "worktree"
    base = G.load_baseline()
    bad, fixed, n = [], [], 0
    try:
        cache = json.load(open(CACHE)) if mode == "worktree" else {}
    except (OSError, ValueError):
        cache = {}
    for f in changed(mode):
        rel = G.rel_art(f)
        if rel is None or not os.path.exists(f):
            continue
        st = os.stat(f)
        sig = [st.st_mtime_ns, st.st_size]
        if mode == "worktree" and cache.get(rel) == sig:
            continue
        err, warn = S.check_image(Image.open(f), S.guess_kind(rel))
        n += 1
        if rel in base:
            if not err:
                fixed.append(rel)
            continue
        if err:
            bad.append((rel, err))
        elif mode == "worktree":
            cache[rel] = sig
    if mode == "worktree":
        try:
            json.dump(cache, open(CACHE, "w"))
        except OSError:
            pass
    for r in fixed:
        print(f"[art_gate] {r} ist jetzt konform -> aus style_baseline.txt entfernen (pixel_lint.py --write-baseline)")
    if bad:
        print("PIXEL LAW VERLETZT (neue/bisher konforme PNGs, nicht in der Baseline):", file=sys.stderr)
        for rel, err in bad:
            print(f"  {rel}", file=sys.stderr)
            for e in err:
                print(f"     {e}", file=sys.stderr)
        print("Fix: Farben aus style_lib.P, Raster Vielfache von 16, Alpha nur 0/255 (siehe ART_STYLE.md). "
              "Nicht umgehen: weder Baseline erweitern noch --no-verify.", file=sys.stderr)
        sys.exit(1 if mode == "staged" else 2)
    if n and mode == "staged":
        print(f"[art_gate] {n} PNGs geprueft, ok")


if __name__ == "__main__":
    main()
