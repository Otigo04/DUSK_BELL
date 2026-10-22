using System.Collections.Generic;
using NUnit.Framework;
using UnityEngine;

namespace Nightward.Items.Tests
{
    public class LootTableTests
    {
        ItemDef bread, apple, gem, knife;

        static ItemDef Make(string id, int stack, ItemRarity rarity = ItemRarity.Common, int durability = 0)
        {
            var d = ScriptableObject.CreateInstance<ItemDef>();
            d.id = id;
            d.displayName = id;
            d.maxStack = stack;
            d.rarity = rarity;
            d.maxDurability = durability;
            return d;
        }

        static LootEntry E(ItemDef d, float w = 1f, int min = 1, int max = 1) => new LootEntry { item = d, weight = w, min = min, max = max };

        static LootTable Table(List<LootEntry> guaranteed, params LootPool[] pools)
        {
            var t = ScriptableObject.CreateInstance<LootTable>();
            if (guaranteed != null) t.guaranteed = guaranteed;
            t.pools = new List<LootPool>(pools);
            return t;
        }

        static int Total(List<ItemStack> list, ItemDef d)
        {
            int n = 0;
            foreach (var s in list) if (s.def == d) n += s.count;
            return n;
        }

        [SetUp]
        public void SetUp()
        {
            bread = Make("bread", 8);
            apple = Make("apple", 16);
            gem = Make("gem", 4, ItemRarity.Rare);
            knife = Make("knife", 1, ItemRarity.Common, 30);
        }

        [Test]
        public void Guaranteed_AlwaysDrops_WithinRange()
        {
            var t = Table(new List<LootEntry> { E(bread, 1f, 2, 4) });
            for (int seed = 0; seed < 50; seed++)
            {
                int n = Total(t.Roll(new System.Random(seed)), bread);
                Assert.That(n, Is.InRange(2, 4));
            }
        }

        [Test]
        public void Roll_SplitsBigCountsIntoStacks()
        {
            var t = Table(new List<LootEntry> { E(bread, 1f, 20, 20) });
            var r = t.Roll(new System.Random(1));
            Assert.AreEqual(3, r.Count, "20 Brot bei Stapel 8 = 8+8+4");
            Assert.AreEqual(20, Total(r, bread));
            foreach (var s in r) Assert.LessOrEqual(s.count, 8);
        }

        [Test]
        public void Pool_Unique_NeverRepeatsAnItem()
        {
            var pool = new LootPool { rollsMin = 2, rollsMax = 2, unique = true, entries = { E(bread), E(apple) } };
            var t = Table(null, pool);
            for (int seed = 0; seed < 40; seed++)
            {
                var r = t.Roll(new System.Random(seed));
                Assert.AreEqual(2, r.Count);
                Assert.AreEqual(1, Total(r, bread));
                Assert.AreEqual(1, Total(r, apple));
            }
        }

        [Test]
        public void Pool_RollsMoreThanEntries_StopsWhenUniqueRunsOut()
        {
            var pool = new LootPool { rollsMin = 5, rollsMax = 5, unique = true, entries = { E(bread) } };
            Assert.AreEqual(1, Table(null, pool).Roll(new System.Random(3)).Count);
        }

        [Test]
        public void Pool_ChanceZero_DropsNothing_ChanceOne_Drops()
        {
            var none = Table(null, new LootPool { chance = 0f, entries = { E(bread) } });
            var always = Table(null, new LootPool { chance = 1f, entries = { E(bread) } });
            for (int seed = 0; seed < 30; seed++)
            {
                Assert.AreEqual(0, none.Roll(new System.Random(seed)).Count);
                Assert.AreEqual(1, always.Roll(new System.Random(seed)).Count);
            }
        }

        [Test]
        public void Pool_NothingWeight_SometimesDrawsNothing()
        {
            var t = Table(null, new LootPool { nothingWeight = 9f, unique = false, entries = { E(bread) } });
            int hits = 0;
            for (int seed = 0; seed < 400; seed++) hits += t.Roll(new System.Random(seed)).Count;
            Assert.That(hits, Is.InRange(15, 80), "etwa 10 Prozent von 400 Wuerfen");
        }

        [Test]
        public void Weights_FavourHeavyEntries()
        {
            var t = Table(null, new LootPool { unique = false, entries = { E(bread, 9f), E(apple, 1f) } });
            int b = 0, a = 0;
            for (int seed = 0; seed < 500; seed++)
            {
                var r = t.Roll(new System.Random(seed));
                b += Total(r, bread);
                a += Total(r, apple);
            }
            Assert.Greater(b, a * 4);
        }

        [Test]
        public void Luck_ShiftsTowardRareItems()
        {
            var t = Table(null, new LootPool { unique = false, entries = { E(bread, 5f), E(gem, 1f) } });
            int plain = 0, lucky = 0;
            for (int seed = 0; seed < 600; seed++)
            {
                plain += Total(t.Roll(new System.Random(seed), 0f), gem);
                lucky += Total(t.Roll(new System.Random(seed), 2f), gem);
            }
            Assert.Greater(lucky, plain, "Glueck bringt mehr Seltenes");
        }

        [Test]
        public void SameSeed_GivesSameLoot()
        {
            var t = Table(null, new LootPool { rollsMin = 1, rollsMax = 4, unique = false, entries = { E(bread, 1f, 1, 5), E(apple, 2f, 1, 9), E(gem) } });
            var a = t.Roll(new System.Random(42));
            var b = t.Roll(new System.Random(42));
            Assert.AreEqual(a.Count, b.Count);
            for (int i = 0; i < a.Count; i++)
            {
                Assert.AreEqual(a[i].def, b[i].def);
                Assert.AreEqual(a[i].count, b[i].count);
            }
        }

        [Test]
        public void RollInto_FillsContainer_AndCountsLostStacks()
        {
            var inv = new Inventory(2);
            var t = Table(new List<LootEntry> { E(knife), E(knife), E(knife) });
            int lost = t.RollInto(inv, new System.Random(5));
            Assert.AreEqual(1, lost, "Drei Messer (nicht stapelbar) in zwei Plaetze");
            Assert.AreEqual(2, inv.UsedSlots());
        }

        [Test]
        public void Place_Scatter_UsesFreeSlotsOnly()
        {
            var inv = new Inventory(6);
            inv.Set(0, new ItemStack(bread, 1));
            var rng = new System.Random(11);
            for (int i = 0; i < 5; i++) Assert.IsTrue(LootTable.Place(inv, new ItemStack(knife), rng, true));
            Assert.AreEqual(6, inv.UsedSlots());
            Assert.AreEqual(bread, inv.Get(0).def, "Bestehendes wird nicht ueberschrieben");
            Assert.IsFalse(LootTable.Place(inv, new ItemStack(knife), rng, true), "voll");
        }

        [Test]
        public void EmptyTable_RollsNothing()
        {
            Assert.AreEqual(0, Table(null).Roll(new System.Random(1)).Count);
        }
    }
}
