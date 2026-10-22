using System.Collections;
using System.Collections.Generic;
using Nightward.Core;
using Nightward.DayNight;
using Nightward.Dialogue;
using Nightward.Interaction;
using Nightward.NPC;
using Nightward.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

namespace Nightward.Opening
{
    /// <summary>
    /// Ablauf der Opening Sequence nach Docs/_Sequences/Opening Sequence.pdf (Spec v1), Texte aus Opening.ink:
    /// Step 1 Charakterwahl, 2 schwarzer Intro-Text, 3 Fahrt, 4 Baumstamm, 5 Aussteigen + Tutorial, 6/7 Stamm untersuchen,
    /// 8 Wenden, 9 Dorfeinfahrt (Beerdigung), 10/11 Bulut am Fenster, 12a Sheriff-Station oder 12b Weiterfahren mit Szene 4.
    /// Grundsatz: immer eins nach dem anderen. Hinweise und Erzaehlung werden erst gelesen, dann darf der Spieler handeln;
    /// Erzaehlung und Sprechblasen laufen nie gleichzeitig.
    /// Die Tag-Uhr startet mit der Main Quest "Investigate the log" und laeuft nur, solange der Spieler frei steuern kann.
    /// </summary>
    public class OpeningDirector : MonoBehaviour
    {
        [Header("Systeme")]
        [SerializeField] OpeningUI ui;
        [SerializeField] CharacterSelect characterSelect;
        [SerializeField] QuestHud questHud;
        [SerializeField] InteractPrompt prompt;
        [SerializeField] OpeningAudio audioPlayer;
        [SerializeField] ScriptedDialogue dialogue;

        [Header("Spieler")]
        [SerializeField] PlayerInteractor player;
        [SerializeField] Animator playerAnimator;
        [SerializeField] RuntimeAnimatorController womanController;
        [SerializeField] RuntimeAnimatorController manController;

        [Header("Auto und Strasse")]
        [SerializeField] CarController car;
        [SerializeField] OpeningInteractable carDoor;
        [SerializeField] float roadX = 0.5f;
        [SerializeField] float startY = -6f;
        [Tooltip("Step 4: Triggerzone vor dem Stamm")]
        [SerializeField] float logTriggerY = 54f;
        [SerializeField] float logStopY = 60.6f;

        [Header("Baumstamm")]
        [SerializeField] GameObject logRoot;
        [SerializeField] OpeningInteractable logInteract;
        [Tooltip("Weitere Punkte entlang des Stamms, loesen dasselbe aus")]
        [SerializeField] OpeningInteractable[] logExtra = new OpeningInteractable[0];
        [SerializeField] SpriteRenderer logRenderer;
        [SerializeField] Sprite logWithoutPaper;
        [SerializeField] Ravens ravens;
        [SerializeField, Range(5f, 10f)] float investigateSeconds = 7f;

        [Header("Dorf")]
        [Tooltip("Ab hier rollt das Auto allein weiter, blendet aus und die Ankunft in Level_01 beginnt")]
        [SerializeField] float villageEntryY = -24f;
        [Tooltip("Tempo des Autos bei der Dorfeinfahrt")]
        [SerializeField] float approachSpeed = 1.6f;

        [Header("Tag-Uhr")]
        [Tooltip("Startpunkt der Uhr: spaeter Nachmittag, warmes Abendlicht")]
        [SerializeField] DayPhase clockPhase = DayPhase.Tag;
        [SerializeField, Range(0f, 1f)] float clockProgress = 0.75f;

        [Header("Testen")]
        [Tooltip("Charakterwahl ueberspringen, wenn schon gewaehlt wurde")]
        [SerializeField] bool skipChoiceIfKnown;
        [SerializeField] bool skipIntro;
        [Tooltip("Steps 1-8 ueberspringen und direkt vor der Dorfeinfahrt starten (Zettel gilt als gefunden)")]
        [SerializeField] bool jumpToVillage;

        public const string QuestLogInvestigate = "Investigate the log";
        public const string QuestReturnToCar = "Return to your car";
        // Nicht in der Spec benannt, nur zur Orientierung im HUD:
        public const string QuestDriveToVillage = "Follow the road";
        public const string QuestFollowBulut = "Follow Bulut to the station";

        bool free;          // Spieler steuert frei (zu Fuss oder am Steuer)
        bool clockStarted;
        bool menuLock;
        bool tutorialActive;
        double odometerAtLog;
        bool odometerFrozen;

