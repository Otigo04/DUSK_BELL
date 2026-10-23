"""MONSTER-KLON-GRINSEN fuer die Portraits der menschlichen Figuren.
Portrait-Bibel: "Monster-Klone im Gegensprech nutzen dieselben Portraits wie das Original, nur mit dem Grinsen-Ausdruck";
Ausdruck Grinsen = Brauen normal, Augen Monsteraugen #d64a6a, Mund breit, Zaehne #f2ead8. Dialogue Bible: Tag 'grin' nur fuer Monster.
Offener Punkt der Portrait-Bibel: "Portrait-Set fuer das Monster-Klon-Grinsen (gemeinsam mit den Originalen)". Der Gast und die Hausfrau haben ihre
eigenen Reveal-Portraits (der_gast_reveal_1..3, die_hausfrau_reveal_1..3), hier geht es um die SIEBEN Menschen:
  Bulut, Ilhan, Veronica, Elenora, Mara, David, Can  ->  <name>_grin.png im jeweiligen portraits-Ordner (64x64).
Vorgehen (damit die Gesichter unveraendert bleiben): Basis = ruhiges Portrait. Augenweiss -> #d64a6a (mit dunklem Rand wie in der_gast_reveal_1),
Mund: das vorhandene Mundbild wird aus der Umgebung ueberdeckt, darueber das Grinsen-Muster aus der_gast_reveal_2 (Zaehne #f2ead8, dunkle Mundhoehle).
Aufruf: python portrait_grin.py   (schreibt die 7 Dateien + Vorschau_Grin.png neben dieses Skript)"""
import os
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.normpath(os.path.join(HERE, '..'))


def H(s):
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


EYE, TEETH = H('d64a6a'), H('f2ead8')
OL1, OL2 = H('1a1526'), H('2b2140')
WHITE = H('e8e0f0')
SKIN = {H('d19a7a'), H('8c5f4d'), H('5e3d33')}
DARK = {OL1, OL2, TEETH}

# Figur: (Ordner, ruhige Basis, Sprech-Frame A)
CAST = {
    'bulut': ('BULUT SHERIFF', 'bulut_calm', 'bulut_talk_A'),
    'ilhan': ('ILHAN BARTENDER', 'ilhan_neutral', 'ilhan_talk_A'),
    'veronica': ('DOCTOR VERONICA', 'veronica_calm', 'veronica_talk_A'),
    'elenora': ('MADAME ELENORA', 'elenora_calm', 'elenora_talk_A'),
    'mara': ('BAKER MARA', 'mara_calm', 'mara_talk_A'),
    'david': ('PASTOR DAVID', 'david_calm', 'david_talk_A'),
    'can': ('CAN', 'can_calm', 'can_talk_A'),
}


def load(path):
    return Image.open(path).convert('RGBA')


def template():
    """Grinsen-Muster aus der_gast_reveal_2: nur die Pixel, die gegenueber reveal_1 neu sind und Zahn/Mundhoehlen-Farbe haben."""
    r1 = load(os.path.join(CHAR, 'DER GAST/portraits/der_gast_reveal_1.png')).load()
    r2 = load(os.path.join(CHAR, 'DER GAST/portraits/der_gast_reveal_2.png')).load()
    tpl = {}
    for y in range(36, 50):
        for x in range(20, 45):
            if r2[x, y] != r1[x, y] and r2[x, y] in DARK:
                tpl[(x, y)] = r2[x, y]
    return tpl


def mouth_rows(calm, talk):
    """Mundhoehe: Bereich, in dem sich das Sprech-Frame vom ruhigen Bild unterscheidet (nur unteres Gesicht)."""
    a, b = calm.load(), talk.load()
    pts = [(x, y) for y in range(34, 52) for x in range(24, 41)
           if sum(abs(p - q) for p, q in zip(a[x, y], b[x, y])) > 24]
    if not pts:
        return None
    ys = [p[1] for p in pts]
    xs = [p[0] for p in pts]
    return (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, min(ys), max(ys)


def heal(img, mask):
    """Pixel in mask durch die haeufigste Nachbarfarbe (ohne Mund-Dunkelfarben) ersetzen."""
    px = img.load()
    out = {}
    for (x, y) in mask:
        cnt = Counter()
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                q = (x + dx, y + dy)
                if q in mask or not (0 <= q[0] < 64 and 0 <= q[1] < 64):
                    continue
                c = px[q]
                if c[3] and c not in DARK:
                    cnt[c] += 1
        if cnt:
            out[(x, y)] = cnt.most_common(1)[0][0]
    for k, c in out.items():
        px[k] = c


def make_grin(name, tpl):
    folder, base, talk = CAST[name]
    calm = load(os.path.join(CHAR, folder, 'portraits', base + '.png'))
    img = calm.copy()
    px = img.load()
    # 1) Augen: Weiss -> Monsterauge, dunkler Rand ueber und neben dem Auge (wie in der_gast_reveal_1)
    eye = [(x, y) for y in range(25, 31) for x in range(20, 45) if px[x, y] == WHITE]
    for (x, y) in eye:
        px[x, y] = EYE
    for (x, y) in eye:
        for dx, dy in ((0, -1), (-1, 0), (1, 0)):
            q = (x + dx, y + dy)
            if 0 <= q[0] < 64 and 0 <= q[1] < 64 and px[q] in SKIN:
                px[q] = OL2
    # 2) Mund: vorhandene Mundpixel (dunkel/Lippen) im unteren Gesicht ueberdecken, dann Grinsen-Muster
    m = mouth_rows(calm, load(os.path.join(CHAR, folder, 'portraits', talk + '.png')))
    cx, cy, y0, y1 = m if m else (31.5, 43.0, 40, 45)
    dx = int(round(cx - 31.5))
    dy = int(round(cy - 43.5))
    erase = set()
    for y in range(int(y0) - 1, int(y1) + 2):
        for x in range(26, 39):
            c = calm.load()[x, y]
            if c not in SKIN and c[3]:
                erase.add((x, y))
    heal(img, erase)
    for (x, y), c in tpl.items():
        xx, yy = x + dx, y + dy
        if 0 <= xx < 64 and 0 <= yy < 64:
            px[xx, yy] = c
    return calm, img


if __name__ == '__main__':
    tpl = template()
    rows = []
    for name, (folder, base, talk) in CAST.items():
        calm, grin = make_grin(name, tpl)
        out = os.path.join(CHAR, folder, 'portraits', name + '_grin.png')
        grin.save(out)
        rows.append((name, calm, grin))
    S = 4
    sh = Image.new('RGBA', (len(rows) * (64 * S + 8) + 8, 2 * (64 * S + 8) + 8), (60, 60, 80, 255))
    for i, (n, c, g) in enumerate(rows):
        sh.alpha_composite(c.resize((64 * S, 64 * S), Image.NEAREST), (8 + i * (64 * S + 8), 8))
        sh.alpha_composite(g.resize((64 * S, 64 * S), Image.NEAREST), (8 + i * (64 * S + 8), 16 + 64 * S))
    sh.save(os.path.join(HERE, 'Vorschau_Grin.png'))
    print('geschrieben:', ', '.join(n + '_grin.png' for n, _, _ in rows))
