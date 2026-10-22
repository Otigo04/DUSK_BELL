"""VERALTET: dodge entsteht jetzt als Ausfallschritt in gen_hauptfiguren_combat.py (seq_dodge). Dieses Skript (Rolle) wird nicht mehr genutzt.

Hauptfiguren Mann/Frau: Ausweich-Rolle (dodge), 8 Richtungen x 6 Frames, 56x56.

Nutzt Frame 0 der Idle-Sheets (Reihenfolge der Zeilen: S, SW, W, NW, N, NE, E, SE) und dreht/staucht ihn:
Ostwaerts rollt die Figur im Uhrzeigersinn, westwaerts dagegen, nach Sueden/Norden ueberschlaegt sie sich senkrecht.
Dazu Staubwolke am Boden beim Absprung/Landen und Windstreifen. Nur Palettenfarben, keine Kantenglaettung.
Aufruf: python gen_dodge.py   -> ../<Frau|Mann>/<name>_dodge.png
"""
import math
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CELL = 56
DIRS = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
FRAMES = 6
DUST, DUST2 = (242, 234, 216, 255), (154, 149, 160, 255)
STREAK = (242, 234, 216, 255)
CENTER = (28, 34)          # Drehpunkt (Koerpermitte) in der Zelle
FEET_Y = 51                # Fuesse stehen bei y=50 (Pivot 5 px ueber dem Rand)

# je Frame: Winkel (Grad, 0..360 Vorwaerts-Rolle), Skalierung, Hub (px nach oben), Staub
STEPS = [
    dict(ang=0,   sy=0.86, sx=1.04, lift=0, dust=1),   # Ausholen: in die Hocke
    dict(ang=40,  sy=0.92, sx=0.92, lift=3, dust=2),   # Absprung
    dict(ang=130, sy=0.78, sx=0.78, lift=7, dust=0),   # zusammengerollt
    dict(ang=230, sy=0.78, sx=0.78, lift=7, dust=0),
    dict(ang=320, sy=0.90, sx=0.90, lift=3, dust=0),   # Aufrichten
    dict(ang=360, sy=0.86, sx=1.04, lift=0, dust=3),   # Landung in der Hocke
]


def cell(sheet, row, col):
    return sheet.crop((col * CELL, row * CELL, (col + 1) * CELL, (row + 1) * CELL))


def transform(src, ang, sx, sy, lift, vertical):
    """Dreht/staucht src um CENTER, Fuesse bleiben (ausser beim Hub) auf dem Boden."""
    w, h = max(1, round(CELL * sx)), max(1, round(CELL * sy))
    im = src.resize((w, h), Image.NEAREST)
    big = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    # Skaliertes Bild so setzen, dass die Fuesse am gleichen Boden bleiben
    x0 = (CELL - w) // 2
    y0 = FEET_Y - round(h * FEET_Y / CELL)
    big.alpha_composite(im, (x0, y0))
    if vertical:
        # Senkrechter Ueberschlag (S/N): Hoehe schrumpft, Mitte kippt kurz auf den Kopf
        t = ang / 360.0
        flip = 0.25 < t < 0.75
        if flip:
            big = big.transpose(Image.FLIP_TOP_BOTTOM)
            # Spiegelung um die Zellmitte; zurueck nach unten, damit der Koerper wieder im Bodenbereich liegt
            big = big.transform(big.size, Image.AFFINE, (1, 0, 0, 0, 1, -16), resample=Image.NEAREST)
    elif ang % 360:
        big = big.rotate(ang, resample=Image.NEAREST, center=CENTER)
    if lift:
        big = big.transform(big.size, Image.AFFINE, (1, 0, 0, 0, 1, lift), resample=Image.NEAREST)
    return big


def put(im, x, y, c):
    if 0 <= x < CELL and 0 <= y < CELL:
        im.putpixel((x, y), c)


def dust(im, n, d):
    """Staubwolke an den Fuessen. n = Phase 1 Absprung klein, 2 Absprung gross, 3 Landung."""
    fx, fy = 28, FEET_Y - 1
    puffs = {
        1: [(-5, 0), (5, 0), (-7, -1), (7, -1)],
        2: [(-8, 0), (8, 0), (-6, -2), (6, -2), (-10, -1), (10, -1)],
        3: [(-9, 0), (9, 0), (-6, -2), (6, -2), (-11, -1), (11, -1), (-3, -3), (3, -3)],
    }[n]
    for i, (dx, dy) in enumerate(puffs):
        c = DUST if i % 2 == 0 else DUST2
        put(im, fx + dx, fy + dy, c)
        put(im, fx + dx + (1 if dx > 0 else -1), fy + dy, c)
        if n >= 2 and i % 2 == 0:
            put(im, fx + dx, fy + dy - 1, c)


def streaks(im, d, strength):
    """Windstreifen hinter der Figur (gegen die Rollrichtung)."""
    vx = {"S": 0, "SW": -1, "W": -1, "NW": -1, "N": 0, "NE": 1, "E": 1, "SE": 1}[d]
    vy = {"S": 1, "SW": 1, "W": 0, "NW": -1, "N": -1, "NE": -1, "E": 0, "SE": 1}[d]
    for k in range(3):
        base_x = 28 - vx * (12 + k * 2)
        base_y = 33 - vy * (8 + k * 3) + (k - 1) * 4
        for j in range(strength + 2):
            put(im, base_x - vx * j, base_y - vy * j, STREAK)


def build(name):
    idle = Image.open(os.path.join(ROOT, name.capitalize(), f"{name}_idle.png")).convert("RGBA")
    sheet = Image.new("RGBA", (CELL * FRAMES, CELL * 8), (0, 0, 0, 0))
    for r, d in enumerate(DIRS):
        base = cell(idle, r, 0)
        vertical = d in ("S", "N")
        sign = -1 if d in ("E", "NE", "SE") else 1     # PIL dreht gegen den Uhrzeigersinn
        for f, st in enumerate(STEPS):
            ang = st["ang"]
            frame = transform(base, sign * ang if not vertical else ang, st["sx"], st["sy"], st["lift"], vertical)
            if 1 <= f <= 4:
                streaks(frame, d, 1 if f in (2, 3) else 0)
            if st["dust"]:
                dust(frame, st["dust"], d)
            sheet.alpha_composite(frame, (f * CELL, r * CELL))
    out = os.path.join(ROOT, name.capitalize(), f"{name}_dodge.png")
    sheet.save(out)
    return out, sheet


if __name__ == "__main__":
    raise SystemExit("gen_dodge.py ist veraltet: python gen_hauptfiguren_combat.py dodge nutzen (Ausfallschritt statt Rolle)")
    for n in ("frau", "mann"):
        path, sh = build(n)
        print("geschrieben:", path, sh.size)
