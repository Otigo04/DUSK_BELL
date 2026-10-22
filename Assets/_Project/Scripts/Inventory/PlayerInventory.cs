using System;
using System.Collections.Generic;
using Nightward.Player;
using Nightward.Survival;
using Nightward.UI;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering.Universal;

namespace Nightward.Items
{
    /// <summary>Waffe in der Hand: Stil (Animation), Werte, und der zugehoerige Gegenstand (null = Faeuste).</summary>
    public struct WeaponInfo
    {
        public ItemDef def;
        public WeaponStyle style;
        public int damage;
        public float reach;
        public float staminaCost;
        public float range;
    }

    /// <summary>
    /// Das Inventar des Spielers (Minecraft-Prinzip): Schnellleiste (die ersten hotbarSize Plaetze von Main) plus Rucksack,
    /// dazu Ausruestung (Licht, Talisman, Kleidung). Waehlt per Zahlentasten 1-8 oder Mausrad den Gegenstand in der Hand;
    /// der bestimmt Waffe, Licht und Benutzen (Rechtsklick). Verbindet Gegenstaende mit dem Survival-System
    /// (Essen, Trinken, Medizin, Ausruestungs-Effekte) und mit PlayerCombat (Waffen, Munition, Haltbarkeit).
    /// </summary>
    [RequireComponent(typeof(PlayerController))]
    [DefaultExecutionOrder(-60)]
    public class PlayerInventory : MonoBehaviour
    {
        public static PlayerInventory Instance { get; private set; }

        [Serializable]
        public class StartItem
        {
            public string id;
            public int count = 1;
        }

        [SerializeField] ItemDatabase database;
        [Tooltip("Plaetze in der Schnellleiste (Zahlentasten 1..n)")]
        [SerializeField, Range(1, 9)] int hotbarSize = 8;
        [SerializeField, Range(1, 12)] int backpackColumns = 8;
        [SerializeField, Range(1, 6)] int backpackRows = 3;
        [Tooltip("Ausruestungsplaetze in dieser Reihenfolge")]
        [SerializeField] EquipSlotKind[] equipmentSlots = { EquipSlotKind.Light, EquipSlotKind.Talisman, EquipSlotKind.Clothing };
        [SerializeField] List<StartItem> startItems = new List<StartItem>();

        [Header("Aufheben")]
        [SerializeField] float pickupRadius = 0.7f;
        [SerializeField] float magnetRadius = 1.9f;

        [Header("Hand-Licht")]
        [SerializeField] float lightFlicker = 0.08f;
        [SerializeField] Vector3 lightOffset = new Vector3(0f, 0.6f, 0f);

        PlayerController controller;
        PlayerActionAnimation actionAnim;
        PlayerSurvival survival;
        Light2D handLight;
        ItemStack burningStack;
        float lastHours;
        bool started;

        public Inventory Main { get; private set; }
        public Inventory Equipment { get; private set; }
        public ItemDatabase Database => database;
        public int HotbarSize => hotbarSize;
        public int BackpackColumns => backpackColumns;
        public int BackpackRows => backpackRows;
        public int Selected { get; private set; }
        public float PickupRadius => pickupRadius;
        public float MagnetRadius => magnetRadius;

        /// <summary>Material der Spielerfigur, damit Gegenstaende in der Welt vom Licht erfasst werden wie sie.</summary>
        public Material WorldMaterial { get; private set; }
        /// <summary>Sortierung der Spielerfigur, damit Gegenstaende in der Welt gleich mit ihr (nach Hoehe) sortiert werden.</summary>
        public int WorldSortingOrder { get; private set; }
        public int WorldSortingLayerId { get; private set; }

        public event Action<int> SelectedChanged;
        /// <summary>Kurze Hinweise ("+2 Bread", "Out of ammo.").</summary>
        public event Action<string> Message;

        public ItemStack SelectedStack => Main.Get(Selected);