        void Start()
        {
            QuestLog.SetMain(null);
            var cycle = DayNightCycle.Instance;
            if (cycle != null)
            {
                cycle.SetPhase(clockPhase, clockProgress);
                cycle.Paused = true;
            }
            StartCoroutine(Run());
        }

        void Update()
        {
            var cycle = DayNightCycle.Instance;
            if (cycle != null) cycle.Paused = !(clockStarted && free && !dialogue.IsOpen && !questHud.MenuOpen);
            questHud.MenusAllowed = free && !dialogue.IsOpen;

            // Menue offen: Spieler zu Fuss sperren, damit F/E nichts ausloesen
            bool onFoot = !car.HasDriver;
            if (questHud.MenuOpen && !menuLock && onFoot) { player.Lock(true); menuLock = true; }
            else if (!questHud.MenuOpen && menuLock) { player.Lock(false); menuLock = false; }

            // Tacho, solange jemand am Steuer sitzt
            if (car.HasDriver && car.EngineOn && !dialogue.IsOpen)
            {
                if (odometerFrozen) car.Odometer = odometerAtLog;
                ui.Gauge(true, Mathf.Abs(car.Speed) / car.MaxSpeed, car.OdometerText, odometerFrozen);
            }
            else ui.Gauge(false);
        }

        static bool Pressed(System.Func<Keyboard, bool> f) => Keyboard.current != null && f(Keyboard.current);

        IEnumerator Run()
        {
            car.Teleport(new Vector2(roadX, startY), 0f);
            car.Enter(player);
            ui.SetFade(1f);

            if (jumpToVillage)
            {
                ApplyProtagonist(PlayerChoice.Current);
                odometerAtLog = car.Odometer;
                QuestLog.SetMain(QuestDriveToVillage);
                questHud.Show(true);
                clockStarted = true;
                car.EngineOn = true;
                audioPlayer.StartDriveAmbience(0.5f);
                audioPlayer.RadioDies(0.1f);
                car.Teleport(new Vector2(roadX, villageEntryY + 8f), 180f);
                yield return ui.FadeIn();
                car.GiveControl();
                free = true;
                goto Village;
            }

            // ---------------- Step 1: Charakterwahl
            audioPlayer.IntroMusic(true, 3f);
            if (skipChoiceIfKnown && PlayerChoice.HasChosen) ApplyProtagonist(PlayerChoice.Current);
            else
            {
                var choose = characterSelect.Run(p => { PlayerChoice.Set(p); ApplyProtagonist(p); });
                choose.MoveNext();      // Karten sichtbar machen (eigener dunkler Hintergrund) ...
                ui.SetFade(0f);         // ... dann erst die Blende weg
                yield return choose;
                yield return ui.FadeOut();   // ueber Schwarz, die Spielwelt bleibt verborgen
                characterSelect.Hide();
            }

            // ---------------- Step 2: schwarzer Intro-Text (Enter ueberspringt)
            if (!skipIntro) yield return ui.PlayIntro(OpeningScript.Intro, OpeningScript.Title);
            ui.SetFade(1f);

            // ---------------- Step 3: Fahrt (erst jetzt Motor und Radio)
            audioPlayer.IntroMusic(false, 2.5f);
            car.EngineOn = true;
            audioPlayer.StartDriveAmbience();
            yield return new WaitForSeconds(0.6f);
            yield return ui.FadeTo(0f, 1.2f);
            yield return ui.Hint("W – Drive", 1.6f);
            car.GiveControl();
            free = true;
            StartCoroutine(ui.Hint("A / D – Steer", 2.2f));
            while (car.transform.position.y < logTriggerY) yield return null;

            // ---------------- Step 4: Baumstamm
            free = false;
            car.DriveTo(new Vector2(roadX, logStopY), Mathf.Max(1f, car.Speed));
            audioPlayer.RadioDies();
            while (!car.AutoArrived || Mathf.Abs(car.Speed) > 0.05f) yield return null;
            car.Park();
            odometerAtLog = car.Odometer;
            yield return ui.Narrate(OpeningScript.RoadLogStop.text);
            prompt.Show(car.transform, "F – Get out", new Vector3(0f, 1.2f, 0f));
            yield return null;
            while (!Pressed(k => k.fKey.wasPressedThisFrame)) yield return null;
            prompt.Hide();

            // ---------------- Step 5: Aussteigen und Tutorial (erst lesen, dann handeln)
            car.Exit(player, unlock: false);
            audioPlayer.SetStatic(0.5f);
            yield return new WaitForSeconds(0.6f);
            QuestLog.SetMain(QuestLogInvestigate);
            questHud.Show(true);
            yield return ui.Hint("New Main Quest: " + QuestLogInvestigate, 2.5f);
            player.Lock(false);
            free = true;
            // "F – Interact" und "E – Talk" erst, wenn es wirklich etwas zu benutzen gibt
            tutorialActive = true;
            StartCoroutine(TutorialHints());

            // ---------------- Step 6/7: umsehen, Stamm untersuchen
            var logPoints = new List<OpeningInteractable>(logExtra) { logInteract };
            yield return WaitForUse(logPoints.ToArray());
            yield return Investigate();

            // ---------------- Step 8: Umdrehen
            yield return WaitForUse(carDoor);
            free = false;
            car.Enter(player);
            QuestLog.CompleteMain(QuestDriveToVillage);
            audioPlayer.SetStatic(1f);
            car.TurnTo(180f);
            while (!car.AutoArrived) yield return null;
            car.GiveControl();
            free = true;

            // ---------------- Step 9: Dorfeinfahrt. Am Dorfrand rollt das Auto allein weiter, es wird dunkel, die Ankunft im Dorf (Level_01) uebernimmt.
            Village:
            while (car.transform.position.y > villageEntryY) yield return null;
            free = false;
            car.SpeedLimit = float.MaxValue;
            car.AllowReverse = false;
            car.DriveTo(new Vector2(roadX, villageEntryY - 7f), approachSpeed);
            yield return new WaitForSeconds(1.2f);
            yield return ui.FadeOut();
            audioPlayer.StopAll(0.4f);
            questHud.Show(false);
            ArrivalState.Pending = true;
            SceneManager.LoadScene("Level_01");
        }

