using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Ein Vitalbalken (Leben, Ausdauer, Sanity). Die Fuellung rastet auf ganze Pixel (60 px), das Sprite wechselt
    /// an den Schwellen. Optional: heller Verlust-Streifen (schrumpft nach einem Treffer) und Schraffur fuer das
    /// gesperrte Maximum (Maximum-Erschoepfung).
    /// </summary>
    public class NwVitalBar : MonoBehaviour
    {
        const int Pixels = 60;

        [SerializeField] Image fill;
        [SerializeField] Image trail;
        [SerializeField] Image hatch;

        [Header("Sprites je Zustand (leer lassen = nicht benutzt)")]
        [SerializeField] Sprite normal;
        [SerializeField] Sprite low;
        [SerializeField] Sprite critical;
        [SerializeField] Sprite empty;
        [SerializeField, Range(0f, 1f)] float lowBelow;
        [SerializeField, Range(0f, 1f)] float criticalBelow;

        [Header("Verlust-Streifen")]
        [SerializeField] float trailDelay = 0.4f;
        [SerializeField] float trailSpeed = 0.8f;

        float value = 1f;
        float shown = 1f;
        float hold;

        public float Value => value;

        static float Snap(float f) => Mathf.Round(f * Pixels) / Pixels;

        /// <summary>fraction 0-1; maxFraction &lt; 1 sperrt den rechten Teil (Schraffur).</summary>
        public void Set(float fraction, float maxFraction = 1f, bool instant = false)
        {
            maxFraction = Mathf.Clamp01(maxFraction);
            fraction = Mathf.Min(Mathf.Clamp01(fraction), maxFraction);

            if (fraction < value) hold = trailDelay;
            value = fraction;
            if (instant || shown < value) shown = value;

            Sprite s = normal;
            bool isEmpty = empty != null && value <= 0f;
            if (isEmpty) s = empty;
            else if (critical != null && value < criticalBelow) s = critical;
            else if (low != null && value < lowBelow) s = low;
            fill.sprite = s;
            fill.fillAmount = isEmpty ? 1f : Snap(value);

            if (trail != null) trail.fillAmount = Snap(shown);
            if (hatch != null)
            {
                hatch.enabled = maxFraction < 1f;
                hatch.fillAmount = Snap(1f - maxFraction);
            }
        }

        void Update()
        {
            if (trail == null || shown <= value) return;
            if (hold > 0f) hold -= Time.unscaledDeltaTime;
            else shown = Mathf.Max(value, shown - trailSpeed * Time.unscaledDeltaTime);
            trail.fillAmount = Snap(shown);
        }
    }
}
