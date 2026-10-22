using Nightward.Combat;
using Nightward.Dialogue;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.NPC
{
    /// <summary>
    /// Monster in Verkleidung (Monster-Bibel): wandert und spricht wie ein Dorfbewohner, bis die Verkleidung bricht.
    /// Enthuellt wechselt es den Animator-Controller, hoert auf zu reden und jagt den Spieler (FollowBehavior).
    /// Testweise: Schlag enthuellt, jeder weitere Treffer kostet Leben. Taste T schaltet die Enthuellung um.
    /// Die echten Schwaechen (Name aussprechen, Essen reichen) und Kampfregeln sind im Regelwerk v0.2.0 noch offen.
    /// </summary>
    [RequireComponent(typeof(NpcBrain))]
    public class MonsterNpc : MonoBehaviour, IDamageable
    {
        [SerializeField] Animator animator;
        [SerializeField] RuntimeAnimatorController disguisedController;
        [SerializeField] RuntimeAnimatorController revealedController;
        [SerializeField] int health = 3;
        [Tooltip("Testtaste T schaltet Verkleidung/Enthuellung um")]
        [SerializeField] bool testToggleKey = true;

        NpcBrain brain;
        NpcAnimator npcAnimator;
        NpcDialogue dialogue;
        FollowBehavior chase;
        WanderBehavior wander;

        public bool Revealed { get; private set; }

        void Awake()
        {
            brain = GetComponent<NpcBrain>();
            npcAnimator = GetComponent<NpcAnimator>();
            dialogue = GetComponent<NpcDialogue>();
            chase = GetComponent<FollowBehavior>();
            wander = GetComponent<WanderBehavior>();
            if (animator == null) animator = GetComponentInChildren<Animator>();
        }

        void Start() => Apply();

        void Update()
        {
            if (!testToggleKey || Keyboard.current == null || !Keyboard.current.tKey.wasPressedThisFrame) return;
            if (dialogue != null && dialogue.InConversation) return;
            SetRevealed(!Revealed);
        }

        public void SetRevealed(bool revealed)
        {
            if (Revealed == revealed) return;
            Revealed = revealed;
            Apply();
        }

        void Apply()
        {
            var controller = Revealed ? revealedController : disguisedController;
            if (animator != null && controller != null) animator.runtimeAnimatorController = controller;
            if (npcAnimator != null) npcAnimator.ResetState();
            if (chase != null) chase.enabled = Revealed;
            if (wander != null) wander.enabled = !Revealed;
            if (dialogue != null) dialogue.enabled = !Revealed;
            brain.ForceDecision();
        }

        public void TakeDamage(int amount, Vector2 hitDirection)
        {
            if (!Revealed) SetRevealed(true);
            health -= amount;
            if (health <= 0) Destroy(gameObject);
        }
    }
}
