# Nightward Pixel Law (ART_STYLE)

Einzige Wahrheit fuer ALLE neuen Pixel-Assets (Aseprite-MCP, Python-Generatoren, Handarbeit).
Ergaenzt die `Style-Bibel – Nightward.pdf` (Stimmung, Figuren, Licht). Bei Widerspruch gilt dieses Dokument.
Pruefung ist maschinell: `tools/pixel_lint.py`. Ein Asset ist erst fertig, wenn der Linter keine Fehler (E_) meldet.

## 1. Palette (gesperrt)
- Nur `Nightward_Master.gpl` / `.png` / `.hex` (46 Farben = 39 Bibel + 7 Welt: Wasser x5, Sumpf dunkel, Sumpf Licht).
- Keine andere Farbe, auch nicht fuer Effekte, Glow oder Schatten. Reines Schwarz #000000 gibt es nicht.
- Farb-Rollen (Linter `E_ROLLE`): Talisman-Farben nur in Talisman-/Schutz-/Baukasten-/Icon-/VFX-Assets, Monsterauge und Blut nur in Gast-/Hausfrau-/Monster-/Blut-/UI-/VFX-Assets; ausserhalb hoechstens 10 % Akzent. Wasser-Blau nur fuer Wasser (Sichtpruefung). Grinsen nur in Zaehne-Farbe #f2ead8 und Monsterauge #d64a6a. Regeln in `style_lib.ROLE_RULES`.
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
4. Vorschau 4x ansehen (nearest) und neben die Anker legen (`__STYLEBIBLE/Anker/`: Anker_Tile, Anker_Bewohner, Anker_Monster, Vorschau in Anker_Vorschau.png): Stil muss zusammenpassen.
5. Unity: Filter Point (no filter), Kompression None, Pixels Per Unit 32.

## 7. Linter-Codes
E_PALETTE Farbe ausserhalb Master | E_ALPHA Halbalpha | E_RASTER falsches Mass | E_ROLLE Sonderfarbe im falschen Asset | E_LESEN Datei defekt
W_OUTLINE Aussenkante <85% Outline-Farbe | W_NOISE >10% Einzelpixel | W_DITHER >2% Schachbrett
W_DETAIL zu wenig Detaildichte/Kleinteile/Farben (Abschnitt 11) | W_PROPORTION Figurenhoehe oder Breite/Hoehe ausserhalb der Referenzen

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

## 10. Skill und Anker
- Projekt-Skill `.claude/skills/nightward-pixelart/SKILL.md`: Kurzfassung der harten Regeln, Checkliste und Validator-Aufruf. Wird bei jedem Asset-Auftrag geladen. Einzige Quelle bleibt dieses Dokument.
- `__STYLEBIBLE/Anker/`: drei Referenz-Kopien (Tile, Bewohner, Monster). Nicht aendern ohne Beschluss des Users.
- Offen: Messung der Grinsen-Breite (2-3 px) ist nicht automatisiert, bis geklaert ist, ob die Breite der Zahnreihe oder die Linienstaerke gemeint ist.

## 11. Detail, Proportion, Wirkung (aus den Referenzfiguren abgeleitet)
Technisch saubere Pixel und passende Kennzahlen sind nicht genug (die Kennzahlen lassen sich mit verstreuten Punkten "erfuellen", ohne dass die Figur gut aussieht: Testfrau v2 hat das gezeigt, siehe Abschnitt 12). Sheriff, Mara, Can, Veronica, Elenora und der Anker-Bewohner wirken, weil sie diese Regeln erfuellen.
Ein Sprite, das nur Abschnitt 1-5 erfuellt, aber hier durchfaellt, ist NICHT fertig.

**Messwerte der Referenzen** (Frame "S", Linter `W_DETAIL`/`W_PROPORTION`):
| Kennzahl | Referenzen | Soll Figur | Soll Portrait |
|---|---|---|---|
| Cluster je 100 deckende Pixel (4er-Flaechen gleicher Farbe) | 13.0-26.3, Median 17.6 | >= 13 | >= 8 |
| Anteil Kleinteile (Cluster <= 2 px) | 30-68 %, Median 50 | >= 35 % | >= 60 % |
| Farben im Frame | 12-22 | 10-24 | 11-20 |
| Figurenhoehe | 42-48 px | 40-48 | - |
| Breite / Hoehe | 0.38-0.53 | 0.36-0.56 | - |
| Kopf (Haar/Hut bis Kinn) | 32-36 % der Hoehe | 30-37 % (Sichtpruefung) | - |
| Beine (Hueftlinie bis Sohle) | 27-36 % | <= 38 % (Sichtpruefung) | - |

**Wirkungsregeln (Sichtpruefung, jede Figur):**
1. **Silhouette-Merkmal:** eine grosse, sofort lesbare Form (Hut, Haarvolumen, Umhaengetasche, Kragen). Silhouette einfarbig gefuellt muss die Figur erkennbar machen.
2. **Wertgruppen:** Kopf/Haare, Oberkoerper, Hose, Schuhe unterscheiden sich in Helligkeit UND Farbfamilie (Sheriff: dunkler Mantel, helle Hose, dunkle Stiefel). Nie alles im selben Blau/Braun.
3. **Zubehoer:** mindestens 3 erkennbare Teile (Knoepfe, Guertel mit Schnalle, Tasche mit Riemen, Stirnband, Brille, Abzeichen, Schal).
4. **Akzentpunkte:** 3-10 helle Einzelpixel/Kleinstflaechen (Glanzlicht auf Haar, Knopf, Schnalle, Lederkante) in warmer Lichtfarbe. Sie liefern die Kleinteile, kein Rauschen.
5. **Material statt Flaeche:** Falten (dunkle 1-px-Linien), Naehte, Saeume, Kniefalten, Muster (Karo, Strick) statt einer glatten Rechteckflaeche.
6. **Gesicht:** Augen mit Weiss und Pupille oder dunklem Lid, Brauen, Nasenschatten, Lippen. Mimik muss bei 1x lesbar sein. Portrait: Lid, Brauenschatten, Nasenschatten, Wangen/Kinn-Schatten, Kragen mit Struktur, Haare mit Glanzpunkten.
7. **Haende, Schuhe:** sichtbare Haende (Daumen/Manschette) und Schuhe mit Sohle und Glanzlicht.
8. **Hierarchie:** das meiste Detail im Gesicht, an Haenden und am Zubehoer; Flaechen (Mantelruecken, Hose) ruhig.

