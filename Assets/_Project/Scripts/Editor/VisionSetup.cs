using Nightward.Core;
using Nightward.NPC;
using Nightward.Vision;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Tilemaps;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Sicht in Gebaeuden einrichten:
    ///  - "Spieler einrichten": Materialien anlegen und PlayerVision ans Player-Prefab haengen.
    ///  - "Auswahl zu Innenraum machen": Interior + Trigger-Box um das gewaehlte Haus. Fenster/Tueren danach als
    ///    Kinder mit VisionOpening (BoxCollider2D, ragt ueber die Aussenkante) anlegen: "Fenster/Tuer hinzufuegen".
    ///  - "Testszene bauen": Scenes/Sandbox/Sicht_Test.unity, ein Raum mit zwei Fenstern und Tuer, draussen ein Monster.
    /// </summary>
    public static class VisionSetup
    {
        const string MatDir = "Assets/_Project/Art/Materials";
        const string MaskMat = MatDir + "/Sicht_Maske.mat";
        const string DarkMat = MatDir + "/Sicht_Dunkelheit.mat";
        const string FalloffMat = MatDir + "/Sicht_Verlauf.mat";
        const string PlayerPrefab = "Assets/_Project/Prefabs/Characters/Player.prefab";
        const string MonsterPrefab = "Assets/_Project/Prefabs/Characters/NPC_Gast.prefab";
        const string TestScene = "Assets/_Project/Scenes/Sandbox/Sicht_Test.unity";
        const string TA = "Assets/_Project/Art/Tiles/TileAssets";

        [MenuItem("Nightward/Sicht/Spieler einrichten")]
        public static void SetupPlayer()
        {
            var mats = Materials();
            var contents = PrefabUtility.LoadPrefabContents(PlayerPrefab);
            var vision = contents.GetComponent<PlayerVision>();
            if (vision == null) vision = contents.AddComponent<PlayerVision>();
            var so = new SerializedObject(vision);
            so.FindProperty("maskMaterial").objectReferenceValue = mats.mask;
            so.FindProperty("darknessMaterial").objectReferenceValue = mats.dark;
            so.FindProperty("falloffMaterial").objectReferenceValue = mats.falloff;
            // Werte, die sich seit der ersten Version geaendert haben (im Prefab gespeicherte alte Werte ueberschreiben)
            so.FindProperty("coneAngle").floatValue = 160f;
            so.FindProperty("edgeSoftness").floatValue = 35f;
            so.FindProperty("range").floatValue = 11f;
            so.FindProperty("turnSmoothTime").floatValue = 0.15f;
            so.FindProperty("eyeOffset").vector2Value = new Vector2(0f, 0.1f);
            so.FindProperty("fadeTime").floatValue = 0.3f;
            so.FindProperty("penumbraNear").floatValue = 0.3f;
            so.FindProperty("penumbraGrowth").floatValue = 0.2f;
            so.ApplyModifiedPropertiesWithoutUndo();
            PrefabUtility.SaveAsPrefabAsset(contents, PlayerPrefab);
            PrefabUtility.UnloadPrefabContents(contents);
            Debug.Log("[Sicht] PlayerVision am Player-Prefab eingerichtet.");
        }

        static (Material mask, Material dark, Material falloff) Materials()
        {
            AssetDatabase.Refresh();
            var mask = LoadOrCreate(MaskMat, "Nightward/Vision Mask", null);
            var dark = LoadOrCreate(DarkMat, "Nightward/Vision Darkness", m => m.SetFloat("_StencilComp", (float)CompareFunction.NotEqual));
            var falloff = LoadOrCreate(FalloffMat, "Nightward/Vision Darkness", m => m.SetFloat("_StencilComp", (float)CompareFunction.Always));
            return (mask, dark, falloff);
        }

        static Material LoadOrCreate(string path, string shader, System.Action<Material> setup)
        {
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                var s = Shader.Find(shader);
                if (s == null) { Debug.LogError("[Sicht] Shader fehlt: " + shader); return null; }
                m = new Material(s);
                AssetDatabase.CreateAsset(m, path);
            }
            setup?.Invoke(m);
            EditorUtility.SetDirty(m);
            return m;
        }

        [MenuItem("Nightward/Sicht/Auswahl zu Innenraum machen")]
        static void MakeInterior()
        {
            var go = Selection.activeGameObject;
            Undo.RegisterFullObjectHierarchyUndo(go, "Innenraum");
            var box = go.GetComponent<BoxCollider2D>();
            if (box == null && go.GetComponent<PolygonCollider2D>() == null)
            {
                box = Undo.AddComponent<BoxCollider2D>(go);
                var b = new Bounds(go.transform.position, Vector3.zero);
                foreach (var r in go.GetComponentsInChildren<Renderer>()) b.Encapsulate(r.bounds);
                box.offset = go.transform.InverseTransformPoint(b.center);
                box.size = b.size;
            }
            if (box != null) box.isTrigger = true;
            if (go.GetComponent<Interior>() == null) Undo.AddComponent<Interior>(go);
        }

        [MenuItem("Nightward/Sicht/Auswahl zu Innenraum machen", true)]
        static bool CanMakeInterior() => Selection.activeGameObject != null;

        [MenuItem("Nightward/Sicht/Fenster oder Tuer hinzufuegen")]
        static void AddOpening()
        {
            var interior = Selection.activeGameObject.GetComponentInParent<Interior>();
            var go = new GameObject("Fenster");
            Undo.RegisterCreatedObjectUndo(go, "Fenster");
            go.transform.SetParent(interior.transform, false);
            var box = go.AddComponent<BoxCollider2D>();
            box.isTrigger = true;
            box.size = new Vector2(1f, 2f);
            go.AddComponent<VisionOpening>();
            Selection.activeGameObject = go;
        }

        [MenuItem("Nightward/Sicht/Fenster oder Tuer hinzufuegen", true)]
        static bool CanAddOpening() => Selection.activeGameObject != null && Selection.activeGameObject.GetComponentInParent<Interior>() != null;

        // ------------------------------------------------------------------ Testszene

        static TileBase Tile(string folder, string name) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/{folder}/{name}.asset");
        static TileBase I(int row, int col) => Tile("Interieur", $"I_{row}_{col}");

        static Tilemap Map(Transform grid, string name, int order, bool collider = false)
        {
            var go = new GameObject(name, typeof(Tilemap), typeof(TilemapRenderer));
            go.transform.SetParent(grid, false);
            var r = go.GetComponent<TilemapRenderer>();
            r.sortingOrder = order;
            if (collider)
            {
                go.AddComponent<TilemapCollider2D>();
                r.enabled = false;
            }
            return go.GetComponent<Tilemap>();
        }

        [MenuItem("Nightward/Sicht/Testszene bauen")]
        public static void BuildTestScene()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            SetupPlayer();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // Raum: Boden x 0..9, y 0..6; Nordwand (2 Kacheln hoch) y 7..8, Mauerkrone y 9; Seitenwaende x -1 und 10; Suedkante y -1 mit Tuer x 4..5
            var grid = new GameObject("Grid", typeof(Grid)).transform;
            var ground = Map(grid, "Boden_Aussen", 0);
            var floor = Map(grid, "Boden_Innen", 1);
            var walls = Map(grid, "Waende", 2);
            var deco = Map(grid, "Moebel", 3);
            var col = Map(grid, "Kollision", 0, collider: true);
            var block = AssetDatabase.LoadAssetAtPath<TileBase>(TA + "/Collision_Block.asset");

            var rng = new System.Random(7);
            for (int y = -14; y <= 26; y++)
                for (int x = -18; x <= 28; x++)
                    ground.SetTile(new Vector3Int(x, y, 0), Tile("Terrain", $"T_4_{(rng.NextDouble() < 0.8 ? 0 : rng.Next(1, 4))}"));

            for (int y = 0; y <= 6; y++)
                for (int x = 0; x <= 9; x++)
                    floor.SetTile(new Vector3Int(x, y, 0), I(0, 0));
            floor.SetTile(new Vector3Int(4, -1, 0), I(0, 0));
            floor.SetTile(new Vector3Int(5, -1, 0), I(0, 0));

            int[] windows = { 2, 7 };
            for (int x = 0; x <= 9; x++)
            {
                bool window = System.Array.IndexOf(windows, x) >= 0;
                walls.SetTile(new Vector3Int(x, 8, 0), I(3, window ? 6 : 0));
                walls.SetTile(new Vector3Int(x, 7, 0), I(4, window ? 6 : 0));
                walls.SetTile(new Vector3Int(x, 9, 0), I(5, 0));
                col.SetTile(new Vector3Int(x, 7, 0), block);
                col.SetTile(new Vector3Int(x, 8, 0), block);
                col.SetTile(new Vector3Int(x, 9, 0), block);
                if (x == 4 || x == 5) continue; // Tuer
                walls.SetTile(new Vector3Int(x, -1, 0), I(5, 0));
                col.SetTile(new Vector3Int(x, -1, 0), block);
            }
            for (int y = -1; y <= 9; y++)
            {
                var tile = y == 9 ? I(5, 4) : y == -1 ? I(5, 5) : I(5, 3);
                walls.SetTile(new Vector3Int(-1, y, 0), tile);
                walls.SetTile(new Vector3Int(10, y, 0), tile);
                col.SetTile(new Vector3Int(-1, y, 0), block);
                col.SetTile(new Vector3Int(10, y, 0), block);
            }
            // etwas Einrichtung
            deco.SetTile(new Vector3Int(1, 3, 0), I(9, 2));
            deco.SetTile(new Vector3Int(2, 3, 0), I(9, 3));
            deco.SetTile(new Vector3Int(8, 5, 0), I(10, 4));
            deco.SetTile(new Vector3Int(8, 1, 0), I(10, 5));
            col.SetTile(new Vector3Int(1, 3, 0), block);
            col.SetTile(new Vector3Int(2, 3, 0), block);
            col.SetTile(new Vector3Int(8, 5, 0), block);
            col.SetTile(new Vector3Int(8, 1, 0), block);
            var rb = col.gameObject.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Static;

            // Innenraum mit zwei Fenstern (Nordwand) und der Tuer (Sueden)
            var room = new GameObject("Haus_Innen");
            var area = room.AddComponent<BoxCollider2D>();
            area.isTrigger = true;
            // Bis an die Aussenkante der Mauerkronen (die Kronen-Tiles fuellen ihre Zelle nicht ganz): x -0.75..10.75, y -0.75..9.5
            area.offset = new Vector2(5f, 4.375f);
            area.size = new Vector2(11.5f, 10.25f);
            room.AddComponent<Interior>();
            foreach (int x in windows) Opening(room.transform, "Fenster_" + x, new Vector2(x + 0.5f, 9f), new Vector2(0.9f, 2.4f));
            Opening(room.transform, "Tuer", new Vector2(5f, -0.6f), new Vector2(1.9f, 1.2f));

            // Licht: Nacht draussen, Lampe drinnen
            var global = new GameObject("Global Light 2D").AddComponent<Light2D>();
            global.lightType = Light2D.LightType.Global;
            global.intensity = 0.45f;
            global.color = new Color(0.62f, 0.66f, 0.95f);
            var lamp = new GameObject("Lampe").AddComponent<Light2D>();
            lamp.lightType = Light2D.LightType.Point;
            lamp.transform.position = new Vector3(8.5f, 5.6f, 0f);
            lamp.color = new Color(1f, 0.75f, 0.45f);
            lamp.intensity = 1.1f;
            lamp.pointLightOuterRadius = 7f;
            lamp.pointLightInnerRadius = 1f;

            var nav = new GameObject("NavGrid").AddComponent<NavGrid>();

            var player = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(PlayerPrefab));
            player.transform.position = new Vector3(5f, 3f, 0f);

            var monsterAsset = AssetDatabase.LoadAssetAtPath<GameObject>(MonsterPrefab);
            if (monsterAsset != null)
            {
                var m = (GameObject)PrefabUtility.InstantiatePrefab(monsterAsset);
                m.transform.position = new Vector3(4.5f, 14.5f, 0f);
                var wander = m.GetComponent<WanderBehavior>();
                if (wander != null)
                {
                    var ws = new SerializedObject(wander);
                    ws.FindProperty("radius").floatValue = 5f;
                    ws.ApplyModifiedPropertiesWithoutUndo();
                }
            }

            var camGo = new GameObject("Main Camera", typeof(Camera));
            camGo.tag = "MainCamera";
            var cam = camGo.GetComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 4.5f;
            cam.transform.position = new Vector3(5f, 3f, -10f);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.07f, 0.11f, 0.08f);
            cam.transparencySortMode = TransparencySortMode.CustomAxis;
            cam.transparencySortAxis = new Vector3(0, 1, 0);
            camGo.AddComponent<UniversalAdditionalCameraData>();
            var ppc = camGo.AddComponent<PixelPerfectCamera>();
            ppc.assetsPPU = 32;
            ppc.refResolutionX = 384;
            ppc.refResolutionY = 216;
            var follow = camGo.AddComponent<CameraFollow2D>();
            var fs = new SerializedObject(follow);
            fs.FindProperty("clampToBounds").boolValue = false;
            fs.ApplyModifiedPropertiesWithoutUndo();

            EditorSceneManager.SaveScene(scene, TestScene);
            Debug.Log("[Sicht] Testszene gebaut: " + TestScene + ". Play druecken, im Raum herumlaufen und zu den Fenstern schauen.");
        }

        static void Opening(Transform parent, string name, Vector2 center, Vector2 size)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = center;
            var box = go.AddComponent<BoxCollider2D>();
            box.isTrigger = true;
            box.size = size;
            go.AddComponent<VisionOpening>();
        }
    }
}
