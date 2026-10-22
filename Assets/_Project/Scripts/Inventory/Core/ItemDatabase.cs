using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Items
{
    /// <summary>Alle Gegenstaende des Spiels. Suche ueber die Id. Das Asset liegt in Data/Items/ItemDatabase.asset.</summary>
    [CreateAssetMenu(fileName = "ItemDatabase", menuName = "Nightward/Item Database")]
    public class ItemDatabase : ScriptableObject
    {
        public List<ItemDef> items = new List<ItemDef>();

        Dictionary<string, ItemDef> lookup;

        public ItemDef Get(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            if (lookup == null || lookup.Count != items.Count) Rebuild();
            lookup.TryGetValue(id, out var d);
            return d;
        }

        public void Rebuild()
        {
            lookup = new Dictionary<string, ItemDef>();
            foreach (var d in items) if (d != null && !string.IsNullOrEmpty(d.id)) lookup[d.id] = d;
        }

        void OnEnable() => lookup = null;
        void OnValidate() => lookup = null;
    }
}
