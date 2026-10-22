using Nightward.Dialogue;
using Nightward.Interaction;
using Nightward.Opening;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Baut die erste Story-Szene in Level_01: Pickup, Ankunfts-UI, Dialog mit den Sprechern (Bulut, Ilhan, das Monster am Fenster)
    /// und den ArrivalDirector, der alles verdrahtet. Die Figuren (Bulut, Ilhan, Mara, David, Veronica, Can) kommen aus dem DorfBuilder
    /// und werden zur Laufzeit per Name gefunden. Laeuft automatisch am Ende von "Dorf bauen" und kann einzeln im Menue gestartet werden.
    /// </summary>
    public static class ArrivalBuilder
    {
        const string ScenePath = "Assets/_Project/Scenes/Game/Level_01.unity";
        const string Art = "Assets/_Project/Art";
        const string NpcData = "Assets/_Project/Data/NPCs/";
        const string BulutPortraits = Art + "/Characters/BULUT SHERIFF/portraits/";
        const int OrderObjects = 4;   // wie DorfBuilder.OrderObjects

        [MenuItem("Nightward/Story/Ankunft in Level_01 bauen")]
        public static void Build()
        {
            if (EditorApplication.isPlaying) { Debug.LogWarning("[Ankunft] Bitte erst den Play-Modus beenden."); return; }
            var scene = SceneManager.GetSceneByPath(ScenePath);
            if (!scene.IsValid() || !scene.isLoaded) scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Additive);
            var previous = SceneManager.GetActiveScene();
            SceneManager.SetActiveScene(scene);
            try
            {
                BuildInto(scene);
                EditorSceneManager.SaveScene(scene);
            }
            finally { if (previous.IsValid() && previous.isLoaded) SceneManager.SetActiveScene(previous); }
        }

        [MenuItem("Nightward/Story/Ankunft beim naechsten Play abspielen")]
        public static void PlayNext()
        {
            ArrivalState.Pending = true;
            Debug.Log("[Ankunft] Pending gesetzt: Level_01 starten (Play) spielt die erste Story-Szene.");
        }

        /// <summary>Baut die Ankunft in die (aktive) Szene. Ersetzt eine fruehere Ankunft.</summary>
        public static void BuildInto(Scene scene)
        {
            foreach (var g in scene.GetRootGameObjects())
                if (g.name == "Ankunft" || g.name == "UI_Ankunft" || g.name == "UI_Opening" || g.name == "UI_Uebergang")
                    Object.DestroyImmediate(g);

            GameObject player = null, hud = null;
            foreach (var g in scene.GetRootGameObjects())
            {
                if (g.name == "Player") player = g;
                else if (g.name == "HUD") hud = g;
            }
            if (player == null) { Debug.LogError("[Ankunft] Kein Player in Level_01."); return; }
            var interactor = player.GetComponent<PlayerInteractor>();
            var playerAnimator = player.GetComponentInChildren<Animator>();
            if (player.GetComponent<Player.PlayerActionAnimation>() == null) player.AddComponent<Player.PlayerActionAnimation>();

            var womanCtrl = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(Art + "/Animations/Hauptfigur_Frau/Hauptfigur_Frau.controller");
            var manCtrl = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(Art + "/Animations/Hauptfigur_Mann/Hauptfigur_Mann.controller");

            var root = new GameObject("Ankunft");
            var audio = root.AddComponent<OpeningAudio>();

            // ---------- Dialog mit mehreren Sprechern
            var view = Object.FindAnyObjectByType<DialogueView>();
            var bulutProfile = AssetDatabase.LoadAssetAtPath<NpcProfile>(NpcData + "NpcProfile_bulut.asset");
            var ilhanProfile = AssetDatabase.LoadAssetAtPath<NpcProfile>(NpcData + "NpcProfile_ilhan_bartender.asset");
            var monsterProfile = AssetDatabase.LoadAssetAtPath<NpcProfile>(NpcData + "NpcProfile_der_gast.asset");
            var dialogue = root.AddComponent<ScriptedDialogue>();
            var dso = new SerializedObject(dialogue);
            dso.FindProperty("view").objectReferenceValue = view;
            dso.FindProperty("audioPlayer").objectReferenceValue = audio;
            // Bulut guckt ernst, nicht traurig: "tense" und "cold" zeigen beide das ernste Gesicht
            var exprs = new[] { ("tense", "bulut_stern.png"), ("cold", "bulut_stern.png"), ("suspicious", "bulut_skeptical.png"), ("angry", "bulut_angry.png") };
            var ex = dso.FindProperty("expressions");
            ex.arraySize = exprs.Length;
            for (int i = 0; i < exprs.Length; i++)
            {
                var e = ex.GetArrayElementAtIndex(i);
                e.FindPropertyRelative("tag").stringValue = exprs[i].Item1;
                e.FindPropertyRelative("sprite").objectReferenceValue = OpeningBuilder.PortraitSprite(BulutPortraits + exprs[i].Item2);
            }
            var voices = dso.FindProperty("voices");
            voices.arraySize = 2;
            void Voice(int i, string speaker, NpcProfile profile, float pitch)
            {
                var v = voices.GetArrayElementAtIndex(i);
                v.FindPropertyRelative("speaker").stringValue = speaker;
                v.FindPropertyRelative("profile").objectReferenceValue = profile;
                v.FindPropertyRelative("pitch").floatValue = pitch;
            }
            Voice(0, "Ilhan", ilhanProfile, 0.95f);
            Voice(1, "Monster", monsterProfile, 0.6f);
            dso.ApplyModifiedPropertiesWithoutUndo();

            // ---------- UI (Fade, Erzaehler, Hinweise, Quest-HUD), eine Wurzel zum Ein- und Ausschalten
            var ui = OpeningBuilder.BuildUI(interactor, womanCtrl, manCtrl, audio, out _, out var questHud, out _);
            var uiRoot = new GameObject("UI_Ankunft");
            foreach (var g in scene.GetRootGameObjects())
                if (g.name == "UI_Opening" || g.name == "UI_Uebergang") g.transform.SetParent(uiRoot.transform, false);

            // ---------- Auto
            var carGo = CarArt.Create(root.transform, new Vector3(34.5f, -14f, 0f), OrderObjects);
            carGo.SetActive(false);
            var car = carGo.GetComponent<CarController>();
            var cso = new SerializedObject(car);
            cso.FindProperty("audioPlayer").objectReferenceValue = audio;
            cso.ApplyModifiedPropertiesWithoutUndo();

            // ---------- Director
            var director = root.AddComponent<ArrivalDirector>();
            var so = new SerializedObject(director);
            void Set(string prop, Object value) { var p = so.FindProperty(prop); if (p != null) p.objectReferenceValue = value; else Debug.LogWarning("[Ankunft] Feld fehlt: " + prop); }
            Set("ui", ui);
            Set("questHud", questHud);
            Set("dialogue", dialogue);
            Set("audioPlayer", audio);
            Set("uiRoot", uiRoot);
            Set("hudRoot", hud);
            Set("player", interactor);
            Set("playerAnimator", playerAnimator);
            Set("womanController", womanCtrl);
            Set("manController", manCtrl);
            Set("car", car);
            Set("bulutProfile", bulutProfile);
            Set("ilhanProfile", ilhanProfile);
            so.ApplyModifiedPropertiesWithoutUndo();

            EditorSceneManager.MarkSceneDirty(scene);
            Debug.Log("[Ankunft] Erste Story-Szene in Level_01 gebaut.");
        }
    }
}
