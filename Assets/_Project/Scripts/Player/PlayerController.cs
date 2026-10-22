using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Player
{
    /// <summary>
    /// WASD-Bewegung in 8 Richtungen und Animation (idle / walk / punch).
    /// Die Eingabe wird normalisiert, damit diagonales Laufen genauso schnell ist wie gerades.
    ///
    /// Gemuetlich statt zackig: Die Figur beschleunigt und bremst weich, Richtungswechsel laufen als kleine Kurve.
    /// Die Blickrichtung folgt der tatsaechlichen Bewegung mit etwas Traegheit (Hysterese + Mindestdauer),
    /// so flackert sie bei schnellem Wechsel von S und D nicht zwischen Sueden, Osten und Suedosten.
    /// Laesst man zwei Tasten fast gleichzeitig los, bleibt die schraege Richtung stehen.
    /// Die Laufanimation laeuft passend zur Geschwindigkeit, damit die Fuesse nicht rutschen.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class PlayerController : MonoBehaviour
    {
        // Reihenfolge entspricht Winkelsektoren: 0 Grad = Ost, gegen den Uhrzeigersinn
        static readonly string[] DirNames = { "E", "NE", "N", "NW", "W", "SW", "S", "SE" };
        // Zustandsnamen vorab, damit pro Frame kein String gebaut wird (vermeidet GC-Ruckler)
        static readonly string[] WalkStates = System.Array.ConvertAll(DirNames, d => "walk_" + d);
        static readonly string[] IdleStates = System.Array.ConvertAll(DirNames, d => "idle_" + d);
        static readonly string[] RunStates = System.Array.ConvertAll(DirNames, d => "run_" + d);
        static readonly string[] SprintStates = System.Array.ConvertAll(DirNames, d => "sprint_" + d);
        static readonly string[] DodgeStates = System.Array.ConvertAll(DirNames, d => "dodge_" + d);
        static readonly Vector2[] DirVectors =
        {
            new Vector2(1, 0), new Vector2(1, 1).normalized, new Vector2(0, 1), new Vector2(-1, 1).normalized,
            new Vector2(-1, 0), new Vector2(-1, -1).normalized, new Vector2(0, -1), new Vector2(1, -1).normalized,
        };

        [SerializeField] Animator animator;
        [Tooltip("Geschwindigkeit in Units (= Kacheln) pro Sekunde")]
        [SerializeField] float moveSpeed = 2.8f;
        [Tooltip("Faktor fuer die Geschwindigkeit waehrend eines Schlags (0 = stehen bleiben)")]
        [SerializeField, Range(0f, 1f)] float attackMoveMultiplier = 0f;

        [Header("Gefuehl")]
        [Tooltip("Units/s pro Sekunde beim Anlaufen (hoeher = schneller auf Tempo)")]
        [SerializeField] float acceleration = 22f;
        [Tooltip("Units/s pro Sekunde beim Abbremsen")]
        [SerializeField] float deceleration = 28f;
        [Tooltip("Glaettung der Eingaberichtung in Sekunden: schnelles Wechseln zwischen S und D wird zu einer weichen Schraege")]
        [SerializeField] float inputSmoothTime = 0.05f;
        [Tooltip("Wie weit (Grad) die Bewegung ueber die Grenze eines Richtungssektors hinaus muss, bevor die Figur sich umdreht")]
        [SerializeField, Range(0f, 20f)] float facingHysteresis = 10f;
        [Tooltip("So lange bleibt eine neue Blickrichtung mindestens, bevor die naechste kommt")]
        [SerializeField] float minFacingTime = 0.08f;
        [Tooltip("Loslassen zweier Tasten innerhalb dieser Zeit zaehlt als gleichzeitig (Schraegrichtung bleibt)")]
        [SerializeField] float releaseGrace = 0.08f;
        [Tooltip("Bei diesem Tempo laeuft die Laufanimation in Originalgeschwindigkeit (danach wurde sie gezeichnet)")]
        [SerializeField] float animationReferenceSpeed = 3.5f;

        [Header("Lauf-Animationen (als Vielfaches der normalen Gehgeschwindigkeit moveSpeed)")]
        [Tooltip("Ab diesem Vielfachen wechselt walk zu run (nur wenn der Controller run-Zustaende hat)")]
        [SerializeField] float runFromRatio = 1.2f;
        [Tooltip("Ab diesem Vielfachen wechselt run zu sprint")]
        [SerializeField] float sprintFromRatio = 1.45f;
        [Tooltip("Bei diesem Vielfachen der Lauf-Referenz laufen run bzw. sprint in Originalgeschwindigkeit")]
        [SerializeField] float runReferenceRatio = 1.4f;
        [SerializeField] float sprintReferenceRatio = 1.6f;

        Rigidbody2D body;
        Vector2 rawInput;
        Vector2 moveInput;
        Vector2 heldDiagonal;
        float releaseTimer;
        Vector2 velocity;
        Vector2 smoothInput;
        int facing = 6; // Start: Sueden
        float facingTimer;
        string currentState;

        public bool IsAttacking { get; private set; }
        /// <summary>Waehrend der Ausweich-Rolle (Animation dodge_*).</summary>
        public bool IsDodging { get; private set; }
        float dodgeEnd;
        /// <summary>Keine Bewegung/Angriffe, z. B. waehrend eines Dialogs.</summary>
        public bool InputLocked { get; set; }
        /// <summary>
        /// Gesteuerte Bewegung in Zwischensequenzen: wirkt wie gedrueckte Laufrichtung (die Laenge ist egal, das Tempo steuert SpeedMultiplier),
        /// auch wenn die Eingabe gesperrt ist. Physik, Kollision und Laufanimation laufen dabei ganz normal.
        /// </summary>
        public Vector2 ScriptedInput { get; set; }
        /// <summary>Tempo bei gesteuerter Bewegung (Units/s). 0 = normales Lauftempo.</summary>
        public float ScriptedSpeed { get; set; }
        public Vector2 FacingVector => DirVectors[facing];
        public Vector2 Velocity => body.linearVelocity;
        /// <summary>Gewollte Geschwindigkeit aus der Eingabe. Anders als Velocity auch dann, wenn er gerade gegen etwas laeuft.</summary>
        public Vector2 DesiredVelocity => moveInput * CurrentMaxSpeed;
        public float MoveSpeed { get => moveSpeed; set => moveSpeed = value; }
        /// <summary>Faktor auf die Geschwindigkeit von aussen (Sprint, Schleichen, Zustaende wie Hunger oder Verletzung).</summary>
        public float SpeedMultiplier { get; set; } = 1f;
        /// <summary>Taumeln (z. B. Rausch): 0 = keins, 1 = stark. Lenkt die Bewegung seitlich ab, solange der Spieler laeuft.</summary>
        public float Sway { get; set; }
        /// <summary>Eingaberichtung (0 = keine Taste).</summary>
        public Vector2 MoveInput => moveInput;

        float CurrentMaxSpeed => ScriptedInput.sqrMagnitude > 0.0001f && ScriptedSpeed > 0f
            ? ScriptedSpeed
            : (IsAttacking ? moveSpeed * attackMoveMultiplier : moveSpeed) * SpeedMultiplier;

        /// <summary>Kurzer Stoss in eine Richtung (Ausweichen, Rueckstoss). Die Geschwindigkeit bremst danach normal ab.</summary>
        public void Kick(Vector2 direction, float speed)
        {
            if (direction.sqrMagnitude < 0.0001f) return;
            velocity = direction.normalized * speed;
            // Auch die Physik-Geschwindigkeit setzen, sonst nimmt FixedUpdate den (noch kleineren) echten Wert wieder an
            body.linearVelocity = velocity;
        }

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            if (animator == null) animator = GetComponentInChildren<Animator>();
        }

        void Update()
        {
            ReadInput();
            facingTimer += Time.deltaTime;
            if (IsDodging && Time.time >= dodgeEnd) EndDodge();
            if (!IsAttacking && !IsDodging) UpdateAnimation();
        }

        void FixedUpdate()
        {
            // Richtung weich nachziehen (nicht die Laenge: Loslassen bremst ueber deceleration)
            float k = inputSmoothTime > 0f ? 1f - Mathf.Exp(-Time.fixedDeltaTime / inputSmoothTime) : 1f;
            // Umkehr (z. B. S -> N) nicht durch die Mitte glaetten, das gaebe einen Schlenker zur Seite; das Bremsen uebernimmt deceleration
            if (moveInput == Vector2.zero || Vector2.Dot(smoothInput, moveInput) < -0.3f) smoothInput = moveInput;
            else smoothInput = Vector2.Lerp(smoothInput, moveInput, k);
            Vector2 dir = smoothInput.sqrMagnitude > 0.0001f ? smoothInput.normalized : Vector2.zero;
            Vector2 target = dir * CurrentMaxSpeed;
            // Bremsen, wenn kein Ziel oder das Ziel gegen die aktuelle Richtung zeigt; sonst normal beschleunigen
            bool braking = target.sqrMagnitude < 0.0001f || Vector2.Dot(target, velocity) < 0f;
            float rate = braking ? deceleration : acceleration;
            // An Hindernissen nicht weiter "anschieben": die echte Geschwindigkeit nach der Physik zaehlt
            if (body.linearVelocity.sqrMagnitude < velocity.sqrMagnitude) velocity = body.linearVelocity;
            velocity = Vector2.MoveTowards(velocity, target, rate * Time.fixedDeltaTime);
            body.linearVelocity = velocity;
        }

        void ReadInput()
        {
            var kb = Keyboard.current;
            rawInput = Vector2.zero;
            if (kb != null && !InputLocked)
            {
                if (kb.dKey.isPressed) rawInput.x += 1f;
                if (kb.aKey.isPressed) rawInput.x -= 1f;
                if (kb.wKey.isPressed) rawInput.y += 1f;
                if (kb.sKey.isPressed) rawInput.y -= 1f;
            }

            if (ScriptedInput.sqrMagnitude > 0.0001f) rawInput = ScriptedInput;

            // Von schraeg auf gerade gewechselt (eine Taste losgelassen)? Kurz die Schraege halten:
            // Wird kurz danach auch die zweite Taste losgelassen, war es ein gemeinsames Loslassen
            bool diagonal = rawInput.x != 0f && rawInput.y != 0f;
            bool single = !diagonal && rawInput != Vector2.zero;
            if (diagonal) { heldDiagonal = rawInput; releaseTimer = 0f; }
            Vector2 input = rawInput;
            if (single && heldDiagonal != Vector2.zero && (rawInput.x == heldDiagonal.x || rawInput.y == heldDiagonal.y) && releaseTimer < releaseGrace)
            {
                releaseTimer += Time.deltaTime;
                input = heldDiagonal;
            }
            else if (!diagonal && rawInput != Vector2.zero) heldDiagonal = Vector2.zero;
            if (rawInput == Vector2.zero) heldDiagonal = Vector2.zero;

            // Diagonale hat sonst Laenge 1,41 und waere schneller
            moveInput = input.sqrMagnitude > 1f ? input.normalized : input;

            // Taumeln: sanft hin und her seitlich zur Laufrichtung
            if (Sway > 0.001f && moveInput != Vector2.zero)
            {
                float wave = Mathf.Sin(Time.time * 2.3f) * 0.6f + Mathf.Sin(Time.time * 5.1f + 1.3f) * 0.4f;
                Vector2 side = new Vector2(-moveInput.y, moveInput.x);
                moveInput = Vector2.ClampMagnitude(moveInput + side * (wave * Sway * 0.6f), 1f);
            }
        }

        void UpdateAnimation()
        {
            float speed = velocity.magnitude;
            bool moving = speed > 0.2f;
            if (moving) UpdateFacing(velocity);
            else if (moveInput.sqrMagnitude > 0.01f && facingTimer >= minFacingTime)
            {
                // Aus dem Stand: gleich in die gedrueckte Richtung drehen
                int dir = DirectionIndex(moveInput);
                if (dir != facing) { facing = dir; facingTimer = 0f; }
            }

            // Tempo waehlt die Animation: walk, ab runFromSpeed run, ab sprintFromSpeed sprint (falls der Controller sie hat)
            string[] set = WalkStates;
            float reference = animationReferenceSpeed;
            if (moving && speed >= moveSpeed * sprintFromRatio && animator.HasState(0, Animator.StringToHash(SprintStates[facing]))) { set = SprintStates; reference = animationReferenceSpeed * sprintReferenceRatio; }
            else if (moving && speed >= moveSpeed * runFromRatio && animator.HasState(0, Animator.StringToHash(RunStates[facing]))) { set = RunStates; reference = animationReferenceSpeed * runReferenceRatio; }
            string state = moving ? set[facing] : IdleStates[facing];
            // Wechsel zwischen walk/run/sprint und Richtungswechsel behalten die Position im Laufzyklus bei (gleiche Bildanzahl)
            bool wasLocomotion = currentState != null && (System.Array.IndexOf(WalkStates, currentState) >= 0
                || System.Array.IndexOf(RunStates, currentState) >= 0 || System.Array.IndexOf(SprintStates, currentState) >= 0);
            Play(state, keepTime: moving && wasLocomotion, force: false);
            // Laufanimation an das Tempo koppeln (Anlaufen = langsamere Schritte), sonst normale Geschwindigkeit
            animator.speed = moving ? Mathf.Clamp(speed / Mathf.Max(0.1f, reference), 0.45f, 1.3f) : 1f;
        }

        // Neue Richtung erst, wenn die Bewegung deutlich im neuen Sektor liegt und die alte eine Weile stand
        void UpdateFacing(Vector2 v)
        {
            float a = Mathf.Atan2(v.y, v.x) * Mathf.Rad2Deg;
            float fromCurrent = Mathf.Abs(Mathf.DeltaAngle(a, facing * 45f));
            if (fromCurrent <= 22.5f + facingHysteresis) return;
            if (facingTimer < minFacingTime) return;
            facing = DirectionIndex(v);
            facingTimer = 0f;
        }

        void Play(string state, bool keepTime, bool force)
        {
            if (!force && state == currentState) return;
            float t = keepTime ? Mathf.Repeat(animator.GetCurrentAnimatorStateInfo(0).normalizedTime, 1f) : 0f;
            animator.Play(state, 0, t);
            currentState = state;
        }

        /// <summary>Startet die Schlag-Animation in Zielrichtung. combo = 1..3.</summary>
        public void BeginAttack(int combo, Vector2 aim) => BeginAttack("punch" + combo, aim);

        /// <summary>Startet eine Angriffs-Animation (Zustand "&lt;anim&gt;_&lt;Richtung&gt;", z. B. knife1, bat, shoot) in Zielrichtung.</summary>
        public void BeginAttack(string anim, Vector2 aim)
        {
            EndDodge();
            facing = DirectionIndex(aim);
            facingTimer = 0f;
            IsAttacking = true;
            animator.speed = 1f;
            Play($"{anim}_{DirNames[facing]}", keepTime: false, force: true);
        }

        /// <summary>Ausweich-Rolle in Richtung dir: spielt dodge_* fuer duration Sekunden.</summary>
        public void BeginDodge(Vector2 dir, float duration)
        {
            if (dir.sqrMagnitude > 0.0001f) facing = DirectionIndex(dir);
            facingTimer = 0f;
            IsDodging = true;
            dodgeEnd = Time.time + duration;
            animator.speed = 1f;
            if (animator.HasState(0, Animator.StringToHash(DodgeStates[facing]))) Play(DodgeStates[facing], keepTime: false, force: true);
        }

        void EndDodge()
        {
            if (!IsDodging) return;
            IsDodging = false;
            currentState = null;
        }

        public void EndAttack()
        {
            IsAttacking = false;
            currentState = null; // naechster Update waehlt idle/walk neu
        }

        /// <summary>Im Stehen in eine Richtung schauen, z. B. zum Gespraechspartner.</summary>
        public void FaceTowards(Vector2 direction)
        {
            if (direction.sqrMagnitude < 0.0001f) return;
            facing = DirectionIndex(direction);
            facingTimer = 0f;
            currentState = null; // naechster Update spielt idle in neuer Richtung
        }

        public static int DirectionIndex(Vector2 v)
        {
            if (v.sqrMagnitude < 0.0001f) return 6;
            float angle = Mathf.Atan2(v.y, v.x) * Mathf.Rad2Deg;
            if (angle < 0f) angle += 360f;
            return Mathf.RoundToInt(angle / 45f) % 8;
        }

        public static Vector2 Quantize(Vector2 v) => DirVectors[DirectionIndex(v)];

        /// <summary>Auf eine der vier Himmelsrichtungen runden (rechts, links, oben, unten). Bei Gleichstand gewinnt die Waagerechte.</summary>
        public static Vector2 Cardinal(Vector2 v)
        {
            if (v.sqrMagnitude < 0.0001f) return Vector2.down;
            if (Mathf.Abs(v.x) >= Mathf.Abs(v.y)) return v.x >= 0f ? Vector2.right : Vector2.left;
            return v.y >= 0f ? Vector2.up : Vector2.down;
        }
    }
}
