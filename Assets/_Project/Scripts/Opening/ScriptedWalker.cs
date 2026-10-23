using System.Collections;
using Nightward.NPC;
using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Laesst einen NPC in Zwischensequenzen sicher an einen Punkt laufen: ohne Pfadsuche, Ausweichen und Kollision.
    /// Der NpcMover wuerde sonst z. B. vor dem Auto stehen bleiben, weil der (unsichtbare) Spieler darin sitzt.
    /// Spielt dabei selbst walk_/idle_ in 8 Richtungen; danach uebernimmt wieder der NpcMover/NpcAnimator.
    /// </summary>
    [RequireComponent(typeof(NpcMover))]
    public class ScriptedWalker : MonoBehaviour
    {
        static readonly string[] Dirs = { "E", "NE", "N", "NW", "W", "SW", "S", "SE" };

        NpcMover mover;
        NpcAnimator npcAnimator;
        Animator animator;
        Rigidbody2D body;

        public bool Walking { get; private set; }

        void Awake()
        {
            mover = GetComponent<NpcMover>();
            npcAnimator = GetComponent<NpcAnimator>();
            animator = GetComponentInChildren<Animator>();
            body = GetComponent<Rigidbody2D>();
        }

        /// <summary>Laeuft geradlinig zum Ziel. speed in Units pro Sekunde. Solange hold true liefert, bleibt die Figur stehen (z. B. wartet auf den Spieler). stand = false: am Ziel nicht anhalten (Zwischenpunkt einer Route, naechster WalkTo folgt gleich).</summary>
        public IEnumerator WalkTo(Vector2 target, float speed, System.Func<bool> hold = null, bool stand = true)
        {
            Walking = true;
            mover.Stop();
            mover.Frozen = true;
            if (npcAnimator != null) npcAnimator.enabled = false;
            string last = null;
            while (true)
            {
                Vector2 pos = body.position;
                Vector2 to = target - pos;
                float dist = to.magnitude;
                if (dist < 0.04f) break;
                string dir = Dirs[Player.PlayerController.DirectionIndex(to)];
                if (hold != null && hold())
                {
                    string idle = "idle_" + dir;
                    if (idle != last && animator != null) { animator.speed = 1f; animator.Play(idle, 0, 0f); last = idle; }
                    yield return null;
                    continue;
                }
                Vector2 step = to / dist * Mathf.Min(dist, speed * Time.deltaTime);
                body.position = pos + step;
                transform.position = body.position;
                string state = "walk_" + dir;
                if (state != last && animator != null) { animator.Play(state, 0, 0f); last = state; }
                if (animator != null) animator.speed = Mathf.Clamp(speed / 2.5f, 0.6f, 1.6f);
                yield return null;
            }
            if (stand) Stand(target + Vector2.down);
            Walking = false;
        }

        string stepState;

        /// <summary>Per-Frame-Steuerung (Verfolgungsjagd): Pfadsuche und Animator aus, die Figur wird mit Step bewegt.</summary>
        public void BeginManual()
        {
            Walking = true;
            mover.Stop();
            mover.Frozen = true;
            if (npcAnimator != null) npcAnimator.enabled = false;
            stepState = null;
        }

        /// <summary>Ein Schritt in Richtung Ziel (speed in Units pro Sekunde), mit walk_ in 8 Richtungen.</summary>
        public void Step(Vector2 target, float speed)
        {
            Vector2 pos = body.position;
            Vector2 to = target - pos;
            float dist = to.magnitude;
            if (dist < 0.001f) return;
            body.position = pos + to / dist * Mathf.Min(dist, speed * Time.deltaTime);
            transform.position = body.position;
            string state = "walk_" + Dirs[Player.PlayerController.DirectionIndex(to)];
            if (state != stepState && animator != null) { animator.Play(state, 0, 0f); stepState = state; }
            if (animator != null) animator.speed = Mathf.Clamp(speed / 2.5f, 0.6f, 1.6f);
        }

        public void EndManual(Vector2 lookAt)
        {
            Walking = false;
            Stand(lookAt);
        }

        /// <summary>Stehen bleiben und zu einem Punkt schauen, dann wieder normal animieren.</summary>
        public void Stand(Vector2 lookAt)
        {
            if (animator != null) animator.speed = 1f;
            mover.Frozen = false;
            mover.Stop();
            mover.LookAt(lookAt);
            if (npcAnimator != null) { npcAnimator.enabled = true; npcAnimator.ResetState(); }
        }
    }
}
