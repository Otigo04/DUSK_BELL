"""Nightward Haus-Baukasten: erzeugt alle PNGs, die Objektliste, prueft die Bauplaene und rendert Vorschauen.
Aufruf (in diesem Ordner):  python bk_build.py
Ausgabe: Art/Tiles/Baukasten/  (Tilesets, Objekte/, Animiert/, _Liste.txt, Vorschau_*.png)
Unity:   Menue  Nightward > Haus-Baukasten > Alles bauen"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import json, os, glob
from PIL import Image
from bk_lib import *
import bk_aussen as A
import bk_innen as I
import bk_fassade as F
import bk_moebel as M
import bk_schutz as SZ
import bk_spalt as SP
import bk_leer as LE
import bk_interieur as IN

OBJ = BK + '/Objekte'
ANI = BK + '/Animiert'
COLS = 26


# ====================================================================== Tilesets
def sheet_aussen():
    sh = Image.new('RGBA', (COLS * 32, (len(A.WALLS) + len(A.ROOFS)) * 32), (0, 0, 0, 0))
    sets = {}
    for r, m in enumerate(A.WALLS):
        t = A.autotile_set(A.wall_tile, m)
        sets['wand_' + m] = t
        for c, tile in enumerate(t):
            sh.paste(tile.im, (c * 32, r * 32))
    for k, m in enumerate(A.ROOFS):
        r = len(A.WALLS) + k
        t = A.autotile_set(A.roof_tile, m)
        sets['dach_' + m] = t
        for c, tile in enumerate(t):
            sh.paste(tile.im, (c * 32, r * 32))
    return sh, sets


ROW_IWALL, ROW_CROWN, ROW_FLOOR, ROW_OVER = 0, 8, 11, 13
OVERLAYS = ['schatten_oben', 'schatten_links', 'schatten_rechts', 'schatten_ecke_links', 'schatten_ecke_rechts',
            'schwelle', 'fussmatte_rot', 'fussmatte_blau', 'fussmatte_gruen']


def sheet_innen():
    sh = Image.new('RGBA', (COLS * 32, 14 * 32), (0, 0, 0, 0))
    sets = {}
    for r, m in enumerate(I.IWALLS):
        t = [I.iwall_tile(m, k, 0) for k in range(16)] + [I.iwall_tile(m, 15, v) for v in (1, 2, 3, 4)]
        sets['iwand_' + m] = t
        for c, tile in enumerate(t):
            sh.paste(tile.im, (c * 32, (ROW_IWALL + r) * 32))
    for k, m in enumerate(I.CROWNS):
        t = I.crown_set(m)
        sets['krone_' + m] = t
        for c, tile in enumerate(t):
            sh.paste(tile.im, (c * 32, (ROW_CROWN + k) * 32))
    for k, m in enumerate(I.FLOORS):
        t = [I.floor_tile(m, v) for v in range(3)]
        sets['boden_' + m] = t
        for v, tile in enumerate(t):
            col, row = (k % 6) * 3 + v, ROW_FLOOR + k // 6
            sh.paste(tile.im, (col * 32, row * 32))
    ov = [I.shade('oben'), I.shade('links'), I.shade('rechts'), I.shade('ecke_links'), I.shade('ecke_rechts'),
          I.threshold(), I.doormat(RED_D), I.doormat(BLUE_D), I.doormat(FOR_M)]
    for c, tile in enumerate(ov):
        sh.paste(tile.im, (c * 32, ROW_OVER * 32))
    sets['overlay'] = dict(zip(OVERLAYS, ov))
    return sh, sets


# ====================================================================== Objekte
def build_objects():
    R = Reg()
    F.register(R)
    M.register(R)
    SZ.register(R)
    SP.register(R)
    LE.register(R)
    IN.register(R)
    os.makedirs(OBJ, exist_ok=True)
    os.makedirs(ANI, exist_ok=True)
    for f in glob.glob(OBJ + '/*.png') + glob.glob(ANI + '/*.png'):
        n = os.path.splitext(os.path.basename(f))[0].replace('_Anim', '')
        if n not in R.obj:
            os.remove(f)                     # verwaiste Datei (umbenanntes Objekt)
            if os.path.exists(f + '.meta'):
                os.remove(f + '.meta')
    lines = ['# Nightward Haus-Baukasten - Objektliste (erzeugt von bk_build.py, nicht von Hand aendern)',
             '# Name | BreitexHoehe px | Kategorie | Fuss-Zeilen | Kollision 1/0 | Frames | ms je Frame']
    for n, (sp, kat, fuss, solid) in sorted(R.obj.items()):
        sp.save(f'{OBJ}/{n}.png')
        fr, ms = R.anim.get(n, ([sp], 0))
        if n in R.anim:
            strip = Image.new('RGBA', (sp.w * len(fr), sp.h), (0, 0, 0, 0))
            for i, f in enumerate(fr):
                strip.paste(f.im, (i * sp.w, 0))
            strip.save(f'{ANI}/{n}_Anim.png')
        lines.append('%s | %dx%d | %s | %d | %d | %d | %d' % (n, sp.w, sp.h, kat, fuss, 1 if solid else 0, len(fr), ms))
    open(BK + '/_Liste.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    return R


# ====================================================================== Pruefung (gleiche Regeln wie im Unity-Builder)
def cells_of(R, name, x, y):
    sp, kat, fuss, solid = R.obj[name]
    w, h = sp.w // 32, sp.h // 32
    return [(x + i, y + j) for i in range(w) for j in range(h)], w, h, kat, fuss


def check_house(R, hs):
    err = []
    a, n = hs['aussen'], hs['name']
    W, WH, DH, UE = a['breite'], a['wandHoehe'], a['dachHoehe'], a.get('ueberstand', 0)
    if a['wand'] not in A.WALLS: err.append(f'{n}: Wandmaterial unbekannt {a["wand"]}')
    if a['dach'] not in A.ROOFS: err.append(f'{n}: Dachmaterial unbekannt {a["dach"]}')
    occ = {}
    doors = 0
    for d in a['deko']:
        o = d['o']
        if o not in R.obj:
            err.append(f'{n} aussen: Objekt fehlt {o}'); continue
        cells, w, h, kat, _ = cells_of(R, o, d['x'], d['y'])
        if not kat.startswith('aussen'):
            err.append(f'{n} aussen: {o} ist kein Aussen-Teil ({kat})'); continue
        if kat == 'aussen_wand':
            bad = [c for c in cells if not (0 <= c[0] < W and 0 <= c[1] < WH)]
            if bad: err.append(f'{n}: {o} ragt aus der Wand {bad}')
            if o.startswith(('Tuer', 'Tor', 'Portal')):
                doors += 1
                if d['y'] != 0: err.append(f'{n}: {o} steht nicht auf dem Boden (y muss 0 sein)')
        elif kat == 'aussen_dach':
            x0, y0 = d['x'], d['y']
            if not (-UE <= x0 < W + UE and WH <= y0 < WH + DH):
                err.append(f'{n}: {o} Ankerzelle nicht auf dem Dach')
            cells = [(x0, y0)]
        elif kat == 'aussen_boden':
            if d['y'] != -1: err.append(f'{n}: {o} muss vor dem Haus stehen (y = -1)')
            bad = [c for c in cells if not (-1 <= c[0] <= W)]
            if bad: err.append(f'{n}: {o} steht zu weit neben dem Haus')
        layer = kat
        for c in cells:
            if (layer, c) in occ:
                err.append(f'{n}: {o} ueberlappt {occ[(layer, c)]} bei {c}')
            occ[(layer, c)] = o
    if doors == 0: err.append(f'{n}: keine Tuer')
    # ---------------- innen
    i = hs['innen']
    Wi, Hi, tx = i['breite'], i['hoehe'], i['tuerX']
    for key, lst in (('boden', I.FLOORS), ('wand', I.IWALLS), ('krone', I.CROWNS)):
        if i[key] not in lst: err.append(f'{n} innen: {key} unbekannt {i[key]}')
    if not (0 <= tx < Wi): err.append(f'{n} innen: tuerX ausserhalb')
    occ = {}
    for d in i['objekte']:
        o = d['o']
        if o not in R.obj:
            err.append(f'{n} innen: Objekt fehlt {o}'); continue
        cells, w, h, kat, fuss = cells_of(R, o, d['x'], d['y'])
        if kat == 'innen_wand':
            bad = [c for c in cells if not (0 <= c[0] < Wi and Hi <= c[1] < Hi + 2)]
            if bad: err.append(f'{n} innen: {o} haengt nicht an der Wand {bad}')
            layer = 'wand'
        elif kat == 'innen_boden':
            bad = [c for c in cells if not (0 <= c[0] < Wi and 0 <= c[1] < Hi)]
            if bad: err.append(f'{n} innen: {o} liegt nicht auf dem Boden {bad}')
            layer = 'teppich'
        elif kat == 'innen_moebel':
            cells = [(d['x'] + k, d['y'] + j) for k in range(w) for j in range(fuss)]
            bad = [c for c in cells if not (0 <= c[0] < Wi and 0 <= c[1] < Hi)]
            if bad: err.append(f'{n} innen: {o} steht ausserhalb des Raums {bad}')
            layer = 'moebel'
        else:
            err.append(f'{n} innen: {o} ist kein Innen-Teil ({kat})'); continue
        for c in cells:
            if (layer, c) in occ:
                err.append(f'{n} innen: {o} ueberlappt {occ[(layer, c)]} bei {c}')
            occ[(layer, c)] = o
    blocked = {c for (l, c) in occ if l == 'moebel'}
    if (tx, 0) in blocked:
        err.append(f'{n} innen: Eingang (tuerX, 0) ist zugestellt')
    else:
        seen, todo = {(tx, 0)}, [(tx, 0)]
        while todo:
            x, y = todo.pop()
            for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if c not in seen and c not in blocked and 0 <= c[0] < Wi and 0 <= c[1] < Hi:
                    seen.add(c); todo.append(c)
        free = Wi * Hi - len(blocked)
        if len(seen) < free:
            err.append(f'{n} innen: {free - len(seen)} freie Bodenfelder sind vom Eingang nicht erreichbar')
    return err


# ====================================================================== Vorschau (gleiche Logik wie Unity)
def mask_at(cells, x, y):
    m = 0
    if (x, y + 1) in cells: m |= N     # Unity: y nach oben
    if (x + 1, y) in cells: m |= E
    if (x, y - 1) in cells: m |= S
    if (x - 1, y) in cells: m |= W
    return m


def fill_pick(x, y, n=3):
    return int(hsh(x * 7 + 1000, y * 13 + 1000, 99) * n) % n


class Canvas:
    def __init__(self, x0, y0, x1, y1, bg):
        """Kachelbereich x0..x1, y0..y1 (Unity-Koordinaten, y nach oben)."""
        self.x0, self.y1 = x0, y1
        self.im = Image.new('RGBA', ((x1 - x0 + 1) * 32, (y1 - y0 + 1) * 32), bg)

    def put(self, img, x, y):
        """Objekt mit Ankerzelle (x, y) links unten."""
        px = (x - self.x0) * 32
        py = (self.y1 - y + 1) * 32 - img.height
        self.im.alpha_composite(img, (px, py)) if px >= 0 and py >= 0 else self._safe(img, px, py)

    def _safe(self, img, px, py):
        tmp = Image.new('RGBA', self.im.size, (0, 0, 0, 0))
        tmp.paste(img, (px, py))
        self.im.alpha_composite(tmp)


EDGE_COLS = {11: (11, 20, 21), 14: (14, 22, 23), 10: (10, 24, 25)}


def autotile(cv, cells, tset, fills=(15, 16, 17)):
    for (x, y) in cells:
        m = mask_at(cells, x, y)
        if m == 15:
            t = tset[fills[fill_pick(x, y, len(fills))]]
        elif m in EDGE_COLS and len(tset) > 20:
            t = tset[EDGE_COLS[m][fill_pick(x, y, 3)]]
        else:
            t = tset[m]
        cv.put(t.im, x, y)


def render_aussen(hs, R, TS):
    a = hs['aussen']
    W, WH, DH, UE = a['breite'], a['wandHoehe'], a['dachHoehe'], a.get('ueberstand', 0)
    top = WH + DH + 2
    cv = Canvas(-1 - UE, -2, W + UE, top, NB_D)
    for x in range(-1 - UE, W + UE + 1):
        for y in (-2, -1):
            cv.put(Image.new('RGBA', (32, 32), FOR_M if (x + y) % 2 else FOR_D), x, y)
    wall = {(x, y) for x in range(W) for y in range(WH)}
    roof = {(x, y) for x in range(-UE, W + UE) for y in range(WH, WH + DH)}
    autotile(cv, wall, TS['wand_' + a['wand']])
    order = {'aussen_wand': 0, 'aussen_dach': 1, 'aussen_boden': 2}
    deko = sorted(a['deko'], key=lambda d: order[R.obj[d['o']][1]])
    for d in deko:
        if R.obj[d['o']][1] == 'aussen_wand':
            cv.put(R.obj[d['o']][0].im, d['x'], d['y'])
    autotile(cv, roof, TS['dach_' + a['dach']], (15, 16, 17))
    for d in deko:
        if R.obj[d['o']][1] != 'aussen_wand':
            cv.put(R.obj[d['o']][0].im, d['x'], d['y'])
    return cv.im


def render_innen(hs, R, TS):
    i = hs['innen']
    Wi, Hi, tx = i['breite'], i['hoehe'], i['tuerX']
    cv = Canvas(-1, -1, Wi, Hi + 2, OL1)
    floor = {(x, y) for x in range(Wi) for y in range(Hi)} | {(tx, -1)}
    fl = TS['boden_' + i['boden']]
    for (x, y) in floor:
        cv.put(fl[fill_pick(x, y)].im, x, y)
    ov = TS['overlay']
    for x in range(Wi):
        k = 'schatten_ecke_links' if x == 0 else ('schatten_ecke_rechts' if x == Wi - 1 else 'schatten_oben')
        cv.put(ov[k].im, x, Hi - 1)
    for y in range(Hi - 1):
        cv.put(ov['schatten_links'].im, 0, y)
        cv.put(ov['schatten_rechts'].im, Wi - 1, y)
    cv.put(ov['schwelle'].im, tx, -1)
    for d in i['objekte']:
        if R.obj[d['o']][1] == 'innen_boden':
            cv.put(R.obj[d['o']][0].im, d['x'], d['y'])
    walls = {(x, y) for x in range(Wi) for y in (Hi, Hi + 1)}
    autotile(cv, walls, TS['iwand_' + i['wand']], (15, 16, 17))
    for d in i['objekte']:
        if R.obj[d['o']][1] == 'innen_wand':
            cv.put(R.obj[d['o']][0].im, d['x'], d['y'])
    for d in sorted([d for d in i['objekte'] if R.obj[d['o']][1] == 'innen_moebel'], key=lambda d: -d['y']):
        cv.put(R.obj[d['o']][0].im, d['x'], d['y'])
    crown = {(x, Hi + 2) for x in range(-1, Wi + 1)} | {(x, -1) for x in range(-1, Wi + 1) if x != tx} | \
            {(-1, y) for y in range(-1, Hi + 3)} | {(Wi, y) for y in range(-1, Hi + 3)}
    cs = TS['krone_' + i['krone']]
    for (x, y) in crown:
        m = mask_at(crown, x, y)
        cv.put(cs[m].im, x, y)
    cv.put(R.obj['Tuerrahmen_UntenLinks'][0].im, tx - 1, -1)
    cv.put(R.obj['Tuerrahmen_UntenRechts'][0].im, tx + 1, -1)
    return cv.im


def check_palette_img(im, name):
    pal = set()
    for l in open(ART + '/Palette.gpl'):
        t = l.split()
        if len(t) >= 3 and t[0].isdigit():
            pal.add((int(t[0]), int(t[1]), int(t[2])))
    bad = {c for _, c in im.getcolors(10 ** 7) if c[3] not in (0, 255) or (c[3] and c[:3] not in pal)}
    return [f'{name}: Fremdfarbe {b}' for b in list(bad)[:3]]


def montage(ims, path, cols, scale=2, gap=16, bg=(20, 16, 30, 255)):
    rows = [ims[k:k + cols] for k in range(0, len(ims), cols)]
    Wt = max(sum(i.width for i in r) + gap * (len(r) + 1) for r in rows)
    Ht = sum(max(i.height for i in r) for r in rows) + gap * (len(rows) + 1)
    out = Image.new('RGBA', (Wt, Ht), bg)
    y = gap
    for r in rows:
        x = gap
        for i in r:
            out.alpha_composite(i, (x, y + max(j.height for j in r) - i.height))
            x += i.width + gap
        y += max(i.height for i in r) + gap
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    out.save(path)


if __name__ == '__main__':
    os.makedirs(BK, exist_ok=True)
    sa, SA = sheet_aussen()
    si, SI = sheet_innen()
    sa.save(BK + '/Tileset_BK_Aussen.png')
    si.save(BK + '/Tileset_BK_Innen.png')
    R = build_objects()
    TS = dict(SA, **SI)
    layout = {'cols': COLS, 'wand': A.WALLS, 'dach': A.ROOFS, 'dachStartZeile': len(A.WALLS),
              'innenWand': I.IWALLS, 'innenWandZeile': ROW_IWALL, 'krone': I.CROWNS, 'kroneZeile': ROW_CROWN,
              'boden': I.FLOORS, 'bodenZeile': ROW_FLOOR, 'bodenJeZeile': 6, 'overlay': OVERLAYS, 'overlayZeile': ROW_OVER}
    json.dump(layout, open(BK + '/_Tilesets.json', 'w', encoding='utf-8', newline='\n'), indent=1)
    errs = check_palette_img(sa, 'Aussen') + check_palette_img(si, 'Innen')
    for n, (sp, *_r) in R.obj.items():
        errs += check_palette_img(sp.im, n)
    for n, (fr, ms) in R.anim.items():
        for k, f in enumerate(fr):
            errs += check_palette_img(f.im, f'{n}[{k}]')
    plan = json.load(open(BK + '/Bauplaene.json', encoding='utf-8'))
    names = set()
    for hs in plan['haeuser']:
        if hs['name'] in names:
            errs.append('Hausname doppelt: ' + hs['name'])
        names.add(hs['name'])
        errs += check_house(R, hs)
    ext = [render_aussen(hs, R, TS) for hs in plan['haeuser']]
    inn = [render_innen(hs, R, TS) for hs in plan['haeuser']]
    montage(ext, BK + '/Vorschau_Aussen.png', 4)
    montage(inn, BK + '/Vorschau_Innen.png', 3)
    print('Objekte: %d (animiert %d), Haeuser: %d' % (len(R.obj), len(R.anim), len(plan['haeuser'])))
    if errs:
        print('FEHLER:')
        print('\n'.join(errs))
        raise SystemExit(1)
    print('Pruefung ok: 0 Fehler, 0 Fremdfarben')
