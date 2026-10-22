using System.Collections;
using Nightward.UI;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Nightward.Opening
{
    /// <summary>
    /// Step 1: zwei Karten (Protagonistin, Protagonist) mit Portraet-Platzhalter und Button nach UI-Cheatsheet.
    /// Eingabe: Klick oder Enter (Enter waehlt die Karte unter der Maus bzw. die zuletzt beruehrte, A/D oder Pfeile wechseln).
    /// Die Wahl ist endgueltig.
    /// </summary>
    public class CharacterSelect : MonoBehaviour
    {
        [SerializeField] CanvasGroup group;
        [SerializeField] NwButton womanButton;
        [SerializeField] NwButton manButton;
        [SerializeField] Image womanFrame;
        [SerializeField] Image manFrame;

        int selected = -1;
        bool done;
        Protagonist result;

        public IEnumerator Run(System.Action<Protagonist> onChosen)
        {
            done = false;
            selected = -1;
            group.gameObject.SetActive(true);
            group.alpha = 1f;
            group.blocksRaycasts = true;
            womanButton.onClick.AddListener(() => Pick(Protagonist.Frau));
            manButton.onClick.AddListener(() => Pick(Protagonist.Mann));
            Refresh();

            while (!done)
            {
                var kb = Keyboard.current;
                var mouse = Mouse.current;
                if (mouse != null && mouse.delta.ReadValue().sqrMagnitude > 0.01f)
                {
                    var p = mouse.position.ReadValue();
                    if (Inside(womanFrame, p) || Inside(womanButton, p)) Select(0);
                    else if (Inside(manFrame, p) || Inside(manButton, p)) Select(1);
                }
                if (kb != null)
                {
                    if (kb.aKey.wasPressedThisFrame || kb.leftArrowKey.wasPressedThisFrame) Select(0);
                    if (kb.dKey.wasPressedThisFrame || kb.rightArrowKey.wasPressedThisFrame) Select(1);
                    if ((kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame) && selected >= 0)
                        Pick(selected == 0 ? Protagonist.Frau : Protagonist.Mann);
                }
                yield return null;
            }

            // Bleibt sichtbar, bis der Director ueber Schwarz ausgeblendet hat (sonst blitzt kurz die Spielwelt auf)
            group.blocksRaycasts = false;
            onChosen?.Invoke(result);
        }

        public void Hide() => group.gameObject.SetActive(false);

        static bool Inside(Component c, Vector2 screen) =>
            c != null && RectTransformUtility.RectangleContainsScreenPoint((RectTransform)c.transform, screen);

        void Select(int i)
        {
            if (selected == i) return;
            selected = i;
            Refresh();
        }

        void Refresh()
        {
            womanButton.Highlighted = selected == 0;
            manButton.Highlighted = selected == 1;
            if (womanFrame != null) womanFrame.color = selected == 0 ? NwTheme.Title : NwTheme.ButtonTextDisabled;
            if (manFrame != null) manFrame.color = selected == 1 ? NwTheme.Title : NwTheme.ButtonTextDisabled;
        }

        void Pick(Protagonist p)
        {
            if (done) return;
            result = p;
            done = true;
        }
    }
}
