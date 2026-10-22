using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>
    /// Spielt walk_/idle_-Animationen in 8 Richtungen passend zur Bewegung des NpcMovers.
    /// Gleiche Zustandsnamen wie beim Spieler (z. B. "walk_NE"), so koennen Controller wiederverwendet werden.
    /// Fehlt ein Zustand im Animator, passiert einfach nichts.
    /// </summary>
    [RequireComponent(typeof(NpcMover))]
    public class NpcAnimator : MonoBehaviour
    {
        static readonly string[] DirNames = { "E", "NE", "N", "NW", "W", "SW", "S", "SE" };
        // Hashes vorab: pro Frame wird kein String gebaut (vermeidet GC-Ruckler bei vielen NPCs)
        static readonly int[] WalkHashes = System.Array.ConvertAll(DirNames, d => Animator.StringToHash("walk_" + d));
        static readonly int[] IdleHashes = System.Array.ConvertAll(DirNames, d => Animator.StringToHash("idle_" + d));

        [SerializeField] Animator animator;

        NpcMover mover;
        int currentState; // 0 = noch keiner
        bool currentWalk;

        void Awake()
        {
            mover = GetComponent<NpcMover>();
            if (animator == null) animator = GetComponentInChildren<Animator>();
        }

        /// <summary>Nach einem Controller-Wechsel, damit der naechste Update den Zustand neu setzt.</summary>
        public void ResetState() => currentState = 0;

        void Update()
        {
            if (animator == null || animator.runtimeAnimatorController == null) return;

            int facing = Player.PlayerController.DirectionIndex(mover.Facing);
            bool moving = mover.IsMoving;
            int hash = moving ? WalkHashes[facing] : IdleHashes[facing];
            if (hash == currentState) return;
            if (!animator.HasState(0, hash)) return;

            // Richtungswechsel beim Laufen behaelt die Position im Laufzyklus bei
            bool keepTime = moving && currentState != 0 && currentWalk;
            float t = keepTime ? Mathf.Repeat(animator.GetCurrentAnimatorStateInfo(0).normalizedTime, 1f) : 0f;
            animator.Play(hash, 0, t);
            currentState = hash;
            currentWalk = moving;
        }
    }
}
