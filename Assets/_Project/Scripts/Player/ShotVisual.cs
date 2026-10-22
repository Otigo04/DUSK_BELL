using UnityEngine;

namespace Nightward.Player
{
    /// <summary>
    /// Sichtbarer Schuss: das Projektil fliegt von der Muendung bis zum Treffer (der Schaden wird sofort per Raycast berechnet),
    /// dort spielt die Einschlag-Animation. Frames: 3 pro Richtung (Flug), 5 fuer den Einschlag.
    /// </summary>
    public class ShotVisual : MonoBehaviour
    {
        const float Speed = 26f;
        const float FlightFps = 14f;
        const float HitFps = 18f;

        Vector2 start, dir;
        float distance, travelled;
        Sprite[] flight, hit;
        SpriteRenderer sr;
        float hitTime = -1f;

        public static void Spawn(Vector2 from, Vector2 direction, float distance, Sprite[] flightFrames, Sprite[] hitFrames, Material material)
        {
            if (flightFrames == null || flightFrames.Length == 0) return;
            var go = new GameObject("Schuss");
            go.transform.position = from;
            var v = go.AddComponent<ShotVisual>();
            v.start = from;
            v.dir = direction.normalized;
            v.distance = Mathf.Max(0.1f, distance);
            v.flight = flightFrames;
            v.hit = hitFrames;
            v.sr = go.AddComponent<SpriteRenderer>();
            v.sr.sortingOrder = 20;
            if (material != null) v.sr.sharedMaterial = material;
            v.sr.sprite = flightFrames[0];
        }

        void Update()
        {
            if (hitTime < 0f)
            {
                travelled += Speed * Time.deltaTime;
                transform.position = start + dir * Mathf.Min(travelled, distance);
                sr.sprite = flight[(int)(Time.time * FlightFps) % flight.Length];
                if (travelled >= distance)
                {
                    hitTime = Time.time;
                    if (hit == null || hit.Length == 0) { Destroy(gameObject); return; }
                }
                return;
            }
            int i = (int)((Time.time - hitTime) * HitFps);
            if (i >= hit.Length) { Destroy(gameObject); return; }
            sr.sprite = hit[i];
        }
    }
}
