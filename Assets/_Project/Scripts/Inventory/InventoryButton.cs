using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Nightward.Items
{
    /// <summary>Kleiner Textknopf im Inventarfenster (Sort, Take all). Hover faerbt gelb, wie die Buttons im UI-Cheatsheet.</summary>
    public class InventoryButton : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler
    {
        public Text label;
        public Color normal = new Color32(0xff, 0xf1, 0xc9, 255);
        public Color hover = new Color32(0xff, 0xd2, 0x7a, 255);
        public Action onClick;

        public void OnPointerEnter(PointerEventData e) => label.color = hover;
        public void OnPointerExit(PointerEventData e) => label.color = normal;
        public void OnPointerClick(PointerEventData e)
        {
            if (e.button == PointerEventData.InputButton.Left) onClick?.Invoke();
        }
        void OnDisable() { if (label != null) label.color = normal; }
    }
}
