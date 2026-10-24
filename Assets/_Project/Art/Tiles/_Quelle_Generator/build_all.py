"""Nightward Tileset-Erweiterung: erzeugt alle neuen PNGs in Art/Tiles (Python + PIL).
Aufruf:  python build_all.py   (aus diesem Ordner)"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math, os, re, sys
from nwlib import *
import fences as F
import cat_nature as CN
import trans as TR
import props as P
import props2 as P2
import props3 as P3

OBJ_DIR = TILES + '/Objekte'
ANIM_DIR = TILES + '/Animiert'
os.makedirs(ANIM_DIR, exist_ok=True)

objs = {}       # name -> Spr (statisch)
anims = {}      # name -> (frames, ms)  -> Animiert/<name>_Anim.png  (Objekt: Objekte/<name>.png = Frame 0)
winds = {}      # name -> Spr           -> Animiert/<name>_Wind.png
WIND_PH = [0, math.pi / 2, 0, -math.pi / 2]


def shear_rows(im, phases, amp, pw=1.6):
    """Zeilenweises Wiegen (Fuss fest, Spitze bewegt), ohne Beschnitt am Rand."""
    px = im.load()
    rows = {}
    for y in range(im.height):
        xs = [x for x in range(im.width) if px[x, y][3]]
        if xs:
            rows[y] = (min(xs), max(xs))
    ys = sorted(rows)
    top, bot = ys[0], ys[-1]
    frames = []
    for ph in phases:
        out = Image.new('RGBA', im.size, (0, 0, 0, 0))
        op = out.load()
        for y in ys:
            w = max(0.0, (bot - y) / max(1, bot - top)) ** pw
            dx = int(round(amp * math.sin(ph) * w))
            lo, hi = rows[y]
            dx = max(-lo, min(im.width - 1 - hi, dx))
            for x in range(im.width):
                if px[x, y][3] and 0 <= x + dx < im.width:
                    op[x + dx, y] = px[x, y]
        frames.append(out)
    return frames


def strip_img(frames):
    w, h = frames[0].size
    s = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    return s


# =============================================================== 1. Zaun-Tileset
def build_fences():
    rows = []
    makers = [lambda m, v=0: F.fence_wood(m, 'holz', v), lambda m, v=0: F.fence_wood(m, 'dunkel', v),
              lambda m, v=0: F.fence_picket(m, 'weiss', v), lambda m, v=0: F.wall_stone(m, v), lambda m, v=0: F.hedge(m, v)]
    sh = Image.new('RGBA', (20 * 32, 5 * 32), (0, 0, 0, 0))
    for r, mk in enumerate(makers):
        for m in range(16):
            sh.paste(mk(m, 0).im, (m * 32, r * 32))
        for k, (mask, var) in enumerate(((10, 1), (10, 2), (10, 3), (5, 1))):
            sh.paste(mk(mask, var).im, ((16 + k) * 32, r * 32))
    sh.save(TILES + '/Tileset_Zaun.png')


# =============================================================== 2. Uebergaenge
def build_transitions():
    sh = Image.new('RGBA', (20 * 32, 5 * 32), (0, 0, 0, 0))
    for r, st in enumerate(('hell', 'dunkel', 'laub', 'nadel')):
        d = TR.trans_set(st)
        for i in range(20):
            sh.paste(d[i], (i * 32, r * 32))
        for k, t in enumerate(TR.fills(st, 4)):
            sh.paste(t, ((r * 4 + k) * 32, 4 * 32))
    sh.save(TILES + '/Tileset_Uebergang.png')


# =============================================================== 3. Hohes Gras
def roll_shear(tile, phases, amp):
    px = tile.load()
    frames = []
    for ph in phases:
        out = Image.new('RGBA', tile.size, (0, 0, 0, 0))
        op = out.load()
        for y in range(tile.height):
            w = max(0.0, (31 - y) / 31.0) ** 1.0
            dx = int(round(amp * math.sin(ph) * w))
            for x in range(tile.width):
                op[(x + dx) % 32, y] = px[x, y]
        frames.append(out)
    return frames


def build_tallgrass():
    V = TR.tall_grass_variants()
    sh = Image.new('RGBA', (len(V) * 32, 4 * 32), (0, 0, 0, 0))
    for c, v in enumerate(V):
        for f, fr in enumerate(roll_shear(v.im, WIND_PH, 2.0)):
            sh.paste(fr, (c * 32, f * 32))
    sh.save(TILES + '/Tileset_HohesGras.png')
    return len(V)


# =============================================================== 4. Objekte
def gate(open_=False):
    sp = Spr(64, 32)
    c = P.WOOD
    for x0 in (3, 54):
        for y in range(5, 29):
            sp.set(x0, y, c[4]); sp.set(x0 + 1, y, c[3]); sp.set(x0 + 2, y, c[2]); sp.set(x0 + 3, y, c[1])
        sp.rect(x0, 5, x0 + 3, 5, c[5])
    if not open_:
        for y in (10, 21):
            for x in range(7, 54):
                sp.set(x, y, c[4]); sp.set(x, y + 1, c[3]); sp.set(x, y + 2, c[1])
        for x in range(8, 53):
            t = (x - 8) / 44.0
            yy = int(round(23 - t * 11))
            sp.set(x, yy, c[3]); sp.set(x, yy + 1, c[2])
        for x in (9, 51):
            for y in range(10, 24):
                sp.set(x, y, c[3]); sp.set(x + 1, y, c[2])
        # Riegel
        sp.rect(26, 15, 36, 16, P.IRON[3]); sp.set(37, 15, P.IRON[4])
    else:
        # Tor aufgeschwungen: Flaeche perspektivisch schmal am linken Pfosten
        for k in range(3):
            xx = 8 + k * 2
            for y in range(8 - k, 26 + k):
                sp.set(xx, y, c[4] if k == 0 else c[3] if k == 1 else c[2])
        for y in (10, 21):
            for x in range(8, 15):
                sp.set(x, y - (x - 8) // 3, c[3])
                sp.set(x, y + 1 - (x - 8) // 3, c[1])
    thick_outline(sp)
    base = Spr(64, 32)
    for x in range(8, 53, 2):
        base.set(x, 28, G_MD)
    base.paste(sp, 0, 0)
    return base


def collect_objects():
    CN.build()
    objs.update(CN.OBJ)
    for n, (fr, ms) in CN.ANIM.items():
        anims[n] = (fr, ms)
    # --- Faesser
    objs['Fass_Zu_A'] = P.barrel(1, 'zu')
    objs['Fass_Zu_B'] = P.barrel(2, 'zu', P.WOOD, P.IRON, w=8, h=20)
    objs['Fass_Leer'] = P.barrel(3, 'leer')
    objs['Fass_Aepfel'] = P.barrel(4, 'aepfel')
    objs['Fass_Korn'] = P.barrel(5, 'korn')
    objs['Fass_Fisch'] = P.barrel(6, 'fisch')
    objs['Fass_Dunkel'] = P.barrel(7, 'zu', P.WOOD_D)
    objs['Fass_Oel'] = P.barrel(8, 'oel', P.WOOD_D)
    objs['Fass_Liegend'] = P.barrel_lying(9)
    objs['Fass_Zerbrochen'] = P.barrel_broken(10)
    objs['Fass_Gruppe'] = P.barrel_group(11)
    objs['Fass_Klein'] = P.keg(12)
    # --- Kisten
    objs['Kiste_Klein'] = P.crate(18, 14, 'zu', 1, top_h=5)
    objs['Kiste_Mittel'] = P.crate(22, 18, 'zu', 2)
    objs['Kiste_Gross'] = P.crate(26, 22, 'zu', 3, top_h=7)
    for k, nm in (('aepfel', 'Aepfel'), ('karotten', 'Karotten'), ('fisch', 'Fisch'), ('offen', 'Offen'), ('stroh', 'Stroh'),
                  ('kohl', 'Kohl'), ('flaschen', 'Flaschen'), ('kartoffeln', 'Kartoffeln')):
        objs['Kiste_' + nm] = P.crate(22, 16, k, sum(map(ord, nm)) % 97)
    objs['Kiste_Stapel_2'] = P.crate_stack(12, 2)
    objs['Kiste_Stapel_3'] = P.crate_stack(14, 3)
    objs['Kiste_Kaputt'] = P.crate_broken(13)
    # --- Saecke, Koerbe, Eimer
    cl = [([P.CLOTH], 'Mehl'), ([[PURP[1], PURP[2], MAUVE, VIOLET, STONE[4], CREAM]], 'Violett'),
          ([[BROWN[1], BROWN[2], BROWN[3], AMBER, YELLOW, SAND]], 'Korn')]
    for i, (c, nm) in enumerate(cl):
        sp = Spr(32, 32)
        P.sack(sp, 16, 29, 18, 19, c[0], i)
        sp.outline(OUT)
        objs['Sack_' + nm] = sp
    sh = Spr(48, 32)
    for i, (ox, oy) in enumerate(((0, 4), (16, 4), (8, -3))):
        s2 = Spr(32, 32)
        P.sack(s2, 16, 29, 18, 19, cl[i % 3][0][0], 10 + i)
        s2.outline(OUT)
        sh.paste(s2, ox, oy)
    objs['Sack_Haufen'] = sh
    for k, nm in (('leer', 'Leer'), ('aepfel', 'Aepfel'), ('pilze', 'Pilze'), ('brot', 'Brot'), ('beeren', 'Beeren'), ('wolle', 'Wolle')):
        objs['Korb_' + nm] = P.basket(k, sum(map(ord, nm)) % 91)
    for k, nm in (('leer', 'Leer'), ('wasser', 'Wasser'), ('milch', 'Milch')):
        objs['Eimer_' + nm] = P.bucket(k, 3)
    # --- Truhen, Kuerbis, Heu, Holz
    objs['Truhe_Zu'] = P.chest('zu', 1)
    objs['Truhe_Gold'] = P.chest('gold', 2)
    objs['Truhe_Schatz'] = P.chest('schatz', 3)
    objs['Truhe_Leer'] = P.chest('leer', 4)
    objs['Truhe_Dunkel'] = P.chest('zu', 5, P.WOOD_D)
    objs['Kuerbis_Gross'] = P.pumpkin(1, 8)
    objs['Kuerbis_Klein'] = P.pumpkin(2, 6)
    objs['Kuerbis_Gesicht'] = P.pumpkin(3, 8, face=True)
    objs['Kuerbis_Gruppe'] = P.pumpkin_group(4)
    objs['Heuballen_Rund'] = P.haybale('rund', 1)
    objs['Heuballen_Eckig'] = P.haybale('eck', 2)
    objs['Holzstapel_Klein'] = P.woodstack(False, 1)
    objs['Holzstapel_Gross'] = P.woodstack(True, 2)
    # --- Moebel & Co
    objs['Tisch'] = P3.table(1)
    objs['Tisch_Gedeckt'] = P3.table(2, items=True)
    objs['Bank'] = P3.bench(3)
    objs['Bank_Lehne'] = P3.bench(4, back=True)
    objs['Hocker'] = P3.stool(5)
    objs['Stuhl'] = P3.chair(6)
    objs['Karren'] = P3.cart(7)
    objs['Karren_Heu'] = P3.cart(8, 'heu')
    objs['Karren_Kisten'] = P3.cart(9, 'kisten')
    objs['Karren_Faesser'] = P3.cart(10, 'faesser')
    objs['Schubkarre'] = P3.wheelbarrow(11)
    objs['Schubkarre_Voll'] = P3.wheelbarrow(12, True)
    objs['Wegweiser'] = P3.signpost('wegweiser')
    objs['Tafel'] = P3.signpost('tafel')
    objs['Warnschild'] = P3.signpost('warnung')
    objs['Schild_Schmied'] = P3.hanging_sign('schmied')
    objs['Schild_Taverne'] = P3.hanging_sign('taverne')
    objs['Schild_Laden'] = P3.hanging_sign('laden')
    objs['Briefkasten'] = P3.mailbox(1)
    objs['Vogelscheuche'] = P3.scarecrow(2)
    objs['Zelt_Braun'] = P3.tent(3)
    objs['Zelt_Violett'] = P3.tent(4, [PURP[1], PURP[3], MAUVE, VIOLET, STONE[4]])
    objs['Hackklotz_Axt'] = P3.chopping_block(5)
    objs['Amboss'] = P3.anvil(6)
    objs['Bienenkorb'] = P3.beehive(7)
    objs['Ruderboot'] = P3.rowboat(8)
    objs['Tor_Zu'] = gate(False)
    objs['Tor_Offen'] = gate(True)
    # --- animierte Props
    anims['Lagerfeuer_Gross'] = ([P2.campfire_frame_clean(f, 3, True) for f in range(6)], 100)
    anims['Kochfeuer'] = ([P2.cookfire_frame(f) for f in range(6)], 110)
    anims['Feuerschale'] = ([P2.brazier_frame(f) for f in range(6)], 100)
    anims['Fackel'] = ([P2.torch_frame(f) for f in range(6)], 100)
    anims['Kerzen'] = ([P2.candle_frame(f) for f in range(4)], 160)
    anims['Windlicht'] = ([P2.lantern_ground_frame(f) for f in range(6)], 130)
    anims['Fahne_Rot'] = ([P2.flag_frame(f) for f in range(8)], 130)
    anims['Fahne_Blau'] = ([P2.flag_frame(f, [BLUE[0], BLUE[1], BLUE[2]]) for f in range(8)], 130)
    anims['Brunnen'] = ([P2.well_frame(f) for f in range(4)], 280)
    anims['Wassertrog'] = ([P2.trough_frame(f) for f in range(4)], 280)
    anims['Fass_Wasser'] = ([P2.barrel_water_frame(f) for f in range(4)], 280)
    # Wind fuer Pflanzen
    for n, sp in list(objs.items()):
        if n.startswith(('Busch_', 'Farn_', 'Grasbusch_', 'Lavendel_', 'Heidekraut_', 'Brombeerbusch_')) and not n.startswith('Busch_Tot'):
            winds[n] = sp


def write_all():
    listed = []
    for n, sp in objs.items():
        sp.save(f'{OBJ_DIR}/{n}.png')
        listed.append((n, sp.w, sp.h))
    for n, (fr, ms) in anims.items():
        fr[0].save(f'{OBJ_DIR}/{n}.png')           # statisches Basisbild = Frame 0
        listed.append((n, fr[0].w, fr[0].h))
        strip_img([f.im for f in fr]).save(f'{ANIM_DIR}/{n}_Anim.png')
    for n, sp in winds.items():
        amp = 1.2 if n.startswith('Busch_') else 1.6
        strip_img(shear_rows(sp.im, WIND_PH, amp)).save(f'{ANIM_DIR}/{n}_Wind.png')
    # --- _Liste.txt (Objekte) ergaenzen
    lp = OBJ_DIR + '/_Liste.txt'
    txt = open(lp, encoding='utf-8').read().rstrip('\n').split('\n')
    have = {re.match(r'^(\w+)', l).group(1) for l in txt if re.match(r'^\w+\s*\|', l)}
    for n, w, h in listed:
        if n not in have:
            txt.append('%s | %dx%d | %.1fx%.1f' % (n, w, h, w / 32.0, h / 32.0))
    open(lp, 'w', encoding='utf-8').write('\n'.join(txt) + '\n')
    # --- Animiert/_Liste.txt ergaenzen
    ap = ANIM_DIR + '/_Liste.txt'
    atxt = open(ap, encoding='utf-8').read().rstrip('\n').split('\n')
    ahave = {re.match(r'^(\w+)', l).group(1) for l in atxt if re.match(r'^\w+\s*\|', l)}
    for n, (fr, ms) in anims.items():
        k = n + '_Anim'
        if k not in ahave:
            atxt.append('%s | %d | %dx%d | %d' % (k, len(fr), fr[0].w, fr[0].h, ms))
    for n, sp in winds.items():
        k = n + '_Wind'
        if k not in ahave:
            atxt.append('%s | 4 | %dx%d | 300' % (k, sp.w, sp.h))
    open(ap, 'w', encoding='utf-8').write('\n'.join(atxt) + '\n')
    return len(listed)


if __name__ == '__main__':
    build_fences()
    build_transitions()
    n = build_tallgrass()
    collect_objects()
    k = write_all()
    print('Zaun/Uebergang/HohesGras(%d) ok, Objekte: %d, animiert: %d, wind: %d' % (n, k, len(anims), len(winds)))
