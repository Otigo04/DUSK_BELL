using System;
using Nightward.Opening;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Nightward.UI
{
    public enum QuestState { Open, Active, Done, Failed }

    /// <summary>
    /// Quest-Tracker oben rechts (152 px breit): Kategorie "Main Quest" (aktuelle und zuletzt erledigte Quests) und
    /// "Side Quests" (mit Anzahl, standardmaessig eingeklappt). Liest den QuestLog. Klick auf die Kopfzeile klappt um.
    /// </summary>
    public class NwQuestTracker : MonoBehaviour
    {
        [SerializeField] RectTransform content;
        [SerializeField] NwQuestHeader headerPrefab;
        [SerializeField] NwQuestEntry entryPrefab;
        [SerializeField] Sprite plateMain;
        [SerializeField] Sprite plateSide;
        [SerializeField] Sprite iconMain;
        [SerializeField] Sprite iconSide;
        [SerializeField] Color sideTitleColor = new Color32(0x9a, 0xb4, 0xe8, 255);
        [SerializeField] int maxDone = 2;

        bool mainOpen = true;
        bool sideOpen;
        float mainProgress = -1f;

        void OnEnable()
        {
            QuestLog.Changed += Refresh;
            Refresh();
        }

        void OnDisable() => QuestLog.Changed -= Refresh;

        /// <summary>Fortschritt der aktiven Main Quest (0-1) als Balken. Negativ blendet ihn aus.</summary>
        public void SetMainProgress(float progress)
        {
            mainProgress = progress;
            Refresh();
        }

        public void Refresh()
        {
            if (content == null) return;
            for (int i = content.childCount - 1; i >= 0; i--)
            {
                var child = content.GetChild(i).gameObject;
                child.SetActive(false);
                Destroy(child);
            }

            var header = Instantiate(headerPrefab, content);
            header.Setup("Main Quest", NwTheme.TextDefault, plateMain, iconMain, -1, mainOpen, () => { mainOpen = !mainOpen; Refresh(); });
            if (mainOpen)
            {
                bool any = false;
                if (!string.IsNullOrEmpty(QuestLog.MainQuest))
                {
                    Instantiate(entryPrefab, content).Setup(QuestLog.MainQuest, QuestState.Active, true, mainProgress);
                    any = true;
                }
                int done = QuestLog.CompletedMain.Count;
                for (int i = done - 1; i >= Mathf.Max(0, done - maxDone); i--)
                {
                    Instantiate(entryPrefab, content).Setup(QuestLog.CompletedMain[i], QuestState.Done, false);
                    any = true;
                }
                if (!any) Instantiate(entryPrefab, content).Setup("None yet", QuestState.Open, false);
            }

            var sides = QuestLog.SideQuests;
            var side = Instantiate(headerPrefab, content);
            side.Setup("Side Quests", sideTitleColor, plateSide, iconSide, sides.Count, sideOpen, () => { sideOpen = !sideOpen; Refresh(); });
            if (sideOpen)
            {
                if (sides.Count == 0) Instantiate(entryPrefab, content).Setup("None yet", QuestState.Open, false);
                foreach (var q in sides) Instantiate(entryPrefab, content).Setup(q, QuestState.Open, false);
            }

            LayoutRebuilder.ForceRebuildLayoutImmediate(content);
        }
    }
}
