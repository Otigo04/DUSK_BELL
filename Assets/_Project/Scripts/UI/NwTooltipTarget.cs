using UnityEngine;
using UnityEngine.EventSystems;

namespace Nightward.UI
{
    /// <summary>Auf ein UI-Element mit Raycast-Grafik legen: Hover zeigt den kurzen englischen Hinweistext (NwTooltip).</summary>
    public class NwTooltipTarget : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
    {
        [SerializeField] string text;

        public void SetText(string value) => text = value;

        public void OnPointerEnter(PointerEventData e) => NwTooltip.Show(this, text);
        public void OnPointerExit(PointerEventData e) => NwTooltip.Hide(this);
        void OnDisable() => NwTooltip.Hide(this);
    }
}
