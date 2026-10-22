using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>
    /// Waehlt regelmaessig das Behavior mit der hoechsten Prioritaet, das gerade laufen will,
    /// und gibt ihm die Kontrolle ueber den NpcMover. Behaviors sind einzelne Komponenten am selben GameObject,
    /// dadurch laesst sich jeder NPC frei zusammenstecken (z. B. Folgen + Wandern als Rueckfall).
    /// </summary>
    [RequireComponent(typeof(NpcMover))]
    public class NpcBrain : MonoBehaviour
    {
        [Tooltip("Wie oft (Sekunden) neu entschieden wird, welches Behavior laeuft")]
        [SerializeField] float decisionInterval = 0.25f;

        NpcBehavior[] behaviors;
        float decisionTimer;

        public NpcMover Mover { get; private set; }
        public NpcBehavior Current { get; private set; }

        void Awake()
        {
            Mover = GetComponent<NpcMover>();
            behaviors = GetComponents<NpcBehavior>();
            foreach (var b in behaviors) b.Init(this);
            // Zeitversatz, damit nicht alle NPCs im selben Frame entscheiden
            decisionTimer = Random.value * decisionInterval;
        }

        void Update()
        {
            decisionTimer -= Time.deltaTime;
            if (decisionTimer <= 0f)
            {
                decisionTimer = decisionInterval;
                Decide();
            }
            if (Current != null) Current.Tick();
        }

        void Decide()
        {
            NpcBehavior best = null;
            foreach (var b in behaviors)
            {
                if (!b.enabled || !b.WantsControl()) continue;
                if (best == null || b.Priority > best.Priority) best = b;
            }
            if (best == Current) return;

            if (Current != null) Current.Exit();
            Current = best;
            if (Current == null) Mover.Stop();
            else Current.Enter();
        }

        /// <summary>Sofort neu entscheiden, z. B. nachdem ein Behavior von aussen umgeschaltet wurde.</summary>
        public void ForceDecision() => decisionTimer = 0f;
    }
}
