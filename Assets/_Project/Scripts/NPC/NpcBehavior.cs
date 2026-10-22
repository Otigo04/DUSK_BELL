using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>
    /// Basis fuer alles, was ein NPC tun kann. Neues Verhalten = neue Unterklasse, an den NPC haengen, fertig.
    /// Das NpcBrain ruft WantsControl regelmaessig auf und laesst das Behavior mit der hoechsten Prioritaet laufen.
    /// </summary>
    [RequireComponent(typeof(NpcBrain))]
    public abstract class NpcBehavior : MonoBehaviour
    {
        [Tooltip("Hoeher gewinnt, wenn mehrere Behaviors gleichzeitig wollen")]
        [SerializeField] protected int priority; // Standardwert setzen Unterklassen in Reset()

        protected NpcBrain Brain { get; private set; }
        protected NpcMover Mover => Brain.Mover;
        public int Priority => priority;
        public bool IsActive => Brain != null && Brain.Current == this;

        internal void Init(NpcBrain brain) => Brain = brain;

        /// <summary>Will dieses Behavior gerade laufen? Wird mehrmals pro Sekunde gefragt, also guenstig halten.</summary>
        public abstract bool WantsControl();
        public virtual void Enter() { }
        public virtual void Tick() { }
        public virtual void Exit() { Mover.Stop(); }
    }
}
