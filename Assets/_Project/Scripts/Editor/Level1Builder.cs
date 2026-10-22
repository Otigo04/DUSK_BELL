using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using Nightward.Core;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Tilemaps;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.Tilemaps;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Erzeugt Tile-Assets, Paletten und die Szene Level_01 aus Tileset_Terrain, Tileset_Wald und Objekte/*.png.
    /// Der Wald besteht aus Einzelbaeumen (Stamm auf der Objekt-Ebene, Krone ueber der Spielfigur),
    /// Waldgras, Waldweg und Unterholz. Kollision nur am Stammfuss.
    /// </summary>
    public static class Level1Builder
    {
        const string TilesRoot = "Assets/_Project/Art/Tiles";
        const string ObjDir = TilesRoot + "/Objekte";
        const string TerrainPng = TilesRoot + "/Tileset_Terrain.png";
        const string WaldPng = TilesRoot + "/Tileset_Wald.png";
        const string TileAssets = TilesRoot + "/TileAssets";
        const string AnimDir = TilesRoot + "/Animiert";
        const string PaletteDir = TilesRoot + "/Palettes";
        const string ScenePath = "Assets/_Project/Scenes/Game/Level_01.unity";
        const int Cell = 32, TCols = 20, TerrainRows = 7, WaldRows = 5;

        // Gesamtkarte inkl. Waldrand. Innenbereich = 0..47 x 0..31.
        const int MinX = -6, MaxX = 53, MinY = -6, MaxY = 37;
        const int W = MaxX - MinX + 1, H = MaxY - MinY + 1;
        const int InW = 48, InH = 32;

        // Sortierreihenfolge der Tilemaps
        const int OrderGround = 0, OrderDeco = 2, OrderBridge = 3, OrderObjects = 4, OrderCrowns = 20;

        // Tempo-Faktoren gegenueber den Zeiten in Animiert/_Liste.txt: ruhiger = kleiner
        const float WindFactor = 0.28f, FireFactor = 0.45f, LanternFactor = 0.22f, PlantFactor = 0.35f, DekoFactor = 0.25f, WaterFps = 0.7f;

        enum Ter { Grass, Dirt, Cobble, Water, Forest, ForestPath }

        static Ter[,] ter;
        static bool[,] blk;          // nur fuer Zufalls-Streuung reserviert
        static string[,] occ;        // belegte Zellen
        static bool[,] nearPW;       // Weg/Wasser in 1 Zelle Umkreis
        static bool[,] nearFP;       // Waldweg in 2 Zellen Umkreis
        static bool[,] forest, deadZone, solid;
        static int[,] forestDepth, openDist;
        static System.Random rng;
        static Dictionary<string, Vector2Int> size = new Dictionary<string, Vector2Int>();
        static Dictionary<string, int> pxWidth = new Dictionary<string, int>();
        static HashSet<string> used = new HashSet<string>();
        static List<string> issues = new List<string>();
        static Tilemap objMap, crownMap;
        static List<Vector3> campLights = new List<Vector3>();
        static List<Vector3> lanternLights = new List<Vector3>();
        static List<Vector2> trunkFeet = new List<Vector2>();
        static Dictionary<string, List<TileBase>> animObj = new Dictionary<string, List<TileBase>>();
        static Dictionary<int, List<TileBase>> animDeko = new Dictionary<int, List<TileBase>>();

        // ---------------------------------------------------------------- Menu

        [MenuItem("Nightward/Level 1/Alles bauen")]
        public static void BuildAll()
        {
            ConfigureImports();
            CreateTilesAndPalettes();
            BuildLevel();
        }

        static void SetupObjectImporter(string path)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Single;
            ti.spritePixelsPerUnit = Cell;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            var s = new TextureImporterSettings();
            ti.ReadTextureSettings(s);
            s.spriteAlignment = (int)SpriteAlignment.BottomLeft;
            s.spriteMeshType = SpriteMeshType.FullRect;
            ti.SetTextureSettings(s);
            ti.SaveAndReimport();
        }

        static void SliceSheet(string path, string prefix, int rows)
        {
            var tt = (TextureImporter)AssetImporter.GetAtPath(path);
            tt.textureType = TextureImporterType.Sprite;
            tt.spriteImportMode = SpriteImportMode.Multiple;
            tt.spritePixelsPerUnit = Cell;
            tt.filterMode = FilterMode.Point;
            tt.textureCompression = TextureImporterCompression.Uncompressed;
            tt.mipmapEnabled = false;
            tt.alphaIsTransparency = true;
            tt.GetSourceTextureWidthAndHeight(out int tw, out int th);
            var metas = new List<SpriteMetaData>();
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < TCols; c++)
                    metas.Add(new SpriteMetaData
                    {
                        name = $"{prefix}_{r}_{c}",
                        rect = new Rect(c * Cell, th - (r + 1) * Cell, Cell, Cell),
                        alignment = (int)SpriteAlignment.Center,
                        pivot = new Vector2(0.5f, 0.5f)
                    });
#pragma warning disable CS0618
            tt.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            tt.SaveAndReimport();
        }

        [MenuItem("Nightward/Level 1/1 Import konfigurieren")]
        public static void ConfigureImports()
        {
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { ObjDir }))
                SetupObjectImporter(AssetDatabase.GUIDToAssetPath(guid));
            SliceSheet(TerrainPng, "T", TerrainRows);
            SliceSheet(WaldPng, "W", WaldRows);
            ConfigureAnimImports();
        }

        // ---------------------------------------------------------------- Animationen

        static List<(string name, int frames, int ms)> ReadAnimList()
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

        static string AnimBase(string name)
        {
            var m = Regex.Match(name, @"^(.+)_(Wind|Anim)$");
            return m.Success ? m.Groups[1].Value : name;
        }

        static TextureImporter AnimImporter(string path)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = Cell;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            return ti;
        }

        /// <summary>Zerlegt die Animationsstreifen in Einzelbilder (Objekte: Pivot unten links).</summary>
        static void ConfigureAnimImports()
        {
            foreach (var (name, frames, ms) in ReadAnimList())
            {
                string p = $"{AnimDir}/{name}.png";
                if (!File.Exists(p)) continue;
                var ti = AnimImporter(p);
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

            // Deko-Zeile des Terrain-Tilesets: 4 Frames als Zeilen, je 20 Kacheln
            string dp = AnimDir + "/Tileset_Deko_Wind.png";
            if (File.Exists(dp))
            {
                var ti = AnimImporter(dp);
                ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
                var metas = new List<SpriteMetaData>();
                for (int f = 0; f < 4; f++)
                    for (int c = 0; c < TCols; c++)
                        metas.Add(new SpriteMetaData
                        {
                            name = $"D_{f}_{c}",
                            rect = new Rect(c * Cell, th - (f + 1) * Cell, Cell, Cell),
                            alignment = (int)SpriteAlignment.Center,
                            pivot = new Vector2(0.5f, 0.5f)
                        });
#pragma warning disable CS0618
                ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
                ti.SaveAndReimport();
            }
        }

        static AnimatedTile MakeAnimTile(string path, Sprite[] frames, float fps, int startFrame)
        {
            var a = AssetDatabase.LoadAssetAtPath<AnimatedTile>(path);
            bool isNew = a == null;
            if (isNew) a = ScriptableObject.CreateInstance<AnimatedTile>();
            a.m_AnimatedSprites = frames;
            a.m_MinSpeed = fps;
            a.m_MaxSpeed = fps;
            a.m_AnimationStartFrame = startFrame;
            if (isNew) AssetDatabase.CreateAsset(a, path);
            else EditorUtility.SetDirty(a);
            return a;
        }

        static float SpeedFactor(string name)
        {
            if (name.StartsWith("Lagerfeuer") || name.StartsWith("Kochfeuer") || name.StartsWith("Feuerschale") ||
                name.StartsWith("Fackel") || name.StartsWith("Kerzen") || name.StartsWith("Windlicht")) return FireFactor;
            if (name.StartsWith("Laterne")) return LanternFactor;
            if (name.StartsWith("Schilf") || name.StartsWith("Seerosen") || name.StartsWith("Brunnen") ||
                name.StartsWith("Wassertrog") || name.StartsWith("Fass_Wasser")) return PlantFactor;
            if (name.StartsWith("Fahne")) return 0.4f;
            if (name.StartsWith("Kristall") || name.StartsWith("Runenstein")) return 0.35f;
            return WindFactor;
        }

        /// <summary>
        /// Setzt das Tempo ALLER vorhandenen animierten Tiles (auch der aus TilesetErweiterung) auf ruhige Werte.
        /// Aendert nur die Geschwindigkeit, Assets und GUIDs bleiben unveraendert.
        /// </summary>
        [MenuItem("Nightward/Level 1/Animationen beruhigen")]
        public static void ApplyAnimSpeeds()
        {
            float[] jitter = { 1f, 0.9f, 1.1f, 0.95f };
            int n = 0;
            foreach (var (name, frames, ms) in ReadAnimList())
                for (int k = 0; k < 4; k++)
                {
                    var a = AssetDatabase.LoadAssetAtPath<AnimatedTile>($"{TileAssets}/Animiert/{name}_v{k}.asset");
                    if (a == null) continue;
                    float fps = 1000f / ms * SpeedFactor(name) * jitter[k];
                    a.m_MinSpeed = fps;
                    a.m_MaxSpeed = fps;
                    EditorUtility.SetDirty(a);
                    n++;
                }
            for (int c = 0; c < TCols; c++)
                for (int k = 0; k < 4; k++)
                {
                    var a = AssetDatabase.LoadAssetAtPath<AnimatedTile>($"{TileAssets}/Animiert/Deko_{c}_v{k}.asset");
                    if (a == null) continue;
                    a.m_MinSpeed = 1000f / 300f * DekoFactor * jitter[k];
                    a.m_MaxSpeed = a.m_MinSpeed;
                    EditorUtility.SetDirty(a);
                    n++;
                }
            var water = AssetDatabase.LoadAssetAtPath<AnimatedTile>(TileAssets + "/Terrain/Wasser_Anim.asset");
            if (water != null) { water.m_MinSpeed = WaterFps; water.m_MaxSpeed = WaterFps; EditorUtility.SetDirty(water); n++; }
            AssetDatabase.SaveAssets();
            Debug.Log($"Animationen beruhigt: {n} animierte Tiles.");
        }

        /// <summary>Legt pro Streifen vier AnimatedTiles mit versetztem Start und leicht anderem Tempo an.</summary>
        static void CreateAnimatedTiles()
        {
            float[] jitter = { 1f, 0.9f, 1.1f, 0.95f };
            foreach (var (name, frames, ms) in ReadAnimList())
            {
                if (!size.ContainsKey(AnimBase(name))) continue;   // Objekt gibt es nicht mehr
                string p = $"{AnimDir}/{name}.png";
                var byName = new Dictionary<string, Sprite>();
                foreach (var o in AssetDatabase.LoadAllAssetsAtPath(p)) if (o is Sprite sp) byName[sp.name] = sp;
                var arr = new Sprite[frames];
                bool ok = true;
                for (int i = 0; i < frames; i++) ok &= byName.TryGetValue($"{name}_{i}", out arr[i]);
                if (!ok) { Debug.LogWarning("Animation unvollstaendig: " + name); continue; }
                int variants = Mathf.Min(4, frames);
                for (int k = 0; k < variants; k++)
                    MakeAnimTile($"{TileAssets}/Animiert/{name}_v{k}.asset", arr, 1000f / ms * SpeedFactor(name) * jitter[k], k * frames / variants);
            }

            var deko = new Dictionary<string, Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(AnimDir + "/Tileset_Deko_Wind.png")) if (o is Sprite sp) deko[sp.name] = sp;
            if (deko.Count > 0)
                for (int c = 0; c < TCols; c++)
                {
                    var arr = new Sprite[4];
                    for (int f = 0; f < 4; f++) arr[f] = deko[$"D_{f}_{c}"];
                    for (int k = 0; k < 4; k++)
                        MakeAnimTile($"{TileAssets}/Animiert/Deko_{c}_v{k}.asset", arr, 1000f / 300f * DekoFactor * jitter[k], k);
                }
            AssetDatabase.SaveAssets();
        }

        static void LoadAnimVariants()
        {
            animObj.Clear();
            animDeko.Clear();
            var rxObj = new Regex(@"^(.+)_(Wind|Anim)_v\d+$");
            var rxDeko = new Regex(@"^Deko_(\d+)_v\d+$");
            foreach (var guid in AssetDatabase.FindAssets("t:TileBase", new[] { TileAssets + "/Animiert" }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var tile = AssetDatabase.LoadAssetAtPath<TileBase>(path);
                string n = Path.GetFileNameWithoutExtension(path);
                var m = rxDeko.Match(n);
                if (m.Success)
                {
                    int c = int.Parse(m.Groups[1].Value);
                    if (!animDeko.ContainsKey(c)) animDeko[c] = new List<TileBase>();
                    animDeko[c].Add(tile);
                    continue;
                }
                m = rxObj.Match(n);
                if (!m.Success) continue;
                string b = m.Groups[1].Value;
                if (!size.ContainsKey(b)) continue;
                if (!animObj.ContainsKey(b)) animObj[b] = new List<TileBase>();
                animObj[b].Add(tile);
            }
        }

        static TileBase PickObjTile(string name)
        {
            if (animObj.TryGetValue(name, out var list) && list.Count > 0) return list[rng.Next(list.Count)];
            return ObjTile(name);
        }

        static TileBase DecoTile(int col)
        {
            if (animDeko.TryGetValue(col, out var list) && list.Count > 0) return list[rng.Next(list.Count)];
            return LoadTerrain(5, col);
        }

        // ---------------------------------------------------------------- Tiles und Paletten

        // Ordner nur anlegen, nie loeschen: TilesetErweiterung.cs schreibt ebenfalls nach TileAssets
        static void EnsureFolder(string path)
        {
            if (!AssetDatabase.IsValidFolder(path))
                AssetDatabase.CreateFolder(Path.GetDirectoryName(path).Replace('\\', '/'), Path.GetFileName(path));
        }

        [MenuItem("Nightward/Level 1/2 Tiles und Paletten")]
        public static void CreateTilesAndPalettes()
        {
            ReadSizes();
            // alte, zusammengesetzte Baeume (ersetzt durch Stamm/Krone-Paare) entfernen
            if (AssetDatabase.IsValidFolder(TilesRoot + "/Zusammengesetzt")) AssetDatabase.DeleteAsset(TilesRoot + "/Zusammengesetzt");
            EnsureFolder(TileAssets);
            foreach (var f in new[] { "Terrain", "Wald", "Objekte", "Animiert" }) EnsureFolder($"{TileAssets}/{f}");
            EnsureFolder(PaletteDir);

            var terrain = new Dictionary<string, Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(TerrainPng))
                if (o is Sprite sp) terrain[sp.name] = sp;
            var wald = new Dictionary<string, Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(WaldPng))
                if (o is Sprite sp) wald[sp.name] = sp;

            foreach (var kv in terrain) MakeTile($"{TileAssets}/Terrain/{kv.Key}.asset", kv.Value);
            foreach (var kv in wald) MakeTile($"{TileAssets}/Wald/{kv.Key}.asset", kv.Value);

            var anim = ScriptableObject.CreateInstance<AnimatedTile>();
            anim.m_AnimatedSprites = new[] { terrain["T_4_16"], terrain["T_4_17"], terrain["T_4_18"], terrain["T_4_19"] };
            anim.m_MinSpeed = WaterFps;
            anim.m_MaxSpeed = WaterFps;
            var waterAsset = AssetDatabase.LoadAssetAtPath<AnimatedTile>(TileAssets + "/Terrain/Wasser_Anim.asset");
            if (waterAsset == null) AssetDatabase.CreateAsset(anim, TileAssets + "/Terrain/Wasser_Anim.asset");
            else
            {
                waterAsset.m_AnimatedSprites = anim.m_AnimatedSprites;
                waterAsset.m_MinSpeed = WaterFps;
                waterAsset.m_MaxSpeed = WaterFps;
                EditorUtility.SetDirty(waterAsset);
            }

            // unsichtbare Kollisionskachel
            if (AssetDatabase.LoadAssetAtPath<Tile>(TileAssets + "/Collision_Block.asset") == null)
            {
                var colTile = ScriptableObject.CreateInstance<Tile>();
                colTile.colliderType = Tile.ColliderType.Grid;
                AssetDatabase.CreateAsset(colTile, TileAssets + "/Collision_Block.asset");
            }

            foreach (var kv in size)
            {
                var sp = AssetDatabase.LoadAssetAtPath<Sprite>($"{ObjDir}/{kv.Key}.png");
                if (sp == null) { Debug.LogWarning("Sprite fehlt: " + kv.Key); continue; }
                MakeTile($"{TileAssets}/Objekte/{kv.Key}.asset", sp);
            }
            AssetDatabase.SaveAssets();
            CreateAnimatedTiles();
            LoadAnimVariants();

            MakePalette("Pal_Terrain", Vector3.zero, tm =>
            {
                for (int r = 0; r < TerrainRows; r++)
                    for (int c = 0; c < TCols; c++)
                    {
                        var t = AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Terrain/T_{r}_{c}.asset");
                        if (t != null) tm.SetTile(new Vector3Int(c, TerrainRows - 1 - r, 0), t);
                    }
                tm.SetTile(new Vector3Int(TCols, 2, 0), AssetDatabase.LoadAssetAtPath<TileBase>(TileAssets + "/Terrain/Wasser_Anim.asset"));
            });

            MakePalette("Pal_Wald", Vector3.zero, tm =>
            {
                for (int r = 0; r < WaldRows; r++)
                    for (int c = 0; c < TCols; c++)
                    {
                        var t = AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Wald/W_{r}_{c}.asset");
                        if (t != null) tm.SetTile(new Vector3Int(c, WaldRows - 1 - r, 0), t);
                    }
            });

            MakePalette("Pal_Objekte", Vector3.zero, tm =>
            {
                var cats = new Dictionary<string, List<string>>();
                string[] order = { "Baeume", "Pflanzen", "Holz", "Steine", "Props" };
                foreach (var o in order) cats[o] = new List<string>();
                var names = new List<string>(size.Keys);
                names.Sort();
                foreach (var n in names) cats[Category(n)].Add(n);

                int baseY = 0;
                foreach (var cat in order)
                {
                    int x = 0, rowH = 1;
                    var line = new List<(string n, int x)>();
                    void Flush()
                    {
                        foreach (var (n, px) in line)
                            tm.SetTile(new Vector3Int(px, baseY, 0), PickPaletteTile(n));
                        baseY -= rowH + 1;
                        line.Clear();
                        x = 0; rowH = 1;
                    }
                    foreach (var n in cats[cat])
                    {
                        if (x + size[n].x > 40) Flush();
                        line.Add((n, x));
                        x += size[n].x + 1;
                        rowH = Mathf.Max(rowH, size[n].y);
                    }
                    if (line.Count > 0) Flush();
                    baseY -= 1;
                }
            });
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
        }

        static TileBase PickPaletteTile(string n)
        {
            if (animObj.TryGetValue(n, out var list) && list.Count > 0) return list[0];
            return AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Objekte/{n}.asset");
        }

        static string Category(string n)
        {
            if (n.StartsWith("Birke") || n.StartsWith("Eiche") || n.StartsWith("Kiefer") || n.StartsWith("Fichte") || n == "Baum_Tot") return "Baeume";
            if (n.StartsWith("Busch") || n.StartsWith("Brombeer") || n.StartsWith("Heidelbeer") || n.StartsWith("Farn") || n == "Hecke" || n == "Schilf" || n == "Seerosen") return "Pflanzen";
            if (n.StartsWith("Stein")) return "Steine";
            if (n.StartsWith("Baumst") || n.StartsWith("Stamm") || n == "Aeste" || n == "Wurzeln") return "Holz";
            return "Props";
        }

        static void MakeTile(string path, Sprite sp)
        {
            var existing = AssetDatabase.LoadAssetAtPath<Tile>(path);
            if (existing != null)
            {
                existing.sprite = sp;
                existing.colliderType = Tile.ColliderType.None;
                EditorUtility.SetDirty(existing);
                return;
            }
            var t = ScriptableObject.CreateInstance<Tile>();
            t.sprite = sp;
            t.colliderType = Tile.ColliderType.None;
            AssetDatabase.CreateAsset(t, path);
        }

        static void MakePalette(string name, Vector3 anchor, Action<Tilemap> fill)
        {
            AssetDatabase.DeleteAsset($"{PaletteDir}/{name}.prefab");
            var go = GridPaletteUtility.CreateNewPalette(PaletteDir, name, GridLayout.CellLayout.Rectangle,
                GridPalette.CellSizing.Automatic, Vector3.one, GridLayout.CellSwizzle.XYZ);
            var path = AssetDatabase.GetAssetPath(go);
            var contents = PrefabUtility.LoadPrefabContents(path);
            var tm = contents.GetComponentInChildren<Tilemap>();
            tm.tileAnchor = anchor;
            fill(tm);
            tm.CompressBounds();
            PrefabUtility.SaveAsPrefabAsset(contents, path);
            PrefabUtility.UnloadPrefabContents(contents);
        }

        static void ReadSizes()
        {
            size.Clear();
            pxWidth.Clear();
            var rx = new Regex(@"^(\w+)\s*\|\s*(\d+)x(\d+)");
            foreach (var line in File.ReadAllLines(ObjDir + "/_Liste.txt"))
            {
                var m = rx.Match(line);
                if (!m.Success) continue;
                string n = m.Groups[1].Value;
                int pw = int.Parse(m.Groups[2].Value), ph = int.Parse(m.Groups[3].Value);
                // Footprint in ganzen Zellen aufgerundet (z.B. 48 px = 2 Zellen)
                size[n] = new Vector2Int(Mathf.CeilToInt(pw / (float)Cell), Mathf.CeilToInt(ph / (float)Cell));
                pxWidth[n] = pw;
            }
        }

        // ---------------------------------------------------------------- Karten-Helfer

        static bool InMap(int x, int y) => x >= MinX && x <= MaxX && y >= MinY && y <= MaxY;

        static Ter GetT(int x, int y)
        {
            x = Mathf.Clamp(x, MinX, MaxX);
            y = Mathf.Clamp(y, MinY, MaxY);
            return ter[x - MinX, y - MinY];
        }

        static void SetT(int x, int y, Ter t)
        {
            if (!InMap(x, y)) return;
            ter[x - MinX, y - MinY] = t;
        }

        static bool GetM(bool[,] m, int x, int y)
        {
            x = Mathf.Clamp(x, MinX, MaxX);
            y = Mathf.Clamp(y, MinY, MaxY);
            return m[x - MinX, y - MinY];
        }

        static bool Blocked(int x, int y) => !InMap(x, y) || blk[x - MinX, y - MinY];
        static string Occ(int x, int y) => !InMap(x, y) ? "Rand" : occ[x - MinX, y - MinY];

        static void Reserve(int x0, int y0, int x1, int y1)
        {
            for (int x = x0; x <= x1; x++)
                for (int y = y0; y <= y1; y++)
                    if (InMap(x, y)) blk[x - MinX, y - MinY] = true;
        }

        static void FillRect(Ter t, int x0, int y0, int x1, int y1)
        {
            for (int x = x0; x <= x1; x++)
                for (int y = y0; y <= y1; y++) SetT(x, y, t);
        }

        static void FillEllipse(Ter t, float cx, float cy, float rx, float ry, float wob, float seed)
        {
            for (int x = Mathf.FloorToInt(cx - rx - 3); x <= Mathf.CeilToInt(cx + rx + 3); x++)
                for (int y = Mathf.FloorToInt(cy - ry - 3); y <= Mathf.CeilToInt(cy + ry + 3); y++)
                {
                    float dx = (x - cx) / rx, dy = (y - cy) / ry;
                    float a = Mathf.Atan2(dy, dx);
                    float r = 1f + wob * Mathf.Sin(a * 3f + seed) + wob * 0.6f * Mathf.Sin(a * 5f + seed * 2f);
                    if (dx * dx + dy * dy <= r * r) SetT(x, y, t);
                }
        }

        static void Line(Ter t, int w, params int[] pts)
        {
            for (int i = 0; i + 3 < pts.Length; i += 2)
            {
                int x0 = pts[i], y0 = pts[i + 1], x1 = pts[i + 2], y1 = pts[i + 3];
                int steps = Mathf.Max(Mathf.Abs(x1 - x0), Mathf.Abs(y1 - y0));
                int lastX = x0, lastY = y0;
                for (int s = 0; s <= steps; s++)
                {
                    float f = steps == 0 ? 0 : (float)s / steps;
                    int px = Mathf.RoundToInt(Mathf.Lerp(x0, x1, f)), py = Mathf.RoundToInt(Mathf.Lerp(y0, y1, f));
                    // Diagonalen mit einem Zwischenfeld verbinden, damit der Weg zusammenhaengt
                    if (px != lastX && py != lastY)
                        for (int ax = 0; ax < w; ax++)
                            for (int ay = 0; ay < w; ay++) SetT(px + ax, lastY + ay, t);
                    for (int ax = 0; ax < w; ax++)
                        for (int ay = 0; ay < w; ay++) SetT(px + ax, py + ay, t);
                    lastX = px; lastY = py;
                }
            }
        }

        // ---------------------------------------------------------------- Terrain

        static void BuildTerrain()
        {
            ter = new Ter[W, H];
            blk = new bool[W, H];
            occ = new string[W, H];
            solid = new bool[W, H];

            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                    if (x < 0 || x >= InW || y < 0 || y >= InH) SetT(x, y, Ter.Forest);

            FillEllipse(Ter.Forest, 41, 26, 8, 6, 0.1f, 1.3f);                  // totes Lager

            Line(Ter.Dirt, 1, 19, 14, -6, 14);                                  // West
            Line(Ter.Dirt, 2, 28, 14, 53, 14);                                  // Ostweg
            Line(Ter.Dirt, 1, 23, 19, 23, 22, 24, 25, 24, 28, 23, 31, 23, 37);  // Nord
            Line(Ter.Dirt, 1, 23, 12, 23, 2, 24, 0, 24, -6);                    // Sued
            Line(Ter.Dirt, 1, 35, 13, 35, 11);                                  // Hoftor
            Line(Ter.Dirt, 1, 38, 16, 38, 24, 39, 24);                          // Pfad zum toten Lager
            FillRect(Ter.Dirt, 32, 4, 40, 10);                                  // Holzplatz

            FillEllipse(Ter.Cobble, 23, 15.5f, 5.2f, 4.6f, 0.05f, 0.7f);

            FillEllipse(Ter.Water, 10, 24, 5.5f, 4.2f, 0.08f, 2.1f);
            for (int y = 7; y <= 21; y++)
            {
                int sx = 9 + Mathf.RoundToInt(Mathf.Sin(y * 0.5f));
                FillRect(Ter.Water, sx, y, sx + 2, y);
            }
            for (int x = 9; x <= 27; x++)
            {
                int dy = (x < 19 || x > 27) ? Mathf.RoundToInt(Mathf.Sin(x * 0.45f)) : 0;
                FillRect(Ter.Water, x, 5 + dy, x, 7 + dy);
            }
            FillEllipse(Ter.Water, 28.3f, 6, 2.0f, 2.2f, 0.04f, 4.2f);
            FillEllipse(Ter.Water, 47, 8, 3.2f, 2.8f, 0.06f, 5.5f);
        }

        // ---------------------------------------------------------------- Waldzone

        /// <summary>Waldzone = Waldrand (unregelmaessig ins Innere) und totes Lager. Wege darin werden zu Waldwegen.</summary>
        static void ComputeForest()
        {
            forest = new bool[W, H];
            deadZone = new bool[W, H];
            forestDepth = new int[W, H];
            openDist = new int[W, H];

            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    bool outside = x < 0 || x >= InW || y < 0 || y >= InH;
                    bool f = true;
                    if (!outside)
                    {
                        int tN = 5 + Mathf.RoundToInt(1.6f * Mathf.Sin(x * 0.33f + 0.7f) + 1.0f * Mathf.Sin(x * 0.85f + 2f));
                        int tS = 1 + Mathf.RoundToInt(0.7f * Mathf.Sin(x * 0.5f) + 0.6f * Mathf.Sin(x * 1.1f));
                        int tW = 1 + Mathf.RoundToInt(0.7f * Mathf.Sin(y * 0.4f) + 0.6f * Mathf.Sin(y * 1.1f + 1f));
                        int tE = 1 + Mathf.RoundToInt(0.7f * Mathf.Sin(y * 0.45f + 2f) + 0.6f * Mathf.Sin(y * 1.0f));
                        f = y >= InH - tN || y < tS || x < tW || x >= InW - tE;
                        float dx = (x - 41f) / 8.5f, dy = (y - 26f) / 6.5f;
                        if (dx * dx + dy * dy < 1f) { f = true; deadZone[x - MinX, y - MinY] = true; }
                    }
                    forest[x - MinX, y - MinY] = f;
                }

            // Ausreisser entfernen, kleine Luecken schliessen
            for (int pass = 0; pass < 2; pass++)
            {
                var nf = (bool[,])forest.Clone();
                for (int x = MinX; x <= MaxX; x++)
                    for (int y = MinY; y <= MaxY; y++)
                    {
                        int n = (GetM(forest, x, y + 1) ? 1 : 0) + (GetM(forest, x + 1, y) ? 1 : 0) + (GetM(forest, x, y - 1) ? 1 : 0) + (GetM(forest, x - 1, y) ? 1 : 0);
                        bool f = forest[x - MinX, y - MinY];
                        if (f && n < 2) nf[x - MinX, y - MinY] = false;
                        else if (!f && n >= 3) nf[x - MinX, y - MinY] = true;
                    }
                forest = nf;
            }

            // Boden anpassen: Wiese -> Waldgras, Erdweg -> Waldweg
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    if (!forest[x - MinX, y - MinY]) continue;
                    var t = GetT(x, y);
                    if (t == Ter.Grass) SetT(x, y, Ter.Forest);
                    else if (t == Ter.Dirt) SetT(x, y, Ter.ForestPath);
                }

            // Abstand der Waldzellen zur offenen Flaeche (Chebyshev, max 9) und umgekehrt
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    bool inF = forest[x - MinX, y - MinY];
                    int best = 99;
                    for (int dx = -9; dx <= 9; dx++)
                        for (int dy = -9; dy <= 9; dy++)
                        {
                            int nx = x + dx, ny = y + dy;
                            if (!InMap(nx, ny) || forest[nx - MinX, ny - MinY] == inF) continue;
                            best = Mathf.Min(best, Mathf.Max(Mathf.Abs(dx), Mathf.Abs(dy)));
                        }
                    if (inF) forestDepth[x - MinX, y - MinY] = best;
                    else openDist[x - MinX, y - MinY] = best;
                }
        }

        // ---------------------------------------------------------------- Autotiling

        static bool IsPathy(Ter t) => t == Ter.Dirt || t == Ter.Cobble || t == Ter.ForestPath;

        static bool Conn(Ter me, Ter n)
        {
            switch (me)
            {
                case Ter.Dirt: return n == Ter.Dirt || n == Ter.Cobble || n == Ter.ForestPath;
                case Ter.ForestPath: return n == Ter.ForestPath || n == Ter.Dirt || n == Ter.Cobble;
                case Ter.Forest: return n == Ter.Forest || n == Ter.ForestPath;
                default: return n == me;
            }
        }

        static TileBase LoadTerrain(int r, int c) =>
            AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Terrain/T_{r}_{c}.asset");

        static TileBase LoadWald(int r, int c) =>
            AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Wald/W_{r}_{c}.asset");

        static int ForestGrassVariant()
        {
            double d = rng.NextDouble();
            if (d < 0.38) return 0;     // normal
            if (d < 0.50) return 1;     // Laub
            if (d < 0.64) return 2;     // Moos
            if (d < 0.76) return 3;     // Nadeln
            if (d < 0.84) return 4;     // Steinchen
            if (d < 0.91) return 5;     // Wurzel
            if (d < 0.96) return 6;     // Lichtung
            return 7;                   // Klee
        }

        static TileBase TerrainTile(int x, int y)
        {
            var t = GetT(x, y);
            if (t == Ter.Grass) return LoadTerrain(4, GrassVariant());

            bool n = Conn(t, GetT(x, y + 1)), e = Conn(t, GetT(x + 1, y)),
                 s = Conn(t, GetT(x, y - 1)), w = Conn(t, GetT(x - 1, y));
            int idx = (n ? 1 : 0) | (e ? 2 : 0) | (s ? 4 : 0) | (w ? 8 : 0);
            bool ne = Conn(t, GetT(x + 1, y + 1)), se = Conn(t, GetT(x + 1, y - 1)),
                 sw = Conn(t, GetT(x - 1, y - 1)), nw = Conn(t, GetT(x - 1, y + 1));
            int corner = idx != 15 ? -1 : !ne ? 16 : !se ? 17 : !sw ? 18 : !nw ? 19 : -1;

            // Wald-Tileset: Zeile 0 Waldweg, Zeile 1 Waldgras-Rand zur Wiese, Zeile 2 Fuellungen
            if (t == Ter.ForestPath)
            {
                if (idx != 15) return LoadWald(0, idx);
                if (corner >= 0) return LoadWald(0, corner);
                return LoadWald(2, 8 + rng.Next(3));
            }
            if (t == Ter.Forest)
            {
                if (idx != 15) return LoadWald(1, idx);
                if (corner >= 0) return LoadWald(1, corner);
                return LoadWald(2, ForestGrassVariant());
            }

            int row = t == Ter.Dirt ? 0 : t == Ter.Cobble ? 1 : 2;
            if (idx != 15) return LoadTerrain(row, idx);
            if (corner >= 0) return LoadTerrain(row, corner);
            switch (t)
            {
                case Ter.Dirt: return LoadTerrain(4, 8 + rng.Next(3));
                case Ter.Cobble: return LoadTerrain(4, 11 + rng.Next(2));
                default: return AssetDatabase.LoadAssetAtPath<TileBase>(TileAssets + "/Terrain/Wasser_Anim.asset");
            }
        }

        static int GrassVariant()
        {
            double d = rng.NextDouble();
            if (d < 0.55) return 0;
            return 1 + rng.Next(7);
        }

        static bool IsShore(int x, int y)
        {
            if (GetT(x, y) != Ter.Water) return false;
            return !(Conn(Ter.Water, GetT(x, y + 1)) && Conn(Ter.Water, GetT(x + 1, y)) &&
                     Conn(Ter.Water, GetT(x, y - 1)) && Conn(Ter.Water, GetT(x - 1, y)));
        }

        // ---------------------------------------------------------------- Objekte

        static TileBase ObjTile(string name) =>
            AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Objekte/{name}.asset");

        static bool IsGround(int x, int y)
        {
            var t = GetT(x, y);
            return t == Ter.Grass || t == Ter.Forest;
        }

        static bool WaterObject(string n) => n == "Schilf" || n == "Seerosen";

        static bool BlocksMovement(string n)
        {
            if (n == "Stein_Platte" || n.StartsWith("Stein_Klein") || n == "Stein_Moos" || n == "Aeste" || n == "Wurzeln" ||
                n == "Schilf" || n == "Seerosen" || n.StartsWith("Farn")) return false;
            return true;
        }

        static bool IsTreeName(string n) =>
            n.StartsWith("Birke_") || n.StartsWith("Eiche_") || n.StartsWith("Kiefer_") || n.StartsWith("Fichte_") || n == "Baum_Tot";

        static bool IsTreePart(string n) => n.EndsWith("_Krone") || n.EndsWith("_Stamm");

        static bool HasSplit(string n) => size.ContainsKey(n + "_Stamm") && size.ContainsKey(n + "_Krone");

        /// <summary>Setzt ein Objekt (kein Baum), prueft Terrain und Ueberlappung.</summary>
        static bool Put(string name, int x, int y, bool quiet = false)
        {
            if (!size.ContainsKey(name)) { issues.Add("Unbekanntes Objekt " + name); return false; }
            var sz = size[name];
            for (int i = 0; i < sz.x; i++)
            {
                var t = InMap(x + i, y) ? GetT(x + i, y) : Ter.Water;
                bool okOnWater = WaterObject(name) || name == "Stein_Platte";
                if (WaterObject(name) ? t != Ter.Water : (t == Ter.Water && !okOnWater))
                {
                    if (!quiet) issues.Add($"{name}@({x},{y}): falsches Terrain {t}");
                    return false;
                }
            }
            for (int i = 0; i < sz.x; i++)
                for (int j = 0; j < sz.y; j++)
                {
                    if (!InMap(x + i, y + j)) continue;
                    var o = Occ(x + i, y + j);
                    if (o != null)
                    {
                        if (!quiet) issues.Add($"{name}@({x},{y}): ueberlappt {o}");
                        return false;
                    }
                }
            for (int i = 0; i < sz.x; i++)
                for (int j = 0; j < sz.y; j++)
                    if (InMap(x + i, y + j)) occ[x + i - MinX, y + j - MinY] = name;
            if (BlocksMovement(name))
                for (int i = 0; i < sz.x; i++)
                    if (InMap(x + i, y)) solid[x + i - MinX, y - MinY] = true;
            objMap.SetTile(new Vector3Int(x, y, 0), PickObjTile(name));
            used.Add(name);
            return true;
        }

        static bool CanTree(int x, int y, string name, bool ignoreBlk)
        {
            var sz = size[name];
            int hf = Mathf.Min(sz.y, 2);                 // belegte Zeilen am Fuss
            if (x < MinX || x + sz.x - 1 > MaxX || y < MinY || y + hf - 1 > MaxY) return false;
            for (int cx = x; cx < x + sz.x; cx++)
                for (int cy = y; cy < y + hf; cy++)
                {
                    if (!ignoreBlk && Blocked(cx, cy)) return false;
                    if (!IsGround(cx, cy) || Occ(cx, cy) != null) return false;
                    if (nearPW[cx - MinX, cy - MinY] || nearFP[cx - MinX, cy - MinY]) return false;
                }
            return true;
        }

        /// <summary>Setzt einen Baum: Stamm auf die Objekt-Ebene, Krone auf die Kronen-Ebene (falls geteilt).</summary>
        static bool PutTree(string name, int x, int y)
        {
            var sz = size[name];
            int hf = Mathf.Min(sz.y, 2);
            for (int i = 0; i < sz.x; i++)
                for (int j = 0; j < hf; j++) occ[x + i - MinX, y + j - MinY] = name;
            var cell = new Vector3Int(x, y, 0);
            bool split = HasSplit(name);
            objMap.SetTile(cell, ObjTile(split ? name + "_Stamm" : name));
            if (split) crownMap.SetTile(cell, ObjTile(name + "_Krone"));
            used.Add(name);
            if (split) { used.Add(name + "_Stamm"); used.Add(name + "_Krone"); }
            // Kollision nur am Stammfuss, Mitte des Sprites
            trunkFeet.Add(new Vector2(x + pxWidth[name] / 64f, y + 0.3f));
            return true;
        }

        static bool TryTreeName(string name, int x, int y, bool ignoreBlk = false)
        {
            if (!size.ContainsKey(name) || !CanTree(x, y, name, ignoreBlk)) return false;
            return PutTree(name, x, y);
        }

        /// <summary>Platziert einen bestimmten Baum moeglichst nahe am Wunschort.</summary>
        static bool HeroTree(string name, int px, int py)
        {
            for (int r = 0; r <= 6; r++)
                for (int dx = -r; dx <= r; dx++)
                    for (int dy = -r; dy <= r; dy++)
                    {
                        if (Mathf.Max(Mathf.Abs(dx), Mathf.Abs(dy)) != r) continue;
                        if (TryTreeName(name, px + dx, py + dy, true)) return true;
                    }
            issues.Add($"HeroTree {name} nahe ({px},{py}) nicht platzierbar");
            return false;
        }

        static string Pick(params (string name, float w)[] opts)
        {
            float total = 0f;
            foreach (var o in opts) total += o.w;
            float r = (float)rng.NextDouble() * total;
            foreach (var o in opts)
            {
                r -= o.w;
                if (r <= 0f) return o.name;
            }
            return opts[opts.Length - 1].name;
        }

        /// <summary>Baumart je nach Region; tief im Wald dunkle Hintergrund-Varianten (_Fern).</summary>
        static string ForestTree(int x, int y, int depth)
        {
            string n;
            if (x >= 0 && x < InW && y >= 0 && y < InH && deadZone[x - MinX, y - MinY])
                n = Pick(("Baum_Tot", 5f), ("Fichte_Jung", 1f));
            else if (x <= 8)   // Westen: Herbstwald
                n = Pick(("Eiche_Herbst", 3f), ("Eiche_A", 1.5f), ("Eiche_B", 1f), ("Birke_A", 1.2f), ("Birke_B", 1.2f), ("Birke_C", 1f), ("Kiefer_A", 0.7f), ("Fichte_Hoch_B", 0.8f));
            else if (y >= 20 || x >= 40)   // Norden und Osten: Nadelwald
                n = Pick(("Fichte_Hoch_A", 3f), ("Fichte_Hoch_B", 3f), ("Fichte_Hoch_C", 3f), ("Fichte_Jung", 1f), ("Kiefer_A", 1f), ("Kiefer_B", 1f), ("Birke_A", 0.8f), ("Birke_C", 0.8f), ("Eiche_B", 0.8f));
            else   // Sueden: Mischwald
                n = Pick(("Eiche_A", 2f), ("Eiche_B", 2f), ("Eiche_Apfel", 0.3f), ("Birke_A", 1.5f), ("Birke_B", 1.5f), ("Birke_C", 1.2f), ("Kiefer_A", 1f), ("Kiefer_B", 1f), ("Fichte_Hoch_A", 1f), ("Fichte_Hoch_C", 1f), ("Fichte_Jung", 0.8f));
            if (depth >= 5 && rng.NextDouble() < 0.85 && size.ContainsKey(n + "_Fern")) n += "_Fern";
            return n;
        }

        static string ClearingTree(int x, int y)
        {
            if (x <= 8)
                return Pick(("Eiche_Herbst", 2f), ("Eiche_A", 1f), ("Birke_A", 1f), ("Birke_B", 1f), ("Birke_C", 1f), ("Fichte_Jung", 0.5f));
            if (y >= 17 || x >= 40)
                return Pick(("Fichte_Hoch_A", 2f), ("Fichte_Hoch_B", 2f), ("Fichte_Hoch_C", 2f), ("Fichte_Jung", 1.5f), ("Kiefer_A", 1f), ("Birke_B", 1f), ("Eiche_B", 1f));
            return Pick(("Eiche_A", 2f), ("Eiche_B", 2f), ("Birke_A", 1.5f), ("Birke_C", 1.5f), ("Kiefer_A", 1f), ("Kiefer_B", 1f), ("Fichte_Jung", 1f), ("Fichte_Hoch_B", 0.6f));
        }

        static List<Vector2Int> ShuffledCells()
        {
            var cells = new List<Vector2Int>();
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++) cells.Add(new Vector2Int(x, y));
            for (int i = cells.Count - 1; i > 0; i--)
            {
                int j = rng.Next(i + 1);
                (cells[i], cells[j]) = (cells[j], cells[i]);
            }
            return cells;
        }

        /// <summary>Dichter, begehbarer Wald: Einzelbaeume mit Abstand, hinten dunkel, vorne hell.</summary>
        static void FillForest()
        {
            foreach (var c in ShuffledCells())
            {
                if (!forest[c.x - MinX, c.y - MinY]) continue;
                int depth = forestDepth[c.x - MinX, c.y - MinY];
                double p = deadZone[c.x - MinX, c.y - MinY] ? 0.10 : depth <= 1 ? 0.45 : 0.62;
                if (rng.NextDouble() > p) continue;
                for (int a = 0; a < 3; a++)
                    if (TryTreeName(ForestTree(c.x, c.y, depth), c.x, c.y)) break;
            }
        }

        /// <summary>Einzelne Baeume und Gruppen vor dem Waldrand.</summary>
        static void ScatterClearingTrees()
        {
            foreach (var c in ShuffledCells())
            {
                if (forest[c.x - MinX, c.y - MinY] || c.x < -1 || c.x > InW || c.y < -1 || c.y > InH) continue;
                int od = openDist[c.x - MinX, c.y - MinY];
                double p = od <= 2 ? 0.07 : od <= 6 ? 0.12 : 0.012;
                if (rng.NextDouble() > p) continue;
                for (int a = 0; a < 3; a++)
                    if (TryTreeName(ClearingTree(c.x, c.y), c.x, c.y)) break;
            }
        }

        static void Light(string kind, int x, int y)
        {
            if (kind == "lantern") lanternLights.Add(new Vector3(x + 0.5f, y + 1.6f, 0));
            else campLights.Add(new Vector3(x + 0.5f, y + 0.6f, 0));
        }

        static void PutLantern(int x, int y)
        {
            if (Put("Laterne", x, y)) Light("lantern", x, y);
        }

        static void PlaceHeroes()
        {
            // --- Plaza mit Lagerfeuer
            if (Put("Lagerfeuer", 23, 15)) Light("camp", 23, 15);
            Put("Baumstamm_Liegend", 20, 17);
            Put("Baumstamm_Liegend", 25, 13);
            Put("Baumstumpf", 20, 15);
            Put("Baumstumpf", 26, 15);
            Put("Baumstumpf_Pilze", 21, 13);
            Put("Baumstumpf_Gross", 25, 18);
            Put("Fass", 27, 17);
            Put("Kiste", 28, 17);
            Put("Holzstapel", 28, 16);
            Put("Schild", 24, 20);
            PutLantern(19, 19); PutLantern(28, 19); PutLantern(19, 12); PutLantern(28, 12);
            PutLantern(22, 21);   // am Nordweg
            PutLantern(34, 12);   // am Hoftor
            PutLantern(8, 15);    // an der Bruecke

            // --- Hecken noerdlich der Plaza
            foreach (int hx in new[] { 19, 25, 27, 29 }) Put("Hecke", hx, 22);
            Put("Busch_Blueten", 21, 22);
            Put("Busch_Blueten", 31, 21);
            Put("Busch_Blueten", 14, 21);

            // --- Gaertchen am Westweg (Zaun)
            Put("Zaun_Pfosten", 13, 16);
            Put("Zaun_Links", 14, 16);
            Put("Zaun_Mitte", 15, 16);
            Put("Zaun_Mitte", 16, 16);
            Put("Zaun_Rechts", 17, 16);
            Put("Zaun_Pfosten", 18, 16);
            Put("Zaun_Senkrecht", 13, 17);
            Put("Zaun_Senkrecht", 18, 17);
            Put("Busch_Beeren", 14, 17);
            Put("Heidelbeerbusch", 16, 17);
            Put("Brombeerbusch", 15, 18);
            Put("Schild", 14, 15);

            // --- Holzplatz mit Zaun (x 31..41, y 3..11), Tor bei x = 35
            for (int y = 4; y <= 10; y++) { Put("Zaun_Senkrecht", 31, y); Put("Zaun_Senkrecht", 41, y); }
            Put("Zaun_Pfosten", 31, 3); Put("Zaun_Pfosten", 41, 3);
            Put("Zaun_Links", 32, 3);
            for (int x = 33; x <= 39; x++) Put("Zaun_Mitte", x, 3);
            Put("Zaun_Rechts", 40, 3);
            Put("Zaun_Links", 31, 11);
            Put("Zaun_Mitte", 32, 11);
            Put("Zaun_Rechts", 33, 11);
            Put("Zaun_Pfosten", 34, 11);
            Put("Zaun_Pfosten", 36, 11);
            Put("Zaun_Links", 37, 11);
            for (int x = 38; x <= 40; x++) Put("Zaun_Mitte", x, 11);
            Put("Zaun_Rechts", 41, 11);
            Put("Schild", 36, 12);
            Put("Holzstapel", 32, 9); Put("Holzstapel", 33, 9); Put("Holzstapel", 32, 5); Put("Holzstapel", 33, 5);
            Put("Kiste", 38, 5); Put("Kiste", 39, 5); Put("Kiste", 39, 6);
            Put("Fass", 40, 9); Put("Fass", 40, 8); Put("Fass", 32, 7);
            Put("Baumstumpf_Gross", 35, 7);
            Put("Baumstumpf", 37, 8);
            Put("Aeste", 34, 8);
            Put("Stein_Platte", 35, 12);
            Put("Stein_Klein_B", 34, 5);
            Put("Baumstamm_Liegend", 36, 5);

            // --- Strasse nach Osten
            Put("Fass", 31, 16); Put("Kiste", 32, 16); Put("Kiste", 32, 17);
            Put("Busch_Gruen", 34, 17); Put("Busch_Beeren", 40, 17);
            Put("Stein_Klein_A", 43, 13); Put("Stein_Klein_C", 45, 16);

            // --- Totes Lager im Nordosten
            Put("Lagerfeuer_Aus", 40, 24);
            Put("Baumstamm_Liegend", 36, 23);
            Put("Baumstumpf", 43, 25);
            Put("Kiste", 42, 23);
            Put("Aeste", 38, 26); Put("Aeste", 44, 22); Put("Aeste", 36, 21);
            Put("Wurzeln", 36, 25); Put("Wurzeln", 45, 27); Put("Wurzeln", 39, 28);
            Put("Busch_Tot", 35, 24); Put("Busch_Tot", 46, 25); Put("Busch_Tot", 41, 29); Put("Busch_Tot", 37, 28);
            HeroTree("Baum_Tot", 36, 27);
            HeroTree("Baum_Tot", 44, 28);
            HeroTree("Baum_Tot", 42, 20);
            HeroTree("Baum_Tot", 39, 30);
            Reserve(34, 22, 44, 27);

            // --- Obstgarten im Suedwesten
            foreach (var a in new[] { new Vector2Int(2, 6), new Vector2Int(5, 6), new Vector2Int(3, 9), new Vector2Int(6, 9) })
                HeroTree("Eiche_Apfel", a.x, a.y);
            foreach (int hx in new[] { 2, 4, 6 }) Put("Hecke", hx, 12);
            Put("Busch_Beeren", 5, 8, true); Put("Heidelbeerbusch", 5, 11, true); Put("Busch_Blueten", 8, 12); Put("Busch_Beeren", 2, 11);
            Reserve(2, 5, 8, 12);

            // --- Felsgruppe
            Put("Stein_Fels_Gross", 13, 9);
            Put("Stein_Fels_Gross_Moos", 16, 9);
            Put("Stein_Gruppe", 14, 12);
            Put("Stein_Haufen", 12, 11);
            Put("Stein_Klein_A", 18, 9); Put("Stein_Klein_B", 15, 11); Put("Stein_Klein_C", 19, 11);
            Put("Stein_Moos", 12, 8); Put("Stein_Moos", 20, 9);
            Put("Busch_Dunkel", 17, 11); Put("Busch_Dunkel", 11, 10);
            Put("Farn_Gross", 18, 11); Put("Farn_Dicht", 12, 12);
            foreach (int px in new[] { 14, 16, 18 }) Put("Stein_Platte", px, 6); // Trittsteine im Kanal
            Reserve(12, 8, 20, 12);

            Reserve(18, 11, 28, 20);   // Plaza
            Reserve(30, 3, 41, 11);    // Holzplatz

            Put("Busch_Herbst", 4, 19); Put("Busch_Herbst", 4, 24); Put("Busch_Herbst", 5, 22);
            Put("Stein_Moos", 33, 21);
            Put("Baumstumpf", 30, 19);

            // --- Blickfang-Baeume (werden bei Bedarf leicht verschoben)
            HeroTree("Birke_A", 14, 19);
            HeroTree("Birke_B", 31, 19);
            HeroTree("Birke_C", 6, 17);
            HeroTree("Eiche_A", 35, 18);
            HeroTree("Eiche_B", 38, 19);
            HeroTree("Eiche_Herbst", 3, 19);
            HeroTree("Eiche_Herbst", 3, 23);
            HeroTree("Kiefer_A", 26, 22);
            HeroTree("Kiefer_B", 20, 24);
            HeroTree("Fichte_Hoch_A", 16, 24);
            HeroTree("Fichte_Hoch_B", 28, 23);
            HeroTree("Fichte_Hoch_C", 31, 24);
            HeroTree("Fichte_Jung", 21, 24);
            HeroTree("Fichte_Jung", 12, 4);
            HeroTree("Birke_A", 20, 3);
        }

        static void ScatterSmall()
        {
            string[] bush = { "Busch_Gruen", "Busch_Gruen", "Busch_Gruen", "Busch_Blueten", "Busch_Blueten", "Busch_Beeren", "Busch_Dunkel", "Brombeerbusch", "Heidelbeerbusch", "Farn_Gross", "Farn_Dicht" };
            string[] stones = { "Stein_Klein_A", "Stein_Klein_B", "Stein_Klein_C", "Stein_Moos", "Stein_Haufen" };
            foreach (var c in ShuffledCells())
            {
                int x = c.x, y = c.y;
                if (Blocked(x, y) || !IsGround(x, y) || Occ(x, y) != null) continue;
                bool inForest = forest[x - MinX, y - MinY];
                double d = rng.NextDouble();
                if (inForest)
                {
                    if (d < 0.05) Put(bush[rng.Next(bush.Length)], x, y, true);
                    else if (d < 0.065) Put(stones[rng.Next(stones.Length)], x, y, true);
                    else if (d < 0.08) Put(new[] { "Aeste", "Wurzeln", "Baumstumpf_Pilze", "Baumstumpf" }[rng.Next(4)], x, y, true);
                }
                else if (x >= -1 && x <= InW && y >= -1 && y <= InH)
                {
                    int od = openDist[x - MinX, y - MinY];
                    if (d < 0.035) Put(bush[rng.Next(bush.Length)], x, y, true);
                    else if (d < 0.045) Put(stones[rng.Next(stones.Length)], x, y, true);
                    else if (od <= 3 && d < 0.06) Put(new[] { "Aeste", "Wurzeln", "Baumstumpf", "Baumstumpf_Pilze", "Baumstamm_Liegend" }[rng.Next(5)], x, y, true);
                }
            }
        }

        static void WaterProps()
        {
            bool lily = false;
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    if (GetT(x, y) != Ter.Water || Occ(x, y) != null) continue;
                    if (IsShore(x, y)) { if (rng.NextDouble() < 0.3) Put("Schilf", x, y); }
                    else if (rng.NextDouble() < 0.14 || (!lily && x > 40)) { if (Put("Seerosen", x, y)) lily = lily || x > 40; }
                }
        }

        // Urspruengliches Objekt-Set: jedes davon soll mindestens einmal im Level stehen.
        // Alle weiteren Objekte (TilesetErweiterung) stehen nur in den Paletten zur Verfuegung.
        static readonly string[] CoreObjects =
        {
            "Aeste", "Baum_Tot", "Baumstamm_Liegend", "Baumstumpf", "Baumstumpf_Gross", "Baumstumpf_Pilze",
            "Birke_A", "Birke_A_Fern", "Birke_B", "Birke_B_Fern", "Birke_C", "Birke_C_Fern",
            "Brombeerbusch", "Busch_Beeren", "Busch_Blueten", "Busch_Dunkel", "Busch_Gruen", "Busch_Herbst", "Busch_Tot",
            "Eiche_A", "Eiche_A_Fern", "Eiche_Apfel", "Eiche_Apfel_Fern", "Eiche_B", "Eiche_B_Fern", "Eiche_Herbst", "Eiche_Herbst_Fern",
            "Farn_Dicht", "Farn_Gross", "Fass", "Fichte_Hoch_A", "Fichte_Hoch_A_Fern", "Fichte_Hoch_B", "Fichte_Hoch_B_Fern",
            "Fichte_Hoch_C", "Fichte_Hoch_C_Fern", "Fichte_Jung", "Fichte_Jung_Fern", "Hecke", "Heidelbeerbusch", "Holzstapel",
            "Kiefer_A", "Kiefer_A_Fern", "Kiefer_B", "Kiefer_B_Fern", "Kiste", "Lagerfeuer", "Lagerfeuer_Aus", "Laterne",
            "Schild", "Schilf", "Seerosen", "Stamm_Basis", "Stamm_Segment",
            "Stein_Fels_Gross", "Stein_Fels_Gross_Moos", "Stein_Gruppe", "Stein_Haufen", "Stein_Klein_A", "Stein_Klein_B",
            "Stein_Klein_C", "Stein_Moos", "Stein_Platte", "Wurzeln",
            "Zaun_Links", "Zaun_Mitte", "Zaun_Pfosten", "Zaun_Rechts", "Zaun_Senkrecht",
        };

        /// <summary>Stellt sicher, dass jedes Objekt des urspruenglichen Sets mindestens einmal vorkommt.</summary>
        static void Fallback()
        {
            var names = new List<string>(CoreObjects);
            foreach (var n in names)
            {
                if (!size.ContainsKey(n) || used.Contains(n)) continue;
                if (n == "Stamm_Basis" || n == "Stamm_Segment") continue;   // einzelne Stamm-Bausteine, nicht noetig
                if (IsTreePart(n)) continue;
                bool placed = false;
                var cells = ShuffledCells();
                foreach (var c in cells)
                {
                    int x = c.x, y = c.y;
                    if (IsTreeName(n))
                    {
                        bool fern = n.EndsWith("_Fern");
                        if (fern && (!forest[x - MinX, y - MinY] || forestDepth[x - MinX, y - MinY] < 3)) continue;
                        if (!fern && (x < 0 || x >= InW || y < 0 || y >= InH)) continue;
                        placed = TryTreeName(n, x, y, true);
                    }
                    else if (IsGround(x, y) && Occ(x, y) == null && !nearPW[x - MinX, y - MinY] && x >= 0 && x < InW && y >= 0 && y < InH)
                        placed = Put(n, x, y, true);
                    if (placed) break;
                }
                if (!placed) issues.Add("Fallback fehlgeschlagen: " + n);
            }
        }

        // ---------------------------------------------------------------- Dekor, Bruecken, Kollision

        static void Deco(Tilemap deco)
        {
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    if (Occ(x, y) != null) continue;
                    var t = GetT(x, y);
                    double d = rng.NextDouble();
                    TileBase tile = null;
                    bool fill = Conn(t, GetT(x, y + 1)) && Conn(t, GetT(x + 1, y)) && Conn(t, GetT(x, y - 1)) && Conn(t, GetT(x - 1, y));
                    int od = openDist[x - MinX, y - MinY];
                    if (t == Ter.Grass)
                    {
                        bool nearPath = nearPW[x - MinX, y - MinY];
                        int col = -1;
                        if (nearPath && d < 0.12) col = 11 + rng.Next(3);
                        else if (d < 0.08) col = rng.Next(6);
                        else if (d < 0.18) col = 6 + rng.Next(3);
                        else if (d < 0.23) col = 9 + rng.Next(2);
                        else if (d < 0.26) col = 19;
                        else if (d < 0.275) col = 18;
                        if (col >= 0) tile = DecoTile(col);
                        else if (od <= 6 && rng.NextDouble() < 0.05) tile = LoadWald(4, rng.Next(3));      // Lichtflecken
                    }
                    else if (t == Ter.Forest && fill)
                    {
                        // Zeile 3: Grasbuschel, Buendel, Grasreihe, Farn, Wildblumen, Pilze, Moos, Laub, Zapfen
                        // Zeile 4: Lichtflecken, Wurzeln, Totholz, Blaubeeren, Glockenblumen, Farn gross, Pilze, Moos, Laub
                        if (d < 0.20) tile = LoadWald(3, rng.Next(19));
                        else if (d < 0.30) tile = LoadWald(4, rng.Next(14));
                    }
                    else if (t == Ter.ForestPath && fill && d < 0.05) tile = LoadWald(3, 17 + rng.Next(2));
                    else if (t == Ter.Dirt && fill && d < 0.06) tile = DecoTile(11 + rng.Next(3));
                    if (tile != null) deco.SetTile(new Vector3Int(x, y, 0), tile);
                }
        }

        static void Bridges(Tilemap bridge)
        {
            int x0 = -99, x1 = -99;
            for (int x = 4; x <= 16; x++)
                if (GetT(x, 14) == Ter.Water) { if (x0 == -99) x0 = x; x1 = x; }
            bridge.SetTile(new Vector3Int(x0 - 1, 14, 0), LoadTerrain(6, 0));
            for (int x = x0; x <= x1; x++) bridge.SetTile(new Vector3Int(x, 14, 0), LoadTerrain(6, 1));
            bridge.SetTile(new Vector3Int(x1 + 1, 14, 0), LoadTerrain(6, 2));
            for (int x = x0 - 1; x <= x1 + 1; x++) occ[x - MinX, 14 - MinY] = "Bruecke";

            int y0 = -99, y1 = -99;
            for (int y = 2; y <= 10; y++)
                if (GetT(23, y) == Ter.Water) { if (y0 == -99) y0 = y; y1 = y; }
            bridge.SetTile(new Vector3Int(23, y1 + 1, 0), LoadTerrain(6, 3));
            for (int y = y0; y <= y1; y++) bridge.SetTile(new Vector3Int(23, y, 0), LoadTerrain(6, 4));
            bridge.SetTile(new Vector3Int(23, y0 - 1, 0), LoadTerrain(6, 5));
            for (int y = y0 - 1; y <= y1 + 1; y++) occ[23 - MinX, y - MinY] = "Bruecke";
        }

        static void FillCollision(Tilemap col)
        {
            var block = AssetDatabase.LoadAssetAtPath<TileBase>(TileAssets + "/Collision_Block.asset");
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    bool s = solid[x - MinX, y - MinY];
                    if (!s && GetT(x, y) == Ter.Water)
                    {
                        string o = occ[x - MinX, y - MinY];
                        s = o != "Bruecke" && o != "Stein_Platte";
                    }
                    if (s) col.SetTile(new Vector3Int(x, y, 0), block);
                }
            // Rahmen um die Karte
            for (int x = MinX - 1; x <= MaxX + 1; x++)
            {
                col.SetTile(new Vector3Int(x, MinY - 1, 0), block);
                col.SetTile(new Vector3Int(x, MaxY + 1, 0), block);
            }
            for (int y = MinY - 1; y <= MaxY + 1; y++)
            {
                col.SetTile(new Vector3Int(MinX - 1, y, 0), block);
                col.SetTile(new Vector3Int(MaxX + 1, y, 0), block);
            }
        }

        // ---------------------------------------------------------------- Level

        [MenuItem("Nightward/Level 1/3 Level bauen")]
        public static void BuildLevel()
        {
            ReadSizes();
            ApplyAnimSpeeds();
            LoadAnimVariants();
            rng = new System.Random(20261018);
            used.Clear();
            issues.Clear();
            campLights.Clear();
            lanternLights.Clear();
            trunkFeet.Clear();

            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            if (!File.Exists(ScenePath))
                AssetDatabase.CopyAsset("Assets/Scenes/SampleScene.unity", ScenePath);
            var scene = EditorSceneManager.OpenScene(ScenePath);

            foreach (var n in new[] { "Level_01", "Characters" })
            {
                var old = GameObject.Find(n);
                if (old != null) UnityEngine.Object.DestroyImmediate(old);
            }

            BuildTerrain();
            ComputeForest();
            nearPW = new bool[W, H];
            nearFP = new bool[W, H];
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    for (int dx = -1; dx <= 1; dx++)
                        for (int dy = -1; dy <= 1; dy++)
                        {
                            var t = GetT(x + dx, y + dy);
                            if (IsPathy(t) || t == Ter.Water) nearPW[x - MinX, y - MinY] = true;
                        }
                    for (int dx = -2; dx <= 2; dx++)
                        for (int dy = -2; dy <= 2; dy++)
                            if (GetT(x + dx, y + dy) == Ter.ForestPath) nearFP[x - MinX, y - MinY] = true;
                }

            var root = new GameObject("Level_01");
            var grid = new GameObject("Grid");
            grid.transform.SetParent(root.transform);
            grid.AddComponent<Grid>();

            var lit = AssetDatabase.LoadAssetAtPath<Material>(
                "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat");
            Tilemap Layer(string name, int order, bool individual)
            {
                var go = new GameObject(name);
                go.transform.SetParent(grid.transform, false);
                var tm = go.AddComponent<Tilemap>();
                tm.animationFrameRate = 1f; // Tempo steckt in den AnimatedTiles
                var tr = go.AddComponent<TilemapRenderer>();
                tr.sortingOrder = order;
                if (lit != null) tr.sharedMaterial = lit;
                if (individual) tr.mode = TilemapRenderer.Mode.Individual;
                return tm;
            }

            var ground = Layer("Ground", OrderGround, false);
            var deco = Layer("Deco", OrderDeco, false);
            var bridge = Layer("Bridge", OrderBridge, false);
            objMap = Layer("Objects", OrderObjects, true);
            objMap.tileAnchor = Vector3.zero;
            crownMap = Layer("Crowns", OrderCrowns, true);
            crownMap.tileAnchor = Vector3.zero;

            Bridges(bridge);
            PlaceHeroes();
            ScatterClearingTrees();
            FillForest();
            ScatterSmall();
            WaterProps();
            Fallback();

            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                    ground.SetTile(new Vector3Int(x, y, 0), TerrainTile(x, y));
            Deco(deco);

            // Kollision: Tiles fuer Wasser/Zaeune/Steine, kleine Boxen nur am Stammfuss
            var colGo = new GameObject("Collision");
            colGo.transform.SetParent(grid.transform, false);
            var colMap = colGo.AddComponent<Tilemap>();
            var tc = colGo.AddComponent<TilemapCollider2D>();
            var rb = colGo.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Static;
            var cc = colGo.AddComponent<CompositeCollider2D>();
            cc.geometryType = CompositeCollider2D.GeometryType.Polygons;
            tc.compositeOperation = Collider2D.CompositeOperation.Merge;
            FillCollision(colMap);

            var trunks = new GameObject("TrunkColliders");
            trunks.transform.SetParent(root.transform);
            var trb = trunks.AddComponent<Rigidbody2D>();
            trb.bodyType = RigidbodyType2D.Static;
            var tcc = trunks.AddComponent<CompositeCollider2D>();
            tcc.geometryType = CompositeCollider2D.GeometryType.Polygons;
            foreach (var f in trunkFeet)
            {
                var box = trunks.AddComponent<BoxCollider2D>();
                box.size = new Vector2(0.3f, 0.22f);
                box.offset = f;
                box.compositeOperation = Collider2D.CompositeOperation.Merge;
            }

            // Kronen ueber der Spielfigur ausblenden
            var fader = crownMap.gameObject.AddComponent<CanopyFader>();
            var fso = new SerializedObject(fader);
            fso.FindProperty("crowns").objectReferenceValue = crownMap;
            fso.ApplyModifiedPropertiesWithoutUndo();

            foreach (var l in UnityEngine.Object.FindObjectsByType<Light2D>(FindObjectsInactive.Exclude))
                if (l.lightType == Light2D.LightType.Global)
                {
                    l.color = new Color(1f, 0.95f, 0.86f);
                    l.intensity = 0.95f;
                }
            var lights = new GameObject("Lights");
            lights.transform.SetParent(root.transform);
            foreach (var p in campLights) MakeLight(lights.transform, "Lagerfeuer_Licht", p, new Color(1f, 0.6f, 0.25f), 1.2f, 7f);
            foreach (var p in lanternLights) MakeLight(lights.transform, "Laternen_Licht", p, new Color(1f, 0.8f, 0.45f), 0.8f, 3.5f);

            var cam = Camera.main;
            if (cam != null)
            {
                cam.backgroundColor = new Color(0.07f, 0.11f, 0.08f);
                cam.transparencySortMode = TransparencySortMode.CustomAxis;
                cam.transparencySortAxis = new Vector3(0, 1, 0);
                var ppc = cam.GetComponent<PixelPerfectCamera>();
                if (ppc != null)
                {
                    // Nah am Spieler: 384x216 = 12 x 6,75 Kacheln (gemuetlich nah dran)
                    ppc.assetsPPU = Cell;
                    ppc.refResolutionX = 384;
                    ppc.refResolutionY = 216;
                }
            }

            // Spielfigur zwischen Objekten sortieren
            var player = GameObject.FindWithTag("Player");
            if (player != null)
                foreach (var sr in player.GetComponentsInChildren<SpriteRenderer>()) sr.sortingOrder = OrderObjects;

            var missing = new List<string>();
            foreach (var n in CoreObjects)
                if (size.ContainsKey(n) && !used.Contains(n) && n != "Stamm_Basis" && n != "Stamm_Segment") missing.Add(n);
            Debug.Log("Level_01 gebaut. Baeume mit Stammkollision: " + trunkFeet.Count + ". Nicht verwendete Objekte: " +
                      (missing.Count == 0 ? "keine" : string.Join(", ", missing)) +
                      "\nProbleme (" + issues.Count + "):\n" + string.Join("\n", issues));

            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }

        static void MakeLight(Transform parent, string name, Vector3 pos, Color col, float intensity, float radius)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent);
            go.transform.position = pos;
            var l = go.AddComponent<Light2D>();
            l.lightType = Light2D.LightType.Point;
            l.color = col;
            l.intensity = intensity;
            l.pointLightOuterRadius = radius;
            l.pointLightInnerRadius = radius * 0.2f;
        }
    }
}
