using System.Collections.Generic;
using Nightward.DayNight;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Tilemaps;
using UnityEngine.UI;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Richtet den Tag-/Nachtzyklus in der offenen Szene ein: Uhr, Licht-Verlauf, Nacht-Volume (Bloom, Vignette),
    /// Lampen und Fenster, Gluehwuermchen, Motten, Schornsteinrauch, Bodennebel, 2D-Schatten und HUD-Symbol.
    /// Kann mehrfach ausgefuehrt werden: die erzeugten Objekte werden ersetzt, Einstellungen an Lichtern ueberschrieben.
    /// </summary>
    public static class DayNightSetup
    {
        const string Art = "Assets/_Project/Art";
        const string VfxDir = Art + "/VFX";
        const string IconDir = Art + "/UI/Icons";
        const string SettingsDir = "Assets/_Project/Resources"; // Resources, damit DayNightBootstrap das Profil in jeder Szene laden kann
        const string TA = Art + "/Tiles/TileAssets/Haus";

        [MenuItem("Nightward/Tag und Nacht/In Szene einrichten")]
        public static void Setup()
        {
            ConfigureImports();
            var unlit = MakeMaterial(VfxDir + "/Mat_Partikel_Unlit.mat", "Universal Render Pipeline/2D/Sprite-Unlit-Default");
            var lit = MakeMaterial(VfxDir + "/Mat_Partikel_Lit.mat", "Universal Render Pipeline/2D/Sprite-Lit-Default");
            var profile = MakeNightProfile();

            var old = GameObject.Find("Tag_Nacht");
            if (old != null) Object.DestroyImmediate(old);
            var root = new GameObject("Tag_Nacht");
            root.AddComponent<DayNightCycle>();
            var lighting = root.AddComponent<DayNightLighting>();

            var volGo = new GameObject("Nacht_Volume");
            volGo.transform.SetParent(root.transform, false);
            var volume = volGo.AddComponent<Volume>();
            volume.isGlobal = true;
            volume.sharedProfile = profile;
            volume.weight = 0f;

            var global = FindGlobalLight();
            var so = new SerializedObject(lighting);
            so.FindProperty("globalLight").objectReferenceValue = global;
            so.FindProperty("nightVolume").objectReferenceValue = volume;
            so.ApplyModifiedPropertiesWithoutUndo();

            var cam = Camera.main;
            if (cam != null) cam.GetComponent<UniversalAdditionalCameraData>().renderPostProcessing = true;

            SetupLamps();
            SetupHouses();

            var fx = new GameObject("Partikel");
            fx.transform.SetParent(root.transform, false);
            SetupFireflies(fx.transform, unlit);
            SetupMoths(fx.transform, unlit);
            SetupChimneySmoke(fx.transform, lit);
            SetupFog(root.transform);
            SetupShadows();
            SetupHud();

            EditorSceneManager.MarkSceneDirty(root.scene);
            AssetDatabase.SaveAssets();
            Debug.Log("[Tag/Nacht] eingerichtet.");
        }

        // ------------------------------------------------------------------ Assets
        static void ConfigureImports()
        {
            AssetDatabase.Refresh();
            Sprite(IconDir + "/Icon_Sonne.png", 16, SpriteMeshType.FullRect, TextureWrapMode.Clamp);
            Sprite(IconDir + "/Icon_Mond.png", 16, SpriteMeshType.FullRect, TextureWrapMode.Clamp);
            // Nebel bewusst weich gefiltert und grob aufgeloest: wirkt als Dunst, nicht als Pixelmuster
            Sprite(VfxDir + "/Nebel.png", 8, SpriteMeshType.FullRect, TextureWrapMode.Repeat, FilterMode.Bilinear);
            Sprite(VfxDir + "/Pixel.png", 32, SpriteMeshType.FullRect, TextureWrapMode.Clamp);
        }

        static void Sprite(string path, int ppu, SpriteMeshType mesh, TextureWrapMode wrap, FilterMode filter = FilterMode.Point)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Single;
            ti.spritePixelsPerUnit = ppu;
            ti.filterMode = filter;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.wrapMode = wrap;
            var s = new TextureImporterSettings();
            ti.ReadTextureSettings(s);
            s.spriteMeshType = mesh;
            ti.SetTextureSettings(s);
            ti.SaveAndReimport();
        }

        static Material MakeMaterial(string path, string shader)
        {
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                m = new Material(Shader.Find(shader));
                AssetDatabase.CreateAsset(m, path);
            }
            m.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(VfxDir + "/Pixel.png");
            EditorUtility.SetDirty(m);
            return m;
        }

        static VolumeProfile MakeNightProfile()
        {
            if (!AssetDatabase.IsValidFolder(SettingsDir)) AssetDatabase.CreateFolder("Assets/_Project", "Resources");
            string path = SettingsDir + "/Volume_Nacht.asset";
            var p = AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
            if (p == null)
            {
                p = ScriptableObject.CreateInstance<VolumeProfile>();
                AssetDatabase.CreateAsset(p, path);
            }

            var bloom = Get<Bloom>(p);
            bloom.threshold.Override(0.85f);
            bloom.intensity.Override(1.4f);
            bloom.scatter.Override(0.65f);
            bloom.tint.Override(new Color(1f, 0.9f, 0.75f));

            var vig = Get<Vignette>(p);
            vig.intensity.Override(0.45f);
            vig.smoothness.Override(0.55f);
            vig.color.Override(new Color(26 / 255f, 21 / 255f, 38 / 255f)); // #1a1526

            var ca = Get<ColorAdjustments>(p);
            ca.saturation.Override(-25f);
            ca.contrast.Override(15f);
            ca.colorFilter.Override(new Color(0.85f, 0.88f, 1f)); // kalter Stich, Lichtquellen bleiben warm

            EditorUtility.SetDirty(p);
            return p;
        }

        static T Get<T>(VolumeProfile p) where T : VolumeComponent
        {
            if (p.TryGet<T>(out var c)) return c;
            c = p.Add<T>(true);
            c.name = typeof(T).Name;
            AssetDatabase.AddObjectToAsset(c, p);
            return c;
        }

        static Light2D FindGlobalLight()
        {
            foreach (var l in Object.FindObjectsByType<Light2D>())
                if (l.lightType == Light2D.LightType.Global) return l;
            return null;
        }

        // ------------------------------------------------------------------ Lichter
        static NightLight Night(Light2D l, bool auto, Vector2 range, float dayLevel, float flicker, float fade)
        {
            var nl = l.GetComponent<NightLight>();
            if (nl == null) nl = l.gameObject.AddComponent<NightLight>();
            var so = new SerializedObject(nl);
            so.FindProperty("autoSwitch").boolValue = auto;
            so.FindProperty("switchOnRange").vector2Value = range;
            so.FindProperty("dayLevel").floatValue = dayLevel;
            so.FindProperty("flicker").floatValue = flicker;
            so.FindProperty("fadeTime").floatValue = fade;
            so.ApplyModifiedPropertiesWithoutUndo();
            return nl;
        }

        static void SetupLamps()
        {
            foreach (var l in Object.FindObjectsByType<Light2D>())
            {
                if (l.name.StartsWith("Laternen_Licht"))
                {
                    // heller als frueher, damit die Lichtinseln gegen die dunkle Nacht stehen
                    l.intensity = 1f;
                    l.pointLightOuterRadius = 3.8f;
                    Night(l, true, new Vector2(0.15f, 0.55f), 0f, 0.05f, 1.2f);
                }
                else if (l.name.StartsWith("Lagerfeuer_Licht")) Night(l, true, new Vector2(0.05f, 0.1f), 0.3f, 0.15f, 2f);
            }
        }

        static void SetupHouses()
        {
            // dunkel <-> beleuchtet laut LIESMICH_Haus (Fenster Fachwerk/Holz/Stein oben+unten, Dachfenster)
            var pairs = new List<(string dark, string lit)>
            {
                ("H_3_10", "H_3_9"), ("H_4_10", "H_4_9"),
                ("H_3_13", "H_3_12"), ("H_4_13", "H_4_12"),
                ("H_3_15", "H_3_14"), ("H_4_15", "H_4_14"),
                ("H_0_12", "H_0_11"),
            };
            var windowLights = new List<Light2D>();
            foreach (var l in Object.FindObjectsByType<Light2D>())
                if (l.name.StartsWith("Haus_01_Fensterlicht")) windowLights.Add(l);

            var haus = GameObject.Find("Haus_01");
            if (haus == null) return;
            var hl = haus.GetComponent<HouseLights>();
            if (hl == null) hl = haus.AddComponent<HouseLights>();
            var so = new SerializedObject(hl);
            var sw = so.FindProperty("swaps");
            sw.arraySize = pairs.Count;
            for (int i = 0; i < pairs.Count; i++)
            {
                var e = sw.GetArrayElementAtIndex(i);
                e.FindPropertyRelative("dark").objectReferenceValue = AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/{pairs[i].dark}.asset");
                e.FindPropertyRelative("lit").objectReferenceValue = AssetDatabase.LoadAssetAtPath<TileBase>($"{TA}/{pairs[i].lit}.asset");
            }
            var wl = so.FindProperty("windowLights");
            wl.arraySize = windowLights.Count;
            for (int i = 0; i < windowLights.Count; i++)
            {
                // Lichtschein soll vor das Haus auf den Boden fallen
                windowLights[i].intensity = 0.7f;
                windowLights[i].pointLightOuterRadius = 2.4f;
                windowLights[i].pointLightInnerRadius = 0.3f;
                wl.GetArrayElementAtIndex(i).objectReferenceValue = Night(windowLights[i], false, Vector2.zero, 0f, 0.04f, 0.8f);
            }
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        // ------------------------------------------------------------------ Partikel
        static ParticleSystem MakePs(string name, Transform parent, Vector3 pos, Material mat, int maxParticles)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.loop = true;
            main.playOnAwake = true;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = maxParticles;
            main.gravityModifier = 0f;
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = mat;
            r.sortingLayerName = "Default";
            r.sortingOrder = 21; // ueber den Baumkronen
            return ps;
        }

        static Gradient Alpha(params (float t, float a)[] keys)
        {
            var g = new Gradient();
            var ak = new GradientAlphaKey[keys.Length];
            for (int i = 0; i < keys.Length; i++) ak[i] = new GradientAlphaKey(keys[i].a, keys[i].t);
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) }, ak);
            return g;
        }

        static Color Hex(string h) { ColorUtility.TryParseHtmlString("#" + h, out var c); return c; }

        static void Rate(ParticleSystem ps, float maxRate, float startAt)
        {
            var np = ps.gameObject.AddComponent<NightParticles>();
            var so = new SerializedObject(np);
            so.FindProperty("maxRate").floatValue = maxRate;
            so.FindProperty("startAt").floatValue = startAt;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static void SetupFireflies(Transform parent, Material mat)
        {
            // Wiesen und Wasser, wo Gluehwuermchen glaubwuerdig sind
            var areas = new[]
            {
                (new Vector3(5f, 25f, 0f), new Vector2(9f, 6f)),
                (new Vector3(16f, 7f, 0f), new Vector2(12f, 4f)),
                (new Vector3(44f, 10f, 0f), new Vector2(6f, 4f)),
                (new Vector3(38f, 24f, 0f), new Vector2(8f, 5f)),
                (new Vector3(14f, 20f, 0f), new Vector2(6f, 4f)),
            };
            int i = 0;
            foreach (var (pos, size) in areas)
            {
                var ps = MakePs("Gluehwuermchen_" + (++i), parent, pos, mat, 60);
                var main = ps.main;
                main.startLifetime = new ParticleSystem.MinMaxCurve(5f, 8f);
                main.startSpeed = new ParticleSystem.MinMaxCurve(0.05f, 0.2f);
                main.startSize = 1f / 16f; // 2 Pixel
                main.startColor = new ParticleSystem.MinMaxGradient(Hex("ffd27a"), Hex("9ab87a"));
                var shape = ps.shape;
                shape.shapeType = ParticleSystemShapeType.Box;
                shape.scale = new Vector3(size.x, size.y, 0.1f);
                var noise = ps.noise;
                noise.enabled = true;
                noise.strength = 0.25f;
                noise.frequency = 0.4f;
                noise.scrollSpeed = 0.2f;
                var col = ps.colorOverLifetime;
                col.enabled = true;
                col.color = Alpha((0f, 0f), (0.15f, 1f), (0.35f, 0.2f), (0.5f, 1f), (0.7f, 0.25f), (0.85f, 1f), (1f, 0f));
                var em = ps.emission;
                em.rateOverTime = 0f;
                Rate(ps, 6f, 0.45f);
            }
        }

        static void SetupMoths(Transform parent, Material mat)
        {
            int i = 0;
            foreach (var l in Object.FindObjectsByType<Light2D>())
            {
                if (!l.name.StartsWith("Laternen_Licht")) continue;
                var ps = MakePs("Motten_" + (++i), parent, l.transform.position + new Vector3(0f, 0.1f, 0f), mat, 6);
                var main = ps.main;
                main.simulationSpace = ParticleSystemSimulationSpace.Local;
                main.startLifetime = new ParticleSystem.MinMaxCurve(2f, 4f);
                main.startSpeed = new ParticleSystem.MinMaxCurve(0.1f, 0.3f);
                main.startSize = 1f / 16f;
                main.startColor = new ParticleSystem.MinMaxGradient(Hex("e8e0f0"), Hex("9a95a0"));
                var shape = ps.shape;
                shape.shapeType = ParticleSystemShapeType.Sphere;
                shape.radius = 0.3f;
                var noise = ps.noise;
                noise.enabled = true;
                noise.strength = 0.9f;
                noise.frequency = 2f;
                noise.scrollSpeed = 1f;
                var col = ps.colorOverLifetime;
                col.enabled = true;
                col.color = Alpha((0f, 0f), (0.1f, 1f), (0.9f, 1f), (1f, 0f));
                var em = ps.emission;
                em.rateOverTime = 0f;
                Rate(ps, 1.5f, 0.6f);
            }
        }

        static void SetupChimneySmoke(Transform parent, Material mat)
        {
            var smokeTop = AssetDatabase.LoadAssetAtPath<TileBase>(TA + "/H_0_10.asset");
            foreach (var tm in Object.FindObjectsByType<Tilemap>())
            {
                foreach (var pos in tm.cellBounds.allPositionsWithin)
                {
                    if (tm.GetTile(pos) != smokeTop) continue;
                    var world = tm.CellToWorld(pos) + new Vector3(0.5f, 0.85f, 0f);
                    var ps = MakePs("Schornsteinrauch", parent, world, mat, 30);
                    var main = ps.main;
                    main.startLifetime = new ParticleSystem.MinMaxCurve(3f, 4.5f);
                    main.startSpeed = 0f;
                    main.startSize = new ParticleSystem.MinMaxCurve(3f / 32f, 5f / 32f);
                    main.startColor = new ParticleSystem.MinMaxGradient(Hex("9a95a0"), Hex("6e6a74"));
                    var shape = ps.shape;
                    shape.shapeType = ParticleSystemShapeType.Sphere;
                    shape.radius = 0.05f;
                    var vel = ps.velocityOverLifetime;
                    vel.enabled = true;
                    vel.space = ParticleSystemSimulationSpace.World;
                    vel.x = new ParticleSystem.MinMaxCurve(0.05f, 0.12f); // leichter Wind
                    vel.y = new ParticleSystem.MinMaxCurve(0.3f, 0.4f);
                    vel.z = new ParticleSystem.MinMaxCurve(0f, 0f);
                    var size = ps.sizeOverLifetime;
                    size.enabled = true;
                    size.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 1f, 1f, 2f));
                    var noise = ps.noise;
                    noise.enabled = true;
                    noise.strength = 0.1f;
                    noise.frequency = 0.5f;
                    var col = ps.colorOverLifetime;
                    col.enabled = true;
                    col.color = Alpha((0f, 0f), (0.1f, 0.8f), (0.6f, 0.5f), (1f, 0f));
                    var em = ps.emission;
                    em.rateOverTime = 2.5f;
                }
            }
        }

        // ------------------------------------------------------------------ Nebel, Schatten, HUD
        static void SetupFog(Transform parent)
        {
            var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(VfxDir + "/Nebel.png");
            var ground = GameObject.Find("Ground").GetComponent<Tilemap>();
            ground.CompressBounds();
            var b = ground.localBounds;
            var layers = new[]
            {
                ("Nebel_A", new Vector2(0.15f, 0.03f), 0.35f, false),
                ("Nebel_B", new Vector2(-0.08f, 0.05f), 0.25f, true),
            };
            foreach (var (name, drift, alpha, flip) in layers)
            {
                var go = new GameObject(name);
                go.transform.SetParent(parent, false);
                // um eine Kachel nach links unten versetzt, damit beim Treiben kein Rand sichtbar wird
                go.transform.position = b.center - (Vector3)(Vector2)sprite.bounds.size;
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = sprite;
                sr.drawMode = SpriteDrawMode.Tiled;
                sr.size = (Vector2)b.size + 2f * (Vector2)sprite.bounds.size;
                sr.flipX = flip;
                sr.sortingLayerName = "Default";
                sr.sortingOrder = 3; // ueber Boden und Deko, unter Figuren und Objekten
                sr.color = new Color(1f, 1f, 1f, 0f);
                var fl = go.AddComponent<FogLayer>();
                var so = new SerializedObject(fl);
                so.FindProperty("drift").vector2Value = drift;
                so.FindProperty("maxAlpha").floatValue = alpha;
                so.ApplyModifiedPropertiesWithoutUndo();
            }
        }

        static void SetupShadows()
        {
            // Baumstaemme: Composite-Collider liefert die Form automatisch (Shape Provider)
            var trunks = GameObject.Find("TrunkColliders");
            if (trunks != null && trunks.GetComponent<ShadowCaster2D>() == null)
            {
                var sc = trunks.AddComponent<ShadowCaster2D>();
                sc.selfShadows = false;
            }
            // Haus: Grundflaeche als Trigger-Box (zaehlt nicht als Hindernis fuer NavGrid und Physik)
            var haus = GameObject.Find("Haus_01");
            if (haus != null && haus.transform.Find("Schattenwerfer") == null)
            {
                var go = new GameObject("Schattenwerfer");
                go.transform.SetParent(haus.transform, false);
                var box = go.AddComponent<BoxCollider2D>();
                box.isTrigger = true;
                box.size = new Vector2(5f, 2f);
                box.offset = new Vector2(2.5f, 1f);
                var sc = go.AddComponent<ShadowCaster2D>();
                sc.selfShadows = false;
            }
            foreach (var l in Object.FindObjectsByType<Light2D>())
                if (l.name.StartsWith("Laternen_Licht") || l.name.StartsWith("Lagerfeuer_Licht"))
                {
                    l.shadowsEnabled = true;
                    l.shadowIntensity = 0.7f;
                }
        }

        static void SetupHud()
        {
            var old = GameObject.Find("HUD");
            if (old != null) Object.DestroyImmediate(old);
            var canvasGo = new GameObject("HUD");
            var canvas = canvasGo.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 100;
            canvas.pixelPerfect = true;
            var scaler = canvasGo.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(640, 360);
            scaler.matchWidthOrHeight = 1f;

            var iconGo = new GameObject("Tageszeit");
            iconGo.transform.SetParent(canvasGo.transform, false);
            var rt = iconGo.AddComponent<RectTransform>();
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0f, 1f);
            rt.anchoredPosition = new Vector2(8f, -8f);
            rt.sizeDelta = new Vector2(16f, 16f);
            var img = iconGo.AddComponent<Image>();
            img.raycastTarget = false;
            var sun = AssetDatabase.LoadAssetAtPath<Sprite>(IconDir + "/Icon_Sonne.png");
            img.sprite = sun;

            var hud = canvasGo.AddComponent<DayNightHud>();
            var so = new SerializedObject(hud);
            so.FindProperty("icon").objectReferenceValue = img;
            so.FindProperty("sun").objectReferenceValue = sun;
            so.FindProperty("moon").objectReferenceValue = AssetDatabase.LoadAssetAtPath<Sprite>(IconDir + "/Icon_Mond.png");
            so.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
