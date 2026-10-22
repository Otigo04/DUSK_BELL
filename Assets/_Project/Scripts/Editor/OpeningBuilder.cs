using System.Collections.Generic;
using System.IO;
using Nightward.Core;
using Nightward.Dialogue;
using Nightward.Interaction;
using Nightward.NPC;
using Nightward.Opening;
using Nightward.Player;
using Nightward.UI;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.Tilemaps;
using UnityEngine.UI;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut die Szene Opening (Docs/_Sequences/Opening Sequence.pdf): gerade Landstrasse durch den Wald mit dem Baumstamm
    /// im Norden, im Sueden das Dorf mit Dorfplatz, frischem Grab, Trauergaesten, ein paar Grabsteinen und Haeusern.
    /// Dazu Auto, Spieler, Bulut, Dialog-UI, Tag/Nacht und die Opening-UI (Charakterwahl, Intro, Quest-HUD ...).
    /// Kann beliebig oft ausgefuehrt werden, die Szene wird jedes Mal neu erzeugt.
    /// </summary>
    public static class OpeningBuilder
    {
        const string ScenePath = "Assets/_Project/Scenes/Game/Opening.unity";
        const string Art = "Assets/_Project/Art";
        const string TileAssets = Art + "/Tiles/TileAssets";
        const string EnvDir = Art + "/Environment/Opening";
        const string VehDir = Art + "/Vehicles";
        const string UiDir = Art + "/UI/Opening";
        const string FontPath = Art + "/UI/Font/SpecialElite-Regular.ttf";      // gut lesbar, Schreibmaschine
        const string HandFont = Art + "/UI/Font/ReenieBeanie-Regular.ttf";      // Handschrift auf dem Zettel
        const string PanelSprite = Art + "/UI/Panels/Panel_Dialog.png";
        const string QuestIcon = Art + "/UI/Icons/Icon_Quest.png";
        const string ButtonPrefab = "Assets/_Project/Prefabs/UI/UI_Button.prefab";
        const string PlayerPrefab = "Assets/_Project/Prefabs/Characters/Player.prefab";
        const string NpcDir = "Assets/_Project/Prefabs/Characters/";
        const string HouseDir = "Assets/_Project/Prefabs/Haeuser/";
        const string BulutPortraits = Art + "/Characters/BULUT SHERIFF/portraits/";
        const string LitMaterial = "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat";

        // Karte (Zellen = Units). Strasse x -1..1 (Mitte 0,5), Wald im Norden, Dorf im Sueden
        const int MinX = -24, MaxX = 26, MinY = -88, MaxY = 84;
        const int ForestStartY = -22;     // ab hier nach Norden Wald
        const int LogY = 64;              // Baumstamm
        const int RoadEndY = 74;
        const float RoadX = 0.5f;
        const int OrderGround = 0, OrderDeco = 2, OrderObjects = 4, OrderCrowns = 20;

        enum Ter { Grass, Dirt, Cobble, Forest }

        static Ter[,] ter;
        static bool[,] occ, solid;
        static System.Random rng;
        static Tilemap objMap, crownMap;
        static readonly List<Vector2> trunkFeet = new List<Vector2>();

        [MenuItem("Nightward/Opening/Szene bauen")]
        public static void Build()
        {
            // Nur bei echten, gespeicherten Szenen nachfragen; eine leere Hilfsszene (ohne Pfad) wird verworfen
            var current = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
            if (current.isDirty && !string.IsNullOrEmpty(current.path) && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            AssetDatabase.Refresh();
            ImportArt();
            var manCtrl = BuildManController();
            var womanCtrl = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(Art + "/Animations/Hauptfigur_Frau/Hauptfigur_Frau.controller");
            AddInteractStates(womanCtrl, "Hauptfigur_Frau", "Hauptfiguren/Frau/frau_interact.png");
            AddInteractStates(manCtrl, "Hauptfigur_Mann", "Hauptfiguren/Mann/mann_interact.png");
            TunePlayerSpeed();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            rng = new System.Random(20261020);
            trunkFeet.Clear();

            // ---------- Kamera und Licht
            var camGo = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener));
            camGo.tag = "MainCamera";
            camGo.transform.position = new Vector3(RoadX, -6f, -10f);
            var cam = camGo.GetComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 3.375f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.07f, 0.11f, 0.08f);
            cam.transparencySortMode = TransparencySortMode.CustomAxis;
            cam.transparencySortAxis = new Vector3(0, 1, 0);
            var camData = camGo.AddComponent<UniversalAdditionalCameraData>();
            camData.renderPostProcessing = true;
            var ppc = camGo.AddComponent<PixelPerfectCamera>();
            ppc.assetsPPU = 32;
            ppc.refResolutionX = 384;
            ppc.refResolutionY = 216;
            var follow = camGo.AddComponent<CameraFollow2D>();

            var globalGo = new GameObject("Global Light 2D");
            var global = globalGo.AddComponent<Light2D>();
            global.lightType = Light2D.LightType.Global;
            global.intensity = 1f;

            // ---------- Karte
            var root = new GameObject("Opening_Karte");
            var grid = new GameObject("Grid");
            grid.transform.SetParent(root.transform);
            grid.AddComponent<Grid>();
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
            var deco = Layer("Deco", OrderDeco, false);
            objMap = Layer("Objects", OrderObjects, true);
            objMap.tileAnchor = Vector3.zero;
            crownMap = Layer("Crowns", OrderCrowns, true);
            crownMap.tileAnchor = Vector3.zero;

            BuildTerrain();
            int w = MaxX - MinX + 1, h = MaxY - MinY + 1;
            occ = new bool[w, h];
            solid = new bool[w, h];

            var houses = PlaceVillage(grid.transform, out var revierDoor, out var manDoor, out var lantern);
            PlaceForest();
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                    ground.SetTile(new Vector3Int(x, y, 0), TerrainTile(x, y));
            Deco(deco);
            BuildCollision(grid.transform, root.transform);

            var fader = crownMap.gameObject.AddComponent<CanopyFader>();
            var fso = new SerializedObject(fader);
            fso.FindProperty("crowns").objectReferenceValue = crownMap;
            fso.ApplyModifiedPropertiesWithoutUndo();

            // ---------- Baumstamm: alt, dick, voller Aeste, versperrt den Weg komplett
            var logSprite = AssetDatabase.LoadAssetAtPath<Sprite>(EnvDir + "/Baumstamm_Alt.png");
            var logEmpty = AssetDatabase.LoadAssetAtPath<Sprite>(EnvDir + "/Baumstamm_Alt_Leer.png");
            var logGo = new GameObject("Baumstamm");
            logGo.transform.SetParent(root.transform);
            logGo.transform.position = new Vector3(RoadX, LogY, 0f);
            var logSr = logGo.AddComponent<SpriteRenderer>();
            logSr.sprite = logSprite;
            logSr.sortingOrder = OrderObjects;
            if (lit != null) logSr.sharedMaterial = lit;
            var logBox = logGo.AddComponent<BoxCollider2D>();
            logBox.size = new Vector2(11f, 0.9f);
            logBox.offset = new Vector2(0f, 0.55f);
            // Nur der Zettel am Stamm laesst sich untersuchen (er sitzt in der Mitte, x = 0, rund 1,6 Units ueber dem Boden)
            var logInteract = Interactable(logGo.transform, "Untersuchen", new Vector3(0f, -0.3f, 0f), "Interact", 2.3f, 1.1f);
            var logExtra = new OpeningInteractable[0];
            var ravensGo = new GameObject("Raben");
            ravensGo.transform.SetParent(logGo.transform, false);
            var ravens = ravensGo.AddComponent<Ravens>();

            // ---------- Auto: alter Sedan in 3/4-Ansicht, animiert
            var carGo = new GameObject("Auto");
            carGo.transform.position = new Vector3(RoadX, -6f, 0f);
            var carBody = carGo.AddComponent<Rigidbody2D>();
            carBody.gravityScale = 0f;
            carBody.mass = 50f;
            carBody.freezeRotation = true;
            carBody.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            var carBox = carGo.AddComponent<BoxCollider2D>();
            carBox.size = new Vector2(1.3f, 1.2f);
            carBox.offset = new Vector2(0f, -0.1f);
            var car = carGo.AddComponent<CarController>();
            var carDoor = Interactable(carGo.transform, "Fahrertuer", new Vector3(-0.9f, 0f, 0f), "Get in", 1.2f);
            var visGo = new GameObject("Visual");
            visGo.transform.SetParent(carGo.transform, false);
            var carSr = visGo.AddComponent<SpriteRenderer>();
            carSr.sortingOrder = OrderObjects;
            if (lit != null) carSr.sharedMaterial = lit;
            var carVis = visGo.AddComponent<CarVisual>();
            var heads = new List<Transform>();
            foreach (var (name, x) in new[] { ("Scheinwerfer_L", -0.3f), ("Scheinwerfer_R", 0.3f) })
            {
                var pivot = new GameObject(name + "_Dreh").transform;
                pivot.SetParent(carGo.transform, false);
                var l = MakeLight(pivot, name, Vector3.zero, new Color(1f, 0.86f, 0.55f), 0.5f, 2.6f);
                l.transform.localPosition = new Vector3(x, 0.8f, 0f);
                l.pointLightInnerAngle = 40f;
                l.pointLightOuterAngle = 70f;
                heads.Add(pivot);
            }
            CarArt.Apply(carGo);   // Pickup (8 Richtungen), Kollision, Scheinwerfer

            // ---------- Spieler
            var player = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(PlayerPrefab));
            player.transform.position = new Vector3(RoadX, -6f, 0f);
            foreach (var sr in player.GetComponentsInChildren<SpriteRenderer>()) sr.sortingOrder = OrderObjects;
            var combat = player.GetComponent<Player.PlayerCombat>();
            if (combat != null) combat.enabled = false; // im Opening wird nicht gekaempft
            // Im Opening gemuetlicher laufen als im Rest des Spiels (nur diese Instanz, nicht das Prefab)
            var pcSo = new SerializedObject(player.GetComponent<Player.PlayerController>());
            pcSo.FindProperty("moveSpeed").floatValue = 1.3f;
            pcSo.ApplyModifiedPropertiesWithoutUndo();
            var interactor = player.GetComponent<PlayerInteractor>();
            var playerAnimator = player.GetComponentInChildren<Animator>();
            if (player.GetComponent<PlayerActionAnimation>() == null) player.AddComponent<PlayerActionAnimation>();

            var cso = new SerializedObject(follow);
            cso.FindProperty("target").objectReferenceValue = player.transform;
            cso.FindProperty("boundsMin").vector2Value = new Vector2(MinX + 1, MinY + 1);
            cso.FindProperty("boundsMax").vector2Value = new Vector2(MaxX, MaxY);
            cso.ApplyModifiedPropertiesWithoutUndo();

            // ---------- Figuren im Dorf
            var people = new GameObject("Dorf_Figuren").transform;
            var grave = new Vector2(7.5f, -48.6f);
            var graveFocus = new GameObject("Grab_Blickpunkt").transform;
            graveFocus.SetParent(people);
            graveFocus.position = grave;
            var crowd = new List<CrowdMember>();
            var crowdSpots = new (string prefab, Vector2 pos)[]
            {
                ("NPC_Ilhan_Bartender", new Vector2(6.0f, -46.8f)),
                ("NPC_Gast", new Vector2(9.0f, -46.9f)),
                ("NPC_Hausfrau", new Vector2(10.1f, -48.4f)),
                ("NPC_Hausfrau", new Vector2(5.0f, -50.2f)),        // Frau mit Tuch
                ("NPC_Gast", new Vector2(9.9f, -50.3f)),
                ("NPC_Hausfrau", new Vector2(6.8f, -51.6f)),
                ("NPC_Ilhan_Bartender", new Vector2(8.6f, -51.7f)),
            };
            foreach (var (prefab, pos) in crowdSpots)
            {
                var m = Npc(prefab, people, pos, mourner: true);
                var cm = m.AddComponent<CrowdMember>();
                cm.SetRest(graveFocus);
                crowd.Add(cm);
            }
            var mother = Npc("NPC_Hausfrau", people, new Vector2(4.1f, -48.3f), mourner: true);
            mother.name = "Mutter";
            var boy = Npc("NPC_Gast", people, new Vector2(4.8f, -48.9f), mourner: true);
            boy.name = "Junge";
            boy.transform.localScale = Vector3.one * 0.72f;
            foreach (var go in new[] { mother, boy }) { var cm = go.AddComponent<CrowdMember>(); cm.SetRest(graveFocus); crowd.Add(cm); }
            var bulut = Npc("NPC_Bulut_Sheriff", people, new Vector2(7.5f, -46.4f), mourner: false);
            var manAtDoorGo = Npc("NPC_Gast", people, manDoor, mourner: false);
            manAtDoorGo.name = "Mann_an_der_Tuer";

            // ---------- Tag und Nacht, Dialog-UI
            DayNightSetup.Setup();
            DialogueSetup.RebuildUI();
            var view = Object.FindAnyObjectByType<DialogueView>();

            // ---------- Opening-System
            var sys = new GameObject("Opening");
            var audio = sys.AddComponent<OpeningAudio>();
            var dialogue = sys.AddComponent<ScriptedDialogue>();
            var dso = new SerializedObject(dialogue);
            dso.FindProperty("view").objectReferenceValue = view;
            dso.FindProperty("audioPlayer").objectReferenceValue = audio;
            var ex = dso.FindProperty("expressions");
            // Bulut guckt ernst, nicht traurig: "tense" und "cold" zeigen beide das ernste Gesicht (worried hat die Mundwinkel unten)
            var exprs = new[] { ("tense", "bulut_stern.png"), ("cold", "bulut_stern.png"), ("suspicious", "bulut_skeptical.png"), ("angry", "bulut_angry.png") };
            ex.arraySize = exprs.Length;
            for (int i = 0; i < exprs.Length; i++)
            {
                var e = ex.GetArrayElementAtIndex(i);
                e.FindPropertyRelative("tag").stringValue = exprs[i].Item1;
                e.FindPropertyRelative("sprite").objectReferenceValue = PortraitSprite(BulutPortraits + exprs[i].Item2);
            }
            dso.ApplyModifiedPropertiesWithoutUndo();

            var aso = new SerializedObject(car);
            aso.FindProperty("audioPlayer").objectReferenceValue = audio;
            aso.ApplyModifiedPropertiesWithoutUndo();

            // Raben: sitzen auf den Aesten und dem Moos, drei kreisen darueber
            var rso = new SerializedObject(ravens);
            SetSprites(rso, "flyFrames", Frames(EnvDir + "/Rabe_Flug.png"));
            SetSprites(rso, "sitFrames", Frames(EnvDir + "/Rabe_Sitzt.png"));
            var perch = rso.FindProperty("perches");
            var perches = new[] { new Vector2(-1.8f, 3.15f), new Vector2(2.05f, 2.85f), new Vector2(-0.8f, 2.1f), new Vector2(3.6f, 2.1f) };
            perch.arraySize = perches.Length;
            for (int i = 0; i < perches.Length; i++) perch.GetArrayElementAtIndex(i).vector2Value = perches[i];
            rso.FindProperty("audioPlayer").objectReferenceValue = audio;
            rso.FindProperty("material").objectReferenceValue = lit;
            rso.ApplyModifiedPropertiesWithoutUndo();

            var ui = BuildUI(interactor, womanCtrl, manCtrl, audio, out var select, out var questHud, out var prompt);

            var director = sys.AddComponent<OpeningDirector>();
            var so = new SerializedObject(director);
            void Set(string prop, Object value) { var sp = so.FindProperty(prop); if (sp != null) sp.objectReferenceValue = value; }   // Felder des alten Dorfablaufs gibt es nicht mehr
            Set("ui", ui);
            Set("characterSelect", select);
            Set("questHud", questHud);
            Set("prompt", prompt);
            Set("audioPlayer", audio);
            Set("dialogue", dialogue);
            Set("player", interactor);
            Set("playerAnimator", playerAnimator);
            Set("womanController", womanCtrl);
            Set("manController", manCtrl);
            Set("car", car);
            Set("carDoor", carDoor);
            so.FindProperty("roadX").floatValue = RoadX;
            Set("logRoot", logGo);
            Set("logInteract", logInteract);
            var le = so.FindProperty("logExtra");
            le.arraySize = logExtra.Length;
            for (int i = 0; i < logExtra.Length; i++) le.GetArrayElementAtIndex(i).objectReferenceValue = logExtra[i];
            Set("logRenderer", logSr);
            Set("logWithoutPaper", logEmpty);
            Set("ravens", ravens);
            Set("boy", boy.GetComponent<NpcMover>());
            Set("mother", mother.GetComponent<NpcMover>());
            Set("manAtDoor", manAtDoorGo);
            Set("graveFocus", graveFocus);
            Set("bulut", bulut.GetComponent<NpcMover>());
            Set("bulutProfile", AssetDatabase.LoadAssetAtPath<NpcProfile>("Assets/_Project/Data/NPCs/NpcProfile_bulut.asset"));
            Set("stationDoor", revierDoor);
            Set("lantern", lantern);
            Set("houseLights", houses);
            so.ApplyModifiedPropertiesWithoutUndo();

            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.SaveScene(scene, ScenePath);
            AddToBuildSettings();
            Debug.Log("[Opening] Szene gebaut: " + ScenePath + " (Baeume mit Kollision: " + trunkFeet.Count + ")");
        }

        // ------------------------------------------------------------------ Assets

        static void ImportArt()
        {
            SliceRow(VehDir + "/Auto_Rauch.png", 10, 32, new Vector2(0.5f, 0.5f));
            CarArt.SliceSheet();
            SliceRow(EnvDir + "/Rabe_Flug.png", 18, 32, new Vector2(0.5f, 0.5f));
            SliceRow(EnvDir + "/Rabe_Sitzt.png", 14, 32, new Vector2(0.5f, 0f));
            SpriteImport(EnvDir + "/Baumstamm_Alt.png", 32, new Vector2(0.5f, 0f));
            SpriteImport(EnvDir + "/Baumstamm_Alt_Leer.png", 32, new Vector2(0.5f, 0f));
            SpriteImport(EnvDir + "/Grab_Offen.png", 32, new Vector2(0.27f, 0f));
            SpriteImport(QuestIcon, 100, new Vector2(0.5f, 0.5f));
            SpriteImport(UiDir + "/Sprechblase.png", 100, new Vector2(0.5f, 0.5f), new Vector4(6, 6, 6, 6));
            SpriteImport(UiDir + "/Sprechblase_Spitze.png", 100, new Vector2(0.5f, 1f));
            SpriteImport(UiDir + "/Tacho.png", 100, new Vector2(0.5f, 0f));
            SpriteImport(UiDir + "/Tacho_Nadel.png", 100, new Vector2(0.5f, 0f));
            SpriteImport(UiDir + "/Zettel_Liste.png", 100, new Vector2(0.5f, 0.5f));
        }

        /// <summary>Waagrechter Streifen gleich breiter Frames (ganze Hoehe), z. B. Auto_Sedan_N.png.</summary>
        static void SliceRow(string path, int frameWidth, float ppu, Vector2 pivot)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            if (ti == null) { Debug.LogError("[Opening] fehlt: " + path); return; }
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = ppu;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
            var metas = new List<SpriteMetaData>();
            string baseName = Path.GetFileNameWithoutExtension(path);
            for (int i = 0; i < tw / frameWidth; i++)
                metas.Add(new SpriteMetaData
                {
                    name = baseName + "_" + i,
                    rect = new Rect(i * frameWidth, 0, frameWidth, th),
                    alignment = (int)SpriteAlignment.Custom,
                    pivot = pivot,
                });
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();
        }

        static Sprite[] Frames(string path)
        {
            var list = new List<Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path)) if (o is Sprite sp) list.Add(sp);
            list.Sort((a, b) => NameIndex(a.name).CompareTo(NameIndex(b.name)));
            return list.ToArray();
        }

        static int NameIndex(string n) { int i = n.LastIndexOf('_'); return i >= 0 && int.TryParse(n.Substring(i + 1), out int v) ? v : 0; }

        static void SetSprites(SerializedObject so, string prop, Sprite[] sprites)
        {
            var p = so.FindProperty(prop);
            p.arraySize = sprites.Length;
            for (int i = 0; i < sprites.Length; i++) p.GetArrayElementAtIndex(i).objectReferenceValue = sprites[i];
        }

        /// <summary>Hocken und Tuefteln (interact_RICHTUNG) im Animator der Hauptfigur, 4 Frames je Richtung.
        /// Wiederverwendbar fuer alle Aktionen (PlayerActionAnimation.Play("interact", ...)).</summary>
        static void AddInteractStates(RuntimeAnimatorController rc, string animFolder, string sheet)
        {
            var ctrl = rc as AnimatorController;
            if (ctrl == null) return;
            string path = "Assets/_Project/Art/Characters/" + sheet;
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            if (ti == null) { Debug.LogError("[Opening] fehlt: " + path); return; }
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = 32;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            // Pivot wie bei idle/walk, damit die Figur beim Wechsel nicht springt
            var idle = StateSprite(ctrl, "idle_S");
            Vector2 pivot = idle != null ? new Vector2(idle.pivot.x / idle.rect.width, idle.pivot.y / idle.rect.height) : new Vector2(0.5f, 0.1f);
            string[] rows = { "S", "SW", "W", "NW", "N", "NE", "E", "SE" };
            ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
            const int cell = 56;
            var metas = new List<SpriteMetaData>();
            for (int r = 0; r < rows.Length; r++)
                for (int c = 0; c < tw / cell; c++)
                    metas.Add(new SpriteMetaData
                    {
                        name = "interact_" + rows[r] + "_" + c,
                        rect = new Rect(c * cell, th - (r + 1) * cell, cell, cell),
                        alignment = (int)SpriteAlignment.Custom,
                        pivot = pivot,
                    });
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();

            var all = new Dictionary<string, Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path)) if (o is Sprite sp) all[sp.name] = sp;
            var sm = ctrl.layers[0].stateMachine;
            string dir = "Assets/_Project/Art/Animations/" + animFolder + "/";
            foreach (var d in rows)
            {
                string name = "interact_" + d;
                foreach (var st in sm.states) if (st.state.name == name) { sm.RemoveState(st.state); break; }
                AssetDatabase.DeleteAsset(dir + name + ".anim");
                var clip = new AnimationClip { frameRate = 6f, name = name };
                var keys = new List<ObjectReferenceKeyframe>();
                for (int c = 0; c < 4; c++)
                    if (all.TryGetValue("interact_" + d + "_" + c, out var sp)) keys.Add(new ObjectReferenceKeyframe { time = c / 6f, value = sp });
                if (keys.Count == 0) continue;
                keys.Add(new ObjectReferenceKeyframe { time = keys.Count / 6f, value = keys[keys.Count - 1].value });
                AnimationUtility.SetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite"), keys.ToArray());
                var settings = AnimationUtility.GetAnimationClipSettings(clip);
                settings.loopTime = true;
                AnimationUtility.SetAnimationClipSettings(clip, settings);
                AssetDatabase.CreateAsset(clip, dir + name + ".anim");
                sm.AddState(name).motion = clip;
            }
            EditorUtility.SetDirty(ctrl);
            AssetDatabase.SaveAssets();
        }

        /// <summary>Spielfigur langsamer, passend zur Laufanimation (gilt global: Werte im Player-Prefab).</summary>
        static void TunePlayerSpeed()
        {
            var root = PrefabUtility.LoadPrefabContents(PlayerPrefab);
            try
            {
                var pc = root.GetComponent<Player.PlayerController>();
                var so = new SerializedObject(pc);
                so.FindProperty("moveSpeed").floatValue = 1.55f;
                so.FindProperty("animationReferenceSpeed").floatValue = 1.55f;
                so.FindProperty("acceleration").floatValue = 12f;
                so.FindProperty("deceleration").floatValue = 16f;
                so.ApplyModifiedPropertiesWithoutUndo();
                PrefabUtility.SaveAsPrefabAsset(root, PlayerPrefab);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
        }

        static void SpriteImport(string path, float ppu, Vector2 pivot, Vector4 border = default)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            if (ti == null) { Debug.LogError("[Opening] fehlt: " + path); return; }
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Single;
            ti.spritePixelsPerUnit = ppu;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            var s = new TextureImporterSettings();
            ti.ReadTextureSettings(s);
            s.spriteAlignment = (int)SpriteAlignment.Custom;
            s.spritePivot = pivot;
            s.spriteMeshType = SpriteMeshType.FullRect;
            ti.SetTextureSettings(s);
            ti.spriteBorder = border;
            ti.SaveAndReimport();
        }

        static Sprite PortraitSprite(string path)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            if (ti == null) return null;
            if (ti.textureType != TextureImporterType.Sprite || ti.spritePixelsPerUnit != 100 || ti.filterMode != FilterMode.Point)
            {
                ti.textureType = TextureImporterType.Sprite;
                ti.spriteImportMode = SpriteImportMode.Single;
                ti.spritePixelsPerUnit = 100;
                ti.filterMode = FilterMode.Point;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                ti.mipmapEnabled = false;
                ti.alphaIsTransparency = true;
                ti.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }

        /// <summary>Animator fuer die Hauptfigur Mann, gleiche Bauweise wie Frau und NPCs (idle/walk in 8 Richtungen).</summary>
        static RuntimeAnimatorController BuildManController() =>
            NpcCastBuilder.Controller("Hauptfigur_Mann", new[]
            {
                new NpcCastBuilder.Clip("idle", "Hauptfiguren/Mann/mann_idle.png", 56, 6, true),
                new NpcCastBuilder.Clip("walk", "Hauptfiguren/Mann/mann_walk.png", 56, 10, true),
            });

        static Sprite StateSprite(RuntimeAnimatorController rc, string state)
        {
            var ctrl = rc as AnimatorController;
            if (ctrl == null) return null;
            foreach (var st in ctrl.layers[0].stateMachine.states)
            {
                if (st.state.name != state || !(st.state.motion is AnimationClip clip)) continue;
                var keys = AnimationUtility.GetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite"));
                return keys.Length > 0 ? (Sprite)keys[0].value : null;
            }
            return null;
        }

        static void AddToBuildSettings()
        {
            var list = new List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
            if (list.Exists(s => s.path == ScenePath)) return;
            list.Add(new EditorBuildSettingsScene(ScenePath, true));
            EditorBuildSettings.scenes = list.ToArray();
        }

        // ------------------------------------------------------------------ Terrain

        static bool InMap(int x, int y) => x >= MinX && x <= MaxX && y >= MinY && y <= MaxY;
        static Ter GetT(int x, int y) => InMap(x, y) ? ter[x - MinX, y - MinY] : Ter.Grass;
        static void SetT(int x, int y, Ter t) { if (InMap(x, y)) ter[x - MinX, y - MinY] = t; }
        static bool Occ(int x, int y) => !InMap(x, y) || occ[x - MinX, y - MinY];
        static void Reserve(int x0, int y0, int x1, int y1)
        {
            for (int x = x0; x <= x1; x++) for (int y = y0; y <= y1; y++) if (InMap(x, y)) occ[x - MinX, y - MinY] = true;
        }

        static void BuildTerrain()
        {
            ter = new Ter[MaxX - MinX + 1, MaxY - MinY + 1];
            // Dichter, dunkler Wald direkt neben der Strasse: nur ein Grasstreifen pro Seite bleibt frei
            for (int y = ForestStartY; y <= MaxY; y++)
            {
                int edgeL = -3 - (Mathf.PerlinNoise(y * 0.2f, 1.3f) > 0.7f ? 1 : 0);
                int edgeR = 3 + (Mathf.PerlinNoise(y * 0.2f, 7.1f) > 0.7f ? 1 : 0);
                for (int x = MinX; x <= MaxX; x++)
                    if (x <= edgeL || x >= edgeR) SetT(x, y, Ter.Forest);
            }
            for (int y = ForestStartY - 3; y < ForestStartY; y++)
                for (int x = MinX; x <= MaxX; x++)
                    if ((x <= -12 || x >= 14) && rng.NextDouble() < 0.6) SetT(x, y, Ter.Forest);
            // Hinter dem Stamm: Wald schliesst die Strasse
            for (int y = RoadEndY + 2; y <= MaxY; y++)
                for (int x = MinX; x <= MaxX; x++) SetT(x, y, Ter.Forest);
            // Landstrasse: gerade, keine Abzweigung
            for (int y = MinY; y <= RoadEndY; y++)
                for (int x = -1; x <= 1; x++) SetT(x, y, Ter.Dirt);
            // Dorfplatz (festgetretene Erde) oestlich der Strasse, Ecken abgerundet
            for (int x = 2; x <= 13; x++)
                for (int y = -53; y <= -41; y++)
                {
                    bool corner = (x >= 12 && y <= -52) || (x >= 12 && y >= -42) || (x == 13 && (y == -51 || y == -43));
                    if (!corner) SetT(x, y, Ter.Dirt);
                }
            // Trampelpfade zu Revier und Kapelle
            for (int y = -40; y >= -41; y--) { SetT(5, y, Ter.Dirt); SetT(6, y, Ter.Dirt); }
            for (int x = 14; x <= 18; x++) SetT(x, -47, Ter.Dirt);
        }

        static bool Conn(Ter me, Ter n)
        {
            switch (me)
            {
                case Ter.Dirt: case Ter.Cobble: return n == Ter.Dirt || n == Ter.Cobble;
                default: return n == me;
            }
        }

        static TileBase LoadTerrain(int r, int c) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Terrain/T_{r}_{c}.asset");
        static TileBase LoadWald(int r, int c) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Wald/W_{r}_{c}.asset");
        static TileBase LoadUebergang(int r, int c) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Uebergang/U_{r}_{c}.asset");
        static TileBase ObjTile(string name) => AssetDatabase.LoadAssetAtPath<TileBase>($"{TileAssets}/Objekte/{name}.asset");

        static TileBase TerrainTile(int x, int y)
        {
            var t = GetT(x, y);
            if (t == Ter.Grass) return LoadTerrain(4, rng.NextDouble() < 0.55 ? 0 : 1 + rng.Next(7));
            bool n = Conn(t, GetT(x, y + 1)), e = Conn(t, GetT(x + 1, y)), s = Conn(t, GetT(x, y - 1)), w = Conn(t, GetT(x - 1, y));
            int idx = (n ? 1 : 0) | (e ? 2 : 0) | (s ? 4 : 0) | (w ? 8 : 0);
            bool ne = Conn(t, GetT(x + 1, y + 1)), se = Conn(t, GetT(x + 1, y - 1)), sw = Conn(t, GetT(x - 1, y - 1)), nw = Conn(t, GetT(x - 1, y + 1));
            int corner = idx != 15 ? -1 : !ne ? 16 : !se ? 17 : !sw ? 18 : !nw ? 19 : -1;
            if (t == Ter.Forest)
            {
                // Tileset_Uebergang Zeile 1 = Wald dunkel (Kante zum Gras), Zeile 4 Spalte 4-7 = Fuellung dunkel
                if (idx != 15) return LoadUebergang(1, idx) ?? LoadWald(1, idx);
                if (corner >= 0) return LoadUebergang(1, corner) ?? LoadWald(1, corner);
                return LoadUebergang(4, 4 + rng.Next(4)) ?? LoadWald(2, 0);
            }
            int row = t == Ter.Dirt ? 0 : 1;
            if (idx != 15) return LoadTerrain(row, idx);
            if (corner >= 0) return LoadTerrain(row, corner);
            return t == Ter.Dirt ? LoadTerrain(4, 8 + rng.Next(3)) : LoadTerrain(4, 11 + rng.Next(2));
        }

        static void Deco(Tilemap deco)
        {
            for (int x = MinX; x <= MaxX; x++)
                for (int y = MinY; y <= MaxY; y++)
                {
                    if (Occ(x, y)) continue;
                    var t = GetT(x, y);
                    double d = rng.NextDouble();
                    TileBase tile = null;
                    if (t == Ter.Grass)
                    {
                        if (d < 0.05) tile = LoadTerrain(5, rng.Next(6));          // Blumen
                        else if (d < 0.16) tile = LoadTerrain(5, 6 + rng.Next(3)); // Grasbueschel
                        else if (d < 0.19) tile = LoadTerrain(5, 19);              // Klee
                    }
                    else if (t == Ter.Forest)
                    {
                        if (d < 0.2) tile = LoadWald(3, rng.Next(19));
                        else if (d < 0.3) tile = LoadWald(4, rng.Next(14));
                    }
                    else if (t == Ter.Dirt && d < 0.05) tile = LoadTerrain(5, 11 + rng.Next(3)); // Kiesel
                    if (tile != null) deco.SetTile(new Vector3Int(x, y, 0), tile);
                }
        }

        // ------------------------------------------------------------------ Wald

        static readonly string[] TreeNames =
            { "Fichte_Hoch_A", "Fichte_Hoch_B", "Fichte_Hoch_C", "Kiefer_A", "Kiefer_B", "Birke_A", "Birke_B", "Birke_C", "Eiche_A", "Eiche_B", "Fichte_Jung" };

        static int SpriteWidth(string name)
        {
            var t = ObjTile(name) as Tile;
            return t != null && t.sprite != null ? Mathf.RoundToInt(t.sprite.rect.width) : 0;
        }

        static bool PutTree(string name, int x, int y)
        {
            int px = SpriteWidth(name);
            if (px == 0) return false;
            int cells = Mathf.CeilToInt(px / 32f);
            for (int i = 0; i < cells; i++)
                for (int j = 0; j < 2; j++)
                {
                    if (Occ(x + i, y + j)) return false;
                    var t = GetT(x + i, y + j);
                    if (t == Ter.Dirt || t == Ter.Cobble) return false;
                }
            Reserve(x, y, x + cells - 1, y + 1);
            bool split = ObjTile(name + "_Stamm") != null && ObjTile(name + "_Krone") != null;
            var cell = new Vector3Int(x, y, 0);
            objMap.SetTile(cell, ObjTile(split ? name + "_Stamm" : name));
            if (split) crownMap.SetTile(cell, ObjTile(name + "_Krone"));
            trunkFeet.Add(new Vector2(x + px / 64f, y + 0.3f));
            return true;
        }

        static void PutObject(string name, int x, int y, bool blocks)
        {
            var tile = ObjTile(name);
            if (tile == null) { Debug.LogWarning("[Opening] Objekt fehlt: " + name); return; }
            int cells = Mathf.Max(1, Mathf.CeilToInt(SpriteWidth(name) / 32f));
            for (int i = 0; i < cells; i++) if (Occ(x + i, y)) return;
            Reserve(x, y, x + cells - 1, y);
            objMap.SetTile(new Vector3Int(x, y, 0), tile);
            if (blocks) for (int i = 0; i < cells; i++) solid[x + i - MinX, y - MinY] = true;
        }

        static readonly string[] DarkBushes = { "Busch_Dunkel_A", "Busch_Dunkel_B", "Busch_Dunkel_C", "Busch_Dunkel", "Farn_Dicht", "Farn_Dunkel", "Grasbusch_Dunkel" };

        /// <summary>Baum ohne Belegungspruefung (darf andere Baeume ueberlappen), nur nicht auf Strasse/Grasstreifen.</summary>
        static void PutTreeDense(string name, int x, int y)
        {
            int px = SpriteWidth(name);
            if (px == 0) return;
            int cells = Mathf.CeilToInt(px / 32f);
            for (int i = 0; i < cells; i++)
            {
                int cx = x + i;
                if (cx >= -2 && cx <= 2 && y <= RoadEndY + 1) return;
                if (!InMap(cx, y)) return;
            }
            Reserve(x, y, x + cells - 1, y + 1);
            bool split = ObjTile(name + "_Stamm") != null && ObjTile(name + "_Krone") != null;
            var cell = new Vector3Int(x, y, 0);
            objMap.SetTile(cell, ObjTile(split ? name + "_Stamm" : name));
            if (split) crownMap.SetTile(cell, ObjTile(name + "_Krone"));
            // Keine Stamm-Kollision: der Waldrand ist ohnehin eine Wand (spart tausende Collider)
        }

        static void PlaceForest()
        {
            // Dichter Wald: Raster alle 2 Zellen mit Versatz, Baeume ueberlappen sich. Vorne normale, hinten dunkle Fern-Baeume.
            // Kein Durchkommen (Kollision am Waldrand) und kein Durchblick.
            for (int y = ForestStartY - 2; y <= MaxY - 1; y++)
            {
                int offset = (y & 1) == 0 ? 0 : 1;
                for (int x = MinX + offset; x <= MaxX - 1; x += 2)
                {
                    int dist = x < 0 ? -x : x - 1;
                    if (y < ForestStartY && dist < 11) continue;
                    // Vor dem Stamm frei lassen, damit man ihn ganz sieht
                    if (y >= LogY - 5 && y <= LogY && x >= -6 && x <= 6) continue;
                    if (rng.NextDouble() < 0.18) continue;
                    int jx = x + (rng.NextDouble() < 0.3 ? (rng.NextDouble() < 0.5 ? -1 : 1) : 0);
                    string name = TreeNames[rng.Next(TreeNames.Length)];
                    if ((dist > 5 || y > RoadEndY) && rng.NextDouble() < 0.55 && ObjTile(name + "_Fern") != null) name += "_Fern";
                    PutTreeDense(name, jx, y);
                }
            }
            // Dichtes, dunkles Unterholz direkt am Waldrand
            for (int y = ForestStartY; y <= MaxY - 1; y++)
                foreach (int x in new[] { -4, -3, 3, 4 })
                {
                    if (y >= LogY - 1 && y <= LogY + 1) continue;
                    var tile = ObjTile(DarkBushes[rng.Next(DarkBushes.Length)]);
                    if (tile != null && objMap.GetTile(new Vector3Int(x, y, 0)) == null && rng.NextDouble() < 0.8) objMap.SetTile(new Vector3Int(x, y, 0), tile);
                }
            // Am Grasstreifen vereinzelt Farn und Pilze
            for (int y = ForestStartY; y <= RoadEndY; y++)
                foreach (int x in new[] { -2, 2 })
                    if (rng.NextDouble() < 0.05 && (y < LogY - 4 || y > LogY + 1)) PutObject(rng.NextDouble() < 0.5 ? "Farn_A" : "Baumstumpf_Pilze", x, y, false);
        }

        // ------------------------------------------------------------------ Dorf

        static Transform PlaceVillage(Transform grid, out Transform revierDoor, out Vector2 manDoor, out Transform lantern)
        {
            var housesRoot = new GameObject("Dorf_Haeuser").transform;
            housesRoot.SetParent(grid, false);
            Transform House(string name, int x, int y, string label = null)
            {
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(HouseDir + "Haus_" + name + "_Aussen.prefab");
                var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, housesRoot);
                go.transform.position = new Vector3(x, y, 0f);
                if (label != null) go.name = label;
                var box = go.GetComponent<BoxCollider2D>();
                int wCells = box != null ? Mathf.CeilToInt(box.size.x) : 6;
                Reserve(x - 1, y - 2, x + wCells, y + 5);
                return go.transform;
            }
            var fachwerk = House("Fachwerkhaus", -9, -31);
            House("Bauernkate", -8, -43);
            House("Kraemerladen", -10, -55);
            House("Schmiede", -9, -67);
            var revier = House("Fischerhuette", 3, -37, "Revier");
            House("Kapelle", 15, -37);
            House("Baeckerei", 4, -62);
            House("Schneiderei", 13, -62);

            revierDoor = Door(revier, "Revier_Tuer");
            var fd = Door(fachwerk, "Fachwerk_Tuer");
            manDoor = fd.position;

            // Laterne am Platz, Bulut steht in Szene 4 darunter
            PutObject("Laterne", 2, -43, true);
            var lightsRoot = new GameObject("Platz_Lichter").transform;
            lightsRoot.SetParent(housesRoot, false);
            MakeLight(lightsRoot, "Laterne_Licht", new Vector3(2.5f, -41.4f, 0f), new Color(1f, 0.8f, 0.45f), 0.9f, 4f);
            lantern = new GameObject("Laterne_Punkt").transform;
            lantern.SetParent(housesRoot, false);
            lantern.position = new Vector3(2.9f, -42.2f, 0f);

            // Frisches Grab mitten auf dem Platz (liegt flach auf dem Boden)
            var graveGo = new GameObject("Grab_Frisch");
            graveGo.transform.SetParent(housesRoot, false);
            graveGo.transform.position = new Vector3(7.0f, -49.9f, 0f);
            graveGo.transform.localScale = Vector3.one * 1.25f;
            var gsr = graveGo.AddComponent<SpriteRenderer>();
            gsr.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(EnvDir + "/Grab_Offen.png");
            gsr.sortingOrder = OrderDeco + 1;
            var lit = AssetDatabase.LoadAssetAtPath<Material>(LitMaterial);
            if (lit != null) gsr.sharedMaterial = lit;
            var gbox = graveGo.AddComponent<BoxCollider2D>();
            gbox.size = new Vector2(0.8f, 1.4f);
            gbox.offset = new Vector2(0.03f, 0.8f);
            // Baeume und Buesche am Dorfrand
            string[] trees = { "Eiche_A", "Eiche_B", "Eiche_Apfel", "Birke_A", "Birke_B", "Kiefer_A" };
            for (int y = -86; y <= ForestStartY - 1; y++)
                for (int x = MinX; x <= MaxX - 1; x++)
                {
                    bool edge = x <= -15 || x >= 23 || y <= -80;
                    if (rng.NextDouble() < (edge ? 0.14 : 0.012)) PutTree(trees[rng.Next(trees.Length)], x, y);
                }
            Reserve(5, -51, 10, -47);

            // Ein paar Grabsteine als Orientierung (Friedhof neben der Kapelle)
            string[] stones = { "Grabstein_A", "Grabstein_B", "Grabstein_C" };
            var spots = new[] { (17, -42), (19, -42), (21, -42), (16, -45), (18, -45), (20, -45), (22, -45), (17, -48), (20, -48), (18, -51) };
            foreach (var (x, y) in spots) PutObject(stones[rng.Next(stones.Length)], x, y, true);
            // Dorfdeko
            PutObject("Wegweiser", 2, -24, true);
            PutObject("Bank", 11, -41, true);
            PutObject("Fass", -3, -33, true);
            PutObject("Holzstapel_Klein", -2, -66, true);
            return housesRoot;
        }

        static Transform Door(Transform house, string name)
        {
            Vector3 pos = house.position + new Vector3(2f, -0.6f, 0f);
            foreach (Transform t in house.GetComponentsInChildren<Transform>())
                if (t.name.StartsWith("Eingang")) { pos = t.position + new Vector3(0f, -0.7f, 0f); break; }
            var go = new GameObject(name);
            go.transform.SetParent(house.parent, false);
            go.transform.position = pos;
            return go.transform;
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
                    // Im Wald: nur ein Streifen links und rechts der Strasse ist begehbar
                    if (y >= ForestStartY && (x <= -3 || x >= 3)) s = true;
                    // Hinter dem Stamm geht es nicht weiter
                    if (y >= LogY + 2) s = true;
                    if (s) colMap.SetTile(new Vector3Int(x, y, 0), block);
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

        // ------------------------------------------------------------------ Figuren und Objekte

        static GameObject Npc(string prefab, Transform parent, Vector2 pos, bool mourner)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(NpcDir + prefab + ".prefab"), parent);
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.transform.position = pos;
            // Gesteuert vom OpeningDirector: kein eigenes Verhalten, keine alten Dialoge, keine Monster-Enthuellung
            foreach (var b in go.GetComponents<NpcBehavior>()) Object.DestroyImmediate(b);
            foreach (var d in go.GetComponents<NpcDialogue>()) Object.DestroyImmediate(d);
            var monster = go.GetComponent<MonsterNpc>();
            if (monster != null) Object.DestroyImmediate(monster);
            var brain = go.GetComponent<NpcBrain>();
            if (brain != null) Object.DestroyImmediate(brain);
            var indicator = go.transform.Find("Interaktion");
            if (indicator != null) Object.DestroyImmediate(indicator.gameObject);
            go.AddComponent<ScriptedWalker>();
            foreach (var sr in go.GetComponentsInChildren<SpriteRenderer>())
            {
                sr.sortingOrder = OrderObjects;
                if (mourner) sr.color = new Color(0.5f, 0.47f, 0.58f); // dunkle Kleidung
            }
            return go;
        }

        static OpeningInteractable Interactable(Transform parent, string name, Vector3 local, string promptText, float indicatorHeight, float reach = 0f)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = local;
            var it = go.AddComponent<OpeningInteractable>();
            var so = new SerializedObject(it);
            so.FindProperty("prompt").stringValue = promptText;
            so.FindProperty("indicatorHeight").floatValue = indicatorHeight;
            so.FindProperty("reach").floatValue = reach;
            so.FindProperty("key").enumValueIndex = (int)InteractKey.F;
            so.ApplyModifiedPropertiesWithoutUndo();
            return it;
        }

        static Light2D MakeLight(Transform parent, string name, Vector3 pos, Color col, float intensity, float radius)
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
            return l;
        }

        // ------------------------------------------------------------------ UI

        static Font font, hand;
        static Sprite panel;
        static readonly Color Ink = new Color32(0x2b, 0x21, 0x40, 0xff);

        static RectTransform RT(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        static RectTransform Place(RectTransform rt, Vector2 anchor, Vector2 pivot, Vector2 pos, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = pivot;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            return rt;
        }

        static Text Txt(RectTransform rt, int size, Color color, TextAnchor align, bool shadow = true, Font f = null)
        {
            var t = rt.gameObject.AddComponent<Text>();
            t.font = f != null ? f : font;
            t.fontSize = size;
            t.color = color;
            t.alignment = align;
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            t.supportRichText = false;
            if (shadow)
            {
                var sh = rt.gameObject.AddComponent<Shadow>();
                sh.effectColor = new Color(0f, 0f, 0f, 0.8f);
                sh.effectDistance = new Vector2(1f, -1f);
            }
            return t;
        }

        static Image Img(RectTransform rt, Color color, bool sliced = false)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.color = color;
            img.raycastTarget = false;
            if (sliced) { img.sprite = panel; img.type = Image.Type.Sliced; }
            return img;
        }

        /// <summary>Dunkle, fast deckende Tafel mit Rahmen: Text darauf ist vor jedem Hintergrund lesbar.</summary>
        static RectTransform Plate(RectTransform parent, string name, Vector2 anchor, Vector2 pivot, Vector2 pos, Vector2 size)
        {
            var rt = Place(RT(name, parent), anchor, pivot, pos, size);
            var bg = RT("Grund", rt);
            Stretch(bg);
            bg.offsetMin = new Vector2(2f, 2f);
            bg.offsetMax = new Vector2(-2f, -2f);
            Img(bg, new Color(NwTheme.TextShadow.r, NwTheme.TextShadow.g, NwTheme.TextShadow.b, 0.94f));
            var frame = RT("Rahmen", rt);
            Stretch(frame);
            Img(frame, Color.white, true);
            return rt;
        }

        static Canvas MakeCanvas(string name, int order)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var c = go.GetComponent<Canvas>();
            c.renderMode = RenderMode.ScreenSpaceOverlay;
            c.sortingOrder = order;
            c.pixelPerfect = true;
            var sc = go.GetComponent<CanvasScaler>();
            sc.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            sc.referenceResolution = new Vector2(480, 270);
            sc.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            sc.matchWidthOrHeight = 0.5f;
            sc.referencePixelsPerUnit = 100;
            return c;
        }

        static CanvasGroup Group(RectTransform rt)
        {
            var g = rt.gameObject.AddComponent<CanvasGroup>();
            g.blocksRaycasts = false;
            return g;
        }

        static NwButton Button(RectTransform parent, string label, Vector2 anchor, Vector2 pos, float width = 96f)
        {
            var go = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(ButtonPrefab), parent);
            var rt = (RectTransform)go.transform;
            Place(rt, anchor, new Vector2(0.5f, 0.5f), pos, new Vector2(width, 24f));
            var b = go.GetComponent<NwButton>();
            b.Label.text = label;
            b.Label.font = font;
            b.Label.fontSize = 11;
            return b;
        }

        static OpeningUI BuildUI(PlayerInteractor interactor, RuntimeAnimatorController woman, RuntimeAnimatorController man, OpeningAudio audio,
                                 out CharacterSelect select, out QuestHud questHud, out InteractPrompt prompt)
        {
            font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);
            hand = AssetDatabase.LoadAssetAtPath<Font>(HandFont);
            panel = AssetDatabase.LoadAssetAtPath<Sprite>(PanelSprite);
            var dark = NwTheme.TextShadow;
            var c0 = MakeCanvas("UI_Opening", 100);
            var top = MakeCanvas("UI_Uebergang", 200);
            var c = (RectTransform)c0.transform;

            // Hintergrund fuer Szenen ohne Karte (Station innen)
            var backdrop = RT("Hintergrund", c);
            Stretch(backdrop);
            Img(backdrop, dark);

            // Tacho unten links: klein und fein, darunter der Kilometerstand
            var gauge = Place(RT("Tacho", c), Vector2.zero, Vector2.zero, new Vector2(8f, 8f), new Vector2(54f, 40f));
            var gaugeImg = Place(RT("Skala", gauge), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), Vector2.zero, new Vector2(44f, 26f));
            var gi = gaugeImg.gameObject.AddComponent<Image>();
            gi.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(UiDir + "/Tacho.png");
            gi.raycastTarget = false;
            var needle = Place(RT("Nadel", gaugeImg), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 3f), new Vector2(2f, 16f));
            var ni = needle.gameObject.AddComponent<Image>();
            ni.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(UiDir + "/Tacho_Nadel.png");
            ni.raycastTarget = false;
            needle.localRotation = Quaternion.Euler(0f, 0f, 80f);
            var odoText = Txt(Place(RT("Kilometer", gauge), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 0f), new Vector2(64f, 12f)),
                              7, NwTheme.TextDefault, TextAnchor.MiddleCenter);

            // Quest-HUD oben rechts
            var hudRoot = Plate(c, "Quest_HUD", Vector2.one, Vector2.one, new Vector2(-6f, -6f), new Vector2(170f, 58f));
            var icon = Place(RT("Symbol", hudRoot), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(7f, -7f), new Vector2(16f, 16f));
            var iconImg = icon.gameObject.AddComponent<Image>();
            iconImg.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(QuestIcon);
            iconImg.raycastTarget = false;
            Txt(Place(RT("Main_Titel", hudRoot), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(28f, -5f), new Vector2(138f, 11f)),
                9, NwTheme.Title, TextAnchor.UpperLeft).text = "Main Quest";
            var mainText = Txt(Place(RT("Main_Text", hudRoot), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(28f, -16f), new Vector2(138f, 14f)),
                               9, NwTheme.TextDefault, TextAnchor.UpperLeft);
            Txt(Place(RT("Side_Titel", hudRoot), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(28f, -31f), new Vector2(138f, 11f)),
                9, NwTheme.Title, TextAnchor.UpperLeft).text = "Side Quests";
            var sideText = Txt(Place(RT("Side_Text", hudRoot), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(28f, -42f), new Vector2(138f, 12f)),
                               9, new Color(0.75f, 0.72f, 0.8f), TextAnchor.UpperLeft);

            // Uebersicht (Q)
            var overview = Plate(c, "Quest_Uebersicht", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(260f, 170f));
            var ovText = Txt(Place(RT("Text", overview), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0f, 6f), new Vector2(232f, 140f)),
                             10, NwTheme.TextDefault, TextAnchor.UpperLeft);
            Txt(Place(RT("Hinweis", overview), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 8f), new Vector2(232f, 12f)),
                9, NwTheme.Title, TextAnchor.MiddleCenter).text = "Q / Esc – Close";

            // Pause (Esc)
            var pause = Plate(c, "Pause", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(160f, 110f));
            Txt(Place(RT("Titel", pause), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, -10f), new Vector2(140f, 20f)),
                14, NwTheme.Title, TextAnchor.MiddleCenter).text = "Paused";
            var resume = Button(pause, "Resume", new Vector2(0.5f, 0.5f), new Vector2(0f, 2f));
            var quit = Button(pause, "Quit", new Vector2(0.5f, 0.5f), new Vector2(0f, -28f));

            // Erzaehler / Gedanken: unten, dunkle Tafel, gut lesbar
            var sub = Plate(c, "Erzaehler", new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 8f), new Vector2(380f, 40f));
            var subGroup = Group(sub);
            var subText = Txt(Place(RT("Text", sub), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(360f, 34f)),
                              11, NwTheme.Narrator, TextAnchor.MiddleCenter);

            // Hinweis oben (Tutorial, Fund): unter dem Quest-HUD (das ist 58 hoch), damit sich beide nicht ueberlappen
            var toast = Plate(c, "Hinweis", new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, -72f), new Vector2(230f, 26f));
            var toastGroup = Group(toast);
            var toastText = Txt(Place(RT("Text", toast), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(220f, 22f)),
                                12, NwTheme.TextDefault, TextAnchor.MiddleCenter);

            // Sprechblase (folgt der Figur)
            var bubble = Place(RT("Sprechblase", c), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0f), Vector2.zero, new Vector2(100f, 20f));
            var bImg = bubble.gameObject.AddComponent<Image>();
            bImg.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(UiDir + "/Sprechblase.png");
            bImg.type = Image.Type.Sliced;
            bImg.raycastTarget = false;
            var tip = Place(RT("Spitze", bubble), new Vector2(0.5f, 0f), new Vector2(0.5f, 1f), new Vector2(0f, 2f), new Vector2(10f, 7f));
            var tipImg = tip.gameObject.AddComponent<Image>();
            tipImg.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(UiDir + "/Sprechblase_Spitze.png");
            tipImg.raycastTarget = false;
            var bubbleText = Txt(RT("Text", bubble), 9, Ink, TextAnchor.MiddleCenter, false);
            Stretch(bubbleText.rectTransform);
            bubbleText.rectTransform.offsetMin = new Vector2(6f, 2f);
            bubbleText.rectTransform.offsetMax = new Vector2(-6f, -2f);
            bubbleText.horizontalOverflow = HorizontalWrapMode.Overflow;

            // Fortschritt ueber der Figur
            var prog = Place(RT("Fortschritt", c), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0f), Vector2.zero, new Vector2(70f, 22f));
            var progLabel = Txt(Place(RT("Text", prog), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), Vector2.zero, new Vector2(90f, 12f)),
                                9, NwTheme.TextDefault, TextAnchor.MiddleCenter);
            Img(Place(RT("Rahmen", prog), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), Vector2.zero, new Vector2(52f, 7f)), dark);
            var fillRt = Place(RT("Fuellung", prog), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 1f), new Vector2(50f, 5f));
            var fill = Img(fillRt, NwTheme.Title);
            fill.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(Art + "/VFX/Pixel.png");
            fill.type = Image.Type.Filled;
            fill.fillMethod = Image.FillMethod.Horizontal;

            // Der Zettel: oben ein sauberer Hinweis, dann nur das Papier mit Handschrift, darunter der Button
            var paper = RT("Zettel", c);
            Stretch(paper);
            var paperGroup = Group(paper);
            Img(paper, new Color(0f, 0f, 0f, 0.55f));
            Txt(Place(RT("Ueberschrift", paper), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0f), new Vector2(0f, 92f), new Vector2(300f, 16f)),
                12, NwTheme.Title, TextAnchor.MiddleCenter).text = "A torn list, handwritten";
            var paperImg = Place(RT("Papier", paper), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0f, 4f), new Vector2(150f, 172f));
            var pi = paperImg.gameObject.AddComponent<Image>();
            pi.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(UiDir + "/Zettel_Liste.png");
            pi.raycastTarget = false;
            var paperText = Txt(Place(RT("Namen", paperImg), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(8f, 4f), new Vector2(126f, 140f)),
                                15, Ink, TextAnchor.UpperLeft, false, hand);
            paperText.lineSpacing = 1.15f;
            var closeButton = Button(paper, "Close  [F]", new Vector2(0.5f, 0.5f), new Vector2(0f, -102f), 110f);

            // Eingabeaufforderung am Objekt
            var promptRoot = Plate(c, "Eingabeaufforderung", new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0f), Vector2.zero, new Vector2(80f, 18f));
            var promptText = Txt(RT("Text", promptRoot), 9, NwTheme.TextDefault, TextAnchor.MiddleCenter);
            Stretch(promptText.rectTransform);
            promptText.horizontalOverflow = HorizontalWrapMode.Overflow;

            // Intro (Step 2)
            var intro = RT("Intro", c);
            Stretch(intro);
            var introGroup = Group(intro);
            Img(intro, NwTheme.TextShadow); // #1a1526
            var introLine = Txt(Place(RT("Zeile", intro), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(400f, 60f)),
                                14, NwTheme.Narrator, TextAnchor.MiddleCenter, false);
            var introTitle = Txt(Place(RT("Titel", intro), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(440f, 70f)),
                                 40, NwTheme.Title, TextAnchor.MiddleCenter, false);

            // Charakterwahl (Step 1)
            var sel = RT("Charakterwahl", c);
            Stretch(sel);
            var selGroup = Group(sel);
            Img(sel, NwTheme.TextShadow);
            Txt(Place(RT("Titel", sel), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, -20f), new Vector2(400f, 24f)),
                18, NwTheme.Title, TextAnchor.MiddleCenter).text = "Who are you?";
            (Image frame, NwButton button) Card(string label, Vector2 pos, RuntimeAnimatorController ctrl)
            {
                var card = Place(RT("Karte_" + label, sel), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), pos, new Vector2(120f, 150f));
                var frame = Img(card, NwTheme.ButtonTextDisabled, true);
                frame.raycastTarget = true;
                var portrait = Place(RT("Portraet", card), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, -8f), new Vector2(76f, 76f));
                var pimg = Img(portrait, Color.white);
                pimg.sprite = StateSprite(ctrl, "idle_S");
                pimg.preserveAspect = true;
                Txt(Place(RT("Name", card), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 40f), new Vector2(110f, 18f)),
                    13, NwTheme.TextDefault, TextAnchor.MiddleCenter).text = label;
                var b = Button(card, "Choose", new Vector2(0.5f, 0f), new Vector2(0f, 16f), 88f);
                return (frame, b);
            }
            var (womanFrame, womanButton) = Card("Woman", new Vector2(-75f, 0f), woman);   // Protagonistin
            var (manFrame, manButton) = Card("Man", new Vector2(75f, 0f), man);           // Protagonist
            Txt(Place(RT("Hinweis", sel), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 12f), new Vector2(400f, 14f)),
                10, new Color(0.8f, 0.77f, 0.85f), TextAnchor.MiddleCenter).text = "Click or press Enter. This choice is final.";

            // Ueberblendung und Endkarte (ueber allem, auch ueber dem Dialog)
            var tc = (RectTransform)top.transform;
            var fadeRt = RT("Schwarz", tc);
            Stretch(fadeRt);
            var fade = Img(fadeRt, Color.black);
            var end = RT("Ende", tc);
            Stretch(end);
            var endGroup = Group(end);
            var endText = Txt(Place(RT("Text", end), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(400f, 40f)),
                              20, NwTheme.Title, TextAnchor.MiddleCenter, false);

            // Komponenten verdrahten
            var ui = c0.gameObject.AddComponent<OpeningUI>();
            var so = new SerializedObject(ui);
            void S(string p, Object v) => so.FindProperty(p).objectReferenceValue = v;
            S("audioPlayer", audio);
            S("fade", fade);
            S("backdrop", backdrop.gameObject);
            S("introPanel", introGroup);
            S("introLine", introLine);
            S("introTitle", introTitle);
            S("subtitleGroup", subGroup);
            S("subtitle", subText);
            S("toastGroup", toastGroup);
            S("toast", toastText);
            S("bubble", bubble);
            S("bubbleText", bubbleText);
            S("progressRoot", prog);
            S("progressFill", fill);
            S("progressLabel", progLabel);
            S("paperGroup", paperGroup);
            S("paperText", paperText);
            S("paperClose", closeButton);
            S("gaugeRoot", gauge.gameObject);
            S("needle", needle);
            S("odometerText", odoText);
            S("endGroup", endGroup);
            S("endText", endText);
            so.ApplyModifiedPropertiesWithoutUndo();

            select = c0.gameObject.AddComponent<CharacterSelect>();
            var sso = new SerializedObject(select);
            sso.FindProperty("group").objectReferenceValue = selGroup;
            sso.FindProperty("womanButton").objectReferenceValue = womanButton;
            sso.FindProperty("manButton").objectReferenceValue = manButton;
            sso.FindProperty("womanFrame").objectReferenceValue = womanFrame;
            sso.FindProperty("manFrame").objectReferenceValue = manFrame;
            sso.ApplyModifiedPropertiesWithoutUndo();
            sel.gameObject.SetActive(false);

            questHud = c0.gameObject.AddComponent<QuestHud>();
            var qso = new SerializedObject(questHud);
            qso.FindProperty("hudRoot").objectReferenceValue = hudRoot.gameObject;
            qso.FindProperty("mainText").objectReferenceValue = mainText;
            qso.FindProperty("sideText").objectReferenceValue = sideText;
            qso.FindProperty("overview").objectReferenceValue = overview.gameObject;
            qso.FindProperty("overviewText").objectReferenceValue = ovText;
            qso.FindProperty("pauseMenu").objectReferenceValue = pause.gameObject;
            qso.FindProperty("resumeButton").objectReferenceValue = resume;
            qso.FindProperty("quitButton").objectReferenceValue = quit;
            qso.ApplyModifiedPropertiesWithoutUndo();

            prompt = c0.gameObject.AddComponent<InteractPrompt>();
            var pso = new SerializedObject(prompt);
            pso.FindProperty("box").objectReferenceValue = promptRoot;
            pso.FindProperty("label").objectReferenceValue = promptText;
            pso.FindProperty("player").objectReferenceValue = interactor;
            pso.ApplyModifiedPropertiesWithoutUndo();

            return ui;
        }
    }
}
