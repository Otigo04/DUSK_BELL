using NUnit.Framework;
using UnityEngine;

namespace Nightward.Survival.Tests
{
    public class SurvivalSimulationTests
    {
        const float SecPerHour = 25f;

        SurvivalSimulation sim;

        [SetUp]
        public void SetUp()
        {
            sim = new SurvivalSimulation(SurvivalDefaults.Create());
            sim.Random = () => 0.5f;
        }

        void Run(float hours, ActivityKind activity = ActivityKind.Idle, EnvironmentInput env = default)
        {
            sim.SetActivity(activity);
            sim.SetEnvironment(env);
            sim.FastForward(hours, SecPerHour);
        }

        static EnvironmentInput Night(bool indoors = false, bool light = false, bool fire = false) =>
            new EnvironmentInput { nightFactor = 1f, indoors = indoors, lightIsland = light, nearFire = fire };

        // ------------------------------------------------------------------ Aufbau
        [Test]
        public void Defaults_CoverAllStatsAndMoods()
        {
            var cfg = SurvivalDefaults.Create();
            foreach (StatId id in System.Enum.GetValues(typeof(StatId))) Assert.NotNull(cfg.Stat(id), "StatDef fehlt: " + id);
            foreach (MoodId id in System.Enum.GetValues(typeof(MoodId)))
            {
                var m = cfg.Mood(id);
                Assert.NotNull(m, "MoodDef fehlt: " + id);
                Assert.AreEqual(4, m.thresholds.Length, id.ToString());
                Assert.AreEqual(4, m.stages.Count, id.ToString());
                for (int i = 1; i < 4; i++) Assert.Greater(m.thresholds[i], m.thresholds[i - 1], id + " Schwellen nicht aufsteigend");
                if (m.positiveThresholds.Length > 0) Assert.AreEqual(2, m.positiveStages.Count, id.ToString());
                Assert.IsFalse(string.IsNullOrEmpty(m.hudTile), id + " ohne HUD-Kachel");
            }
        }

        [Test]
        public void Start_NoMoodActive_ExceptNone()
        {
            foreach (MoodId id in System.Enum.GetValues(typeof(MoodId)))
                Assert.IsFalse(sim.Mood(id).level > 0, "Beim Start darf keine negative Stimmung aktiv sein: " + id);
        }

        // ------------------------------------------------------------------ Bedarf
        [Test]
        public void Hunger_RisesWithTime_AndTriggersMood()
        {
            float start = sim.Value(StatId.Hunger);
            Run(12f);
            Assert.Greater(sim.Value(StatId.Hunger), start + 25f);
            Assert.GreaterOrEqual(sim.Mood(MoodId.Hungry).level, 1);
            Run(20f);
            Assert.GreaterOrEqual(sim.Mood(MoodId.Hungry).level, 3);
        }

        [Test]
        public void Sprinting_MakesThirstyMuchFaster_ThanWalking()
        {
            var a = new SurvivalSimulation(SurvivalDefaults.Create());
            var b = new SurvivalSimulation(SurvivalDefaults.Create());
            a.Set(StatId.Hunger, 0); b.Set(StatId.Hunger, 0);
            a.Set(StatId.Thirst, 0); b.Set(StatId.Thirst, 0);
            for (int i = 0; i < 400; i++)
            {
                a.SetActivity(ActivityKind.Walking); a.Tick(0.1f, 0.02f);
                b.SetActivity(ActivityKind.Sprinting); b.Set(StatId.Stamina, 100f); b.Tick(0.1f, 0.02f);
            }
            Assert.Greater(b.Value(StatId.Thirst), a.Value(StatId.Thirst) * 1.8f, "Sprint soll deutlich mehr Durst machen");
            Assert.Greater(b.Value(StatId.Hunger), a.Value(StatId.Hunger) * 1.4f);
        }

