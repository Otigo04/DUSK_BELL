#!/usr/bin/env python3
"""Familien-Vergleich fuer neue Charaktere (ART_STYLE.md Abschnitt 12/13, Pflicht vor "fertig").

    python3 character_compare.py <Charakter-Ordner> [--out vergleich.png]

Sucht im Charakter-Ordner  *stand_8dir.png  (Sprite, Frame S/SW/W) und  portraits/*calm.png  und legt sie neben ALLE bestehenden Charaktere
(Characters/*/ANIMATIONS_8DIR und portraits). Schreibt ein Vergleichsbild (Koepfe 8x, Portraits 3x, ganze Figuren 4x) und druckt Kennzahlen:
Hautbreite/-hoehe, Gesichtsbeginn, Kinnzeile, Hautanteil Portrait, Figurenhoehe/-breite. Abweichungen ausserhalb der Referenzspannen werden markiert.
Das Bild ist mit den eigenen Augen zu bewerten; die Zahlen ersetzen das nicht.
"""
import argparse, os, statistics, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_lib as S

CHARS = os.path.join(S.ART, "Characters")
SK = {S.P[n] for n in ("haut_hell", "haut_mittel", "haut_schatten")}


def first_cell(path):
    st = Image.open(path).convert("RGBA")
    c = 48 if st.height % 48 == 0 and st.width % 48 == 0 else st.height
    return st.crop((0, 0, c, c)), st, c


def head_crop(cell, rows=22):
    bb = cell.getchannel("A").getbbox()
    cx = (bb[0] + bb[2]) // 2
    return cell.crop((cx - 14, bb[1] - 1, cx + 14, bb[1] + rows - 1)), bb


def skin_stats(cell, maxrows=22):
    bb = cell.getchannel("A").getbbox()
    px = cell.load()
    pts = [(x, y) for y in range(bb[1], min(bb[1] + maxrows, cell.height)) for x in range(cell.width)
           if px[x, y][3] == 255 and px[x, y][:3] in SK]
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return dict(w=max(xs) - min(xs) + 1, h=max(ys) - min(ys) + 1, top=min(ys) - bb[1], chin=max(ys) - bb[1] + 1,
                fig_h=bb[3] - bb[1], fig_w=bb[2] - bb[0])


def portrait_stats(path):
    im = Image.open(path).convert("RGBA")
    px = im.load()
    pts = [(x, y) for y in range(im.height) for x in range(im.width) if px[x, y][3] == 255 and px[x, y][:3] in SK]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return dict(w=max(xs) - min(xs) + 1, h=max(ys) - min(ys) + 1, share=100.0 * len(pts) / (im.width * im.height))


