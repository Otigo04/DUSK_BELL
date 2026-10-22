using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>Kopfzeile einer Quest-Kategorie: Symbol, Titel, optional Anzahl, Pfeil (auf/zu). Klick klappt um.</summary>
    public class NwQuestHeader : MonoBehaviour, IPointerClickHandler, IPointerEnterHandler, IPointerExitHandler
    {
        [SerializeField] Image plate;
        [SerializeField] Image icon;
        [SerializeField] Text title;
        [SerializeField] Image arrow;
        [SerializeField] GameObject badge;
        [SerializeField] Text badgeText;
        [SerializeField] Sprite arrowOpen;
        [SerializeField] Sprite arrowOpenHover;
        [SerializeField] Sprite arrowClosed;
        [SerializeField] Sprite arrowClosedHover;

        bool expanded;
        bool hover;
        Action toggle;

        public void Setup(string text, Color titleColor, Sprite plateSprite, Sprite iconSprite, int count, bool isExpanded, Action onToggle)
        {
            title.text = text;
            title.color = titleColor;
            plate.sprite = plateSprite;
            icon.sprite = iconSprite;
            badge.SetActive(count >= 0);
            if (count >= 0) badgeText.text = count.ToString();
            expanded = isExpanded;
            toggle = onToggle;
            UpdateArrow();
        }

        void UpdateArrow()
        {
            arrow.sprite = expanded ? (hover ? arrowOpenHover : arrowOpen) : (hover ? arrowClosedHover : arrowClosed);
        }

        public void OnPointerClick(PointerEventData e) => toggle?.Invoke();
        public void OnPointerEnter(PointerEventData e) { hover = true; UpdateArrow(); }
        public void OnPointerExit(PointerEventData e) { hover = false; UpdateArrow(); }
    }
}
