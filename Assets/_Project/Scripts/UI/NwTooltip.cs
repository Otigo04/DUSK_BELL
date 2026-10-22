using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Kleiner Hinweiskasten (Plate_Flyout, Schriftgroesse 8) am Mauszeiger. Erscheint nach 2,5 s Hover ueber einem
    /// NwTooltipTarget und bleibt im Bild. Laeuft auch bei Time.timeScale = 0.
    /// </summary>
    public class NwTooltip : MonoBehaviour
    {
        static NwTooltip instance;

        [SerializeField] RectTransform box;
        [SerializeField] Text label;
        [SerializeField] float delay = 2.5f;
        [SerializeField] float padding = 10f;
        [SerializeField] Vector2 cursorOffset = new Vector2(8f, -10f);

        Object owner;
        string pending;
        float timer;
        bool visible;

        void Awake()
        {
            instance = this;
            box.gameObject.SetActive(false);
        }

        void OnDestroy()
        {
            if (instance == this) instance = null;
        }

        public static void Show(Object owner, string text)
        {
            if (instance == null || string.IsNullOrEmpty(text)) return;
            instance.owner = owner;
            instance.pending = text;
            instance.timer = 0f;
            instance.SetVisible(false);
        }

        public static void Hide(Object owner)
        {
            if (instance == null || instance.owner != owner) return;
            instance.owner = null;
            instance.SetVisible(false);
        }

        void SetVisible(bool value)
        {
            visible = value;
            box.gameObject.SetActive(value);
        }

        void Update()
        {
            if (owner == null) return;
            if (!visible)
            {
                timer += Time.unscaledDeltaTime;
                if (timer < delay) return;
                label.text = pending;
                box.sizeDelta = new Vector2(Mathf.Ceil(NwTextFit.Width(label, pending)) + padding, box.sizeDelta.y);
                SetVisible(true);
            }
            Follow();
        }

        void Follow()
        {
            var mouse = Mouse.current;
            if (mouse == null) return;
            var area = (RectTransform)transform;
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(area, mouse.position.ReadValue(), null, out var local)) return;

            Rect r = area.rect;
            Vector2 size = box.sizeDelta;
            Vector2 p = local + cursorOffset;                   // Pivot oben links
            if (p.x + size.x > r.xMax - 2f) p.x = local.x - cursorOffset.x - size.x;
            if (p.y - size.y < r.yMin + 2f) p.y = local.y - cursorOffset.y + size.y;
            p.x = Mathf.Clamp(p.x, r.xMin + 2f, r.xMax - size.x - 2f);
            p.y = Mathf.Clamp(p.y, r.yMin + size.y + 2f, r.yMax - 2f);
            box.anchoredPosition = new Vector2(Mathf.Round(p.x), Mathf.Round(p.y));
        }
    }
}