def find_refs(skip):
    refs = []
    for d in sorted(os.listdir(CHARS)):
        base = os.path.join(CHARS, d)
        if not os.path.isdir(base) or os.path.abspath(base) == os.path.abspath(skip):
            continue
        stand = [os.path.join(r, f) for r, _, fs in os.walk(base) for f in fs
                 if f.endswith("stand_8dir.png") and "OLD" not in r and "_Quelle" not in r]
        calm = [os.path.join(r, f) for r, _, fs in os.walk(base) for f in fs if f.endswith("_calm.png") and "portraits" in r]
        if stand or calm:
            refs.append((d.title(), stand[0] if stand else None, calm[0] if calm else None))
    return refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default="character_vergleich.png")
    a = ap.parse_args()
    new_stand = [os.path.join(r, f) for r, _, fs in os.walk(a.folder) for f in fs if f.endswith("stand_8dir.png")]
    new_calm = [os.path.join(r, f) for r, _, fs in os.walk(a.folder) for f in fs if f.endswith("calm.png") and "portraits" in r]
    if not new_stand and not new_calm:
        sys.exit("Keine *stand_8dir.png / portraits/*calm.png im Ordner gefunden")
    name = os.path.basename(os.path.abspath(a.folder))
    refs = find_refs(a.folder)
    sprites, ports, stats = [], [], []
    for n, st, pc in refs:
        if st:
            cell, _, c = first_cell(st)
            h, bb = head_crop(cell)
            sprites.append((n, h, cell.crop((bb[0] - 4, bb[1] - 1, bb[2] + 4, bb[3] + 1))))
            m = skin_stats(cell)
            if m:
                stats.append((n, "ref", m, portrait_stats(pc) if pc else None))
        if pc:
            ports.append((n, Image.open(pc).convert("RGBA")))
    if new_stand:
        st = Image.open(new_stand[0]).convert("RGBA")
        c = 48 if st.height % 48 == 0 and st.width % 48 == 0 else st.height
        for nm, i in (("S", 0), ("SW", 1), ("W", 2)):
            cell = st.crop((i * c, 0, i * c + c, c))
            h, bb = head_crop(cell)
            sprites.append((f"{name} {nm}", h, cell.crop((bb[0] - 4, bb[1] - 1, bb[2] + 4, bb[3] + 1))))
        stats.append((name, "NEU", skin_stats(st.crop((0, 0, c, c))), portrait_stats(new_calm[0]) if new_calm else None))
    if new_calm:
        ports.append((name, Image.open(new_calm[0]).convert("RGBA")))
    S_, W = 8, 28 * 8 + 6
    cols = 5
    rows1 = (len(sprites) + cols - 1) // cols
    rows2 = (len(ports) + 4) // 5
    out = Image.new("RGBA", (cols * W, rows1 * (22 * S_ + 22) + rows2 * 210 + (60 * 4 + 24)), (110, 110, 110, 255))
    d = ImageDraw.Draw(out)
    for k, (n, h, _) in enumerate(sprites):
        x, y = (k % cols) * W, (k // cols) * (22 * S_ + 22)
        out.alpha_composite(h.resize((28 * S_, 22 * S_), Image.NEAREST), (x, y + 18))
        d.text((x + 4, y + 3), n, fill=(255, 255, 255, 255))
    y0 = rows1 * (22 * S_ + 22)
    for k, (n, im) in enumerate(ports):
        x, y = (k % 5) * 196 + 4, y0 + (k // 5) * 210
        out.alpha_composite(im.resize((192, 192), Image.NEAREST), (x, y + 16))
        d.text((x + 4, y + 2), n, fill=(255, 255, 255, 255))
    y1 = y0 + rows2 * 210
    x = 4
    for n, _, fig in sprites:
        if n.endswith(" W") or n.endswith(" SW"):
            continue
        if x + fig.width * 3 > cols * W:
            break
        out.alpha_composite(fig.resize((fig.width * 3, fig.height * 3), Image.NEAREST), (x, y1 + 18))
        d.text((x + 2, y1 + 3), n[:14], fill=(255, 255, 255, 255))
        x += fig.width * 3 + 8
    out.convert("RGB").save(a.out)
    # Kennzahlen
    print(f"{'Figur':16s} {'Haut B':>6s} {'Haut H':>6s} {'Gesicht ab':>10s} {'Kinn':>5s} {'Fig H':>6s} {'Fig B':>6s} | Portrait Haut B  H  Anteil")
    for n, kind, m, p in stats:
        ps = f"{p['w']:5d} {p['h']:3d} {p['share']:5.1f}%" if p else "-"
        print(f"{n[:16]:16s} {m['w']:6d} {m['h']:6d} {m['top']:10d} {m['chin']:5d} {m['fig_h']:6d} {m['fig_w']:6d} | {ps}   {'<== NEU' if kind == 'NEU' else ''}")
    ref = [s for s in stats if s[1] == "ref"]
    new = [s for s in stats if s[1] == "NEU"]
    if ref and new:
        def span(f):
            v = [f(s) for s in ref]
            return min(v), statistics.median(v), max(v)
        def span2(f, need_port):
            v = [f(r) for r in ref if (r[3] or not need_port)]
            return min(v), statistics.median(v), max(v)
        checks = [("Sprite Haut-Breite", lambda s: s[2]["w"], False), ("Gesicht beginnt ab Zeile", lambda s: s[2]["top"], False),
                  ("Kinn bei Zeile", lambda s: s[2]["chin"], False), ("Figurenhoehe", lambda s: s[2]["fig_h"], False)]
        if new[0][3]:
            checks += [("Portrait Haut-Breite", lambda s: s[3]["w"], True), ("Portrait Haut-Hoehe", lambda s: s[3]["h"], True),
                       ("Portrait Hautanteil %", lambda s: s[3]["share"], True)]
        print("\nAbweichungen gegen die Familie (Referenzspanne min..max):")
        bad = 0
        for label, f, need_port in checks:
            lo, med, hi = span2(f, need_port)
            v = f(new[0])
            flag = "" if lo - 0.5 <= v <= hi + 0.5 else "   <== AUSSERHALB"
            bad += bool(flag)
            print(f"  {label:26s} neu {v:6.1f}   Familie {lo:5.1f} .. {hi:5.1f} (Median {med:5.1f}){flag}")
        print("\nAusserhalb der Spanne:", bad, "- Bild ansehen und ehrlich entscheiden. Kennzahlen ersetzen die Sichtpruefung nicht.")
    print("Vergleichsbild:", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
