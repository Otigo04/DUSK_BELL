using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>Laeuft eine feste Route aus Wegpunkten ab, im Kreis oder hin und zurueck.</summary>
    public class PatrolBehavior : NpcBehavior
    {
        [SerializeField] Transform[] waypoints;
        [Tooltip("Aus = am Ende umdrehen (A-B-C-B-A), an = von vorne (A-B-C-A)")]
        [SerializeField] bool loop = true;
        [SerializeField] Vector2 waitTime = new Vector2(0.5f, 2f);
        [SerializeField, Range(0.2f, 1.5f)] float speedMultiplier = 0.8f;

        int index;
        int step = 1;
        float waitTimer;
        bool walking;

        void Reset() => priority = 10;

        public override bool WantsControl() => waypoints != null && waypoints.Length > 0;

        public override void Enter()
        {
            index = NearestWaypoint();
            walking = false;
            waitTimer = 0f;
        }

        public override void Tick()
        {
            if (walking)
            {
                if (!Mover.HasArrived) return;
                walking = false;
                waitTimer = Random.Range(waitTime.x, waitTime.y);
                Advance();
            }

            waitTimer -= Time.deltaTime;
            if (waitTimer > 0f) return;

            var wp = waypoints[index];
            if (wp == null) { Advance(); return; }
            Mover.SetDestination(wp.position, speedMultiplier);
            walking = true;
        }

        void Advance()
        {
            if (waypoints.Length == 1) return;
            if (loop) { index = (index + 1) % waypoints.Length; return; }
            if (index + step < 0 || index + step >= waypoints.Length) step = -step;
            index += step;
        }

        int NearestWaypoint()
        {
            int best = 0;
            float bestDist = float.MaxValue;
            for (int i = 0; i < waypoints.Length; i++)
            {
                if (waypoints[i] == null) continue;
                float d = ((Vector2)waypoints[i].position - Mover.Position).sqrMagnitude;
                if (d < bestDist) { bestDist = d; best = i; }
            }
            return best;
        }

        void OnDrawGizmosSelected()
        {
            if (waypoints == null) return;
            Gizmos.color = new Color(0.7f, 0.5f, 1f, 0.8f);
            for (int i = 0; i < waypoints.Length; i++)
            {
                if (waypoints[i] == null) continue;
                Gizmos.DrawWireSphere(waypoints[i].position, 0.2f);
                int next = i + 1;
                if (next >= waypoints.Length) { if (!loop) break; next = 0; }
                if (waypoints[next] != null) Gizmos.DrawLine(waypoints[i].position, waypoints[next].position);
            }
        }
    }
}
