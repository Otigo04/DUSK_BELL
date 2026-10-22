using System.Collections.Generic;
using System.IO;
using Nightward.Items;
using Nightward.Player;
using Nightward.Survival;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Richtet das Inventar ein: Item-Assets aus dem Katalog (Data/Items), ItemDatabase, Sprite-Import der Inventar-Art,
    /// Komponenten am Spieler der offenen Szene (PlayerInventory, InventoryUI, Debug-Panel), Schuss-Sprites fuer PlayerCombat.
    /// Menue: Nightward > Inventar
    /// </summary>
    public static class InventorySetup
    {
        const string ItemsDir = "Assets/_Project/Data/Items";
        const string DbPath = ItemsDir + "/ItemDatabase.asset";
        const string ArtItems = "Assets/_Project/Art/Items/";
        const string UiDir = "Assets/_Project/Art/UI/Inventory/";
        const string ShotDir = "Assets/_Project/Art/VFX/Projektil/";
        const string KitName = "Inventar_Testkit";

        [MenuItem("Nightward/Inventar/Alles einrichten (Spieler der offenen Szene)")]
        public static void SetupAll()
        {
            ImportSprites();
            var db = BuildItems(false);
            WirePlayer(db);
            Debug.Log("[Inventar] Einrichtung fertig: " + db.items.Count + " Gegenstaende.");
        }

        [MenuItem("Nightward/Inventar/Katalog zuruecksetzen (ueberschreibt Item-Assets)")]
        public static void ResetCatalog()
        {
            if (!EditorUtility.DisplayDialog("Item-Katalog", "Alle Item-Assets mit den Standardwerten aus ItemCatalog ueberschreiben? Eigene Aenderungen in den Assets gehen verloren.", "Ueberschreiben", "Abbrechen")) return;
            ImportSprites();
            BuildItems(true);
        }

        // ------------------------------------------------------------------ Sprites
        static void SetupSprite(string path, int ppu, Vector4? border = null)
        {
            var ti = AssetImporter.GetAtPath(path) as TextureImporter;
            if (ti == null) return;
            bool changed = ti.textureType != TextureImporterType.Sprite || ti.filterMode != FilterMode.Point || ti.spritePixelsPerUnit != ppu
                           || ti.textureCompression != TextureImporterCompression.Uncompressed || ti.spriteImportMode != SpriteImportMode.Single;
            if (!changed) return;
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Single;
            ti.spritePixelsPerUnit = ppu;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.SaveAndReimport();
        }

        static void ImportSprites()
        {
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { UiDir.TrimEnd('/') }))
            {
                string p = AssetDatabase.GUIDToAssetPath(guid);
                if (!Path.GetFileName(p).StartsWith("Vorschau")) SetupSprite(p, 100);
            }
            foreach (var e in ItemCatalog.All()) SetupSprite(ArtItems + e.icon, 32);
        }

        // ------------------------------------------------------------------ Items
        public static ItemDatabase BuildItems(bool overwrite)
        {
            Directory.CreateDirectory(ItemsDir);
            var db = AssetDatabase.LoadAssetAtPath<ItemDatabase>(DbPath);
            if (db == null)
            {
                db = ScriptableObject.CreateInstance<ItemDatabase>();
                AssetDatabase.CreateAsset(db, DbPath);
            }
            db.items.Clear();

            foreach (var e in ItemCatalog.All())
            {
                string dir = ItemsDir + "/" + e.folder;
                Directory.CreateDirectory(dir);
                string path = dir + "/Item_" + e.id + ".asset";
                var def = AssetDatabase.LoadAssetAtPath<ItemDef>(path);
                bool isNew = def == null;
                if (isNew) { def = ScriptableObject.CreateInstance<ItemDef>(); AssetDatabase.CreateAsset(def, path); }
                if (isNew || overwrite)
                {
                    // frische Standardwerte (Felder zuruecksetzen, dann Katalog anwenden)
                    var fresh = ScriptableObject.CreateInstance<ItemDef>();
                    EditorUtility.CopySerialized(fresh, def);
                    Object.DestroyImmediate(fresh);
                    def.id = e.id;
                    def.displayName = e.name;
                    def.description = e.desc;
                    def.category = e.category;
                    def.rarity = e.rarity;
                    def.maxStack = e.stack;
                    def.value = e.value;
                    e.extra?.Invoke(def);
                    if (def.HasDurability) def.maxStack = 1;
                }
                // Animations- und Kleidungswerte gehoeren zu den Sprites und bleiben aktuell, der Rest gehoert dem Inspector
                e.always?.Invoke(def);
                // Icon bleibt aktuell, auch wenn der Rest eigene Werte hat
                var icon = AssetDatabase.LoadAssetAtPath<Sprite>(ArtItems + e.icon);
                if (icon != null && (isNew || overwrite || def.icon == null)) def.icon = icon;
                else if (icon == null) Debug.LogWarning("[Inventar] Icon fehlt: " + e.icon);
                EditorUtility.SetDirty(def);
                db.items.Add(def);
            }
            EditorUtility.SetDirty(db);
            AssetDatabase.SaveAssets();
            return db;
        }

        // ------------------------------------------------------------------ Spieler
        static void WirePlayer(ItemDatabase db)
        {
            var controller = Object.FindAnyObjectByType<PlayerController>();
            if (controller == null) { Debug.LogWarning("[Inventar] Kein Spieler in der offenen Szene."); return; }
            var go = controller.gameObject;

            var pi = go.GetComponent<PlayerInventory>();
            bool fresh = pi == null;
            if (fresh) pi = go.AddComponent<PlayerInventory>();
            var so = new SerializedObject(pi);
            so.FindProperty("database").objectReferenceValue = db;
            if (fresh)
            {
                var start = so.FindProperty("startItems");
                var items = new[] { ("bread", 3), ("water", 2), ("bandage", 1), ("candle", 2), ("wachtgroschen", 12) };
                start.arraySize = items.Length;
                for (int i = 0; i < items.Length; i++)
                {
                    var el = start.GetArrayElementAtIndex(i);
                    el.FindPropertyRelative("id").stringValue = items[i].Item1;
                    el.FindPropertyRelative("count").intValue = items[i].Item2;
                }
            }
            so.ApplyModifiedPropertiesWithoutUndo();

            var ui = go.GetComponent<InventoryUI>();
            if (ui == null) ui = go.AddComponent<InventoryUI>();
            var uso = new SerializedObject(ui);
            SetSprite(uso, "slotNormal", "Slot_Normal.png");
            SetSprite(uso, "slotHover", "Slot_Hover.png");
            SetSprite(uso, "slotSelected", "Slot_Selected.png");
            SetSprite(uso, "slotEquip", "Slot_Equip.png");
            SetSprite(uso, "slotContainer", "Slot_Container.png");
            SetSprite(uso, "emptyLight", "Leer_Licht.png");
            SetSprite(uso, "emptyTalisman", "Leer_Talisman.png");
            SetSprite(uso, "emptyClothing", "Leer_Kleidung.png");
            uso.FindProperty("plate").objectReferenceValue = AssetDatabase.LoadAssetAtPath<Sprite>("Assets/_Project/Art/UI/HUD_Neu/Plates/Plate_Flyout.png");
            uso.ApplyModifiedPropertiesWithoutUndo();

            if (go.GetComponent<InventoryDebugPanel>() == null) go.AddComponent<InventoryDebugPanel>();

            WireCombat(go.GetComponent<PlayerCombat>());
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
            EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());
        }

        static void SetSprite(SerializedObject so, string field, string file)
        {
            var sp = AssetDatabase.LoadAssetAtPath<Sprite>(UiDir + file);
            if (sp == null) Debug.LogWarning("[Inventar] Sprite fehlt: " + file);
            so.FindProperty(field).objectReferenceValue = sp;
        }

        /// <summary>Schneidet die Projektil-Sheets (16x16-Zellen) und haengt sie an PlayerCombat.</summary>
        static void WireCombat(PlayerCombat combat)
        {
            if (combat == null) return;
            var flight = SliceGrid(ShotDir + "projektil_pistole.png", 16, 8, 3, "shot");
            var hit = SliceGrid(ShotDir + "projektil_treffer.png", 16, 1, 5, "hit");
            var so = new SerializedObject(combat);
            var a = so.FindProperty("shotFrames");
            a.arraySize = flight.Count;
            for (int i = 0; i < flight.Count; i++) a.GetArrayElementAtIndex(i).objectReferenceValue = flight[i];
            var b = so.FindProperty("shotHitFrames");
            b.arraySize = hit.Count;
            for (int i = 0; i < hit.Count; i++) b.GetArrayElementAtIndex(i).objectReferenceValue = hit[i];
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static List<Sprite> SliceGrid(string path, int cell, int rows, int cols, string prefix)
        {
            var ti = AssetImporter.GetAtPath(path) as TextureImporter;
            var result = new List<Sprite>();
            if (ti == null) return result;
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = 32;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            var metas = new List<SpriteMetaData>();
            int h = rows * cell;
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < cols; c++)
                    metas.Add(new SpriteMetaData { name = $"{prefix}_{r}_{c}", rect = new Rect(c * cell, h - (r + 1) * cell, cell, cell), alignment = (int)SpriteAlignment.Center, pivot = new Vector2(0.5f, 0.5f) });
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();

            var map = new Dictionary<string, Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path)) if (o is Sprite s) map[s.name] = s;
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < cols; c++)
                    if (map.TryGetValue($"{prefix}_{r}_{c}", out var sp)) result.Add(sp);
            return result;
        }

        // ------------------------------------------------------------------ Testkit
        [MenuItem("Nightward/Inventar/Testkit neben dem Spieler anlegen")]
        public static void CreateTestKit()
        {
            var controller = Object.FindAnyObjectByType<PlayerController>();
            var db = AssetDatabase.LoadAssetAtPath<ItemDatabase>(DbPath);
            if (controller == null || db == null) { Debug.LogWarning("[Inventar] Erst 'Alles einrichten'."); return; }
            var old = GameObject.Find(KitName);
            if (old != null) Object.DestroyImmediate(old);

            var root = new GameObject(KitName);
            Undo.RegisterCreatedObjectUndo(root, "Inventar-Testkit");
            Vector3 o = controller.transform.position;
            root.transform.position = o;

            // Truhe mit Beute
            var chest = new GameObject("Truhe (Beute)");
            chest.transform.SetParent(root.transform, false);
            chest.transform.position = o + new Vector3(4f, 0f, 0f);
            var c = chest.AddComponent<ItemContainer>();
            c.Prompt = "Open";
            var cso = new SerializedObject(c);
            cso.FindProperty("title").stringValue = "Old Chest";
            var entries = new (string id, int min, int max, float chance)[]
            {
                ("knife", 1, 1, 1f), ("club", 1, 1, 1f), ("pistol", 1, 1, 1f), ("ammo", 6, 12, 1f), ("lantern", 1, 1, 1f), ("oil_jug", 1, 2, 1f),
                ("wool_coat", 1, 1, 1f), ("talisman_blue", 1, 1, 1f), ("talisman_red", 1, 1, 1f), ("torch", 2, 3, 1f), ("stew_placeholder", 0, 0, 0f),
                ("honey", 1, 2, 0.7f), ("cheese", 2, 4, 1f), ("whisky", 1, 2, 0.8f), ("herbal_salve", 1, 1, 1f),
            };
            var list = cso.FindProperty("contents");
            int n = 0;
            list.arraySize = entries.Length;
            foreach (var e in entries)
            {
                var def = db.Get(e.id);
                if (def == null) continue;
                var el = list.GetArrayElementAtIndex(n++);
                el.FindPropertyRelative("item").objectReferenceValue = def;
                el.FindPropertyRelative("min").intValue = e.min;
                el.FindPropertyRelative("max").intValue = e.max;
                el.FindPropertyRelative("chance").floatValue = e.chance;
            }
            list.arraySize = n;
            cso.ApplyModifiedPropertiesWithoutUndo();

            // Lose Gegenstaende zum Aufheben
            var drops = new (string id, int count, Vector2 off)[]
            {
                ("bread", 3, new Vector2(2, -2)), ("apple", 5, new Vector2(3, -2)), ("machete", 1, new Vector2(4, -2)), ("wachtgroschen", 25, new Vector2(5, -2)),
                ("candle", 1, new Vector2(2, -3.5f)), ("axe", 1, new Vector2(3, -3.5f)), ("beer", 3, new Vector2(4, -3.5f)), ("talisman_green", 1, new Vector2(5, -3.5f)),
            };
            foreach (var d in drops)
            {
                var def = db.Get(d.id);
                if (def == null) continue;
                var go = new GameObject("Pickup_" + d.id);
                go.transform.SetParent(root.transform, false);
                go.transform.position = o + (Vector3)d.off;
                var p = go.AddComponent<ItemPickup>();
                var pso = new SerializedObject(p);
                pso.FindProperty("def").objectReferenceValue = def;
                pso.FindProperty("count").intValue = d.count;
                pso.ApplyModifiedPropertiesWithoutUndo();
            }

            Selection.activeGameObject = root;
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
            Debug.Log("[Inventar] Testkit angelegt (Truhe + lose Gegenstaende). Mit 'Testkit entfernen' loeschen.");
        }

        [MenuItem("Nightward/Inventar/Testkit entfernen")]
        public static void RemoveTestKit()
        {
            var kit = GameObject.Find(KitName);
            if (kit != null) Object.DestroyImmediate(kit);
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        }
    }
}
