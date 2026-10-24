"""Item-Icons aus den importierten Paketen (Art/_IMPORTED) nach Art/Items:
  - Waffen (GUNS_V1.00): Pistole unveraendert (32x32), lange Waffen schraeg gedreht und auf 32x32 verkleinert, mit Kontur.
  - Schrotpatronen: Munitionsschachtel in Rot umgefaerbt.
  - Essen (Ghostpixxells_pixelfood): 32x32, werden unveraendert als Item_<Name>.png kopiert (Namen aus FOOD unten).
Aufruf: python gen_import_icons.py"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import os
import re
import shutil
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))   # .../Art
IMP = os.path.join(ROOT, '_IMPORTED')
ITEMS = os.path.join(ROOT, 'Items')
K = (0x1a, 0x15, 0x26, 255)

GUN_DIR = os.path.join(IMP, 'GUNS_V1.00', 'V1.00', 'PNG')
GUNS = {
    'Item_Pistole_Silber.png': ('GUN_01_[square_frame]_01_V1.00.png', None),
    'Item_Sturmgewehr.png': ('Assault_rifle_V1.01.png', 40),
    'Item_Pumpgun.png': ('[design]Shotgun_V1.02.png', 40),
    'Item_Kar98.png': ('[design]_Sniper_rifle_[KAR98]_V1.00.png', 36),
}


def diag_icon(path, angle, size=32, pad=1):
    im = Image.open(path).convert('RGBA')
    im = im.crop(im.getbbox())
    big = im.resize((im.width * 4, im.height * 4), Image.NEAREST).rotate(angle, expand=True, resample=Image.BICUBIC)
    big = big.crop(big.getbbox())
    sc = min((size - 2 * pad - 2) / big.width, (size - 2 * pad - 2) / big.height)
    sm = big.resize((max(1, round(big.width * sc)), max(1, round(big.height * sc))), Image.BOX)
    body = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    body.paste(sm, ((size - sm.width) // 2, (size - sm.height) // 2), sm)
    px = body.load()
    for y in range(size):
        for x in range(size):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 110 else (0, 0, 0, 0)
    out = body.copy()
    op = out.load()
    for y in range(size):                       # 1 px Kontur
        for x in range(size):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < size and 0 <= Y < size and px[X, Y][3] > 0:
                        op[x, y] = K
                        break
    return out


def shells_icon():
    src = Image.open(os.path.join(ITEMS, 'Waffen', 'Item_Munition.png')).convert('RGBA')
    m = {(0xff, 0xd2, 0x7a): (0xd6, 0x4a, 0x6a), (0xff, 0xa5, 0x50): (0xc4, 0x63, 0x6b), (0xe8, 0x73, 0x3a): (0x8a, 0x1f, 0x3d)}
    px = src.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in m:
                px[x, y] = m[(r, g, b)] + (a,)
    return src


# Nummer im Dateinamen -> Dateiname Item_<Name>.png  (Namen = Item-Ids in Pascal-Case, siehe FoodTable.cs)
def food_files():
    d = os.path.join(IMP, 'Ghostpixxells_pixelfood')
    out = {}
    for f in os.listdir(d):
        m = re.match(r'^(\d+)_(.+)\.png$', f)
        if m:
            out[int(m.group(1))] = (f, m.group(2))
    return out


def main():
    for name, (src, ang) in GUNS.items():
        p = os.path.join(GUN_DIR, src)
        if ang is None:
            shutil.copyfile(p, os.path.join(ITEMS, 'Waffen', name))
        else:
            diag_icon(p, ang).save(os.path.join(ITEMS, 'Waffen', name))
        print('ok', name)
    shells_icon().save(os.path.join(ITEMS, 'Waffen', 'Item_Schrot.png'))
    print('ok Item_Schrot.png')
    dst = os.path.join(ITEMS, 'Essen')
    os.makedirs(dst, exist_ok=True)
    n = 0
    for num, (f, name) in sorted(food_files().items()):
        shutil.copyfile(os.path.join(IMP, 'Ghostpixxells_pixelfood', f), os.path.join(dst, 'Food_%03d_%s.png' % (num, name)))
        n += 1
    print('food', n)


if __name__ == '__main__':
    main()
