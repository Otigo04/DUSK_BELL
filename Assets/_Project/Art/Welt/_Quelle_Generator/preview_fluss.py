"""Vorschau-Karte fuer das Fluss-Tileset: setzt eine Testkarte aus dem Sheet zusammen (Autotile wie in Unity), schreibt PNG je Frame + GIF.
Aufruf: python preview_fluss.py [Strom] [Ufer]      Standard: S Gras"""
import os, sys
from PIL import Image
import welt_lib as W

stream = sys.argv[1] if len(sys.argv) > 1 else 'S'
kind = sys.argv[2] if len(sys.argv) > 2 else 'Gras'
MAP = [
    "..........~~~.......",
    "..........~~~~......",
    "...........~~.......",
    "....~~~~~..~~~......",
    "...~~~~~~~~~~.......",
    "...~~~~~~~~~~..~....",
    "....~~~~~~..~~~~~...",
    ".....~~~....~~~~~~..",
    "..........~~~~~~~~..",
    "..........~~~.......",
    "..........~~........",
    "..........~~~.......",
]
wet = {(x, y) for y, r in enumerate(MAP) for x, c in enumerate(r) if c == '~'}
sheet = Image.open('%s/03_Fluss/Tileset/Fluss_%s_%s.png' % (W.WELT, stream, kind)).convert('RGBA')
ts = Image.open(W.ART + '/Tiles/Tileset_Terrain.png').convert('RGBA')
grass = ts.crop((0, 4 * 32, 32, 5 * 32))
Wd, Hd = len(MAP[0]), len(MAP)
frames = []
for t in range(16):
    im = Image.new('RGBA', (Wd * 32, Hd * 32))
    for y in range(Hd):
        for x in range(Wd):
            if (x, y) in wet:
                m, n = W.mask_from_map(wet, x, y)
                i = W.idx_of(m, n)
                im.paste(sheet.crop((i * 32, t * 32, i * 32 + 32, t * 32 + 32)), (x * 32, y * 32))
            else:
                # Land: Gras, am Rand des Wassers deckt die Wasser-Kachel schon das Ufer; hier reines Gras
                im.paste(grass, (x * 32, y * 32))
    frames.append(im)
od = W.WELT + '/_Vorschau'
os.makedirs(od, exist_ok=True)
frames[0].save('%s/Fluss_%s_%s_f0.png' % (od, stream, kind))
frames[5].save('%s/Fluss_%s_%s_f5.png' % (od, stream, kind))
frames[0].save('%s/Fluss_%s_%s.gif' % (od, stream, kind), save_all=True, append_images=frames[1:], duration=125, loop=0, disposal=2)
print('ok', Wd, Hd)
