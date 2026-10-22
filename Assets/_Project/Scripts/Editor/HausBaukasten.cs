using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Nightward.DayNight;
using Nightward.Vision;
using UnityEditor;
using UnityEditor.Tilemaps;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Tilemaps;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Haus-Baukasten: importiert Art/Tiles/Baukasten (erzeugt von _Quelle_Generator/bk_build.py), legt Tiles,
    /// AnimatedTiles und RuleTiles an (Waende, Daecher, Innenwaende, Mauerkronen, Boeden setzen Kanten/Ecken selbst),
    /// baut vier Paletten und erzeugt aus Bauplaene.json je Haus ein Aussen- und ein Innen-Prefab.
    /// Jeder Bauplan wird vorher geprueft (gleiche Regeln wie im Python-Generator); fehlerhafte Plaene werden nicht gebaut.
    /// Bestehende Tile-Assets werden aktualisiert statt geloescht (GUIDs bleiben, Szenen behalten ihre Referenzen).
    /// </summary>
    public static class HausBaukasten
    {
        const string Root = "Assets/_Project/Art/Tiles/Baukasten";
        const string ObjDir = Root + "/Objekte";
        const string AnimDir = Root + "/Animiert";
        const string TA = "Assets/_Project/Art/Tiles/TileAssets/Baukasten";
        const string PaletteDir = "Assets/_Project/Art/Tiles/Palettes";
        const string PrefabDir = "Assets/_Project/Prefabs/Haeuser";
        const string CollisionTile = "Assets/_Project/Art/Tiles/TileAssets/Collision_Block.asset";
        const string SheetA = Root + "/Tileset_BK_Aussen.png";
        const string SheetI = Root + "/Tileset_BK_Innen.png";
        const int Cell = 32;

        // Sortierung wie Level1Builder: Objects/Spieler = 4 (Innen-Kronen sortieren mit, damit Tuerdurchgaenge stimmen)
        const int OrderObjects = 4;

        // Kanten-Laeufe mit Zufallsvarianten (Spalten im Aussen-Sheet, siehe bk_aussen.autotile_set)
        static readonly Dictionary<int, int[]> EdgeVariants = new Dictionary<int, int[]>
        {
            { 11, new[] { 11, 20, 21 } }, { 14, new[] { 14, 22, 23 } }, { 10, new[] { 10, 24, 25 } },
        };

        // ------------------------------------------------------------------ Daten
        [Serializable] class Layout
        {
            public int cols;
            public string[] wand, dach, innenWand, krone, boden, overlay;
            public int dachStartZeile, innenWandZeile, kroneZeile, bodenZeile, bodenJeZeile, overlayZeile;
        }

        [Serializable] public class Obj { public string o; public int x, y; }
        [Serializable] public class Aussen { public int breite, wandHoehe, dachHoehe, ueberstand; public string wand, dach; public Obj[] deko; }
        [Serializable] public class Innen { public int breite, hoehe, tuerX; public string boden, wand, krone; public Obj[] objekte; }
        [Serializable] public class Haus { public string name; public Aussen aussen; public Innen innen; }
        [Serializable] class Plan { public Haus[] haeuser; }

        public class Info { public string name, kat; public int w, h, fuss, frames, ms; public bool solid; }

        static Layout layout;
        static Dictionary<string, Info> infos;

        static Layout LoadLayout() => JsonUtility.FromJson<Layout>(File.ReadAllText(Root + "/_Tilesets.json"));

        public static Dictionary<string, Info> LoadInfos()
        {
            var d = new Dictionary<string, Info>();
            foreach (var raw in File.ReadAllLines(Root + "/_Liste.txt"))
            {
                if (raw.StartsWith("#") || raw.Trim().Length == 0) continue;
                var p = raw.Split('|').Select(s => s.Trim()).ToArray();
                var wh = p[1].Split('x');
                d[p[0]] = new Info
                {
                    name = p[0], w = int.Parse(wh[0]) / Cell, h = int.Parse(wh[1]) / Cell, kat = p[2],
                    fuss = int.Parse(p[3]), solid = p[4] == "1", frames = int.Parse(p[5]), ms = int.Parse(p[6])
                };
            }
            return d;
        }

        // ------------------------------------------------------------------ Menue
        [MenuItem("Nightward/Haus-Baukasten/Alles bauen (Import, Tiles, Paletten, Haeuser)")]
        public static void BuildAll()
        {
            ImportAndTiles();
            BuildHouses();
        }

        [MenuItem("Nightward/Haus-Baukasten/1 Import + Tiles + Paletten")]
        public static void ImportAndTiles()
        {
            AssetDatabase.Refresh();
            layout = LoadLayout();
            infos = LoadInfos();
            ConfigureImports();
            CreateTiles();
            CreateRuleTiles();
            CreatePalettes();
            AssetDatabase.SaveAssets();
            Debug.Log($"[Haus-Baukasten] Import fertig: {infos.Count} Objekte, Paletten Pal_BK_*.");
        }

        [MenuItem("Nightward/Haus-Baukasten/2 Haeuser aus Bauplaene.json bauen")]
        public static void BuildHouses()
        {
            layout = layout ?? LoadLayout();
            infos = LoadInfos();
            var plan = JsonUtility.FromJson<Plan>(File.ReadAllText(Root + "/Bauplaene.json"));
            Directory.CreateDirectory(PrefabDir);
            int ok = 0, bad = 0;
            var names = new HashSet<string>();
            foreach (var h in plan.haeuser)
            {
                var errs = Check(h, infos);
                if (!names.Add(h.name)) errs.Add($"{h.name}: Name doppelt");
                if (errs.Count > 0)
                {
                    bad++;
                    Debug.LogError($"[Haus-Baukasten] {h.name} NICHT gebaut:\n- " + string.Join("\n- ", errs));
                    continue;
                }
                SavePrefab(BuildExterior(h), $"{PrefabDir}/Haus_{h.name}_Aussen.prefab");
                SavePrefab(BuildInterior(h), $"{PrefabDir}/Haus_{h.name}_Innen.prefab");
                ok++;
            }
            AssetDatabase.SaveAssets();
            if (bad == 0) Debug.Log($"[Haus-Baukasten] {ok} Haeuser gebaut (Aussen + Innen) in {PrefabDir}, 0 Fehler.");
            else Debug.LogWarning($"[Haus-Baukasten] {ok} gebaut, {bad} fehlerhaft (siehe Fehler oben).");
        }

        [MenuItem("Nightward/Haus-Baukasten/Bauplaene nur pruefen")]
        public static void CheckOnly()
        {
            infos = LoadInfos();
            var plan = JsonUtility.FromJson<Plan>(File.ReadAllText(Root + "/Bauplaene.json"));
            int n = 0;
            foreach (var h in plan.haeuser)
            {
                var errs = Check(h, infos);
                n += errs.Count;
                if (errs.Count > 0) Debug.LogError($"[Haus-Baukasten] {h.name}:\n- " + string.Join("\n- ", errs));
            }
            if (n == 0) Debug.Log($"[Haus-Baukasten] {plan.haeuser.Length} Bauplaene ok, 0 Fehler.");
        }

        /// <summary>
        /// Prueft ein selbst gebautes Haus in der Szene (Auswahl = Wurzel mit Grid und den Ebenen Wand, Wand_Deko, Dach,
        /// Dach_Deko bzw. Boden, Moebel, Krone): Deko ohne Wand darunter, Dachteile neben dem Dach, ueberlappende Moebel,
        /// Moebel ausserhalb des Bodens, Tuer-/Eingangspruefung.
        /// </summary>
        [MenuItem("Nightward/Haus-Baukasten/Ausgewaehltes Haus pruefen")]
        public static void CheckSelection()
        {
            var sel = Selection.activeGameObject;
            if (sel == null) { Debug.LogWarning("[Haus-Baukasten] Bitte die Wurzel eines Hauses auswaehlen."); return; }
            infos = LoadInfos();
            var maps = sel.GetComponentsInChildren<Tilemap>(true).GroupBy(t => t.name).ToDictionary(g => g.Key, g => g.First());
            var err = new List<string>();
            Info InfoOf(TileBase t) => t != null && infos.TryGetValue(t.name, out var i) ? i : null;
            IEnumerable<(Vector3Int pos, TileBase tile)> All(string name)
            {
                if (!maps.TryGetValue(name, out var tm)) yield break;
                tm.CompressBounds();
                foreach (var p in tm.cellBounds.allPositionsWithin) { var t = tm.GetTile(p); if (t != null) yield return (p, t); }
            }
            bool Has(string map, int x, int y) => maps.TryGetValue(map, out var tm) && tm.GetTile(new Vector3Int(x, y, 0)) != null;

            if (maps.ContainsKey("Dach") || maps.ContainsKey("Wand") && !maps.ContainsKey("Boden"))
            {
                int doors = 0;
                var occ = new Dictionary<Vector3Int, string>();
                foreach (var (p, t) in All("Wand_Deko"))
                {
                    var i = InfoOf(t);
                    if (i == null) { err.Add($"Wand_Deko {p}: '{t.name}' ist kein Baukasten-Objekt"); continue; }
                    if (i.name.StartsWith("Tuer") || i.name.StartsWith("Tor") || i.name.StartsWith("Portal"))
                    {
                        doors++;
                        if (Has("Wand", p.x, p.y - 1)) err.Add($"{i.name} bei {p}: steht nicht unten an der Wand");
                    }
                    for (int x = 0; x < i.w; x++)
                        for (int y = 0; y < i.h; y++)
                        {
                            var c = new Vector3Int(p.x + x, p.y + y, 0);
                            if (!Has("Wand", c.x, c.y)) err.Add($"{i.name} bei {p}: Feld {c} hat keine Wand dahinter");
                            if (occ.TryGetValue(c, out var o)) err.Add($"{i.name} bei {p}: ueberlappt {o}");
                            occ[c] = i.name;
                        }
                }
                foreach (var (p, t) in All("Dach_Deko"))
                    if (!Has("Dach", p.x, p.y)) err.Add($"{t.name} bei {p}: Ankerzelle liegt nicht auf dem Dach");
                if (doors == 0) err.Add("keine Tuer in Wand_Deko");
            }
            else if (maps.ContainsKey("Boden"))
            {
                var occ = new Dictionary<Vector3Int, string>();
                foreach (var (p, t) in All("Moebel"))
                {
                    var i = InfoOf(t);
                    if (i == null) { err.Add($"Moebel {p}: '{t.name}' ist kein Baukasten-Objekt"); continue; }
                    for (int x = 0; x < i.w; x++)
                        for (int y = 0; y < Mathf.Max(1, i.fuss); y++)
                        {
                            var c = new Vector3Int(p.x + x, p.y + y, 0);
                            if (!Has("Boden", c.x, c.y)) err.Add($"{i.name} bei {p}: Feld {c} hat keinen Boden");
                            if (occ.TryGetValue(c, out var o)) err.Add($"{i.name} bei {p}: ueberlappt {o}");
                            occ[c] = i.name;
                        }
                }
                foreach (var (p, t) in All("Wand_Deko"))
                {
                    var i = InfoOf(t);
                    if (i == null) continue;
                    for (int x = 0; x < i.w; x++)
                        for (int y = 0; y < i.h; y++)
                            if (!Has("Wand", p.x + x, p.y + y)) err.Add($"{i.name} bei {p}: Feld ({p.x + x},{p.y + y}) hat keine Wand dahinter");
                }
            }
            else err.Add("keine Baukasten-Ebenen gefunden (Wand/Dach bzw. Boden/Moebel)");

            if (err.Count == 0) Debug.Log($"[Haus-Baukasten] {sel.name}: ok, 0 Fehler.");
            else Debug.LogError($"[Haus-Baukasten] {sel.name}: {err.Count} Fehler\n- " + string.Join("\n- ", err.Distinct()));
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
            ti.wrapMode = TextureWrapMode.Clamp;
            return ti;
        }

        static void ConfigureImports()
        {
            foreach (var (png, prefix) in new[] { (SheetA, "BKA"), (SheetI, "BKI") })
            {
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

            foreach (var inf in infos.Values)
            {
                // Objekte: Ankerzelle links unten (wie Art/Tiles/Objekte, Tilemap mit tileAnchor 0)
                string p = $"{ObjDir}/{inf.name}.png";
                var ti = Importer(p, SpriteImportMode.Single);
                var s = new TextureImporterSettings();
                ti.ReadTextureSettings(s);
                // Klapptuer dreht um ihr Scharnier (oben Mitte), alles andere: Anker links unten
                s.spriteAlignment = (int)(inf.kat == "innen_tuer" ? SpriteAlignment.TopCenter : SpriteAlignment.BottomLeft);
                s.spriteMeshType = SpriteMeshType.FullRect;
                ti.SetTextureSettings(s);
                ti.SaveAndReimport();
                if (inf.frames <= 1) continue;
                string a = $"{AnimDir}/{inf.name}_Anim.png";
                var ta = Importer(a, SpriteImportMode.Multiple);
                var metas = new List<SpriteMetaData>();
                for (int i = 0; i < inf.frames; i++)
                    metas.Add(new SpriteMetaData
                    {
                        name = $"{inf.name}_Anim_{i}",
                        rect = new Rect(i * inf.w * Cell, 0, inf.w * Cell, inf.h * Cell),
                        alignment = (int)SpriteAlignment.BottomLeft,
                        pivot = Vector2.zero
                    });
#pragma warning disable CS0618
                ta.spritesheet = metas.ToArray();
#pragma warning restore CS0618
                ta.SaveAndReimport();
            }
        }

        // ------------------------------------------------------------------ Tiles
        static Dictionary<string, Sprite> SpritesOf(string png)
        {
            var d = new Dictionary<string, Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(png)) if (o is Sprite sp) d[sp.name] = sp;
            return d;
        }

        static T Upsert<T>(string path) where T : TileBase
        {
            var existing = AssetDatabase.LoadAssetAtPath<TileBase>(path);
            if (existing is T t) return t;
            if (existing != null) AssetDatabase.DeleteAsset(path);   // Typ geaendert (statisch <-> animiert)
            t = ScriptableObject.CreateInstance<T>();
            AssetDatabase.CreateAsset(t, path);
            return t;
        }

        static void CreateTiles()
        {
            foreach (var d in new[] { "Objekte", "Zellen", "RuleTiles" }) Directory.CreateDirectory($"{TA}/{d}");
            AssetDatabase.Refresh();

            foreach (var (png, _) in new[] { (SheetA, "BKA"), (SheetI, "BKI") })
                foreach (var kv in SpritesOf(png))
                {
                    if (IsEmpty(kv.Value)) continue;
                    var t = Upsert<Tile>($"{TA}/Zellen/{kv.Key}.asset");
                    t.sprite = kv.Value;
                    t.colliderType = Tile.ColliderType.None;
                    EditorUtility.SetDirty(t);
                }

            foreach (var inf in infos.Values)
            {
                string path = $"{TA}/Objekte/{inf.name}.asset";
                if (inf.frames > 1)
                {
                    var by = SpritesOf($"{AnimDir}/{inf.name}_Anim.png");
                    var frames = new Sprite[inf.frames];
                    for (int i = 0; i < inf.frames; i++) frames[i] = by[$"{inf.name}_Anim_{i}"];
                    var a = Upsert<AnimatedTile>(path);
                    a.m_AnimatedSprites = frames;
                    float fps = 1000f / Mathf.Max(1, inf.ms);
                    a.m_MinSpeed = fps * 0.95f;     // leichte Streuung, damit gleiche Teile nicht im Gleichtakt laufen
                    a.m_MaxSpeed = fps * 1.05f;
                    a.m_TileColliderType = Tile.ColliderType.None;
                    EditorUtility.SetDirty(a);
                }
                else
                {
                    var t = Upsert<Tile>(path);
                    t.sprite = AssetDatabase.LoadAssetAtPath<Sprite>($"{ObjDir}/{inf.name}.png");
                    t.colliderType = Tile.ColliderType.None;
                    EditorUtility.SetDirty(t);
                }
            }
        }

        static readonly Dictionary<string, Texture2D> texCache = new Dictionary<string, Texture2D>();

        static bool IsEmpty(Sprite sp)
        {
            // Leere Zellen (nicht belegte Sheet-Felder) ueberspringen. Pixel direkt aus der Datei (kein Read/Write noetig)
            var path = AssetDatabase.GetAssetPath(sp);
            if (!texCache.TryGetValue(path, out var tex) || tex == null)
            {
                tex = new Texture2D(2, 2);
                tex.LoadImage(File.ReadAllBytes(path));
                texCache[path] = tex;
            }
            var r = sp.rect;
            foreach (var p in tex.GetPixels((int)r.x, (int)r.y, (int)r.width, (int)r.height)) if (p.a > 0.01f) return false;
            return true;
        }

        static TileBase Cell_(string prefix, int r, int c) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/Zellen/{prefix}_{r}_{c}.asset");

        public static TileBase ObjTile(string name) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/Objekte/{name}.asset");

        // ------------------------------------------------------------------ RuleTiles
        // Nachbarreihenfolge im RuleTile: NW, N, NE, W, E, SW, S, SE
        static RuleTile.TilingRule Rule(bool? n, bool? e, bool? s, bool? w, bool? nw, bool? ne, bool? sw, bool? se, params Sprite[] sprites)
        {
            int V(bool? b) => b == null ? 0 : (b.Value ? RuleTile.TilingRuleOutput.Neighbor.This : RuleTile.TilingRuleOutput.Neighbor.NotThis);
            return new RuleTile.TilingRule
            {
                m_Sprites = sprites,
                m_Output = sprites.Length > 1 ? RuleTile.TilingRuleOutput.OutputSprite.Random : RuleTile.TilingRuleOutput.OutputSprite.Single,
                m_PerlinScale = 0.95f,
                m_Neighbors = new List<int> { V(nw), V(n), V(ne), V(w), V(e), V(sw), V(s), V(se) }
            };
        }

        static RuleTile SaveRuleTile(string path, RuleTile fresh)
        {
            var rt = AssetDatabase.LoadAssetAtPath<RuleTile>(path);
            if (rt == null)
            {
                AssetDatabase.CreateAsset(fresh, path);
                return fresh;
            }
            rt.m_DefaultSprite = fresh.m_DefaultSprite;
            rt.m_DefaultColliderType = fresh.m_DefaultColliderType;
            rt.m_TilingRules = fresh.m_TilingRules;
            EditorUtility.SetDirty(rt);
            return rt;
        }

        /// <summary>Wand/Dach/Innenwand: 16 Kanten (Maske N1 E2 S4 W8), Mitte zufaellig aus den Fuell-Varianten.</summary>
        static void MakeMaskRuleTile(string path, Func<int, Sprite> col, int[] fills, bool edgeVariants)
        {
            var rt = ScriptableObject.CreateInstance<RuleTile>();
            rt.m_DefaultSprite = col(15);
            rt.m_DefaultColliderType = Tile.ColliderType.None;
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, null, null, null, fills.Select(col).ToArray()));
            for (int m = 0; m < 15; m++)
            {
                var sprites = edgeVariants && EdgeVariants.TryGetValue(m, out var v) ? v.Select(col).ToArray() : new[] { col(m) };
                rt.m_TilingRules.Add(Rule((m & 1) != 0, (m & 2) != 0, (m & 4) != 0, (m & 8) != 0, null, null, null, null, sprites));
            }
            SaveRuleTile(path, rt);
        }

        /// <summary>Mauerkrone: 16 Kanten + Innenecken (Spalte 16-19: fehlt NO, SO, SW, NW).</summary>
        static void MakeCrownRuleTile(string path, Func<int, Sprite> col)
        {
            var rt = ScriptableObject.CreateInstance<RuleTile>();
            rt.m_DefaultSprite = col(15);
            rt.m_DefaultColliderType = Tile.ColliderType.None;
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, false, null, null, col(16)));
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, null, null, false, col(17)));
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, null, false, null, col(18)));
            rt.m_TilingRules.Add(Rule(true, true, true, true, false, null, null, null, col(19)));
            rt.m_TilingRules.Add(Rule(true, true, true, true, null, null, null, null, col(15)));
            for (int m = 0; m < 15; m++)
                rt.m_TilingRules.Add(Rule((m & 1) != 0, (m & 2) != 0, (m & 4) != 0, (m & 8) != 0, null, null, null, null, col(m)));
            SaveRuleTile(path, rt);
        }

        static void CreateRuleTiles()
        {
            var a = SpritesOf(SheetA);
            var i = SpritesOf(SheetI);
            string T = $"{TA}/RuleTiles";
            for (int k = 0; k < layout.wand.Length; k++)
            {
                int r = k;
                MakeMaskRuleTile($"{T}/RT_BK_Wand_{Cap(layout.wand[k])}.asset", c => a[$"BKA_{r}_{c}"], new[] { 15, 16, 17 }, true);
            }
            for (int k = 0; k < layout.dach.Length; k++)
            {
                int r = layout.dachStartZeile + k;
                MakeMaskRuleTile($"{T}/RT_BK_Dach_{Cap(layout.dach[k])}.asset", c => a[$"BKA_{r}_{c}"], new[] { 15, 16, 17 }, true);
            }
            for (int k = 0; k < layout.innenWand.Length; k++)
            {
                int r = layout.innenWandZeile + k;
                MakeMaskRuleTile($"{T}/RT_BK_Innenwand_{Cap(layout.innenWand[k])}.asset", c => i[$"BKI_{r}_{c}"], new[] { 15, 16, 17 }, false);
            }
            for (int k = 0; k < layout.krone.Length; k++)
            {
                int r = layout.kroneZeile + k;
                MakeCrownRuleTile($"{T}/RT_BK_Krone_{Cap(layout.krone[k])}.asset", c => i[$"BKI_{r}_{c}"]);
            }
            for (int k = 0; k < layout.boden.Length; k++)
            {
                var (r, c0) = FloorCell(k);
                var rt = ScriptableObject.CreateInstance<RuleTile>();
                rt.m_DefaultSprite = i[$"BKI_{r}_{c0}"];
                rt.m_TilingRules.Add(Rule(null, null, null, null, null, null, null, null,
                    i[$"BKI_{r}_{c0}"], i[$"BKI_{r}_{c0 + 1}"], i[$"BKI_{r}_{c0 + 2}"]));
                SaveRuleTile($"{T}/RT_BK_Boden_{Cap(layout.boden[k])}.asset", rt);
            }
        }

        static (int row, int col) FloorCell(int k) => (layout.bodenZeile + k / layout.bodenJeZeile, (k % layout.bodenJeZeile) * 3);

        static string Cap(string s) => string.Join("_", s.Split('_').Select(p => char.ToUpper(p[0]) + p.Substring(1)));

        public static TileBase RT(string kind, string mat) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/RuleTiles/RT_BK_{kind}_{Cap(mat)}.asset");

        static TileBase Overlay(string name)
        {
            int c = Array.IndexOf(layout.overlay, name);
            return Cell_("BKI", layout.overlayZeile, c);
        }

        // ------------------------------------------------------------------ Paletten
        static void MakePalette(string name, bool objectAnchor, Action<Tilemap> fill)
        {
            AssetDatabase.DeleteAsset($"{PaletteDir}/{name}.prefab");
            var go = GridPaletteUtility.CreateNewPalette(PaletteDir, name, GridLayout.CellLayout.Rectangle,
                GridPalette.CellSizing.Automatic, Vector3.one, GridLayout.CellSwizzle.XYZ);
            var path = AssetDatabase.GetAssetPath(go);
            var contents = PrefabUtility.LoadPrefabContents(path);
            var tm = contents.GetComponentInChildren<Tilemap>();
            if (objectAnchor) tm.tileAnchor = Vector3.zero;
            fill(tm);
            tm.CompressBounds();
            PrefabUtility.SaveAsPrefabAsset(contents, path);
            PrefabUtility.UnloadPrefabContents(contents);
        }

        static void Shelf(Tilemap tm, IEnumerable<Info> items, ref int y, int maxW = 24)
        {
            var list = items.OrderBy(i => i.name, StringComparer.Ordinal).ToList();
            if (list.Count == 0) return;
            int x = 0, rowH = 1;
            foreach (var it in list)
            {
                if (x + it.w > maxW) { y -= rowH + 1; x = 0; rowH = 1; }
                rowH = Mathf.Max(rowH, it.h);
                tm.SetTile(new Vector3Int(x, y - it.h + 1, 0), ObjTile(it.name));
                x += it.w + 1;
            }
            y -= rowH + 2;
        }

        static void CreatePalettes()
        {
            MakePalette("Pal_BK_Aussen_Bau", false, tm =>
            {
                // Zeile 0: Wand-RuleTiles, Zeile -2: Dach-RuleTiles, darunter alle Einzelzellen 1:1 (z. B. verwitterte Varianten)
                for (int k = 0; k < layout.wand.Length; k++) tm.SetTile(new Vector3Int(k * 2, 0, 0), RT("Wand", layout.wand[k]));
                for (int k = 0; k < layout.dach.Length; k++) tm.SetTile(new Vector3Int(k * 2, -2, 0), RT("Dach", layout.dach[k]));
                int rows = layout.dachStartZeile + layout.dach.Length;
                for (int r = 0; r < rows; r++)
                    for (int c = 0; c < layout.cols; c++)
                    {
                        var t = Cell_("BKA", r, c);
                        if (t != null) tm.SetTile(new Vector3Int(c, -5 - r, 0), t);
                    }
            });
            MakePalette("Pal_BK_Innen_Bau", false, tm =>
            {
                for (int k = 0; k < layout.boden.Length; k++) tm.SetTile(new Vector3Int(k % 6 * 2, -(k / 6) * 2, 0), RT("Boden", layout.boden[k]));
                for (int k = 0; k < layout.innenWand.Length; k++) tm.SetTile(new Vector3Int(k * 2, -4, 0), RT("Innenwand", layout.innenWand[k]));
                for (int k = 0; k < layout.krone.Length; k++) tm.SetTile(new Vector3Int(k * 2, -6, 0), RT("Krone", layout.krone[k]));
                for (int k = 0; k < layout.overlay.Length; k++) tm.SetTile(new Vector3Int(k, -8, 0), Overlay(layout.overlay[k]));
                for (int r = 0; r < layout.overlayZeile; r++)
                    for (int c = 0; c < layout.cols; c++)
                    {
                        var t = Cell_("BKI", r, c);
                        if (t != null) tm.SetTile(new Vector3Int(c, -11 - r, 0), t);
                    }
            });
            MakePalette("Pal_BK_Aussen_Objekte", true, tm =>
            {
                int y = 0;
                var v = infos.Values;
                Shelf(tm, v.Where(i => i.kat == "aussen_wand" && i.name.StartsWith("Fenster")), ref y);
                Shelf(tm, v.Where(i => i.kat == "aussen_wand" && (i.name.StartsWith("Schaufenster") || i.name.StartsWith("Tuer") || i.name.StartsWith("Tor") || i.name.StartsWith("Portal"))), ref y);
                Shelf(tm, v.Where(i => i.kat == "aussen_wand" && (i.name.StartsWith("Haengeschild") || i.name.StartsWith("Wandlaterne") || i.name.StartsWith("Talisman") || i.name.StartsWith("Schild"))), ref y);
                Shelf(tm, v.Where(i => i.kat == "aussen_wand" && (i.name.StartsWith("Vordach") || i.name.StartsWith("Blumenkasten") || i.name.StartsWith("Fallrohr") || i.name.StartsWith("Efeu") || i.name.StartsWith("Leiter"))), ref y);
                Shelf(tm, v.Where(i => i.kat == "aussen_dach"), ref y);
                Shelf(tm, v.Where(i => i.kat == "aussen_boden"), ref y);
            });
            MakePalette("Pal_BK_Innen_Objekte", true, tm =>
            {
                int y = 0;
                var v = infos.Values;
                Shelf(tm, v.Where(i => i.kat == "innen_moebel" && i.h >= 2), ref y);
                Shelf(tm, v.Where(i => i.kat == "innen_moebel" && i.h < 2 && i.w >= 2), ref y);
                Shelf(tm, v.Where(i => i.kat == "innen_moebel" && i.h < 2 && i.w < 2), ref y);
                Shelf(tm, v.Where(i => i.kat == "innen_wand"), ref y);
                Shelf(tm, v.Where(i => i.kat == "innen_boden"), ref y);
                Shelf(tm, v.Where(i => i.kat == "innen_rahmen"), ref y);
            });
        }

        // ------------------------------------------------------------------ Pruefung (gleiche Regeln wie bk_build.check_house)
        public static List<string> Check(Haus hs, Dictionary<string, Info> inf)
        {
            var err = new List<string>();
            layout = layout ?? LoadLayout();
            var a = hs.aussen;
            string n = hs.name;
            if (a == null || hs.innen == null) { err.Add($"{n}: aussen/innen fehlt"); return err; }
            int W = a.breite, WH = a.wandHoehe, DH = a.dachHoehe, UE = a.ueberstand;
            if (W < 1 || WH < 1 || DH < 1) err.Add($"{n}: Breite/Wandhoehe/Dachhoehe muessen >= 1 sein");
            if (!layout.wand.Contains(a.wand)) err.Add($"{n}: Wandmaterial unbekannt '{a.wand}' (moeglich: {string.Join(", ", layout.wand)})");
            if (!layout.dach.Contains(a.dach)) err.Add($"{n}: Dachmaterial unbekannt '{a.dach}' (moeglich: {string.Join(", ", layout.dach)})");
            var occ = new Dictionary<(string, int, int), string>();
            int doors = 0;
            foreach (var d in a.deko ?? new Obj[0])
            {
                if (!inf.TryGetValue(d.o, out var i)) { err.Add($"{n} aussen: Objekt fehlt '{d.o}'"); continue; }
                if (!i.kat.StartsWith("aussen")) { err.Add($"{n} aussen: {d.o} ist kein Aussen-Teil ({i.kat})"); continue; }
                var cells = new List<(int, int)>();
                for (int x = 0; x < i.w; x++) for (int y = 0; y < i.h; y++) cells.Add((d.x + x, d.y + y));
                if (i.kat == "aussen_wand")
                {
                    if (cells.Any(c => c.Item1 < 0 || c.Item1 >= W || c.Item2 < 0 || c.Item2 >= WH)) err.Add($"{n}: {d.o} bei ({d.x},{d.y}) ragt aus der Wand");
                    if (d.o.StartsWith("Tuer") || d.o.StartsWith("Tor") || d.o.StartsWith("Portal"))
                    {
                        doors++;
                        if (d.y != 0) err.Add($"{n}: {d.o} steht nicht auf dem Boden (y muss 0 sein)");
                    }
                }
                else if (i.kat == "aussen_dach")
                {
                    if (d.x < -UE || d.x >= W + UE || d.y < WH || d.y >= WH + DH) err.Add($"{n}: {d.o} Ankerzelle ({d.x},{d.y}) nicht auf dem Dach");
                    cells = new List<(int, int)> { (d.x, d.y) };
                }
                else if (i.kat == "aussen_boden")
                {
                    if (d.y != -1) err.Add($"{n}: {d.o} muss vor dem Haus stehen (y = -1)");
                    if (cells.Any(c => c.Item1 < -1 || c.Item1 > W)) err.Add($"{n}: {d.o} steht zu weit neben dem Haus");
                }
                foreach (var c in cells)
                {
                    var key = (i.kat, c.Item1, c.Item2);
                    if (occ.TryGetValue(key, out var other)) err.Add($"{n}: {d.o} ueberlappt {other} bei {c}");
                    occ[key] = d.o;
                }
            }
            if (doors == 0) err.Add($"{n}: keine Tuer (Tuer_*, Tor_*, Portal_*)");

            var inn = hs.innen;
            int Wi = inn.breite, Hi = inn.hoehe, tx = inn.tuerX;
            if (Wi < 2 || Hi < 2) err.Add($"{n} innen: Raum mindestens 2x2");
            if (!layout.boden.Contains(inn.boden)) err.Add($"{n} innen: Boden unbekannt '{inn.boden}'");
            if (!layout.innenWand.Contains(inn.wand)) err.Add($"{n} innen: Wand unbekannt '{inn.wand}'");
            if (!layout.krone.Contains(inn.krone)) err.Add($"{n} innen: Krone unbekannt '{inn.krone}'");
            if (tx < 0 || tx >= Wi) err.Add($"{n} innen: tuerX ausserhalb des Raums");
            occ.Clear();
            var blocked = new HashSet<(int, int)>();
            foreach (var d in inn.objekte ?? new Obj[0])
            {
                if (!inf.TryGetValue(d.o, out var i)) { err.Add($"{n} innen: Objekt fehlt '{d.o}'"); continue; }
                var cells = new List<(int, int)>();
                string layer;
                if (i.kat == "innen_wand")
                {
                    for (int x = 0; x < i.w; x++) for (int y = 0; y < i.h; y++) cells.Add((d.x + x, d.y + y));
                    if (cells.Any(c => c.Item1 < 0 || c.Item1 >= Wi || c.Item2 < Hi || c.Item2 >= Hi + 2)) err.Add($"{n} innen: {d.o} bei ({d.x},{d.y}) haengt nicht an der Wand (Wandzeilen y = {Hi} und {Hi + 1})");
                    layer = "wand";
                }
                else if (i.kat == "innen_boden")
                {
                    for (int x = 0; x < i.w; x++) for (int y = 0; y < i.h; y++) cells.Add((d.x + x, d.y + y));
                    if (cells.Any(c => c.Item1 < 0 || c.Item1 >= Wi || c.Item2 < 0 || c.Item2 >= Hi)) err.Add($"{n} innen: {d.o} liegt nicht auf dem Boden");
                    layer = "teppich";
                }
                else if (i.kat == "innen_moebel")
                {
                    for (int x = 0; x < i.w; x++) for (int y = 0; y < i.fuss; y++) cells.Add((d.x + x, d.y + y));
                    if (cells.Any(c => c.Item1 < 0 || c.Item1 >= Wi || c.Item2 < 0 || c.Item2 >= Hi)) err.Add($"{n} innen: {d.o} bei ({d.x},{d.y}) steht ausserhalb des Raums");
                    layer = "moebel";
                    foreach (var c in cells) blocked.Add(c);
                }
                else { err.Add($"{n} innen: {d.o} ist kein Innen-Teil ({i.kat})"); continue; }
                foreach (var c in cells)
                {
                    var key = (layer, c.Item1, c.Item2);
                    if (occ.TryGetValue(key, out var other)) err.Add($"{n} innen: {d.o} ueberlappt {other} bei {c}");
                    occ[key] = d.o;
                }
            }
            if (blocked.Contains((tx, 0))) err.Add($"{n} innen: Eingang ({tx},0) ist zugestellt");
            else
            {
                var seen = new HashSet<(int, int)> { (tx, 0) };
                var todo = new Stack<(int, int)>();
                todo.Push((tx, 0));
                while (todo.Count > 0)
                {
                    var (x, y) = todo.Pop();
                    foreach (var c in new[] { (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1) })
                        if (!seen.Contains(c) && !blocked.Contains(c) && c.Item1 >= 0 && c.Item1 < Wi && c.Item2 >= 0 && c.Item2 < Hi)
                        { seen.Add(c); todo.Push(c); }
                }
                int free = Wi * Hi - blocked.Count;
                if (seen.Count < free) err.Add($"{n} innen: {free - seen.Count} freie Bodenfelder sind vom Eingang aus nicht erreichbar");
            }
            return err;
        }

        // ------------------------------------------------------------------ Prefabs
        static Material LitMaterial() => AssetDatabase.LoadAssetAtPath<Material>(
            "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat");

        static Tilemap Layer(Transform grid, string name, int order, bool individual, bool objectAnchor)
        {
            var go = new GameObject(name);
            go.transform.SetParent(grid, false);
            var tm = go.AddComponent<Tilemap>();
            tm.animationFrameRate = 1f; // Tempo steckt in den AnimatedTiles
            if (objectAnchor) tm.tileAnchor = Vector3.zero;
            var tr = go.AddComponent<TilemapRenderer>();
            tr.sortingOrder = order;
            var lit = LitMaterial();
            if (lit != null) tr.sharedMaterial = lit;
            if (individual) tr.mode = TilemapRenderer.Mode.Individual;
            return tm;
        }

        static (GameObject root, Transform grid) NewRoot(string name)
        {
            var root = new GameObject(name);
            var grid = new GameObject("Grid");
            grid.transform.SetParent(root.transform, false);
            grid.AddComponent<Grid>();
            return (root, grid.transform);
        }

        static void Put(Tilemap tm, string obj, int x, int y) => tm.SetTile(new Vector3Int(x, y, 0), ObjTile(obj));

        static GameObject BuildExterior(Haus h)
        {
            var a = h.aussen;
            var (root, grid) = NewRoot($"Haus_{h.name}_Aussen");
            // Ein Haus sortiert als Ganzes gegen Spieler/Objekte (Pivot = Bodenlinie der Fassade)
            var sg = root.AddComponent<SortingGroup>();
            sg.sortingOrder = OrderObjects;
            var wall = Layer(grid, "Wand", 0, false, false);
            var wallDeko = Layer(grid, "Wand_Deko", 1, false, true);
            var roof = Layer(grid, "Dach", 2, false, false);
            var roofDeko = Layer(grid, "Dach_Deko", 3, false, true);
            var front = Layer(grid, "Vorne", 4, true, true);

            var rtW = RT("Wand", a.wand);
            var rtD = RT("Dach", a.dach);
            for (int x = 0; x < a.breite; x++)
                for (int y = 0; y < a.wandHoehe; y++) wall.SetTile(new Vector3Int(x, y, 0), rtW);
            for (int x = -a.ueberstand; x < a.breite + a.ueberstand; x++)
                for (int y = a.wandHoehe; y < a.wandHoehe + a.dachHoehe; y++) roof.SetTile(new Vector3Int(x, y, 0), rtD);
            var lights = new GameObject("Lichter").transform;
            lights.SetParent(root.transform, false);
            foreach (var d in a.deko)
            {
                var i = infos[d.o];
                var tm = i.kat == "aussen_wand" ? wallDeko : i.kat == "aussen_dach" ? roofDeko : front;
                Put(tm, d.o, d.x, d.y);
                AddLight(lights, d.o, i, d.x, d.y, true);
            }

            var col = root.AddComponent<BoxCollider2D>();
            col.size = new Vector2(a.breite, a.wandHoehe);
            col.offset = new Vector2(a.breite / 2f, a.wandHoehe / 2f);

            // Eingang: Trigger vor jeder Tuer (fuer Szenenwechsel ins Innen-Prefab)
            foreach (var d in a.deko.Where(d => d.o.StartsWith("Tuer") || d.o.StartsWith("Tor") || d.o.StartsWith("Portal")))
            {
                var i = infos[d.o];
                var e = new GameObject("Eingang_" + d.o);
                e.transform.SetParent(root.transform, false);
                e.transform.localPosition = new Vector3(d.x + i.w / 2f, -0.5f, 0);
                var bc = e.AddComponent<BoxCollider2D>();
                bc.isTrigger = true;
                bc.size = new Vector2(i.w * 0.8f, 0.8f);
            }
            return root;
        }

        static GameObject BuildInterior(Haus h)
        {
            var n = h.innen;
            int W = n.breite, H = n.hoehe, tx = n.tuerX;
            var (root, grid) = NewRoot($"Haus_{h.name}_Innen");
            var floor = Layer(grid, "Boden", 0, false, false);
            var floorDeko = Layer(grid, "Boden_Deko", 1, false, true);
            var shade = Layer(grid, "Boden_Schatten", 1, false, false);
            var wall = Layer(grid, "Wand", 2, false, false);
            var wallDeko = Layer(grid, "Wand_Deko", 3, false, true);
            var furn = Layer(grid, "Moebel", OrderObjects, true, true);
            // Kronen y-sortiert mit der Spielfigur (obere hinter ihr, untere davor), Tuerrahmen knapp davor
            var crown = Layer(grid, "Krone", OrderObjects, true, false);
            var frame = Layer(grid, "Tuerrahmen", OrderObjects, true, true);
            frame.transform.localPosition = new Vector3(0f, -0.02f, 0f);

            var rtF = RT("Boden", n.boden);
            for (int x = 0; x < W; x++) for (int y = 0; y < H; y++) floor.SetTile(new Vector3Int(x, y, 0), rtF);
            floor.SetTile(new Vector3Int(tx, -1, 0), rtF);
            for (int x = 0; x < W; x++)
                shade.SetTile(new Vector3Int(x, H - 1, 0), Overlay(x == 0 ? "schatten_ecke_links" : x == W - 1 ? "schatten_ecke_rechts" : "schatten_oben"));
            for (int y = 0; y < H - 1; y++)
            {
                shade.SetTile(new Vector3Int(0, y, 0), Overlay("schatten_links"));
                shade.SetTile(new Vector3Int(W - 1, y, 0), Overlay("schatten_rechts"));
            }
            shade.SetTile(new Vector3Int(tx, -1, 0), Overlay("schwelle"));

            var rtW = RT("Innenwand", n.wand);
            for (int x = 0; x < W; x++) for (int y = H; y < H + 2; y++) wall.SetTile(new Vector3Int(x, y, 0), rtW);
            var rtK = RT("Krone", n.krone);
            var crownCells = new List<Vector3Int>();
            for (int x = -1; x <= W; x++) { crownCells.Add(new Vector3Int(x, H + 2, 0)); if (x != tx) crownCells.Add(new Vector3Int(x, -1, 0)); }
            for (int y = 0; y <= H + 1; y++) { crownCells.Add(new Vector3Int(-1, y, 0)); crownCells.Add(new Vector3Int(W, y, 0)); }
            foreach (var c in crownCells) crown.SetTile(c, rtK);
            Put(frame, "Tuerrahmen_UntenLinks", tx - 1, -1);
            Put(frame, "Tuerrahmen_UntenRechts", tx + 1, -1);

            var lights = new GameObject("Lichter").transform;
            lights.SetParent(root.transform, false);
            var solid = new HashSet<Vector3Int>();
            foreach (var d in n.objekte)
            {
                var i = infos[d.o];
                var tm = i.kat == "innen_wand" ? wallDeko : i.kat == "innen_boden" ? floorDeko : furn;
                Put(tm, d.o, d.x, d.y);
                AddLight(lights, d.o, i, d.x, d.y, false);
                if (i.kat == "innen_moebel" && i.solid)
                    for (int x = 0; x < i.w; x++) for (int y = 0; y < i.fuss; y++) solid.Add(new Vector3Int(d.x + x, d.y + y, 0));
            }

            // Kollision: Kronen, Wandflaeche, feste Moebel (Fussfelder)
            var colGo = new GameObject("Kollision");
            colGo.transform.SetParent(grid, false);
            var colMap = colGo.AddComponent<Tilemap>();
            var tc = colGo.AddComponent<TilemapCollider2D>();
            var rb = colGo.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Static;
            var cc = colGo.AddComponent<CompositeCollider2D>();
            cc.geometryType = CompositeCollider2D.GeometryType.Polygons;
            tc.compositeOperation = Collider2D.CompositeOperation.Merge;
            var block = AssetDatabase.LoadAssetAtPath<TileBase>(CollisionTile);
            if (block == null) Debug.LogWarning("[Haus-Baukasten] Collision_Block.asset fehlt (Level1Builder einmal laufen lassen).");
            else
            {
                foreach (var c in crownCells) colMap.SetTile(c, block);
                for (int x = 0; x < W; x++) colMap.SetTile(new Vector3Int(x, H, 0), block);
                foreach (var c in solid) colMap.SetTile(c, block);
            }

            // Sichtsystem (Scripts/Vision): Innenraum ohne Oeffnungen - das Innen-Prefab steht allein, draussen ist nichts
            var area = root.AddComponent<BoxCollider2D>();
            area.isTrigger = true;
            area.offset = new Vector2(W / 2f, (H + 2) / 2f);
            area.size = new Vector2(W + 2, H + 4);
            root.AddComponent<Interior>();

            var exit = new GameObject("Ausgang");
            exit.transform.SetParent(root.transform, false);
            exit.transform.localPosition = new Vector3(tx + 0.5f, -0.5f, 0);
            var ebc = exit.AddComponent<BoxCollider2D>();
            ebc.isTrigger = true;
            ebc.size = new Vector2(0.8f, 0.8f);
            return root;
        }

        // Lichtquellen (Style-Bibel: Fenster warm-gelb, Feuer/Laterne warm-orange, Talisman kuehl-blau)
        static readonly Color Warm = new Color(1f, 0.82f, 0.48f), Fire = new Color(1f, 0.65f, 0.31f), Talisman = new Color(0.44f, 0.83f, 0.9f);

        static void AddLight(Transform parent, string name, Info i, int x, int y, bool outside)
        {
            Color col; float radius, intensity;
            if (name.Contains("Talisman")) { col = Talisman; radius = 1.6f; intensity = 0.8f; }
            else if (name.StartsWith("Kamin") || name.StartsWith("Herd") || name.StartsWith("Esse") || name.StartsWith("Backofen")) { col = Fire; radius = 4.5f; intensity = 1.1f; }
            else if (name.Contains("Laterne")) { col = Fire; radius = 3f; intensity = 1f; }
            else if (name.Contains("Kerze") || name.StartsWith("Altar") || name.StartsWith("Kerzenstaender") || name == "Wand_Kerzenleuchter") { col = Warm; radius = 2.4f; intensity = 0.8f; }
            else if (outside && (name.Contains("Licht") || name.Contains("Bunt") || name.StartsWith("Schaufenster") || name.StartsWith("Tuer_Oberlicht") || name.StartsWith("Tuer_Laden"))) { col = Warm; radius = 2.2f; intensity = 0.7f; }
            else return;
            var go = new GameObject("Licht_" + name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = new Vector3(x + i.w / 2f, y + i.h / 2f, 0);
            var l = go.AddComponent<Light2D>();
            l.lightType = Light2D.LightType.Point;
            l.color = col;
            l.intensity = intensity;
            l.pointLightOuterRadius = radius;
            l.pointLightInnerRadius = radius * 0.2f;
            if (outside) go.AddComponent<NightLight>();   // Aussenlichter gehen in der Daemmerung an
        }

        static void SavePrefab(GameObject go, string path)
        {
            PrefabUtility.SaveAsPrefabAsset(go, path);
            UnityEngine.Object.DestroyImmediate(go);
        }
    }
}