        // Essen, Trinken, Medizin: Animation mit Fortschrittsbalken, die Wirkung kommt erst am Ende
        Inventory consumeInv;
        int consumeSlot;
        ItemStack consumeStack;
        string consumeVerb;
        float consumeStart, consumeEnd;
        const float ConsumeSeconds = 0.85f;

        /// <summary>Ein Gegenstand wird gerade verzehrt (Balken laeuft).</summary>
        public bool IsConsuming => consumeStack != null;
        /// <summary>0..1 des laufenden Verzehrs.</summary>
        public float ConsumeProgress => consumeStack == null ? 0f : Mathf.Clamp01((Time.time - consumeStart) / Mathf.Max(0.01f, consumeEnd - consumeStart));
        public string ConsumeVerb => consumeVerb;
        /// <summary>Der Spieler kann jetzt etwas benutzen (nicht gesperrt durch Dialog, Inventar, Aktion oder Tod).</summary>
        public bool CanUseNow => !controller.InputLocked && !survival.Sim.IsDead;

        void Awake()
        {
            Instance = this;
            controller = GetComponent<PlayerController>();
            // Liegt nicht in jeder Szene am Spieler (nur Opening): bei Bedarf ergaenzen
            actionAnim = GetComponent<PlayerActionAnimation>();
            if (actionAnim == null) actionAnim = gameObject.AddComponent<PlayerActionAnimation>();
            // Angelegte Kleidung sichtbar machen (Variante der Figur-Sheets, siehe PlayerOutfit)
            if (GetComponent<PlayerOutfit>() == null) gameObject.AddComponent<PlayerOutfit>();
            survival = GetComponent<PlayerSurvival>();
            Main = new Inventory(hotbarSize + backpackColumns * backpackRows);
            // Hose und Schuhe kommen immer dazu, auch wenn Prefab oder Szene noch die alte Liste (Licht, Talisman, Kleidung) gespeichert haben
            var slots = new List<EquipSlotKind>(equipmentSlots);
            foreach (var k in new[] { EquipSlotKind.Legs, EquipSlotKind.Feet }) if (!slots.Contains(k)) slots.Add(k);
            Equipment = new Inventory(slots.Count, slots.ToArray());
            var sr = GetComponentInChildren<SpriteRenderer>();
            if (sr != null)
            {
                WorldMaterial = sr.sharedMaterial;
                WorldSortingOrder = sr.sortingOrder;
                WorldSortingLayerId = sr.sortingLayerID;
            }
        }

        void Start()
        {
            started = true;
            if (database != null)
                foreach (var s in startItems)
                {
                    var def = database.Get(s.id);
                    if (def != null) Main.Add(def, s.count);
                    else Debug.LogWarning($"[Inventar] Startgegenstand '{s.id}' unbekannt.", this);
                }
            Equipment.SlotChanged += _ => ApplyEquipmentEffects();
            survival.Sim.Damaged += _ => CancelConsume();
            survival.Sim.Died += CancelConsume;
            ApplyEquipmentEffects();
            lastHours = survival.Sim.TotalGameHours;
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
            if (started && survival != null && survival.Sim != null) survival.Sim.RemoveModifiers(this);
        }

        // ------------------------------------------------------------------ Eingabe
        void Update()
        {
            UpdateHeldLight();
            UpdateConsume();

            var kb = Keyboard.current;
            var mouse = Mouse.current;
            if (kb == null || controller.InputLocked || survival.Sim.IsDead) return;

            for (int i = 0; i < hotbarSize; i++)
                if (kb[(Key)((int)Key.Digit1 + i)].wasPressedThisFrame) Select(i);

            if (mouse != null)
            {
                float wheel = mouse.scroll.ReadValue().y;
                if (Mathf.Abs(wheel) > 0.1f && !NwPointer.OverUI) Select(Selected + (wheel > 0f ? -1 : 1));
                if (mouse.rightButton.wasPressedThisFrame && !NwPointer.OverUI) Use(Main, Selected);
            }
            if (kb.qKey.wasPressedThisFrame) DropFromSlot(Main, Selected, kb.leftCtrlKey.isPressed ? int.MaxValue : 1);
        }

