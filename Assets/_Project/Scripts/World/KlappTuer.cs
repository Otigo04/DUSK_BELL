using Nightward.Interaction;
using UnityEngine;

namespace Nightward.World
{
    /// <summary>
    /// Tuer in einem Durchgang: haengt zu senkrecht von oben nach unten (Scharnier oben) und blockiert.
    /// Mit E klappt sie sofort um 90 Grad nach innen auf (Kollision aus), nochmal E klappt sie wieder zu.
    /// Pivot des Objekts = Scharnier, das Tuerblatt ist ein Kind mit SpriteRenderer (Pivot oben Mitte).
    /// </summary>
    public class KlappTuer : Interactable
    {
        [Tooltip("+1 = klappt nach rechts (+x) auf, -1 = nach links")]
        [SerializeField] int richtung = 1;
        [SerializeField] bool offen;
        [SerializeField] Transform blatt;
        [SerializeField] Collider2D sperre;

        public bool Offen => offen;

        void Start() => Anwenden();

        public override bool CanInteract(PlayerInteractor who)
        {
            if (!isActiveAndEnabled) return false;
            // Nicht zuklappen, solange jemand im Durchgang steht
            if (offen && sperre != null && who != null)
            {
                var b = sperre.bounds;
                b.Expand(new Vector3(-0.1f, -0.1f, 0f));
                if (b.Contains(new Vector3(who.transform.position.x, who.transform.position.y, b.center.z))) return false;
            }
            return true;
        }

        public override void Interact(PlayerInteractor who)
        {
            offen = !offen;
            Anwenden();
        }

        void Anwenden()
        {
            if (blatt != null) blatt.localRotation = Quaternion.Euler(0f, 0f, offen ? 90f * richtung : 0f);
            if (sperre != null) sperre.enabled = !offen;
        }
    }
}
