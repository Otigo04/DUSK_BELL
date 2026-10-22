using System.Collections.Generic;
using UnityEngine;
using E = Nightward.Survival.EffectKind;

namespace Nightward.Survival
{
    /// <summary>
    /// Standard-Balancing. Hier steht alles als Code, damit das System auch ohne Asset laeuft und sich
    /// per "Auf Standardwerte zuruecksetzen" jederzeit wiederherstellen laesst.
    /// Einheiten: PerGameHour = pro Spielstunde (1/24 eines Tag-Nacht-Zyklus), PerSecond = pro Echtzeit-Sekunde.
    /// Alle Werte laufen 0-100, Prozent-Bedingungen beziehen sich darauf.
    /// </summary>
    public static class SurvivalDefaults
    {
        public static SurvivalConfig Create()
        {
            var c = ScriptableObject.CreateInstance<SurvivalConfig>();
            c.hideFlags = HideFlags.DontSave;
            Fill(c);
            return c;
        }

        public static void Fill(SurvivalConfig c)
        {
            c.tuning = new SurvivalTuning();
            c.tuning.afterDeath = new List<StatAmount>
            {
                new StatAmount(StatId.Health, 30), new StatAmount(StatId.Stamina, 40), new StatAmount(StatId.StaminaCap, 60),
                new StatAmount(StatId.Sanity, 25), new StatAmount(StatId.Hunger, 55), new StatAmount(StatId.Thirst, 55),
                new StatAmount(StatId.Fatigue, 45), new StatAmount(StatId.Pain, 40), new StatAmount(StatId.Stress, 55),
                new StatAmount(StatId.Happiness, 35), new StatAmount(StatId.Intoxication, 0), new StatAmount(StatId.Cold, 20),
            };
            c.stats = Stats();
            c.moods = Moods();
            c.rules = Rules();
            c.consumables = Consumables();
            c.consumables.AddRange(FoodConsumables());
        }

        // ------------------------------------------------------------------ Werte
        static StatDef S(StatId id, string name, RateUnit unit, float start, float baseRate, bool better, float min = 0f) =>
            new StatDef { id = id, displayName = name, unit = unit, min = min, max = 100f, start = start, baseRate = baseRate, higherIsBetter = better };

        static List<StatDef> Stats() => new List<StatDef>
        {
            S(StatId.Health, "Leben", RateUnit.PerGameHour, 100, 0, true),
            S(StatId.Stamina, "Ausdauer", RateUnit.PerSecond, 100, 0, true),
            S(StatId.StaminaCap, "Maximum-Erschoepfung", RateUnit.PerSecond, 100, 0, true, 20f),
            S(StatId.Sanity, "Sanity", RateUnit.PerGameHour, 100, 0, true),
            S(StatId.Hunger, "Hunger", RateUnit.PerGameHour, 15, 2.4f, false),
            S(StatId.Thirst, "Durst", RateUnit.PerGameHour, 15, 3.4f, false),
            S(StatId.Fatigue, "Muedigkeit", RateUnit.PerGameHour, 5, 3.0f, false),
            S(StatId.Intoxication, "Rausch", RateUnit.PerGameHour, 0, -10f, false),
            S(StatId.Pain, "Schmerz", RateUnit.PerGameHour, 0, -5f, false),
            S(StatId.Happiness, "Laune", RateUnit.PerGameHour, 65, -0.5f, true),
            S(StatId.Loneliness, "Einsamkeit", RateUnit.PerGameHour, 25, 1.6f, false),
            S(StatId.Stress, "Anspannung", RateUnit.PerGameHour, 18, -1.2f, false),
            S(StatId.Cold, "Kaelte", RateUnit.PerGameHour, 0, 0f, false),
        };

        // ------------------------------------------------------------------ Regeln
        static Condition[] When(params Condition[] c) => c;
        static Condition F(ContextFlag f) => Condition.Flag(f);
        static Condition Not(ContextFlag f) => Condition.Flag(f, true);

        static Rule R(string name, Condition[] when, params Effect[] fx) =>
            new Rule { name = name, when = new List<Condition>(when), effects = new List<Effect>(fx) };

