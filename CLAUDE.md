# DUSK_BELL / Nightward

## Pixel-Art: strikt nach dem Pixel Law
Bevor du IRGENDEIN Pixel-Asset erzeugst oder aenderst (Aseprite-MCP, Python-Generator, Tileset, Sprite, Item, UI, VFX):
1. Lies `Assets/_Project/Art/__STYLEBIBLE/ART_STYLE.md` (Palette, Raster, Outline, Schattierung).
2. Nutze nur `Nightward_Master.gpl` und `Assets/_Project/Art/__STYLEBIBLE/tools/style_lib.py` (Generatoren speichern ueber `save()`).
3. Pruefe jedes neue PNG mit `python3 Assets/_Project/Art/__STYLEBIBLE/tools/pixel_lint.py <Datei>`. Ohne E_-Fehler = fertig, sonst nicht.
Regeln nie aus dem Gedaechtnis anwenden und nie ohne Erlaubnis die Palette erweitern.

### Durchsetzung
- Jeder Generator unter `Art/**/_Quelle_Generator` importiert als erste Zeile `pixel_guard` (blockiert Verstoesse beim Speichern). Neue Generatoren: gleiche Zeile uebernehmen, Farben nur aus `style_lib.P`.
- `style_baseline.txt` ist eine Ratsche: nie erweitern, nur Eintraege entfernen, wenn Dateien konform werden.
- Git-Hook einmal aktivieren: `git config core.hooksPath .githooks`. Nie `--no-verify`.
- Ein Hook in `.claude/settings.json` meldet Verstoesse nach Bash/Write/Edit/Aseprite-Export. Melden, beheben, nicht umgehen.
