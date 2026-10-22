using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using Nightward.Core;
using Nightward.DayNight;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using UnityEngine.Tilemaps;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut das Dorf in Scenes/Game/Level_01 nach Dorfplan (nightward_dorfplan.svg): Nord-Sued-Dorfstrasse mit Bach, Bruecke und Villa im Norden,
    /// links Wohnhaeuser, Baeckerei, Pfarrhaus, rechts Aerztehaus, Ilhans Bar, Diner, Revier, Markt, Scheune, Friedhof,
    /// unten Zone 1 (Waldrand). Haeuser kommen als Prefabs aus dem Haus-Baukasten (DorfXxx), die Bar aus Bar_Ilhans_Komplett.
    /// Wege: Erdstrasse mit Pflasterband, Kieswege (Gassen), Plattenvorplaetze, Pflasterplaetze - alles als Overlay-Autotiles mit
    /// Moos-/Kiesel-Saum (Tileset_Dorf.png, erzeugt von _Quelle_Generator/dorf_tiles.py). Objekte aus Tiles/Dorf/Objekte (dorf_objekte.py).
    /// Level1Builder bleibt unveraendert; dieses Skript ersetzt nur das Objekt "Level_01" der Szene und laesst Spielfigur,
    /// NPCs, Tag/Nacht und UI stehen.
    /// </summary>
    public static class DorfBuilder
    {
        const string TilesRoot = "Assets/_Project/Art/Tiles";
        const string TileAssets = TilesRoot + "/TileAssets";
        const string DorfSheet = TilesRoot + "/Tileset_Dorf.png";
        const string DorfObjDir = TilesRoot + "/Dorf/Objekte";
        const string DorfAssets = TileAssets + "/Dorf";
        const string ScenePath = "Assets/_Project/Scenes/Game/Level_01.unity";
        const string HouseDir = "Assets/_Project/Prefabs/Haeuser/";
        const string BarPrefab = HouseDir + "Bar_Ilhans_Komplett.prefab";
        const string LitMaterial = "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat";

        // Karte: x = West-Ost, y = Sued-Nord. Zone 1 (Waldrand) liegt bei y 0..8, die Villa oben bei y 120..130.
        const int MinX = -14, MaxX = 84, MinY = -16, MaxY = 160;
        const int W = MaxX - MinX + 1, H = MaxY - MinY + 1;
        const int OrderGround = 0, OrderOverlay = 1, OrderDeco = 2, OrderBridge = 3, OrderObjects = 4, OrderCrowns = 20;
        const int StreetX0 = 32, StreetX1 = 37;      // Dorfstrasse, 6 Zellen breit
        const int BachY = 134;                       // Bach y 133..135
        const int NorthEnd = BachY + 9;              // ab hier Wald (Strasse bleibt offen)
        const int VY = 128;                          // Basis der Villa

        enum Ter { Grass, Dirt, Cobble, Slab, Gravel, Water, Forest, ForestPath }

        static Ter[,] ter;
        static bool[,] occ, solid, forest, nearPW;
        static int[,] fdepth;
        static System.Random rng;
        static Tilemap objMap, crownMap, decoMap;
        static Transform lightsRoot, housesRoot, levelRoot;
        static List<Vector2> trunkFeet = new List<Vector2>();
        static HashSet<string> missing = new HashSet<string>();
        static Dictionary<string, List<TileBase>> animObj = new Dictionary<string, List<TileBase>>();
        static Dictionary<int, List<TileBase>> animDeko = new Dictionary<int, List<TileBase>>();
        static Dictionary<string, Vector2Int> sizeCache = new Dictionary<string, Vector2Int>();
        static List<string> issues = new List<string>();
        static int lampCount;

        // ------------------------------------------------------------------ Hilfen

        static bool InMap(int x, int y) => x >= MinX && x <= MaxX && y >= MinY && y <= MaxY;
        static Ter GetT(int x, int y) => ter[Mathf.Clamp(x, MinX, MaxX) - MinX, Mathf.Clamp(y, MinY, MaxY) - MinY];
        static void SetT(int x, int y, Ter t) { if (InMap(x, y)) ter[x - MinX, y - MinY] = t; }
        static bool Occ(int x, int y) => !InMap(x, y) || occ[x - MinX, y - MinY];
        static bool GetM(bool[,] m, int x, int y) => m[Mathf.Clamp(x, MinX, MaxX) - MinX, Mathf.Clamp(y, MinY, MaxY) - MinY];
        static bool IsOverlay(Ter t) => t == Ter.Cobble || t == Ter.Slab || t == Ter.Gravel;
        static Ter Base(Ter t) => IsOverlay(t) ? Ter.Dirt : t;

        static void Reserve(int x0, int y0, int x1, int y1)
        {
            for (int x = x0; x <= x1; x++)
                for (int y = y0; y <= y1; y++)
                    if (InMap(x, y)) occ[x - MinX, y - MinY] = true;
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
                    if (px != lastX && py != lastY)
                        for (int ax = 0; ax < w; ax++)
                            for (int ay = 0; ay < w; ay++) SetT(px + ax, lastY + ay, t);
                    for (int ax = 0; ax < w; ax++)
                        for (int ay = 0; ay < w; ay++) SetT(px + ax, py + ay, t);
                    lastX = px; lastY = py;
                }
            }
        }

        static TileBase ObjTile(string name)
        {
            var t = AssetDatabase.LoadAssetAtPath<TileBase>($"{DorfAssets}/Objekte/{name}.asset");
            return t != null ? t : AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Objekte/{name}.asset");
        }
        static TileBase LoadTerrain(int r, int c) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Terrain/T_{r}_{c}.asset");
        static TileBase LoadWald(int r, int c) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Wald/W_{r}_{c}.asset");
        static TileBase LoadDorf(int r, int c) => AssetDatabase.LoadAssetAtPath<TileBase>($"{DorfAssets}/P_{r}_{c}.asset");

        /// <summary>Groesse eines Objekts in Zellen (aus dem Sprite, aufgerundet).</summary>
        static Vector2Int SizeOf(string name)
        {
            if (sizeCache.TryGetValue(name, out var s)) return s;
            Sprite sp = null;
            var tile = ObjTile(name);
            if (tile is Tile t) sp = t.sprite;
            else if (tile is AnimatedTile at && at.m_AnimatedSprites != null && at.m_AnimatedSprites.Length > 0) sp = at.m_AnimatedSprites[0];
            if (sp == null && animObj.TryGetValue(name, out var list) && list.Count > 0 && list[0] is AnimatedTile at2 && at2.m_AnimatedSprites.Length > 0)
                sp = at2.m_AnimatedSprites[0];
            s = sp == null ? Vector2Int.zero : new Vector2Int(Mathf.CeilToInt(sp.rect.width / 32f), Mathf.CeilToInt(sp.rect.height / 32f));
            sizeCache[name] = s;
            return s;
        }

        static float PixelWidth(string name)
        {
            var tile = ObjTile(name);
            if (tile is Tile t && t.sprite != null) return t.sprite.rect.width;
            return SizeOf(name).x * 32f;
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
                if (ObjTile(b) == null) continue;
                if (!animObj.ContainsKey(b)) animObj[b] = new List<TileBase>();
                animObj[b].Add(tile);
            }
        }

        // ------------------------------------------------------------------ Import der neuen Dorf-Art

        static void EnsureFolder(string path)
        {
            if (!AssetDatabase.IsValidFolder(path))
                AssetDatabase.CreateFolder(Path.GetDirectoryName(path).Replace('\\', '/'), Path.GetFileName(path));
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

        /// <summary>Zerlegt Tileset_Dorf.png (20 Spalten) und legt Tiles fuer Sheet + alle Dorf-Objekte an.</summary>
        [MenuItem("Nightward/Dorf/1 Dorf-Art importieren")]
        public static void ImportDorfArt()
        {
            AssetDatabase.Refresh();
            EnsureFolder(TilesRoot + "/Dorf");
            EnsureFolder(DorfAssets);
            EnsureFolder(DorfAssets + "/Objekte");

            var ti = (TextureImporter)AssetImporter.GetAtPath(DorfSheet);
            if (ti == null) { Debug.LogError("[Dorf] Tileset_Dorf.png fehlt (dorf_tiles.py ausfuehren)."); return; }
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = 32;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
            int rows = th / 32;
            var metas = new List<SpriteMetaData>();
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < tw / 32; c++)
                    metas.Add(new SpriteMetaData
                    {
                        name = $"P_{r}_{c}",
                        rect = new Rect(c * 32, th - (r + 1) * 32, 32, 32),
                        alignment = (int)SpriteAlignment.Center,
                        pivot = new Vector2(0.5f, 0.5f)
                    });
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(DorfSheet))
                if (o is Sprite sp) MakeTile($"{DorfAssets}/{sp.name}.asset", sp);

            int n = 0;
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { DorfObjDir }))
            {
                string p = AssetDatabase.GUIDToAssetPath(guid);
                var oi = (TextureImporter)AssetImporter.GetAtPath(p);
                oi.textureType = TextureImporterType.Sprite;
                oi.spriteImportMode = SpriteImportMode.Single;
                oi.spritePixelsPerUnit = 32;
                oi.filterMode = FilterMode.Point;
                oi.textureCompression = TextureImporterCompression.Uncompressed;
                oi.mipmapEnabled = false;
                oi.alphaIsTransparency = true;
                var s = new TextureImporterSettings();
                oi.ReadTextureSettings(s);
                s.spriteAlignment = (int)SpriteAlignment.BottomLeft;
                s.spriteMeshType = SpriteMeshType.FullRect;
                oi.SetTextureSettings(s);
                oi.SaveAndReimport();
                var sp = AssetDatabase.LoadAssetAtPath<Sprite>(p);
                if (sp != null) { MakeTile($"{DorfAssets}/Objekte/{Path.GetFileNameWithoutExtension(p)}.asset", sp); n++; }
            }
            AssetDatabase.SaveAssets();
            Debug.Log($"[Dorf] Art importiert: {rows} Sheet-Zeilen, {n} Objekte.");
        }

        [MenuItem("Nightward/Dorf/Alles: Art importieren + Dorf bauen")]
        public static void ImportAndBuild()
        {
            ImportDorfArt();
            Build();
        }

        // ------------------------------------------------------------------ Terrain

        static void BuildTerrain()
        {
            ter = new Ter[W, H];
            occ = new bool[W, H];
            solid = new bool[W, H];

            // Dorfstrasse Nord-Sued: bleibt nach Norden und Sueden offen (spaeter Anschluss an weitere Gebiete)
            FillRect(Ter.Dirt, StreetX0, MinY, StreetX1, BachY - 3);
            FillRect(Ter.Dirt, StreetX0 + 1, BachY - 2, StreetX1 - 1, MaxY);
            // Pflasterband in der Mitte, nur im Dorf (y 12 .. Bruecke)
            FillRect(Ter.Cobble, 34, 12, 35, BachY - 4);

            // Dorfplatz mit Brunnen (Mitte), Marktplatz; Plattenring um den Brunnen
            FillEllipse(Ter.Cobble, 35f, 66f, 8f, 4.2f, 0.05f, 0.7f);
            FillEllipse(Ter.Slab, 35f, 66.3f, 3.6f, 2.5f, 0.04f, 1.1f);
            FillRect(Ter.Cobble, 41, 39, 58, 52);
            FillRect(Ter.Slab, 43, 40, 56, 41);
            FillRect(Ter.Cobble, 38, 45, 40, 46);
            // Villa: Vorplatz aus Platten, Zufahrt als Kiesweg
            FillRect(Ter.Slab, 43, VY - 5, 56, VY - 2);
            FillRect(Ter.Gravel, 38, VY - 4, 42, VY - 3);

            // Bach mit Teich am Ostende
            for (int x = MinX; x <= 40; x++)
            {
                int dy = (x < 28 || x > 40) ? Mathf.RoundToInt(1.4f * Mathf.Sin(x * 0.33f) + 0.8f * Mathf.Sin(x * 0.8f + 1f)) : 0;
                FillRect(Ter.Water, x, BachY - 1 + dy, x, BachY + 1 + dy);
            }
            FillEllipse(Ter.Water, 42f, BachY, 3.4f, 2.8f, 0.07f, 3.1f);

            // Gassen zu den Haeusern (Kies) mit Plattenvorplatz vor der Tuer
            foreach (var h in Houses) LaneFor(h);

            // Uferweg am Bach (Suedufer, westlich der Strasse) und Verbindung Markt -> Schmiede
            FillRect(Ter.Gravel, 4, BachY - 7, StreetX0 - 1, BachY - 6);
            FillRect(Ter.Gravel, 58, 36, 59, 39);

            // Friedhofsweg
            FillRect(Ter.Gravel, StreetX1 + 1, 6, 51, 7);
            FillRect(Ter.Gravel, 50, 8, 52, 9);

            // Zone 1: Waldweg nach Suedwesten
            Line(Ter.Dirt, 2, 31, 8, 28, 5, 24, 2, 21, -1, 19, -4);
        }

        static void LaneFor(House h)
        {
            if (h.noLane) return;
            int dc = h.x + h.door;
            int aw = Mathf.Max(1, h.doorW);
            // Vorplatz aus Platten direkt vor der Tuer, dann Kiesweg zur Strasse
            FillRect(Ter.Slab, dc - 1, h.y - 3, dc + aw, h.y - 2);
            if (h.west) FillRect(Ter.Gravel, dc - 1, h.y - 5, StreetX0 - 1, h.y - 4);
            else FillRect(Ter.Gravel, h.laneStartX != -999 ? h.laneStartX : StreetX1 + 1, h.y - 5, dc + aw, h.y - 4);
        }

        // ------------------------------------------------------------------ Wald

        static void ComputeForest()
        {
            forest = new bool[W, H];
            fdepth = new int[W, H];
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    // Waldrand: schmaler Streifen links/rechts, im Sueden (Zone 1) schiebt er sich Richtung Strasse
                    float creep = Mathf.Max(0f, 12f - y) * 1.5f;
                    int wE = 7 + Mathf.RoundToInt(2.2f * Mathf.Sin(y * 0.21f + 0.6f) + 1.4f * Mathf.Sin(y * 0.53f + 2f) + creep);
                    int eE = 74 - Mathf.RoundToInt(2.0f * Mathf.Sin(y * 0.19f + 1.2f) + 1.4f * Mathf.Sin(y * 0.47f) + creep);
                    int nE = NorthEnd + Mathf.RoundToInt(1.5f * Mathf.Sin(x * 0.3f) + Mathf.Sin(x * 0.9f));
                    bool f = x < wE || x >= eE || y >= nE || y <= -3;
                    forest[x - MinX, y - MinY] = f;
                }
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
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    if (!forest[x - MinX, y - MinY]) continue;
                    var t = GetT(x, y);
                    if (t == Ter.Grass) SetT(x, y, Ter.Forest);
                    else if (IsOverlay(t)) SetT(x, y, Ter.Dirt);   // Erdwege bleiben auch im Wald Erdwege (Waldweg-Fuellkachel wirkt zu flaechig)
                }
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    if (!forest[x - MinX, y - MinY]) continue;
                    int best = 99;
                    for (int dx = -6; dx <= 6; dx++)
                        for (int dy = -6; dy <= 6; dy++)
                        {
                            int nx = x + dx, ny = y + dy;
                            if (!InMap(nx, ny) || forest[nx - MinX, ny - MinY]) continue;
                            best = Mathf.Min(best, Mathf.Max(Mathf.Abs(dx), Mathf.Abs(dy)));
                        }
                    fdepth[x - MinX, y - MinY] = best;
                }
        }

        // ------------------------------------------------------------------ Autotiling

        static bool IsPathy(Ter t) => t == Ter.Dirt || IsOverlay(t) || t == Ter.ForestPath;

        static bool Conn(Ter me, Ter n)
        {
            switch (me)
            {
                case Ter.Dirt: return n == Ter.Dirt || IsOverlay(n) || n == Ter.ForestPath;
                case Ter.ForestPath: return n == Ter.ForestPath || n == Ter.Dirt || IsOverlay(n);
                case Ter.Forest: return n == Ter.Forest || n == Ter.ForestPath;
                default: return n == me;
            }
        }

        static int GrassVariant() => rng.NextDouble() < 0.55 ? 0 : 1 + rng.Next(7);

        static int ForestGrassVariant()
        {
            double d = rng.NextDouble();
            if (d < 0.38) return 0;
            if (d < 0.50) return 1;
            if (d < 0.64) return 2;
            if (d < 0.76) return 3;
            if (d < 0.84) return 4;
            if (d < 0.91) return 5;
            if (d < 0.96) return 6;
            return 7;
        }

        /// <summary>Bodenkachel. Pflaster/Platten/Kies liegen als Overlay auf Erde, darunter ist also Erde.</summary>
        static TileBase TerrainTile(int x, int y)
        {
            var t = Base(GetT(x, y));
            if (t == Ter.Grass) return LoadTerrain(4, GrassVariant());
            bool n = Conn(t, GetT(x, y + 1)), e = Conn(t, GetT(x + 1, y)), s = Conn(t, GetT(x, y - 1)), w = Conn(t, GetT(x - 1, y));
            int idx = (n ? 1 : 0) | (e ? 2 : 0) | (s ? 4 : 0) | (w ? 8 : 0);
            bool ne = Conn(t, GetT(x + 1, y + 1)), se = Conn(t, GetT(x + 1, y - 1)), sw = Conn(t, GetT(x - 1, y - 1)), nw = Conn(t, GetT(x - 1, y + 1));
            int corner = idx != 15 ? -1 : !ne ? 16 : !se ? 17 : !sw ? 18 : !nw ? 19 : -1;
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
            if (t == Ter.Dirt)
            {
                if (idx != 15) return LoadTerrain(0, idx);
                if (corner >= 0) return LoadTerrain(0, corner);
                return LoadTerrain(4, 8 + rng.Next(3));
            }
            return AssetDatabase.LoadAssetAtPath<TileBase>(TileAssets + "/Terrain/Wasser_Anim.asset");   // Water
        }

        static bool OvSame(Ter me, int x, int y)
        {
            var n = GetT(x, y);
            if (me == Ter.Cobble) return n == Ter.Cobble;
            return n == Ter.Gravel || n == Ter.Slab;
        }

        /// <summary>Overlay-Kachel (Pflaster / Platten / Kies) mit Rand, Moos und Kiesel-Saum.</summary>
        static TileBase OverlayTile(int x, int y)
        {
            var t = GetT(x, y);
            if (!IsOverlay(t)) return null;
            int row = t == Ter.Cobble ? 0 : t == Ter.Slab ? 3 : 6;
            bool n = OvSame(t, x, y + 1), e = OvSame(t, x + 1, y), s = OvSame(t, x, y - 1), w = OvSame(t, x - 1, y);
            int idx = (n ? 1 : 0) | (e ? 2 : 0) | (s ? 4 : 0) | (w ? 8 : 0);
            int variant = (x * 7 + y * 13) % 2;
            if (idx != 15) return LoadDorf(row + variant, idx);
            bool ne = OvSame(t, x + 1, y + 1), se = OvSame(t, x + 1, y - 1), sw = OvSame(t, x - 1, y - 1), nw = OvSame(t, x - 1, y + 1);
            int corner = !ne ? 16 : !se ? 17 : !sw ? 18 : !nw ? 19 : -1;
            if (corner >= 0) return LoadDorf(row, corner);
            double d = rng.NextDouble();
            int f;
            if (t == Ter.Cobble) f = d < 0.52 ? rng.Next(3) : d < 0.86 ? 3 + rng.Next(5) : 8 + rng.Next(4);
            else if (t == Ter.Slab) f = d < 0.55 ? rng.Next(3) : d < 0.86 ? 3 + rng.Next(4) : 7 + rng.Next(3);
            else f = d < 0.88 ? rng.Next(8) : 8 + rng.Next(2);
            return LoadDorf(row + 2, f);
        }

        static void Deco()
        {
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    if (Occ(x, y)) continue;
                    var t = GetT(x, y);
                    double d = rng.NextDouble();
                    TileBase tile = null;
                    bool fill = Conn(Base(t), GetT(x, y + 1)) && Conn(Base(t), GetT(x + 1, y)) && Conn(Base(t), GetT(x, y - 1)) && Conn(Base(t), GetT(x - 1, y));
                    if (t == Ter.Grass)
                    {
                        bool nearPath = nearPW[x - MinX, y - MinY];
                        int col = -1;
                        if (nearPath && d < 0.10) col = 11 + rng.Next(3);       // Kiesel am Weg
                        else if (d < 0.11) col = rng.Next(6);                   // Blumen
                        else if (d < 0.24) col = 6 + rng.Next(3);               // Grasbueschel
                        else if (d < 0.29) col = 9 + rng.Next(2);
                        else if (d < 0.32) col = 19;
                        else if (d < 0.335) col = 18;
                        if (col >= 0) tile = DecoTile(col);
                        // Grasbueschel/Moos/Pilze/Steinchen unmittelbar am Wegrand: der Uebergang wirkt gewachsen
                        else if (nearPath && d < 0.20) tile = LoadDorf(9, 8 + rng.Next(4));
                    }
                    else if (t == Ter.Forest && fill)
                    {
                        if (d < 0.20) tile = LoadWald(3, rng.Next(19));
                        else if (d < 0.30) tile = LoadWald(4, rng.Next(14));
                    }
                    else if (t == Ter.ForestPath && fill && d < 0.05) tile = LoadWald(3, 17 + rng.Next(2));
                    else if (t == Ter.Dirt)
                    {
                        bool shoulder = x == StreetX0 || x == StreetX0 + 1 || x == StreetX1 || x == StreetX1 - 1;
                        if (fill)
                        {
                            if (shoulder && y > 6 && d < 0.30) tile = LoadDorf(9, 3 + rng.Next(3));                  // Spurrillen (senkrecht)
                            else if (d > 0.985) tile = LoadDorf(9, 6 + rng.Next(2));                                   // Pfuetze (selten)
                            else if (d > 0.94) tile = LoadDorf(9, 12 + rng.Next(3));                                   // Steine
                            else if (d > 0.90) tile = LoadDorf(9, 15 + rng.Next(2));                                   // Laub
                            else if (d > 0.87) tile = LoadDorf(9, 17 + rng.Next(2));                                   // Stroh
                            else if (d > 0.855) tile = LoadDorf(9, 19);                                                // Fussabdruecke
                        }
                        else if (d < 0.50) tile = LoadDorf(9, 8 + rng.Next(4));                                        // Gras ragt in den Weg
                        else if (d < 0.70) tile = LoadDorf(10, 13 + rng.Next(3));                                      // Kieselsaum
                    }
                    else if (t == Ter.Cobble)
                    {
                        if (d < 0.07) tile = LoadDorf(10, rng.Next(4));                                                // Moosflecken
                        else if (d < 0.11) tile = LoadDorf(10, 4 + rng.Next(4));                                       // Risse
                        else if (d < 0.125) tile = LoadDorf(10, 8 + rng.Next(3));                                      // Blumen in den Fugen
                        else if (d < 0.135) tile = LoadDorf(10, 11 + rng.Next(2));                                     // Pilze
                        else if (d < 0.16) tile = LoadDorf(9, 15 + rng.Next(2));                                       // Laub
                        else if (d < 0.17) tile = LoadDorf(9, 6 + rng.Next(2));                                        // Pfuetze
                    }
                    else if (t == Ter.Slab)
                    {
                        if (d < 0.08) tile = LoadDorf(10, rng.Next(4));
                        else if (d < 0.12) tile = LoadDorf(10, 4 + rng.Next(4));
                        else if (d < 0.15) tile = LoadDorf(9, 8 + rng.Next(4));
                        else if (d < 0.19) tile = LoadDorf(9, 15 + rng.Next(2));
                    }
                    else if (t == Ter.Gravel)
                    {
                        if (d < 0.04) tile = LoadDorf(9, 6 + rng.Next(2));
                        else if (d < 0.09) tile = LoadDorf(9, 12 + rng.Next(3));
                        else if (d < 0.14) tile = LoadDorf(9, 15 + rng.Next(2));
                        else if (d < 0.17) tile = LoadDorf(9, 8 + rng.Next(4));
                        else if (d < 0.19) tile = LoadDorf(9, 17 + rng.Next(2));
                    }
                    if (tile != null) decoMap.SetTile(new Vector3Int(x, y, 0), tile);
                }
        }

        // ------------------------------------------------------------------ Objekte

        static bool IsGround(int x, int y)
        {
            var t = GetT(x, y);
            return t == Ter.Grass || t == Ter.Forest;
        }

        static readonly string[] NonSolidPrefixes =
        {
            "Stein_Klein", "Stein_Moos", "Stein_Platte", "Stein_Sand", "Kiesel", "Trittstein", "Aeste", "Wurzeln", "Farn", "Lavendel",
            "Grasbusch", "Heidekraut", "Kuerbis_Klein", "Korb", "Eimer", "Sack_Korn", "Kiste_Klein", "Windlicht", "Kerzen", "Schilf", "Seerosen",
            "Beet_", "Blumenkuebel", "Waescheleine", "Wegweiser_", "Ortsschild",
        };

        static bool BlocksMovement(string n)
        {
            foreach (var p in NonSolidPrefixes) if (n.StartsWith(p)) return false;
            return true;
        }

        /// <summary>Wie weit das Objekt in Zellen nach oben reserviert wird (hohe Objekte nur am Fuss).</summary>
        static int FootRows(string name)
        {
            if (name.StartsWith("Wegweiser_") || name == "Ortsschild" || name == "Waescheleine" || name == "Talisman_Pfosten" || name == "Kreuz_Schild" ||
                name == "Gartenlicht" || name == "Laterne_Doppel") return 1;
            return Mathf.Min(SizeOf(name).y, 2);
        }

        /// <summary>Setzt ein Objekt (kein Baum). onPath = darf auch auf Weg/Pflaster stehen (Laternen, Baenke, Marktstaende).</summary>
        static bool Put(string name, int x, int y, bool onPath = false)
        {
            var tile = PickObjTile(name);
            if (tile == null) { missing.Add(name); return false; }
            var sz = SizeOf(name);
            if (sz.x == 0) sz = Vector2Int.one;
            int rows = Mathf.Max(1, FootRows(name));
            for (int i = 0; i < sz.x; i++)
            {
                if (Occ(x + i, y)) return false;
                var t = GetT(x + i, y);
                if (t == Ter.Water) return false;
                if (!onPath && !(t == Ter.Grass || t == Ter.Forest)) return false;
            }
            for (int i = 0; i < sz.x; i++)
                for (int j = 0; j < rows; j++)
                    if (Occ(x + i, y + j)) return false;
            for (int i = 0; i < sz.x; i++)
                for (int j = 0; j < rows; j++)
                    occ[x + i - MinX, y + j - MinY] = true;
            if (BlocksMovement(name))
                for (int i = 0; i < sz.x; i++) if (InMap(x + i, y)) solid[x + i - MinX, y - MinY] = true;
            objMap.SetTile(new Vector3Int(x, y, 0), tile);
            return true;
        }

        static bool PutAny(string[] names, int x, int y, bool onPath = false)
        {
            int start = rng.Next(names.Length);
            for (int i = 0; i < names.Length; i++)
                if (Put(names[(start + i) % names.Length], x, y, onPath)) return true;
            return false;
        }

        static int Scatter(string[] names, int x0, int y0, int x1, int y1, int n, bool onPath = false)
        {
            int placed = 0;
            for (int k = 0; k < n * 6 && placed < n; k++)
                if (PutAny(names, rng.Next(x0, x1 + 1), rng.Next(y0, y1 + 1), onPath)) placed++;
            return placed;
        }

        /// <summary>Rechteck frei, Wiese und nicht reserviert.</summary>
        static bool Free(int x, int y, int w, int h)
        {
            for (int i = 0; i < w; i++)
                for (int j = 0; j < h; j++)
                    if (Occ(x + i, y + j) || !IsGround(x + i, y + j) || forest[x + i - MinX, y + j - MinY]) return false;
            return true;
        }

        // Zaeune: immer vollstaendig mit Endpfosten; ist ein Feld belegt, entstehen saubere Teilstuecke statt abgeschnittener Latten
        static void FenceH(int x0, int x1, int y)
        {
            int x = x0;
            while (x <= x1)
            {
                if (!Free(x, y, 1, 1)) { x++; continue; }
                int e = x;
                while (e + 1 <= x1 && Free(e + 1, y, 1, 1)) e++;
                if (e == x) Put("Zaun_Pfosten", x, y);
                else
                {
                    Put("Zaun_Links", x, y);
                    for (int i = x + 1; i < e; i++) Put("Zaun_Mitte", i, y);
                    Put("Zaun_Rechts", e, y);
                }
                x = e + 1;
            }
        }

        static void FenceV(int x, int y0, int y1)
        {
            int y = y0;
            while (y <= y1)
            {
                if (!Free(x, y, 1, 1)) { y++; continue; }
                int e = y;
                while (e + 1 <= y1 && Free(x, e + 1, 1, 1)) e++;
                Put("Zaun_Pfosten", x, y);
                for (int i = y + 1; i < e; i++) Put("Zaun_Senkrecht", x, i);
                if (e > y) Put("Zaun_Pfosten", x, e);
                y = e + 1;
            }
        }

        static void Light(Transform parent, string name, Vector3 pos, Color col, float intensity, float radius, bool night = true)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            var l = go.AddComponent<Light2D>();
            l.lightType = Light2D.LightType.Point;
            l.color = col;
            l.intensity = intensity;
            l.pointLightOuterRadius = radius;
            l.pointLightInnerRadius = radius * 0.2f;
            if (night) go.AddComponent<NightLight>();
        }

        static readonly Color LampColor = new Color(1f, 0.8f, 0.45f), FireColor = new Color(1f, 0.6f, 0.25f), TalismanColor = new Color(0.44f, 0.83f, 0.9f);

        /// <summary>Laterne mit Licht. kind: Laterne (Strasse), Gartenlicht (Gassen/Tueren), Laterne_Doppel (Plaetze).</summary>
        static bool Lamp(string kind, int x, int y)
        {
            if (!Put(kind, x, y, true)) return false;
            lampCount++;
            switch (kind)
            {
                case "Gartenlicht":
                    Light(lightsRoot, "Gartenlicht_Licht", new Vector3(x + 0.5f, y + 1.15f, 0), LampColor, 0.85f, 3.4f);
                    break;
                case "Laterne_Doppel":
                    Light(lightsRoot, "Laterne_Licht", new Vector3(x + 0.4f, y + 1.0f, 0), LampColor, 0.9f, 4.4f);
                    Light(lightsRoot, "Laterne_Licht", new Vector3(x + 1.6f, y + 1.0f, 0), LampColor, 0.9f, 4.4f);
                    break;
                default:
                    Light(lightsRoot, "Laternen_Licht", new Vector3(x + 0.5f, y + 1.6f, 0), LampColor, 0.95f, 4.4f);
                    break;
            }
            return true;
        }

        static void Lantern(int x, int y) => Lamp("Laterne", x, y);

        static void Fire(string name, int x, int y)
        {
            if (Put(name, x, y, true)) Light(lightsRoot, "Feuer_Licht", new Vector3(x + 0.5f, y + 0.7f, 0), FireColor, 1.1f, 5f);
        }

        static void Sign(string key, bool west, int x, int y) => Put($"Wegweiser_{key}_{(west ? "L" : "R")}", x, y);

        // ------------------------------------------------------------------ Baeume

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

        static string ForestTree(int x, int y, int depth)
        {
            string n;
            if (x < 30)
                n = Pick(("Eiche_Herbst", 2.5f), ("Eiche_A", 1.5f), ("Eiche_B", 1f), ("Birke_A", 1.5f), ("Birke_B", 1.5f), ("Birke_C", 1f), ("Kiefer_A", 0.8f), ("Fichte_Hoch_B", 0.8f));
            else if (y >= 100)
                n = Pick(("Fichte_Hoch_A", 3f), ("Fichte_Hoch_B", 3f), ("Fichte_Hoch_C", 3f), ("Fichte_Jung", 1f), ("Kiefer_A", 1f), ("Kiefer_B", 1f), ("Birke_A", 0.8f), ("Eiche_B", 0.8f));
            else
                n = Pick(("Eiche_A", 2f), ("Eiche_B", 2f), ("Birke_A", 1.5f), ("Birke_B", 1.5f), ("Birke_C", 1.2f), ("Kiefer_A", 1f), ("Kiefer_B", 1f), ("Fichte_Hoch_A", 1f), ("Fichte_Hoch_C", 1f), ("Fichte_Jung", 0.8f));
            if (depth >= 4 && rng.NextDouble() < 0.85 && ObjTile(n + "_Fern") != null) n += "_Fern";
            return n;
        }

        static string VillageTree()
        {
            return Pick(("Eiche_A", 2f), ("Eiche_B", 2f), ("Eiche_Apfel", 1.6f), ("Birke_A", 1.5f), ("Birke_B", 1.5f), ("Birke_C", 1.2f), ("Kiefer_A", 0.5f), ("Fichte_Jung", 0.6f));
        }

        static bool CanTree(int x, int y, string name, bool ignoreNear)
        {
            if (ObjTile(name) == null) { missing.Add(name); return false; }
            int cells = Mathf.Max(1, SizeOf(name).x);
            for (int cx = x; cx < x + cells; cx++)
                for (int cy = y; cy < y + 2; cy++)
                {
                    if (!InMap(cx, cy) || Occ(cx, cy) || !IsGround(cx, cy)) return false;
                    if (!ignoreNear && nearPW[cx - MinX, cy - MinY]) return false;
                }
            return true;
        }

        static bool PutTree(string name, int x, int y, bool collide, bool ignoreNear = false)
        {
            if (!CanTree(x, y, name, ignoreNear)) return false;
            int cells = Mathf.Max(1, SizeOf(name).x);
            for (int i = 0; i < cells; i++)
                for (int j = 0; j < 2; j++) occ[x + i - MinX, y + j - MinY] = true;
            bool split = ObjTile(name + "_Stamm") != null && ObjTile(name + "_Krone") != null;
            var cell = new Vector3Int(x, y, 0);
            objMap.SetTile(cell, ObjTile(split ? name + "_Stamm" : name));
            if (split) crownMap.SetTile(cell, ObjTile(name + "_Krone"));
            if (collide) trunkFeet.Add(new Vector2(x + PixelWidth(name) / 64f, y + 0.3f));
            return true;
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

        static void FillForest()
        {
            foreach (var c in ShuffledCells())
            {
                if (!forest[c.x - MinX, c.y - MinY]) continue;
                int depth = fdepth[c.x - MinX, c.y - MinY];
                bool zone1 = c.y >= -2 && c.y <= 9;
                double p = zone1 ? (depth <= 1 ? 0.30 : 0.45) : depth <= 1 ? 0.55 : 0.80;
                if (rng.NextDouble() > p) continue;
                bool collide = depth <= 2;
                for (int a = 0; a < 3; a++)
                    if (PutTree(ForestTree(c.x, c.y, depth), c.x, c.y, collide)) break;
            }
        }

        static void ScatterVillageTrees()
        {
            foreach (var c in ShuffledCells())
            {
                int x = c.x, y = c.y;
                if (forest[x - MinX, y - MinY] || occ[x - MinX, y - MinY] || y < -1) continue;
                bool edge = x < 14 || x > 66 || y > BachY - 8 || y < 14;
                double p = edge ? 0.20 : 0.075;
                if (rng.NextDouble() > p) continue;
                for (int a = 0; a < 3; a++)
                    if (PutTree(VillageTree(), x, y, true)) break;
            }
        }

        // Nur Buesche, deren Sprite nicht an der Zellkante abgeschnitten ist (Busch_Blueten_Rosa/Weiss/..., Busch_Gruen_A-D, Grasbusch_* u. a. sind flach beschnitten)
        static readonly string[] Bushes =
        {
            "Busch_Gruen", "Busch_Gruen", "Busch_Rund", "Busch_Rund", "Busch_Klein_A", "Busch_Klein_B", "Busch_Klein_C", "Busch_Gross_A", "Busch_Gross_B",
            "Busch_Blueten", "Busch_Blueten_Gross", "Heidelbeerbusch", "Lavendel_A", "Lavendel_B", "Farn_Gross",
        };
        static readonly string[] FlowerBeds = { "Busch_Rund", "Busch_Klein_A", "Busch_Klein_B", "Busch_Klein_C", "Lavendel_A", "Lavendel_B", "Busch_Blueten", "Blumenkuebel_Rosa", "Blumenkuebel_Gelb" };
        static readonly string[] Stones = { "Stein_Klein_A", "Stein_Klein_B", "Stein_Klein_C", "Stein_Moos", "Stein_Haufen", "Stein_Klein_D", "Stein_Klein_E" };

        static void ScatterSmall()
        {
            foreach (var c in ShuffledCells())
            {
                int x = c.x, y = c.y;
                if (!IsGround(x, y) || Occ(x, y)) continue;
                bool inF = forest[x - MinX, y - MinY];
                double d = rng.NextDouble();
                if (inF)
                {
                    if (d < 0.05) Put(Bushes[rng.Next(Bushes.Length)], x, y, false);
                    else if (d < 0.065) Put(Stones[rng.Next(Stones.Length)], x, y);
                    else if (d < 0.085) Put(new[] { "Aeste", "Wurzeln", "Baumstumpf_Pilze", "Baumstumpf" }[rng.Next(4)], x, y);
                }
                else if (!nearPW[x - MinX, y - MinY])
                {
                    if (d < 0.030) Put(Bushes[rng.Next(Bushes.Length)], x, y);
                    else if (d < 0.040) Put(Stones[rng.Next(Stones.Length)], x, y);
                    else if (d < 0.046) Put(new[] { "Baumstumpf", "Baumstumpf_Pilze", "Aeste" }[rng.Next(3)], x, y);
                }
            }
        }

        static void WaterProps()
        {
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    if (GetT(x, y) != Ter.Water || Occ(x, y)) continue;
                    bool shore = !(Conn(Ter.Water, GetT(x, y + 1)) && Conn(Ter.Water, GetT(x + 1, y)) && Conn(Ter.Water, GetT(x, y - 1)) && Conn(Ter.Water, GetT(x - 1, y)));
                    if (x >= StreetX0 - 1 && x <= StreetX1 + 1) continue;
                    var tile = shore ? (rng.NextDouble() < 0.3 ? PickObjTile("Schilf") : null) : (rng.NextDouble() < 0.12 ? PickObjTile("Seerosen") : null);
                    if (tile == null) continue;
                    occ[x - MinX, y - MinY] = true;
                    objMap.SetTile(new Vector3Int(x, y, 0), tile);
                }
        }

        // ------------------------------------------------------------------ Haeuser

        class House
        {
            public string prefab, label, sign;
            public int x, y, w, h;       // Basis links unten, Breite, Gesamthoehe (Wand + Dach + Schornstein)
            public int door, doorW;      // Tuer: x-Versatz und Breite
            public bool west, noLane;
            public int laneStartX = -999;
            public Transform tr;
        }

        static House H_(string prefab, string label, int x, int y, int w, int h, int door, int doorW, bool west, string sign = null) =>
            new House { prefab = prefab, label = label, x = x, y = y, w = w, h = h, door = door, doorW = doorW, west = west, sign = sign };

        static House NoLane(House h) { h.noLane = true; return h; }
        static House Lane(House h, int startX) { h.laneStartX = startX; return h; }

        // Dorfplan: links Wohnhaeuser/Baeckerei/Pfarrhaus, rechts Aerztehaus/Diner/Revier/Scheune (Bar, Markt, Friedhof separat), Reihen alle 15 Zellen
        static readonly House[] Houses =
        {
            H_("DorfWohnhausA", "Haus 1 (Bewohner)", 15, 112, 10, 8, 6, 1, true, "Homes"),
            H_("DorfWohnhausB", "Haus 2 (Bewohner)", 13, 97, 10, 8, 2, 1, true),
            H_("DorfWohnhausC", "Haus 3 (Bewohner)", 16, 82, 11, 8, 8, 1, true, "Homes"),
            H_("DorfBaeckerei", "Baeckerei (Mara)", 15, 67, 11, 8, 2, 2, true, "Bakery"),
            H_("DorfPfarrhaus", "Pfarrhaus (David)", 14, 52, 11, 9, 4, 2, true, "Pastor"),
            H_("DorfWohnhausD", "Dorfrand-Haus 5", 16, 37, 10, 8, 3, 1, true, "Homes"),
            H_("DorfWohnhausE", "Dorfrand-Haus 6 (leer)", 14, 22, 10, 8, 4, 1, true, "Homes"),
            H_("DorfAerztehaus", "Aerztehaus", 45, 112, 10, 8, 2, 1, false, "Doctor"),
            H_("DorfDiner", "Diner", 45, 77, 12, 8, 5, 2, false, "Diner"),
            H_("DorfRevier", "Revier (Bulut)", 46, 61, 11, 8, 5, 1, false, "Sheriff"),
            H_("DorfScheune", "Scheune", 45, 29, 12, 9, 4, 2, false, "Barn"),
            NoLane(H_("DorfVilla", "Villa", 41, VY, 16, 12, 7, 2, false)),
            // Zusaetzliche Kleinbauten fuer ein lebendiges Dorf (aus dem bestehenden Haus-Baukasten)
            Lane(H_("Schmiede", "Schmiede", 62, 41, 6, 7, 1, 2, false), 58),
            Lane(H_("Stall", "Stall", 61, 29, 7, 7, 6, 1, false), 49),
        };

        static void PlaceHouses()
        {
            housesRoot = new GameObject("Dorf_Haeuser").transform;
            housesRoot.SetParent(levelRoot, false);
            foreach (var h in Houses)
            {
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>($"{HouseDir}Haus_{h.prefab}_Aussen.prefab");
                if (prefab == null) { issues.Add("Haus-Prefab fehlt: " + h.prefab); continue; }
                var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, housesRoot);
                go.transform.position = new Vector3(h.x, h.y, 0f);
                go.name = h.label;
                h.tr = go.transform;
                FillRect(Ter.Grass, h.x - 1, h.y, h.x + h.w, h.y + h.h);
                Reserve(h.x - 1, h.y - 1, h.x + h.w, h.y + h.h);
            }
        }

        // ------------------------------------------------------------------ Bar, Markt, Friedhof, Villa-Garten

        static GameObject barInstance;
        const int BarX = 46, BarY = 96;

        static void PlaceBar()
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(BarPrefab);
            if (prefab == null) { issues.Add("Bar-Prefab fehlt: " + BarPrefab); return; }
            FillRect(Ter.Grass, BarX - 8, BarY - 10, BarX + 28, BarY + 9);
            barInstance = (GameObject)PrefabUtility.InstantiatePrefab(prefab, housesRoot);
            barInstance.name = "Ilhans_Bar";
            barInstance.transform.position = new Vector3(BarX, BarY, 0f);
            // Die alte, helle Barstrasse des Prefabs wird durch Dorf-Pflaster ersetzt (Moos, Randsteine, sauberer Uebergang zur Erdstrasse);
            // nur der Platz vor der Bar bleibt aus dem Prefab
            var weg = barInstance.transform.Find("Aussen/Gelaende/a_weg");
            var wegMap = weg != null ? weg.GetComponent<Tilemap>() : null;
            if (wegMap != null)
                foreach (var pos in wegMap.cellBounds.allPositionsWithin)
                    if (wegMap.HasTile(pos)) wegMap.SetTile(pos, null);
            FillRect(Ter.Cobble, 38, BarY - 10, BarX + 27, BarY - 9);          // Strasse
            FillRect(Ter.Cobble, BarX + 5, BarY - 10, BarX + 15, BarY - 2);    // Platz vor der Bar
            var innen = barInstance.transform.Find("Innen_IlhansBar");
            if (innen != null) innen.localPosition = new Vector3(100f, -BarY, 0f);
            for (int x = BarX - 8; x <= BarX + 28; x++)
                for (int y = BarY - 10; y <= BarY + 10; y++)
                    if (InMap(x, y)) { forest[x - MinX, y - MinY] = false; fdepth[x - MinX, y - MinY] = 0; }
            // Wiese drumherum bleibt frei fuer Baeume, Laternen und kleine Szenen; erst die eigenen Objekte setzen, dann nur
            // Gebaeude, Platz, Strasse und die Objekte des Bar-Prefabs (Schilder, Brunnen, Baenke) als belegt markieren
            Lamp("Laterne_Doppel", BarX - 5, BarY - 7); Lamp("Laterne_Doppel", BarX + 25, BarY - 7);
            Lamp("Gartenlicht", BarX - 2, BarY - 7); Lamp("Gartenlicht", BarX + 22, BarY - 7);
            Lamp("Gartenlicht", BarX + 10, BarY - 11);
            Sign("Bar", false, 40, BarY - 12);
            Lamp("Gartenlicht", 39, BarY - 12);
            Put("Talisman_Pfosten", BarX - 3, BarY + 1);
            Light(lightsRoot, "Talisman_Licht", new Vector3(BarX - 2.5f, BarY + 2.2f, 0), TalismanColor, 0.8f, 3f);
            Put("Talisman_Pfosten", BarX + 23, BarY + 1);
            Light(lightsRoot, "Talisman_Licht", new Vector3(BarX + 23.5f, BarY + 2.2f, 0), TalismanColor, 0.8f, 3f);
            Reserve(BarX - 1, BarY - 2, BarX + 21, BarY + 9);        // Gebaeude mit Veranda
            Reserve(BarX + 4, BarY - 10, BarX + 16, BarY - 2);       // Pflasterplatz
            Reserve(BarX - 8, BarY - 10, BarX + 28, BarY - 8);       // Strasse nach Westen/Osten
            Reserve(BarX - 1, BarY - 8, BarX + 4, BarY - 3);         // Schild links
            Reserve(BarX + 16, BarY - 9, BarX + 28, BarY - 3);       // Brunnen, Schild, Baenke rechts
        }

        static void FenceRect(int x0, int y0, int x1, int y1, int gapX0 = -999, int gapX1 = -999)
        {
            // Rahmen aus vollstaendigen Zaunstuecken; die Luecke (Tor) liegt unten
            if (gapX0 == -999) FenceH(x0, x1, y0);
            else { FenceH(x0, gapX0 - 1, y0); FenceH(gapX1 + 1, x1, y0); }
            FenceH(x0, x1, y1);
            FenceV(x0, y0 + 1, y1 - 1);
            FenceV(x1, y0 + 1, y1 - 1);
        }

        static void PlaceMarket()
        {
            string[] tents = { "Zelt_Braun", "Zelt_Violett", "Zelt_Braun" };
            int x = 43;
            foreach (var t in tents)
            {
                int w = Mathf.Max(3, SizeOf(t).x);
                if (Put(t, x, 48, true))
                {
                    Put("Tisch", x, 46, true);
                    Put("Korb_Aepfel", x + 1, 45, true); Put("Kiste_Karotten", x + Mathf.Max(1, w - 1), 45, true);
                    Put("Sack_Mehl", x + w, 46, true);
                    Put("Fass_Aepfel", x - 1, 48, true);
                }
                x += w + 2;
            }
            Put("Fahne_Rot", 41, 51, true); Put("Fahne_Blau", 58, 51, true); Put("Fahne_Rot", 58, 39, true);
            Put("Karren_Kisten", 52, 42, true); Put("Karren_Heu", 44, 42, true); Put("Schubkarre_Voll", 48, 43, true);
            Put("Tisch_Gedeckt", 54, 44, true); Put("Hocker", 53, 43, true); Put("Hocker", 56, 43, true);
            Put("Kiste_Fisch", 46, 40, true); Put("Kiste_Kohl", 49, 40, true); Put("Kuerbis_Gruppe", 55, 49, true);
            Put("Korb_Brot", 50, 44, true); Put("Eimer_Milch", 57, 40, true);
            Lamp("Laterne_Doppel", 41, 52); Lamp("Laterne_Doppel", 57, 52); Lamp("Laterne_Doppel", 41, 39); Lamp("Laterne_Doppel", 56, 39);
            Put("Schild_Laden", 40, 53, true);
            Sign("Market", false, 39, 48);
            Lamp("Gartenlicht", 38, 47);
        }

        static void PlaceGraveyard()
        {
            FenceRect(45, 9, 58, 22, 50, 52);
            Put("Tor_Offen", 50, 9, true);
            string[] stones = { "Grabstein_A", "Grabstein_B", "Grabstein_C" };
            for (int gx = 47; gx <= 55; gx += 2)
                for (int gy = 12; gy <= 20; gy += 2)
                    if (!(gx >= 49 && gx <= 53 && gy <= 12)) Put(stones[rng.Next(stones.Length)], gx, gy);
            Put("Menhir_A", 51, 20); Put("Windlicht", 49, 11, true); Put("Windlicht", 53, 11, true);
            Put("Kerzen", 48, 14, true); Put("Kerzen", 56, 17, true);
            PutTree("Birke_A", 46, 18, true, true); PutTree("Birke_C", 56, 11, true, true);
            Put("Busch_Dunkel", 47, 10); Put("Busch_Dunkel", 56, 21);
            Sign("Graves", false, 39, 8);
            Lamp("Gartenlicht", 38, 8); Lamp("Gartenlicht", 49, 8); Lamp("Gartenlicht", 53, 8);
            Put("Talisman_Pfosten", 59, 13);
            Light(lightsRoot, "Talisman_Licht", new Vector3(59.5f, 14.2f, 0), TalismanColor, 0.8f, 3f);
        }

        static void PlaceVillaGarden()
        {
            // Vorplatz: Platten, Hecken, Fahnen, Brunnen, Laternen
            for (int x = 40; x <= 59; x += 2) if (x < 47 || x > 52) Put("Hecke", x, VY - 7);
            Put("Fahne_Rot", 43, VY - 6, true); Put("Fahne_Rot", 55, VY - 6, true);
            Lamp("Laterne_Doppel", 43, VY - 4); Lamp("Laterne_Doppel", 55, VY - 4);
            Lamp("Gartenlicht", 46, VY - 2); Lamp("Gartenlicht", 51, VY - 2);
            Scatter(FlowerBeds, 58, VY - 6, 63, VY + 2, 6);
            Scatter(FlowerBeds, 38, VY - 2, 41, VY + 6, 3);
            Put("Brunnen", 52, VY - 5, true);
            Put("Bank_Lehne", 44, VY - 2, true); Put("Bank_Lehne", 56, VY - 2, true);
            Sign("Villa", false, 39, VY - 2);
            Lamp("Gartenlicht", 38, VY - 4);
            Put("Talisman_Pfosten", 41, VY - 3);
            Light(lightsRoot, "Talisman_Licht", new Vector3(41.5f, VY - 1.8f, 0), TalismanColor, 0.8f, 3f);
            PutTree("Eiche_A", 60, VY - 1, true, true); PutTree("Birke_B", 58, VY + 6, true, true);
        }

        static void PlaceStreet()
        {
            // Strassenlaternen: links/rechts abwechselnd alle 8 Zellen; Schilder, Plaetze, Bruecke bekommen eigene Lichter
            for (int y = 4; y <= BachY - 8; y += 8)
            {
                Lantern(StreetX0 - 1, y);
                Lantern(StreetX1 + 1, y + 4);
            }
            // Dorfplatz: Brunnen im Plattenring, Baenke, Doppellaternen, Wassertrog
            Put("Brunnen", 34, 66, true);
            Put("Bank_Lehne", 29, 66, true); Put("Bank_Lehne", 40, 66, true); Put("Bank", 31, 63, true); Put("Bank", 38, 69, true);
            Lamp("Laterne_Doppel", 28, 63); Lamp("Laterne_Doppel", 41, 69); Lamp("Laterne_Doppel", 28, 69); Lamp("Laterne_Doppel", 41, 63);
            Put("Wassertrog", 30, 69, true); Put("Fass_Wasser", 39, 62, true); Put("Tafel", 38, 62, true);
            Fire("Feuerschale", 33, 62); Fire("Feuerschale", 37, 70);
            // Ortseingaenge: "DUSK BELL"-Schild, Strasse bleibt offen
            Put("Ortsschild", 28, BachY + 5);
            Put("Ortsschild", 39, 2);
            Lamp("Laterne_Doppel", 29, BachY + 2); Lamp("Laterne_Doppel", 38, BachY + 2);
            Lamp("Laterne_Doppel", 29, BachY - 6); Lamp("Laterne_Doppel", 38, BachY - 6);
            Lamp("Gartenlicht", 31, 3); Lamp("Gartenlicht", 38, 7);
            Sign("Forest", true, 29, 9);
            // Uferweg am Bach: Baenke, Laternen, Boot, Fischerei
            Put("Bank_Lehne", 14, BachY - 9); Put("Bank_Lehne", 24, BachY - 9);
            foreach (int lx in new[] { 8, 16, 22, 28 }) Lamp("Gartenlicht", lx, BachY - 5);
            Put("Ruderboot", 12, BachY - 4); Put("Fass_Fisch", 15, BachY - 4); Put("Kiste_Fisch", 16, BachY - 4); Put("Wassertrog", 26, BachY - 4);
            Put("Wegweiser_Homes_L", 29, BachY - 9);
        }

        static void GardenFor(House h)
        {
            if (h.noLane) return;
            int dc = h.x + h.door;
            int aw = Mathf.Max(1, h.doorW);
            int apronL = dc - 1, apronR = dc + aw;
            bool west = h.west;
            // Zaun an der Grundstuecksgrenze (vollstaendig, mit Endpfosten)
            FenceH(h.x - 2, h.x + h.w + 1, h.y - 6);
            int outerX = west ? h.x - 2 : h.x + h.w + 1;
            FenceV(outerX, h.y - 5, h.y + 5);
            // Tuerplatz: Laternen links und rechts, Talisman-Pfosten (Schutzraum), Schilder
            Lamp("Gartenlicht", apronL - 1, h.y - 2);
            Lamp("Gartenlicht", apronR + 1, h.y - 2);
            if (h.label.StartsWith("Haus") || h.label.StartsWith("Dorfrand") || h.label.StartsWith("Baeckerei") || h.label.StartsWith("Pfarr") || h.label.StartsWith("Revier") || h.label.StartsWith("Aerzte"))
            {
                int tx = west ? apronL - 3 : apronR + 3;
                if (Put("Talisman_Pfosten", tx, h.y - 3))
                    Light(lightsRoot, "Talisman_Licht", new Vector3(tx + 0.5f, h.y - 1.8f, 0), TalismanColor, 0.7f, 2.6f);
            }
            // Gasse: Wegweiser an der Einmuendung (zuerst, damit die Laterne ihn nicht verdraengt), daneben eine Laterne
            if (h.sign != null) Sign(h.sign, west, west ? 28 : 40, h.y - 3);
            Lamp("Gartenlicht", west ? StreetX0 - 2 : StreetX1 + 2, h.y - 3);
            if (h.sign == "Doctor")
            {
                Put("Kreuz_Schild", h.x - 1, h.y - 2);
                Put("Kreuz_Schild", StreetX1 + 3, h.y - 2);
            }
            // Beete und Kuebel links/rechts des Tuerplatzes
            string[] beds = { "Beet_Kohl", "Beet_Karotten", "Beet_Kraeuter", "Beet_Blumen", "Beet_Kuerbis" };
            Put(beds[rng.Next(beds.Length)], h.x, h.y - 3);
            if (apronL - 2 >= h.x + 2) Put(beds[rng.Next(beds.Length)], h.x + 2, h.y - 3);
            Put("Blumenkuebel_Rosa", apronR + 2, h.y - 2); Put("Blumenkuebel_Gelb", apronR + 3, h.y - 2);
            // Seitengarten (abgewandt von der Strasse): Gemuese, Waescheleine, Brennholz, Obstbaeume
            int sx = west ? h.x - 8 : h.x + h.w + 2;
            Put("Waescheleine", sx, h.y + 3);
            Put(beds[rng.Next(beds.Length)], sx, h.y);
            Put(beds[rng.Next(beds.Length)], sx + 2, h.y);
            Put("Holzstapel_Gross", west ? h.x - 4 : h.x + h.w + 2, h.y + 5);
            Put("Fass_Wasser", west ? h.x - 3 : h.x + h.w + 4, h.y + 6);
            PutTree("Eiche_Apfel", west ? h.x - 5 : h.x + h.w + 8, h.y + 1, true);
            PutTree(rng.NextDouble() < 0.5 ? "Birke_A" : "Eiche_B", west ? h.x + h.w + 2 : h.x - 4, h.y + 1, true);
            PutTree(VillageTree(), h.x + 2, h.y + h.h + 1, true);
            PutTree(VillageTree(), h.x + h.w - 3, h.y + h.h + 2, true);
            Scatter(FlowerBeds, h.x - 1, h.y - 5, h.x + h.w, h.y - 4, 3);
        }

        static void PlaceSpecialProps()
        {
            var b = Houses[3];   // Baeckerei
            Put("Korb_Brot", b.x + 6, b.y - 2, true); Put("Sack_Mehl", b.x + 8, b.y - 2, true); Put("Sack_Mehl", b.x + 9, b.y - 2, true);
            Put("Tisch", b.x + 6, b.y - 4); Put("Hocker", b.x + 5, b.y - 4); Put("Hocker", b.x + 8, b.y - 4);
            var p = Houses[4];   // Pfarrhaus
            Put("Windlicht", p.x + 2, p.y - 2, true); Put("Windlicht", p.x + 8, p.y - 2, true);
            Put("Bank_Lehne", p.x + 7, p.y - 3);
            var d = Houses[8];   // Diner
            foreach (int tx in new[] { 0, 3, 9 })
            {
                Put("Tisch", d.x + tx, d.y - 3); Put("Hocker", d.x + tx - 1, d.y - 3); Put("Hocker", d.x + tx + 1, d.y - 3);
            }
            Put("Schild_Taverne", d.x + 11, d.y - 2, true);
            var r = Houses[9];   // Revier
            Put("Fahne_Blau", r.x + 1, r.y - 2, true); Put("Fahne_Blau", r.x + 9, r.y - 2, true);
            Put("Bank_Lehne", r.x + 7, r.y - 3); Put("Tafel", r.x + 3, r.y - 3);
            var s = Houses[10];  // Scheune
            Put("Heuballen_Rund", s.x + 12, s.y - 1); Put("Heuballen_Eckig", s.x + 13, s.y - 1); Put("Karren_Heu", s.x + 7, s.y - 3);
            Put("Heuballen_Rund", s.x - 3, s.y - 1); Put("Vogelscheuche", s.x - 2, s.y - 5);
            var e = Houses[6];   // leeres Haus: verwildert
            Scatter(new[] { "Busch_Dunkel_A", "Busch_Dornen", "Busch_Tot_C", "Farn_Dunkel", "Stein_Klein_B" }, e.x - 2, e.y - 6, e.x + e.w + 1, e.y - 2, 9);
            Put("Fass_Zerbrochen", e.x + 8, e.y - 3); Put("Kiste_Kaputt", e.x + 1, e.y - 3);
            var sm = Houses[12]; // Schmiede
            Put("Amboss", sm.x + 2, sm.y - 2, true); Put("Hackklotz_Axt", sm.x + 4, sm.y - 3);
            Fire("Feuerschale", sm.x - 1, sm.y - 3);
            Sign("Smith", false, 59, 40);
            Lamp("Gartenlicht", 60, 38);
            var st = Houses[13]; // Stall
            Put("Heuballen_Rund", st.x - 2, st.y - 1); Put("Heuballen_Eckig", st.x + st.w + 1, st.y - 1); Put("Karren_Heu", st.x + 8, st.y - 3);
            Put("Briefkasten", 30, 58, true); Put("Briefkasten", 39, 73, true);
        }

        static void PlaceZone1()
        {
            PutTree("Birke_A", 8, 4, true, true);
            Put("Baumstumpf", 10, 3); Put("Baumstumpf_Pilze", 11, 5); Put("Wurzeln", 9, 2); Put("Aeste", 12, 6);
            Put("Stein_Findling", 26, 3, true); Put("Stein_Moos", 27, 5); Put("Farn_Gross", 24, 4); Put("Farn_Dicht", 29, 4);
        }

        /// <summary>Keine grossen leeren Flaechen: freie Fenster bekommen kleine Szenen (Sitzplatz, Holzplatz, Beet, Baumgruppe, Rastplatz).</summary>
        static void FillEmpty()
        {
            for (int pass = 0; pass < 8; pass++)
            {
                int placedThisPass = 0;
                for (int y = 8; y <= BachY - 8; y += 2)
                    for (int x = 8; x <= 72; x += 2)
                    {
                        if (!Free(x, y, 4, 4)) continue;
                        int cx = x + 1, cy = y + 1;
                        switch (rng.Next(7))
                        {
                            case 0:
                                PutTree(VillageTree(), cx + 1, cy, true, true);
                                Scatter(FlowerBeds, x, y, x + 4, y + 4, 3);
                                break;
                            case 1:
                                Put("Bank_Lehne", cx, cy); Lamp("Gartenlicht", cx + 2, cy); Scatter(FlowerBeds, x, y, x + 4, y + 4, 3);
                                break;
                            case 2:
                                Put("Fass", cx, cy); Put("Kiste", cx + 1, cy); Put("Sack_Haufen", cx, cy + 1); Put("Kiste_Stapel_2", cx + 2, cy + 1); Put("Eimer_Wasser", cx + 3, cy);
                                break;
                            case 3:
                                Put("Holzstapel_Gross", cx, cy); Put("Hackklotz_Axt", cx + 2, cy); Put("Baumstumpf", cx + 3, cy + 1); Put("Aeste", cx + 1, cy + 2);
                                break;
                            case 4:
                                Put("Heuballen_Rund", cx, cy); Put("Heuballen_Eckig", cx + 1, cy); Put("Karren_Heu", cx, cy + 2);
                                break;
                            case 5:
                                Put("Tisch", cx, cy); Put("Hocker", cx - 1, cy); Put("Hocker", cx + 1, cy); Put("Windlicht", cx, cy + 1);
                                break;
                            default:
                                Put("Beet_Kohl", cx, cy); Put("Beet_Blumen", cx, cy + 1); Put("Vogelscheuche", cx + 2, cy + 1); Scatter(FlowerBeds, x, y, x + 4, y + 4, 2);
                                break;
                        }
                        placedThisPass++;
                        Reserve(x, y, x + 3, y + 3);   // Fenster markieren, damit nicht doppelt gefuellt wird
                    }
                if (placedThisPass == 0) break;
            }
        }

        // ------------------------------------------------------------------ Kollision

        static void BuildCollision(Transform grid, Transform root)
        {
            var colGo = new GameObject("Collision");
            colGo.transform.SetParent(grid, false);
            var colMap = colGo.AddComponent<Tilemap>();
            var tc = colGo.AddComponent<TilemapCollider2D>();
            var rb = colGo.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Static;
            var cc = colGo.AddComponent<CompositeCollider2D>();
            cc.geometryType = CompositeCollider2D.GeometryType.Polygons;
            tc.compositeOperation = Collider2D.CompositeOperation.Merge;
            var block = AssetDatabase.LoadAssetAtPath<TileBase>(TileAssets + "/Collision_Block.asset");

            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    bool s = solid[x - MinX, y - MinY];
                    int i = x - MinX, j = y - MinY;
                    var t = ter[i, j];
                    // tiefer Wald ist eine Wand, Waldwege (auch die Strasse nach Norden und Sueden) bleiben offen
                    bool pathy = t == Ter.ForestPath || t == Ter.Dirt;
                    if (forest[i, j] && fdepth[i, j] >= 3 && !pathy) s = true;
                    if (y <= -4 && !pathy) s = true;
                    if (t == Ter.Water && !(x >= 33 && x <= 36 && y >= BachY - 2 && y <= BachY + 2)) s = true;
                    if (s) colMap.SetTile(new Vector3Int(x, y, 0), block);
                }
            // Bruecke: Gelaender links und rechts
            for (int y = BachY - 1; y <= BachY + 1; y++)
            {
                colMap.SetTile(new Vector3Int(32, y, 0), block);
                colMap.SetTile(new Vector3Int(37, y, 0), block);
            }
            for (int x = MinX - 1; x <= MaxX + 1; x++)
            {
                colMap.SetTile(new Vector3Int(x, MinY - 1, 0), block);
                colMap.SetTile(new Vector3Int(x, MaxY + 1, 0), block);
            }
            for (int y = MinY - 1; y <= MaxY + 1; y++)
            {
                colMap.SetTile(new Vector3Int(MinX - 1, y, 0), block);
                colMap.SetTile(new Vector3Int(MaxX + 1, y, 0), block);
            }

            var trunks = new GameObject("TrunkColliders");
            trunks.transform.SetParent(root);
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
        }

        static void BuildBridge(Tilemap bridge)
        {
            int y0 = BachY - 1, y1 = BachY + 1;
            for (int x = 33; x <= 36; x++)
            {
                bridge.SetTile(new Vector3Int(x, y1 + 1, 0), LoadTerrain(6, 3));
                for (int y = y0; y <= y1; y++) bridge.SetTile(new Vector3Int(x, y, 0), LoadTerrain(6, 4));
                bridge.SetTile(new Vector3Int(x, y0 - 1, 0), LoadTerrain(6, 5));
            }
        }

        // ------------------------------------------------------------------ Bauen

        [MenuItem("Nightward/Dorf/2 Dorf bauen (Level_01)")]
        public static void Build()
        {
            if (EditorApplication.isPlaying) { Debug.LogWarning("[Dorf] Bitte erst den Play-Modus beenden."); return; }
            if (LoadDorf(0, 0) == null) ImportDorfArt();
            var scene = SceneManager.GetSceneByPath(ScenePath);
            if (!scene.IsValid() || !scene.isLoaded) scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Additive);
            var previous = SceneManager.GetActiveScene();
            SceneManager.SetActiveScene(scene);
            try { BuildInto(scene); }
            finally { if (previous.IsValid() && previous.isLoaded) SceneManager.SetActiveScene(previous); }
        }

        static void BuildInto(Scene scene)
        {
            rng = new System.Random(20261021);
            trunkFeet.Clear();
            missing.Clear();
            issues.Clear();
            sizeCache.Clear();
            lampCount = 0;
            LoadAnimVariants();

            foreach (var g in scene.GetRootGameObjects())
                if (g.name == "Level_01") UnityEngine.Object.DestroyImmediate(g);

            BuildTerrain();
            ComputeForest();

            var root = new GameObject("Level_01");
            levelRoot = root.transform;
            var grid = new GameObject("Grid");
            grid.transform.SetParent(root.transform);
            grid.AddComponent<Grid>();
            lightsRoot = new GameObject("Lights").transform;
            lightsRoot.SetParent(root.transform);

            var lit = AssetDatabase.LoadAssetAtPath<Material>(LitMaterial);
            Tilemap Layer(string name, int order, bool individual)
            {
                var go = new GameObject(name);
                go.transform.SetParent(grid.transform, false);
                var tm = go.AddComponent<Tilemap>();
                tm.animationFrameRate = 1f;
                var tr = go.AddComponent<TilemapRenderer>();
                tr.sortingOrder = order;
                if (lit != null) tr.sharedMaterial = lit;
                if (individual) tr.mode = TilemapRenderer.Mode.Individual;
                return tm;
            }
            var ground = Layer("Ground", OrderGround, false);
            var overlay = Layer("Wege", OrderOverlay, false);
            decoMap = Layer("Deco", OrderDeco, false);
            var bridge = Layer("Bridge", OrderBridge, false);
            objMap = Layer("Objects", OrderObjects, true);
            objMap.tileAnchor = Vector3.zero;
            crownMap = Layer("Crowns", OrderCrowns, true);
            crownMap.tileAnchor = Vector3.zero;

            PlaceHouses();
            PlaceBar();
            nearPW = new bool[W, H];
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                    for (int dx = -1; dx <= 1; dx++)
                        for (int dy = -1; dy <= 1; dy++)
                        {
                            var t = GetT(x + dx, y + dy);
                            if (IsPathy(t) || t == Ter.Water) nearPW[x - MinX, y - MinY] = true;
                        }

            // Reihenfolge: erst feste Strukturen (Zaeune, Schilder, Laternen, Beete), dann freie Dekoration, dann Baeume
            BuildBridge(bridge);
            PlaceStreet();
            PlaceMarket();
            PlaceGraveyard();
            PlaceVillaGarden();
            PlaceSpecialProps();
            foreach (var h in Houses) GardenFor(h);
            PlaceZone1();
            ScatterVillageTrees();
            FillForest();
            FillEmpty();
            ScatterSmall();
            WaterProps();

            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    ground.SetTile(new Vector3Int(x, y, 0), TerrainTile(x, y));
                    var ov = OverlayTile(x, y);
                    if (ov != null) overlay.SetTile(new Vector3Int(x, y, 0), ov);
                }
            Deco();

            BuildCollision(grid.transform, root.transform);

            var fader = crownMap.gameObject.AddComponent<CanopyFader>();
            var fso = new SerializedObject(fader);
            fso.FindProperty("crowns").objectReferenceValue = crownMap;
            fso.ApplyModifiedPropertiesWithoutUndo();

            foreach (var g in scene.GetRootGameObjects())
            {
                if (g.name == "Main Camera")
                {
                    var cam = g.GetComponent<Camera>();
                    cam.backgroundColor = new Color(0.07f, 0.11f, 0.08f);
                    cam.transparencySortMode = TransparencySortMode.CustomAxis;
                    cam.transparencySortAxis = new Vector3(0, 1, 0);
                    var cf = g.GetComponent<CameraFollow2D>();
                    if (cf != null)
                    {
                        var so = new SerializedObject(cf);
                        so.FindProperty("clampToBounds").boolValue = false;   // Bar-Innenraum liegt ausserhalb der Dorfkarte
                        so.ApplyModifiedPropertiesWithoutUndo();
                    }
                }
                else if (g.name == "Player")
                {
                    g.transform.position = new Vector3(35f, 12f, 0f);
                    foreach (var sr in g.GetComponentsInChildren<SpriteRenderer>()) sr.sortingOrder = OrderObjects;
                }
                else if (g.name == "NPC_Ilhan") g.transform.position = new Vector3(BarX + 8f, BarY - 4.5f, 0f);
                else if (g.name == "NPC_Ilhan_Bartender") g.transform.position = new Vector3(BarX + 12f, BarY - 4.5f, 0f);
                else if (g.name == "NPC_Bulut_Sheriff") g.transform.position = new Vector3(Houses[9].x + Houses[9].door + 1.5f, Houses[9].y - 3.5f, 0f);
                else if (g.name == "NPC_Gast") g.transform.position = new Vector3(31.5f, 64.5f, 0f);
                else if (g.name == "NPC_Hausfrau") g.transform.position = new Vector3(Houses[5].x + Houses[5].door + 1.5f, Houses[5].y - 3.5f, 0f);
            }

            Debug.Log("[Dorf] Level_01 gebaut. Baeume mit Stammkollision: " + trunkFeet.Count + ", Laternen: " + lampCount +
                      (missing.Count > 0 ? "\nFehlende Objekte: " + string.Join(", ", missing) : "") +
                      (issues.Count > 0 ? "\nProbleme:\n" + string.Join("\n", issues) : ""));

            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }
    }
}
