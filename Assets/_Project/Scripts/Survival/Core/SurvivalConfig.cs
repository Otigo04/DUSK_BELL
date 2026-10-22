using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Survival
{
    /// <summary>
    /// Alle Zahlen des Ueberlebens-Systems an einer Stelle: Werte, Stimmungen, Regeln, Verbrauchsgueter und Feinabstimmung.
    /// Ein Asset (Assets/_Project/Data/Balancing/SurvivalConfig.asset) ist die einzige Stelle zum Balancen.
    /// Ohne Asset laufen die Standardwerte aus SurvivalDefaults. Rechtsklick auf das Asset: "Auf Standardwerte zuruecksetzen".
    /// </summary>
    [CreateAssetMenu(fileName = "SurvivalConfig", menuName = "Nightward/Survival Config")]
    public class SurvivalConfig : ScriptableObject
    {
        public SurvivalTuning tuning = new SurvivalTuning();
        [Tooltip("Pro Wert: Grenzen, Startwert, Grundrate (pro Spielstunde oder pro Sekunde)")]
        public List<StatDef> stats = new List<StatDef>();
        [Tooltip("Stimmungen mit Stufen. Die Effekte jeder Stufe wirken, solange die Stufe aktiv ist")]
        public List<MoodDef> moods = new List<MoodDef>();
        [Tooltip("Wenn-dann-Regeln: Taetigkeit, Umwelt und Querwirkungen zwischen den Werten")]
        public List<Rule> rules = new List<Rule>();
        [Tooltip("Essen, Trinken, Medizin. Ansprechbar ueber die Id")]
        public List<ConsumableDef> consumables = new List<ConsumableDef>();

        public StatDef Stat(StatId id)
        {
            for (int i = 0; i < stats.Count; i++) if (stats[i].id == id) return stats[i];
            return null;
        }

        public MoodDef Mood(MoodId id)
        {
            for (int i = 0; i < moods.Count; i++) if (moods[i].id == id) return moods[i];
            return null;
        }

        public ConsumableDef Consumable(string id)
        {
            for (int i = 0; i < consumables.Count; i++) if (consumables[i].id == id) return consumables[i];
            return null;
        }

        public Rule Rule(string name)
        {
            for (int i = 0; i < rules.Count; i++) if (rules[i].name == name) return rules[i];
            return null;
        }

        /// <summary>Neue Config im Speicher mit allen Standardwerten (nicht als Asset gespeichert).</summary>
        public static SurvivalConfig CreateDefault()
        {
            var c = CreateInstance<SurvivalConfig>();
            c.hideFlags = HideFlags.DontSave;
            c.FillDefaults();
            return c;
        }

        [ContextMenu("Auf Standardwerte zuruecksetzen")]
        public void FillDefaults() => SurvivalDefaults.Fill(this);

        // Unity ruft Reset beim Anlegen des Assets auf
        void Reset() => FillDefaults();

        /// <summary>Fehlende Werte/Stimmungen aus den Standardwerten ergaenzen, damit nach neuen StatIds nichts fehlt.</summary>
        void OnValidate()
        {
            if (stats.Count == 0 && moods.Count == 0) return;
            var def = SurvivalDefaults.Create();
            foreach (var s in def.stats) if (Stat(s.id) == null) stats.Add(s);
            foreach (var m in def.moods) if (Mood(m.id) == null) moods.Add(m);
            foreach (var m in moods)
            {
                if (m.thresholds == null || m.thresholds.Length != 4) m.thresholds = new[] { 0.25f, 0.5f, 0.75f, 0.9f };
                else System.Array.Sort(m.thresholds);
                if (m.positiveThresholds != null && m.positiveThresholds.Length == 2) System.Array.Sort(m.positiveThresholds);
                while (m.stages.Count < 4) m.stages.Add(new MoodStage());
                while (m.positiveStages.Count < 2 && m.positiveThresholds != null && m.positiveThresholds.Length == 2) m.positiveStages.Add(new MoodStage());
            }
            tuning.lifePoints = Mathf.Max(1, tuning.lifePoints);
        }
    }
}