        [Test]
        public void Intoxication_DecaysOverTime()
        {
            sim.Consume("schnaps");
            sim.Consume("schnaps");
            Assert.GreaterOrEqual(sim.Mood(MoodId.Drunk).level, 2);
            Run(8f);
            Assert.AreEqual(0, sim.Mood(MoodId.Drunk).level, "Rausch klingt nach einer Nacht ab");
        }

        // ------------------------------------------------------------------ Ausdauer
        [Test]
        public void Sprint_DrainsStamina_ThenWinded_ThenRecovers()
        {
            sim.SetActivity(ActivityKind.Sprinting);
            int guard = 0;
            while (sim.Value(StatId.Stamina) > 0.01f && guard++ < 1000) sim.Tick(0.05f, 0f);
            Assert.IsTrue(sim.IsWinded, "Leere Ausdauer macht ausser Atem");
            Assert.IsFalse(sim.CanSprint);

            sim.SetActivity(ActivityKind.Idle);
            for (int i = 0; i < 20; i++) sim.Tick(0.05f, 0f);   // 1 s: noch in der Regenerationsverzoegerung bzw. kaum erholt
            Assert.IsFalse(sim.CanSprint);
            for (int i = 0; i < 200; i++) sim.Tick(0.05f, 0f);  // 10 s Ruhe
            Assert.IsTrue(sim.CanSprint, "Nach Erholung wieder sprinten");
            Assert.Greater(sim.Value(StatId.Stamina), 50f);
        }

        [Test]
        public void Stamina_DoesNotRegenerateWhileSprinting_OrDuringDelay()
        {
            sim.Set(StatId.Stamina, 50f);
            Assert.IsTrue(sim.TryConsumeStamina(8f));
            float after = sim.Value(StatId.Stamina);
            sim.SetActivity(ActivityKind.Idle);
            sim.Tick(0.3f, 0f);
            Assert.AreEqual(after, sim.Value(StatId.Stamina), 0.01f, "Keine Regeneration in der Verzoegerung");
            sim.Tick(1.0f, 0f);
            Assert.Greater(sim.Value(StatId.Stamina), after);
        }

        [Test]
        public void Attack_CostsStamina_AndIsRefusedWhenEmpty()
        {
            sim.Set(StatId.Stamina, 10f);
            Assert.IsTrue(sim.TryAttack());
            Assert.IsFalse(sim.TryAttack(), "Nicht genug Ausdauer fuer den zweiten Schlag");
            Assert.Less(sim.Value(StatId.Stamina), 5f);
        }

        [Test]
        public void SprintThroughThicket_LowersCap_RestRestores()
        {
            sim.SetActivity(ActivityKind.Sprinting);
            sim.SetEnvironment(new EnvironmentInput { thicket = true });
            for (int i = 0; i < 400; i++) { sim.Set(StatId.Stamina, 100f); sim.Tick(0.1f, 0f); }
            float cap = sim.Value(StatId.StaminaCap);
            Assert.Less(cap, 80f, "Dickicht-Sprint senkt das Maximum");
            Assert.LessOrEqual(sim.Value(StatId.Stamina), cap + 0.01f, "Ausdauer darf das Maximum nicht uebersteigen");

            // Gehen und Stehen holen das Maximum NICHT zurueck
            Run(2f, ActivityKind.Idle);
            Assert.AreEqual(cap, sim.Value(StatId.StaminaCap), 0.5f);

            // Rast erholt es
            sim.SetActivity(ActivityKind.Resting);
            for (int i = 0; i < 400; i++) sim.Tick(0.1f, 0.001f);
            Assert.Greater(sim.Value(StatId.StaminaCap), cap + 20f);
        }

        // ------------------------------------------------------------------ Leben und Kampf
        [Test]
        public void ThreeLifePoints_DieAfterThreeHits_WithInvulnerabilityBetween()
        {
            Assert.IsTrue(sim.TakeLifePoints(1));
            Assert.IsFalse(sim.TakeLifePoints(1), "Unverwundbar direkt nach einem Treffer");
            Assert.IsTrue(sim.IsInvulnerable);
            sim.Tick(2.1f, 0f);
            Assert.IsTrue(sim.TakeLifePoints(1));
            sim.Tick(2.1f, 0f);
            bool died = false;
            sim.Died += () => died = true;
            Assert.IsTrue(sim.TakeLifePoints(1));
            Assert.IsTrue(died);
            Assert.IsTrue(sim.IsDead);
        }

