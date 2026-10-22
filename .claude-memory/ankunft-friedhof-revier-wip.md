---
name: ankunft-friedhof-revier-wip
description: "WIP-Stand 2026-10-22 - Ankunft in Level_01, Friedhof am Südeingang, Revier-Innenraum, Sheriff-Szene (Branch wip/ankunft-friedhof-revier); was fertig ist und was noch fehlt"
metadata:
  node_type: memory
  type: project
  originSessionId: 1b3a8387-7cfb-4092-86ed-800459e2fabc
  modified: 2026-10-22T08:22:00.530Z
---

Auftrag des Users (2026-10-22, autonom): Opening-Auto/Ankunft auf das neue Dorf Level_01 umbauen, Friedhof an den Dorfeingang (Wiese westlich der Straße, Südeingang), Toter in Weiß neben Sarg (Priester kommt später, nur Platz `GravePriest` reserviert), Sheriff-Station mit Innenraum, Sheriff-Story aus `Downloads/Nightward – Sheriff Bulut Erste Begegnung (Ink).pdf` (Scene 1 nur bis "Go now. Ilhan is waiting.", Bar/Nacht später). Entscheidung: Tür-Durchgang (Durchgang + BildUebergang) statt freiem Reinlaufen.

**Fertig (auf main gepusht, ArrivalDirector/ArrivalScript noch nie kompiliert):**
- `Art/Tiles/_Quelle_Generator/friedhof_objekte.py` -> 11 neue Sprites in Tiles/Dorf/Objekte (Grab_Offen, Sarg_Leer, Toter_Weiss, Erdhaufen, Schaufel, Grabhügel, Grabstein_D/E/F, Kreuz_Holz); importiert.
- `Bauplaene.json` DorfRevier: Innenraum = Sheriff-Stube (Schreibtisch, Kamin, Talisman_Schrein, Bücherwand ...), Außen Arzt-Schild -> Schild_Brett; Häuser neu gebaut (0 Fehler).
- `DorfBuilder.cs`: neue Konstanten GraveX0..GraveY1/GravePit/RevierInnenOrigin(200,60), neuer PlaceGraveyard (Zaun x12-28,y8-16, Tor Ost), PlaceRevierInterior (Durchgang Tür<->Innen, Marker `Revier_Innen_Eingang`/`Revier_Aussen_Ausgang`), Friedhofsweg nach Westen. Zuletzt gebaut ohne Fehler; danach Grabstein-Verteilung (priestSpot) gepatcht -> **DorfBuilder muss noch einmal laufen** (Menü Nightward/Dorf/Alles: Art importieren + Dorf bauen).
- Neue Skripte (Scripts/Opening): `ArrivalDirector.cs`, `ArrivalScript.cs` (englische Texte), `ArrivalState.cs` (PlayerPrefs-Flag); geändert: ScriptedWalker (hold-Parameter), ScriptedDialogue/OpeningScript.Line (player-Zeilen "You"), DialogueView.PlayerLabel.
- Backup der ungespeicherten Level_01 vor Umbau: `_Backup_vor_Claude_2026-10-22/Level_01_vor_Friedhof.unity` (12 MB, nicht im Branch).

**Noch offen (in dieser Reihenfolge):**
1. Unity kompilieren lassen und Konsole auf Fehler prüfen (ArrivalDirector wurde nie kompiliert!).
2. Editor-Skript `ArrivalBuilder.cs` schreiben (fehlt komplett): in Level_01 Root "Ankunft" mit Auto (Code wie OpeningBuilder Z.166-206, Sprites Art/Vehicles/Auto_Sedan_*), Trauergäste aus NPC-Prefabs (Gast/Hausfrau, Behaviors/Brain/Dialogue entfernen, ScriptedWalker+CrowdMember, dunkel getönt, um GravePit (22,12): Süd/West/Ost-Bogen, Mutter+Junge Richtung Tor), `graveFocus`, OpeningUI via `OpeningBuilder.BuildUI` (private -> public machen) + OpeningAudio + ScriptedDialogue (Bulut-Portraits wie OpeningBuilder Z.274-284, Profil Data/NPCs/NpcProfile_bulut.asset), ScriptedWalker auf NPC_Bulut_Sheriff, ArrivalDirector verdrahten (hudRoot = Szenenobjekt "HUD", uiRoot = UI_Opening-Canvas, Controller Art/Animations/Hauptfigur_Frau|Mann/*.controller). Muss DorfBuilder-Neubau überleben (Director findet Marker per Namen) und nach DorfBuilder.Build automatisch laufen oder im Menü hängen.
3. `OpeningDirector.Run`: nach `villageEntryY` ausblenden, `ArrivalState.Pending=true`, `SceneManager.LoadScene("Level_01")`; alte Dorf/Station/DriveOn-Methoden entfernen (OpeningBuilder setzt die Felder noch per FindProperty -> Felder behalten oder Builder anpassen).
4. Testen per Play: Flag `nw_arrival_pending` (oder runWithoutOpening am ArrivalDirector); Dialog-Weiterschalten per Space, Antworten per `DialogueView.Select(i)`. Screenshots: execute_code mit temporärer Kamera + RenderTexture (cam.Render() zweimal).
5. Prüfen: Quest-HUD vs. Level_01-HUD Überlappung, Kamera im Innenraum, Bulut-Sitz (kinematisch), Auto-Stopp bei (34.5,8.8), Mourner nicht in Kollision, Friedhof-Optik.

**Technik-Hinweise:** Der Unity-MCP-Server läuft auf http://127.0.0.1:8080/mcp, ist aber nach Sitzungsstart oft nicht als Tools geladen -> per JSON-RPC (initialize, Mcp-Session-Id, tools/call) mit Python-Helper ansprechen (Tools: execute_code, execute_menu_item, read_console, refresh_unity, manage_scene). execute_code nutzt C# 6 (CodeDom): `UnityEngine.Object` voll ausschreiben. Nach Skriptänderung `refresh_unity compile=request` und warten. Level_01 war beim Start ungespeichert (dirty); DorfBuilder speichert die Szene.

Siehe [[dorf-builder-level01]], [[scripts-untracked-in-git]].
