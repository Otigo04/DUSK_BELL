using System.Text;
using Nightward.UI;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Nightward.Opening
{
    /// <summary>
    /// Oben rechts: Quest-Symbol mit den Kategorien "Main Quest" und "Side Quests" (aktuelle Quest bzw. "None yet").
    /// Q oeffnet die Quest- und Fortschrittsuebersicht, Esc das Pausenmenue bzw. schliesst offene Menues.
    /// Beides nur, wenn der Spieler frei steuern kann (MenusAllowed, setzt der OpeningDirector).
    /// </summary>
    public class QuestHud : MonoBehaviour
    {
        [SerializeField] GameObject hudRoot;
        [SerializeField] Text mainText;
        [SerializeField] Text sideText;
        [Header("Uebersicht (Q)")]
        [SerializeField] GameObject overview;
        [SerializeField] Text overviewText;
        [Header("Pause (Esc)")]
        [SerializeField] GameObject pauseMenu;
        [SerializeField] NwButton resumeButton;
        [SerializeField] NwButton quitButton;

        public bool MenusAllowed { get; set; }
        public bool MenuOpen => overview.activeSelf || pauseMenu.activeSelf;

        void Awake()
        {
            hudRoot.SetActive(false);
            overview.SetActive(false);
            pauseMenu.SetActive(false);
            QuestLog.Changed += Refresh;
            if (resumeButton != null) resumeButton.onClick.AddListener(CloseMenus);
            if (quitButton != null) quitButton.onClick.AddListener(Quit);
        }

        void OnDestroy()
        {
            QuestLog.Changed -= Refresh;
            Time.timeScale = 1f;
        }

        /// <summary>Wo ein NwQuestTracker im Hud ist (Level_01), macht er die Quest-Anzeige oben rechts; diese Box bleibt dort aus, damit nichts doppelt steht.</summary>
        public void Show(bool visible)
        {
            if (trackerPresent == null) trackerPresent = FindAnyObjectByType<NwQuestTracker>(FindObjectsInactive.Include) != null;
            hudRoot.SetActive(visible && !trackerPresent.Value);
            Refresh();
        }

        bool? trackerPresent;

        void Refresh()
        {
            if (mainText == null) return;
            mainText.text = string.IsNullOrEmpty(QuestLog.MainQuest) ? "-" : QuestLog.MainQuest;
            sideText.text = QuestLog.SideQuests.Count == 0 ? "None yet" : string.Join("\n", QuestLog.SideQuests);
            if (overview.activeSelf) FillOverview();
        }

        void FillOverview()
        {
            var sb = new StringBuilder();
            sb.AppendLine("MAIN QUEST");
            if (!string.IsNullOrEmpty(QuestLog.MainQuest)) sb.AppendLine("> " + QuestLog.MainQuest);
            foreach (var q in QuestLog.CompletedMain) sb.AppendLine("[x] " + q);
            if (string.IsNullOrEmpty(QuestLog.MainQuest) && QuestLog.CompletedMain.Count == 0) sb.AppendLine("None yet");
            sb.AppendLine();
            sb.AppendLine("SIDE QUESTS");
            if (QuestLog.SideQuests.Count == 0) sb.AppendLine("None yet");
            foreach (var q in QuestLog.SideQuests) sb.AppendLine("> " + q);
            overviewText.text = sb.ToString();
        }

        void Update()
        {
            var kb = Keyboard.current;
            if (kb == null) return;
            if (kb.escapeKey.wasPressedThisFrame)
            {
                if (MenuOpen) CloseMenus();
                else if (MenusAllowed) OpenPause();
            }
            else if (kb.qKey.wasPressedThisFrame)
            {
                if (overview.activeSelf) CloseMenus();
                else if (MenusAllowed && !pauseMenu.activeSelf) OpenOverview();
            }
        }

        void OpenOverview()
        {
            overview.SetActive(true);
            FillOverview();
            Time.timeScale = 0f;
        }

        void OpenPause()
        {
            pauseMenu.SetActive(true);
            Time.timeScale = 0f;
        }

        public void CloseMenus()
        {
            overview.SetActive(false);
            pauseMenu.SetActive(false);
            Time.timeScale = 1f;
        }

        void Quit()
        {
            Time.timeScale = 1f;
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
    }
}
