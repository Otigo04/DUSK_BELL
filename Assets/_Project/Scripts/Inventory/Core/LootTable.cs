using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Items
{
    /// <summary>Ein moeglicher Fund: Gegenstand, Gewicht (je hoeher, desto haeufiger) und Menge von min bis max.</summary>
    [Serializable]
    public class LootEntry
    {
        public ItemDef item;
        [Min(0f)] public float weight = 1f;
        [Min(1)] public int min = 1;
        [Min(1)] public int max = 1;
    }

    /// <summary>
    /// Ein Wurf der Beute-Tabelle: mit der Wahrscheinlichkeit chance gibt es rollsMin bis rollsMax Ziehungen aus den Eintraegen.
    /// nothingWeight ist das Gewicht fuer "diesmal nichts" (leere Ziehung).
    /// </summary>
    [Serializable]
    public class LootPool
    {
        public string name = "Pool";
        [Range(0f, 1f)] public float chance = 1f;
        [Min(0)] public int rollsMin = 1;
        [Min(0)] public int rollsMax = 1;
        [Tooltip("Ein Gegenstand kann in diesem Pool nur einmal gezogen werden")]
        public bool unique = true;
        [Tooltip("Gewicht fuer 'nichts gezogen' (0 = jede Ziehung trifft)")]
        [Min(0f)] public float nothingWeight;
        public List<LootEntry> entries = new List<LootEntry>();
    }

    /// <summary>
    /// Beute-Tabelle als Asset (Roguelike-Prinzip): feste Funde (guaranteed) plus gewichtete Pools. Jeder Aufruf von Roll
    /// wuerfelt neu. luck verschiebt die Gewichte zu selteneren Gegenstaenden (0 = normal, 1 = Seltene doppelt so oft je Stufe).
    /// Neue Tabelle: Rechtsklick Create > Nightward > Loot Table. Reine Logik ohne Szene, deshalb testbar.
    /// </summary>
    [CreateAssetMenu(fileName = "Loot_Neu", menuName = "Nightward/Loot Table")]
    public class LootTable : ScriptableObject
    {
        [Tooltip("Kommt immer heraus (jeweils Menge min bis max)")]
        public List<LootEntry> guaranteed = new List<LootEntry>();
        public List<LootPool> pools = new List<LootPool>();

        /// <summary>Wuerfelt die Tabelle. Die Staepel sind schon auf die Stapelgroesse aufgeteilt.</summary>
        public List<ItemStack> Roll(System.Random rng, float luck = 0f)
        {
            var result = new List<ItemStack>();
            foreach (var g in guaranteed) AddEntry(result, g, rng);

            foreach (var pool in pools)
            {
                if (pool == null || pool.entries.Count == 0) continue;
                if (pool.chance < 1f && rng.NextDouble() > pool.chance) continue;
                int rolls = pool.rollsMax <= pool.rollsMin ? pool.rollsMin : rng.Next(pool.rollsMin, pool.rollsMax + 1);

                var open = new List<LootEntry>(pool.entries);
                for (int i = 0; i < rolls && open.Count > 0; i++)
                {
                    var pick = Pick(open, pool.nothingWeight, luck, rng);
                    if (pick == null) continue;
                    AddEntry(result, pick, rng);
                    if (pool.unique) open.Remove(pick);
                }
            }
            return result;
        }

        /// <summary>Zufallsgenerator fuer das Spiel (aus dem Unity-Zufall gesetzt, damit jeder Durchgang anders faellt).</summary>
        public static System.Random NewRng() => new System.Random(UnityEngine.Random.Range(int.MinValue, int.MaxValue));

        /// <summary>Wuerfelt und legt in den Behaelter (auf freie Plaetze, bei scatter an zufaellige). Gibt zurueck, wie viele Staepel nicht passten.</summary>
        public int RollInto(Inventory inv, System.Random rng, float luck = 0f, bool scatter = false)
        {
            int lost = 0;
            foreach (var s in Roll(rng, luck)) if (!Place(inv, s, rng, scatter)) lost++;
            return lost;
        }

        /// <summary>Legt einen Stapel in den Behaelter. scatter = zufaelliger freier Platz (Truhe wirkt "gefuellt" statt vorn sortiert).</summary>
        public static bool Place(Inventory inv, ItemStack s, System.Random rng, bool scatter)
        {
            if (scatter && inv.Accepts(0, s.def))
            {
                var free = new List<int>();
                for (int i = 0; i < inv.Size; i++) if (inv.Get(i) == null) free.Add(i);
                if (free.Count > 0)
                {
                    inv.Set(free[rng.Next(free.Count)], s);
                    return true;
                }
            }
            return inv.Add(s) <= 0;
        }

        // ------------------------------------------------------------------ Intern
        static LootEntry Pick(List<LootEntry> entries, float nothingWeight, float luck, System.Random rng)
        {
            float total = nothingWeight;
            foreach (var e in entries) total += Weight(e, luck);
            if (total <= 0f) return null;
            float r = (float)rng.NextDouble() * total;
            if (r < nothingWeight) return null;
            r -= nothingWeight;
            foreach (var e in entries)
            {
                r -= Weight(e, luck);
                if (r < 0f) return e;
            }
            return entries[entries.Count - 1];
        }

        static float Weight(LootEntry e, float luck)
        {
            if (e == null || e.item == null) return 0f;
            return Mathf.Max(0f, e.weight * (1f + luck * (int)e.item.rarity));
        }

        static void AddEntry(List<ItemStack> into, LootEntry e, System.Random rng)
        {
            if (e == null || e.item == null) return;
            int count = e.max <= e.min ? e.min : rng.Next(e.min, e.max + 1);
            int cap = Mathf.Max(1, e.item.maxStack);
            while (count > 0)
            {
                int n = Mathf.Min(cap, count);
                into.Add(new ItemStack(e.item, n));
                count -= n;
            }
        }
    }
}
