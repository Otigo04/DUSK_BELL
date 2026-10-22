using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Dialogbox mit Schreibmaschinen-Effekt. Bewohner: Name in Warmgelb (oder eigener Namensfarbe), Text kerzenweiss.
    /// Erzaehler: kein Name, Text in Blattlicht, dafuer mehr Platz.
    /// Lange Texte werden in Seiten geteilt, die genau in die Box passen. Der Text laeuft nie aus der Box:
    /// Klick blaettert, der Weiterpfeil blinkt am Seitenende.
    /// </summary>
    public class NwDialogBox : MonoBehaviour, IPointerClickHandler
    {
        [SerializeField] Text nameText;
        [SerializeField] Text bodyText;
        [SerializeField] RectTransform bodyRect;
        [SerializeField] Graphic arrow;
        [SerializeField] float charsPerSecond = 24f;
        [Tooltip("Abstand der Textflaeche zum oberen Rand: mit Name / ohne Name")]
        [SerializeField] float bodyTopWithName = 30f;
        [SerializeField] float bodyTopNoName = 12f;
        [Tooltip("Schriftgroesse fuer Name und Text (die Pixelschrift ist nur in ganzzahligen Vielfachen ihres Rasters scharf)")]
        [SerializeField] int nameSize = NwTheme.FontMenu;
        [SerializeField] int bodySize = NwTheme.FontMenu;
        [Header("Namensschild (optional)")]
        [Tooltip("Schild, das oben aus der Box ragt und den Namen traegt. Leer = Name steht in der Box")]
        [SerializeField] RectTransform namePlate;
        [Tooltip("Rahmen des Schilds, wird in der Namensfarbe eingefaerbt")]
        [SerializeField] Graphic namePlateFrame;
        [SerializeField] float namePlatePadding = 8f;
        [SerializeField] float namePlateMinWidth = 36f;

        readonly List<string> pages = new List<string>();
        int page;
        Coroutine routine;
        TextGenerator measure;
        float baseBottom;
        bool baseKnown;
        Vector2 plateLeft;
        bool plateKnown;
        string lastSpeaker;
        Coroutine plateRoutine;
        float pendingDelay;

        /// <summary>Aus, wenn der Aufrufer Klicks selbst auswertet (z. B. ein Klick irgendwo auf dem Bildschirm).</summary>
        public bool ClickEnabled { get; set; } = true;

        public bool IsTyping { get; private set; }
        /// <summary>Wartezeit vor dem Tippen (z. B. kurze Atempause des Sprechers). Name und Box stehen schon da, ein Klick ueberspringt sie.</summary>
        public bool IsDelaying { get; private set; }
        public int PageCount => pages.Count;

        /// <summary>Klick/Weiter, nachdem die letzte Seite fertig ist.</summary>
        public event Action Advance;

        /// <summary>Bewohner oder Figur: Name in nameColor (nie eine Monsterfarbe).
        /// plateRight: Namensschild rechts statt links, z. B. wenn der Spieler selbst spricht.</summary>
        public void ShowResident(string speaker, Color nameColor, string line, float reserveBottom = 0f, bool plateRight = false, float startDelay = 0f)
        {
            nameText.gameObject.SetActive(true);
            nameText.color = nameColor;
            if (namePlate == null) NwTextFit.Fit(nameText, speaker, nameText.rectTransform.rect.width, nameSize, Mathf.Min(nameSize, NwTheme.FontHint));
            Begin(line, NwTheme.TextDefault, bodyTopWithName, reserveBottom, startDelay);
            if (namePlate != null) ShowPlate(speaker, nameColor, plateRight);
        }

        void ShowPlate(string speaker, Color color, bool right)
        {
            if (!plateKnown) { plateLeft = namePlate.anchoredPosition; plateKnown = true; }
            namePlate.gameObject.SetActive(true);
            nameText.horizontalOverflow = HorizontalWrapMode.Overflow;
            nameText.fontSize = nameSize;
            nameText.text = speaker;
            float width = Mathf.Max(namePlateMinWidth, Mathf.Ceil(NwTextFit.Width(nameText, speaker)) + 2f * namePlatePadding);
            namePlate.sizeDelta = new Vector2(width, namePlate.sizeDelta.y);
            // Links: Pivot links an der linken Boxkante. Rechts: gespiegelt an der rechten Kante
            float x = right ? 1f : 0f;
            namePlate.anchorMin = new Vector2(x, namePlate.anchorMin.y);
            namePlate.anchorMax = new Vector2(x, namePlate.anchorMax.y);
            namePlate.pivot = new Vector2(x, namePlate.pivot.y);
            Vector2 basePos = new Vector2(right ? -plateLeft.x : plateLeft.x, plateLeft.y);
            namePlate.anchoredPosition = basePos;
            if (namePlateFrame != null) namePlateFrame.color = color;

            // Sprecherwechsel: Schild springt kurz hoch, damit man sieht, dass jemand anderes redet
            if (speaker != lastSpeaker && gameObject.activeInHierarchy)
            {
                if (plateRoutine != null) StopCoroutine(plateRoutine);
                plateRoutine = StartCoroutine(Hop(basePos));
            }
            lastSpeaker = speaker;
        }

        IEnumerator Hop(Vector2 basePos)
        {
            float[] offsets = { 3f, 2f, 1f, 0f };
            foreach (float o in offsets)
            {
                namePlate.anchoredPosition = basePos + new Vector2(0f, o);
                float t = 0f;
                while (t < 0.04f) { t += Time.unscaledDeltaTime; yield return null; }
            }
            plateRoutine = null;
        }

        public void ShowResident(string speaker, string line) => ShowResident(speaker, NwTheme.Title, line);

        public void ShowNarrator(string line, float reserveBottom = 0f, float startDelay = 0f)
        {
            nameText.gameObject.SetActive(false);
            if (namePlate != null) namePlate.gameObject.SetActive(false);
            lastSpeaker = null;
            Begin(line, NwTheme.Narrator, bodyTopNoName, reserveBottom, startDelay);
        }

        public void Hide()
        {
            if (routine != null) StopCoroutine(routine);
            IsTyping = false;
            IsDelaying = false;
            if (namePlate != null) namePlate.gameObject.SetActive(false);
            lastSpeaker = null;
            gameObject.SetActive(false);
        }

        /// <summary>reserveBottom: Platz unter dem Text, den z. B. die Antwortliste braucht. Die Seiten werden darauf zugeschnitten.</summary>
        void Begin(string line, Color bodyColor, float top, float reserveBottom, float startDelay = 0f)
        {
            gameObject.SetActive(true);
            if (routine != null) StopCoroutine(routine);
            bodyText.color = bodyColor;
            bodyText.fontSize = bodySize;
            bodyText.verticalOverflow = VerticalWrapMode.Truncate;
            bodyText.horizontalOverflow = HorizontalWrapMode.Wrap;
            if (!baseKnown) { baseBottom = bodyRect.offsetMin.y; baseKnown = true; }
            bodyRect.offsetMin = new Vector2(bodyRect.offsetMin.x, baseBottom + reserveBottom);
            bodyRect.offsetMax = new Vector2(bodyRect.offsetMax.x, -top);
            Paginate(line);
            page = 0;
            pendingDelay = startDelay;
            StartPage();
        }

        /// <summary>Teilt den Text in Seiten, die komplett in die Textflaeche passen (an Wortgrenzen).</summary>
        void Paginate(string text)
        {
            pages.Clear();
            if (measure == null) measure = new TextGenerator();
            var settings = bodyText.GetGenerationSettings(bodyText.rectTransform.rect.size);
            settings.verticalOverflow = VerticalWrapMode.Truncate;
            settings.horizontalOverflow = HorizontalWrapMode.Wrap;

            string rest = (text ?? "").Trim();
            for (int guard = 0; rest.Length > 0 && guard < 128; guard++)
            {
                measure.Populate(rest, settings);
                int fit = measure.characterCountVisible;
                if (fit >= rest.Length) { pages.Add(rest); rest = ""; break; }

                int cut = Mathf.Max(1, fit);
                int sp = rest.LastIndexOfAny(new[] { ' ', '\n' }, Mathf.Min(cut, rest.Length - 1));
                if (sp <= 0) sp = cut;
                pages.Add(rest.Substring(0, sp).TrimEnd());
                rest = rest.Substring(sp).TrimStart();
            }
            if (pages.Count == 0) pages.Add("");
        }

        void StartPage()
        {
            if (routine != null) StopCoroutine(routine);
            bodyText.text = "";
            arrow.gameObject.SetActive(false);
            routine = StartCoroutine(Type(pages[page], pendingDelay));
            pendingDelay = 0f;
        }

        IEnumerator Type(string full, float delay)
        {
            IsTyping = true;
            if (delay > 0f)
            {
                IsDelaying = true;
                for (float t = 0f; t < delay; t += Time.unscaledDeltaTime) yield return null;
                IsDelaying = false;
            }
            float shown = 0f;
            while (shown < full.Length)
            {
                shown += charsPerSecond * Time.unscaledDeltaTime;
                bodyText.text = full.Substring(0, Mathf.Min(full.Length, Mathf.FloorToInt(shown)));
                yield return null;
            }
            FinishPage();
        }

        void FinishPage()
        {
            bodyText.text = pages[page];
            IsTyping = false;
            IsDelaying = false;
            arrow.gameObject.SetActive(true);
        }

        public void OnPointerClick(PointerEventData e) { if (ClickEnabled) Next(); }

        /// <summary>Wie ein Klick: Tippen beenden, sonst naechste Seite, sonst Advance. Fuer Tastatur-Steuerung.</summary>
        public void Next()
        {
            if (IsTyping)
            {
                if (routine != null) StopCoroutine(routine);
                FinishPage();
            }
            else if (page < pages.Count - 1)
            {
                page++;
                StartPage();
            }
            else Advance?.Invoke();
        }

        /// <summary>Letzte Seite fertig getippt: jetzt koennen z. B. Antworten erscheinen.</summary>
        public bool IsFinished => !IsTyping && page >= pages.Count - 1;

        /// <summary>Weiterpfeil aus, z. B. solange Antworten zur Wahl stehen.</summary>
        public void HideArrow() => arrow.gameObject.SetActive(false);
    }
}
