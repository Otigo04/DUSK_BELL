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
        [SerializeField] float villageEntryY = -24f;
        [Tooltip("Ab hier beginnt die Cutscene: die Kamera schwenkt zu den Trauergaesten, das Auto faehrt von selbst")]
        [SerializeField] float squareApproachY = -37f;
        [Tooltip("Tempo zwischen Dorfeingang und Dorfplatz (noch nichts zu sehen, soll nicht ewig dauern)")]
        [SerializeField] float approachSpeed = 1.6f;
        [Tooltip("Hier haelt das Auto in der Cutscene, auf Hoehe der Trauergaeste")]
        [SerializeField] float cutsceneStopY = -47f;
        [Tooltip("Tempo des Autos in der Cutscene")]
        [SerializeField] float cutsceneSpeed = 1f;
        [Tooltip("Tempo beim Wegfahren aus dem Dorf (Szene 4)")]
        [SerializeField] float villageSpeed = 0.75f;
        [SerializeField] List<CrowdMember> crowd = new List<CrowdMember>();
        [SerializeField] NpcMover boy;
        [SerializeField] NpcMover mother;
        [SerializeField] GameObject manAtDoor;
        [Tooltip("Blickpunkt der Kamera am Grab (leer = Mitte der Trauergaeste)")]
        [SerializeField] Transform graveFocus;

        [Header("Bulut")]
        [SerializeField] NpcMover bulut;
        [SerializeField] NpcProfile bulutProfile;
        [SerializeField] Transform stationDoor;
        [SerializeField] Transform lantern;
        [SerializeField] Transform houseLights;

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
        bool hasList;
        bool villageDone;
        bool tutorialActive;
        double odometerAtLog;
        bool odometerFrozen;
        Coroutine villageRoutine;

        void Start()
        {
            QuestLog.SetMain(null);
            var cycle = DayNightCycle.Instance;
            if (cycle != null)
            {
                cycle.SetPhase(clockPhase, clockProgress);
                cycle.Paused = true;
            }
            foreach (var c in crowd) if (c != null) c.Watch = car.transform;
            if (manAtDoor != null) manAtDoor.SetActive(false);
            if (graveFocus == null) graveFocus = MakeGraveFocus();
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

        /// <summary>Blickpunkt der Kamera: Mitte der Trauergaeste.</summary>
        Transform MakeGraveFocus()
        {
            var found = GameObject.Find("Grab_Blickpunkt");
            if (found != null) return found.transform;
            var go = new GameObject("Grab_Blickpunkt");
            Vector3 sum = Vector3.zero;
            int n = 0;
            foreach (var c in crowd) if (c != null) { sum += c.transform.position; n++; }
            go.transform.position = n > 0 ? sum / n : transform.position;
            return go.transform;
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
                hasList = true;
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

            // ---------------- Step 9: Dorfeinfahrt (Beerdigung)
            Village:
            while (car.transform.position.y > villageEntryY) yield return null;
            car.SpeedLimit = approachSpeed;
            car.AllowReverse = false;
            while (car.transform.position.y > squareApproachY) yield return null;

            // ---------------- Step 9/10: Cutscene am Friedhof. Der Spieler steuert nichts mehr, das Auto faehrt von selbst
            // zum Dorfplatz, die Kamera schwenkt zu den Trauergaesten und das Auto bleibt links im Bild.
            free = false;
            villageDone = false;
            car.SpeedLimit = float.MaxValue;
            car.DriveTo(new Vector2(roadX, cutsceneStopY), cutsceneSpeed);
            StartCoroutine(CutsceneCamera());
            villageRoutine = StartCoroutine(VillageEntry());
            while (!villageDone || !car.AutoArrived || Mathf.Abs(car.Speed) > 0.05f) yield return null;
            car.Park();
            ui.HideSubtitle();
            ui.HideBubble();
            yield return new WaitForSeconds(1.0f);
            yield return BulutRunsToCar(3.5f);

            // ---------------- Step 11: Dialog (Szene 3)
            dialogue.Open(bulutProfile);
            var s3 = OpeningScript.Scene3;
            for (int i = 0; i < s3.Length - 1; i++) yield return dialogue.PlayLine(s3[i]);
            yield return dialogue.PlayLine(s3[s3.Length - 1], 2);
            yield return dialogue.Choose(new[] { OpeningScript.ChoiceGo, OpeningScript.ChoiceDrive });
            bool goWithHim = dialogue.Chosen == 0;
            dialogue.ChangeRelationship(goWithHim ? +1 : -1); // rel_bulut_player
            yield return new WaitForSeconds(2.6f);      // die Beziehungsanzeige soll in Ruhe zu sehen sein
            dialogue.Close();
            if (CameraFollow2D.Main != null) CameraFollow2D.Main.ClearFocus();
            yield return new WaitForSeconds(1.2f);

            if (goWithHim) yield return Station();
            else yield return DriveOn();

            questHud.Show(false);
            free = false;
            yield return ui.ShowEnd("To be continued");
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
            hasList = true;
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

        // ------------------------------------------------------------ Step 9

        IEnumerator VillageEntry()
        {
            var lines = OpeningScript.VillageEntry;
            var w = OpeningScript.Whispers;

            // Trigger: erzaehlt wird erst, wenn man die Menschen auch sieht (die Kamera schwenkt in CutsceneCamera)
            yield return WaitVisible(Speaker(0), Speaker(1));
            yield return ui.Narrate(lines[0].text);
            yield return WaitVisible(Speaker(0));
            yield return ui.Bubble(Speaker(0), w[0]);
            yield return WaitVisible(Speaker(2));
            yield return ui.Bubble(Speaker(2), w[1]);

            yield return WaitVisible(Speaker(3), boy != null ? boy.transform : Speaker(3));
            yield return ui.Narrate(lines[1].text);
            StartCoroutine(BoyPulledBack());
            yield return new WaitForSeconds(1.0f);
            if (mother != null)
            {
                yield return WaitVisible(mother.transform);
                yield return ui.Bubble(mother.transform, OpeningScript.MotherCall);
            }
            yield return WaitVisible(Speaker(4));
            yield return ui.Bubble(Speaker(4), w[2]);
            yield return ui.Narrate(lines[2].text, thought: true);
            yield return ui.Narrate(lines[3].text, thought: true);
            villageDone = true;
        }

        /// <summary>
        /// Kamera der Cutscene: schwenkt je weiter das Auto kommt von ihm weg zur Mitte der Trauergaeste. Das Auto bleibt dabei
        /// immer links im Bild, die Menschen rechts. Am Ende bleibt die Kamera stehen (auch fuer den Dialog).
        /// </summary>
        IEnumerator CutsceneCamera()
        {
            var cam = Camera.main;
            var follow = CameraFollow2D.Main;
            if (cam == null || follow == null) yield break;

            // Mitte der Gruppe (Fuesse bis Kopf) und Platz fuer das Auto links
            float minY = float.MaxValue, maxY = float.MinValue;
            void Include(Transform t) { if (t == null) return; minY = Mathf.Min(minY, t.position.y); maxY = Mathf.Max(maxY, t.position.y + 1.7f); }
            foreach (var c in crowd) if (c != null) Include(c.transform);
            if (boy != null) Include(boy.transform);
            if (mother != null) Include(mother.transform);
            // 0,9 hoeher: unten verdeckt die Erzaehlerzeile sonst die vorderen Gaeste
            float centerY = (minY < maxY ? (minY + maxY) * 0.5f : graveFocus.position.y) + 0.9f;
            float halfW = cam.orthographicSize * cam.aspect;
            float targetX = Mathf.Min(graveFocus.position.x, roadX + halfW * 0.7f);

            var point = new GameObject("Cutscene_Kamerapunkt").transform;
            float startY = car.transform.position.y;
            point.position = player.transform.position;     // dort schaut die Kamera gerade hin: kein Sprung beim Start
            follow.SetFocus(point, 1f);
            while (!villageDone || !car.AutoArrived || Mathf.Abs(car.Speed) > 0.05f)
            {
                float progress = Mathf.InverseLerp(startY, cutsceneStopY, car.transform.position.y);
                float k = progress * progress * progress;      // erst spaet wegschwenken: das Auto bleibt im Bild
                Vector2 start = (Vector2)player.transform.position + follow.Offset;
                Vector2 center = Vector2.Lerp(start, new Vector2(targetX, centerY), k);
                point.position = center - follow.Offset;
                yield return null;
            }
            // Endlage halten
            point.position = new Vector2(targetX, centerY) - follow.Offset;
        }

        /// <summary>Wartet, bis alle Figuren gut im Bild sind (Text und Sprechblasen nur, wenn man die Sprecher sieht). Hoechstens 8 s.</summary>
        IEnumerator WaitVisible(params Transform[] targets)
        {
            for (float t = 0f; t < 8f; t += Time.deltaTime)
            {
                bool all = true;
                foreach (var target in targets) if (!InView(target)) { all = false; break; }
                if (all) yield break;
                yield return null;
            }
        }

        bool InView(Transform t)
        {
            var cam = Camera.main;
            if (cam == null || t == null) return true;
            Vector3 v = cam.WorldToViewportPoint(t.position + Vector3.up * 0.5f);
            return v.x > 0.04f && v.x < 0.96f && v.y > 0.06f && v.y < 0.94f;
        }

        Transform Speaker(int i) => crowd.Count > 0 ? crowd[Mathf.Clamp(i, 0, crowd.Count - 1)].transform : transform;

        IEnumerator BoyPulledBack()
        {
            if (boy == null || mother == null) yield break;
            var boyWalk = boy.GetComponent<ScriptedWalker>();
            var motherWalk = mother.GetComponent<ScriptedWalker>();
            Vector2 home = boy.Position, motherHome = mother.Position;
            Vector2 toCar = ((Vector2)car.transform.position - home).normalized;
            yield return boyWalk.WalkTo(home + toCar * 1.1f, 1.1f);
            boy.LookAt(car.transform.position);
            yield return new WaitForSeconds(0.5f);
            yield return motherWalk.WalkTo(home + toCar * 0.6f, 1.2f);
            StartCoroutine(motherWalk.WalkTo(motherHome, 0.8f));
            yield return boyWalk.WalkTo(home, 0.9f);
            boy.LookAt(car.transform.position);
        }

        // ------------------------------------------------------------ Step 10

        IEnumerator BulutRunsToCar(float seconds)
        {
            Vector2 window = car.SidePoint(1.45f, 0.3f);
            float dist = Vector2.Distance(bulut.Position, window);
            var walk = bulut.GetComponent<ScriptedWalker>();
            yield return walk.WalkTo(window, Mathf.Max(0.9f, dist / seconds));
            bulut.LookAt(car.transform.position);
        }

        // ------------------------------------------------------------ Step 12a: Mitkommen

        IEnumerator Station()
        {
            QuestLog.CompleteMain(QuestFollowBulut);
            var walk = bulut.GetComponent<ScriptedWalker>();

            // Aussteigen: Bulut tritt einen Schritt zurueck, damit die Figur nicht in ihm steht. Erst die Erzaehlung, dann geht er los.
            StartCoroutine(walk.WalkTo(bulut.Position + car.Left * 0.9f + car.Forward * 0.3f, 0.7f));
            car.Exit(player, unlock: false);
            yield return ui.Narrate(OpeningScript.RevierWalk[0].text);
            yield return new WaitForSeconds(0.6f);

            // Bulut geht zur Station, waehrend die Erzaehlung das sagt. Die Kamera bleibt bei ihm, damit man sieht, wohin er geht.
            var follow = CameraFollow2D.Main;
            if (follow != null) follow.SetFocus(bulut.transform, 0.85f);
            StartCoroutine(walk.WalkTo(stationDoor.position, 1.0f));
            yield return ui.Narrate(OpeningScript.RevierWalk[1].text);
            while (walk.Walking) yield return null;     // erst wenn er an der Tuer steht, geht es weiter
            yield return new WaitForSeconds(0.8f);
            if (follow != null) follow.ClearFocus();
            yield return new WaitForSeconds(0.8f);      // Kamera kommt zum Spieler zurueck

            player.Lock(false);
            free = true;
            StartCoroutine(ui.Narrate(OpeningScript.RevierWalk[2].text));

            // Bulut wartet an der Tuer, bis der Spieler nachkommt
            while (!(!walk.Walking && Vector2.Distance(player.transform.position, stationDoor.position) < 1.8f))
            {
                if (!walk.Walking) bulut.LookAt(player.transform.position);
                yield return null;
            }
            free = false;
            player.Lock(true);
            ui.HideSubtitle();
            yield return ui.FadeOut();
            ui.Backdrop(true);
            QuestLog.CompleteMain(null);
            yield return ui.FadeIn();

            dialogue.Open(bulutProfile);
            var inside = OpeningScript.RevierInside;
            for (int i = 0; i < inside.Length - 1; i++) yield return dialogue.PlayLine(inside[i]);
            var options = new List<string>();
            if (hasList) options.Add(OpeningScript.ChoiceShowList);
            options.Add(OpeningScript.ChoiceAskMonsters);
            yield return dialogue.PlayLine(inside[inside.Length - 1], options.Count);
            yield return dialogue.Choose(options);
            bool showList = options[dialogue.Chosen] == OpeningScript.ChoiceShowList;

            int rel = Relationships.Get(bulutProfile.id); // rel_bulut_player
            if (showList)
            {
                yield return dialogue.PlayLine(OpeningScript.ShowListIntro);
                yield return dialogue.Play(rel >= 5 ? OpeningScript.ShowListTrusted : OpeningScript.ShowListDistrust);
            }
            else
            {
                yield return dialogue.PlayLine(OpeningScript.AskMonstersIntro);
                yield return dialogue.Play(rel >= 5 ? OpeningScript.AskMonstersTrusted
                    : rel <= -5 ? OpeningScript.AskMonstersHostile : OpeningScript.AskMonstersNeutral);
            }
            yield return dialogue.Play(OpeningScript.RevierEnd);
            dialogue.Close();
            yield return ui.FadeOut();
        }

        // ------------------------------------------------------------ Step 12b: Weiterfahren (Cutscene)

        IEnumerator DriveOn()
        {
            QuestLog.CompleteMain(null);
            free = false;
            var walk = bulut.GetComponent<ScriptedWalker>();
            StartCoroutine(walk.WalkTo(bulut.Position + car.Left * 1.2f, 0.9f));
            car.SpeedLimit = float.MaxValue;
            car.AllowReverse = true;
            car.TurnTo(0f);
            while (!car.AutoArrived) yield return null;
            car.DriveTo(new Vector2(roadX, -8f), 4f);
            yield return new WaitForSeconds(3.5f);
            yield return ui.FadeOut();

            // Der Stamm ist weg, die Strasse fuehrt geradeaus. Der Kilometerzaehler zeigt dieselbe Zahl wie vorher
            if (logRoot != null) logRoot.SetActive(false);
            car.Teleport(new Vector2(roadX, logStopY - 12f), 0f);
            odometerFrozen = true;
            car.DriveTo(new Vector2(roadX, logStopY + 14f), 3f);
            yield return ui.FadeIn();
            yield return ui.Narrate(OpeningScript.CutsceneLoop.text);
            yield return ui.FadeOut();
            odometerFrozen = false;

            // Szene 4: Abenddaemmerung, das Dorf liegt wieder vor dem Auto
            var cycle = DayNightCycle.Instance;
            if (cycle != null) cycle.SetPhase(DayPhase.Daemmerung, 0.35f);
            foreach (var c in crowd) if (c != null) c.gameObject.SetActive(false);
            if (boy != null) boy.gameObject.SetActive(false);
            if (mother != null) mother.gameObject.SetActive(false);
            if (manAtDoor != null) manAtDoor.SetActive(true);
            bulut.Stop();
            bulut.transform.position = lantern.position + Vector3.down * 0.6f;
            var bb = bulut.GetComponent<Rigidbody2D>();
            if (bb != null) bb.position = bulut.transform.position;
            car.Teleport(new Vector2(roadX, villageEntryY + 6f), 180f);
            car.SpeedLimit = villageSpeed * 1.6f;
            car.DriveTo(new Vector2(roadX, lantern.position.y - 0.5f), villageSpeed * 1.6f);
            yield return ui.FadeIn();
            audioPlayer.Bell(2);
            while (!car.AutoArrived || Mathf.Abs(car.Speed) > 0.05f) yield return null;
            car.Park();
            bulut.LookAt(car.transform.position);
            if (manAtDoor != null && manAtDoor.TryGetComponent<NpcMover>(out var man)) man.LookAt(car.transform.position);

            dialogue.Open(bulutProfile);
            yield return dialogue.Play(OpeningScript.Scene4Intro);
            if (manAtDoor != null) manAtDoor.SetActive(false); // er schliesst die Tuer
            yield return dialogue.Play(OpeningScript.Scene4Bulut);
            dialogue.Close();

            audioPlayer.Bell(1);
            StartCoroutine(ui.Narrate(OpeningScript.Scene4End.text));
            yield return new WaitForSeconds(1.2f);
            if (houseLights != null)
                foreach (var l in houseLights.GetComponentsInChildren<Light2D>())
                {
                    l.enabled = false;
                    yield return new WaitForSeconds(0.35f);
                }
            yield return new WaitForSeconds(2f);
            audioPlayer.StopAll(1.5f);
            yield return ui.FadeOut();
        }
    }
}
