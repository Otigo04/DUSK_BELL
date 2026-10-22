using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Nightward.Opening
{
    /// <summary>
    /// Bildschirm-Elemente der Opening Sequence. Alle Texte erscheinen wie mit der Schreibmaschine (Buchstabe fuer Buchstabe),
    /// damit der Spieler merkt, dass gerade etwas steht. Erzaehlung, Hinweise und Sprechblasen sind Koroutinen, die erst
    /// enden, wenn der Text gelesen werden konnte: so kommt alles nacheinander statt gleichzeitig.
    /// Keine Spiellogik, die steuert der OpeningDirector.
    /// </summary>
    public class OpeningUI : MonoBehaviour
    {
        [SerializeField] OpeningAudio audioPlayer;
        [Tooltip("Buchstaben pro Sekunde fuer Erzaehler und Hinweise")]
        [SerializeField] float typeSpeed = 20f;
        [Tooltip("Buchstaben pro Sekunde im schwarzen Intro (langsam)")]
        [SerializeField] float introTypeSpeed = 15f;

        [Header("Ueberblendung")]
        [SerializeField] Image fade;
        [SerializeField] float fadeTime = 0.5f;

        [Header("Hintergrund (Innenraum ohne Karte)")]
        [SerializeField] GameObject backdrop;

        [Header("Intro (Step 2)")]
        [SerializeField] CanvasGroup introPanel;
        [SerializeField] Text introLine;
        [SerializeField] Text introTitle;

        [Header("Erzaehler / Gedanken unten")]
        [SerializeField] CanvasGroup subtitleGroup;
        [SerializeField] Text subtitle;

        [Header("Hinweis oben (Tutorial, Fund)")]
        [SerializeField] CanvasGroup toastGroup;
        [SerializeField] Text toast;

        [Header("Sprechblase")]
        [SerializeField] RectTransform bubble;
        [SerializeField] Text bubbleText;
        [SerializeField] Vector3 bubbleOffset = new Vector3(0f, 1.9f, 0f);

        [Header("Fortschritt (ueber der Figur)")]
        [SerializeField] RectTransform progressRoot;
        [SerializeField] Image progressFill;
        [SerializeField] Text progressLabel;

        [Header("Zettel")]
        [SerializeField] CanvasGroup paperGroup;
        [SerializeField] Text paperText;
        [SerializeField] UI.NwButton paperClose;

        [Header("Tacho")]
        [SerializeField] GameObject gaugeRoot;
        [SerializeField] RectTransform needle;
        [SerializeField] Text odometerText;

        [Header("Ende")]
        [SerializeField] CanvasGroup endGroup;
        [SerializeField] Text endText;

        RectTransform canvasRect;
        Transform bubbleTarget, progressTarget;
        bool paperClosed;
        bool toastBusy, toastAbort;
        readonly Dictionary<CanvasGroup, int> fadeToken = new Dictionary<CanvasGroup, int>();

        public bool IntroSkipped { get; private set; }

        void Awake()
        {
            canvasRect = (RectTransform)transform;
            SetAlpha(introPanel, 0f);
            SetAlpha(subtitleGroup, 0f);
            SetAlpha(toastGroup, 0f);
            SetAlpha(paperGroup, 0f);
            SetAlpha(endGroup, 0f);
            progressRoot.gameObject.SetActive(false);
            bubble.gameObject.SetActive(false);
            gaugeRoot.SetActive(false);
            if (backdrop != null) backdrop.SetActive(false);
            if (paperClose != null) paperClose.onClick.AddListener(() => paperClosed = true);
            SetFade(1f);
        }

        static void SetAlpha(CanvasGroup g, float a)
        {
            if (g == null) return;
            g.alpha = a;
            g.blocksRaycasts = a > 0.5f;
            g.gameObject.SetActive(a > 0f);
        }

        void LateUpdate()
        {
            Follow(bubble, bubbleTarget, bubbleOffset);
            Follow(progressRoot, progressTarget, new Vector3(0f, 1.75f, 0f));
        }

        void Follow(RectTransform rt, Transform target, Vector3 offset)
        {
            if (target == null || !rt.gameObject.activeSelf) return;
            var cam = Camera.main;
            Vector2 screen = cam.WorldToScreenPoint(target.position + offset);
            RectTransformUtility.ScreenPointToLocalPointInRectangle(canvasRect, screen, null, out var local);
            rt.anchoredPosition = new Vector2(Mathf.Round(local.x), Mathf.Round(local.y));
        }

        // ------------------------------------------------------------ Schreibmaschine

        /// <summary>Tippt text in t. Mit skippable bricht Enter den Vorgang ab (nur Intro).</summary>
        IEnumerator Type(Text t, string text, float cps, bool skippable = false)
        {
            t.text = "";
            float shown = 0f;
            int last = 0;
            while (last < text.Length)
            {
                if (skippable && CheckSkip()) { t.text = text; yield break; }
                shown += cps * Time.deltaTime;
                int n = Mathf.Min(text.Length, Mathf.FloorToInt(shown));
                if (n > last)
                {
                    // Leiser Anschlag etwa jeden zweiten Buchstaben, nicht bei Leerzeichen
                    if (audioPlayer != null && text[n - 1] != ' ' && n % 2 == 0) audioPlayer.Tick();
                    last = n;
                    t.text = text.Substring(0, n);
                }
                yield return null;
            }
        }

        /// <summary>Lesedauer nach dem Tippen (mitgelesen wird schon beim Tippen): etwa 18 Zeichen pro Sekunde, mindestens 2,2 s.</summary>
        public static float ReadTime(string text) => Mathf.Max(2.2f, text.Length / 18f);

        // ------------------------------------------------------------ Ueberblendung

        public void SetFade(float a)
        {
            fade.gameObject.SetActive(a > 0f);
            fade.color = new Color(0f, 0f, 0f, a);
        }

        public IEnumerator FadeOut() => FadeTo(1f, fadeTime);
        public IEnumerator FadeIn() => FadeTo(0f, fadeTime);

        public IEnumerator FadeTo(float target, float time)
        {
            float start = fade.color.a;
            fade.gameObject.SetActive(true);
            for (float t = 0f; t < time; t += Time.deltaTime)
            {
                SetFade(Mathf.Lerp(start, target, t / time));
                yield return null;
            }
            SetFade(target);
        }

        public void Backdrop(bool visible) { if (backdrop != null) backdrop.SetActive(visible); }

        // ------------------------------------------------------------ Step 2

        /// <summary>Jede Zeile wird langsam getippt, bleibt 3 s und blendet 1 s aus. Danach der Titel. Enter ueberspringt.</summary>
        public IEnumerator PlayIntro(string[] lines, string title, float hold = 3f, float fadeOutTime = 1f)
        {
            IntroSkipped = false;
            SetAlpha(introPanel, 1f);
            introTitle.color = Alpha(introTitle.color, 0f);
            introLine.color = Alpha(introLine.color, 1f);
            yield return FadeTo(0f, 0.8f);

            foreach (var line in lines)
            {
                introLine.color = Alpha(introLine.color, 1f);
                yield return Type(introLine, line, introTypeSpeed, skippable: true);
                if (IntroSkipped) break;
                yield return Wait(hold);
                if (IntroSkipped) break;
                yield return Fade(introLine, 1f, 0f, fadeOutTime);
                if (IntroSkipped) break;
                yield return Wait(0.4f);
                if (IntroSkipped) break;
            }
            if (!IntroSkipped)
            {
                introLine.text = "";
                introTitle.text = title;
                yield return Fade(introTitle, 0f, 1f, 2f);
                if (!IntroSkipped) yield return Wait(3f);
                if (!IntroSkipped) yield return Fade(introTitle, 1f, 0f, 2f);
            }
            yield return FadeTo(1f, IntroSkipped ? 0.3f : 0.8f);
            SetAlpha(introPanel, 0f);
        }

        IEnumerator Fade(Text text, float from, float to, float time)
        {
            for (float t = 0f; t < time; t += Time.deltaTime)
            {
                if (CheckSkip()) yield break;
                text.color = Alpha(text.color, Mathf.Lerp(from, to, t / time));
                yield return null;
            }
            text.color = Alpha(text.color, to);
        }

        IEnumerator Wait(float time)
        {
            for (float t = 0f; t < time; t += Time.deltaTime)
            {
                if (CheckSkip()) yield break;
                yield return null;
            }
        }

        bool CheckSkip()
        {
            var kb = Keyboard.current;
            if (kb != null && (kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame)) IntroSkipped = true;
            return IntroSkipped;
        }

        static Color Alpha(Color c, float a) { c.a = a; return c; }

        // ------------------------------------------------------------ Erzaehler unten

        /// <summary>Erzaehler- oder Gedankenzeile: tippt, bleibt zum Lesen stehen, blendet aus. Endet erst danach.</summary>
        public IEnumerator Narrate(string text, bool thought = false, float extraHold = 0f)
        {
            subtitle.fontStyle = thought ? FontStyle.Italic : FontStyle.Normal;
            subtitle.text = "";     // sonst blitzt kurz der alte Text auf, bevor der neue getippt wird
            yield return ShowGroup(subtitleGroup, true);
            yield return Type(subtitle, text, typeSpeed);
            yield return new WaitForSeconds(ReadTime(text) + extraHold);
            yield return ShowGroup(subtitleGroup, false);
        }

        /// <summary>Erzaehlerzeile, die stehen bleibt, bis HideSubtitle (z. B. waehrend der Spieler etwas tun soll).</summary>
        public IEnumerator NarrateAndKeep(string text)
        {
            subtitle.fontStyle = FontStyle.Normal;
            subtitle.text = "";
            yield return ShowGroup(subtitleGroup, true);
            yield return Type(subtitle, text, typeSpeed);
        }

        public void HideSubtitle() => StartCoroutine(ShowGroup(subtitleGroup, false));

        IEnumerator ShowGroup(CanvasGroup g, bool show)
        {
            if (show == (g.gameObject.activeSelf && g.alpha > 0.99f)) yield break;
            // Ein neuer Vorgang bricht einen noch laufenden auf derselben Gruppe ab (sonst kaempfen beide um die Transparenz)
            fadeToken.TryGetValue(g, out int token);
            int mine = fadeToken[g] = token + 1;
            g.gameObject.SetActive(true);
            g.blocksRaycasts = false;
            float from = g.alpha, to = show ? 1f : 0f;
            for (float t = 0f; t < 0.25f; t += Time.deltaTime)
            {
                if (fadeToken[g] != mine) yield break;
                g.alpha = Mathf.Lerp(from, to, t / 0.25f);
                yield return null;
            }
            if (fadeToken[g] != mine) yield break;
            g.alpha = to;
            if (!show) g.gameObject.SetActive(false);
        }

        // ------------------------------------------------------------ Hinweis oben

        /// <summary>Tutorial-Hinweis: tippt, steht seconds lang, blendet aus. Endet danach. Mehrere Hinweise laufen nacheinander.</summary>
        public IEnumerator Hint(string text, float seconds = 3f)
        {
            while (toastBusy) yield return null;
            toastBusy = true;
            toastAbort = false;
            toast.text = "";        // sonst blitzt kurz der alte Hinweis auf
            yield return ShowGroup(toastGroup, true);
            yield return Type(toast, text, typeSpeed);
            for (float t = 0f; t < seconds && !toastAbort; t += Time.deltaTime) yield return null;
            yield return ShowGroup(toastGroup, false);
            toastBusy = false;
        }

        /// <summary>Beendet den gerade sichtbaren Hinweis vorzeitig (z. B. wenn der Spieler schon handelt).</summary>
        public void AbortHint() => toastAbort = true;

        // ------------------------------------------------------------ Sprechblase

        /// <summary>Sprechblase ueber einer Figur: tippt, bleibt zum Lesen, verschwindet. Immer nur eine zur Zeit.</summary>
        public IEnumerator Bubble(Transform speaker, string text, float extraHold = 0.4f)
        {
            bubbleTarget = speaker;
            bubbleText.text = "";
            float w = Mathf.Clamp(UI.NwTextFit.Width(bubbleText, text) + 16f, 40f, 160f);
            bubble.sizeDelta = new Vector2(w, bubble.sizeDelta.y);
            bubble.gameObject.SetActive(true);
            Follow(bubble, speaker, bubbleOffset);
            yield return Type(bubbleText, text, typeSpeed * 0.8f);
            yield return new WaitForSeconds(ReadTime(text) + extraHold);
            bubble.gameObject.SetActive(false);
            bubbleTarget = null;
        }

        public void HideBubble()
        {
            bubble.gameObject.SetActive(false);
            bubbleTarget = null;
        }

        // ------------------------------------------------------------ Fortschritt

        public void Progress(float value01, string label, Transform above = null)
        {
            progressRoot.gameObject.SetActive(value01 >= 0f);
            if (value01 < 0f) { progressTarget = null; return; }
            if (above != null) progressTarget = above;
            progressFill.fillAmount = Mathf.Clamp01(value01);
            // Punkte laufen mit, damit man sieht, dass etwas passiert
            int dots = 1 + (int)(Time.time * 2f) % 3;
            progressLabel.text = label + new string('.', dots);
            Follow(progressRoot, progressTarget, new Vector3(0f, 1.75f, 0f));
        }

        // ------------------------------------------------------------ Zettel

        /// <summary>Zeigt den Zettel (nur der handschriftliche Inhalt), bis F / Esc / Enter / Leertaste oder der Button ihn schliesst.</summary>
        public IEnumerator ShowPaper(string[] entries)
        {
            paperText.text = string.Join("\n", entries);
            paperClosed = false;
            yield return ShowGroup(paperGroup, true);
            paperGroup.blocksRaycasts = true;
            yield return null;
            while (!paperClosed)
            {
                var kb = Keyboard.current;
                if (kb != null && (kb.fKey.wasPressedThisFrame || kb.enterKey.wasPressedThisFrame
                                   || kb.spaceKey.wasPressedThisFrame || kb.escapeKey.wasPressedThisFrame)) break;
                yield return null;
            }
            paperGroup.blocksRaycasts = false;
            yield return ShowGroup(paperGroup, false);
        }

        // ------------------------------------------------------------ Tacho

        /// <summary>Kleiner Tacho unten links: Nadel nach Tempo (0..1), darunter fein der Kilometerstand.</summary>
        public void Gauge(bool visible, float speed01 = 0f, string odometer = null, bool highlight = false)
        {
            gaugeRoot.SetActive(visible);
            if (!visible) return;
            float angle = Mathf.Lerp(80f, -80f, Mathf.Clamp01(speed01));
            needle.localRotation = Quaternion.Lerp(needle.localRotation, Quaternion.Euler(0f, 0f, angle), Time.deltaTime * 8f);
            if (odometer != null) odometerText.text = odometer;
            odometerText.color = highlight ? UI.NwTheme.Title : new Color(0.91f, 0.88f, 0.94f, 0.85f);
        }

        // ------------------------------------------------------------ Ende

        public IEnumerator ShowEnd(string text)
        {
            endText.text = "";
            endGroup.gameObject.SetActive(true);
            endGroup.alpha = 1f;
            yield return Type(endText, text, introTypeSpeed);
        }
    }
}