        static List<Rule> Rules() => new List<Rule>
        {
            // --- Ausdauer je Taetigkeit (pro Sekunde)
            R("Stehen: Ausdauer erholt sich", When(F(ContextFlag.Idle), F(ContextFlag.StaminaRested)), Effect.Rate(StatId.Stamina, 18f)),
            R("Gehen: Ausdauer erholt sich", When(F(ContextFlag.Walking), F(ContextFlag.StaminaRested)), Effect.Rate(StatId.Stamina, 10f)),
            R("Schleichen: Ausdauer erholt sich", When(F(ContextFlag.Sneaking), F(ContextFlag.StaminaRested)), Effect.Rate(StatId.Stamina, 12f)),
            R("Sprint: Ausdauer sinkt", When(F(ContextFlag.Sprinting)), Effect.Rate(StatId.Stamina, -14f)),
            R("Sprint: Maximum sinkt langsam", When(F(ContextFlag.Sprinting)), Effect.Rate(StatId.StaminaCap, -0.04f)),
            R("Sprint durchs Dickicht: Maximum sinkt", When(F(ContextFlag.Sprinting), F(ContextFlag.Thicket)), Effect.Rate(StatId.StaminaCap, -0.7f)),
            R("Rast: Ausdauer und Maximum erholen sich", When(F(ContextFlag.Resting)), Effect.Rate(StatId.Stamina, 28f), Effect.Rate(StatId.StaminaCap, 1.5f)),

            // --- Verbrauch je Taetigkeit (Multiplikatoren auf die Grundrate)
            R("Bewegung: etwas mehr Durst und Hunger", When(F(ContextFlag.Moving)), Effect.Drain(StatId.Thirst, 1.15f), Effect.Drain(StatId.Hunger, 1.1f)),
            R("Sprint: viel mehr Durst, Hunger, Muedigkeit", When(F(ContextFlag.Sprinting)),
                Effect.Drain(StatId.Thirst, 2.4f), Effect.Drain(StatId.Hunger, 1.7f), Effect.Drain(StatId.Fatigue, 1.5f)),
            R("Kampf: Anstrengung", When(F(ContextFlag.Fighting)),
                Effect.Drain(StatId.Thirst, 1.5f), Effect.Drain(StatId.Hunger, 1.3f), Effect.Rate(StatId.Stress, 5f)),
            R("Rast: Erholung", When(F(ContextFlag.Resting)),
                Effect.Rate(StatId.Fatigue, -2f), Effect.Rate(StatId.Stress, -4f), Effect.Rate(StatId.Sanity, 1f)),
            R("Schlaf: Erholung", When(F(ContextFlag.Sleeping)),
                Effect.Rate(StatId.Fatigue, -14f), Effect.Rate(StatId.Health, 4f), Effect.Rate(StatId.Sanity, 3f),
                Effect.Rate(StatId.Stress, -6f), Effect.Recover(StatId.Pain, 2f),
                Effect.Drain(StatId.Hunger, 0.5f), Effect.Drain(StatId.Thirst, 0.6f),
                Effect.Rate(StatId.Stamina, 40f), Effect.Rate(StatId.StaminaCap, 1.2f)),

            // --- Umwelt
            R("Dunkelheit: Sanity sinkt", When(F(ContextFlag.Darkness)), Effect.Rate(StatId.Sanity, -5f), Effect.Rate(StatId.Stress, 3f)),
            R("Dunkelheit und schwache Nerven: Panik", When(F(ContextFlag.Darkness), Condition.Below(StatId.Sanity, 30f)), Effect.Rate(StatId.Stress, 4f)),
            R("Lichtinsel: Sanity erholt sich", When(F(ContextFlag.LightIsland)), Effect.Rate(StatId.Sanity, 3f), Effect.Rate(StatId.Stress, -3f)),
            R("Feuer: Waerme und Ruhe", When(F(ContextFlag.NearFire)),
                Effect.Rate(StatId.Sanity, 3f), Effect.Rate(StatId.Stress, -3f), Effect.Rate(StatId.Happiness, 2f), Effect.Rate(StatId.Cold, -25f)),
            R("Drinnen: waermer", When(F(ContextFlag.Indoors)), Effect.Rate(StatId.Cold, -12f), Effect.Rate(StatId.Stress, -1f)),
            R("Nachts draussen: Kaelte", When(F(ContextFlag.Night), Not(ContextFlag.Indoors), Not(ContextFlag.NearFire)), Effect.Rate(StatId.Cold, 9f)),
            R("Tagsueber: Kaelte laesst nach", When(Not(ContextFlag.Night)), Effect.Rate(StatId.Cold, -8f)),

            // --- Querwirkungen
            R("Satt und getrunken: Leben erholt sich", When(Condition.Below(StatId.Hunger, 45f), Condition.Below(StatId.Thirst, 45f), Not(ContextFlag.Sleeping)),
                Effect.Rate(StatId.Health, 1f)),
        };

