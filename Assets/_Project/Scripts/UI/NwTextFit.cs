using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Haelt einzeiligen Text innerhalb seiner Box: erst Schriftgroesse 16, passt es nicht, 8,
    /// passt es immer noch nicht, wird mit "…" gekuerzt. Nur Rasterstufen der Pixelschrift, kein stufenloses Skalieren.
    /// </summary>
    public static class NwTextFit
    {
        public static float Width(Text t, string s)
        {
            var settings = t.GetGenerationSettings(Vector2.zero);
            settings.horizontalOverflow = HorizontalWrapMode.Overflow;
            return t.cachedTextGeneratorForLayout.GetPreferredWidth(s, settings) / t.pixelsPerUnit;
        }

        public static void Fit(Text t, string s, float maxWidth, int big = NwTheme.FontMenu, int small = NwTheme.FontHint)
        {
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Truncate;
            t.fontSize = big;
            t.text = s;
            if (string.IsNullOrEmpty(s) || maxWidth <= 0f) return;
            if (Width(t, s) <= maxWidth) return;

            t.fontSize = small;
            if (Width(t, s) <= maxWidth) return;

            int len = s.Length;
            while (len > 1 && Width(t, s.Substring(0, len) + "…") > maxWidth) len--;
            t.text = s.Substring(0, len).TrimEnd() + "…";
        }
    }
}
