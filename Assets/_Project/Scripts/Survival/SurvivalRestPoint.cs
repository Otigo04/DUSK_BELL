using Nightward.Interaction;
using UnityEngine;

namespace Nightward.Survival
{
    /// <summary>Bank, Quelle, Rastplatz: kurz ausruhen. Erholt Ausdauer und das Maximum (Maximum-Erschoepfung), optional mit einem Getraenk.</summary>
    public class SurvivalRestPoint : Interactable
    {
        [SerializeField] float restSeconds = 6f;
        [Tooltip("Optional: Id eines Verbrauchsguts aus der SurvivalConfig, z. B. spring_water")]
        [SerializeField] string consumableId;

        void Reset() { Prompt = "Rest"; key = InteractKey.F; }

        public override bool CanInteract(PlayerInteractor who) => base.CanInteract(who) && PlayerSurvival.Instance != null && !PlayerSurvival.Instance.Busy;

        public override void Interact(PlayerInteractor who)
        {
            var p = PlayerSurvival.Instance;
            if (p == null) return;
            if (!string.IsNullOrEmpty(consumableId)) p.Sim.Consume(consumableId);
            p.Rest(restSeconds);
        }
    }
}
