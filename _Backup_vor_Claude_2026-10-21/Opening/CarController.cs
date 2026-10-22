using Nightward.Interaction;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Opening
{
    /// <summary>
    /// Auto in Draufsicht. Spieler am Steuer: W/Pfeil hoch Gas, S/Pfeil runter bremsen und rueckwaerts,
    /// A/D bzw. Pfeile lenken (nur in Fahrt). Fuer Zwischensequenzen faehrt es per Autopilot auf ein Ziel zu
    /// oder dreht auf der Stelle (Wenden). Waehrend der Fahrt sitzt die Spielfigur unsichtbar im Auto.
    /// Die Kamera folgt ihr; die Figur wird dazu ein Stueck vor das Auto gesetzt, so steht das Auto im unteren
    /// Bildbereich und man sieht, was vorne kommt. Das Sprite dreht sich nicht (3/4-Ansicht, CarVisual waehlt die Richtung).
    /// Zaehlt die gefahrene Strecke (Kilometerzaehler).
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class CarController : MonoBehaviour
    {
        public enum Mode { Parked, Player, Auto }

        [SerializeField] float maxSpeed = 4.4f;
        [SerializeField] float reverseSpeed = 1.6f;
        [SerializeField] float acceleration = 2.6f;
        [SerializeField] float brakeForce = 7f;
        [SerializeField] float rolling = 1.2f;
        [Tooltip("Grad pro Sekunde bei voller Fahrt")]
        [SerializeField] float steerRate = 85f;
        [Tooltip("Kilometerstand beim Start")]
        [SerializeField] double odometerStart = 48213.6;
        [Tooltip("So viele Kilometer zaehlt eine gefahrene Kachel (spuerbar, aber nicht absurd)")]
        [SerializeField] double kmPerUnit = 0.01;
        [Tooltip("Abstand der Fahrertuer zur Mitte (links in Fahrtrichtung), dort steigt die Figur aus")]
        [SerializeField] float doorDistance = 1.05f;
        [Tooltip("So weit schaut die Kamera beim Fahren voraus (Auto steht dann im unteren Bildbereich)")]
        [SerializeField] float cameraLead = 2.4f;
        [SerializeField] OpeningAudio audioPlayer;

        Rigidbody2D body;
        float speed;
        float heading;      // Grad, 0 = Norden (Sprite zeigt nach oben)
        Vector2 autoTarget;
        float autoSpeed;
        bool autoHasTarget;
        float? spinTarget;
        Transform driver;
        Rigidbody2D driverBody;
        Collider2D[] driverColliders;
        Renderer[] driverRenderers;
        float lead;
        bool braking;

        public Mode Current { get; private set; } = Mode.Parked;
        public float Speed => speed;
        public float SpeedLimit { get; set; } = float.MaxValue;
        /// <summary>Motor laeuft (Ton, Wippen, Abgas). Im schwarzen Intro sitzt man schon im Auto, hoert aber nichts.</summary>
        public bool EngineOn { get; set; }
        /// <summary>Aus = S bremst nur bis zum Stillstand (z. B. im Dorf), statt rueckwaerts zu fahren.</summary>
        public bool AllowReverse { get; set; } = true;
        public double Odometer { get; set; }
        public bool HasDriver => driver != null;
        public bool AutoArrived => !autoHasTarget && spinTarget == null;
        public float Heading => heading;
        /// <summary>Bremslichter: Spieler bremst, oder der Autopilot verzoegert.</summary>
        public bool Braking => braking;
        public Vector2 Forward => Quaternion.Euler(0, 0, heading) * Vector2.up;
        public Vector2 Left => Quaternion.Euler(0, 0, heading + 90f) * Vector2.up;
        public Vector3 ExitPoint => SidePoint(doorDistance, 0.1f);

        /// <summary>Punkt neben dem Auto: side = Abstand nach links (Fahrerseite), ahead = nach vorne.</summary>
        public Vector3 SidePoint(float side, float ahead) => (Vector2)transform.position + Left * side + Forward * ahead;

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            body.gravityScale = 0f;
            body.freezeRotation = true;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            heading = transform.eulerAngles.z;
            transform.rotation = Quaternion.identity;
            Odometer = odometerStart;
        }

        // ------------------------------------------------------------ Ein-/Aussteigen

        /// <summary>Figur steigt ein: unsichtbar, keine Kollision, folgt dem Auto.</summary>
        public void Enter(PlayerInteractor player)
        {
            driver = player.transform;
            driverBody = player.GetComponent<Rigidbody2D>();
            driverColliders = player.GetComponentsInChildren<Collider2D>();
            driverRenderers = player.GetComponentsInChildren<Renderer>();
            player.Lock(true);
            foreach (var c in driverColliders) c.enabled = false;
            foreach (var r in driverRenderers) r.enabled = false;
            if (driverBody != null) { driverBody.linearVelocity = Vector2.zero; driverBody.simulated = false; }
            lead = 0f;
            SyncDriver();
        }

        /// <summary>Figur steigt auf der Fahrerseite aus. Gibt die Steuerung nicht automatisch frei.</summary>
        public void Exit(PlayerInteractor player, bool unlock = true)
        {
            if (driver == null) return;
            Current = Mode.Parked;
            speed = 0f;
            body.linearVelocity = Vector2.zero;
            var p = ExitPoint;
            driver.position = p;
            if (driverBody != null) { driverBody.simulated = true; driverBody.position = p; }
            foreach (var c in driverColliders) c.enabled = true;
            foreach (var r in driverRenderers) r.enabled = true;
            player.Controller.FaceTowards(Vector2.down);
            driver = null;
            if (unlock) player.Lock(false);
        }

        void SyncDriver()
        {
            if (driver == null) return;
            lead = Mathf.MoveTowards(lead, cameraLead, Time.deltaTime * 1.2f);
            Vector2 p = (Vector2)transform.position + Forward * lead;
            driver.position = p;
            if (driverBody != null) driverBody.position = p;
        }

        // ------------------------------------------------------------ Steuerung

        public void GiveControl() { Current = Mode.Player; autoHasTarget = false; spinTarget = null; }

        public void Park() { Current = Mode.Parked; autoHasTarget = false; spinTarget = null; }

        /// <summary>Faehrt auf einen Punkt zu und haelt dort an.</summary>
        public void DriveTo(Vector2 target, float atSpeed)
        {
            Current = Mode.Auto;
            autoTarget = target;
            autoSpeed = atSpeed;
            autoHasTarget = true;
            spinTarget = null;
        }

        /// <summary>Wenden: dreht langsam auf die neue Richtung (Grad, 0 = Norden), kriecht dabei etwas.</summary>
        public void TurnTo(float newHeading)
        {
            Current = Mode.Auto;
            autoHasTarget = false;
            spinTarget = newHeading;
        }

        /// <summary>Sofort an einen Ort setzen (z. B. nach einer Ueberblendung).</summary>
        public void Teleport(Vector2 position, float newHeading)
        {
            heading = newHeading;
            speed = 0f;
            body.position = position;
            transform.position = position;
            body.linearVelocity = Vector2.zero;
            SyncDriver();
        }

        void FixedUpdate()
        {
            float dt = Time.fixedDeltaTime;
            float throttle = 0f, steer = 0f;
            float speedBefore = speed;
            var kb = Keyboard.current;

            if (Current == Mode.Player && kb != null)
            {
                if (kb.wKey.isPressed || kb.upArrowKey.isPressed) throttle += 1f;
                if (kb.sKey.isPressed || kb.downArrowKey.isPressed) throttle -= 1f;
                if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) steer += 1f;
                if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) steer -= 1f;
            }
            else if (Current == Mode.Auto)
            {
                if (spinTarget.HasValue)
                {
                    float delta = Mathf.DeltaAngle(heading, spinTarget.Value);
                    float step = 70f * dt;
                    heading += Mathf.Clamp(delta, -step, step);
                    // Beim Wenden ein Stueck zurueck und wieder vor: wirkt wie Lenkeinschlag
                    speed = Mathf.Sin(Mathf.Clamp01(Mathf.Abs(delta) / 180f) * Mathf.PI) * -0.9f;
                    if (Mathf.Abs(delta) < 0.5f) { heading = spinTarget.Value; spinTarget = null; speed = 0f; }
                }
                else if (autoHasTarget)
                {
                    Vector2 to = autoTarget - body.position;
                    float dist = to.magnitude;
                    if (dist < 0.15f) autoHasTarget = false;
                    else
                    {
                        float want = Mathf.Atan2(-to.x, to.y) * Mathf.Rad2Deg;
                        heading = Mathf.MoveTowardsAngle(heading, want, 60f * dt);
                        float target = Mathf.Min(autoSpeed, dist * 1.2f + 0.2f);
                        speed = Mathf.MoveTowards(speed, target, (target > speed ? acceleration : brakeForce) * dt);
                    }
                }
                if (!autoHasTarget && !spinTarget.HasValue) speed = Mathf.MoveTowards(speed, 0f, brakeForce * dt);
            }
            else speed = Mathf.MoveTowards(speed, 0f, brakeForce * dt);

            if (Current == Mode.Player)
            {
                if (throttle > 0f) speed = speed < 0f ? Mathf.MoveTowards(speed, 0f, brakeForce * dt) : speed + acceleration * dt;
                else if (throttle < 0f) speed = speed > 0f ? Mathf.MoveTowards(speed, 0f, brakeForce * dt) : speed - acceleration * 0.6f * dt;
                else speed = Mathf.MoveTowards(speed, 0f, rolling * dt);
                speed = Mathf.Clamp(speed, AllowReverse ? -reverseSpeed : 0f, Mathf.Min(maxSpeed, SpeedLimit));
                // Lenken nur in Fahrt, rueckwaerts andersherum
                float factor = Mathf.Clamp(speed / 2f, -1f, 1f);
                heading += steer * steerRate * factor * dt;
            }
            else if (speed > SpeedLimit) speed = Mathf.MoveTowards(speed, SpeedLimit, brakeForce * dt);

            body.linearVelocity = Forward * speed;
            body.angularVelocity = 0f;
            bool slowing = Mathf.Abs(speed) < Mathf.Abs(speedBefore) - 0.02f;
            braking = driver != null && ((Current == Mode.Player && throttle != 0f && Mathf.Sign(throttle) != Mathf.Sign(speed) && Mathf.Abs(speed) > 0.05f)
                                         || (Current != Mode.Player && slowing)
                                         || (Current == Mode.Player && throttle < 0f && Mathf.Abs(speed) <= 0.05f));
            Odometer += Mathf.Abs(speed) * dt * kmPerUnit;

            if (audioPlayer != null) audioPlayer.Engine(driver != null && EngineOn, Mathf.Clamp01(Mathf.Abs(speed) / maxSpeed));
        }

        void OnCollisionStay2D(Collision2D c)
        {
            // An Baeumen/Waenden nicht weiter Gas "aufstauen"
            if (Current == Mode.Player) speed *= 0.9f;
        }

        void LateUpdate() => SyncDriver();

        /// <summary>Stand wie auf dem Tacho: 6 Stellen, eine Nachkommastelle.</summary>
        public string OdometerText => Odometer.ToString("000000.0", System.Globalization.CultureInfo.InvariantCulture) + " km";
    }
}
