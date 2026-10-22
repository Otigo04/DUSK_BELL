using System;
using System.Collections.Generic;
using Nightward.Items;
using Nightward.Survival;
using UnityEngine;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Standard-Gegenstaende des Spiels (Texte englisch wie die UI). Daraus erzeugt InventorySetup die ItemDef-Assets
    /// in Data/Items. Danach sind die Assets die Quelle: dort im Inspector balancen. "Katalog zuruecksetzen" ueberschreibt sie wieder.
    /// Icons: Art/Items/...
    /// </summary>
    public static class ItemCatalog
    {
        public class Entry
        {
            public string id, name, desc, icon, folder;
            public ItemCategory category;
            public ItemRarity rarity;
            public int stack = 16, value = 1;
            public Action<ItemDef> extra;
            /// <summary>Wird bei jedem Einrichten angewendet (auch ohne Ueberschreiben): nur Werte, die zu Animationen/Kleidung gehoeren.</summary>
            public Action<ItemDef> always;
            public Entry Always(Action<ItemDef> a) { always = a; return this; }
        }

        static readonly List<Entry> list = new List<Entry>();

        static Entry Add(string folder, string id, string name, string icon, ItemCategory cat, int stack, int value, string desc, ItemRarity rarity = ItemRarity.Common, Action<ItemDef> extra = null)
        {
            var e = new Entry { id = id, name = name, icon = icon, folder = folder, category = cat, stack = stack, value = value, desc = desc, rarity = rarity, extra = extra };
            list.Add(e);
            return e;
        }

        // ------------------------------------------------------------------ Kleidung aus JSON
        [Serializable] class ClothingEffect { public string type, key; public float value; }
        [Serializable] class ClothingEntry { public string id, name, desc, rarity, slot; public int value; public string[] palette; public ClothingEffect[] effects; }
        [Serializable] class ClothingFile { public ClothingEntry[] items; }

        static ClothingEntry[] LoadClothing()
        {
            const string path = "Assets/_Project/Art/Items/Kleidung/kleidung.json";
            if (!System.IO.File.Exists(path)) { Debug.LogWarning("[Katalog] Kleidung fehlt: " + path + " (python gen_kleidung.py)"); return new ClothingEntry[0]; }
            return JsonUtility.FromJson<ClothingFile>(System.IO.File.ReadAllText(path)).items;
        }

        static Effect ToEffect(ClothingEffect e)
        {
            switch (e.type)
            {
                case "rate": return Effect.Rate((StatId)Enum.Parse(typeof(StatId), e.key), e.value);
                case "drain": return Effect.Drain((StatId)Enum.Parse(typeof(StatId), e.key), e.value);
                case "recover": return Effect.Recover((StatId)Enum.Parse(typeof(StatId), e.key), e.value);
                default: return Effect.Gameplay((EffectKind)Enum.Parse(typeof(EffectKind), e.key), e.value);
            }
        }

        /// <summary>Pfad (relativ zu Art/Items) des Essens-Icons mit dieser Nummer (Food_NNN_name.png).</summary>
        static string FoodIcon(int n)
        {
            var files = System.IO.Directory.GetFiles("Assets/_Project/Art/Items/Essen", "Food_" + n.ToString("000") + "_*.png");
            return files.Length > 0 ? "Essen/" + System.IO.Path.GetFileName(files[0]) : "Essen/Food_" + n.ToString("000") + ".png";
        }

        static Action<ItemDef> Use(string consumable, string verb) => d => { d.consumableId = consumable; d.useVerb = verb; };

        public static List<Entry> All()
        {
            if (list.Count > 0) return list;

            // ---- Essen
            Add("Essen", "bread", "Bread", "Vorraete/Item_Brot.png", ItemCategory.Food, 8, 2, "Dense and filling.", extra: Use("bread", "Eat"));
            Add("Essen", "apple", "Apple", "Vorraete/Item_Apfel.png", ItemCategory.Food, 16, 1, "Crisp and a little sour.", extra: Use("apple", "Eat"));
            Add("Essen", "dried_meat", "Smoked Sausage", "Vorraete/Item_Raeucherwurst.png", ItemCategory.Food, 8, 3, "Salty. Makes you thirsty.", extra: Use("dried_meat", "Eat"));
            Add("Essen", "cheese", "Cheese", "Vorraete/Item_Kaese.png", ItemCategory.Food, 8, 3, "A hard wedge from the village.", extra: Use("cheese", "Eat"));
            Add("Essen", "honey", "Honey Jar", "Vorraete/Item_Honigglas.png", ItemCategory.Food, 4, 4, "Sweet. It lifts your spirits.", ItemRarity.Uncommon, Use("honey", "Eat"));
            Add("Essen", "forest_mushroom", "Forest Mushroom", "Vorraete/Item_Waldpilz.png", ItemCategory.Food, 16, 1, "Found near the tree line.", extra: Use("forest_mushroom", "Eat"));

            // ---- Trinken
            Add("Trinken", "water", "Water Bottle", "Versorgung/Item_Wasserflasche.png", ItemCategory.Drink, 4, 2, "Cold and clear.", extra: Use("water", "Drink"));
            Add("Trinken", "tea_calming", "Calming Tea", "Versorgung/Item_Beruhigungstee.png", ItemCategory.Drink, 4, 4, "Settles nerves and sobers you up.", ItemRarity.Uncommon, Use("tea_calming", "Drink"));
            Add("Trinken", "beer", "Beer", "Getraenke/Item_Glas_Bier.png", ItemCategory.Drink, 4, 1, "From Ilhan's bar.", extra: Use("beer", "Drink"));
            Add("Trinken", "mead", "Mead", "Getraenke/Item_Glas_Met.png", ItemCategory.Drink, 4, 1, "Sweet and strong.", extra: Use("mead", "Drink"));
            Add("Trinken", "red_wine", "Red Wine", "Getraenke/Item_Glas_Rotwein.png", ItemCategory.Drink, 4, 2, "Warms the chest.", extra: Use("red_wine", "Drink"));
            Add("Trinken", "white_wine", "White Wine", "Getraenke/Item_Glas_Weisswein.png", ItemCategory.Drink, 4, 2, "Light and dry.", extra: Use("white_wine", "Drink"));
            Add("Trinken", "schnaps", "Schnapps", "Getraenke/Item_Glas_Schnaps.png", ItemCategory.Drink, 4, 2, "Burns on the way down.", extra: Use("schnaps", "Drink"));
            Add("Trinken", "whisky", "Whisky", "Getraenke/Item_Glas_Whisky.png", ItemCategory.Drink, 4, 3, "Smoky and slow.", ItemRarity.Uncommon, Use("whisky", "Drink"));
            Add("Trinken", "rum", "Rum", "Getraenke/Item_Glas_Rum.png", ItemCategory.Drink, 4, 3, "Dark and sweet.", ItemRarity.Uncommon, Use("rum", "Drink"));
            Add("Trinken", "bourbon", "Bourbon", "Getraenke/Item_Glas_Bourbon.png", ItemCategory.Drink, 4, 4, "Aged in oak.", ItemRarity.Uncommon, Use("bourbon", "Drink"));

            // ---- Medizin und Genuss
            Add("Medizin", "bandage", "Bandage", "Versorgung/Item_Verband.png", ItemCategory.Medicine, 8, 3, "Clean linen for wounds.", extra: Use("bandage", "Apply"));
            Add("Medizin", "herbal_salve", "Herbal Salve", "Versorgung/Item_Salbentiegel.png", ItemCategory.Medicine, 4, 5, "Eases pain.", ItemRarity.Uncommon, Use("herbal_salve", "Apply"));
            Add("Medizin", "tobacco", "Pipe Tobacco", "Versorgung/Item_Tabakpfeife.png", ItemCategory.Medicine, 8, 2, "A calm few minutes.", extra: Use("tobacco", "Smoke"));

            // ---- Essen aus dem Essens-Paket (Art/_IMPORTED/Ghostpixxells_pixelfood), alle Werte in Survival/Core/FoodTable.cs
            foreach (var f in FoodTable.All)
            {
                var food = f;
                Add("Essen", food.id, food.name, FoodIcon(food.icon), ItemCategory.Food, food.stack, food.value, food.desc,
                    food.uncommon ? ItemRarity.Uncommon : ItemRarity.Common,
                    d => { d.consumableId = food.id; d.useVerb = "Eat"; if (!string.IsNullOrEmpty(food.leftover)) d.leftoverItemId = food.leftover; });
            }
            foreach (var w in FoodTable.Ware) Add("Essen", w.id, w.name, FoodIcon(w.icon), ItemCategory.Misc, w.stack, 1, w.desc);

            // ---- Waffen (Kampfregeln: jede Waffe hat Haltbarkeit)
            Add("Waffen", "knife", "Hunting Knife", "Waffen/Item_Jagdmesser.png", ItemCategory.Weapon, 1, 8, "Quick and quiet.", ItemRarity.Common,
                d => { d.weapon = WeaponStyle.Knife; d.damage = 2; d.maxDurability = 40; d.reach = 0.85f; d.staminaCostMultiplier = 0.9f; });
            // Animationen (Zustaende <anim>_<Richtung>, 14 fps): Dauer = Bilder / 14, Treffer = Zeit des Aufprall-Bildes
            Add("Waffen", "club", "Wooden Club", "Waffen/Item_Knueppel.png", ItemCategory.Weapon, 1, 4, "Heavy. Needs both hands.", ItemRarity.Common,
                d => { d.weapon = WeaponStyle.Bat; d.damage = 3; d.maxDurability = 25; d.reach = 1f; d.staminaCostMultiplier = 1.4f; })
                .Always(d => { d.attackAnim = "club"; d.attackCombo = 1; d.attackSeconds = 7f / 14f; d.hitSeconds = 0.26f; });
            Add("Waffen", "bat", "Baseball Bat", "Waffen/Item_Baseballschlaeger.png", ItemCategory.Weapon, 1, 6, "Splintered, but it still swings.", ItemRarity.Common,
                d => { d.weapon = WeaponStyle.Bat; d.damage = 3; d.maxDurability = 30; d.reach = 1f; d.staminaCostMultiplier = 1.3f; })
                .Always(d => { d.attackAnim = "bat"; d.attackCombo = 1; d.attackSeconds = 7f / 14f; d.hitSeconds = 0.26f; });
            Add("Waffen", "axe", "Wood Axe", "Waffen/Item_Axt.png", ItemCategory.Weapon, 1, 10, "High damage, tiring to swing.", ItemRarity.Uncommon,
                d => { d.weapon = WeaponStyle.Bat; d.damage = 4; d.maxDurability = 45; d.reach = 0.95f; d.staminaCostMultiplier = 1.9f; })
                .Always(d => { d.attackAnim = "chop"; d.attackCombo = 1; d.attackSeconds = 8f / 14f; d.hitSeconds = 0.3f; });
            Add("Waffen", "machete", "Machete", "Waffen/Item_Machete.png", ItemCategory.Weapon, 1, 9, "Fast. Cuts through brush.", ItemRarity.Uncommon,
                d => { d.weapon = WeaponStyle.Knife; d.damage = 2; d.maxDurability = 35; d.reach = 0.95f; d.staminaCostMultiplier = 1f; })
                .Always(d => { d.attackAnim = "machete"; d.attackCombo = 2; d.attackSeconds = 6f / 14f; d.hitSeconds = 0.21f; });
            Add("Waffen", "crowbar", "Crowbar", "Waffen/Item_Brecheisen.png", ItemCategory.Weapon, 1, 9, "Opens doors. Settles arguments.", ItemRarity.Uncommon,
                d => { d.weapon = WeaponStyle.Bat; d.damage = 3; d.maxDurability = 60; d.reach = 0.95f; d.staminaCostMultiplier = 1.3f; })
                .Always(d => { d.attackAnim = "crowbar"; d.attackCombo = 1; d.attackSeconds = 7f / 14f; d.hitSeconds = 0.26f; });
            Add("Waffen", "flail", "Threshing Flail", "Waffen/Item_Dreschflegel.png", ItemCategory.Weapon, 1, 8, "Slow to swing. Hits hard.", ItemRarity.Uncommon,
                d => { d.weapon = WeaponStyle.Bat; d.damage = 3; d.maxDurability = 35; d.reach = 1.05f; d.staminaCostMultiplier = 1.6f; })
                .Always(d => { d.attackAnim = "flail"; d.attackCombo = 1; d.attackSeconds = 8f / 14f; d.hitSeconds = 0.32f; });
            Add("Waffen", "pistol", "Revolver", "Waffen/Item_Pistole.png", ItemCategory.Weapon, 1, 30, "Loud. Every shot counts.", ItemRarity.Rare,
                d => { d.weapon = WeaponStyle.Pistol; d.damage = 4; d.maxDurability = 60; d.ammoItemId = "ammo"; d.rangedRange = 9f; d.staminaCostMultiplier = 0.6f; });
            Add("Waffen", "rifle", "Hunting Rifle", "Waffen/Item_Jagdgewehr.png", ItemCategory.Weapon, 1, 45, "Long reach. Loud enough to wake the village.", ItemRarity.Rare,
                d => { d.weapon = WeaponStyle.Rifle; d.damage = 6; d.maxDurability = 80; d.ammoItemId = "ammo"; d.rangedRange = 13f; d.staminaCostMultiplier = 0.8f; });
            // Waffen aus dem Waffen-Paket (Art/_IMPORTED/GUNS_V1.00); Animationen gen_hauptfiguren_combat.py (shotgun, assault, sniper)
            Add("Waffen", "pistol_silver", "Pistol", "Waffen/Item_Pistole_Silber.png", ItemCategory.Weapon, 1, 22, "Compact and reliable.", ItemRarity.Uncommon,
                d => { d.weapon = WeaponStyle.Pistol; d.damage = 3; d.maxDurability = 70; d.ammoItemId = "ammo"; d.rangedRange = 10f; d.staminaCostMultiplier = 0.6f; });
            Add("Waffen", "shotgun", "Pump Shotgun", "Waffen/Item_Pumpgun.png", ItemCategory.Weapon, 1, 40, "Pump, aim, pray.", ItemRarity.Rare,
                d => { d.weapon = WeaponStyle.Rifle; d.damage = 8; d.maxDurability = 50; d.ammoItemId = "shells"; d.rangedRange = 7f; d.staminaCostMultiplier = 1.3f; })
                .Always(d => { d.attackAnim = "shotgun"; d.attackCombo = 1; d.attackSeconds = 9f / 14f; d.hitSeconds = 0.16f; });
            Add("Waffen", "assault_rifle", "Assault Rifle", "Waffen/Item_Sturmgewehr.png", ItemCategory.Weapon, 1, 60, "Not made for this village.", ItemRarity.Rare,
                d => { d.weapon = WeaponStyle.Rifle; d.damage = 4; d.maxDurability = 120; d.ammoItemId = "ammo"; d.rangedRange = 12f; d.staminaCostMultiplier = 0.7f; })
                .Always(d => { d.attackAnim = "assault"; d.attackCombo = 1; d.attackSeconds = 7f / 14f; d.hitSeconds = 0.16f; });
            Add("Waffen", "sniper_rifle", "Bolt-Action Rifle", "Waffen/Item_Kar98.png", ItemCategory.Weapon, 1, 55, "One shot, then work the bolt.", ItemRarity.Rare,
                d => { d.weapon = WeaponStyle.Rifle; d.damage = 9; d.maxDurability = 70; d.ammoItemId = "ammo"; d.rangedRange = 18f; d.staminaCostMultiplier = 1f; })
                .Always(d => { d.attackAnim = "sniper"; d.attackCombo = 1; d.attackSeconds = 10f / 14f; d.hitSeconds = 0.16f; });
            Add("Waffen", "shells", "Shotgun Shells", "Waffen/Item_Schrot.png", ItemCategory.Material, 16, 2, "Ammunition for the shotgun.", ItemRarity.Uncommon);
            Add("Waffen", "ammo", "Cartridges", "Waffen/Item_Munition.png", ItemCategory.Material, 24, 1, "Ammunition for revolver and rifle.", ItemRarity.Uncommon);

            // ---- Licht (Laterne braucht Oel, Kerze und Fackel brennen ab)
            Add("Licht", "candle", "Candle", "Licht/Item_Kerze.png", ItemCategory.Light, 1, 1, "A small, safe pool of light.", ItemRarity.Common,
                d => { d.lightRadius = 3.5f; d.maxDurability = 40; d.burnPerHour = 8f; d.consumedWhenBurnedOut = true; d.lightIntensity = 0.8f; d.lightColor = new Color32(0xff, 0xd2, 0x7a, 255); });
            Add("Licht", "torch", "Torch", "Licht/Item_Fackel.png", ItemCategory.Light, 1, 2, "Bright, but burns fast.", ItemRarity.Common,
                d => { d.lightRadius = 5.5f; d.maxDurability = 60; d.burnPerHour = 15f; d.consumedWhenBurnedOut = true; d.lightIntensity = 1f; d.lightColor = new Color32(0xe8, 0x73, 0x3a, 255); });
            Add("Licht", "lantern", "Lantern", "Licht/Item_Laterne.png", ItemCategory.Light, 1, 14, "Keeps the dark at a distance. Needs oil.", ItemRarity.Uncommon,
                d => { d.lightRadius = 7.5f; d.maxDurability = 100; d.burnPerHour = 6f; d.lightIntensity = 1.1f; d.equipSlot = EquipSlotKind.Light; d.lightColor = new Color32(0xff, 0xa5, 0x50, 255); });
            Add("Licht", "oil_jug", "Oil Jug", "Licht/Item_Oelkrug.png", ItemCategory.Material, 4, 3, "Refills a lantern.", ItemRarity.Common,
                d => { d.refuelsItemId = "lantern"; d.refuelAmount = 60f; d.useVerb = "Refill"; });
            Add("Licht", "tinderbox", "Tinderbox", "Licht/Item_Zunderbuechse.png", ItemCategory.Tool, 1, 4, "Dry tinder and flint.");

            // ---- Talismane (nur im Wald zu finden, Zusatzschutz)
            Add("Talismane", "talisman_blue", "Blue Talisman", "Talismane/Talisman_Blau.png", ItemCategory.Talisman, 1, 20, "Quiets a racing mind.", ItemRarity.Rare,
                d => { d.equipSlot = EquipSlotKind.Talisman; d.equipEffects.Add(Effect.Rate(StatId.Stress, -2f)); });
            Add("Talismane", "talisman_yellow", "Yellow Talisman", "Talismane/Talisman_Gelb.png", ItemCategory.Talisman, 1, 20, "Warm, like a lit window.", ItemRarity.Rare,
                d => { d.equipSlot = EquipSlotKind.Talisman; d.equipEffects.Add(Effect.Rate(StatId.Sanity, 1.5f)); });
            Add("Talismane", "talisman_green", "Green Talisman", "Talismane/Talisman_Gruen.png", ItemCategory.Talisman, 1, 20, "Wounds close a little faster.", ItemRarity.Rare,
                d => { d.equipSlot = EquipSlotKind.Talisman; d.equipEffects.Add(Effect.Rate(StatId.Health, 0.8f)); });
            Add("Talismane", "talisman_red", "Red Talisman", "Talismane/Talisman_Rot.png", ItemCategory.Talisman, 1, 25, "Dulls the bite of a blow.", ItemRarity.Rare,
                d => { d.equipSlot = EquipSlotKind.Talisman; d.equipEffects.Add(Effect.Gameplay(EffectKind.DamageTakenMult, 0.85f)); });
            Add("Talismane", "talisman_violet", "Violet Talisman", "Talismane/Talisman_Violett.png", ItemCategory.Talisman, 1, 30, "Tired legs find a second wind.", ItemRarity.Unique,
                d => { d.equipSlot = EquipSlotKind.Talisman; d.equipEffects.Add(Effect.Recover(StatId.Stamina, 1.25f)); });

            // ---- Kleidung: 10 Oberteile, 10 Hosen, 10 Schuhe aus Art/Items/Kleidung/kleidung.json (geschrieben von gen_kleidung.py)
            foreach (var c in LoadClothing())
            {
                var cl = c;
                string icon = cl.id == "wool_coat" ? "Kleidung/Item_Wollmantel.png" : "Kleidung/Item_" + cl.id + ".png";
                var slot = (EquipSlotKind)System.Enum.Parse(typeof(EquipSlotKind), cl.slot);
                var rarity = (ItemRarity)System.Enum.Parse(typeof(ItemRarity), cl.rarity);
                Add("Kleidung", cl.id, cl.name, icon, ItemCategory.Clothing, 1, cl.value, cl.desc, rarity, d =>
                {
                    d.equipSlot = slot;
                    foreach (var e in cl.effects) d.equipEffects.Add(ToEffect(e));
                }).Always(d =>
                {
                    d.equipSlot = slot;
                    var pal = new Color[cl.palette.Length];
                    for (int i = 0; i < pal.Length; i++) { ColorUtility.TryParseHtmlString(cl.palette[i], out pal[i]); }
                    d.outfitPalette = pal;
                });
            }

            // ---- Werkzeug und Material
            Add("Werkzeug", "hammer", "Hammer", "Werkzeug/Item_Hammer.png", ItemCategory.Tool, 1, 5, "For barricades.");
            Add("Werkzeug", "plank", "Wooden Plank", "Werkzeug/Item_Holzbrett.png", ItemCategory.Material, 16, 1, "Rough-sawn.");
            Add("Werkzeug", "nails", "Nail Pouch", "Werkzeug/Item_Nagelbeutel.png", ItemCategory.Material, 8, 2, "A handful of iron nails.");
            Add("Werkzeug", "rope", "Rope", "Werkzeug/Item_Seil.png", ItemCategory.Tool, 4, 3, "Twenty feet of hemp.");
            Add("Werkzeug", "compass", "Compass", "Werkzeug/Item_Kompass.png", ItemCategory.Tool, 1, 12, "The needle never settles at night.", ItemRarity.Uncommon);
            Add("Werkzeug", "forest_map", "Forest Map", "Werkzeug/Item_Waldkarte.png", ItemCategory.Key, 1, 6, "Hand-drawn, with gaps.", ItemRarity.Uncommon);
            Add("Werkzeug", "backpack", "Spare Backpack", "Werkzeug/Item_Rucksack.png", ItemCategory.Misc, 1, 8, "Worn leather straps.");
            Add("Werkzeug", "firewood", "Firewood", "Vorraete/Item_Brennholz.png", ItemCategory.Material, 16, 1, "Split and dry.");
            Add("Werkzeug", "herbs", "Herb Bundle", "Vorraete/Item_Kraeuterbuendel.png", ItemCategory.Material, 16, 2, "Dried and tied.");
            Add("Werkzeug", "supply_sack", "Supply Sack", "Vorraete/Item_Vorratssack.png", ItemCategory.Misc, 4, 5, "Heavy with provisions.");

            // ---- Schutz und Hinweise
            Add("Schutz", "hand_bell", "Hand Bell", "Schutz/Item_Handglocke.png", ItemCategory.Misc, 1, 6, "Rung at dusk.", ItemRarity.Uncommon);
            Add("Schutz", "house_key", "House Key", "Schutz/Item_Hausschluessel.png", ItemCategory.Key, 1, 1, "Iron, worn smooth.");
            Add("Schutz", "incense", "Incense Bundle", "Schutz/Item_Raeucherbuendel.png", ItemCategory.Material, 8, 3, "Its smoke hangs in doorways.");
            Add("Schutz", "salt_pouch", "Salt Pouch", "Schutz/Item_Salzbeutel.png", ItemCategory.Material, 8, 3, "A line across the threshold.");
            Add("Schutz", "sheriff_badge", "Sheriff's Badge", "Schutz/Item_SheriffAbzeichen.png", ItemCategory.Key, 1, 0, "Bulut's own.", ItemRarity.Unique);
            Add("Schutz", "door_bar", "Door Bar", "Schutz/Item_Tuerriegel.png", ItemCategory.Tool, 1, 6, "A heavy wooden beam.");
            Add("Hinweise", "monster_tooth", "Monster Tooth", "Hinweise/Item_Monsterzahn.png", ItemCategory.Misc, 4, 0, "Too sharp to be human.", ItemRarity.Rare);
            Add("Hinweise", "sealed_letter", "Sealed Letter", "Hinweise/Item_Siegelbrief.png", ItemCategory.Key, 1, 0, "The seal is unbroken.", ItemRarity.Unique);
            Add("Hinweise", "cloth_scrap", "Torn Cloth", "Hinweise/Item_Stofffetzen.png", ItemCategory.Misc, 4, 0, "Caught on a branch.", ItemRarity.Uncommon);
            Add("Hinweise", "journal", "Journal", "Hinweise/Item_Tagebuch.png", ItemCategory.Key, 1, 0, "Someone else's handwriting.", ItemRarity.Rare);

            // ---- Waehrung
            Add("Waehrung", "wachtgroschen", "Wachtgroschen", "Waehrung/Item_Wachtgroschen.png", ItemCategory.Currency, 99, 1, "Village silver (WG).", extra: d => d.autoPickup = true);
            Add("Waehrung", "coin_purse", "Coin Purse", "Waehrung/Item_Muenzbeutel.png", ItemCategory.Currency, 4, 20, "Heavier than it looks.", ItemRarity.Uncommon, d => d.autoPickup = true);
            return list;
        }
    }
}
