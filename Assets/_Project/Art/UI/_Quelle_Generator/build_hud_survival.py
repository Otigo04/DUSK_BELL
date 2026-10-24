"""HUD (Neu), Erweiterung fuers Survival-System: drei weitere Zustands-Kacheln (Erschoepft, Kalt, Verstoert).
Ergaenzt Art/UI/HUD_Neu/Needs um Symbol_* und Anzeige_<Kette>_Stufe_1..4 im gleichen Stil wie build_hud_neu.py
(Kachel 22x22, Symbol 16x16 bei 3,1; nur Farben der Style-Bibel). Einzeln lauffaehig: python build_hud_survival.py
Texte der Stufen stehen in Scripts/UI/NwNeedTile.cs (NwNeedTexts) und Beduerfnisse_Texte.json."""
import os as _o, sys as _s; _s.path.insert(0, _o.path.normpath(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)), '../../__STYLEBIBLE/tools'))); import pixel_guard  # noqa: E402,F401  (Pixel Law, siehe __STYLEBIBLE/ART_STYLE.md)
import json
import os

from hud2_lib import *

TILE = 22
STAGE_COL = {1: "sv3", 2: "ly", 3: "lo", 4: "eye"}


def tile(col, pips, pip_col):
    # Gleiche Kachel wie build_hud_neu.tile (dort laeuft beim Import das ganze Paket, deshalb hier kopiert)
    im = new(TILE, TILE)
    rect(im, 0, 0, TILE - 1, TILE - 1, "od")
    rect(im, 1, 1, TILE - 2, TILE - 2, col)
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


def icon_erschoepft():
    """Stiefel mit Schweisstropfen: ausgepowert."""
    rows = [
        "..............",
        "...WWWW.......",
        "...WHWW....B..",
        "...WHWW...BBB.",
        "...WWWW...BmB.",
        "...WWWW....B..",
        "...WWWWW......",
        "...WWWWWWW....",
        "..WWWWWWWWWW..",
        "..WHWWWWWWWWD.",
        "..WWWWWWWWWWD.",
        "..SSSSSSSSSSS.",
        "..............",
        "..............",
    ]
    core = from_ascii(rows, {"W": "wm", "H": "wh", "D": "wd", "S": "ed", "B": "blh", "m": "moon"})
    return icon_from(14, 14, lambda im: im.paste(core, (0, 0)), 16)


def icon_kalt():
    """Schneeflocke in Nachtblau/Mondweiss."""
    def f(im):
        c = 6
        for i in range(13):
            put(im, c, i, "blh")
            put(im, i, c, "blh")
        for i in range(2, 11):
            put(im, i, i, "blh")
            put(im, i, 12 - i, "blh")
        for (x, y) in ((5, 2), (7, 2), (5, 10), (7, 10), (2, 5), (2, 7), (10, 5), (10, 7)):
            put(im, x, y, "moon")
        for (x, y) in ((6, 0), (6, 12), (0, 6), (12, 6), (6, 6)):
            put(im, x, y, "moon")
    return icon_from(13, 13, f, 16)


def icon_verstoert():
    """Dunkle Scheibe mit Wirbel und rotem Punkt: der Verstand dreht sich."""
    def f(im):
        for y in range(14):
            for x in range(14):
                if math.hypot(x - 6.5, y - 6.5) <= 6.6:
                    put(im, x, y, "sv1" if (x + y) % 7 else "sv2")
        pts = []
        t = 0.0
        while t < 6.2 * math.pi:
            r = 0.55 + t * 0.30
            pts.append((int(round(6.5 + r * math.cos(t))), int(round(6.5 + r * math.sin(t)))))
            t += 0.18
        for (x, y) in pts:
            if math.hypot(x - 6.5, y - 6.5) <= 6.0:
                put(im, x, y, "moon")
        put(im, 6, 6, "eye"); put(im, 7, 6, "eye"); put(im, 6, 7, "eye"); put(im, 7, 7, "eye")
    return icon_from(14, 14, f, 16)


tiles = {st: tile(STAGE_COL[st], st, STAGE_COL[st]) for st in (1, 2, 3, 4)}
CHAINS = [("Erschoepft", "Erschoepft", icon_erschoepft()), ("Kalt", "Kalt", icon_kalt()), ("Verstoert", "Verstoert", icon_verstoert())]

for chain, symbol, icon in CHAINS:
    save(icon, "Needs", "Symbol_" + symbol)
    for st in (1, 2, 3, 4):
        t = tiles[st].copy()
        t.alpha_composite(icon, (3, 1))
        save(t, "Needs", f"Anzeige_{chain}_Stufe_{st}")

# Texte (Englisch) in die JSON-Doku aufnehmen
TEXTS = {
    "Erschoepft": ["A bit winded.", "I'm out of breath.", "My legs are shaking.", "I'm completely spent."],
    "Kalt": ["A chill in the air.", "I'm cold.", "I'm freezing.", "I'm frozen to the bone."],
    "Verstoert": ["Slightly uneasy.", "I'm rattled.", "I'm losing my grip.", "I don't trust my own mind."],
}
jpath = os.path.join(OUT, "Beduerfnisse_Texte.json")
with open(jpath, encoding="utf-8") as fh:
    data = json.load(fh)
data["need_stages"].update(TEXTS)
with open(jpath, "w", encoding="utf-8") as fh:
    json.dump(data, fh, ensure_ascii=False, indent=2)
    fh.write("\n")

# Vorschau (3x) zum Pruefen
prev = new(TILE * 4 * 3 + 5 * 3, TILE * 3 * 3 + 4 * 3)
prev.paste((26, 21, 38, 255), (0, 0, prev.width, prev.height))
for r, (chain, symbol, icon) in enumerate(CHAINS):
    for st in (1, 2, 3, 4):
        t = tiles[st].copy()
        t.alpha_composite(icon, (3, 1))
        t = t.resize((TILE * 3, TILE * 3), Image.NEAREST)
        prev.alpha_composite(t, (3 + (st - 1) * (TILE * 3 + 3), 3 + r * (TILE * 3 + 3)))
prev.save(os.path.join(OUT, "Preview", "Vorschau_Survival_Kacheln.png"))
print("Survival-Kacheln erzeugt:", [c[0] for c in CHAINS])
