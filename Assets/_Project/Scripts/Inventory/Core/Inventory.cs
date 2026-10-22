using System;
using System.Collections.Generic;

namespace Nightward.Items
{
    /// <summary>
    /// Ein Behaelter mit festen Plaetzen (Rucksack, Schnellleiste, Truhe, Ausruestung). Reine Logik ohne Oberflaeche.
    /// Jeder Platz kann auf einen Ausruestungstyp beschraenkt sein (EquipSlotKind). Aenderungen melden SlotChanged.
    /// </summary>
    public sealed class Inventory
    {
        readonly ItemStack[] slots;
        readonly EquipSlotKind[] filters;

        /// <summary>Index des geaenderten Platzes, -1 = viele Plaetze (Sortieren, Laden).</summary>
        public event Action<int> SlotChanged;

        public Inventory(int size, EquipSlotKind[] slotFilters = null)
        {
            slots = new ItemStack[size];
            filters = slotFilters;
        }

        public int Size => slots.Length;
        public ItemStack this[int i] => slots[i];
        public ItemStack Get(int i) => i >= 0 && i < slots.Length ? slots[i] : null;

        public EquipSlotKind FilterOf(int i) => filters != null && i < filters.Length ? filters[i] : EquipSlotKind.None;

        public bool Accepts(int i, ItemDef def)
        {
            var f = FilterOf(i);
            return f == EquipSlotKind.None || def.equipSlot == f;
        }

        public void Set(int i, ItemStack s)
        {
            if (s != null && s.count <= 0) s = null;
            slots[i] = s;
            SlotChanged?.Invoke(i);
        }

        public void Notify(int i = -1) => SlotChanged?.Invoke(i);

        int Last(int last) => last < 0 || last >= slots.Length ? slots.Length - 1 : last;

        // ------------------------------------------------------------------ Hinzufuegen
        /// <summary>Legt einen Gegenstand ab (erst auf bestehende Stapel, dann in leere Plaetze). Gibt zurueck, wie viele nicht passten.</summary>
        public int Add(ItemDef def, int count, float durability = -1f, int first = 0, int last = -1)
        {
            if (def == null || count <= 0) return 0;
            int end = Last(last);
            int left = count;

            if (def.IsStackable && !def.HasDurability)
            {
                for (int i = first; i <= end && left > 0; i++)
                {
                    var s = slots[i];
                    if (s == null || s.def != def || s.IsFull || !Accepts(i, def)) continue;
                    int move = Math.Min(s.Space, left);
                    s.count += move;
                    left -= move;
                    SlotChanged?.Invoke(i);
                }
            }
            for (int i = first; i <= end && left > 0; i++)
            {
                if (slots[i] != null || !Accepts(i, def)) continue;
                int put = Math.Min(def.maxStack, left);
                slots[i] = new ItemStack(def, put, durability);
                left -= put;
                SlotChanged?.Invoke(i);
            }
            return left;
        }

        /// <summary>Wie Add, mit einem vorhandenen Stapel (behaelt die Haltbarkeit). stack.count wird auf den Rest gesetzt.</summary>
        public int Add(ItemStack stack, int first = 0, int last = -1)
        {
            if (stack == null) return 0;
            int left = Add(stack.def, stack.count, stack.durability, first, last);
            stack.count = left;
            return left;
        }

        public bool CanFit(ItemDef def, int count, int first = 0, int last = -1)
        {
            if (def == null || count <= 0) return true;
            int end = Last(last);
            int left = count;
            for (int i = first; i <= end && left > 0; i++)
            {
                var s = slots[i];
                if (s != null && s.def == def && def.IsStackable && !def.HasDurability && Accepts(i, def)) left -= s.Space;
                else if (s == null && Accepts(i, def)) left -= def.maxStack;
            }
            return left <= 0;
        }

        // ------------------------------------------------------------------ Abfragen und Entnehmen
        public int CountOf(string id)
        {
            int n = 0;
            foreach (var s in slots) if (s != null && s.def.id == id) n += s.count;
            return n;
        }

