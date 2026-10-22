using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Button mit vier Zustaenden (Normal, Hover, Gedrueckt, Deaktiviert). Nur Sprite- und Farbwechsel,
    /// keine Bewegung. Rahmenlogik wie die Dialogbox (9-Slice).
    /// </summary>
    [RequireComponent(typeof(Image))]
    public class NwButton : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler, IPointerClickHandler
    {
        [SerializeField] Image background;
        [SerializeField] Text label;
        [SerializeField] Sprite normal;
        [SerializeField] Sprite hover;
        [SerializeField] Sprite pressed;
        [SerializeField] Sprite disabled;
        [SerializeField] bool interactable = true;
        public UnityEvent onClick = new UnityEvent();

        bool over;
        bool down;
        bool highlighted;

        public Text Label => label;

        /// <summary>Wie Hover, aber per Tastatur-Auswahl gesetzt (z. B. Antwortauswahl im Dialog).</summary>
        public bool Highlighted
        {
            get => highlighted;
            set { highlighted = value; Refresh(); }
        }

        public bool Interactable
        {
            get => interactable;
            set { interactable = value; Refresh(); }
        }

        void Reset() => background = GetComponent<Image>();

        void OnEnable()
        {
            over = down = false;
            Refresh();
        }

        public void OnPointerEnter(PointerEventData e) { over = true; Refresh(); }
        public void OnPointerExit(PointerEventData e) { over = false; Refresh(); }
        public void OnPointerDown(PointerEventData e) { down = true; Refresh(); }
        public void OnPointerUp(PointerEventData e) { down = false; Refresh(); }

        public void OnPointerClick(PointerEventData e)
        {
            if (interactable && e.button == PointerEventData.InputButton.Left) onClick.Invoke();
        }

        void Refresh()
        {
            if (background == null) return;
            Sprite s;
            Color c;
            if (!interactable) { s = disabled; c = NwTheme.ButtonTextDisabled; }
            else if (down && over) { s = pressed; c = NwTheme.ButtonTextPressed; }
            else if (over || highlighted) { s = hover; c = NwTheme.ButtonTextHover; }
            else { s = normal; c = NwTheme.ButtonTextNormal; }
            if (s != null) background.sprite = s;
            if (label != null) label.color = c;
            // Schatten nur wenn aktiv: deaktivierter Text bleibt flach
            if (label != null)
            {
                var sh = label.GetComponent<Shadow>();
                if (sh != null) sh.enabled = interactable;
            }
        }
    }
}