        [Test]
        public void ThreeHits_StillKill_WhenHealthRegeneratedABit()
        {
            // Etwas Regeneration darf den Spieler nicht mit einem Kruemel Leben ueberleben lassen
            sim.Set(StatId.Health, 100.4f);
            for (int i = 0; i < 2; i++) { sim.TakeLifePoints(1); sim.Tick(2.1f, 0f); }
            sim.Set(StatId.Health, sim.Value(StatId.Health) + 0.4f);
            Assert.IsTrue(sim.TakeLifePoints(1));
            Assert.IsTrue(sim.IsDead);
        }

        [Test]
        public void Sprint_Stutter_DoesNotFlicker_AtEmptyStamina()
        {
            sim.Set(StatId.Stamina, 0.3f);
            sim.SetActivity(ActivityKind.Walking);
            sim.Tick(0.1f, 0f);
            Assert.IsFalse(sim.CanSprint, "Knapp ueber null = ausser Atem, kein Sprint-Flackern");
            for (int i = 0; i < 30; i++) sim.Tick(0.05f, 0f);
            Assert.IsFalse(sim.CanSprint, "Erst ab 25 % wieder sprinten");
        }

        [Test]
        public void Damage_CausesPain_AndWoundedMood()
        {
            sim.TakeLifePoints(1);
            sim.Tick(0.1f, 0f);
            Assert.Greater(sim.Value(StatId.Pain), 10f);
            Assert.GreaterOrEqual(sim.Mood(MoodId.Wounded).level, 1);
            sim.Tick(2.1f, 0f);
            sim.TakeLifePoints(1);
            sim.Tick(0.1f, 0f);
            Assert.GreaterOrEqual(sim.Mood(MoodId.Wounded).level, 3, "Zwei von drei Lebenspunkten verloren = schwer verletzt");
        }

        [Test]
        public void Dodge_GivesShortInvulnerability_AndCostsStamina()
        {
            float before = sim.Value(StatId.Stamina);
            Assert.IsTrue(sim.TryDodge());
            Assert.Less(sim.Value(StatId.Stamina), before - 20f);
            Assert.IsFalse(sim.TakeLifePoints(1), "Waehrend des Ausweichens kein Schaden");
            sim.Tick(0.4f, 0f);
            Assert.IsTrue(sim.TakeLifePoints(1));
        }

        [Test]
        public void Revive_AppliesWeakenedState()
        {
            sim.GodMode = false;
            for (int i = 0; i < 3; i++) { sim.TakeLifePoints(1); sim.Tick(2.1f, 0f); }
            Assert.IsTrue(sim.IsDead);
            sim.Revive();
            Assert.IsFalse(sim.IsDead);
            Assert.AreEqual(30f, sim.Value(StatId.Health), 0.01f);
            Assert.AreEqual(25f, sim.Value(StatId.Sanity), 0.01f);
        }

        [Test]
        public void Starving_DrainsHealth_UntilDeath()
        {
            sim.Set(StatId.Hunger, 100f);
            sim.Set(StatId.Thirst, 100f);
            float h0 = sim.Value(StatId.Health);
            Run(4f);
            Assert.Less(sim.Value(StatId.Health), h0 - 10f, "Verhungern und Verdursten kostet Leben");
            Run(40f);
            Assert.IsTrue(sim.IsDead);
        }

        [Test]
        public void WellFed_RegeneratesHealth()
        {
            sim.Set(StatId.Health, 50f);
            Run(6f);
            Assert.Greater(sim.Value(StatId.Health), 54f);
        }

