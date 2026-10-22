using System.Collections.Generic;
using Nightward.DayNight;
using UnityEngine;

namespace Nightward.UI
{
    /// <summary>Testszene fuer UI_Test: Knoepfe loesen Dialog, Bericht, Zeit und HUD-Werte aus.</summary>
    public class NwUITestController : MonoBehaviour
    {
        [SerializeField] NwDialogBox dialog;
        [SerializeField] NwHud hud;
        [SerializeField] NwReport report;

        struct Line
        {
            public string speaker;     // null = Erzaehler
            public Color color;
            public string text;
        }

        static readonly float[] Speeds = { 1f, 10f, 30f, 60f };

        readonly List<Line> script = new List<Line>();
        int cursor;
        int actions = 3;
        int talismans = 5;
        int trust = 7;
        int knowledge = 3;
        int wake = 2;
        int health = 7;
        const int MaxHealth = 10;

        void Awake()
        {
            script.Add(new Line { speaker = null, text = "Der Wind riecht nach Regen. Zwischen den Häusern brennt noch ein einzelnes Licht, und irgendwo hinter dem Wald knackt etwas im Unterholz." });
            script.Add(new Line { speaker = "Ilhan", color = new Color32(0xff, 0xd2, 0x7a, 255), text = "Heute Nacht schließen wir die Fensterläden früher, Fremder. Ärger gibt es immer, wenn der Mond tief steht, und die Hunde bellen schon seit dem Abendessen." });
            script.Add(new Line { speaker = "Mara", color = new Color32(0xc4, 0x63, 0x6b, 255), text = "Bring die Öllampen in den Keller. Und vergiss den Talisman nicht!" });
        }

        void OnEnable()
        {
            dialog.Advance += NextLine;
            report.Continued += OnReportContinued;
        }

        void OnDisable()
        {
            dialog.Advance -= NextLine;
            report.Continued -= OnReportContinued;
        }

        void Start()
        {
            dialog.gameObject.SetActive(false);
            report.gameObject.SetActive(false);
            hud.SetActions(actions);
            hud.SetTalismans(talismans, 6);
            hud.SetTrust(trust);
            hud.SetKnowledge(knowledge);
            hud.SetHealth(health, MaxHealth);
            hud.ShowWake(true);
            hud.SetWake(wake);
        }

        void ShowLine()
        {
            var l = script[cursor];
            if (l.speaker == null) dialog.ShowNarrator(l.text);
            else dialog.ShowResident(l.speaker, l.color, l.text);
        }

        void NextLine()
        {
            cursor++;
            if (cursor >= script.Count) dialog.Hide();
            else ShowLine();
        }

        void OnReportContinued() { }

        // --- Knopf-Ereignisse
        public void OnDialog()
        {
            report.gameObject.SetActive(false);
            cursor = 1;
            ShowLine();
        }

        public void OnNarrator()
        {
            report.gameObject.SetActive(false);
            cursor = 0;
            ShowLine();
        }

        public void OnReport()
        {
            dialog.Hide();
            int day = DayNightCycle.Instance != null ? DayNightCycle.Instance.Day : 3;
            report.Begin(day, new List<ReportLine>
            {
                new ReportLine(ReportKind.GainTalisman, "+1 Talisman"),
                new ReportLine(ReportKind.Warning, "Das Versteck regt sich."),
                new ReportLine(ReportKind.Loss, "Mara"),
                new ReportLine(ReportKind.GainKnowledge, "Wissen: Der Brunnen ruft nachts und niemand weiß warum."),
                new ReportLine(ReportKind.GainKnowledge, "Wissen: Die Eiche am Weg"),
                new ReportLine(ReportKind.Warning, "Der Keller riecht nach nassem Fell."),
            });
        }

        public void OnPhase() { if (DayNightCycle.Instance != null) DayNightCycle.Instance.SkipToNextPhase(); }

        public void OnSpeed()
        {
            var c = DayNightCycle.Instance;
            if (c == null) return;
            int i = System.Array.IndexOf(Speeds, c.TimeScale);
            c.TimeScale = Speeds[(i + 1) % Speeds.Length];
        }

        public void OnPause() { if (DayNightCycle.Instance != null) DayNightCycle.Instance.Paused = !DayNightCycle.Instance.Paused; }
        public void OnAction() { actions = (actions + 4) % 5; hud.SetActions(actions); }
        public void OnTalisman() { talismans = (talismans + 6) % 7; hud.SetTalismans(talismans, 6); }
        public void OnTrust() { trust = (trust + 1) % 11; hud.SetTrust(trust); }
        public void OnKnowledge() { knowledge = (knowledge + 1) % 11; hud.SetKnowledge(knowledge); }
        public void OnWake() { wake = (wake + 1) % 6; hud.SetWake(wake); }
        public void OnHealthMinus() { health = Mathf.Max(0, health - 1); hud.SetHealth(health, MaxHealth); }
        public void OnHealthPlus() { health = Mathf.Min(MaxHealth, health + 1); hud.SetHealth(health, MaxHealth); }
    }
}
