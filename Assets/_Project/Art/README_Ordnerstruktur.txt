ART - ORDNERSTRUKTUR (Stand 2026-10-23)
=================================================================================================
Regel: neue Welt-Art kommt in Art/Welt/<NN_Zone>/{Tileset|Objekte|Animiert|Tiere}. Bestehende Ordner werden NICHT verschoben, weil Unity Objekte per GUID
(.meta) und Pfad verknuepft; ein Verschieben ohne Unity wuerde Prefabs/Szenen/Tile-Assets zerreissen. Verschieben bitte spaeter im Unity-Editor (Project-Fenster).

Art/
  Palette.png / Palette.gpl / Palette_Vorschau.png   40-Farben-Palette fuer AUSSEN (Gelaende, Wald, Fluss, Welt)
  __STYLEBIBLE/        Style-Bibel (Haus/Interieur: 39-Farben-Palette Palette.gpl der Bibel)
  Tiles/               Zone 1 = Dorf: Terrain, Wald, Zaun, Hohes Gras, Strasse, Baukasten (Haeuser/Interieur), Objekte, Animiert
     _Quelle_Generator/  Python-Generatoren der Dorf-Tiles (nwlib, autotile, paths, bk_*)
  Welt/                Zone 2-6 + Gemeinsam (NEU, siehe Welt/LIESMICH_Welt.txt)
  Characters/          Figuren (Portraits, Sprites), Statisten/, Tiere/ (Hund, Huhn, Pferd)
  Items/ UI/ VFX/ Vehicles/ Environment/ Materials/ Animations/   wie bisher
  _IMPORTED/           Rohimporte (nicht bearbeiten)

Zonen-Nummern: 01 Dorf (Art/Tiles) | 02 Tiefwald | 03 Fluss | 04 Sumpf | 05 Felsland | 06 Ruinen | 00 gemeinsame Objekte.
Wo finde ich was?  Fluss-Tileset: Welt/03_Fluss/Tileset | Fische: Welt/03_Fluss/Tiere | Alle Dateien: Welt/_Liste.txt
Neue Zone anlegen: Ordner Welt/<NN_Name>/{Tileset,Objekte,Animiert} + Generator gen_<name>.py im _Quelle_Generator + Eintrag in build_welt.py (STEPS/ORDER)
                   und welt_lib.ZONEN. QA (qa_welt.py) erfasst neue Zonen automatisch.
Audio liegt getrennt in Assets/_Project/Audio (siehe dort LIESMICH_Audio.txt).
