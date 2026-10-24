"""TESTFRAU v3: Test-Charakter nach dem Pixel Law (ART_STYLE.md, Abschnitt 11/12) - Zelle 48x48, 8 Richtungen, Idle (6 Frames), Walk (8 Frames),
Portraits 64x64.

Proportionen nach Mara/Sheriff: grosser Kopf (16 Zeilen), kleines Gesicht, Haar rahmt es breit, knielanger Mantel mit ausgestelltem Saum, kurze Beine.
Koepfe sind von Hand gezeichnete Raster (sprite_testfrau.py), Mantel und Portrait nutzen Kurven mit Lichtschattierung oben-links.
Zeilen: S, SW, W, NW, N, NE, E, SE (NE/E/SE gespiegelt). Farben nur ueber style_lib.P.

Ausgabe nach Characters/Testfrau/: testfrau_stand_8dir.png, testfrau_idle_sheet.png, testfrau_walk_sheet.png, portraits/testfrau_*.png, testfrau_animation.json.
"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import json
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import style_lib as S  # noqa: E402
import sprite_testfrau as T  # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, '..'))
CELL = 48
ORDER = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE']
MIRROR = {'NE': 'NW', 'E': 'W', 'SE': 'SW'}
IDLE_BOB = [0, 0, 0, 1, 1, 0]
WALK_BOB = [0, 1, 1, 0, 0, 1, 1, 0]
IDLE_BLINK = {4}
OUTLINE = S.P['outline_dunkel']


class Cv:
    def __init__(self, w, h):
        self.w, self.h, self.px = w, h, {}

    def P(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[(x, y)] = c

    def R(self, x1, y1, x2, y2, c):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.P(x, y, c)

    def img(self, oy=0):
        im = S.new(self.w, self.h)
        for (x, y), c in self.px.items():
            if 0 <= y + oy < self.h:
                im.putpixel((x, y + oy), (*c, 255))
        return im


def front_details(cv, dy, tx):
    cx = T.CX_FRONT
    T.belt(cv, dy, cx, T.HW_FRONT, tx)
    px = 24 + tx
    for y in list(range(23, 28)) + list(range(30, 37)):
        cv.P(px, y + (dy if y < 30 else 0), T.C_K)                   # Knopfleiste
    for by in (24, 26):
        cv.P(px - 1, by + dy, T.BTN)
    for by in (32, 35):
        cv.P(px - 1, by, T.BTN)
    for sx in (-1, 1):                                               # Taschenklappen
        x0 = px + (-6 if sx < 0 else 3) + (0 if sx < 0 else 0)
        cv.R(x0, 32, x0 + 2, 32, T.C_K)
        cv.R(x0, 31, x0 + 2, 31, T.C_L)


def front(view, dy, lifts, swing, blk, sway):
    turn = view == 'SW'
    tx = -1 if turn else 0
    cv = Cv(CELL, CELL)
    T.legs_front(cv, 19, 25, lifts, tx)
    T.arm(cv, 15 + tx, 24 + dy, swing, True)
    T.arm(cv, 31 + tx, 24 + dy, -swing, False)
    T.coat(cv, dy, T.CX_FRONT, T.HW_FRONT, sway=-sway * 0.0 + (1 if swing > 0 else -1 if swing < 0 else 0) * 0.6, tx=tx)
    front_details(cv, dy, tx)
    T.strap(cv, 18 + tx, 21 + dy, 31 + tx, 31 + dy)
    T.bag(cv, 30 + tx, 29, sway)
    tpl = T.HEAD_SW if turn else T.HEAD_S
    T.blit(cv, T._blink(tpl) if blk else tpl, 15 + tx, 4 + dy)
    T.scarf(cv, dy, tx)
    return cv


def back(view, dy, lifts, swing, sway):
    turn = view == 'NW'
    tx = -1 if turn else 0
    cv = Cv(CELL, CELL)
    T.legs_front(cv, 19, 25, lifts, tx)
    T.arm(cv, 15 + tx, 24 + dy, swing, True)
    T.arm(cv, 31 + tx, 24 + dy, -swing, False)
    T.coat(cv, dy, T.CX_FRONT, T.HW_FRONT, sway=(1 if swing > 0 else -1 if swing < 0 else 0) * 0.6, tx=tx)
    T.belt(cv, dy, T.CX_FRONT, T.HW_FRONT, tx, buckle=False)
    for y in list(range(22, 28)) + list(range(30, 37)):
        cv.P(24 + tx, y + (dy if y < 30 else 0), T.C_D)               # Ruecken-Naht
    T.strap(cv, 30 + tx, 21 + dy, 17 + tx, 31 + dy)
    T.bag(cv, 12 + tx, 29, sway)
    T.blit(cv, T.HEAD_B, 15 + tx, 4 + dy)
    cv.R(26 + tx, 20 + dy, 27 + tx, 21 + dy, T.SC_L)                 # Schalende im Nacken
    return cv


def side(dy, phase, blk, idle):
    cv = Cv(CELL, CELL)
    if idle:
        far, near, swing, sway = (27, 45), (21, 45), 0, 0.0
    else:
        s_, c_, c2 = math.sin(2 * math.pi * phase), math.cos(2 * math.pi * phase), math.cos(2 * math.pi * (phase + 0.5))
        near = (round(24 - s_ * 4), 45 - round(max(0.0, c_) * 3))
        far = (round(24 + s_ * 4), 45 - round(max(0.0, c2) * 3))
        swing, sway = round(s_ * 3), s_ * 0.6
    T.leg_side(cv, far[0], far[1], True)
    T.leg_side(cv, near[0], near[1], False)
    T.coat(cv, dy, T.CX_SIDE, T.HW_SIDE, sway=sway)
    T.belt(cv, dy, T.CX_SIDE, T.HW_SIDE, 0)
    T.strap(cv, 26, 21 + dy, 22, 30 + dy)
    for y in range(31, 36):
        cv.P(24, y, T.C_K)
    cv.R(23 + swing, 24 + dy, 24 + swing, 30 + dy, T.C_B)            # Arm (nah)
    cv.R(23 + swing, 24 + dy, 23 + swing, 30 + dy, T.C_L)
    cv.R(24 + swing, 24 + dy, 24 + swing, 30 + dy, T.C_D)
    cv.R(23 + swing, 31 + dy, 24 + swing, 31 + dy, T.C_L)
    cv.R(23 + swing, 32 + dy, 24 + swing, 33 + dy, T.SKIN_L)
    cv.P(24 + swing, 33 + dy, T.SKIN_M)
    T.bag(cv, 21, 29, 0)
    T.blit(cv, T._blink(T.HEAD_W) if blk else T.HEAD_W, 15, 4 + dy)
    T.scarf(cv, dy, side=True)
    return cv


def render(view, kind, i):
    v = MIRROR.get(view, view)
    idle = kind == 'idle'
    phase = None if idle else i / 8.0
    dy = (IDLE_BOB if idle else WALK_BOB)[i]
    blk = idle and i in IDLE_BLINK
    if idle:
        lifts, swing, sway = (0, 0), 0, 0
    else:
        lifts = (round(max(0.0, math.cos(2 * math.pi * phase)) * 2), round(max(0.0, math.cos(2 * math.pi * (phase + 0.5))) * 2))
        swing = round(math.sin(2 * math.pi * phase) * 1)
        sway = round(math.sin(2 * math.pi * (phase + 0.25)) * 1)
    if v in ('S', 'SW'):
        cv = front(v, dy, lifts, swing, blk, sway)
    elif v in ('N', 'NW'):
        cv = back(v, dy, lifts, swing, sway)
    else:
        cv = side(dy, phase, blk, idle)
    im = S.add_outline(cv.img(oy=1), OUTLINE)
    if view in MIRROR:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


def sheet(kind, n):
    sh = S.new(CELL * n, CELL * len(ORDER))
    for r, view in enumerate(ORDER):
        for i in range(n):
            sh.paste(render(view, kind, i), (i * CELL, r * CELL))
    return sh


def portrait(mood):
    import portrait_testfrau as PT
    cv = Cv(64, 64)
    PT.draw(cv, mood)
    im = cv.img()
    for x in range(64):                                              # untere Kante als Outline-Farbe
        if im.getpixel((x, 63))[3] == 255:
            im.putpixel((x, 63), (*OUTLINE, 255))
    return S.add_outline(im, OUTLINE)


def main():
    os.makedirs(os.path.join(OUT, 'portraits'), exist_ok=True)
    idle, walk = sheet('idle', 6), sheet('walk', 8)
    stand = S.new(CELL * 8, CELL)
    for i, view in enumerate(ORDER):
        stand.paste(idle.crop((0, i * CELL, CELL, (i + 1) * CELL)), (i * CELL, 0))
    S.save(stand, os.path.join(OUT, 'testfrau_stand_8dir.png'), 'char')
    S.save(idle, os.path.join(OUT, 'testfrau_idle_sheet.png'), 'char')
    S.save(walk, os.path.join(OUT, 'testfrau_walk_sheet.png'), 'char')
    for mood in ('calm', 'blink', 'talk_A', 'talk_E', 'talk_O'):
        S.save(portrait(mood), os.path.join(OUT, 'portraits', f'testfrau_{mood}.png'), 'portrait')
    meta = {'name': 'Testfrau', 'cell': [CELL, CELL], 'pivot': 'bottom-center', 'ppu': 32, 'rows': ORDER,
            'mirrored': MIRROR, 'idle': {'frames': 6, 'fps': 6, 'sheet': 'testfrau_idle_sheet.png'},
            'walk': {'frames': 8, 'fps': 10, 'sheet': 'testfrau_walk_sheet.png'}, 'stand': 'testfrau_stand_8dir.png',
            'portraits': ['calm', 'blink', 'talk_A', 'talk_E', 'talk_O']}
    json.dump(meta, open(os.path.join(OUT, 'testfrau_animation.json'), 'w'), indent=2)
    print('fertig:', OUT)


if __name__ == '__main__':
    main()
