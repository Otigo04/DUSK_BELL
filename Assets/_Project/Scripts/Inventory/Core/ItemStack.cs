using System;
using UnityEngine;

namespace Nightward.Items
{
    /// <summary>Ein Stapel in einem Platz: Gegenstandstyp, Anzahl und (bei Werkzeug/Waffe/Licht) die verbleibende Haltbarkeit.</summary>
    public sealed class ItemStack
    {
        public ItemDef def;
        public int count;
        public float durability;

        public ItemStack(ItemDef def, int count = 1, float durability = -1f)
        {
            this.def = def;
            this.count = count;
            this.durability = durability >= 0f ? durability : def.maxDurability;
        }

        public int Space => def.maxStack - count;
        public bool IsFull => count >= def.maxStack;
        /// <summary>0..1 der Haltbarkeit (1 bei Gegenstaenden ohne Haltbarkeit).</summary>
        public float DurabilityFraction => def.HasDurability ? Mathf.Clamp01(durability / def.maxDurability) : 1f;

        public ItemStack Clone() => new ItemStack(def, count, durability);

        /// <summary>Gleicher Typ, stapelbar und beide ohne Haltbarkeit-Unterschied: dann duerfen sie zusammen.</summary>
        public bool CanMerge(ItemStack other) => other != null && other.def == def && def.IsStackable && !def.HasDurability;

        public override string ToString() => def != null ? $"{count}x {def.id}" : "(leer)";
    }

    [Serializable]
    public class SavedStack
    {
        public string id;
        public int count;
        public float durability;
    }

    [Serializable]
    public class InventorySave
    {
        public SavedStack[] slots = new SavedStack[0];
    }
}
