import sys
from nwlib import *
from autotile import *

ts = Image.open(TILES + '/Tileset_Terrain.png').convert('RGBA')


def dirt(x, y, v=0):
    x %= 32
    y %= 32
    h = hsh(x, y, 100 + v)
    c = BROWN[3]
    if h < 0.09:
        c = BROWN[2]
    elif h < 0.135:
        c = BROWN[4]
    elif h < 0.145:
        c = BROWN[5]
    elif h < 0.152:
        c = BROWN[1]
    hb = hsh(x // 3, y // 3, 200 + v)
    if hb < 0.12 and c == BROWN[3]:
        c = BROWN[2]
    elif hb > 0.92 and c == BROWN[3]:
        c = BROWN[4]
    if hsh(x // 2, y // 2, 300 + v) < 0.02 and x % 2 == 0 and y % 2 == 0:
        c = STONE[3]
    if hsh((x - 1) // 2, (y - 1) // 2, 300 + v) < 0.02 and x % 2 == 1 and y % 2 == 1:
        c = STONE[1]
    return c


ROWS = [0, 5, 11, 16, 21, 27, 32]   # Zeilenhoehen 5,6,5,5,6,5


def cobble(x, y, v=0):
    x %= 32
    y %= 32
    row = 0
    while ROWS[row + 1] <= y:
        row += 1
    by = y - ROWS[row]
    bh = ROWS[row + 1] - ROWS[row]
    off = 4 if row % 2 else 0
    xx = (x + off) % 32
    bx = xx % 8
    bi = xx // 8
    if bx == 7 or by == bh - 1:
        return STONE[0]
    h = hsh(bi, row, 400 + v)
    base = 4 if h < 0.62 else (3 if h < 0.93 else 2)
    if by == 0 and bx < 6:
        base = min(5, base + 1)
    elif bx == 0 and by < bh - 2:
        base = min(5, base + 1) if base < 4 else base
    elif by == bh - 2 or bx == 6:
        base = max(1, base - 1)
    if hsh(x, y, 500 + v) < 0.04 and base > 1:
        base -= 1
    return STONE[base]


def tiles_for(kind, v=0):
    out = {}
    if kind == 'weg':
        tex = lambda x, y: dirt(x, y, v)
        edge, rd, rl = BROWN[1], BROWN[2], BROWN[4]
        over = (G_MD, G_BASE)
    else:
        tex = lambda x, y: cobble(x, y, v)
        edge, rd, rl = PURP[2], STONE[1], STONE[4]
        over = (G_MD, G_BASE)
    for idx in range(16):
        bg = tile_from(ts, idx % 8, 4)
        out[idx] = render(idx, None, tex, bg, edge, rd, rl, seed=idx + (0 if kind == 'weg' else 50), over=over)
    for k, nt in enumerate(['NE', 'SE', 'SW', 'NW']):
        bg = tile_from(ts, k, 4)
        out[16 + k] = render(15, nt, tex, bg, edge, rd, rl, seed=70 + k + (0 if kind == 'weg' else 50), over=over)
    return out


if __name__ == '__main__':
    res = {}
    res['weg'] = tiles_for('weg')
    res['pfl'] = tiles_for('pfl')
    import pickle
    pickle.dump({k: {i: t.tobytes() for i, t in d.items()} for k, d in res.items()}, open(sys.argv[1], 'wb'))
    rows = []
    for k in ('weg', 'pfl'):
        for i in range(20):
            rows.append(res[k][i])
    sh = sheet(rows, 20, 32, 32)
    sh.save(sys.argv[2])
