using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>
    /// Schlendert zu zufaelligen erreichbaren Punkten rund um den Heimatpunkt und wartet dazwischen.
    /// Niedrige Prioritaet: typischer Rueckfall, wenn sonst nichts zu tun ist.
    /// </summary>
    public class WanderBehavior : NpcBehavior
    {
        [Tooltip("Mittelpunkt des Bereichs. Leer = Startposition")]
        [SerializeField] Transform home;
        [SerializeField] float radius = 4f;
        [SerializeField] Vector2 waitTime = new Vector2(1.5f, 4f);
        [SerializeField, Range(0.2f, 1.5f)] float speedMultiplier = 0.6f;

        Vector2 homePos;
        float waitTimer;

        void Reset() => priority = 0;

        void Start() => homePos = home != null ? (Vector2)home.position : (Vector2)transform.position;

        public override bool WantsControl() => true;

        public override void Enter() => waitTimer = Random.Range(0f, waitTime.y);

        public override void Tick()
        {
            if (!Mover.HasArrived) return;
            waitTimer -= Time.deltaTime;
            if (waitTimer > 0f) return;

            waitTimer = Random.Range(waitTime.x, waitTime.y);
            var nav = NavGrid.Instance;
            if (nav != null && nav.TryGetRandomPoint(homePos, radius, out var point))
                Mover.SetDestination(point, speedMultiplier);
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(1f, 0.85f, 0.4f, 0.6f);
            Vector3 c = Application.isPlaying ? (Vector3)homePos : (home != null ? home.position : transform.position);
            Gizmos.DrawWireSphere(c, radius);
        }
    }
}
