using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Survival
{
    /// <summary>Zustand einer Stimmung: negative Stufe 0-4 oder (wenn keine negative aktiv ist) positive Stufe 0-2.</summary>
    public struct MoodState : IEquatable<MoodState>
    {
        public int level;
        public int positive;

        public bool IsActive => level > 0 || positive > 0;
        public bool IsPositive => level == 0 && positive > 0;
        /// <summary>Anzeige-Stufe: negativ 1-4 oder positiv 1-2.</summary>
        public int Stage => level > 0 ? level : positive;

        public bool Equals(MoodState o) => level == o.level && positive == o.positive;
        public override string ToString() => level > 0 ? "-" + level : positive > 0 ? "+" + positive : "0";
    }

    /// <summary>Was die Welt gerade ueber den Spieler sagt. Wird vom Spiel jeden Frame gesetzt.</summary>
    public struct EnvironmentInput
    {
        public float nightFactor;
        public bool indoors, lightIsland, nearFire, thicket;
    }

    public sealed class ActiveEffect
    {
        public string id;
        public float remainingHours;
        public List<Effect> effects;
    }

    /// <summary>Ein Posten in der Aufschluesselung einer Rate (fuer das Debug-Panel).</summary>
    public struct RateEntry
    {
        public string source;
        public int level;
        public EffectKind kind;
        public StatId stat;
        public float value;
    }

    public struct SleepResult
    {
        public bool slept;
        public string reason;
        public bool nightmare;
        public float hours;
    }

    [Serializable]
    public class SurvivalSaveData
    {
        public float[] values;
        public int[] moodLevel;
        public int[] moodPositive;
        public List<string> buffIds = new List<string>();
        public List<float> buffHours = new List<float>();
        public List<string> talkIds = new List<string>();
        public List<float> talkHours = new List<float>();
        public float totalHours;
        public bool dead;
    }

    /// <summary>
    /// Der Kern: alle Werte, Stimmungen und Regeln, ohne Unity-Objekte. Laeuft deshalb auch in Tests.
    ///
    /// Ablauf pro Tick: Flags aus Taetigkeit und Umwelt bilden, Regeln und Stimmungsstufen und Effekte einsammeln,
    /// Raten anwenden, Ausdauer-Zustand pruefen, Stimmungen neu bewerten. Die Stimmungen eines Ticks wirken im naechsten
    /// (eine Tick-Verzoegerung, dadurch keine Rueckkopplung innerhalb eines Ticks).
    ///
    /// Rate eines Werts = (Grundrate + Summe der StatRate-Effekte) * Multiplikator, wobei der Multiplikator
    /// StatDrainMult heisst, wenn die Rate den Wert verschlechtert, und StatRecoverMult, wenn sie ihn verbessert.
    /// </summary>
    public sealed class SurvivalSimulation
    {
        static readonly int StatCount = Enum.GetValues(typeof(StatId)).Length;
        static readonly int MoodCount = Enum.GetValues(typeof(MoodId)).Length;
        static readonly int KindCount = Enum.GetValues(typeof(EffectKind)).Length;
        static readonly int FlagCount = Enum.GetValues(typeof(ContextFlag)).Length;

        readonly SurvivalConfig cfg;
        readonly StatDef[] defs = new StatDef[StatCount];
        readonly MoodDef[] moodDefs = new MoodDef[MoodCount];
        readonly float[] values = new float[StatCount];
        readonly MoodState[] moods = new MoodState[MoodCount];

        // Pro Tick eingesammelt
        readonly float[] addRate = new float[StatCount];
        readonly float[] drainMult = new float[StatCount];
        readonly float[] recoverMult = new float[StatCount];
        readonly float[] gpMult = new float[KindCount];
        readonly float[] gpAdd = new float[KindCount];
        readonly bool[] gpBlock = new bool[KindCount];
        readonly bool[] flags = new bool[FlagCount];

        readonly List<ActiveEffect> buffs = new List<ActiveEffect>();
        readonly Dictionary<object, List<Effect>> modifiers = new Dictionary<object, List<Effect>>();
        readonly Dictionary<string, float> lastTalk = new Dictionary<string, float>();
        readonly List<RateEntry> breakdown = new List<RateEntry>();

        ActivityKind activity;
        EnvironmentInput env;
        float time;
        float totalHours;
        float lastStaminaUse = -99f;
        float invulnerableUntil;
        bool winded;
        bool dead;
        bool collapseLatch;

        /// <summary>Zufallsquelle 0..1 (fuer Tests austauschbar).</summary>
        public Func<float> Random = () => UnityEngine.Random.value;
        /// <summary>Aufschluesselung pro Tick mitschreiben (Debug-Panel). Kostet etwas Speicher.</summary>
        public bool CaptureBreakdown;
        /// <summary>Unverwundbar (Debug).</summary>
        public bool GodMode;

        public event Action Died;
        public event Action<float> Damaged;
        public event Action Collapsed;
        public event Action<MoodId, MoodState, MoodState> MoodChanged;

        public SurvivalSimulation(SurvivalConfig config)
        {
            cfg = config != null ? config : SurvivalDefaults.Create();
            foreach (var s in cfg.stats) defs[(int)s.id] = s;
            foreach (var m in cfg.moods) moodDefs[(int)m.id] = m;
            ResetValues();
        }

        public SurvivalConfig Config => cfg;
        public SurvivalTuning Tuning => cfg.tuning;
        public bool IsDead => dead;
        public bool IsWinded => winded;
        public float SimTime => time;
        public float TotalGameHours => totalHours;
        public ActivityKind Activity => activity;
        public EnvironmentInput Environment => env;
        public IReadOnlyList<ActiveEffect> Buffs => buffs;
        public IReadOnlyList<RateEntry> Breakdown => breakdown;
        public bool IsInvulnerable => time < invulnerableUntil;

        // ------------------------------------------------------------------ Werte lesen
        public StatDef Def(StatId id) => defs[(int)id];

        /// <summary>Aktueller Wert.</summary>
        public float Value(StatId id) => values[(int)id];

        /// <summary>Obergrenze: bei der Ausdauer das Maximum-Erschoepfung, sonst das max des Werts.</summary>
        public float Max(StatId id)
        {
            var d = defs[(int)id];
            if (d == null) return 0f;
            if (id == StatId.Stamina && defs[(int)StatId.StaminaCap] != null) return Mathf.Min(d.max, values[(int)StatId.StaminaCap]);
            return d.max;
        }

        /// <summary>Wert in Prozent seines Bereichs (0-100).</summary>
        public float Percent(StatId id)
        {
            var d = defs[(int)id];
            return d == null ? 0f : (values[(int)id] - d.min) / d.Range * 100f;
        }

        /// <summary>Wert 0-1 (Anteil des Bereichs).</summary>
        public float Normalized(StatId id) => Percent(id) / 100f;

        /// <summary>Schwere 0 (gut) bis 1 (schlecht), unabhaengig davon, ob der Wert steigend gut oder schlecht ist.</summary>
        public float Severity(StatId id)
        {
            var d = defs[(int)id];
            if (d == null) return 0f;
            float n = Mathf.Clamp01((values[(int)id] - d.min) / d.Range);
            return d.higherIsBetter ? 1f - n : n;
        }

        public MoodState Mood(MoodId id) => moods[(int)id];

        /// <summary>Gesamtfaktor eines Spielwerts (Produkt aller Multiplikatoren), z. B. MoveSpeedMult.</summary>
        public float Mult(EffectKind kind) => gpMult[(int)kind];
        public float Sum(EffectKind kind) => gpAdd[(int)kind];
        public bool Blocked(EffectKind kind) => gpBlock[(int)kind];
        public bool Has(ContextFlag flag) => flags[(int)flag];

        public bool CanSprint => !dead && !winded && !gpBlock[(int)EffectKind.BlockSprint] && values[(int)StatId.Stamina] > 0.5f;
        public bool CanAttack => !dead && !winded && !gpBlock[(int)EffectKind.BlockAttack];

        // ------------------------------------------------------------------ Eingaben der Welt
        public void SetActivity(ActivityKind a) => activity = a;

        public void SetEnvironment(EnvironmentInput e) => env = e;

        /// <summary>Alle Werte auf ihre Startwerte, Stimmungen neu bewerten.</summary>
        public void ResetValues()
        {
            for (int i = 0; i < StatCount; i++) if (defs[i] != null) values[i] = Mathf.Clamp(defs[i].start, defs[i].min, defs[i].max);
            Array.Clear(moods, 0, moods.Length);
            buffs.Clear();
            lastTalk.Clear();
            dead = false;
            winded = false;
            collapseLatch = false;
            time = 0f;
            totalHours = 0f;
            lastStaminaUse = -99f;
            invulnerableUntil = 0f;
            for (int i = 0; i < KindCount; i++) { gpMult[i] = 1f; gpAdd[i] = 0f; gpBlock[i] = false; }
            UpdateMoods(true);
        }

        // ------------------------------------------------------------------ Zeit
        /// <summary>
        /// Einen Schritt simulieren. dt = Echtzeit-Sekunden (fuer Raten pro Sekunde), gameHours = vergangene Spielstunden
        /// (fuer Raten pro Spielstunde, 0 bei pausierter Weltzeit).
        /// </summary>
        public void Tick(float dt, float gameHours)
        {
            if (dead || (dt <= 0f && gameHours <= 0f)) return;
            dt = Mathf.Max(0f, dt);
            gameHours = Mathf.Max(0f, gameHours);
            time += dt;
            totalHours += gameHours;

            UpdateFlags();
            TickBuffs(gameHours);
            CollectEffects();
            ApplyRates(dt, gameHours);
            UpdateStaminaState();
            UpdateMoods(false);
            CheckCollapse();
            CheckDeath();
        }

        /// <summary>Viele Spielstunden in Schritten simulieren (Schlaf, Warten, Tests).</summary>
        public void FastForward(float hours, float secondsPerHour, float stepHours = 0.25f)
        {
            stepHours = Mathf.Max(0.01f, stepHours);
            float left = hours;
            while (left > 0.0001f && !dead)
            {
                float h = Mathf.Min(stepHours, left);
                Tick(h * secondsPerHour, h);
                left -= h;
            }
        }

        void UpdateFlags()
        {
            Array.Clear(flags, 0, flags.Length);
            flags[(int)activity] = true; // die ersten acht ContextFlags entsprechen der ActivityKind
            flags[(int)ContextFlag.Moving] = activity == ActivityKind.Walking || activity == ActivityKind.Sneaking || activity == ActivityKind.Sprinting;
            bool night = env.nightFactor >= cfg.tuning.nightThreshold;
            flags[(int)ContextFlag.Night] = night;
            flags[(int)ContextFlag.Indoors] = env.indoors;
            flags[(int)ContextFlag.LightIsland] = env.lightIsland;
            flags[(int)ContextFlag.NearFire] = env.nearFire;
            flags[(int)ContextFlag.Thicket] = env.thicket;
            flags[(int)ContextFlag.Darkness] = night && !env.indoors && !env.lightIsland && !env.nearFire;
            if (activity == ActivityKind.Sprinting) lastStaminaUse = time;
            flags[(int)ContextFlag.StaminaRested] = time - lastStaminaUse >= cfg.tuning.staminaRegenDelay;
            flags[(int)ContextFlag.Winded] = winded;
        }

        void TickBuffs(float gameHours)
        {
            for (int i = buffs.Count - 1; i >= 0; i--)
            {
                buffs[i].remainingHours -= gameHours;
                if (buffs[i].remainingHours <= 0f) buffs.RemoveAt(i);
            }
        }

        // ------------------------------------------------------------------ Effekte einsammeln
        void CollectEffects()
        {
            for (int i = 0; i < StatCount; i++) { addRate[i] = 0f; drainMult[i] = 1f; recoverMult[i] = 1f; }
            for (int i = 0; i < KindCount; i++) { gpMult[i] = 1f; gpAdd[i] = 0f; gpBlock[i] = false; }
            breakdown.Clear();

            foreach (var r in cfg.rules)
            {
                if (!r.enabled || !Matches(r.when)) continue;
                Apply(r.effects, r.name, 0);
            }
            for (int i = 0; i < MoodCount; i++)
            {
                var def = moodDefs[i];
                if (def == null) continue;
                var s = moods[i];
                if (s.level > 0 && s.level <= def.stages.Count) Apply(def.stages[s.level - 1].effects, def.displayName, s.level);
                else if (s.positive > 0 && s.positive <= def.positiveStages.Count) Apply(def.positiveStages[s.positive - 1].effects, def.displayName, -s.positive);
            }
            foreach (var b in buffs) Apply(b.effects, b.id, 0);
            foreach (var kv in modifiers) Apply(kv.Value, CaptureBreakdown ? OwnerName(kv.Key) : null, 0);
        }

        static string OwnerName(object owner) => owner is UnityEngine.Object o ? (o != null ? o.name : "(zerstoert)") : owner.ToString();

        bool Matches(List<Condition> when)
        {
            for (int i = 0; i < when.Count; i++)
            {
                var c = when[i];
                bool ok;
                switch (c.kind)
                {
                    case ConditionKind.Flag: ok = flags[(int)c.flag]; break;
                    case ConditionKind.StatAbove: ok = defs[(int)c.stat] != null && Percent(c.stat) > c.value; break;
                    case ConditionKind.StatBelow: ok = defs[(int)c.stat] != null && Percent(c.stat) < c.value; break;
                    default: ok = moods[(int)c.mood].level >= Mathf.RoundToInt(c.value); break;
                }
                if (ok == c.negate) return false;
            }
            return true;
        }

        void Apply(List<Effect> list, string source, int level)
        {
            for (int i = 0; i < list.Count; i++)
            {
                var e = list[i];
                int k = (int)e.kind;
                switch (e.kind)
                {
                    case EffectKind.StatRate: addRate[(int)e.stat] += e.value; break;
                    case EffectKind.StatDrainMult: drainMult[(int)e.stat] *= e.value; break;
                    case EffectKind.StatRecoverMult: recoverMult[(int)e.stat] *= e.value; break;
                    default:
                        if (EffectKinds.IsMultiplier(e.kind)) gpMult[k] *= e.value;
                        else if (EffectKinds.IsAdditive(e.kind)) gpAdd[k] += e.value;
                        else if (e.value > 0f) gpBlock[k] = true;
                        break;
                }
                if (CaptureBreakdown) breakdown.Add(new RateEntry { source = source, level = level, kind = e.kind, stat = e.stat, value = e.value });
            }
        }

        // ------------------------------------------------------------------ Raten anwenden
        void ApplyRates(float dt, float gameHours)
        {
            for (int i = 0; i < StatCount; i++)
            {
                var d = defs[i];
                if (d == null) continue;
                float rate = d.baseRate + addRate[i];
                if (rate != 0f)
                {
                    bool good = d.higherIsBetter ? rate > 0f : rate < 0f;
                    rate *= good ? recoverMult[i] : drainMult[i];
                }
                float amount = d.unit == RateUnit.PerSecond ? dt : gameHours;
                values[i] = Mathf.Clamp(values[i] + rate * amount, d.min, d.max);
            }
            // Obergrenze der Ausdauer nachziehen (das Maximum kann gerade gesunken sein)
            ClampStamina();
        }

        void ClampStamina()
        {
            int s = (int)StatId.Stamina;
            if (defs[s] != null) values[s] = Mathf.Clamp(values[s], defs[s].min, Max(StatId.Stamina));
        }

        /// <summary>Momentane Rate eines Werts in seiner Einheit (nach dem letzten Tick), fuer Anzeigen und Debug.</summary>
        public float CurrentRate(StatId id)
        {
            var d = defs[(int)id];
            if (d == null) return 0f;
            float rate = d.baseRate + addRate[(int)id];
            if (rate == 0f) return 0f;
            bool good = d.higherIsBetter ? rate > 0f : rate < 0f;
            return rate * (good ? recoverMult[(int)id] : drainMult[(int)id]);
        }

        void UpdateStaminaState()
        {
            var d = defs[(int)StatId.Stamina];
            if (d == null) return;
            float v = values[(int)StatId.Stamina];
            // Knapp ueber null schon "ausser Atem", sonst flackert Sprint an/aus, wenn die Ausdauer an der Grenze haengt
            if (v <= 0.5f) winded = true;
            else if (winded && v >= cfg.tuning.windedRecoverFraction * Max(StatId.Stamina)) winded = false;
        }

        // ------------------------------------------------------------------ Stimmungen
        void UpdateMoods(bool silent)
        {
            for (int i = 0; i < MoodCount; i++)
            {
                var def = moodDefs[i];
                if (def == null) continue;
                float sev = 0f;
                foreach (var src in def.sources)
                {
                    float s = Severity(src.stat);
                    float m = src.to <= src.from ? (s >= src.from ? 1f : 0f) : Mathf.Clamp01((s - src.from) / (src.to - src.from));
                    if (m > sev) sev = m;
                }

                var old = moods[i];
                int lv = old.level;
                var thr = def.thresholds;
                while (lv < 4 && lv < thr.Length && sev >= thr[lv]) lv++;
                while (lv > 0 && sev < thr[lv - 1] - def.hysteresis) lv--;

                int pos = old.positive;
                var pt = def.positiveThresholds;
                if (lv == 0 && pt != null && pt.Length == 2 && def.sources.Count > 0)
                {
                    float good = 1f - Severity(def.sources[0].stat);
                    while (pos < 2 && good >= pt[pos]) pos++;
                    while (pos > 0 && good < pt[pos - 1] - def.hysteresis) pos--;
                }
                else pos = 0;

                var now = new MoodState { level = lv, positive = pos };
                if (now.Equals(old)) continue;
                moods[i] = now;
                if (!silent) MoodChanged?.Invoke(def.id, old, now);
            }
        }

        void CheckCollapse()
        {
            var d = defs[(int)StatId.Fatigue];
            if (d == null) return;
            float p = Percent(StatId.Fatigue);
            if (!collapseLatch && p >= cfg.tuning.collapseFatiguePercent - 0.01f)
            {
                collapseLatch = true;
                Collapsed?.Invoke();
            }
            else if (collapseLatch && p < cfg.tuning.collapseFatiguePercent - 10f) collapseLatch = false;
        }

        // ------------------------------------------------------------------ Direkte Aenderungen
        public void Set(StatId id, float value)
        {
            var d = defs[(int)id];
            if (d == null) return;
            values[(int)id] = Mathf.Clamp(value, d.min, d.max);
            if (id == StatId.Stamina || id == StatId.StaminaCap) ClampStamina();
            if (id == StatId.Stamina) UpdateStaminaState();
            if (id == StatId.Health) CheckDeath();
        }

        /// <summary>Sofortige Aenderung (kein Schaden: ignoriert Unverwundbarkeit und Schadensmultiplikator).</summary>
        public void Add(StatId id, float amount) => Set(id, values[(int)id] + amount);

        /// <summary>Ausdauer verbrauchen (Schlag, Ausweichen). false = nicht genug oder erschoepft, nichts passiert.</summary>
        public bool TryConsumeStamina(float baseCost)
        {
            if (dead || winded) return false;
            float cost = baseCost * gpMult[(int)EffectKind.StaminaCostMult];
            if (values[(int)StatId.Stamina] < cost) return false;
            values[(int)StatId.Stamina] -= cost;
            lastStaminaUse = time;
            UpdateStaminaState();
            return true;
        }

        public bool TryAttack() => CanAttack && TryConsumeStamina(cfg.tuning.attackStaminaCost);

        public bool TryDodge()
        {
            if (!TryConsumeStamina(cfg.tuning.dodgeStaminaCost)) return false;
            GrantInvulnerability(cfg.tuning.dodgeWindow * gpMult[(int)EffectKind.ReactionWindowMult]);
            return true;
        }

        public void GrantInvulnerability(float seconds) => invulnerableUntil = Mathf.Max(invulnerableUntil, time + seconds);

        /// <summary>Schaden in Lebenspunkten (Kampfregeln: 3). Gibt true zurueck, wenn der Treffer wirkte.</summary>
        public bool TakeLifePoints(int points) => TakeDamage(points * Max(StatId.Health) / Mathf.Max(1, cfg.tuning.lifePoints));

        /// <summary>Schaden in Lebens-Einheiten (0-100). Unverwundbarkeit, Multiplikator, Schmerz, Stress und Sanity-Verlust inklusive.</summary>
        public bool TakeDamage(float amount)
        {
            if (dead || amount <= 0f || GodMode || time < invulnerableUntil) return false;
            amount *= gpMult[(int)EffectKind.DamageTakenMult];
            invulnerableUntil = time + cfg.tuning.hitInvulnerability;
            float lifePoint = Max(StatId.Health) / Mathf.Max(1, cfg.tuning.lifePoints);
            float remaining = values[(int)StatId.Health] - amount;
            // Kleiner Rest unter dem Todesrand zaehlt als erledigt (durch Heilung/Regeneration bleibt sonst oft ein Krümel Leben)
            values[(int)StatId.Health] = remaining < lifePoint * cfg.tuning.deathMarginLifePoints ? 0f : remaining;
            if (defs[(int)StatId.Pain] != null) Add(StatId.Pain, amount * cfg.tuning.painPerDamage);
            if (defs[(int)StatId.Stress] != null) Add(StatId.Stress, amount * cfg.tuning.stressPerDamage);
            if (defs[(int)StatId.Sanity] != null) Add(StatId.Sanity, -amount * cfg.tuning.sanityPerDamage);
            Damaged?.Invoke(amount);
            CheckDeath();
            return true;
        }

        public void Heal(float amount) => Add(StatId.Health, amount);

        void CheckDeath()
        {
            // Kleiner Puffer: drei Treffer zu je einem Drittel ergeben wegen Rundung nie ganz null
            if (dead || defs[(int)StatId.Health] == null || values[(int)StatId.Health] > 0.05f) return;
            values[(int)StatId.Health] = 0f;
            dead = true;
            activity = ActivityKind.Idle;
            Died?.Invoke();
        }

        /// <summary>Wiederbeleben mit den Werten aus Tuning.afterDeath (geschwaecht, niedrige Sanity).</summary>
        public void Revive()
        {
            dead = false;
            winded = false;
            buffs.Clear();
            foreach (var a in cfg.tuning.afterDeath) Set(a.stat, a.amount);
            if (values[(int)StatId.Health] <= 0f) values[(int)StatId.Health] = 1f;
            invulnerableUntil = time + 3f;
            activity = ActivityKind.Idle;
            UpdateMoods(false);
        }

        // ------------------------------------------------------------------ Verbrauchsgueter und Effekte
        public bool Consume(string id)
        {
            var c = cfg.Consumable(id);
            if (c == null) return false;
            Consume(c);
            return true;
        }

        public void Consume(ConsumableDef c)
        {
            foreach (var a in c.instant) Add(a.stat, a.amount);
            foreach (var t in c.timed) AddTimedEffect(t);
            UpdateMoods(false);
        }

        public void AddTimedEffect(TimedEffectDef def)
        {
            foreach (var b in buffs)
            {
                if (b.id != def.id) continue;
                b.remainingHours = def.refresh ? Mathf.Max(b.remainingHours, def.durationHours) : b.remainingHours + def.durationHours;
                return;
            }
            buffs.Add(new ActiveEffect { id = def.id, remainingHours = def.durationHours, effects = def.effects });
        }

        public void RemoveTimedEffect(string id) => buffs.RemoveAll(b => b.id == id);

        /// <summary>Dauerhafter Effekt von aussen (z. B. eine Zone). Mit RemoveModifiers(owner) wieder entfernen.</summary>
        public void SetModifiers(object owner, List<Effect> effects)
        {
            if (effects == null || effects.Count == 0) modifiers.Remove(owner);
            else modifiers[owner] = effects;
        }

        public void RemoveModifiers(object owner) => modifiers.Remove(owner);

        // ------------------------------------------------------------------ Soziales
        /// <summary>
        /// Gespraech mit einer Person: weniger Einsamkeit, bessere Laune und Sanity, weniger Stress.
        /// Dieselbe Person gibt innerhalb der Abklingzeit nur einen Bruchteil, damit man das nicht ausnutzt.
        /// </summary>
        public void RegisterConversation(string npcId, float quality = 1f)
        {
            var t = cfg.tuning;
            float factor = quality;
            if (!string.IsNullOrEmpty(npcId))
            {
                if (lastTalk.TryGetValue(npcId, out float last) && totalHours - last < t.conversationCooldownHours) factor *= t.conversationRepeatFactor;
                lastTalk[npcId] = totalHours;
            }
            Add(StatId.Loneliness, t.conversationLoneliness * factor);
            Add(StatId.Happiness, t.conversationHappiness * factor);
            Add(StatId.Sanity, t.conversationSanity * factor);
            Add(StatId.Stress, t.conversationStress * factor);
            UpdateMoods(false);
        }

        // ------------------------------------------------------------------ Schlaf
        public bool CanSleep(out string reason)
        {
            reason = null;
            if (dead) { reason = "Not now."; return false; }
            if (gpBlock[(int)EffectKind.BlockSleep]) { reason = "I can't sleep like this."; return false; }
            if (defs[(int)StatId.Sanity] != null && Normalized(StatId.Sanity) < cfg.tuning.sleepSanityBlock)
            {
                reason = "Too restless to sleep.";
                return false;
            }
            return true;
        }

        /// <summary>Schlafen: die Zeit vergeht in Schritten mit Taetigkeit "Sleeping". Bei niedriger Sanity drohen Albtraeume.</summary>
        public SleepResult Sleep(float hours, float secondsPerHour)
        {
            var r = new SleepResult();
            if (!CanSleep(out r.reason)) return r;
            // Albtraum-Risiko haengt vom Zustand VOR dem Schlaf ab (der Schlaf selbst hebt die Sanity)
            float sanityBefore = Normalized(StatId.Sanity);
            var before = activity;
            activity = ActivityKind.Sleeping;
            FastForward(hours, secondsPerHour, cfg.tuning.sleepStepHours);
            activity = before == ActivityKind.Sleeping ? ActivityKind.Idle : before;
            r.slept = !dead;
            r.hours = hours;

            float sanity = sanityBefore;
            if (sanity < cfg.tuning.nightmareSanityBelow && cfg.tuning.nightmareSanityBelow > 0f)
            {
                float chance = cfg.tuning.nightmareMaxChance * (1f - sanity / cfg.tuning.nightmareSanityBelow);
                if (Random() < chance)
                {
                    r.nightmare = true;
                    Add(StatId.Sanity, -cfg.tuning.nightmareSanityLoss);
                    Add(StatId.Stress, 8f);
                }
            }
            UpdateMoods(false);
            return r;
        }

        // ------------------------------------------------------------------ Speichern
        public SurvivalSaveData Save()
        {
            var s = new SurvivalSaveData
            {
                values = (float[])values.Clone(),
                moodLevel = new int[MoodCount],
                moodPositive = new int[MoodCount],
                totalHours = totalHours,
                dead = dead,
            };
            for (int i = 0; i < MoodCount; i++) { s.moodLevel[i] = moods[i].level; s.moodPositive[i] = moods[i].positive; }
            foreach (var b in buffs) { s.buffIds.Add(b.id); s.buffHours.Add(b.remainingHours); }
            foreach (var kv in lastTalk) { s.talkIds.Add(kv.Key); s.talkHours.Add(kv.Value); }
            return s;
        }

        public void Load(SurvivalSaveData s)
        {
            if (s == null || s.values == null) return;
            for (int i = 0; i < StatCount && i < s.values.Length; i++) if (defs[i] != null) values[i] = Mathf.Clamp(s.values[i], defs[i].min, defs[i].max);
            for (int i = 0; i < MoodCount; i++)
            {
                moods[i] = new MoodState { level = s.moodLevel != null && i < s.moodLevel.Length ? s.moodLevel[i] : 0, positive = s.moodPositive != null && i < s.moodPositive.Length ? s.moodPositive[i] : 0 };
            }
            totalHours = s.totalHours;
            dead = s.dead;
            buffs.Clear();
            for (int i = 0; i < s.buffIds.Count; i++)
            {
                var def = FindTimed(s.buffIds[i]);
                if (def != null) buffs.Add(new ActiveEffect { id = def.id, remainingHours = s.buffHours[i], effects = def.effects });
            }
            lastTalk.Clear();
            for (int i = 0; i < s.talkIds.Count; i++) lastTalk[s.talkIds[i]] = s.talkHours[i];
            ClampStamina();
            UpdateStaminaState();
            UpdateMoods(true);
        }

        TimedEffectDef FindTimed(string id)
        {
            foreach (var c in cfg.consumables) foreach (var t in c.timed) if (t.id == id) return t;
            return null;
        }
    }
}
