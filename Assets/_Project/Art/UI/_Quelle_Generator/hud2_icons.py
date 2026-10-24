"""HUD-Paket (Neu): Icons. 16x16 fuer Beduerfnisse/Stimmung und Ereignisse, 11x11 fuer die Vitalbalken.
Stil wie das vorhandene Icon-Paket: dicke Form, dunkle Outline #1a1526, Licht oben links, Schatten unten rechts."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
from hud2_lib import *


# ================================================================ Bedürfnisse (16x16)
def icon_hunger():
    """Brotlaib mit drei Einschnitten."""
    rows = [
        "................",
        "................",
        ".....oooooo.....",
        "...ooBHHBBBoo...",
        "..oBHHBBBBBBBo..",
        ".oBHBBBMBBMBBBo.",
        ".oBBBBMMBMMBBDo.",
        ".oBBBBBMBBMBBDo.",
        ".oBBBBBBBBBBDDo.",
        "..oBBBBBBBBDDo..",
        "...oDDDDDDDDo...",
        "....oooooooo....",
        "................",
        "................",
        "................",
        "................",
    ]
    im = from_ascii(rows, {"o": "od", "B": "straw", "H": "ly", "M": "wh", "D": "wh"})
    # Kruste unten dunkler, Einschnitte tief
    for x in range(4, 12):
        put(im, x, 10, "wm")
    for (x, y) in ((8, 6), (8, 7), (11, 6), (11, 7), (7, 5)):
        put(im, x, y, "wm")
    put(im, 3, 4, "candle"); put(im, 4, 3, "candle")
    return im


def icon_durst():
    """Wassertropfen in Nachtblau-Tönen (Talisman-Cyan ist tabu)."""
    rows = [
        "................",
        ".......oo.......",
        ".......oo.......",
        "......oWWo......",
        "......oWWo......",
        ".....oWWWWo.....",
        "....oWHWWWWo....",
        "...oWHHWWWWDo...",
        "...oWHWWWWWDo...",
        "...oWWWWWWWDo...",
        "...oWWWWWWDDo...",
        "....oWWWWDDo....",
        ".....oDDDDo.....",
        "......oooo......",
        "................",
        "................",
    ]
    return from_ascii(rows, {"o": "od", "W": "blh", "H": "moon", "D": "bl"})


def icon_muede():
    """Drei Z, die nach oben rechts kleiner werden."""
    def z(im, x, y, n, col, sh, th=1):
        for t in range(th):
            for i in range(n):
                put(im, x + i, y + t, col)
                put(im, x + i, y + n - 1 - t, col)
        for i in range(n):
            xx = x + n - 1 - i
            for t in range(th):
                put(im, xx - t if th > 1 else xx, y + i, col)
        for i in range(n):
            put(im, x + i, y + n - 1, sh)

    def f(im):
        z(im, 0, 7, 7, "moon", "s3", 2)
        z(im, 6, 3, 5, "moon", "s3", 1)
        z(im, 10, 0, 3, "s3", "s2", 1)
    return icon_from(14, 14, f, 16)


def icon_froh():
    """Lächelndes Gesicht in Warmgelb."""
    def f(im):
        for y in range(14):
            for x in range(14):
                dx, dy = x - 6.5, y - 6.5
                if math.hypot(dx, dy) <= 6.6:
                    put(im, x, y, "lo" if dx + dy > 4.2 else "ly")
        put(im, 3, 3, "candle"); put(im, 4, 3, "candle"); put(im, 3, 4, "candle")
        for (x, y) in ((4, 5), (4, 6), (9, 5), (9, 6)):
            put(im, x, y, "od")
        for (x, y) in ((3, 8), (4, 9), (5, 10), (6, 10), (7, 10), (8, 10), (9, 9), (10, 8)):
            put(im, x, y, "od")
        put(im, 2, 7, "pink"); put(im, 11, 7, "pink")
    return icon_from(14, 14, f, 16)


def icon_sozial():
    """Zwei Sprechblasen, hinten Kerzenweiß, vorn Rosé."""
    def f(im):
        rect(im, 0, 1, 8, 6, "candle")
        for (x, y) in ((0, 1), (8, 1), (0, 6), (8, 6)):
            put(im, x, y, "candle", 0)
        rect(im, 1, 6, 8, 6, "s3")
        put(im, 2, 7, "candle"); put(im, 2, 8, "s3"); put(im, 3, 7, "s3")
        for x in (2, 4, 6):
            put(im, x, 3, "s2")
        rect(im, 5, 7, 13, 12, "pink")
        for (x, y) in ((5, 7), (13, 7), (5, 12), (13, 12)):
            put(im, x, y, "pink", 0)
        rect(im, 6, 12, 13, 12, "rd")
        put(im, 11, 13, "pink"); put(im, 12, 13, "rd"); put(im, 12, 12, "rd")
        # kleines Herz in der vorderen Blase
        for (x, y) in ((8, 9), (10, 9), (8, 10), (9, 10), (10, 10), (9, 11)):
            put(im, x, y, "candle")
        put(im, 9, 9, "pink")
    return icon_from(14, 14, f, 16)


def icon_ruhe():
    """Dampfende Teetasse (Beruhigungstee, Kamin)."""
    def f(im):
        for y in range(6, 12):
            for x in range(2, 10):
                if y == 11 and x in (2, 9):
                    continue
                put(im, x, y, "s3" if x >= 8 else "moon")
        rect(im, 2, 6, 9, 6, "wh")                    # Tee
        rect(im, 3, 6, 5, 6, "wm")
        for (x, y) in ((10, 7), (11, 7), (11, 8), (11, 9), (10, 10), (9, 10)):
            put(im, x, y, "moon" if y < 10 else "s3")
        rect(im, 1, 12, 10, 12, "s3")                 # Untertasse
        rect(im, 2, 13, 9, 13, "s2")
        # Dampf: zwei getrennte Schlangenlinien
        for (x, y) in ((3, 4), (4, 3), (3, 2), (4, 1)):
            put(im, x, y, "s3")
        for (x, y) in ((7, 3), (8, 2), (7, 1), (8, 0)):
            put(im, x, y, "s3")
    return icon_from(14, 14, f, 16, pad=(1, 1))


def icon_rausch():
    """Grüne Flasche mit Etikett."""
    def f(im):
        rect(im, 6, 0, 7, 0, "wh")                    # Korken
        rect(im, 6, 1, 7, 4, "fm")                    # Hals
        put(im, 6, 1, "g")
        rect(im, 5, 5, 8, 5, "fm")
        rect(im, 4, 6, 9, 12, "g")                    # Koerper
        for y in range(6, 13):
            put(im, 4, y, "gh")
            put(im, 9, y, "fd")
            put(im, 8, y, "fm")
        rect(im, 4, 13, 9, 13, "fd")
        rect(im, 4, 8, 9, 10, "candle")               # Etikett
        put(im, 9, 8, "s3"); put(im, 9, 9, "s3"); put(im, 9, 10, "s3")
        for x in (5, 6, 7):
            put(im, x, 9, "s2")
        put(im, 5, 5, "g")
    return icon_from(14, 14, f, 16)


def icon_verletzt():
    """Gewickelter Verband mit Polster und Kreuzstichen."""
    def f(im):
        for y in range(14):
            for x in range(14):
                d = (x + y) - 13
                e = x - y
                if abs(d) <= 3 and abs(e) <= 7 - abs(d) // 2 * 0:
                    if abs(e) > 6 or (abs(e) == 6 and abs(d) == 3):
                        continue
                    c = "candle" if d < 1 else "s3"
                    if abs(d) <= 1 and abs(e) <= 2:
                        c = "k3" if d < 1 else "k2"
                    put(im, x, y, c)
        for (x, y) in ((4, 7), (5, 8), (8, 4), (9, 5)):   # Wickelkanten
            put(im, x, y, "s2")
        for (x, y) in ((5, 7), (4, 8), (9, 4), (8, 5)):
            put(im, x, y, "s2")
    return icon_from(14, 14, f, 16)


# ================================================================ Ereignisse (16x16)
def icon_haus():
    """Kleines Dorfhaus mit warmem Fenster: ruhige Nacht, nichts passiert."""
    rows = [
        "................",
        ".......oo.......",
        "......oRRo......",
        ".....oRRRRo.....",
        "....oRRHRRRo....",
        "...oRRHRRRRRo...",
        "..oRRHRRRRRRRo..",
        ".oooooooooooooo.",
        "..oWWWWWWWWWWo..",
        "..oWWYYWWWDDWo..",
        "..oWWYYWWWDDWo..",
        "..oWWWWWWWWWWo..",
        "..oWWWWWooWWWo..",
        "..oDDDDDoLoDDo..",
        "..oooooooooooo..",
        "................",
    ]
    im = from_ascii(rows, {"o": "od", "R": "rd", "H": "pink", "W": "wh", "D": "wm", "Y": "ly", "L": "wd"})
    put(im, 9, 12, "wd"); put(im, 9, 13, "wd")
    return im


def icon_kerze():
    """Weiße Kerze mit Flamme: Erinnerung an Verstorbene."""
    rows = [
        "................",
        "......oo........",
        ".....oLLo.......",
        ".....oLYo.......",
        "......oYoo......",
        ".....ooCCoo.....",
        "....oCCCCCCo....",
        "....oCCCCCDo....",
        "....oCCCCCDo....",
        "....oCCCCCDo....",
        "....oCCCCCDo....",
        "....oCCCCCDo....",
        "...ooCCCCCDoo...",
        "..oSSSSSSSSSSo..",
        "..oooooooooooo..",
        "................",
    ]
    im = from_ascii(rows, {"o": "od", "L": "lo", "Y": "ly", "C": "candle", "D": "s3", "S": "s2"})
    put(im, 6, 2, "ly"); put(im, 6, 3, "candle")
    return im


def icon_glocke():
    """Die Abendglocke (Dusk Bell)."""
    rows = [
        "................",
        ".......oo.......",
        "......oLLo......",
        ".....ooLLoo.....",
        "....oHHHYYYo....",
        "...oHHYYYYYDo...",
        "...oHYYYYYYDo...",
        "...oHYYYYYYDo...",
        "..oHYYYYYYYYDo..",
        "..oHYYYYYYYDDo..",
        ".oHYYYYYYYYDDDo.",
        ".oDDDDDDDDDDDDo.",
        ".ooooooooooooooo",
        "......oLLo......",
        ".......oo.......",
        "................",
    ]
    rows = [r[:16] for r in rows]
    im = from_ascii(rows, {"o": "od", "L": "wh", "H": "candle", "Y": "ly", "D": "lo"})
    return im


# ================================================================ Vital-Icons (11x11)
def vital_herz():
    rows = [
        ".PPP.PPP.",
        "PCPPPPPPR",
        "PPPPPPPPR",
        "PPPPPPPRR",
        ".PPPPPRR.",
        "..PPPRR..",
        "...PRR...",
        "....R....",
        ".........",
    ]
    core = from_ascii(rows, {"P": "pink", "C": "candle", "R": "rd"})
    full = new(11, 11)
    full.paste(core, (1, 1))
    return outline(full)


def vital_blitz():
    rows = [
        "....LGGG.",
        "...LGGG..",
        "..LGGG...",
        ".LGGGGGG.",
        "..DDGGG..",
        "....GGD..",
        "...GGD...",
        "..GGD....",
        "..GD.....",
    ]
    core = from_ascii(rows, {"L": "candle", "G": "leaf", "D": "g"})
    full = new(11, 11)
    full.paste(core, (1, 1))
    return outline(full)


def vital_geist():
    """Offenes Auge mit Wirbel-Pupille: Sanity."""
    rows = [
        "..MMMMM..",
        ".MWWWWWM.",
        "MWWIIIWWM",
        "MWIIPIIWM",
        "MWWIIIWWM",
        ".MWWWWWM.",
        "..MMMMM..",
    ]
    core = from_ascii(rows, {"M": "sv3", "W": "moon", "I": "blh", "P": "od"})
    put(core, 3, 2, "candle")
    full = new(11, 11)
    full.paste(core, (1, 2))
    return outline(full)


BEDUERFNIS_ICONS = [
    ("Hunger", icon_hunger), ("Durst", icon_durst), ("Muede", icon_muede), ("Froh", icon_froh),
    ("Sozial", icon_sozial), ("Ruhe", icon_ruhe), ("Rausch", icon_rausch), ("Verletzt", icon_verletzt),
]
EREIGNIS_ICONS = [("Haus", icon_haus), ("Kerze", icon_kerze), ("Glocke", icon_glocke)]
VITAL_ICONS = [("Herz", vital_herz), ("Ausdauer", vital_blitz), ("Geist", vital_geist)]
