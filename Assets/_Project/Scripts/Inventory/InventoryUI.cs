using System.Collections.Generic;
using System.Text;
using Nightward.DayNight;
using Nightward.Interaction;
using Nightward.Survival;
using Nightward.UI;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Nightward.Items
{
    /// <summary>
    /// Die Inventar-Oberflaeche (Referenz 480x270, Pixelschrift, Palette der Style-Bibel).
    /// Immer sichtbar: die Schnellleiste unten mit Zahlen 1-8, Hinweis zum gewaehlten Gegenstand und kurze Meldungen.
    /// Mit Tab oder I geht das Inventar auf: Rucksack (8x3) unten, darueber Ausruestung und Werte oder eine Truhe.
    /// Bedienung wie Minecraft: Linksklick nimmt/legt den ganzen Stapel, Rechtsklick die Haelfte bzw. eines, Umschalt+Klick
    /// verschiebt schnell, Doppelklick sammelt gleiche Stapel, Q wirft weg (Strg+Q ganzer Stapel), Zahl ueber einem Platz
    /// tauscht mit der Schnellleiste, E benutzt, Klick neben die Fenster wirft den Stapel in der Hand weg.
    /// Waehrend es offen ist, steht die Weltzeit still (Regelwerk) und der Spieler ist gesperrt.
    /// Die Oberflaeche wird beim Start per Code unter dem HUD-Canvas aufgebaut.
    /// </summary>
    [DefaultExecutionOrder(40)]
    public class InventoryUI : MonoBehaviour
    {
        public static InventoryUI Instance { get; private set; }

        [Header("Sprites (vom Setup gesetzt)")]
        [SerializeField] Sprite slotNormal;
        [SerializeField] Sprite slotHover;
        [SerializeField] Sprite slotSelected;
        [SerializeField] Sprite slotEquip;
        [SerializeField] Sprite slotContainer;
        [SerializeField] Sprite emptyLight;
        [SerializeField] Sprite emptyTalisman;
        [SerializeField] Sprite emptyClothing;
        Sprite emptyLegs, emptyFeet;   // aus Resources/UI (kein Szenen-Feld noetig)
        [Tooltip("9-Slice-Platte fuer Fenster und Hinweis (Plate_Flyout)")]
        [SerializeField] Sprite plate;

        [Header("Verhalten")]
        [SerializeField] bool pauseWorldWhileOpen = true;
        [SerializeField] float toastSeconds = 2.4f;
        [SerializeField] float selectLabelSeconds = 1.8f;

        // Masse in Referenzpixeln
        const int S = 34;          // Platz
        const int Pad = 5;
        const int TitleH = 8;
        const int HotbarBottom = 4;
        const float HotbarScale = 0.75f;            // Schnellleiste kleiner als die Fenster, damit sie weniger vom Bild verdeckt
        const float HotbarTop = HotbarBottom + S * HotbarScale;
        const int WindowGap = 3;
        const int MaxContainerRows = 6;
        const int ContainerCols = 5;               // Behaelter steht neben dem Rucksack (auf breiten Bildern ist darueber kein Platz)
        const int ContainerGap = 4;
        const int CharacterHeight = 62;
        const int StatPitch = 9;
        const float ConsumeBarWidth = 46f;
        const float ToastLift = 22f;               // Meldungen ueber Name und Benutzen-Hinweis

        static readonly Color Dim = new Color(0.05f, 0.04f, 0.09f, 0.55f);

        PlayerInventory inv;
        PlayerInteractor interactor;
        PlayerSurvival survival;
        Canvas canvas;
        RectTransform canvasRect;
        Font font;

        RectTransform root, hotbarRoot, dim, mainWindow, upperWindow, characterPanel, containerPanel, cursorRT, tipRT, toastRoot, hintRoot, consumeBar;
        Text mainTitle, containerTitle, selectLabel, tipText, cursorCount, hintText;
        RectTransform consumeFill, takeAllButton, sortContainerButton;
        Image cursorIcon;
        readonly List<InventorySlotUI> allSlots = new List<InventorySlotUI>();
        readonly List<InventorySlotUI> hotbarSlots = new List<InventorySlotUI>();
        readonly List<InventorySlotUI> containerSlots = new List<InventorySlotUI>();
        readonly Text[] statLines = new Text[10];
        float characterWidth;   // Ausruestung + Werte nebeneinander
        readonly List<Toast> toasts = new List<Toast>();
        readonly StringBuilder sb = new StringBuilder();

        ItemStack cursor;
        ItemContainer container;
        bool openedWithContainer;
        int containerRows = 2, containerOffset;
        InventorySlotUI hover;
        bool built, dirty = true, prevPaused;
        float selectLabelUntil;
        float statTimer;

        class Toast { public Text text; public float until; }

        public bool IsOpen { get; private set; }
        public bool HasCursorItem => cursor != null;

        // ------------------------------------------------------------------ Aufbau
        void Awake() => Instance = this;

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Start() => TryBuild();

        bool TryBuild()
        {
            if (built) return true;
            inv = PlayerInventory.Instance;
            var hud = NwGameHud.Instance;
            if (inv == null || hud == null) return false;
            interactor = inv.GetComponent<PlayerInteractor>();
            survival = inv.GetComponent<PlayerSurvival>();
            canvas = hud.GetComponentInParent<Canvas>();
            if (canvas == null) return false;
            canvasRect = canvas.GetComponent<RectTransform>();
            var uiRoot = canvas.GetComponent<NwUIRoot>();
            font = uiRoot != null ? uiRoot.PixelFont : null;

            BuildAll();
            // Hinweis "F - Pick up ..." ueber Gegenstaenden und Behaeltern
            var hint = inv.GetComponent<InteractHintUI>();
            if (hint == null) hint = inv.gameObject.AddComponent<InteractHintUI>();
            hint.Init(canvas, font, plate);
            inv.Main.SlotChanged += _ => dirty = true;
            inv.Equipment.SlotChanged += _ => dirty = true;
            inv.SelectedChanged += OnSelectedChanged;
            inv.Message += Toast_;
            if (survival != null) survival.Message += Toast_;
            built = true;
            return true;
        }

        void BuildAll()
        {
            root = NewRT("UI_Inventar", canvas.transform);
            Stretch(root);

            // Hinter allem: Abdunkelung, faengt Klicks neben den Fenstern ab
            dim = NewRT("Abdunkelung", root);
            Stretch(dim);
            var dimImg = dim.gameObject.AddComponent<Image>();
            dimImg.color = Dim;
            dimImg.raycastTarget = true;
            dim.gameObject.AddComponent<InventoryBackdrop>().ui = this;
            dim.gameObject.SetActive(false);

            BuildHotbar();
            BuildMainWindow();
            BuildUpperWindow();
            BuildToasts();

            // Stapel in der Hand und Hinweiskasten ganz oben
            cursorRT = NewRT("Cursor", root);
            Anchor(cursorRT, new Vector2(0.5f, 0.5f), new Vector2(32, 32));
            cursorIcon = cursorRT.gameObject.AddComponent<Image>();
            cursorIcon.raycastTarget = false;
            cursorIcon.preserveAspect = true;
            cursorCount = MakeText(cursorRT, "Anzahl", 8, NwTheme.TextDefault, TextAnchor.LowerRight);
            Rect(cursorCount.rectTransform, new Vector2(1, 0), new Vector2(1, 0), new Vector2(1, 0), new Vector2(0, 1), new Vector2(34, 10));
            cursorRT.gameObject.SetActive(false);

            tipRT = NewRT("Hinweis", root);
            Anchor(tipRT, new Vector2(0.5f, 0.5f), new Vector2(120, 40));
            tipRT.pivot = new Vector2(0, 1);
            var tipBg = tipRT.gameObject.AddComponent<Image>();
            tipBg.sprite = plate;
            tipBg.type = Image.Type.Sliced;
            tipBg.raycastTarget = false;
            tipText = MakeText(tipRT, "Text", 8, NwTheme.TextDefault, TextAnchor.UpperLeft);
            tipText.supportRichText = true;
            tipText.horizontalOverflow = HorizontalWrapMode.Wrap;
            Rect(tipText.rectTransform, Vector2.zero, Vector2.one, new Vector2(0, 1), new Vector2(5, -4), new Vector2(-5, -4), true);
            tipRT.gameObject.SetActive(false);

            RefreshAll();
            SetWindowsVisible(false);
        }

        // --- Schnellleiste
        void BuildHotbar()
        {
            int n = inv.HotbarSize;
            hotbarRoot = NewRT("Schnellleiste", root);
            Rect(hotbarRoot, new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, HotbarBottom), new Vector2(n * S, S));
            hotbarRoot.localScale = new Vector3(HotbarScale, HotbarScale, 1f);

            for (int i = 0; i < n; i++)
            {
                var slot = MakeSlot(hotbarRoot, new Vector2(i * S, 0), inv.Main, i, SlotKind.Hotbar);
                slot.hint = MakeText(slot.transform, "Zahl", 8, NwTheme.TextDim, TextAnchor.UpperLeft);
                Rect(slot.hint.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(3, -2), new Vector2(12, 10));
                slot.hint.text = (i + 1).ToString();
                hotbarSlots.Add(slot);
            }

            // Name des gewaehlten Gegenstands ueber der Leiste
            selectLabel = MakeText(root, "Auswahl", 8, NwTheme.TextDefault, TextAnchor.LowerCenter);
            Rect(selectLabel.rectTransform, new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, HotbarTop + 1), new Vector2(200, 10));
            selectLabel.text = "";

            // Benutzen-Hinweis ("RMB Eat") ueber dem gewaehlten Platz, waehrend des Verzehrs ersetzt ihn ein kleiner Balken
            hintRoot = NewRT("Benutzen", root);
            Rect(hintRoot, new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, HotbarTop + 1), new Vector2(90, 10));
            hintText = MakeText(hintRoot, "Text", 8, NwTheme.TextDefault, TextAnchor.LowerCenter);
            hintText.supportRichText = true;
            Stretch(hintText.rectTransform);
            consumeBar = NewRT("Balken", root);
            Rect(consumeBar, new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, HotbarTop + 3), new Vector2(ConsumeBarWidth, 6));
            var barBack = NewRT("Hinten", consumeBar);
            Stretch(barBack);
            var backImg = barBack.gameObject.AddComponent<Image>();
            backImg.color = NwTheme.TextShadow;
            backImg.raycastTarget = false;
            consumeFill = NewRT("Fuellung", consumeBar);
            consumeFill.anchorMin = new Vector2(0, 0);
            consumeFill.anchorMax = new Vector2(0, 1);
            consumeFill.pivot = new Vector2(0, 0.5f);
            consumeFill.anchoredPosition = new Vector2(1, 0);
            consumeFill.sizeDelta = new Vector2(0, -2);
            var fillImg = consumeFill.gameObject.AddComponent<Image>();
            fillImg.color = NwTheme.Title;
            fillImg.raycastTarget = false;
            hintRoot.gameObject.SetActive(false);
            consumeBar.gameObject.SetActive(false);
            UpdateSelection();
        }

        // --- Rucksack-Fenster
        void BuildMainWindow()
        {
            int cols = inv.BackpackColumns, rows = inv.BackpackRows;
            float w = cols * S + Pad * 2, h = Pad * 2 + TitleH + rows * S;
            mainWindow = Window("Rucksack", w, h, HotbarTop + WindowGap);

            mainTitle = MakeText(mainWindow, "Titel", 8, NwTheme.Title, TextAnchor.UpperLeft);
            mainTitle.text = "Backpack";
            Rect(mainTitle.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(Pad, -Pad + 1), new Vector2(120, 10));

            MakeButton(mainWindow, "Sort", new Vector2(w - Pad - 22, -Pad + 1), new Vector2(22, 10), () => { inv.Main.Sort(inv.HotbarSize); });

            for (int r = 0; r < rows; r++)
                for (int c = 0; c < cols; c++)
                    MakeSlot(mainWindow, new Vector2(Pad + c * S, -(Pad + TitleH + r * S)), inv.Main, inv.HotbarSize + r * cols + c, SlotKind.Backpack);
        }

        // --- Oberes Fenster: Ausruestung + Werte, oder Truhe
        void BuildUpperWindow()
        {
            float w = inv.BackpackColumns * S + Pad * 2;
            float bottom = mainWindow.anchoredPosition.y + mainWindow.sizeDelta.y + WindowGap;
            upperWindow = Window("Oben", w, CharacterHeight, bottom);

            // Modus Charakter: Ausruestung links, Werte rechts
            characterPanel = NewRT("Charakter", upperWindow);
            Stretch(characterPanel);
            var title = MakeText(characterPanel, "Titel", 8, NwTheme.Title, TextAnchor.UpperLeft);
            title.text = "Equipment";
            Rect(title.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(Pad, -Pad + 1), new Vector2(100, 10));
            var statsTitle = MakeText(characterPanel, "TitelWerte", 8, NwTheme.Title, TextAnchor.UpperLeft);
            statsTitle.text = "Condition";
            float statsX = Pad + inv.Equipment.Size * (S + 3) + 12;
            characterWidth = statsX + 2 * 76 + Pad;
            emptyLegs = Resources.Load<Sprite>("UI/Leer_Hose");
            emptyFeet = Resources.Load<Sprite>("UI/Leer_Schuhe");
            Rect(statsTitle.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(statsX, -Pad + 1), new Vector2(100, 10));

            for (int i = 0; i < inv.Equipment.Size; i++)
            {
                var slot = MakeSlot(characterPanel, new Vector2(Pad + i * (S + 3), -(Pad + TitleH + 3)), inv.Equipment, i, SlotKind.Equipment);
                slot.background.sprite = slotEquip;
                slot.normalSprite = slotEquip;
                switch (inv.Equipment.FilterOf(i))
                {
                    case EquipSlotKind.Light: slot.placeholder.sprite = emptyLight; break;
                    case EquipSlotKind.Talisman: slot.placeholder.sprite = emptyTalisman; break;
                    case EquipSlotKind.Clothing: slot.placeholder.sprite = emptyClothing; break;
                    case EquipSlotKind.Legs: slot.placeholder.sprite = emptyLegs; break;
                    case EquipSlotKind.Feet: slot.placeholder.sprite = emptyFeet; break;
                }
            }
            for (int i = 0; i < statLines.Length; i++)
            {
                int col = i / 5, row = i % 5;
                var t = MakeText(characterPanel, "Wert" + i, 8, NwTheme.TextDefault, TextAnchor.UpperLeft);
                Rect(t.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(statsX + col * 76, -(Pad + TitleH + 2 + row * StatPitch)), new Vector2(74, 10));
                statLines[i] = t;
            }

            // Modus Truhe
            containerPanel = NewRT("Truhe", upperWindow);
            Stretch(containerPanel);
            containerTitle = MakeText(containerPanel, "Titel", 8, NwTheme.Title, TextAnchor.UpperLeft);
            Rect(containerTitle.rectTransform, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), new Vector2(Pad, -Pad + 1), new Vector2(160, 10));
            takeAllButton = MakeButton(containerPanel, "Take all", new Vector2(w - Pad - 42, -Pad + 1), new Vector2(42, 10), TakeAll);
            sortContainerButton = MakeButton(containerPanel, "Sort", new Vector2(w - Pad - 42 - 12 - 22, -Pad + 1), new Vector2(22, 10), () => { if (container != null) container.Inv.Sort(0); });
            containerPanel.gameObject.SetActive(false);
        }

        void BuildToasts()
        {
            toastRoot = NewRT("Meldungen", root);
            Rect(toastRoot, new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, HotbarTop + ToastLift), new Vector2(240, 40));
        }

        // ------------------------------------------------------------------ Bau-Helfer
        RectTransform Window(string name, float w, float h, float bottom)
        {
            var rt = NewRT(name, root);
            Rect(rt, new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0, bottom), new Vector2(w, h));
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = plate;
            img.type = Image.Type.Sliced;
            img.raycastTarget = true;     // Klicks auf die Platte zaehlen nicht als "daneben"
            return rt;
        }

        InventorySlotUI MakeSlot(Transform parent, Vector2 topLeft, Inventory source, int index, SlotKind kind)
        {
            var rt = NewRT("Platz_" + index, parent);
            Rect(rt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), topLeft, new Vector2(S, S));
            var slot = rt.gameObject.AddComponent<InventorySlotUI>();
            slot.inventory = source;
            slot.index = index;
            slot.kind = kind;
            slot.normalSprite = kind == SlotKind.Container ? slotContainer : slotNormal;
            slot.hoverSprite = slotHover;
            slot.selectedSprite = slotSelected;
            slot.background = rt.gameObject.AddComponent<Image>();
            slot.background.sprite = slot.normalSprite;
            slot.background.raycastTarget = true;

            var ph = NewRT("Leer", rt);
            Rect(ph, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(32, 32));
            slot.placeholder = ph.gameObject.AddComponent<Image>();
            slot.placeholder.raycastTarget = false;
            slot.placeholder.enabled = false;

            var ic = NewRT("Symbol", rt);
            Rect(ic, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(32, 32));
            slot.icon = ic.gameObject.AddComponent<Image>();
            slot.icon.raycastTarget = false;
            slot.icon.preserveAspect = true;
            slot.icon.enabled = false;

            slot.count = MakeText(rt, "Anzahl", 8, NwTheme.TextDefault, TextAnchor.LowerRight);
            Rect(slot.count.rectTransform, new Vector2(1, 0), new Vector2(1, 0), new Vector2(1, 0), new Vector2(-2, 2), new Vector2(30, 10));

            var bb = NewRT("HaltbarkeitHinten", rt);
            Rect(bb, new Vector2(0, 0), new Vector2(0, 0), new Vector2(0, 0), new Vector2(3, 3), new Vector2(28, 4));
            slot.barBack = bb.gameObject.AddComponent<Image>();
            slot.barBack.color = NwTheme.TextShadow;
            slot.barBack.raycastTarget = false;
            var bf = NewRT("Haltbarkeit", rt);
            Rect(bf, new Vector2(0, 0), new Vector2(0, 0), new Vector2(0, 0), new Vector2(4, 4), new Vector2(26, 2));
            slot.barFill = bf.gameObject.AddComponent<Image>();
            slot.barFill.raycastTarget = false;
            slot.barBack.enabled = slot.barFill.enabled = false;

            slot.Init(this);
            allSlots.Add(slot);
            return slot;
        }

        RectTransform MakeButton(Transform parent, string label, Vector2 topLeft, Vector2 size, System.Action action)
        {
            var rt = NewRT("Knopf_" + label, parent);
            Rect(rt, new Vector2(0, 1), new Vector2(0, 1), new Vector2(0, 1), topLeft, size);
            var hit = rt.gameObject.AddComponent<Image>();
            hit.color = new Color(0, 0, 0, 0);
            hit.raycastTarget = true;
            var t = MakeText(rt, "Text", 8, NwTheme.TextDefault, TextAnchor.UpperRight);
            Stretch(t.rectTransform);
            t.text = label;
            var b = rt.gameObject.AddComponent<InventoryButton>();
            b.label = t;
            b.onClick = action;
            return rt;
        }

        Text MakeText(Transform parent, string name, int size, Color color, TextAnchor anchor)
        {
            var rt = NewRT(name, parent);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = font;
            t.fontSize = size;
            t.color = color;
            t.alignment = anchor;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.supportRichText = false;
            t.raycastTarget = false;
            t.lineSpacing = 1f;
            var sh = rt.gameObject.AddComponent<Shadow>();
            sh.effectColor = NwTheme.TextShadow;
            sh.effectDistance = new Vector2(1, -1);
            return t;
        }

        static RectTransform NewRT(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = parent.gameObject.layer;
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        static void Anchor(RectTransform rt, Vector2 anchor, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = size;
        }

        /// <summary>Ankerpunkt = Pivot, Position/Groesse in Referenzpixeln. Mit stretch: pos/size sind Rand-Offsets (min/max).</summary>
        static void Rect(RectTransform rt, Vector2 aMin, Vector2 aMax, Vector2 pivot, Vector2 pos, Vector2 size, bool stretch = false)
        {
            rt.anchorMin = aMin;
            rt.anchorMax = aMax;
            rt.pivot = pivot;
            if (stretch) { rt.offsetMin = pos; rt.offsetMax = size; }
            else { rt.anchoredPosition = pos; rt.sizeDelta = size; }
        }

        // ------------------------------------------------------------------ Oeffnen und Schliessen
        void SetWindowsVisible(bool v)
        {
            dim.gameObject.SetActive(v);
            mainWindow.gameObject.SetActive(v);
            upperWindow.gameObject.SetActive(v);
        }

        /// <summary>Oeffnet das Inventar, optional mit einem Behaelter (Truhe) oben.</summary>
        public void Open(ItemContainer withContainer = null)
        {
            if (!TryBuild() || IsOpen) return;
            if (survival != null && (survival.Busy || survival.Sim.IsDead)) return;
            if (interactor != null && interactor.Busy) return;

            IsOpen = true;
            container = withContainer;
            openedWithContainer = withContainer != null;
            if (container != null) container.SetOpen(true);
            if (interactor != null) interactor.Lock(true);
            var cycle = DayNightCycle.Instance;
            if (pauseWorldWhileOpen && cycle != null) { prevPaused = cycle.Paused; cycle.Paused = true; }

            SetWindowsVisible(true);
            characterPanel.gameObject.SetActive(container == null);
            containerPanel.gameObject.SetActive(container != null);
            toastRoot.gameObject.SetActive(false);
            LayoutWindows(container != null);
            if (container != null) BuildContainerSlots();
            RefreshAll();
            statTimer = 0f;
        }

        /// <summary>
        /// Ohne Behaelter: Rucksack unten mittig, Ausruestung und Werte darueber. Mit Behaelter: Rucksack links, Behaelter rechts
        /// daneben, beide unten buendig (so passt es auch auf sehr breite Bilder mit wenig Hoehe).
        /// </summary>
        void LayoutWindows(bool withContainer)
        {
            float mainW = mainWindow.sizeDelta.x;
            float bottom = HotbarTop + WindowGap;
            if (!withContainer)
            {
                mainWindow.anchoredPosition = new Vector2(0f, bottom);
                upperWindow.anchoredPosition = new Vector2(0f, bottom + mainWindow.sizeDelta.y + WindowGap);
                upperWindow.sizeDelta = new Vector2(Mathf.Max(mainW, characterWidth), CharacterHeight);
                return;
            }
            float cw = ContainerCols * S + Pad * 2;
            mainWindow.anchoredPosition = new Vector2(-(cw + ContainerGap) / 2f, bottom);
            upperWindow.anchoredPosition = new Vector2((mainW + ContainerGap) / 2f, bottom);
            upperWindow.sizeDelta = new Vector2(cw, upperWindow.sizeDelta.y);
            takeAllButton.anchoredPosition = new Vector2(cw - Pad - 42, -Pad + 1);
            sortContainerButton.anchoredPosition = new Vector2(cw - Pad - 42 - 12 - 22, -Pad + 1);
        }

        public void Close()
        {
            if (!IsOpen) return;
            IsOpen = false;
            ReturnCursor();
            if (container != null) container.SetOpen(false);
            container = null;
            LayoutWindows(false);
            SetWindowsVisible(false);
            toastRoot.gameObject.SetActive(true);
            tipRT.gameObject.SetActive(false);
            hover = null;
            if (interactor != null) interactor.Lock(false);
            var cycle = DayNightCycle.Instance;
            if (pauseWorldWhileOpen && cycle != null) cycle.Paused = prevPaused;
        }

        public void Toggle()
        {
            if (IsOpen) Close(); else Open();
        }

        void BuildContainerSlots()
        {
            foreach (var s in containerSlots) { allSlots.Remove(s); Destroy(s.gameObject); }
            containerSlots.Clear();
            containerTitle.text = container.Title;
            var ci = container.Inv;
            ci.SlotChanged -= OnContainerChanged;
            ci.SlotChanged += OnContainerChanged;
            int cols = ContainerCols;

            // So viele Reihen, wie in die Bildhoehe passen (Seitenverhaeltnis bestimmt die Canvas-Hoehe); der Rest blaettert per Mausrad
            float free = canvasRect.rect.height - (upperWindow.anchoredPosition.y) - (Pad * 2 + TitleH) - 2f;
            int totalRows = Mathf.CeilToInt(ci.Size / (float)cols);
            containerRows = Mathf.Clamp(Mathf.FloorToInt(free / S), 1, Mathf.Min(MaxContainerRows, totalRows));
            containerOffset = 0;
            upperWindow.sizeDelta = new Vector2(upperWindow.sizeDelta.x, Pad * 2 + TitleH + containerRows * S);

            for (int i = 0; i < cols * containerRows; i++)
            {
                int r = i / cols, c = i % cols;
                var slot = MakeSlot(containerPanel, new Vector2(Pad + c * S, -(Pad + TitleH + r * S)), ci, i, SlotKind.Container);
                containerSlots.Add(slot);
            }
            ApplyContainerOffset();
        }

        /// <summary>Mausrad ueber der Truhe blaettert zeilenweise, wenn sie mehr Plaetze hat als sichtbar sind.</summary>
        void ScrollContainer(float wheel)
        {
            int cols = ContainerCols;
            int totalRows = Mathf.CeilToInt(container.Inv.Size / (float)cols);
            int max = Mathf.Max(0, totalRows - containerRows);
            int next = Mathf.Clamp(containerOffset + (wheel > 0f ? -1 : 1), 0, max);
            if (next == containerOffset) return;
            containerOffset = next;
            ApplyContainerOffset();
        }

        void ApplyContainerOffset()
        {
            int cols = ContainerCols;
            for (int i = 0; i < containerSlots.Count; i++)
            {
                int idx = containerOffset * cols + i;
                containerSlots[i].index = idx;
                containerSlots[i].gameObject.SetActive(idx < container.Inv.Size);
            }
            dirty = true;
        }

        void OnContainerChanged(int _) => dirty = true;

        void TakeAll()
        {
            if (container == null) return;
            var ci = container.Inv;
            for (int i = 0; i < ci.Size; i++) InventoryOps.QuickMove(ci, i, inv.Main);
        }

        /// <summary>Stapel in der Hand zurueck in den Rucksack, sonst fallen lassen.</summary>
        void ReturnCursor()
        {
            if (cursor == null) return;
            inv.Main.Add(cursor);
            if (cursor.count > 0) inv.DropStack(cursor);
            cursor = null;
            UpdateCursorVisual();
        }

        // ------------------------------------------------------------------ Hover, Klicks
        public void SetHover(InventorySlotUI s) { hover = s; }
        public void ClearHover(InventorySlotUI s) { if (hover == s) hover = null; }

        public void OnSlotClick(InventorySlotUI s, PointerEventData e)
        {
            if (!IsOpen)
            {
                // Schnellleiste bei geschlossenem Inventar: Linksklick waehlt den Platz
                if (s.kind == SlotKind.Hotbar && e.button == PointerEventData.InputButton.Left) inv.Select(s.index);
                return;
            }
            var kb = Keyboard.current;
            bool shift = kb != null && kb.leftShiftKey.isPressed;

            if (e.button == PointerEventData.InputButton.Left)
            {
                if (shift && cursor == null) QuickMove(s);
                else if (e.clickCount >= 2 && cursor != null) InventoryOps.CollectToCursor(s.inventory, ref cursor);
                else InventoryOps.LeftClick(s.inventory, s.index, ref cursor);
            }
            else if (e.button == PointerEventData.InputButton.Right)
            {
                if (shift && cursor == null) inv.Use(s.inventory, s.index);
                else InventoryOps.RightClick(s.inventory, s.index, ref cursor);
            }
            UpdateCursorVisual();
            dirty = true;
        }

        void QuickMove(InventorySlotUI s)
        {
            var st = s.inventory.Get(s.index);
            if (st == null) return;
            if (s.kind == SlotKind.Equipment) { InventoryOps.QuickMove(inv.Equipment, s.index, inv.Main); return; }
            if (s.kind == SlotKind.Container) { InventoryOps.QuickMove(container.Inv, s.index, inv.Main); return; }
            if (container != null) { InventoryOps.QuickMove(inv.Main, s.index, container.Inv); return; }
            if (st.def.equipSlot != EquipSlotKind.None) { inv.Use(inv.Main, s.index); return; }
            if (s.index < inv.HotbarSize) InventoryOps.QuickMove(inv.Main, s.index, inv.Main, inv.HotbarSize, -1);
            else InventoryOps.QuickMove(inv.Main, s.index, inv.Main, 0, inv.HotbarSize - 1);
        }

        public void OnBackdropClick(PointerEventData e)
        {
            if (cursor == null) return;
            if (e.button == PointerEventData.InputButton.Right && cursor.count > 1)
            {
                inv.DropStack(new ItemStack(cursor.def, 1, cursor.durability));
                cursor.count--;
            }
            else
            {
                inv.DropStack(cursor);
                cursor = null;
            }
            UpdateCursorVisual();
        }

        // ------------------------------------------------------------------ Update
        void Update()
        {
            if (!built && !TryBuild()) return;
            var kb = Keyboard.current;
            if (kb == null) return;

            bool dead = survival != null && survival.Sim.IsDead;
            if (kb.tabKey.wasPressedThisFrame || kb.iKey.wasPressedThisFrame) { if (IsOpen) Close(); else if (!dead) Open(); }
            else if (IsOpen && (kb.escapeKey.wasPressedThisFrame || (container != null && kb.fKey.wasPressedThisFrame))) Close();
            if (IsOpen && dead) Close();
            if (IsOpen && openedWithContainer && container == null) Close();   // Behaelter wurde zerstoert

            UpdateToasts();
            UpdateUseHint();

            if (!IsOpen) return;

            HandleHoverKeys(kb);
            var mouse = Mouse.current;
            if (container != null && mouse != null)
            {
                float wheel = mouse.scroll.ReadValue().y;
                if (Mathf.Abs(wheel) > 0.1f) ScrollContainer(wheel);
            }
            UpdateCursorPosition();
            UpdateTooltip();

            statTimer -= Time.unscaledDeltaTime;
            if (statTimer <= 0f && container == null) { statTimer = 0.2f; UpdateStats(); }
        }

        void LateUpdate()
        {
            if (!built || !dirty) return;
            dirty = false;
            RefreshAll();
        }

        void HandleHoverKeys(Keyboard kb)
        {
            if (hover == null) return;
            var st = hover.inventory.Get(hover.index);

            if (kb.qKey.wasPressedThisFrame && st != null && cursor == null)
                inv.DropFromSlot(hover.inventory, hover.index, kb.leftCtrlKey.isPressed ? int.MaxValue : 1);
            if (kb.eKey.wasPressedThisFrame && st != null && cursor == null) inv.Use(hover.inventory, hover.index);

            // Zahl ueber einem Platz: mit dem Schnellleisten-Platz tauschen
            if (hover.inventory == inv.Main)
                for (int i = 0; i < inv.HotbarSize; i++)
                    if (kb[(Key)((int)Key.Digit1 + i)].wasPressedThisFrame && cursor == null) InventoryOps.Swap(inv.Main, hover.index, i);
        }

        // ------------------------------------------------------------------ Benutzen-Hinweis und Verzehr-Balken
        /// <summary>
        /// Ueber der Schnellleiste: bei einem benutzbaren Gegenstand in der Hand "RMB Eat" ueber dem gewaehlten Platz,
        /// waehrend des Verzehrs stattdessen ein kleiner Fortschrittsbalken. Der Name des Gegenstands steht darueber.
        /// </summary>
        void UpdateUseHint()
        {
            bool consuming = inv.IsConsuming;
            string verb = null;
            if (!IsOpen && !consuming && cursor == null && inv.CanUseNow) verb = inv.UseVerb(inv.SelectedStack);

            float x = (inv.Selected + 0.5f - inv.HotbarSize / 2f) * S * HotbarScale;
            bool showText = verb != null;
            hintRoot.gameObject.SetActive(showText);
            consumeBar.gameObject.SetActive(consuming);
            if (showText)
            {
                hintRoot.anchoredPosition = new Vector2(x, HotbarTop + 1);
                hintText.text = "<color=#" + Hex(NwTheme.TextDim) + ">RMB</color> " + verb;
            }
            if (consuming)
            {
                consumeBar.anchoredPosition = new Vector2(x, HotbarTop + 3);
                consumeFill.sizeDelta = new Vector2(Mathf.Round((ConsumeBarWidth - 2f) * inv.ConsumeProgress), -2f);
            }

            if (selectLabel != null)
            {
                selectLabel.enabled = Time.unscaledTime < selectLabelUntil;
                selectLabel.rectTransform.anchoredPosition = new Vector2(0, HotbarTop + 1 + (showText || consuming ? 10f : 0f));
            }
        }

        // ------------------------------------------------------------------ Anzeige
        void RefreshAll()
        {
            foreach (var s in allSlots) if (s != null) s.Refresh();
            UpdateSelection();
        }

        void OnSelectedChanged(int index)
        {
            UpdateSelection();
            var st = inv.SelectedStack;
            if (selectLabel != null)
            {
                selectLabel.text = st != null ? st.def.displayName : "";
                selectLabel.color = st != null ? ItemDef.RarityColor(st.def.rarity) : NwTheme.TextDefault;
                selectLabelUntil = Time.unscaledTime + selectLabelSeconds;
            }
        }

        void UpdateSelection()
        {
            for (int i = 0; i < hotbarSlots.Count; i++) hotbarSlots[i].SetSelected(i == inv.Selected);
        }

        void UpdateCursorVisual()
        {
            bool has = cursor != null;
            cursorRT.gameObject.SetActive(has);
            if (!has) return;
            cursorIcon.sprite = cursor.def.icon;
            cursorCount.text = cursor.count > 1 ? cursor.count.ToString() : "";
            UpdateCursorPosition();
        }

        void UpdateCursorPosition()
        {
            var mouse = Mouse.current;
            if (mouse == null) return;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(canvasRect, mouse.position.ReadValue(), null, out var p);
            if (cursorRT.gameObject.activeSelf) cursorRT.anchoredPosition = p;
            tipPos = p;
        }

        Vector2 tipPos;

        void UpdateStats()
        {
            var sim = survival.Sim;
            Stat(0, "Health", StatId.Health);
            Stat(1, "Stamina", StatId.Stamina);
            Stat(2, "Sanity", StatId.Sanity);
            Stat(3, "Hunger", StatId.Hunger);
            Stat(4, "Thirst", StatId.Thirst);
            Stat(5, "Fatigue", StatId.Fatigue);
            Stat(6, "Cold", StatId.Cold);
            Stat(7, "Stress", StatId.Stress);
            Stat(8, "Mood", StatId.Happiness);
            Stat(9, "Lonely", StatId.Loneliness);
        }

        void Stat(int line, string label, StatId id)
        {
            var sim = survival.Sim;
            float sev = sim.Severity(id);
            Color c = sev < 0.5f ? NwTheme.TextDefault : sev < 0.75f ? NwTheme.Title : sev < 0.9f ? NwTheme.Warning : NwTheme.Loss;
            // Beduerfnisse zeigen "wie schlimm" (Hunger 80 = hungrig), die Vitalwerte "wie viel" (Leben 80 = gut)
            float shown = sim.Value(id);
            statLines[line].text = $"{label,-8}{Mathf.RoundToInt(shown),3}";
            statLines[line].color = c;
        }

        void UpdateTooltip()
        {
            ItemStack st = hover != null ? hover.inventory.Get(hover.index) : null;
            bool showEmptyEquip = hover != null && st == null && hover.kind == SlotKind.Equipment && cursor == null;
            if (cursor != null || (st == null && !showEmptyEquip)) { tipRT.gameObject.SetActive(false); return; }

            sb.Clear();
            if (st != null) BuildTooltip(st, hover);
            else sb.Append("<color=#ffd27a>").Append(EquipName(hover.inventory.FilterOf(hover.index))).Append("</color>\n<color=#9a95a0>Empty slot</color>");
            tipText.text = sb.ToString();

            const float width = 150f;
            tipRT.sizeDelta = new Vector2(width, 20);
            tipText.rectTransform.sizeDelta = new Vector2(width - 10, 10);
            float h = tipText.preferredHeight;
            tipRT.sizeDelta = new Vector2(width, h + 9);
            tipRT.gameObject.SetActive(true);

            // Neben dem Zeiger, im Bild halten
            float cw = canvasRect.rect.width, ch = canvasRect.rect.height;
            Vector2 pos = tipPos + new Vector2(10, -4);
            float left = pos.x + cw / 2f, top = pos.y + ch / 2f;
            if (left + width > cw - 2) pos.x = tipPos.x - 10 - width;
            if (top - tipRT.sizeDelta.y < 2) pos.y = tipPos.y + 6 + tipRT.sizeDelta.y;
            tipRT.anchoredPosition = pos;
        }

        static string EquipName(EquipSlotKind k)
        {
            switch (k)
            {
                case EquipSlotKind.Light: return "Light";
                case EquipSlotKind.Talisman: return "Talisman";
                case EquipSlotKind.Clothing: return "Clothing";
                case EquipSlotKind.Legs: return "Trousers";
                case EquipSlotKind.Feet: return "Shoes";
                default: return "Slot";
            }
        }

        static string Hex(Color c) => ColorUtility.ToHtmlStringRGB(c);

        void BuildTooltip(ItemStack st, InventorySlotUI slot)
        {
            var d = st.def;
            sb.Append("<color=#").Append(Hex(ItemDef.RarityColor(d.rarity))).Append('>').Append(d.displayName).Append("</color>");
            if (st.count > 1) sb.Append(" <color=#9a95a0>x").Append(st.count).Append("</color>");
            sb.Append("\n<color=#9a95a0>").Append(d.category);
            if (d.rarity != ItemRarity.Common) sb.Append(" - ").Append(d.rarity);
            sb.Append("</color>");
            if (!string.IsNullOrEmpty(d.description)) sb.Append('\n').Append(d.description);

            var cfg = survival.Sim.Config;
            if (!string.IsNullOrEmpty(d.consumableId))
            {
                var c = cfg.Consumable(d.consumableId);
                if (c != null)
                    foreach (var a in c.instant)
                    {
                        var sd = cfg.Stat(a.stat);
                        if (sd == null || Mathf.Approximately(a.amount, 0f)) continue;
                        bool good = (a.amount > 0f) == sd.higherIsBetter;
                        sb.Append("\n<color=").Append(good ? "#9ab87a" : "#d64a6a").Append('>').Append(a.amount > 0 ? "+" : "").Append(Mathf.RoundToInt(a.amount)).Append(' ').Append(sd.displayName).Append("</color>");
                    }
            }
            if (d.IsWeapon)
            {
                sb.Append("\n<color=#ffa550>Damage ").Append(d.damage).Append("</color>");
                if (!string.IsNullOrEmpty(d.ammoItemId)) sb.Append("  <color=#9a95a0>needs ").Append(d.ammoItemId).Append("</color>");
            }
            if (d.IsLight) sb.Append("\n<color=#ffd27a>Light, radius ").Append(Mathf.RoundToInt(d.lightRadius)).Append("</color>");
            foreach (var e in d.equipEffects) sb.Append("\n<color=#6b7fb8>").Append(EffectText(e, cfg)).Append("</color>");
            if (d.HasDurability) sb.Append("\n<color=#9a95a0>").Append(d.IsLight ? "Fuel " : "Durability ").Append(Mathf.CeilToInt(st.durability)).Append('/').Append(d.maxDurability).Append("</color>");
            if (d.value > 0) sb.Append("\n<color=#9a95a0>Value ").Append(d.value).Append(" WG</color>");

            // Bedienhinweise
            var hints = new List<string>();
            if (d.equipSlot != EquipSlotKind.None) hints.Add(slot.kind == SlotKind.Equipment ? "E: take off" : "E: equip");
            else if (!string.IsNullOrEmpty(d.consumableId)) hints.Add("E: " + d.useVerb.ToLowerInvariant());
            else if (!string.IsNullOrEmpty(d.refuelsItemId)) hints.Add("E: refill");
            hints.Add("Q: drop");
            sb.Append("\n<color=#6e6a74>").Append(string.Join("  ", hints)).Append("</color>");
        }

        static string EffectText(Effect e, SurvivalConfig cfg)
        {
            var sd = EffectKinds.UsesStat(e.kind) ? cfg.Stat(e.stat) : null;
            string name = sd != null ? sd.displayName : "";
            switch (e.kind)
            {
                case EffectKind.StatRate: return $"{name} {(e.value > 0 ? "+" : "")}{e.value:0.#}/h";
                case EffectKind.StatDrainMult: return $"{name} worsens x{e.value:0.##}";
                case EffectKind.StatRecoverMult: return $"{name} recovers x{e.value:0.##}";
                case EffectKind.MoveSpeedMult: return $"Speed x{e.value:0.##}";
                case EffectKind.DamageTakenMult: return $"Damage taken x{e.value:0.##}";
                case EffectKind.StaminaCostMult: return $"Stamina cost x{e.value:0.##}";
                default: return e.ToString();
            }
        }

        // ------------------------------------------------------------------ Meldungen
        void Toast_(string text)
        {
            if (!built || string.IsNullOrEmpty(text)) return;
            // Gleiche Meldung nur auffrischen (z. B. mehrfaches Aufheben)
            foreach (var t in toasts) if (t.text.text == text) { t.until = Time.unscaledTime + toastSeconds; return; }
            var tx = MakeText(toastRoot, "Meldung", 8, NwTheme.TextDefault, TextAnchor.LowerCenter);
            Rect(tx.rectTransform, new Vector2(0.5f, 0), new Vector2(0.5f, 0), new Vector2(0.5f, 0), Vector2.zero, new Vector2(240, 10));
            tx.text = text;
            toasts.Add(new Toast { text = tx, until = Time.unscaledTime + toastSeconds });
            while (toasts.Count > 4) { Destroy(toasts[0].text.gameObject); toasts.RemoveAt(0); }
        }

        void UpdateToasts()
        {
            for (int i = toasts.Count - 1; i >= 0; i--)
                if (Time.unscaledTime >= toasts[i].until) { Destroy(toasts[i].text.gameObject); toasts.RemoveAt(i); }
            // Neueste unten, aeltere darueber; kurz vor Ablauf ausblenden
            for (int i = 0; i < toasts.Count; i++)
            {
                var t = toasts[i];
                int fromBottom = toasts.Count - 1 - i;
                t.text.rectTransform.anchoredPosition = new Vector2(0, fromBottom * 10);
                var c = t.text.color;
                c.a = Mathf.Clamp01((t.until - Time.unscaledTime) / 0.4f);
                t.text.color = c;
            }
        }
    }
}
