using System;
using System.Collections;
using System.Collections.Generic;
using Nightward.Dialogue;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Opening
{
    /// <summary>
    /// Spielt feste Zeilen (OpeningScript) in der normalen Dialogbox ab, ohne DialogAsset: Erzaehler oder NPC,
    /// Ausdruck pro Zeile (#expr), Pause vor NPC-Zeilen (#pause) und Mumble beim Tippen (#voice:mumble).
    /// Weiter mit E / Leertaste / Enter / Linksklick irgendwo auf dem Bildschirm: erst vervollstaendigt der Klick den Text,
    /// der naechste geht zur naechsten Zeile. Antworten nur per Maus, keine Vorauswahl.
    /// </summary>
    public class ScriptedDialogue : MonoBehaviour
    {
        [Serializable]
        public class Expression
        {
            public string tag;
            public Sprite sprite;
        }

        [SerializeField] DialogueView view;
        [SerializeField] OpeningAudio audioPlayer;
        [Tooltip("Ausdruecke aus der Dialogue Bible (tense, cold, suspicious ...) fuer das Portraet")]
        [SerializeField] List<Expression> expressions = new List<Expression>();
        [SerializeField] float voicePitch = 0.8f;
        [Tooltip("Name der Spielerzeilen in der Dialogbox (die Opening-Texte sind englisch)")]
        [SerializeField] string playerLabel = "You";

        NpcProfile profile;
        bool advance;
        int chosen = -1;
        readonly Dictionary<string, Sprite[]> talkFrames = new Dictionary<string, Sprite[]>();

        public bool IsOpen { get; private set; }

        void Awake()
        {
            if (view != null) view.Advance += () => advance = true;
        }

        public void Open(NpcProfile npc)
        {
            profile = npc;
            IsOpen = true;
            view.BoxClickEnabled = false;   // Klicks wertet PlayLine selbst aus (auch neben der Box)
            view.PlayerLabel = playerLabel;
            BuildTalkFrames();
            view.Open(npc);
            if (audioPlayer != null) audioPlayer.SetVoice(voicePitch);
        }

        public void Close()
        {
            IsOpen = false;
            if (audioPlayer != null) audioPlayer.Mumbling = false;
            view.BoxClickEnabled = true;
            view.PlayerLabel = "Du";
            view.Close();
        }

        public IEnumerator Play(IList<Line> lines)
        {
            foreach (var l in lines) yield return PlayLine(l);
        }

        /// <summary>choicesAfter &gt; 0: danach folgen so viele Antworten. Die Zeile wartet dann nicht auf Weiter,
        /// sondern laesst unter dem Text Platz fuer die Antworten (Choose direkt danach aufrufen).</summary>
        public IEnumerator PlayLine(Line l, int choicesAfter = 0)
        {
            bool npc = !string.IsNullOrEmpty(l.speaker) && !l.player && profile != null;
            view.Portrait.SetExpression(npc ? Find(l.expr) : null, npc ? FindTalk(l.expr) : null);
            // Die Atempause vor einer NPC-Zeile passiert in der Box (Name steht schon da, ein Klick ueberspringt sie)
            view.ShowLine(npc ? Speaker.Npc : l.player ? Speaker.Spieler : Speaker.Erzaehler, profile, l.text, choicesAfter, npc ? l.pause : 0f);
            advance = false;
            yield return null; // Taste vom letzten Weiter nicht doppelt zaehlen
            while (choicesAfter > 0 ? !view.LineFinished : !advance)
            {
                if (audioPlayer != null) audioPlayer.Mumbling = npc && l.mumble && view.IsTyping;
                if (AdvancePressed()) view.Next();
                yield return null;
            }
            if (audioPlayer != null) audioPlayer.Mumbling = false;
        }

        /// <summary>E, Leertaste, Enter oder Linksklick (egal wo auf dem Bildschirm) in diesem Frame.</summary>
        static bool AdvancePressed()
        {
            var kb = Keyboard.current;
            if (kb != null && (kb.eKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame
                               || kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame)) return true;
            var mouse = Mouse.current;
            return mouse != null && mouse.leftButton.wasPressedThisFrame;
        }

        /// <summary>Zeigt Antworten unter der letzten Zeile. Ergebnis in Chosen (Index).</summary>
        public IEnumerator Choose(IList<string> options)
        {
            while (!view.LineFinished) yield return null;
            chosen = -1;
            view.ShowChoices(options, i => chosen = i);
            while (chosen < 0) yield return null;
            view.ClearChoices();
        }

        public int Chosen => chosen;

        /// <summary>Beziehung zum aktuellen NPC aendern und die Leiste animieren.</summary>
        public void ChangeRelationship(int delta)
        {
            if (profile == null) return;
            int before = Relationships.Get(profile.id);
            int after = Relationships.Change(profile.id, delta);
            if (after != before) view.ShowRelationship(before, after);
        }

        /// <summary>Zu jedem Ausdruck die Sprech-Frames bauen (gleiches Gesicht, Mund aus dem Profil), damit das Portraet auch spricht.</summary>
        void BuildTalkFrames()
        {
            talkFrames.Clear();
            if (profile == null) return;
            foreach (var e in expressions)
                if (!string.IsNullOrEmpty(e.tag) && e.sprite != null && !talkFrames.ContainsKey(e.tag))
                    talkFrames[e.tag] = PortraitTalkFrames.Build(profile.portraitIdle, profile.portraitTalk, e.sprite);
        }

        Sprite[] FindTalk(string tag) => !string.IsNullOrEmpty(tag) && talkFrames.TryGetValue(tag, out var f) ? f : null;

        Sprite Find(string tag)
        {
            if (string.IsNullOrEmpty(tag)) return null;
            foreach (var e in expressions) if (e.tag == tag) return e.sprite;
            return null;
        }
    }
}