        void ApplyProtagonist(Protagonist p)
        {
            var ctrl = p == Protagonist.Mann ? manController : womanController;
            if (playerAnimator != null && ctrl != null) playerAnimator.runtimeAnimatorController = ctrl;
        }

        /// <summary>Zeigt "F – Interact" bzw. "E – Talk" zum ersten Mal, wenn der Spieler wirklich vor etwas steht, das sich benutzen laesst.</summary>
        IEnumerator TutorialHints()
        {
            bool shownF = false, shownE = false;
            while (tutorialActive && !(shownF && shownE))
            {
                var cur = player.Current;
                if (cur != null && !player.Busy && free)
                {
                    if (cur.Key == InteractKey.F && !shownF) { shownF = true; yield return ui.Hint("F – Interact", 2.5f); }
                    else if (cur.Key == InteractKey.E && !shownE) { shownE = true; yield return ui.Hint("E – Talk", 2.5f); }
                }
                yield return null;
            }
        }

        IEnumerator WaitForUse(params OpeningInteractable[] points)
        {
            bool used = false;
            void OnUsed() => used = true;
            foreach (var it in points) { it.Allowed = true; it.Used += OnUsed; }
            while (!used) yield return null;
            foreach (var it in points) { it.Used -= OnUsed; it.Allowed = false; }
        }

        // ------------------------------------------------------------ Step 7

        IEnumerator Investigate()
        {
            free = false;
            tutorialActive = false;
            ui.AbortHint();
            player.Lock(true);
            Vector2 toLog = new Vector2(0f, 1f);
            var action = player.GetComponent<PlayerActionAnimation>();
            if (action != null) action.Play("interact", toLog);
            else player.Controller.FaceTowards(toLog);
            if (ravens != null) ravens.Scare();
            audioPlayer.SetStatic(0f, 0.6f);   // waehrend der Untersuchung bleibt es still
            yield return new WaitForSeconds(0.4f);
            audioPlayer.Rustle(true);
            for (float t = 0f; t < investigateSeconds; t += Time.deltaTime)
            {
                ui.Progress(t / investigateSeconds, "Investigating", player.transform);
                yield return null;
            }
            ui.Progress(-1f, null);
            audioPlayer.Rustle(false);
            if (action != null) action.Stop();
            if (logRenderer != null && logWithoutPaper != null) logRenderer.sprite = logWithoutPaper;
            Relationships.SetFlag("has_list");
            yield return ui.Hint(OpeningScript.LogFound.TrimEnd('.'), 2.2f);
            yield return ui.ShowPaper(OpeningScript.ListEntries);
            QuestLog.CompleteMain(QuestReturnToCar);
            yield return ui.Hint("New Main Quest: " + QuestReturnToCar, 2.2f);
            audioPlayer.SetStatic(0.5f);
            player.Lock(false);
            free = true;
            clockStarted = true;    // das Tutorial ist vorbei: ab jetzt laeuft die Zeit
        }
    }
}
