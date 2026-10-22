using System;
using System.Collections.Generic;
using Nightward.UI;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.Dialogue
{
    /// <summary>
    /// Darstellung eines Gespraechs: grosses Portraet links, daneben die NwDialogBox mit Namensschild,
    /// Antwortliste (NwChoiceRow) unter dem Text in der Box und die Beziehungsleiste unten rechts.
    /// Wer spricht, sieht man sofort: spricht der NPC, leuchtet der Portraetrahmen in seiner Namensfarbe und
    /// sein Schild steht links; spricht der Spieler, wird das Portraet abgedunkelt und "Du" steht rechts.
    /// Enthaelt keine Logik, die steuert der DialogueRunner.
    /// </summary>
    public class DialogueView : MonoBehaviour
    {
        [Tooltip("Box, Portraet und Antworten. Die Beziehungsanzeige liegt ausserhalb, damit sie nach dem Gespraech noch ausblenden kann")]
        [SerializeField] GameObject content;
        [SerializeField] NwDialogBox box;
        [SerializeField] GameObject portraitPanel;
        [SerializeField] PortraitAnimator portrait;
        [SerializeField] RectTransform choiceContainer;
        [SerializeField] Font choiceFont;
        [SerializeField] Sprite choiceMarker;
        [SerializeField] int choiceSize = 12;
        [Header("Sprecher hervorheben")]
        [Tooltip("Rahmen ueber dem Portraet, leuchtet in der Namensfarbe, solange der NPC spricht")]
        [SerializeField] Graphic portraitGlow;
        [SerializeField] Image portraitImage;
        [SerializeField] Color portraitListening = new Color(0.45f, 0.42f, 0.55f, 1f);
        [SerializeField] float highlightSpeed = 10f;
        [Header("Beziehung")]
        [Tooltip("Ausserhalb von content, damit eine Aenderung am Gespraechsende noch zu Ende laufen kann")]
        [SerializeField] RelationshipMeter relationMeter;

        readonly List<NwChoiceRow> buttons = new List<NwChoiceRow>();
        bool npcSpeaking;
        Color portraitTarget = Color.white;
        float glowTarget;

        public bool IsTyping => box.IsTyping && !box.IsDelaying;
        public bool LineFinished => box.IsFinished;
        public int ChoiceCount => buttons.Count;
        public PortraitAnimator Portrait => portrait;

        /// <summary>Aus: ein Klick auf die Box blaettert nicht mehr von selbst (der Aufrufer wertet Klicks selbst aus).</summary>
        public bool BoxClickEnabled { get => box.ClickEnabled; set => box.ClickEnabled = value; }

        /// <summary>Klick auf die Box nach der letzten Seite.</summary>
        public event Action Advance;

        void Awake()
        {
            box.Advance += () => Advance?.Invoke();
        }

        void Update()
        {
            portrait.Talking = npcSpeaking && IsTyping;
            float k = 1f - Mathf.Exp(-highlightSpeed * Time.unscaledDeltaTime);
            if (portraitImage != null) portraitImage.color = Color.Lerp(portraitImage.color, portraitTarget, k);
            if (portraitGlow != null)
            {
                var c = portraitGlow.color;
                c.a = Mathf.Lerp(c.a, glowTarget, k);
                portraitGlow.color = c;
            }
        }

        public void Open(NpcProfile profile)
        {
            content.SetActive(true);
            portrait.SetProfile(profile);
            portraitPanel.SetActive(profile != null && profile.portraitIdle != null);
            ClearChoices();
            if (relationMeter != null && profile != null) relationMeter.Show(profile, Relationships.Get(profile.id));
        }

        public void Close()
        {
            ClearChoices();
            box.Hide();
            content.SetActive(false);
            if (relationMeter != null) relationMeter.Hide();
        }

        void Highlight(Speaker speaker, NpcProfile profile)
        {
            bool npc = speaker == Speaker.Npc;
            portraitTarget = npc ? Color.white : speaker == Speaker.Spieler ? portraitListening : Color.Lerp(portraitListening, Color.white, 0.5f);
            glowTarget = npc ? 1f : 0f;
            if (portraitGlow != null && profile != null)
            {
                var c = profile.nameColor;
                c.a = portraitGlow.color.a;
                portraitGlow.color = c;
            }
        }

        /// <summary>Platz, den die Box unter dem Text fuer die Antworten freihaelt.</summary>
        public static float ChoiceReserve(int count) => count <= 0 ? 0f : count * NwChoiceRow.Height + 6f;

        /// <summary>choiceCount: so viele Antworten folgen; der Text wird so geteilt, dass er daneben noch komplett lesbar bleibt.</summary>
        public void ShowLine(Speaker speaker, NpcProfile profile, string text, int choiceCount = 0, float startDelay = 0f)
        {
            ClearChoices();
            npcSpeaking = speaker == Speaker.Npc;
            Highlight(speaker, profile);
            float reserve = ChoiceReserve(choiceCount);
            switch (speaker)
            {
                case Speaker.Npc: box.ShowResident(profile.displayName, profile.nameColor, text, reserve, startDelay: startDelay); break;
                case Speaker.Spieler: box.ShowResident("Du", NwTheme.TextDefault, text, reserve, plateRight: true, startDelay: startDelay); break;
                default: box.ShowNarrator(text, reserve, startDelay); break;
            }
        }

        /// <summary>Weiter wie ein Klick: Tippen beenden, blaettern oder Advance.</summary>
        public void Next() => box.Next();

        public void ShowChoices(IList<string> texts, Action<int> onPick)
        {
            ClearChoices();
            box.HideArrow();
            float rowWidth = choiceContainer.rect.width;
            for (int i = 0; i < texts.Count; i++)
            {
                var b = NwChoiceRow.Create(choiceContainer, choiceFont, choiceMarker, choiceSize);
                b.gameObject.name = "Antwort_" + (i + 1);
                // Antworten moeglichst kurz halten; zu lange brechen auf eine zweite Zeile um
                b.SetText(texts[i], rowWidth);
                int index = i;
                b.onClick.AddListener(() => onPick(index));
                buttons.Add(b);
            }
            Select(-1); // keine Vorauswahl: hervorgehoben wird nur, was die Maus beruehrt
        }

        public void Select(int index)
        {
            for (int i = 0; i < buttons.Count; i++) buttons[i].Highlighted = i == index;
        }

        public void ClearChoices()
        {
            foreach (var b in buttons) if (b != null) Destroy(b.gameObject);
            buttons.Clear();
        }

        /// <summary>Beziehung hat sich geaendert: Leiste animiert von from nach to.</summary>
        public void ShowRelationship(int from, int to)
        {
            if (relationMeter != null) relationMeter.Animate(from, to);
        }
    }
}
