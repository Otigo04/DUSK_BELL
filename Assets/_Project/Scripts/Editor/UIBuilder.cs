using System.IO;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;
using Nightward.DayNight;
using Nightward.UI;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut das Test-UI nach dem UI-Cheatsheet: Sprite-Import (Point, 9-Slice-Raender), Prefabs
    /// (Button, Dialogbox, HUD, Lagebericht) und die Szene UI_Test.
    /// Menue: Nightward > UI > Test-UI bauen (alles)
    /// </summary>
    public static class UIBuilder
    {
        const string ArtDir = "Assets/_Project/Art/UI";
        const string PrefabDir = "Assets/_Project/Prefabs/UI";
        const string ScenePath = "Assets/_Project/Scenes/Sandbox/UI_Test.unity";
        const string FontPath = ArtDir + "/Font/Nightward_Pixel.ttf";

        static Font font;

        [MenuItem("Nightward/UI/Test-UI bauen (alles)")]
        public static void BuildAll()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            ConfigureImports();
            BuildPrefabs();
            BuildScene();
            Debug.Log("[UI] Test-UI gebaut: " + ScenePath);
        }

        // ------------------------------------------------------------------ Import
        [MenuItem("Nightward/UI/1 Import konfigurieren")]
        public static void ConfigureImports()
        {
            AssetDatabase.Refresh();

            var fi = AssetImporter.GetAtPath(FontPath) as TrueTypeFontImporter;
            if (fi != null)
            {
                fi.fontTextureCase = FontTextureCase.Dynamic;
                fi.fontRenderingMode = FontRenderingMode.HintedRaster;   // keine Anti-Aliasing-Kanten
                fi.includeFontData = true;
                fi.SaveAndReimport();
            }

            foreach (var folder in new[] { "Icons", "Panels", "Buttons", "HUD" })
            {
                foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { ArtDir + "/" + folder }))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
                    var ti = AssetImporter.GetAtPath(path) as TextureImporter;
                    if (ti == null) continue;
                    ti.textureType = TextureImporterType.Sprite;
                    ti.spriteImportMode = SpriteImportMode.Single;
                    ti.spritePixelsPerUnit = 100;                  // 1 Pixel = 1 Canvas-Einheit (Reference PPU 100)
                    ti.filterMode = FilterMode.Point;
                    ti.textureCompression = TextureImporterCompression.Uncompressed;
                    ti.mipmapEnabled = false;
                    ti.alphaIsTransparency = true;
                    ti.npotScale = TextureImporterNPOTScale.None;
                    var s = new TextureImporterSettings();
                    ti.ReadTextureSettings(s);
                    s.spriteMeshType = SpriteMeshType.FullRect;
                    s.spriteAlignment = (int)SpriteAlignment.Center;
                    ti.SetTextureSettings(s);
                    // 9-Slice: Vector4(links, unten, rechts, oben)
                    if (folder == "Panels") ti.spriteBorder = new Vector4(8, 8, 8, 8);
                    else if (folder == "Buttons") ti.spriteBorder = new Vector4(8, 7, 8, 7);
                    else ti.spriteBorder = Vector4.zero;
                    ti.SaveAndReimport();
                }
            }
            AssetDatabase.Refresh();
        }

        // ------------------------------------------------------------------ Helfer
        static Sprite Spr(string rel) => AssetDatabase.LoadAssetAtPath<Sprite>(ArtDir + "/" + rel);

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

        static void Stretch(RectTransform rt, Vector2 offsetMin, Vector2 offsetMax)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = offsetMin;
            rt.offsetMax = offsetMax;
        }

        static Image AddImage(RectTransform rt, Sprite s, bool sliced)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = s;
            img.type = sliced ? Image.Type.Sliced : Image.Type.Simple;
            img.raycastTarget = sliced;
            img.pixelsPerUnitMultiplier = 1f;
            return img;
        }

        static Text AddText(RectTransform rt, int size, Color color, TextAnchor anchor, bool shadow = true)
        {
            var t = rt.gameObject.AddComponent<Text>();
            t.font = font;
            t.fontSize = size;
            t.fontStyle = FontStyle.Normal;
            t.color = color;
            t.alignment = anchor;
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.supportRichText = false;
            t.raycastTarget = false;
            t.lineSpacing = 1f;
            if (shadow)
            {
                var sh = rt.gameObject.AddComponent<Shadow>();
                sh.effectColor = NwTheme.TextShadow;
                sh.effectDistance = new Vector2(1, -1);   // 1 Pixel nach unten rechts
            }
            return t;
        }

        static void SetField(Object target, string field, object value)
        {
            var so = new SerializedObject(target);
            var p = so.FindProperty(field);
            if (p == null) { Debug.LogError("Feld fehlt: " + target.GetType().Name + "." + field); return; }
            switch (value)
            {
                case Object o: p.objectReferenceValue = o; break;
                case bool b: p.boolValue = b; break;
                case float f: p.floatValue = f; break;
                case int i: p.intValue = i; break;
                default: Debug.LogError("Typ nicht unterstuetzt: " + value); break;
            }
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

        static GameObject Save(GameObject root, string name)
        {
            Directory.CreateDirectory(PrefabDir);
            var path = $"{PrefabDir}/{name}.prefab";
            var prefab = PrefabUtility.SaveAsPrefabAsset(root, path);
            Object.DestroyImmediate(root);
            return prefab;
        }

        // ------------------------------------------------------------------ Prefabs
        public static void BuildPrefabs()
        {
            font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);
            if (font == null) { Debug.LogError("[UI] Font fehlt: " + FontPath); return; }

            // Prefabs in einer leeren Hilfsszene bauen, damit die geoeffnete Szene unberuehrt bleibt
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            BuildButton();
            BuildReportRow();
            BuildDialog();
            BuildHud();
            BuildReport();
            AssetDatabase.SaveAssets();
        }

        static void BuildButton()
        {
            var rt = NewRT("UI_Button", null);
            Place(rt, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(96, 24));
            var img = AddImage(rt, Spr("Buttons/Button_Normal.png"), true);
            img.raycastTarget = true;

            var lab = NewRT("Label", rt);
            Stretch(lab, new Vector2(4, 2), new Vector2(-4, -2));
            var text = AddText(lab, NwTheme.FontMenu, NwTheme.ButtonTextNormal, TextAnchor.MiddleCenter);
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            text.text = "Weiter";

            var b = rt.gameObject.AddComponent<NwButton>();
            SetField(b, "background", img);
            SetField(b, "label", text);
            SetField(b, "normal", Spr("Buttons/Button_Normal.png"));
            SetField(b, "hover", Spr("Buttons/Button_Hover.png"));
            SetField(b, "pressed", Spr("Buttons/Button_Pressed.png"));
            SetField(b, "disabled", Spr("Buttons/Button_Disabled.png"));
            Save(rt.gameObject, "UI_Button");
        }

        static void BuildReportRow()
        {
            var rt = NewRT("UI_ReportRow", null);
            Place(rt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), Vector2.zero, new Vector2(340, 20));
            var le = rt.gameObject.AddComponent<LayoutElement>();
            le.preferredHeight = 20;
            le.minHeight = 20;

            var icon = NewRT("Icon", rt);
            Place(icon, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(0, 0), new Vector2(16, 16));
            var iconImg = AddImage(icon, Spr("Icons/Icon_Warnung.png"), false);

            var lab = NewRT("Text", rt);
            Stretch(lab, new Vector2(22, 0), Vector2.zero);
            var text = AddText(lab, NwTheme.FontMenu, NwTheme.TextDefault, TextAnchor.MiddleLeft);
            text.horizontalOverflow = HorizontalWrapMode.Overflow;

            var row = rt.gameObject.AddComponent<NwReportRow>();
            SetField(row, "icon", iconImg);
            SetField(row, "label", text);
            Save(rt.gameObject, "UI_ReportRow");
        }

        static void BuildDialog()
        {
            var rt = NewRT("UI_Dialogbox", null);
            Place(rt, new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, 8), new Vector2(456, 96));
            AddImage(rt, Spr("Panels/Panel_Dialog.png"), true);

            var name = NewRT("Name", rt);
            name.anchorMin = new Vector2(0, 1); name.anchorMax = new Vector2(1, 1);
            name.pivot = new Vector2(0, 1);
            name.offsetMin = new Vector2(12, -30); name.offsetMax = new Vector2(-12, -8);
            var nameText = AddText(name, NwTheme.FontMenu, NwTheme.Title, TextAnchor.UpperLeft);
            nameText.verticalOverflow = VerticalWrapMode.Truncate;
            nameText.text = "Ilhan";
            name.gameObject.AddComponent<RectMask2D>();

            // Textflaeche mit Abstand zum Rahmen; RectMask2D schneidet alles ab, was doch herausragen wuerde
            var body = NewRT("Text", rt);
            Stretch(body, new Vector2(14, 14), new Vector2(-14, -30));
            var bodyText = AddText(body, NwTheme.FontMenu, NwTheme.TextDefault, TextAnchor.UpperLeft);
            bodyText.verticalOverflow = VerticalWrapMode.Truncate;
            bodyText.text = "Text";
            body.gameObject.AddComponent<RectMask2D>();

            var arrow = NewRT("Weiterpfeil", rt);
            Place(arrow, new Vector2(1, 0), new Vector2(1, 0), new Vector2(1, 0), new Vector2(-14, 5), new Vector2(9, 6));
            var arrowImg = AddImage(arrow, Spr("HUD/HUD_Pfeil_Weiter.png"), false);
            arrow.gameObject.AddComponent<NwBlink>();

            var d = rt.gameObject.AddComponent<NwDialogBox>();
            SetField(d, "nameText", nameText);
            SetField(d, "bodyText", bodyText);
            SetField(d, "bodyRect", body);
            SetField(d, "arrow", arrowImg);
            Save(rt.gameObject, "UI_Dialogbox");
        }

        static void BuildHud()
        {
            var rt = NewRT("UI_HUD", null);
            Place(rt, new Vector2(0, 1), new Vector2(1, 1), new Vector2(0.5f, 1), Vector2.zero, new Vector2(0, 40));

            Image Icon(string name, string sprite, Transform parent, float x, float y)
            {
                var r = NewRT(name, parent);
                Place(r, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(x, y), new Vector2(16, 16));
                return AddImage(r, Spr("Icons/" + sprite), false);
            }

            Text Value(string name, Transform parent, float x, float y, int size, Color color, string initial, float w, float h)
            {
                var r = NewRT(name, parent);
                Place(r, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(x, y), new Vector2(w, h));
                var t = AddText(r, size, color, TextAnchor.MiddleLeft);
                t.horizontalOverflow = HorizontalWrapMode.Overflow;
                t.verticalOverflow = VerticalWrapMode.Overflow;
                t.text = initial;
                return t;
            }

            // --- Zeile 1: Tageszeit, Leben
            var phaseIcon = Icon("Tageszeit", "Icon_Nacht.png", rt, 4, -3);
            var clock = Value("Uhrzeit", rt, 22, -1, NwTheme.FontMenu, NwTheme.TextDefault, "21:00", 64, 20);
            var phase = Value("Phase", rt, 88, -6, NwTheme.FontHint, NwTheme.Title, "Nacht", 40, 10);

            var frame = NewRT("Leben", rt);
            Place(frame, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(134, -5), new Vector2(76, 12));
            AddImage(frame, Spr("HUD/HUD_Leben_Rahmen.png"), false);
            var fillRt = NewRT("Fuellung", frame);
            Place(fillRt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(3, -3), new Vector2(70, 6));
            var fill = AddImage(fillRt, Spr("HUD/HUD_Leben_Fuellung.png"), false);
            fill.type = Image.Type.Filled;
            fill.fillMethod = Image.FillMethod.Horizontal;
            fill.fillOrigin = (int)Image.OriginHorizontal.Left;
            fill.fillAmount = 0.7f;
            var ticksRt = NewRT("Teiler", frame);
            Place(ticksRt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(3, -3), new Vector2(70, 6));
            AddImage(ticksRt, Spr("HUD/HUD_Leben_Teiler.png"), false);
            var healthText = Value("Leben_Wert", rt, 214, -6, NwTheme.FontHint, NwTheme.TextDefault, "7/10", 36, 10);

            // Weckstufe: oben rechts, nur im Versteck sichtbar
            var wake = NewRT("Weckstufe", rt);
            Place(wake, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), new Vector2(-4, -3), new Vector2(76, 16));
            var wakeIcon = NewRT("Icon", wake);
            Place(wakeIcon, new Vector2(0, 0.5f), new Vector2(0, 0.5f), new Vector2(0, 0.5f), Vector2.zero, new Vector2(16, 16));
            AddImage(wakeIcon, Spr("Icons/Icon_Versteck.png"), false);
            var bars = new Image[5];
            for (int i = 0; i < 5; i++)
            {
                var r = NewRT("Balken" + (i + 1), wake);
                Place(r, new Vector2(1, 0.5f), new Vector2(1, 0.5f), new Vector2(1, 0.5f), new Vector2(-(4 - i) * 8, 0), new Vector2(6, 12));
                bars[i] = AddImage(r, Spr("HUD/HUD_Weckbalken_Leer.png"), false);
            }

            // --- Zeile 2: Aktionen, Talismane, Vertrauen, Wissen
            var dots = new Image[4];
            var dotsRoot = NewRT("Aktionen", rt);
            Place(dotsRoot, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), Vector2.zero, Vector2.zero);
            for (int i = 0; i < 4; i++)
            {
                var r = NewRT("Punkt" + (i + 1), dotsRoot);
                Place(r, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(8 + i * 9, -25), new Vector2(7, 7));
                dots[i] = AddImage(r, Spr("HUD/HUD_Aktion_Voll.png"), false);
            }
            Icon("Talisman_Icon", "Icon_Talisman.png", rt, 56, -20);
            var talisman = Value("Talisman_Wert", rt, 74, -18, NwTheme.FontMenu, NwTheme.Talisman, "5/6", 40, 20);
            Icon("Vertrauen_Icon", "Icon_Vertrauen.png", rt, 124, -20);
            var trust = Value("Vertrauen_Wert", rt, 142, -18, NwTheme.FontMenu, NwTheme.Trust, "7", 28, 20);
            Icon("Wissen_Icon", "Icon_Wissen.png", rt, 172, -20);
            var knowledge = Value("Wissen_Wert", rt, 190, -18, NwTheme.FontMenu, NwTheme.Knowledge, "3", 28, 20);

            var hud = rt.gameObject.AddComponent<NwHud>();
            SetField(hud, "phaseIcon", phaseIcon);
            SetField(hud, "clockText", clock);
            SetField(hud, "phaseText", phase);
            SetField(hud, "iconMorning", Spr("Icons/Icon_Morgen.png"));
            SetField(hud, "iconDay", Spr("Icons/Icon_Tag.png"));
            SetField(hud, "iconEvening", Spr("Icons/Icon_Abend.png"));
            SetField(hud, "iconNight", Spr("Icons/Icon_Nacht.png"));
            SetField(hud, "healthFill", fill);
            SetField(hud, "healthText", healthText);
            SetField(hud, "fillNormal", Spr("HUD/HUD_Leben_Fuellung.png"));
            SetField(hud, "fillCritical", Spr("HUD/HUD_Leben_Kritisch.png"));
            SetArray(hud, "actionDots", dots);
            SetField(hud, "dotFull", Spr("HUD/HUD_Aktion_Voll.png"));
            SetField(hud, "dotEmpty", Spr("HUD/HUD_Aktion_Leer.png"));
            SetField(hud, "talismanText", talisman);
            SetField(hud, "trustText", trust);
            SetField(hud, "knowledgeText", knowledge);
            SetField(hud, "wakeRoot", wake.gameObject);
            SetArray(hud, "wakeBars", bars);
            SetField(hud, "barEmpty", Spr("HUD/HUD_Weckbalken_Leer.png"));
            SetField(hud, "barYellow", Spr("HUD/HUD_Weckbalken_Gelb.png"));
            SetField(hud, "barOrange", Spr("HUD/HUD_Weckbalken_Orange.png"));
            SetField(hud, "barRed", Spr("HUD/HUD_Weckbalken_Rot.png"));
            Save(rt.gameObject, "UI_HUD");
        }

        static void BuildReport()
        {
            var rowPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_ReportRow.prefab");
            var btnPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_Button.prefab");

            var rt = NewRT("UI_Lagebericht", null);
            Place(rt, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0, 0), new Vector2(400, 220));
            AddImage(rt, Spr("Panels/Panel_Lagebericht.png"), true);

            var title = NewRT("Titel", rt);
            Place(title, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(16, -10), new Vector2(260, 22));
            var titleText = AddText(title, NwTheme.FontMenu, NwTheme.Title, TextAnchor.UpperLeft);
            titleText.horizontalOverflow = HorizontalWrapMode.Overflow;
            titleText.verticalOverflow = VerticalWrapMode.Truncate;
            titleText.text = "Morgen in Nightward";

            var day = NewRT("Tag", rt);
            Place(day, new Vector2(1, 1), new Vector2(1, 1), new Vector2(1, 1), new Vector2(-16, -10), new Vector2(84, 22));
            var dayText = AddText(day, NwTheme.FontMenu, NwTheme.TextDefault, TextAnchor.UpperRight);
            dayText.text = "Tag 3";

            var rows = NewRT("Zeilen", rt);
            Stretch(rows, new Vector2(16, 46), new Vector2(-16, -44));
            rows.gameObject.AddComponent<RectMask2D>();
            var vlg = rows.gameObject.AddComponent<VerticalLayoutGroup>();
            vlg.childAlignment = TextAnchor.UpperLeft;
            vlg.spacing = 4;
            vlg.childControlWidth = true;
            vlg.childControlHeight = true;
            vlg.childForceExpandWidth = true;
            vlg.childForceExpandHeight = false;

            var btn = (GameObject)PrefabUtility.InstantiatePrefab(btnPrefab, rt);
            btn.name = "Weiter";
            var brt = (RectTransform)btn.transform;
            Place(brt, new Vector2(1, 0), new Vector2(1, 0), new Vector2(1, 0), new Vector2(-12, 12), new Vector2(96, 24));
            PrefabUtility.RecordPrefabInstancePropertyModifications(brt);

            var report = rt.gameObject.AddComponent<NwReport>();
            SetField(report, "titleText", titleText);
            SetField(report, "dayText", dayText);
            SetField(report, "rows", rows);
            SetField(report, "rowPrefab", rowPrefab.GetComponent<NwReportRow>());
            SetField(report, "continueButton", btn.GetComponent<NwButton>());
            SetField(report, "iconLoss", Spr("Icons/Icon_Warnung.png"));
            SetField(report, "iconWarning", Spr("Icons/Icon_Versteck.png"));
            SetField(report, "iconTalisman", Spr("Icons/Icon_Talisman.png"));
            SetField(report, "iconKnowledge", Spr("Icons/Icon_Wissen.png"));
            Save(rt.gameObject, "UI_Lagebericht");
        }

        // ------------------------------------------------------------------ Szene
        [MenuItem("Nightward/UI/3 Testszene bauen")]
        public static void BuildScene()
        {
            font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);
            var hudPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_HUD.prefab");
            var dialogPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_Dialogbox.prefab");
            var reportPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_Lagebericht.prefab");
            var btnPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_Button.prefab");
            if (hudPrefab == null || dialogPrefab == null || reportPrefab == null || btnPrefab == null)
            {
                Debug.LogError("[UI] Prefabs fehlen - erst 'Test-UI bauen (alles)' ausfuehren.");
                return;
            }

            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            foreach (var l in Object.FindObjectsByType<Light>(FindObjectsInactive.Exclude)) Object.DestroyImmediate(l.gameObject);
            var cam = Camera.main;
            if (cam != null)
            {
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = new Color32(0x1f, 0x2a, 0x3d, 255);
            }

            var canvasGo = new GameObject("UI_Canvas", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasGo.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(480, 270);   // wie die Spielkamera (PixelPerfect 480x270)
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            scaler.referencePixelsPerUnit = 100;
            var root = canvasGo.AddComponent<NwUIRoot>();
            SetField(root, "pixelFont", font);

            // Spieluhr fuer die HUD-Uhr (Zeitraffer 30x, damit man die Phasen sieht; F5 Phase, F6 Tempo, F7 Pause)
            var cycleGo = new GameObject("DayNightCycle");
            var cycle = cycleGo.AddComponent<DayNightCycle>();
            SetField(cycle, "timeScale", 30f);

            var es = new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
            es.GetComponent<InputSystemUIInputModule>().AssignDefaultActions();

            // Platzhalter-Szene hinter dem UI: HUD bleibt transparent
            var bgRt = NewRT("Szene_Platzhalter", canvasGo.transform);
            Stretch(bgRt, Vector2.zero, Vector2.zero);
            var bg = bgRt.gameObject.AddComponent<Image>();
            bg.color = new Color32(0x2f, 0x5a, 0x3c, 255);
            bg.raycastTarget = false;

            var hud = (GameObject)PrefabUtility.InstantiatePrefab(hudPrefab, canvasGo.transform);
            var dialog = (GameObject)PrefabUtility.InstantiatePrefab(dialogPrefab, canvasGo.transform);
            var report = (GameObject)PrefabUtility.InstantiatePrefab(reportPrefab, canvasGo.transform);

            var ctrlGo = new GameObject("UI_TestController");
            var ctrl = ctrlGo.AddComponent<NwUITestController>();
            SetField(ctrl, "dialog", dialog.GetComponent<NwDialogBox>());
            SetField(ctrl, "hud", hud.GetComponent<NwHud>());
            SetField(ctrl, "report", report.GetComponent<NwReport>());

            // Testknoepfe links in zwei Spalten (72x16: kleinste erlaubte Groesse ist 48x16)
            var tests = new (string label, UnityEngine.Events.UnityAction action)[]
            {
                ("Dialog", ctrl.OnDialog),
                ("Erzähler", ctrl.OnNarrator),
                ("Bericht", ctrl.OnReport),
                ("Phase +", ctrl.OnPhase),
                ("Tempo", ctrl.OnSpeed),
                ("Pause", ctrl.OnPause),
                ("Aktion", ctrl.OnAction),
                ("Talisman", ctrl.OnTalisman),
                ("Vertrauen", ctrl.OnTrust),
                ("Wissen", ctrl.OnKnowledge),
                ("Weckstufe", ctrl.OnWake),
                ("Leben -", ctrl.OnHealthMinus),
                ("Leben +", ctrl.OnHealthPlus),
            };
            for (int i = 0; i < tests.Length; i++)
            {
                var b = (GameObject)PrefabUtility.InstantiatePrefab(btnPrefab, canvasGo.transform);
                b.name = "Test_" + tests[i].label;
                var brt = (RectTransform)b.transform;
                Place(brt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1),
                    new Vector2(6 + (i / 7) * 78, -48 - (i % 7) * 20), new Vector2(72, 16));
                var nb = b.GetComponent<NwButton>();
                nb.Label.fontSize = NwTheme.FontHint;
                nb.Label.text = tests[i].label;
                UnityEventTools.AddPersistentListener(nb.onClick, tests[i].action);
                PrefabUtility.RecordPrefabInstancePropertyModifications(brt);
                PrefabUtility.RecordPrefabInstancePropertyModifications(nb);
                PrefabUtility.RecordPrefabInstancePropertyModifications(nb.Label);
            }

            EditorSceneManager.MarkSceneDirty(scene);
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath));
            EditorSceneManager.SaveScene(scene, ScenePath);
        }
    }
}
