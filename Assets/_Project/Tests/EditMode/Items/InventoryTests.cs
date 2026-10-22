using NUnit.Framework;
using UnityEngine;

namespace Nightward.Items.Tests
{
    public class InventoryTests
    {
        ItemDef bread, apple, knife, lantern, coat;
        ItemDatabase db;

        static ItemDef Make(string id, int stack, ItemCategory cat = ItemCategory.Misc, int durability = 0, EquipSlotKind slot = EquipSlotKind.None)
        {
            var d = ScriptableObject.CreateInstance<ItemDef>();
            d.id = id;
            d.displayName = id;
            d.maxStack = stack;
            d.category = cat;
            d.maxDurability = durability;
            d.equipSlot = slot;
            return d;
        }

        [SetUp]
        public void SetUp()
        {
            bread = Make("bread", 8, ItemCategory.Food);
            apple = Make("apple", 16, ItemCategory.Food);
            knife = Make("knife", 1, ItemCategory.Weapon, 30);
            lantern = Make("lantern", 1, ItemCategory.Light, 100, EquipSlotKind.Light);
            coat = Make("coat", 1, ItemCategory.Clothing, 0, EquipSlotKind.Clothing);
            db = ScriptableObject.CreateInstance<ItemDatabase>();
            db.items.AddRange(new[] { bread, apple, knife, lantern, coat });
        }

        // ------------------------------------------------------------------ Hinzufuegen
        [Test]
        public void Add_FillsExistingStacksThenEmptySlots()
        {
            var inv = new Inventory(3);
            Assert.AreEqual(0, inv.Add(bread, 5));
            Assert.AreEqual(0, inv.Add(bread, 6));          // 3 auf den ersten Stapel, 8 passen -> neuer Stapel mit 3
            Assert.AreEqual(8, inv.Get(0).count);
            Assert.AreEqual(3, inv.Get(1).count);
            Assert.AreEqual(11, inv.CountOf("bread"));
        }

        [Test]
        public void Add_ReturnsLeftover_WhenFull()
        {
            var inv = new Inventory(2);
            Assert.AreEqual(4, inv.Add(bread, 20));         // 2 Plaetze * 8 = 16
            Assert.AreEqual(16, inv.CountOf("bread"));
            Assert.IsFalse(inv.CanFit(bread, 1));
        }

        [Test]
        public void Add_DurableItems_DoNotStack_KeepDurability()
        {
            var inv = new Inventory(4);
            inv.Add(knife, 1);
            inv.Add(knife, 1);
            Assert.AreEqual(2, inv.UsedSlots());
            Assert.AreEqual(30f, inv.Get(0).durability);
            inv.Get(0).durability = 12f;
            var stack = inv.Take(0, 1);
            Assert.AreEqual(12f, stack.durability);
        }

        [Test]
        public void Add_RespectsRange_HotbarFirst()
        {
            var inv = new Inventory(10);
            inv.Add(apple, 3, -1f, 0, 3);                    // nur Plaetze 0..3 (Schnellleiste)
            Assert.AreEqual(3, inv.Get(0).count);
            inv.Add(knife, 1, -1f, 4, 9);
            Assert.AreEqual(apple, inv.Get(0).def);
            Assert.AreEqual(knife, inv.Get(4).def);
        }

        [Test]
        public void EquipSlots_AcceptOnlyMatchingItems()
        {
            var eq = new Inventory(3, new[] { EquipSlotKind.Light, EquipSlotKind.Talisman, EquipSlotKind.Clothing });
            Assert.AreEqual(1, eq.Add(bread, 1), "Brot passt in keinen Ausruestungsplatz");
            Assert.AreEqual(0, eq.Add(lantern, 1));
            Assert.AreEqual(lantern, eq.Get(0).def);
            Assert.AreEqual(0, eq.Add(coat, 1));
            Assert.AreEqual(coat, eq.Get(2).def);
        }

        [Test]
        public void Remove_TakesAcrossStacks()
        {
            var inv = new Inventory(3);
            inv.Add(bread, 14);
            Assert.AreEqual(10, inv.Remove("bread", 10));
            Assert.AreEqual(4, inv.CountOf("bread"));
            Assert.AreEqual(4, inv.Remove("bread", 99));
            Assert.AreEqual(0, inv.UsedSlots());
        }

        // ------------------------------------------------------------------ Klick-Operationen
        [Test]
        public void LeftClick_PicksUp_Places_Merges_Swaps()
        {
            var inv = new Inventory(3);
            inv.Add(bread, 5);
            inv.Set(1, new ItemStack(apple, 4));
            ItemStack cursor = null;

            Assert.IsTrue(InventoryOps.LeftClick(inv, 0, ref cursor));
            Assert.AreEqual(5, cursor.count);
            Assert.IsNull(inv.Get(0));

            Assert.IsTrue(InventoryOps.LeftClick(inv, 2, ref cursor));   // in leeren Platz ablegen
            Assert.IsNull(cursor);
            Assert.AreEqual(5, inv.Get(2).count);

            InventoryOps.LeftClick(inv, 2, ref cursor);                  // wieder nehmen
            Assert.IsTrue(InventoryOps.LeftClick(inv, 1, ref cursor));   // auf Apfel: tauschen
            Assert.AreEqual(apple, cursor.def);
            Assert.AreEqual(bread, inv.Get(1).def);

            inv.Set(0, new ItemStack(apple, 14));
            Assert.IsTrue(InventoryOps.LeftClick(inv, 0, ref cursor));   // Apfel (4) auf Apfel (14): 2 passen, 2 bleiben
            Assert.AreEqual(16, inv.Get(0).count);
            Assert.AreEqual(2, cursor.count);
        }

