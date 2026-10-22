using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Aussehen des Autos in 3/4-Ansicht: Sprite je Richtung (von hinten = Norden, Seite = Osten/Westen gespiegelt,
    /// von vorne = Sueden), je 4 Frames (Karosserie wippt, Raeder drehen) und eine Variante mit leuchtenden Bremslichtern.
    /// Stoesst im Leerlauf und bei Fahrt kleine Abgaswoelkchen aus.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class CarVisual : MonoBehaviour
    {
        [SerializeField] CarController car;
        [Tooltip("Je 8 Frames: 0-3 normal, 4-7 Bremslicht")]
        [SerializeField] Sprite[] north = new Sprite[0];
        [SerializeField] Sprite[] east = new Sprite[0];
        [SerializeField] Sprite[] south = new Sprite[0];
        [SerializeField] Sprite[] smoke = new Sprite[0];
        [Tooltip("Bilder pro Sekunde bei voller Fahrt (Raeder)")]
        [SerializeField] float maxFps = 12f;
        [Tooltip("Wippen im Leerlauf")]
        [SerializeField] float idleFps = 3f;
        [SerializeField] float smokeInterval = 0.55f;
        [SerializeField] Transform[] headlights = new Transform[0];

        SpriteRenderer sr;
        float frameTime;
        int frame;
        float smokeTimer;
        int dir; // 0 N, 1 E, 2 S, 3 W

        void Awake()
        {
            sr = GetComponent<SpriteRenderer>();
            if (car == null) car = GetComponentInParent<CarController>();
        }

        void LateUpdate()
        {
            float h = Mathf.Repeat(car.Heading, 360f);
            // Hysterese, damit es an der 45-Grad-Grenze nicht flackert
            int want = h < 45f || h >= 315f ? 0 : h < 135f ? 3 : h < 225f ? 2 : 1;
            float center = want == 0 ? 0f : want == 3 ? 90f : want == 2 ? 180f : 270f;
            if (want != dir && Mathf.Abs(Mathf.DeltaAngle(h, center)) < 38f) dir = want;

            bool running = car.HasDriver && car.EngineOn;
            float speed01 = Mathf.Clamp01(Mathf.Abs(car.Speed) / 4.4f);
            float fps = speed01 > 0.02f ? Mathf.Lerp(4f, maxFps, speed01) : running ? idleFps : 0f;
            if (fps > 0f)
            {
                frameTime += Time.deltaTime * fps;
                while (frameTime >= 1f) { frameTime -= 1f; frame = (frame + 1) % 4; }
            }
            else frame = 0;

            var set = dir == 0 ? north : dir == 2 ? south : east;
            int index = frame + (car.Braking ? 4 : 0);
            if (set.Length > index) sr.sprite = set[index];
            sr.flipX = dir == 3;

            foreach (var l in headlights) if (l != null) l.rotation = Quaternion.Euler(0f, 0f, car.Heading);

            if (running) Smoke(speed01);
        }

        void Smoke(float speed01)
        {
            if (smoke.Length == 0 || dir == 2) return; // von vorne ist der Auspuff verdeckt
            smokeTimer -= Time.deltaTime * (1f + speed01);
            if (smokeTimer > 0f) return;
            smokeTimer = smokeInterval * Random.Range(0.8f, 1.2f);
            Vector3 local = dir == 0 ? new Vector3(0.28f, -0.78f, 0f) : new Vector3(dir == 1 ? -1.3f : 1.3f, -0.38f, 0f);
            var go = new GameObject("Abgas");
            go.transform.position = transform.position + local;
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
