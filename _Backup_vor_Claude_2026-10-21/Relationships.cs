using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Dialogue
{
    /// <summary>
    /// Beziehungen (-10 bis +10, Start 0) und Story-Flags ("ilhan_kennengelernt").
    /// Grundsaetzlich zwischen zwei beliebigen Figuren (IDs aus dem NpcProfile, der Spieler ist <see cref="Player"/>),
    /// die Kurzformen ohne zweite ID meinen immer Spieler und NPC. Jede Antwort im Dialog kann die Beziehung veraendern.
    /// Stufen und Namen kommen aus <see cref="RelationshipTiers"/>. Haelt nur den Laufzeitstand,
    /// fuers Speichern gibt es <see cref="Capture"/> und <see cref="Restore"/>.
    /// </summary>
    public static class Relationships
    {
        public const int Min = -10;
        public const int Max = 10;
        public const string Player = "spieler";

        static readonly Dictionary<string, int> values = new Dictionary<string, int>();
        static readonly HashSet<string> flags = new HashSet<string>();

        /// <summary>Beziehung Spieler - NPC: npcId, neuer Wert, Aenderung</summary>
        public static event Action<string, int, int> Changed;
        /// <summary>Jede Beziehung, auch NPC - NPC: a, b, neuer Wert, Aenderung</summary>
        public static event Action<string, string, int, int> PairChanged;
        /// <summary>Spieler - NPC hat die Stufe gewechselt: npcId, alte Stufe, neue Stufe</summary>
        public static event Action<string, RelationshipTier, RelationshipTier> TierChanged;
        public static event Action<string> FlagSet;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetAll()
        {
            values.Clear();
            flags.Clear();
            Changed = null;
            PairChanged = null;
            TierChanged = null;
            FlagSet = null;
        }

        // Reihenfolge egal: a-b ist dieselbe Beziehung wie b-a
        static string Key(string a, string b) => string.CompareOrdinal(a, b) <= 0 ? a + "|" + b : b + "|" + a;

        // ---------- Spieler - NPC ----------

        public static int Get(string npcId) => Get(Player, npcId);

        public static int Change(string npcId, int delta) => Change(Player, npcId, delta);

        public static int Set(string npcId, int value) => Set(Player, npcId, value);

        public static RelationshipTier Tier(string npcId) => RelationshipTiers.Active.Get(Get(npcId));

        /// <summary>Kurzbeschreibung fuer UI und Debug.</summary>
        public static string Describe(int value, NpcGender gender = NpcGender.Maennlich) =>
            RelationshipTiers.Active.Get(value)?.Label(gender) ?? "";

        /// <summary>Darf der Spieler z. B. zu einem Date einladen? NPC muss 'romanceable' sein und den Mindestwert erreichen.</summary>
        public static bool CanRomance(NpcProfile npc) =>
            npc != null && npc.romanceable && Get(npc.id) >= RelationshipTiers.Active.romanceMinimum;

        // ---------- beliebige Paare (auch NPC - NPC) ----------

        public static bool Has(string a, string b) => !string.IsNullOrEmpty(a) && !string.IsNullOrEmpty(b) && values.ContainsKey(Key(a, b));

        public static int Get(string a, string b) =>
            !string.IsNullOrEmpty(a) && !string.IsNullOrEmpty(b) && values.TryGetValue(Key(a, b), out var v) ? v : 0;

        public static int Change(string a, string b, int delta)
        {
            if (delta == 0) return Get(a, b);
            return Set(a, b, Get(a, b) + delta);
        }

        public static int Set(string a, string b, int value)
        {
            if (string.IsNullOrEmpty(a) || string.IsNullOrEmpty(b) || a == b) return 0;
            int before = Get(a, b);
            int after = Mathf.Clamp(value, Min, Max);
            values[Key(a, b)] = after;
            if (after == before) return after;

            PairChanged?.Invoke(a, b, after, after - before);
            string npc = a == Player ? b : b == Player ? a : null;
            if (npc != null)
            {
                Changed?.Invoke(npc, after, after - before);
                var tiers = RelationshipTiers.Active;
                var oldTier = tiers.Get(before);
                var newTier = tiers.Get(after);
                if (oldTier != newTier) TierChanged?.Invoke(npc, oldTier, newTier);
            }
            return after;
        }

        /// <summary>Startwert setzen, falls es noch keinen Wert gibt (ohne Events). Fuer NpcProfile.startRelationship.</summary>
        public static void Seed(string a, string b, int value)
        {
            if (value == 0 || string.IsNullOrEmpty(a) || string.IsNullOrEmpty(b) || a == b || Has(a, b)) return;
            values[Key(a, b)] = Mathf.Clamp(value, Min, Max);
        }

        // ---------- Flags ----------

        public static bool HasFlag(string flag) => !string.IsNullOrEmpty(flag) && flags.Contains(flag);

        public static void SetFlag(string flag)
        {
            if (string.IsNullOrEmpty(flag) || !flags.Add(flag)) return;
            FlagSet?.Invoke(flag);
        }

        public static void ClearFlag(string flag) => flags.Remove(flag);

        // ---------- Speichern ----------

        [Serializable]
        public class State
        {
            public List<string> keys = new List<string>();
            public List<int> values = new List<int>();
            public List<string> flags = new List<string>();
        }

        /// <summary>Kompletter Stand, z. B. fuer JsonUtility.ToJson.</summary>
        public static State Capture()
        {
            var s = new State();
            foreach (var kv in values) { s.keys.Add(kv.Key); s.values.Add(kv.Value); }
            s.flags.AddRange(flags);
            return s;
        }

        /// <summary>Ersetzt den Stand komplett. Loest keine Changed-Events aus.</summary>
        public static void Restore(State s)
        {
            values.Clear();
            flags.Clear();
            if (s == null) return;
            for (int i = 0; i < Mathf.Min(s.keys.Count, s.values.Count); i++) values[s.keys[i]] = Mathf.Clamp(s.values[i], Min, Max);
            foreach (var f in s.flags) flags.Add(f);
        }
    }
}
