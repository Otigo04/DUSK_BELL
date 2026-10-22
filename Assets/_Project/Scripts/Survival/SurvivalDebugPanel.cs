using System;
using System.Text;
using Nightward.DayNight;
using Nightward.Items;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Survival
{
    /// <summary>
    /// Balancing-Panel (nur Editor/Development-Build). F8 oeffnet es. Zeigt alle Werte mit ihrer aktuellen Rate, die Stimmungen,
    /// aktive Effekte und die Aufschluesselung einer Rate; per Schieber, Knopf oder Verbrauchsgut laesst sich alles manipulieren.
    /// </summary>
    public class SurvivalDebugPanel : MonoBehaviour
    {
        [SerializeField] Key toggleKey = Key.F8;
        [SerializeField] bool startOpen;

        SurvivalSystem system;
        bool open;
        StatId inspected = StatId.Thirst;
        Vector2 scroll;
        GUIStyle label, small;
        readonly StringBuilder sb = new StringBuilder();

        void Awake()
        {
            system = GetComponent<SurvivalSystem>();
            open = startOpen;
        }

#if UNITY_EDITOR || DEVELOPMENT_BUILD
        void Update()
        {
            if (Keyboard.current != null && Keyboard.current[toggleKey].wasPressedThisFrame)
            {
                open = !open;
                if (system != null) system.CaptureBreakdown = open;
            }
        }

        void OnGUI()
        {
            if (!open || system == null || system.Sim == null) return;
            var sim = system.Sim;
            float k = Mathf.Max(1f, Screen.height / 720f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(k, k, 1f));
            if (label == null)
            {
                label = new GUIStyle(GUI.skin.label) { fontSize = 12 };
                small = new GUIStyle(GUI.skin.label) { fontSize = 11, normal = { textColor = new Color(0.8f, 0.8f, 0.85f) } };
            }

            float h = Screen.height / k;
            GUILayout.BeginArea(new Rect(8, 8, 430, h - 16), GUI.skin.box);
            scroll = GUILayout.BeginScrollView(scroll);

            GUILayout.Label($"SURVIVAL  {sim.Activity}  | Spielstunden {sim.TotalGameHours:0.0}  | {(sim.IsDead ? "TOT" : sim.IsWinded ? "ausser Atem" : "ok")}", label);
            GUILayout.BeginHorizontal();
            system.GodMode = GUILayout.Toggle(system.GodMode, "Unverwundbar");
            GUILayout.Label($"Zeit x{system.HoursScale:0.0}", label, GUILayout.Width(70));
            system.HoursScale = GUILayout.HorizontalSlider(system.HoursScale, 0f, 20f, GUILayout.Width(120));
            GUILayout.EndHorizontal();
            var cyc = DayNightCycle.Instance;
            if (cyc != null)
            {
                GUILayout.BeginHorizontal();
                GUILayout.Label($"Tag {cyc.Day} {cyc.Phase}  x{cyc.TimeScale:0}", label, GUILayout.Width(150));
                cyc.TimeScale = GUILayout.HorizontalSlider(cyc.TimeScale, 0f, 60f, GUILayout.Width(150));
                GUILayout.EndHorizontal();
            }

            GUILayout.Space(4);
            foreach (StatId id in Enum.GetValues(typeof(StatId)))
            {
                var d = sim.Def(id);
                if (d == null) continue;
                GUILayout.BeginHorizontal();
                if (GUILayout.Button(id == inspected ? ">" : " ", GUILayout.Width(22))) inspected = id;
                GUILayout.Label($"{d.displayName,-22}", label, GUILayout.Width(150));
                float v = GUILayout.HorizontalSlider(sim.Value(id), d.min, d.max, GUILayout.Width(120));
                if (Mathf.Abs(v - sim.Value(id)) > 0.001f) sim.Set(id, v);
                string unit = d.unit == RateUnit.PerSecond ? "/s" : "/h";
                GUILayout.Label($"{sim.Value(id),5:0.0}  {sim.CurrentRate(id):+0.00;-0.00;0.00}{unit}", small, GUILayout.Width(110));
                GUILayout.EndHorizontal();
            }

            GUILayout.Space(4);
            sb.Clear();
            foreach (MoodId id in Enum.GetValues(typeof(MoodId)))
            {
                var m = sim.Mood(id);
                if (m.IsActive) sb.Append(id).Append(' ').Append(m.ToString()).Append("   ");
            }
            GUILayout.Label("Stimmungen: " + (sb.Length > 0 ? sb.ToString() : "-"), label);

            sb.Clear();
            foreach (ContextFlag f in Enum.GetValues(typeof(ContextFlag))) if (sim.Has(f)) sb.Append(f).Append(' ');
            GUILayout.Label("Flags: " + sb, small);

            sb.Clear();
            foreach (var b in sim.Buffs) sb.Append(b.id).Append(' ').Append(b.remainingHours.ToString("0.0")).Append("h  ");
            GUILayout.Label("Effekte: " + (sb.Length > 0 ? sb.ToString() : "-"), small);

            GUILayout.Label($"Spiel: Tempo x{sim.Mult(EffectKind.MoveSpeedMult):0.00}  Ausdauerkosten x{sim.Mult(EffectKind.StaminaCostMult):0.00}  " +
                            $"Schaden x{sim.Mult(EffectKind.DamageDealtMult):0.00}  Taumeln {sim.Sum(EffectKind.ControlSway):0.00}  Halluz. {sim.Sum(EffectKind.Hallucination):0.00}", small);

            GUILayout.Space(4);
            GUILayout.Label($"Posten fuer {sim.Def(inspected).displayName}:", label);
            foreach (var e in sim.Breakdown)
            {
                bool match = e.stat == inspected && EffectKinds.UsesStat(e.kind);
                if (!match) continue;
                string lv = e.level != 0 ? (e.level > 0 ? $" (Stufe {e.level})" : $" (positiv {-e.level})") : "";
                GUILayout.Label($"  {e.source}{lv}: {e.kind} {e.value:+0.##;-0.##}", small);
            }

            GUILayout.Space(4);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("1 Leben Schaden")) sim.TakeLifePoints(1);
            if (GUILayout.Button("Heilen")) sim.Heal(100f);
            if (GUILayout.Button("Alles auf Start")) sim.ResetValues();
            if (GUILayout.Button("Wiederbeleben")) sim.Revive();
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Schlafen (8 h)")) sim.Sleep(8f, system.SecondsPerHour);
            if (GUILayout.Button("+1 h")) sim.FastForward(1f, system.SecondsPerHour);
            if (GUILayout.Button("+6 h")) sim.FastForward(6f, system.SecondsPerHour);
            if (GUILayout.Button("Gespraech")) sim.RegisterConversation("debug");
            GUILayout.EndHorizontal();

            var inv = PlayerInventory.Instance;
            var db = inv != null ? inv.Database : null;
            if (db != null)
            {
                GUILayout.Label("Gegenstaende ins Inventar (Shift = ganzer Stapel):", label);
                var shift = Keyboard.current != null && Keyboard.current.shiftKey.isPressed;
                foreach (ItemCategory cat in Enum.GetValues(typeof(ItemCategory)))
                {
                    int col = 0;
                    foreach (var it in db.items)
                    {
                        if (it == null || it.category != cat) continue;
                        if (col == 0)
                        {
                            GUILayout.Label(cat.ToString(), small);
                            GUILayout.BeginHorizontal();
                        }
                        if (GUILayout.Button(it.displayName, GUILayout.Width(92)))
                            inv.Give(it, shift ? it.maxStack : 1);
                        if (++col % 4 == 0) { GUILayout.EndHorizontal(); GUILayout.BeginHorizontal(); }
                    }
                    if (col > 0) GUILayout.EndHorizontal();
                }
            }

            // Verbrauchsgueter ohne Gegenstand lassen sich nur sofort anwenden
            GUILayout.Label("Nur sofort (kein Gegenstand):", label);
            int col2 = 0;
            GUILayout.BeginHorizontal();
            foreach (var c in sim.Config.consumables)
            {
                if (db != null && HasItemFor(db, c.id)) continue;
                if (GUILayout.Button(c.displayName, GUILayout.Width(92)))
                    sim.Consume(c);
                if (++col2 % 4 == 0) { GUILayout.EndHorizontal(); GUILayout.BeginHorizontal(); }
            }
            GUILayout.EndHorizontal();

            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        static bool HasItemFor(ItemDatabase db, string consumableId)
        {
            foreach (var it in db.items) if (it != null && it.consumableId == consumableId) return true;
            return false;
        }
#endif
    }
}
