"""MONSTER-VFX (Art/VFX/Monster). Nur Palette (39 Farben), keine halbtransparenten Pixel: Weichheit entsteht durch Bayer-Dither.
Quellen: Regelwerk (Warnstufen: Knarren, Krallen am Holz, Tatze/Fratze; Talisman-Feld), Kampfregeln (Enthuellungsmoment: Kamera nah, Ton dumpf,
dann das Grinsen), Monster-Bibel (Grinsen 2-3 px breit in #f2ead8, Augen #d64a6a - nur in diesen Farben, kein anderes Rot), Style-Bibel.
Sheets = Frames nebeneinander (Name_Sheet.png), Liste in _Liste.txt (Framegroesse, Frames, ms, Loop).

  Klopfwelle         64x64  8 Fr  90 ms   Ringe breiten sich von der Klopfstelle aus (Gast klopft dreimal, Monster-Klon starr)
  Enthuellung_Augen  32x16  6 Fr 100 ms   Monsterauge #d64a6a glimmt im Dunkeln auf (Silhouette am Tuerspion, Gast/Hausfrau)
  Grinsen_Aufblitzen 32x16  6 Fr 100 ms   Mundlinie, dann 2-3 px breite Zaehne #f2ead8, bleibt kurz, verschwindet
  Enthuellung_Burst  64x64  8 Fr  80 ms   Verkleidung bricht: Hautsplitter, rotes Aufblitzen, dumpfe Druckwelle
  Kratzer_Holz_A/B/C 32x32  statisch      Krallenspuren in Holz (Tuer, Laden, Balken); Kratzer_Holz_Sheet 6 Fr 140 ms wachsend
  Kratzer_Stein      32x32  statisch      Krallenspuren in Stein/Putz
  Fussspur_Mensch_L/R, Fussspur_Monster_L/R  32x32  Abdruecke im Matsch; Monster: gleiche Gestalt, aber zu lange, gleichmaessige Zehen
  Fussspuren_Pfad_Mensch/_Monster  64x32  vier Abdruecke im Wechsel
  Schleifspur_H 64x32, Schleifspur_V 32x64   zwei Rillen mit aufgeworfener Erde (etwas wurde gezogen)
  Handabdruck_Glas   32x32  verschmierter Abdruck mit zu langen Fingern auf dunklem Fensterglas
  Talisman_Puls      64x64  8 Fr 100 ms   das Talisman-Feld pulsiert als Ring (TAL/TAL_H)
  Talisman_Funken    32x32  6 Fr  90 ms   Funkenschauer beim Aufhaengen/Aktivieren
  Staub_Puff         32x32  6 Fr 100 ms   Staubwolke (Tuer-Wucht, Aufprall)
  Holzsplitter_Burst 32x32  6 Fr  80 ms   Holz splittert (Tatze durch den Spalt, Tuer-Wucht)
Aufruf: python monster_vfx.py   (schreibt auch Vorschau_MonsterVFX.png)"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from nwlib import *

OUTDIR = ART + '/VFX/Monster'
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

OL1, OL2 = H('1a1526'), H('2b2140')
SV_D, SV_M, SV_L = H('3d2e4a'), H('4f3d5c'), H('6b5a7a')
MOON, CREAM, SAND = H('e8e0f0'), H('fff1c9'), H('b89a72')
ST_D, ST_M, ST_L = H('4a4550'), H('6e6a74'), H('9a95a0')
EARTHS = [H(x) for x in ('2b2140', '3b2a22', '5c4033', '7a5a43', '9c7a5a', 'b89a72')]
WOOD_L, WOOD_M, WOOD_D = H('9c7a5a'), H('7a5a43'), H('5c4033')
SK_L, SK_M, SK_S = H('d19a7a'), H('8c5f4d'), H('5e3d33')
TEETH, EYE = H('f2ead8'), H('d64a6a')
TAL, TAL_H, TAL_D = H('6fd3e6'), H('a8f0ff'), H('2b6b8a')
NB_D = H('1f2a3d')


def put(sp, x, y, c, strength=1.0):
    """Pixel setzen; strength<1 -> Bayer-Dither (weiche Raender ohne Halbtransparenz)."""
    if strength >= 1.0 or BAYER[y % 4][x % 4] < strength * 16:
        sp.set(x, y, c)


def ring(sp, cx, cy, r, th, col, strength=1.0):
    for y in range(int(cy - r - th - 1), int(cy + r + th + 2)):
        for x in range(int(cx - r - th - 1), int(cx + r + th + 2)):
            if abs(math.hypot(x + 0.5 - cx, y + 0.5 - cy) - r) <= th / 2:
                put(sp, x, y, col, strength)


def disc(sp, cx, cy, r, col, strength=1.0):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                put(sp, x, y, col, strength)


# ====================================================================== Animationen
def klopfwelle(f):
    sp = Spr(64, 64)
    cols = [CREAM, CREAM, MOON, MOON, ST_L, ST_L, SV_L, SV_L]
    r = 4 + f * 3.6
    ring(sp, 32, 32, r, 2.2 if f < 5 else 1.4, cols[f], 1.0 if f < 3 else max(0.25, 1.0 - (f - 2) * 0.14))
    if f >= 2:
        ring(sp, 32, 32, r - 6, 1.4, cols[min(7, f + 1)], 0.6)
    if f == 0:
        disc(sp, 32, 32, 3, CREAM)
    return sp


def augen(f):
    sp = Spr(32, 16)
    for ex in (9, 19):
        if f == 0:
            for x in range(ex, ex + 4):
                put(sp, x, 8, EYE, 0.5)
        elif f == 1:
            for x in range(ex, ex + 5):
                sp.set(x, 8, EYE)
        else:
            w = 5
            for y, ww in ((7, 3), (8, 5), (9, 3)):
                for x in range(ex + (w - ww) // 2, ex + (w - ww) // 2 + ww):
                    sp.set(x, y, EYE)
            if f in (3, 4):
                for y in range(4, 13):
                    for x in range(ex - 3, ex + 8):
                        d = math.hypot(x - (ex + 2), (y - 8) * 1.4)
                        if 3.2 < d < (5.5 if f == 3 else 7):
                            put(sp, x, y, EYE, 0.22)
            if f == 5:
                for y in (7, 9):
                    for x in range(ex, ex + 5):
                        sp.set(x, y, (0, 0, 0, 0))
    return sp


def grinsen(f):
    sp = Spr(32, 16)
    cx, cy = 16, 8
    w = (10, 12, 14, 14, 14, 10)[f]
    for x in range(cx - w // 2, cx + w // 2):
        sp.set(x, cy, OL2)
    sp.set(cx - w // 2 - 1, cy - 1, OL2)
    sp.set(cx + w // 2, cy - 1, OL2)
    tw = (0, 2, 3, 3, 4, 0)[f]
    for y in (cy, cy + 1):
        for x in range(cx - tw // 2, cx - tw // 2 + tw):
            sp.set(x, y, TEETH)
    if tw:
        for x in range(cx - tw // 2 - 1, cx - tw // 2 + tw + 1):
            sp.set(x, cy + 2, OL1)
    return sp


def burst(f):
    sp = Spr(64, 64)
    if f == 0:
        disc(sp, 32, 32, 6, EYE)
        disc(sp, 32, 32, 3, CREAM)
    elif f == 1:
        ring(sp, 32, 32, 10, 3, EYE)
        disc(sp, 32, 32, 4, EYE, 0.6)
    if f >= 1:
        ring(sp, 32, 32, 6 + f * 4.5, 3.5 if f < 5 else 2, OL2 if f % 2 else SV_D, max(0.2, 1.0 - f * 0.11))   # dumpfe Druckwelle
    for k in range(30):                                          # Hautsplitter
        a = hsh(k, 1, 7) * 6.283
        v = 4 + hsh(k, 2, 7) * 6
        r = v * (f + 1) ** 0.85 + 3
        x, y = 32 + math.cos(a) * r, 32 + math.sin(a) * r * 0.9 + f * f * 0.4
        c = SK_L if hsh(k, 3, 7) < 0.4 else (SK_M if hsh(k, 3, 7) < 0.8 else TEETH)
        if f < 5:
            sp.rect(int(x), int(y), int(x) + 1, int(y) + 1, c)
        elif f < 7:
            sp.set(int(x), int(y), c)
        elif hsh(k, 4, 7) < 0.4:
            sp.set(int(x), int(y), SK_S)
    return sp


def talisman_puls(f):
    sp = Spr(64, 64)
    r = 6 + f * 3.6
    ring(sp, 32, 32, r, 2.4, TAL_H if f < 3 else TAL, max(0.3, 1.0 - f * 0.1))
    if f >= 1:
        ring(sp, 32, 32, r - 5, 1.6, TAL_D, 0.55)
    for k in range(8):
        a = k * 0.785 + f * 0.2
        put(sp, int(32 + math.cos(a) * r), int(32 + math.sin(a) * r), TAL_H)
    return sp


def talisman_funken(f):
    sp = Spr(32, 32)
    for k in range(14):
        a = hsh(k, 5, 8) * 6.283
        v = 2 + hsh(k, 6, 8) * 3
        r = v * (f + 1) ** 0.8
        x, y = 16 + math.cos(a) * r, 16 + math.sin(a) * r - f * 0.5
        c = TAL_H if (k + f) % 3 == 0 else (TAL if (k + f) % 3 == 1 else TAL_D)
        if f < 4:
            sp.set(int(x), int(y), c)
            if f < 2:
                sp.set(int(x) + 1, int(y), c)
        elif hsh(k, 7, 8) < 0.5:
            sp.set(int(x), int(y), TAL_D)
    return sp


def staub(f):
    sp = Spr(32, 32)
    cols = [ST_L, ST_L, ST_M, ST_M, ST_D, SV_L]
    for k in range(9):
        a = hsh(k, 1, 9) * 6.283
        d = (3 + hsh(k, 2, 9) * 4) * (f * 0.7 + 1)
        x, y = 16 + math.cos(a) * d, 20 + math.sin(a) * d * 0.55 - f * 1.2
        disc(sp, x, y, 3 + f * 0.7 - hsh(k, 3, 9) * 1.5, cols[f], max(0.25, 1.0 - f * 0.15))
    return sp


def splitter(f):
    sp = Spr(32, 32)
    for k in range(16):
        a = -3.4 + hsh(k, 1, 10) * 3.6
        v = 3 + hsh(k, 2, 10) * 5
        t = f + 1
        x, y = 16 + math.cos(a) * v * t * 0.8, 18 + math.sin(a) * v * t * 0.8 + f * f * 0.9
        c = (WOOD_L, SAND, WOOD_M, WOOD_D)[int(hsh(k, 3, 10) * 4)]
        L = 3 if k % 3 == 0 and f < 4 else 2
        if f < 5 or hsh(k, 4, 10) < 0.5:
            sp.line(int(x), int(y), int(x + math.cos(a + 1) * (L - 1)), int(y + math.sin(a + 1) * (L - 1)), c)
    return sp


# ====================================================================== Statische Spuren
def kratzer(variant, wood=True, f=None):
    """Krallenspuren: 3-4 Rillen leicht gebogen und schraeg; Holz: dunkle Rille mit hellem Rand/Spaenen, Stein: helle Ritzen."""
    sp = Spr(32, 32)
    n = (3, 4, 3)[variant % 3] if wood else 3
    ang = (math.radians(62), math.radians(78), math.radians(48))[variant % 3]
    length = 22 if f is None else int(4 + f * 4)
    for k in range(n):
        ox = 8 + k * (4 if variant != 1 else 3) + (variant * 2) % 3
        oy = 3 + (k % 2)
        for i in range(length):
            x = ox + math.cos(ang) * i * 0.55 + math.sin(i * 0.18) * 0.8
            y = oy + math.sin(ang) * i * 0.95
            if not (0 <= x < 32 and 0 <= y < 32):
                continue
            if wood:
                sp.set(int(x), int(y), OL2)
                if hsh(int(x), int(y), 11) < 0.7:
                    sp.set(int(x) - 1, int(y), WOOD_L)
                if i == 0 or (i < 3 and hsh(k, i, 12) < 0.6):
                    sp.set(int(x) + 1, int(y) - 1, SAND)             # Span am Ansatz
            else:
                sp.set(int(x), int(y), ST_L)
                if hsh(int(x), int(y), 13) < 0.4:
                    sp.set(int(x) + 1, int(y), ST_M)
    return sp


def footprint(kind, side):
    """Fussabdruck im Matsch (32x32), von oben, Zehen oben. Mensch: normaler Fuss. Monster (Monster-Bibel: gleiche Menschengestalt, aber
    zu gleichmaessig): schmale Ferse, fuenf gleich lange, zu lange Zehen in einer geraden Reihe."""
    sp = Spr(32, 32)
    if kind == 'mensch':
        parts = [(15, 25, 3.2, 4.2), (15.5, 18.5, 2.2, 3.0), (15, 13, 4.6, 3.8),
                 (19.5, 6.8, 2.0, 2.4), (15.8, 5.4, 1.5, 1.9), (12.8, 6.0, 1.4, 1.7), (10.6, 7.6, 1.3, 1.6), (8.8, 9.6, 1.2, 1.4)]
    else:
        parts = [(15, 26, 2.3, 4.4), (15, 19, 1.6, 3.6), (15, 13, 3.8, 4.2)] + [(9.6 + k * 2.4, 5.0, 0.95, 3.3) for k in range(5)]
    for x, y, rx, ry in parts:
        for yy in range(int(y - ry - 1), int(y + ry + 2)):
            for xx in range(int(x - rx - 1), int(x + rx + 2)):
                if ((xx + 0.5 - x) / rx) ** 2 + ((yy + 0.5 - y) / ry) ** 2 <= 1.0:
                    sp.set(xx, yy, EARTHS[0] if hsh(xx, yy, 14) < 0.75 else EARTHS[1])
    if side == 'R':                                               # rechter Fuss = gespiegelt
        m = Spr(32, 32)
        for yy in range(32):
            for xx in range(32):
                c = sp.get(xx, yy)
                if c[3]:
                    m.set(31 - xx, yy, c)
        sp = m
    rim = []
    for yy in range(32):                                          # aufgeworfener Rand oben links, heller
        for xx in range(32):
            if sp.solid(xx, yy) and not sp.solid(xx - 1, yy - 1) and not sp.solid(xx, yy - 1) and not sp.solid(xx - 1, yy):
                rim.append((xx - 1, yy - 1))
    for xx, yy in rim:
        sp.set(xx, yy, EARTHS[3])
    return sp


def trail(kind):
    out = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    for i in range(4):
        fp = footprint(kind, 'L' if i % 2 == 0 else 'R').im.crop((8, 0, 24, 32))
        out.alpha_composite(fp, (i * 16, 0 if i % 2 == 0 else 7), (0, 0, 16, 25) if i % 2 else (0, 0, 16, 32))
    return out


def schleifspur(horizontal=True):
    sp = Spr(64, 32) if horizontal else Spr(32, 64)
    L = 64 if horizontal else 64
    for rail in (11, 19):
        for i in range(L):
            wob = int(math.sin(i * 0.2 + rail) * 1.2)
            a, b = (i, rail + wob) if horizontal else (rail + wob, i)
            sp.set(a, b, EARTHS[0])
            sp.set(a, b + 1 if horizontal else b, EARTHS[1]) if horizontal else sp.set(a + 1, b, EARTHS[1])
            if hsh(i, rail, 15) < 0.3:                            # aufgeworfene Erde am Rand
                if horizontal:
                    sp.set(a, b - 2, EARTHS[4])
                else:
                    sp.set(a - 2, b, EARTHS[4])
    return sp


def handabdruck():
    sp = Spr(32, 32)
    for y in range(18, 29):                                       # Handballen
        for x in range(9, 20):
            if ((x - 14) / 5.5) ** 2 + ((y - 23) / 5.5) ** 2 <= 1.0 and hsh(x, y, 16) < 0.82:
                sp.set(x, y, ST_L if hsh(x, y, 17) < 0.6 else MOON)
    for k, (x0, ln) in enumerate(((8, 11), (11, 15), (14, 16), (17, 14), (20, 9))):   # fuenf zu lange Finger
        for i in range(ln):
            y = 19 - i
            x = x0 + (k - 2) * (i // 6) * 0 + int((2 - k) * i * 0.12)
            if hsh(x, y, 18) < 0.85:
                sp.set(x, y, ST_L if i % 3 else MOON)
                sp.set(x + 1, y, ST_M)
    for x in (10, 13, 16, 19):                                     # Schlieren nach unten
        for y in range(28, 31):
            if hsh(x, y, 19) < 0.6:
                sp.set(x, y, ST_M)
    return sp


# ====================================================================== Ausgabe
ANIMS = [('Klopfwelle', klopfwelle, 8, 90, 'einmal', (64, 64)), ('Enthuellung_Augen', augen, 6, 100, 'einmal', (32, 16)),
         ('Grinsen_Aufblitzen', grinsen, 6, 100, 'einmal', (32, 16)), ('Enthuellung_Burst', burst, 8, 80, 'einmal', (64, 64)),
         ('Talisman_Puls', talisman_puls, 8, 100, 'loop', (64, 64)), ('Talisman_Funken', talisman_funken, 6, 90, 'einmal', (32, 32)),
         ('Staub_Puff', staub, 6, 100, 'einmal', (32, 32)), ('Holzsplitter_Burst', splitter, 6, 80, 'einmal', (32, 32)),
         ('Kratzer_Holz', lambda f: kratzer(0, True, f), 6, 140, 'einmal', (32, 32))]
STATICS = {'Kratzer_Holz_A': lambda: kratzer(0), 'Kratzer_Holz_B': lambda: kratzer(1), 'Kratzer_Holz_C': lambda: kratzer(2),
           'Kratzer_Stein': lambda: kratzer(0, False), 'Fussspur_Mensch_L': lambda: footprint('mensch', 'L'),
           'Fussspur_Mensch_R': lambda: footprint('mensch', 'R'), 'Fussspur_Monster_L': lambda: footprint('monster', 'L'),
           'Fussspur_Monster_R': lambda: footprint('monster', 'R'), 'Schleifspur_H': lambda: schleifspur(True),
           'Schleifspur_V': lambda: schleifspur(False), 'Handabdruck_Glas': handabdruck}

if __name__ == '__main__':
    os.makedirs(OUTDIR, exist_ok=True)
    lines = ['# Monster-VFX (Art/VFX/Monster), erzeugt von monster_vfx.py', '# Name | Framegroesse | Frames | ms | Wiedergabe']
    sheets = []
    for name, fn, n, ms, mode, (w, h) in ANIMS:
        fr = [fn(f) for f in range(n)]
        strip = Image.new('RGBA', (w * n, h), (0, 0, 0, 0))
        for i, s in enumerate(fr):
            strip.paste(s.im, (i * w, 0))
        strip.save(OUTDIR + '/' + name + '_Sheet.png')
        lines.append('%s_Sheet | %dx%d | %d | %d | %s' % (name, w, h, n, ms, mode))
        sheets.append((name, strip))
    stat = {}
    for name, fn in STATICS.items():
        sp = fn()
        sp.save(OUTDIR + '/' + name + '.png')
        stat[name] = sp.im
        lines.append('%s | %dx%d | 1 | 0 | statisch' % (name, sp.w, sp.h))
    for kind in ('mensch', 'monster'):
        t = trail(kind)
        t.save(OUTDIR + '/Fussspuren_Pfad_%s.png' % kind.capitalize())
        stat['Fussspuren_Pfad_' + kind.capitalize()] = t
        lines.append('Fussspuren_Pfad_%s | 64x32 | 1 | 0 | statisch' % kind.capitalize())
    open(OUTDIR + '/_Liste.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    # Vorschau: Sheets 3x auf dunklem Grund, darunter Statics 4x
    S = 3
    W = max(s.width for _, s in sheets) * S + 20
    H = sum(s.height * S + 8 for _, s in sheets) + 20
    sh = Image.new('RGBA', (W, H + 4 * 70 + 140), (50, 44, 62, 255))
    y = 10
    for _, s in sheets:
        b = s.resize((s.width * S, s.height * S), Image.NEAREST)
        sh.alpha_composite(b, (10, y))
        y += b.height + 8
    x = 10
    for n, im in stat.items():
        b = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
        if x + b.width > W - 10:
            x = 10
            y += 100
        bg = Image.new('RGBA', b.size, (78, 60, 52, 255))
        bg.alpha_composite(b)
        sh.alpha_composite(bg, (x, y))
        x += b.width + 8
    sh.crop((0, 0, W, y + 110)).save(OUTDIR + '/Vorschau_MonsterVFX.png')
    print('Monster-VFX:', len(ANIMS), 'Sheets,', len(stat), 'statische ->', OUTDIR)
