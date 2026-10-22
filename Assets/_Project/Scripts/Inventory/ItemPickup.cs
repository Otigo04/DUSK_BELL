using System.Collections;
using System.Collections.Generic;
using Nightward.Interaction;
using UnityEngine;

namespace Nightward.Items
{
    /// <summary>Wie ein Gegenstand in der Welt aufgenommen wird. Default richtet sich nach ItemDef.autoPickup.</summary>
    public enum PickupMode { Default, Manual, Auto }

    /// <summary>
    /// Gegenstand in der Welt: schwebt ueber einem Schatten, Seltenes glimmt in der Farbe der Seltenheit. Mit F aufheben
    /// (Hinweis "F - Pick up Bread"); Muenzen und alles mit autoPickup werden stattdessen vom Spieler in der Naehe angezogen.
    /// Gleiche Gegenstaende, die nah beieinander fallen, verschmelzen zu einem Stapel. Platzierbar im Editor (def + count)
    /// oder per Code ueber ItemPickup.Spawn (Fallenlassen, Beute). Passt nichts mehr in den Rucksack, bleibt er liegen.
    /// </summary>
    public class ItemPickup : Interactable
    {
        static readonly List<ItemPickup> active = new List<ItemPickup>();
        static readonly RaycastHit2D[] hits = new RaycastHit2D[8];
        static Sprite shadowSprite, glowSprite;

        const float MergeRadius = 0.55f;

        [SerializeField] ItemDef def;
        [SerializeField, Min(1)] int count = 1;
        [Tooltip("Sekunden nach dem Erscheinen, bevor er aufgehoben werden kann")]
        [SerializeField] float pickupDelay;
        [SerializeField] PickupMode mode = PickupMode.Default;

        public ItemStack Stack { get; set; }

        SpriteRenderer sr, shadowSr, glowSr;
        Transform visual;
        Vector2 velocity;
        float bobSeed;
        float noPickupUntil;
        bool collecting;
        Material worldMaterial;
        int sortingOrder = 4;
        int sortingLayerId;

        public bool IsAuto => mode == PickupMode.Auto || (mode == PickupMode.Default && Stack != null && Stack.def.autoPickup);

        // ------------------------------------------------------------------ Erzeugen
        /// <summary>
        /// Erzeugt einen Gegenstand in der Welt. velocity = Wurfschwung (klingt schnell ab). Liegt schon ein gleicher
        /// Gegenstand dicht daneben, wird zusammengelegt: der zurueckgegebene Pickup ist dann der bestehende.
        /// </summary>
        public static ItemPickup Spawn(ItemStack stack, Vector3 position, Vector2 velocity, PlayerInventory owner = null)
        {
            var merged = TryMerge(stack, position);
            if (merged != null) return merged;

            var go = new GameObject("Item_" + stack.def.id);
            go.transform.position = position;
            var p = go.AddComponent<ItemPickup>();
            p.Stack = stack;
            p.velocity = velocity;
            p.noPickupUntil = Time.time + 0.3f;
            if (owner != null) p.CopyWorldLook(owner);
            return p;
        }

        /// <summary>Spawn-Punkt vor dem Spieler: bleibt auf der Spielerseite einer Wand, statt dahinter zu landen.</summary>
        public static Vector3 SafePoint(Vector3 from, Vector3 to)
        {
            Vector2 d = to - from;
            float len = d.magnitude;
            if (len < 0.001f) return to;
            if (FirstSolidHit(from, d / len, len, out var hit)) return from + (Vector3)(d / len) * Mathf.Max(0f, hit.distance - 0.15f);
            return to;
        }

        static ItemPickup TryMerge(ItemStack stack, Vector3 position)
        {
            var d = stack.def;
            if (!d.IsStackable || d.HasDurability) return null;
            foreach (var p in active)
            {
                if (p == null || p.collecting || p.Stack == null || p.Stack.def != d || p.Stack.Space <= 0) continue;
                if (((Vector2)p.transform.position - (Vector2)position).sqrMagnitude > MergeRadius * MergeRadius) continue;
                int move = Mathf.Min(p.Stack.Space, stack.count);
                p.Stack.count += move;
                stack.count -= move;
                if (stack.count <= 0) return p;
            }
            return null;
        }

