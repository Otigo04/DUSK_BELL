using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Raben am Baumstamm: einige sitzen auf den Aesten und nicken, andere kreisen langsam darueber.
    /// Ab und zu kraechzt einer (leise). Scare() laesst die sitzenden auffliegen und mitkreisen.
    /// </summary>
    public class Ravens : MonoBehaviour
    {
        [SerializeField] Sprite[] flyFrames = new Sprite[0];
        [SerializeField] Sprite[] sitFrames = new Sprite[0];
        [Tooltip("Sitzplaetze relativ zum Stamm (Weltkoordinaten-Versatz)")]
        [SerializeField] Vector2[] perches = new Vector2[0];
        [SerializeField] int circling = 3;
        [SerializeField] Vector2 circleRadius = new Vector2(4.5f, 1.6f);
        [SerializeField] float circleHeight = 3.2f;
        [SerializeField] OpeningAudio audioPlayer;
        [SerializeField] Vector2 cawInterval = new Vector2(5f, 11f);
        [SerializeField] Material material;

        class Bird
        {
            public SpriteRenderer sr;
            public bool flying;
            public float phase, speed, radiusScale, frameT, nod;
            public Vector3 from;
            public float takeoff; // 0..1 Uebergang vom Sitzplatz in den Kreis
        }

        readonly List<Bird> birds = new List<Bird>();
        float cawTimer;

        void Start()
        {
            foreach (var p in perches) birds.Add(Make(false, (Vector2)transform.position + p));
            for (int i = 0; i < circling; i++)
            {
                var b = Make(true, transform.position);
                b.phase = i * Mathf.PI * 2f / Mathf.Max(1, circling) + Random.value;
                birds.Add(b);
            }
            cawTimer = Random.Range(cawInterval.x, cawInterval.y);
        }

        Bird Make(bool flying, Vector3 pos)
        {
            var go = new GameObject(flying ? "Rabe_Flug" : "Rabe_Sitzt");
            go.transform.SetParent(transform, true);
            go.transform.position = pos;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = flying ? 30 : 5;
            if (material != null) sr.sharedMaterial = material;
            return new Bird
            {
                sr = sr, flying = flying, speed = Random.Range(0.35f, 0.55f), radiusScale = Random.Range(0.75f, 1.15f),
                nod = Random.Range(0f, 3f), takeoff = flying ? 1f : 0f, from = pos,
            };
        }

        /// <summary>Alle sitzenden Raben fliegen auf.</summary>
        public void Scare()
        {
            foreach (var b in birds)
                if (!b.flying) { b.flying = true; b.from = b.sr.transform.position; b.takeoff = 0f; b.phase = Random.value * 6f; b.sr.sortingOrder = 30; }
            if (audioPlayer != null) audioPlayer.Raven(0.95f);
        }

        void Update()
        {
            float dt = Time.deltaTime;
            Vector3 center = transform.position + Vector3.up * circleHeight;
            foreach (var b in birds)
            {
                if (b.flying)
                {
                    b.phase += dt * b.speed;
                    Vector3 target = center + new Vector3(Mathf.Cos(b.phase) * circleRadius.x * b.radiusScale, Mathf.Sin(b.phase) * circleRadius.y * b.radiusScale, 0f);
                    b.takeoff = Mathf.Min(1f, b.takeoff + dt * 0.6f);
                    b.sr.transform.position = Vector3.Lerp(b.from, target, Mathf.SmoothStep(0f, 1f, b.takeoff));
                    b.sr.flipX = -Mathf.Sin(b.phase) < 0f; // Blickrichtung = Flugrichtung
                    b.frameT += dt * 7f;
                    if (flyFrames.Length > 0) b.sr.sprite = flyFrames[(int)b.frameT % flyFrames.Length];
                }
                else
                {
                    b.nod -= dt;
                    if (sitFrames.Length > 1) b.sr.sprite = b.nod < 0.25f ? sitFrames[1] : sitFrames[0];
                    if (b.nod < 0f) b.nod = Random.Range(1.5f, 4f);
                }
            }
            cawTimer -= dt;
            if (cawTimer <= 0f)
            {
                cawTimer = Random.Range(cawInterval.x, cawInterval.y);
                var cam = Camera.main;
                bool near = cam != null && ((Vector2)(cam.transform.position - transform.position)).sqrMagnitude < 15f * 15f;
                if (audioPlayer != null && near) audioPlayer.Raven(Random.Range(0.9f, 1.1f));
            }
        }
    }
}
