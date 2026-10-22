using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>Eine Zeile im Lagebericht: Icon plus Text. Der Text bleibt in der Zeile (Fit auf 16, 8, gekuerzt).</summary>
    public class NwReportRow : MonoBehaviour
    {
        [SerializeField] Image icon;
        [SerializeField] Text label;

        string content = "";

        public void Set(Sprite sprite, string text, Color color)
        {
            icon.sprite = sprite;
            icon.enabled = sprite != null;
            content = text;
            label.color = color;
            label.text = text;
        }

        /// <summary>Nach dem Layout aufrufen, wenn die echte Breite feststeht.</summary>
        public void FitText(int big = NwTheme.FontMenu, int small = NwTheme.FontHint)
            => NwTextFit.Fit(label, content, label.rectTransform.rect.width, big, small);
    }
}
