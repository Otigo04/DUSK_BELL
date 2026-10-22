using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.Tilemaps;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Schneidet Tileset_Haus und Tileset_Interieur in 32x32-Zellen, legt Tile-Assets an und baut je eine Palette,
    /// die das Sheet 1:1 abbildet (Zelle Spalte c, Reihe r liegt in der Palette bei x = c, y = -r).
    /// So passen die Spalten/Reihen-Angaben aus den LIESMICH-Dateien direkt zur Palette.
    /// Mehrzellige Teile (Tueren 32x64, Betten 64x64 ...) einfach Zelle fuer Zelle bzw. per Box-Auswahl malen.
    /// Leere Zellen werden uebersprungen. Bestehende Tile-Assets werden nie geloescht (GUIDs bleiben).
    /// </summary>
    public static class TilesetHaus
    {
        const string Root = "Assets/_Project/Art/Tiles";
        const string TA = Root + "/TileAssets";
        const string PaletteDir = Root + "/Palettes";
        const int Cell = 32;

        static readonly (string png, string prefix, string folder, string palette)[] Sheets =
        {
            (Root + "/Tileset_Haus.png", "H", "Haus", "Pal_Haus"),
            (Root + "/Tileset_Interieur.png", "I", "Interieur", "Pal_Interieur"),
        };

        [MenuItem("Nightward/Tiles/Haus + Interieur bauen")]
        public static void BuildAll()
        {
            foreach (var sheet in Sheets)
            {
                if (!File.Exists(sheet.png)) { Debug.LogWarning("Fehlt: " + sheet.png); continue; }
                Slice(sheet.png, sheet.prefix);
                var tiles = CreateTiles(sheet.png, sheet.folder);
                CreatePalette(sheet.palette, tiles, sheet.prefix);
                Debug.Log($"[Tileset-Haus] {sheet.palette}: {tiles.Count} Tiles.");
            }
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
        }

        static void Slice(string png, string prefix)
        {
            // Pixel direkt aus der Datei lesen, damit die Textur nicht auf Read/Write gestellt werden muss
            var tex = new Texture2D(2, 2);
            tex.LoadImage(File.ReadAllBytes(png));
            int cols = tex.width / Cell, rows = tex.height / Cell;

            var ti = (TextureImporter)AssetImporter.GetAtPath(png);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = Cell;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;

            var metas = new List<SpriteMetaData>();
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < cols; c++)
                {
                    var rect = new Rect(c * Cell, tex.height - (r + 1) * Cell, Cell, Cell);
                    if (IsEmpty(tex, rect)) continue;
                    metas.Add(new SpriteMetaData
                    {
                        name = $"{prefix}_{r}_{c}",
                        rect = rect,
                        alignment = (int)SpriteAlignment.Center,
                        pivot = new Vector2(0.5f, 0.5f)
                    });
                }
            Object.DestroyImmediate(tex);
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();
        }

        static bool IsEmpty(Texture2D tex, Rect r)
        {
            var px = tex.GetPixels((int)r.x, (int)r.y, (int)r.width, (int)r.height);
            foreach (var p in px) if (p.a > 0.01f) return false;
            return true;
        }

        static Dictionary<string, TileBase> CreateTiles(string png, string folder)
        {
            Directory.CreateDirectory($"{TA}/{folder}");
            AssetDatabase.Refresh();
            var res = new Dictionary<string, TileBase>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(png))
            {
                if (!(o is Sprite sp)) continue;
                string path = $"{TA}/{folder}/{sp.name}.asset";
                var t = AssetDatabase.LoadAssetAtPath<Tile>(path);
                if (t == null)
                {
                    t = ScriptableObject.CreateInstance<Tile>();
                    t.colliderType = Tile.ColliderType.None;
                    AssetDatabase.CreateAsset(t, path);
                }
                t.sprite = sp; // nach neuem Schnitt aktualisieren
                EditorUtility.SetDirty(t);
                res[sp.name] = t;
            }
            return res;
        }

        static void CreatePalette(string name, Dictionary<string, TileBase> tiles, string prefix)
        {
            AssetDatabase.DeleteAsset($"{PaletteDir}/{name}.prefab");
            var go = GridPaletteUtility.CreateNewPalette(PaletteDir, name, GridLayout.CellLayout.Rectangle,
                GridPalette.CellSizing.Automatic, Vector3.one, GridLayout.CellSwizzle.XYZ);
            var path = AssetDatabase.GetAssetPath(go);
            var contents = PrefabUtility.LoadPrefabContents(path);
            var tm = contents.GetComponentInChildren<Tilemap>();
            foreach (var kv in tiles)
            {
                var parts = kv.Key.Substring(prefix.Length + 1).Split('_');
                int r = int.Parse(parts[0]), c = int.Parse(parts[1]);
                tm.SetTile(new Vector3Int(c, -r, 0), kv.Value);
            }
            tm.CompressBounds();
            PrefabUtility.SaveAsPrefabAsset(contents, path);
            PrefabUtility.UnloadPrefabContents(contents);
        }
    }
}