        void CopyWorldLook(PlayerInventory owner)
        {
            worldMaterial = owner.WorldMaterial;
            sortingOrder = owner.WorldSortingOrder;
            sortingLayerId = owner.WorldSortingLayerId;
        }

        // ------------------------------------------------------------------ Lebenszyklus
        protected override void OnEnable()
        {
            base.OnEnable();
            active.Add(this);
        }

        protected override void OnDisable()
        {
            base.OnDisable();
            active.Remove(this);
        }

        void Awake()
        {
            key = InteractKey.F;
            Prompt = "Pick up";
            if (Stack == null && def != null) Stack = new ItemStack(def, count);
            bobSeed = Random.value * 10f;
            noPickupUntil = Mathf.Max(noPickupUntil, Time.time + pickupDelay);
        }

        void Reset()
        {
            key = InteractKey.F;
            Prompt = "Pick up";
        }

        void Start()
        {
            if (Stack == null || Stack.def == null) { Destroy(gameObject); return; }
            var inv = PlayerInventory.Instance;
            if (worldMaterial == null && inv != null) CopyWorldLook(inv);

            glowSr = MakeSprite("Glanz", GlowSprite(), sortingOrder - 1);
            glowSr.gameObject.SetActive(Stack.def.rarity != ItemRarity.Common);
            glowSr.color = ItemDef.RarityColor(Stack.def.rarity);
            shadowSr = MakeSprite("Schatten", ShadowSprite(), sortingOrder - 1);

            visual = new GameObject("Bild").transform;
            visual.SetParent(transform, false);
            visual.localScale = Vector3.one * 0.7f;
            sr = visual.gameObject.AddComponent<SpriteRenderer>();
            sr.sprite = Stack.def.icon;
            sr.sortingLayerID = sortingLayerId;
            sr.sortingOrder = sortingOrder;
            if (worldMaterial != null) sr.sharedMaterial = worldMaterial;
        }

        SpriteRenderer MakeSprite(string name, Sprite sprite, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var r = go.AddComponent<SpriteRenderer>();
            r.sprite = sprite;
            r.sortingLayerID = sortingLayerId;
            r.sortingOrder = order;
            if (worldMaterial != null) r.sharedMaterial = worldMaterial;
            return r;
        }

        static Sprite ShadowSprite()
        {
            if (shadowSprite != null) return shadowSprite;
            shadowSprite = Ellipse(14, 6, new Color32(0x1a, 0x15, 0x26, 140), 1f);
            return shadowSprite;
        }

        static Sprite GlowSprite()
        {
            if (glowSprite != null) return glowSprite;
            glowSprite = Ellipse(22, 10, new Color32(255, 255, 255, 255), 0.5f);
            return glowSprite;
        }

