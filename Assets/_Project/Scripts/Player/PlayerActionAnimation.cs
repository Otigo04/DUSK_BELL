using UnityEngine;

namespace Nightward.Player
{
    /// <summary>
    /// Spielt eine Aktions-Animation der Spielfigur in Blickrichtung, z. B. "interact" (hocken und an etwas tuefteln)
    /// fuer Untersuchen, Reparieren, Durchsuchen. Erwartet Zustaende "&lt;name&gt;_&lt;Richtung&gt;" im Animator (wie walk_/idle_).
    /// Waehrend der Aktion sollte die Eingabe gesperrt sein (PlayerInteractor.Lock); Stop() gibt an PlayerController zurueck.
    /// </summary>
    [RequireComponent(typeof(PlayerController))]
    public class PlayerActionAnimation : MonoBehaviour
    {
        static readonly string[] Dirs = { "E", "NE", "N", "NW", "W", "SW", "S", "SE" };

        [SerializeField] Animator animator;

        PlayerController controller;
        int hash;

        public bool Playing { get; private set; }

        float timedEnd;
        bool timed;
        bool lockedByUs;

        /// <summary>Eine zeitlich begrenzte Aktion (Essen, Trinken) laeuft. Die Bewegung ist dann gesperrt.</summary>
        public bool TimedActive => timed;

        void Awake()
        {
            controller = GetComponent<PlayerController>();
            if (animator == null) animator = GetComponentInChildren<Animator>();
        }

        /// <summary>Startet die Aktion. Gibt false zurueck, wenn der Animator den Zustand nicht kennt.</summary>
        public bool Play(string action, Vector2 towards)
        {
            controller.FaceTowards(towards);
            int dir = PlayerController.DirectionIndex(towards);
            hash = Animator.StringToHash(action + "_" + Dirs[dir]);
            if (animator == null || !animator.HasState(0, hash)) return false;
            animator.speed = 1f;
            animator.Play(hash, 0, 0f);
            Playing = true;
            return true;
        }

        /// <summary>Kennt der Animator die Aktion in dieser Blickrichtung? cardinal = nur rechts, links, oben, unten.</summary>
        public bool HasAction(string action, bool cardinal)
        {
            if (animator == null) return false;
            Vector2 face = cardinal ? PlayerController.Cardinal(controller.FacingVector) : controller.FacingVector;
            return animator.HasState(0, Animator.StringToHash(action + "_" + Dirs[PlayerController.DirectionIndex(face)]));
        }

        /// <summary>Eine Aktion kann jetzt starten: nichts anderes laeuft, kein Kampf/Ausweichen, Eingabe nicht gesperrt.</summary>
        public bool CanStartTimed => !Playing && !timed && !controller.IsAttacking && !controller.IsDodging && !controller.InputLocked;

        /// <summary>
        /// Spielt die Aktion in Blickrichtung fuer length Sekunden und sperrt dabei die Bewegung (Essen, Trinken).
        /// cardinal = die Blickrichtung vorher auf rechts, links, oben oder unten runden (Essen, Trinken, Medizin gibt es nur so).
        /// false, wenn schon eine Aktion laeuft, der Spieler kaempft/ausweicht, gesperrt ist oder der Animator den Zustand nicht kennt.
        /// </summary>
        public bool PlayTimed(string action, float length, bool cardinal = false)
        {
            if (!CanStartTimed) return false;
            Vector2 face = cardinal ? PlayerController.Cardinal(controller.FacingVector) : controller.FacingVector;
            if (!Play(action, face)) return false;
            timed = true;
            timedEnd = Time.time + length;
            controller.InputLocked = true;
            lockedByUs = true;
            return true;
        }

        /// <summary>Bricht eine zeitliche Aktion ab (Wechsel der Hand, Treffer) und gibt die Bewegung frei.</summary>
        public void CancelTimed()
        {
            if (timed) EndTimed();
        }

        void Update()
        {
            if (!timed) return;
            // Kampf/Ausweichen kann es nicht geben (Eingabe gesperrt), aber ein Dialog o. ae. beendet die Aktion nicht vorzeitig
            if (Time.time >= timedEnd) EndTimed();
        }

        void EndTimed()
        {
            timed = false;
            if (lockedByUs) controller.InputLocked = false;
            lockedByUs = false;
            Stop();
        }

        // Der PlayerController setzt nach FaceTowards einmal idle: danach die Aktion wieder herstellen
        void LateUpdate()
        {
            if (Playing && animator.GetCurrentAnimatorStateInfo(0).shortNameHash != hash) animator.Play(hash, 0, 0f);
        }

        public void Stop()
        {
            if (!Playing) return;
            Playing = false;
            controller.FaceTowards(controller.FacingVector); // naechster Update spielt wieder idle
        }
    }
}
