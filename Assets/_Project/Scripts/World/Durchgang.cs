using Nightward.Core;
using Nightward.Interaction;
using UnityEngine;

namespace Nightward.World
{
    /// <summary>
    /// Tuer zwischen zwei Bereichen derselben Szene (z. B. Aussen und Innenraum): Betritt die Spielfigur den Trigger,
    /// spielt der Bildschirm-Uebergang (BildUebergang), in der Mitte wird sie zum Ziel gesetzt und die Kamera springt mit.
    /// Waehrenddessen ist die Spielfigur gesperrt. Eine kurze Sperre verhindert Hin-und-her-Springen.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Durchgang : MonoBehaviour
    {
        [SerializeField] Transform ziel;
        [SerializeField] float sperre = 0.6f;

        static float gesperrtBis;

        void Reset() => GetComponent<Collider2D>().isTrigger = true;

        void OnTriggerEnter2D(Collider2D other)
        {
            if (ziel == null || Time.time < gesperrtBis || !other.CompareTag("Player")) return;
            var uebergang = BildUebergang.Instance;
            if (uebergang != null && uebergang.Laeuft) return;

            var body = other.attachedRigidbody;
            var t = body != null ? body.transform : other.transform;
            var interactor = t.GetComponent<PlayerInteractor>();
            gesperrtBis = float.MaxValue;
            if (interactor != null) interactor.Lock(true);
            if (body != null) body.linearVelocity = Vector2.zero;

            void Teleport()
            {
                t.position = ziel.position;
                if (body != null)
                {
                    body.position = ziel.position;
                    body.linearVelocity = Vector2.zero;
                }
                Physics2D.SyncTransforms();
                if (CameraFollow2D.Main != null) CameraFollow2D.Main.Snap();
            }

            void Fertig()
            {
                if (interactor != null) interactor.Lock(false);
                gesperrtBis = Time.time + sperre;
            }

            if (uebergang != null) uebergang.Spielen(Teleport, Fertig);
            else
            {
                Teleport();
                Fertig();
            }
        }
    }
}
