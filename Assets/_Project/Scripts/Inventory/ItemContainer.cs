using System;
using System.Collections.Generic;
using Nightward.DayNight;
using Nightward.Interaction;
using UnityEngine;

namespace Nightward.Items
{
    /// <summary>
    /// Truhe, Kiste, Fass, Schrank, Vorratsregal: ein Behaelter mit eigenen Plaetzen, mit F geoeffnet (das Inventar geht
    /// mit dem Behaelter darueber auf). Der Inhalt kommt aus einer Beute-Tabelle (jeder Durchgang anders) und/oder einer
    /// festen Liste, wird einmal beim Start gewuerfelt und bleibt danach, auch was der Spieler hineinlegt. Optional mit
    /// Schloss (Schluessel-Gegenstand) und mit Nachfuellen, wenn er leer ist und genug Tage vergangen sind.
    /// Das Aussehen (zu/offen/leer) kommt von ContainerVisual, die Verteilung in der Welt von LootSpawner.
    /// </summary>
    public class ItemContainer : Interactable
    {
        [Serializable]
        public class Entry
        {
            public ItemDef item;
            [Min(1)] public int min = 1;
            [Min(1)] public int max = 1;
            [Tooltip("Wahrscheinlichkeit 0-1, dass der Eintrag in der Truhe liegt (Festinhalt: 1)")]
            [Range(0f, 1f)] public float chance = 1f;
        }

        [Header("Inhalt")]
        [SerializeField] string title = "Chest";
        [SerializeField, Range(1, 24)] int slots = 12;
        [Tooltip("Beute-Tabelle: wird beim Start gewuerfelt")]
        [SerializeField] LootTable lootTable;
        [Tooltip("Glueck: verschiebt die Tabelle zu selteneren Funden (0 = normal)")]
        [SerializeField, Range(0f, 2f)] float luck;
        [Tooltip("Zusaetzlich feste Gegenstaende (z. B. ein Schluessel in genau dieser Truhe)")]
        [SerializeField] List<Entry> contents = new List<Entry>();
        [Tooltip("Aus = Inhalt ist Festinhalt, an = jeder Eintrag wird mit seiner Wahrscheinlichkeit gewuerfelt")]
        [SerializeField] bool rollChances = true;
        [Tooltip("An = Fund liegt auf zufaelligen Plaetzen, aus = von vorn")]
        [SerializeField] bool scatter = true;

        [Header("Schloss")]
        [Tooltip("Gegenstand, der zum Aufschliessen noetig ist. Leer = nicht verschlossen")]
        [SerializeField] ItemDef keyItem;
        [SerializeField] bool consumeKey = true;

        [Header("Nachfuellen")]
        [Tooltip("Ist die Truhe leer, fuellt sie sich nach so vielen Tagen neu (0 = nie)")]
        [SerializeField, Min(0)] int refillAfterDays;

        Inventory inv;
        bool locked;
        bool searched;
        int lastFillDay = 1;

        public Inventory Inv => inv;
        public string Title => title;
        public bool IsOpen { get; private set; }
        /// <summary>Wurde schon einmal geoeffnet.</summary>
        public bool Searched => searched;
        public bool IsLocked => locked;
        public bool IsEmpty => inv == null || inv.UsedSlots() == 0;

        /// <summary>true = geoeffnet, false = zugemacht.</summary>
        public event Action<bool> OpenChanged;
        /// <summary>Inhalt hat sich geaendert (Entnehmen, Hineinlegen, Neufuellen).</summary>
        public event Action Changed;
        public event Action Unlocked;

        void Reset() { Prompt = "Open"; key = InteractKey.F; }

        void Awake()
        {
            key = InteractKey.F;
            EnsureInventory();
        }

        protected override void OnEnable()
        {
            base.OnEnable();
            EnsureInventory();
            if (DayNightCycle.Instance != null) DayNightCycle.Instance.NewDay += OnNewDay;
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            if (DayNightCycle.Instance != null) DayNightCycle.Instance.NewDay -= OnNewDay;
        }

        void EnsureInventory()
        {
            if (inv != null) return;
            inv = new Inventory(slots);
            inv.SlotChanged += _ => Changed?.Invoke();
            locked = keyItem != null;
            Fill();
            if (DayNightCycle.Instance != null) lastFillDay = DayNightCycle.Instance.Day;
        }

        // ------------------------------------------------------------------ Inhalt
        /// <summary>Wuerfelt Tabelle und Festinhalt und legt sie in die freien Plaetze.</summary>
        public void Fill()
        {
            var rng = LootTable.NewRng();
            if (lootTable != null) lootTable.RollInto(inv, rng, luck, scatter);
            foreach (var e in contents)
            {
                if (e.item == null) continue;
                if (rollChances && rng.NextDouble() > e.chance) continue;
                var s = new ItemStack(e.item, rng.Next(e.min, Mathf.Max(e.min, e.max) + 1));
                LootTable.Place(inv, s, rng, scatter);
            }
            Changed?.Invoke();
        }

        void OnNewDay(int day)
        {
            if (refillAfterDays <= 0 || IsOpen || !IsEmpty || day - lastFillDay < refillAfterDays) return;
            lastFillDay = day;
            searched = false;
            Fill();
        }

        // ------------------------------------------------------------------ Interaktion
        public override bool ShowsPromptBox => true;

        public override string PromptLabel
        {
            get
            {
                if (locked)
                {
                    var p = PlayerInventory.Instance;
                    return p != null && p.Has(keyItem.id) ? $"Unlock {title}" : $"{title} (locked)";
                }
                return $"{Prompt} {title}";
            }
        }

        public override bool CanInteract(PlayerInteractor who) => base.CanInteract(who) && InventoryUI.Instance != null && !InventoryUI.Instance.IsOpen;

        public override bool ShowsIndicator(PlayerInteractor who) => false;

        public override void Interact(PlayerInteractor who)
        {
            var ui = InventoryUI.Instance;
            if (ui == null) return;
            if (locked && !TryUnlock(who != null ? who.GetComponent<PlayerInventory>() : PlayerInventory.Instance)) return;
            ui.Open(this);
        }

        bool TryUnlock(PlayerInventory pi)
        {
            if (pi == null) return false;
            if (!pi.Has(keyItem.id)) { pi.Say($"Locked. You need: {keyItem.displayName}."); return false; }
            if (consumeKey) pi.Consume(keyItem.id);
            locked = false;
            pi.Say($"Unlocked {title}.");
            Unlocked?.Invoke();
            Changed?.Invoke();
            return true;
        }

        /// <summary>Vom Inventar aufgerufen, wenn das Fenster dieses Behaelters auf- bzw. zugeht.</summary>
        public void SetOpen(bool open)
        {
            if (IsOpen == open) return;
            IsOpen = open;
            if (open) searched = true;
            OpenChanged?.Invoke(open);
            Changed?.Invoke();
        }

        // ------------------------------------------------------------------ Speichern
        [Serializable]
        class SaveData
        {
            public InventorySave items;
            public bool locked, searched;
            public int lastFillDay;
        }

        public string SaveJson() => JsonUtility.ToJson(new SaveData { items = inv.Save(), locked = locked, searched = searched, lastFillDay = lastFillDay });

        public void LoadJson(string json, ItemDatabase db)
        {
            if (string.IsNullOrEmpty(json)) return;
            var d = JsonUtility.FromJson<SaveData>(json);
            inv.Load(d.items, db);
            locked = d.locked;
            searched = d.searched;
            lastFillDay = d.lastFillDay;
            Changed?.Invoke();
        }
    }
}