        /// <summary>Gefuellte Ellipse; inner = ab diesem Anteil des Radius wird der Rand weicher (1 = hart).</summary>
        static Sprite Ellipse(int w, int h, Color32 color, float inner)
        {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    float dx = (x - (w - 1) / 2f) / (w / 2f), dy = (y - (h - 1) / 2f) / (h / 2f);
                    float r = Mathf.Sqrt(dx * dx + dy * dy);
                    float a = r > 1f ? 0f : inner >= 1f || r < inner ? 1f : 1f - (r - inner) / (1f - inner);
                    var c = color;
                    c.a = (byte)(color.a * a);
                    tex.SetPixel(x, y, c);
                }
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 32f);
        }

        // ------------------------------------------------------------------ Bewegung, Anzeige, Magnet
        void Update()
        {
            if (Stack == null || visual == null || collecting) return;
            if (Stack.count <= 0) { Destroy(gameObject); return; }

            if (velocity.sqrMagnitude > 0.01f) Throw();

            // Schweben (Bild hebt sich ueber den Schatten), Seltenes glimmt
            float bob = 0.28f + Mathf.Sin(Time.time * 2.2f + bobSeed) * 0.04f;
            visual.localPosition = new Vector3(0f, bob, 0f);
            if (glowSr.gameObject.activeSelf)
            {
                var c = glowSr.color;
                c.a = 0.2f + 0.12f * Mathf.Sin(Time.time * 2.6f + bobSeed);
                glowSr.color = c;
            }

            if (!IsAuto || Time.time < noPickupUntil) return;
            var inv = PlayerInventory.Instance;
            if (inv == null) return;
            Vector2 to = (Vector2)inv.transform.position + Vector2.up * 0.3f - (Vector2)transform.position;
            float dist = to.magnitude;
            if (dist > inv.MagnetRadius || !inv.Main.CanFit(Stack.def, 1)) return;

            // Zum Spieler hin ziehen, je naeher desto schneller
            transform.position += (Vector3)(to.normalized * Mathf.Lerp(1.2f, 7f, 1f - dist / inv.MagnetRadius) * Time.deltaTime);
            if (dist <= inv.PickupRadius) Collect(inv);
        }

        /// <summary>Wurfschwung mit Wand-Abbruch: der Gegenstand rutscht nicht durch feste Hindernisse.</summary>
        void Throw()
        {
            Vector2 step = velocity * Time.deltaTime;
            float len = step.magnitude;
            if (len > 0.0001f && FirstSolidHit(transform.position, step / len, len + 0.12f, out var hit))
            {
                transform.position = (Vector2)transform.position + step / len * Mathf.Max(0f, hit.distance - 0.12f);
                velocity = Vector2.zero;
                return;
            }
            transform.position += (Vector3)step;
            velocity = Vector2.MoveTowards(velocity, Vector2.zero, 6f * Time.deltaTime);
        }

        /// <summary>Erster fester Treffer auf der Strecke. Ausloeser, Spieler und Figuren (bewegliche Koerper) zaehlen nicht.</summary>
        static bool FirstSolidHit(Vector2 origin, Vector2 dir, float distance, out RaycastHit2D hit)
        {
            var filter = new ContactFilter2D { useTriggers = false };
            int n = Physics2D.Raycast(origin, dir, filter, hits, distance);
            for (int i = 0; i < n; i++)
            {
                var rb = hits[i].collider.attachedRigidbody;
                if (rb != null && rb.bodyType != RigidbodyType2D.Static) continue;
                hit = hits[i];
                return true;
            }
            hit = default;
            return false;
        }

        // ------------------------------------------------------------------ Aufheben
        public override bool CanInteract(PlayerInteractor who) =>
            base.CanInteract(who) && !collecting && !IsAuto && Stack != null && Time.time >= noPickupUntil;

        public override bool ShowsIndicator(PlayerInteractor who) => false;
        public override bool ShowsPromptBox => true;

        public override Vector3 IndicatorPosition => transform.position + Vector3.up * 0.75f;

        public override string PromptLabel
        {
            get
            {
                if (Stack == null || Stack.def == null) return Prompt;
                return Stack.count > 1 ? $"{Prompt} {Stack.def.displayName} x{Stack.count}" : $"{Prompt} {Stack.def.displayName}";
            }
        }

        public override Color PromptTint => Stack != null && Stack.def != null ? ItemDef.RarityColor(Stack.def.rarity) : Color.clear;

        public override void Interact(PlayerInteractor who)
        {
            var inv = who != null ? who.GetComponent<PlayerInventory>() : PlayerInventory.Instance;
            if (inv == null || Stack == null) return;
            if (!inv.Main.CanFit(Stack.def, 1)) { inv.Say("Backpack is full."); return; }
            Collect(inv);
        }

        /// <summary>Nimmt auf, so viel passt. Ist alles weg, fliegt das Bild kurz zum Spieler und verschwindet.</summary>
        void Collect(PlayerInventory inv)
        {
            inv.TryPickup(Stack);
            if (Stack.count > 0) { inv.Say("Backpack is full."); return; }
            collecting = true;
            enabled = false;   // nicht mehr im Interactable-Verzeichnis
            StartCoroutine(FlyTo(inv.transform));
        }

        IEnumerator FlyTo(Transform target)
        {
            const float duration = 0.14f;
            Vector3 start = transform.position;
            for (float t = 0f; t < duration; t += Time.deltaTime)
            {
                float k = t / duration;
                if (target != null) transform.position = Vector3.Lerp(start, target.position + Vector3.up * 0.3f, k * k);
                transform.localScale = Vector3.one * (1f - 0.6f * k);
                yield return null;
            }
            Destroy(gameObject);
        }
    }
}
