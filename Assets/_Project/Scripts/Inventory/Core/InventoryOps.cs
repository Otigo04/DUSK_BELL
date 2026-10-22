using System;

namespace Nightward.Items
{
    /// <summary>
    /// Mausbedienung nach Minecraft-Vorbild als reine Logik: der Cursor haelt einen Stapel in der Hand.
    /// Linksklick = ganzen Stapel nehmen/ablegen/tauschen, Rechtsklick = Haelfte nehmen bzw. eines ablegen,
    /// Umschalt+Klick = schnell in den anderen Behaelter, Doppelklick = gleiche Stapel einsammeln.
    /// </summary>
    public static class InventoryOps
    {
        /// <summary>Linksklick auf einen Platz. true = etwas hat sich geaendert.</summary>
        public static bool LeftClick(Inventory inv, int slot, ref ItemStack cursor)
        {
            var s = inv.Get(slot);
            if (cursor == null)
            {
                if (s == null) return false;
                cursor = s;
                inv.Set(slot, null);
                return true;
            }
            if (!inv.Accepts(slot, cursor.def)) return false;
            if (s == null)
            {
                inv.Set(slot, cursor);
                cursor = null;
                return true;
            }
            if (s.CanMerge(cursor))
            {
                int move = Math.Min(s.Space, cursor.count);
                if (move <= 0) return false;
                s.count += move;
                cursor.count -= move;
                if (cursor.count <= 0) cursor = null;
                inv.Set(slot, s);
                return true;
            }
            // Anderer Gegenstand: tauschen
            inv.Set(slot, cursor);
            cursor = s;
            return true;
        }

        /// <summary>Rechtsklick auf einen Platz: Haelfte nehmen, ein Stueck ablegen, sonst wie Linksklick (tauschen).</summary>
        public static bool RightClick(Inventory inv, int slot, ref ItemStack cursor)
        {
            var s = inv.Get(slot);
            if (cursor == null)
            {
                if (s == null) return false;
                int take = (s.count + 1) / 2;
                cursor = new ItemStack(s.def, take, s.durability);
                s.count -= take;
                inv.Set(slot, s.count > 0 ? s : null);
                return true;
            }
            if (!inv.Accepts(slot, cursor.def)) return false;
            if (s == null)
            {
                inv.Set(slot, new ItemStack(cursor.def, 1, cursor.durability));
                cursor.count--;
                if (cursor.count <= 0) cursor = null;
                return true;
            }
            if (s.CanMerge(cursor) && s.Space > 0)
            {
                s.count++;
                cursor.count--;
                if (cursor.count <= 0) cursor = null;
                inv.Set(slot, s);
                return true;
            }
            if (s.CanMerge(cursor)) return false;
            inv.Set(slot, cursor);
            cursor = s;
            return true;
        }

        /// <summary>Schnell verschieben: den Stapel aus from[slot] nach to (Bereich toFirst..toLast). Gibt die verschobene Menge zurueck.</summary>
        public static int QuickMove(Inventory from, int slot, Inventory to, int toFirst = 0, int toLast = -1)
        {
            var s = from.Get(slot);
            if (s == null) return 0;
            int before = s.count;
            var rest = new ItemStack(s.def, s.count, s.durability);
            int left = to.Add(rest, toFirst, toLast);
            int moved = before - left;
            if (moved <= 0) return 0;
            if (left <= 0) from.Set(slot, null);
            else { s.count = left; from.Set(slot, s); }
            return moved;
        }

        /// <summary>Doppelklick: gleiche Stapel aus dem Behaelter in den Cursor einsammeln (kleine zuerst).</summary>
        public static int CollectToCursor(Inventory inv, ref ItemStack cursor)
        {
            if (cursor == null || !cursor.def.IsStackable || cursor.def.HasDurability) return 0;
            int gathered = 0;
            for (int pass = 0; pass < 2 && !cursor.IsFull; pass++)
            {
                for (int i = 0; i < inv.Size && !cursor.IsFull; i++)
                {
                    var s = inv.Get(i);
                    if (s == null || s.def != cursor.def) continue;
                    if (pass == 0 && s.IsFull) continue; // erst unvollstaendige Stapel
                    int take = Math.Min(cursor.Space, s.count);
                    cursor.count += take;
                    s.count -= take;
                    gathered += take;
                    inv.Set(i, s.count > 0 ? s : null);
                }
            }
            return gathered;
        }

        /// <summary>Zwei Plaetze desselben Behaelters tauschen (Zahlentaste ueber einem Platz).</summary>
        public static bool Swap(Inventory inv, int a, int b)
        {
            if (a == b) return false;
            var sa = inv.Get(a);
            var sb = inv.Get(b);
            if (sa == null && sb == null) return false;
            if (sa != null && !inv.Accepts(b, sa.def)) return false;
            if (sb != null && !inv.Accepts(a, sb.def)) return false;
            inv.Set(a, sb);
            inv.Set(b, sa);
            return true;
        }
    }
}
