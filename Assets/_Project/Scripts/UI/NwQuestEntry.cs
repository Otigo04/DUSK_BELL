using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>Eine Quest-Zeile: Marke (verfolgt), Statuspunkt, Text, optional Fortschrittsbalken (40x5).</summary>
    public class NwQuestEntry : MonoBehaviour
    {
        const float TextWidth = 124f;

        [SerializeField] Image tracked;
        [SerializeField] Image dot;
        [SerializeField] Text label;
        [SerializeField] GameObject progressRoot;
        [SerializeField] Image progressFill;
        [SerializeField] LayoutElement layout;
        [SerializeField] Sprite dotOpen;
        [SerializeField] Sprite dotActive;
        [SerializeField] Sprite dotDone;
        [SerializeField] Sprite dotFailed;

        /// <summary>progress &lt; 0 = kein Balken.</summary>
        public void Setup(string text, QuestState state, bool isTracked, float progress = -1f)
        {
            tracked.enabled = isTracked;
            switch (state)
            {
                case QuestState.Active: dot.sprite = dotActive; label.color = NwTheme.TextDefault; break;
                case QuestState.Done: dot.sprite = dotDone; label.color = NwTheme.TextDim; break;
                case QuestState.Failed: dot.sprite = dotFailed; label.color = NwTheme.Loss; break;
                default: dot.sprite = dotOpen; label.color = NwTheme.TextDefault; break;
            }
            NwTextFit.Fit(label, text, TextWidth, NwTheme.FontHint, NwTheme.FontHint);
            bool bar = progress >= 0f;
            progressRoot.SetActive(bar);
            if (bar) progressFill.fillAmount = Mathf.Round(Mathf.Clamp01(progress) * 38f) / 38f;
            layout.preferredHeight = bar ? 21f : 12f;
        }
    }
}