        [Test]
        public void RightClick_TakesHalf_PlacesOne()
        {
            var inv = new Inventory(3);
            inv.Add(apple, 9);
            ItemStack cursor = null;
            Assert.IsTrue(InventoryOps.RightClick(inv, 0, ref cursor));
            Assert.AreEqual(5, cursor.count, "Haelfte aufgerundet");
            Assert.AreEqual(4, inv.Get(0).count);

            Assert.IsTrue(InventoryOps.RightClick(inv, 1, ref cursor));  // eines in leeren Platz
            Assert.AreEqual(1, inv.Get(1).count);
            Assert.AreEqual(4, cursor.count);
            Assert.IsTrue(InventoryOps.RightClick(inv, 1, ref cursor));  // eines auf bestehenden Stapel
            Assert.AreEqual(2, inv.Get(1).count);
        }

        [Test]
        public void Click_OnEquipSlot_RefusesWrongItem()
        {
            var eq = new Inventory(1, new[] { EquipSlotKind.Light });
            ItemStack cursor = new ItemStack(bread, 1);
            Assert.IsFalse(InventoryOps.LeftClick(eq, 0, ref cursor));
            Assert.AreEqual(bread, cursor.def);
            cursor = new ItemStack(lantern, 1);
            Assert.IsTrue(InventoryOps.LeftClick(eq, 0, ref cursor));
            Assert.IsNull(cursor);
        }

        [Test]
        public void QuickMove_MovesBetweenInventories_PartialWhenFull()
        {
            var a = new Inventory(2);
            var b = new Inventory(1);
            a.Add(bread, 8);
            b.Add(bread, 5);
            int moved = InventoryOps.QuickMove(a, 0, b);
            Assert.AreEqual(3, moved);
            Assert.AreEqual(5, a.Get(0).count);
            Assert.AreEqual(8, b.Get(0).count);
        }

        [Test]
        public void CollectToCursor_GathersSmallStacksFirst()
        {
            var inv = new Inventory(4);
            inv.Set(0, new ItemStack(apple, 16));
            inv.Set(1, new ItemStack(apple, 3));
            inv.Set(2, new ItemStack(apple, 2));
            ItemStack cursor = new ItemStack(apple, 5);
            int got = InventoryOps.CollectToCursor(inv, ref cursor);
            Assert.AreEqual(11, got);
            Assert.AreEqual(16, cursor.count);
            Assert.IsNull(inv.Get(1));
            Assert.IsNull(inv.Get(2));
            Assert.AreEqual(10, inv.Get(0).count, "Rest des vollen Stapels");
        }

        [Test]
        public void Swap_ExchangesSlots_RespectingFilters()
        {
            var inv = new Inventory(3, new[] { EquipSlotKind.None, EquipSlotKind.None, EquipSlotKind.Light });
            inv.Add(bread, 2);
            inv.Add(lantern, 1, -1f, 1, 1);
            Assert.IsTrue(InventoryOps.Swap(inv, 0, 1));
            Assert.AreEqual(lantern, inv.Get(0).def);
            Assert.IsFalse(InventoryOps.Swap(inv, 1, 2) && inv.Get(2) != null && inv.Get(2).def == bread, "Brot darf nicht in den Lichtplatz");
        }

        // ------------------------------------------------------------------ Sortieren, Speichern
        [Test]
        public void Sort_MergesStacks_AndGroupsByCategory()
        {
            var inv = new Inventory(6);
            inv.Set(1, new ItemStack(apple, 3));
            inv.Set(3, new ItemStack(knife, 1));
            inv.Set(5, new ItemStack(apple, 4));
            inv.Sort(0);
            Assert.AreEqual(apple, inv.Get(0).def);
            Assert.AreEqual(7, inv.Get(0).count);
            Assert.AreEqual(knife, inv.Get(1).def, "Essen vor Waffen (Kategorie)");
            Assert.IsNull(inv.Get(2));
        }

        [Test]
        public void SaveLoad_RoundTrip_KeepsDurability()
        {
            var inv = new Inventory(4);
            inv.Add(bread, 5);
            inv.Add(knife, 1);
            inv.Get(1).durability = 7f;
            string json = JsonUtility.ToJson(inv.Save());

            var other = new Inventory(4);
            other.Load(JsonUtility.FromJson<InventorySave>(json), db);
            Assert.AreEqual(5, other.CountOf("bread"));
            Assert.AreEqual(7f, other.Get(1).durability);
            Assert.AreEqual(knife, other.Get(1).def);
        }

        [Test]
        public void Events_FireForChangedSlots()
        {
            var inv = new Inventory(3);
            int last = -2, n = 0;
            inv.SlotChanged += i => { last = i; n++; };
            inv.Add(bread, 3);
            Assert.AreEqual(0, last);
            inv.Take(0, 1);
            Assert.AreEqual(2, n);
            inv.Clear();
            Assert.AreEqual(-1, last);
        }

        [Test]
        public void ItemDef_DurableItemsNeverStack()
        {
            var d = Make("x", 16, ItemCategory.Tool, 10);
            var go = typeof(ItemDef).GetMethod("OnValidate", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            go.Invoke(d, null);
            Assert.AreEqual(1, d.maxStack);
        }
    }
}
