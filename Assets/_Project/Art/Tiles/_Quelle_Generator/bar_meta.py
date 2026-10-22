"""Schreibt die Unity-.meta fuer die Bar-Tilesets nach dem Muster von Tileset_Haus.png.meta:
Point-Filter, PPU 32, keine Kompression, 32x32-Zellen als Sprites (leere Zellen entfallen).
GUID bleibt erhalten (Unity vergibt sie beim ersten Import)."""
import re, hashlib
from PIL import Image
from bar_lib import TILES

TEMPLATE = TILES + '/Tileset_Haus.png.meta'


def sid(iid):
    v = iid & 0xFFFFFFFFFFFFFFFF
    return ('%016x' % v)[::-1] + '0800000000000000'


def make(png, prefix):
    im = Image.open(TILES + '/' + png + '.png').convert('RGBA')
    W, H = im.size
    guid = re.search(r'guid: (\w+)', open(TILES + '/' + png + '.png.meta', encoding='utf-8').read()).group(1)
    t = open(TEMPLATE, encoding='utf-8').read()
    t = re.sub(r'guid: \w+', 'guid: ' + guid, t, count=1)
    cells = []
    for r in range(H // 32):
        for c in range(W // 32):
            if im.crop((c * 32, r * 32, c * 32 + 32, r * 32 + 32)).getchannel('A').getbbox():
                cells.append((prefix + '_%d_%d' % (r, c), c * 32, H - (r + 1) * 32))

    def iid(name):
        n = int(hashlib.md5((guid + name).encode()).hexdigest()[:16], 16)
        return n - (1 << 64) if n >= (1 << 63) else n

    main = png + '_0'
    # 1) internalIDToNameTable
    table = '  internalIDToNameTable:\n' + ''.join(
        '  - first:\n      213: %d\n    second: %s\n' % (iid(n), n) for n in [main] + [c[0] for c in cells])
    a = t.index('  internalIDToNameTable:\n'); b = t.index('  externalObjects:')
    t = t[:a] + table + t[b:]
    # 2) sprites
    sp = ''
    for n, x, y in cells:
        i = iid(n)
        sp += ('    - serializedVersion: 2\n      name: %s\n      rect:\n        serializedVersion: 2\n        x: %d\n        y: %d\n'
               '        width: 32\n        height: 32\n      alignment: 0\n      pivot: {x: 0.5, y: 0.5}\n'
               '      border: {x: 0, y: 0, z: 0, w: 0}\n      customData: \n      outline: []\n      physicsShape: []\n'
               '      tessellationDetail: -1\n      bones: []\n      spriteID: %s\n      internalID: %d\n      vertices: []\n'
               '      indices: \n      edges: []\n      weights: []\n') % (n, x, y, sid(i), i)
    a = t.index('    sprites:\n') + len('    sprites:\n'); b = t.index('    outline: []\n    customData: \n    physicsShape: []\n    bones: []\n    spriteID: \n')
    t = t[:a] + sp + t[b:]
    # 3) nameFileIdTable
    a = t.index('    nameFileIdTable:\n') + len('    nameFileIdTable:\n'); b = t.index('  mipmapLimitGroupName:')
    names = sorted([(main, iid(main))] + [(n, iid(n)) for n, _, _ in cells])
    t = t[:a] + ''.join('      %s: %d\n' % (n, i) for n, i in names) + t[b:]
    open(TILES + '/' + png + '.png.meta', 'w', encoding='utf-8', newline='\n').write(t)
    return len(cells)


if __name__ == '__main__':
    print('Aussen Sprites:', make('Tileset_Bar_Aussen', 'BA'))
    print('Innen Sprites:', make('Tileset_Bar_Innen', 'BI'))
