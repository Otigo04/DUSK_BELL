using UnityEngine;

namespace Nightward.Core
{
    /// <summary>
    /// Weiche Kamera-Verfolgung wie in gemuetlichen Spielen: folgt der Figur mit etwas Verzoegerung,
    /// schaut ein Stueck in Laufrichtung voraus (das Vorausschauen kommt und geht noch langsamer, damit nichts ruckt)
    /// und kann sanft auf einen zweiten Punkt schwenken, z. B. die Mitte zwischen Spieler und Gespraechspartner.
    /// Kurze Stoesse (Shake) fuer Treffer werden obendrauf gerechnet und stoeren das Folgen nicht.
    /// Optional auf die Levelgrenzen begrenzt. Den Zoom bestimmt die Pixel Perfect Camera (Referenzaufloesung).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class CameraFollow2D : MonoBehaviour
    {
        /// <summary>Die Kamera, die gerade folgt (fuer Dialoge, Zwischensequenzen ...).</summary>
        public static CameraFollow2D Main { get; private set; }

        [SerializeField] Transform target;
        [SerializeField] Vector2 offset = new Vector2(0f, 0.7f);
        [Tooltip("Verzoegerung beim Folgen in Sekunden (hoeher = traeger, gemuetlicher)")]
        [SerializeField] float smoothTime = 0.22f;
        [Header("Vorausschauen")]
        [Tooltip("So viele Sekunden Laufweg schaut die Kamera voraus")]
        [SerializeField] float lookAheadTime = 0.15f;
        [Tooltip("Hoechstens so viele Units voraus")]
        [SerializeField] float maxLookAhead = 0.4f;
        [Tooltip("Wie traege das Vorausschauen sich aendert")]
        [SerializeField] float lookAheadSmoothTime = 0.9f;
        [Header("Stoss (Shake)")]
        [Tooltip("Wie schnell ein Stoss abklingt (pro Sekunde)")]
        [SerializeField] float shakeDecay = 1.6f;
        [SerializeField] float shakeFrequency = 22f;
        [Header("Fokus (z. B. Dialog)")]
        [SerializeField] float focusSmoothTime = 0.6f;
        [Header("Begrenzung (Weltkoordinaten)")]
        [SerializeField] bool clampToBounds = true;
        [SerializeField] Vector2 boundsMin = new Vector2(-6f, -6f);
        [SerializeField] Vector2 boundsMax = new Vector2(54f, 38f);

        Camera cam;
        Rigidbody2D targetBody;
        Vector3 velocity;
        Vector2 lookAhead, lookAheadVelocity;
        Transform focus;
        float focusWeight, focusTarget, focusVelocity;
        Vector2 lastFocusPos;
        Vector3 basePos;        // Position ohne Stoss: daran wird weich weitergefolgt
        float trauma, shakeStrength, shakeSeed;

        void Awake()
        {
            cam = GetComponent<Camera>();
            Main = this;
        }

        void OnDestroy()
        {
            if (Main == this) Main = null;
        }

        void Start()
        {
            if (target == null)
            {
                var player = GameObject.FindWithTag("Player");
                if (player != null) target = player.transform;
            }
            if (target != null)
            {
                targetBody = target.GetComponent<Rigidbody2D>();
                transform.position = basePos = Clamp(Desired());
            }
        }

        /// <summary>Versatz der Kamera zum Ziel (die Bildmitte liegt Offset ueber dem Fokuspunkt).</summary>
        public Vector2 Offset => offset;

        /// <summary>Sanft auf die Mitte zwischen Ziel und point schwenken (weight 0 = nur Ziel, 1 = nur point).</summary>
        public void SetFocus(Transform point, float weight = 0.5f)
        {
            focus = point;
            focusTarget = point != null ? Mathf.Clamp01(weight) : 0f;
            if (point != null) lastFocusPos = point.position;
        }

        public void ClearFocus() => focusTarget = 0f;

        /// <summary>Kurzer Kamerastoss. strength in Units (0,05 = leicht), duration grob in Sekunden.</summary>
        public void Shake(float strength, float duration)
        {
            shakeStrength = Mathf.Max(shakeStrength * trauma, strength);
            trauma = 1f;
            shakeDecay = 1f / Mathf.Max(0.02f, duration);
            shakeSeed = Random.value * 100f;
        }

        /// <summary>Sofort auf das Ziel springen, z. B. nach einem Teleport oder Szenenwechsel.</summary>
        public void Snap()
        {
            if (target == null) return;
            velocity = Vector3.zero;
            lookAhead = lookAheadVelocity = Vector2.zero;
            transform.position = basePos = Clamp(Desired());
        }

        void LateUpdate()
        {
            if (target == null) return;
            float dt = Time.deltaTime;

            Vector2 moving = targetBody != null ? targetBody.linearVelocity : Vector2.zero;
            Vector2 wantedAhead = Vector2.ClampMagnitude(moving * lookAheadTime, maxLookAhead);
            lookAhead = Vector2.SmoothDamp(lookAhead, wantedAhead, ref lookAheadVelocity, lookAheadSmoothTime, Mathf.Infinity, dt);

            focusWeight = Mathf.SmoothDamp(focusWeight, focusTarget, ref focusVelocity, focusSmoothTime, Mathf.Infinity, dt);
            if (focus != null) lastFocusPos = focus.position;

            if (basePos == Vector3.zero) basePos = transform.position;
            basePos = Clamp(Vector3.SmoothDamp(basePos, Desired(), ref velocity, smoothTime, Mathf.Infinity, dt));

            Vector3 shake = Vector3.zero;
            if (trauma > 0f)
            {
                trauma = Mathf.Max(0f, trauma - shakeDecay * dt);
                float amount = trauma * trauma * shakeStrength;
                float tt = Time.time * shakeFrequency;
                shake = new Vector3(Mathf.PerlinNoise(shakeSeed, tt) * 2f - 1f, Mathf.PerlinNoise(shakeSeed + 7f, tt) * 2f - 1f, 0f) * amount;
            }
            transform.position = basePos + shake;
        }

        Vector3 Desired()
        {
            Vector2 p = (Vector2)target.position + offset + lookAhead;
            if (focusWeight > 0.001f) p = Vector2.Lerp(p, lastFocusPos + offset, focusWeight);
            return new Vector3(p.x, p.y, transform.position.z);
        }

        Vector3 Clamp(Vector3 p)
        {
            if (!clampToBounds) return p;
            float halfH = cam.orthographicSize, halfW = halfH * cam.aspect;
            p.x = boundsMax.x - boundsMin.x <= halfW * 2f ? (boundsMin.x + boundsMax.x) * 0.5f : Mathf.Clamp(p.x, boundsMin.x + halfW, boundsMax.x - halfW);
            p.y = boundsMax.y - boundsMin.y <= halfH * 2f ? (boundsMin.y + boundsMax.y) * 0.5f : Mathf.Clamp(p.y, boundsMin.y + halfH, boundsMax.y - halfH);
            return p;
        }
    }
}
