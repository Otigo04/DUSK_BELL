using System;

namespace Nightward.Core
{
    /// <summary>
    /// Zwischensequenz laeuft: der Spieler hat keinen Einfluss mehr (keine Bewegung, kein Inventar, kein Kampf), das Spiel
    /// laeuft wie ein Film weiter. Die Sequenz-Skripte rufen Begin/End, andere Systeme (Inventar, HUD ...) fragen Active ab.
    /// Mehrfaches Begin wird mitgezaehlt, erst das letzte End beendet die Sequenz.
    /// </summary>
    public static class Cutscene
    {
        static int depth;

        public static bool Active => depth > 0;

        public static event Action<bool> Changed;

        public static void Begin()
        {
            depth++;
            if (depth == 1) Changed?.Invoke(true);
        }

        public static void End()
        {
            if (depth == 0) return;
            depth--;
            if (depth == 0) Changed?.Invoke(false);
        }

        /// <summary>Notfall (z. B. Szenenwechsel): alles zuruecksetzen.</summary>
        public static void Reset()
        {
            bool was = depth > 0;
            depth = 0;
            if (was) Changed?.Invoke(false);
        }
    }
}
