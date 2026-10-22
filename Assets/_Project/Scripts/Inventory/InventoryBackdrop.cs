using UnityEngine;
using UnityEngine.EventSystems;

namespace Nightward.Items
{
    /// <summary>Unsichtbare Flaeche hinter den Fenstern: Klick daneben wirft den Stapel in der Hand in die Welt.</summary>
    public class InventoryBackdrop : MonoBehaviour, IPointerClickHandler
    {
        public InventoryUI ui;
        public void OnPointerClick(PointerEventData e) => ui.OnBackdropClick(e);
    }
}
