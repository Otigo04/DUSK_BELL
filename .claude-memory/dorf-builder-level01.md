---
name: dorf-builder-level01
description: Dorf in Level_01 wird per Editor-Skript DorfBuilder.cs gebaut; Opening-Szene überlagert Koordinaten beim Rendern
metadata:
  node_type: memory
  type: project
  originSessionId: 18218320-2434-4812-a314-fb808c0ae529
  modified: 2026-10-21T10:18:16.374Z
---

Level_01 (Dorf, Plan nightward_dorfplan.svg, nur Nord bis Zone 1 Waldrand) entsteht über `Nightward/Dorf/Dorf bauen (Level_01)` (Scripts/Editor/DorfBuilder.cs). Es ersetzt nur das Root-Objekt "Level_01"; Player/NPCs/Tag-Nacht bleiben. Große Häuser kommen als `DorfXxx`-Einträge in Art/Tiles/Baukasten/Bauplaene.json (Prefabs/Haeuser), die Bar als Prefab Bar_Ilhans_Komplett (Innenraum bei x≈206).

**Why:** Level1Builder.cs bleibt unangetastet (Backup der Szene/Skripte lag im Scratchpad); DorfBuilder ist re-runnable.
**How to apply:** Änderungen am Dorf im DorfBuilder machen und neu bauen, nicht die Szene von Hand umbauen. Für Screenshots die Opening-Szene ausblenden (gleiche Koordinaten) und `cam.Render()` zweimal aufrufen, sonst fehlen Haus-Deko-Tiles im ersten Bild. Opening war beim Start ungespeichert (dirty) — nie speichern/schließen ohne Rückfrage. Unity-Absturz beim Kompilieren passiert; danach MCP-Session neu starten.

Dorf-Art entsteht per Python (`Art/Tiles/_Quelle_Generator/dorf_tiles.py` -> Tileset_Dorf.png/.aseprite, `dorf_objekte.py` -> Tiles/Dorf/Objekte); Menü `Nightward/Dorf/Alles: Art importieren + Dorf bauen`. Pflaster/Platten/Kies sind Overlay-Autotiles über Erde. Wegweiser sind englisch (Doctor, Bakery, Bar, Diner, Sheriff, Pastor, Market, Barn, Graves, Smith, Villa, Homes, Forest). Einige 32x32-Büsche (Busch_Blueten_*, Busch_Gruen_A-D, Grasbusch_*) sind an der Zellkante abgeschnitten, nicht streuen. Nach Skriptänderung erst kompilieren lassen, sonst läuft beim Menüaufruf noch der alte Code. Wichtige Docs: Style-Bibel (39-Farben-Palette, cozy düster, Lichtinseln), Opening Sequence (Dusk Bell). Straße muss nach Norden und Süden offen bleiben; Villa liegt laut Plan im Norden (User sagte einmal „unten“ – offen).

Siehe auch [[scripts-untracked-in-git]].
