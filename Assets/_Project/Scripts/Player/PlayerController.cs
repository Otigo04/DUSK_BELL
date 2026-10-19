using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Player
{
    /// <summary>
    /// WASD-Bewegung in 8 Richtungen und Animation (idle / walk / punch).
    /// Die Eingabe wird normalisiert, damit diagonales Laufen genauso schnell ist wie gerades.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class PlayerController : MonoBehaviour
    {
        // Reihenfolge entspricht Winkelsektoren: 0 Grad = Ost, gegen den Uhrzeigersinn
        static readonly string[] DirNames = { "E", "NE", "N", "NW", "W", "SW", "S", "SE" };
        static readonly Vector2[] DirVectors =
        {
            new Vector2(1, 0), new Vector2(1, 1).normalized, new Vector2(0, 1), new Vector2(-1, 1).normalized,
            new Vector2(-1, 0), new Vector2(-1, -1).normalized, new Vector2(0, -1), new Vector2(1, -1).normalized,
        };

        [SerializeField] Animator animator;
        [Tooltip("Geschwindigkeit in Units (= Kacheln) pro Sekunde")]
        [SerializeField] float moveSpeed = 3.5f;
        [Tooltip("Faktor fuer die Geschwindigkeit waehrend eines Schlags (0 = stehen bleiben)")]
        [SerializeField, Range(0f, 1f)] float attackMoveMultiplier = 0f;

        Rigidbody2D body;
        Vector2 moveInput;
        int facing = 6; // Start: Sueden
        string currentState;

        public bool IsAttacking { get; private set; }
        public Vector2 FacingVector => DirVectors[facing];
        public Vector2 Velocity => body.linearVelocity;

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            if (animator == null) animator = GetComponentInChildren<Animator>();
        }

        void Update()
        {
            ReadInput();
            if (!IsAttacking) UpdateAnimation();
        }

        void FixedUpdate()
        {
            float speed = IsAttacking ? moveSpeed * attackMoveMultiplier : moveSpeed;
            body.linearVelocity = moveInput * speed;
        }

        void ReadInput()
        {
            var kb = Keyboard.current;
            moveInput = Vector2.zero;
            if (kb == null) return;

            if (kb.dKey.isPressed) moveInput.x += 1f;
            if (kb.aKey.isPressed) moveInput.x -= 1f;
            if (kb.wKey.isPressed) moveInput.y += 1f;
            if (kb.sKey.isPressed) moveInput.y -= 1f;

            // Diagonale hat sonst Laenge 1,41 und waere schneller
            if (moveInput.sqrMagnitude > 1f) moveInput.Normalize();
        }

        void UpdateAnimation()
        {
            bool moving = moveInput.sqrMagnitude > 0.01f;
            if (moving) facing = DirectionIndex(moveInput);

            string state = (moving ? "walk_" : "idle_") + DirNames[facing];
            // Richtungswechsel beim Laufen behaelt die Position im Laufzyklus bei
            Play(state, keepTime: moving && currentState != null && currentState.StartsWith("walk_"), force: false);
        }

        void Play(string state, bool keepTime, bool force)
        {
            if (!force && state == currentState) return;
            float t = keepTime ? Mathf.Repeat(animator.GetCurrentAnimatorStateInfo(0).normalizedTime, 1f) : 0f;
            animator.Play(state, 0, t);
            currentState = state;
        }

        /// <summary>Startet die Schlag-Animation in Zielrichtung. combo = 1..3.</summary>
        public void BeginAttack(int combo, Vector2 aim)
        {
            facing = DirectionIndex(aim);
            IsAttacking = true;
            Play($"punch{combo}_{DirNames[facing]}", keepTime: false, force: true);
        }

        public void EndAttack()
        {
            IsAttacking = false;
            currentState = null; // naechster Update waehlt idle/walk neu
        }

        public static int DirectionIndex(Vector2 v)
        {
            if (v.sqrMagnitude < 0.0001f) return 6;
            float angle = Mathf.Atan2(v.y, v.x) * Mathf.Rad2Deg;
            if (angle < 0f) angle += 360f;
            return Mathf.RoundToInt(angle / 45f) % 8;
        }

        public static Vector2 Quantize(Vector2 v) => DirVectors[DirectionIndex(v)];
    }
}
