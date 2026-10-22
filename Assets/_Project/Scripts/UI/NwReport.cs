using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    public enum ReportKind
    {
        Loss = 0,          // Verlust: nur Name, Warnung-Icon
        Warning = 1,       // Warnung des Verstecks, Versteck-Icon
        GainTalisman = 2,  // Gewinn Talisman
        GainKnowledge = 3, // Gewinn Wissen
    }

    [Serializable]
    public struct ReportLine
    {
        public ReportKind kind;
        public string text;

        public ReportLine(ReportKind kind, string text)
        {
            this.kind = kind;
            this.text = text;
        }
    }

    /// <summary>
    /// Morgenbericht als Dialogbox: Titel, Tag-Zaehler, Verluste, Warnungen, Gewinne, Weiter-Knopf.
    /// Einzige Animation: die Zeilen erscheinen nacheinander (je 0,3 s).
    /// Es werden nur so viele Zeilen gezeigt, wie in die Box passen; der Rest wird als "... und N weitere" zusammengefasst.
    /// </summary>
    public class NwReport : MonoBehaviour
    {
        [SerializeField] Text titleText;
        [SerializeField] Text dayText;
        [SerializeField] RectTransform rows;
        [SerializeField] NwReportRow rowPrefab;
        [SerializeField] NwButton continueButton;
        [SerializeField] float lineDelay = NwTheme.ReportLineDelay;
        [SerializeField] float rowHeight = 20f;
        [SerializeField] float rowSpacing = 4f;

        [Header("Icons")]
        [SerializeField] Sprite iconLoss;
        [SerializeField] Sprite iconWarning;
        [SerializeField] Sprite iconTalisman;
        [SerializeField] Sprite iconKnowledge;

        Coroutine routine;

        public event Action Continued;

        void Awake()
        {
            if (continueButton != null) continueButton.onClick.AddListener(OnContinue);
        }

        int Capacity => Mathf.Max(1, Mathf.FloorToInt((rows.rect.height + rowSpacing) / (rowHeight + rowSpacing)));

        public void Begin(int day, IList<ReportLine> lines)
        {
            gameObject.SetActive(true);
            if (routine != null) StopCoroutine(routine);
            for (int i = rows.childCount - 1; i >= 0; i--) Destroy(rows.GetChild(i).gameObject);
            titleText.text = "";
            dayText.text = "";
            continueButton.gameObject.SetActive(false);

            var sorted = lines.OrderBy(l => (int)l.kind).ToList();   // Reihenfolge: Verluste, Warnungen, Gewinne
            routine = StartCoroutine(Reveal(day, sorted));
        }

        IEnumerator Reveal(int day, List<ReportLine> lines)
        {
            titleText.text = "Morgen in Nightward";
            yield return new WaitForSecondsRealtime(NwTheme.ReportLineDelay);
            dayText.text = "Tag " + day;

            int cap = Capacity;
            int shown = lines.Count <= cap ? lines.Count : cap - 1;
            for (int i = 0; i < shown; i++)
            {
                yield return new WaitForSecondsRealtime(lineDelay);
                var line = lines[i];
                Sprite icon;
                Color color;
                switch (line.kind)
                {
                    case ReportKind.Loss: icon = iconLoss; color = NwTheme.Loss; break;
                    case ReportKind.Warning: icon = iconWarning; color = NwTheme.Warning; break;
                    case ReportKind.GainTalisman: icon = iconTalisman; color = NwTheme.Talisman; break;
                    default: icon = iconKnowledge; color = NwTheme.Knowledge; break;
                }
                AddRow(icon, line.text, color);
            }
            if (shown < lines.Count)
            {
                yield return new WaitForSecondsRealtime(lineDelay);
                AddRow(null, "… und " + (lines.Count - shown) + " weitere", NwTheme.TextDefault);
            }
            yield return new WaitForSecondsRealtime(lineDelay);
            continueButton.gameObject.SetActive(true);
        }

        void AddRow(Sprite icon, string text, Color color)
        {
            var row = Instantiate(rowPrefab, rows);
            row.Set(icon, text, color);
            LayoutRebuilder.ForceRebuildLayoutImmediate(rows);
            row.FitText();
        }

        void OnContinue()
        {
            Continued?.Invoke();
            gameObject.SetActive(false);
        }
    }
}
