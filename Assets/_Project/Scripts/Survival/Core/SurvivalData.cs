using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Survival
{
    /// <summary>Eine einzelne Wirkung. Rate-Effekte sind in der Einheit des Zielwerts (pro Spielstunde oder pro Sekunde).</summary>
    [Serializable]
    public class Effect
    {
        public EffectKind kind;
        [Tooltip("Nur fuer StatRate / StatDrainMult / StatRecoverMult")]
        public StatId stat;
        [Tooltip("StatRate: Menge pro Einheit. Multiplikatoren: Faktor (1 = keine Wirkung). Sperren: 1 = aktiv")]
        public float value = 1f;

        public Effect() { }
        public Effect(EffectKind kind, StatId stat, float value) { this.kind = kind; this.stat = stat; this.value = value; }

        public static Effect Rate(StatId stat, float perUnit) => new Effect(EffectKind.StatRate, stat, perUnit);
        public static Effect Drain(StatId stat, float factor) => new Effect(EffectKind.StatDrainMult, stat, factor);
        public static Effect Recover(StatId stat, float factor) => new Effect(EffectKind.StatRecoverMult, stat, factor);
        public static Effect Gameplay(EffectKind kind, float value = 1f) => new Effect(kind, StatId.Health, value);

        public Effect Clone() => new Effect(kind, stat, value);

        public override string ToString() => EffectKinds.UsesStat(kind) ? $"{kind}({stat}) {value:0.##}" : $"{kind} {value:0.##}";
    }

    /// <summary>Eine Bedingung. Mehrere Bedingungen einer Regel gelten zusammen (UND).</summary>
    [Serializable]
    public class Condition
    {
        public ConditionKind kind;
        public ContextFlag flag;
        public StatId stat;
        public MoodId mood;
        [Tooltip("StatAbove/StatBelow: Prozent 0-100. MoodAtLeast: Stufe 1-4")]
        public float value;
        [Tooltip("Bedingung umkehren")]
        public bool negate;

        public static Condition Flag(ContextFlag f, bool negate = false) => new Condition { kind = ConditionKind.Flag, flag = f, negate = negate };
        public static Condition Above(StatId s, float percent) => new Condition { kind = ConditionKind.StatAbove, stat = s, value = percent };
        public static Condition Below(StatId s, float percent) => new Condition { kind = ConditionKind.StatBelow, stat = s, value = percent };
        public static Condition Mood(MoodId m, int level) => new Condition { kind = ConditionKind.MoodAtLeast, mood = m, value = level };
    }

    /// <summary>"Wenn alle Bedingungen zutreffen, gelten diese Effekte." Das Grundelement fuer Umwelt, Taetigkeiten und Querwirkungen.</summary>
    [Serializable]
    public class Rule
    {
        public string name;
        public bool enabled = true;
        public List<Condition> when = new List<Condition>();
        public List<Effect> effects = new List<Effect>();
    }

    /// <summary>Ein Wert (Leben, Hunger, ...) mit Grenzen, Startwert und Grundrate.</summary>
    [Serializable]
    public class StatDef
    {
        public StatId id;
        public string displayName;
        public RateUnit unit = RateUnit.PerGameHour;
        public float min;
        public float max = 100f;
        public float start = 100f;
        [Tooltip("Aenderung pro Einheit ohne jeden Effekt (negativ = faellt von selbst)")]
        public float baseRate;
        [Tooltip("An = hoeher ist besser (Leben, Ausdauer, Sanity, Laune). Aus = hoeher ist schlechter (Hunger, Durst, ...)")]
        public bool higherIsBetter = true;

        public float Range => Mathf.Max(0.0001f, max - min);
    }

    /// <summary>Aus welchem Wert eine Stimmung ihre Schwere bezieht. from/to bilden die Schwere (0-1) auf 0-1 ab.</summary>
    [Serializable]
    public class MoodSource
    {
        public StatId stat;
        [Range(0f, 1f), Tooltip("Ab dieser Schwere des Werts beginnt die Stimmung (0 = ganz gut, 1 = ganz schlecht)")]
        public float from;
        [Range(0f, 2f), Tooltip("Bei dieser Schwere ist die Stimmung voll ausgepraegt")]
        public float to = 1f;
    }

    /// <summary>Eine Stufe einer Stimmung: Text fuer das HUD und die Effekte, die auf dieser Stufe gelten.</summary>
    [Serializable]
    public class MoodStage
    {
        [Tooltip("Optionaler Text (das HUD hat eigene englische Texte)")]
        public string text;
        public List<Effect> effects = new List<Effect>();
    }

    /// <summary>
    /// Eine Stimmung. Schwere = Maximum ueber alle Quellen. Die vier Schwellen legen fest, ab welcher Schwere
    /// Stufe 1-4 beginnt. Positive Stufen (optional) gelten, wenn keine negative aktiv ist.
    /// </summary>
    [Serializable]
    public class MoodDef
    {
        public MoodId id;
        public string displayName;
        [Tooltip("Name der HUD-Kachel (NeedKind), z. B. Hunger, Durst, Muede, Erschoepft")]
        public string hudTile;
        public List<MoodSource> sources = new List<MoodSource>();
        [Tooltip("Schwere (0-1), ab der Stufe 1, 2, 3, 4 beginnt")]
        public float[] thresholds = { 0.25f, 0.5f, 0.75f, 0.9f };
        [Tooltip("Positive Stufen: Guete (0-1) des ersten Werts, ab der Positiv 1 und 2 beginnt. Leer = keine positive Stimmung")]
        public float[] positiveThresholds = new float[0];
        [Tooltip("Um so viel muss die Schwere unter die Schwelle fallen, bevor die Stufe wieder sinkt (verhindert Flackern)")]
        public float hysteresis = 0.04f;
        public List<MoodStage> stages = new List<MoodStage>();
        public List<MoodStage> positiveStages = new List<MoodStage>();
    }

    [Serializable]
    public class StatAmount
    {
        public StatId stat;
        public float amount;
        public StatAmount() { }
        public StatAmount(StatId stat, float amount) { this.stat = stat; this.amount = amount; }
    }

    /// <summary>Ein Effekt mit Ablaufzeit (Tee, Rausch-Nachwirkung, Segen ...). Dauer in Spielstunden.</summary>
    [Serializable]
    public class TimedEffectDef
    {
        public string id;
        public float durationHours = 2f;
        [Tooltip("Erneutes Anwenden setzt die Dauer zurueck (sonst wird sie addiert)")]
        public bool refresh = true;
        public List<Effect> effects = new List<Effect>();
    }

    /// <summary>Essen, Trinken, Medizin: sofortige Aenderungen plus zeitlich begrenzte Effekte.</summary>
    [Serializable]
    public class ConsumableDef
    {
        public string id;
        public string displayName;
        [Tooltip("Sofortige Aenderung (positiv/negativ) an Werten")]
        public List<StatAmount> instant = new List<StatAmount>();
        public List<TimedEffectDef> timed = new List<TimedEffectDef>();
    }

    /// <summary>Alle Einzelwerte, die sich nicht als Regel ausdruecken lassen.</summary>
    [Serializable]
    public class SurvivalTuning
    {
        [Header("Zeit")]
        [Tooltip("Sekunden pro Spielstunde, wenn kein Tag-Nacht-Zyklus da ist")]
        public float fallbackSecondsPerGameHour = 25f;
        [Range(0f, 1f), Tooltip("Ab diesem NightFactor gilt die Nacht")]
        public float nightThreshold = 0.5f;

        [Header("Kampf")]
        [Tooltip("Leben = so viele Lebenspunkte (Kampfregeln: 3). Ein Treffer von 1 nimmt Max/Lebenspunkte")]
        public int lifePoints = 3;
        [Tooltip("Unverwundbar nach einem Treffer (Sekunden)")]
        public float hitInvulnerability = 2f;
        [Tooltip("Unverwundbar beim Ausweichen (Sekunden, Kampfregeln: 0,3)")]
        public float dodgeWindow = 0.3f;
        [Range(0f, 0.5f), Tooltip("Bleibt nach einem Treffer weniger als dieser Anteil eines Lebenspunkts uebrig, ist der Spieler tot")]
        public float deathMarginLifePoints = 0.2f;
        [Tooltip("Schmerz = Schaden mal Faktor")]
        public float painPerDamage = 0.8f;
        public float stressPerDamage = 0.25f;
        public float sanityPerDamage = 0.08f;

        [Header("Ausdauer")]
        public float attackStaminaCost = 8f;
        public float dodgeStaminaCost = 25f;
        [Tooltip("So lange nach dem letzten Verbrauch (Sekunden) regeneriert die Ausdauer noch nicht")]
        public float staminaRegenDelay = 0.9f;
        [Range(0f, 1f), Tooltip("War die Ausdauer leer, darf erst ab diesem Anteil wieder gesprintet werden")]
        public float windedRecoverFraction = 0.25f;

        [Header("Bewegung")]
        public float sprintSpeedMultiplier = 1.55f;
        public float sneakSpeedMultiplier = 0.55f;

        [Header("Schlaf")]
        [Range(0f, 1f), Tooltip("Unter diesem Sanity-Anteil verweigert der Spieler den Schlaf (Regelwerk: 40 %)")]
        public float sleepSanityBlock = 0.4f;
        [Range(0f, 1f), Tooltip("Unter diesem Sanity-Anteil drohen Albtraeume")]
        public float nightmareSanityBelow = 0.5f;
        [Range(0f, 1f), Tooltip("Albtraum-Chance bei Sanity 0")]
        public float nightmareMaxChance = 0.7f;
        public float nightmareSanityLoss = 12f;
        [Tooltip("Wie viel schneller Hunger/Durst im Schlaf laufen, ist als Regel 'Schlaf' hinterlegt")]
        public float sleepStepHours = 0.25f;

        [Header("Gespraeche")]
        [Tooltip("Gleicher Gespraechspartner gibt erst nach dieser Zeit (Spielstunden) wieder volle Wirkung")]
        public float conversationCooldownHours = 6f;
        [Range(0f, 1f), Tooltip("Anteil der Wirkung bei Wiederholung innerhalb der Abklingzeit")]
        public float conversationRepeatFactor = 0.2f;
        public float conversationLoneliness = -28f;
        public float conversationHappiness = 4f;
        public float conversationSanity = 2.5f;
        public float conversationStress = -4f;

        [Header("Zusammenbruch")]
        [Tooltip("Bei dieser Muedigkeit (Prozent) bricht der Spieler zusammen (Ereignis Collapsed)")]
        public float collapseFatiguePercent = 100f;

        [Header("Nach dem Tod (absolute Werte, Regelwerk: geschwaecht, niedrige Sanity)")]
        public List<StatAmount> afterDeath = new List<StatAmount>();
    }
}
