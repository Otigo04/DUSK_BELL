using Nightward.Interaction;
using Nightward.UI;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.Opening
{
    /// <summary>
    /// Eingabeaufforderung in der Naehe des Objekts oder der Person, z. B. "F – Interact" oder "E – Talk".
    /// Folgt dem Interactable, das der PlayerInteractor gerade im Blick hat. Mit Show(...) laesst sich ein
    /// eigener Hinweis an ein Objekt heften (z. B. "F – Get out" am Auto).
    /// </summary>
    public class InteractPrompt : MonoBehaviour
    {
        [SerializeField] RectTransform box;
        [SerializeField] Text label;
        [SerializeField] PlayerInteractor player;
        [SerializeField] Vector3 worldOffset = new Vector3(0f, 0.25f, 0f);

        Transform forced;
        Vector3 forcedOffset;
        string forcedText;
        RectTransform canvasRect;
        Camera cam;

        void Awake()
        {
            canvasRect = (RectTransform)GetComponentInParent<Canvas>().transform;
            box.gameObject.SetActive(false);
        }

        public void Show(Transform target, string text, Vector3 offset)
        {
            forced = target;
            forcedText = text;
            forcedOffset = offset;
        }

        public void Hide() => forced = null;

        void LateUpdate()
        {
            if (cam == null) cam = Camera.main;
            Vector3 world;
            string text;
            if (forced != null)
            {
                world = forced.position + forcedOffset;
                text = forcedText;
            }
            else if (player != null && !player.Busy && player.Current != null)
            {
                var it = player.Current;
                world = it.IndicatorPosition + worldOffset;
                text = (it.Key == InteractKey.F ? "F" : "E") + " – " + it.PromptLabel;
            }
            else
            {
                box.gameObject.SetActive(false);
                return;
            }

            box.gameObject.SetActive(true);
            if (label.text != text)
            {
                label.text = text;
                box.sizeDelta = new Vector2(Mathf.Ceil(NwTextFit.Width(label, text)) + 12f, box.sizeDelta.y);
            }
            Vector2 screen = cam.WorldToScreenPoint(world);
            RectTransformUtility.ScreenPointToLocalPointInRectangle(canvasRect, screen, null, out var local);
            box.anchoredPosition = new Vector2(Mathf.Round(local.x), Mathf.Round(local.y));
        }
    }
}
