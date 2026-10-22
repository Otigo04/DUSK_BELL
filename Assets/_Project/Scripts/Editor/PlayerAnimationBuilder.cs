using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Haengt alle Kampf-, Lauf- und Ausweich-Animationen der Hauptfiguren (Mann, Frau) an ihre Animator-Controller:
    /// run, sprint, punch1-3, knife1-2, bat, shoot, club, crowbar, chop, flail, machete1-2, rifle, shotgun, assault, sniper, dodge (zusaetzlich zu idle, walk, interact). Zustaende heissen
    /// "&lt;anim&gt;_&lt;Richtung&gt;" (S, SW, W, NW, N, NE, E, SE). Bestehende Controller bleiben erhalten (gleiche Guids,
    /// Prefab und Opening verweisen darauf), vorhandene Zustaende bekommen nur neue Clips. Idempotent.
    /// Quelle der Sheets: Art/Characters/Hauptfiguren/_Quelle_Generator (gen_hauptfiguren_combat.py, gen_dodge.py).
    /// </summary>
    public static class PlayerAnimationBuilder
    {
        const string CharDir = "Assets/_Project/Art/Characters/";
        const string AnimDir = "Assets/_Project/Art/Animations/";
        const int Cell = 56;
        static readonly string[] Dirs = { "S", "SW", "W", "NW", "N", "NE", "E", "SE" };

        struct Spec
        {
            public string state, file;
            public float fps;
            public bool loop;
            public Spec(string state, string file, float fps, bool loop) { this.state = state; this.file = file; this.fps = fps; this.loop = loop; }
        }

        static readonly Spec[] Specs =
        {
            new Spec("run", "run", 12f, true),
            new Spec("sprint", "sprint", 14f, true),
            new Spec("punch1", "punch1", 14f, false),
            new Spec("punch2", "punch2", 14f, false),
            new Spec("punch3", "punch3", 14f, false),
            new Spec("knife1", "knife1", 14f, false),
            new Spec("knife2", "knife2", 14f, false),
            new Spec("bat", "bat", 14f, false),
            new Spec("shoot", "shoot", 14f, false),
            new Spec("club", "club", 14f, false),
            new Spec("crowbar", "crowbar", 14f, false),
            new Spec("chop", "chop", 14f, false),
            new Spec("flail", "flail", 14f, false),
            new Spec("machete1", "machete1", 14f, false),
            new Spec("machete2", "machete2", 14f, false),
            new Spec("rifle", "rifle", 14f, false),
            new Spec("shotgun", "shotgun", 14f, false),
            new Spec("assault", "assault", 14f, false),
            new Spec("sniper", "sniper", 14f, false),
            new Spec("dodge", "dodge", 14f, false),
        };

        [MenuItem("Nightward/Spieler/Alle Kampf-, Lauf- und Ausweich-Animationen einbauen")]
        public static void BuildAll()
        {
            AssetDatabase.Refresh();
            Build("Hauptfigur_Frau", "Frau", "frau");
            Build("Hauptfigur_Mann", "Mann", "mann");
            AssetDatabase.SaveAssets();
            Debug.Log("[Spieler] Animationen fuer Frau und Mann eingebaut.");
        }

        static void Build(string controllerName, string folder, string prefix)
        {
            string ctrlPath = AnimDir + controllerName + "/" + controllerName + ".controller";
            var ctrl = AssetDatabase.LoadAssetAtPath<AnimatorController>(ctrlPath);
            if (ctrl == null) { Debug.LogError("[Spieler] Controller fehlt: " + ctrlPath); return; }
            var sm = ctrl.layers[0].stateMachine;

            // Fuesse sollen beim Wechsel nicht springen: Pivot wie das idle-Bild
            Vector2 pivot = IdlePivot(ctrl);

            foreach (var spec in Specs)
            {
                string sheet = $"{CharDir}Hauptfiguren/{folder}/{prefix}_{spec.file}.png";
                if (!File.Exists(sheet)) { Debug.LogWarning("[Spieler] Sheet fehlt: " + sheet); continue; }
                var frames = Slice(sheet, spec.state, pivot, out int cols);

                for (int r = 0; r < Dirs.Length; r++)
                {
                    var list = new List<Sprite>();
                    for (int c = 0; c < cols; c++) if (frames[r, c] != null) list.Add(frames[r, c]);
                    if (list.Count == 0) continue;

                    string stateName = spec.state + "_" + Dirs[r];
                    string clipPath = AnimDir + controllerName + "/" + stateName + ".anim";
                    var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
                    bool isNew = clip == null;
                    if (isNew) clip = new AnimationClip { name = stateName };
                    clip.frameRate = spec.fps;

                    var keys = new List<ObjectReferenceKeyframe>();
                    for (int i = 0; i < list.Count; i++) keys.Add(new ObjectReferenceKeyframe { time = i / spec.fps, value = list[i] });
                    // Schluesselbild am Ende, damit das letzte Bild seine volle Dauer behaelt
                    keys.Add(new ObjectReferenceKeyframe { time = list.Count / spec.fps, value = list[list.Count - 1] });
                    AnimationUtility.SetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite"), keys.ToArray());
                    var settings = AnimationUtility.GetAnimationClipSettings(clip);
                    settings.loopTime = spec.loop;
                    AnimationUtility.SetAnimationClipSettings(clip, settings);
                    if (isNew) AssetDatabase.CreateAsset(clip, clipPath); else EditorUtility.SetDirty(clip);

                    AnimatorState state = null;
                    foreach (var st in sm.states) if (st.state.name == stateName) state = st.state;
                    if (state == null) state = sm.AddState(stateName);
                    state.motion = clip;
                }
            }
            EditorUtility.SetDirty(ctrl);
        }

        static Vector2 IdlePivot(AnimatorController ctrl)
        {
            foreach (var st in ctrl.layers[0].stateMachine.states)
            {
                if (st.state.name != "idle_S") continue;
                var keys = AnimationUtility.GetObjectReferenceCurve((AnimationClip)st.state.motion, EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite"));
                if (keys.Length > 0 && keys[0].value is Sprite sp) return new Vector2(sp.pivot.x / sp.rect.width, sp.pivot.y / sp.rect.height);
            }
            return new Vector2(0.5f, 5f / Cell);
        }

        /// <summary>Schneidet ein Sheet (8 Zeilen S..SE, n Spalten, 56 px) in Sprites mit dem Namen "&lt;anim&gt;_&lt;Zeile&gt;_&lt;Spalte&gt;".</summary>
        static Sprite[,] Slice(string path, string anim, Vector2 pivot, out int cols)
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = 32;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.GetSourceTextureWidthAndHeight(out int tw, out int th);
            cols = tw / Cell;

            var tex = new Texture2D(2, 2);
            tex.LoadImage(File.ReadAllBytes(path));
            var metas = new List<SpriteMetaData>();
            for (int r = 0; r < Dirs.Length; r++)
                for (int c = 0; c < cols; c++)
                {
                    var rect = new Rect(c * Cell, th - (r + 1) * Cell, Cell, Cell);
                    if (IsEmpty(tex, rect)) continue;
                    metas.Add(new SpriteMetaData { name = $"{anim}_{r}_{c}", rect = rect, alignment = (int)SpriteAlignment.Custom, pivot = pivot });
                }
            Object.DestroyImmediate(tex);
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();

            var result = new Sprite[Dirs.Length, cols];
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path))
            {
                if (!(o is Sprite s) || !s.name.StartsWith(anim + "_")) continue;
                var parts = s.name.Substring(anim.Length + 1).Split('_');
                if (parts.Length != 2) continue;
                result[int.Parse(parts[0]), int.Parse(parts[1])] = s;
            }
            return result;
        }

        static bool IsEmpty(Texture2D tex, Rect rect)
        {
            var px = tex.GetPixels((int)rect.x, (int)rect.y, (int)rect.width, (int)rect.height);
            foreach (var p in px) if (p.a > 0.01f) return false;
            return true;
        }
    }
}
