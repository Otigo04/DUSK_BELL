# Survival-System (Leben, Ausdauer, Sanity, Bedarf, Stimmungen)

Alles Balancing liegt in **einem Asset**: `Assets/_Project/Data/Balancing/SurvivalConfig.asset`.
Rechtsklick auf das Asset -> "Auf Standardwerte zuruecksetzen" (Standardwerte stehen in `Core/SurvivalDefaults.cs`).
Ohne Asset laufen die Standardwerte aus dem Code.

## Aufbau

| Teil | Datei | Aufgabe |
|---|---|---|
| Kern (eigene Assembly `Nightward.Survival`, ohne Spielcode, testbar) | `Core/` | Werte, Stimmungen, Regeln, Effekte, Speichern |
| Spieler-Anbindung | `PlayerSurvival.cs` | Sprint/Schleichen/Ausweichen, Zeit + Umwelt liefern, Schaden, Tod, Schlaf, Rast |
| HUD | `SurvivalHudBinder.cs` | schreibt ins `NwGameHud` (Balken + 11 Kacheln) |
| Welt | `SurvivalZone`, `SurvivalSource`, `SurvivalBed`, `SurvivalRestPoint` | Feuer/Dickicht/Orte, Essen+Trinken, Bett, Bank/Quelle |
| Debug | `SurvivalDebugPanel.cs` | **F8**: alle Werte, Raten, Aufschluesselung, Schieber, Verbrauchsgueter |
| Tests | `Tests/EditMode/SurvivalSimulationTests.cs` | 39 Tests (Test Runner, EditMode) |

Menue `Nightward > Survival`: Alles einrichten, Config-Asset, Testkit (Brunnen, Brot, Tee, Bank, Bett, Zonen) anlegen/entfernen.
Das System haengt nur am Spieler von Level_01 (nicht im Player-Prefab, wegen Opening/IlhansBar).

## Zeit
Raten stehen **pro Spielstunde** (= 1/24 eines Tag-Nacht-Zyklus, gleichmaessig ueber alle Phasen) oder **pro Sekunde** (Ausdauer).
Aendert man die Phasendauer im DayNightCycle, skaliert alles mit. Pausiert der Zyklus (Dialog), stehen Hunger/Durst still.
Gesamt-Tempo: `SurvivalSystem.hoursScale` (2 = alles doppelt so schnell, ein einfacher Schwierigkeitsregler).

## Wie man etwas aendert
* **Grundrate eines Werts**: `stats` -> StatDef.baseRate.
* **"Wenn rennen, dann mehr Durst"**: `rules` -> Regel mit Bedingung `Sprinting` und Effekt `StatDrainMult Thirst 2.4`.
* **Neue Regel**: Bedingungen (Flag, Wert ueber/unter %, Stimmung ab Stufe) + Effekte, alles im Inspector. Haken `enabled` schaltet sie ab.
* **Stimmung**: `moods` -> Quellen, 4 Schwellen (Schwere 0-1), pro Stufe eigene Effekte (Tempo, Ausdauerkosten, Schaden, Taumeln, Sprint sperren, Wert-Raten ...).
* **Essen/Trinken/Medizin**: `consumables` (sofortige Aenderung + zeitliche Effekte). Nutzen: `sim.Consume("bread")` oder `SurvivalSource`.
* **Kampf-Zahlen** (Lebenspunkte 3, Unverwundbarkeit 2 s, Ausweichfenster 0,3 s, Ausdauerkosten): `tuning`.

Effekt-Arten: StatRate (+/- pro Einheit), StatDrainMult / StatRecoverMult (nur die verschlechternde / verbessernde Aenderung),
MoveSpeedMult, SprintSpeedMult, StaminaCostMult, DamageDealtMult, DamageTakenMult, ReactionWindowMult, ControlSway, Hallucination,
BlockSprint, BlockSleep, BlockAttack.
Rate = (Grundrate + Summe StatRate) * Multiplikator.

## Werte (StatId)
Health, Stamina, StaminaCap (Maximum-Erschoepfung), Sanity, Hunger, Thirst, Fatigue, Intoxication, Pain, Happiness, Loneliness, Stress, Cold.
Neuer Wert: Eintrag in `StatId` + StatDef in der Config (die Config ergaenzt Fehlendes selbst aus den Standardwerten).

## Stimmungen (HUD-Kacheln, Stufe 1-4, teils positiv 1-2)
Hungrig, Durstig, Muede, **Erschoepft** (neu), Betrunken, Verletzt, Stimmung (traurig/froh), Einsam/Sozial, Angespannt/Ruhig,
**Frierend** (neu), **Verstoert** (neu, Sanity niedrig). Neue Kachel: Symbol in `Art/UI/_Quelle_Generator/build_hud_survival.py`,
`NeedKind` + `NwNeedTexts` (UI/NwNeedTile.cs), Eintrag in `HudNeuBuilder.BuildHud`, dann `Nightward/UI/HUD Neu/2 Prefabs bauen` + `3 In offene Szene einbauen`.

## Spiel-Regeln, die schon drin sind
* Sprint (Shift): Ausdauer sinkt, Durst x2,4, Hunger x1,7; leere Ausdauer = ausser Atem bis 25 %.
* Sprint durchs Dickicht (Zone `Thicket`) senkt das Maximum, nur Rast/Quellwasser/Schlaf erholt es.
* Schlag und Ausweichen (Leertaste, 0,3 s Unverwundbarkeit) kosten Ausdauer; Zustaende schwaechen Schlag und Tempo.
* Dunkelheit draussen in der Nacht senkt Sanity; Lichtinsel (Light2D), Kamin, Gespraeche, Tee, Schlaf heben sie.
* Schlafsperre unter 40 % Sanity; Albtraeume bei niedriger Sanity; Schlaf nur in Daemmerung/Nacht.
* Tod: Spieler erwacht am Morgen geschwaecht am Startpunkt (`respawnPoint` setzbar). Rucksack/Corpse-Run ist noch nicht gebaut (kein Inventar).
* Zusammenbruch bei 100 % Muedigkeit (3 s Sperre).
* Gespraeche (DialogueRunner.Ended) senken Einsamkeit; derselbe Partner gibt innerhalb 6 Spielstunden nur 20 %.
* Speichern: `SurvivalSystem.SaveJson()/LoadJson()`.

## Noch offen
* Kein Inventar: Verbrauchsgueter werden ueber Quellen/Debug benutzt, nicht aus dem Rucksack.
* Barrikade als Schlaf-Voraussetzung (Regelwerk) fehlt, ebenso Wecklevel-Kopplung.
* Halluzinationen/Sanity-Bildschirmeffekte: Wert `Hallucination` liegt in der Simulation bereit, es gibt noch keine Darstellung.
* Aseprite-Datei `HUD_Needs.aseprite` ist nicht um die drei neuen Kacheln erweitert (PNG + Generator sind die Quelle).
