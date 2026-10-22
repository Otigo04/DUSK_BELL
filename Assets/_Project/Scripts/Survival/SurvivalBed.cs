using Nightward.Interaction;

namespace Nightward.Survival
{
    /// <summary>Bett: schlafen bis zum Morgen. Geht nur in Daemmerung/Nacht und nicht unter der Schlafsperre (Sanity unter 40 %).</summary>
    public class SurvivalBed : Interactable
    {
        void Reset() { Prompt = "Sleep"; key = InteractKey.F; }

        public override bool CanInteract(PlayerInteractor who) => base.CanInteract(who) && PlayerSurvival.Instance != null && !PlayerSurvival.Instance.Busy;

        public override void Interact(PlayerInteractor who)
        {
            var p = PlayerSurvival.Instance;
            if (p != null) p.TrySleep(out _);
        }
    }
}
