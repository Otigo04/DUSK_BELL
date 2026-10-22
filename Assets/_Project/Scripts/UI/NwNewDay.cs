using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    public enum NightEventKind
    {
        Quiet = 0,        // ruhige Nacht (Haus)
        Loss = 1,         // Verlust, nur der Name (rot)
        Remembrance = 2,  // Gedenken (Kerze)
        Bell = 3,         // Glocke
        Wounded = 4,      // Verletzt
        Warning = 5,      // Versteck regt sich
        Talisman = 6,     // +Talisman
        Knowledge = 7,    // +Wissen
    }

    [Serializable]
    public struct NightEvent
    {
        public NightEventKind kind;
        public string text;

        public NightEvent(NightEventKind kind, string text)
        {
            this.kind = kind;
            this.text = text;
        }
    }

    /// <summary>
    /// Neuer-Tag-Banner (nach dem Schlafen: Morgen-Variante, nach 00:00: Mitternachts-Variante), ca. 4 s, danach der
    /// Bericht der letzten Nacht im Dorf. Time.timeScale wird nicht angefasst, alle Zeiten laufen unscaled.
    /// </summary>
    [RequireComponent(typeof(CanvasGroup))]
    public class NwNewDay : MonoBehaviour
    {
        [Header("Banner")]
        [SerializeField] RectTransform bannerRoot;
        [SerializeField] Image band;
        [SerializeField] Image skyline;
        [SerializeField] GameObject rays;
        [SerializeField] Text titleText;
        [SerializeField] Text subtitleText;
        [SerializeField] Sprite bandMorning;
        [SerializeField] Sprite bandMidnight;
        [SerializeField] Sprite skylineMorning;
        [SerializeField] Sprite skylineMidnight;
        [SerializeField] float bannerTime = 4f;
        [SerializeField] float fadeTime = 0.4f;

        [Header("Bericht")]
        [SerializeField] RectTransform report;
        [SerializeField] Text reportTitle;
        [SerializeField] RectTransform rows;
        [SerializeField] NwReportRow rowPrefab;
        [SerializeField] NwButton continueButton;
        [SerializeField] float rowHeight = 16f;
        [SerializeField] float rowSpacing = 1f;

        [Header("Symbole")]
        [SerializeField] Sprite iconQuiet;
        [SerializeField] Sprite iconLoss;
        [SerializeField] Sprite iconRemembrance;
        [SerializeField] Sprite iconBell;
        [SerializeField] Sprite iconWounded;
        [SerializeField] Sprite iconWarning;
        [SerializeField] Sprite iconTalisman;
        [SerializeField] Sprite iconKnowledge;

        CanvasGroup group;
        Coroutine routine;

        public event Action Continued;
        public bool IsShowing => gameObject.activeSelf && group != null && group.alpha > 0f;

        void Awake()
        {
            group = GetComponent<CanvasGroup>();
            if (continueButton != null) continueButton.onClick.AddListener(OnContinue);
        }

        int Capacity => Mathf.Max(1, Mathf.FloorToInt((rows.rect.height + rowSpacing) / (rowHeight + rowSpacing)));

        /// <summary>events == null: nur der Banner, kein Bericht. Leere Liste: "ruhige Nacht".</summary>
        public void Show(int day, bool midnight, IList<NightEvent> events, string subtitle = null)
        {
            gameObject.SetActive(true);
            if (routine != null) StopCoroutine(routine);

            band.sprite = midnight ? bandMidnight : bandMorning;
            skyline.sprite = midnight ? skylineMidnight : skylineMorning;
            rays.SetActive(!midnight);
            titleText.text = "DAY " + day;
            subtitleText.text = subtitle ?? (midnight ? "Midnight. The bell has tolled." : "Dawn breaks over Dusk Bell.");
            report.gameObject.SetActive(false);
            bannerRoot.gameObject.SetActive(true);
            group.blocksRaycasts = true;
            routine = StartCoroutine(Run(events));
        }

        IEnumerator Run(IList<NightEvent> events)
        {
            yield return Fade(0f, 1f);
            yield return new WaitForSecondsRealtime(bannerTime);
            if (events == null)
            {
                yield return Fade(1f, 0f);
                Close();
                yield break;
            }
            bannerRoot.gameObject.SetActive(false);
            yield return ShowReport(events);
        }

        IEnumerator ShowReport(IList<NightEvent> events)
        {
            for (int i = rows.childCount - 1; i >= 0; i--) Destroy(rows.GetChild(i).gameObject);
            continueButton.gameObject.SetActive(false);
            reportTitle.text = "Last night in Dusk Bell";
            report.gameObject.SetActive(true);

            var list = events.Count == 0
                ? new List<NightEvent> { new NightEvent(NightEventKind.Quiet, "The night was quiet. Nothing stirred.") }
                : events.OrderBy(e => (int)e.kind).ToList();

            int cap = Capacity;
            int shown = list.Count <= cap ? list.Count : cap - 1;
            for (int i = 0; i < shown; i++)
            {
                yield return new WaitForSecondsRealtime(NwTheme.ReportLineDelay);
                AddRow(list[i].kind, list[i].text);
            }
            if (shown < list.Count)
            {
                yield return new WaitForSecondsRealtime(NwTheme.ReportLineDelay);
                AddRow(null, "... and " + (list.Count - shown) + " more", NwTheme.TextDefault);
            }
            yield return new WaitForSecondsRealtime(NwTheme.ReportLineDelay);
            continueButton.gameObject.SetActive(true);
        }

        void AddRow(NightEventKind kind, string text)
        {
            Sprite icon;
            Color color;
            switch (kind)
            {
                case NightEventKind.Loss: icon = iconLoss; color = NwTheme.Loss; break;
                case NightEventKind.Remembrance: icon = iconRemembrance; color = NwTheme.TextDefault; break;
                case NightEventKind.Bell: icon = iconBell; color = NwTheme.Title; break;
                case NightEventKind.Wounded: icon = iconWounded; color = NwTheme.Loss; break;
                case NightEventKind.Warning: icon = iconWarning; color = NwTheme.Warning; break;
                case NightEventKind.Talisman: icon = iconTalisman; color = NwTheme.Talisman; break;
                case NightEventKind.Knowledge: icon = iconKnowledge; color = NwTheme.Knowledge; break;
                default: icon = iconQuiet; color = NwTheme.TextDefault; break;
            }
            AddRow(icon, text, color);
        }

        void AddRow(Sprite icon, string text, Color color)
        {
            var row = Instantiate(rowPrefab, rows);
            var le = row.GetComponent<LayoutElement>();
            le.preferredHeight = rowHeight;
            le.minHeight = rowHeight;
            row.Set(icon, text, color);
            LayoutRebuilder.ForceRebuildLayoutImmediate(rows);
            row.FitText(NwTheme.FontHint, NwTheme.FontHint);
        }

        IEnumerator Fade(float from, float to)
        {
            for (float t = 0f; t < fadeTime; t += Time.unscaledDeltaTime)
            {
                group.alpha = Mathf.Lerp(from, to, t / fadeTime);
                yield return null;
            }
            group.alpha = to;
        }

        void OnContinue()
        {
            Continued?.Invoke();
            Close();
        }

        void Close()
        {
            group.blocksRaycasts = false;
            gameObject.SetActive(false);
        }
    }
}
