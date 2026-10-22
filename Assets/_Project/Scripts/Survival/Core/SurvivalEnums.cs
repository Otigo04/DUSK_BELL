namespace Nightward.Survival
{
    /// <summary>Alle Werte, die der Spieler hat. Neuer Wert = hier eintragen + ein StatDef in der SurvivalConfig.</summary>
    public enum StatId
    {
        Health,        // Leben
        Stamina,       // Ausdauer (Sprint, Schlag, Ausweichen)
        StaminaCap,    // Maximum-Erschoepfung: Obergrenze der Ausdauer, nur Rast erholt es
        Sanity,        // Geisteszustand
        Hunger,        // steigt = schlechter
        Thirst,        // steigt = schlechter
        Fatigue,       // Muedigkeit, steigt = schlechter
        Intoxication,  // Rausch, steigt = schlechter
        Pain,          // Schmerz nach Treffern, klingt ab
        Happiness,     // Laune, sinkt = schlechter
        Loneliness,    // Einsamkeit, steigt = schlechter
        Stress,        // Anspannung, steigt = schlechter
        Cold,          // Kaelte, steigt = schlechter
    }

    /// <summary>Stimmungen/Zustaende, die als Kachel im HUD erscheinen (Project-Zomboid-Prinzip, Stufe 1-4).</summary>
    public enum MoodId
    {
        Hungry,
        Thirsty,
        Tired,       // schlaefrig (Fatigue)
        Exhausted,   // koerperlich ausgepowert (Ausdauer / Maximum-Erschoepfung)
        Drunk,
        Wounded,
        Mood,        // traurig <-> froh
        Lonely,      // einsam <-> sozial
        Tense,       // angespannt <-> ruhig
        Cold,
        Shaken,      // Sanity niedrig: verstoert
    }

    /// <summary>Was der Spieler gerade tut. Genau eine Taetigkeit gleichzeitig.</summary>
    public enum ActivityKind { Idle, Walking, Sneaking, Sprinting, Fighting, Talking, Resting, Sleeping }

    /// <summary>
    /// Bedingungen fuer Regeln. Die ersten acht entsprechen 1:1 der ActivityKind (gleiche Reihenfolge).
    /// </summary>
    public enum ContextFlag
    {
        Idle, Walking, Sneaking, Sprinting, Fighting, Talking, Resting, Sleeping,
        Moving,         // Walking, Sneaking oder Sprinting
        Night,          // NightFactor ueber der Schwelle
        Indoors,
        LightIsland,    // im Licht einer Lampe/Kerze
        NearFire,       // bei Kamin/Lagerfeuer
        Darkness,       // Nacht, draussen und kein Licht in der Naehe
        Thicket,        // im Dickicht/Unterholz
        StaminaRested,  // seit einer Weile keine Ausdauer verbraucht (Regeneration darf laufen)
        Winded,         // Ausdauer war leer und hat sich noch nicht erholt
    }

    /// <summary>Was ein Effekt bewirkt. StatRate und die Stat-Multiplikatoren brauchen ein StatId.</summary>
    public enum EffectKind
    {
        StatRate,            // addiert zur Aenderungsrate des Werts (Einheit des Werts: pro Spielstunde oder pro Sekunde)
        StatDrainMult,       // multipliziert die Aenderung, die den Wert verschlechtert
        StatRecoverMult,     // multipliziert die Aenderung, die den Wert verbessert
        MoveSpeedMult,
        SprintSpeedMult,
        StaminaCostMult,     // Kosten fuer Schlag und Ausweichen
        DamageDealtMult,
        DamageTakenMult,
        ReactionWindowMult,  // Zeitfenster fuer Ausweichen/Reaktion
        ControlSway,         // Taumeln beim Laufen, 0..1 (addiert)
        Hallucination,       // Staerke von Halluzinationen, 0..1 (addiert)
        BlockSprint,
        BlockSleep,
        BlockAttack,
    }

    public enum ConditionKind
    {
        Flag,        // ContextFlag ist gesetzt
        StatAbove,   // Wert in Prozent (0-100) ueber value
        StatBelow,
        MoodAtLeast, // Stimmung hat mindestens Stufe value (nur negative Stufen)
    }

    /// <summary>In welcher Zeit ein Wert sich aendert.</summary>
    public enum RateUnit { PerGameHour, PerSecond }

    public static class EffectKinds
    {
        public static bool UsesStat(EffectKind k) => k <= EffectKind.StatRecoverMult;
        public static bool IsStatMult(EffectKind k) => k == EffectKind.StatDrainMult || k == EffectKind.StatRecoverMult;
        public static bool IsMultiplier(EffectKind k) => k >= EffectKind.MoveSpeedMult && k <= EffectKind.ReactionWindowMult;
        public static bool IsAdditive(EffectKind k) => k == EffectKind.ControlSway || k == EffectKind.Hallucination;
        public static bool IsBlock(EffectKind k) => k >= EffectKind.BlockSprint;
    }
}
