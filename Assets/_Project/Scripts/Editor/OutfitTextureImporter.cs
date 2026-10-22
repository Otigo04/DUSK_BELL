using UnityEditor;
using UnityEngine;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Import-Regeln fuer das Kleidungssystem (siehe PlayerOutfit), automatisch bei jedem Import:
    ///  - Resources/OutfitMasks: Masken der Figuren-Sheets. Brauchen exakte Werte und muessen lesbar sein (keine Kompression, Punkt-Filter, Read/Write).
    ///  - Art/Characters/Hauptfiguren/&lt;Mann|Frau&gt;/*.png: die Sheets selbst muessen lesbar sein, damit sie zur Laufzeit umgefaerbt werden koennen.
    ///  - Resources/UI: Platzhalter leerer Ausruestungsplaetze (Sprites, 100 px pro Einheit wie die anderen UI-Bilder).
    /// </summary>
    public class OutfitTextureImporter : AssetPostprocessor
    {
        void OnPreprocessTexture()
        {
            var ti = (TextureImporter)assetImporter;
            string p = assetPath;
            if (p.Contains("/Resources/OutfitMasks/"))
            {
                ti.textureType = TextureImporterType.Default;
                ti.sRGBTexture = false;
                ti.filterMode = FilterMode.Point;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                ti.mipmapEnabled = false;
                ti.alphaIsTransparency = false;
                ti.npotScale = TextureImporterNPOTScale.None;
                ti.isReadable = true;
            }
            else if (p.Contains("/Art/Characters/Hauptfiguren/") && (p.Contains("/Mann/mann_") || p.Contains("/Frau/frau_")) && p.EndsWith(".png"))
            {
                ti.isReadable = true;
            }
            else if (p.Contains("/Resources/UI/"))
            {
                ti.textureType = TextureImporterType.Sprite;
                ti.spriteImportMode = SpriteImportMode.Single;
                ti.spritePixelsPerUnit = 100;
                ti.filterMode = FilterMode.Point;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                ti.mipmapEnabled = false;
                ti.alphaIsTransparency = true;
            }
        }
    }
}
