"""Kleidung: 10 Oberteile, 10 Hosen, 10 Schuhe. Quelle der Daten UND der 32x32-Icons.

Schreibt  Art/Items/Kleidung/kleidung.json  (liest der ItemCatalog in Unity) und Art/Items/Kleidung/Item_<id>.png.
Die Figur wird zur Laufzeit umgefaerbt (PlayerOutfit): jedes Stueck bringt eine Palette mit, in der Reihenfolge der Masken
  Oberteil: Licht, Grund, Schatten, Tief      Hose: Dunkel, Grund, Licht      Schuhe: Sohle, Dunkel, Grund, Licht
Farben nur aus der Nightward-Palette. Aufruf: python gen_kleidung.py
Effekte: ('rate', Stat, Wert) aendert die Rate, ('drain', Stat, Faktor) verlangsamt/beschleunigt Verschlechterung, ('recover', Stat, Faktor),
('game', EffectKind, Faktor) z. B. DamageTakenMult 0.9."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'Items', 'Kleidung'))
K = (0x1a, 0x15, 0x26, 255)

# ------------------------------------------------------------------ Daten
# id, Name, Beschreibung, Seltenheit, Wert, Palette, Effekte, Form, Extras
TOPS = [
    ('linen_shirt', 'Linen Shirt', 'Light and plain.', 'Common', 4, ['#fff1c9', '#f2ead8', '#9a95a0', '#6e6a74'], [], 'shirt', []),
    ('flannel_shirt', 'Flannel Shirt', 'Red check, worn soft.', 'Common', 6, ['#d64a6a', '#8a1f3d', '#5e3d33', '#2b2140'], [('drain', 'Cold', 0.92)], 'shirt', ['check']),
    ('work_jacket', 'Work Jacket', 'Stiff canvas with deep pockets.', 'Common', 8, ['#b89a72', '#9c7a5a', '#7a5a43', '#5c4033'], [('drain', 'Cold', 0.88)], 'jacket', ['pockets']),
    ('wool_coat', 'Wool Coat', 'Keeps the night chill out.', 'Uncommon', 12, ['#e8e0f0', '#6b7fb8', '#3a4a7a', '#2b2140'], [('drain', 'Cold', 0.55)], 'coat', ['buttons']),
    ('hunting_jacket', 'Hunting Jacket', 'Green, quiet, full of loops.', 'Uncommon', 14, ['#9ab87a', '#4a7a4f', '#2f5a3c', '#1e3a2b'], [('drain', 'Cold', 0.8), ('game', 'ReactionWindowMult', 1.05)], 'jacket', ['pockets', 'zip']),
    ('oilskin_coat', 'Oilskin Coat', 'Waxed against the rain.', 'Uncommon', 16, ['#a8f0ff', '#2b6b8a', '#2c3e56', '#1f2a3d'], [('drain', 'Cold', 0.7), ('drain', 'Fatigue', 0.9)], 'coat', ['buttons']),
    ('leather_jacket', 'Leather Jacket', 'Takes a bite and keeps its shape.', 'Rare', 30, ['#8c5f4d', '#5e3d33', '#3b2a22', '#1a1526'], [('drain', 'Cold', 0.85), ('game', 'DamageTakenMult', 0.9)], 'jacket', ['zip', 'pockets']),
    ('cassock', 'Black Cassock', 'The pastor wore one like it.', 'Rare', 32, ['#6b5a7a', '#3d2e4a', '#2b2140', '#1a1526'], [('rate', 'Sanity', 1.2), ('rate', 'Stress', -1.0)], 'robe', ['buttons']),
    ('doctor_coat', "Doctor's Coat", 'Spotless, mostly.', 'Rare', 34, ['#fff1c9', '#e8e0f0', '#9a95a0', '#6e6a74'], [('rate', 'Health', 0.6), ('recover', 'Pain', 1.3)], 'coat', ['pockets']),
    ('fur_coat', 'Fur-lined Coat', 'Heavy, warm and unforgettable.', 'Unique', 60, ['#d19a7a', '#8c5f4d', '#5c4033', '#3b2a22'], [('drain', 'Cold', 0.35), ('game', 'MoveSpeedMult', 0.97)], 'coat', ['fur']),
]
LEGS = [
    ('blue_jeans', 'Blue Jeans', 'The ones you started in.', 'Common', 4, ['#1f2a3d', '#2c3e56', '#3f5570'], [], 'trousers', []),
    ('work_trousers', 'Work Trousers', 'Brown and patched at the knees.', 'Common', 5, ['#5c4033', '#7a5a43', '#9c7a5a'], [], 'trousers', ['pockets']),
    ('canvas_pants', 'Canvas Pants', 'Sand coloured, hard wearing.', 'Common', 6, ['#7a5a43', '#9c7a5a', '#b89a72'], [('drain', 'Cold', 0.95)], 'trousers', ['pockets']),
    ('black_trousers', 'Black Trousers', 'For church and funerals.', 'Common', 6, ['#1a1526', '#2b2140', '#3d2e4a'], [], 'trousers', ['crease']),
    ('corduroy_pants', 'Corduroy Pants', 'Ribbed green cord.', 'Uncommon', 12, ['#1e3a2b', '#2f5a3c', '#4a7a4f'], [('drain', 'Cold', 0.92)], 'trousers', ['ribs']),
    ('wool_trousers', 'Wool Trousers', 'Grey and thick.', 'Uncommon', 14, ['#4a4550', '#6e6a74', '#9a95a0'], [('drain', 'Cold', 0.75)], 'trousers', ['crease']),
    ('hunting_pants', 'Hunting Pants', 'Roomy knees, quiet cloth.', 'Uncommon', 15, ['#2f5a3c', '#4a7a4f', '#6e9a5e'], [('drain', 'Stamina', 0.93)], 'trousers', ['pockets']),
    ('leather_pants', 'Leather Pants', 'Stiff, creaks a little.', 'Rare', 28, ['#3b2a22', '#5e3d33', '#8c5f4d'], [('game', 'DamageTakenMult', 0.93), ('drain', 'Cold', 0.9)], 'trousers', ['seams']),
    ('sheriff_trousers', "Sheriff's Trousers", 'Blue with a pale stripe.', 'Rare', 30, ['#2c3e56', '#3a4a7a', '#6b7fb8'], [('game', 'ReactionWindowMult', 1.1)], 'trousers', ['stripe']),
    ('runner_trousers', "Runner's Trousers", 'Light, and cut for speed.', 'Unique', 55, ['#1f2a3d', '#2b6b8a', '#6b7fb8'], [('game', 'SprintSpeedMult', 1.08), ('recover', 'Stamina', 1.15)], 'trousers', ['stripe']),
]
FEET = [
    ('worn_boots', 'Worn Boots', 'The ones you started in.', 'Common', 4, ['#3b2a22', '#5c4033', '#7a5a43', '#9c7a5a'], [], 'boot', []),
    ('work_boots', 'Work Boots', 'Heavy soles, steel toes.', 'Common', 7, ['#1a1526', '#3b2a22', '#5c4033', '#7a5a43'], [], 'boot', ['laces']),
    ('sneakers', 'Sneakers', 'White and quick.', 'Common', 8, ['#4a4550', '#9a95a0', '#e8e0f0', '#fff1c9'], [('game', 'MoveSpeedMult', 1.03)], 'sneaker', ['laces']),
    ('dress_shoes', 'Dress Shoes', 'Polished black.', 'Common', 6, ['#1a1526', '#2b2140', '#3d2e4a', '#6b5a7a'], [], 'shoe', []),
    ('rubber_boots', 'Rubber Boots', 'Green and tall. Mud slides off.', 'Uncommon', 12, ['#1a1526', '#1e3a2b', '#2f5a3c', '#4a7a4f'], [('drain', 'Cold', 0.93)], 'wader', []),
    ('hiking_boots', 'Hiking Boots', 'Ankle support and good grip.', 'Uncommon', 16, ['#3b2a22', '#7a5a43', '#9c7a5a', '#b89a72'], [('drain', 'Stamina', 0.9)], 'boot', ['laces']),
    ('leather_boots', 'Leather Boots', 'Broken in and supple.', 'Uncommon', 15, ['#3b2a22', '#5e3d33', '#8c5f4d', '#d19a7a'], [('drain', 'Cold', 0.93)], 'boot', []),
    ('felt_boots', 'Felt Boots', 'Thick grey felt, warm to the toes.', 'Uncommon', 14, ['#2b2140', '#4a4550', '#6e6a74', '#9a95a0'], [('drain', 'Cold', 0.82)], 'wader', []),
    ('soft_moccasins', 'Soft Moccasins', 'You hear nothing when they walk.', 'Rare', 28, ['#3b2a22', '#5e3d33', '#8c5f4d', '#d19a7a'], [('game', 'ReactionWindowMult', 1.1)], 'shoe', []),
    ('red_boots', 'Red Boots', 'Loud colour, light on the foot.', 'Rare', 32, ['#2b2140', '#7a2e3a', '#c4636b', '#d64a6a'], [('game', 'MoveSpeedMult', 1.05), ('game', 'SprintSpeedMult', 1.05)], 'boot', ['laces']),
]


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


# ------------------------------------------------------------------ Formen (Polygone im 32x32-Raster)
def poly(draw, pts):
    draw.polygon(pts, fill=255)


def mask_of(fn):
    m = Image.new('L', (32, 32), 0)
    fn(ImageDraw.Draw(m))
    return m


def shape_top(kind):
    def f(d):
        if kind == 'shirt':
            poly(d, [(10, 7), (22, 7), (23, 26), (9, 26)])
            poly(d, [(10, 7), (5, 9), (2, 21), (6, 22), (9, 14)])
            poly(d, [(22, 7), (27, 9), (30, 21), (26, 22), (23, 14)])
        elif kind == 'jacket':
            poly(d, [(10, 6), (22, 6), (23, 25), (9, 25)])
            poly(d, [(10, 6), (5, 8), (2, 22), (6, 23), (9, 13)])
            poly(d, [(22, 6), (27, 8), (30, 22), (26, 23), (23, 13)])
        elif kind == 'coat':
            poly(d, [(10, 5), (22, 5), (25, 29), (7, 29)])
            poly(d, [(10, 5), (5, 7), (2, 22), (6, 23), (9, 13)])
            poly(d, [(22, 5), (27, 7), (30, 22), (26, 23), (23, 13)])
        else:  # robe
            poly(d, [(11, 4), (21, 4), (24, 29), (8, 29)])
            poly(d, [(11, 5), (6, 8), (3, 24), (7, 25), (10, 14)])
            poly(d, [(21, 5), (26, 8), (29, 24), (25, 25), (22, 14)])
    return f


def shape_legs():
    def f(d):
        poly(d, [(9, 4), (23, 4), (23, 9), (9, 9)])
        poly(d, [(9, 9), (16, 9), (15, 29), (9, 29)])
        poly(d, [(16, 9), (23, 9), (23, 29), (17, 29)])
    return f


def shape_shoe(kind):
    def f(d):
        if kind == 'boot':        # Stiefel von der Seite, Spitze nach rechts
            poly(d, [(9, 4), (18, 4), (18, 17), (27, 21), (28, 27), (7, 27), (7, 24), (9, 22)])
        elif kind == 'wader':     # hoher Gummistiefel
            poly(d, [(9, 2), (19, 2), (19, 19), (27, 22), (28, 28), (7, 28), (8, 24)])
        elif kind == 'sneaker':   # niedrig, dicke Sohle
            poly(d, [(7, 14), (14, 12), (16, 16), (27, 20), (28, 27), (6, 27)])
        else:                     # Halbschuh
            poly(d, [(7, 15), (13, 13), (16, 18), (27, 21), (28, 27), (6, 27)])
    return f


# ------------------------------------------------------------------ Schattierung
def paint(mask, pal, extras, slot, kind):
    """Maske -> Pixel: Kanten oben/links hell, unten/rechts Schatten, Mitte Grund; Details in Tief."""
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    px = mask.load()
    out = im.load()

    def inside(x, y):
        return 0 <= x < 32 and 0 <= y < 32 and px[x, y] > 0

    if slot == 'top':
        hl, base, sh, dk = [rgb(c) for c in pal]
    elif slot == 'legs':
        dk, base, hl = [rgb(c) for c in pal]
        sh = dk
    else:
        sole, dk, base, hl = [rgb(c) for c in pal]
        sh = dk
    for y in range(32):
        for x in range(32):
            if not inside(x, y):
                continue
            c = base
            if not inside(x, y - 1) or not inside(x - 1, y):
                c = hl
            if not inside(x, y + 1) or not inside(x + 1, y):
                c = sh
            out[x, y] = c + (255,)
    deep = dk if slot != 'legs' else rgb(pal[0])
    det = Image.new('L', (32, 32), 0)
    dd = ImageDraw.Draw(det)

    if slot == 'top':
        # Kragen: V-Ausschnitt
        neck = {'shirt': [(13, 7), (19, 7), (16, 11)], 'jacket': [(13, 6), (19, 6), (16, 10)], 'coat': [(12, 5), (20, 5), (16, 12)], 'robe': [(13, 4), (19, 4), (16, 8)]}[kind]
        dd.polygon(neck, fill=255)
        top_y = {'shirt': 7, 'jacket': 6, 'coat': 5, 'robe': 4}[kind]
        for y in range(32):
            for x in range(32):
                if det.getpixel((x, y)):
                    out[x, y] = deep + (255,) if y > top_y else (0, 0, 0, 0)
        # Knopfleiste / Reissverschluss
        bottom = {'shirt': 25, 'jacket': 24, 'coat': 28, 'robe': 28}[kind]
        if 'zip' in extras or kind in ('jacket',) and 'buttons' not in extras:
            for y in range(10 if kind != 'shirt' else 11, bottom):
                if 'zip' in extras:
                    out[16, y] = hl + (255,)
                    out[15, y] = deep + (255,)
        if 'buttons' in extras:
            for y in range(12, bottom - 1, 4):
                out[15, y] = hl + (255,)
                out[16, y] = hl + (255,)
        if kind in ('coat', 'robe') and 'buttons' not in extras:
            for y in range(12, bottom):
                out[16, y] = deep + (255,)
        if 'pockets' in extras:
            for (x0, y0) in ((10, 17 if kind != 'coat' else 20), (19, 17 if kind != 'coat' else 20)):
                for x in range(x0, x0 + 4):
                    out[x, y0] = deep + (255,)
                for y in range(y0, y0 + 3):
                    out[x0, y] = deep + (255,)
                    out[x0 + 3, y] = deep + (255,)
        if 'check' in extras:
            for y in range(8, 25):
                for x in range(10, 23):
                    if out[x, y][3] and (x % 4 == 0 or y % 4 == 0):
                        out[x, y] = sh + (255,)
        if 'fur' in extras:
            for x in range(8, 25):
                for y in (27, 28, 29):
                    if out[x, y][3] and (x + y) % 2 == 0:
                        out[x, y] = hl + (255,)
            for x in range(11, 21):
                for y in (5, 6):
                    out[x, y] = hl + (255,) if (x + y) % 2 == 0 else base + (255,)
            for y in range(6, 28):
                if out[10, y][3] and y % 2 == 0:
                    out[10, y] = hl + (255,)
                if out[22, y][3] and y % 2 == 0:
                    out[22, y] = hl + (255,)
        # Manschetten
        for x in (2, 3, 4, 5, 6):
            pass
    elif slot == 'legs':
        hi = rgb(pal[2])
        for y in range(4, 29):                    # Spalt zwischen den Beinen
            if y >= 11:
                out[15, y] = (0, 0, 0, 0)
                out[16, y] = deep + (255,)
        for x in range(9, 24):                    # Bund
            out[x, 8] = rgb(pal[0]) + (255,)
        out[16, 5] = hi + (255,)
        out[15, 5] = hi + (255,)                  # Knopf
        if 'pockets' in extras:
            for y in range(11, 16):
                out[10, y] = deep + (255,)
                out[21, y] = deep + (255,)
            out[11, 11] = deep + (255,)
            out[20, 11] = deep + (255,)
        if 'crease' in extras:
            for y in range(12, 28):
                out[12, y] = hi + (255,)
                out[19, y] = hi + (255,)
        if 'ribs' in extras:
            for y in range(10, 28):
                for x in (11, 13, 19, 21):
                    if out[x, y][3]:
                        out[x, y] = sh + (255,) if False else rgb(pal[0]) + (255,)
        if 'seams' in extras:
            for y in range(10, 28):
                out[10, y] = hi + (255,)
                out[22, y] = hi + (255,)
        if 'stripe' in extras:
            for y in range(10, 28):
                out[11, y] = hi + (255,)
                out[20, y] = hi + (255,)
        for x in (9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 22):   # Saum
            if out[x, 28][3]:
                out[x, 28] = rgb(pal[0]) + (255,)
    else:
        # Sohle: unterste zwei Zeilen
        for y in (26, 27):
            for x in range(32):
                if out[x, y][3]:
                    out[x, y] = rgb(pal[0]) + (255,)
        if kind == 'sneaker':
            for y in (26, 27):
                for x in range(32):
                    if out[x, y][3]:
                        out[x, y] = rgb(pal[3]) + (255,) if y == 26 else rgb(pal[1]) + (255,)
        if 'laces' in extras:
            for (x, y) in ((11, 8), (13, 10), (11, 12), (13, 14)) if kind in ('boot',) else ((12, 14), (14, 15), (16, 17)):
                if 0 <= x < 32 and out[x, y][3]:
                    out[x, y] = rgb(pal[3]) + (255,)
        # Schaft-Rand
        if kind in ('boot', 'wader'):
            ytop = 4 if kind == 'boot' else 2
            for x in range(9, 19):
                if out[x, ytop][3]:
                    out[x, ytop] = rgb(pal[3]) + (255,)
        # Kappe
        for (x, y) in ((24, 24), (25, 24), (26, 24)):
            if out[x, y][3]:
                out[x, y] = rgb(pal[1]) + (255,)
    return im


def outline(im):
    out = im.copy()
    src = im.load()
    dst = out.load()
    for y in range(32):
        for x in range(32):
            if src[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < 32 and 0 <= Y < 32 and src[X, Y][3] > 0:
                        dst[x, y] = K
                        break
    return out


def icon(slot, item):
    id_, name, desc, rar, val, pal, eff, kind, extras = item
    mask = mask_of(shape_top(kind) if slot == 'top' else shape_legs() if slot == 'legs' else shape_shoe(kind))
    return outline(paint(mask, pal, extras, slot, kind))


def placeholders():
    """Leere Ausruestungsplaetze (Silhouette in den Farben von Leer_Kleidung.png) fuer Hose und Schuhe nach Resources/UI."""
    dst = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'Resources', 'UI'))
    os.makedirs(dst, exist_ok=True)
    fill, edge = (0x4f, 0x3d, 0x5c, 255), (0x2b, 0x21, 0x40, 255)
    for name, fn in (('Leer_Hose.png', shape_legs()), ('Leer_Schuhe.png', shape_shoe('boot'))):
        m = mask_of(fn)
        im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        px = m.load()
        for y in range(32):
            for x in range(32):
                if px[x, y]:
                    im.putpixel((x, y), fill)
        im = outline(im)
        o = im.load()
        for y in range(32):
            for x in range(32):
                if o[x, y] == K:
                    o[x, y] = edge
        im.save(os.path.join(dst, name))


def main(write_icons=True):
    placeholders()
    os.makedirs(OUT, exist_ok=True)
    data = []
    for slot, items in (('Clothing', TOPS), ('Legs', LEGS), ('Feet', FEET)):
        sl = {'Clothing': 'top', 'Legs': 'legs', 'Feet': 'feet'}[slot]
        for it in items:
            id_, name, desc, rar, val, pal, eff, kind, extras = it
            data.append(dict(id=id_, name=name, desc=desc, rarity=rar, value=val, slot=slot, palette=pal,
                             effects=[dict(type=e[0], key=e[1], value=e[2]) for e in eff]))
            if write_icons and id_ != 'wool_coat':           # der Wollmantel behaelt sein handgezeichnetes Icon
                icon(sl, it).save(os.path.join(OUT, 'Item_%s.png' % id_))
    json.dump({'items': data}, open(os.path.join(OUT, 'kleidung.json'), 'w', encoding='utf-8'), indent=1)
    print('ok', len(data))


if __name__ == '__main__':
    main()