        // ------------------------------------------------------------------ Sanity und Umwelt
        [Test]
        public void DarknessOutdoors_DrainsSanity_LightAndFireRestoreIt()
        {
            Run(4f, ActivityKind.Idle, Night());
            float dark = sim.Value(StatId.Sanity);
            Assert.Less(dark, 90f);

            sim.Set(StatId.Sanity, 50f);
            Run(3f, ActivityKind.Idle, Night(light: true));
            Assert.Greater(sim.Value(StatId.Sanity), 50f, "Lichtinsel erholt");

            sim.Set(StatId.Sanity, 50f);
            Run(3f, ActivityKind.Idle, Night(fire: true));
            Assert.Greater(sim.Value(StatId.Sanity), 55f, "Kamin erholt mehr");

            sim.Set(StatId.Sanity, 50f);
            Run(3f, ActivityKind.Idle, Night(indoors: true));
            Assert.GreaterOrEqual(sim.Value(StatId.Sanity), 49.9f, "Drinnen kein Dunkelheits-Verlust");
        }

        [Test]
        public void LowSanity_BecomesShaken_BlocksSleep_AtFortyPercent()
        {
            sim.Set(StatId.Sanity, 41f);
            Assert.IsTrue(sim.CanSleep(out _));
            sim.Set(StatId.Sanity, 39f);
            Assert.IsFalse(sim.CanSleep(out var reason));
            StringAssert.Contains("restless", reason);
            sim.Tick(0.1f, 0f);
            Assert.GreaterOrEqual(sim.Mood(MoodId.Shaken).level, 2);
        }

        [Test]
        public void Night_OutdoorsWithoutFire_GetsCold_FireWarms()
        {
            Run(8f, ActivityKind.Idle, Night());
            Assert.Greater(sim.Value(StatId.Cold), 40f);
            Assert.GreaterOrEqual(sim.Mood(MoodId.Cold).level, 1);
            Run(4f, ActivityKind.Idle, Night(fire: true));
            Assert.Less(sim.Value(StatId.Cold), 5f);
        }

        // ------------------------------------------------------------------ Stimmungen
        [Test]
        public void Mood_HasHysteresis_NoFlicker()
        {
            // Hunger-Stufe 1 beginnt bei Schwere 0.30
            sim.Set(StatId.Hunger, 31f);
            sim.Tick(0.01f, 0f);
            Assert.AreEqual(1, sim.Mood(MoodId.Hungry).level);
            sim.Set(StatId.Hunger, 29f);
            sim.Tick(0.01f, 0f);
            Assert.AreEqual(1, sim.Mood(MoodId.Hungry).level, "Knapp unter der Schwelle bleibt die Stufe (Hysterese)");
            sim.Set(StatId.Hunger, 20f);
            sim.Tick(0.01f, 0f);
            Assert.AreEqual(0, sim.Mood(MoodId.Hungry).level);
        }

        [Test]
        public void Mood_ChangedEvent_Fires()
        {
            MoodId seen = MoodId.Cold; MoodState now = default; int count = 0;
            sim.MoodChanged += (id, from, to) => { seen = id; now = to; count++; };
            sim.Set(StatId.Thirst, 70f);
            sim.Tick(0.01f, 0f);
            Assert.AreEqual(MoodId.Thirsty, seen);
            Assert.AreEqual(2, now.level);
            Assert.AreEqual(1, count);
        }

        [Test]
        public void PositiveMood_AfterCalmingTea()
        {
            sim.Consume("tea_calming");
            sim.Consume("tea_calming");
            sim.Tick(0.01f, 0f);
            var m = sim.Mood(MoodId.Tense);
            Assert.IsTrue(m.IsPositive, "Beruhigungstee macht ruhig (gruene Kachel)");
        }

        [Test]
        public void MoodEffects_SlowDownStamina_AndMovement()
        {
            Assert.AreEqual(1f, sim.Mult(EffectKind.MoveSpeedMult), 0.001f);
            sim.Set(StatId.Hunger, 100f);
            sim.Set(StatId.Thirst, 100f);
            sim.Tick(0.01f, 0f);
            sim.Tick(0.01f, 0f);
            Assert.Less(sim.Mult(EffectKind.MoveSpeedMult), 0.95f, "Verhungern verlangsamt");
        }

