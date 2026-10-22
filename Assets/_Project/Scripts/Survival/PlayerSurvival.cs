using System;
using System.Collections;
using System.Collections.Generic;
using Nightward.Combat;
using Nightward.DayNight;
using Nightward.Dialogue;
using Nightward.Interaction;
using Nightward.Player;
using Nightward.Vision;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering.Universal;

namespace Nightward.Survival
{
    /// <summary>
    /// Verbindet den Spieler mit dem Ueberlebens-System: liest Sprint/Schleichen/Ausweichen, meldet die Taetigkeit,
    /// liefert Zeit (Tag-Nacht-Zyklus) und Umwelt (Licht, Innenraum, Zonen) und setzt die Zustaende in Bewegung um
    /// (Tempo, Taumeln). Nimmt Schaden an (IDamageable), regelt Tod, Zusammenbruch, Schlaf, Rast und Gespraeche.
    ///
    /// Tasten: Linke Umschalt = Sprint, Linke Strg = Schleichen, Leertaste = Ausweichen (siehe Felder).
    /// </summary>
    [RequireComponent(typeof(PlayerController))]
    [RequireComponent(typeof(SurvivalSystem))]
    [DefaultExecutionOrder(-100)]
    public class PlayerSurvival : MonoBehaviour, IDamageable
    {
        public static PlayerSurvival Instance { get; private set; }

        [Header("Tasten")]
        [SerializeField] Key sprintKey = Key.LeftShift;
        [SerializeField] Key sneakKey = Key.LeftCtrl;
        [SerializeField] Key dodgeKey = Key.Space;

        [Header("Ausweichen")]
        [Tooltip("Tempo des Ausweich-Stosses (Units/s). Mit der Bremsung des Spielers ergibt das etwa 1 Kachel Weg")]
        [SerializeField] float dodgeSpeed = 7f;
        [SerializeField] float dodgeCooldown = 0.5f;
        [Tooltip("Dauer der Rollen-Animation (6 Bilder, 14 fps = 0,43 s)")]
        [SerializeField] float dodgeAnimTime = 0.43f;

        [Header("Kampf")]
        [Tooltip("So lange nach einem Schlag zaehlt die Taetigkeit als Kampf")]
        [SerializeField] float fightHold = 1.6f;
        [SerializeField] float knockbackSpeed = 5f;

        [Header("Tod und Zusammenbruch")]
        [Tooltip("Hier erwacht der Spieler nach dem Tod. Leer = Startposition")]
        [SerializeField] Transform respawnPoint;
        [SerializeField] float deathDelay = 2.5f;
        [Tooltip("Nach dem Tod springt die Uhr zum naechsten Morgen (Regelwerk: Spieler erwacht am Morgen im Bett)")]
        [SerializeField] bool deathSkipsToMorning = true;
        [SerializeField] float collapseDuration = 3f;
        [Tooltip("Muedigkeit (Prozent) nach dem Zusammenbruch")]
        [SerializeField] float fatigueAfterCollapse = 80f;

        [Header("Licht (Lichtinseln)")]
        [Tooltip("Anteil des Licht-Radius, in dem man als 'im Licht' gilt")]
        [SerializeField, Range(0.2f, 1f)] float lightReach = 0.85f;
        [Tooltip("Lampen unter dieser Helligkeit zaehlen nicht")]
        [SerializeField] float minLightIntensity = 0.25f;
        [SerializeField] float lightScanInterval = 1.5f;

        PlayerController controller;
        PlayerInteractor interactor;
        SurvivalSystem system;
        PlayerVision vision;
        Rigidbody2D body;
        Vector3 homePosition;

        readonly Dictionary<SurvivalZone, int> zones = new Dictionary<SurvivalZone, int>();
        Light2D[] lights = new Light2D[0];
        float nextLightScan;
        float fightUntil;
        float nextDodge;
        bool hasForced;
        ActivityKind forcedActivity;
        bool routineRunning;
        bool subscribedDialogue;

        public SurvivalSimulation Sim => system.Sim;
        public SurvivalSystem Host => system;
        public bool Busy => routineRunning;

