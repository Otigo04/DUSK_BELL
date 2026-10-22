using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Nightward.Items
{
    public enum SlotKind { Hotbar, Backpack, Equipment, Container }

    /// <summary>Ein Platz in der Oberflaeche: Rahmen, Symbol, Anzahl, Haltbarkeitsbalken. Meldet Hover und Klicks an das InventoryUI.</summary>
    public class InventorySlotUI : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler
    {
        public Inventory inventory;
        public int index;
        public SlotKind kind;

        public Image background, icon, placeholder, barBack, barFill;
        public Text count, hint;
        public Sprite normalSprite, hoverSprite, selectedSprite;

        InventoryUI ui;
        bool hovered;
        bool selected;

        public void Init(InventoryUI owner) => ui = owner;

        public void SetSelected(bool value)
        {
            selected = value;
            UpdateBackground();
        }

        void UpdateBackground()
        {
            background.sprite = selected ? selectedSprite : hovered ? hoverSprite : normalSprite;
        }

        public void Refresh()
        {
            var s = inventory.Get(index);
            icon.enabled = s != null;
            if (s != null) icon.sprite = s.def.icon;
            count.text = s != null && s.count > 1 ? s.count.ToString() : "";
            if (placeholder != null) placeholder.enabled = s == null && placeholder.sprite != null;

            bool bar = s != null && s.def.HasDurability;
            barBack.enabled = bar;
            barFill.enabled = bar;
            if (bar)
            {
                float f = s.DurabilityFraction;
                var rt = barFill.rectTransform;
                rt.sizeDelta = new Vector2(Mathf.Max(1f, Mathf.Round(26f * f)), rt.sizeDelta.y);
                // gruen -> gelb -> rot (Palette: Gras hell, Warmgelb, Monsterauge)
                barFill.color = f > 0.5f ? new Color32(0x6e, 0x9a, 0x5e, 255) : f > 0.2f ? new Color32(0xff, 0xd2, 0x7a, 255) : new Color32(0xd6, 0x4a, 0x6a, 255);
            }
        }

        public void OnPointerEnter(PointerEventData e)
        {
            hovered = true;
            UpdateBackground();
            ui.SetHover(this);
        }

        public void OnPointerExit(PointerEventData e)
        {
            hovered = false;
            UpdateBackground();
            ui.ClearHover(this);
        }

        public void OnPointerClick(PointerEventData e) => ui.OnSlotClick(this, e);

        void OnDisable()
        {
            hovered = false;
            if (background != null) UpdateBackground();
        }
    }
}
