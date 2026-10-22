using System.Collections.Generic;

namespace Nightward.Survival
{
    /// <summary>Ein Essen aus dem Ghostpixxells-Paket (Art/_IMPORTED): Anzeige, Wirkung und Icon-Nummer (Art/Items/Essen/Food_NNN_*.png).</summary>
    public class FoodDef
    {
        public string id, name, desc, leftover;
        public int icon;
        public int stack = 8, value = 2;
        public bool uncommon;
        public List<StatAmount> effects = new List<StatAmount>();
    }

    /// <summary>Geschirr ohne Wirkung (Teller, Schalen), bleibt nach dem Essen vom Teller uebrig.</summary>
    public class WareDef
    {
        public string id, name, desc;
        public int icon, stack = 8;
    }

    /// <summary>
    /// Alle Speisen des Spiels aus dem Essens-Paket, an einer Stelle: daraus entstehen die Gegenstaende (ItemCatalog) und die
    /// Verbrauchsgueter der SurvivalConfig (SurvivalDefaults). Werte: Hunger sinkt um hunger, Durst/Laune/Leben/Stress/Kaelte/Sanity
    /// aendern sich direkt (Kaelte negativ = waermt, Durst negativ = loescht Durst, positiv = salzig). Brot saettigt 32, Eintopf 55.
    /// Angerichtet (Teller/Schale, "_plated") saettigt ein Drittel mehr, hebt die Laune und hinterlaesst den leeren Teller.
    /// </summary>
    public static class FoodTable
    {
        static List<FoodDef> foods;
        static List<WareDef> ware;

        public static IReadOnlyList<FoodDef> All { get { Build(); return foods; } }
        public static IReadOnlyList<WareDef> Ware { get { Build(); return ware; } }

        static FoodDef F(int icon, string id, string name, float hunger, float happy, string desc, float thirst = 0f, float health = 0f,
                         float stress = 0f, float cold = 0f, float sanity = 0f, int stack = 8, int value = 2, bool uncommon = false)
        {
            var f = new FoodDef { id = id, name = name, desc = desc, icon = icon, stack = stack, value = value, uncommon = uncommon };
            Add(f, StatId.Hunger, -hunger);
            Add(f, StatId.Happiness, happy);
            Add(f, StatId.Thirst, thirst);
            Add(f, StatId.Health, health);
            Add(f, StatId.Stress, stress);
            Add(f, StatId.Cold, cold);
            Add(f, StatId.Sanity, sanity);
            foods.Add(f);
            return f;
        }

        static void Add(FoodDef f, StatId stat, float amount)
        {
            if (amount != 0f) f.effects.Add(new StatAmount(stat, amount));
        }

        /// <summary>Angerichtete Fassung eines Essens (anderes Icon, Teller oder Schale als Rest).</summary>
        static void P(int icon, string baseId, string leftover = "plate")
        {
            var b = foods.Find(x => x.id == baseId);
            var f = new FoodDef
            {
                id = baseId + "_plated", name = b.name + " (Plated)", icon = icon, leftover = leftover, stack = System.Math.Max(2, b.stack / 2),
                value = b.value + 2, uncommon = b.uncommon, desc = "Served properly. " + b.desc,
            };
            bool happy = false;
            foreach (var e in b.effects)
            {
                float a = e.amount;
                if (e.stat == StatId.Hunger) a *= 1.35f;
                if (e.stat == StatId.Happiness) { a += 2f; happy = true; }
                f.effects.Add(new StatAmount(e.stat, a));
            }
            if (!happy) f.effects.Add(new StatAmount(StatId.Happiness, 2f));
            foods.Add(f);
        }