        /// <summary>Faktor auf den Schaden, den der Spieler austeilt (Hunger, Rausch, Verletzung ...).</summary>
        public float DamageDealtMultiplier => Sim.Mult(EffectKind.DamageDealtMult);

        /// <summary>Kurze Mitteilung fuer den Spieler (englisch, wie der Rest der Texte), z. B. "Too restless to sleep."</summary>
        /// <summary>Der Spieler traegt eine brennende Lichtquelle (Laterne, Kerze, Fackel): zaehlt als Lichtinsel.</summary>
        public bool CarriesLight { get; set; }

        public event Action<string> Message;
        public event Action Dodged;

        void Awake()
        {
            Instance = this;
            controller = GetComponent<PlayerController>();
            interactor = GetComponent<PlayerInteractor>();
            system = GetComponent<SurvivalSystem>();
            body = GetComponent<Rigidbody2D>();
            homePosition = transform.position;
            system.GameHoursSource = GameHours;
            system.EnvironmentSource = SampleEnvironment;
            system.SecondsPerHourSource = SecondsPerHour;
        }

        void Start()
        {
            vision = FindAnyObjectByType<PlayerVision>();
            Sim.Died += OnDied;
            Sim.Collapsed += OnCollapsed;
            ScanLights();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
            if (system != null && system.Sim != null)
            {
                system.Sim.Died -= OnDied;
                system.Sim.Collapsed -= OnCollapsed;
            }
            if (DialogueRunner.Instance != null && subscribedDialogue) DialogueRunner.Instance.Ended -= OnDialogueEnded;
        }

        // ------------------------------------------------------------------ Zeit und Umwelt
        static float CycleSeconds(DayNightCycle c) =>
            c.Duration(DayPhase.Morgen) + c.Duration(DayPhase.Tag) + c.Duration(DayPhase.Daemmerung) + c.Duration(DayPhase.Nacht);

        float SecondsPerHour()
        {
            var c = DayNightCycle.Instance;
            return c != null ? CycleSeconds(c) / 24f : 0f;
        }

        /// <summary>Eine Spielstunde = 1/24 des Tag-Nacht-Zyklus, gleichmaessig ueber alle Phasen. Pausiert der Zyklus, steht die Zeit.</summary>
        float GameHours(float dt)
        {
            var c = DayNightCycle.Instance;
            if (c == null) return dt / Mathf.Max(0.01f, Sim.Tuning.fallbackSecondsPerGameHour);
            if (c.Paused) return 0f;
            return dt * c.TimeScale * 24f / CycleSeconds(c);
        }

        EnvironmentInput SampleEnvironment()
        {
            var e = new EnvironmentInput();
            var c = DayNightCycle.Instance;
            e.nightFactor = c != null ? c.NightFactor : 0f;
            if (vision == null) vision = FindAnyObjectByType<PlayerVision>();
            e.indoors = vision != null && vision.Current != null;

            if (Time.time >= nextLightScan) ScanLights();
            e.lightIsland = NearLight() || CarriesLight;

            foreach (var kv in zones)
            {
                var z = kv.Key;
                if (z == null) continue;
                e.indoors |= z.Indoors;
                e.nearFire |= z.NearFire;
                e.lightIsland |= z.LightIsland;
                e.thicket |= z.Thicket;
            }
            return e;
        }

        void ScanLights()
        {
            nextLightScan = Time.time + lightScanInterval;
            lights = FindObjectsByType<Light2D>();
        }

        bool NearLight()
        {
            Vector2 p = transform.position;
            foreach (var l in lights)
            {
                if (l == null || !l.enabled || !l.gameObject.activeInHierarchy) continue;
                if (l.lightType != Light2D.LightType.Point || l.intensity < minLightIntensity) continue;
                if (l.transform.IsChildOf(transform)) continue; // eigenes Licht zaehlt nicht
                if (((Vector2)l.transform.position - p).sqrMagnitude < l.pointLightOuterRadius * lightReach * l.pointLightOuterRadius * lightReach) return true;
            }
            return false;
        }

