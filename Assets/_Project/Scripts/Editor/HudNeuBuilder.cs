using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Nightward.DayNight;
using Nightward.UI;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut das neue HUD (Art/UI/HUD_Neu): Sprite-Import (Point, 9-Slice-Raender), Prefabs (HUD, Wecklevel, Neuer Tag,
    /// Quest-Zeilen) und setzt sie ins Canvas "HUD" der offenen Szene (Level_01).
    /// Menue: Nightward > UI > HUD Neu > Alles bauen
    /// </summary>
    public static class HudNeuBuilder
    {
        const string ArtDir = "Assets/_Project/Art/UI";
        const string HudDir = ArtDir + "/HUD_Neu";
        const string PrefabDir = "Assets/_Project/Prefabs/UI";
        const string FontPath = ArtDir + "/Font/Nightward_Pixel.ttf";

        static readonly string[] SpriteFolders = { "Plates", "Vitals", "Clock", "Needs", "Quest", "Wake", "Banner", "Events" };

        static Font font;

        [MenuItem("Nightward/UI/HUD Neu/Alles bauen (Import, Prefabs, Szene)")]
        public static void BuildAll()
        {
            ConfigureImports();
            BuildPrefabs();
            InstallInScene();
        }

        // ------------------------------------------------------------------ Import
        [MenuItem("Nightward/UI/HUD Neu/1 Import konfigurieren")]
        public static void ConfigureImports()
        {
            AssetDatabase.Refresh();
            foreach (var folder in SpriteFolders)
            {
                foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { HudDir + "/" + folder }))
                {
                    var path = AssetDatabase.GUIDToAssetPath(guid);
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
                    s.spriteAlignment = (int)SpriteAlignment.Center;
                    ti.SetTextureSettings(s);
                    ti.spriteBorder = BorderFor(Path.GetFileNameWithoutExtension(path));   // (links, unten, rechts, oben)
                    ti.SaveAndReimport();
                }
            }
            AssetDatabase.Refresh();
        }

        static Vector4 BorderFor(string name)
        {
            switch (name)
            {
                case "Plate_HUD":
                case "Plate_Flyout": return new Vector4(3, 3, 3, 3);
                case "Plate_Header_Haupt":
                case "Plate_Header_Neben": return new Vector4(4, 3, 3, 3);
                case "Titelband":
                case "Titelband_Klein": return new Vector4(14, 0, 14, 0);
                default: return Vector4.zero;
            }
        }

        // ------------------------------------------------------------------ Helfer
        static Sprite S(string rel)
        {
            var s = AssetDatabase.LoadAssetAtPath<Sprite>(HudDir + "/" + rel);
            if (s == null) Debug.LogError("[HUD Neu] Sprite fehlt: " + rel);
            return s;
        }

        static Sprite Old(string rel)
        {
            var s = AssetDatabase.LoadAssetAtPath<Sprite>(ArtDir + "/" + rel);
            if (s == null) Debug.LogError("[HUD Neu] Sprite fehlt: " + rel);
            return s;
        }

        static RectTransform NewRT(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return go.GetComponent<RectTransform>();
        }

        static readonly Vector2 TL = new Vector2(0, 1);
        static readonly Vector2 TR = new Vector2(1, 1);
        static readonly Vector2 TC = new Vector2(0.5f, 1);
        static readonly Vector2 BC = new Vector2(0.5f, 0);
        static readonly Vector2 BR = new Vector2(1, 0);
        static readonly Vector2 MC = new Vector2(0.5f, 0.5f);

        /// <summary>Anker = Pivot (Ecke), Position und Groesse in Canvas-Pixeln.</summary>
        static RectTransform Corner(RectTransform rt, Vector2 corner, Vector2 pos, Vector2 size)
        {
            rt.anchorMin = corner;
            rt.anchorMax = corner;
            rt.pivot = corner;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            return rt;
        }

        static RectTransform Stretch(RectTransform rt, Vector2 offsetMin, Vector2 offsetMax)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = offsetMin;
            rt.offsetMax = offsetMax;
            return rt;
        }

        static Image Img(Transform parent, string name, Sprite sprite, Vector2 corner, Vector2 pos, Vector2 size, Image.Type type = Image.Type.Simple)
        {
            var rt = Corner(NewRT(name, parent), corner, pos, size);
            return AddImage(rt, sprite, type);
        }

        static Image AddImage(RectTransform rt, Sprite s, Image.Type type = Image.Type.Simple)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = s;
            img.type = type;
            img.raycastTarget = false;
            img.pixelsPerUnitMultiplier = 1f;
            return img;
        }

        /// <summary>Unsichtbare Flaeche, die Hover und Klicks auffaengt (Tooltip, Klicks gehen nicht ins Spiel).</summary>
        static Image HitArea(Transform parent, string name, Vector2 corner, Vector2 pos, Vector2 size, string tip)
        {
            var img = Img(parent, name, null, corner, pos, size);
            img.color = new Color(0, 0, 0, 0);
            img.raycastTarget = true;
            if (tip != null) img.gameObject.AddComponent<NwTooltipTarget>().SetText(tip);
            return img;
        }

        static Image Filled(Image img, Image.OriginHorizontal origin = Image.OriginHorizontal.Left)
        {
            img.type = Image.Type.Filled;
            img.fillMethod = Image.FillMethod.Horizontal;
            img.fillOrigin = (int)origin;
            img.fillAmount = 1f;
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
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.supportRichText = false;
            t.raycastTarget = false;
            t.lineSpacing = 1f;
            if (shadow)
            {
                var sh = rt.gameObject.AddComponent<Shadow>();
                sh.effectColor = NwTheme.TextShadow;
                sh.effectDistance = new Vector2(1, -1);
            }
            return t;
        }

        static Text TextAt(Transform parent, string name, string content, int size, Color color, TextAnchor anchor, Vector2 corner, Vector2 pos, Vector2 boxSize)
        {
            var rt = Corner(NewRT(name, parent), corner, pos, boxSize);
            var t = AddText(rt, size, color, anchor);
            t.text = content;
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
                case System.Enum e: p.enumValueIndex = System.Convert.ToInt32(e); break;
                default: Debug.LogError("Typ nicht unterstuetzt: " + value); break;
            }
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static void SetArray(Object target, string field, Object[] values)
        {
            var so = new SerializedObject(target);
            var p = so.FindProperty(field);
            if (p == null) { Debug.LogError("Feld fehlt: " + target.GetType().Name + "." + field); return; }
            p.arraySize = values.Length;
            for (int i = 0; i < values.Length; i++) p.GetArrayElementAtIndex(i).objectReferenceValue = values[i];
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        static GameObject Save(GameObject root, string name)
        {
            Directory.CreateDirectory(PrefabDir);
            var path = $"{PrefabDir}/{name}.prefab";
            PrefabUtility.SaveAsPrefabAsset(root, path);
            Object.DestroyImmediate(root);
            return AssetDatabase.LoadAssetAtPath<GameObject>(path);   // frisch laden, das Rueckgabe-Objekt ist nach dem Zerstoeren unsicher
        }

        // ------------------------------------------------------------------ Prefabs
        [MenuItem("Nightward/UI/HUD Neu/2 Prefabs bauen")]
        public static void BuildPrefabs()
        {
            font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);
            if (font == null) { Debug.LogError("[HUD Neu] Font fehlt: " + FontPath); return; }

            var header = BuildQuestHeader();
            var entry = BuildQuestEntry();
            BuildHud(header, entry);
            BuildWakeLevel();
            BuildNewDay();
            AssetDatabase.SaveAssets();
            Debug.Log("[HUD Neu] Prefabs gebaut: UI_GameHud, UI_WakeLevel, UI_NewDay, UI_QuestHeader, UI_QuestEntry");
        }

        // ---------------- Quest-Zeilen
        static GameObject BuildQuestHeader()
        {
            var rt = NewRT("UI_QuestHeader", null);
            Corner(rt, TL, Vector2.zero, new Vector2(146, 13));
            var plate = AddImage(rt, S("Plates/Plate_Header_Haupt.png"), Image.Type.Sliced);
            plate.raycastTarget = true;
            var le = rt.gameObject.AddComponent<LayoutElement>();
            le.preferredHeight = 13;
            le.minHeight = 13;

            var icon = Img(rt, "Symbol", S("Quest/Symbol_Haupt.png"), new Vector2(0, 0.5f), new Vector2(6, 0), new Vector2(12, 12));
            var title = AddText(Stretch(NewRT("Titel", rt), new Vector2(21, 0), new Vector2(-28, 0)), NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.MiddleLeft);
            title.text = "Main Quest";
            var arrow = Img(rt, "Pfeil", S("Quest/Pfeil_Auf.png"), new Vector2(1, 0.5f), new Vector2(-5, 0), new Vector2(7, 7));

            var badge = Img(rt, "Anzahl", S("Quest/Abzeichen_Zahl.png"), new Vector2(1, 0.5f), new Vector2(-16, 0), new Vector2(13, 9));
            var badgeText = AddText(Stretch(NewRT("Zahl", badge.transform), Vector2.zero, Vector2.zero), NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.MiddleCenter, false);
            badgeText.text = "0";

            var h = rt.gameObject.AddComponent<NwQuestHeader>();
            SetField(h, "plate", plate);
            SetField(h, "icon", icon);
            SetField(h, "title", title);
            SetField(h, "arrow", arrow);
            SetField(h, "badge", badge.gameObject);
            SetField(h, "badgeText", badgeText);
            SetField(h, "arrowOpen", S("Quest/Pfeil_Auf.png"));
            SetField(h, "arrowOpenHover", S("Quest/Pfeil_Auf_Hover.png"));
            SetField(h, "arrowClosed", S("Quest/Pfeil_Zu.png"));
            SetField(h, "arrowClosedHover", S("Quest/Pfeil_Zu_Hover.png"));
            return Save(rt.gameObject, "UI_QuestHeader");
        }

        static GameObject BuildQuestEntry()
        {
            var rt = NewRT("UI_QuestEntry", null);
            Corner(rt, TL, Vector2.zero, new Vector2(146, 12));
            var le = rt.gameObject.AddComponent<LayoutElement>();
            le.preferredHeight = 12;
            le.minHeight = 12;

            var tracked = Img(rt, "Verfolgt", S("Quest/Marke_Verfolgt.png"), TL, new Vector2(2, -3), new Vector2(4, 7));
            var dot = Img(rt, "Punkt", S("Quest/Punkt_Offen.png"), TL, new Vector2(9, -3), new Vector2(7, 7));
            var label = TextAt(rt, "Text", "Quest", NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.MiddleLeft, TL, new Vector2(19, -1), new Vector2(124, 10));

            var progress = Corner(NewRT("Fortschritt", rt), TL, new Vector2(19, -13), new Vector2(40, 5));
            AddImage(progress, S("Quest/Fortschritt_Rahmen.png"));
            var fill = Filled(Img(progress, "Fuellung", S("Quest/Fortschritt_Fuellung.png"), TL, new Vector2(1, -1), new Vector2(38, 3)));
            progress.gameObject.SetActive(false);

            var e = rt.gameObject.AddComponent<NwQuestEntry>();
            SetField(e, "tracked", tracked);
            SetField(e, "dot", dot);
            SetField(e, "label", label);
            SetField(e, "progressRoot", progress.gameObject);
            SetField(e, "progressFill", fill);
            SetField(e, "layout", le);
            SetField(e, "dotOpen", S("Quest/Punkt_Offen.png"));
            SetField(e, "dotActive", S("Quest/Punkt_Aktiv.png"));
            SetField(e, "dotDone", S("Quest/Punkt_Fertig.png"));
            SetField(e, "dotFailed", S("Quest/Punkt_Gescheitert.png"));
            return Save(rt.gameObject, "UI_QuestEntry");
        }

        // ---------------- HUD
        static NwVitalBar BuildBar(Transform parent, string name, float top, Sprite icon, Sprite fillNormal,
            Sprite low, Sprite critical, Sprite empty, float lowBelow, float criticalBelow,
            Sprite divider, Sprite mark, bool trail, bool hatch, string tip)
        {
            Img(parent, name + "_Icon", icon, TL, new Vector2(0, -(top - 1)), new Vector2(11, 11));

            var row = Corner(NewRT(name, parent), TL, new Vector2(14, -top), new Vector2(64, 9));
            AddImage(row, S("Vitals/Balken_Rahmen.png"));
            Image trailImg = trail ? Filled(Img(row, "Verlust", S("Vitals/Verlust_Spur.png"), TL, new Vector2(2, -2), new Vector2(60, 5))) : null;
            var fill = Filled(Img(row, "Fuellung", fillNormal, TL, new Vector2(2, -2), new Vector2(60, 5)));
            if (divider != null) Img(row, "Teiler", divider, TL, new Vector2(2, -2), new Vector2(60, 5));
            if (mark != null) Img(row, "Schlafsperre", mark, TL, new Vector2(2, -2), new Vector2(60, 5));
            Image hatchImg = null;
            if (hatch)
            {
                hatchImg = Filled(Img(row, "Gesperrt", S("Vitals/Schraffur_Gesperrt.png"), TL, new Vector2(2, -2), new Vector2(60, 5)), Image.OriginHorizontal.Right);
                hatchImg.fillAmount = 0f;
                hatchImg.enabled = false;
            }

            HitArea(parent, name + "_Hover", TL, new Vector2(0, -(top - 1)), new Vector2(78, 11), tip);

            var bar = row.gameObject.AddComponent<NwVitalBar>();
            SetField(bar, "fill", fill);
            if (trailImg != null) SetField(bar, "trail", trailImg);
            if (hatchImg != null) SetField(bar, "hatch", hatchImg);
            SetField(bar, "normal", fillNormal);
            if (low != null) SetField(bar, "low", low);
            if (critical != null) SetField(bar, "critical", critical);
            if (empty != null) SetField(bar, "empty", empty);
            SetField(bar, "lowBelow", lowBelow);
            SetField(bar, "criticalBelow", criticalBelow);
            return bar;
        }

        static NwNeedTile BuildTile(Transform parent, NeedKind kind, string chain, string symbol, string symbolPositive)
        {
            var rt = Corner(NewRT("Need_" + kind, parent), TL, Vector2.zero, new Vector2(22, 22));
            var tile = AddImage(rt, S($"Needs/Anzeige_{chain}_Stufe_1.png"));
            tile.raycastTarget = true;
            var overlay = Img(rt, "Symbol", S($"Needs/Symbol_{symbol}.png"), TL, new Vector2(3, -1), new Vector2(16, 16));
            overlay.enabled = false;

            var fly = Corner(NewRT("Flyout", rt), new Vector2(0, 0.5f), new Vector2(-5, 0), new Vector2(80, 16));
            fly.pivot = new Vector2(1, 0.5f);
            AddImage(fly, S("Plates/Plate_Flyout.png"), Image.Type.Sliced);
            var text = AddText(Stretch(NewRT("Text", fly), Vector2.zero, Vector2.zero), NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.MiddleCenter);
            var pointer = Img(fly, "Zeiger", S("Plates/Plate_Flyout_Zeiger.png"), new Vector2(1, 0.5f), new Vector2(-1, 0), new Vector2(6, 9));
            pointer.rectTransform.pivot = new Vector2(0, 0.5f);
            fly.gameObject.SetActive(false);

            var n = rt.gameObject.AddComponent<NwNeedTile>();
            SetField(n, "kind", kind);
            SetField(n, "tile", tile);
            SetField(n, "symbolOverlay", overlay);
            SetField(n, "flashTile", S("Needs/Kachel_Blitz.png"));
            SetField(n, "symbol", S($"Needs/Symbol_{symbol}.png"));
            if (symbolPositive != null) SetField(n, "symbolPositive", S($"Needs/Symbol_{symbolPositive}.png"));
            SetField(n, "flyout", fly);
            SetField(n, "flyoutText", text);
            var stages = new Object[4];
            for (int i = 0; i < 4; i++) stages[i] = S($"Needs/Anzeige_{chain}_Stufe_{i + 1}.png");
            SetArray(n, "stageSprites", stages);
            if (symbolPositive != null)
                SetArray(n, "positiveSprites", new Object[] { S($"Needs/Anzeige_{chain}_Positiv_1.png"), S($"Needs/Anzeige_{chain}_Positiv_2.png") });
            rt.gameObject.SetActive(false);
            return n;
        }

        static void BuildHud(GameObject headerPrefab, GameObject entryPrefab)
        {
            var root = NewRT("UI_GameHud", null);
            Stretch(root, Vector2.zero, Vector2.zero);
            root.gameObject.AddComponent<CanvasGroup>();

            // --- Uhr-Platte oben links (68x30): Phasen-Symbol, Uhrzeit, Tag
            var clock = Corner(NewRT("Uhr", root), TL, new Vector2(6, -6), new Vector2(68, 30));
            AddImage(clock, S("Plates/Plate_HUD.png"), Image.Type.Sliced).raycastTarget = true;
            clock.gameObject.AddComponent<NwTooltipTarget>().SetText("Current time and day.");
            var phaseIcon = Img(clock, "Phase", Old("Icons/Icon_Tag.png"), TL, new Vector2(5, -7), new Vector2(16, 16));
            var clockText = TextAt(clock, "Uhrzeit", "12:45", NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.MiddleLeft, TL, new Vector2(26, -4), new Vector2(38, 10));
            var dayText = TextAt(clock, "Tag", "Day 1", NwTheme.FontHint, NwTheme.Title, TextAnchor.MiddleLeft, TL, new Vector2(26, -15), new Vector2(38, 10));

            // --- Tagesspur (2 px pro Stunde, 0-24 Uhr): Marke oben, Glocke bei 18 Uhr unten
            var track = Corner(NewRT("Tagesspur", root), TL, new Vector2(12, -38), new Vector2(50, 17));
            var marker = Img(track, "Marke", S("Clock/Spur_Marke.png"), TL, new Vector2(1, 0), new Vector2(5, 4));
            Img(track, "Rahmen", S("Clock/Spur_Rahmen.png"), TL, new Vector2(0, -4), new Vector2(50, 5));
            Img(track, "Segmente", S("Clock/Spur_Segmente.png"), TL, new Vector2(1, -5), new Vector2(48, 3));
            var past = Filled(Img(track, "Vergangen", S("Clock/Spur_Vergangen.png"), TL, new Vector2(1, -5), new Vector2(48, 3)));
            past.fillAmount = 0f;
            Img(track, "Glocke", S("Clock/Spur_Glocke.png"), TL, new Vector2(34, -10), new Vector2(7, 7));
            HitArea(track, "Hover", TL, Vector2.zero, new Vector2(50, 17), "Day timeline. Bell rings at 18:00.");

            // --- Vitalbalken (Zeilenabstand 14 px) unten links, damit sie neben dem Spielgeschehen nicht ablenken
            var vitals = Corner(NewRT("Vitalwerte", root), new Vector2(0, 0), new Vector2(6, 6), new Vector2(78, 38));
            vitals.pivot = new Vector2(0, 0);
            var health = BuildBar(vitals, "Leben", 1, S("Vitals/Icon_Herz.png"), S("Vitals/Fuellung_Leben.png"),
                null, S("Vitals/Fuellung_Leben_Kritisch.png"), null, 0f, 0.3f, S("Vitals/Teiler_3.png"), null, true, false,
                null);
            var stamina = BuildBar(vitals, "Ausdauer", 15, S("Vitals/Icon_Ausdauer.png"), S("Vitals/Fuellung_Ausdauer.png"),
                null, null, S("Vitals/Fuellung_Ausdauer_Leer.png"), 0f, 0f, null, null, false, true,
                null);
            var sanity = BuildBar(vitals, "Sanity", 29, S("Vitals/Icon_Geist.png"), S("Vitals/Fuellung_Geist.png"),
                S("Vitals/Fuellung_Geist_Niedrig.png"), S("Vitals/Fuellung_Geist_Kritisch.png"), null, 0.4f, 0.2f, null, S("Vitals/Marke_Schlafsperre.png"), false, false,
                null);

            // --- Bedarf und Stimmung: rechts, untere Haelfte, senkrecht gestapelt (Abstand 3 px, Kachel 22 px)
            // Unten rechts verankert, waechst nach oben. Ab sieben Kacheln beginnt links daneben eine zweite Spalte,
            // damit der Stapel auch mit allen elf aktiven Zustaenden nicht in den Quest-Tracker ragt
            var stack = Corner(NewRT("Beduerfnisse", root), BR, new Vector2(-6, 6), new Vector2(47, 172));
            var grid = stack.gameObject.AddComponent<GridLayoutGroup>();
            grid.cellSize = new Vector2(22, 22);
            grid.spacing = new Vector2(3, 3);
            grid.startCorner = GridLayoutGroup.Corner.LowerRight;
            grid.startAxis = GridLayoutGroup.Axis.Vertical;
            grid.childAlignment = TextAnchor.LowerRight;
            grid.constraint = GridLayoutGroup.Constraint.FixedRowCount;
            grid.constraintCount = 7;
            var tiles = new[]
            {
                BuildTile(stack, NeedKind.Hunger, "Hunger", "Hunger", null),
                BuildTile(stack, NeedKind.Durst, "Durst", "Durst", null),
                BuildTile(stack, NeedKind.Muede, "Muede", "Muede", null),
                BuildTile(stack, NeedKind.Rausch, "Rausch", "Rausch", null),
                BuildTile(stack, NeedKind.Verletzt, "Verletzt", "Verletzt", null),
                BuildTile(stack, NeedKind.Stimmung, "Stimmung", "Traurig", "Froh"),
                BuildTile(stack, NeedKind.Gesellschaft, "Gesellschaft", "Einsam", "Sozial"),
                BuildTile(stack, NeedKind.Anspannung, "Anspannung", "Stress", "Ruhe"),
                BuildTile(stack, NeedKind.Erschoepft, "Erschoepft", "Erschoepft", null),
                BuildTile(stack, NeedKind.Kalt, "Kalt", "Kalt", null),
                BuildTile(stack, NeedKind.Verstoert, "Verstoert", "Verstoert", null),
            };

            // --- Quest-Tracker oben rechts (152 px breit, waechst mit dem Inhalt)
            var quest = Corner(NewRT("QuestTracker", root), TR, new Vector2(-6, -6), new Vector2(152, 20));
            AddImage(quest, S("Plates/Plate_HUD.png"), Image.Type.Sliced).raycastTarget = true;   // Klicks gehen nicht ins Spiel
            var qv = quest.gameObject.AddComponent<VerticalLayoutGroup>();
            qv.padding = new RectOffset(3, 3, 3, 3);
            qv.spacing = 2;
            qv.childAlignment = TextAnchor.UpperLeft;
            qv.childControlWidth = true;
            qv.childControlHeight = true;
            qv.childForceExpandWidth = true;
            qv.childForceExpandHeight = false;
            var fitter = quest.gameObject.AddComponent<ContentSizeFitter>();
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            var tracker = quest.gameObject.AddComponent<NwQuestTracker>();
            SetField(tracker, "content", quest);
            SetField(tracker, "headerPrefab", headerPrefab.GetComponent<NwQuestHeader>());
            SetField(tracker, "entryPrefab", entryPrefab.GetComponent<NwQuestEntry>());
            SetField(tracker, "plateMain", S("Plates/Plate_Header_Haupt.png"));
            SetField(tracker, "plateSide", S("Plates/Plate_Header_Neben.png"));
            SetField(tracker, "iconMain", S("Quest/Symbol_Haupt.png"));
            SetField(tracker, "iconSide", S("Quest/Symbol_Neben.png"));

            // Tooltip ganz oben (letztes Kind)
            var tipArea = Stretch(NewRT("Tooltip", root), Vector2.zero, Vector2.zero);
            var tipBox = Corner(NewRT("Box", tipArea), MC, Vector2.zero, new Vector2(80, 16));
            tipBox.pivot = TL;
            AddImage(tipBox, S("Plates/Plate_Flyout.png"), Image.Type.Sliced);
            var tipText = AddText(Stretch(NewRT("Text", tipBox), Vector2.zero, Vector2.zero), NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.MiddleCenter);
            tipBox.gameObject.SetActive(false);
            var tooltip = tipArea.gameObject.AddComponent<NwTooltip>();
            SetField(tooltip, "box", tipBox);
            SetField(tooltip, "label", tipText);

            var hud = root.gameObject.AddComponent<NwGameHud>();
            SetField(hud, "phaseIcon", phaseIcon);
            SetField(hud, "clockText", clockText);
            SetField(hud, "dayText", dayText);
            SetField(hud, "iconMorning", Old("Icons/Icon_Morgen.png"));
            SetField(hud, "iconDay", Old("Icons/Icon_Tag.png"));
            SetField(hud, "iconEvening", Old("Icons/Icon_Abend.png"));
            SetField(hud, "iconNight", Old("Icons/Icon_Nacht.png"));
            SetField(hud, "trackPast", past);
            SetField(hud, "trackMarker", marker.rectTransform);
            SetField(hud, "health", health);
            SetField(hud, "stamina", stamina);
            SetField(hud, "sanity", sanity);
            SetArray(hud, "needs", tiles);
            Save(root.gameObject, "UI_GameHud");
        }

        // ---------------- Wecklevel (oben Mitte, nur kurz)
        static void BuildWakeLevel()
        {
            var root = Corner(NewRT("UI_WakeLevel", null), TC, new Vector2(0, -6), new Vector2(120, 32));
            root.gameObject.AddComponent<CanvasGroup>();
            AddImage(root, S("Plates/Plate_HUD.png"), Image.Type.Sliced);
            Img(root, "Symbol", S("Wake/Symbol_Versteck.png"), TL, new Vector2(8, -8), new Vector2(16, 16));
            TextAt(root, "Titel", "Wake level", NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.MiddleLeft, TL, new Vector2(28, -4), new Vector2(84, 10));

            var bars = new Image[5];
            for (int i = 0; i < 5; i++)
                bars[i] = Img(root, "Balken" + (i + 1), S("Wake/Balken_Leer.png"), TL, new Vector2(28 + i * 9, -16), new Vector2(7, 12));
            var pulse = Img(root, "Puls", S("Wake/Balken_Puls.png"), TL, new Vector2(27, -15), new Vector2(9, 14));
            pulse.enabled = false;
            var value = TextAt(root, "Wert", "0 / 5", NwTheme.FontHint, NwTheme.TextDefault, TextAnchor.MiddleLeft, TL, new Vector2(80, -17), new Vector2(34, 10));

            var w = root.gameObject.AddComponent<NwWakeLevel>();
            SetArray(w, "bars", bars);
            SetField(w, "pulse", pulse);
            SetField(w, "valueText", value);
            SetField(w, "barEmpty", S("Wake/Balken_Leer.png"));
            SetField(w, "barYellow", S("Wake/Balken_Gelb.png"));
            SetField(w, "barOrange", S("Wake/Balken_Orange.png"));
            SetField(w, "barRed", S("Wake/Balken_Rot.png"));
            Save(root.gameObject, "UI_WakeLevel");
        }

        // ---------------- Neuer Tag: Banner und Bericht
        static void BuildNewDay()
        {
            var buttonPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_Button.prefab");
            var rowPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_ReportRow.prefab");
            if (buttonPrefab == null || rowPrefab == null)
            {
                Debug.LogError("[HUD Neu] UI_Button / UI_ReportRow fehlen - erst 'Nightward > UI > Test-UI bauen (alles)' ausfuehren.");
                return;
            }

            var root = NewRT("UI_NewDay", null);
            Stretch(root, Vector2.zero, Vector2.zero);
            var cg = root.gameObject.AddComponent<CanvasGroup>();
            cg.alpha = 0f;
            cg.blocksRaycasts = false;
            HitArea(root, "Blocker", TL, Vector2.zero, Vector2.zero, null);   // kein Klick durchs Banner ins Spiel
            var blocker = (RectTransform)root.GetChild(root.childCount - 1);
            Stretch(blocker, Vector2.zero, Vector2.zero);

            // Band: 116 px hoch, waagerecht gekachelt (nicht strecken, sonst wird der Dither grob)
            var banner = Corner(NewRT("Banner", root), TC, new Vector2(0, -38), new Vector2(0, 116));
            banner.anchorMin = new Vector2(0, 1);
            banner.anchorMax = new Vector2(1, 1);
            banner.sizeDelta = new Vector2(0, 116);
            var band = AddImage(Stretch(NewRT("Band", banner), Vector2.zero, Vector2.zero), S("Banner/Band_Morgen.png"), Image.Type.Tiled);

            // Reihenfolge von hinten: Band, Strahlen, Sterne, Skyline, Zierlinien, Titelband, Text
            var rays = Img(banner, "Strahlen", S("Banner/Strahlen_Morgen.png"), TC, new Vector2(0, 0), new Vector2(240, 110));
            var big = S("Banner/Stern_Gross.png");
            var small = S("Banner/Stern_Klein.png");
            var stars = new (Sprite s, int x, int y)[]
            {
                (big, -194, -16), (small, -152, -38), (small, -180, -72),
                (small, 152, -42), (small, 212, -68), (big, 190, -18),
            };
            for (int i = 0; i < stars.Length; i++)
            {
                var st = Img(banner, "Stern" + (i + 1), stars[i].s, TL, Vector2.zero, new Vector2(stars[i].s.rect.width, stars[i].s.rect.height));
                st.rectTransform.anchorMin = st.rectTransform.anchorMax = TC;
                st.rectTransform.pivot = TL;
                st.rectTransform.anchoredPosition = new Vector2(stars[i].x, stars[i].y);
            }
            var skyline = Img(banner, "Skyline", S("Banner/Skyline_Morgen.png"), BC, Vector2.zero, new Vector2(200, 60));
            var lineL = Img(banner, "Linie_L", S("Banner/Verzierung_Linie.png"), TC, new Vector2(-216, -17), new Vector2(96, 11));
            lineL.rectTransform.pivot = TL;
            var lineR = Img(banner, "Linie_R", S("Banner/Verzierung_Linie.png"), TC, new Vector2(216, -17), new Vector2(96, 11));
            lineR.rectTransform.pivot = TL;
            lineR.rectTransform.localScale = new Vector3(-1, 1, 1);   // gespiegelt, wächst nach links an die Mitte

            var ribbon = Img(banner, "Titelband", S("Banner/Titelband.png"), TC, new Vector2(0, -7), new Vector2(210, 34), Image.Type.Sliced);
            var title = AddText(Stretch(NewRT("Titel", ribbon.transform), new Vector2(14, 0), new Vector2(-14, 0)), 24, NwTheme.Title, TextAnchor.MiddleCenter);
            title.text = "DAY 2";
            var subtitle = TextAt(banner, "Untertitel", "Dawn breaks over Dusk Bell.", NwTheme.FontHint, NwTheme.Narrator, TextAnchor.MiddleCenter, TC, new Vector2(0, -44), new Vector2(300, 10));

            // Bericht: vorhandenes Panel_Lagebericht, Zeilen mit Events/Symbol_*
            var report = Corner(NewRT("Bericht", root), BC, new Vector2(0, 14), new Vector2(300, 98));
            AddImage(report, Old("Panels/Panel_Lagebericht.png"), Image.Type.Sliced).raycastTarget = true;
            var reportTitle = TextAt(report, "Titel", "Last night in Dusk Bell", NwTheme.FontHint, NwTheme.Title, TextAnchor.MiddleLeft, TL, new Vector2(14, -8), new Vector2(240, 10));
            Img(report, "Trenner", S("Events/Trenner.png"), TL, new Vector2(14, -21), new Vector2(48, 1));
            var rows = Stretch(NewRT("Zeilen", report), new Vector2(14, 4), new Vector2(-14, -26));
            rows.gameObject.AddComponent<RectMask2D>();
            var vlg = rows.gameObject.AddComponent<VerticalLayoutGroup>();
            vlg.childAlignment = TextAnchor.UpperLeft;
            vlg.spacing = 1;
            vlg.childControlWidth = true;
            vlg.childControlHeight = true;
            vlg.childForceExpandWidth = true;
            vlg.childForceExpandHeight = false;

            var btn = (GameObject)PrefabUtility.InstantiatePrefab(buttonPrefab, report);
            btn.name = "Weiter";
            var brt = (RectTransform)btn.transform;
            Corner(brt, BR, new Vector2(-10, 7), new Vector2(56, 16));
            var nb = btn.GetComponent<NwButton>();
            nb.Label.fontSize = NwTheme.FontHint;
            nb.Label.text = "Continue";
            PrefabUtility.RecordPrefabInstancePropertyModifications(brt);
            PrefabUtility.RecordPrefabInstancePropertyModifications(nb.Label);
            report.gameObject.SetActive(false);

            var nd = root.gameObject.AddComponent<NwNewDay>();
            SetField(nd, "bannerRoot", banner);
            SetField(nd, "band", band);
            SetField(nd, "skyline", skyline);
            SetField(nd, "rays", rays.gameObject);
            SetField(nd, "titleText", title);
            SetField(nd, "subtitleText", subtitle);
            SetField(nd, "bandMorning", S("Banner/Band_Morgen.png"));
            SetField(nd, "bandMidnight", S("Banner/Band_Mitternacht.png"));
            SetField(nd, "skylineMorning", S("Banner/Skyline_Morgen.png"));
            SetField(nd, "skylineMidnight", S("Banner/Skyline_Mitternacht.png"));
            SetField(nd, "report", report);
            SetField(nd, "reportTitle", reportTitle);
            SetField(nd, "rows", rows);
            SetField(nd, "rowPrefab", rowPrefab.GetComponent<NwReportRow>());
            SetField(nd, "continueButton", nb);
            SetField(nd, "iconQuiet", S("Events/Symbol_Haus.png"));
            SetField(nd, "iconLoss", S("Events/Symbol_Verlust.png"));
            SetField(nd, "iconRemembrance", S("Events/Symbol_Kerze.png"));
            SetField(nd, "iconBell", S("Events/Symbol_Glocke.png"));
            SetField(nd, "iconWounded", S("Events/Symbol_Verletzt.png"));
            SetField(nd, "iconWarning", Old("Icons/Icon_Versteck.png"));
            SetField(nd, "iconTalisman", Old("Icons/Icon_Talisman.png"));
            SetField(nd, "iconKnowledge", Old("Icons/Icon_Wissen.png"));
            Save(root.gameObject, "UI_NewDay");
        }

        // ------------------------------------------------------------------ Szene
        [MenuItem("Nightward/UI/HUD Neu/3 In offene Szene einbauen")]
        public static void InstallInScene()
        {
            font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);
            var hudPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_GameHud.prefab");
            var wakePrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_WakeLevel.prefab");
            var dayPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabDir + "/UI_NewDay.prefab");
            if (hudPrefab == null || wakePrefab == null || dayPrefab == null)
            {
                Debug.LogError("[HUD Neu] Prefabs fehlen - erst 'Prefabs bauen' ausfuehren.");
                return;
            }

            var scene = EditorSceneManager.GetActiveScene();

            // Canvas "HUD" der Szene wiederverwenden (dort lag bisher nur das Sonne/Mond-Symbol), sonst neu anlegen
            Canvas canvas = null;
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsInactive.Include))
                if (c.gameObject.name == "HUD") canvas = c;
            GameObject canvasGo;
            if (canvas == null)
            {
                canvasGo = new GameObject("HUD", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler));
                canvas = canvasGo.GetComponent<Canvas>();
            }
            else canvasGo = canvas.gameObject;

            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            if (scaler == null) scaler = canvasGo.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(480, 270);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            scaler.referencePixelsPerUnit = 100;
            if (canvasGo.GetComponent<GraphicRaycaster>() == null) canvasGo.AddComponent<GraphicRaycaster>();
            var uiRoot = canvasGo.GetComponent<NwUIRoot>();
            if (uiRoot == null) uiRoot = canvasGo.AddComponent<NwUIRoot>();
            SetField(uiRoot, "pixelFont", font);

            // Altes Tageszeit-Symbol und sein Skript entfernen, bereits eingebaute Instanzen ersetzen
            var oldHud = canvasGo.GetComponent<DayNightHud>();
            if (oldHud != null) Object.DestroyImmediate(oldHud);
            for (int i = canvasGo.transform.childCount - 1; i >= 0; i--)
            {
                var child = canvasGo.transform.GetChild(i).gameObject;
                if (child.name == "Tageszeit" || child.name == "UI_GameHud" || child.name == "UI_WakeLevel" || child.name == "UI_NewDay")
                    Object.DestroyImmediate(child);
            }

            var hud = (GameObject)PrefabUtility.InstantiatePrefab(hudPrefab, canvasGo.transform);
            var wake = (GameObject)PrefabUtility.InstantiatePrefab(wakePrefab, canvasGo.transform);
            var day = (GameObject)PrefabUtility.InstantiatePrefab(dayPrefab, canvasGo.transform);
            day.SetActive(false);

            var dbg = canvasGo.GetComponent<NwGameHudDebug>();
            if (dbg == null) dbg = canvasGo.AddComponent<NwGameHudDebug>();
            SetField(dbg, "hud", hud.GetComponent<NwGameHud>());
            SetField(dbg, "wake", wake.GetComponent<NwWakeLevel>());
            SetField(dbg, "newDay", day.GetComponent<NwNewDay>());

            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            Debug.Log("[HUD Neu] HUD in Szene eingebaut: " + scene.name);
        }
    }
}
