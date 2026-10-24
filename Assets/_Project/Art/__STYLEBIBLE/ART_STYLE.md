# Nightward Pixel Law (ART_STYLE)

Einzige Wahrheit fuer ALLE neuen Pixel-Assets (Aseprite-MCP, Python-Generatoren, Handarbeit).
Ergaenzt die `Style-Bibel – Nightward.pdf` (Stimmung, Figuren, Licht). Bei Widerspruch gilt dieses Dokument.
Pruefung ist maschinell: `tools/pixel_lint.py`. Ein Asset ist erst fertig, wenn der Linter keine Fehler (E_) meldet.

## 1. Palette (gesperrt)
- Nur `Nightward_Master.gpl` / `.png` / `.hex` (46 Farben = 39 Bibel + 7 Welt: Wasser x5, Sumpf dunkel, Sumpf Licht).
- Keine andere Farbe, auch nicht fuer Effekte, Glow oder Schatten. Reines Schwarz #000000 gibt es nicht.
- Talisman-Blau nur fuer Talismane. Monster-Rot nur Zaehne + Monsterauge + Blut. Wasser-Blau nur fuer Wasser.
- Alt-Palette `Art/Palette.png` (40 Farben) ist Legacy. Nicht mehr verwenden.
- Palette erweitern nur per ausdruecklichem Beschluss des Users, dann in `tools/style_lib.py` (_MASTER) + `python3 style_lib.py`.

## 2. Raster und Groessenklassen
Alle Masse sind Vielfache von 16. Kein Skalieren, Drehen oder Mischen von Pixelgroessen (1 Sprite-Pixel = 1 Bildpixel).
| Klasse | Mass | Hinweis |
|---|---|---|
| tile | Vielfache von 32x32 | Tilesets, Boden, Waende |
| nature | Vielfache von 16 | Baeume, Buesche, Gras |
| object | Vielfache von 16 | Props, Moebel, Hausteile |
| item | 16x16 oder 32x32 | Inventar |
| char | Zelle 32x48 (breit 48x48), Koerper 40-44 px hoch | Fuss-Pivot unten-Mitte, alle Frames gleiche Zelle |
| portrait | 64x64 pro Frame | |
| ui / vfx | Vielfache von 16 | |
Kein 22x22, 7x7, 56x56, 40x112 usw.

## 3. Outline
- 1 px, dunkle Farbe aus {outline_dunkel, outline_nacht, schatten_violett_dunkel, nachtblau_dunkel, wald_dunkel, erde_dunkel, sumpf_dunkel}.
- Aussen immer geschlossen (kein Loch), innen nur zur Formtrennung ("selective outline"). Innenkanten duerfen heller sein als die Aussenkante.
- Ausnahmen ohne Outline: Boden-/Wand-Tiles, Gras, Baeume und Buesche (Linter prueft dort nicht).
- Keine Doppel-Outline, keine 2-px-Linien, keine Outline in Schwarz.

## 4. Schattierung und Licht
- Pro Material 3 Stufen: Schatten (kuehl-violett), Basis, Licht (warm-gelb). Rampen in `style_lib.RAMPS`.
- Licht immer von OBEN-LINKS. Schatten fallen nach unten-rechts.
- Kein Dithering im Vordergrund (nur Nebel, Himmel, weiche Uebergaenge). Kein Rausch-/Noise-Muster als Textur.
- Kein Pillow-Shading (Licht nicht vom Rand zur Mitte), keine Gradient-Fuellung, kein Blur.
- Lichtquellen bleiben hell (Laterne/Feuer orange, Fenster warm-gelb, Talisman kuehl-blau). Kein Alpha-Glow, Glow nur als Pixel-Ringe.

## 5. Saubere Pixel
- Keine Anti-Aliasing-Kanten, keine halbtransparenten Pixel (Alpha nur 0 oder 255).
- Linien: gleichmaessige Stufen (2-2-2 oder 3-3), keine "Jaggies" (einzelne Stolperpixel).
- Moeglichst wenige Einzelpixel; Flaechen als zusammenhaengende Cluster.
- Silhouette zuerst lesbar machen. Figuren: eigenes markantes Element (Hut, Tuch, Werkzeug). Monster = Menschengestalt + Grinsen 2-3 px breit.