        public void Select(int index)
        {
            index = ((index % hotbarSize) + hotbarSize) % hotbarSize;
            if (index == Selected) return;
            CancelConsume();
            Selected = index;
            SelectedChanged?.Invoke(Selected);
        }

        // ------------------------------------------------------------------ Hinzufuegen, Entnehmen, Fallenlassen
        public bool Has(string id, int count = 1) => Main.CountOf(id) >= count;

        /// <summary>Legt Gegenstaende in den Rucksack (erst Schnellleiste, dann Rest). Gibt zurueck, wie viele nicht passten.</summary>
        public int Give(string id, int count = 1)
        {
            var def = database != null ? database.Get(id) : null;
            if (def == null) { Debug.LogWarning($"[Inventar] Gegenstand '{id}' unbekannt."); return count; }
            return Give(def, count);
        }

        public int Give(ItemDef def, int count = 1, float durability = -1f)
        {
            int left = Main.Add(def, count, durability);
            int got = count - left;
            if (got > 0) Say($"+{got} {def.displayName}");
            return left;
        }

        /// <summary>Nimmt einen Stapel auf (Pickup in der Welt). stack.count wird auf den Rest gesetzt.</summary>
        public bool TryPickup(ItemStack stack)
        {
            int before = stack.count;
            Main.Add(stack);
            int got = before - stack.count;
            if (got > 0) Say($"+{got} {stack.def.displayName}");
            return got > 0;
        }

        public int Count(string id) => Main.CountOf(id) + Equipment.CountOf(id);

        /// <summary>Verbraucht Gegenstaende aus dem Rucksack. false = nicht genug, nichts passiert.</summary>
        public bool Consume(string id, int count = 1)
        {
            if (Main.CountOf(id) < count) return false;
            Main.Remove(id, count);
            return true;
        }

        /// <summary>Wirft n Stueck aus einem Platz in die Welt vor die Fuesse des Spielers.</summary>
        public void DropFromSlot(Inventory inv, int slot, int count)
        {
            var s = inv.Get(slot);
            if (s == null) return;
            var taken = inv.Take(slot, Mathf.Min(count, s.count));
            if (taken != null) DropStack(taken);
        }

        public void DropStack(ItemStack stack)
        {
            Vector2 dir = controller.FacingVector;
            // Vor einer Wand faellt er an der Wand statt dahinter
            Vector3 from = transform.position + Vector3.up * 0.2f;
            Vector3 at = ItemPickup.SafePoint(from, from + (Vector3)(dir * 0.5f)) - Vector3.up * 0.2f;
            ItemPickup.Spawn(stack, at, dir * 2.2f, this);
        }

        // ------------------------------------------------------------------ Benutzen
        /// <summary>Benutzt den Gegenstand in einem Platz: anlegen, essen/trinken/heilen oder nachfuellen.</summary>
        public bool Use(Inventory inv, int slot)
        {
            var s = inv.Get(slot);
            if (s == null || survival.Sim.IsDead) return false;
            var def = s.def;

            if (def.equipSlot != EquipSlotKind.None && inv != Equipment) return Equip(inv, slot);
            if (def.equipSlot != EquipSlotKind.None && inv == Equipment) return Unequip(slot);

            if (!string.IsNullOrEmpty(def.refuelsItemId)) return Refuel(inv, slot);

            if (!string.IsNullOrEmpty(def.consumableId))
            {
                // Waehrend des Verzehrs nichts Weiteres benutzen
                if (IsConsuming) return false;
                var cons = survival.Sim.Config.Consumable(def.consumableId);
                if (cons == null)
                {
                    Debug.LogWarning($"[Inventar] '{def.id}' verweist auf unbekanntes Verbrauchsgut '{def.consumableId}'.");
                    return false;
                }
                if (!WouldHaveEffect(cons)) { Say("You don't need that now."); return false; }

                // Aus dem offenen Inventar (Eingabe gesperrt) wirkt es sofort, in der Welt mit Animation und Balken
                string anim = UseAnimation(def);
                if (anim != null && actionAnim != null && !controller.InputLocked && actionAnim.HasAction(anim, true))
                {
                    if (!actionAnim.CanStartTimed) return false; // Kampf, Ausweichen oder andere Aktion
                    consumeStart = Time.time;
                    consumeEnd = consumeStart + ConsumeSeconds;
                    if (!actionAnim.PlayTimed(anim, ConsumeSeconds, true)) return false;
                    consumeInv = inv;
                    consumeSlot = slot;
                    consumeStack = s;
                    consumeVerb = def.useVerb;
                    return true;
                }
                return FinishConsume(inv, slot, def, cons);
            }
            return false;
        }

