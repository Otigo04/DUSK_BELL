ANKER-ASSETS (Referenz fuer jeden neuen Asset-Auftrag)
Die Style-Bibel verlangt drei fertige Anker, bevor Masse erzeugt wird: Tile, Bewohner, Monster.
Neue Assets muessen neben diesen Dateien (4x/6x, Point-Filter) stilistisch zusammenpassen: gleiche Outline-Staerke,
gleiche Schattenstufen, gleiche Lichtrichtung (oben-links), gleiche Saettigung.

  Anker_Tile.png      32x32  Gras-Kachel aus Tileset_Terrain (Zelle mit dem hoechsten Gras-Anteil, voll deckend)
  Anker_Bewohner.png  48x48  Hauptfigur_Frau
  Anker_Monster.png   48x48  Der Gast, Final Form (Idle)
  Anker_Vorschau.png  alle drei 6x vergroessert

Kopien, keine Verschiebung (Unity-GUIDs der Originale bleiben). Aenderung eines Ankers nur per Beschluss des Users.
Pruefung: python3 Assets/_Project/Art/__STYLEBIBLE/tools/pixel_lint.py Assets/_Project/Art/__STYLEBIBLE/Anker/Anker_*.png
