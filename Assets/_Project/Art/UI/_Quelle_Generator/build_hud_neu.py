"""Baut das neue, modulare HUD-Paket (Art/UI/HUD_Neu): Plates, Vitalbalken (Leben, Ausdauer, Sanity), Uhr + Tagesspur,
Beduerfnis-/Stimmungs-Kacheln mit Stufen, Quest-Tracker (aufklappbar), Wecklevel-Einblendung, Tages-Banner und Ereignis-Icons.
Alles nur Farben der Style-Bibel (nwui.PAL), Outline #1a1526, keine Anti-Aliasing-Kanten.

Aufruf:  python build_hud_neu.py      (danach pack_aseprite.lua ueber den Aseprite-MCP)
"""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import json
import math

from hud2_lib import *
import hud2_icons as IC
from hud2_extra import *   # Weitere Icons (negative Stimmungen) und Banner-Emblem

# ================================================================ Plates (9-Slice)
plate_hud = save(frame(12, 12, "od", 170, "sv2", "sv3"), "Plates", "Plate_HUD")                 # Border 3
plate_flyout = save(frame(12, 12, "on", 240, "sv2", "sv3"), "Plates", "Plate_Flyout")           # Border 3


def header(accent):
    im = frame(13, 13, "sv1", 235, "sv2", "sv3")
    for y in range(2, 11):
        put(im, 2, y, accent)
        put(im, 3, y, accent)
    return im


save(header("ly"), "Plates", "Plate_Header_Haupt")        # 9-Slice Border L4 T3 R3 B3, Akzent im linken Rand
save(header("blh"), "Plates", "Plate_Header_Neben")

pointer = new(6, 9)
for y in range(9):
    w = 5 - abs(y - 4)
    for x in range(max(w, 0)):
        put(pointer, x, y, "on")
    if w > 0:
        put(pointer, w - 1, y, "sv2")
save(pointer, "Plates", "Plate_Flyout_Zeiger")

# ================================================================ Vitalbalken
BAR_W, BAR_H = 64, 9
IW, IH = 60, 5


def bar_frame():
    im = new(BAR_W, BAR_H)
    rect(im, 0, 0, BAR_W - 1, BAR_H - 1, "od")
    rect(im, 1, 1, BAR_W - 2, BAR_H - 2, "sv2")
    rect(im, 2, 2, BAR_W - 3, BAR_H - 3, "on")
    for (x, y) in ((0, 0), (BAR_W - 1, 0), (0, BAR_H - 1), (BAR_W - 1, BAR_H - 1)):
        put(im, x, y, "od", 0)
    put(im, 1, 1, "sv3")
    for x in range(2, BAR_W - 2):
        put(im, x, 1, "sv3")
    return im


def bar_fill(main, shade, light):
    im = new(IW, IH)
    rect(im, 0, 0, IW - 1, IH - 1, main)
    rect(im, 0, 0, IW - 1, 0, light)
    rect(im, 0, IH - 1, IW - 1, IH - 1, shade)
    return im


save(bar_frame(), "Vitals", "Balken_Rahmen")
save(bar_fill("pink", "rd", "candle"), "Vitals", "Fuellung_Leben")
save(bar_fill("eye", "blood", "candle"), "Vitals", "Fuellung_Leben_Kritisch")
save(bar_fill("gh", "g", "leaf"), "Vitals", "Fuellung_Ausdauer")
save(bar_fill("lo", "rd", "ly"), "Vitals", "Fuellung_Ausdauer_Leer")          # erschoepft: orange
save(bar_fill("moon", "s3", "candle"), "Vitals", "Fuellung_Geist")
save(bar_fill("lo", "rd", "ly"), "Vitals", "Fuellung_Geist_Niedrig")           # unter 40 %: Schlafsperre
save(bar_fill("eye", "blood", "pink"), "Vitals", "Fuellung_Geist_Kritisch")    # unter 20 %


def ticks(n):
    im = new(IW, IH)
    for k in range(1, n):
        x = round(k * IW / n) - 1
        rect(im, x, 0, x, IH - 1, "on")
    return im


save(ticks(3), "Vitals", "Teiler_3")            # 3 Lebenspunkte (Kampfregeln)
save(ticks(10), "Vitals", "Teiler_10")


def sleep_mark():
    im = new(IW, IH)
    x = int(IW * 0.4) - 1
    for y in (0, 2, 4):
        put(im, x, y, "ly")
    return im


save(sleep_mark(), "Vitals", "Marke_Schlafsperre")   # 40 %


def lock_hatch():
    im = new(IW, IH)
    for y in range(IH):
        for x in range(IW):
            put(im, x, y, "sv1" if (x + y) % 4 in (0, 1) else "on")
    for x in range(IW):
        put(im, x, 0, "on")
        put(im, x, IH - 1, "on")
    return im