        [Test]
        public void Drunk_AddsSway_AndSlowsReaction()
        {
            for (int i = 0; i < 4; i++) sim.Consume("whisky");
            sim.Tick(0.01f, 0f);
            sim.Tick(0.01f, 0f);
            Assert.Greater(sim.Sum(EffectKind.ControlSway), 0.5f);
            Assert.Less(sim.Mult(EffectKind.ReactionWindowMult), 0.8f);
        }

        // ------------------------------------------------------------------ Verbrauchsgueter, Effekte
        [Test]
        public void Consume_Bread_LowersHunger()
        {
            sim.Set(StatId.Hunger, 60f);
            Assert.IsTrue(sim.Consume("bread"));
            Assert.AreEqual(28f, sim.Value(StatId.Hunger), 0.01f);
            Assert.IsFalse(sim.Consume("does_not_exist"));
        }

        [Test]
        public void SpringWater_RestoresStaminaCap()
        {
            sim.Set(StatId.StaminaCap, 50f);
            sim.Consume("spring_water");
            Assert.AreEqual(65f, sim.Value(StatId.StaminaCap), 0.01f);
        }

        [Test]
        public void TimedEffect_LastsDuration_ThenExpires()
        {
            sim.Set(StatId.Stress, 60f);
            sim.Consume("tobacco");
            Assert.AreEqual(1, sim.Buffs.Count);
            float afterHalf = 0f;
            Run(0.75f);
            afterHalf = sim.Value(StatId.Stress);
            Assert.AreEqual(1, sim.Buffs.Count);
            Run(1f);
            Assert.AreEqual(0, sim.Buffs.Count, "Effekt ist nach 1,5 h abgelaufen");
            Assert.Less(afterHalf, 46f);
        }

        [Test]
        public void TimedEffect_SameId_RefreshesInsteadOfStacking()
        {
            sim.Consume("tobacco");
            Run(1f);
            sim.Consume("tobacco");
            Assert.AreEqual(1, sim.Buffs.Count);
            Assert.AreEqual(1.5f, sim.Buffs[0].remainingHours, 0.01f);
        }

        [Test]
        public void ExternalModifier_AppliesAndRemoves()
        {
            var owner = new object();
            sim.Set(StatId.Sanity, 50f);
            sim.SetModifiers(owner, new System.Collections.Generic.List<Effect> { Effect.Rate(StatId.Sanity, -10f) });
            Run(2f);
            Assert.Less(sim.Value(StatId.Sanity), 35f);
            sim.RemoveModifiers(owner);
            float v = sim.Value(StatId.Sanity);
            Run(2f);
            Assert.GreaterOrEqual(sim.Value(StatId.Sanity), v - 0.5f);
        }

        // ------------------------------------------------------------------ Schlaf
        [Test]
        public void Sleep_RestoresFatigue_AndPassesTime()
        {
            sim.Set(StatId.Fatigue, 90f);
            sim.Set(StatId.Health, 60f);
            var r = sim.Sleep(8f, SecPerHour);
            Assert.IsTrue(r.slept);
            Assert.Less(sim.Value(StatId.Fatigue), 15f);
            Assert.Greater(sim.Value(StatId.Health), 80f);
            Assert.AreNotEqual(ActivityKind.Sleeping, sim.Activity);
        }

        [Test]
        public void Sleep_RefusedUnderSanityBlock()
        {
            sim.Set(StatId.Sanity, 20f);
            var r = sim.Sleep(8f, SecPerHour);
            Assert.IsFalse(r.slept);
            Assert.IsNotNull(r.reason);
        }

        [Test]
        public void Sleep_NightmareWithLowSanity_CostsSanity()
        {
            sim.Set(StatId.Sanity, 42f);
            sim.Random = () => 0f; // immer Albtraum
            var r = sim.Sleep(8f, SecPerHour);
            Assert.IsTrue(r.nightmare);
        }

