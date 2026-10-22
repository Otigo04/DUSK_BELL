using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Uebergabe vom Opening (Fahrt, Baumstamm) an die Ankunft im Dorf (Level_01): Das Opening setzt Pending und laedt Level_01,
    /// der ArrivalDirector liest und loescht das Flag beim Start. Ueber PlayerPrefs, damit es auch einen Neustart der Domain ueberlebt
    /// (z. B. beim Testen im Editor).
    /// </summary>
    public static class ArrivalState
    {
        const string Key = "nw_arrival_pending";

        public static bool Pending
        {
            get => PlayerPrefs.GetInt(Key, 0) == 1;
            set
            {
                PlayerPrefs.SetInt(Key, value ? 1 : 0);
                PlayerPrefs.Save();
            }
        }
    }
}