        static void Build()
        {
            if (foods != null) return;
            foods = new List<FoodDef>();
            ware = new List<WareDef>
            {
                new WareDef { id = "platter", name = "Serving Platter", desc = "An oval dish for the table.", icon = 1, stack = 4 },
                new WareDef { id = "plate", name = "Plate", desc = "Clean, for once.", icon = 2, stack = 8 },
                new WareDef { id = "plate_stack", name = "Stack of Plates", desc = "Enough for a whole table.", icon = 3, stack = 2 },
                new WareDef { id = "bowl", name = "Bowl", desc = "Deep enough for soup.", icon = 4, stack = 8 },
            };

            // ---- Backwaren
            F(7, "crusty_bread", "Crusty Bread", 30, 1, "Hard crust, soft inside.");
            F(9, "baguette", "Baguette", 34, 2, "Long and crisp.", thirst: 2, stack: 4);
            F(11, "buns", "Bread Buns", 20, 1, "Two small buns.");
            F(20, "bagel", "Bagel", 26, 1, "Chewy, with a hole.");
            F(48, "garlic_bread", "Garlic Bread", 22, 2, "Smells up the whole room.");
            F(65, "bread_loaf", "Bread Loaf", 40, 1, "A sliced white loaf.", stack: 4);
            // ---- Fleisch und Fisch
            F(13, "bacon", "Bacon", 24, 3, "Crispy and salty.", thirst: 5);
            F(69, "meatball", "Meatball", 20, 2, "On a stick, still warm.");
            F(85, "roast_chicken", "Roast Chicken", 60, 6, "Golden and juicy.", health: 3, stack: 2, value: 8, uncommon: true);
            F(88, "salmon", "Salmon Fillet", 34, 3, "Pink and rich.", health: 3, value: 4);
            F(95, "steak", "Steak", 50, 4, "Seared on both sides.", health: 4, stack: 2, value: 7, uncommon: true);
            F(97, "sushi", "Sushi", 26, 4, "Raw fish on rice.", value: 4);
            F(36, "dumplings", "Dumplings", 34, 3, "Soft and steaming.", cold: -6);
            // ---- Gerichte
            F(15, "burger", "Burger", 42, 4, "Stacked high.", thirst: 4, stack: 2, value: 4);
            F(17, "wrapped_burger", "Wrapped Burger", 40, 4, "Wrapped in a napkin.", thirst: 4, stack: 2, value: 4);
            F(18, "burrito", "Burrito", 40, 3, "Rolled tight.", thirst: 4, stack: 2, value: 3);
            F(54, "hotdog", "Hotdog", 32, 3, "A sausage in a bun.", stack: 4, value: 3);
            F(55, "hotdog_sauce", "Hotdog with Sauce", 34, 4, "Mustard and ketchup.", stack: 4, value: 3);
            F(92, "sandwich", "Sandwich", 34, 3, "Ham, cheese and lettuce.", stack: 4, value: 3);
            F(81, "pizza", "Pizza Slice", 30, 5, "Still stretchy.", stack: 4, value: 3);
            F(99, "taco", "Taco", 28, 4, "Crunchy shell.", stack: 4, value: 3);
            F(32, "curry_sauce", "Curry Sauce", 26, 3, "Warming spice.", cold: -8, stack: 4, value: 3);
            F(67, "mac_and_cheese", "Mac and Cheese", 42, 5, "Creamy and heavy.", cold: -10, stack: 2, value: 4);
            F(94, "spaghetti", "Spaghetti", 48, 4, "A plate of noodles.", cold: -6, stack: 2, value: 4);
            F(87, "ramen", "Ramen", 52, 5, "A bowl of hot broth.", thirst: -6, cold: -18, stack: 2, value: 5, uncommon: true);
            F(38, "fried_egg", "Fried Egg", 20, 2, "Sunny side up.");
            F(40, "egg_salad", "Egg Salad", 24, 2, "Cool and creamy.", thirst: -2);
            F(73, "omelette", "Omelette", 30, 3, "Folded around herbs.", value: 3);
            F(44, "french_fries", "French Fries", 22, 3, "Salty and golden.", thirst: 4);
            F(77, "potato_chips", "Potato Chips", 12, 3, "Crunchy and salty.", thirst: 6);
            F(24, "cheese_puffs", "Cheese Puffs", 14, 3, "Orange fingers.", thirst: 6);
            F(71, "nacho", "Nacho Chips", 8, 2, "Needs a dip.", thirst: 3);
            F(83, "popcorn", "Popcorn", 10, 4, "Light and buttery.", thirst: 3);
            // ---- Suesses
            F(5, "apple_pie", "Apple Pie", 22, 5, "A warm slice.", stack: 4);
            F(22, "cheesecake", "Cheesecake", 20, 6, "Smooth and rich.", stack: 4, value: 3);
            F(26, "chocolate", "Chocolate", 10, 7, "A dark bar.", stress: -3, value: 3);
            F(28, "cookies", "Cookies", 12, 5, "Still soft in the middle.");
            F(30, "chocolate_cake", "Chocolate Cake", 20, 7, "Dense and dark.", stress: -3, stack: 4, value: 3);
            F(34, "donut", "Donut", 14, 5, "Glazed and sticky.");
            F(42, "egg_tart", "Egg Tart", 14, 4, "Flaky pastry, custard centre.");
            F(46, "fruitcake", "Fruitcake", 22, 4, "Heavy with fruit and nuts.", stack: 4);
            F(50, "gummy_bear", "Giant Gummy Bear", 10, 6, "Chewy and red.", stress: -2);
            F(52, "gingerbread_man", "Gingerbread Man", 12, 4, "He looks worried.");
            F(57, "ice_cream", "Ice Cream", 10, 7, "Three scoops.", thirst: -4, cold: 6, stack: 2);
            F(59, "jelly", "Jelly", 10, 4, "Wobbles when you look at it.", thirst: -3);
            F(61, "jam", "Jam Jar", 12, 5, "Strawberry, with a checked lid.", stack: 4, value: 3);
            F(63, "lemon_pie", "Lemon Pie", 20, 5, "Sharp and sweet.", thirst: -3, stack: 4);
            F(75, "pudding", "Pudding", 16, 6, "Caramel on top.");
            F(79, "pancakes", "Pancakes", 28, 5, "A short stack with syrup.", stack: 4, value: 3);
            F(90, "strawberry_cake", "Strawberry Cake", 20, 7, "Pink and light.", stack: 4, value: 3);
            F(101, "waffle", "Waffle", 24, 5, "Cream and a cherry.", stack: 4, value: 3);

            // ---- Angerichtet (Teller oder Schale)
            P(6, "apple_pie"); P(8, "crusty_bread"); P(10, "baguette"); P(12, "buns"); P(14, "bacon"); P(16, "burger");
            P(19, "burrito"); P(21, "bagel"); P(23, "cheesecake"); P(25, "cheese_puffs", "bowl"); P(27, "chocolate"); P(29, "cookies");
            P(31, "chocolate_cake"); P(33, "curry_sauce"); P(35, "donut"); P(37, "dumplings"); P(39, "fried_egg"); P(41, "egg_salad", "bowl");
            P(43, "egg_tart"); P(45, "french_fries"); P(47, "fruitcake"); P(49, "garlic_bread"); P(51, "gummy_bear"); P(53, "gingerbread_man");
            P(56, "hotdog"); P(58, "ice_cream", "bowl"); P(60, "jelly"); P(62, "jam"); P(64, "lemon_pie"); P(66, "bread_loaf");
            P(68, "mac_and_cheese"); P(70, "meatball"); P(72, "nacho"); P(74, "omelette"); P(76, "pudding"); P(78, "potato_chips", "bowl");
            P(80, "pancakes"); P(82, "pizza"); P(84, "popcorn", "bowl"); P(86, "roast_chicken"); P(89, "salmon"); P(91, "strawberry_cake");
            P(93, "sandwich"); P(96, "steak"); P(98, "sushi"); P(100, "taco"); P(102, "waffle");

            // Spaghetti und Ramen sind schon angerichtet: sie hinterlassen Teller bzw. Schale
            foods.Find(x => x.id == "spaghetti").leftover = "plate";
            foods.Find(x => x.id == "ramen").leftover = "bowl";
        }
    }
}
