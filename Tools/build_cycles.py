"""Baut Idle- und Walk-Zyklen komplett aus der Stand-Pose (8 Richtungen, 56x56-Rahmen).

Warum: Die Original-Sheets zeichnen Gesicht, Kleidung und Beine in jedem Frame neu. Hier bleibt jeder Pixel
von Kopf und Oberkoerper identisch zur Stand-Pose, nur Atmung, Gehwippen und die Beine bewegen sich.
Zeilenreihenfolge (wie die Sheets): S, SW, W, NW, N, NE, E, SE.

Aufruf aus dem Projektordner:  python Tools/build_cycles.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from faces import clean_stand  # noqa: E402

ROOT = 'Assets/_Project/Art/Characters/'
PALETTE_FILE = 'Assets/_Project/Art/Palette.gpl'


def _load_palette():
    import re
    pal = []
    for line in open(PALETTE_FILE, encoding='utf-8'):
        m = re.match(r'\s*(\d+)\s+(\d+)\s+(\d+)\s', line)
        if m:
            pal.append(tuple(int(v) for v in m.groups()))
    return pal


PALETTE = _load_palette()
_SHADE_CACHE = {}


def shade(rgb, factor=0.72):
    """Naechste Palettenfarbe zu einer abgedunkelten Variante (fuer das hintere Bein)."""
    if rgb not in _SHADE_CACHE:
        target = tuple(v * factor for v in rgb)
        _SHADE_CACHE[rgb] = min(PALETTE, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, target)))
    return _SHADE_CACHE[rgb]


def darken(img):
    out = img.copy()
    ys, xs = np.where(img[:, :, 3] > 0)
    for y, x in zip(ys, xs):
        out[y, x, :3] = shade(tuple(int(v) for v in img[y, x, :3]))
    return out

CELL = 56
# Vorwaertsrichtung auf der x-Achse je Zeile (0 = von vorn/hinten gesehen)
FORWARD = [0, -1, -1, -1, 0, 1, 1, 1]
# Schrittweite (px am Fuss) je Zeile
STRIDE = [0, 3, 6, 3, 0, 3, 6, 3]

# Basis -> (Anteil der Figurenhoehe, ab dem die Beine beginnen)
SETS = {
    # Beinansatz (Anteil der Hoehe), Beinbreite vorn/hinten und seitlich, Stiefelhoehe, Rumpf: Zeilen/Spalten weg
    # style: pants = (dunkel, mittel, hell), cuff = (Saum, Saumkante) oder None, boot = (Grundfarbe, Glanz, Sohle)
    'ILHAN BARTENDER/ANIMATIONS_8DIR/ilhan': dict(key='ilhan', frac=0.80, w=5, w_side=6, boots=5, cut_rows=4, cut_cols=2, arms=True,
        style=dict(pants=('#1f2a3d', '#2c3e56', '#3f5570'), cuff=('#4a4550', '#9a95a0'), boot=('#2b2140', '#4f3d5c', '#1a1526'))),
    'BULUT SHERIFF/ANIMATIONS_8DIR/bulut': dict(key='bulut', frac=0.82, w=5, w_side=6, boots=4, cut_rows=4, cut_cols=2, arms=True,
        style=dict(pants=('#2c3e56', '#3a4a7a', '#6b7fb8'), cuff=None, boot=('#5c4033', '#7a5a43', '#3b2a22'))),
    'DER GAST/ANIMATIONS_8DIR/der_gast_disguised': dict(key='gast', frac=0.76, w=5, w_side=6, boots=3, cut_rows=2, cut_cols=0,
        style=dict(pants=('#1a1526', '#2b2140', '#3d2e4a'), cuff=None, boot=('#3d2e4a', '#4f3d5c', '#1a1526'))),
    'DER GAST/ANIMATIONS_8DIR/der_gast_revealed': dict(key='gast_rev', frac=0.76, w=5, w_side=6, boots=3, cut_rows=2, cut_cols=0,
        style=dict(pants=('#1a1526', '#2b2140', '#3d2e4a'), cuff=None, boot=('#3d2e4a', '#4f3d5c', '#1a1526'))),
    'DIE HAUSFRAU/ANIMATIONS_8DIR/die_hausfrau_disguised': dict(key='hausfrau', frac=0.82, w=5, w_side=6, boots=3, cut_rows=2, cut_cols=0,
        style=dict(pants=('#3b2a22', '#5c4033', '#7a5a43'), cuff=None, boot=('#3b2a22', '#5c4033', '#1a1526'))),
    'DIE HAUSFRAU/ANIMATIONS_8DIR/die_hausfrau_revealed': dict(key='hausfrau_rev', frac=0.82, w=5, w_side=6, boots=3, cut_rows=2, cut_cols=0,
        style=dict(pants=('#3b2a22', '#5c4033', '#7a5a43'), cuff=None, boot=('#3b2a22', '#5c4033', '#1a1526'))),
}


def _hex(h):
    return tuple(int(h[k:k + 2], 16) for k in (1, 3, 5))


def resolve_style(style):
    return dict(pants=tuple(_hex(c) for c in style['pants']),
                cuff=tuple(_hex(c) for c in style['cuff']) if style['cuff'] else None,
                boot=tuple(_hex(c) for c in style['boot']))


def bbox_rows(img):
    ys = np.where((img[:, :, 3] > 0).any(axis=1))[0]
    return int(ys.min()), int(ys.max())


def paste(dst, src, dx=0, dy=0):
    """Legt src (nicht transparente Pixel) um (dx, dy) versetzt auf dst."""
    h, w = src.shape[:2]
    ys, xs = np.where(src[:, :, 3] > 0)
    for y, x in zip(ys, xs):
        ty, tx = y + dy, x + dx
        if 0 <= ty < dst.shape[0] and 0 <= tx < dst.shape[1]:
            dst[ty, tx] = src[y, x]


OUTLINE_COLORS = {(0x1a, 0x15, 0x26), (0x2b, 0x21, 0x40)}


def leg_colors(stand_cell, leg_top, bottom, pants_rows=None, boot_h=3):
    """Hosen-, Schatten- und Schuhfarbe aus den Beinen der Stand-Pose."""
    from collections import Counter
    region = stand_cell[leg_top:bottom + 1]
    shoe_c, pants_c = Counter(), Counter()
    for y in range(region.shape[0]):
        for x in range(CELL):
            if region[y, x, 3] == 0:
                continue
            c = tuple(int(v) for v in region[y, x, :3])
            if c in OUTLINE_COLORS:
                continue
            if y >= region.shape[0] - boot_h:
                shoe_c[c] += 1
            elif pants_rows is None or y < pants_rows:
                pants_c[c] += 1
    pants = pants_c.most_common(1)[0][0] if pants_c else (0x3a, 0x4a, 0x7a)
    shoe = shoe_c.most_common(1)[0][0] if shoe_c else (0x5c, 0x40, 0x33)
    return pants, shade(pants, 0.8), shoe, shade(shoe, 0.75)


def draw_leg(img, hip_x, hip_y, foot_x, foot_y, w, colors, tip=0, dark=False, boot_h=3):
    """Gerades Bein gleicher Breite w in jedem Frame. Outline aussen, Schattenspalte innen, Schuh unten, Spitze nach vorn (tip = -1/+1)."""
    pants, pants_shade, shoe, shoe_shade = colors
    outline = (0x1a, 0x15, 0x26)
    n = max(1, foot_y - hip_y)

    def put(y, x, col):
        if 0 <= y < CELL and 0 <= x < CELL:
            img[y, x, :3] = shade(col, 0.75) if (dark and col != outline) else col
            img[y, x, 3] = 255

    for y in range(hip_y, foot_y + 1):
        cx = hip_x + (foot_x - hip_x) * (y - hip_y) / n
        x0 = int(round(cx - w / 2.0))
        is_shoe = y > foot_y - boot_h
        sole = y == foot_y
        for i in range(w):
            if sole or i == 0 or i == w - 1:
                col = outline
            elif is_shoe:
                col = shoe_shade if i == w - 2 else shoe
            else:
                col = pants_shade if i == w - 2 else pants
            put(y, x0 + i, col)
        if tip and is_shoe:
            # Schuhspitze: 2 px nach vorn, Sohle und Rand in Outline
            for d in range(2):
                x = x0 + w + d if tip > 0 else x0 - 1 - d
                put(y, x, outline if (sole or d == 1) else shoe)


def _pick(diffs, n, lo, hi, spacing=3):
    """Waehlt n Positionen mit der kleinsten Aenderung zum Nachbarn (Inhalt bleibt, Duplikate fliegen raus)."""
    order = sorted(range(lo, hi), key=lambda i: diffs[i])
    chosen = []
    for i in order:
        if all(abs(i - j) >= spacing for j in chosen):
            chosen.append(i)
        if len(chosen) == n:
            break
    return sorted(chosen)


def reproportion(cell, top, neck, leg_top, n_rows, n_cols):
    """Verkuerzt und verschmaelert den Oberkoerper (Kopf bleibt): n_rows Zeilen und n_cols Spalten weniger.
    Die Beine werden dadurch laenger und der Rumpf wirkt nicht mehr massig."""
    if n_rows == 0 and n_cols == 0:
        return cell.copy(), leg_top
    out = np.zeros_like(cell)
    out[top:neck] = cell[top:neck]

    # Zeilen entfernen
    torso = list(range(neck, leg_top))
    row_diff = {i: int((cell[i, :, :] != cell[i + 1, :, :]).any(axis=1).sum()) for i in range(neck, leg_top - 1)}
    drop = set(_pick(row_diff, n_rows, neck + 2, leg_top - 3)) if n_rows else set()
    keep = [i for i in torso if i not in drop]
    for k, i in enumerate(keep):
        out[neck + k] = cell[i]
    new_leg_top = leg_top - n_rows

    # Spalten entfernen (nur Rumpfzeilen), abwechselnd links/rechts schieben, damit die Mitte bleibt
    if n_cols:
        rows = slice(neck, new_leg_top)
        block = out[rows]
        xs = np.where(block[:, :, 3].any(axis=0))[0]
        x0, x1 = int(xs.min()), int(xs.max())
        col_diff = {j: int((block[:, j] != block[:, j + 1]).any(axis=1).sum()) for j in range(x0, x1)}
        cols = _pick(col_diff, n_cols, x0 + 3, x1 - 2)
        for t, c in enumerate(reversed(cols)):
            if t % 2 == 0:  # linke Seite nach rechts ruecken
                block[:, 1:c + 1] = block[:, 0:c].copy()
                block[:, 0] = 0
            else:           # rechte Seite nach links ruecken
                block[:, c:-1] = block[:, c + 1:].copy()
                block[:, -1] = 0
        out[rows] = block
    return out, new_leg_top


SKIN_TONES = {(0xd1, 0x9a, 0x7a), (0x8c, 0x5f, 0x4d), (0x5e, 0x3d, 0x33)}


def swing_arms(upper, row, neck, leg_top, sinp):
    """Armschwung nur fuer Figuren mit freien Armen. Gegenlaeufig zu den Beinen.
    Vorn/hinten und diagonal: die beiden Aussenarme heben/senken sich (Schulter bleibt).
    Seitlich: der Unterarm samt Hand pendelt um den Ellbogen, der Rest des Koerpers bleibt stehen."""
    out = upper.copy()
    fwd = FORWARD[row]
    rows = range(neck + 3, leg_top)
    if row in (2, 6):  # reine Seitenansicht: Unterarm pendelt
        elbow = leg_top - 9
        k = -fwd * 2.0 * sinp
        span = max(1, leg_top - elbow)
        moved = []
        for y in range(elbow, leg_top):
            shift = int(round(k * (y - elbow + 1) / span))
            if shift == 0:
                continue
            for x in range(CELL):
                if out[y, x, 3] > 0 and tuple(int(v) for v in out[y, x, :3]) in SKIN_TONES:
                    moved.append((y, x, shift, out[y, x].copy()))
        for y, x, shift, px in moved:
            # Luecke mit der Farbe des Stoffs daneben fuellen, damit kein Loch im Koerper bleibt
            left = out[y, x - 1] if x > 0 else out[y, x]
            right = out[y, x + 1] if x < CELL - 1 else out[y, x]
            cand = [c for c in (left, right) if c[3] > 0 and tuple(int(v) for v in c[:3]) not in SKIN_TONES]
            out[y, x] = cand[0] if cand else out[y - 1, x]
        for y, x, shift, px in moved:
            tx = x + shift
            if 0 <= tx < CELL:
                out[y, tx] = px
        return out

    # Aussenarme: je 5 Spalten vom Silhouettenrand. Die Schulter bleibt fest, der Arm wird nach unten gestreckt
    # bzw. gestaucht (Arm schwingt vor/zurueck), so reisst nichts von der Schulter ab.
    d = int(round(2.0 * sinp))
    if d == 0:
        return out
    ys = [y for y in rows if out[y, :, 3].any()]
    if not ys:
        return out
    xmin = min(int(np.where(out[y, :, 3] > 0)[0].min()) for y in ys)
    xmax = max(int(np.where(out[y, :, 3] > 0)[0].max()) for y in ys)
    a0, a1 = neck + 3, leg_top - 1
    length = a1 - a0 + 1
    for sgn, (a, b) in ((-1, (xmin, xmin + 4)), (1, (xmax - 4, xmax))):
        block = out[a0:a1 + 1, a:b + 1].copy()
        out[a0:a1 + 1, a:b + 1] = 0
        new_len = max(4, length + d * (-sgn))  # linker und rechter Arm laufen gegeneinander
        for y2 in range(new_len):
            src = min(length - 1, int(y2 * length / new_len))
            ty = a0 + y2
            if 0 <= ty < CELL:
                out[ty, a:b + 1] = block[src]
    return out


def frame_cell(stand_cell, row, leg_top, bob, phase=None, colors=None, leg_w=6, boot_h=3, leg_w_side=8, bottom=None, arms=False, neck=None):
    """Ein Rahmen: Oberkoerper (Stand-Pose), darunter gegliederte Beine; Idle = Phase ohne Schritt."""
    import legs as legmod
    top, own_bottom = bbox_rows(stand_cell)
    bottom = own_bottom if bottom is None else bottom  # Fusspunkt der urspruenglichen Figur
    upper = stand_cell.copy()
    upper[leg_top:] = 0

    xs = np.where(stand_cell[leg_top - 3, :, 3] > 0)[0]  # Figurenmitte am Rumpfende
    cx = (xs.min() + xs.max() + 1) / 2.0
    fwd = FORWARD[row]
    idle = phase is None
    hip_y = leg_top - 2
    shape = (CELL, CELL)
    if fwd == 0:
        widths = (leg_w, leg_w, leg_w, leg_w)
        legs_img, drop = legmod.render_front(shape, cx, hip_y, bottom, phase or 0.0, widths, colors, boot_h, shade, idle)
    else:
        sw = leg_w_side
        widths = (sw, sw - 1, sw - 1, max(3, sw - 2))
        amp = 0.50 if row in (2, 6) else 0.38  # Diagonalen: kuerzerer Schritt
        legs_img, drop = legmod.render_side(shape, cx, hip_y, bottom, fwd, phase or 0.0, amp, widths, colors, boot_h, shade, idle)
    if arms and not idle and neck is not None:
        upper = swing_arms(upper, row, neck, leg_top, math.sin(2 * math.pi * phase))
    out = legs_img
    paste(out, upper, 0, bob if idle else int(round(drop)))
    return out


def build(stand_path, out_idle, out_walk, cfg):
    stand = clean_stand(np.array(Image.open(stand_path).convert('RGBA')), cfg['key'])
    Image.fromarray(stand).save(stand_path.replace('_stand_8dir.png', '_stand_clean.png'))

    idle_bob = [0, 0, 0, 1, 1, 0]
    walk_bob = [1, 1, 0, 0, 1, 1, 0, 0]
    idle = np.zeros((8 * CELL, 6 * CELL, 4), dtype=np.uint8)
    walk = np.zeros((8 * CELL, 8 * CELL, 4), dtype=np.uint8)
    # Hosen- und Schuhfarben immer aus der Vorderansicht (unveraenderte Stand-Pose): seitlich verdeckt der Schuh die Hose
    colors = resolve_style(cfg['style'])
    for r in range(8):
        cell = stand[0:CELL, r * CELL:(r + 1) * CELL]
        top, bottom = bbox_rows(cell)
        neck = int(top + (bottom - top) * 0.36)
        leg_top = int(top + (bottom - top) * cfg['frac'])
        cell, leg_top = reproportion(cell, top, neck, leg_top, cfg['cut_rows'], cfg['cut_cols'])
        for c, bob in enumerate(idle_bob):
            idle[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = frame_cell(cell, r, leg_top, bob, None, colors, cfg['w'], cfg['boots'], cfg['w_side'], bottom, cfg.get('arms', False), neck)
        for c, bob in enumerate(walk_bob):
            walk[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = frame_cell(cell, r, leg_top, bob, c / 8.0, colors, cfg['w'], cfg['boots'], cfg['w_side'], bottom, cfg.get('arms', False), neck)
    Image.fromarray(idle).save(out_idle)
    Image.fromarray(walk).save(out_walk)


if __name__ == '__main__':
    for base, cfg in SETS.items():
        build(ROOT + base + '_stand_8dir.png', ROOT + base + '_idle_fixed.png', ROOT + base + '_walk_fixed.png', cfg)
        print('ok', base)