        // ------------------------------------------------------------------ Stimmungen
        static MoodStage St(params Effect[] fx) => new MoodStage { effects = new List<Effect>(fx) };
        static Effect G(EffectKind k, float v = 1f) => Effect.Gameplay(k, v);

        static MoodDef M(MoodId id, string name, string tile, float[] thr, float[] pos, MoodStage[] neg, MoodStage[] posStages, params MoodSource[] src) =>
            new MoodDef
            {
                id = id, displayName = name, hudTile = tile, thresholds = thr, positiveThresholds = pos ?? new float[0],
                stages = new List<MoodStage>(neg), positiveStages = new List<MoodStage>(posStages ?? new MoodStage[0]),
                sources = new List<MoodSource>(src),
            };

        static MoodSource Src(StatId s, float from = 0f, float to = 1f) => new MoodSource { stat = s, from = from, to = to };

        static List<MoodDef> Moods() => new List<MoodDef>
        {
            M(MoodId.Hungry, "Hungrig", "Hunger", new[] { 0.30f, 0.55f, 0.75f, 0.90f }, null,
                new[]
                {
                    St(),
                    St(Effect.Recover(StatId.Stamina, 0.92f), Effect.Rate(StatId.Happiness, -0.4f)),
                    St(Effect.Recover(StatId.Stamina, 0.82f), G(E.DamageDealtMult, 0.9f), Effect.Rate(StatId.Stress, 1.5f), Effect.Rate(StatId.Happiness, -0.8f)),
                    St(Effect.Rate(StatId.Health, -2.5f), G(E.MoveSpeedMult, 0.92f), G(E.DamageDealtMult, 0.75f), Effect.Recover(StatId.Stamina, 0.7f), Effect.Rate(StatId.Sanity, -1.5f)),
                }, null, Src(StatId.Hunger)),

            M(MoodId.Thirsty, "Durstig", "Durst", new[] { 0.30f, 0.55f, 0.75f, 0.90f }, null,
                new[]
                {
                    St(),
                    St(Effect.Recover(StatId.Stamina, 0.90f)),
                    St(Effect.Recover(StatId.Stamina, 0.78f), Effect.Rate(StatId.Stress, 2f)),
                    St(Effect.Rate(StatId.Health, -4.5f), G(E.MoveSpeedMult, 0.90f), Effect.Rate(StatId.Sanity, -2f), Effect.Recover(StatId.Stamina, 0.6f)),
                }, null, Src(StatId.Thirst)),

            M(MoodId.Tired, "Muede", "Muede", new[] { 0.35f, 0.60f, 0.80f, 0.93f }, null,
                new[]
                {
                    St(),
                    St(Effect.Recover(StatId.Stamina, 0.93f), G(E.ReactionWindowMult, 0.95f)),
                    St(Effect.Recover(StatId.Stamina, 0.85f), G(E.StaminaCostMult, 1.12f), G(E.MoveSpeedMult, 0.96f), G(E.ReactionWindowMult, 0.85f), Effect.Rate(StatId.Happiness, -0.5f)),
                    St(G(E.MoveSpeedMult, 0.90f), G(E.StaminaCostMult, 1.25f), G(E.ReactionWindowMult, 0.70f), Effect.Rate(StatId.Sanity, -2f), Effect.Recover(StatId.Stamina, 0.75f), G(E.Hallucination, 0.15f)),
                }, null, Src(StatId.Fatigue)),

            // Erschoepft: kurzfristig leere Ausdauer UND dauerhaft gesunkenes Maximum
            M(MoodId.Exhausted, "Erschoepft", "Erschoepft", new[] { 0.15f, 0.40f, 0.65f, 0.85f }, null,
                new[]
                {
                    St(Effect.Recover(StatId.Stamina, 0.95f)),
                    St(G(E.StaminaCostMult, 1.1f), G(E.SprintSpeedMult, 0.95f), Effect.Recover(StatId.Stamina, 0.9f)),
                    St(G(E.StaminaCostMult, 1.25f), G(E.MoveSpeedMult, 0.93f), G(E.SprintSpeedMult, 0.9f), Effect.Recover(StatId.Stamina, 0.8f)),
                    St(G(E.BlockSprint), G(E.MoveSpeedMult, 0.85f), G(E.StaminaCostMult, 1.5f), G(E.DamageDealtMult, 0.8f)),
                }, null, Src(StatId.Stamina, 0.72f, 1.25f), Src(StatId.StaminaCap, 0.1f, 1f)),

            M(MoodId.Drunk, "Betrunken", "Rausch", new[] { 0.15f, 0.35f, 0.60f, 0.85f }, null,
                new[]
                {
                    St(G(E.ControlSway, 0.12f)),
                    St(G(E.ControlSway, 0.30f), G(E.ReactionWindowMult, 0.85f), Effect.Rate(StatId.Stress, -3f), Effect.Rate(StatId.Happiness, 1.5f)),
                    St(G(E.ControlSway, 0.55f), G(E.MoveSpeedMult, 0.93f), G(E.DamageDealtMult, 0.85f), G(E.ReactionWindowMult, 0.70f), Effect.Rate(StatId.Fatigue, 2f)),
                    St(G(E.ControlSway, 1f), G(E.MoveSpeedMult, 0.80f), G(E.DamageDealtMult, 0.6f), G(E.ReactionWindowMult, 0.5f), G(E.Hallucination, 0.25f), Effect.Rate(StatId.Fatigue, 4f)),
                }, null, Src(StatId.Intoxication)),

            M(MoodId.Wounded, "Verletzt", "Verletzt", new[] { 0.12f, 0.35f, 0.60f, 0.80f }, null,
                new[]
                {
                    St(),
                    St(Effect.Recover(StatId.Stamina, 0.93f)),
                    St(G(E.MoveSpeedMult, 0.92f), G(E.DamageDealtMult, 0.9f), G(E.StaminaCostMult, 1.1f), Effect.Recover(StatId.Stamina, 0.85f)),
                    St(G(E.MoveSpeedMult, 0.78f), G(E.BlockSprint), G(E.DamageDealtMult, 0.7f)),
                }, null, Src(StatId.Health, 0f, 1f), Src(StatId.Pain)),

            M(MoodId.Mood, "Stimmung", "Stimmung", new[] { 0.45f, 0.60f, 0.78f, 0.90f }, new[] { 0.72f, 0.88f },
                new[]
                {
                    St(),
                    St(Effect.Rate(StatId.Sanity, -0.5f)),
                    St(Effect.Rate(StatId.Sanity, -1f), Effect.Recover(StatId.Stamina, 0.9f)),
                    St(Effect.Rate(StatId.Sanity, -2f), Effect.Recover(StatId.Stamina, 0.8f), Effect.Rate(StatId.Stress, 2f)),
                },
                new[]
                {
                    St(Effect.Rate(StatId.Sanity, 0.4f)),
                    St(Effect.Rate(StatId.Sanity, 0.8f), Effect.Rate(StatId.Stress, -1.5f)),
                }, Src(StatId.Happiness)),

            M(MoodId.Lonely, "Einsam", "Gesellschaft", new[] { 0.40f, 0.60f, 0.80f, 0.92f }, new[] { 0.82f, 0.93f },
                new[]
                {
                    St(),
                    St(Effect.Rate(StatId.Happiness, -0.6f)),
                    St(Effect.Rate(StatId.Happiness, -1.2f), Effect.Rate(StatId.Sanity, -0.8f)),
                    St(Effect.Rate(StatId.Happiness, -2f), Effect.Rate(StatId.Sanity, -1.5f), Effect.Rate(StatId.Stress, 1.5f)),
                },
                new[]
                {
                    St(Effect.Rate(StatId.Happiness, 0.4f)),
                    St(Effect.Rate(StatId.Happiness, 0.9f), Effect.Rate(StatId.Sanity, 0.5f)),
                }, Src(StatId.Loneliness)),

            M(MoodId.Tense, "Angespannt", "Anspannung", new[] { 0.35f, 0.55f, 0.75f, 0.90f }, new[] { 0.88f, 0.96f },
                new[]
                {
                    St(),
                    St(Effect.Recover(StatId.Stamina, 0.93f), G(E.ReactionWindowMult, 0.95f)),
                    St(Effect.Recover(StatId.Stamina, 0.85f), Effect.Rate(StatId.Sanity, -1f)),
                    St(Effect.Recover(StatId.Stamina, 0.7f), Effect.Rate(StatId.Sanity, -2f), G(E.Hallucination, 0.2f), G(E.ControlSway, 0.1f)),
                },
                new[]
                {
                    St(G(E.ReactionWindowMult, 1.05f)),
                    St(Effect.Recover(StatId.Stamina, 1.1f), Effect.Rate(StatId.Sanity, 0.6f)),
                }, Src(StatId.Stress)),

            M(MoodId.Cold, "Frierend", "Kalt", new[] { 0.25f, 0.50f, 0.75f, 0.90f }, null,
                new[]
                {
                    St(),
                    St(Effect.Recover(StatId.Stamina, 0.92f)),
                    St(Effect.Rate(StatId.Health, -0.8f), G(E.MoveSpeedMult, 0.96f), Effect.Recover(StatId.Stamina, 0.8f)),
                    St(Effect.Rate(StatId.Health, -2.5f), G(E.MoveSpeedMult, 0.88f), Effect.Recover(StatId.Stamina, 0.6f), Effect.Rate(StatId.Sanity, -1f)),
                }, null, Src(StatId.Cold)),

            M(MoodId.Shaken, "Verstoert", "Verstoert", new[] { 0.30f, 0.60f, 0.80f, 0.92f }, null,
                new[]
                {
                    St(Effect.Rate(StatId.Stress, 1f)),
                    St(Effect.Rate(StatId.Stress, 2.5f), G(E.ReactionWindowMult, 0.9f), G(E.Hallucination, 0.1f)),
                    St(Effect.Rate(StatId.Stress, 4f), G(E.ReactionWindowMult, 0.8f), G(E.Hallucination, 0.35f), G(E.ControlSway, 0.08f), Effect.Recover(StatId.Stamina, 0.85f)),
                    St(Effect.Rate(StatId.Stress, 6f), G(E.Hallucination, 0.7f), G(E.ControlSway, 0.2f), G(E.DamageTakenMult, 1.15f), Effect.Recover(StatId.Stamina, 0.7f)),
                }, null, Src(StatId.Sanity)),
        };

