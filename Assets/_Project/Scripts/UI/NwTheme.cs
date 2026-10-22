using UnityEngine;

namespace Nightward.UI
{
    /// <summary>Farben und Konstanten aus dem UI-Cheatsheet. Nur Palettenwerte.</summary>
    public static class NwTheme
    {
        static Color Hex(string h)
        {
            ColorUtility.TryParseHtmlString(h, out var c);
            return c;
        }

        // Schrift
        public static readonly Color TextDefault = Hex("#fff1c9");   // Kerzenweiss
        public static readonly Color Title = Hex("#ffd27a");         // Warmgelb
        public static readonly Color Narrator = Hex("#9ab87a");      // Blattlicht
        public static readonly Color TextShadow = Hex("#1a1526");
        public const int FontHint = 8;
        public const int FontMenu = 16;

        // Dialogbox
        public static readonly Color Arrow = Hex("#ffa550");

        // Buttons: Text je Zustand
        public static readonly Color ButtonTextNormal = Hex("#fff1c9");
        public static readonly Color ButtonTextHover = Hex("#ffd27a");
        public static readonly Color ButtonTextPressed = Hex("#9a95a0");
        public static readonly Color ButtonTextDisabled = Hex("#6e6a74");

        // HUD
        public static readonly Color Talisman = Hex("#6fd3e6");
        public static readonly Color TalismanZero = Hex("#8a1f3d");
        public static readonly Color Trust = Hex("#c4636b");
        public static readonly Color Knowledge = Hex("#6b7fb8");

        // HUD Neu: Beduerfnisse/Stimmung (Stufe 1-4, positiv), gedaempfter Text
        public static readonly Color[] NeedStage = { Hex("#6b5a7a"), Hex("#ffd27a"), Hex("#ffa550"), Hex("#d64a6a") };
        public static readonly Color NeedPositive = Hex("#6e9a5e");
        public static readonly Color TextDim = Hex("#9a95a0");
        public const float NeedFlash = 0.3f;

        // Lagebericht
        public static readonly Color Loss = Hex("#d64a6a");
        public static readonly Color Warning = Hex("#ffa550");

        public const float ArrowBlink = 0.5f;
        public const float ReportLineDelay = 0.3f;
    }
}
