using System.Collections.Generic;
using System.Text;
using Nightward.Items;
using UnityEngine;

namespace Nightward.Player
{
    /// <summary>
    /// Zeigt die angelegte Kleidung (Oberteil, Hose, Schuhe) an der Spielfigur. Jedes Kleidungsstueck bringt eine Farbpalette mit
    /// (ItemDef.outfitPalette). Zu jedem Figuren-Sheet gibt es eine Maske (Resources/OutfitMasks/&lt;Mann|Frau&gt;/&lt;sheet&gt;.png, vom Generator
    /// mit NW_MASK=1 gezeichnet): Rot = Bereich (1 Oberteil, 2 Hose, 3 Schuhe), Gruen = Farbstufe. Aus Sheet plus Maske entsteht beim ersten
    /// Gebrauch eine umgefaerbte Kopie, und jedes Bild des Animators wird nach dem Animieren durch das gleiche Bild (gleiche Textur, gleiches
    /// Rechteck) der Kopie ersetzt. Das gilt fuer alle Animationen, ohne zweiten Animator und ohne Clips. Ohne Kleidung oder ohne Maske
    /// bleibt das Originalbild. Die Kopien werden beim Wechsel freigegeben.
    /// </summary>
    [DefaultExecutionOrder(100)]
    public class PlayerOutfit : MonoBehaviour
    {
        // Bereich -> Anzahl Stufen in der Maske
        static readonly int[] Levels = { 0, 4, 3, 4 };

        SpriteRenderer sr;
        PlayerInventory inventory;
        string signature = "";
        readonly Color32[][] palettes = new Color32[4][];

        readonly Dictionary<Sprite, Sprite> variantOf = new Dictionary<Sprite, Sprite>();   // Original -> Variante
        readonly Dictionary<Sprite, Sprite> originalOf = new Dictionary<Sprite, Sprite>();  // Variante -> Original
        readonly Dictionary<string, Texture2D> sheets = new Dictionary<string, Texture2D>(); // Texturname -> Kopie (null = keine)
        bool warnedReadable;

        /// <summary>Unterscheidet die aktuelle Kleidung (leer = Grundkleidung).</summary>
        public string Current => signature;

        void Awake()
        {
            inventory = GetComponent<PlayerInventory>();
            var visual = transform.Find("Visual");
            sr = visual != null ? visual.GetComponent<SpriteRenderer>() : GetComponentInChildren<SpriteRenderer>();
        }

        void LateUpdate()
        {
            if (sr == null || inventory == null || inventory.Equipment == null) return;
            string wanted = ReadEquipment();
            if (wanted != signature)
            {
                Restore();
                Release();
                signature = wanted;
            }
            if (signature.Length == 0) return;
            var cur = sr.sprite;
            if (cur == null || originalOf.ContainsKey(cur)) return;   // schon die Kopie
            sr.sprite = VariantOf(cur);
        }

        void OnDestroy() => Release();

        // Palette je Bereich aus den Ausruestungsplaetzen lesen; gibt eine Kennung der Kombination zurueck
        string ReadEquipment()
        {
            for (int r = 1; r < palettes.Length; r++) palettes[r] = null;
            var sb = new StringBuilder();
            var eq = inventory.Equipment;
            for (int i = 0; i < eq.Size; i++)
            {
                var s = eq.Get(i);
                if (s == null || s.def == null) continue;
                int region = Region(s.def.equipSlot);
                var pal = s.def.outfitPalette;
                if (region == 0 || pal == null || pal.Length < Levels[region]) continue;
                var p = new Color32[Levels[region]];
                sb.Append(region).Append(':');
                for (int k = 0; k < p.Length; k++)
                {
                    p[k] = pal[k];
                    sb.Append(ColorUtility.ToHtmlStringRGB(pal[k]));
                }
                sb.Append(';');
                palettes[region] = p;
            }
            return sb.ToString();
        }

        static int Region(EquipSlotKind k)
        {
            switch (k)
            {
                case EquipSlotKind.Clothing: return 1;
                case EquipSlotKind.Legs: return 2;
                case EquipSlotKind.Feet: return 3;
                default: return 0;
            }
        }

        // Beim Ausziehen sofort das Originalbild zeigen (der Animator schreibt es sonst erst beim naechsten Bildwechsel)
        void Restore()
        {
            if (sr != null && sr.sprite != null && originalOf.TryGetValue(sr.sprite, out var orig)) sr.sprite = orig;
        }

        Sprite VariantOf(Sprite orig)
        {
            if (variantOf.TryGetValue(orig, out var v)) return v;
            v = Build(orig);
            variantOf[orig] = v;
            if (v != orig) originalOf[v] = orig;
            return v;
        }

        Sprite Build(Sprite orig)
        {
            var tex = orig.texture;
            if (tex == null) return orig;
            var sheet = Sheet(tex);
            var r = orig.rect;
            if (sheet == null || r.xMax > sheet.width || r.yMax > sheet.height) return orig;
            var pivot = new Vector2(orig.pivot.x / r.width, orig.pivot.y / r.height);
            var sp = Sprite.Create(sheet, r, pivot, orig.pixelsPerUnit, 0, SpriteMeshType.FullRect);
            sp.name = orig.name;
            return sp;
        }

        Texture2D Sheet(Texture2D src)
        {
            if (sheets.TryGetValue(src.name, out var t)) return t;
            t = null;
            string who = src.name.StartsWith("frau") ? "Frau" : "Mann";
            var mask = Resources.Load<Texture2D>("OutfitMasks/" + who + "/" + src.name);
            if (mask != null)
            {
                if (!src.isReadable || !mask.isReadable)
                {
                    if (!warnedReadable) Debug.LogWarning("[Kleidung] Sheet oder Maske nicht lesbar: " + src.name + " (Import-Einstellung Read/Write).");
                    warnedReadable = true;
                }
                else t = Recolor(src, mask);
                Resources.UnloadAsset(mask);
            }
            sheets[src.name] = t;
            return t;
        }

        Texture2D Recolor(Texture2D src, Texture2D mask)
        {
            var px = src.GetPixels32();
            var mp = mask.GetPixels32();
            if (px.Length != mp.Length) return null;
            for (int i = 0; i < px.Length; i++)
            {
                var m = mp[i];
                if (m.a == 0 || m.r >= palettes.Length) continue;
                var pal = palettes[m.r];
                if (pal == null || m.g >= pal.Length) continue;
                px[i] = new Color32(pal[m.g].r, pal[m.g].g, pal[m.g].b, px[i].a);
            }
            var t = new Texture2D(src.width, src.height, TextureFormat.RGBA32, false)
            {
                name = src.name + "_outfit", filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp,
            };
            t.SetPixels32(px);
            t.Apply(false, true);   // Kopie im Speicher freigeben, nur die Grafikkarte behaelt sie
            return t;
        }

        void Release()
        {
            foreach (var v in originalOf.Keys) if (v != null) Destroy(v);
            foreach (var t in sheets.Values) if (t != null) Destroy(t);
            variantOf.Clear();
            originalOf.Clear();
            sheets.Clear();
        }
    }
}