        // ------------------------------------------------------------------ Verbrauchsgueter
        static ConsumableDef Item(string id, string name, params StatAmount[] instant) =>
            new ConsumableDef { id = id, displayName = name, instant = new List<StatAmount>(instant) };

        static StatAmount A(StatId s, float amount) => new StatAmount(s, amount);

        static ConsumableDef WithTimed(ConsumableDef d, string id, float hours, params Effect[] fx)
        {
            d.timed.Add(new TimedEffectDef { id = id, durationHours = hours, effects = new List<Effect>(fx) });
            return d;
        }

        /// <summary>Alle Speisen aus der FoodTable als Verbrauchsgueter.</summary>
        public static List<ConsumableDef> FoodConsumables()
        {
            var list = new List<ConsumableDef>();
            foreach (var f in FoodTable.All) list.Add(Item(f.id, f.name, f.effects.ToArray()));
            return list;
        }

        static List<ConsumableDef> Consumables() => new List<ConsumableDef>
        {
            // Essen
            Item("bread", "Brot", A(StatId.Hunger, -32), A(StatId.Happiness, 1)),
            Item("apple", "Apfel", A(StatId.Hunger, -10), A(StatId.Thirst, -8)),
            Item("dried_meat", "Trockenfleisch", A(StatId.Hunger, -28), A(StatId.Thirst, 6)),
            Item("cheese", "Kaese", A(StatId.Hunger, -22), A(StatId.Happiness, 2)),
            Item("honey", "Honig", A(StatId.Hunger, -14), A(StatId.Happiness, 6), A(StatId.Sanity, 2), A(StatId.Stress, -4)),
            Item("forest_mushroom", "Waldpilz", A(StatId.Hunger, -12), A(StatId.Thirst, 3)),
            Item("stew", "Eintopf", A(StatId.Hunger, -55), A(StatId.Thirst, -10), A(StatId.Happiness, 5), A(StatId.Cold, -20), A(StatId.Health, 4)),
            // Trinken
            Item("water", "Wasser", A(StatId.Thirst, -38)),
            Item("spring_water", "Quellwasser", A(StatId.Thirst, -55), A(StatId.StaminaCap, 15), A(StatId.Fatigue, -5)),
            WithTimed(Item("tea_calming", "Beruhigungstee", A(StatId.Thirst, -20), A(StatId.Stress, -18), A(StatId.Sanity, 5), A(StatId.Cold, -10)),
                "calming_tea", 3f, Effect.Rate(StatId.Intoxication, -15f), Effect.Rate(StatId.Stress, -4f), Effect.Rate(StatId.Sanity, 1.5f)),
            // Getraenke aus Ilhans Bar (Docs: Getraenke - Rezepte und Preise)
            Item("beer", "Bier", A(StatId.Intoxication, 10), A(StatId.Sanity, 3), A(StatId.Thirst, -10), A(StatId.Happiness, 3)),
            Item("mead", "Met", A(StatId.Intoxication, 12), A(StatId.Sanity, 3), A(StatId.Thirst, -6), A(StatId.Happiness, 3)),
            Item("red_wine", "Rotwein", A(StatId.Intoxication, 12), A(StatId.Sanity, 5), A(StatId.Happiness, 3)),
            Item("white_wine", "Weisswein", A(StatId.Intoxication, 12), A(StatId.Sanity, 5), A(StatId.Happiness, 3)),
            WithTimed(Item("schnaps", "Schnaps", A(StatId.Intoxication, 20), A(StatId.Sanity, 8), A(StatId.Happiness, 2)),
                "spirit_warmth", 1f, Effect.Rate(StatId.Cold, -10f)),
            WithTimed(Item("whisky", "Whisky", A(StatId.Intoxication, 22), A(StatId.Sanity, 8), A(StatId.Happiness, 2)),
                "spirit_warmth", 1f, Effect.Rate(StatId.Cold, -10f)),
            WithTimed(Item("rum", "Rum", A(StatId.Intoxication, 22), A(StatId.Sanity, 8), A(StatId.Happiness, 2)),
                "spirit_warmth", 1f, Effect.Rate(StatId.Cold, -10f)),
            WithTimed(Item("bourbon", "Bourbon", A(StatId.Intoxication, 24), A(StatId.Sanity, 8), A(StatId.Happiness, 2)),
                "spirit_warmth", 1f, Effect.Rate(StatId.Cold, -10f)),
            // Sonstiges
            WithTimed(Item("tobacco", "Tabak", A(StatId.Stress, -14), A(StatId.Sanity, 3), A(StatId.Thirst, 4)),
                "tobacco_calm", 1.5f, Effect.Rate(StatId.Stress, -5f)),
            WithTimed(Item("bandage", "Verband", A(StatId.Health, 18), A(StatId.Pain, -25)),
                "bandaged", 6f, Effect.Rate(StatId.Health, 1.5f), Effect.Recover(StatId.Pain, 1.6f)),
            Item("herbal_salve", "Kraeutersalbe", A(StatId.Pain, -35), A(StatId.Health, 8)),
        };
    }
}