        public bool Has(string id, int count = 1) => CountOf(id) >= count;

        public int FindFirst(string id)
        {
            for (int i = 0; i < slots.Length; i++) if (slots[i] != null && slots[i].def.id == id) return i;
            return -1;
        }

        /// <summary>Nimmt bis zu count Stueck heraus (von vorn). Gibt zurueck, wie viele entnommen wurden.</summary>
        public int Remove(string id, int count)
        {
            int removed = 0;
            for (int i = 0; i < slots.Length && removed < count; i++)
            {
                var s = slots[i];
                if (s == null || s.def.id != id) continue;
                int take = Math.Min(s.count, count - removed);
                s.count -= take;
                removed += take;
                if (s.count <= 0) slots[i] = null;
                SlotChanged?.Invoke(i);
            }
            return removed;
        }

        /// <summary>Nimmt n Stueck aus einem Platz (der Stapel bleibt, wenn noch etwas uebrig ist).</summary>
        public ItemStack Take(int i, int n)
        {
            var s = slots[i];
            if (s == null || n <= 0) return null;
            n = Math.Min(n, s.count);
            var taken = new ItemStack(s.def, n, s.durability);
            s.count -= n;
            if (s.count <= 0) slots[i] = null;
            SlotChanged?.Invoke(i);
            return taken;
        }

        public void Clear()
        {
            Array.Clear(slots, 0, slots.Length);
            SlotChanged?.Invoke(-1);
        }

        public int UsedSlots()
        {
            int n = 0;
            foreach (var s in slots) if (s != null) n++;
            return n;
        }

        // ------------------------------------------------------------------ Sortieren
        /// <summary>Fasst Stapel zusammen und sortiert Plaetze first..last nach Kategorie, Name.</summary>
        public void Sort(int first, int last = -1)
        {
            int end = Last(last);
            var list = new List<ItemStack>();
            for (int i = first; i <= end; i++) if (slots[i] != null) { list.Add(slots[i]); slots[i] = null; }

            var merged = new List<ItemStack>();
            foreach (var s in list)
            {
                if (s.def.IsStackable && !s.def.HasDurability)
                {
                    foreach (var m in merged)
                    {
                        if (m.def != s.def || m.IsFull) continue;
                        int move = Math.Min(m.Space, s.count);
                        m.count += move;
                        s.count -= move;
                        if (s.count <= 0) break;
                    }
                }
                if (s.count > 0) merged.Add(s);
            }
            merged.Sort((a, b) =>
            {
                int c = a.def.category.CompareTo(b.def.category);
                if (c != 0) return c;
                c = string.CompareOrdinal(a.def.displayName, b.def.displayName);
                return c != 0 ? c : b.count.CompareTo(a.count);
            });
            int k = first;
            foreach (var s in merged)
            {
                while (k <= end && !Accepts(k, s.def)) k++;
                if (k > end) break;
                slots[k++] = s;
            }
            SlotChanged?.Invoke(-1);
        }

        // ------------------------------------------------------------------ Speichern
        public InventorySave Save()
        {
            var save = new InventorySave { slots = new SavedStack[slots.Length] };
            for (int i = 0; i < slots.Length; i++)
            {
                var s = slots[i];
                save.slots[i] = s == null ? new SavedStack() : new SavedStack { id = s.def.id, count = s.count, durability = s.durability };
            }
            return save;
        }

        public void Load(InventorySave save, ItemDatabase db)
        {
            Array.Clear(slots, 0, slots.Length);
            if (save != null && save.slots != null)
            {
                for (int i = 0; i < slots.Length && i < save.slots.Length; i++)
                {
                    var sv = save.slots[i];
                    var def = sv != null ? db.Get(sv.id) : null;
                    if (def != null && sv.count > 0) slots[i] = new ItemStack(def, sv.count, sv.durability);
                }
            }
            SlotChanged?.Invoke(-1);
        }
    }
}
