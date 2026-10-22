using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Quest- und Fortschrittsstand: eine aktive Main Quest, erledigte Main Quests und Side Quests.
    /// Haelt nur den Laufzeitstand. Das HUD (QuestHud) haengt sich an Changed.
    /// </summary>
    public static class QuestLog
    {
        public static string MainQuest { get; private set; }
        public static readonly List<string> CompletedMain = new List<string>();
        public static readonly List<string> SideQuests = new List<string>();

        public static event Action Changed;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetAll()
        {
            MainQuest = null;
            CompletedMain.Clear();
            SideQuests.Clear();
            Changed = null;
        }

        public static void SetMain(string quest)
        {
            MainQuest = quest;
            Changed?.Invoke();
        }

        /// <summary>Aktive Main Quest abschliessen, optional gleich die naechste setzen.</summary>
        public static void CompleteMain(string next = null)
        {
            if (!string.IsNullOrEmpty(MainQuest)) CompletedMain.Add(MainQuest);
            MainQuest = next;
            Changed?.Invoke();
        }
    }

    public enum Protagonist { Frau, Mann }

    /// <summary>Wahl aus der Charakterwahl (Step 1). Gilt fuer das ganze Spiel und ist endgueltig.</summary>
    public static class PlayerChoice
    {
        const string Key = "Nightward.Protagonist";

        public static bool HasChosen => PlayerPrefs.HasKey(Key);
        public static Protagonist Current => (Protagonist)PlayerPrefs.GetInt(Key, 0);

        public static void Set(Protagonist p)
        {
            PlayerPrefs.SetInt(Key, (int)p);
            PlayerPrefs.Save();
        }
    }
}
