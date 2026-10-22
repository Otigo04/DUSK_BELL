using Nightward.Items;
using Nightward.UI;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.Interaction
{
    /// <summary>
    /// Kleiner Hinweis-Kasten ueber dem Objekt, das der Spieler gerade ansteuert ("F  Pick up Bread x3", "F  Open Chest").
    /// Erscheint nur fuer Interactables mit ShowsPromptBox (Gegenstaende, Behaelter); NPCs und Tueren behalten ihre Symbole.
    /// Wird vom InventoryUI beim Aufbau der Oberflaeche angelegt und baut seinen Kasten selbst (Referenz 480x270, Pixelschrift).
    /// </summary>
    public class InteractHintUI : MonoBehaviour
    {
        const int Height = 13;

        PlayerInteractor interactor;
        Camera cam;
        RectTransform canvasRect, box;
        Text label;
        string shown;

        public void Init(Canvas canvas, Font font, Sprite plate)
        {
            interactor = GetComponent<PlayerInteractor>();
            canvasRect = canvas.GetComponent<RectTransform>();

            var go = new GameObject("Interaktions-Hinweis", typeof(RectTransform));
            go.layer = canvas.gameObject.layer;
            box = (RectTransform)go.transform;
            box.SetParent(canvas.transform, false);
            box.anchorMin = box.anchorMax = new Vector2(0.5f, 0.5f);
            box.pivot = new Vector2(0.5f, 0f);
            box.sizeDelta = new Vector2(60, Height);
            var bg = go.AddComponent<Image>();
            bg.sprite = plate;
            bg.type = Image.Type.Sliced;
            bg.raycastTarget = false;

            var tgo = new GameObject("Text", typeof(RectTransform));
            tgo.layer = go.layer;
            var trt = (RectTransform)tgo.transform;
            trt.SetParent(box, false);
            trt.anchorMin = Vector2.zero;
            trt.anchorMax = Vector2.one;
            trt.offsetMin = trt.offsetMax = Vector2.zero;
            label = tgo.AddComponent<Text>();
            label.font = font;
            label.fontSize = 8;
            label.alignment = TextAnchor.MiddleCenter;
            label.horizontalOverflow = HorizontalWrapMode.Overflow;
            label.verticalOverflow = VerticalWrapMode.Overflow;
            label.supportRichText = true;
            label.raycastTarget = false;
            var sh = tgo.AddComponent<Shadow>();
            sh.effectColor = NwTheme.TextShadow;
            sh.effectDistance = new Vector2(1, -1);
            go.SetActive(false);
        }

        void LateUpdate()
        {
            if (box == null || interactor == null) return;
            var it = interactor.Current;
            var ui = InventoryUI.Instance;
            bool show = it != null && it.ShowsPromptBox && !interactor.Busy && (ui == null || !ui.IsOpen);
            if (box.gameObject.activeSelf != show) box.gameObject.SetActive(show);
            if (!show) return;

            if (cam == null) cam = Camera.main;
            if (cam == null) return;

            var tint = it.PromptTint;
            string key = it.Key == InteractKey.F ? "F" : "E";
            string name = it.PromptLabel;
            string text = "<color=#" + ColorUtility.ToHtmlStringRGB(NwTheme.Title) + ">" + key + "</color>  "
                          + (tint.a > 0f ? "<color=#" + ColorUtility.ToHtmlStringRGB(tint) + ">" + name + "</color>" : name);
            if (text != shown)
            {
                shown = text;
                label.text = text;
                box.sizeDelta = new Vector2(Mathf.Ceil(label.preferredWidth) + 12f, Height);
            }

            Vector2 screen = cam.WorldToScreenPoint(it.IndicatorPosition);
            RectTransformUtility.ScreenPointToLocalPointInRectangle(canvasRect, screen, null, out var p);
            // Im Bild halten
            float halfW = canvasRect.rect.width / 2f - box.sizeDelta.x / 2f - 2f;
            float halfH = canvasRect.rect.height / 2f;
            p.x = Mathf.Clamp(p.x, -halfW, halfW);
            p.y = Mathf.Clamp(p.y, -halfH + 2f, halfH - Height - 2f);
            box.anchoredPosition = new Vector2(Mathf.Round(p.x), Mathf.Round(p.y));
        }
    }
}