        // ------------------------------------------------------------------ Zonen
        public void EnterZone(SurvivalZone z)
        {
            zones.TryGetValue(z, out int n);
            zones[z] = n + 1;
            if (n == 0) Sim.SetModifiers(z, z.Effects);
        }

        public void ExitZone(SurvivalZone z, bool all = false)
        {
            if (!zones.TryGetValue(z, out int n)) return;
            if (n <= 1 || all)
            {
                zones.Remove(z);
                Sim.RemoveModifiers(z);
            }
            else zones[z] = n - 1;
        }

        // ------------------------------------------------------------------ Taetigkeit
        /// <summary>Taetigkeit von aussen erzwingen (Rast, Schlaf). Mit EndActivity() wieder freigeben.</summary>
        public void BeginActivity(ActivityKind kind) { hasForced = true; forcedActivity = kind; }
        public void EndActivity() => hasForced = false;

        void Update()
        {
            var sim = Sim;
            if (sim == null) return;

            if (!subscribedDialogue && DialogueRunner.Instance != null)
            {
                DialogueRunner.Instance.Ended += OnDialogueEnded;
                subscribedDialogue = true;
            }

            var kb = Keyboard.current;
            bool locked = controller.InputLocked;
            bool moving = !locked && controller.MoveInput.sqrMagnitude > 0.01f;

            ActivityKind a;
            if (sim.IsDead) a = ActivityKind.Idle;
            else if (hasForced) a = forcedActivity;
            else if (interactor != null && interactor.Busy) a = ActivityKind.Talking;
            else if (Time.time < fightUntil) a = ActivityKind.Fighting;
            else if (moving && kb != null && kb[sprintKey].isPressed && sim.CanSprint) a = ActivityKind.Sprinting;
            else if (moving && kb != null && kb[sneakKey].isPressed) a = ActivityKind.Sneaking;
            else if (moving) a = ActivityKind.Walking;
            else a = ActivityKind.Idle;
            sim.SetActivity(a);

            ApplyMovement(sim, a);

            if (kb != null && !locked && !sim.IsDead && kb[dodgeKey].wasPressedThisFrame) TryDodge();
        }

        void ApplyMovement(SurvivalSimulation sim, ActivityKind a)
        {
            if (sim.IsDead) { controller.SpeedMultiplier = 0f; controller.Sway = 0f; return; }
            float m = sim.Mult(EffectKind.MoveSpeedMult);
            if (a == ActivityKind.Sprinting) m *= sim.Tuning.sprintSpeedMultiplier * sim.Mult(EffectKind.SprintSpeedMult);
            else if (a == ActivityKind.Sneaking) m *= sim.Tuning.sneakSpeedMultiplier;
            controller.SpeedMultiplier = m;
            controller.Sway = Mathf.Clamp01(sim.Sum(EffectKind.ControlSway));
        }

        void TryDodge()
        {
            if (Time.time < nextDodge || controller.IsAttacking || routineRunning) return;
            if (!Sim.TryDodge()) return;
            nextDodge = Time.time + dodgeCooldown;
            Vector2 dir = controller.MoveInput.sqrMagnitude > 0.01f ? controller.MoveInput : -controller.FacingVector;
            controller.Kick(dir, dodgeSpeed);
            controller.BeginDodge(dir, dodgeAnimTime);
            Dodged?.Invoke();
        }

        // ------------------------------------------------------------------ Kampf
        /// <summary>Wird von PlayerCombat vor jedem Schlag gerufen. false = zu erschoepft oder gesperrt.</summary>
        public bool TryAttack(float costMultiplier = 1f)
        {
            if (!Sim.CanAttack || !Sim.TryConsumeStamina(Sim.Tuning.attackStaminaCost * costMultiplier)) return false;
            fightUntil = Time.time + fightHold;
            return true;
        }

        /// <summary>Treffer von Monstern: amount = Lebenspunkte (Kampfregeln: 3 insgesamt).</summary>
        public void TakeDamage(int amount, Vector2 hitDirection)
        {
            if (!Sim.TakeLifePoints(Mathf.Max(1, amount))) return;
            controller.Kick(hitDirection, knockbackSpeed);
            if (Core.CameraFollow2D.Main != null) Core.CameraFollow2D.Main.Shake(0.06f, 0.2f);
        }

