import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math, os, json
from PIL import Image

T = 'F:/!!!_GAMES/NIGHTWARD/Nightward/Assets/_Project/Art/Tiles'
OUT = T + '/Animiert'
os.makedirs(OUT, exist_ok=True)
meta = {}


def load(p):
    return Image.open(p).convert('RGBA')


def strip(frames, name, ms):
    w, h = frames[0].size
    s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    s.save(OUT + '/' + name + '.png')
    meta[name] = (len(frames), w, h, ms)


def bbox_rows(im):
    px = im.load()
    rows = {}
    for y in range(im.height):
        xs = [x for x in range(im.width) if px[x, y][3]]
        if xs:
            rows[y] = (min(xs), max(xs))
    return rows


def shift_row(src, dst, y, dx):
    sp, dp = src.load(), dst.load()
    for x in range(src.width):
        p = sp[x, y]
        if p[3]:
            nx = x + dx
            if 0 <= nx < src.width:
                dp[nx, y] = p


def shear(im, phases, amp, pw=1.6):
    rows = bbox_rows(im)
    ys = sorted(rows)
    top, bottom = ys[0], ys[-1]
    frames = []
    for ph in phases:
        out = Image.new('RGBA', im.size, (0, 0, 0, 0))
        for y in ys:
            w = max(0.0, (bottom - y) / max(1, bottom - top)) ** pw
            dx = int(round(amp * math.sin(ph) * w))
            lo, hi = rows[y]
            dx = max(-lo, min(im.width - 1 - hi, dx))  # kein Beschnitt am Rand
            shift_row(im, out, y, dx)
        frames.append(out)
    return frames


def fire():
    src = load(T + '/Objekte/Lagerfeuer.png')
    sp = src.load()
    base = src.copy()
    bp = base.load()
    for y in range(0, 20):
        for x in range(32):
            bp[x, y] = (0, 0, 0, 0)
    flame = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    fp = flame.load()
    for y in range(7, 20):
        for x in range(32):
            fp[x, y] = sp[x, y]
    ks = [1.00, 1.12, 0.92, 1.18, 1.04, 0.88]
    sw = [0, 1, 0, -1, 1, 0]
    sparkc = [(0xf6, 0xd3, 0x4a, 255), (0xe8, 0x86, 0x3f, 255)]
    spark_path = [(14, 8, 0), (20, 10, 3)]
    frames = []
    for i in range(6):
        out = base.copy()
        op = out.load()
        k = ks[i]
        for y in range(2, 20):
            sy = int(round(19 - (19 - y) / k))
            if sy < 7 or sy > 19:
                continue
            w = (19 - y) / 13.0
            dx = int(round(sw[i] * w * 1.2))
            for x in range(32):
                p = fp[x, sy]
                if p[3]:
                    nx = x + dx
                    if 0 <= nx < 32:
                        op[nx, y] = p
        for x in range(32):
            for y in (20, 21):
                if op[x, y][:3] == (0xef, 0xe7, 0xdd) and (x + i + y) % 3 == 0:
                    op[x, y] = (0xf6, 0xd3, 0x4a, 255)
        tip = int(round(19 - 12 * k))
        for j, (sx, sy0, st) in enumerate(spark_path):
            t = (i + st) % 6
            yy = tip - 1 - t
            xx = sx + (1 if (t + j) % 2 else -1) * (1 if t > 1 else 0) + sw[i]
            if yy >= 0 and t < 5 and 0 <= xx < 32:
                op[xx, yy] = sparkc[0 if t < 3 else 1]
        frames.append(out)
    strip(frames, 'Lagerfeuer_Anim', 100)


def lantern():
    src = load(T + '/Objekte/Laterne.png')
    E = (0xe8, 0x86, 0x3f, 255)
    F = (0xf3, 0xa6, 0x5a, 255)
    G = (0xf6, 0xd3, 0x4a, 255)
    H = (0xef, 0xe7, 0xdd, 255)
    maps = [{}, {E: F, F: G, G: H}, {G: F, F: E, H: G}]
    seq = [0, 1, 0, 2, 1, 0, 2, 0]
    frames = []
    for s in seq:
        im = src.copy()
        px = im.load()
        m = maps[s]
        for y in range(im.height):
            for x in range(im.width):
                if px[x, y] in m:
                    px[x, y] = m[px[x, y]]
        frames.append(im)
    strip(frames, 'Laterne_Anim', 120)


