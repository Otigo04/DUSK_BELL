using System.IO;
using Nightward.Player;
using Nightward.Survival;
using Nightward.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Richtet das Ueberlebens-System ein: Config-Asset anlegen, Spieler der offenen Szene mit den Komponenten
    /// ausstatten, HUD-Testtasten abschalten. Idempotent, jederzeit erneut ausfuehrbar.
    /// Menue: Nightward > Survival
    /// </summary>
    public static class SurvivalSetup
    {
        const string ConfigPath = "Assets/_Project/Data/Balancing/SurvivalConfig.asset";
        const string PlayerPrefabPath = "Assets/_Project/Prefabs/Characters/Player.prefab";
        const string KitName = "Survival_Testkit";

        [MenuItem("Nightward/Survival/Alles einrichten (Spieler der offenen Szene)")]
        public static void SetupAll()
        {
            var config = EnsureConfig();
            RemoveFromPlayerPrefab();
            WireScenePlayer(config);
            Debug.Log("[Survival] Einrichtung fertig. Config: " + ConfigPath);
        }

        [MenuItem("Nightward/Survival/Config-Asset anlegen oder auswaehlen")]
        public static SurvivalConfig EnsureConfig()
        {
            var config = AssetDatabase.LoadAssetAtPath<SurvivalConfig>(ConfigPath);
            if (config == null)
            {
                Directory.CreateDirectory(Path.GetDirectoryName(ConfigPath));
                config = ScriptableObject.CreateInstance<SurvivalConfig>();
                config.FillDefaults();
                AssetDatabase.CreateAsset(config, ConfigPath);
                AssetDatabase.SaveAssets();
                Debug.Log("[Survival] Config angelegt: " + ConfigPath);
            }
            Selection.activeObject = config;
            return config;
        }

        [MenuItem("Nightward/Survival/Config auf Standardwerte zuruecksetzen")]
        public static void ResetConfig()
        {
            if (!EditorUtility.DisplayDialog("Survival-Config", "Alle Werte der SurvivalConfig auf die Standardwerte aus dem Code zuruecksetzen?", "Zuruecksetzen", "Abbrechen")) return;
            var config = EnsureConfig();
            config.FillDefaults();
            EditorUtility.SetDirty(config);
            AssetDatabase.SaveAssets();
        }

        [MenuItem("Nightward/Survival/Fehlende Verbrauchsgueter ergaenzen (behaelt eigene Werte)")]
        public static int MergeMissingConsumables()
        {
            var config = EnsureConfig();
            var defaults = SurvivalDefaults.Create();
            int added = 0;
            foreach (var d in defaults.consumables)
            {
                if (config.Consumable(d.id) != null) continue;
                config.consumables.Add(d);
                added++;
            }
            Object.DestroyImmediate(defaults);
            EditorUtility.SetDirty(config);
            AssetDatabase.SaveAssets();
            Debug.Log("[Survival] " + added + " Verbrauchsgueter ergaenzt.");
            return added;
        }

        /// <summary>
        /// Das Player-Prefab steckt auch in Opening, IlhansBar und Sicht_Test. Dort soll das System nicht mitlaufen
        /// (Leertaste = Ausweichen wuerde z. B. mit dem Weiterklicken im Opening kollidieren), deshalb kommt es nur
        /// an den Spieler der gewuenschten Szene. Raeumt Reste im Prefab auf.
        /// </summary>
        static void RemoveFromPlayerPrefab()
        {
            var root = PrefabUtility.LoadPrefabContents(PlayerPrefabPath);
            try
            {
                bool changed = false;
                foreach (var t in new[] { typeof(SurvivalDebugPanel), typeof(SurvivalHudBinder), typeof(PlayerSurvival), typeof(SurvivalSystem) })
                {
                    var c = root.GetComponent(t);
                    if (c != null) { Object.DestroyImmediate(c); changed = true; }
                }
                if (changed)
                {
                    PrefabUtility.SaveAsPrefabAsset(root, PlayerPrefabPath);
                    Debug.Log("[Survival] Komponenten wieder aus dem Player-Prefab entfernt (nur Szenen-Spieler).");
                }
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
        }

        static void WireScenePlayer(SurvivalConfig config)
        {
            var scene = EditorSceneManager.GetActiveScene();
            var controller = Object.FindAnyObjectByType<PlayerController>();
            if (controller == null) { Debug.LogWarning("[Survival] Kein Spieler in der offenen Szene."); return; }

            Equip(controller.gameObject, config);

            // Die alten HUD-Testtasten wuerden die Werte aus der Simulation sofort wieder ueberschreiben
            foreach (var dbg in Object.FindObjectsByType<NwGameHudDebug>(FindObjectsInactive.Include))
            {
                var so = new SerializedObject(dbg);
                var p = so.FindProperty("enableKeys");
                if (p != null && p.boolValue) { p.boolValue = false; so.ApplyModifiedProperties(); }
            }
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }

        static void Equip(GameObject player, SurvivalConfig config)
        {
            var system = player.GetComponent<SurvivalSystem>();
            if (system == null) system = player.AddComponent<SurvivalSystem>();
            var so = new SerializedObject(system);
            so.FindProperty("config").objectReferenceValue = config;
            so.ApplyModifiedPropertiesWithoutUndo();

            if (player.GetComponent<PlayerSurvival>() == null) player.AddComponent<PlayerSurvival>();
            if (player.GetComponent<SurvivalHudBinder>() == null) player.AddComponent<SurvivalHudBinder>();
            if (player.GetComponent<SurvivalDebugPanel>() == null) player.AddComponent<SurvivalDebugPanel>();
        }

        // ------------------------------------------------------------------ Testkit
        [MenuItem("Nightward/Survival/Testkit neben dem Spieler anlegen")]
        public static void CreateTestKit()
        {
            var controller = Object.FindAnyObjectByType<PlayerController>();
            if (controller == null) { Debug.LogWarning("[Survival] Kein Spieler in der Szene."); return; }
            var old = GameObject.Find(KitName);
            if (old != null) Object.DestroyImmediate(old);

            var root = new GameObject(KitName);
            Undo.RegisterCreatedObjectUndo(root, "Survival-Testkit");
            Vector3 o = controller.transform.position;
            root.transform.position = o;

            Source(root, "Brunnen (Wasser)", o + new Vector3(3, 0), "water", "Drink", -1);
            Source(root, "Brotkorb (3x Brot)", o + new Vector3(3, 2), "bread", "Eat", 3);
            Source(root, "Teekanne (Beruhigungstee)", o + new Vector3(5, 0), "tea_calming", "Drink", -1);
            Source(root, "Bar-Theke (Schnaps)", o + new Vector3(5, 2), "schnaps", "Drink", -1);

            var bench = Child(root, "Bank (Rast + Quellwasser)", o + new Vector3(7, 2));
            var rest = bench.AddComponent<SurvivalRestPoint>();
            var rso = new SerializedObject(rest);
            rso.FindProperty("consumableId").stringValue = "spring_water";
            rso.ApplyModifiedPropertiesWithoutUndo();
            rest.Prompt = "Rest";

            var bed = Child(root, "Bett (Schlafen)", o + new Vector3(7, 0));
            bed.AddComponent<SurvivalBed>().Prompt = "Sleep";

            Zone(root, "Lagerfeuer (Zone)", o + new Vector3(0, -4), new Vector2(4, 4), nearFire: true, light: true);
            Zone(root, "Dickicht (Zone)", o + new Vector3(-6, 0), new Vector2(6, 5), thicket: true);
            Zone(root, "Unheimlicher Ort (Sanity -6 pro Stunde)", o + new Vector3(0, 5), new Vector2(4, 3), eerie: true);

            Selection.activeGameObject = root;
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
            Debug.Log("[Survival] Testkit angelegt. Mit 'Testkit entfernen' wieder loeschen.");
        }

        [MenuItem("Nightward/Survival/Testkit entfernen")]
        public static void RemoveTestKit()
        {
            var kit = GameObject.Find(KitName);
            if (kit == null) return;
            Object.DestroyImmediate(kit);
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        }

        static GameObject Child(GameObject parent, string name, Vector3 pos)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent.transform, false);
            go.transform.position = pos;
            return go;
        }

        static void Source(GameObject parent, string name, Vector3 pos, string id, string prompt, int uses)
        {
            var go = Child(parent, name, pos);
            var src = go.AddComponent<SurvivalSource>();
            var so = new SerializedObject(src);
            so.FindProperty("consumableId").stringValue = id;
            so.FindProperty("uses").intValue = uses;
            so.ApplyModifiedPropertiesWithoutUndo();
            src.Prompt = prompt;
        }

        static void Zone(GameObject parent, string name, Vector3 pos, Vector2 size, bool nearFire = false, bool light = false, bool thicket = false, bool eerie = false)
        {
            var go = Child(parent, name, pos);
            var box = go.AddComponent<BoxCollider2D>();
            box.size = size;
            box.isTrigger = true;
            var zone = go.AddComponent<SurvivalZone>();
            var so = new SerializedObject(zone);
            so.FindProperty("nearFire").boolValue = nearFire;
            so.FindProperty("lightIsland").boolValue = light;
            so.FindProperty("thicket").boolValue = thicket;
            if (eerie)
            {
                var fx = so.FindProperty("effects");
                fx.arraySize = 2;
                SetEffect(fx.GetArrayElementAtIndex(0), EffectKind.StatRate, StatId.Sanity, -6f);
                SetEffect(fx.GetArrayElementAtIndex(1), EffectKind.StatRate, StatId.Stress, 4f);
            }
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static void SetEffect(SerializedProperty e, EffectKind kind, StatId stat, float value)
        {
            e.FindPropertyRelative("kind").enumValueIndex = (int)kind;
            e.FindPropertyRelative("stat").enumValueIndex = (int)stat;
            e.FindPropertyRelative("value").floatValue = value;
        }
    }
}
