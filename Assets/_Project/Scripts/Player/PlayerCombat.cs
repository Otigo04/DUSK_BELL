using System.Collections.Generic;
using Nightward.Combat;
using Nightward.Items;
using Nightward.UI;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Player
{
    /// <summary>
    /// Linksklick = Angriff in Richtung Maus mit dem Gegenstand in der Hand (Schnellleiste, PlayerInventory):
    /// Faeuste (punch1-3), Messer (knife1-2), Schlagwaffe (bat) oder Pistole/Gewehr (shoot, rifle; brauchen Munition).
    /// Welche Animation, Dauer und Trefferzeit eine Waffe hat, steht im ItemDef (attackAnim ...), sonst gilt die Standard-
    /// Einstellung der Waffenart. Die Figur dreht sich in 8 Richtungen, Schuesse fliegen aber genau zur Maus (frei zielen).
    /// Waffen verlieren pro Treffer Haltbarkeit und brechen. Ohne Inventar kaempft der Spieler mit den Faeusten.
    /// </summary>
    [RequireComponent(typeof(PlayerController))]
    public class PlayerCombat : MonoBehaviour
    {
        [SerializeField] int damage = 1;

        [Header("Zeiten je Angriffsart in Sekunden (passend zu den Clips, 14 fps)")]
        [SerializeField] float punchDuration = 0.43f;
        [SerializeField] float punchHitTime = 0.18f;
        [SerializeField] float knifeDuration = 0.43f;
        [SerializeField] float knifeHitTime = 0.18f;
        [SerializeField] float batDuration = 0.5f;
        [SerializeField] float batHitTime = 0.26f;
        [SerializeField] float shootDuration = 0.5f;
        [SerializeField] float shootHitTime = 0.16f;
        [Tooltip("Zeit nach einem Schlag, in der der naechste Klick die Kombo fortsetzt")]
        [SerializeField] float comboWindow = 0.35f;
        [Tooltip("Ab diesem Anteil des Schlags wird ein weiterer Klick vorgemerkt")]
        [SerializeField, Range(0f, 1f)] float bufferFrom = 0.4f;

        [Header("Trefferzone")]
        [SerializeField] float hitReach = 0.8f;
        [SerializeField] float hitRadius = 0.6f;
        [SerializeField] float hitHeight = 0.7f;
        [SerializeField] LayerMask hitMask = ~0;

        [Header("Schuss")]
        [Tooltip("Flug-Frames je Richtung (Reihenfolge S, SW, W, NW, N, NE, E, SE, je 3 Frames), vom Setup gesetzt")]
        [SerializeField] Sprite[] shotFrames = new Sprite[0];
        [SerializeField] Sprite[] shotHitFrames = new Sprite[0];
        [SerializeField] float muzzleForward = 0.55f;

        PlayerController controller;
        Survival.PlayerSurvival survival;
        PlayerInventory inventory;
        Camera cam;
        readonly HashSet<IDamageable> alreadyHit = new HashSet<IDamageable>();
        int combo;
        bool attacking, hitDone, queued;
        float attackStart, lastEnd = -10f;
        Vector2 aimDir = Vector2.down;      // auf 8 Richtungen gerundet (Animation, Nahkampf)
        Vector2 aimExact = Vector2.down;    // genau zur Maus (Schuesse)
        WeaponInfo weapon;
        float duration, hitTime;
        int maxCombo;
        string animBase;

        void Awake()
        {
            controller = GetComponent<PlayerController>();
            survival = GetComponent<Survival.PlayerSurvival>();
            inventory = GetComponent<PlayerInventory>();
            cam = Camera.main;
        }

        void Update()
        {
            var mouse = Mouse.current;
            if (mouse == null) return;
            // Klick auf ein UI-Element (HUD, Quest-Tracker, Dialog ...) schlaegt nicht zu
            bool click = mouse.leftButton.wasPressedThisFrame && !NwPointer.OverUI;

            if (!attacking)
            {
                if (click && !controller.InputLocked && !controller.IsDodging) StartAttack(mouse);
                return;
            }

            float elapsed = Time.time - attackStart;
            if (click && elapsed >= duration * bufferFrom) queued = true;

            if (!hitDone && elapsed >= hitTime)
            {
                hitDone = true;
                if (IsRanged) Shoot(); else DoHit();
            }

            if (elapsed >= duration) FinishAttack(mouse);
        }

        void StartAttack(Mouse mouse)
        {
            weapon = inventory != null ? inventory.CurrentWeapon() : new WeaponInfo { style = WeaponStyle.Fists, damage = damage, staminaCost = 1f };
            if (weapon.style == WeaponStyle.Fists) weapon.damage = damage;

            // Fernwaffe ohne Munition: klick, nichts passiert
            if (inventory != null && !inventory.HasAmmo(weapon, false))
            {
                inventory.Say("Out of ammo.");
                Abort();
                return;
            }
            // Ausdauer und Zustand (erschoepft, verletzt ...) entscheiden, ob der Angriff moeglich ist
            if (survival != null && !survival.TryAttack(weapon.staminaCost))
            {
                Abort();
                return;
            }
            if (inventory != null) inventory.HasAmmo(weapon, true);

            SetupStyle();
            bool chained = Time.time - lastEnd <= comboWindow && combo < maxCombo;
            combo = chained ? combo + 1 : 1;

            Vector2 raw = AimVector(mouse);
            aimExact = raw.sqrMagnitude > 0.0004f ? raw.normalized : controller.FacingVector;
            aimDir = PlayerController.Quantize(aimExact);
            controller.BeginAttack(maxCombo > 1 ? animBase + combo : animBase, aimDir);
            attacking = true;
            hitDone = false;
            queued = false;
            attackStart = Time.time;
            alreadyHit.Clear();
        }

        void Abort()
        {
            attacking = false;
            if (controller.IsAttacking) controller.EndAttack();
        }

        void SetupStyle()
        {
            switch (weapon.style)
            {
                case WeaponStyle.Knife: animBase = "knife"; maxCombo = 2; duration = knifeDuration; hitTime = knifeHitTime; break;
                case WeaponStyle.Bat: animBase = "bat"; maxCombo = 1; duration = batDuration; hitTime = batHitTime; break;
                case WeaponStyle.Pistol: animBase = "shoot"; maxCombo = 1; duration = shootDuration; hitTime = shootHitTime; break;
                case WeaponStyle.Rifle: animBase = "rifle"; maxCombo = 1; duration = shootDuration; hitTime = shootHitTime; break;
                default: animBase = "punch"; maxCombo = 3; duration = punchDuration; hitTime = punchHitTime; break;
            }
            // Die Waffe selbst darf Animation, Kombo und Zeiten vorgeben (axt: chop, machete: machete1/2 ...)
            var d = weapon.def;
            if (d == null) return;
            if (!string.IsNullOrEmpty(d.attackAnim)) { animBase = d.attackAnim; maxCombo = Mathf.Max(1, d.attackCombo); }
            if (d.attackSeconds > 0f) duration = d.attackSeconds;
            if (d.hitSeconds > 0f) hitTime = d.hitSeconds;
        }

        bool IsRanged => weapon.style == WeaponStyle.Pistol || weapon.style == WeaponStyle.Rifle;

        void FinishAttack(Mouse mouse)
        {
            attacking = false;
            lastEnd = Time.time;
            if (queued) StartAttack(mouse);
            else controller.EndAttack();
        }

        Vector2 AimVector(Mouse mouse)
        {
            if (cam == null) cam = Camera.main;
            Vector2 screen = mouse.position.ReadValue();
            Vector3 world = cam.ScreenToWorldPoint(new Vector3(screen.x, screen.y, -cam.transform.position.z));
            return (Vector2)world - ((Vector2)transform.position + Vector2.up * hitHeight);
        }

        float Reach() => weapon.reach > 0f ? weapon.reach : weapon.style == WeaponStyle.Bat ? 1.0f : weapon.style == WeaponStyle.Knife ? 0.85f : hitReach;
        float Radius() => weapon.style == WeaponStyle.Bat ? hitRadius * 1.25f : hitRadius;

        Vector2 HitCenter() => (Vector2)transform.position + Vector2.up * hitHeight + aimDir * Reach();

        int Dealt()
        {
            float mult = survival != null ? survival.DamageDealtMultiplier : 1f;
            // Zustaende (hungrig, betrunken ...) schwaechen den Schlag: Bruchteile werden zufaellig auf- oder abgerundet
            return Mathf.FloorToInt(weapon.damage * mult + Random.value);
        }

        void DoHit()
        {
            bool hitSomething = false;
            foreach (var col in Physics2D.OverlapCircleAll(HitCenter(), Radius(), hitMask))
            {
                if (col.transform.IsChildOf(transform)) continue;
                var target = col.GetComponentInParent<IDamageable>();
                if (target == null || !alreadyHit.Add(target)) continue;
                int dealt = Dealt();
                if (dealt <= 0) continue;
                target.TakeDamage(dealt, aimDir);
                hitSomething = true;
            }
            if (hitSomething)
            {
                // Treffer spuerbar machen: ganz kurzer, kaum merklicher Kamerastoss (gemuetlich bleiben)
                if (Core.CameraFollow2D.Main != null) Core.CameraFollow2D.Main.Shake(weapon.style == WeaponStyle.Bat ? 0.04f : 0.02f, 0.1f);
                if (inventory != null) inventory.WearWeapon(weapon);
            }
        }

        void Shoot()
        {
            // Frei zielen: der Schuss fliegt genau zur Maus, die Figur zeigt nur in die naechste der 8 Richtungen
            Vector2 shotDir = aimExact;
            Vector2 origin = (Vector2)transform.position + Vector2.up * hitHeight + shotDir * muzzleForward;
            float range = weapon.range > 0f ? weapon.range : 9f;
            float hitDist = range;

            var hits = Physics2D.RaycastAll(origin, shotDir, range, hitMask);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (var h in hits)
            {
                if (h.collider == null || h.collider.isTrigger || h.collider.transform.IsChildOf(transform)) continue;
                var target = h.collider.GetComponentInParent<IDamageable>();
                if (target != null)
                {
                    int dealt = Dealt();
                    if (dealt > 0) target.TakeDamage(dealt, shotDir);
                    hitDist = h.distance;
                    break;
                }
                // Wand oder Hindernis ohne Schaden-Komponente stoppt den Schuss
                hitDist = h.distance;
                break;
            }

            int dir = PlayerController.DirectionIndex(shotDir);
            // Sprite-Reihenfolge im Sheet: S, SW, W, NW, N, NE, E, SE (Zeilen), Controller-Reihenfolge ist Winkel (E, NE, N ...)
            int row = SheetRow(dir);
            if (shotFrames != null && shotFrames.Length >= (row + 1) * 3)
            {
                var flight = new Sprite[3] { shotFrames[row * 3], shotFrames[row * 3 + 1], shotFrames[row * 3 + 2] };
                Material mat = inventory != null ? inventory.WorldMaterial : null;
                ShotVisual.Spawn(origin, shotDir, hitDist, flight, shotHitFrames, mat);
            }
            if (Core.CameraFollow2D.Main != null) Core.CameraFollow2D.Main.Shake(0.05f, 0.12f);
            if (inventory != null) inventory.WearWeapon(weapon);
        }

        // DirectionIndex: 0 = Ost, gegen den Uhrzeigersinn (E, NE, N, NW, W, SW, S, SE) -> Sheet-Zeile (S, SW, W, NW, N, NE, E, SE)
        static readonly int[] RowOfDir = { 6, 5, 4, 3, 2, 1, 0, 7 };
        static int SheetRow(int dirIndex) => RowOfDir[dirIndex];

        void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.red;
            Vector2 c = Application.isPlaying ? HitCenter() : (Vector2)transform.position + Vector2.up * hitHeight + Vector2.down * hitReach;
            Gizmos.DrawWireSphere(c, hitRadius);
        }
    }
}
