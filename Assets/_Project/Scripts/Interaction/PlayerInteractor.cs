using System;
using Nightward.Player;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Interaction
{
    /// <summary>
    /// Sucht das naechste Interactable in Reichweite (Blickrichtung wird bevorzugt) und loest es mit seiner Taste aus (E oder F).
    /// Waehrend einer Interaktion (z. B. Dialog) ist der Spieler gesperrt.
    /// </summary>
    [RequireComponent(typeof(PlayerController))]
    public class PlayerInteractor : MonoBehaviour
    {
        [SerializeField] float range = 1.4f;
        [Tooltip("Wie stark Ziele in Blickrichtung bevorzugt werden (in Kacheln Bonus)")]
        [SerializeField] float facingBonus = 0.4f;
        [Tooltip("Sperre nach einer Interaktion, damit dieselbe Taste nicht sofort wieder ausloest")]
        [SerializeField] float cooldown = 0.25f;

        PlayerController controller;
        float readyTime;

        public Interactable Current { get; private set; }
        public bool Busy { get; private set; }
        public PlayerController Controller => controller;

        public event Action<Interactable> CurrentChanged;

        void Awake() => controller = GetComponent<PlayerController>();

        void Update()
        {
            if (Busy || Time.time < readyTime)
            {
                SetCurrent(null);
                return;
            }
            SetCurrent(FindBest());

            var kb = Keyboard.current;
            if (Current == null || kb == null) return;
            var keyControl = Current.Key == InteractKey.F ? kb.fKey : kb.eKey;
            if (keyControl.wasPressedThisFrame) Current.Interact(this);
        }

        Interactable FindBest()
        {
            Vector2 pos = transform.position;
            Vector2 facing = controller.FacingVector;
            Interactable best = null;
            float bestScore = float.MaxValue;
            foreach (var it in Interactable.All)
            {
                Vector2 d = (Vector2)it.transform.position - pos;
                float dist = d.magnitude;
                if (dist > (it.Reach > 0f ? it.Reach : range) || !it.CanInteract(this)) continue;
                float score = dist - facingBonus * (dist > 0.001f ? Vector2.Dot(facing, d / dist) : 1f);
                if (score < bestScore) { bestScore = score; best = it; }
            }
            return best;
        }

        void SetCurrent(Interactable it)
        {
            if (it == Current) return;
            Current = it;
            CurrentChanged?.Invoke(it);
        }

        /// <summary>Sperrt Bewegung, Angriff und weitere Interaktionen (z. B. fuer die Dauer eines Dialogs).</summary>
        public void Lock(bool locked)
        {
            Busy = locked;
            controller.InputLocked = locked;
            if (!locked) readyTime = Time.time + cooldown;
        }
    }
}
