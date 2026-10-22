---
name: hauptfiguren-kampf-animationen
description: "Kampf-/Run-Animationen der Hauptfiguren Mann/Frau werden per Python-Generator erzeugt, nicht von Hand in Aseprite gemalt"
metadata:
  node_type: memory
  type: project
  originSessionId: 6fdc3b00-d5e9-4615-aa79-37ca5c3a4908
  modified: 2026-10-21T19:49:40.127Z
---

Run, Sprint, Dodge (Ausfallschritt, keine Rolle mehr; altes gen_dodge.py veraltet), Boxen (punch1-3), Messer (knife1/2), Baseballschlaeger (bat), Pistole (shoot) + Projektil entstehen aus
`Art/Characters/Hauptfiguren/_Quelle_Generator/gen_hauptfiguren_combat.py` (baut auf gen_hauptfiguren.py auf, 56x56, 8 Richtungen,
Zeilen S,SW,W,NW,N,NE,E,SE). Projektil: `gen_projektil.py` -> `Art/VFX/Projektil/`. `.aseprite` werden per Aseprite-MCP-Lua aus den PNG-Sheets
zusammengesetzt (`Hauptfigur_<Name>_Kampf.aseprite`, Tags `<anim>_<Dir>`). Muendungspositionen: `Hauptfiguren/kampf_muendung.json`.

Stand 2026-10-21 spaet: Run/Sprint-Arme sind ansichtsabhaengig (`run_hand` im Generator, Arme von vorn/hinten am Koerper, Beine in Schraegansichten per `diag`-Faktor entkreuzt). Eat/Drink (8 Frames, Brot/Flasche als `prop`-fx) kommen aus `gen_eatdrink.py`, Clips `eat_<Dir>`/`drink_<Dir>` + Controller-States per Unity-execute_code angelegt; Ausloeser `PlayerInventory.PlayUseAnimation` -> `PlayerActionAnimation.PlayTimed`. Die `.aseprite`-Kampfdateien wurden dafuer NICHT neu zusammengebaut (nur PNG-Sheets aktuell).
Fallstrick: Loop-Clips hatten `stopTime` = letzte Key-Zeit + 1 Frame (Dup-Schlusskey) -> letztes Bild haengte jede Runde doppelt; fuer neue Clips stopTime = Zeit des Dup-Keys setzen.

**Why:** Aenderungen an Posen immer im Generator machen und neu erzeugen, sonst gehen Handkorrekturen im .aseprite beim naechsten Lauf verloren.
**How to apply:** Nach Generator-Aenderung `python gen_hauptfiguren_combat.py`, dann `build_manifest.py` und die Lua-Zusammenbau-Schritte wiederholen. Unity-Slicing/Controller (`<anim>_<Dir>`-States) macht der Unity-Agent. Siehe [[scripts-untracked-in-git]].
**Gotcha:** Beim Aseprite-Zusammenbau Tags erst nach allen Frames anlegen (newFrame am Ende dehnt Tags aus). Rueckansichten (N/NW/NE) im Run/Sprint: Haende nach Tiefe sortieren (`sort_north`), nie auf den Ruecken legen.

**Stand 2026-10-22:** Rueckansichten (N/NW/NE) im Kampf: Haende nach Tiefe sortiert plus `FLARE` (seitlich ausgestellt), nie auf dem Ruecken. Neue Waffen-Anims (Generator `DRAWERS`/`ANIMS`): club, crowbar, chop (Axt), flail, machete1/2, rifle; Zuordnung ueber `ItemDef.attackAnim/attackCombo/attackSeconds/hitSeconds` (Katalog `.Always(...)` in ItemCatalog.cs), Clips baut `PlayerAnimationBuilder` (Specs ergaenzen, 14 fps, Dauer = Bilder/14). Schuesse zielen frei (`aimExact` in PlayerCombat), Figur nur 8 Richtungen.
[ALT, ersetzt] Icons neuer Waffen: `gen_waffen_icons.py`.
**Gotcha:** `python -I` findet gen_hauptfiguren nicht, mit `PYTHONPATH=.` laufen lassen. `to_img` erlaubt nur Palettenfarben.

**Stand 2026-10-22 (Import):** Aus `Art/_IMPORTED` (Waffen GUNS_V1.00, Essen Ghostpixxells_pixelfood) wurden Items: `gen_import_icons.py` baut die Icons (Waffen schraeg gedreht auf 32x32, Essen als `Items/Essen/Food_NNN_name.png`). Essen steht komplett in `Survival/Core/FoodTable.cs` (98 Speisen inkl. "_plated" mit Teller-Rest, 4 Geschirr), daraus ItemCatalog + SurvivalDefaults.FoodConsumables; bestehende Config-Assets mit Menue "Nightward/Survival/Fehlende Verbrauchsgueter ergaenzen" nachziehen. Neue Langwaffen-Anims shotgun/assault/sniper (`seq_longgun`). Rueckansicht-Fix: `clear_head` + `SIDE_SWAP_KINDS` (Schusshand im NW links) + Ellbogen nach innen (`elbow_flare=-0.6`).
**Gotcha:** `execute_code` (CodeDom, C# 6) kennt keine lokalen Funktionen, `compiler: roslyn` ist nicht installiert: Func-Lambdas nutzen.

**Stand 2026-10-22 (Kleidung):** 30 Stuecke (10 Oberteile/Hosen/Schuhe), Daten+Icons aus `gen_kleidung.py` -> `Art/Items/Kleidung/kleidung.json` (ItemCatalog liest es; Slots Clothing/Legs/Feet). Umfaerben zur Laufzeit: `PlayerOutfit` nutzt Masken `Resources/OutfitMasks/<Who>/<sheet>.png` (R=Bereich 1 Oberteil/2 Hose/3 Schuhe, G=Stufe), erzeugt mit `NW_MASK=1 python gen_hauptfiguren.py|gen_hauptfiguren_combat.py|gen_eatdrink.py <Ordner>` plus `mask_interact.py` (Heuristik). **Bei jeder neuen/geaenderten Animation die Masken neu erzeugen**, sonst bleibt die Figur dort ohne Kleidung. Sheets + Masken muessen lesbar sein (OutfitTextureImporter setzt Read/Write). Lauf (seq_run/sprint) hat Kniehub/Flugphase (`env`, `leg_dy`); neue Armwerte nur Seitenansicht, `alt=` fuer Diagonalen.

