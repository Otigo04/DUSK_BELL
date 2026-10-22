using Nightward.Interaction;
using UnityEngine;

namespace Nightward.Survival
{
    /// <summary>Etwas zum Essen oder Trinken (Brunnen, Kochtopf, Teekanne). Gibt ein Verbrauchsgut aus der SurvivalConfig ab.</summary>
    public class SurvivalSource : Interactable
    {
        [Tooltip("Id des Verbrauchsguts, z. B. water, bread, stew, tea_calming")]
        [SerializeField] string consumableId = "water";
        [Tooltip("Wie oft benutzbar. -1 = unbegrenzt")]
        [SerializeField] int uses = -1;
        [Tooltip("Pause zwischen zwei Benutzungen in Sekunden")]
        [SerializeField] float cooldown = 1.5f;

        float readyAt;

        void Reset() { Prompt = "Drink"; key = InteractKey.F; }

        public override bool CanInteract(PlayerInteractor who) =>
            base.CanInteract(who) && PlayerSurvival.Instance != null && uses != 0 && Time.time >= readyAt;

        public override void Interact(PlayerInteractor who)
        {
            var p = PlayerSurvival.Instance;
            if (p == null || uses == 0) return;
            if (!p.Sim.Consume(consumableId)) { Debug.LogWarning($"SurvivalSource '{name}': unbekanntes Verbrauchsgut '{consumableId}'.", this); return; }
            if (uses > 0) uses--;
            readyAt = Time.time + cooldown;
        }
    }
}
