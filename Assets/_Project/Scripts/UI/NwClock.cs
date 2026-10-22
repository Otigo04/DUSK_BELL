using Nightward.DayNight;
using UnityEngine;

namespace Nightward.UI
{
    /// <summary>
    /// Uebersetzt die Phasen des DayNightCycle in eine Uhrzeit fuers HUD.
    /// Morgen 05:00-09:00, Tag 09:00-18:00, Abend (Daemmerung) 18:00-21:00, Nacht 21:00-05:00.
    /// Die Uhr laeuft innerhalb einer Phase linear, so wechselt sie genau mit der Phase.
    /// </summary>
    public static class NwClock
    {
        static readonly float[] Start = { 5f, 9f, 18f, 21f };
        static readonly float[] Length = { 4f, 9f, 3f, 8f };

        public static float Hour(DayPhase phase, float progress)
        {
            int i = (int)phase;
            return (Start[i] + Length[i] * Mathf.Clamp01(progress)) % 24f;
        }

        public static string PhaseName(DayPhase phase)
        {
            switch (phase)
            {
                case DayPhase.Morgen: return "Morgen";
                case DayPhase.Tag: return "Tag";
                case DayPhase.Daemmerung: return "Abend";
                default: return "Nacht";
            }
        }

        /// <summary>Farbe des Phasennamens: Sonne warmgelb, Abend orange, Nacht Mondlila.</summary>
        public static Color PhaseColor(DayPhase phase)
        {
            switch (phase)
            {
                case DayPhase.Daemmerung: return NwTheme.Warning;
                case DayPhase.Nacht: return new Color32(0xe8, 0xe0, 0xf0, 255);
                default: return NwTheme.Title;
            }
        }
    }
}
