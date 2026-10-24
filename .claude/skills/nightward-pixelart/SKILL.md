---
name: nightward-pixelart
description: Verbindliches Pixel-Art-Regelwerk fuer Nightward/DUSK_BELL. IMMER laden, bevor ein Pixel-Asset erzeugt, geaendert oder gesnappt wird (Aseprite-MCP, Python-Generator, Tileset, Sprite, Item, UI, VFX, Portrait, Monster, Talisman). Enthaelt harte Regeln, Checkliste und Validator-Aufruf.
---

# Nightward Pixelart: Assets nur nach diesem Skill, immer validieren

Einzige Quelle der Wahrheit: `Assets/_Project/Art/__STYLEBIBLE/ART_STYLE.md` (zuerst lesen). Dieses Dokument ist nur Kurzfassung und Ablauf.

## Harte Regeln (Verstoss = nicht fertig)
- **Palette:** nur `Nightward_Master` (46 Farben, `__STYLEBIBLE/Nightward_Master.hex`). Kein reines Schwarz, keine Fremd-Hex-Werte, kein 8-stelliges Hex.
- **Alpha:** nur 0 oder 255. Kein Anti-Aliasing, kein Glow per Alpha.
- **Raster:** Masse Vielfache von 16. tile 32x32, char-Zelle 32x48 (breit 48x48), item 16/32, portrait 64x64.
- **Outline:** 1 px dunkle Palettenfarbe, aussen geschlossen, innen nur zur Formtrennung. Baeume, Gras, Boden-Tiles ohne Outline.
- **Schattierung:** max. 3 Stufen pro Material (Schatten kuehl-violett, Basis, Licht warm-gelb), Licht oben-links, kein Dithering im Vordergrund, kein Rausch-Muster.
- **Farb-Rollen:** Talisman-Farben (#6fd3e6 #a8f0ff #2b6b8a) nur in Talisman-/Schutz-Assets, Monster-Farben (Monsterauge #d64a6a, Blut #8a1f3d) nur in Monster-/Blut-/UI-Assets; sonst max. 10 % Akzent. Wasser-Blau nur fuer Wasser (Sichtpruefung). Grinsen nur in Zaehne-Farbe #f2ead8 und Monsterauge #d64a6a.
- **Monster:** gleiche Koerpergroesse und Gesichtsform wie Menschen, Grinsen ist das einzige Erkennungsmerkmal, im Raster eindeutig lesbar (2-3 px).

## Ablauf (Checkliste)
1. [ ] `ART_STYLE.md` gelesen, Klasse und Mass festgelegt.
2. [ ] Anker angesehen: `__STYLEBIBLE/Anker/Anker_Vorschau.png` (Tile, Bewohner, Monster). Neues Asset muss daneben passen.
3. [ ] Erzeugen:
   - Aseprite-MCP: `create_canvas` -> `load_palette_file` (`__STYLEBIBLE/Nightward_Master.gpl`) -> `draw_rectangle`/`draw_pixels` nur mit Hex aus der Palette -> `export_sprite` PNG. Der MCP erzwingt die Palette NICHT.
   - Python: `from style_lib import P, ramp, new, add_outline, snap_image, save`; speichern nur ueber `save()`; Generator-Datei beginnt mit `import pixel_guard` (siehe bestehende Generatoren).
4. [ ] Validieren: `python3 Assets/_Project/Art/__STYLEBIBLE/tools/pixel_lint.py <Datei>`. E_-Fehler beheben (Palette, Alpha, Raster, Rolle). W_-Warnungen bewerten.
5. [ ] Sichtpruefung: 4x vergroessern, neben Anker legen. Outline, Schattenstufen, Licht oben-links, Silhouette.
6. [ ] Erst dann als fertig melden. Hooks (`art_gate`) pruefen zusaetzlich nach jedem Bash-/Write-/Aseprite-Aufruf.

## Verboten
Palette erweitern ohne Beschluss, `style_baseline.txt` erweitern, `git commit --no-verify`, `PIXEL_GUARD=warn`, Guard-Import entfernen, Anker aendern, Regeln aus dem Gedaechtnis statt aus `ART_STYLE.md` anwenden.

## Altbestand
Wird nie nebenbei angefasst. Eigener Schritt: `tools/snap_altbestand.py` (Trockenlauf, dann `--apply --pool auto`), danach `pixel_lint.py --write-baseline` (schrumpft die Baseline).

## Offene Regelfrage
Messung der Grinsen-Breite (2-3 px): noch nicht automatisiert, weil unklar ist, ob die Breite der Zahnreihe oder die Linienstaerke gemeint ist. Bis zur Klaerung per Sichtpruefung.
