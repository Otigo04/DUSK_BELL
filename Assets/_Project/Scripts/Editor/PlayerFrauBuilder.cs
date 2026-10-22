using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Setzt die Hauptfigur Frau als Spielerfigur ein: schneidet ihre Idle-/Walk-Sheets, baut den 8-Richtungs-Controller
    /// (gleiche Bauweise wie bei den NPCs) und tauscht Controller und Sprite am "Visual" des Player-Prefabs.
    /// Fuer die Schlaege gibt es noch keine Frau-Animation: punch1-3 zeigen vorerst das Standbild in Blickrichtung.
    /// </summary>
    public static class PlayerFrauBuilder
    {
        const string AnimDir = "Assets/_Project/Art/Animations/Hauptfigur_Frau/";
        const string PlayerPrefab = "Assets/_Project/Prefabs/Characters/Player.prefab";
        static readonly string[] Dirs = { "S", "SW", "W", "NW", "N", "NE", "E", "SE" };

        [MenuItem("Nightward/Spieler/Hauptfigur Frau einsetzen")]
        public static void Apply()
        {
            AssetDatabase.Refresh();
            var ctrl = NpcCastBuilder.Controller("Hauptfigur_Frau", new[]
            {
                new NpcCastBuilder.Clip("idle", "Hauptfiguren/Frau/frau_idle.png", 56, 6, true),
                new NpcCastBuilder.Clip("walk", "Hauptfiguren/Frau/frau_walk.png", 56, 10, true),
            });
            AddPunchPlaceholders(ctrl);

            var root = PrefabUtility.LoadPrefabContents(PlayerPrefab);
            try
            {
                var visual = root.transform.Find("Visual");
                visual.GetComponent<Animator>().runtimeAnimatorController = ctrl;
                visual.GetComponent<SpriteRenderer>().sprite = StateSprite(ctrl, "idle_S");
                PrefabUtility.SaveAsPrefabAsset(root, PlayerPrefab);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            AssetDatabase.SaveAssets();
            Debug.Log("[Spieler] Hauptfigur Frau eingesetzt.");
        }

        static void AddPunchPlaceholders(AnimatorController ctrl)
        {
            var sm = ctrl.layers[0].stateMachine;
            foreach (var d in Dirs)
            {
                var sprite = StateSprite(ctrl, "idle_" + d);
                if (sprite == null) continue;
                for (int combo = 1; combo <= 3; combo++)
                {
                    string name = $"punch{combo}_{d}";
                    var clip = new AnimationClip { frameRate = 12f, name = name };
                    AnimationUtility.SetObjectReferenceCurve(clip, EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite"),
                        new[] { new ObjectReferenceKeyframe { time = 0f, value = sprite } });
                    AssetDatabase.CreateAsset(clip, AnimDir + name + ".anim");
                    sm.AddState(name).motion = clip;
                }
            }
            EditorUtility.SetDirty(ctrl);
            AssetDatabase.SaveAssets();
        }

        static Sprite StateSprite(AnimatorController ctrl, string state)
        {
            foreach (var st in ctrl.layers[0].stateMachine.states)
            {
                if (st.state.name != state) continue;
                var keys = AnimationUtility.GetObjectReferenceCurve((AnimationClip)st.state.motion, EditorCurveBinding.PPtrCurve("", typeof(SpriteRenderer), "m_Sprite"));
                return keys.Length > 0 ? (Sprite)keys[0].value : null;
            }
            return null;
        }
    }
}
