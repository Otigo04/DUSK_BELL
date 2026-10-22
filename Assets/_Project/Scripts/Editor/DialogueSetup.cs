using System.Collections.Generic;
using Nightward.Dialogue;
using Nightward.Interaction;
using Nightward.NPC;
using Nightward.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Richtet das Dialogsystem ein: Portraet-Import, NPC-Profil und Beispieldialoge fuer Ilhan,
    /// Dialog-UI (aus den UI-Prefabs), PlayerInteractor am Spieler und Ilhan ansprechbar machen.
    /// Bestehende Dialog- und Profil-Assets werden nie ueberschrieben (eigene Aenderungen bleiben erhalten).
    ///
    /// Neuer NPC: NPC-Profil + Dialoge anlegen (Rechtsklick > Create > Nightward), NPC in der Szene waehlen,
    /// Menue "Nightward/Dialog/Auswahl ansprechbar machen", dann im NpcDialogue Profil und Dialoge eintragen.
    /// </summary>
    public static class DialogueSetup
    {
        const string DataDir = "Assets/_Project/Data";
        const string IconDir = "Assets/_Project/Art/UI/Icons";
        const string PortraitSheet = "Assets/_Project/Art/Characters/Ilhan/Ilhan_Portrait_Sheet.png";
        const string IlhanPrefab = "Assets/_Project/Prefabs/Characters/NPC_Ilhan.prefab";
        const string PlayerPrefab = "Assets/_Project/Prefabs/Characters/Player.prefab";
        const string DialogPrefab = "Assets/_Project/Prefabs/UI/UI_Dialogbox.prefab";
        const string ArrowSprite = "Assets/_Project/Art/UI/HUD/HUD_Pfeil_Weiter.png";
        const string PanelSprite = "Assets/_Project/Art/UI/Panels/Panel_Dialog.png";
        const string FontPath = "Assets/_Project/Art/UI/Font/Jersey10-Regular.ttf"; // schlanke Pixelschrift (OFL) nur fuer den Dialog
        const int TextSize = 12;
        const int NameSize = 24;   // Name im Schild doppelt so gross wie der Text
        const int PopupSize = 24;  // "+1" der Beziehungsleiste
        const string PlateFill = "Assets/_Project/Art/UI/Panels/Namensschild_Grund.png";
        const string PlateFrame = "Assets/_Project/Art/UI/Panels/Namensschild_Rahmen.png";
        const string MeterBar = "Assets/_Project/Art/UI/HUD/Beziehung_Leiste.png";
        const string MeterMarker = "Assets/_Project/Art/UI/HUD/Beziehung_Marker.png";
        const string MeterFlash = "Assets/_Project/Art/UI/HUD/Beziehung_Segment.png";
        const string UnlitMaterial = "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Unlit-Default.mat";

        [MenuItem("Nightward/Dialog/In Szene einrichten")]
        public static void Setup()
        {
            ImportArt();
            var profile = IlhanProfile();
            var entries = IlhanDialogues();

            BuildUI();
            EnsurePlayerInteractor();

            var contents = PrefabUtility.LoadPrefabContents(IlhanPrefab);
            MakeTalkable(contents, profile, entries);
            PrefabUtility.SaveAsPrefabAsset(contents, IlhanPrefab);
            PrefabUtility.UnloadPrefabContents(contents);

            AssetDatabase.SaveAssets();
            EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
            Debug.Log("[Dialog] eingerichtet.");
        }

        [MenuItem("Nightward/Dialog/UI neu bauen")]
        public static void RebuildUI()
        {
            BuildUI();
            EditorSceneManager.MarkSceneDirty(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
            Debug.Log("[Dialog] UI neu gebaut.");
        }

        [MenuItem("Nightward/Dialog/Auswahl ansprechbar machen")]
        static void MakeSelectionTalkable()
        {
            foreach (var go in Selection.gameObjects)
            {
                Undo.RegisterFullObjectHierarchyUndo(go, "Ansprechbar machen");
                MakeTalkable(go, null, null);
                EditorUtility.SetDirty(go);
            }
        }

        [MenuItem("Nightward/Dialog/Auswahl ansprechbar machen", true)]
        static bool CanMakeSelectionTalkable() => Selection.activeGameObject != null && Selection.activeGameObject.GetComponent<NpcBrain>() != null;

        // ------------------------------------------------------------------ Assets
        static void ImportArt()
        {
            AssetDatabase.Refresh();
            var ti = (TextureImporter)AssetImporter.GetAtPath(PortraitSheet);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = 100; // UI: 1 Pixel = 1 Canvas-Einheit
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            string[] names = { "Ilhan_Portrait_Ruhe", "Ilhan_Portrait_Mund_Halb", "Ilhan_Portrait_Mund_Offen", "Ilhan_Portrait_Blinzeln" };
            var metas = new SpriteMetaData[names.Length];
            for (int i = 0; i < names.Length; i++)
                metas[i] = new SpriteMetaData { name = names[i], rect = new Rect(i * 80, 0, 80, 80), alignment = (int)SpriteAlignment.Center, pivot = new Vector2(0.5f, 0.5f) };
#pragma warning disable CS0618
            ti.spritesheet = metas;
#pragma warning restore CS0618
            ti.SaveAndReimport();

            foreach (var icon in new[] { "Icon_Sprechen", "Icon_Taste_E" })
            {
                var ii = (TextureImporter)AssetImporter.GetAtPath($"{IconDir}/{icon}.png");
                ii.textureType = TextureImporterType.Sprite;
                ii.spriteImportMode = SpriteImportMode.Single;
                ii.spritePixelsPerUnit = 32;
                ii.filterMode = FilterMode.Point;
                ii.textureCompression = TextureImporterCompression.Uncompressed;
                ii.mipmapEnabled = false;
                ii.alphaIsTransparency = true;
                ii.SaveAndReimport();
            }
        }

        static Sprite Frame(string name)
        {
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(PortraitSheet))
                if (o is Sprite s && s.name == name) return s;
            return null;
        }

        static void EnsureFolder(string parent, string child)
        {
            if (!AssetDatabase.IsValidFolder(parent + "/" + child)) AssetDatabase.CreateFolder(parent, child);
        }

        static NpcProfile IlhanProfile()
        {
            EnsureFolder(DataDir, "NPCs");
            string path = DataDir + "/NPCs/NpcProfile_Ilhan.asset";
            var p = AssetDatabase.LoadAssetAtPath<NpcProfile>(path);
            if (p == null)
            {
                p = ScriptableObject.CreateInstance<NpcProfile>();
                p.id = "ilhan";
                p.displayName = "Ilhan";
                ColorUtility.TryParseHtmlString("#ffa550", out p.nameColor); // Laterne Orange: eigene Namensfarbe
                AssetDatabase.CreateAsset(p, path);
            }
            p.portraitIdle = Frame("Ilhan_Portrait_Ruhe");
            p.portraitTalk = new[] { Frame("Ilhan_Portrait_Mund_Halb"), Frame("Ilhan_Portrait_Mund_Offen") };
            p.portraitBlink = Frame("Ilhan_Portrait_Blinzeln");
            EditorUtility.SetDirty(p);
            return p;
        }

        // ------------------------------------------------------------------ Beispieldialoge
        static DialogueNode N(string id, Speaker s, string text, string next = null, int rel = 0, string flag = null, params DialogueChoice[] choices) =>
            new DialogueNode { id = id, speaker = s, text = text, next = next, relationship = rel, setFlag = flag, choices = new List<DialogueChoice>(choices) };

        static DialogueChoice C(string text, string next, int rel = 0, string flag = null) =>
            new DialogueChoice { text = text, next = next, relationship = rel, setFlag = flag };

        static DialogueAsset Dialog(string file, params DialogueNode[] nodes)
        {
            EnsureFolder(DataDir, "Dialoge");
            EnsureFolder(DataDir + "/Dialoge", "Ilhan");
            string path = $"{DataDir}/Dialoge/Ilhan/{file}.asset";
            var d = AssetDatabase.LoadAssetAtPath<DialogueAsset>(path);
            if (d != null) return d; // eigene Aenderungen nie ueberschreiben
            d = ScriptableObject.CreateInstance<DialogueAsset>();
            d.startNode = nodes[0].id;
            d.nodes = new List<DialogueNode>(nodes);
            AssetDatabase.CreateAsset(d, path);
            return d;
        }

        static List<DialogueEntry> IlhanDialogues()
        {
            var kennen = Dialog("Dialog_Ilhan_Kennenlernen",
                N("start", Speaker.Npc, "Hm? Ein neues Gesicht. Hierher verirrt sich kaum jemand, schon gar nicht freiwillig.", null, 0, "ilhan_kennengelernt",
                    C("Nur auf der Durchreise.", "reise"),
                    C("Freut mich! Wer bist du?", "name", 1),
                    C("Kümmer dich um deinen Kram.", "abweisend", -2)),
                N("reise", Speaker.Npc, "Durchreise, ja? Das haben die anderen auch gesagt. Der Wald lässt einen nicht so leicht gehen.", "name2"),
                N("name", Speaker.Npc, "Ilhan. Ich halte das Dorf mit Feuerholz am Leben. Ohne Holz kein Licht, und ohne Licht ... na ja.", "frage"),
                N("name2", Speaker.Npc, "Ich bin Ilhan, der Holzfäller. Merk dir den Namen, du wirst ihn noch brauchen.", "frage"),
                N("abweisend", Speaker.Npc, "Schon gut. Aber wenn es dunkel wird, bist du froh, dass hier jemand Holz hackt."),
                N("frage", Speaker.Npc, "Sag mal ... hast du keine Angst vor der Nacht?", null, 0, null,
                    C("Ein bisschen schon.", "ehrlich", 1),
                    C("Angst? Ich doch nicht.", "mutig"),
                    C("Was ist mit der Nacht?", "wissen", 0, "wissen_nacht")),
                N("ehrlich", Speaker.Npc, "Gut. Wer keine Angst hat, ist entweder dumm oder schon tot. Bleib in der Nähe der Laternen."),
                N("mutig", Speaker.Npc, "Das sagen alle, bis es an der Tür klopft. Und draußen lächelt jemand, der nicht lächeln sollte."),
                N("wissen", Speaker.Npc, "Nachts kommen sie aus dem Wald. Sie sehen aus wie wir. Nur das Grinsen ... das Grinsen stimmt nicht.", "wissen2"),
                N("wissen2", Speaker.Erzaehler, "Ilhan umklammert den Stiel seiner Axt etwas fester."));

            var kalt = Dialog("Dialog_Ilhan_Kalt",
                N("start", Speaker.Npc, "Was willst du? Ich hab zu tun.", null, 0, null,
                    C("Tut mir leid wegen vorhin.", "versoehnt", 2),
                    C("Nichts.", "nichts", -1)),
                N("versoehnt", Speaker.Npc, "... Schon gut. Jeder hat mal einen schlechten Tag. Auch Fremde."),
                N("nichts", Speaker.Npc, "Dann lass mich arbeiten."));

            var freundlich = Dialog("Dialog_Ilhan_Freundlich",
                N("start", Speaker.Npc, "Da bist du ja wieder! Brauchst du Holz, oder nur jemanden zum Reden?", null, 0, null,
                    C("Nur mal Hallo sagen.", "hallo", 1),
                    C("Gibt es Neuigkeiten?", "neu"),
                    C("Ich muss weiter.", "weiter")),
                N("hallo", Speaker.Npc, "Das ist nett. Hier sagt kaum noch jemand einfach Hallo."),
                N("neu", Speaker.Npc, "Am Waldrand waren Spuren im Matsch. Barfuß. Und viel zu groß für einen Menschen.", null, 0, "wissen_spuren"),
                N("weiter", Speaker.Npc, "Pass auf dich auf. Und sei vor der Dämmerung zuhause."));

            var alltag = Dialog("Dialog_Ilhan_Alltag",
                N("start", Speaker.Npc, "Das Holz hackt sich nicht von allein.", null, 0, null,
                    C("Kann ich helfen?", "helfen", 1),
                    C("Bis später.", "tschuess")),
                N("helfen", Speaker.Npc, "Ha! Mit den Händen? Komm wieder, wenn du Schwielen hast. Aber danke."),
                N("tschuess", Speaker.Npc, "Bis später. Und sei vor Einbruch der Nacht zuhause."));

            return new List<DialogueEntry>
            {
                new DialogueEntry { dialogue = kennen, onlyOnce = true },
                new DialogueEntry { dialogue = kalt, maxRelationship = -3 },
                new DialogueEntry { dialogue = freundlich, minRelationship = 2 },
                new DialogueEntry { dialogue = alltag, smallTalk = true },
            };
        }

        // ------------------------------------------------------------------ NPC und Spieler
        /// <summary>Haengt NpcDialogue, TalkBehavior und das Hinweis-Symbol an. Profil/Dialoge nur, wenn angegeben.</summary>
        public static void MakeTalkable(GameObject npc, NpcProfile profile, List<DialogueEntry> entries)
        {
            var dlg = npc.GetComponent<NpcDialogue>();
            if (dlg == null) dlg = npc.AddComponent<NpcDialogue>();
            var so = new SerializedObject(dlg);
            if (profile != null) so.FindProperty("profile").objectReferenceValue = profile;
            if (entries != null)
            {
                var list = so.FindProperty("dialogues");
                list.arraySize = entries.Count;
                for (int i = 0; i < entries.Count; i++)
                {
                    var e = list.GetArrayElementAtIndex(i);
                    e.FindPropertyRelative("dialogue").objectReferenceValue = entries[i].dialogue;
                    e.FindPropertyRelative("minRelationship").intValue = entries[i].minRelationship;
                    e.FindPropertyRelative("maxRelationship").intValue = entries[i].maxRelationship;
                    e.FindPropertyRelative("requireFlag").stringValue = entries[i].requireFlag ?? "";
                    e.FindPropertyRelative("forbidFlag").stringValue = entries[i].forbidFlag ?? "";
                    e.FindPropertyRelative("onlyOnce").boolValue = entries[i].onlyOnce;
                    e.FindPropertyRelative("smallTalk").boolValue = entries[i].smallTalk;
                }
            }
            so.ApplyModifiedPropertiesWithoutUndo();

            var talk = npc.GetComponent<TalkBehavior>();
            if (talk == null) talk = npc.AddComponent<TalkBehavior>();
            var ts = new SerializedObject(talk);
            ts.FindProperty("priority").intValue = 100;
            ts.ApplyModifiedPropertiesWithoutUndo();

            var t = npc.transform.Find("Interaktion");
            if (t == null)
            {
                t = new GameObject("Interaktion").transform;
                t.SetParent(npc.transform, false);
            }
            var sr = t.GetComponent<SpriteRenderer>();
            if (sr == null) sr = t.gameObject.AddComponent<SpriteRenderer>();
            sr.sortingLayerName = "Default";
            sr.sortingOrder = 25; // ueber Baumkronen und Partikeln
            var unlit = AssetDatabase.LoadAssetAtPath<Material>(UnlitMaterial);
            if (unlit != null) sr.sharedMaterial = unlit; // auch nachts gut sichtbar
            var ind = t.GetComponent<InteractionIndicator>();
            if (ind == null) ind = t.gameObject.AddComponent<InteractionIndicator>();
            var isd = new SerializedObject(ind);
            isd.FindProperty("target").objectReferenceValue = dlg;
            isd.FindProperty("nearbySprite").objectReferenceValue = AssetDatabase.LoadAssetAtPath<Sprite>($"{IconDir}/Icon_Sprechen.png");
            isd.FindProperty("inRangeSprite").objectReferenceValue = AssetDatabase.LoadAssetAtPath<Sprite>($"{IconDir}/Icon_Taste_E.png");
            isd.ApplyModifiedPropertiesWithoutUndo();
        }

        static void EnsurePlayerInteractor()
        {
            var contents = PrefabUtility.LoadPrefabContents(PlayerPrefab);
            if (contents.GetComponent<PlayerInteractor>() == null) contents.AddComponent<PlayerInteractor>();
            PrefabUtility.SaveAsPrefabAsset(contents, PlayerPrefab);
            PrefabUtility.UnloadPrefabContents(contents);
        }

        // ------------------------------------------------------------------ UI
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

        static Image SlicedImage(RectTransform rt, string spritePath)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(spritePath);
            img.type = Image.Type.Sliced;
            img.raycastTarget = false;
            return img;
        }

        static Image NativeImage(RectTransform rt, string spritePath)
        {
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(spritePath);
            img.raycastTarget = false;
            if (img.sprite != null) rt.sizeDelta = img.sprite.rect.size;
            return img;
        }

        static void AddShadow(GameObject go)
        {
            var sh = go.AddComponent<Shadow>();
            sh.effectColor = NwTheme.TextShadow;
            sh.effectDistance = new Vector2(1f, -1f);
        }

        static void AddOutline(GameObject go)
        {
            var o = go.AddComponent<Outline>();
            o.effectColor = NwTheme.TextShadow;
            o.effectDistance = new Vector2(1f, -1f);
        }

        static Text MakeText(RectTransform rt, Font font, int size, TextAnchor align)
        {
            var t = rt.gameObject.AddComponent<Text>();
            t.font = font;
            t.fontSize = size;
            t.alignment = align;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        /// <summary>Beziehungsleiste: Schild mit Stufenname und Leiste, darueber die "+1"-Anzeige.
        /// rightMid: rechte Kante, vertikale Mitte (liegt auf der unteren Boxkante), relativ zur Bildschirmmitte unten.</summary>
        /// <summary>Dunkle, fast deckende Flaeche (Hintergrund der Dialogbox), liegt hinter den folgenden Elementen.</summary>
        static void Backing(RectTransform parent, string name, Vector2 pos, Vector2 size)
        {
            var rt = RT(name, parent);
            rt.anchorMin = rt.anchorMax = rt.pivot = Vector2.zero;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            rt.SetAsFirstSibling();
            var img = rt.gameObject.AddComponent<Image>();
            img.color = new Color(NwTheme.TextShadow.r, NwTheme.TextShadow.g, NwTheme.TextShadow.b, 0.93f);
            img.raycastTarget = false;
        }

        static RelationshipMeter BuildMeter(RectTransform parent, Font font, Vector2 rightMid, float width, float height)
        {
            var root = RT("Beziehung", parent);
            root.anchorMin = root.anchorMax = new Vector2(0.5f, 0f);
            root.pivot = new Vector2(1f, 0.5f);
            root.anchoredPosition = rightMid;
            root.sizeDelta = new Vector2(width, height);
            var group = root.gameObject.AddComponent<CanvasGroup>();
            group.alpha = 0f;
            group.blocksRaycasts = false;
            group.interactable = false;

            var plateBg = RT("Grund", root);
            Stretch(plateBg);
            plateBg.offsetMin = new Vector2(2f, 2f);
            plateBg.offsetMax = new Vector2(-2f, -2f);
            var plateBgImg = plateBg.gameObject.AddComponent<Image>();
            plateBgImg.color = new Color(NwTheme.TextShadow.r, NwTheme.TextShadow.g, NwTheme.TextShadow.b, 0.95f);
            plateBgImg.raycastTarget = false;
            var plate = RT("Schild", root);
            Stretch(plate);
            SlicedImage(plate, PanelSprite);

            var labelRt = RT("Stufe", plate);
            labelRt.anchorMin = labelRt.anchorMax = labelRt.pivot = new Vector2(0f, 0.5f);
            labelRt.anchoredPosition = new Vector2(7f, 0f);
            labelRt.sizeDelta = new Vector2(64f, 14f);
            var label = MakeText(labelRt, font, TextSize, TextAnchor.MiddleLeft);
            AddShadow(label.gameObject);

            var barRt = RT("Leiste", plate);
            barRt.anchorMin = barRt.anchorMax = new Vector2(1f, 0f);
            barRt.pivot = Vector2.zero;
            NativeImage(barRt, MeterBar);
            barRt.anchoredPosition = new Vector2(-6f - barRt.sizeDelta.x, 5f);

            var flashRt = RT("Blitz", barRt);
            flashRt.anchorMin = flashRt.anchorMax = flashRt.pivot = Vector2.zero;
            var flash = NativeImage(flashRt, MeterFlash);

            var markerRt = RT("Marker", barRt);
            markerRt.anchorMin = markerRt.anchorMax = markerRt.pivot = Vector2.zero;
            NativeImage(markerRt, MeterMarker);

            // "+1" ueber dem Schild, rechtsbuendig; links daneben bei neuer Stufe deren Name
            var popup = RT("Aenderung", root);
            popup.anchorMin = popup.anchorMax = popup.pivot = new Vector2(1f, 1f);
            popup.anchoredPosition = new Vector2(-4f, 22f);
            popup.sizeDelta = new Vector2(width, 22f);
            popup.gameObject.AddComponent<CanvasGroup>().blocksRaycasts = false;
            var numRt = RT("Zahl", popup);
            numRt.anchorMin = numRt.anchorMax = numRt.pivot = new Vector2(1f, 0.5f);
            numRt.anchoredPosition = Vector2.zero;
            numRt.sizeDelta = new Vector2(40f, 22f);
            var num = MakeText(numRt, font, PopupSize, TextAnchor.MiddleRight);
            AddOutline(num.gameObject);
            var tierRt = RT("Stufe", popup);
            tierRt.anchorMin = tierRt.anchorMax = tierRt.pivot = new Vector2(1f, 0.5f);
            tierRt.anchoredPosition = new Vector2(-30f, 0f);
            tierRt.sizeDelta = new Vector2(width - 30f, 14f);
            var tier = MakeText(tierRt, font, TextSize, TextAnchor.MiddleRight);
            AddOutline(tier.gameObject);

            var meter = root.gameObject.AddComponent<RelationshipMeter>();
            var so = new SerializedObject(meter);
            so.FindProperty("group").objectReferenceValue = group;
            so.FindProperty("plate").objectReferenceValue = plate;
            so.FindProperty("bar").objectReferenceValue = barRt;
            so.FindProperty("marker").objectReferenceValue = markerRt;
            so.FindProperty("flash").objectReferenceValue = flash;
            so.FindProperty("label").objectReferenceValue = label;
            so.FindProperty("popup").objectReferenceValue = popup;
            so.FindProperty("popupText").objectReferenceValue = num;
            so.FindProperty("popupTier").objectReferenceValue = tier;
            so.ApplyModifiedPropertiesWithoutUndo();
            return meter;
        }

        static void ImportDialogSprites()
        {
            foreach (var (path, border) in new[] { (PlateFill, 5), (PlateFrame, 5), (MeterBar, 0), (MeterMarker, 0), (MeterFlash, 0) })
            {
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                if (ti == null) { Debug.LogWarning("[Dialog] Sprite fehlt: " + path + " (python build_dialog.py)"); continue; }
                ti.textureType = TextureImporterType.Sprite;
                ti.spriteImportMode = SpriteImportMode.Single;
                ti.spritePixelsPerUnit = 100;
                ti.filterMode = FilterMode.Point;
                ti.textureCompression = TextureImporterCompression.Uncompressed;
                ti.mipmapEnabled = false;
                ti.alphaIsTransparency = true;
                ti.spriteBorder = new Vector4(border, border, border, border);
                ti.SaveAndReimport();
            }
        }

        static void BuildUI()
        {
            AssetDatabase.Refresh();
            ImportDialogSprites();
            var old = GameObject.Find("UI_Dialog");
            if (old != null) Object.DestroyImmediate(old);
            var fontImporter = (TrueTypeFontImporter)AssetImporter.GetAtPath(FontPath);
            if (fontImporter.fontSize != TextSize || fontImporter.fontRenderingMode != FontRenderingMode.HintedRaster)
            {
                fontImporter.fontSize = TextSize;
                fontImporter.fontRenderingMode = FontRenderingMode.HintedRaster; // harte Pixelkanten
                fontImporter.SaveAndReimport();
            }
            var font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);

            var canvasGo = new GameObject("UI_Dialog", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasGo.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 110; // ueber dem HUD
            canvas.pixelPerfect = true;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(480, 270); // wie UI_Test und die Spielkamera
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            scaler.referencePixelsPerUnit = 100;
            var root = canvasGo.AddComponent<NwUIRoot>();
            var rso = new SerializedObject(root);
            rso.FindProperty("pixelFont").objectReferenceValue = font;
            rso.ApplyModifiedPropertiesWithoutUndo();

            var viewRt = RT("Dialog", canvasGo.transform);
            Stretch(viewRt);
            var content = RT("Inhalt", viewRt);
            Stretch(content);

            // Layout (Referenz 480x270): alles bleibt unter der Bildschirmmitte.
            // Portraet links, Dialogbox gleich hoch rechts daneben; Antworten stehen unter dem Text in der Box.
            // Namensschild ragt oben links aus der Box, die Beziehungsleiste unten rechts (daher etwas Abstand nach unten).
            const float margin = 6f;
            const float bottomMargin = 16f;
            const float portraitFrame = 120f; // Portraet 112 (80-px-Vorlage x1,4), Rahmen 4 px
            const float gap = 4f;
            const float boxHeight = portraitFrame;
            float boxX = portraitFrame + gap;
            float blockWidth = 480f - 2f * margin;
            float boxWidth = blockWidth - boxX;
            const float textInset = 12f;   // links/rechts in der Box
            const float bodyTop = 16f;     // Abstand Textflaeche zur Oberkante der Box (unter dem Namensschild)
            const float bodyBottom = 14f;
            const float plateHeight = 22f; // Namensschild, zur Haelfte ueber der Box
            const float meterWidth = 188f, meterHeight = 26f;

            // Block mittig am unteren Rand: bleibt auch bei breiteren Bildschirmen zusammen
            var block = RT("Block", content);
            block.anchorMin = block.anchorMax = new Vector2(0.5f, 0f);
            block.pivot = new Vector2(0.5f, 0f);
            block.anchoredPosition = new Vector2(0f, bottomMargin);
            block.sizeDelta = new Vector2(blockWidth, portraitFrame);

            // Dialogbox aus dem Prefab (bleibt Prefab-Instanz, spaetere UI-Updates kommen automatisch mit)
            var boxGo = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(DialogPrefab), block);
            var boxRt = (RectTransform)boxGo.transform;
            boxRt.anchorMin = boxRt.anchorMax = boxRt.pivot = Vector2.zero;
            boxRt.anchoredPosition = new Vector2(boxX, 0f);
            boxRt.sizeDelta = new Vector2(boxWidth, boxHeight);
            // Deckender dunkler Grund hinter der Box: Text bleibt auch vor hellem/gruenem Hintergrund lesbar
            Backing(block, "Box_Grund", new Vector2(boxX + 2f, 2f), new Vector2(boxWidth - 4f, boxHeight - 4f));
            foreach (var t in boxGo.GetComponentsInChildren<Text>(true)) t.font = font;
            var box = boxGo.GetComponent<NwDialogBox>();
            var bso = new SerializedObject(box);
            var oldName = (Text)bso.FindProperty("nameText").objectReferenceValue;
            if (oldName != null) oldName.gameObject.SetActive(false); // Name steht jetzt im Schild
            var bodyRt = (RectTransform)bso.FindProperty("bodyRect").objectReferenceValue;
            bodyRt.offsetMin = new Vector2(textInset, bodyBottom);
            bodyRt.offsetMax = new Vector2(-textInset, -bodyTop);
            // Weiterpfeil links neben die Beziehungsleiste
            var arrowRt = ((Graphic)bso.FindProperty("arrow").objectReferenceValue).rectTransform;
            arrowRt.anchorMin = arrowRt.anchorMax = new Vector2(1f, 0f);
            arrowRt.pivot = Vector2.zero;
            arrowRt.anchoredPosition = new Vector2(-(meterWidth + 8f + 6f + arrowRt.rect.width), 6f);

            // Namensschild: oben links, halb ueber der Boxkante. Grund dunkel, Rahmen in der Namensfarbe
            var plate = RT("Namensschild", boxGo.transform);
            plate.anchorMin = plate.anchorMax = new Vector2(0f, 1f);
            plate.pivot = new Vector2(0f, 0.5f);
            plate.anchoredPosition = new Vector2(8f, 2f);
            plate.sizeDelta = new Vector2(60f, plateHeight);
            var plateBg = RT("Grund", plate);
            Stretch(plateBg);
            var plateBgImg = SlicedImage(plateBg, PlateFill);
            plateBgImg.color = NwTheme.TextShadow;
            var plateFrame = RT("Rahmen", plate);
            Stretch(plateFrame);
            var plateFrameImg = SlicedImage(plateFrame, PlateFrame);
            var nameRt = RT("Name", plate);
            Stretch(nameRt);
            nameRt.offsetMin = new Vector2(0f, 1f); // Pixelschrift sitzt optisch mittig
            var nameText = MakeText(nameRt, font, NameSize, TextAnchor.MiddleCenter);
            AddShadow(nameText.gameObject);

            bso.FindProperty("nameText").objectReferenceValue = nameText;
            bso.FindProperty("namePlate").objectReferenceValue = plate;
            bso.FindProperty("namePlateFrame").objectReferenceValue = plateFrameImg;
            bso.FindProperty("namePlatePadding").floatValue = 10f;
            bso.FindProperty("nameSize").intValue = NameSize;
            bso.FindProperty("bodySize").intValue = TextSize;
            bso.FindProperty("bodyTopWithName").floatValue = bodyTop;
            bso.FindProperty("bodyTopNoName").floatValue = 12f;
            bso.ApplyModifiedPropertiesWithoutUndo();

            // Portraet links unten
            Backing(block, "Portraet_Grund", new Vector2(2f, 2f), new Vector2(portraitFrame - 4f, portraitFrame - 4f));
            var frame = RT("Portraet_Rahmen", block);
            frame.anchorMin = frame.anchorMax = frame.pivot = Vector2.zero;
            frame.anchoredPosition = Vector2.zero;
            frame.sizeDelta = new Vector2(portraitFrame, portraitFrame);
            var frameImg = frame.gameObject.AddComponent<Image>();
            frameImg.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(PanelSprite);
            frameImg.type = Image.Type.Sliced;
            frameImg.raycastTarget = false;
            var portraitRt = RT("Portraet", frame);
            portraitRt.anchorMin = portraitRt.anchorMax = portraitRt.pivot = new Vector2(0.5f, 0.5f);
            portraitRt.sizeDelta = new Vector2(portraitFrame - 8f, portraitFrame - 8f);
            var portraitImg = portraitRt.gameObject.AddComponent<Image>();
            portraitImg.preserveAspect = true;
            portraitImg.raycastTarget = false;
            var portrait = portraitRt.gameObject.AddComponent<PortraitAnimator>();
            // Leuchtrahmen in der Namensfarbe, solange der NPC spricht
            var glowRt = RT("Portraet_Glanz", frame);
            Stretch(glowRt);
            var glowImg = SlicedImage(glowRt, PlateFrame);
            glowImg.color = new Color(1f, 1f, 1f, 0f);

            // Antworten: unten in der Box, unter dem Text (die Box reserviert den Platz beim Seitenumbruch)
            var choices = RT("Antworten", block);
            choices.anchorMin = choices.anchorMax = choices.pivot = Vector2.zero;
            choices.anchoredPosition = new Vector2(boxX + textInset - 4f, bodyBottom);
            choices.sizeDelta = new Vector2(boxWidth - 2f * (textInset - 4f), boxHeight - bodyTop - bodyBottom);
            var vlg = choices.gameObject.AddComponent<VerticalLayoutGroup>();
            vlg.spacing = 1f;
            vlg.childAlignment = TextAnchor.LowerLeft; // Antworten sitzen am unteren Boxrand, darueber bleibt der Text
            vlg.childControlWidth = true;
            vlg.childForceExpandWidth = true;
            vlg.childControlHeight = true;
            vlg.childForceExpandHeight = false;

            // Beziehungsleiste ausserhalb von Inhalt, damit eine Aenderung am Gespraechsende noch zu sehen ist
            // ueber der rechten oberen Ecke der Box, damit sie den Text nicht ueberdeckt
            var meter = BuildMeter(viewRt, font, new Vector2(blockWidth / 2f - 4f, bottomMargin + boxHeight + meterHeight / 2f + 4f), meterWidth, meterHeight);

            var view = viewRt.gameObject.AddComponent<DialogueView>();
            var vso = new SerializedObject(view);
            vso.FindProperty("content").objectReferenceValue = content.gameObject;
            vso.FindProperty("box").objectReferenceValue = boxGo.GetComponent<NwDialogBox>();
            vso.FindProperty("portraitPanel").objectReferenceValue = frame.gameObject;
            vso.FindProperty("portrait").objectReferenceValue = portrait;
            vso.FindProperty("portraitImage").objectReferenceValue = portraitImg;
            vso.FindProperty("portraitGlow").objectReferenceValue = glowImg;
            vso.FindProperty("choiceContainer").objectReferenceValue = choices;
            vso.FindProperty("choiceFont").objectReferenceValue = font;
            vso.FindProperty("choiceSize").intValue = TextSize;
            vso.FindProperty("choiceMarker").objectReferenceValue = AssetDatabase.LoadAssetAtPath<Sprite>(ArrowSprite);
            vso.FindProperty("relationMeter").objectReferenceValue = meter;
            vso.ApplyModifiedPropertiesWithoutUndo();

            var runner = canvasGo.AddComponent<DialogueRunner>();
            var rso2 = new SerializedObject(runner);
            rso2.FindProperty("view").objectReferenceValue = view;
            rso2.ApplyModifiedPropertiesWithoutUndo();

            if (Object.FindAnyObjectByType<EventSystem>() == null)
            {
                var es = new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
                es.GetComponent<InputSystemUIInputModule>().AssignDefaultActions();
            }
        }
    }
}
