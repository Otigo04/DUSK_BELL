using Nightward.Dialogue;
using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>
    /// Waehrend eines Gespraechs: stehen bleiben, nicht ausweichen und den Spieler ansehen.
    /// Hoechste Prioritaet, damit Wandern, Folgen usw. pausieren.
    /// </summary>
    [RequireComponent(typeof(NpcDialogue))]
    public class TalkBehavior : NpcBehavior
    {
        NpcDialogue dialogue;
        Transform player;

        void Reset() => priority = 100;

        void Awake() => dialogue = GetComponent<NpcDialogue>();

        public override bool WantsControl() => dialogue.InConversation;

        public override void Enter()
        {
            Mover.Stop();
            Mover.Frozen = true;
            var p = GameObject.FindGameObjectWithTag("Player");
            player = p != null ? p.transform : null;
        }

        public override void Tick()
        {
            if (player != null) Mover.LookAt(player.position);
        }

        public override void Exit()
        {
            Mover.Frozen = false;
            base.Exit();
        }
    }
}
