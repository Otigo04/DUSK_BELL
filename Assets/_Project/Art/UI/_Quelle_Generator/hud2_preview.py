"""Vorschau-Bilder fuer das HUD-Paket (Neu): Spiel-Mock mit HUD, Tages-Banner mit Ereignisliste, Bauteil-Uebersicht.
Wird von build_hud_neu.py am Ende importiert (liest die gespeicherten PNGs)."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
from hud2_lib import *
from hud2_lib import MANIFEST

CW, CH = 480, 270      # Spielkamera / Canvas wie UI_Test


def P(group, name):
    return Image.open(os.path.join(OUT, group, name + ".png")).convert("RGBA")


def OLD(group, name):
    return Image.open(os.path.join(UI, group, name + ".png")).convert("RGBA")


def backdrop(night=0.0):
    """Schlichter Platzhalter fuer die Spielszene: Gras, Weg, zwei Haeuser, dunkler je nach night (0..1)."""
    im = Image.new("RGBA", (CW, CH), rgb("fm"))
    d = ImageDraw.Draw(im)
    for y in range(0, CH, 8):
        for x in range(0, CW, 8):
            if (x // 8 + y // 8) % 3 == 0:
                d.rectangle([x, y, x + 7, y + 7], fill=rgb("g"))
            if (x * 7 + y * 3) % 29 == 0:
                d.rectangle([x + 2, y + 3, x + 3, y + 4], fill=rgb("gh"))
    d.rectangle([0, 150, CW, 178], fill=rgb("wh"))
    d.rectangle([0, 154, CW, 174], fill=rgb("straw"))
    for (hx, hy) in ((60, 96), (300, 88)):
        d.rectangle([hx, hy, hx + 90, hy + 56], fill=rgb("wm"))
        d.polygon([(hx - 6, hy), (hx + 45, hy - 34), (hx + 96, hy)], fill=rgb("rd"))
        d.rectangle([hx + 16, hy + 14, hx + 34, hy + 32], fill=rgb("ly"))
        d.rectangle([hx + 56, hy + 24, hx + 76, hy + 56], fill=rgb("wd"))
    if night:
        ov = Image.new("RGBA", (CW, CH), rgb("od"))
        ov.putalpha(int(255 * night))
        im.alpha_composite(ov)
    return im


def player(im, x, y):
    fp = os.path.join(UI, "..", "Art", "Characters", "Hauptfiguren", "Frau", "frau_idle.png")
    fp = os.path.abspath(os.path.join(UI, "..", "Characters", "Hauptfiguren", "Frau", "frau_idle.png"))
    if os.path.exists(fp):
        sh = Image.open(fp).convert("RGBA")
        im.alpha_composite(sh.crop((0, 0, 56, 56)), (x - 28, y - 50))


def bar(cv, x, y, icon, fills, frac, lock=0.0, ticks=None, mark=False, trail=None):
    cv.alpha_composite(P("Vitals", "Icon_" + icon), (x, y - 1))
    cv.alpha_composite(P("Vitals", "Balken_Rahmen"), (x + 14, y))
    ix = x + 14 + 2
    if lock:
        lw = int(60 * lock)
        cv.alpha_composite(P("Vitals", "Schraffur_Gesperrt").crop((60 - lw, 0, 60, 5)), (ix + 60 - lw, y + 2))
    if trail:
        cv.alpha_composite(P("Vitals", "Verlust_Spur").crop((0, 0, int(60 * trail), 5)), (ix, y + 2))
    w = int(60 * frac)
    cv.alpha_composite(P("Vitals", fills).crop((0, 0, w, 5)), (ix, y + 2))
    if ticks:
        cv.alpha_composite(P("Vitals", ticks).crop((0, 0, 60, 5)), (ix, y + 2))
    if mark:
        cv.alpha_composite(P("Vitals", "Marke_Schlafsperre"), (ix, y + 2))


def hud_mock():
    cv = backdrop(0.18)
    player(cv, 238, 215)

    # ---- Uhr (oben links)
    cv.alpha_composite(nine(P("Plates", "Plate_HUD"), (3, 3, 3, 3), 68, 30), (6, 6))
    cv.alpha_composite(OLD("Icons", "Icon_Tag"), (11, 13))
    text(cv, 32, 11, "12:45", "candle", 8)
    text(cv, 32, 21, "Day 2", "ly", 8)
    tx, ty = 7, 39
    cv.alpha_composite(P("Clock", "Spur_Rahmen"), (tx + 5, ty + 5))
    cv.alpha_composite(P("Clock", "Spur_Segmente"), (tx + 6, ty + 6))
    now = 12.75
    px = int(now * 2)
    cv.alpha_composite(P("Clock", "Spur_Vergangen").crop((0, 0, px, 3)), (tx + 6, ty + 6))
    cv.alpha_composite(P("Clock", "Spur_Marke"), (tx + 6 + px - 2, ty + 0))
    cv.alpha_composite(P("Clock", "Spur_Glocke"), (tx + 6 + 36 - 4, ty + 12))

    # ---- Vitalbalken (unter der Uhr)
    bar(cv, 8, 66, "Herz", "Fuellung_Leben", 0.67, ticks="Teiler_3")
    bar(cv, 8, 80, "Ausdauer", "Fuellung_Ausdauer", 0.62, lock=0.2)
    bar(cv, 8, 94, "Geist", "Fuellung_Geist", 0.58, mark=True)

    # ---- Quest-Tracker (oben rechts), Hauptquest offen, Nebenquests eingeklappt
    qw = 152
    px0 = CW - 6 - qw
    cv.alpha_composite(nine(P("Plates", "Plate_HUD"), (3, 3, 3, 3), qw, 76), (px0, 6))
    cv.alpha_composite(nine(P("Plates", "Plate_Header_Haupt"), (4, 3, 3, 3), qw - 6, 13), (px0 + 3, 9))
    cv.alpha_composite(P("Quest", "Symbol_Haupt"), (px0 + 9, 8))
    text(cv, px0 + 24, 12, "Main Quest", "ly", 8)
    cv.alpha_composite(P("Quest", "Pfeil_Auf"), (px0 + qw - 16, 12))
    cv.alpha_composite(P("Quest", "Marke_Verfolgt"), (px0 + 6, 30))
    cv.alpha_composite(P("Quest", "Punkt_Aktiv"), (px0 + 12, 29))
    text(cv, px0 + 24, 28, "Investigate the log", "candle", 8)
    cv.alpha_composite(P("Quest", "Fortschritt_Rahmen"), (px0 + 24, 40))
    cv.alpha_composite(P("Quest", "Fortschritt_Fuellung").crop((0, 0, 22, 3)), (px0 + 25, 41))
    cv.alpha_composite(P("Quest", "Punkt_Fertig"), (px0 + 12, 50))
    text(cv, px0 + 24, 49, "Find the car", "s3", 8)
    cv.alpha_composite(nine(P("Plates", "Plate_Header_Neben"), (4, 3, 3, 3), qw - 6, 13), (px0 + 3, 62))
    cv.alpha_composite(P("Quest", "Symbol_Neben"), (px0 + 9, 61))
    text(cv, px0 + 24, 65, "Side Quests", "blh", 8)
    cv.alpha_composite(P("Quest", "Abzeichen_Zahl"), (px0 + qw - 36, 64))
    text(cv, px0 + qw - 32, 66, "2", "candle", 8, False)
    cv.alpha_composite(P("Quest", "Pfeil_Zu"), (px0 + qw - 16, 65))

    # ---- Beduerfnisse und Stimmung (rechte untere Haelfte), oberster aufgeklappt
    tx0, ty0 = CW - 6 - 22, 132
    items = [("Hunger", 3, "neg"), ("Durst", 1, "neg"), ("Gesellschaft", 1, "pos"), ("Muede", 2, "neg"), ("Anspannung", 2, "neg")]
    for i, (need, st, kind) in enumerate(items):
        y = ty0 + i * 25
        nm = f"Anzeige_{need}_Stufe_{st}" if kind == "neg" else f"Anzeige_{need}_Positiv_{st}"
        cv.alpha_composite(P("Needs", nm), (tx0, y))
    # Flyout fuer Hunger (Stufe 3) links neben der Kachel
    label = "I'm really hungry."
    fw = text_w(label) + 12
    fx = tx0 - 6 - fw
    cv.alpha_composite(nine(P("Plates", "Plate_Flyout"), (3, 3, 3, 3), fw, 17), (fx, ty0 + 3))
    text(cv, fx + 6, ty0 + 7, label, "lo", 8)
    cv.alpha_composite(P("Plates", "Plate_Flyout_Zeiger"), (fx + fw - 1, ty0 + 7))
    # zweite Flyout (Durst Stufe 1)
    label = "Your mouth feels dry."
    fw = text_w(label) + 12
    fx = tx0 - 6 - fw
    cv.alpha_composite(nine(P("Plates", "Plate_Flyout"), (3, 3, 3, 3), fw, 17), (fx, ty0 + 28))
    text(cv, fx + 6, ty0 + 32, label, "s3", 8)
    cv.alpha_composite(P("Plates", "Plate_Flyout_Zeiger"), (fx + fw - 1, ty0 + 32))
    return cv


def wake_mock():
    cv = backdrop(0.45)
    w = 122
    x, y = (CW - w) // 2, 10
    cv.alpha_composite(nine(P("Plates", "Plate_HUD"), (3, 3, 3, 3), w, 32), (x, y))
    cv.alpha_composite(P("Wake", "Symbol_Versteck"), (x + 6, y + 8))
    text(cv, x + 28, y + 5, "Wake level", "candle", 8)
    for i in range(5):
        name = "Gelb" if i < 2 else ("Orange" if i == 2 else "Rot")
        if i >= 4:
            name = "Leer"
        cv.alpha_composite(P("Wake", "Balken_" + name), (x + 28 + i * 9, y + 16))
    cv.alpha_composite(P("Wake", "Balken_Puls"), (x + 28 + 3 * 9 - 1, y + 15))
    text(cv, x + 82, y + 18, "4 / 5", "eye", 8)
    return cv


def banner_mock(kind="morgen"):
    cv = backdrop(0.55)
    by = 36
    bh = 116
    tile_ = P("Banner", "Band_Morgen" if kind == "morgen" else "Band_Mitternacht")
    band = Image.new("RGBA", (CW, bh), (0, 0, 0, 0))
    for tx_ in range(0, CW, tile_.width):
        band.alpha_composite(tile_, (tx_, 0))
    cv.alpha_composite(band, (0, by))
    clip = Image.new("RGBA", (CW, bh), (0, 0, 0, 0))
    if kind == "morgen":
        clip.alpha_composite(P("Banner", "Strahlen_Morgen"), (120, 94 + 0 - 108 + 0))
        cv.alpha_composite(clip, (0, by))
    # Sterne
    stars = ((46, 18, "Gross"), (88, 40, "Klein"), (430, 20, "Gross"), (392, 44, "Klein"), (60, 74, "Klein"), (452, 70, "Klein"))
    if kind == "mitternacht":
        stars += ((120, 22, "Klein"), (350, 16, "Klein"), (20, 50, "Klein"), (410, 84, "Gross"), (150, 70, "Klein"), (320, 66, "Klein"))
    for (sx, sy, k) in stars:
        cv.alpha_composite(P("Banner", "Stern_" + k), (sx, by + sy))
    # Dorf mit Glockenturm
    sk = P("Banner", "Skyline_" + ("Morgen" if kind == "morgen" else "Mitternacht"))
    cv.alpha_composite(sk, ((CW - 200) // 2, by + 54))
    # Titelband mit Zierlinien
    rw = 220
    rx = (CW - rw) // 2
    for (ox, flip) in ((rx - 100, True), (rx + rw + 4, False)):
        orn = P("Banner", "Verzierung_Linie")
        if flip:
            orn = orn.transpose(Image.FLIP_LEFT_RIGHT)
        cv.alpha_composite(orn, (ox, by + 19))
    cv.alpha_composite(nine(P("Banner", "Titelband"), (14, 0, 14, 0), rw, 34), (rx, by + 8))
    title = "DAY 2"
    text(cv, (CW - text_w(title, 24)) // 2, by + 13, title, "ly", 24)
    sub = "Dawn breaks over Dusk Bell." if kind == "morgen" else "Midnight. The bell has tolled."
    text(cv, (CW - text_w(sub)) // 2, by + 46, sub, "leaf", 8)
    # Lagebericht darunter
    nw, nh = 300, 98
    nx, ny = (CW - nw) // 2, by + bh + 6
    pan = OLD("Panels", "Panel_Lagebericht")
    cv.alpha_composite(nine(pan, (8, 8, 8, 8), nw, nh), (nx, ny))
    text(cv, nx + 14, ny + 9, "Last night in Dusk Bell", "ly", 8)
    cv.alpha_composite(P("Events", "Trenner"), (nx + 14, ny + 21))
    rows = [("Haus", "The night was quiet. Nothing stirred.", "candle"),
            ("Verlust", "Tobias did not return.", "eye"),
            ("Versteck", "The hideout is stirring.", "lo"),
            ("Talisman", "+1 Talisman", "tal")]
    ry = ny + 26
    for (ic, txt, col) in rows:
        if ic == "Haus":
            im = P("Events", "Symbol_Haus")
        elif ic == "Verlust":
            im = P("Events", "Symbol_Verlust")
        elif ic == "Versteck":
            im = OLD("Icons", "Icon_Versteck")
        else:
            im = OLD("Icons", "Icon_Talisman")
        cv.alpha_composite(im, (nx + 12, ry))
        text(cv, nx + 32, ry + 4, txt, col, 8)
        ry += 17
    btn = nine(OLD("Buttons", "Button_Normal"), (8, 7, 8, 7), 56, 16)
    cv.alpha_composite(btn, (nx + nw - 56 - 10, ny + nh - 22))
    text(cv, nx + nw - 56 - 10 + (56 - text_w("Continue")) // 2, ny + nh - 22 + 4, "Continue", "candle", 8)
    return cv


def sheet():
    """Alle Bausteine, nach Gruppen sortiert, 4x vergroessert."""
    pad = 6
    groups = [g for g in GROUPS if g in MANIFEST]
    rows = []
    for g in groups:
        x, y, rowh, placed = pad, pad + 10, 0, []
        maxw = 520
        for (nm, im) in MANIFEST[g]:
            if im.width > 140 and im.height > 14:
                continue
            if x + im.width + pad > maxw:
                x = pad
                y += rowh + pad
                rowh = 0
            placed.append((im, x, y))
            x += im.width + pad
            rowh = max(rowh, im.height)
        rows.append((g, placed, y + rowh + pad))
    H = sum(r[2] for r in rows) + 4
    cv = Image.new("RGBA", (520, H), rgb("nb1"))
    oy = 0
    for g, placed, h in rows:
        text(cv, 4, oy + 3, g, "s3", 8, False)
        for (im, x, y) in placed:
            cv.alpha_composite(im, (x, oy + y))
        oy += h
    return cv


scaled(hud_mock(), 3).save(os.path.join(OUT, "Preview", "Vorschau_HUD.png"))
scaled(wake_mock(), 3).save(os.path.join(OUT, "Preview", "Vorschau_Wecklevel.png"))
scaled(banner_mock("morgen"), 3).save(os.path.join(OUT, "Preview", "Vorschau_Neuer_Tag.png"))
scaled(banner_mock("mitternacht"), 3).save(os.path.join(OUT, "Preview", "Vorschau_Neuer_Tag_Mitternacht.png"))
scaled(sheet(), 3).save(os.path.join(OUT, "Preview", "Bauteile.png"))
