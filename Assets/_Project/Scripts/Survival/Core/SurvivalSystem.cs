using System;
using UnityEngine;

namespace Nightward.Survival
{
    /// <summary>
    /// Haengt die SurvivalSimulation an die Unity-Zeit. Liegt auf dem Spieler (oder einem Manager-Objekt).
    /// Die Welt kuemmert sich selbst darum, Zeit und Umwelt zu liefern: GameHoursSource (Tag-Nacht-Zyklus) und
    /// EnvironmentSource (Licht, Innenraum, Feuer). Ohne diese laeuft die Fallback-Zeit aus der Config.
    /// </summary>
    [DefaultExecutionOrder(-90)]
    public class SurvivalSystem : MonoBehaviour
    {
        public static SurvivalSystem Instance { get; private set; }

        [Tooltip("Balancing-Asset. Leer = Standardwerte aus dem Code")]
        [SerializeField] SurvivalConfig config;

        [Header("Feinabstimmung zur Laufzeit")]
        [Tooltip("Faktor auf alle Raten pro Spielstunde (Hunger, Durst, Sanity ...). 1 = wie in der Config, 2 = doppelt so schnell. Auch ein einfacher Schwierigkeitsregler")]
        [SerializeField, Range(0f, 10f)] float hoursScale = 1f;
        [SerializeField] bool autoTick = true;
        [Tooltip("Unverwundbar (zum Testen)")]
        [SerializeField] bool godMode;
        [SerializeField] bool captureBreakdown;

        public SurvivalSimulation Sim { get; private set; }

        /// <summary>Liefert die vergangenen Spielstunden fuer dt Sekunden (0 bei pausierter Weltzeit). Leer = Fallback der Config.</summary>
        public Func<float, float> GameHoursSource;
        /// <summary>Liefert Nachtanteil, Innenraum, Licht, Feuer. Leer = Tag, draussen.</summary>
        public Func<EnvironmentInput> EnvironmentSource;
        /// <summary>Sekunden pro Spielstunde fuer Fast-Forward (Schlaf). Leer = Fallback der Config.</summary>
        public Func<float> SecondsPerHourSource;

        public float HoursScale { get => hoursScale; set => hoursScale = Mathf.Max(0f, value); }
        public bool AutoTick { get => autoTick; set => autoTick = value; }
        public bool GodMode { get => godMode; set { godMode = value; if (Sim != null) Sim.GodMode = value; } }
        public bool CaptureBreakdown { get => captureBreakdown; set { captureBreakdown = value; if (Sim != null) Sim.CaptureBreakdown = value; } }
        public SurvivalConfig Config => Sim != null ? Sim.Config : config;

        public float SecondsPerHour
        {
            get
            {
                float s = SecondsPerHourSource != null ? SecondsPerHourSource() : 0f;
                return s > 0.01f ? s : Sim.Tuning.fallbackSecondsPerGameHour;
            }
        }

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Debug.LogWarning("Mehr als ein SurvivalSystem, " + name + " wird ignoriert.", this);
                enabled = false;
                return;
            }
            Instance = this;
            Sim = new SurvivalSimulation(config != null ? config : SurvivalDefaults.Create());
            Sim.GodMode = godMode;
            Sim.CaptureBreakdown = captureBreakdown;
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Update()
        {
            if (!autoTick || Sim == null) return;
            // Grosse Spruenge (Ladebildschirm, Breakpoint) nicht als Echtzeit zaehlen
            float dt = Mathf.Min(Time.deltaTime, 0.1f);
            float hours = GameHoursSource != null ? GameHoursSource(dt) : dt / Mathf.Max(0.01f, Sim.Tuning.fallbackSecondsPerGameHour);
            Sim.SetEnvironment(EnvironmentSource != null ? EnvironmentSource() : default);
            Sim.Tick(dt, hours * hoursScale);
        }

        /// <summary>Spielstand als JSON.</summary>
        public string SaveJson() => JsonUtility.ToJson(Sim.Save());

        public void LoadJson(string json)
        {
            if (!string.IsNullOrEmpty(json)) Sim.Load(JsonUtility.FromJson<SurvivalSaveData>(json));
        }
    }
}