**Tonlaeufe:** Schatten kuehl-violett, Licht warm. Akzentglanz (1-2 zusaetzliche helle Pixel pro Material) zaehlt nicht als vierte Schattenstufe.
**Vorgehen:** erst Silhouette in 2 Tonwerten, dann Wertgruppen, dann Zubehoer, dann Akzente. Vor "fertig" neben `Anker_Vorschau.png` und dem Sheriff legen (`Characters/BULUT SHERIFF/ANIMATIONS_8DIR/bulut_stand_8dir.png`).

## 12. Form und Handschrift (Lehre aus Testfrau v1/v2, Pflicht vor jedem Charakter)
Kennzahlen (Abschnitt 11) pruefen nur Dichte, nicht Form. Figuren, die aus Rechtecken, Streifenschatten und verstreuten Glanzpunkten zusammengesetzt sind,
wirken "hingerotzt", auch wenn der Linter nichts meldet. So bauen die guten Figuren (Mara, Sheriff, Can, Anker):
1. **Rundungen statt Rechtecken.** Gesicht = Ei/Oval (Portrait ca. 22x28, Kinn verjuengt), Kopf/Haare gerundet, Schultern gerundet. Keine geraden 45-Grad-Dreiecke (Schultern), keine Eimerkoepfe.
2. **Kurvenschattierung.** Licht oben-links als Verlauf ueber die Form (Normale mal Lichtrichtung in 3 Baendern), nicht 1-px-Streifen an den Rechteckkanten.
3. **Chibi-Proportion im Sprite:** Kopf mit Haar ca. 35 % der Figurenhoehe (16 von 46 Zeilen), Gesicht klein (ca. 8x8), Haar rahmt es breit (Haarbreite ~ doppelte Gesichtsbreite), Beine kurz (ca. 20-25 %), Mantel/Kleid/Tasche nehmen den Rumpf ein. Lange duenne Beine und kleiner Kopf sehen generisch aus.
4. **Haar:** lange Haare fallen als Straehnen VOR die Schultern (verdecken die Schulterlinie, geben senkrechte Linien); Rim-Light-Akzent in warmer Farbe nur am Rand.
5. **Gesicht:** Sprite: Augen sind 2 px breit und 2 Zeilen hoch: oben dunkler Lidstrich (outline_dunkel), darunter die Irisfarbe (z.B. stoff_blau_hell fuer blaue Augen). KEINE Braue und KEIN Schatten darunter (drei dunkle Zeilen ergeben einen fetten schwarzen Block), aber auch nicht nur ein reiner Strich: ohne Irisfarbe sind die Augen leblos. Dazu Wangen-Akzent und Lippen 2 px. Portrait: Auge 6x4 (Lid, Weiss, Iris, Pupille, Lichtpunkt), geschwungene Brauen, Nasenschatten, Lippen mit Glanz. Augenfarbe der Figur ist Teil des Designs und muss im Sprite UND im Portrait stimmen.
6. **Zubehoer am Koerper statt auf der Flaeche:** Taschen, Riemen, Schal, Spangen, Ohrstecker sitzen an Konturen und aendern die Silhouette.
7. **Arbeitsweise:** nie aus Rechtecken addieren. Zuerst Referenz als Pixelraster ansehen (`pixel_lint` + Raster-Ausdruck), Konstruktion der Referenz verstehen (Zeilenbreiten, Haar-/Gesichtsverhaeltnis), dann Formen mit Kurven zeichnen, dann Details. Danach neben die Referenz legen und ehrlich vergleichen; "Linter gruen" ist nicht "fertig".
8. **Koepfe von Hand:** Gesichter/Koepfe der Sprites als Raster-Schablone (Zeichen je Pixel) zeichnen und pro Ansicht eigens (S, SW, W, N), nicht aus einer Vorlage abgeleitet.
9. **Familien-Vergleich (Pflicht):** Jede neue Figur wird vor "fertig" mit ALLEN bestehenden Charakteren verglichen, Sprite-Koepfe (8x) und Portraits (3x) nebeneinander. Die Familie hat: Haar/Hut als anliegende Kappe (1-2 px breiter als das Gesicht, Seitenhaar endet am Kiefer), Augen auf ca. 60 % der Kopfhoehe, Gesicht 8-10 px breit, Portrait-Gesicht 28-38 px breit (Hautanteil 14-19 % des Bildes), Schraffur-Schattierung mit gezackter Kante statt weicher Verlaeufe, kein Glitzer/Streupunkte, keine rosa Wangenflecken, kleiner Mund. Abweichung = nicht fertig, auch bei gruenem Linter (Lehre Testfrau v3).
10. **Haar-Kappe:** Kappe hoechstens 6 Zeilen hoch (Sprite), Gesicht beginnt frueh. Eine hohe, schmale Haarkuppe mit dem Gesicht ganz unten wirkt wie eine Kugelspitze.
