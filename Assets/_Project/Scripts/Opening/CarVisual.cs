using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Aussehen des Pickups in 3/4-Ansicht: ein Blatt mit 8 Richtungen (E, NE, N, NW, W, SW, S, SE), je 8 Bildern
    /// (0-3 Fahrt: Raeder drehen, Karosserie wippt; 4-7 dasselbe mit leuchtenden Bremslichtern).
    /// Das Sprite dreht sich nicht, es wird je nach Fahrtrichtung die passende Ansicht gewaehlt.
    /// Im Leerlauf (Motor an) wippt das Auto leicht, in Fahrt und beim Anrollen stoesst es kleine Abgaswoelkchen aus.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class CarVisual : MonoBehaviour
    {
        const int Frames = 8;

        [SerializeField] CarController car;
        [Tooltip("8 Richtungen x 8 Bilder (Richtung E, NE, N, NW, W, SW, S, SE), je 8 Bilder: 0-3 normal, 4-7 Bremslicht")]
        [SerializeField] Sprite[] sheet = new Sprite[0];
        [SerializeField] Sprite[] smoke = new Sprite[0];
        [Tooltip("Bilder pro Sekunde bei voller Fahrt (Raeder)")]
        [SerializeField] float maxFps = 12f;
        [Tooltip("Wippen im Leerlauf (Hertz)")]
        [SerializeField] float idleFps = 3f;
        [SerializeField] float smokeInterval = 0.55f;
        [SerializeField] Transform[] headlights = new Transform[0];
        [Tooltip("Auspuffende relativ zur Automitte (Welteinheiten, x nach links, y nach vorne)")]
        [SerializeField] Vector2 exhaust = new Vector2(0.45f, -1.55f);

        SpriteRenderer sr;
        float frameTime;
        int frame;
        float smokeTimer;
        float idleTime;
        int dir = 2; // Index im Blatt: 0 E, 1 NE, 2 N ...

        void Awake()
        {
            sr = GetComponent<SpriteRenderer>();
            if (car == null) car = GetComponentInParent<CarController>();
        }

        void LateUpdate()
        {
            // Blickrichtung als Mathe-Winkel (0 = rechts, 90 = oben); mit Hysterese, damit es an der Grenze nicht flackert
            float phi = Mathf.Repeat(car.Heading + 90f, 360f);
            int want = Mathf.RoundToInt(phi / 45f) % 8;
            if (want != dir && Mathf.Abs(Mathf.DeltaAngle(phi, dir * 45f)) > 30f) dir = want;

            bool running = car.HasDriver && car.EngineOn;
            float speed01 = Mathf.Clamp01(Mathf.Abs(car.Speed) / 4.4f);
            bool rolling = speed01 > 0.02f;
            float fps = rolling ? Mathf.Lerp(4f, maxFps, speed01) : 0f;
            if (fps > 0f)
            {
                frameTime += Time.deltaTime * fps;
                while (frameTime >= 1f) { frameTime -= 1f; frame = (frame + 1) % 4; }
            }
            else frame = 0;

            // Leerlauf: Motor wackelt das Auto um einen Bildpunkt
            Vector3 lp = Vector3.zero;
            if (!rolling && running)
            {
                idleTime += Time.deltaTime * idleFps;
                if (Mathf.Repeat(idleTime, 1f) > 0.5f) lp.y = 1f / 32f;
            }
            sr.transform.localPosition = lp;

            int index = dir * Frames + frame + (car.Braking ? 4 : 0);
            if (sheet.Length > index) sr.sprite = sheet[index];

            foreach (var l in headlights) if (l != null) l.rotation = Quaternion.Euler(0f, 0f, car.Heading);

            if (running) Smoke(speed01);
        }

        void Smoke(float speed01)
        {
            if (smoke.Length == 0) return;
            smokeTimer -= Time.deltaTime * (1f + speed01);
            if (smokeTimer > 0f) return;
            smokeTimer = smokeInterval * Random.Range(0.8f, 1.2f);
            Vector3 at = transform.position + (Vector3)(car.Left * exhaust.x + car.Forward * exhaust.y) + new Vector3(0f, 0.3f, 0f);
            var go = new GameObject("Abgas");
            go.transform.position = at;
            var s = go.AddComponent<SpriteRenderer>();
            s.sprite = smoke[0];
            s.sortingOrder = sr.sortingOrder - 1;
            s.sharedMaterial = sr.sharedMaterial;
            var puff = go.AddComponent<SmokePuff>();
            Vector2 drift = -car.Forward * (0.2f + speed01 * 0.6f) + Vector2.up * 0.25f;
            puff.Init(smoke, drift);
        }
    }

    /// <summary>Ein Abgaswoelkchen: waechst in Frames, treibt nach hinten oben und verschwindet.</summary>
    public class SmokePuff : MonoBehaviour
    {
        Sprite[] frames;
        Vector2 drift;
        float t;
        SpriteRenderer sr;

        public void Init(Sprite[] f, Vector2 velocity)
        {
            frames = f;
            drift = velocity;
            sr = GetComponent<SpriteRenderer>();
        }

        void Update()
        {
            t += Time.deltaTime;
            transform.position += (Vector3)(drift * Time.deltaTime);
            const float life = 0.9f;
            int i = Mathf.Min(frames.Length - 1, (int)(t / life * frames.Length));
            sr.sprite = frames[i];
            var c = sr.color;
            c.a = Mathf.Clamp01(1.2f - t / life) * 0.7f;
            sr.color = c;
            if (t >= life) Destroy(gameObject);
        }
    }
}
