using Nightward.DayNight;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Das Spiel-HUD (Art/UI/HUD_Neu). Oben links: Uhr-Platte (Phasen-Symbol, Uhrzeit, Tag), Tagesspur, Vitalbalken
    /// (Leben, Ausdauer, Sanity). Rechts unten: Bedarfs- und Stimmungskacheln. Der Quest-Tracker (NwQuestTracker)
    /// haengt als Kind darunter und liest den QuestLog selbst.
    /// Die Uhr folgt dem DayNightCycle, sofern einer in der Szene ist. Alle Werte kommen ueber die Set-Methoden,
    /// z. B. NwGameHud.Instance.SetHealth(2, 3).
    /// </summary>
    [RequireComponent(typeof(CanvasGroup))]
    public class NwGameHud : MonoBehaviour
    {
        public static NwGameHud Instance { get; private set; }

        const int TrackPixels = 48;      // 2 px pro Stunde
        const float TrackLeft = 1f;      // Segmente beginnen 1 px im Rahmen

        [Header("Uhr")]
        [SerializeField] bool followDayNightCycle = true;
        [SerializeField] Image phaseIcon;
        [SerializeField] Text clockText;
        [SerializeField] Text dayText;
        [SerializeField] Sprite iconMorning;
        [SerializeField] Sprite iconDay;
        [SerializeField] Sprite iconEvening;
        [SerializeField] Sprite iconNight;

        [Header("Tagesspur")]
        [SerializeField] Image trackPast;
        [SerializeField] RectTransform trackMarker;

        [Header("Vitalbalken")]
        [SerializeField] NwVitalBar health;
        [SerializeField] NwVitalBar stamina;
        [SerializeField] NwVitalBar sanity;

        [Header("Bedarf und Stimmung")]
        [SerializeField] NwNeedTile[] needs;

        CanvasGroup group;
        int lastMinute = -1;
        int lastPhase = -1;
        int lastDay = -1;

        void Awake()
        {
            Instance = this;
            group = GetComponent<CanvasGroup>();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Start()
        {
            health.Set(1f, 1f, true);
            stamina.Set(1f, 1f, true);
            sanity.Set(1f, 1f, true);
            foreach (var n in needs) n.Set(0);
        }

        void Update()
        {
            if (!followDayNightCycle) return;
            var c = DayNightCycle.Instance;
            if (c != null) SetTime(c.Phase, NwClock.Hour(c.Phase, c.PhaseProgress), c.Day);
        }

        /// <summary>HUD ein-/ausblenden (z. B. waehrend Cutscenes).</summary>
        public void SetVisible(bool visible)
        {
            group.alpha = visible ? 1f : 0f;
            group.blocksRaycasts = visible;
        }

        // ------------------------------------------------------------------ Uhr
        /// <summary>Uhrzeit (0-24), Phase und Tag. Aktualisiert nur bei Aenderung.</summary>
        public void SetTime(DayPhase phase, float hour, int day)
        {
            int minutes = Mathf.FloorToInt(hour * 60f) % 1440;
            if (minutes != lastMinute)
            {
                lastMinute = minutes;
                clockText.text = (minutes / 60).ToString("00") + ":" + (minutes % 60).ToString("00");
                UpdateTrack(minutes / 60f);
            }
            if (day != lastDay)
            {
                lastDay = day;
                dayText.text = "Day " + day;
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
        }

        void UpdateTrack(float hour)
        {
            int px = Mathf.Clamp(Mathf.FloorToInt(hour * 2f), 0, TrackPixels);
            trackPast.fillAmount = px / (float)TrackPixels;
            var p = trackMarker.anchoredPosition;
            p.x = TrackLeft + px - 2f;       // Marke ist 5 px breit, Mitte auf der aktuellen Stunde
            trackMarker.anchoredPosition = p;
        }

        // ------------------------------------------------------------------ Vitalwerte
        /// <summary>Leben. Unter 30 % wird die Fuellung kritisch (rot).</summary>
        public void SetHealth(float current, float max) => health.Set(Fraction(current, max));

        /// <summary>Ausdauer. maxAllowed &lt; max = Maximum-Erschoepfung (rechter Teil schraffiert gesperrt).</summary>
        public void SetStamina(float current, float max, float maxAllowed = -1f)
        {
            float cap = maxAllowed < 0f ? 1f : Fraction(maxAllowed, max);
            stamina.Set(Fraction(current, max), cap);
        }

        /// <summary>Sanity. Unter 40 % orange (Schlafsperre), unter 20 % rot.</summary>
        public void SetSanity(float current, float max) => sanity.Set(Fraction(current, max));

        static float Fraction(float current, float max) => max <= 0f ? 0f : Mathf.Clamp01(current / max);

        // ------------------------------------------------------------------ Bedarf und Stimmung
        /// <summary>Stufe 0 = Kachel aus, 1-4 = Bedarf, positive = gruene Stimmung (nur Stimmung/Gesellschaft/Anspannung, 1-2).</summary>
        public void SetNeed(NeedKind kind, int level, bool positive = false)
        {
            var tile = FindTile(kind);
            if (tile != null) tile.Set(level, positive);
        }

        public NwNeedTile FindTile(NeedKind kind)
        {
            foreach (var n in needs) if (n.Kind == kind) return n;
            return null;
        }
    }
}
