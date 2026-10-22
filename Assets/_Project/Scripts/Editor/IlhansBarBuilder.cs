using System.Collections.Generic;
using System.IO;
using Nightward.Core;
using Nightward.DayNight;
using Nightward.Interaction;
using Nightward.Vision;
using Nightward.World;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using UnityEngine.Tilemaps;
using UnityEngine.UI;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut die Szene Scenes/Game/IlhansBar.unity: Ilhans Bar als Hauptgebaeude, aussen (Fassade, Veranda, Platz) und
    /// innen (Schankraum mit Theke und Spirituosen, Kueche, Hinterzimmer, Lager). Das Layout kommt aus
    /// Art/Tiles/Baukasten/Szene_IlhansBar.json (erzeugt von _Quelle_Generator/bar_szene.py, dort mit Vorschau + Pruefung).
    /// Die Szene wird additiv erzeugt und gespeichert, die gerade offene Szene bleibt unberuehrt.
    /// </summary>
    public static class IlhansBarBuilder
    {
        const string LayoutPath = "Assets/_Project/Art/Tiles/Baukasten/Szene_IlhansBar.json";
        const string ScenePath = "Assets/_Project/Scenes/Game/IlhansBar.unity";
        const string TilesRoot = "Assets/_Project/Art/Tiles";
        const string TA = TilesRoot + "/TileAssets";
        const string PlayerPrefab = "Assets/_Project/Prefabs/Characters/Player.prefab";
        const string TransitionSheet = "Assets/_Project/Art/VFX/Transitions/Transition_Tueren_Sheet.png";
        const int TransitionW = 480, TransitionH = 270;
        const string DoorSprite = "Assets/_Project/Art/Tiles/Baukasten/Objekte/Klapptuer.png";
        const string IconE = "Assets/_Project/Art/UI/Icons/Icon_Taste_E.png";
        const int OrderObjects = 4;

        [System.Serializable] class Eintrag { public string l, r; public int x, y, dx, dy; }
        [System.Serializable] class Licht { public float x, y, rad, i; public string k; public bool n; }
        [System.Serializable] class Zelle { public string l; public int x, y; }
        [System.Serializable] class Tuer { public int x, y, d; }
        [System.Serializable] class Layout
        {
            public int innenX, aussenBreite, aussenWandHoehe, innenBreite, innenHoehe;
            public float aussenTuerX, aussenSpawnX, aussenSpawnY, innenAusgangX, innenSpawnX, innenSpawnY;
            public Eintrag[] eintraege;
            public Licht[] lichter;
            public Zelle[] kollision;
            public Tuer[] tueren;
        }

        // Ebene -> (Wurzel, Sortierung, Individual, Objekt-Anker links unten)
        static readonly Dictionary<string, (string root, int order, bool individual, bool objAnchor)> Layers =
            new Dictionary<string, (string, int, bool, bool)>
            {
                { "a_boden", ("Gelaende", 0, false, false) }, { "a_weg", ("Gelaende", 1, false, false) },
                { "a_veranda", ("Gelaende", 2, false, false) }, { "a_vorne", ("Gelaende", OrderObjects, true, false) },
                { "a_obj", ("Gelaende", OrderObjects, true, true) },
                { "a_wand", ("Gebaeude", 0, false, false) }, { "a_dach", ("Gebaeude", 1, false, false) },
                { "a_deko", ("Gebaeude", 2, false, false) },
                { "i_boden", ("Innen", 0, false, false) }, { "i_schatten", ("Innen", 1, false, false) },
                { "i_bodendeko", ("Innen", 1, false, false) }, { "i_teppich", ("Innen", 1, false, true) },
                { "i_wand", ("Innen", 2, false, false) }, { "i_wanddeko", ("Innen", 3, false, false) },
                { "i_wandobj", ("Innen", 3, false, true) }, { "i_moebel", ("Innen", OrderObjects, true, false) },
                { "i_obj", ("Innen", OrderObjects, true, true) }, { "i_decke", ("Innen", 19, false, false) },
                // Kronen + Tuerrahmen y-sortiert mit der Spielfigur: obere Kronen liegen hinter ihr, untere davor
                // (sonst verschwinden Kopf/Beine in Tuerdurchgaengen)
                { "i_krone", ("Innen", OrderObjects, true, false) }, { "i_rahmen", ("Innen", OrderObjects, true, true) },
            };

        static readonly Color Warm = new Color(1f, 0.82f, 0.48f), Feuer = new Color(1f, 0.65f, 0.31f), Talisman = new Color(0.44f, 0.83f, 0.9f);

        [MenuItem("Nightward/Haus-Baukasten/Ilhans Bar Szene bauen")]
        public static void Build()
        {
            if (EditorApplication.isPlaying) { Debug.LogWarning("[Ilhans Bar] Bitte erst den Play-Modus beenden."); return; }
            var lay = JsonUtility.FromJson<Layout>(File.ReadAllText(LayoutPath));
            EnsureBarTiles();
            var transitionFrames = SliceTransition();
            var missing = new HashSet<string>();

            var previous = SceneManager.GetActiveScene();
            var existing = SceneManager.GetSceneByPath(ScenePath);
            // Ist die Bar-Szene gerade offen, wird sie direkt neu befuellt (Unity erlaubt kein Ueberschreiben einer offenen Szene).
            // Sonst additiv erzeugen, damit die gerade offene Szene unberuehrt bleibt.
            bool reuse = existing.IsValid() && existing.isLoaded;
            Scene scene;
            if (reuse)
            {
                scene = existing;
                foreach (var go in scene.GetRootGameObjects()) Object.DestroyImmediate(go);
            }
            else scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Additive);
            SceneManager.SetActiveScene(scene);
            try
            {
                var roots = new Dictionary<string, Transform>();
                var maps = new Dictionary<string, Tilemap>();
                var lit = AssetDatabase.LoadAssetAtPath<Material>("Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat");

                var aussen = new GameObject("Aussen").transform;
                var gebaeude = new GameObject("Gebaeude_IlhansBar").transform;
                gebaeude.SetParent(aussen, false);
                var sg = gebaeude.gameObject.AddComponent<SortingGroup>();   // Gebaeude sortiert als Ganzes (Pivot = Bodenlinie)
                sg.sortingOrder = OrderObjects;
                var innen = new GameObject("Innen_IlhansBar").transform;
                roots["Gelaende"] = Grid(aussen, "Gelaende");
                roots["Gebaeude"] = Grid(gebaeude, "Grid");
                roots["Innen"] = Grid(innen, "Grid");

                Tilemap Map(string layer)
                {
                    if (maps.TryGetValue(layer, out var m)) return m;
                    var (root, order, individual, objAnchor) = Layers[layer];
                    var go = new GameObject(layer);
                    go.transform.SetParent(roots[root], false);
                    if (layer == "i_rahmen") go.transform.localPosition = new Vector3(0f, -0.02f, 0f);   // knapp vor der Krone sortieren
                    m = go.AddComponent<Tilemap>();
                    m.animationFrameRate = 1f;
                    if (objAnchor) m.tileAnchor = Vector3.zero;
                    var tr = go.AddComponent<TilemapRenderer>();
                    tr.sortingOrder = order;
                    if (lit != null) tr.sharedMaterial = lit;
                    if (individual) tr.mode = TilemapRenderer.Mode.Individual;
                    maps[layer] = m;
                    return m;
                }

                foreach (var e in lay.eintraege)
                {
                    var tile = Resolve(e.r);
                    if (tile == null) { missing.Add(e.r); continue; }
                    var tm = Map(e.l);
                    var p = new Vector3Int(e.x, e.y, 0);
                    tm.SetTile(p, tile);
                    if (e.dx != 0 || e.dy != 0)
                    {
                        tm.SetTileFlags(p, TileFlags.None);
                        tm.SetTransformMatrix(p, Matrix4x4.Translate(new Vector3(e.dx / 32f, e.dy / 32f, 0)));
                    }
                }

                // Kollision
                var block = AssetDatabase.LoadAssetAtPath<TileBase>(TA + "/Collision_Block.asset");
                var colA = Collision(roots["Gelaende"]);
                var colI = Collision(roots["Innen"]);
                foreach (var c in lay.kollision) (c.l == "a" ? colA : colI).SetTile(new Vector3Int(c.x, c.y, 0), block);
                var wallBox = gebaeude.gameObject.AddComponent<BoxCollider2D>();
                wallBox.size = new Vector2(lay.aussenBreite, lay.aussenWandHoehe);
                wallBox.offset = new Vector2(lay.aussenBreite / 2f, lay.aussenWandHoehe / 2f);

                // Lichter
                foreach (var l in lay.lichter)
                {
                    var go = new GameObject("Licht_" + l.k);
                    go.transform.SetParent(l.x >= lay.innenX - 2 ? innen : aussen, true);
                    go.transform.position = new Vector3(l.x, l.y, 0);
                    var li = go.AddComponent<Light2D>();
                    li.lightType = Light2D.LightType.Point;
                    li.color = l.k == "feuer" ? Feuer : (l.k == "talisman" ? Talisman : Warm);
                    li.intensity = l.i;
                    li.pointLightOuterRadius = l.rad;
                    li.pointLightInnerRadius = l.rad * 0.2f;
                    if (l.n) go.AddComponent<NightLight>();
                }
                var global = new GameObject("Global Light 2D").AddComponent<Light2D>();
                global.lightType = Light2D.LightType.Global;
                global.color = new Color(0.72f, 0.74f, 0.95f);
                global.intensity = 0.55f;

                // Tueren (Aussen <-> Innen) und Spawnpunkte
                var spawnA = Marker(aussen, "Spawn_Aussen", new Vector3(lay.aussenSpawnX, lay.aussenSpawnY));
                var spawnI = Marker(innen, "Spawn_Innen", new Vector3(lay.innenSpawnX, lay.innenSpawnY));
                Door(aussen, "Tuer_Eingang", new Vector2(lay.aussenTuerX, -0.6f), new Vector2(1.8f, 0.6f), spawnI);
                Door(innen, "Tuer_Ausgang", new Vector2(lay.innenAusgangX, 0.35f), new Vector2(0.9f, 0.5f), spawnA);

                // Klapptueren in den Durchgaengen (E: 90 Grad nach innen auf / zu)
                var doorSprite = AssetDatabase.LoadAssetAtPath<Sprite>(DoorSprite);
                var iconE = AssetDatabase.LoadAssetAtPath<Sprite>(IconE);
                foreach (var d in lay.tueren ?? new Tuer[0])
                {
                    var door = new GameObject("Klapptuer");
                    door.transform.SetParent(innen, false);
                    door.transform.position = new Vector3(d.x + 0.5f, d.y + 1f, 0f);      // Scharnier oben im Durchgang
                    var doorBlock = door.AddComponent<BoxCollider2D>();
                    doorBlock.offset = new Vector2(0f, -0.5f);
                    doorBlock.size = new Vector2(0.9f, 1f);
                    var leaf = new GameObject("Blatt");
                    leaf.transform.SetParent(door.transform, false);
                    var sr = leaf.AddComponent<SpriteRenderer>();
                    sr.sprite = doorSprite;
                    sr.sortingOrder = OrderObjects;
                    sr.spriteSortPoint = SpriteSortPoint.Pivot;
                    if (lit != null) sr.sharedMaterial = lit;
                    var kt = door.AddComponent<KlappTuer>();
                    var so = new SerializedObject(kt);
                    so.FindProperty("richtung").intValue = d.d;
                    so.FindProperty("blatt").objectReferenceValue = leaf.transform;
                    so.FindProperty("sperre").objectReferenceValue = doorBlock;
                    so.FindProperty("prompt").stringValue = "Door";
                    so.FindProperty("indicatorHeight").floatValue = 0.4f;
                    so.ApplyModifiedPropertiesWithoutUndo();
                    var ind = new GameObject("Hinweis");
                    ind.transform.SetParent(door.transform, false);
                    var isr = ind.AddComponent<SpriteRenderer>();
                    isr.sortingOrder = 30;
                    var ii = ind.AddComponent<InteractionIndicator>();
                    var iso = new SerializedObject(ii);
                    iso.FindProperty("target").objectReferenceValue = kt;
                    iso.FindProperty("nearbySprite").objectReferenceValue = iconE;
                    iso.FindProperty("inRangeSprite").objectReferenceValue = iconE;
                    iso.FindProperty("showDistance").floatValue = 1.6f;
                    iso.ApplyModifiedPropertiesWithoutUndo();
                }

                // Bildschirm-Uebergang (Art/VFX/Transitions/Transition_Tueren) fuer Eingang/Ausgang
                var tGo = new GameObject("BildUebergang");
                var canvas = tGo.AddComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                canvas.sortingOrder = 500;
                tGo.AddComponent<CanvasScaler>().uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                var imgGo = new GameObject("Bild", typeof(RectTransform));
                imgGo.transform.SetParent(tGo.transform, false);
                var rtf = (RectTransform)imgGo.transform;
                rtf.anchorMin = Vector2.zero;
                rtf.anchorMax = Vector2.one;
                rtf.offsetMin = rtf.offsetMax = Vector2.zero;
                var img = imgGo.AddComponent<Image>();
                img.raycastTarget = false;
                img.enabled = false;
                var bu = tGo.AddComponent<BildUebergang>();
                var bso = new SerializedObject(bu);
                bso.FindProperty("bild").objectReferenceValue = img;
                var fp = bso.FindProperty("frames");
                fp.arraySize = transitionFrames.Count;
                for (int i = 0; i < transitionFrames.Count; i++) fp.GetArrayElementAtIndex(i).objectReferenceValue = transitionFrames[i];
                bso.ApplyModifiedPropertiesWithoutUndo();

                // Sichtsystem: Innenraum ohne Oeffnungen - draussen gibt es hier nichts zu sehen (Aussenbereich liegt weit weg)
                var area = innen.gameObject.AddComponent<BoxCollider2D>();
                area.isTrigger = true;
                area.offset = new Vector2(lay.innenX + lay.innenBreite / 2f, lay.innenHoehe / 2f);
                area.size = new Vector2(lay.innenBreite, lay.innenHoehe);
                innen.gameObject.AddComponent<Interior>();

                // Spielfigur + Kamera
                var pf = AssetDatabase.LoadAssetAtPath<GameObject>(PlayerPrefab);
                if (pf != null)
                {
                    var player = (GameObject)PrefabUtility.InstantiatePrefab(pf, scene);
                    player.transform.position = new Vector3(lay.aussenSpawnX, lay.aussenSpawnY - 3f, 0);
                    foreach (var sr in player.GetComponentsInChildren<SpriteRenderer>()) sr.sortingOrder = OrderObjects;
                }
                var camGo = new GameObject("Main Camera", typeof(Camera));
                camGo.tag = "MainCamera";
                var cam = camGo.GetComponent<Camera>();
                cam.orthographic = true;
                cam.orthographicSize = 4.5f;
                cam.transform.position = new Vector3(lay.aussenSpawnX, lay.aussenSpawnY, -10f);
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = new Color(0.1f, 0.08f, 0.15f);
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

                if (!EditorSceneManager.SaveScene(scene, ScenePath)) Debug.LogError("[Ilhans Bar] Szene konnte nicht gespeichert werden: " + ScenePath);
            }
            finally
            {
                if (previous.IsValid() && previous.isLoaded && previous != scene)
                {
                    SceneManager.SetActiveScene(previous);
                    if (!reuse) EditorSceneManager.CloseScene(scene, true);
                }
            }
            if (missing.Count > 0) Debug.LogError("[Ilhans Bar] Fehlende Tiles: " + string.Join(", ", missing));
            else Debug.Log($"[Ilhans Bar] Szene gebaut: {ScenePath} ({lay.eintraege.Length} Tiles, {lay.lichter.Length} Lichter, " +
                           $"{(lay.tueren ?? new Tuer[0]).Length} Klapptueren, Uebergang {transitionFrames.Count} Frames), 0 Fehler.");
        }

        /// <summary>Transition_Tueren in 480x270-Frames schneiden (leere Frames entfallen), Reihenfolge = zeilenweise.</summary>
        static List<Sprite> SliceTransition()
        {
            var res = new List<Sprite>();
            var ti = (TextureImporter)AssetImporter.GetAtPath(TransitionSheet);
            if (ti == null) { Debug.LogWarning("[Ilhans Bar] Uebergang fehlt: " + TransitionSheet); return res; }
            var tex = new Texture2D(2, 2);
            tex.LoadImage(File.ReadAllBytes(TransitionSheet));
            int cols = tex.width / TransitionW, rows = tex.height / TransitionH;
            var metas = new List<SpriteMetaData>();
            var names = new List<string>();
            for (int r = 0; r < rows; r++)
                for (int c = 0; c < cols; c++)
                {
                    var rect = new Rect(c * TransitionW, tex.height - (r + 1) * TransitionH, TransitionW, TransitionH);
                    bool empty = true;
                    foreach (var p in tex.GetPixels((int)rect.x, (int)rect.y, TransitionW, TransitionH)) if (p.a > 0.01f) { empty = false; break; }
                    if (empty) continue;
                    string n = "Transition_Tueren_" + metas.Count;
                    metas.Add(new SpriteMetaData { name = n, rect = rect, alignment = (int)SpriteAlignment.Center, pivot = new Vector2(0.5f, 0.5f) });
                    names.Add(n);
                }
            Object.DestroyImmediate(tex);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();
            var all = new Dictionary<string, Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(TransitionSheet)) if (o is Sprite sp) all[sp.name] = sp;
            foreach (var n in names) if (all.TryGetValue(n, out var sp)) res.Add(sp);
            return res;
        }

        static Transform Grid(Transform parent, string name)
        {
            var g = new GameObject(name);
            g.transform.SetParent(parent, false);
            g.AddComponent<Grid>();
            return g.transform;
        }

        static Tilemap Collision(Transform grid)
        {
            var go = new GameObject("Kollision");
            go.transform.SetParent(grid, false);
            var tm = go.AddComponent<Tilemap>();
            var tc = go.AddComponent<TilemapCollider2D>();
            var rb = go.AddComponent<Rigidbody2D>();
            rb.bodyType = RigidbodyType2D.Static;
            var cc = go.AddComponent<CompositeCollider2D>();
            cc.geometryType = CompositeCollider2D.GeometryType.Polygons;
            tc.compositeOperation = Collider2D.CompositeOperation.Merge;
            return tm;
        }

        static Transform Marker(Transform parent, string name, Vector3 pos)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            return go.transform;
        }

        static void Door(Transform parent, string name, Vector2 pos, Vector2 size, Transform target)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            var bc = go.AddComponent<BoxCollider2D>();
            bc.isTrigger = true;
            bc.size = size;
            var d = go.AddComponent<Durchgang>();
            var so = new SerializedObject(d);
            so.FindProperty("ziel").objectReferenceValue = target;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>Zellen der Bar-Tilesets als Tile-Assets (TileAssets/Bar), einmalig.</summary>
        static void EnsureBarTiles()
        {
            Directory.CreateDirectory(TA + "/Bar");
            AssetDatabase.Refresh();
            foreach (var png in new[] { TilesRoot + "/Tileset_Bar_Aussen.png", TilesRoot + "/Tileset_Bar_Innen.png" })
                foreach (var o in AssetDatabase.LoadAllAssetsAtPath(png))
                {
                    if (!(o is Sprite sp)) continue;
                    string path = $"{TA}/Bar/{sp.name}.asset";
                    var t = AssetDatabase.LoadAssetAtPath<Tile>(path);
                    if (t == null)
                    {
                        t = ScriptableObject.CreateInstance<Tile>();
                        t.colliderType = Tile.ColliderType.None;
                        AssetDatabase.CreateAsset(t, path);
                    }
                    t.sprite = sp;
                    EditorUtility.SetDirty(t);
                }
            AssetDatabase.SaveAssets();
        }

        static readonly Dictionary<string, TileBase> cache = new Dictionary<string, TileBase>();

        static TileBase Resolve(string reference)
        {
            if (cache.TryGetValue(reference, out var hit) && hit != null) return hit;
            TileBase t = null;
            foreach (var alt in reference.Split('|'))
            {
                var p = alt.Split(':');
                switch (p[0])
                {
                    case "BA": case "BI": t = Load($"{TA}/Bar/{p[0]}_{p[1]}_{p[2]}.asset"); break;
                    case "BKO": t = HausBaukasten.ObjTile(p[1]); break;
                    case "BKI": t = Load($"{TA}/Baukasten/Zellen/BKI_{p[1]}_{p[2]}.asset"); break;
                    case "RT": t = HausBaukasten.RT(p[1], p[2]); break;
                    case "T": t = Load($"{TA}/Terrain/T_{p[1]}_{p[2]}.asset"); break;
                    case "TRT": t = Load($"{TA}/RuleTiles/{p[1]}.asset"); break;
                    case "OBJ": t = Load($"{TA}/Objekte/{p[1]}.asset"); break;
                    case "ANI": t = Load($"{TA}/Animiert/{p[1]}.asset"); break;
                }
                if (t != null) break;
            }
            cache[reference] = t;
            return t;
        }

        static TileBase Load(string path) => AssetDatabase.LoadAssetAtPath<TileBase>(path);
    }
}