        /// <summary>Animation fuer einen Gegenstand: Essen eat, Trinken drink, Medizin interact. Sonst keine.</summary>
        static string UseAnimation(ItemDef def)
        {
            switch (def.category)
            {
                case ItemCategory.Food: return "eat";
                case ItemCategory.Drink: return "drink";
                case ItemCategory.Medicine: return "interact";
                default: return null;
            }
        }

        /// <summary>Kurzer Text fuer den Hinweis ueber der Schnellleiste ("Eat", "Drink", "Equip" ...). null = nicht benutzbar.</summary>
        public string UseVerb(ItemStack s)
        {
            if (s == null) return null;
            var d = s.def;
            if (d.equipSlot != EquipSlotKind.None) return "Equip";
            if (!string.IsNullOrEmpty(d.consumableId) || !string.IsNullOrEmpty(d.refuelsItemId)) return string.IsNullOrEmpty(d.useVerb) ? "Use" : d.useVerb;
            return null;
        }

        /// <summary>Aendert das Verbrauchsgut etwas? Nein, wenn es nur Werte aendert, die schon am Anschlag sind (satt essen, wenn man nicht hungrig ist).</summary>
        bool WouldHaveEffect(ConsumableDef c)
        {
            if (c.timed.Count > 0) return true;
            var sim = survival.Sim;
            foreach (var a in c.instant)
            {
                var sd = sim.Def(a.stat);
                if (sd == null || Mathf.Approximately(a.amount, 0f)) continue;
                float v = sim.Value(a.stat);
                if (a.amount > 0f ? v < sim.Max(a.stat) - 0.01f : v > sd.min + 0.01f) return true;
            }
            return false;
        }

        /// <summary>Wendet das Verbrauchsgut an: Werte, ein Stueck weniger, ggf. Rest (leere Flasche).</summary>
        bool FinishConsume(Inventory inv, int slot, ItemDef def, ConsumableDef cons)
        {
            survival.Sim.Consume(cons);
            if (def.consumedOnUse) inv.Take(slot, 1);
            if (!string.IsNullOrEmpty(def.leftoverItemId) && database != null)
            {
                var left = database.Get(def.leftoverItemId);
                if (left != null && Main.Add(left, 1) > 0) DropStack(new ItemStack(left, 1));
            }
            return true;
        }

        void UpdateConsume()
        {
            if (consumeStack == null) return;
            // Hand gewechselt, Stapel weg oder tot: abbrechen
            if (consumeInv.Get(consumeSlot) != consumeStack || (consumeInv == Main && consumeSlot != Selected) || survival.Sim.IsDead)
            {
                CancelConsume();
                return;
            }
            if (Time.time < consumeEnd) return;

            var inv = consumeInv;
            int slot = consumeSlot;
            var def = consumeStack.def;
            consumeStack = null;
            consumeInv = null;
            var cons = survival.Sim.Config.Consumable(def.consumableId);
            if (cons != null) FinishConsume(inv, slot, def, cons);
        }

        /// <summary>Bricht den laufenden Verzehr ab (nichts wird verbraucht).</summary>
        public void CancelConsume()
        {
            if (consumeStack == null) return;
            consumeStack = null;
            consumeInv = null;
            if (actionAnim != null) actionAnim.CancelTimed();
        }

