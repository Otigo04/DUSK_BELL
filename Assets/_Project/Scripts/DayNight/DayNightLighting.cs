using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Nightward.DayNight
{
    /// <summary>
    /// Faerbt das Global Light 2D ueber den Tagesverlauf (Style-Bibel: Global Light 2D fuer den Tagesverlauf)
    /// und blendet das Nacht-Volume (Bloom, Vignette, Farbstich) mit dem NightFactor ein.
    /// Nachts wird nur die Umgebung dunkel, Lichtquellen bleiben hell (NightLight).
    /// </summary>
    public class DayNightLighting : MonoBehaviour
    {
        /// <summary>Nacht-Profil unter Assets/_Project/Resources, damit der Bootstrap es in jeder Szene laden kann.</summary>
        public const string NightProfileResource = "Volume_Nacht";

        [SerializeField] Light2D globalLight;
        [Tooltip("Farbe des Umgebungslichts ueber LightTime (0 Morgengrauen, 0.1 Morgen, 0.6 Daemmerung, 0.8 Nacht)")]
        [SerializeField] Gradient color = DefaultColor();
        [SerializeField] AnimationCurve intensity = DefaultIntensity();
        [Tooltip("Wird mit dem NightFactor eingeblendet")]
        [SerializeField] Volume nightVolume;

        void Reset()
        {
            color = DefaultColor();
            intensity = DefaultIntensity();
        }

        void Start()
        {
            // Szenen ohne Einrichtung (Bootstrap): Global Light, Volume und Post-Processing selbst besorgen
            if (globalLight == null)
                foreach (var l in FindObjectsByType<Light2D>())
                    if (l.lightType == Light2D.LightType.Global) { globalLight = l; break; }

            if (nightVolume == null)
            {
                var profile = Resources.Load<VolumeProfile>(NightProfileResource);
                if (profile != null)
                {
                    var go = new GameObject("Nacht_Volume");
                    go.transform.SetParent(transform, false);
                    nightVolume = go.AddComponent<Volume>();
                    nightVolume.isGlobal = true;
                    nightVolume.sharedProfile = profile;
                    nightVolume.weight = 0f;
                }
            }

            var cam = Camera.main;
            if (cam != null && cam.TryGetComponent<UniversalAdditionalCameraData>(out var data))
                data.renderPostProcessing = true;
        }

        void LateUpdate()
        {
            var cycle = DayNightCycle.Instance;
            if (cycle == null) return;
            float t = cycle.LightTime;
            if (globalLight != null)
            {
                globalLight.color = color.Evaluate(t);
                globalLight.intensity = intensity.Evaluate(t);
            }
            if (nightVolume != null) nightVolume.weight = cycle.NightFactor;
        }

        static Color Rgb(int r, int g, int b) => new Color(r / 255f, g / 255f, b / 255f);

        static Gradient DefaultColor()
        {
            var night = Rgb(78, 88, 140); // kaltes, gespenstisches Nachtblau, an der Palette (3f5570 / 3a4a7a) orientiert
            var g = new Gradient();
            g.SetKeys(new[]
            {
                new GradientColorKey(night, 0f),
                new GradientColorKey(Rgb(196, 150, 178), 0.05f), // Morgengrauen rosa-violett
                new GradientColorKey(Rgb(255, 222, 180), 0.1f),  // warmer Morgen
                new GradientColorKey(Rgb(255, 248, 235), 0.35f), // Mittag
                new GradientColorKey(Rgb(255, 230, 190), 0.58f), // goldener Nachmittag
                new GradientColorKey(Rgb(255, 166, 112), 0.66f), // Sonnenuntergang (Feuer Glut)
                new GradientColorKey(Rgb(176, 120, 160), 0.72f), // Daemmerung violett-rosa
                new GradientColorKey(night, 0.8f),
            }, new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(1f, 1f) });
            return g;
        }

        static AnimationCurve DefaultIntensity() => new AnimationCurve(
            new Keyframe(0f, 0.18f), new Keyframe(0.1f, 0.85f), new Keyframe(0.35f, 1f), new Keyframe(0.58f, 0.95f),
            new Keyframe(0.66f, 0.75f), new Keyframe(0.72f, 0.45f), new Keyframe(0.8f, 0.18f), new Keyframe(1f, 0.18f));
    }
}
