"""Baut alle Nightward-UI-Sprites (Icons, 9-Slice-Panel, Buttons, HUD) nach UI-Cheatsheet.
Aufruf: python build_ui.py   (vorher build_font.py)"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

from nwui import PAL, ALLOWED, rgb, new, put, rect, from_ascii, outline, scaled, used_colors

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
DIRS = {d: os.path.join(OUT, d) for d in ("Icons", "Panels", "Buttons", "HUD", "Font")}
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)


def save(im, sub, name):
    assert used_colors(im) <= ALLOWED, (name, used_colors(im) - ALLOWED)
    im.save(os.path.join(DIRS[sub], name))


# ------------------------------------------------------------------ Icons 16x16
def shape(fn, size=14):
    """fn(x, y) -> Farbname | None  auf 14x14, wird mit Kontur auf 16x16 gesetzt."""
    core = new(size, size)
    for y in range(size):
        for x in range(size):
            c = fn(x, y)
            if c:
                put(core, x, y, c)
    full = new(16, 16)
    full.paste(core, (1, 1))
    return outline(full)


def icon_talisman():
    rows = [
        "................",
        ".......oo.......",
        "......ohho......",
        ".....ohhmmo.....",
        "....ohhmmmmo....",
        "...ohhmmmmmdo...",
        "..ohhmmmmmmddo..",
        "..ohmmmmmmmddo..",
        "..ommmmmmmmddo..",
        "...ommmmmmddo...",
        "....ommmmddo....",
        ".....ommddo.....",
        "......omdo......",
        ".......oo.......",
        "................",
        "................",
    ]
    im = from_ascii(rows, {"o": "od", "h": "talh", "m": "tal", "d": "tald"})
    # kleiner Glanzpunkt + Facette
    put(im, 7, 4, "talh"); put(im, 8, 4, "talh"); put(im, 6, 6, "talh")
    put(im, 8, 7, "talh"); put(im, 8, 8, "tal")
    return im


def icon_aktion():
    def f(x, y):
        dx, dy = x - 6.5, y - 6.5
        if (abs(dx) / 6.6) ** 0.62 + (abs(dy) / 6.6) ** 0.62 > 1:
            return None
        if abs(dx) < 1.6 and abs(dy) < 1.6:
            return "candle"
        return "lo" if dx + dy > 2.2 else "ly"
    return shape(f)


def icon_tag():
    def f(x, y):
        dx, dy = x - 6.5, y - 6.5
        d = math.hypot(dx, dy)
        if d <= 4.3:
            if d <= 2.2 and dx < 1 and dy < 1:
                return "candle"
            return "lo" if dx + dy > 2.6 else "ly"
        rays = {(6, 0), (7, 0), (6, 1), (7, 1), (6, 12), (7, 12), (6, 13), (7, 13),
                (0, 6), (0, 7), (1, 6), (1, 7), (12, 6), (12, 7), (13, 6), (13, 7),
                (2, 2), (11, 2), (2, 11), (11, 11), (3, 3), (10, 3), (3, 10), (10, 10)}
        return "ly" if (x, y) in rays else None
    return shape(f)


def icon_nacht():
    def f(x, y):
        dx, dy = x - 6.5, y - 6.5
        if math.hypot(dx, dy) <= 6.3 and math.hypot(x - 9.6, y - 4.4) > 5.2:
            return "s3" if (x - y) < -2 else "moon"
        star = {(11, 2), (10, 3), (11, 3), (12, 3), (11, 4)}
        return "moon" if (x, y) in star else None
    return shape(f)


def icon_vertrauen():
    def f(x, y):
        a, b = (x - 6.5) / 6.3, (6.6 - y) / 6.0
        if (a * a + b * b - 1) ** 3 - a * a * b ** 3 > 0:
            return None
        if (x, y) in {(3, 3), (4, 3), (3, 4), (4, 2)}:
            return "candle"
        return "rd" if (x + y) > 14 else "pink"
    return shape(f)


def icon_warnung():
    def f(x, y):
        if y > 12:
            return None
        hw = (y + 0.6) / 13.0 * 6.2
        if abs(x - 6.5) > hw:
            return None
        if x in (6, 7) and 4 <= y <= 8:
            return "candle"
        if x in (6, 7) and 10 <= y <= 11:
            return "candle"
        return "blood" if x - 6.5 > hw - 2.0 else "eye"
    return shape(f)


def icon_wald():
    tiers = [0.5, 1.5, 2.5, 3.5, 1.5, 2.5, 3.5, 4.5, 2.5, 3.5, 4.5, 5.5]

    def f(x, y):
        if y < 12:
            hw = tiers[y]
            if abs(x - 6.5) > hw:
                return None
            if x - 6.5 >= hw - 1.0:
                return "fm"
            if x - 6.5 <= -hw + 0.0 and hw > 1:
                return "gh"
            return "g" if x < 7 else "fm"
        if x in (6, 7):
            return "wm" if x == 6 else "wd"
        return None
    return shape(f)


def icon_versteck():
    def f(x, y):
        if y > 13:
            return None
        a, b = (x - 6.5) / 6.6, (y - 13.0) / 12.6
        if a * a + b * b > 1:
            return None
        ha, hb = (x - 6.5) / 3.1, (y - 13.0) / 6.6
        if ha * ha + hb * hb <= 1:
            if (x, y) in {(5, 9), (8, 9)}:
                return "eye"
            return "od"
        d = math.hypot(x - 4.0, y - 4.0)
        if a * a + b * b > 0.80 and x < 6:
            return "sv3"
        return "sv1" if x > 8 else "sv2"
    return shape(f)


def icon_vorraete():
    def f(x, y):
        if y <= 2:
            return ("wd" if y == 2 else "wh") if abs(x - 6.5) <= 1.6 else (("wd") if y == 2 and abs(x - 6.5) <= 2.6 else None)
        if y == 3:
            return "wd" if abs(x - 6.5) <= 2.6 else None
        t = (y - 3) / 10.0
        hw = 2.6 + 3.9 * math.sin(min(1.0, t * 1.05 + 0.18) * math.pi * 0.55)
        if abs(x - 6.5) > hw:
            return None
        if x - 6.5 >= hw - 1.4 or y >= 12:
            return "wm"
        if x - 6.5 <= -hw + 1.6 and y < 11:
            return "straw"
        return "wh"
    return shape(f)


def icon_wissen():
    def f(x, y):
        if 2 <= x <= 11 and 1 <= y <= 11:
            if x <= 3:
                return "bl"
            if (x, y) in {(6, 5), (7, 5), (6, 6), (7, 6)}:
                return "ly"
            if (x, y) == (6, 5):
                return "candle"
            if x == 10 and y >= 8:
                return "pink"
            if y == 1 or x == 4:
                return "candle" if y == 1 and x > 4 else "blh"
            return "blh"
        if 3 <= x <= 12 and 12 <= y <= 13:
            return "s3" if y == 13 else "teeth"
        if x == 12 and 3 <= y <= 11:
            return "teeth"
        return None
    return shape(f)


def _sunrise(sun, sun_dark, ray, hill, hill_hi, cy):
    def f(x, y):
        hy = int(cy + 1.2)          # erste Hügelzeile
        if y >= hy:
            if y == hy:
                return hill_hi if 1 <= x <= 12 else None
            return hill if (x >= 1 or y > hy + 1) else None
        dx, dy = x - 6.5, y - cy
        if math.hypot(dx, dy) <= 4.3 and y <= cy + 0.5:
            if (x, y) in {(5, int(cy) - 1), (4, int(cy)), (5, int(cy))}:
                return "candle"
            return sun_dark if dx + dy > 2.6 else sun
        rays = {(6, 1), (7, 1), (6, 2), (7, 2), (2, 3), (3, 4), (11, 3), (10, 4), (0, int(cy) - 1), (1, int(cy) - 1),
                (12, int(cy) - 1), (13, int(cy) - 1)}
        return ray if (x, y) in rays else None
    return shape(f)


def icon_morgen():
    return _sunrise("ly", "lo", "ly", "g", "gh", 9.0)


def icon_abend():
    return _sunrise("lo", "fire", "lo", "sv2", "sv3", 10.0)


ICONS = [
    ("Talisman", icon_talisman), ("Aktion", icon_aktion), ("Wissen", icon_wissen), ("Vertrauen", icon_vertrauen),
    ("Nacht", icon_nacht), ("Tag", icon_tag), ("Warnung", icon_warnung), ("Wald", icon_wald),
    ("Versteck", icon_versteck), ("Vorraete", icon_vorraete), ("Morgen", icon_morgen), ("Abend", icon_abend),
]


def disabled(im):
    out = new(im.width, im.height)
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] == 0:
                continue
            if p[:3] == rgb("od")[:3]:
                put(out, x, y, "od")
            else:
                lum = 0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]
                put(out, x, y, "s2" if lum > 150 else "s1")
    return out


icon_imgs = {}
for name, fn in ICONS:
    im = fn()
    icon_imgs[name] = im
    save(im, "Icons", f"Icon_{name}.png")
    save(disabled(im), "Icons", f"Icon_{name}_Aus.png")

sheet = new(16 * len(ICONS), 32)
for i, (name, _) in enumerate(ICONS):
    sheet.paste(icon_imgs[name], (i * 16, 0))
    sheet.paste(disabled(icon_imgs[name]), (i * 16, 16))
save(sheet, "Icons", "Icons_Sheet.png")


# ------------------------------------------------------------------ 9-Slice-Rahmen
def frame(w, h, bg, bg_alpha, fr, hi=None, stud=None):
    """Rahmen mit 1px Kante, angeschnittenen Ecken, Licht oben links. Ecken 8x8 -> bei w,h >= 17 echte 9-Slice-Mitte."""
    im = new(w, h)
    rect(im, 1, 1, w - 2, h - 2, bg, bg_alpha)
    for x in range(1, w - 1):
        put(im, x, 0, fr); put(im, x, h - 1, fr)
    for y in range(1, h - 1):
        put(im, 0, y, fr); put(im, w - 1, y, fr)
    for (cx, cy) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        put(im, cx, cy, fr)
    if hi:
        for x in range(2, w - 2):
            put(im, x, 1, hi)
        for y in range(2, h - 2):
            put(im, 1, y, hi)
        put(im, 1, 1, hi)
    if stud:
        for (sx, sy, dx, dy) in ((3, 3, 1, 1), (w - 4, 3, -1, 1), (3, h - 4, 1, -1), (w - 4, h - 4, -1, -1)):
            put(im, sx, sy, stud)
            put(im, sx + dx, sy, stud)
            put(im, sx, sy + dy, stud)
    return im


panel = frame(24, 24, "od", 217, "sv2", "sv3", "sv3")   # 85 % Deckkraft
save(panel, "Panels", "Panel_Dialog.png")
# Lagebericht nutzt denselben Rahmen
save(panel.copy(), "Panels", "Panel_Lagebericht.png")

BTN = {
    "Normal": ("nb2", "sv2", "sv3"),
    "Hover": ("nb3", "ly", "candle"),
    "Pressed": ("nb1", "od", None),
    "Disabled": ("on", "on", None),
}
for st, (bg, fr, hi) in BTN.items():
    save(frame(24, 16, bg, 255, fr, hi), "Buttons", f"Button_{st}.png")


# ------------------------------------------------------------------ HUD
def dot(fill):
    core = new(5, 5)
    for y in range(5):
        for x in range(5):
            if math.hypot(x - 2, y - 2) <= 2.3:
                put(core, x, y, fill)
    full = new(7, 7)
    full.paste(core, (1, 1))
    out = outline(full)
    return out


save(dot("ly"), "HUD", "HUD_Aktion_Voll.png")
save(dot("on"), "HUD", "HUD_Aktion_Leer.png")


def bar(fill):
    full = new(6, 12)
    rect(full, 1, 1, 4, 10, fill)
    return outline(full)


for nm, col in (("Leer", "on"), ("Gelb", "ly"), ("Orange", "lo"), ("Rot", "eye")):
    save(bar(col), "HUD", f"HUD_Weckbalken_{nm}.png")

arrow = new(9, 6)
for r, w in enumerate((7, 5, 3, 1)):
    rect(arrow, 1 + (7 - w) // 2, 1 + r, 1 + (7 - w) // 2 + w - 1, 1 + r, "lo")
save(outline(arrow), "HUD", "HUD_Pfeil_Weiter.png")


# Lebensbalken: Rahmen 76x12, Fuellung 70x6 (10 Segmente a 7 px), Teiler-Overlay
def life_frame():
    im = new(76, 12)
    rect(im, 0, 0, 75, 11, "od")
    rect(im, 1, 1, 74, 10, "sv2")
    rect(im, 2, 2, 73, 9, "on")
    put(im, 0, 0, "od", 0); put(im, 75, 0, "od", 0); put(im, 0, 11, "od", 0); put(im, 75, 11, "od", 0)
    return im


def life_fill(main, shade, light):
    im = new(70, 6)
    rect(im, 0, 0, 69, 5, main)
    rect(im, 0, 0, 69, 0, light)
    rect(im, 0, 4, 69, 5, shade)
    return im


def life_ticks():
    im = new(70, 6)
    for k in range(1, 10):
        rect(im, k * 7 - 1, 0, k * 7 - 1, 5, "on")
    return im


save(life_frame(), "HUD", "HUD_Leben_Rahmen.png")
save(life_fill("pink", "rd", "candle"), "HUD", "HUD_Leben_Fuellung.png")
save(life_fill("eye", "blood", "candle"), "HUD", "HUD_Leben_Kritisch.png")
save(life_ticks(), "HUD", "HUD_Leben_Teiler.png")


# ------------------------------------------------------------------ Vorschau (zeigt Font + 9-Slice + Farbregeln)
def nine(src, border, w, h):
    l, t, r, b = border
    out = new(w, h)
    sw, sh = src.size
    parts = {
        "tl": (0, 0, l, t, 0, 0, l, t), "tr": (sw - r, 0, sw, t, w - r, 0, w, t),
        "bl": (0, sh - b, l, sh, 0, h - b, l, h), "br": (sw - r, sh - b, sw, sh, w - r, h - b, w, h),
        "t": (l, 0, sw - r, t, l, 0, w - r, t), "b": (l, sh - b, sw - r, sh, l, h - b, w - r, h),
        "l": (0, t, l, sh - b, 0, t, l, h - b), "r": (sw - r, t, sw, sh - b, w - r, t, w, h - b),
        "c": (l, t, sw - r, sh - b, l, t, w - r, h - b),
    }
    for _, (x0, y0, x1, y1, dx0, dy0, dx1, dy1) in parts.items():
        if x1 <= x0 or y1 <= y0 or dx1 <= dx0 or dy1 <= dy0:
            continue
        piece = src.crop((x0, y0, x1, y1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
        out.alpha_composite(piece, (dx0, dy0))
    return out


FONT_PATH = os.path.join(DIRS["Font"], "Nightward_Pixel.ttf")


def text(im, x, y, s, color, size=8, shadow=True):
    f = ImageFont.truetype(FONT_PATH, size)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    if shadow:
        d.text((x + 1, y + 1), s, font=f, fill=rgb("od"))
    d.text((x, y), s, font=f, fill=rgb(color))


def text_w(s, size=8):
    return len(s) * 6 * (size // 8)


W, H = 336, 304
canvas = Image.new("RGBA", (W, H), rgb("nb1"))
cv = canvas
# HUD
text(cv, 4, 3, "HUD", "s3", 8, False)
for i in range(4):
    cv.alpha_composite(Image.open(os.path.join(DIRS["HUD"], "HUD_Aktion_Voll.png" if i < 3 else "HUD_Aktion_Leer.png")), (24 + i * 9, 3))
cv.alpha_composite(icon_imgs["Talisman"], (66, 0)); text(cv, 84, 4, "5/6", "tal")
cv.alpha_composite(icon_imgs["Vertrauen"], (112, 0)); text(cv, 130, 4, "7", "pink")
cv.alpha_composite(icon_imgs["Wissen"], (146, 0)); text(cv, 164, 4, "3", "blh")
cv.alpha_composite(icon_imgs["Nacht"], (186, 0)); cv.alpha_composite(icon_imgs["Tag"], (204, 0))
for i, nm in enumerate(("Gelb", "Gelb", "Orange", "Rot", "Leer")):
    cv.alpha_composite(Image.open(os.path.join(DIRS["HUD"], f"HUD_Weckbalken_{nm}.png")), (236 + i * 7, 2))
text(cv, 276, 4, "0/6", "blood")

# Dialogbox Bewohner
cv.alpha_composite(nine(panel, (8, 8, 8, 8), 200, 52), (8, 24))
text(cv, 18, 31, "Ilhan", "ly", 8)
text(cv, 18, 42, "Heute Nacht schließen wir die", "candle", 8)
text(cv, 18, 53, "Fensterläden früher, Fremder.", "candle", 8)
cv.alpha_composite(Image.open(os.path.join(DIRS["HUD"], "HUD_Pfeil_Weiter.png")), (192, 64))
# Erzaehler 16 px
cv.alpha_composite(nine(panel, (8, 8, 8, 8), 112, 52), (216, 24))
text(cv, 224, 31, "Der Wind riecht", "leaf", 8)
text(cv, 224, 42, "nach Regen.", "leaf", 8)

# Dialog 16 px
cv.alpha_composite(nine(panel, (8, 8, 8, 8), 320, 50), (8, 84))
text(cv, 18, 90, "Übung: Äpfel & Öl", "ly", 16)
text(cv, 18, 108, "Ärzte, Ölkrüge, Straße?", "candle", 8)

# Buttons
for i, st in enumerate(("Normal", "Hover", "Pressed", "Disabled")):
    img = Image.open(os.path.join(DIRS["Buttons"], f"Button_{st}.png"))
    b = nine(img, (8, 7, 8, 7), 72, 20)
    cv.alpha_composite(b, (8 + i * 80, 162))
    col = {"Normal": "candle", "Hover": "ly", "Pressed": "s3", "Disabled": "s2"}[st]
    lab = {"Normal": "Weiter", "Hover": "Weiter", "Pressed": "Weiter", "Disabled": "Weiter"}[st]
    tw = text_w(lab)
    text(cv, 8 + i * 80 + (72 - tw) // 2, 168, lab, col, 8, st != "Disabled")

# Lagebericht
cv.alpha_composite(nine(panel, (8, 8, 8, 8), 320, 66), (8, 190))
text(cv, 18, 196, "Morgen in Nightward", "ly", 16)
text(cv, 270, 198, "Tag 3", "candle", 8)
cv.alpha_composite(icon_imgs["Warnung"], (18, 215)); text(cv, 38, 219, "Mara", "eye")
cv.alpha_composite(icon_imgs["Versteck"], (18, 231)); text(cv, 38, 235, "Das Versteck regt sich.", "lo")
cv.alpha_composite(icon_imgs["Talisman"], (190, 215)); text(cv, 208, 219, "+1 Talisman", "tal")
cv.alpha_composite(nine(Image.open(os.path.join(DIRS["Buttons"], "Button_Normal.png")), (8, 7, 8, 7), 48, 16), (276, 232))
text(cv, 276 + (48 - text_w("Weiter")) // 2, 236, "Weiter", "candle")

# Icon-Streifen
for i, (nm, _) in enumerate(ICONS):
    cv.alpha_composite(icon_imgs[nm], (8 + i * 20, 138))
    cv.alpha_composite(disabled(icon_imgs[nm]), (212 + i * 11 if False else 8 + i * 20, 138)) if False else None


# Zeit + Leben
x = 8
for nm, hh, col in (("Morgen", "07:30", "ly"), ("Tag", "12:00", "ly"), ("Abend", "19:45", "lo"), ("Nacht", "23:10", "moon")):
    cv.alpha_composite(icon_imgs[nm], (x, 272))
    text(cv, x + 18, 276, hh, "candle", 16)
    text(cv, x + 18, 292, nm, col, 8)
    x += 82
fr = Image.open(os.path.join(DIRS["HUD"], "HUD_Leben_Rahmen.png"))
for k, (fn, frac) in enumerate((("HUD_Leben_Fuellung.png", 0.7), ("HUD_Leben_Kritisch.png", 0.2))):
    base = (336 - 90, 270 + k * 16)
    cv.alpha_composite(fr, base)
    fi = Image.open(os.path.join(DIRS["HUD"], fn)).crop((0, 0, int(70 * frac), 6))
    cv.alpha_composite(fi, (base[0] + 3, base[1] + 3))
    cv.alpha_composite(Image.open(os.path.join(DIRS["HUD"], "HUD_Leben_Teiler.png")), (base[0] + 3, base[1] + 3))

big = scaled(canvas, 3)
big.save(os.path.join(OUT, "UI_Vorschau.png"))
print("UI fertig:", OUT)