        bool Equip(Inventory from, int slot)
        {
            var s = from.Get(slot);
            for (int i = 0; i < Equipment.Size; i++)
            {
                if (Equipment.FilterOf(i) != s.def.equipSlot) continue;
                var old = Equipment.Get(i);
                if (old == null)
                {
                    Equipment.Set(i, s);
                    from.Set(slot, null);
                }
                else
                {
                    Equipment.Set(i, s);
                    from.Set(slot, old);
                }
                return true;
            }
            return false;
        }

        bool Unequip(int equipSlot)
        {
            var s = Equipment.Get(equipSlot);
            if (s == null) return false;
            int left = Main.Add(s);
            if (left > 0) { Say("Backpack is full."); return false; }
            Equipment.Set(equipSlot, null);
            return true;
        }

        bool Refuel(Inventory inv, int slot)
        {
            var fuel = inv.Get(slot);
            ItemStack target = null;
            // Erst die Hand, dann Ausruestung, dann der Rest
            target = FindRefuelTarget(Main.Get(Selected), fuel) ?? FindRefuelTarget(Equipment, fuel) ?? FindRefuelTarget(Main, fuel);
            if (target == null) { Say("Nothing to refill."); return false; }
            target.durability = Mathf.Min(target.def.maxDurability, target.durability + fuel.def.refuelAmount);
            inv.Take(slot, 1);
            Main.Notify();
            Equipment.Notify();
            Say(target.def.displayName + " refilled.");
            return true;
        }

        static ItemStack FindRefuelTarget(ItemStack s, ItemStack fuel) =>
            s != null && s.def.id == fuel.def.refuelsItemId && s.durability < s.def.maxDurability ? s : null;

        static ItemStack FindRefuelTarget(Inventory inv, ItemStack fuel)
        {
            for (int i = 0; i < inv.Size; i++)
            {
                var t = FindRefuelTarget(inv.Get(i), fuel);
                if (t != null) return t;
            }
            return null;
        }

        // ------------------------------------------------------------------ Ausruestung wirkt aufs Survival-System
        void ApplyEquipmentEffects()
        {
            if (survival == null || survival.Sim == null) return;
            var effects = new List<Effect>();
            for (int i = 0; i < Equipment.Size; i++)
            {
                var s = Equipment.Get(i);
                if (s != null) effects.AddRange(s.def.equipEffects);
            }
            survival.Sim.SetModifiers(this, effects);
        }

        // ------------------------------------------------------------------ Waffe in der Hand
        public WeaponInfo CurrentWeapon()
        {
            var s = SelectedStack;
            if (s != null && s.def.IsWeapon)
            {
                var d = s.def;
                // Fernwaffe ohne Munition und kaputte Waffen: wie Faeuste
                bool broken = d.HasDurability && s.durability <= 0f;
                if (!broken)
                    return new WeaponInfo { def = d, style = d.weapon, damage = d.damage, reach = d.reach, staminaCost = d.staminaCostMultiplier, range = d.rangedRange };
            }
            return new WeaponInfo { def = null, style = WeaponStyle.Fists, damage = 1, reach = 0f, staminaCost = 1f, range = 0f };
        }

        /// <summary>Munition fuer die Waffe in der Hand vorhanden? Verbraucht sie, wenn consume gesetzt ist.</summary>
        public bool HasAmmo(WeaponInfo w, bool consume)
        {
            if (w.def == null || string.IsNullOrEmpty(w.def.ammoItemId)) return true;
            if (Main.CountOf(w.def.ammoItemId) < 1) return false;
            if (consume) Main.Remove(w.def.ammoItemId, 1);
            return true;
        }

        /// <summary>Haltbarkeit der Waffe in der Hand senken (pro Treffer/Schuss). Bei 0 bricht sie.</summary>
        public void WearWeapon(WeaponInfo w)
        {
            var s = SelectedStack;
            if (w.def == null || s == null || s.def != w.def || !w.def.HasDurability) return;
            s.durability -= w.def.durabilityPerUse;
            if (s.durability <= 0f)
            {
                Main.Set(Selected, null);
                Say($"Your {w.def.displayName} broke.");
            }
            else Main.Notify(Selected);
        }

