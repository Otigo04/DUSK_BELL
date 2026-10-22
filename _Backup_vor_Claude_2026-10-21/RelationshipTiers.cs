using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Dialogue
{
    /// <summary>Eine Beziehungsstufe ab einem Mindestwert, z. B. "Freundlich" ab +3.</summary>
    [Serializable]
    public class RelationshipTier
    {
        [Tooltip("Fester Schluessel fuer Code und Bedingungen, z. B. 'freundlich'. Nie aendern")]
        public string id;
        [Tooltip("Ab diesem Wert gilt die Stufe (bis zur naechsten)")]
        [Range(Relationships.Min, Relationships.Max)] public int minValue;
        public string label;
        [Tooltip("Weibliche Form, leer = wie label")]
        public string labelFemale;
        public Color color = Color.white;

        public string Label(NpcGender gender) =>
            gender == NpcGender.Weiblich && !string.IsNullOrEmpty(labelFemale) ? labelFemale : label;
    }

    /// <summary>
    /// Stufen der Beziehung (-10 bis +10) mit Namen und Farbe fuer die UI.
    /// Ein Asset unter Resources/RelationshipTiers ersetzt die eingebauten Stufen, ohne Code anzufassen.
    /// Weitere Regeln (z. B. ab welchem Wert ein Date moeglich ist) stehen ebenfalls hier.
    /// </summary>
    [CreateAssetMenu(menuName = "Nightward/Beziehungsstufen", fileName = "RelationshipTiers")]
    public class RelationshipTiers : ScriptableObject
    {
        [Tooltip("Aufsteigend nach minValue. Die erste Stufe sollte bei -10 beginnen")]
        public List<RelationshipTier> tiers = new List<RelationshipTier>();
        [Tooltip("Ab diesem Wert kann ein NPC mit 'romanceable' z. B. auf ein Date eingeladen werden")]
        [Range(Relationships.Min, Relationships.Max)] public int romanceMinimum = Relationships.Max;

        static RelationshipTiers active;

        /// <summary>Asset aus Resources, sonst die eingebauten Standardstufen.</summary>
        public static RelationshipTiers Active
        {
            get
            {
                if (active != null) return active;
                active = Resources.Load<RelationshipTiers>("RelationshipTiers");
                if (active == null || active.tiers.Count == 0) active = CreateDefault();
                active.Sort();
                return active;
            }
            set => active = value;
        }

        static Color Hex(string h)
        {
            ColorUtility.TryParseHtmlString(h, out var c);
            return c;
        }

        static RelationshipTier T(string id, int min, string label, string female, string color) =>
            new RelationshipTier { id = id, minValue = min, label = label, labelFemale = female, color = Hex(color) };

        public static RelationshipTiers CreateDefault()
        {
            var t = CreateInstance<RelationshipTiers>();
            t.name = "RelationshipTiers (Standard)";
            t.hideFlags = HideFlags.DontSave;
            t.tiers = new List<RelationshipTier>
            {
                T("feindselig", -10, "Feindselig", null, "#d64a6a"),
                T("misstrauisch", -6, "Misstrauisch", null, "#ffa550"),
                T("neutral", -2, "Neutral", null, "#b89a72"),
                T("freundlich", 3, "Freundlich", null, "#9ab87a"),
                T("befreundet", 5, "Guter Freund", "Gute Freundin", "#6e9a5e"),
                T("vertraut", 8, "Bester Freund", "Beste Freundin", "#ffd27a"),
            };
            return t;
        }

        void Sort() => tiers.Sort((a, b) => a.minValue.CompareTo(b.minValue));

        public RelationshipTier Get(int value)
        {
            RelationshipTier found = tiers.Count > 0 ? tiers[0] : null;
            foreach (var tier in tiers)
                if (value >= tier.minValue) found = tier;
            return found;
        }

        public int IndexOf(int value) => tiers.IndexOf(Get(value));

        public RelationshipTier Find(string id) => tiers.Find(t => t.id == id);
    }
}
