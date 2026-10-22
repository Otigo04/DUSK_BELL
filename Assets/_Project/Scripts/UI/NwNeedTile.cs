using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Nightward.UI
{
    public enum NeedKind { Hunger, Durst, Muede, Rausch, Verletzt, Stimmung, Gesellschaft, Anspannung, Erschoepft, Kalt, Verstoert }

    /// <summary>Texte der Stufen (Englisch, wie Art/UI/HUD_Neu/Beduerfnisse_Texte.json), Index = (int)NeedKind.</summary>
    public static class NwNeedTexts
    {
        static readonly string[][] Stages =
        {
            new[] { "Your stomach growls.", "I'm hungry.", "I'm really hungry.", "I'm starving." },
            new[] { "Your mouth feels dry.", "I'm thirsty.", "I'm really thirsty.", "I'm parched." },
            new[] { "A little drowsy.", "I'm tired.", "I'm exhausted.", "I can't keep my eyes open." },
            new[] { "Tipsy.", "Drunk.", "Very drunk.", "Wasted." },
            new[] { "A scratch.", "I'm hurt.", "I'm badly hurt.", "I'm barely standing." },
            new[] { "Feeling a bit down.", "I'm unhappy.", "I'm miserable.", "I feel hollow." },
            new[] { "A bit lonely.", "I'm lonely.", "I'm really lonely.", "I haven't spoken to anyone." },
            new[] { "A little tense.", "I'm on edge.", "I'm stressed.", "I'm about to panic." },
            new[] { "A bit winded.", "I'm out of breath.", "My legs are shaking.", "I'm completely spent." },
            new[] { "A chill in the air.", "I'm cold.", "I'm freezing.", "I'm frozen to the bone." },
            new[] { "Slightly uneasy.", "I'm rattled.", "I'm losing my grip.", "I don't trust my own mind." },
        };

        static readonly string[][] Positive =
        {
            null, null, null, null, null,
            new[] { "Feeling good.", "I'm happy." },
            new[] { "Good company.", "I'm among friends." },
            new[] { "Feeling relaxed.", "I'm completely calm." },
            null, null, null,
        };

        public static bool HasPositive(NeedKind kind) => Positive[(int)kind] != null;

        public static string Get(NeedKind kind, int level, bool positive)
        {
            var list = positive ? Positive[(int)kind] : Stages[(int)kind];
            if (list == null || level < 1) return "";
            return list[Mathf.Min(level, list.Length) - 1];
        }
    }

    /// <summary>
    /// Eine Bedarfs-/Stimmungskachel (22x22) am rechten Rand. Erscheint nur, wenn der Zustand aktiv ist (Stufe 1-4,
    /// bei Stimmung/Gesellschaft/Anspannung auch positiv 1-2). Hover oder Klick zeigt links das Flyout mit dem Text
    /// in der Stufenfarbe. Beim Stufenwechsel blitzt der Rand 0,3 s auf.
    /// </summary>
    public class NwNeedTile : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler
    {
        [SerializeField] NeedKind kind;
        [SerializeField] Image tile;
        [SerializeField] Image symbolOverlay;        // nur waehrend des Blitzes sichtbar (16x16 bei 3,1)
        [SerializeField] Sprite flashTile;           // Kachel_Blitz: heller Rand
        [SerializeField] Sprite symbol;
        [SerializeField] Sprite symbolPositive;
        [SerializeField] RectTransform flyout;
        [SerializeField] Text flyoutText;
        [SerializeField] Sprite[] stageSprites;      // Stufe 1-4
        [SerializeField] Sprite[] positiveSprites;   // positiv 1-2, leer = nicht moeglich
        [SerializeField] float flyoutPadding = 10f;
        [Tooltip("So lange muss die Maus auf der Kachel liegen, bis das Flyout erscheint. Klick zeigt es sofort.")]
        [SerializeField] float hoverDelay = 2f;

        int level;
        bool positive;
        bool hover;
        bool pinned;
        bool hoverShown;
        float hoverTime;
        float flashLeft;

        public NeedKind Kind => kind;
        public int Level => level;
        public bool Positive => positive;

        /// <summary>level 0 = Kachel aus. positive = gruene Stimmung (Stufe 1-2).</summary>
        public void Set(int newLevel, bool newPositive = false)
        {
            var sprites = newPositive ? positiveSprites : stageSprites;
            int max = sprites == null ? 0 : sprites.Length;
            newLevel = Mathf.Clamp(newLevel, 0, max);
            if (newLevel == 0) newPositive = false;
            if (newLevel == level && newPositive == positive) return;

            level = newLevel;
            positive = newPositive;
            gameObject.SetActive(level > 0);
            if (level == 0) return;

            string text = NwNeedTexts.Get(kind, level, positive);
            flyoutText.text = text;
            flyoutText.color = positive ? NwTheme.NeedPositive : NwTheme.NeedStage[level - 1];
            flyout.sizeDelta = new Vector2(Mathf.Ceil(NwTextFit.Width(flyoutText, text)) + flyoutPadding, flyout.sizeDelta.y);

            flashLeft = NwTheme.NeedFlash;
            ApplyTile();
            UpdateFlyout();
        }

        void OnDisable()
        {
            hover = false;
            hoverShown = false;
            pinned = false;
            flashLeft = 0f;
            UpdateFlyout();
        }

        /// <summary>Waehrend des Blitzes: Kachel mit hellem Rand plus Symbol, danach das fertige Anzeige-Sprite.</summary>
        void ApplyTile()
        {
            if (level < 1) return;
            bool blitz = flashLeft > 0f && flashTile != null;
            tile.sprite = blitz ? flashTile : (positive ? positiveSprites : stageSprites)[level - 1];
            symbolOverlay.sprite = positive ? symbolPositive : symbol;
            symbolOverlay.enabled = blitz;
        }

        void Update()
        {
            if (hover && !hoverShown)
            {
                hoverTime += Time.unscaledDeltaTime;
                if (hoverTime >= hoverDelay) { hoverShown = true; UpdateFlyout(); }
            }
            if (flashLeft <= 0f) return;
            flashLeft -= Time.unscaledDeltaTime;
            if (flashLeft <= 0f) ApplyTile();
        }

        void UpdateFlyout()
        {
            bool show = level > 0 && (hoverShown || pinned);
            if (show) RaiseFlyout();
            flyout.gameObject.SetActive(show);
        }

        // Das Flyout reicht nach links ueber andere HUD-Teile (Schnellleiste): eigene Sortierung knapp ueber dem HUD, unter den Dialogen
        void RaiseFlyout()
        {
            var c = flyout.GetComponent<Canvas>();
            if (c == null) c = flyout.gameObject.AddComponent<Canvas>();
            c.overrideSorting = true;
            c.sortingOrder = 105;
        }

        public void OnPointerEnter(PointerEventData e) { hover = true; hoverTime = 0f; }
        public void OnPointerExit(PointerEventData e) { hover = false; hoverShown = false; UpdateFlyout(); }
        public void OnPointerClick(PointerEventData e) { pinned = !pinned; UpdateFlyout(); }

        /// <summary>Flyout dauerhaft zeigen (z. B. fuer Screenshots oder wenn eine Stufe neu ist).</summary>
        public void SetExpanded(bool value) { pinned = value; UpdateFlyout(); }
    }
}
