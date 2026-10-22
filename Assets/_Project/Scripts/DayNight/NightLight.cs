using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Nightward.DayNight
{
    /// <summary>
    /// Light 2D, das in der Daemmerung angeht und am Morgen wieder aus. Jede Lampe bekommt einen zufaelligen
    /// Schaltpunkt, so gehen die Lichter im Dorf nacheinander an statt alle gleichzeitig. Leichtes Flackern optional.
    /// Mit autoSwitch = aus steuert ein anderes Skript (z. B. HouseLights) das Licht ueber SwitchOn.
    /// </summary>
    [RequireComponent(typeof(Light2D))]
    public class NightLight : MonoBehaviour
    {
        [Tooltip("Licht folgt automatisch dem NightFactor. Aus = Steuerung von aussen ueber SwitchOn")]
        [SerializeField] bool autoSwitch = true;
        [Tooltip("Bei welchem Nachtanteil (0..1) das Licht angeht, zufaellig in diesem Bereich")]
        [SerializeField] Vector2 switchOnRange = new Vector2(0.15f, 0.55f);
        [SerializeField] float fadeTime = 1.2f;
        [Tooltip("Helligkeit am Tag relativ zur Nacht (z. B. Lagerfeuer brennt auch tagsueber schwach)")]
        [SerializeField, Range(0f, 1f)] float dayLevel;

        [Header("Flackern")]
        [SerializeField, Range(0f, 0.5f)] float flicker = 0.06f;
        [SerializeField] float flickerSpeed = 3f;

        Light2D lightSource;
        float maxIntensity;
        float threshold;
        float level;
        float seed;
        bool on;
        bool initialized;

        public bool IsOn => on;

        void Awake()
        {
            lightSource = GetComponent<Light2D>();
            maxIntensity = lightSource.intensity;
            threshold = Random.Range(switchOnRange.x, switchOnRange.y);
            seed = Random.value * 100f;
        }

        void Start()
        {
            // Beim Laden ohne Einblenden direkt im richtigen Zustand starten
            if (autoSwitch) on = Night() >= threshold;
            level = on ? 1f : 0f;
            initialized = true;
        }

        /// <summary>Licht ein/aus (mit Einblenden). Fuer autoSwitch = aus.</summary>
        public void SwitchOn(bool value, bool instant = false)
        {
            on = value;
            if (instant || !initialized) level = on ? 1f : 0f;
        }

        void Update()
        {
            if (autoSwitch)
            {
                float night = Night();
                // kleine Hysterese, damit das Licht am Schaltpunkt nicht flimmert
                if (!on && night >= threshold) on = true;
                else if (on && night < threshold - 0.05f) on = false;
            }
            level = Mathf.MoveTowards(level, on ? 1f : 0f, Time.deltaTime / Mathf.Max(0.01f, fadeTime));

            float f = 1f + (Mathf.PerlinNoise(seed, Time.time * flickerSpeed) - 0.5f) * 2f * flicker;
            float target = Mathf.Lerp(dayLevel, 1f, level) * maxIntensity * f;
            lightSource.intensity = target;
            lightSource.enabled = target > 0.001f;
        }

        static float Night() => DayNightCycle.Instance != null ? DayNightCycle.Instance.NightFactor : 1f;
    }
}
