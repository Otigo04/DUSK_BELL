"""HUD-Paket (Neu): negative Stimmungs-Symbole, Banner-Emblem, Titelband, Sterne."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
from hud2_lib import *


def icon_traurig():
    """Trauriges Gesicht in Nachtblau mit Träne (Stimmung gesunken)."""
    def f(im):
        for y in range(14):
            for x in range(14):
                dx, dy = x - 6.5, y - 6.5
                if math.hypot(dx, dy) <= 6.6:
                    put(im, x, y, "bl" if dx + dy > 4.2 else "blh")
        put(im, 3, 3, "moon"); put(im, 4, 3, "moon"); put(im, 3, 4, "moon")
        for (x, y) in ((4, 5), (4, 6), (9, 5), (9, 6)):
            put(im, x, y, "od")
        for (x, y) in ((3, 10), (4, 9), (5, 8), (6, 8), (7, 8), (8, 8), (9, 9), (10, 10)):
            put(im, x, y, "od")
        put(im, 4, 7, "moon"); put(im, 4, 8, "moon")                    # Traene
    return icon_from(14, 14, f, 16)


def icon_einsam():
    """Eine einzelne Sprechblase, die zweite ist ausgegraut und leer."""
    def f(im):
        rect(im, 5, 7, 13, 12, "s1")
        for (x, y) in ((5, 7), (13, 7), (5, 12), (13, 12)):
            put(im, x, y, "s1", 0)
        put(im, 11, 13, "s1"); put(im, 12, 13, "s1")
        rect(im, 0, 1, 8, 6, "candle")
        for (x, y) in ((0, 1), (8, 1), (0, 6), (8, 6)):
            put(im, x, y, "candle", 0)
        rect(im, 1, 6, 8, 6, "s3")
        put(im, 2, 7, "candle"); put(im, 2, 8, "s3"); put(im, 3, 7, "s3")
        for x in (2, 4, 6):
            put(im, x, 3, "s2")
    return icon_from(14, 14, f, 16)


def icon_stress():
    """Spitzer Stern mit Ausrufezeichen: Anspannung."""
    def f(im):
        pts = []
        for i in range(16):
            ang = math.pi * 2 * i / 16 - math.pi / 2
            r = 6.8 if i % 2 == 0 else 4.4
            pts.append((6.5 + r * math.cos(ang), 6.5 + r * math.sin(ang)))
        poly(im, pts, "lo")
        for y in range(14):
            for x in range(14):
                if im.getpixel((x, y))[3] and (x - 6.5) + (y - 6.5) < -2.0:
                    put(im, x, y, "ly")
        for (x, y) in ((6, 3), (7, 3), (6, 4), (7, 4), (6, 5), (7, 5), (6, 6), (7, 6), (6, 8), (7, 8), (6, 9), (7, 9)):
            put(im, x, y, "od")
    return icon_from(14, 14, f, 16)


def star(n):
    im = new(n, n)
    c = n // 2
    for i in range(n):
        put(im, c, i, "ly")
        put(im, i, c, "ly")
    put(im, c, c, "candle")
    if n >= 7:
        for (x, y) in ((c - 1, c), (c + 1, c), (c, c - 1), (c, c + 1)):
            put(im, x, y, "candle")
    return im


# ---------------------------------------------------------------- Tages-Banner
BAYER = ((0, 2), (3, 1))


def _grad(stops, y, h):
    """Farbe an Zeile y: Dither (Bayer 2x2) zwischen zwei benachbarten Farbstufen. stops = [(anteil, farbe), ...]."""
    t = y / float(h - 1)
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t0 <= t <= t1:
            return c0, c1, (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    return stops[-1][1], stops[-1][1], 0.0


def band(kind):
    """8 px breite Kachel, wird waagerecht gestreckt. Farbverlauf per Dither, obere/untere Kante blendet per Dither aus."""
    H = 116
    W = 8
    im = new(W, H)
    if kind == "morgen":
        stops = [(0.0, "od"), (0.35, "on"), (0.62, "sv1"), (0.82, "rd"), (1.0, "sv2")]
    else:
        stops = [(0.0, "od"), (0.4, "nb1"), (0.72, "nb2"), (1.0, "nb1")]
    for y in range(H):
        c0, c1, f = _grad(stops, y, H)
        d = min(y, H - 1 - y)
        for x in range(W):
            if d < 5:
                dens = (0, 1, 2, 3, 3)[d] / 4.0 if d else 0.0
                if d >= 4:
                    dens = 1.0
                if d == 4:
                    dens = 1.0
                thr = (BAYER[y % 2][x % 2] + 0.5) / 4.0
                if dens < 1.0 and thr > dens:
                    continue
            thr = (BAYER[y % 2][x % 2] + 0.5) / 4.0
            put(im, x, y, c1 if f > thr else c0, 255)
    # feine Zierlinien
    for x in range(W):
        put(im, x, 9, "sv2")
        put(im, x, H - 10, "sv2")
    return im


def rays():
    """Sonnenstrahlen als flache, halbtransparente Keile (Faecher nach oben)."""
    W, H = 240, 110
    im = new(W, H)
    d = ImageDraw.Draw(im)
    cx, cy = 120, 108
    for i in range(15):
        ang = math.pi * (0.06 + 0.88 * i / 14.0)
        half = 0.028 if i % 2 == 0 else 0.016
        r = 118
        pts = [(cx, cy),
               (cx - r * math.cos(ang - half), cy - r * math.sin(ang - half)),
               (cx - r * math.cos(ang + half), cy - r * math.sin(ang + half))]
        c = rgb("ly") if i % 2 == 0 else rgb("lo")
        d.polygon(pts, fill=(c[0], c[1], c[2], 70 if i % 2 == 0 else 46))
    return im


def skyline(kind):
    """Dorf-Silhouette mit Glockenturm; dahinter Sonne (Morgen) oder Mond (Mitternacht). 200x60."""
    import random
    rnd = random.Random(7 if kind == "morgen" else 11)
    W, H = 200, 60
    im = new(W, H)
    cx, cy = 100, 40
    if kind == "morgen":
        for y in range(H):
            for x in range(W):
                dd = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if dd <= 21:
                    put(im, x, y, "lo" if dd > 17 else ("ly" if dd > 8 else "candle"))
                elif dd <= 24 and (x + y) % 2 == 0:
                    put(im, x, y, "lo")
    else:
        for y in range(H):
            for x in range(W):
                d1 = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                d2 = math.hypot(x + 0.5 - (cx + 8), y + 0.5 - (cy - 5))
                if d1 <= 18 and d2 > 15:
                    put(im, x, y, "moon" if (x - cx) + (y - cy) < 6 else "s3")
                elif d1 <= 22 and (x + y) % 2 == 0 and d2 > 18:
                    put(im, x, y, "nb3")

    def house(x, w, wall, roof, col, lit):
        base = 54
        rect(im, x, base - wall, x + w - 1, base, col)
        poly(im, [(x - 2, base - wall), (x + w // 2, base - wall - roof), (x + w + 1, base - wall)], col)
        if w >= 12:
            put(im, x + w - 4, base - wall - roof // 2 - 2, "sv1")          # Schornstein
            rect(im, x + w - 5, base - wall - roof // 2 - 5, x + w - 4, base - wall - roof // 2 - 2, col)
        for wx in range(x + 3, x + w - 3, 5):
            if rnd.random() < lit:
                rect(im, wx, base - wall + 3, wx + 1, base - wall + 5, "ly")

    lit = 0.6 if kind == "morgen" else 0.22
    for (x, w, wall, roof) in ((14, 22, 11, 9), (46, 18, 13, 8), (126, 20, 12, 9), (150, 22, 11, 10)):
        house(x, w, wall, roof, "sv1", lit)
    for (x, w, wall, roof) in ((0, 16, 12, 9), (30, 20, 16, 11), (62, 22, 14, 10), (128, 24, 15, 12), (160, 20, 13, 10), (184, 16, 11, 8)):
        house(x, w, wall, roof, "on", lit)
    # Glockenturm
    rect(im, 92, 22, 107, 54, "on")
    poly(im, [(90, 22), (100, 2), (110, 22)], "on")
    rect(im, 96, 27, 103, 37, "od")
    rect(im, 98, 29, 101, 34, "ly")
    put(im, 99, 35, "lo"); put(im, 100, 35, "lo")
    rect(im, 91, 39, 108, 39, "sv1")
    for wy in (43, 49):
        rect(im, 98, wy, 101, wy + 2, "ly" if kind == "morgen" else "sv2")
    put(im, 100, 1, "ly")
    # Tannen an den Raendern
    for (tx, th) in ((4, 24), (22, 17), (176, 18), (194, 25)):
        for r in range(th):
            half = 1 + r // 3
            for x in range(tx - half, tx + half + 1):
                if 0 <= x < W:
                    put(im, x, 54 - th + r + 1, "fd")
    # Boden
    for x in range(W):
        top = 53 + (1 if (x // 6) % 2 else 0)
        for y in range(top, H):
            put(im, x, y, "fm" if y == top else "fd")
    # Randlicht oben auf den Silhouetten
    rim = "rd" if kind == "morgen" else "sv2"
    src = im.copy()
    for y in range(1, H):
        for x in range(W):
            p = src.getpixel((x, y))
            if p[3] and p[:3] in (rgb("on")[:3], rgb("sv1")[:3]) and src.getpixel((x, y - 1))[3] == 0:
                put(im, x, y, rim)
    return im


def ribbon(h=34):
    """Rotes Titelband mit Schwalbenschwanz-Enden. 9-Slice: links/rechts je 14 px bleiben, die Mitte streckt."""
    W = 56
    H = h
    im = new(W, H)
    body_h = H - 8
    for side in (0, 1):
        x0 = 0 if side == 0 else W - 14
        for y in range(6, H - 1):
            dist = abs(y - (6 + (H - 7) / 2.0))
            lim = 7 - dist * 0.55
            for x in range(x0, x0 + 14):
                rel = x - x0 if side == 0 else (x0 + 13) - x
                if rel < lim:
                    continue
                put(im, x, y, "blood")
        for x in range(x0 + 2, x0 + 14):
            put(im, x, H - 2, "od") if (side == 0 and x - x0 >= 3) or (side == 1 and (x0 + 13) - x >= 3) else None
    rect(im, 10, 1, W - 11, body_h, "rd")
    rect(im, 10, 1, W - 11, 3, "pink")
    rect(im, 10, body_h - 1, W - 11, body_h, "blood")
    for y in range(1, body_h + 1):
        put(im, 10, y, "blood")
        put(im, W - 11, y, "blood")
    # goldene Zierlinie
    rect(im, 11, 5, W - 12, 5, "ly")
    rect(im, 11, body_h - 3, W - 12, body_h - 3, "ly")
    return outline(im)


def line_ornament():
    """Auslaufende Zierlinie mit Raute am rechten Ende (links gespiegelt benutzen). 96x11."""
    im = new(96, 11)
    for x in range(0, 84):
        c = "sv1" if x < 30 else ("sv2" if x < 60 else "sv3")
        if x % 2 == 0 or x > 60:
            put(im, x, 5, c)
    poly(im, [(88, 2), (92, 5), (88, 8), (84, 5)], "ly")
    put(im, 88, 5, "candle")
    put(im, 94, 5, "ly")
    return im
