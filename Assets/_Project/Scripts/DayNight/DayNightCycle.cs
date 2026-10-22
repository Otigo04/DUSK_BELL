using System;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.DayNight
{
    public enum DayPhase { Morgen, Tag, Daemmerung, Nacht }

    /// <summary>
    /// Spieluhr mit den festen Phasen aus dem Regelwerk (Morgen 0:30, Tag 6:00, Daemmerung 1:00, Nacht 2:30).
    /// Andere Systeme lesen Phase/NightFactor oder haengen sich an PhaseChanged/NewDay.
    /// Zum Testen: Zeitraffer und Pause im Inspector, im Editor/Development-Build auch per Taste
    /// (F5 naechste Phase, F6 Zeitraffer 1x/10x/30x/60x, F7 Pause).
    /// </summary>
    [DefaultExecutionOrder(-200)]
    public class DayNightCycle : MonoBehaviour
    {
        public static DayNightCycle Instance { get; private set; }

        [Header("Phasendauer in Sekunden (Regelwerk: 30 / 360 / 60 / 150)")]
        [SerializeField] float morgenDauer = 30f;
        [SerializeField] float tagDauer = 360f;
        [SerializeField] float daemmerungDauer = 60f;
        [SerializeField] float nachtDauer = 150f;

        [Header("Start")]
        [SerializeField] DayPhase startPhase = DayPhase.Morgen;
        [SerializeField, Range(0f, 1f)] float startProgress;

        [Header("Testen")]
        [Tooltip("Zeitraffer, 1 = Echtzeit. Laesst sich im Play-Mode live aendern")]
        [SerializeField, Range(0f, 120f)] float timeScale = 1f;
        [SerializeField] bool paused;
        [Tooltip("F5 naechste Phase, F6 Zeitraffer umschalten, F7 Pause (nur Editor/Development-Build)")]
        [SerializeField] bool debugKeys = true;

        static readonly float[] DebugScales = { 1f, 10f, 30f, 60f };
        // Anteil jeder Phase am sichtbaren Lichtverlauf (LightTime 0..1), unabhaengig von der echten Dauer
        static readonly float[] LightStart = { 0f, 0.1f, 0.6f, 0.8f };
        static readonly float[] LightLength = { 0.1f, 0.5f, 0.2f, 0.2f };

        float elapsed;

        public int Day { get; private set; } = 1;
        public DayPhase Phase { get; private set; }
        public float PhaseProgress => Mathf.Clamp01(elapsed / Duration(Phase));
        public float PhaseTimeLeft => Duration(Phase) - elapsed;
        /// <summary>0 = heller Tag, 1 = volle Nacht. Weicher Uebergang in Morgen und Daemmerung.</summary>
        public float NightFactor { get; private set; }
        /// <summary>Sichtbarer Tagesverlauf 0..1 fuer Licht-Verlaeufe (0 Morgengrauen, 0.6 Daemmerung, 0.8 Nacht).</summary>
        public float LightTime => LightStart[(int)Phase] + LightLength[(int)Phase] * PhaseProgress;
        public float TimeScale { get => timeScale; set => timeScale = Mathf.Max(0f, value); }
        public bool Paused { get => paused; set => paused = value; }

        public event Action<DayPhase> PhaseChanged;
        public event Action<int> NewDay;

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Debug.LogWarning("Mehr als ein DayNightCycle in der Szene, " + name + " wird ignoriert.", this);
                enabled = false;
                return;
            }
            Instance = this;
            Phase = startPhase;
            elapsed = startProgress * Duration(startPhase);
            UpdateNightFactor();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Update()
        {
#if UNITY_EDITOR || DEVELOPMENT_BUILD
            if (debugKeys) HandleDebugKeys();
#endif
            if (!paused) Advance(Time.deltaTime * timeScale);
            UpdateNightFactor();
        }

        void Advance(float dt)
        {
            elapsed += dt;
            // while statt if: bei hohem Zeitraffer koennen mehrere Phasen in einem Frame vergehen
            while (elapsed >= Duration(Phase))
            {
                elapsed -= Duration(Phase);
                EnterPhase(Next(Phase));
            }
        }

        void EnterPhase(DayPhase phase)
        {
            Phase = phase;
            if (phase == DayPhase.Morgen)
            {
                Day++;
                NewDay?.Invoke(Day);
            }
            PhaseChanged?.Invoke(phase);
        }

        void UpdateNightFactor()
        {
            float p = PhaseProgress;
            switch (Phase)
            {
                case DayPhase.Morgen: NightFactor = 1f - Mathf.SmoothStep(0f, 1f, p); break;
                case DayPhase.Tag: NightFactor = 0f; break;
                case DayPhase.Daemmerung: NightFactor = Mathf.SmoothStep(0f, 1f, p); break;
                default: NightFactor = 1f; break;
            }
        }

        public float Duration(DayPhase phase)
        {
            switch (phase)
            {
                case DayPhase.Morgen: return Mathf.Max(0.01f, morgenDauer);
                case DayPhase.Tag: return Mathf.Max(0.01f, tagDauer);
                case DayPhase.Daemmerung: return Mathf.Max(0.01f, daemmerungDauer);
                default: return Mathf.Max(0.01f, nachtDauer);
            }
        }

        static DayPhase Next(DayPhase p) => (DayPhase)(((int)p + 1) % 4);

        /// <summary>Springt direkt in eine Phase (z. B. Debug oder Story-Ereignis). Loest PhaseChanged aus.</summary>
        public void SetPhase(DayPhase phase, float progress = 0f)
        {
            bool changed = phase != Phase;
            Phase = phase;
            elapsed = Mathf.Clamp01(progress) * Duration(phase);
            UpdateNightFactor();
            if (changed) PhaseChanged?.Invoke(phase);
        }

        public void SkipToNextPhase()
        {
            elapsed = 0f;
            EnterPhase(Next(Phase));
            UpdateNightFactor();
        }

        [ContextMenu("Springen: Morgen")] void JumpMorgen() => SetPhase(DayPhase.Morgen);
        [ContextMenu("Springen: Tag")] void JumpTag() => SetPhase(DayPhase.Tag);
        [ContextMenu("Springen: Daemmerung")] void JumpDaemmerung() => SetPhase(DayPhase.Daemmerung);
        [ContextMenu("Springen: Nacht")] void JumpNacht() => SetPhase(DayPhase.Nacht);

        void HandleDebugKeys()
        {
            var kb = Keyboard.current;
            if (kb == null) return;
            if (kb.f5Key.wasPressedThisFrame) SkipToNextPhase();
            if (kb.f6Key.wasPressedThisFrame)
            {
                int i = Array.IndexOf(DebugScales, timeScale);
                timeScale = DebugScales[(i + 1) % DebugScales.Length];
                Debug.Log($"[Tag/Nacht] Zeitraffer {timeScale}x");
            }
            if (kb.f7Key.wasPressedThisFrame) paused = !paused;
        }
    }
}
