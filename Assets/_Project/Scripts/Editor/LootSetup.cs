using System;
using System.Collections.Generic;
using System.IO;
using Nightward.Items;
using Nightward.Player;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Richtet das Beute-System ein: Beute-Tabellen (Data/Loot), Behaelter-Prefabs (Prefabs/Loot) und die Verteilung in
    /// Level_01 (Demo-Gruppe beim Spieler plus zufaellige Spawner im Dorf). Tabellen und Prefabs werden nur angelegt, wenn sie
    /// fehlen, damit Balancing im Inspector erhalten bleibt; die "neu bauen"-Eintraege ueberschreiben sie.
    /// Menue: Nightward > Loot
    /// </summary>
    public static class LootSetup
    {
        const string DbPath = "Assets/_Project/Data/Items/ItemDatabase.asset";
        const string TableDir = "Assets/_Project/Data/Loot";
        const string PrefabDir = "Assets/_Project/Prefabs/Loot";
        const string SpriteDir = "Assets/_Project/Art/Tiles/Objekte/";
        const string LitMaterial = "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat";
        const string RootName = "Beute";
        const int OrderObjects = 4;   // wie die Objekt-Ebene und die Spielerfigur in Level_01 (Hoehensortierung)

        // ------------------------------------------------------------------ Menue
        [MenuItem("Nightward/Loot/Alles einrichten (Tabellen, Prefabs, Level_01)")]
        public static void SetupAll()
        {
            var db = LoadDb();
            if (db == null) return;
            ApplyItemFlags(db);
            BuildTables(db, false);
            BuildPrefabs(db, false);
            PopulateLevel();
        }

        [MenuItem("Nightward/Loot/Tabellen und Prefabs neu bauen (ueberschreibt)")]
        public static void RebuildAssets()
        {
            if (!EditorUtility.DisplayDialog("Beute", "Beute-Tabellen und Behaelter-Prefabs mit den Standardwerten ueberschreiben? Eigene Aenderungen daran gehen verloren.", "Ueberschreiben", "Abbrechen")) return;
            var db = LoadDb();
            if (db == null) return;
            ApplyItemFlags(db);
            BuildTables(db, true);
            BuildPrefabs(db, true);
        }

        [MenuItem("Nightward/Loot/Level_01 bestuecken (neu verteilen)")]
        public static void PopulateLevelMenu() => PopulateLevel();

        [MenuItem("Nightward/Loot/Level_01 Beute entfernen")]
        public static void RemoveFromLevel()
        {
            var old = GameObject.Find(RootName);
            if (old != null) UnityEngine.Object.DestroyImmediate(old);
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        }

        static ItemDatabase LoadDb()
        {
            var db = AssetDatabase.LoadAssetAtPath<ItemDatabase>(DbPath);
            if (db == null) Debug.LogWarning("[Loot] ItemDatabase fehlt. Erst Nightward > Inventar > Alles einrichten.");
            return db;
        }

        /// <summary>Muenzen werden automatisch aufgenommen (ItemDef.autoPickup), alles andere mit F.</summary>
        static void ApplyItemFlags(ItemDatabase db)
        {
            foreach (var d in db.items)
            {
                if (d == null || d.category != ItemCategory.Currency || d.autoPickup) continue;
                d.autoPickup = true;
                if (string.IsNullOrEmpty(d.name)) d.name = Path.GetFileNameWithoutExtension(AssetDatabase.GetAssetPath(d));
                EditorUtility.SetDirty(d);
            }
            AssetDatabase.SaveAssets();
        }

        // ------------------------------------------------------------------ Tabellen
        static LootEntry E(ItemDatabase db, string id, float weight, int min = 1, int max = 1)
        {
            var d = db.Get(id);
            if (d == null) { Debug.LogWarning("[Loot] Gegenstand fehlt: " + id); return null; }
            return new LootEntry { item = d, weight = weight, min = min, max = max };
        }

        static LootPool Pool(string name, float chance, int rollsMin, int rollsMax, float nothing, bool unique, params LootEntry[] entries)
        {
            var p = new LootPool { name = name, chance = chance, rollsMin = rollsMin, rollsMax = rollsMax, nothingWeight = nothing, unique = unique };
            foreach (var e in entries) if (e != null) p.entries.Add(e);
            return p;
        }

        static LootTable MakeTable(string name, bool overwrite, Action<LootTable> fill)
        {
            Directory.CreateDirectory(TableDir);
            string path = $"{TableDir}/{name}.asset";
            var t = AssetDatabase.LoadAssetAtPath<LootTable>(path);
            if (t != null && !overwrite) return t;
            if (t == null)
            {
                t = ScriptableObject.CreateInstance<LootTable>();
                AssetDatabase.CreateAsset(t, path);
            }
            t.guaranteed = new List<LootEntry>();
            t.pools = new List<LootPool>();
            fill(t);
            EditorUtility.SetDirty(t);
            return t;
        }

        static void BuildTables(ItemDatabase db, bool overwrite)
        {
            // Haushalt: Truhe im Haus. Meist etwas zu essen, oft Kleinkram, manchmal Muenzen, selten etwas Gutes.
            MakeTable("Loot_Haushalt", overwrite, t =>
            {
                t.pools.Add(Pool("Essen", 0.9f, 1, 2, 0f, true, E(db, "bread", 4, 1, 3), E(db, "apple", 4, 2, 4), E(db, "cheese", 2), E(db, "dried_meat", 2), E(db, "honey", 0.7f)));
                t.pools.Add(Pool("Kleinkram", 0.65f, 1, 2, 0f, true, E(db, "bandage", 3), E(db, "candle", 3), E(db, "water", 3), E(db, "tinderbox", 1), E(db, "rope", 1), E(db, "nails", 1), E(db, "herbs", 2, 1, 3)));
                t.pools.Add(Pool("Leckerbissen", 0.35f, 1, 1, 0f, true, E(db, "cookies", 3), E(db, "apple_pie", 2), E(db, "jam", 2), E(db, "crusty_bread", 3), E(db, "bacon", 2), E(db, "pancakes", 1.5f), E(db, "cheesecake", 1), E(db, "chocolate", 1.5f), E(db, "omelette", 1.5f), E(db, "sandwich", 2), E(db, "fruitcake", 1)));
                t.pools.Add(Pool("Kleidung", 0.18f, 1, 1, 0f, true, E(db, "linen_shirt", 3), E(db, "flannel_shirt", 3), E(db, "work_jacket", 2), E(db, "blue_jeans", 3), E(db, "work_trousers", 3), E(db, "canvas_pants", 2), E(db, "black_trousers", 2), E(db, "worn_boots", 3), E(db, "work_boots", 2), E(db, "sneakers", 2), E(db, "dress_shoes", 2)));
                t.pools.Add(Pool("Muenzen", 0.6f, 1, 1, 0f, true, E(db, "wachtgroschen", 1, 3, 9)));
                t.pools.Add(Pool("Gut", 0.1f, 1, 1, 0f, true, E(db, "oil_jug", 2), E(db, "wool_coat", 1), E(db, "herbal_salve", 2), E(db, "knife", 1)));
            });

            // Vorrat: Kisten. Viel Essen und Material.
            MakeTable("Loot_Vorrat", overwrite, t =>
            {
                t.pools.Add(Pool("Essen", 1f, 1, 3, 0.5f, true, E(db, "bread", 4, 2, 4), E(db, "apple", 4, 3, 6), E(db, "cheese", 2, 1, 2), E(db, "dried_meat", 2, 1, 3), E(db, "forest_mushroom", 3, 2, 5), E(db, "honey", 0.6f)));
                t.pools.Add(Pool("Zubereitet", 0.45f, 1, 2, 0f, true, E(db, "baguette", 3), E(db, "bread_loaf", 2), E(db, "buns", 3), E(db, "bacon", 2), E(db, "sandwich", 2), E(db, "pizza", 1.5f), E(db, "french_fries", 1.5f), E(db, "potato_chips", 2), E(db, "hotdog", 1.5f), E(db, "burger", 1), E(db, "taco", 1), E(db, "salmon", 1), E(db, "sushi", 0.7f), E(db, "steak", 0.7f), E(db, "roast_chicken", 0.5f)));
                t.pools.Add(Pool("Material", 0.6f, 1, 2, 0f, true, E(db, "plank", 3, 2, 5), E(db, "nails", 2), E(db, "firewood", 3, 2, 4), E(db, "rope", 1), E(db, "hammer", 0.6f)));
                t.pools.Add(Pool("Muenzen", 0.3f, 1, 1, 0f, true, E(db, "wachtgroschen", 1, 2, 6)));
            });

            // Fass: Getraenke, manchmal Oel.
            MakeTable("Loot_Fass", overwrite, t =>
            {
                t.pools.Add(Pool("Getraenke", 0.9f, 1, 2, 0f, true, E(db, "beer", 4, 1, 3), E(db, "water", 4, 1, 2), E(db, "mead", 2), E(db, "red_wine", 1.5f), E(db, "white_wine", 1.5f), E(db, "schnaps", 1.5f), E(db, "whisky", 0.5f), E(db, "rum", 0.5f)));
                t.pools.Add(Pool("Oel", 0.25f, 1, 1, 0f, true, E(db, "oil_jug", 1, 1, 2)));
            });

            // Schatz: Truhe mit Muenzen und mehreren guten Funden.
            MakeTable("Loot_Schatz", overwrite, t =>
            {
                t.guaranteed.Add(E(db, "wachtgroschen", 1, 18, 40));
                t.pools.Add(Pool("Wertvoll", 1f, 1, 2, 0f, true, E(db, "coin_purse", 3), E(db, "compass", 2), E(db, "whisky", 2, 1, 2), E(db, "bourbon", 1.5f), E(db, "honey", 2, 1, 2)));
                t.pools.Add(Pool("Ausruestung", 0.8f, 1, 2, 0f, true, E(db, "machete", 2), E(db, "axe", 2), E(db, "flail", 1.5f), E(db, "knife", 2), E(db, "bat", 1.5f), E(db, "crowbar", 1.5f), E(db, "lantern", 2), E(db, "wool_coat", 2), E(db, "torch", 2, 2, 3)));
                t.pools.Add(Pool("Kleidung", 0.45f, 1, 2, 0f, true, E(db, "hunting_jacket", 2), E(db, "oilskin_coat", 2), E(db, "corduroy_pants", 2), E(db, "wool_trousers", 2), E(db, "hunting_pants", 2), E(db, "rubber_boots", 2), E(db, "hiking_boots", 2), E(db, "leather_boots", 2), E(db, "felt_boots", 2), E(db, "leather_jacket", 1), E(db, "cassock", 1), E(db, "doctor_coat", 1), E(db, "leather_pants", 1), E(db, "sheriff_trousers", 1), E(db, "soft_moccasins", 1), E(db, "red_boots", 1), E(db, "fur_coat", 0.3f), E(db, "runner_trousers", 0.3f)));
                t.pools.Add(Pool("Talisman", 0.3f, 1, 1, 0f, true, E(db, "talisman_blue", 3), E(db, "talisman_yellow", 3), E(db, "talisman_green", 3), E(db, "talisman_red", 2.5f), E(db, "talisman_violet", 0.7f)));
                t.pools.Add(Pool("Waffe", 0.2f, 1, 1, 0f, true, E(db, "pistol", 1), E(db, "pistol_silver", 1), E(db, "rifle", 0.5f), E(db, "shotgun", 0.6f), E(db, "sniper_rifle", 0.4f), E(db, "assault_rifle", 0.3f)));
                t.pools.Add(Pool("Munition", 0.35f, 1, 1, 0f, true, E(db, "ammo", 1, 4, 10), E(db, "shells", 0.6f, 3, 8)));
            });

            // Versteck: Funde im Freien, auch fuer lose Gegenstaende am Boden.
            MakeTable("Loot_Versteck", overwrite, t =>
            {
                t.pools.Add(Pool("Fund", 1f, 1, 3, 0.4f, true, E(db, "forest_mushroom", 3, 1, 4), E(db, "herbs", 3, 1, 3), E(db, "cloth_scrap", 1.5f), E(db, "apple", 2, 1, 3), E(db, "monster_tooth", 0.4f), E(db, "bandage", 1.5f), E(db, "candle", 1.5f)));
                t.pools.Add(Pool("Muenzen", 0.55f, 1, 1, 0f, true, E(db, "wachtgroschen", 1, 2, 7)));
                t.pools.Add(Pool("Schluessel", 0.12f, 1, 1, 0f, true, E(db, "house_key", 1)));
            });

            // Boden: lose Kleinigkeiten, die am Wegesrand liegen.
            MakeTable("Loot_Boden", overwrite, t =>
            {
                t.pools.Add(Pool("Boden", 1f, 1, 2, 0.5f, true, E(db, "apple", 3, 1, 2), E(db, "forest_mushroom", 3, 1, 3), E(db, "herbs", 2), E(db, "firewood", 2, 1, 2), E(db, "wachtgroschen", 3, 1, 4), E(db, "bandage", 0.6f), E(db, "candle", 0.8f)));
            });

            AssetDatabase.SaveAssets();
        }

        static LootTable Table(string name) => AssetDatabase.LoadAssetAtPath<LootTable>($"{TableDir}/{name}.asset");

        // ------------------------------------------------------------------ Prefabs
        class ContainerSpec
        {
            public string file, title, closed, openFull, openEmpty, table, keyId, prompt = "Open";
            public int slots = 12;
            public float luck;
            public int refillDays;
        }

        static void BuildPrefabs(ItemDatabase db, bool overwrite)
        {
            Directory.CreateDirectory(PrefabDir);
            var specs = new[]
            {
                new ContainerSpec { file = "Loot_Truhe_Holz", title = "Old Chest", closed = "Truhe_Dunkel", openFull = "Truhe_Leer", openEmpty = "Truhe_Leer", table = "Loot_Haushalt", slots = 12, luck = 0.1f },
                new ContainerSpec { file = "Loot_Truhe_Schatz", title = "Treasure Chest", closed = "Truhe_Dunkel", openFull = "Truhe_Gold", openEmpty = "Truhe_Leer", table = "Loot_Schatz", slots = 12, luck = 0.5f },
                new ContainerSpec { file = "Loot_Truhe_Verschlossen", title = "Iron Chest", closed = "Truhe_Dunkel", openFull = "Truhe_Schatz", openEmpty = "Truhe_Leer", table = "Loot_Schatz", keyId = "house_key", slots = 12, luck = 1f },
                new ContainerSpec { file = "Loot_Kiste", title = "Crate", closed = "Kiste", openFull = "Kiste_Offen", openEmpty = "Kiste_Offen", table = "Loot_Vorrat", slots = 8 },
                new ContainerSpec { file = "Loot_Fass", title = "Barrel", closed = "Fass_Zu_A", openFull = "Fass_Leer", openEmpty = "Fass_Leer", table = "Loot_Fass", slots = 6 },
                new ContainerSpec { file = "Lager_Truhe", title = "Storage Chest", closed = "Truhe_Dunkel", openFull = "Truhe_Leer", openEmpty = "Truhe_Leer", table = null, slots = 24, prompt = "Open" },
            };
            foreach (var s in specs) BuildContainerPrefab(db, s, overwrite);
            AssetDatabase.SaveAssets();
        }

        static Sprite LoadSprite(string name) => AssetDatabase.LoadAssetAtPath<Sprite>(SpriteDir + name + ".png");

        /// <summary>Leere Pixelzeilen unten im Bild: damit der Fuss des Behaelters genau auf dem Pivot sitzt (Hoehensortierung).</summary>
        static int BottomPadding(string spriteName, out int width)
        {
            width = 32;
            string path = SpriteDir + spriteName + ".png";
            if (!File.Exists(path)) return 0;
            var tex = new Texture2D(2, 2);
            tex.LoadImage(File.ReadAllBytes(path));
            int pad = 0;
            for (int y = 0; y < tex.height; y++)
            {
                bool any = false;
                for (int x = 0; x < tex.width && !any; x++) any = tex.GetPixel(x, y).a > 0.01f;
                if (any) break;
                pad++;
            }
            int minX = tex.width, maxX = 0;
            for (int x = 0; x < tex.width; x++)
                for (int y = 0; y < tex.height; y++)
                    if (tex.GetPixel(x, y).a > 0.01f) { minX = Mathf.Min(minX, x); maxX = Mathf.Max(maxX, x); break; }
            width = Mathf.Max(8, maxX - minX + 1);
            UnityEngine.Object.DestroyImmediate(tex);
            return pad;
        }

        static void BuildContainerPrefab(ItemDatabase db, ContainerSpec s, bool overwrite)
        {
            string path = $"{PrefabDir}/{s.file}.prefab";
            if (!overwrite && AssetDatabase.LoadAssetAtPath<GameObject>(path) != null) return;

            var closed = LoadSprite(s.closed);
            if (closed == null) { Debug.LogWarning("[Loot] Sprite fehlt: " + s.closed); return; }

            var root = new GameObject(s.file);
            var pic = new GameObject("Bild");
            pic.transform.SetParent(root.transform, false);
            int pad = BottomPadding(s.closed, out int width);
            pic.transform.localPosition = new Vector3(0f, 0.5f - pad / 32f, 0f);
            var sr = pic.AddComponent<SpriteRenderer>();
            sr.sprite = closed;
            sr.sortingOrder = OrderObjects;
            var lit = AssetDatabase.LoadAssetAtPath<Material>(LitMaterial);
            if (lit != null) sr.sharedMaterial = lit;

            // Der Behaelter blockiert den Weg (Fuss des Bildes)
            var box = root.AddComponent<BoxCollider2D>();
            box.size = new Vector2(width / 32f * 0.9f, 0.3f);
            box.offset = new Vector2(0f, 0.17f);

            var c = root.AddComponent<ItemContainer>();
            var v = root.AddComponent<ContainerVisual>();

            var so = new SerializedObject(c);
            so.FindProperty("prompt").stringValue = s.prompt;
            so.FindProperty("key").enumValueIndex = 1; // F
            so.FindProperty("indicatorHeight").floatValue = 1.05f;
            so.FindProperty("title").stringValue = s.title;
            so.FindProperty("slots").intValue = s.slots;
            so.FindProperty("luck").floatValue = s.luck;
            so.FindProperty("lootTable").objectReferenceValue = s.table != null ? Table(s.table) : null;
            so.FindProperty("keyItem").objectReferenceValue = s.keyId != null ? db.Get(s.keyId) : null;
            so.ApplyModifiedPropertiesWithoutUndo();

            var vso = new SerializedObject(v);
            vso.FindProperty("target").objectReferenceValue = sr;
            vso.FindProperty("closed").objectReferenceValue = closed;
            vso.FindProperty("openFull").objectReferenceValue = LoadSprite(s.openFull);
            vso.FindProperty("openEmpty").objectReferenceValue = LoadSprite(s.openEmpty);
            vso.ApplyModifiedPropertiesWithoutUndo();

            PrefabUtility.SaveAsPrefabAsset(root, path);
            UnityEngine.Object.DestroyImmediate(root);
        }

        static GameObject LoadPrefab(string file) => AssetDatabase.LoadAssetAtPath<GameObject>($"{PrefabDir}/{file}.prefab");

        // ------------------------------------------------------------------ Level_01
        static Tilemap Map(string name)
        {
            var go = GameObject.Find("Level_01/Grid/" + name);
            return go != null ? go.GetComponent<Tilemap>() : null;
        }

        static void PopulateLevel()
        {
            var scene = EditorSceneManager.GetActiveScene();
            var player = UnityEngine.Object.FindAnyObjectByType<PlayerController>();
            var ground = Map("Ground");
            if (player == null || ground == null) { Debug.LogWarning("[Loot] Level_01 mit Spieler und Grid/Ground muss geoeffnet sein."); return; }
            if (LoadPrefab("Loot_Truhe_Holz") == null) { Debug.LogWarning("[Loot] Prefabs fehlen. Erst 'Alles einrichten'."); return; }

            var old = GameObject.Find(RootName);
            if (old != null) UnityEngine.Object.DestroyImmediate(old);
            var root = new GameObject(RootName);
            Undo.RegisterCreatedObjectUndo(root, "Beute verteilen");
            Physics2D.SyncTransforms();

            var wege = Map("Wege");
            var objects = Map("Objects");
            var rng = new System.Random(20261021);
            var taken = new List<Vector2>();

            // ---- Demo-Gruppe vor dem Spieler: eine feste Auswahl, damit man alles sofort ausprobieren kann
            Vector2 origin = player.transform.position;
            var demo = new (string prefab, int dx)[] { ("Loot_Truhe_Holz", 0), ("Loot_Kiste", 1), ("Loot_Fass", 2), ("Loot_Truhe_Schatz", 3), ("Loot_Truhe_Verschlossen", 4), ("Lager_Truhe", 5) };
            Vector2 start = origin + new Vector2(0f, 5f);
            if (!FindFree(start, ground, wege, objects, taken, 8, out var rowOrigin)) rowOrigin = start;
            int placed = 0;
            foreach (var d in demo)
            {
                Vector2 want = rowOrigin + new Vector2(d.dx * 1.6f, 0f);
                if (!FindFree(want, ground, wege, objects, taken, 3, out var at)) continue;
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(LoadPrefab(d.prefab), root.transform);
                inst.transform.position = at;
                taken.Add(at);
                placed++;
            }
            // Schluessel und lose Gegenstaende zum Aufheben
            var loose = new (string id, int count)[] { ("house_key", 1), ("bread", 3), ("wachtgroschen", 15), ("lantern", 1), ("apple", 4), ("machete", 1) };
            Vector2 looseStart = rowOrigin + new Vector2(0f, -2.2f);
            int li = 0;
            foreach (var l in loose)
            {
                var def = LoadDb().Get(l.id);
                if (def == null) continue;
                if (!FindFree(looseStart + new Vector2(li++ * 1.2f, 0f), ground, wege, objects, taken, 3, out var at)) continue;
                var go = new GameObject("Fund_" + l.id);
                go.transform.SetParent(root.transform, false);
                go.transform.position = at;
                var p = go.AddComponent<ItemPickup>();
                var pso = new SerializedObject(p);
                pso.FindProperty("def").objectReferenceValue = def;
                pso.FindProperty("count").intValue = l.count;
                pso.ApplyModifiedPropertiesWithoutUndo();
                taken.Add(at);
            }

            // ---- Zufalls-Spawner ueber die Karte: bei jedem Start wuerfeln sie neu, was liegt
            var bounds = ground.cellBounds;
            var spawnerRoot = new GameObject("Spawner");
            spawnerRoot.transform.SetParent(root.transform, false);
            int containers = 0, grounds = 0;
            for (int attempt = 0; attempt < 4000 && (containers < 18 || grounds < 14); attempt++)
            {
                var cell = new Vector3Int(rng.Next(bounds.xMin, bounds.xMax), rng.Next(bounds.yMin, bounds.yMax), 0);
                Vector2 p = ground.GetCellCenterWorld(cell);
                p.y -= 0.5f;   // Fuss der Zelle
                if (Vector2.Distance(p, origin) < 6f) continue;
                bool wantContainer = containers < 18 && (grounds >= 14 || rng.NextDouble() < 0.55);
                if (!IsFree(p, ground, wege, objects) || TooClose(p, taken, wantContainer ? 9f : 5f)) continue;
                MakeSpawner(spawnerRoot.transform, p, wantContainer, containers + grounds);
                taken.Add(p);
                if (wantContainer) containers++; else grounds++;
            }

            Selection.activeGameObject = root;
            if (scene.name == "Level_01")
            {
                EditorSceneManager.MarkSceneDirty(scene);
                EditorSceneManager.SaveScene(scene);
            }
            Debug.Log($"[Loot] Level_01: {placed} Behaelter als Demo beim Spieler, {containers} Behaelter-Spawner und {grounds} Boden-Spawner verteilt.");
        }

        static bool TooClose(Vector2 p, List<Vector2> taken, float dist)
        {
            foreach (var t in taken) if ((t - p).sqrMagnitude < dist * dist) return true;
            return false;
        }

        /// <summary>Freier Boden: Boden vorhanden, kein Weg, kein Objekt, kein Hindernis (Collider) in der Naehe.</summary>
        static bool IsFree(Vector2 p, Tilemap ground, Tilemap wege, Tilemap objects)
        {
            var cell = ground.WorldToCell(p + Vector2.up * 0.5f);
            if (!ground.HasTile(cell)) return false;
            if (wege != null && wege.HasTile(wege.WorldToCell(p + Vector2.up * 0.5f))) return false;
            if (objects != null)
            {
                for (int dx = -1; dx <= 1; dx++)
                    for (int dy = 0; dy <= 1; dy++)
                        if (objects.HasTile(objects.WorldToCell(p + new Vector2(dx, dy + 0.5f)))) return false;
            }
            foreach (var h in Physics2D.OverlapBoxAll(p + new Vector2(0f, 0.4f), new Vector2(1.4f, 1.1f), 0f))
                if (!h.isTrigger) return false;
            return true;
        }

        /// <summary>Sucht in wachsenden Ringen um want einen freien Punkt, der nicht zu nah an schon gesetzten liegt.</summary>
        static bool FindFree(Vector2 want, Tilemap ground, Tilemap wege, Tilemap objects, List<Vector2> taken, float maxRadius, out Vector2 result)
        {
            for (float r = 0f; r <= maxRadius; r += 0.5f)
            {
                int steps = r < 0.01f ? 1 : Mathf.CeilToInt(r * 8f);
                for (int i = 0; i < steps; i++)
                {
                    float a = i / (float)steps * Mathf.PI * 2f;
                    Vector2 p = want + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r;
                    p = new Vector2(Mathf.Round(p.x * 2f) / 2f, Mathf.Round(p.y * 2f) / 2f);
                    if (!TooClose(p, taken, 1.1f) && IsFree(p, ground, wege, objects)) { result = p; return true; }
                }
            }
            result = want;
            return false;
        }

        static void MakeSpawner(Transform parent, Vector2 pos, bool container, int index)
        {
            var go = new GameObject((container ? "Behaelter_" : "Boden_") + index);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            var sp = go.AddComponent<LootSpawner>();
            var so = new SerializedObject(sp);
            if (container)
            {
                so.FindProperty("kind").enumValueIndex = (int)LootSpawner.Kind.Container;
                so.FindProperty("spawnChance").floatValue = 0.6f;
                var list = so.FindProperty("containers");
                var options = new (string file, float weight)[] { ("Loot_Truhe_Holz", 3f), ("Loot_Kiste", 4f), ("Loot_Fass", 3f), ("Loot_Truhe_Schatz", 0.8f), ("Loot_Truhe_Verschlossen", 0.5f) };
                list.arraySize = options.Length;
                for (int i = 0; i < options.Length; i++)
                {
                    var el = list.GetArrayElementAtIndex(i);
                    el.FindPropertyRelative("prefab").objectReferenceValue = LoadPrefab(options[i].file);
                    el.FindPropertyRelative("weight").floatValue = options[i].weight;
                }
            }
            else
            {
                so.FindProperty("kind").enumValueIndex = (int)LootSpawner.Kind.GroundItems;
                so.FindProperty("spawnChance").floatValue = 0.7f;
                so.FindProperty("groundTable").objectReferenceValue = Table(index % 3 == 0 ? "Loot_Versteck" : "Loot_Boden");
                so.FindProperty("scatterRadius").floatValue = 0.6f;
            }
            so.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
