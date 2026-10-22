using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Titelbildschirm: Menue mit vier Buttons (Neues Spiel, Fortsetzen, Optionen, Beenden), Auswahl per
    /// Maus, Pfeiltasten/W/S oder Gamepad. Sterne funkeln durch Wechsel zweier Bilder, Ein-/Ausblenden ueber Nachtviolett.
    /// Fortsetzen ist deaktiviert, solange es keinen Spielstand gibt.
    /// </summary>
    public class NwTitleScreen : MonoBehaviour
    {
        public const string SaveKey = "Nightward.Save.Exists";   // setzt das spaetere Speichersystem

        [Header("Menue")]
        [SerializeField] NwButton[] buttons;     // 0 Neues Spiel, 1 Fortsetzen, 2 Optionen, 3 Beenden
        [SerializeField] Text hint;
        [SerializeField] string gameScene = "Opening";

        [Header("Atmosphaere")]
        [SerializeField] Image starsA;
        [SerializeField] Image starsB;
        [SerializeField] float starInterval = 0.8f;
        [SerializeField] Image fade;
        [SerializeField] float fadeTime = 0.6f;

        int selected;
        float starTimer;
        bool busy;
        Coroutine hintRoutine;

        public static bool HasSave => PlayerPrefs.GetInt(SaveKey, 0) == 1;

        void Start()
        {
            Time.timeScale = 1f;
            if (hint != null) hint.text = "";
            if (buttons.Length > 1) buttons[1].Interactable = HasSave;
            Select(HasSave ? 1 : 0);
            if (starsA != null) starsA.enabled = true;
            if (starsB != null) starsB.enabled = false;
            if (fade != null) StartCoroutine(Fade(1f, 0f, null));
        }

        void Update()
        {
            if (busy) return;

            starTimer += Time.unscaledDeltaTime;
            if (starTimer >= starInterval)
            {
                starTimer -= starInterval;
                if (starsA != null) starsA.enabled = !starsA.enabled;
                if (starsB != null) starsB.enabled = !starsB.enabled;
            }

            var mouse = Mouse.current;
            if (mouse != null && mouse.delta.ReadValue().sqrMagnitude > 0.01f)
            {
                var p = mouse.position.ReadValue();
                for (int i = 0; i < buttons.Length; i++)
                {
                    if (!buttons[i].Interactable) continue;
                    if (RectTransformUtility.RectangleContainsScreenPoint((RectTransform)buttons[i].transform, p)) Select(i);
                }
            }

            var kb = Keyboard.current;
            var pad = Gamepad.current;
            bool up = (kb != null && (kb.upArrowKey.wasPressedThisFrame || kb.wKey.wasPressedThisFrame))
                      || (pad != null && pad.dpad.up.wasPressedThisFrame);
            bool down = (kb != null && (kb.downArrowKey.wasPressedThisFrame || kb.sKey.wasPressedThisFrame))
                        || (pad != null && pad.dpad.down.wasPressedThisFrame);
            bool confirm = (kb != null && (kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame
                                           || kb.spaceKey.wasPressedThisFrame || kb.eKey.wasPressedThisFrame))
                           || (pad != null && pad.buttonSouth.wasPressedThisFrame);

            if (up) Move(-1);
            if (down) Move(1);
            if (confirm && buttons[selected].Interactable) buttons[selected].onClick.Invoke();
        }

        void Move(int dir)
        {
            for (int n = 1; n <= buttons.Length; n++)
            {
                int i = (selected + dir * n + buttons.Length * 2) % buttons.Length;
                if (!buttons[i].Interactable) continue;
                Select(i);
                return;
            }
        }

        void Select(int index)
        {
            selected = index;
            for (int i = 0; i < buttons.Length; i++) buttons[i].Highlighted = i == index;
        }

        // ------------------------------------------------------------------ Knoepfe
        public void OnNewGame()
        {
            if (busy) return;
            PlayerPrefs.SetInt(SaveKey, 0);
            StartGame();
        }

        public void OnContinue()
        {
            if (busy || !HasSave) return;
            StartGame();
        }

        public void OnOptions() => ShowHint("Optionen folgen noch.");

        public void OnQuit()
        {
            if (busy) return;
            busy = true;
            StartCoroutine(Fade(0f, 1f, () =>
            {
#if UNITY_EDITOR
                UnityEditor.EditorApplication.isPlaying = false;
#else
                Application.Quit();
#endif
            }));
        }

        void StartGame()
        {
            busy = true;
            StartCoroutine(Fade(0f, 1f, () => SceneManager.LoadScene(gameScene)));
        }

        void ShowHint(string text)
        {
            if (hint == null) return;
            if (hintRoutine != null) StopCoroutine(hintRoutine);
            hintRoutine = StartCoroutine(HintRoutine(text));
        }

        IEnumerator HintRoutine(string text)
        {
            hint.text = text;
            yield return new WaitForSecondsRealtime(2.5f);
            hint.text = "";
            hintRoutine = null;
        }

        IEnumerator Fade(float from, float to, System.Action done)
        {
            if (fade == null) { done?.Invoke(); yield break; }
            fade.raycastTarget = true;
            var c = fade.color;
            for (float t = 0f; t < fadeTime; t += Time.unscaledDeltaTime)
            {
                c.a = Mathf.Lerp(from, to, t / fadeTime);
                fade.color = c;
                yield return null;
            }
            c.a = to;
            fade.color = c;
            fade.raycastTarget = to > 0.5f;
            done?.Invoke();
        }
    }
}