        [Test]
        public void Sleep_NoNightmareWithHighSanity()
        {
            sim.Random = () => 0f;
            var r = sim.Sleep(8f, SecPerHour);
            Assert.IsFalse(r.nightmare);
        }

        [Test]
        public void Fatigue_AtMax_RaisesCollapseOnce()
        {
            int n = 0;
            sim.Collapsed += () => n++;
            sim.Set(StatId.Fatigue, 99.9f);
            Run(1f);
            Assert.AreEqual(1, n);
            Run(1f);
            Assert.AreEqual(1, n, "Nur einmal, bis die Muedigkeit wieder sinkt");
        }

        // ------------------------------------------------------------------ Soziales
        [Test]
        public void Conversation_ReducesLoneliness_RepeatIsWeaker()
        {
            sim.Set(StatId.Loneliness, 80f);
            sim.RegisterConversation("ilhan");
            float first = 80f - sim.Value(StatId.Loneliness);
            float mid = sim.Value(StatId.Loneliness);
            sim.RegisterConversation("ilhan");
            float second = mid - sim.Value(StatId.Loneliness);
            Assert.Greater(first, 20f);
            Assert.Less(second, first * 0.3f);
            sim.RegisterConversation("bulut");
            Assert.Greater(mid - second - sim.Value(StatId.Loneliness), 15f, "Anderer Gespraechspartner gibt wieder volle Wirkung");
        }

        // ------------------------------------------------------------------ Speichern, Steuerung
        [Test]
        public void SaveLoad_RoundTrip()
        {
            sim.Set(StatId.Hunger, 77f);
            sim.Set(StatId.StaminaCap, 55f);
            sim.Consume("tea_calming");
            Run(0.5f);
            string json = JsonUtility.ToJson(sim.Save());

            var other = new SurvivalSimulation(SurvivalDefaults.Create());
            other.Load(JsonUtility.FromJson<SurvivalSaveData>(json));
            Assert.AreEqual(sim.Value(StatId.Hunger), other.Value(StatId.Hunger), 0.001f);
            Assert.AreEqual(55f, other.Value(StatId.StaminaCap), 0.001f);
            Assert.AreEqual(sim.Buffs.Count, other.Buffs.Count);
            Assert.AreEqual(sim.Mood(MoodId.Hungry).level, other.Mood(MoodId.Hungry).level);
        }

        [Test]
        public void ConfigChange_TakesEffect_WithoutCodeChange()
        {
            var cfg = SurvivalDefaults.Create();
            cfg.Stat(StatId.Hunger).baseRate = 30f; // zehnmal schneller
            var fast = new SurvivalSimulation(cfg);
            fast.Set(StatId.Hunger, 0f);
            fast.SetActivity(ActivityKind.Idle);
            fast.FastForward(2f, SecPerHour);
            Assert.Greater(fast.Value(StatId.Hunger), 55f);

            var cfg2 = SurvivalDefaults.Create();
            cfg2.Rule("Dunkelheit: Sanity sinkt").enabled = false;
            var s2 = new SurvivalSimulation(cfg2);
            s2.SetEnvironment(Night());
            s2.FastForward(4f, SecPerHour);
            Assert.Greater(s2.Value(StatId.Sanity), 99f, "Regel abgeschaltet = kein Dunkelheits-Verlust");
        }

        [Test]
        public void PausedWorldTime_StopsNeeds_ButNotStamina()
        {
            sim.Set(StatId.Stamina, 40f);
            float hunger = sim.Value(StatId.Hunger);
            sim.SetActivity(ActivityKind.Idle);
            for (int i = 0; i < 100; i++) sim.Tick(0.1f, 0f);
            Assert.AreEqual(hunger, sim.Value(StatId.Hunger), 0.0001f);
            Assert.Greater(sim.Value(StatId.Stamina), 40f);
        }
    }
}
