using System.Collections.Generic;
using Nightward.Combat;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Player
{
    /// <summary>
    /// Linksklick = Schlag in Richtung Maus. Aufeinanderfolgende Klicks ergeben die Kombo punch1 -> punch2 -> punch3.
    /// </summary>
    [RequireComponent(typeof(PlayerController))]
    public class PlayerCombat : MonoBehaviour
    {
        [SerializeField] int damage = 1;
        [Header("Timing (Sekunden, passend zu den Aseprite-Clips)")]
        [SerializeField] float punchDuration = 0.43f;
        [SerializeField] float hitTime = 0.18f;
        [Tooltip("Zeit nach einem Schlag, in der der naechste Klick die Kombo fortsetzt")]
        [SerializeField] float comboWindow = 0.35f;
        [Tooltip("Ab diesem Anteil des Schlags wird ein weiterer Klick vorgemerkt")]
        [SerializeField, Range(0f, 1f)] float bufferFrom = 0.4f;
        [Header("Trefferzone")]
        [SerializeField] float hitReach = 0.8f;
        [SerializeField] float hitRadius = 0.6f;
        [SerializeField] float hitHeight = 0.7f;
        [SerializeField] LayerMask hitMask = ~0;

        PlayerController controller;
        Camera cam;
        readonly HashSet<IDamageable> alreadyHit = new HashSet<IDamageable>();
        int combo;
        bool attacking, hitDone, queued;
        float attackStart, lastEnd = -10f;
        Vector2 aimDir = Vector2.down;

        void Awake()
        {
            controller = GetComponent<PlayerController>();
            cam = Camera.main;
        }

        void Update()
        {
            var mouse = Mouse.current;
            if (mouse == null) return;
            bool click = mouse.leftButton.wasPressedThisFrame;

            if (!attacking)
            {
                if (click) StartAttack(mouse);
                return;
            }

            float elapsed = Time.time - attackStart;
            if (click && elapsed >= punchDuration * bufferFrom) queued = true;

            if (!hitDone && elapsed >= hitTime)
            {
                hitDone = true;
                DoHit();
            }

            if (elapsed >= punchDuration) FinishAttack(mouse);
        }

        void StartAttack(Mouse mouse)
        {
            bool chained = Time.time - lastEnd <= comboWindow && combo < 3;
            combo = chained ? combo + 1 : 1;

            aimDir = PlayerController.Quantize(AimVector(mouse));
            controller.BeginAttack(combo, aimDir);
            attacking = true;
            hitDone = false;
            queued = false;
            attackStart = Time.time;
            alreadyHit.Clear();
        }

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

        Vector2 HitCenter() => (Vector2)transform.position + Vector2.up * hitHeight + aimDir * hitReach;

        void DoHit()
        {
            foreach (var col in Physics2D.OverlapCircleAll(HitCenter(), hitRadius, hitMask))
            {
                if (col.transform.IsChildOf(transform)) continue;
                var target = col.GetComponentInParent<IDamageable>();
                if (target == null || !alreadyHit.Add(target)) continue;
                target.TakeDamage(damage, aimDir);
            }
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.red;
            Vector2 c = Application.isPlaying ? HitCenter() : (Vector2)transform.position + Vector2.up * hitHeight + Vector2.down * hitReach;
            Gizmos.DrawWireSphere(c, hitRadius);
        }
    }
}
