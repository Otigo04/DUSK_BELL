using UnityEngine;

namespace Nightward.DayNight
{
    /// <summary>
    /// Gedithertes Nebel-Sprite (Draw Mode Tiled), das langsam treibt und nur in Daemmerung, Nacht und
    /// am fruehen Morgen sichtbar ist (Style-Bibel: Dithering nur fuer Nebel, Himmel und weiche Uebergaenge).
    /// Die Position springt nach einer Kachellaenge zurueck, so wirkt die Bewegung endlos.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class FogLayer : MonoBehaviour
    {
        [SerializeField] Vector2 drift = new Vector2(0.15f, 0.03f);
        [SerializeField, Range(0f, 1f)] float maxAlpha = 0.35f;
        [Tooltip("Ab diesem NightFactor wird der Nebel sichtbar")]
        [SerializeField, Range(0f, 1f)] float startAt = 0.3f;

        SpriteRenderer sr;
        Vector3 origin;
        Vector2 offset;
        Vector2 tileSize;

        void Awake()
        {
            sr = GetComponent<SpriteRenderer>();
            origin = transform.position;
            tileSize = sr.sprite != null ? (Vector2)sr.sprite.bounds.size : Vector2.one;
        }

        void Update()
        {
            offset += drift * Time.deltaTime;
            offset.x = Mathf.Repeat(offset.x, tileSize.x);
            offset.y = Mathf.Repeat(offset.y, tileSize.y);
            transform.position = origin + (Vector3)offset;

            float night = DayNightCycle.Instance != null ? DayNightCycle.Instance.NightFactor : 1f;
            var c = sr.color;
            c.a = maxAlpha * Mathf.InverseLerp(startAt, 1f, night);
            sr.color = c;
            sr.enabled = c.a > 0.001f;
        }
    }
}