        // ------------------------------------------------------------------ Licht in der Hand
        ItemStack LightSource()
        {
            var hand = SelectedStack;
            if (hand != null && hand.def.IsLight && (!hand.def.HasDurability || hand.durability > 0f)) return hand;
            for (int i = 0; i < Equipment.Size; i++)
            {
                var e = Equipment.Get(i);
                if (e != null && e.def.IsLight && (!e.def.HasDurability || e.durability > 0f)) return e;
            }
            return null;
        }

        void UpdateHeldLight()
        {
            if (survival == null || survival.Sim == null) return;
            float hours = survival.Sim.TotalGameHours;
            float dh = Mathf.Max(0f, hours - lastHours);
            lastHours = hours;

            var src = LightSource();
            if (src == null)
            {
                if (handLight != null && handLight.enabled) handLight.enabled = false;
                survival.CarriesLight = false;
                burningStack = null;
                return;
            }
            if (handLight == null)
            {
                var go = new GameObject("Hand-Licht");
                go.transform.SetParent(transform, false);
                go.transform.localPosition = lightOffset;
                handLight = go.AddComponent<Light2D>();
                handLight.lightType = Light2D.LightType.Point;
                handLight.shadowsEnabled = false;
            }
            var d = src.def;
            handLight.enabled = true;
            handLight.color = d.lightColor;
            handLight.pointLightOuterRadius = d.lightRadius;
            handLight.pointLightInnerRadius = d.lightRadius * 0.15f;
            float flicker = 1f + (Mathf.PerlinNoise(7.3f, Time.time * 3f) - 0.5f) * 2f * lightFlicker;
            // Der Brennstoff geht zur Neige: das Licht wird schwaecher
            float fuel = d.HasDurability ? Mathf.Clamp01(src.durability / (d.maxDurability * 0.2f)) : 1f;
            handLight.intensity = d.lightIntensity * flicker * Mathf.Lerp(0.5f, 1f, fuel);
            survival.CarriesLight = true;
            burningStack = src;

            if (d.HasDurability && dh > 0f)
            {
                src.durability = Mathf.Max(0f, src.durability - d.burnPerHour * dh);
                if (src.durability <= 0f)
                {
                    Say(d.consumedWhenBurnedOut ? $"The {d.displayName.ToLowerInvariant()} burned out." : $"The {d.displayName.ToLowerInvariant()} ran out of fuel.");
                    if (d.consumedWhenBurnedOut) RemoveStack(src);
                    Main.Notify();
                    Equipment.Notify();
                }
                else if (Time.frameCount % 30 == 0) { Main.Notify(Selected); }
            }
        }

        void RemoveStack(ItemStack s)
        {
            for (int i = 0; i < Main.Size; i++) if (Main.Get(i) == s) { Main.Take(i, 1); return; }
            for (int i = 0; i < Equipment.Size; i++) if (Equipment.Get(i) == s) { Equipment.Take(i, 1); return; }
        }

        // ------------------------------------------------------------------ Nachrichten, Speichern
        public void Say(string text) => Message?.Invoke(text);

        [Serializable]
        class SaveData
        {
            public InventorySave main, equipment;
            public int selected;
        }

        public string SaveJson() => JsonUtility.ToJson(new SaveData { main = Main.Save(), equipment = Equipment.Save(), selected = Selected });

        public void LoadJson(string json)
        {
            if (string.IsNullOrEmpty(json)) return;
            var d = JsonUtility.FromJson<SaveData>(json);
            Main.Load(d.main, database);
            Equipment.Load(d.equipment, database);
            Selected = Mathf.Clamp(d.selected, 0, hotbarSize - 1);
            SelectedChanged?.Invoke(Selected);
            ApplyEquipmentEffects();
        }
    }
}
