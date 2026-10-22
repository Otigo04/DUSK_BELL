using System;
using Nightward.Interaction;
using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Objekt der Opening Sequence, das mit F benutzt wird (Baumstamm, Auto). Ob es gerade geht und was passiert,
    /// bestimmt der OpeningDirector ueber Allowed und Used.
    /// </summary>
    public class OpeningInteractable : Interactable
    {
        public bool Allowed { get; set; }
        public event Action Used;

        void Reset() => key = InteractKey.F;

        void Awake() => key = InteractKey.F;

        public override bool CanInteract(PlayerInteractor who) => base.CanInteract(who) && Allowed;

        public override void Interact(PlayerInteractor who) => Used?.Invoke();
    }
}
