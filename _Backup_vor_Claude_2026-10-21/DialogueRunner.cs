using System;
using System.Collections.Generic;
using Nightward.Interaction;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Dialogue
{
    /// <summary>
    /// Fuehrt ein Gespraech Knoten fuer Knoten aus: Text zeigen, Antworten anbieten, Beziehung und Flags anwenden.
    /// Steuerung: E / Leertaste / Enter / Klick = weiter. Antworten nur per Mausklick, keine ist vorausgewaehlt.
    /// Eine Instanz pro Szene (liegt am Dialog-Canvas).
    /// </summary>
    public class DialogueRunner : MonoBehaviour
    {
        public static DialogueRunner Instance { get; private set; }

        [SerializeField] DialogueView view;

        NpcDialogue npc;
        DialogueAsset dialogue;
        DialogueNode node;
        PlayerInteractor player;
        readonly List<DialogueChoice> choices = new List<DialogueChoice>();
        bool choicesShown;
        int startFrame;

        public bool IsRunning { get; private set; }
        public NpcDialogue CurrentNpc => npc;

        public event Action<NpcDialogue> Started;
        public event Action<NpcDialogue> Ended;

        void Awake()
        {
            Instance = this;
            view.Advance += OnAdvance;
            view.Close();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        public void Begin(NpcDialogue speaker, DialogueAsset asset, PlayerInteractor who)
        {
            if (IsRunning || asset == null) return;
            npc = speaker;
            dialogue = asset;
            player = who;
            IsRunning = true;
            startFrame = Time.frameCount;

            player.Lock(true);
            player.Controller.FaceTowards(npc.transform.position - player.transform.position);
            npc.SetInConversation(true);
            view.Open(npc.Profile);
            // Kamera schwenkt sanft zwischen beide Gespraechspartner
            if (Core.CameraFollow2D.Main != null) Core.CameraFollow2D.Main.SetFocus(npc.transform, 0.4f);
            Started?.Invoke(npc);
            Show(dialogue.Start);
        }

        void Show(DialogueNode n)
        {
            node = n;
            choicesShown = false;
            if (n == null) { End(); return; }

            Apply(n.relationship, n.setFlag);
            choices.Clear();
            foreach (var c in n.choices)
            {
                if (npc.Relationship < c.minRelationship) continue;
                if (!string.IsNullOrEmpty(c.requireFlag) && !Relationships.HasFlag(c.requireFlag)) continue;
                choices.Add(c);
            }
            // Der Spieler hat das letzte Wort: endet das Gespraech nach dem NPC, bietet er einen Abschied an
            if (choices.Count == 0 && string.IsNullOrEmpty(n.next) && n.speaker != Speaker.Spieler && !n.noFarewell)
                AddFarewells();
            view.ShowLine(n.speaker, npc.Profile, Format(n.text), choices.Count);
        }

        static readonly string[] FarewellsCold = { "Ich gehe.", "Schon gut. Tschüss." };
        static readonly string[] FarewellsNeutral = { "Ich muss jetzt gehen.", "Tschüss.", "Bis später.", "Ich muss weiter." };
        static readonly string[] FarewellsWarm = { "Bis später!", "Pass auf dich auf.", "Ich komme bald wieder.", "Ich muss los. Bis bald!" };

        // Zwei verschiedene Abschiede, passend zur Beziehung. Beide beenden das Gespraech ohne Folgen
        void AddFarewells()
        {
            int rel = npc.Relationship;
            // Stufe unter neutral = kuehl, darueber = herzlich
            var tiers = RelationshipTiers.Active;
            var neutral = tiers.Find("neutral");
            int cold = neutral != null ? neutral.minValue : -2;
            int warmIndex = neutral != null ? tiers.tiers.IndexOf(neutral) + 1 : -1;
            int warm = warmIndex > 0 && warmIndex < tiers.tiers.Count ? tiers.tiers[warmIndex].minValue : 3;
            var pool = rel < cold ? FarewellsCold : rel >= warm ? FarewellsWarm : FarewellsNeutral;
            int first = UnityEngine.Random.Range(0, pool.Length);
            int second = (first + 1 + UnityEngine.Random.Range(0, pool.Length - 1)) % pool.Length;
            choices.Add(new DialogueChoice { text = pool[first] });
            choices.Add(new DialogueChoice { text = pool[second] });
        }

        string Format(string text) => (text ?? "").Replace("{name}", npc.Profile.displayName);

        void Update()
        {
            if (!IsRunning || Time.frameCount == startFrame) return;

            // Antworten erst zeigen, wenn der Text komplett dasteht
            if (choices.Count > 0 && !choicesShown && view.LineFinished)
            {
                var texts = new List<string>();
                for (int i = 0; i < choices.Count; i++) texts.Add(Format(choices[i].text));
                view.ShowChoices(texts, Choose);
                choicesShown = true;
            }

            // Antworten nur per Mausklick (Opening-Spec): keine Tasten, keine Vorauswahl
            if (choicesShown) return;

            var kb = Keyboard.current;
            if (kb == null) return;
            bool confirm = kb.eKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame
                           || kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame;
            if (confirm) view.Next();
        }

        // Klick auf die Box nach der letzten Seite (ohne Antworten) = weiter
        void OnAdvance()
        {
            if (!IsRunning || choices.Count > 0) return;
            Show(dialogue.Find(node.next));
        }

        void Choose(int index)
        {
            if (!choicesShown || index < 0 || index >= choices.Count) return;
            var c = choices[index];
            Apply(c.relationship, c.setFlag);
            choices.Clear();
            view.ClearChoices();
            Show(dialogue.Find(c.next));
        }

        void Apply(int relationship, string flag)
        {
            if (relationship != 0)
            {
                int before = npc.Relationship;
                int after = Relationships.Change(npc.Profile.id, relationship);
                if (after != before) view.ShowRelationship(before, after);
            }
            Relationships.SetFlag(flag);
        }

        public void End()
        {
            if (!IsRunning) return;
            IsRunning = false;
            view.Close();
            if (Core.CameraFollow2D.Main != null) Core.CameraFollow2D.Main.ClearFocus();
            npc.SetInConversation(false);
            player.Lock(false);
            var finished = npc;
            npc = null;
            Ended?.Invoke(finished);
        }
    }
}