## 6. Arbeitsablauf (Pflicht)
1. Vor jeder Art-Arbeit diese Datei lesen. Klasse und Mass festlegen (Abschnitt 2).
2. Aseprite-MCP: `create_canvas` mit RGB, `load_palette_file` -> `__STYLEBIBLE/Nightward_Master.gpl`, Anti-Aliasing aus, nur Palettenfarben, auf 1-px-Leinwandrand Platz fuer Outline lassen.
   ACHTUNG (getestet 2026-10-24): Der MCP erzwingt die Palette NICHT. `draw_*` akzeptiert jedes Hex und Alpha-Hex (#RRGGBBAA). Immer nur Hex-Werte aus `Nightward_Master.hex`, nie ein 8-stelliges Hex. Der Linter ist die einzige Absicherung. Export-Kette: `create_canvas` -> `load_palette_file` -> `draw_rectangle`/`draw_pixels` -> `export_sprite` (.png) -> `pixel_lint.py`. Tools mit Kantenglaettung (draw_circle, draw_ellipse, draw_text, rotate, resize) nur nutzen, wenn danach der Linter sauber ist.
   Python: `from style_lib import P, ramp, new, add_outline, snap_image, save`; Speichern IMMER ueber `save()` (bricht bei Verstoss ab).
3. Export als PNG, dann: `python3 Assets/_Project/Art/__STYLEBIBLE/tools/pixel_lint.py <Datei>`. E_-Fehler beheben, W_-Warnungen bewerten.
4. Vorschau 4x ansehen (nearest) und neben ein Referenz-Asset (Anker: Hauptfigur_Frau, Amboss, Monster_Mann_Grinsen) halten: Stil muss zusammenpassen.
5. Unity: Filter Point (no filter), Kompression None, Pixels Per Unit 32.

## 7. Linter-Codes
E_PALETTE Farbe ausserhalb Master | E_ALPHA Halbalpha | E_RASTER falsches Mass | E_LESEN Datei defekt
W_OUTLINE Aussenkante <85% Outline-Farbe | W_NOISE >10% Einzelpixel | W_DITHER >2% Schachbrett

## 8. Altbestand
Rund 2000 PNGs vor diesem Regelwerk. Sie sind NICHT konform (Stand 2026-10-24: ~90% E_PALETTE). Angleichen ist ein eigener Schritt
(`snap_image` + Abweichungsliste via `pixel_lint.py --report`), nie stillschweigend beim Bearbeiten anderer Dinge.
Neue/ueberarbeitete Assets muessen konform sein.

## 9. Durchsetzung (automatisch, nicht verhandelbar)
Vier Schichten stellen sicher, dass kein Asset am Regelwerk vorbeikommt:
1. **Guard in jedem Generator** (`tools/pixel_guard.py`): die erste Zeile jedes `_Quelle_Generator/*.py` importiert ihn. Er faengt jedes `Image.save()` auf PNGs unter `Art/` ab. Eine Datei, die nicht in `style_baseline.txt` steht, muss E_-fehlerfrei sein, sonst `PixelLawError` und die Datei wird nicht geschrieben.
   Neuer Generator: erste Zeile aus einem bestehenden Generator kopieren (Pfad zu `tools` anpassen) und Farben nur aus `style_lib.P` holen.
2. **Baseline mit Ratsche** (`style_baseline.txt`): Liste bekannter Altlasten (E_-Fehler). Sie darf nur schrumpfen. Wird eine Altlast konform, aus der Liste entfernen: `python3 tools/pixel_lint.py --write-baseline <Art-Ordner>` (bricht ab, wenn die Liste wachsen wuerde).
3. **Git-Hook** (`.githooks/pre-commit`): prueft gestagte PNGs unter `Art/` mit `art_gate.py --staged`. Einmal pro Klon aktivieren: `git config core.hooksPath .githooks`.
4. **Claude-Hook** (`.claude/settings.json`): nach Bash-, Write-, Edit- und Aseprite-Export-Aufrufen prueft `art_gate.py --worktree` geaenderte PNGs und meldet Verstoesse sofort zurueck.
Verboten: Baseline erweitern, `--no-verify`, `PIXEL_GUARD=warn` dauerhaft, den Guard-Import entfernen oder Image.save umgehen.
Grenze: der Linter prueft Palette, Alpha, Raster und per Heuristik Outline/Rauschen/Dithering. Formensprache, Schattierung und Licht oben-links bleiben Sichtpruefung (Abschnitt 6, Schritt 4).
