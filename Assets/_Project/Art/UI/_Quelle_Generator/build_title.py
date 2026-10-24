"""Baut den Titelbildschirm (480x270, wie die Spielkamera): Hintergrund, Sterne, Logo "DUSK BELL".
Nur Farben der Style-Bibel (39er Palette). Aufruf: python build_title.py   (nach build_font.py)

Ausgabe in ../Title/:
  Title_Hintergrund.png   480x270  Dorf bei Daemmerung, Glockenturm vor dem Mond
  Title_Sterne_A/B.png    480x270  zwei Sternenbilder (Funkeln durch Wechsel), transparent
  Title_Logo.png          Schriftzug DUSK BELL, transparent
  Title_Vorschau.png      Hintergrund + Logo, 3x, zum Anschauen
"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import math
import os
import random
from PIL import Image, ImageDraw, ImageFont

from nwui import ALLOWED, rgb, new, put, rect, scaled, used_colors, outline

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "Title"))
FONT = os.path.abspath(os.path.join(HERE, "..", "Font", "Nightward_Pixel.ttf"))
os.makedirs(OUT, exist_ok=True)

W, H = 480, 270
HORIZON = 188          # Boden beginnt hier
rnd = random.Random(412)   # "412 nach dem Schweigen"

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def thr(x, y):
    return (BAYER[y % 4][x % 4] + 0.5) / 16.0


def dither(im, x, y, t, a, b):
    """t in 0..1: Anteil von b gegenueber a."""
    put(im, x, y, b if t > thr(x, y) else a)


def save(im, name):
    assert used_colors(im) <= ALLOWED, (name, used_colors(im) - ALLOWED)
    im.save(os.path.join(OUT, name))


# ------------------------------------------------------------------ Himmel
def sky(im):
    bands = ["nb1", "nb2", "nb3"]
    for y in range(0, HORIZON + 30):
        t = y / (HORIZON + 10)
        # drei Baender mit dithering-Uebergang
        if t < 0.30:
            c = "nb1"
            for x in range(W):
                put(im, x, y, c)
        elif t < 0.46:
            k = (t - 0.30) / 0.16
            for x in range(W):
                dither(im, x, y, k, "nb1", "nb2")
        elif t < 0.64:
            for x in range(W):
                put(im, x, y, "nb2")
        elif t < 0.82:
            k = (t - 0.64) / 0.18
            for x in range(W):
                dither(im, x, y, k, "nb2", "nb3")
        else:
            for x in range(W):
                put(im, x, y, "nb3")
    # warmer Daemmerungsstreifen am Horizont: Lichter warm-gelb verschoben
    for y in range(HORIZON - 14, HORIZON + 4):
        k = (y - (HORIZON - 14)) / 18.0
        for x in range(W):
            if k * 0.55 > thr(x, y):
                put(im, x, y, "sv3")


MOON = (372, 64, 24)


def moon(im):
    cx, cy, r = MOON
    # Halo: lockeres Dithering aus Nachtblau hell
    for y in range(cy - 46, cy + 47):
        for x in range(cx - 46, cx + 47):
            d = math.hypot(x - cx, y - cy)
            if r < d < 46:
                k = 1 - (d - r) / (46 - r)
                if k * 0.5 > thr(x, y):
                    put(im, x, y, "nb3")
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                # Schatten unten links (kuehl), Licht oben rechts
                lx, ly = (x - cx) / r, (y - cy) / r
                shade = (-lx + ly) * 0.5
                c = "moon"
                if shade > 0.55 and thr(x, y) < 0.9:
                    c = "s3"
                elif shade > 0.38 and thr(x, y) < 0.5:
                    c = "s3"
                put(im, x, y, c)
    # Krater
    for (dx, dy, rr) in ((-8, -6, 3), (8, 5, 3), (-1, 12, 2), (11, -10, 2)):
        for y in range(-rr, rr + 1):
            for x in range(-rr, rr + 1):
                if math.hypot(x, y) <= rr:
                    put(im, cx + dx + x, cy + dy + y, "s3")
                    if x + y < -rr * 0.6:
                        put(im, cx + dx + x, cy + dy + y, "moon")


STAR_RECTS = []


def stars():
    """Zwei Bilder: gemeinsame feste Sterne + je ein Satz, der in A bzw. B leuchtet."""
    a, b = new(W, H), new(W, H)
    pts = []
    tries = 0
    while len(pts) < 95 and tries < 5000:
        tries += 1
        x = rnd.randrange(2, W - 2)
        y = rnd.randrange(2, 130)
        if math.hypot(x - MOON[0], y - MOON[1]) < MOON[2] + 14:
            continue
        # links dichter, weil dort das Menue steht (ruhiger Himmel rechts)
        pts.append((x, y))
    for i, (x, y) in enumerate(pts):
        col = "candle" if i % 7 == 0 else "moon"
        group = i % 3     # 0 = nur A, 1 = nur B, 2 = immer
        target = [a] if group == 0 else [b] if group == 1 else [a, b]
        for im in target:
            put(im, x, y, col)
        if i % 11 == 0:          # grosse Sterne als Kreuz, funkeln versetzt
            for im in ([a] if group != 1 else [b]):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(im, x + dx, y + dy, "nb3" if y > 40 else "sv3")
    return a, b


# ------------------------------------------------------------------ Silhouetten
def hills(im):
    # ferne Huegel, violett
    for x in range(W):
        top = int(HORIZON - 14 + 7 * math.sin(x / 41.0) + 4 * math.sin(x / 15.0 + 1.3))
        for y in range(top, HORIZON + 30):
            put(im, x, y, "sv1")
        put(im, x, top, "sv2")
    # zweite Huegelreihe, naeher und dunkler
    for x in range(W):
        top = int(HORIZON - 4 + 5 * math.sin(x / 29.0 + 2.0) + 3 * math.sin(x / 9.0))
        for y in range(top, HORIZON + 30):
            put(im, x, y, "on")


def conifer(im, cx, base, h, w, body, rim, light_side=1):
    """Tanne aus gestapelten Dreiecken. rim = Licht an der Mondseite (rechts)."""
    tiers = max(3, h // 12)
    tier_h = h / tiers
    for t in range(tiers):
        top = base - h + int(t * tier_h * 0.78)
        bottom = base - h + int((t + 1) * tier_h * 0.78 + tier_h * 0.5)
        half_max = w * (0.38 + 0.62 * (t + 1) / tiers) / 2
        for y in range(top, min(bottom, base) + 1):
            k = (y - top) / max(1, bottom - top)
            half = max(1, int(half_max * k))
            # zackige Kante
            for x in range(cx - half, cx + half + 1):
                put(im, x, y, body)
            if light_side and half > 1:
                put(im, cx + half, y, rim)
                if (y + t) % 3 == 0 and half > 3:
                    put(im, cx + half - 1, y, rim)
    # Stamm
    rect(im, cx - 1, base, cx, base + 6, "ed" if body != "od" else "od")


def tree_line(im):
    x = -6
    while x < W + 10:
        h = rnd.randrange(34, 58)
        conifer(im, x, HORIZON + 14, h, rnd.randrange(16, 24), "fd", "fm")
        x += rnd.randrange(9, 17)


# ------------------------------------------------------------------ Haeuser
def house(im, x, base, w, h, roof_h, wall="s1", wall_lit="s2", roof="sv1", roof_rim="sv3",
          windows=((0.25, 0.3), (0.65, 0.3)), lit=(1, 1), chimney=True):
    top = base - h
    # Wand
    rect(im, x, top, x + w - 1, base - 1, wall)
    rect(im, x + w - 2, top, x + w - 1, base - 1, wall_lit)        # Mondlicht rechts
    rect(im, x, top, x + 2, base - 1, "sv1")                       # Schatten links
    # Fachwerk / Holzbalken
    for yy in range(top + 4, base - 1, 6):
        for xx in range(x + 3, x + w - 2):
            if (xx + yy) % 5 == 0:
                put(im, xx, yy, "s2")
    # Dach (Satteldach)
    mid = x + w // 2
    for i in range(roof_h):
        y = top - i - 1
        half = (w // 2 + 3) - int(i * (w // 2 + 3) / (roof_h + 1))
        for xx in range(mid - half, mid + half + 1):
            put(im, xx, y, roof)
        put(im, mid + half, y, roof_rim)
        put(im, mid - half, y, "on")
    rect(im, x - 2, top, x + w + 1, top, "on")                     # Traufe
    rect(im, x - 3, top - 1, x + w + 2, top - 1, "sv2")
    if chimney:
        cxp = mid + w // 5
        rect(im, cxp, top - roof_h - 3, cxp + 3, top - roof_h + 3, "s1")
        rect(im, cxp + 3, top - roof_h - 3, cxp + 3, top - roof_h + 3, "s2")
        rect(im, cxp - 1, top - roof_h - 4, cxp + 4, top - roof_h - 4, "on")
    # Fenster
    for i, (fx, fy) in enumerate(windows):
        wx = x + int(fx * w)
        wy = top + int(fy * h)
        on = lit[i % len(lit)]
        rect(im, wx - 1, wy - 1, wx + 4, wy + 5, "od")
        rect(im, wx, wy, wx + 3, wy + 4, "ly" if on else "nb1")
        if on:
            rect(im, wx, wy + 3, wx + 3, wy + 4, "lo")
            put(im, wx + 1, wy, "candle")
            rect(im, wx + 2, wy, wx + 2, wy + 4, "od")             # Fensterkreuz
            rect(im, wx, wy + 2, wx + 3, wy + 2, "od")
            # Lichtschein auf Wand davor
            for yy in range(wy - 4, wy + 12):
                for xx in range(wx - 6, wx + 10):
                    d = math.hypot((xx - wx - 1.5) / 1.4, yy - wy - 2)
                    if 5 < d < 9 and (9 - d) / 4 * 0.55 > thr(xx, yy) and not (wx - 1 <= xx <= wx + 4 and wy - 1 <= yy <= wy + 5):
                        if top <= yy < base:
                            put(im, xx, yy, "wm")
    # Tuer
    dx = x + w // 2 - 2
    rect(im, dx, base - 9, dx + 4, base - 1, "ed")
    rect(im, dx + 1, base - 8, dx + 3, base - 1, "wd")
    put(im, dx + 3, base - 4, "ly")


def smoke(im, x, y):
    for i in range(14):
        yy = y - i * 2
        xx = x + int(math.sin(i * 0.7) * 2) + i // 3
        for dx in range(-1, 2):
            if (i + dx) % 2 == 0 or i < 4:
                dither(im, xx + dx, yy, 0.65, "nb3", "nb3") if False else None
        put(im, xx, yy, "nb3" if i % 2 == 0 else "sv3")
        put(im, xx + 1, yy - 1, "nb3")


def tower(im, bx, base):
    """Der Glockenturm: Mittelpunkt des Bildes. Schaft, Uhr, Glockenstuhl, Spitze."""
    w = 34
    x0 = bx - w // 2
    shaft_top = base - 96
    # Schaft: Steinmauer, Mondlicht rechts
    rect(im, x0, shaft_top, x0 + w - 1, base - 1, "s1")
    rect(im, x0 + w - 6, shaft_top, x0 + w - 1, base - 1, "s2")
    rect(im, x0, shaft_top, x0 + 5, base - 1, "sv1")
    # Mauerwerk-Fugen
    for yy in range(shaft_top + 3, base - 1, 5):
        for xx in range(x0 + 1, x0 + w - 1):
            if (xx + (yy // 5) * 3) % 7 == 0:
                put(im, xx, yy, "s2" if xx > x0 + w - 7 else "sv2")
    # Sockel-Strebepfeiler
    rect(im, x0 - 2, base - 12, x0 + w + 1, base - 1, "s1")
    rect(im, x0 + w - 4, base - 12, x0 + w + 1, base - 1, "s2")
    rect(im, x0 - 2, base - 12, x0 + 3, base - 1, "sv1")
    rect(im, x0 - 2, base - 13, x0 + w + 1, base - 13, "s3")
    # Tor
    rect(im, bx - 4, base - 16, bx + 3, base - 1, "od")
    rect(im, bx - 3, base - 15, bx + 2, base - 1, "ed")
    rect(im, bx - 3, base - 15, bx - 1, base - 1, "wd")
    for yy in range(base - 17, base - 15):
        rect(im, bx - 3, yy, bx + 2, yy, "od")
    # Uhr
    ccx, ccy = bx, shaft_top + 36
    for y in range(-8, 9):
        for x in range(-8, 9):
            d = math.hypot(x, y)
            if d <= 8:
                put(im, ccx + x, ccy + y, "od")
            if d <= 6.6:
                put(im, ccx + x, ccy + y, "candle")
    for k in range(12):
        a = k * math.pi / 6
        put(im, ccx + int(round(5.4 * math.sin(a))), ccy - int(round(5.4 * math.cos(a))), "od")
    # Zeiger: halb sieben
    for i in range(0, 5):
        put(im, ccx, ccy + i, "od")                  # Minutenzeiger zeigt 6
    for i in range(0, 4):
        put(im, ccx - i // 2 - 0, ccy + i, "od") if i > 1 else None
    put(im, ccx, ccy, "od")
    put(im, ccx, ccy - 1, "od")
    # Glockenstuhl (breiter, Holz+Stein)
    st_top = shaft_top - 30
    rect(im, x0 - 3, shaft_top - 2, x0 + w + 2, shaft_top - 1, "s2")
    rect(im, x0 - 3, shaft_top - 2, x0 - 1, shaft_top - 1, "sv2")
    rect(im, x0 - 1, st_top, x0 + w, shaft_top - 3, "s1")
    rect(im, x0 + w - 5, st_top, x0 + w, shaft_top - 3, "s2")
    rect(im, x0 - 1, st_top, x0 + 4, shaft_top - 3, "sv1")
    # Bogenoeffnung
    ax0, ax1 = bx - 9, bx + 9
    ay0 = st_top + 4
    ay1 = shaft_top - 3
    for y in range(ay0, ay1 + 1):
        for x in range(ax0, ax1 + 1):
            dx = (x - bx)
            inside = True
            if y < ay0 + 9:
                inside = math.hypot(dx, y - (ay0 + 9)) <= 9
            if inside:
                put(im, x, y, "od")
    # Lichtschein der Laterne im Inneren (warm), Dithering
    for y in range(ay0, ay1 + 1):
        for x in range(ax0 + 1, ax1):
            dx = x - bx
            inside = True
            if y < ay0 + 9:
                inside = math.hypot(dx, y - (ay0 + 9)) <= 8
            if inside:
                d = math.hypot(dx, y - (ay0 + 14))
                if (1 - d / 14) * 1.1 > thr(x, y):
                    put(im, x, y, "ed")
    # Glocke
    bcx, bcy = bx, ay0 + 8
    rect(im, bcx - 1, ay0 + 1, bcx + 1, ay0 + 3, "wm")                    # Joch/Balken
    rect(im, bcx - 6, ay0 + 1, bcx + 6, ay0 + 2, "wd")
    bell_rows = [
        (4, 1), (4, 2), (5, 3), (6, 4), (6, 5), (7, 6), (7, 7), (8, 8), (9, 9),
    ]
    for i, (half, dy) in enumerate(bell_rows):
        y = bcy + dy - 3
        for x in range(bcx - half + 2, bcx + half - 1):
            c = "ly"
            if x > bcx + half - 5:
                c = "lo"
            if x < bcx - half + 4:
                c = "lo" if i > 3 else "ly"
            put(im, x, y, c)
        put(im, bcx - half + 2, y, "od") if False else None
    # Glanzlicht und Rand der Glocke
    for y in range(bcy - 2, bcy + 4):
        put(im, bcx - 2, y, "candle")
    rect(im, bcx - 7, bcy + 6, bcx + 6, bcy + 6, "fire")
    rect(im, bcx - 7, bcy + 7, bcx + 6, bcy + 7, "od")
    put(im, bcx, bcy + 8, "wm")                                            # Klöppel
    put(im, bcx, bcy + 9, "wm")
    # Spitze
    sp_h = 40
    mid = bx
    for i in range(sp_h):
        y = st_top - 1 - i
        half = int((w // 2 + 4) * (1 - i / sp_h))
        for x in range(mid - half, mid + half + 1):
            put(im, x, y, "sv1")
        put(im, mid + half, y, "sv3")
        if half > 2:
            put(im, mid + half - 1, y, "sv2")
        put(im, mid - half, y, "on")
        # Dachziegel-Linien
        if i % 5 == 4:
            for x in range(mid - half + 1, mid + half):
                put(im, x, y, "on" if x < mid else "sv2")
    rect(im, x0 - 4, st_top, x0 + w + 4, st_top, "on")
    rect(im, x0 - 5, st_top - 1, x0 + w + 5, st_top - 1, "sv2")
    # Wetterhahn / Kreuz
    top_y = st_top - sp_h
    rect(im, mid, top_y - 10, mid, top_y, "od")
    rect(im, mid - 3, top_y - 7, mid + 3, top_y - 7, "od")
    rect(im, mid - 1, top_y - 12, mid + 1, top_y - 12, "od")
    put(im, mid + 1, top_y - 8, "s3")
    # Rim-Light am Turmstein
    return (bx, ay0)


def fence(im, x0, x1, y):
    for x in range(x0, x1, 5):
        rect(im, x, y - 6, x + 1, y, "wd")
        put(im, x, y - 7, "wd")
        put(im, x + 1, y - 6, "wm")
    rect(im, x0, y - 4, x1, y - 4, "wd")
    rect(im, x0, y - 2, x1, y - 2, "wd")


def lantern_post(im, x, y):
    rect(im, x, y - 22, x + 1, y, "ed")
    rect(im, x - 3, y - 24, x + 4, y - 23, "od")
    rect(im, x - 2, y - 22, x + 3, y - 18, "od")
    rect(im, x - 1, y - 21, x + 2, y - 19, "ly")
    put(im, x, y - 20, "candle")
    rect(im, x - 3, y - 17, x + 4, y - 17, "od")
    # Lichtinsel
    for yy in range(y - 42, y + 16):
        for xx in range(x - 34, x + 36):
            d = math.hypot((xx - x) / 1.6, yy - (y - 20))
            if d < 22 and (1 - d / 22) * 0.9 > thr(xx, yy):
                if yy >= HORIZON:
                    put(im, xx, yy, "wm")
                else:
                    put(im, xx, yy, "lo")


# ------------------------------------------------------------------ Boden
def ground(im):
    for y in range(HORIZON, H):
        t = (y - HORIZON) / (H - HORIZON)
        for x in range(W):
            if t < 0.25:
                dither(im, x, y, t / 0.25, "fm", "fd")
            else:
                dither(im, x, y, min(1, (t - 0.25) / 0.6) * 0.35, "fd", "on")
    # Grasbueschel
    for _ in range(190):
        x = rnd.randrange(0, W)
        y = rnd.randrange(HORIZON + 3, H - 2)
        c = "g" if y < HORIZON + 40 else "fm"
        put(im, x, y, c)
        put(im, x, y - 1, c)
        if rnd.random() < 0.5:
            put(im, x + 1, y - 2, c)


def path(im):
    for y in range(HORIZON + 2, H):
        t = (y - HORIZON) / (H - HORIZON)
        cx = 318 - (t ** 1.4) * 46
        half = 5 + t * 52
        for x in range(int(cx - half), int(cx + half) + 1):
            edge = abs(x - cx) > half - 2
            if edge:
                dither(im, x, y, 0.5, "wd", "ed")
            else:
                dither(im, x, y, 0.15 + 0.45 * t, "wd", "ed")
        # Wagenspuren
        if t > 0.15:
            put(im, int(cx - half * 0.35), y, "ed")
            put(im, int(cx + half * 0.35), y, "ed")
    # Steinchen
    for _ in range(46):
        y = rnd.randrange(HORIZON + 8, H - 2)
        t = (y - HORIZON) / (H - HORIZON)
        cx = 318 - (t ** 1.4) * 46
        half = 5 + t * 52
        x = int(cx + rnd.uniform(-half * 0.8, half * 0.8))
        put(im, x, y, "wm")


def fog(im):
    for y in range(HORIZON - 10, HORIZON + 22):
        k = 1 - abs(y - (HORIZON + 3)) / 16.0
        if k <= 0:
            continue
        for x in range(W):
            n = 0.5 + 0.5 * math.sin(x / 23.0 + y / 4.0) * math.sin(x / 61.0)
            if k * n * 0.5 > thr(x, y):
                put(im, x, y, "nb2" if y < HORIZON + 3 else "sv2")


def foreground_trees(im):
    # linke Seite: dunkle Rahmung, hinter den Menuetasten
    conifer(im, 20, 285, 262, 78, "od", "on")
    conifer(im, 72, 285, 214, 62, "on", "sv1")
    conifer(im, -4, 285, 300, 90, "od", "on")
    conifer(im, 118, 285, 120, 40, "on", "sv1")
    # rechte Kante
    conifer(im, 468, 285, 232, 72, "od", "on")
    conifer(im, 440, 285, 128, 44, "on", "sv1")
    conifer(im, 492, 285, 280, 80, "od", "on")


def vignette(im):
    cx, cy = W / 2, H / 2
    for y in range(H):
        for x in range(W):
            d = math.hypot((x - cx) / (W / 2), (y - cy) / (H / 2))
            k = (d - 0.80) * 1.4
            if k > 0 and k > thr(x, y):
                put(im, x, y, "on")
    # leichter Verlauf links, damit das Menue Ruhe hat
    for y in range(H):
        for x in range(0, 170):
            k = (1 - x / 170.0) * 0.55
            if k > thr(x, y):
                put(im, x, y, "on")


def fireflies(im):
    for _ in range(14):
        x = rnd.randrange(150, 470)
        y = rnd.randrange(HORIZON - 4, HORIZON + 60)
        put(im, x, y, "leaf")


# ------------------------------------------------------------------ Hintergrund
def build_background():
    im = new(W, H)
    sky(im)
    moon(im)
    # Sterne werden getrennt gezeichnet (Funkeln), nicht hier.
    hills(im)
    tree_line(im)
    ground(im)

    # hintere Haeuserreihe (klein, dunkler)
    house(im, 196, HORIZON + 12, 34, 22, 14, wall="sv1", wall_lit="sv2", roof="on", roof_rim="sv2",
          windows=((0.3, 0.35),), lit=(1,), chimney=False)
    house(im, 420, HORIZON + 12, 36, 24, 14, wall="sv1", wall_lit="sv2", roof="on", roof_rim="sv2",
          windows=((0.5, 0.35),), lit=(1,), chimney=False)
    smoke(im, 224, HORIZON - 14)

    tower(im, 345, HORIZON + 16)

    # vordere Haeuser
    house(im, 248, HORIZON + 24, 44, 30, 18, windows=((0.18, 0.3), (0.62, 0.3)), lit=(1, 1))
    house(im, 388, HORIZON + 26, 48, 32, 20, windows=((0.18, 0.3), (0.66, 0.3)), lit=(1, 0))
    house(im, 150, HORIZON + 26, 40, 28, 16, windows=((0.22, 0.32), (0.62, 0.32)), lit=(1, 1))
    smoke(im, 405, HORIZON - 36)
    smoke(im, 276, HORIZON - 14)

    path(im)
    fog(im)
    fence(im, 100, 146, HORIZON + 40)
    fence(im, 440, 476, HORIZON + 34)
    lantern_post(im, 288, 226)
    lantern_post(im, 410, 236)
    fireflies(im)
    foreground_trees(im)
    vignette(im)
    save(im, "Title_Hintergrund.png")
    return im


# ------------------------------------------------------------------ Logo
def glyph_bitmap(text, size=8):
    """Rastert Text mit der Projekt-Pixelschrift 1:1 (5x7-Zellen) in eine 1-Bit-Maske."""
    f = ImageFont.truetype(FONT, size)
    w = int(f.getlength(text)) + 2
    mask = Image.new("L", (w, 12), 0)
    d = ImageDraw.Draw(mask)
    d.fontmode = "1"
    d.text((0, 0), text, font=f, fill=255)
    return mask


def build_logo():
    scale = 4
    word1 = glyph_bitmap("DUSK")
    word2 = glyph_bitmap("BELL")

    def crop(m):
        bb = m.getbbox()
        return m.crop(bb)
    w1, w2 = crop(word1), crop(word2)
    gap = 5
    pad = 6
    # beide Woerter in eine Zeile, Glocke dazwischen
    bell = build_bell()
    total_w = (w1.width + gap + w2.width) * scale + bell.width * 2 + 14 * scale // 3
    th = max(w1.height, w2.height) * scale
    im = new(total_w + pad * 2, th + pad * 2 + 6)
    x = pad
    y = pad
    parts = [(w1, x)]
    xw2 = x + w1.width * scale + bell.width * 2 + 14
    parts.append((w2, xw2))
    for m, ox in parts:
        # Dunkle Kontur (2 px), Schatten, Fuellung mit Farbverlauf
        for my in range(m.height):
            for mx in range(m.width):
                if m.getpixel((mx, my)) == 0:
                    continue
                px, py = ox + mx * scale, y + my * scale
                # Schatten (1 Zelle nach unten rechts)
                rect(im, px + 2, py + 2, px + scale + 1, py + scale + 1, "on")
        for my in range(m.height):
            for mx in range(m.width):
                if m.getpixel((mx, my)) == 0:
                    continue
                px, py = ox + mx * scale, y + my * scale
                row = my / max(1, m.height - 1)
                col = "candle" if row < 0.15 else "ly" if row < 0.55 else "lo" if row < 0.85 else "fire"
                rect(im, px, py, px + scale - 1, py + scale - 1, col)
                # Facette: untere/rechte Kante der Zelle eine Stufe dunkler
                shade = {"candle": "ly", "ly": "lo", "lo": "fire", "fire": "wm"}[col]
                rect(im, px, py + scale - 2, px + scale - 1, py + scale - 1, shade)
    # Glocke zwischen den Woertern, mit Schatten
    bx = x + w1.width * scale + 7
    by = y + (th - bell.height * 2) // 2 - 2
    big = scaled(bell, 2)
    im.alpha_composite(big, (bx, by))
    # 2px dunkle Aussenkontur um das ganze Logo (Zellen-Rand)
    im = outline_n(im, "od", 2)
    save(im, "Title_Logo.png")
    return im


def outline_n(im, name, n):
    for _ in range(n):
        outline(im, name)
    return im


def build_bell():
    rows = [
        "......oooo......",
        ".....oyyyyo.....",
        "......oWWo......",
        ".....oyyyyo.....",
        "....oyYyyyyo....",
        "....oyYyyyyo....",
        "...oyYyyyyyLo...",
        "...oyYyyyyyLo...",
        "..oyYyyyyyyLLo..",
        "..oyYyyyyyyLLo..",
        ".oyYyyyyyyyLLLo.",
        ".oyyyyyyyyyLLLo.",
        "oLLLLLLLLLLLLLLo",
        "oFFFFFFFFFFFFFFo",
        ".oooooooooooooo.",
        ".......oo.......",
        "......ogho......",
        ".......oo.......",
    ]
    cmap = {"o": "od", "y": "ly", "Y": "candle", "L": "lo", "F": "fire", "W": "wm", "g": "wm", "h": "wd"}
    w = len(rows[0])
    im = new(w, len(rows))
    for yy, row in enumerate(rows):
        assert len(row) == w, (yy, row)
        for xx, ch in enumerate(row):
            if ch != ".":
                put(im, xx, yy, cmap[ch])
    return im


# ------------------------------------------------------------------ Sterne
def build_stars():
    a, b = stars()
    save(a, "Title_Sterne_A.png")
    save(b, "Title_Sterne_B.png")
    return a, b


def preview(bg, logo, a):
    prev = bg.copy()
    prev.alpha_composite(a)
    prev.alpha_composite(logo, (16, 14))
    scaled(prev, 3).save(os.path.join(OUT, "Title_Vorschau.png"))


if __name__ == "__main__":
    bg = build_background()
    logo = build_logo()
    a, b = build_stars()
    preview(bg, logo, a)
    print("OK", OUT, "Logo", logo.size)
