"""Nightward Pixel Law - gemeinsame Bibliothek fuer ALLE Art-Generatoren.

Regelwerk: ../ART_STYLE.md  (einzige Wahrheit).  Jedes neue PNG laeuft vor dem
Speichern durch save(); Verstoesse (Palette, Halbalpha, Raster) brechen ab.

Nutzung in einem Generator:
    from style_lib import P, RAMPS, new, add_outline, snap_image, save
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(os.path.dirname(HERE))   # .../Art

# ---------------------------------------------------------------- Master-Palette
# 39 Style-Bibel-Farben + 7 Welt-Farben (Wasser, Sumpf). Gesperrt: nur per Beschluss erweitern.
_MASTER = [
    ("outline_dunkel", "1a1526"), ("outline_nacht", "2b2140"),
    ("schatten_violett_dunkel", "3d2e4a"), ("schatten_violett_mittel", "4f3d5c"), ("schatten_violett_hell", "6b5a7a"),
    ("nachtblau_dunkel", "1f2a3d"), ("nachtblau_mittel", "2c3e56"), ("nachtblau_hell", "3f5570"),
    ("mondlila_himmel", "e8e0f0"),
    ("erde_dunkel", "3b2a22"), ("holz_dunkel", "5c4033"), ("holz_mittel", "7a5a43"), ("holz_hell", "9c7a5a"),
    ("stroh_sand", "b89a72"),
    ("wald_dunkel", "1e3a2b"), ("wald_mittel", "2f5a3c"), ("gras", "4a7a4f"), ("gras_hell", "6e9a5e"),
    ("blattlicht", "9ab87a"),
    ("stein_dunkel", "4a4550"), ("stein_mittel", "6e6a74"), ("stein_hell", "9a95a0"),
    ("haut_schatten", "5e3d33"), ("haut_mittel", "8c5f4d"), ("haut_hell", "d19a7a"),
    ("stoff_rot_gedaempft", "7a2e3a"), ("akzent_rose", "c4636b"),
    ("stoff_blau_gedaempft", "3a4a7a"), ("stoff_blau_hell", "6b7fb8"),
    ("licht_warmgelb", "ffd27a"), ("laterne_orange", "ffa550"), ("feuer_glut", "e8733a"),
    ("kerzenweiss", "fff1c9"),
    ("talisman_schutz", "6fd3e6"), ("talisman_highlight", "a8f0ff"), ("talisman_dunkel", "2b6b8a"),
    ("zaehne_grinsen", "f2ead8"), ("monsterauge", "d64a6a"), ("blut_dunkel", "8a1f3d"),
    # Erweiterung Welt (Fluss, Sumpf)
    ("wasser_tief", "23336b"), ("wasser_dunkel", "2f4f8f"), ("wasser_mittel", "3f72b0"),
    ("wasser_hell", "5b99c4"), ("wasser_schaum", "8cc4d6"),
    ("sumpf_dunkel", "243b3f"), ("sumpf_licht", "cde06a"),
]


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


P = {n: _rgb(h) for n, h in _MASTER}          # Name -> (r,g,b)
NAMES = {v: k for k, v in P.items()}          # (r,g,b) -> Name
MASTER_RGB = frozenset(P.values())
TRANSPARENT = (0, 0, 0, 0)

# Outline-Farben: nie Schwarz, immer farbig-dunkel
OUTLINE_COLORS = frozenset(P[n] for n in ("outline_dunkel", "outline_nacht", "schatten_violett_dunkel",
                                          "nachtblau_dunkel", "wald_dunkel", "erde_dunkel", "sumpf_dunkel"))
OUTLINE = P["outline_dunkel"]

# Schattenrampen: (Schatten, Basis, Licht). Max. 3 Stufen pro Material. Licht oben-links.
RAMPS = {
    "holz":      ("holz_dunkel", "holz_mittel", "holz_hell"),
    "laub":      ("wald_dunkel", "wald_mittel", "gras"),
    "gras":      ("wald_mittel", "gras", "gras_hell"),
    "blatt":     ("gras", "gras_hell", "blattlicht"),
    "stein":     ("stein_dunkel", "stein_mittel", "stein_hell"),
    "haut":      ("haut_schatten", "haut_mittel", "haut_hell"),
    "violett":   ("schatten_violett_dunkel", "schatten_violett_mittel", "schatten_violett_hell"),
    "nachtblau": ("nachtblau_dunkel", "nachtblau_mittel", "nachtblau_hell"),
    "stoff_rot": ("blut_dunkel", "stoff_rot_gedaempft", "akzent_rose"),
    "stoff_blau": ("nachtblau_mittel", "stoff_blau_gedaempft", "stoff_blau_hell"),
    "sand":      ("holz_hell", "stroh_sand", "kerzenweiss"),
    "feuer":     ("feuer_glut", "laterne_orange", "licht_warmgelb"),
    "talisman":  ("talisman_dunkel", "talisman_schutz", "talisman_highlight"),
    "wasser_tief": ("wasser_tief", "wasser_dunkel", "wasser_mittel"),
    "wasser":    ("wasser_dunkel", "wasser_mittel", "wasser_hell"),
    "wasser_hell": ("wasser_mittel", "wasser_hell", "wasser_schaum"),
    "sumpf":     ("sumpf_dunkel", "wald_mittel", "sumpf_licht"),
    "erde":      ("erde_dunkel", "holz_dunkel", "holz_mittel"),
}
LIGHT_DIR = (-1, -1)   # Licht kommt von oben-links

# Farb-Rollen: Sonderfarben duerfen nur in passenden Assets flaechig vorkommen.
# Ausserhalb der erlaubten Pfad-Stichworte gilt ein Akzent-Limit (Anteil an den deckenden Pixeln).
ROLE_RULES = [
    ("Talisman-Farben", frozenset(P[n] for n in ("talisman_schutz", "talisman_highlight", "talisman_dunkel")),
     ("talisman", "schutz", "baukasten", "icon", "vfx", "tuerspion"), 0.10),
    ("Monster-Farben (Monsterauge, Blut)", frozenset((P["monsterauge"], P["blut_dunkel"])),
     ("gast", "hausfrau", "monster", "blut", "hud", "icon", "warnung", "tuerspion", "vfx", "spalt", "grin"), 0.10),
]


def ramp(name):
    """(schatten, basis, licht) als RGB-Tupel."""
    return tuple(P[n] for n in RAMPS[name])


# ---------------------------------------------------------------- Raster-Klassen
# kind -> (Breite teilbar durch, Hoehe teilbar durch, Outline noetig)
KINDS = {
    "tile":     (32, 32, False),   # Tilesets, Boden, Wand-Tiles
    "nature":   (16, 16, False),   # Baeume, Gras, Buesche: Outline optional
    "object":   (16, 16, True),    # Props, Moebel, Gebaeude-Teile
    "item":     (16, 16, True),    # Inventar-Items 16x16 / 32x32
    "char":     (16, 48, True),    # Figuren/Tiere: Zelle 32x48 (breit 48x48), Koerper 40-44 px hoch
    "portrait": (64, 64, True),    # Dialog-Portraits 64x64
    "ui":       (16, 16, False),
    "vfx":      (16, 16, False),
}

SKIP_DIRS = ("_IMPORTED", "_Quelle_Generator", "__STYLEBIBLE", "_Backup")
SKIP_NAMES = ("Vorschau", "Uebersicht", "Palette")


def guess_kind(path):
    p = "/" + path.replace("\\", "/").lower()
    if "portrait" in p: return "portrait"
    if "/ui/" in p: return "ui"
    if "/vfx/" in p: return "vfx"
    if "/items/" in p: return "item"
    if "/characters/" in p or "/tiere/" in p: return "char"
    if "tileset" in p or "/tileassets/" in p or "/terrain" in p: return "tile"
    if any(k in p for k in ("baum", "fichte", "busch", "gras", "farn", "riesenbaum", "pilz")): return "nature"
    return "object"


# ---------------------------------------------------------------- Pruefung
def check_image(img, kind="object", dither_max=0.02, noise_max=0.10, path=None):
    """-> (fehler, warnungen). Fehler = Asset ist NICHT fertig. path (relativ zu Art/) aktiviert die Farb-Rollen-Regel."""
    err, warn = [], []
    im = img.convert("RGBA")
    w, h = im.size
    px = im.load()
    cw, ch, need_outline = KINDS[kind]
    if w % 16 or h % 16:
        err.append(f"E_RASTER {w}x{h}: Masse muessen Vielfache von 16 sein")
    elif kind != "ui" and kind != "vfx" and (w % cw or h % ch):
        err.append(f"E_RASTER {w}x{h}: Klasse '{kind}' braucht Vielfache von {cw}x{ch}")
    bad_pal, semi = {}, 0
    opaque = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if a != 255:
                semi += 1
                continue
            opaque += 1
            if (r, g, b) not in MASTER_RGB:
                bad_pal[(r, g, b)] = bad_pal.get((r, g, b), 0) + 1
    if semi:
        err.append(f"E_ALPHA {semi} Halbtransparente Pixel (nur Alpha 0 oder 255)")
    if bad_pal:
        top = sorted(bad_pal.items(), key=lambda kv: -kv[1])[:3]
        n = sum(bad_pal.values())
        err.append("E_PALETTE %d Pixel / %d Farben ausserhalb Master-Palette, z.B. %s" %
                   (n, len(bad_pal), ", ".join("#%02x%02x%02x(%d)" % (*c, k) for c, k in top)))
    if not opaque:
        return err, warn
    if path:
        low = "/" + path.replace("\\", "/").lower()
        counts = {}
        for y in range(h):
            for x in range(w):
                if px[x, y][3] == 255:
                    c = px[x, y][:3]
                    counts[c] = counts.get(c, 0) + 1
        for label, cols, allowed, cap in ROLE_RULES:
            share = sum(n for c, n in counts.items() if c in cols) / opaque
            if share > cap and not any(k in low for k in allowed):
                err.append(f"E_ROLLE {label} {int(share * 100)}% in diesem Asset (ausserhalb {'/'.join(allowed[:3])}... max {int(cap * 100)}%)")

    def op(x, y):
        return 0 <= x < w and 0 <= y < h and px[x, y][3] == 255

    # Outline: aeussere Kantenpixel muessen dunkle Outline-Farben sein
    if need_outline:
        edge = dark = 0
        for y in range(h):
            for x in range(w):
                if px[x, y][3] == 255 and not all(op(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    edge += 1
                    if px[x, y][:3] in OUTLINE_COLORS:
                        dark += 1
        if edge and dark / edge < 0.85:
            warn.append(f"W_OUTLINE nur {100 * dark // edge}% der Aussenkante ist Outline-Farbe (Soll >=85%)")
    # Noise (einzelne Pixel) und Dithering (Schachbrett)
    iso = chk = 0
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 255:
                continue
            c = px[x, y][:3]
            nb = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            if not any(op(*n) and px[n][:3] == c for n in nb):
                iso += 1
            if all(op(*n) and px[n][:3] != c for n in nb) and \
               all(op(x + dx, y + dy) and px[x + dx, y + dy][:3] == c for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1))):
                chk += 1
    if iso / opaque > noise_max:
        warn.append(f"W_NOISE {100 * iso // opaque}% Einzelpixel (Soll <={int(noise_max * 100)}%): Rausch-Textur?")
    if chk / opaque > dither_max:
        warn.append(f"W_DITHER {100 * chk // opaque}% Schachbrett-Pixel: Dithering nur fuer Nebel/Himmel")
    return err, warn


# ---------------------------------------------------------------- Werkzeuge
def new(w, h):
    """Leere RGBA-Leinwand (transparent)."""
    return Image.new("RGBA", (w, h), TRANSPARENT)


def _dist(a, b):
    # leichte Gewichtung: Gruen zaehlt mehr (wahrgenommene Helligkeit)
    return 2 * (a[0] - b[0]) ** 2 + 4 * (a[1] - b[1]) ** 2 + 3 * (a[2] - b[2]) ** 2


# Snap-Pools: wohin Fremdfarben abgebildet werden duerfen. Verhindert z.B. kuehlen Stein -> Wasser-Blau.
_SPECIAL = ("wasser", "talisman", "monsterauge", "blut", "sumpf_licht")
POOLS = {
    "allgemein": frozenset(v for k, v in P.items() if not k.startswith(_SPECIAL)),
    "wasser":    frozenset(v for k, v in P.items() if not k.startswith(tuple(x for x in _SPECIAL if x != "wasser"))),
    "sumpf":     frozenset(v for k, v in P.items() if not k.startswith(tuple(x for x in _SPECIAL if x != "sumpf_licht"))),
    "alle":      MASTER_RGB,
    "auto":      MASTER_RGB,   # Sonderfall, siehe snap(): Wasser nur fuer gesaettigtes Blau
}
_SNAP_CACHE = {}


def snap(rgb, pool="allgemein"):
    """Naechste Farbe des Pools (Standard: allgemein = ohne Wasser/Talisman/Monster/Sumpf-Licht).
    Farben, die schon in der Master-Palette liegen, bleiben unveraendert."""
    rgb = tuple(rgb[:3])
    if rgb in MASTER_RGB:
        return rgb
    key = (rgb, pool)
    if key not in _SNAP_CACHE:
        use = pool
        if pool == "auto":   # gesaettigte Blautoene duerfen auf Wasser, graue/neutrale Toene nie
            r, g, b = rgb
            use = "wasser" if (b > r + 20 and b >= g and (max(rgb) - min(rgb)) / max(max(rgb), 1) > 0.30) else "allgemein"
        _SNAP_CACHE[key] = min(POOLS[use], key=lambda m: _dist(m, rgb))
    return _SNAP_CACHE[key]


def snap_image(img, pool="allgemein", alpha_cut=128):
    """Alle Pixel auf Master-Palette (Pool), Alpha hart auf 0/255 (Schwelle alpha_cut)."""
    im = img.convert("RGBA")
    out = new(*im.size)
    s, d = im.load(), out.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = s[x, y]
            if a >= alpha_cut:
                d[x, y] = (*snap((r, g, b), pool), 255)
    return out


def add_outline(img, color=OUTLINE, diagonal=False):
    """1 px Aussen-Outline (4er-Nachbarschaft; diagonal=True fuer 8er). Veraendert Groesse nicht:
    Leinwand muss 1 px Rand haben."""
    im = img.convert("RGBA")
    s = im.load()
    out = im.copy()
    d = out.load()
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (-1, -1), (1, -1), (-1, 1)] if diagonal else [])
    for y in range(im.height):
        for x in range(im.width):
            if s[x, y][3] == 0 and any(0 <= x + dx < im.width and 0 <= y + dy < im.height and
                                       s[x + dx, y + dy][3] == 255 for dx, dy in steps):
                d[x, y] = (*color, 255)
    return out


def save(img, path, kind=None, strict=True):
    """Prueft gegen das Regelwerk und schreibt das PNG. strict -> Fehler werfen ValueError."""
    kind = kind or guess_kind(path)
    ap = os.path.abspath(str(path))
    rel = ap[len(ART) + 1:] if ap.startswith(ART + os.sep) else None
    err, warn = check_image(img, kind, path=rel)
    for m in warn:
        print(f"  [warn] {os.path.basename(path)}: {m}")
    if err and strict:
        raise ValueError(f"{path} ({kind}) verletzt Pixel Law:\n  " + "\n  ".join(err))
    img.convert("RGBA").save(path)
    return err, warn


def write_palette_files(outdir=None):
    """Erzeugt Nightward_Master.gpl / .png / .hex neben ART_STYLE.md."""
    outdir = outdir or os.path.dirname(HERE)
    with open(os.path.join(outdir, "Nightward_Master.gpl"), "w") as f:
        f.write("GIMP Palette\nName: Nightward Master\nColumns: 8\n#\n")
        for n, h in _MASTER:
            r, g, b = _rgb(h)
            f.write(f"{r:3d} {g:3d} {b:3d}\t{n} #{h}\n")
    with open(os.path.join(outdir, "Nightward_Master.hex"), "w") as f:
        f.write("\n".join(h for _, h in _MASTER) + "\n")
    strip = new(len(_MASTER), 1)
    for i, (_, h) in enumerate(_MASTER):
        strip.putpixel((i, 0), (*_rgb(h), 255))
    strip.save(os.path.join(outdir, "Nightward_Master.png"))
    # Vorschau 8 Spalten, 16 px Kacheln
    cols = 8
    rows = (len(_MASTER) + cols - 1) // cols
    pv = new(cols * 16, rows * 16)
    for i, (_, h) in enumerate(_MASTER):
        for yy in range(16):
            for xx in range(16):
                pv.putpixel(((i % cols) * 16 + xx, (i // cols) * 16 + yy), (*_rgb(h), 255))
    pv.save(os.path.join(outdir, "Nightward_Master_Vorschau.png"))


if __name__ == "__main__":
    write_palette_files()
    print(len(_MASTER), "Farben geschrieben")
