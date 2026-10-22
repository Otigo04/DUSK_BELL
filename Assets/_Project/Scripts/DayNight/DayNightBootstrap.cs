using UnityEngine;
using UnityEngine.SceneManagement;

namespace Nightward.DayNight
{
    /// <summary>
    /// Stellt sicher, dass jede geladene Szene einen Tag-/Nachtzyklus samt Lichtsteuerung hat.
    /// Dadurch gehen Zeitraffer und Debug-Tasten (F5 Phase, F6 Tempo, F7 Pause) in jeder Szene,
    /// auch wenn sie nie ueber "Nightward/Tag und Nacht" eingerichtet wurde.
    /// Von Hand eingerichtete Szenen (Tag_Nacht-Objekt) bleiben unveraendert.
    /// </summary>
    public static class DayNightBootstrap
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Init()
        {
            SceneManager.sceneLoaded += (_, _) => Ensure();
            Ensure();
        }

        static void Ensure()
        {
            GameObject host = null;
            if (DayNightCycle.Instance == null)
            {
                host = new GameObject("Tag_Nacht");
                host.AddComponent<DayNightCycle>();
            }
            else host = DayNightCycle.Instance.gameObject;

            if (Object.FindAnyObjectByType<DayNightLighting>() == null)
                host.AddComponent<DayNightLighting>();
        }
    }
}
