using Nightward.DayNight;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// HUD am oberen Rand (transparent). Zeile 1: Tageszeit-Symbol, Uhrzeit, Phase (Morgen, Tag, Abend, Nacht),
    /// Lebensbalken, ganz rechts Weckstufe des Verstecks (nur dort sichtbar).
    /// Zeile 2: 4 Aktionspunkte, Talismane (z. B. 5/6), Vertrauen 0-10, Wissen 0-10.
    /// Keine Animation ausser Wertaenderungen. Die Uhr folgt dem DayNightCycle, sofern einer in der Szene ist.
    /// </summary>
    public class NwHud : MonoBehaviour
    {
        const int HealthPixels = 70;      // Breite der Fuellung in Pixeln
        const float CriticalAt = 0.3f;

        [Header("Tageszeit")]
        [SerializeField] bool followDayNightCycle = true;
        [SerializeField] Image phaseIcon;
        [SerializeField] Text clockText;
        [SerializeField] Text phaseText;
        [SerializeField] Sprite iconMorning;
        [SerializeField] Sprite iconDay;
        [SerializeField] Sprite iconEvening;
        [SerializeField] Sprite iconNight;

        [Header("Leben")]
        [SerializeField] Image healthFill;
        [SerializeField] Text healthText;
        [SerializeField] Sprite fillNormal;
        [SerializeField] Sprite fillCritical;

        [Header("Aktionen")]
        [SerializeField] Image[] actionDots;
        [SerializeField] Sprite dotFull;
        [SerializeField] Sprite dotEmpty;

        [Header("Werte")]
        [SerializeField] Text talismanText;
        [SerializeField] Text trustText;
        [SerializeField] Text knowledgeText;

        [Header("Weckstufe (Versteck)")]
        [SerializeField] GameObject wakeRoot;
        [SerializeField] Image[] wakeBars;
        [SerializeField] Sprite barEmpty;
        [SerializeField] Sprite barYellow;
        [SerializeField] Sprite barOrange;
        [SerializeField] Sprite barRed;

        int lastMinute = -1;
        int lastPhase = -1;

        void Update()
        {
            if (!followDayNightCycle) return;
            var c = DayNightCycle.Instance;
            if (c != null) SetTime(c.Phase, NwClock.Hour(c.Phase, c.PhaseProgress));
        }

        /// <summary>Uhrzeit (0-24) und Phase. Aktualisiert nur bei Aenderung.</summary>
        public void SetTime(DayPhase phase, float hour)
        {
            int minutes = Mathf.FloorToInt(hour * 60f) % 1440;
            if (minutes != lastMinute)
            {
                lastMinute = minutes;
                clockText.text = (minutes / 60).ToString("00") + ":" + (minutes % 60).ToString("00");
            }
            if ((int)phase == lastPhase) return;
            lastPhase = (int)phase;
            switch (phase)
            {
                case DayPhase.Morgen: phaseIcon.sprite = iconMorning; break;
                case DayPhase.Tag: phaseIcon.sprite = iconDay; break;
                case DayPhase.Daemmerung: phaseIcon.sprite = iconEvening; break;
                default: phaseIcon.sprite = iconNight; break;
            }
            phaseText.text = NwClock.PhaseName(phase);
            phaseText.color = NwClock.PhaseColor(phase);
        }

        /// <summary>Lebensbalken: 10 Segmente a 7 px, die Fuellung rastet auf ganze Pixel.</summary>
        public void SetHealth(int current, int max)
        {
            max = Mathf.Max(1, max);
            current = Mathf.Clamp(current, 0, max);
            float frac = (float)current / max;
            healthFill.fillAmount = Mathf.Round(frac * HealthPixels) / HealthPixels;
            healthFill.sprite = frac <= CriticalAt ? fillCritical : fillNormal;
            healthText.text = current + "/" + max;
            healthText.color = current <= 0 ? NwTheme.TalismanZero : NwTheme.TextDefault;
        }

        public void SetActions(int current)
        {
            for (int i = 0; i < actionDots.Length; i++)
                actionDots[i].sprite = i < current ? dotFull : dotEmpty;
        }

        public void SetTalismans(int current, int max)
        {
            talismanText.text = current + "/" + max;
            talismanText.color = current <= 0 ? NwTheme.TalismanZero : NwTheme.Talisman;
        }

        public void SetTrust(int value)
        {
            trustText.text = Mathf.Clamp(value, 0, 10).ToString();
            trustText.color = NwTheme.Trust;
        }

        public void SetKnowledge(int value)
        {
            knowledgeText.text = Mathf.Clamp(value, 0, 10).ToString();
            knowledgeText.color = NwTheme.Knowledge;
        }

        public void ShowWake(bool visible) => wakeRoot.SetActive(visible);

        /// <summary>Stufe 0-5. Ab 3 orange, ab 4 rot.</summary>
        public void SetWake(int level)
        {
            level = Mathf.Clamp(level, 0, wakeBars.Length);
            var filled = level >= 4 ? barRed : level >= 3 ? barOrange : barYellow;
            for (int i = 0; i < wakeBars.Length; i++)
                wakeBars[i].sprite = i < level ? filled : barEmpty;
        }
    }
}
