using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Tilemaps;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut die Tileset-Erweiterung: neue Objekte (Buesche, Steine, Props), Zaun-/Uebergangs-/Hohes-Gras-Tilesets,
    /// animierte Varianten, RuleTiles (inkl. Weg/Pflaster/Wasser/Waldboden) und Paletten.
    /// Bestehende Tile-Assets werden nie geloescht (GUIDs bleiben, Szenen behalten ihre Referenzen).
    /// </summary>
    public static class TilesetErweiterung
    {
        const string Root = "Assets/_Project/Art/Tiles";
        const string ObjDir = Root + "/Objekte";
        const string AnimDir = Root + "/Animiert";
        const string TA = Root + "/TileAssets";
        const string PaletteDir = Root + "/Palettes";
        const int Cell = 32;

        static readonly (string png, string prefix, string folder)[] Sheets =
        {
            (Root + "/Tileset_Zaun.png", "Z", "Zaun"),
            (Root + "/Tileset_Uebergang.png", "U", "Uebergang"),
            (Root + "/Tileset_HohesGras.png", "G", "HohesGras"),
        };

        [MenuItem("Nightward/Tiles/Erweiterung bauen (alles)")]
        public static void BuildAll()
        {
            ConfigureImports();
            CreateTiles();
            CreateRuleTiles();
            CreatePalettes();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Tileset-Erweiterung] fertig.");
        }

        // ------------------------------------------------------------------ Import
        static TextureImporter Importer(string path, SpriteImportMode mode)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = mode;
            ti.spritePixelsPerUnit = Cell;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            return ti;
        }

        static void SetupObject(string path)
        {
            var ti = Importer(path, SpriteImportMode.Single);
            var s = new TextureImporterSettings();
            ti.ReadTextureSettings(s);
            s.spriteAlignment = (int)SpriteAlignment.BottomLeft;
            s.spriteMeshType = SpriteMeshType.FullRect;
            ti.SetTextureSettings(s);
            ti.SaveAndReimport();
        }

        static List<string> ObjectNames()
        {
            var res = new List<string>();
            var rx = new Regex(@"^(\w+)\s*\|\s*(\d+)x(\d+)");
            foreach (var line in File.ReadAllLines(ObjDir + "/_Liste.txt"))
            {
                var m = rx.Match(line);
                if (m.Success) res.Add(m.Groups[1].Value);
            }
            return res;
        }

        static List<(string name, int frames, int ms)> AnimList()
        {
            var res = new List<(string, int, int)>();
            var rx = new Regex(@"^(\w+)\s*\|\s*(\d+)\s*\|\s*\d+x\d+\s*\|\s*(\d+)\s*$");
            foreach (var line in File.ReadAllLines(AnimDir + "/_Liste.txt"))
            {
                var m = rx.Match(line.Trim());
                if (m.Success) res.Add((m.Groups[1].Value, int.Parse(m.Groups[2].Value), int.Parse(m.Groups[3].Value)));
            }
            return res;
        }

        public static void ConfigureImports()
        {
            AssetDatabase.Refresh();
            int n = 0;
            foreach (var name in ObjectNames())
            {
                string p = $"{ObjDir}/{name}.png";
                if (!File.Exists(p)) continue;
                if (File.Exists($"{TA}/Objekte/{name}.asset")) continue;   // schon importiert + als Tile angelegt
                SetupObject(p);
                n++;
            }

            foreach (var (png, prefix, _) in Sheets)
            {
                if (!File.Exists(png)) continue;
                var ti = Importer(png, SpriteImportMode.Multiple);
                ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
                var metas = new List<SpriteMetaData>();
                for (int r = 0; r < th / Cell; r++)
                    for (int c = 0; c < tw / Cell; c++)
                        metas.Add(new SpriteMetaData
                        {
                            name = $"{prefix}_{r}_{c}",
                            rect = new Rect(c * Cell, th - (r + 1) * Cell, Cell, Cell),
                            alignment = (int)SpriteAlignment.Center,
                            pivot = new Vector2(0.5f, 0.5f)
                        });
#pragma warning disable CS0618
                ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
                ti.SaveAndReimport();
            }

            foreach (var (name, frames, _) in AnimList())
            {
                string p = $"{AnimDir}/{name}.png";
                if (!File.Exists(p)) continue;
                var ti0 = (TextureImporter)AssetImporter.GetAtPath(p);
#pragma warning disable CS0618
                if (ti0.spriteImportMode == SpriteImportMode.Multiple && ti0.spritesheet.Length == frames) continue;
#pragma warning restore CS0618
                var ti = Importer(p, SpriteImportMode.Multiple);
                ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
                int fw = tw / frames;
                var metas = new List<SpriteMetaData>();
                for (int i = 0; i < frames; i++)
                    metas.Add(new SpriteMetaData
                    {
                        name = $"{name}_{i}",
                        rect = new Rect(i * fw, 0, fw, th),
                        alignment = (int)SpriteAlignment.BottomLeft,
                        pivot = Vector2.zero
                    });
#pragma warning disable CS0618
                ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
                ti.SaveAndReimport();
            }
            Debug.Log($"[Tileset-Erweiterung] Import konfiguriert ({n} neue Objekte).");
        }

        // ------------------------------------------------------------------ Tiles
        static Tile MakeTile(string path, Sprite sp)
        {
            if (File.Exists(path)) return AssetDatabase.LoadAssetAtPath<Tile>(path);
            var t = ScriptableObject.CreateInstance<Tile>();
            t.sprite = sp;
            t.colliderType = Tile.ColliderType.None;
            AssetDatabase.CreateAsset(t, path);
            return t;
        }

        static Dictionary<string, Sprite> SpritesOf(string png)
        {
            var d = new Dictionary<string, Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(png)) if (o is Sprite sp) d[sp.name] = sp;
            return d;
        }

        static float SpeedFactor(string name)
        {
            if (name.StartsWith("Lagerfeuer") || name.StartsWith("Kochfeuer") || name.StartsWith("Feuerschale") || name.StartsWith("Fackel")
                || name.StartsWith("Kerzen") || name.StartsWith("Windlicht")) return 0.45f;
            if (name.StartsWith("Laterne")) return 0.22f;
            if (name.StartsWith("Schilf") || name.StartsWith("Seerosen")) return 0.35f;
            if (name.StartsWith("Brunnen") || name.StartsWith("Wassertrog") || name.StartsWith("Fass_Wasser")) return 0.5f;
            if (name.StartsWith("Kristall") || name.StartsWith("Runenstein")) return 0.4f;
            if (name.StartsWith("Fahne")) return 0.4f;
            return 0.28f;
        }

        static void MakeAnim(string path, Sprite[] frames, float fps, int start)
        {
            if (File.Exists(path)) return;
            var a = ScriptableObject.CreateInstance<AnimatedTile>();
            a.m_AnimatedSprites = frames;
            a.m_MinSpeed = fps;
            a.m_MaxSpeed = fps;
            a.m_AnimationStartFrame = start;
            AssetDatabase.CreateAsset(a, path);
        }

        public static void CreateTiles()
        {
            foreach (var d in new[] { "Objekte", "Zaun", "Uebergang", "HohesGras", "Animiert", "RuleTiles" })
                Directory.CreateDirectory($"{TA}/{d}");
            Directory.CreateDirectory(PaletteDir);
            AssetDatabase.Refresh();

            int made = 0;
            foreach (var name in ObjectNames())
            {
                string tp = $"{TA}/Objekte/{name}.asset";
                if (File.Exists(tp)) continue;
                var sp = AssetDatabase.LoadAssetAtPath<Sprite>($"{ObjDir}/{name}.png");
                if (sp == null) { Debug.LogWarning("Sprite fehlt: " + name); continue; }
                MakeTile(tp, sp);
                made++;
            }

            foreach (var (png, prefix, folder) in Sheets)
                foreach (var kv in SpritesOf(png))
                    MakeTile($"{TA}/{folder}/{kv.Key}.asset", kv.Value);

            float[] jitter = { 1f, 0.9f, 1.1f, 0.95f };
            foreach (var (name, frames, ms) in AnimList())
            {
                var by = SpritesOf($"{AnimDir}/{name}.png");
                var arr = new Sprite[frames];
                bool ok = true;
                for (int i = 0; i < frames; i++) ok &= by.TryGetValue($"{name}_{i}", out arr[i]);
                if (!ok) { Debug.LogWarning("Animation unvollstaendig: " + name); continue; }
                int variants = Mathf.Min(4, frames);
                for (int k = 0; k < variants; k++)
                    MakeAnim($"{TA}/Animiert/{name}_v{k}.asset", arr, 1000f / ms * SpeedFactor(name) * jitter[k], k * frames / variants);
            }

            // Hohes Gras: animierte Variante je Spalte (4 Frames = Zeilen)
            var g = SpritesOf(Root + "/Tileset_HohesGras.png");
            if (g.Count > 0)
            {
                int cols = 0;
                while (g.ContainsKey($"G_0_{cols}")) cols++;
                for (int c = 0; c < cols; c++)
                {
                    var arr = new Sprite[4];
                    for (int f = 0; f < 4; f++) arr[f] = g[$"G_{f}_{c}"];
                    for (int k = 0; k < 4; k++)
                        MakeAnim($"{TA}/Animiert/HohesGras_{c}_v{k}.asset", arr, 1000f / 300f * 0.25f * jitter[k], k);
                }
            }
            AssetDatabase.SaveAssets();
            Debug.Log($"[Tileset-Erweiterung] {made} neue Objekt-Tiles.");
        }

        // ------------------------------------------------------------------ RuleTiles
        // Nachbarreihenfolge im RuleTile: NW, N, NE, W, E, SW, S, SE
        static RuleTile.TilingRule Rule(bool? n, bool? e, bool? s, bool? w, bool? nw, bool? ne, bool? sw, bool? se, params Sprite[] sprites)
        {
            int V(bool? b) => b == null ? 0 : (b.Value ? RuleTile.TilingRuleOutput.Neighbor.This : RuleTile.TilingRuleOutput.Neighbor.NotThis);
            var r = new RuleTile.TilingRule
            {
                m_Sprites = sprites,
                m_Output = sprites.Length > 1 ? RuleTile.TilingRuleOutput.OutputSprite.Random : RuleTile.TilingRuleOutput.OutputSprite.Single,
                m_PerlinScale = 1f,
                m_Neighbors = new List<int> { V(nw), V(n), V(ne), V(w), V(e), V(sw), V(s), V(se) }
            };
            return r;
        }

        /// <summary>Kanten-Set N1 E2 S4 W8 (Spalte 0-15), Innenecken fehlt NO/SO/SW/NW (Spalte 16-19), Fuellungen fuer Mitte.</summary>
        static void MakeAutoRuleTile(string path, Func<int, Sprite> edge, Sprite[] fills)
        {
            var rt = ScriptableObject.CreateInstance<RuleTile>();
            rt.m_DefaultSprite = edge(15);
            rt.m_DefaultColliderType = Tile.ColliderType.None;
            // Innenecken zuerst
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, false, null, null, edge(16)));   // fehlt NO
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, null, null, false, edge(17)));   // fehlt SO
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, null, false, null, edge(18)));   // fehlt SW
            rt.m_TilingRules.Add(Rule(true, true, true, true, false, null, null, null, edge(19)));   // fehlt NW
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, null, null, null, fills));       // Mitte
            for (int m = 0; m < 15; m++)
                rt.m_TilingRules.Add(Rule((m & 1) != 0, (m & 2) != 0, (m & 4) != 0, (m & 8) != 0, null, null, null, null, edge(m)));
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(rt, path);
        }

        public static void CreateRuleTiles()
        {
            Directory.CreateDirectory($"{TA}/RuleTiles");
            AssetDatabase.Refresh();
            string T = $"{TA}/RuleTiles";

            // Zaeune / Mauer / Hecke (Zeile r im Tileset_Zaun)
            var z = SpritesOf(Root + "/Tileset_Zaun.png");
            string[] zn = { "RT_Zaun_Holz", "RT_Zaun_Dunkel", "RT_Zaun_Weiss", "RT_Mauer_Stein", "RT_Hecke" };
            for (int r = 0; r < zn.Length; r++)
            {
                int rr = r;
                MakeAutoRuleTile($"{T}/{zn[r]}.asset", i => z[$"Z_{rr}_{i}"], new[] { z[$"Z_{rr}_15"] });
            }

            // Uebergaenge Gras -> Wald
            var u = SpritesOf(Root + "/Tileset_Uebergang.png");
            string[] un = { "RT_Wald_Hell", "RT_Wald_Dunkel", "RT_Wald_Laub", "RT_Wald_Nadel" };
            for (int r = 0; r < un.Length; r++)
            {
                int rr = r;
                var fills = new Sprite[4];
                for (int k = 0; k < 4; k++) fills[k] = u[$"U_4_{rr * 4 + k}"];
                MakeAutoRuleTile($"{T}/{un[r]}.asset", i => u[$"U_{rr}_{i}"], fills);
            }

            // bestehende Terrain-Autotiles (nur neue RuleTile-Huellen, Tile-Assets bleiben unberuehrt)
            var t = SpritesOf(Root + "/Tileset_Terrain.png");
            MakeAutoRuleTile($"{T}/RT_Weg.asset", i => t[$"T_0_{i}"], new[] { t["T_0_15"], t["T_4_8"], t["T_4_9"], t["T_4_10"] });
            MakeAutoRuleTile($"{T}/RT_Pflaster.asset", i => t[$"T_1_{i}"], new[] { t["T_1_15"], t["T_4_11"], t["T_4_12"] });
            MakeAutoRuleTile($"{T}/RT_Wasser.asset", i => t[$"T_2_{i}"], new[] { t["T_2_15"] });
            MakeAutoRuleTile($"{T}/RT_Waldboden.asset", i => t[$"T_3_{i}"], new[] { t["T_3_15"], t["T_4_13"], t["T_4_14"], t["T_4_15"] });
            AssetDatabase.SaveAssets();
            Debug.Log("[Tileset-Erweiterung] RuleTiles erzeugt.");
        }

        // ------------------------------------------------------------------ Paletten
        static void MakePalette(string name, Action<Tilemap> fill)
        {
            AssetDatabase.DeleteAsset($"{PaletteDir}/{name}.prefab");
            var go = GridPaletteUtility.CreateNewPalette(PaletteDir, name, GridLayout.CellLayout.Rectangle,
                GridPalette.CellSizing.Automatic, Vector3.one, GridLayout.CellSwizzle.XYZ);
            var path = AssetDatabase.GetAssetPath(go);
            var contents = PrefabUtility.LoadPrefabContents(path);
            var tm = contents.GetComponentInChildren<Tilemap>();
            fill(tm);
            tm.CompressBounds();
            PrefabUtility.SaveAsPrefabAsset(contents, path);
            PrefabUtility.UnloadPrefabContents(contents);
        }

        static Vector2Int SizeOf(string name)
        {
            var rx = new Regex(@"^" + name + @"\s*\|\s*(\d+)x(\d+)");
            foreach (var line in File.ReadAllLines(ObjDir + "/_Liste.txt"))
            {
                var m = rx.Match(line);
                if (m.Success) return new Vector2Int(Mathf.CeilToInt(int.Parse(m.Groups[1].Value) / (float)Cell), Mathf.CeilToInt(int.Parse(m.Groups[2].Value) / (float)Cell));
            }
            return Vector2Int.one;
        }

        /// <summary>Regale: je Gruppe eine Zeile, Objekte nebeneinander (mit Umbruch), Hoehe = hoechstes Objekt.</summary>
        static void Shelf(Tilemap tm, List<(string name, TileBase tile, Vector2Int size)> items, ref int baseY, int maxW = 36)
        {
            int x = 0, rowH = 1;
            foreach (var it in items) rowH = Mathf.Max(rowH, it.size.y);
            foreach (var it in items)
            {
                if (x + it.size.x > maxW) { x = 0; baseY -= rowH + 1; }
                tm.SetTile(new Vector3Int(x, baseY, 0), it.tile);
                x += it.size.x + 1;
            }
            baseY -= rowH + 1;
        }

        static List<(string, TileBase, Vector2Int)> Collect(Func<string, bool> pick, bool animatedFirst)
        {
            var res = new List<(string, TileBase, Vector2Int)>();
            var names = ObjectNames();
            names.Sort(StringComparer.Ordinal);
            foreach (var n in names)
            {
                if (!pick(n)) continue;
                TileBase t = null;
                if (animatedFirst)
                {
                    t = AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/Animiert/{n}_Anim_v0.asset")
                        ?? AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/Animiert/{n}_Wind_v0.asset");
                }
                t = t ?? AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/Objekte/{n}.asset");
                if (t != null) res.Add((n, t, SizeOf(n)));
            }
            return res;
        }

        static bool Has(string n, params string[] prefixes)
        {
            foreach (var p in prefixes) if (n.StartsWith(p, StringComparison.Ordinal)) return true;
            return false;
        }

        public static void CreatePalettes()
        {
            MakePalette("Pal_Natur_Neu", tm =>
            {
                int y = 0;
                Shelf(tm, Collect(n => Has(n, "Busch_Gruen", "Busch_Klein", "Busch_Rund", "Busch_Gross", "Busch_Riesig"), true), ref y);
                Shelf(tm, Collect(n => Has(n, "Busch_Beeren", "Busch_Blueten", "Brombeerbusch"), true), ref y);
                Shelf(tm, Collect(n => Has(n, "Busch_Dunkel", "Busch_Herbst", "Busch_Tot", "Busch_Dornen"), true), ref y);
                Shelf(tm, Collect(n => Has(n, "Farn_", "Lavendel", "Grasbusch", "Heidekraut"), true), ref y);
                Shelf(tm, Collect(n => Has(n, "Stein_Klein", "Kiesel", "Trittstein"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Stein_Mittel", "Stein_Sand", "Stein_Dunkel", "Steinhaufen"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Stein_Gross", "Stein_Findling", "Menhir", "Grabstein"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Kristall", "Runenstein"), true), ref y);
            });

            MakePalette("Pal_Props_Neu", tm =>
            {
                int y = 0;
                Shelf(tm, Collect(n => Has(n, "Fass"), true), ref y);
                Shelf(tm, Collect(n => Has(n, "Kiste"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Sack", "Korb", "Eimer", "Truhe", "Kuerbis"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Heuballen", "Holzstapel", "Hackklotz", "Amboss", "Bienenkorb"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Tisch", "Bank", "Hocker", "Stuhl"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Karren", "Schubkarre", "Ruderboot", "Zelt"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Wegweiser", "Tafel", "Warnschild", "Schild_", "Briefkasten", "Vogelscheuche", "Tor_"), false), ref y);
                Shelf(tm, Collect(n => Has(n, "Lagerfeuer_Gross", "Kochfeuer", "Feuerschale", "Fackel", "Kerzen", "Windlicht", "Fahne", "Brunnen", "Wassertrog"), true), ref y);
            });

            MakePalette("Pal_Autotiles", tm =>
            {
                // RuleTiles einzeln anklickbar (ein Tile je Gruppe)
                int x = 0;
                foreach (var g in AssetDatabase.FindAssets("t:RuleTile", new[] { TA + "/RuleTiles" }))
                {
                    var rt = AssetDatabase.LoadAssetAtPath<TileBase>(AssetDatabase.GUIDToAssetPath(g));
                    tm.SetTile(new Vector3Int(x % 8, -(x / 8) * 2, 0), rt);
                    x++;
                }
            });

            MakePalette("Pal_Zaun_Uebergang_Gras", tm =>
            {
                void Sheet(string folder, string prefix, int rows, int cols, ref int yy)
                {
                    for (int r = 0; r < rows; r++)
                        for (int c = 0; c < cols; c++)
                        {
                            var t = AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/{folder}/{prefix}_{r}_{c}.asset");
                            if (t != null) tm.SetTile(new Vector3Int(c, yy - r, 0), t);
                        }
                    yy -= rows + 1;
                }
                int y = 0;
                Sheet("Zaun", "Z", 5, 20, ref y);
                Sheet("Uebergang", "U", 5, 20, ref y);
                // Hohes Gras: Variante je Spalte, animiert
                for (int c = 0; c < 16; c++)
                {
                    var t = AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/Animiert/HohesGras_{c}_v0.asset");
                    if (t != null) tm.SetTile(new Vector3Int(c, y, 0), t);
                }
            });
        }
    }
}
