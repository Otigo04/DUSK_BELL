"""OTIGO: Charakter nach dem Pixel Law (ART_STYLE.md Abschnitt 11-13) - Zelle 48x48, 8 Richtungen (S,SW,W,NW,N,NE,E,SE; NE/E/SE gespiegelt),
Idle (6 Frames), Walk (8 Frames), Portraits 64x64 (calm, blink, talk_A, talk_E, talk_O).

Design (nach Foto des Users, Spiel-Version): nach hinten gestrichenes dunkles Haar mit Volumen, kraeftige Brauen, braune Augen, Stoppelbart,
olivgruene Jacke mit Reissverschluss ueber dunklem Shirt, dunkle Jeans, braune Stiefel. Zubehoer: Kette mit Anhaenger, Armbanduhr, Guertel mit Schnalle, Guerteltasche.
Ausgabe nach Characters/Otigo/. Aufruf: python3 gen_otigo.py
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
import sprite_otigo as T  # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, '..'))
CELL = 48
ORDER = ['S', 'SW', 'W', 'NW', 'N', 'NE', 'E', 'SE']
MIRROR = {'NE': 'NW', 'E': 'W', 'SE': 'SW'}
IDLE_BOB = [0, 0, 0, 1, 1, 0]
WALK_BOB = [0, 1, 1, 0, 0, 1, 1, 0]
IDLE_BLINK = {4}
OUTLINE = S.P['outline_dunkel']
HY = 3                                                              # Kopf-Oberkante (Kopf 17 Zeilen -> endet bei y19)


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


def front(view, dy, lifts, swing, blk, sway):
    turn = view == 'SW'
    tx = -1 if turn else 0
    cv = Cv(CELL, CELL)
    T.legs_front(cv, 19, 25, lifts, tx)
    T.arm(cv, 15 + tx, 23 + dy, swing, True)
    T.arm(cv, 31 + tx, 23 + dy, -swing, False)
    T.jacket(cv, dy, T.CX_FRONT, T.HW_FRONT, tx)
    T.zipper(cv, dy, tx)
    T.belt(cv, tx)
    T.chain(cv, dy, tx)
    T.pouch(cv, 30 + tx, 30 + (1 if sway > 0 else 0))
    tpl = T.HEAD_SW if turn else T.HEAD_S
    T.blit(cv, T.blink(tpl) if blk else tpl, 15 + tx, HY + dy)
    return cv


def back(view, dy, lifts, swing, sway):
    turn = view == 'NW'
    tx = -1 if turn else 0
    cv = Cv(CELL, CELL)
    T.legs_front(cv, 19, 25, lifts, tx)
    T.arm(cv, 15 + tx, 23 + dy, swing, True)
    T.arm(cv, 31 + tx, 23 + dy, -swing, False)
    T.jacket(cv, dy, T.CX_FRONT, T.HW_FRONT, tx)
    T.belt(cv, tx, buckle=False)
    for y in range(22, 32):
        cv.P(24 + tx, y + dy, T.J_D)                                # Ruecken-Naht
    T.pouch(cv, 13 + tx, 30 + (1 if sway > 0 else 0))
    T.blit(cv, T.HEAD_B, 15 + tx, HY + dy)
    return cv


def side(dy, phase, blk, idle):
    cv = Cv(CELL, CELL)
    if idle:
        far, near, swing, sway = (27, 45), (21, 45), 0, 0.0
    else:
        s_, c_, c2 = math.sin(2 * math.pi * phase), math.cos(2 * math.pi * phase), math.cos(2 * math.pi * (phase + 0.5))
        near = (round(24 - s_ * 4), 45 - round(max(0.0, c_) * 3))
        far = (round(24 + s_ * 4), 45 - round(max(0.0, c2) * 3))
        swing, sway = round(s_ * 3), s_
    T.leg_side(cv, far[0], far[1], True)
    T.leg_side(cv, near[0], near[1], False)
    T.jacket(cv, dy, T.CX_SIDE, T.HW_SIDE)
    T.belt(cv, 0, T.CX_SIDE, 5.2)
    cv.R(23 + swing, 23 + dy, 24 + swing, 30 + dy, T.J_B)
    cv.R(23 + swing, 23 + dy, 23 + swing, 30 + dy, T.J_L)
    cv.R(24 + swing, 23 + dy, 24 + swing, 30 + dy, T.J_D)
    cv.R(23 + swing, 31 + dy, 24 + swing, 31 + dy, T.J_D)
    cv.R(23 + swing, 32 + dy, 24 + swing, 33 + dy, T.SKIN_L)
    cv.P(24 + swing, 33 + dy, T.SKIN_M)
    cv.R(23 + swing, 30 + dy, 24 + swing, 30 + dy, T.METAL_L)       # Armbanduhr
    T.pouch(cv, 22, 30 + (1 if sway > 0 else 0))
    for y in range(20, 23):                                         # Kette im Ausschnitt
        cv.P(21, y + dy, T.METAL_L)
    T.blit(cv, T.blink(T.HEAD_W) if blk else T.HEAD_W, 15, HY + dy)
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
    import portrait_otigo as PT
    cv = Cv(64, 64)
    PT.draw(cv, mood)
    im = cv.img()
    for x in range(64):
        if im.getpixel((x, 63))[3] == 255:
            im.putpixel((x, 63), (*OUTLINE, 255))
    return S.add_outline(im, OUTLINE)


def main():
    os.makedirs(os.path.join(OUT, 'portraits'), exist_ok=True)
    idle, walk = sheet('idle', 6), sheet('walk', 8)
    stand = S.new(CELL * 8, CELL)
    for i, view in enumerate(ORDER):
        stand.paste(idle.crop((0, i * CELL, CELL, (i + 1) * CELL)), (i * CELL, 0))
    S.save(stand, os.path.join(OUT, 'otigo_stand_8dir.png'), 'char')
    S.save(idle, os.path.join(OUT, 'otigo_idle_sheet.png'), 'char')
    S.save(walk, os.path.join(OUT, 'otigo_walk_sheet.png'), 'char')
    for mood in ('calm', 'blink', 'talk_A', 'talk_E', 'talk_O'):
        S.save(portrait(mood), os.path.join(OUT, 'portraits', f'otigo_{mood}.png'), 'portrait')
    meta = {'name': 'Otigo', 'cell': [CELL, CELL], 'pivot': 'bottom-center', 'ppu': 32, 'rows': ORDER,
            'mirrored': MIRROR, 'idle': {'frames': 6, 'fps': 6, 'sheet': 'otigo_idle_sheet.png'},
            'walk': {'frames': 8, 'fps': 10, 'sheet': 'otigo_walk_sheet.png'}, 'stand': 'otigo_stand_8dir.png',
            'portraits': ['calm', 'blink', 'talk_A', 'talk_E', 'talk_O']}
    json.dump(meta, open(os.path.join(OUT, 'otigo_animation.json'), 'w'), indent=2)
    print('fertig:', OUT)


if __name__ == '__main__':
    main()
