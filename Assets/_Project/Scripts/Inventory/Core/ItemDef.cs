using System.Collections.Generic;
using Nightward.Survival;
using UnityEngine;

namespace Nightward.Items
{
    public enum ItemCategory { Food, Drink, Medicine, Weapon, Tool, Light, Talisman, Clothing, Material, Currency, Key, Misc }

    public enum ItemRarity { Common, Uncommon, Rare, Unique }

    /// <summary>Angriffsart einer Waffe. Bestimmt die Animation (punch, knife, bat, shoot) und das Kampfverhalten.</summary>
    public enum WeaponStyle { None, Fists, Knife, Bat, Pistol, Rifle }

    /// <summary>Ausruestungsplatz, in den ein Gegenstand passt (None = kein Ausruestungsgegenstand). Clothing = Oberkoerper, Legs = Hose, Feet = Schuhe.</summary>
    public enum EquipSlotKind { None, Light, Talisman, Clothing, Legs, Feet }

    /// <summary>
    /// Ein Gegenstandstyp als Asset: Anzeige, Stapelgroesse, Wirkung beim Benutzen (Essen, Trinken, Medizin ueber die
    /// SurvivalConfig), Waffenwerte, Ausruestungs-Effekte und Lichtquelle. Alle Werte im Inspector aenderbar.
    /// Neuer Gegenstand: Rechtsklick Create > Nightward > Item, ins ItemDatabase-Asset eintragen.
    /// </summary>
    [CreateAssetMenu(fileName = "Item_Neu", menuName = "Nightward/Item")]
    public class ItemDef : ScriptableObject
    {
        [Header("Anzeige")]
        [Tooltip("Eindeutige Kennung, z. B. bread. Wird in Speicherstaenden, Loot und Verbrauch benutzt")]
        public string id;
        public string displayName;
        [TextArea(1, 3)] public string description;
        public Sprite icon;
        public ItemCategory category = ItemCategory.Misc;
        public ItemRarity rarity = ItemRarity.Common;
        [Tooltip("Wie viele auf einen Platz passen. 1 = nicht stapelbar (Werkzeuge, Waffen mit Haltbarkeit)")]
        [Min(1)] public int maxStack = 16;
        [Tooltip("Wert in Wachtgroschen")]
        public int value = 1;
        [Tooltip("Liegt in der Welt und wird beim Vorbeigehen automatisch aufgenommen (Muenzen). Sonst mit F aufheben")]
        public bool autoPickup;

        [Header("Benutzen (Rechtsklick auf die Schnellleiste, E im Inventar)")]
        [Tooltip("Id eines Verbrauchsguts aus der SurvivalConfig (bread, water, tea_calming ...). Leer = nicht benutzbar")]
        public string consumableId;
        [Tooltip("Text auf dem Hinweis, z. B. Eat, Drink, Apply")]
        public string useVerb = "Use";
        [Tooltip("Beim Benutzen wird ein Stueck verbraucht")]
        public bool consumedOnUse = true;
        [Tooltip("Optional: Gegenstand, der nach dem Benutzen uebrig bleibt (z. B. leere Flasche)")]
        public string leftoverItemId;
        [Tooltip("Dieser Gegenstand fuellt einen Brennstoff nach: Id der Lichtquelle (z. B. lantern fuer Oel)")]
        public string refuelsItemId;
        [Tooltip("So viel Haltbarkeit (Brennstoff) bekommt die Lichtquelle")]
        public float refuelAmount = 50f;

