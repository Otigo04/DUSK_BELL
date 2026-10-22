using UnityEngine;

namespace Nightward.Interaction
{
    /// <summary>
    /// Symbol ueber einem Interactable (sofern es ShowsIndicator erlaubt): Sprechblase, wenn der Spieler in der Naehe ist,
    /// E-Taste, wenn er nah genug zum Ausloesen ist. Wippt leicht, auf ganze Pixel gerundet.
    /// Liegt auf einem eigenen Kind-Objekt mit SpriteRenderer.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class InteractionIndicator : MonoBehaviour
    {
        [SerializeField] Interactable target;
        [SerializeField] Sprite nearbySprite;
        [SerializeField] Sprite inRangeSprite;
        [Tooltip("Ab dieser Entfernung zum Spieler erscheint das Symbol")]
        [SerializeField] float showDistance = 4.5f;
        [Tooltip("Hoehe des Symbols in Kacheln, unabhaengig von den Import-Einstellungen")]
        [SerializeField] float worldSize = 0.5f;
        [SerializeField] float bobHeight = 1f / 16f;
        [SerializeField] float bobSpeed = 2.5f;
        [SerializeField] int pixelsPerUnit = 32;

        SpriteRenderer sr;
        PlayerInteractor player;

        void Awake()
        {
            sr = GetComponent<SpriteRenderer>();
            if (target == null) target = GetComponentInParent<Interactable>();
        }

        void LateUpdate()
        {
            if (player == null) player = FindAnyObjectByType<PlayerInteractor>();
            bool show = target != null && player != null && !player.Busy
                        && Vector2.Distance(player.transform.position, target.transform.position) <= showDistance
                        && target.CanInteract(player) && target.ShowsIndicator(player);
            sr.enabled = show;
            if (!show) return;

            sr.sprite = player.Current == target ? inRangeSprite : nearbySprite;
            float h = sr.sprite != null ? sr.sprite.bounds.size.y : 1f;
            transform.localScale = Vector3.one * (worldSize / Mathf.Max(0.0001f, h));

            Vector3 p = target.IndicatorPosition + Vector3.up * (Mathf.Sin(Time.time * bobSpeed) * bobHeight);
            p.x = Mathf.Round(p.x * pixelsPerUnit) / pixelsPerUnit;
            p.y = Mathf.Round(p.y * pixelsPerUnit) / pixelsPerUnit;
            transform.position = p;
        }
    }
}
