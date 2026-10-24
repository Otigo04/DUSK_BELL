"""Vorschau aller Objekte einer Zone auf Wasser/Gras-Hintergrund (Kontaktbogen). Aufruf: python preview_objekte.py <Zone-Ordner z. B. 03_Fluss> [Frame]"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import os, sys, glob
from PIL import Image
import welt_lib as W
zone = sys.argv[1] if len(sys.argv) > 1 else '03_Fluss'
fr = int(sys.argv[2]) if len(sys.argv) > 2 else 0
bg = Image.open(W.ART + '/Tiles/Tileset_Terrain.png').convert('RGBA').crop(((0 if zone != '03_Fluss' else 16) * 32, 4 * 32, (1 if zone != '03_Fluss' else 17) * 32, 5 * 32))  # Wasser bzw. Gras
items = []
for sub in ('Objekte', 'Animiert'):
    for p in sorted(glob.glob('%s/%s/%s/*.png' % (W.WELT, zone, sub))):
        im = Image.open(p).convert('RGBA')
        h = im.height
        if sub == 'Animiert':
            if im.width < h:
                continue
            w = h if im.width % h == 0 else im.width // 8
            n = im.width // w
            im = im.crop(((fr % n) * w, 0, (fr % n) * w + w, h))
        items.append((os.path.basename(p)[:-4], im))
cell = max(72, min(128, max(max(i.width, i.height) for _, i in items) + 8))
cols = max(4, 1280 // cell)
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGBA', (cols * cell, rows * cell))
for i, (n, im) in enumerate(items):
    x0, y0 = (i % cols) * cell, (i // cols) * cell
    for yy in range(0, cell, 32):
        for xx in range(0, cell, 32):
            sheet.paste(bg, (x0 + xx, y0 + yy))
    ox, oy = max(0, (cell - im.width) // 2), max(0, (cell - im.height) // 2)
    sheet.alpha_composite(im.crop((0, 0, min(im.width, cell), min(im.height, cell))), (x0 + ox, y0 + oy))
os.makedirs(W.WELT + '/_Vorschau', exist_ok=True)
out = '%s/_Vorschau/Objekte_%s_f%d.png' % (W.WELT, zone, fr)
sheet.save(out)
print(out, len(items), 'Objekte')
for i, (n, _) in enumerate(items):
    print(i // cols, i % cols, n)