        [Header("Waffe")]
        public WeaponStyle weapon = WeaponStyle.None;
        [Tooltip("Animation des Angriffs (Zustand <Name>_<Richtung>, bei Kombo <Name>1, <Name>2 ...), z. B. machete, chop, club, crowbar, flail, rifle. Leer = die Standard-Animation der Waffenart")]
        public string attackAnim;
        [Tooltip("Anzahl der Schlaege einer Kombo (die Animationen heissen dann <attackAnim>1..n)")]
        [Min(1)] public int attackCombo = 1;
        [Tooltip("Dauer des Angriffs in Sekunden (Clip: Bilder / 14). 0 = Standard der Waffenart")]
        public float attackSeconds;
        [Tooltip("Zeitpunkt des Treffers/Schusses in Sekunden nach Beginn. 0 = Standard der Waffenart")]
        public float hitSeconds;
        [Min(0)] public int damage = 1;
        [Tooltip("Reichweite des Schlags in Units (0 = Standard)")]
        public float reach;
        [Tooltip("Reichweite des Schusses in Units")]
        public float rangedRange = 9f;
        [Tooltip("Munition (Id) fuer Fernwaffen, leer = keine")]
        public string ammoItemId;
        [Tooltip("Faktor auf die Ausdauerkosten eines Schlags")]
        public float staminaCostMultiplier = 1f;

        [Header("Haltbarkeit")]
        [Tooltip("0 = unbegrenzt. Waffen verlieren pro Treffer/Schuss, Lichtquellen pro Spielstunde. Bei 0 bricht die Waffe bzw. ist das Licht leer")]
        [Min(0)] public int maxDurability;
        [Min(0)] public float durabilityPerUse = 1f;

        [Header("Ausruestung")]
        public EquipSlotKind equipSlot = EquipSlotKind.None;
        [Tooltip("Kleidung (Oberteil, Hose, Schuhe): Farben, in die PlayerOutfit die Figur umfaerbt. Oberteil: Licht, Grund, Schatten, Tief. " +
                 "Hose: Dunkel, Grund, Licht. Schuhe: Sohle, Dunkel, Grund, Licht. Leer = die Figur sieht gleich aus")]
        public Color[] outfitPalette = new Color[0];
        [Tooltip("Gelten, solange der Gegenstand angelegt ist (z. B. warme Jacke: Kaelte langsamer)")]
        public List<Effect> equipEffects = new List<Effect>();

        [Header("Lichtquelle (in Hand oder angelegt)")]
        [Tooltip("0 = kein Licht")]
        public float lightRadius;
        public Color lightColor = new Color(1f, 0.65f, 0.31f, 1f);
        [Range(0f, 2f)] public float lightIntensity = 0.9f;
        [Tooltip("Verbrauch an Haltbarkeit pro Spielstunde, solange es leuchtet")]
        public float burnPerHour = 10f;
        [Tooltip("Verbrennt komplett (Kerze, Fackel): bei 0 verschwindet der Gegenstand")]
        public bool consumedWhenBurnedOut;

        public bool IsStackable => maxStack > 1;
        public bool HasDurability => maxDurability > 0;
        public bool IsLight => lightRadius > 0f;
        public bool IsWeapon => weapon != WeaponStyle.None;
        public bool IsRanged => weapon == WeaponStyle.Pistol || weapon == WeaponStyle.Rifle;
        public bool IsUsable => !string.IsNullOrEmpty(consumableId) || !string.IsNullOrEmpty(refuelsItemId) || equipSlot != EquipSlotKind.None;

        /// <summary>Titelfarbe nach Seltenheit (Palette der Style-Bibel).</summary>
        public static Color RarityColor(ItemRarity r)
        {
            switch (r)
            {
                case ItemRarity.Uncommon: return new Color32(0x9a, 0xb8, 0x7a, 255); // Blattlicht
                case ItemRarity.Rare: return new Color32(0x6b, 0x7f, 0xb8, 255);     // Stoff Blau hell
                case ItemRarity.Unique: return new Color32(0xff, 0xa5, 0x50, 255);   // Laterne Orange
                default: return new Color32(0xff, 0xf1, 0xc9, 255);                  // Kerzenweiss
            }
        }

        void OnValidate()
        {
            if (maxStack < 1) maxStack = 1;
            if (HasDurability && maxStack > 1) maxStack = 1; // Gegenstaende mit Haltbarkeit stapeln nicht
        }
    }
}