        // ------------------------------------------------------------------ Gespraeche
        void OnDialogueEnded(NpcDialogue npc)
        {
            string id = npc != null && npc.Profile != null ? npc.Profile.id : null;
            Sim.RegisterConversation(id);
        }

        // ------------------------------------------------------------------ Tod und Zusammenbruch
        void OnDied()
        {
            if (!routineRunning) StartCoroutine(DeathRoutine());
        }

        IEnumerator DeathRoutine()
        {
            routineRunning = true;
            controller.InputLocked = true;
            yield return new WaitForSeconds(deathDelay);

            var cycle = DayNightCycle.Instance;
            if (deathSkipsToMorning && cycle != null)
            {
                for (int i = 0; i < 8 && cycle.Phase != DayPhase.Morgen; i++) cycle.SkipToNextPhase();
            }
            Vector3 target = respawnPoint != null ? respawnPoint.position : homePosition;
            if (body != null) { body.position = target; body.linearVelocity = Vector2.zero; }
            transform.position = target;
            Sim.Revive();
            controller.InputLocked = false;
            routineRunning = false;
            Message?.Invoke("I woke up weak and shaken.");
        }

        void OnCollapsed()
        {
            if (!routineRunning && !Sim.IsDead) StartCoroutine(CollapseRoutine());
        }

        IEnumerator CollapseRoutine()
        {
            routineRunning = true;
            controller.InputLocked = true;
            Message?.Invoke("My legs gave out.");
            yield return new WaitForSeconds(collapseDuration);
            Sim.Set(StatId.Fatigue, fatigueAfterCollapse);
            controller.InputLocked = false;
            routineRunning = false;
        }

        // ------------------------------------------------------------------ Schlaf und Rast
        /// <summary>Bis zum Morgen schlafen. Nur in Daemmerung und Nacht, nicht bei niedriger Sanity (Schlafsperre).</summary>
        public bool TrySleep(out string reason)
        {
            reason = null;
            if (routineRunning) { reason = "Not now."; return false; }
            var c = DayNightCycle.Instance;
            if (c != null && (c.Phase == DayPhase.Morgen || c.Phase == DayPhase.Tag))
            {
                reason = "It's too early to sleep.";
                Message?.Invoke(reason);
                return false;
            }
            if (!Sim.CanSleep(out reason))
            {
                Message?.Invoke(reason);
                return false;
            }
            StartCoroutine(SleepRoutine());
            return true;
        }

        float HoursUntilMorning()
        {
            var c = DayNightCycle.Instance;
            if (c == null) return 8f;
            float seconds = c.PhaseTimeLeft;
            if (c.Phase == DayPhase.Daemmerung) seconds += c.Duration(DayPhase.Nacht);
            return Mathf.Max(0.5f, seconds / SecondsPerHour());
        }

        IEnumerator SleepRoutine()
        {
            routineRunning = true;
            controller.InputLocked = true;
            float hours = HoursUntilMorning();
            yield return new WaitForSeconds(0.8f);
            var result = Sim.Sleep(hours, system.SecondsPerHour);

            var cycle = DayNightCycle.Instance;
            if (cycle != null)
            {
                for (int i = 0; i < 8 && cycle.Phase != DayPhase.Morgen; i++) cycle.SkipToNextPhase();
            }
            if (result.nightmare) Message?.Invoke("Nightmares. I barely slept.");
            controller.InputLocked = false;
            routineRunning = false;
        }

        /// <summary>Hinsetzen und ausruhen (Bank, Quelle): Ausdauer und Maximum-Erschoepfung erholen sich.</summary>
        public void Rest(float seconds)
        {
            if (!routineRunning) StartCoroutine(RestRoutine(seconds));
        }

        IEnumerator RestRoutine(float seconds)
        {
            routineRunning = true;
            controller.InputLocked = true;
            BeginActivity(ActivityKind.Resting);
            yield return new WaitForSeconds(seconds);
            EndActivity();
            controller.InputLocked = false;
            routineRunning = false;
        }

        public void Say(string text) => Message?.Invoke(text);
    }
}
