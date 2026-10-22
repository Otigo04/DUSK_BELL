using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;
using Nightward.UI;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut den Titelbildschirm "Dusk Bell": Sprite-Import, Szene Scenes/Bootstrap/TitleScreen.unity und
    /// traegt die Szenen in die Build Settings ein (Titel zuerst). Grafiken: Art/UI/_Quelle_Generator/build_title.py
    /// Menue: Nightward > UI > Titelbildschirm bauen
    /// </summary>
    public static class TitleScreenBuilder
    {
        const string TitleDir = "Assets/_Project/Art/UI/Title";
        const string FontPath = "Assets/_Project/Art/UI/Font/Nightward_Pixel.ttf";
        const string ButtonPrefab = "Assets/_Project/Prefabs/UI/UI_Button.prefab";
        const string ScenePath = "Assets/_Project/Scenes/Bootstrap/TitleScreen.unity";
        const string GameScenePath = "Assets/_Project/Scenes/Game/Level_01.unity";

        static Font font;

        [MenuItem("Nightward/UI/Titelbildschirm bauen")]
        public static void Build()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            ConfigureImports();

            font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);
            var btnPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(ButtonPrefab);
            if (font == null || btnPrefab == null)
            {
                Debug.LogError("[Titel] Font oder UI_Button fehlt - erst 'Nightward > UI > Test-UI bauen (alles)' ausfuehren.");
                return;
            }

            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Exclude)) Object.DestroyImmediate(l.gameObject);
            var cam = Camera.main;
            if (cam != null)
            {
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = new Color32(0x1a, 0x15, 0x26, 255);
            }

            var canvasGo = new GameObject("UI_Canvas", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            canvasGo.GetComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(480, 270);   // wie die Spielkamera
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            scaler.referencePixelsPerUnit = 100;
            SetObj(canvasGo.AddComponent<NwUIRoot>(), "pixelFont", font);

            var es = new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
            es.GetComponent<InputSystemUIInputModule>().AssignDefaultActions();

            // Hintergrund und Sterne fuellen den Bildschirm (16:9 passt genau, sonst wird beschnitten)
            var bg = FullScreenSprite("Hintergrund", canvasGo.transform, "Title_Hintergrund.png");
            var starsA = FullScreenSprite("Sterne_A", canvasGo.transform, "Title_Sterne_A.png");
            var starsB = FullScreenSprite("Sterne_B", canvasGo.transform, "Title_Sterne_B.png");

            // Logo und Untertitel oben links
            var logoSprite = Spr("Title_Logo.png");
            var logo = NewRT("Logo", canvasGo.transform);
            Place(logo, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(16, -14),
                new Vector2(logoSprite.rect.width, logoSprite.rect.height));
            var logoImg = logo.gameObject.AddComponent<Image>();
            logoImg.sprite = logoSprite;
            logoImg.raycastTarget = false;

            var tag = NewRT("Untertitel", canvasGo.transform);
            Place(tag, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(22, -66), new Vector2(260, 12));
            var tagText = AddText(tag, NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.UpperLeft);
            tagText.text = "Wenn die Glocke läutet, verriegle die Tür.";

            // Menue
            var screenGo = new GameObject("TitelMenue");
            var screen = screenGo.AddComponent<NwTitleScreen>();
            var labels = new[] { "Neues Spiel", "Fortsetzen", "Optionen", "Beenden" };
            var actions = new UnityEngine.Events.UnityAction[] { screen.OnNewGame, screen.OnContinue, screen.OnOptions, screen.OnQuit };
            var buttons = new Object[labels.Length];
            for (int i = 0; i < labels.Length; i++)
            {
                var b = (GameObject)PrefabUtility.InstantiatePrefab(btnPrefab, canvasGo.transform);
                b.name = "Button_" + labels[i];
                var brt = (RectTransform)b.transform;
                Place(brt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(20, -90 - i * 28), new Vector2(140, 24));
                var nb = b.GetComponent<NwButton>();
                nb.Label.text = labels[i];
                UnityEventTools.AddPersistentListener(nb.onClick, actions[i]);
                PrefabUtility.RecordPrefabInstancePropertyModifications(brt);
                PrefabUtility.RecordPrefabInstancePropertyModifications(nb);
                PrefabUtility.RecordPrefabInstancePropertyModifications(nb.Label);
                buttons[i] = nb;
            }

            // Hinweiszeile und Version unten
            var hintRt = NewRT("Hinweis", canvasGo.transform);
            Place(hintRt, new Vector2(0, 0), new Vector2(0, 0), new Vector2(0, 0), new Vector2(20, 10), new Vector2(240, 12));
            var hintText = AddText(hintRt, NwTheme.FontHint, NwTheme.Warning, TextAnchor.LowerLeft);

            var verRt = NewRT("Version", canvasGo.transform);
            Place(verRt, new Vector2(1, 0), new Vector2(1, 0), new Vector2(1, 0), new Vector2(-8, 6), new Vector2(160, 12));
            var verText = AddText(verRt, NwTheme.FontHint, new Color32(0x6e, 0x6a, 0x74, 255), TextAnchor.LowerRight);
            verText.text = "v0.2.0 - Vertical Slice";

            // Ein-/Ausblenden (Nachtviolett #1a1526), liegt ganz oben
            var fadeRt = NewRT("Blende", canvasGo.transform);
            Stretch(fadeRt);
            var fadeImg = fadeRt.gameObject.AddComponent<Image>();
            fadeImg.color = new Color32(0x1a, 0x15, 0x26, 255);

            SetArray(screen, "buttons", buttons);
            SetObj(screen, "hint", hintText);
            SetObj(screen, "starsA", starsA);
            SetObj(screen, "starsB", starsB);
            SetObj(screen, "fade", fadeImg);
            var so = new SerializedObject(screen);
            so.FindProperty("gameScene").stringValue = "Opening";
            so.ApplyModifiedPropertiesWithoutUndo();

            EditorSceneManager.MarkSceneDirty(scene);
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.SaveScene(scene, ScenePath);
            RegisterBuildScenes();
            Debug.Log("[Titel] Titelbildschirm gebaut: " + ScenePath);
        }

        // ------------------------------------------------------------------ Import / Build Settings
        static void ConfigureImports()
        {
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { TitleDir }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                if (path.EndsWith("Title_Vorschau.png")) continue;   // nur zum Anschauen
                var ti = AssetImporter.GetAtPath(path) as TextureImporter;
                if (ti == null) continue;
                ti.textureType = TextureImporterType.Sprite;
                ti.spriteImportMode = SpriteImportMode.Single;
                ti.spritePixelsPerUnit = 100;
                ti.filterMode = FilterMode.Point;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                ti.mipmapEnabled = false;
                ti.alphaIsTransparency = true;
                ti.npotScale = TextureImporterNPOTScale.None;
                var s = new TextureImporterSettings();
                ti.ReadTextureSettings(s);
                s.spriteMeshType = SpriteMeshType.FullRect;
                ti.SetTextureSettings(s);
                ti.SaveAndReimport();
            }
        }

        static void RegisterBuildScenes()
        {
            var list = new List<EditorBuildSettingsScene> { new EditorBuildSettingsScene(ScenePath, true) };
            if (File.Exists(GameScenePath)) list.Add(new EditorBuildSettingsScene(GameScenePath, true));
            foreach (var s in EditorBuildSettings.scenes)
            {
                if (s.path == ScenePath || s.path == GameScenePath || !File.Exists(s.path)) continue;
                list.Add(s);
            }
            EditorBuildSettings.scenes = list.ToArray();
        }

        // ------------------------------------------------------------------ Helfer
        static Sprite Spr(string file) => AssetDatabase.LoadAssetAtPath<Sprite>(TitleDir + "/" + file);

        static RectTransform NewRT(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return go.GetComponent<RectTransform>();
        }

        static void Place(RectTransform rt, Vector2 anchorMin, Vector2 anchorMax, Vector2 pivot, Vector2 pos, Vector2 size)
        {
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.pivot = pivot;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
        }

        static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        static Image FullScreenSprite(string name, Transform parent, string file)
        {
            var rt = NewRT(name, parent);
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = new Vector2(480, 270);
            var fit = rt.gameObject.AddComponent<AspectRatioFitter>();
            fit.aspectMode = AspectRatioFitter.AspectMode.EnvelopeParent;
            fit.aspectRatio = 480f / 270f;
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = Spr(file);
            img.raycastTarget = false;
            return img;
        }

        static Text AddText(RectTransform rt, int size, Color color, TextAnchor anchor)
        {
            var t = rt.gameObject.AddComponent<Text>();
            t.font = font;
            t.fontSize = size;
            t.fontStyle = FontStyle.Normal;
            t.color = color;
            t.alignment = anchor;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.supportRichText = false;
            t.raycastTarget = false;
            var sh = rt.gameObject.AddComponent<Shadow>();
            sh.effectColor = NwTheme.TextShadow;
            sh.effectDistance = new Vector2(1, -1);   // 1 Pixel nach unten rechts
            return t;
        }

        static void SetObj(Object target, string field, Object value)
        {
            var so = new SerializedObject(target);
            var p = so.FindProperty(field);
            if (p == null) { Debug.LogError("Feld fehlt: " + target.GetType().Name + "." + field); return; }
            p.objectReferenceValue = value;
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static void SetArray(Object target, string field, Object[] values)
        {
            var so = new SerializedObject(target);
            var p = so.FindProperty(field);
            p.arraySize = values.Length;
            for (int i = 0; i < values.Length; i++) p.GetArrayElementAtIndex(i).objectReferenceValue = values[i];
            so.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
