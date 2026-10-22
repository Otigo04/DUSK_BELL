using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.UI
{
    /// <summary>
    /// Testtasten fuers HUD (nur Editor/Development-Build), alle mit linker Alt-Taste:
    /// 1/2 Leben -/+, 3/4 Ausdauer -/+, 5/6 Sanity -/+, 7 Maximum-Erschoepfung, 8 Bedarf (naechste Stufe, abwechselnd),
    /// 9 Stimmung positiv, 0 Wecklevel, Minus Neuer-Tag-Banner (Morgen), Gleichheitszeichen Banner (Mitternacht).
    /// </summary>
    public class NwGameHudDebug : MonoBehaviour
    {
        [SerializeField] NwGameHud hud;
        [SerializeField] NwWakeLevel wake;
        [SerializeField] NwNewDay newDay;
        [SerializeField] bool enableKeys = true;

        const float Max = 100f;
        float health = 100f, stamina = 100f, sanity = 100f, cap = 100f;
        int wakeLevel;
        int needIndex;
        readonly int[] needLevels = new int[8];

#if UNITY_EDITOR || DEVELOPMENT_BUILD
        void Update()
        {
            if (!enableKeys) return;
            var kb = Keyboard.current;
            if (kb == null || !kb.leftAltKey.isPressed) return;

            if (kb.digit1Key.wasPressedThisFrame) { health = Mathf.Max(0f, health - 10f); hud.SetHealth(health, Max); }
            if (kb.digit2Key.wasPressedThisFrame) { health = Mathf.Min(Max, health + 10f); hud.SetHealth(health, Max); }
            if (kb.digit3Key.wasPressedThisFrame) { stamina = Mathf.Max(0f, stamina - 10f); hud.SetStamina(stamina, Max, cap); }
            if (kb.digit4Key.wasPressedThisFrame) { stamina = Mathf.Min(cap, stamina + 10f); hud.SetStamina(stamina, Max, cap); }
            if (kb.digit5Key.wasPressedThisFrame) { sanity = Mathf.Max(0f, sanity - 10f); hud.SetSanity(sanity, Max); }
            if (kb.digit6Key.wasPressedThisFrame) { sanity = Mathf.Min(Max, sanity + 10f); hud.SetSanity(sanity, Max); }
            if (kb.digit7Key.wasPressedThisFrame)
            {
                cap = cap <= 40f ? 100f : cap - 20f;
                stamina = Mathf.Min(stamina, cap);
                hud.SetStamina(stamina, Max, cap);
            }
            if (kb.digit8Key.wasPressedThisFrame) CycleNeed();
            if (kb.digit9Key.wasPressedThisFrame)
            {
                var t = hud.FindTile(NeedKind.Stimmung);
                hud.SetNeed(NeedKind.Stimmung, t.Positive ? 0 : 2, !t.Positive);
            }
            if (kb.digit0Key.wasPressedThisFrame) { wakeLevel = (wakeLevel + 1) % 6; wake.Show(wakeLevel); }
            if (kb.minusKey.wasPressedThisFrame) ShowNewDay(false);
            if (kb.equalsKey.wasPressedThisFrame) ShowNewDay(true);
        }

        void CycleNeed()
        {
            var kind = (NeedKind)needIndex;
            needLevels[needIndex] = (needLevels[needIndex] + 1) % 5;
            hud.SetNeed(kind, needLevels[needIndex]);
            if (needLevels[needIndex] == 0) needIndex = (needIndex + 1) % needLevels.Length;
        }

        void ShowNewDay(bool midnight)
        {
            var events = new List<NightEvent>
            {
                new NightEvent(NightEventKind.Quiet, "The night was quiet. Nothing stirred."),
                new NightEvent(NightEventKind.Loss, "Tobias did not return."),
                new NightEvent(NightEventKind.Warning, "The hideout is stirring."),
                new NightEvent(NightEventKind.Talisman, "+1 Talisman"),
            };
            newDay.Show(2, midnight, events);
        }
#endif
    }
}
