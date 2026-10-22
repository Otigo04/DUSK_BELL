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
    /// Weiter mit E / Leertaste / Enter / Klick. Antworten nur per Maus, keine Vorauswahl.
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

        NpcProfile profile;
        bool advance;
        int chosen = -1;

        public bool IsOpen { get; private set; }

        void Awake()
        {
            if (view != null) view.Advance += () => advance = true;
        }

        public void Open(NpcProfile npc)
        {
            profile = npc;
            IsOpen = true;
            view.Open(npc);
            if (audioPlayer != null) audioPlayer.SetVoice(voicePitch);
        }

        public void Close()
        {
            IsOpen = false;
            if (audioPlayer != null) audioPlayer.Mumbling = false;
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
            bool npc = !string.IsNullOrEmpty(l.speaker) && profile != null;
            if (npc && l.pause > 0f) yield return new WaitForSeconds(l.pause);

            view.Portrait.SetExpression(npc ? Find(l.expr) : null);
            view.ShowLine(npc ? Speaker.Npc : Speaker.Erzaehler, profile, l.text, choicesAfter);
            advance = false;
            yield return null; // Taste vom letzten Weiter nicht doppelt zaehlen
            while (choicesAfter > 0 ? !view.LineFinished : !advance)
            {
                if (audioPlayer != null) audioPlayer.Mumbling = npc && l.mumble && view.IsTyping;
                var kb = Keyboard.current;
                if (kb != null && (kb.eKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame
                                   || kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame))
                    view.Next();
                yield return null;
            }
            if (audioPlayer != null) audioPlayer.Mumbling = false;
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

        Sprite Find(string tag)
        {
            if (string.IsNullOrEmpty(tag)) return null;
            foreach (var e in expressions) if (e.tag == tag) return e.sprite;
            return null;
        }
    }
}
