using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Eine Antwortzeile im Dialog: flacher Text ohne Buttonrahmen. Die gewaehlte Zeile bekommt
    /// einen Pfeil, einen dezenten Streifen und Warmgelb. Wird zur Laufzeit von der DialogueView gebaut.
    /// </summary>
    public class NwChoiceRow : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler
    {
        public const float Height = 16f;
        const float TextLeft = 16f;

        Image stripe;
        Image marker;
        Text label;
        int fontSize = NwTheme.FontMenu;
        bool over;
        bool highlighted;

        public Text Label => label;

        /// <summary>Setzt den Text in voller Schriftgroesse und bricht bei Platzmangel auf max. zwei Zeilen um.</summary>
        public void SetText(string text, float rowWidth)
        {
            float width = rowWidth - TextLeft - 6f;
            label.fontSize = fontSize;
            label.horizontalOverflow = HorizontalWrapMode.Wrap;
            label.verticalOverflow = VerticalWrapMode.Truncate;
            label.text = text;
            var settings = label.GetGenerationSettings(new Vector2(width, 0f));
            float h = label.cachedTextGeneratorForLayout.GetPreferredHeight(text, settings) / label.pixelsPerUnit;
            float rowHeight = Mathf.Clamp(Mathf.Ceil(h) + 4f, Height, 2f * Height + 4f);
            var le = GetComponent<LayoutElement>();
            le.minHeight = le.preferredHeight = rowHeight;
        }
        public readonly UnityEvent onClick = new UnityEvent();

        public bool Highlighted
        {
            get => highlighted;
            set { highlighted = value; Refresh(); }
        }

        public static NwChoiceRow Create(Transform parent, Font font, Sprite markerSprite, int fontSize)
        {
            var go = new GameObject("Antwort", typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var row = go.AddComponent<NwChoiceRow>();
            row.fontSize = fontSize;
            var le = go.AddComponent<LayoutElement>();
            le.minHeight = le.preferredHeight = Height;

            row.stripe = go.AddComponent<Image>();
            row.stripe.raycastTarget = true;

            var m = new GameObject("Marker", typeof(RectTransform));
            m.transform.SetParent(go.transform, false);
            var mrt = (RectTransform)m.transform;
            mrt.anchorMin = mrt.anchorMax = new Vector2(0f, 0.5f);
            mrt.pivot = new Vector2(0.5f, 0.5f);
            mrt.anchoredPosition = new Vector2(8f, 0f);
            mrt.sizeDelta = new Vector2(9f, 6f);
            mrt.localRotation = Quaternion.Euler(0f, 0f, 90f); // Weiterpfeil zeigt nach unten, hier nach rechts
            row.marker = m.AddComponent<Image>();
            row.marker.sprite = markerSprite;
            row.marker.raycastTarget = false;
            row.marker.color = NwTheme.Arrow;

            var t = new GameObject("Text", typeof(RectTransform));
            t.transform.SetParent(go.transform, false);
            var trt = (RectTransform)t.transform;
            trt.anchorMin = Vector2.zero;
            trt.anchorMax = Vector2.one;
            trt.offsetMin = new Vector2(TextLeft, 0f);
            trt.offsetMax = new Vector2(-6f, 0f);
            row.label = t.AddComponent<Text>();
            row.label.font = font;
            row.label.fontSize = fontSize;
            row.label.alignment = TextAnchor.MiddleLeft;
            row.label.horizontalOverflow = HorizontalWrapMode.Overflow;
            row.label.verticalOverflow = VerticalWrapMode.Truncate;
            row.label.raycastTarget = false;
            var sh = t.AddComponent<Shadow>();
            sh.effectColor = NwTheme.TextShadow;
            sh.effectDistance = new Vector2(1f, -1f);

            row.Refresh();
            return row;
        }

        public void OnPointerEnter(PointerEventData e) { over = true; Refresh(); }
        public void OnPointerExit(PointerEventData e) { over = false; Refresh(); }

        public void OnPointerClick(PointerEventData e)
        {
            if (e.button == PointerEventData.InputButton.Left) onClick.Invoke();
        }

        void Refresh()
        {
            bool on = highlighted || over;
            // Streifen bleibt als Raycast-Ziel aktiv und wird nur transparent (ein deaktiviertes Image bekommt kein Hover)
            if (stripe != null)
            {
                var c = NwTheme.Title;
                stripe.color = new Color(c.r, c.g, c.b, on ? 0.12f : 0f);
            }
            if (marker != null) marker.enabled = on;
            if (label != null) label.color = on ? NwTheme.ButtonTextHover : NwTheme.ButtonTextNormal;
        }
    }
}
