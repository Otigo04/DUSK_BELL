---
name: survival-system
description: "Survival-System (Stats, Moods, Regeln) in Scripts/Survival, Config-Asset, nur am Level_01-Spieler, Fallen beim Bauen"
metadata:
  node_type: memory
  type: project
  originSessionId: 76e856fe-531e-47e9-99e9-bc4a00736d4e
  modified: 2026-10-21T18:53:15.517Z
---

Seit 2026-10-21 gibt es ein datengetriebenes Survival-System (Doku: `Scripts/Survival/LIESMICH_Survival.md`). Kern in eigener asmdef `Scripts/Survival/Core` (Nightward.Survival, 39 EditMode-Tests in Tests/EditMode), Glue in `Scripts/Survival/`, Balancing in `Data/Balancing/SurvivalConfig.asset`. "Outsource-System" des Users = Ausdauer (Sprachdiktat).

**Why:** User wollte modulare Werte/Moods (Hunger, Durst, Müde, Erschöpft ...), leicht einstellbar; Regeln wenn-dann statt Hardcode.
**How to apply:** Balancing im Config-Asset oder `SurvivalDefaults.cs` (nach Code-Änderung am Default das Asset per `FillDefaults()` neu füllen, sonst gilt das alte Asset). Komponenten liegen nur am Spieler in Level_01, NICHT im Player-Prefab (Opening/IlhansBar teilen es; Leertaste = Ausweichen kollidiert mit Dialog-Skip). Jede MonoBehaviour braucht eine eigene Datei mit gleichem Namen (sonst "Script missing" nach Play). Unity-MCP: nach `refresh force` hängt die Brücke oft, Unity-Fenster per PowerShell in den Vordergrund holen. Nightward/Survival-Menü: Einrichten, Testkit anlegen/entfernen. HUD-Bedarfskacheln sind jetzt 11 (2-spaltiges Raster unten rechts). Siehe auch [[scripts-untracked-in-git]].
