using Nightward.NPC;
using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Trauergast auf dem Dorfplatz: schaut zum Grab, bis das Auto in Sichtweite ist, dann dreht er den Kopf mit dem Auto mit.
    /// Kurze Verzoegerung pro Person, damit sich nicht alle im selben Frame umdrehen.
    /// </summary>
    [RequireComponent(typeof(NpcMover))]
    public class CrowdMember : MonoBehaviour
    {
        [SerializeField] Transform restTarget;
        [SerializeField] float range = 11f;
        [SerializeField] Vector2 reactionDelay = new Vector2(0.1f, 0.9f);

        NpcMover mover;
        float delay;
        float seen;

        public Transform Watch { get; set; }

        void Awake()
        {
            mover = GetComponent<NpcMover>();
            delay = Random.Range(reactionDelay.x, reactionDelay.y);
        }

        public void SetRest(Transform t) => restTarget = t;

        void Update()
        {
            if (mover.IsMoving || !mover.HasArrived) return;
            bool near = Watch != null && Vector2.Distance(Watch.position, transform.position) < range;
            seen = near ? seen + Time.deltaTime : 0f;
            if (near && seen >= delay) mover.LookAt(Watch.position);
            else if (!near && restTarget != null) mover.LookAt(restTarget.position);
        }
    }
}
