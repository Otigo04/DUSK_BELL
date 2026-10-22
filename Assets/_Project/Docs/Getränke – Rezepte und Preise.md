# Getränke – Rezepte und Preise (Ilhans Bar)

Stand: Vorschlag, noch nicht im GDD. Währung: **Wachtgroschen (WG)**, nur Silber.
Sprites: `Art/Items/Getraenke/`. Preise stehen auch auf den Tafeln im Bar-Tileset (`Preistafel`, `Kreidetafel`).

## Einschenken

Flasche (oder Fass/Krug) + leeres Glas → gefülltes Glas. Pro Glas sinkt der Füllstand der Flasche um eine Portion. Leere Flasche bleibt als Leergut (Rückgabe optional).

| Getränk | Behälter | Einkauf | Portionen | Leeres Glas | Gefülltes Glas | Verkauf je Glas |
|---|---|---|---|---|---|---|
| Bier | `Item_Bierfass` | 10 WG | 12 | `Item_Glas_Leer_Humpen` | `Item_Glas_Bier` | 1 WG |
| Bier | `Item_Flasche_Bier` | 2 WG | 2 | `Item_Glas_Leer_Humpen` | `Item_Glas_Bier` | 1 WG |
| Met | `Item_Krug_Met` | 3 WG | 3 | `Item_Glas_Leer_Humpen` | `Item_Glas_Met` | 1 WG |
| Rotwein | `Item_Flasche_Rotwein` | 5 WG | 4 | `Item_Glas_Leer_Weinglas` | `Item_Glas_Rotwein` | 2 WG |
| Weißwein | `Item_Flasche_Weisswein` | 5 WG | 4 | `Item_Glas_Leer_Weinglas` | `Item_Glas_Weisswein` | 2 WG |
| Schnaps (Korn) | `Item_Flasche_Schnaps` | 6 WG | 6 | `Item_Glas_Leer_Stamperl` | `Item_Glas_Schnaps` | 2 WG |
| Whisky | `Item_Flasche_Whisky` | 9 WG | 4 | `Item_Glas_Leer_Tumbler` | `Item_Glas_Whisky` | 3 WG |
| Rum | `Item_Flasche_Rum` | 8 WG | 4 | `Item_Glas_Leer_Tumbler` | `Item_Glas_Rum` | 3 WG |
| Bourbon | `Item_Flasche_Bourbon` | 12 WG | 4 | `Item_Glas_Leer_Tumbler` | `Item_Glas_Bourbon` | 4 WG |

Der Einkaufspreis ist der Preis beim Händler, nicht beim Spieler im Wald (Flaschen sind dort Funde).

## Vorschlag für Wirkung (offen, bitte gegen das Regelwerk prüfen)

- **Bier, Met:** Sanity +3, Vertrauen des Gastes +1 bei Bewirtung.
- **Wein:** Sanity +5, Vertrauen +1.
- **Schnaps, Whisky, Rum, Bourbon:** Sanity +8, dafür Rausch-Stufe +1 (schlechtere Sicht am Türspion, kürzeres Reaktionsfenster bei Warnstufe 2).
- **Rausch:** klingt nach einer Nacht ab, nur Beruhigungstee beschleunigt es.
- Hardcore: Alkohol hebt die Schlafsperre (unter 40 % Sanity) nicht auf, nur Tee, Tabak oder Kamin.

## Stammgäste (Idee)

Jeder Bewohner hat ein Lieblingsgetränk. Wird es serviert, gibt es doppelt Vertrauen. Passt zum Wiedererkennungs-Prinzip der Style-Bibel (markantes Element pro Figur).
