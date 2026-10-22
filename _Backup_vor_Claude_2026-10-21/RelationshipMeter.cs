using System.Collections;
using Nightward.UI;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.Dialogue
{
    /// <summary>
    /// Beziehungsleiste unten rechts an der Dialogbox: 21 Segmente (-10 rot, 0 neutral, +10 gruen),
    /// ein Dreieck ueber dem aktuellen Wert und der Name der Stufe daneben.
    /// Bei einer Aenderung springt eine grosse "+1"/"-1"-Zahl hoch, das Dreieck wandert Segment fuer Segment,
    /// die ueberstrichenen Segmente blitzen auf, das Schild huepft (besser) oder wackelt (schlechter).
    /// Bei neuer Stufe wird zusaetzlich der Stufenname eingeblendet. Alles in unskalierter Zeit (laeuft auch bei Pause).
    /// </summary>
    public class RelationshipMeter : MonoBehaviour
    {
        // Masse der Leisten-Grafik (HUD/Beziehung_Leiste.png, siehe build_dialog.py)
        const int SegWidth = 4, SegHeight = 8, SegStep = 5, Border = 2, SegBottom = 4, BarTop = 14;

        [SerializeField] CanvasGroup group;
        [Tooltip("Wackelt/huepft bei Aenderungen")]
        [SerializeField] RectTransform plate;
        [SerializeField] RectTransform bar;
        [SerializeField] RectTransform marker;
        [SerializeField] Image flash;
        [SerializeField] Text label;
        [Header("Aenderung")]
        [SerializeField] RectTransform popup;
        [SerializeField] Text popupText;
        [SerializeField] Text popupTier;
        [SerializeField] float stepTime = 0.12f;
        [SerializeField] float popupTime = 1.4f;
        [SerializeField] float popupRise = 18f;
        [SerializeField] float fadeOutTime = 0.25f;

        static readonly Color Better = Hex("#9ab87a");
        static readonly Color Worse = Hex("#d64a6a");

        NpcGender gender;
        int shown;
        bool visible;
        bool hideWhenDone;
        Coroutine changeRoutine;
        Coroutine popupRoutine;
        Coroutine fadeRoutine;
        Vector2 plateBase;
        Vector2 popupBase;
        Vector2 labelBase;
        float bob;

        public bool IsAnimating => changeRoutine != null || popupRoutine != null;

        static Color Hex(string h)
        {
            ColorUtility.TryParseHtmlString(h, out var c);
            return c;
        }

        void Awake()
        {
            plateBase = plate.anchoredPosition;
            popupBase = popup.anchoredPosition;
            labelBase = label.rectTransform.anchoredPosition;
            popup.gameObject.SetActive(false);
            flash.gameObject.SetActive(false);
            group.alpha = 0f;
            group.blocksRaycasts = false;
        }

        /// <summary>Beim Gespraechsbeginn: aktuellen Stand ohne Animation zeigen.</summary>
        public void Show(NpcProfile profile, int value)
        {
            StopAll();
            gender = profile != null ? profile.gender : NpcGender.Maennlich;
            visible = true;
            hideWhenDone = false;
            group.alpha = 1f;
            SetValue(value);
        }

        /// <summary>Gespraechsende: laeuft gerade eine Aenderung, bleibt die Leiste stehen, bis man sie gesehen hat.</summary>
        public void Hide()
        {
            if (!visible) return;
            if (IsAnimating) { hideWhenDone = true; return; }
            visible = false;
            if (fadeRoutine != null) StopCoroutine(fadeRoutine);
            fadeRoutine = StartCoroutine(FadeOut());
        }

        public void Animate(int from, int to)
        {
            if (from == to) return;
            if (!visible) { visible = true; group.alpha = 1f; }
            if (fadeRoutine != null) { StopCoroutine(fadeRoutine); fadeRoutine = null; group.alpha = 1f; }
            StopAll();
            SetValue(from);

            var tiers = RelationshipTiers.Active;
            var newTier = tiers.Get(to);
            bool tierChanged = tiers.Get(from) != newTier;
            popupRoutine = StartCoroutine(Popup(to - from, tierChanged ? newTier : null));
            changeRoutine = StartCoroutine(Slide(from, to));
        }

        void StopAll()
        {
            StopAllCoroutines();
            changeRoutine = popupRoutine = fadeRoutine = null;
            plate.anchoredPosition = plateBase;
            popup.gameObject.SetActive(false);
            flash.gameObject.SetActive(false);
            label.rectTransform.anchoredPosition = labelBase;
        }

        void SetValue(int value)
        {
            shown = Mathf.Clamp(value, Relationships.Min, Relationships.Max);
            var tier = RelationshipTiers.Active.Get(shown);
            label.text = tier != null ? tier.Label(gender) : "";
            label.color = tier != null ? tier.color : NwTheme.TextDefault;
            PlaceMarker(shown, 0f);
        }

        static float SegmentLeft(int value) => Border + (value - Relationships.Min) * SegStep;

        void PlaceMarker(int value, float yOffset)
        {
            // Dreieck (8 px, Spitze 2 px) mittig ueber dem 4 px breiten Segment, Spitze beruehrt den Rahmen
            marker.anchoredPosition = new Vector2(SegmentLeft(value) - 2f, BarTop - 1f + yOffset);
        }

        void Update()
        {
            if (!visible || changeRoutine != null) return;
            // Dreieck wippt ruhig um einen Pixel
            bob += Time.unscaledDeltaTime;
            PlaceMarker(shown, Mathf.Repeat(bob, 1f) < 0.5f ? 0f : 1f);
        }

        IEnumerator Slide(int from, int to)
        {
            int dir = to > from ? 1 : -1;
            yield return Wait(0.15f);
            for (int v = from + dir; dir > 0 ? v <= to : v >= to; v += dir)
            {
                SetValue(v);
                Flash(v);
                StartCoroutine(Jolt(dir > 0));
                yield return Wait(stepTime);
            }
            flash.gameObject.SetActive(false);
            yield return PulseLabel();
            changeRoutine = null;
            CheckHide();
        }

        void Flash(int value)
        {
            flash.gameObject.SetActive(true);
            flash.rectTransform.anchoredPosition = new Vector2(SegmentLeft(value), SegBottom);
            flash.rectTransform.sizeDelta = new Vector2(SegWidth, SegHeight);
            flash.color = NwTheme.TextDefault;
        }

        // Besser: kurzer Hopser nach oben. Schlechter: zwei Pixel links/rechts wackeln
        IEnumerator Jolt(bool up)
        {
            Vector2[] steps = up
                ? new[] { new Vector2(0f, 2f), new Vector2(0f, 1f), Vector2.zero }
                : new[] { new Vector2(-2f, 0f), new Vector2(2f, 0f), new Vector2(-1f, 0f), Vector2.zero };
            foreach (var s in steps)
            {
                plate.anchoredPosition = plateBase + s;
                yield return Wait(0.04f);
            }
            if (flash.gameObject.activeSelf) flash.color = new Color(1f, 1f, 1f, 0.5f);
        }

        // Pixelschrift nicht skalieren (wuerde unscharf), daher 1 px hoch und runter
        IEnumerator PulseLabel()
        {
            var rt = label.rectTransform;
            for (int i = 0; i < 3; i++)
            {
                rt.anchoredPosition = labelBase + new Vector2(0f, 1f);
                yield return Wait(0.06f);
                rt.anchoredPosition = labelBase;
                yield return Wait(0.06f);
            }
        }

        IEnumerator Popup(int delta, RelationshipTier newTier)
        {
            popup.gameObject.SetActive(true);
            popupText.text = (delta > 0 ? "+" : "") + delta;
            popupText.color = delta > 0 ? Better : Worse;
            bool showTier = newTier != null && popupTier != null;
            if (popupTier != null)
            {
                popupTier.gameObject.SetActive(showTier);
                if (showTier)
                {
                    popupTier.text = (delta > 0 ? "Neu: " : "Jetzt: ") + newTier.Label(gender);
                    popupTier.color = newTier.color;
                }
            }
            var cg = popup.GetComponent<CanvasGroup>();
            float total = showTier ? popupTime + 0.8f : popupTime;
            float t = 0f;
            while (t < total)
            {
                t += Time.unscaledDeltaTime;
                // schnell hoch, dann stehen lassen, am Ende ausblenden. Ganze Pixel, damit die Schrift scharf bleibt
                float rise = Mathf.Round(popupRise * (1f - Mathf.Pow(1f - Mathf.Clamp01(t / 0.35f), 3f)));
                popup.anchoredPosition = popupBase + new Vector2(0f, rise);
                if (cg != null) cg.alpha = Mathf.Clamp01((total - t) / 0.3f);
                yield return null;
            }
            popup.gameObject.SetActive(false);
            popupRoutine = null;
            CheckHide();
        }

        void CheckHide()
        {
            if (!hideWhenDone || IsAnimating) return;
            hideWhenDone = false;
            visible = true; // Hide prueft visible
            Hide();
        }

        IEnumerator FadeOut()
        {
            float t = 0f;
            float start = group.alpha;
            while (t < fadeOutTime)
            {
                t += Time.unscaledDeltaTime;
                group.alpha = Mathf.Lerp(start, 0f, t / fadeOutTime);
                yield return null;
            }
            group.alpha = 0f;
            fadeRoutine = null;
        }

        static IEnumerator Wait(float seconds)
        {
            float t = 0f;
            while (t < seconds) { t += Time.unscaledDeltaTime; yield return null; }
        }
    }
}
