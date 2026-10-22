using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>
    /// Folgt einem Ziel (z. B. dem Spieler) mit Abstand. Plant nur neu, wenn sich das Ziel spuerbar bewegt hat,
    /// damit viele Folger nicht jeden Frame A* rechnen.
    /// </summary>
    public class FollowBehavior : NpcBehavior
    {
        [Tooltip("Leer = Objekt mit Tag 'Player' suchen")]
        [SerializeField] Transform target;
        [Tooltip("Ab dieser Entfernung zum Ziel faengt er an zu folgen")]
        [SerializeField] float startRange = 6f;
        [Tooltip("Ist das Ziel weiter weg, gibt er auf. 0 = nie aufgeben")]
        [SerializeField] float giveUpRange = 12f;
        [Tooltip("Hier bleibt er stehen")]
        [SerializeField] float stopDistance = 1.25f;
        [Tooltip("So weit muss sich das Ziel bewegen, bevor neu geplant wird")]
        [SerializeField] float repathDistance = 0.75f;
        [Tooltip("Ab dieser Entfernung laeuft er schneller, um aufzuholen")]
        [SerializeField] float catchUpDistance = 4f;
        [SerializeField] float catchUpSpeedMultiplier = 1.4f;

        Vector2 lastTargetPos;
        bool following;

        public Transform Target { get => target; set => target = value; }

        void Reset() => priority = 50;

        void Start()
        {
            if (target == null)
            {
                var player = GameObject.FindGameObjectWithTag("Player");
                if (player != null) target = player.transform;
            }
        }

        public override bool WantsControl()
        {
            if (target == null) return false;
            float dist = Vector2.Distance(Mover.Position, target.position);
            // Hysterese: einmal am Folgen, bleibt er bis giveUpRange dran
            following = IsActive ? (giveUpRange <= 0f || dist <= giveUpRange) : dist <= startRange;
            return following && (NavGrid.Instance == null || NavGrid.Instance.IsReachable(Mover.Position, target.position));
        }

        public override void Enter() => lastTargetPos = new Vector2(float.MaxValue, float.MaxValue);

        public override void Tick()
        {
            Vector2 goal = target.position;
            float dist = Vector2.Distance(Mover.Position, goal);

            if (dist <= stopDistance)
            {
                if (!Mover.HasArrived) Mover.Stop();
                Mover.LookAt(goal);
                lastTargetPos = new Vector2(float.MaxValue, float.MaxValue); // beim Loslaufen sofort planen
                return;
            }

            bool targetMoved = (goal - lastTargetPos).sqrMagnitude > repathDistance * repathDistance;
            if (!targetMoved && !Mover.HasArrived) return;

            lastTargetPos = goal;
            float speed = dist > catchUpDistance ? catchUpSpeedMultiplier : 1f;
            // Nicht genau auf das Ziel laufen, sondern bis knapp davor
            Vector2 standPoint = goal + (Mover.Position - goal).normalized * (stopDistance * 0.8f);
            Mover.SetDestination(standPoint, speed);
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0.4f, 0.8f, 1f, 0.5f);
            Gizmos.DrawWireSphere(transform.position, startRange);
            if (giveUpRange > 0f)
            {
                Gizmos.color = new Color(1f, 0.4f, 0.4f, 0.4f);
                Gizmos.DrawWireSphere(transform.position, giveUpRange);
            }
        }
    }
}