save(lock_hatch(), "Vitals", "Schraffur_Gesperrt")   # Maximum-Erschoepfung: der gesperrte Teil rechts

trail = new(IW, IH)
rect(trail, 0, 0, IW - 1, IH - 1, "candle", 150)
save(trail, "Vitals", "Verlust_Spur")

for nm, fn in IC.VITAL_ICONS:
    save(fn(), "Vitals", "Icon_" + nm)

# ================================================================ Uhr und Tagesspur
TRACK_W = 48
SEG = [(0, 5, "nb3", "sv3"), (5, 9, "ly", "candle"), (9, 18, "candle", "moon"), (18, 21, "lo", "ly"), (21, 24, "nb3", "sv3")]


def track():
    im = new(TRACK_W, 3)
    for (h0, h1, main, light) in SEG:
        x0, x1 = h0 * 2, h1 * 2 - 1
        rect(im, x0, 0, x1, 2, main)
        rect(im, x0, 0, x1, 0, light)
    return im


def track_frame():
    im = new(TRACK_W + 2, 5)
    rect(im, 0, 0, TRACK_W + 1, 4, "od")
    rect(im, 1, 1, TRACK_W, 3, "on")
    return im


save(track_frame(), "Clock", "Spur_Rahmen")
save(track(), "Clock", "Spur_Segmente")
past = new(TRACK_W, 3)
rect(past, 0, 0, TRACK_W - 1, 2, "od", 140)
save(past, "Clock", "Spur_Vergangen")          # wird auf die Breite der vergangenen Zeit gecroppt

marker = new(5, 4)
for y in range(3):
    rect(marker, y, y, 4 - y, y, "candle")
save(outline(marker), "Clock", "Spur_Marke")

bell_rows = [
    "...L...",
    "..HHH..",
    ".HYYYD.",
    ".HYYYD.",
    "HYYYYYD",
    "DDDDDDD",
    "...D...",
]
save(outline(from_ascii(bell_rows, {"L": "wh", "H": "candle", "Y": "ly", "D": "lo"})), "Clock", "Spur_Glocke")

# ================================================================ Beduerfnisse: Kacheln und Symbole
STAGE_COL = {1: "sv3", 2: "ly", 3: "lo", 4: "eye"}
POS_COL = "gh"
TILE = 22


def tile(col, pips, pip_col, flash=False):
    im = new(TILE, TILE)
    rect(im, 0, 0, TILE - 1, TILE - 1, "od")
    rect(im, 1, 1, TILE - 2, TILE - 2, "candle" if flash else col)
    rect(im, 2, 2, TILE - 3, TILE - 3, "on")
    for (x, y) in ((0, 0), (TILE - 1, 0), (0, TILE - 1), (TILE - 1, TILE - 1)):
        put(im, x, y, "od", 0)
    for (x, y) in ((1, 1), (TILE - 2, 1), (1, TILE - 2), (TILE - 2, TILE - 2)):
        put(im, x, y, "od")
    for x in range(3, TILE - 3):
        put(im, x, 2, "sv1")
    for i in range(4):
        x = 5 + i * 3
        rect(im, x, 18, x + 1, 19, pip_col if i < pips else "od")
    return im


tiles = {}
for st in (1, 2, 3, 4):
    tiles[("neg", st)] = save(tile(STAGE_COL[st], st, STAGE_COL[st]), "Needs", f"Kachel_Stufe_{st}")
for st in (1, 2):
    tiles[("pos", st)] = save(tile(POS_COL, st, "leaf"), "Needs", f"Kachel_Positiv_{st}")
save(tile("sv3", 0, "od", flash=True), "Needs", "Kachel_Blitz")       # kurzes Aufleuchten bei Stufenwechsel

NEED_ICONS = {}
for nm, fn in IC.BEDUERFNIS_ICONS:
    NEED_ICONS[nm] = fn()
NEED_ICONS["Traurig"] = icon_traurig()
NEED_ICONS["Einsam"] = icon_einsam()
NEED_ICONS["Stress"] = icon_stress()
for nm, im in NEED_ICONS.items():
    save(im, "Needs", "Symbol_" + nm)