def reeds():
    im = load(T + '/Objekte/Schilf.png')
    ph = [2 * math.pi * i / 6 for i in range(6)]
    strip(shear(im, ph, 2.2, pw=1.4), 'Schilf_Anim', 220)


def lilies():
    im = load(T + '/Objekte/Seerosen.png')
    px = im.load()
    seen = set()
    comps = []
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3] and (x, y) not in seen:
                st = [(x, y)]
                seen.add((x, y))
                c = []
                while st:
                    a, b = st.pop()
                    c.append((a, b))
                    for da in (-1, 0, 1):
                        for db in (-1, 0, 1):
                            n = (a + da, b + db)
                            if 0 <= n[0] < 32 and 0 <= n[1] < 32 and n not in seen and px[n[0], n[1]][3]:
                                seen.add(n)
                                st.append(n)
                comps.append(c)
    frames = []
    for i in range(8):
        out = Image.new('RGBA', im.size, (0, 0, 0, 0))
        op = out.load()
        for k, c in enumerate(comps):
            ph = 2 * math.pi * i / 8 + k * 2.1
            dy = int(round(math.sin(ph) * 0.8))
            dx = int(round(math.cos(ph * 0.5 + k) * 0.7))
            for (a, b) in c:
                if 0 <= a + dx < 32 and 0 <= b + dy < 32:
                    op[a + dx, b + dy] = px[a, b]
        frames.append(out)
    strip(frames, 'Seerosen_Anim', 280)


WIND = [0, math.pi / 2, 0, -math.pi / 2]


def foliage(path, name, amp):
    strip(shear(load(path), WIND, amp), name + '_Wind', 300)


def tileset_deko():
    ts = load(T + '/Tileset_Terrain.png')
    out = Image.new('RGBA', (640, 32 * 4), (0, 0, 0, 0))
    for c in range(20):
        tile = ts.crop((c * 32, 5 * 32, c * 32 + 32, 5 * 32 + 32))
        if c in list(range(0, 11)) + [18, 19]:
            fr = shear(tile, WIND, 1.2, pw=1.0)
        else:
            fr = [tile] * 4
        for f in range(4):
            out.paste(fr[f], (c * 32, f * 32))
    out.save(OUT + '/Tileset_Deko_Wind.png')
    meta['Tileset_Deko_Wind'] = (4, 640, 32, 300)


fire()
lantern()
reeds()
lilies()
O = T + '/Objekte/'
for n in ['Laubbaum_Gross', 'Laubbaum_Gross_Apfel', 'Laubbaum_Gross_Herbst', 'Laubbaum_Klein', 'Laubbaum_Klein_Herbst',
          'Fichte_Gross', 'Fichte_Klein', 'Busch_Gruen', 'Busch_Beeren', 'Busch_Blueten', 'Busch_Dunkel', 'Busch_Herbst',
          'Hecke', 'Krone_A', 'Krone_B', 'Krone_Herbst', 'Krone_Klein', 'Teil_Laubbaum_Krone']:
    foliage(O + n + '.png', n, 1.2 if ('Busch' in n or n == 'Hecke') else 1.8)
Z = T + '/Zusammengesetzt/'
for f in sorted(os.listdir(Z)):
    if f.endswith('.png'):
        foliage(Z + f, f[:-4], 1.8)
tileset_deko()
json.dump(meta, open(OUT + '/_meta.json', 'w'), indent=1)
with open(OUT + '/_Liste.txt', 'w', encoding='utf-8') as fh:
    fh.write('Nightward animierte Tiles/Objekte (horizontale Streifen, Frame = Breite/Frames)\n')
    fh.write('Name | Frames | Frame-Groesse | ms pro Frame\n\n')
    for k, (n, w, h, ms) in meta.items():
        fh.write('%s | %d | %dx%d | %d\n' % (k, n, w, h, ms))
print(len(meta), 'Streifen')
