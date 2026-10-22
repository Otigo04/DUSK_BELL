using UnityEngine;
using UnityEngine.UI;

namespace Nightward.DayNight
{
    /// <summary>
    /// Tageszeit-Symbol oben links (UI-Cheatsheet): Sonne #ffd27a am Tag, Mond #e8e0f0 in der Nacht.
    /// Wechselt mit kurzem Ueberblenden, sobald es mehr Nacht als Tag ist.
    /// </summary>
    public class DayNightHud : MonoBehaviour
    {
        [SerializeField] Image icon;
        [SerializeField] Sprite sun;
        [SerializeField] Sprite moon;
        [SerializeField] float fadeTime = 0.4f;

        bool showingMoon;
        float alpha = 1f;
        bool fadingOut;

        void Start()
        {
            showingMoon = IsNight();
            icon.sprite = showingMoon ? moon : sun;
        }

        void Update()
        {
            if (!fadingOut && IsNight() != showingMoon) fadingOut = true;

            float step = Time.deltaTime / Mathf.Max(0.01f, fadeTime);
            if (fadingOut)
            {
                alpha -= step;
                if (alpha <= 0f)
                {
                    alpha = 0f;
                    fadingOut = false;
                    showingMoon = !showingMoon;
                    icon.sprite = showingMoon ? moon : sun;
                }
            }
            else alpha = Mathf.Min(1f, alpha + step);

            var c = icon.color;
            c.a = alpha;
            icon.color = c;
        }

        static bool IsNight() => DayNightCycle.Instance != null && DayNightCycle.Instance.NightFactor > 0.5f;
    }
}
