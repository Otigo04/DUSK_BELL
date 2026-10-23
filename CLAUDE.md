# CLAUDE.md – DUSK BELL

## Projekt

- **Spielname:** DUSK BELL (früher „Nightward“, Arbeitstitel). Im Code, in Menüs (`Nightward/...`) und in Ordnern tauchen noch alte Namen auf. Diese bitte **nicht** eigenmächtig umbenennen.
- **Repo:** https://github.com/Otigo04/DUSK_BELL
- **Lokaler Arbeitsordner des Users (Windows):** `F:\!!!_GAMES\NIGHTWARD\Nightward`
- **Engine:** Unity 6000.4.7f1 (6.4), C#, Pixel-Art. Die Assets (Sprites, Tiles, Prefabs, Szenen) liegen unter `Assets/`.
- **Sprache:** Der User schreibt auf Deutsch. Spieltexte sind überwiegend englisch.

## Projektgedächtnis

- `.claude-memory/` ist eine Sync-Kopie der Claude-Memory vom Haupt-PC. Dort stehen Notizen zu Dorf-Builder, Survival-System, Kampf-Animationen und zum WIP-Stand. Vor größeren Arbeiten lesen: `.claude-memory/MEMORY.md` ist der Index.
- Die Dateien sind per `README.md` in den Memory-Ordner des Projekts zu kopieren, nicht umgekehrt.

## Regeln für die Arbeit

- **Generierte Art nicht von Hand ändern.** Sprites entstehen über Python-Generatoren (z. B. `Art/Tiles/_Quelle_Generator/`, `Art/Characters/Hauptfiguren/_Quelle_Generator/`). Änderungen im Generator machen und neu erzeugen.
- **Dorf in Level_01** wird über das Editor-Skript `DorfBuilder.cs` gebaut (Menü `Nightward/Dorf/...`). Änderungen dort machen und neu bauen, die Szene nicht von Hand umbauen.
- **Szenen und Prefabs nicht ohne Rückfrage speichern oder schließen.** Die Opening-Szene war teils ungespeichert.
- **Vor dem Überschreiben von Projektdateien** eine Kopie in den Scratchpad legen. Nie Git-Ausgaben direkt auf Projektdateien umleiten (`git show … > datei` hat schon einmal eine Datei abgeschnitten).
- **Backups** liegen in `_Backup_vor_Claude_*`. Diese Ordner nicht löschen.
- Nach Skriptänderungen erst kompilieren lassen, bevor Editor-Menüs laufen.

## Git

- Entwicklungsbranch für Claude-Sitzungen: `claude/optimistic-shannon-r6v88f`. Auf `main` nur pushen, wenn der User es ausdrücklich verlangt.
- Commits mit klarer Beschreibung. Pushen mit `git push -u origin <branch>`.
- Keine Pull Requests ohne ausdrückliche Anfrage.
