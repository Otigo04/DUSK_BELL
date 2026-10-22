using System;
using System.Collections;
using System.Collections.Generic;
using Nightward.Dialogue;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Opening
{
    /// <summary>
    /// Spielt feste Zeilen (OpeningScript/ArrivalScript) in der normalen Dialogbox ab, ohne DialogAsset: Erzaehler oder NPC,
    /// Ausdruck pro Zeile (#expr), Pause vor NPC-Zeilen (#pause) und Mumble beim Tippen (#voice:mumble).
    /// Mehrere Sprecher in einem Gespraech: pro Sprecher ein Eintrag in "voices" (Name wie in Line.speaker, Profil, Ausdruecke);
    /// beim Sprecherwechsel wechselt das Portraet. Ohne Eintrag gilt das Profil aus Open.
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

        [Serializable]
        public class Voice
        {
            [Tooltip("Name wie in Line.speaker (z. B. Bulut, Ilhan, Monster)")]
            public string speaker;
            public NpcProfile profile;
            [Tooltip("Ausdruecke dieses Sprechers (tense, cold, ...)")]
            public List<Expression> expressions = new List<Expression>();
            public float pitch = 0.8f;
        }

        [SerializeField] DialogueView view;
        [SerializeField] OpeningAudio audioPlayer;
        [Tooltip("Ausdruecke aus der Dialogue Bible (tense, cold, suspicious ...) fuer das Profil aus Open")]
        [SerializeField] List<Expression> expressions = new List<Expression>();
        [Tooltip("Weitere Sprecher mit eigenem Portraet")]
        [SerializeField] List<Voice> voices = new List<Voice>();
        [SerializeField] float voicePitch = 0.8f;
        [Tooltip("Name der Spielerzeilen in der Dialogbox (die Opening-Texte sind englisch)")]
        [SerializeField] string playerLabel = "You";

        NpcProfile profile;     // Standardprofil (Open)
        NpcProfile shown;       // Portraet, das gerade im View steht
        bool advance;
        int chosen = -1;
        readonly Dictionary<string, Sprite[]> talkFrames = new Dictionary<string, Sprite[]>();

        /// <summary>Nur zum Testen: Zeilen blaettern sich selbst weiter und Antworten werden automatisch gewaehlt (AutoChoice).</summary>
        public static bool AutoAdvance { get; set; }
        public static int AutoChoice { get; set; }

        public bool IsOpen { get; private set; }

        void Awake()
        {
            if (view != null) view.Advance += () => advance = true;
        }

        public void Open(NpcProfile npc)
        {
            profile = npc;
            shown = npc;
            IsOpen = true;
            view.BoxClickEnabled = false;   // Klicks wertet PlayLine selbst aus (auch neben der Box)
            view.PlayerLabel = playerLabel;
            view.Open(npc);
            if (audioPlayer != null) audioPlayer.SetVoice(voicePitch);
        }

        public void Close()
        {
            IsOpen = false;
            shown = null;
            if (audioPlayer != null) audioPlayer.Mumbling = false;
            view.BoxClickEnabled = true;
            view.PlayerLabel = "Du";
            view.Close();
        }

        public IEnumerator Play(IList<Line> lines)
        {
            foreach (var l in lines) yield return PlayLine(l);
        }

        Voice FindVoice(string speaker)
        {
            if (string.IsNullOrEmpty(speaker)) return null;
            foreach (var v in voices)
                if (v.profile != null && string.Equals(v.speaker, speaker, StringComparison.OrdinalIgnoreCase)) return v;
            return null;
        }

        /// <summary>choicesAfter &gt; 0: danach folgen so viele Antworten. Die Zeile wartet dann nicht auf Weiter,
        /// sondern laesst unter dem Text Platz fuer die Antworten (Choose direkt danach aufrufen).</summary>
        public IEnumerator PlayLine(Line l, int choicesAfter = 0)
        {
            var voice = l.player ? null : FindVoice(l.speaker);
            var who = voice != null ? voice.profile : profile;
            bool npc = !string.IsNullOrEmpty(l.speaker) && !l.player && who != null;

            if (npc && who != shown)
            {
                // Sprecherwechsel: Portraet und Namensplakette des neuen Sprechers
                shown = who;
                view.Open(who);
                if (audioPlayer != null) audioPlayer.SetVoice(voice != null ? voice.pitch : voicePitch);
            }
            var list = voice != null ? voice.expressions : expressions;
            view.Portrait.SetExpression(npc ? Find(list, l.expr) : null, npc ? FindTalk(who, list, l.expr) : null);
            // Die Atempause vor einer NPC-Zeile passiert in der Box (Name steht schon da, ein Klick ueberspringt sie)
            view.ShowLine(npc ? Speaker.Npc : l.player ? Speaker.Spieler : Speaker.Erzaehler, who, l.text, choicesAfter, npc ? l.pause : 0f);
            advance = false;
            yield return null; // Taste vom letzten Weiter nicht doppelt zaehlen
            float idle = 0f;
            while (choicesAfter > 0 ? !view.LineFinished : !advance)
            {
                if (audioPlayer != null) audioPlayer.Mumbling = npc && l.mumble && view.IsTyping;
                if (AdvancePressed()) view.Next();
                if (AutoAdvance && !view.IsTyping)
                {
                    idle += Time.deltaTime;
                    if (idle > 0.5f) { idle = 0f; view.Next(); }
                }
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
            float wait = 0f;
            while (chosen < 0)
            {
                wait += Time.deltaTime;
                if (AutoAdvance && wait > 0.8f) chosen = Mathf.Clamp(AutoChoice, 0, options.Count - 1);
                yield return null;
            }
            view.ClearChoices();
        }

        public int Chosen => chosen;

        /// <summary>Beziehung zum aktuellen NPC aendern und die Leiste animieren.</summary>
        public void ChangeRelationship(int delta)
        {
            var p = shown != null ? shown : profile;
            if (p == null) return;
            int before = Relationships.Get(p.id);
            int after = Relationships.Change(p.id, delta);
            if (after != before) view.ShowRelationship(before, after);
        }

        /// <summary>Sprech-Frames zu einem Ausdruck (gleiches Gesicht, Mund aus dem Profil), damit das Portraet auch spricht. Je Profil und Ausdruck einmal gebaut.</summary>
        Sprite[] FindTalk(NpcProfile who, List<Expression> list, string tag)
        {
            if (string.IsNullOrEmpty(tag) || who == null) return null;
            string key = who.id + "|" + tag;
            if (talkFrames.TryGetValue(key, out var cached)) return cached;
            var sprite = Find(list, tag);
            if (sprite == null) return null;
            var frames = PortraitTalkFrames.Build(who.portraitIdle, who.portraitTalk, sprite);
            talkFrames[key] = frames;
            return frames;
        }

        static Sprite Find(List<Expression> list, string tag)
        {
            if (string.IsNullOrEmpty(tag)) return null;
            foreach (var e in list) if (e.tag == tag) return e.sprite;
            return null;
        }
    }
}
