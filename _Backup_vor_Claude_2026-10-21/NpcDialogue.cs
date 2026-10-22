using System;
using System.Collections.Generic;
using Nightward.Interaction;
using Nightward.NPC;
using UnityEngine;

namespace Nightward.Dialogue
{
    /// <summary>Ein moeglicher Dialog eines NPCs mit Bedingungen. Der erste passende Eintrag von oben gewinnt.</summary>
    [Serializable]
    public class DialogueEntry
    {
        public DialogueAsset dialogue;
        [Range(Relationships.Min, Relationships.Max)] public int minRelationship = Relationships.Min;
        [Range(Relationships.Min, Relationships.Max)] public int maxRelationship = Relationships.Max;
        [Tooltip("Nur wenn dieses Flag gesetzt ist")]
        public string requireFlag;
        [Tooltip("Nicht, wenn dieses Flag gesetzt ist")]
        public string forbidFlag;
        [Tooltip("Nur ein einziges Mal (z. B. Kennenlernen)")]
        public bool onlyOnce;
        [Tooltip("Wiederholbares Geplauder: zaehlt nie als Neuigkeit, der NPC zeigt dafuer keine Sprechblase")]
        public bool smallTalk;
    }

    /// <summary>
    /// Macht einen NPC ansprechbar: E startet den passenden Dialog aus der Liste
    /// (nach Beziehung, Flags und 'nur einmal'). Waehrend des Gespraechs bleibt der NPC stehen (TalkBehavior).
    /// </summary>
    public class NpcDialogue : Interactable
    {
        [SerializeField] NpcProfile profile;
        [Tooltip("Reihenfolge = Prioritaet. Der letzte Eintrag ohne Bedingungen dient als Standard")]
        [SerializeField] List<DialogueEntry> dialogues = new List<DialogueEntry>();

        NpcBrain brain;

        public NpcProfile Profile => profile;
        public bool InConversation { get; private set; }
        public int Relationship => profile != null ? Relationships.Get(profile.id) : 0;

        public event Action ConversationStarted;
        public event Action ConversationEnded;

        void Awake()
        {
            brain = GetComponent<NpcBrain>();
            if (profile != null) Relationships.Seed(Relationships.Player, profile.id, profile.startRelationship);
        }

        public override bool CanInteract(PlayerInteractor who) =>
            base.CanInteract(who) && profile != null && !InConversation
            && DialogueRunner.Instance != null && !DialogueRunner.Instance.IsRunning && Pick() != null;

        /// <summary>Sprechblase nur, wenn der NPC etwas Neues zu sagen hat: der Dialog, der jetzt dran waere, wurde noch nicht gefuehrt.
        /// Aendern sich Beziehung oder Flags so, dass ein anderer Dialog passt, kommt die Blase von selbst wieder.</summary>
        public bool HasNews
        {
            get
            {
                var e = Pick();
                return e != null && !e.smallTalk && !Relationships.HasFlag(SeenFlag(e));
            }
        }

        public override bool ShowsIndicator(PlayerInteractor who) => HasNews;

        public override void Interact(PlayerInteractor who)
        {
            var entry = Pick();
            if (entry == null) return;
            Relationships.SetFlag(SeenFlag(entry));
            if (entry.onlyOnce) Relationships.SetFlag(OnceFlag(entry));
            DialogueRunner.Instance.Begin(this, entry.dialogue, who);
        }

        DialogueEntry Pick()
        {
            int rel = Relationship;
            foreach (var e in dialogues)
            {
                if (e.dialogue == null) continue;
                if (rel < e.minRelationship || rel > e.maxRelationship) continue;
                if (!string.IsNullOrEmpty(e.requireFlag) && !Relationships.HasFlag(e.requireFlag)) continue;
                if (!string.IsNullOrEmpty(e.forbidFlag) && Relationships.HasFlag(e.forbidFlag)) continue;
                if (e.onlyOnce && Relationships.HasFlag(OnceFlag(e))) continue;
                return e;
            }
            return null;
        }

        string OnceFlag(DialogueEntry e) => profile.id + ":" + e.dialogue.name;
        string SeenFlag(DialogueEntry e) => profile.id + ":gehoert:" + e.dialogue.name;

        internal void SetInConversation(bool value)
        {
            if (InConversation == value) return;
            InConversation = value;
            if (brain != null) brain.ForceDecision();
            if (value) ConversationStarted?.Invoke();
            else ConversationEnded?.Invoke();
        }
    }
}