# Welche Symbole gehoeren zu welcher Kette: (Anzeigename, Symbol Negativ, Symbol Positiv oder None)
NEEDS = [
    ("Hunger", "Hunger", None), ("Durst", "Durst", None), ("Muede", "Muede", None),
    ("Rausch", "Rausch", None), ("Verletzt", "Verletzt", None),
    ("Stimmung", "Traurig", "Froh"), ("Gesellschaft", "Einsam", "Sozial"), ("Anspannung", "Stress", "Ruhe"),
]
komplett = []
for need, neg, pos in NEEDS:
    for st in (1, 2, 3, 4):
        t = tiles[("neg", st)].copy()
        t.alpha_composite(NEED_ICONS[neg], (3, 1))
        komplett.append(save(t, "Needs", f"Anzeige_{need}_Stufe_{st}"))
    if pos:
        for st in (1, 2):
            t = tiles[("pos", st)].copy()
            t.alpha_composite(NEED_ICONS[pos], (3, 1))
            komplett.append(save(t, "Needs", f"Anzeige_{need}_Positiv_{st}"))

NEED_TEXT = {
    "Hunger": ["Your stomach growls.", "I'm hungry.", "I'm really hungry.", "I'm starving."],
    "Durst": ["Your mouth feels dry.", "I'm thirsty.", "I'm really thirsty.", "I'm parched."],
    "Muede": ["A little drowsy.", "I'm tired.", "I'm exhausted.", "I can't keep my eyes open."],
    "Rausch": ["Tipsy.", "Drunk.", "Very drunk.", "Wasted."],
    "Verletzt": ["A scratch.", "I'm hurt.", "I'm badly hurt.", "I'm barely standing."],
    "Stimmung": ["Feeling a bit down.", "I'm unhappy.", "I'm miserable.", "I feel hollow."],
    "Gesellschaft": ["A bit lonely.", "I'm lonely.", "I'm really lonely.", "I haven't spoken to anyone."],
    "Anspannung": ["A little tense.", "I'm on edge.", "I'm stressed.", "I'm about to panic."],
}
NEED_POS_TEXT = {"Stimmung": ["Feeling good.", "I'm happy."], "Gesellschaft": ["Good company.", "I'm among friends."],
                 "Anspannung": ["Feeling relaxed.", "I'm completely calm."]}

# ================================================================ Quest-Tracker
# Pfeile: eingeklappt zeigt nach rechts, aufgeklappt nach unten
az = new(7, 7)
for y in range(7):
    w = 4 - abs(y - 3)
    for x in range(1, 1 + max(w, 0)):
        put(az, x, y, "candle")
save(az, "Quest", "Pfeil_Zu")
ao = new(7, 7)
for x in range(7):
    h = 4 - abs(x - 3)
    for y in range(1, 1 + max(h, 0)):
        put(ao, x, y, "candle")
save(ao, "Quest", "Pfeil_Auf")
azh, aoh = az.copy(), ao.copy()
for im in (azh, aoh):
    for y in range(7):
        for x in range(7):
            if im.getpixel((x, y))[3]:
                put(im, x, y, "ly")
save(azh, "Quest", "Pfeil_Zu_Hover")
save(aoh, "Quest", "Pfeil_Auf_Hover")

q_main = icon_from(10, 10, lambda im: (
    poly(im, [(4, 0), (9, 4), (4, 9), (0, 4)], "ly"),
    [put(im, x, y, "lo") for (x, y) in ((5, 5), (6, 4), (4, 6), (5, 6), (6, 5), (7, 4), (3, 7), (4, 7), (5, 7))],
    [put(im, 4, y, "od") for y in (2, 3, 4)],
    put(im, 4, 6, "od"),
    put(im, 3, 2, "candle"), put(im, 2, 3, "candle")), 12)
save(q_main, "Quest", "Symbol_Haupt")
scroll_rows = [
    ".oooooooo.",
    "oCCCCCCCCo",
    "oCSSSSSCCo",
    "oCCCCCCCCo",
    "oCSSSSCCCo",
    "oCCCCCCCDo",
    "oCSSSSSCDo",
    ".oDDDDDDo.",
]
q_side = from_ascii(scroll_rows, {"o": "od", "C": "candle", "D": "s3", "S": "blh"})
sq = new(12, 12)
sq.paste(q_side, (1, 2))
save(sq, "Quest", "Symbol_Neben")

ring = new(7, 7)
disc(ring, 3, 3, 2.8, "s2")
disc(ring, 3, 3, 1.4, "on")
save(ring, "Quest", "Punkt_Offen")
act = new(7, 7)
disc(act, 3, 3, 2.9, "ly")
disc(act, 3, 3, 1.2, "lo")
save(act, "Quest", "Punkt_Aktiv")
done = new(7, 7)
disc(done, 3, 3, 2.9, "g")
for (x, y) in ((1, 3), (2, 4), (3, 3), (4, 2), (5, 1)):
    put(done, x, y, "candle")
save(done, "Quest", "Punkt_Fertig")
fail = new(7, 7)
disc(fail, 3, 3, 2.9, "rd")
for i in range(3):
    put(fail, 2 + i, 2 + i, "pink")
    put(fail, 4 - i, 2 + i, "pink")
