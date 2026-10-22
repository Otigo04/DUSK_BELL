using UnityEngine.EventSystems;

namespace Nightward.UI
{
    /// <summary>Fragt ab, ob die Maus gerade ueber einem UI-Element liegt. Spielaktionen (Schlag, Interaktion per Klick) pruefen das.</summary>
    public static class NwPointer
    {
        public static bool OverUI => EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
    }
}