save(fail, "Quest", "Punkt_Gescheitert")

pr_frame = new(40, 5)
rect(pr_frame, 0, 0, 39, 4, "od")
rect(pr_frame, 1, 1, 38, 3, "on")
for (x, y) in ((0, 0), (39, 0), (0, 4), (39, 4)):
    put(pr_frame, x, y, "od", 0)
save(pr_frame, "Quest", "Fortschritt_Rahmen")
pr_fill = new(38, 3)
rect(pr_fill, 0, 0, 37, 2, "ly")
rect(pr_fill, 0, 0, 37, 0, "candle")
rect(pr_fill, 0, 2, 37, 2, "lo")
save(pr_fill, "Quest", "Fortschritt_Fuellung")

badge_new = frame(19, 9, "ly", 255, "od", "candle")
for (x, y) in ((0, 0), (18, 0), (0, 8), (18, 8)):
    put(badge_new, x, y, "od", 0)
save(badge_new, "Quest", "Abzeichen_Neu")        # Text "NEW" in #1a1526
badge_cnt = frame(13, 9, "sv1", 255, "od", "sv2")
save(badge_cnt, "Quest", "Abzeichen_Zahl")
mk = new(4, 7)
for y in range(7):
    w = 4 - abs(y - 3)
    rect(mk, 0, y, max(w, 1) - 1, y, "ly")
save(mk, "Quest", "Marke_Verfolgt")
sep = new(32, 1)
for x in range(0, 32, 2):
    put(sep, x, 0, "sv2")
save(sep, "Quest", "Trenner")

# ================================================================ Wecklevel (1 bis 5)
def wake_pip(main, light, shade):
    im = new(7, 12)
    rect(im, 1, 1, 5, 10, main)
    rect(im, 1, 1, 5, 2, light)
    rect(im, 1, 9, 5, 10, shade)
    return outline(im)


for nm, (m, l, s_) in {"Leer": ("on", "sv1", "od"), "Gelb": ("ly", "candle", "lo"), "Orange": ("lo", "ly", "fire"),
                       "Rot": ("eye", "pink", "blood")}.items():
    save(wake_pip(m, l, s_), "Wake", "Balken_" + nm)
pulse = new(9, 14)
rect(pulse, 0, 0, 8, 13, "candle", 190)
rect(pulse, 1, 1, 7, 12, "candle", 0)
save(pulse, "Wake", "Balken_Puls")
vers = Image.open(os.path.join(UI, "Icons", "Icon_Versteck.png")).convert("RGBA")
save(vers, "Wake", "Symbol_Versteck")

# ================================================================ Tages-Banner
save(band("morgen"), "Banner", "Band_Morgen")                 # 8x116, waagerecht KACHELN (Image Type Tiled), nicht strecken
save(band("mitternacht"), "Banner", "Band_Mitternacht")
save(skyline("morgen"), "Banner", "Skyline_Morgen")           # 200x60, Dorf mit Glockenturm, Sonne dahinter
save(skyline("mitternacht"), "Banner", "Skyline_Mitternacht")
save(rays(), "Banner", "Strahlen_Morgen")                     # 240x110, halbtransparent, hinter Titelband
save(ribbon(34), "Banner", "Titelband")                       # 9-Slice, Border 14/0/14/0, Hoehe 34 fuer Schriftgroesse 24
save(ribbon(22), "Banner", "Titelband_Klein")                 # fuer Schriftgroesse 16
save(line_ornament(), "Banner", "Verzierung_Linie")           # 96x11, links gespiegelt verwenden
save(star(5), "Banner", "Stern_Klein")
save(star(7), "Banner", "Stern_Gross")

# ================================================================ Ereignisse
for nm, fn in IC.EREIGNIS_ICONS:
    save(fn(), "Events", "Symbol_" + nm)
save(Image.open(os.path.join(UI, "Icons", "Icon_Warnung.png")).convert("RGBA"), "Events", "Symbol_Verlust")
save(IC.icon_verletzt(), "Events", "Symbol_Verletzt")
dot_sep = new(48, 1)
for x in range(0, 48, 3):
    put(dot_sep, x, 0, "sv2")
save(dot_sep, "Events", "Trenner")

# ================================================================ Daten fuer Unity
data = {
    "need_stages": NEED_TEXT, "need_positive": NEED_POS_TEXT,
    "stage_colors": {k: PAL[v] for k, v in STAGE_COL.items()}, "positive_color": PAL[POS_COL],
}
with open(os.path.join(OUT, "Beduerfnisse_Texte.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

import hud2_preview  # noqa: E402,F401  (baut die Vorschaubilder)
print("HUD_Neu fertig:", OUT, sum(len(v) for v in MANIFEST.values()), "Sprites")
