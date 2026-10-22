using System.Collections;
using System.Collections.Generic;
using Nightward.Core;
using Nightward.DayNight;
using Nightward.Dialogue;
using Nightward.Interaction;
using Nightward.NPC;
using Nightward.Player;
using Nightward.World;
using UnityEngine;

namespace Nightward.Opening
{
    /// <summary>
    /// Ankunft im Dorf (Level_01) nach dem Opening: Das Auto rollt von Sueden an den Dorfeingang, am Friedhof wird gerade jemand beerdigt
    /// (offenes Grab, Sarg, der Tote in weissem Tuch), alle drehen die Koepfe. Bulut kommt zum Autofenster, der Spieler geht mit ihm
    /// die Dorfstrasse hinauf zur Sheriff-Station und betritt sie. Drinnen laeuft die erste Begegnung nach "Sheriff Bulut: Erste Begegnung (Ink)"
    /// bis Bulut den Spieler zur Bar schickt. Danach ist Level_01 normal spielbar (Hud, Tag/Nacht, Kampf kommen zurueck).
    /// Start: Opening setzt ArrivalState.Pending und laedt Level_01; zum Testen "runWithoutOpening" oder das Menue Nightward/Story.
    /// Alle Orte stehen als Zahlen hier oder werden ueber Namen gefunden, damit ein Neubau des Dorfs (DorfBuilder) die Szene nicht zerlegt.
    /// </summary>
    public class ArrivalDirector : MonoBehaviour
    {
        [Header("Systeme")]
        [SerializeField] OpeningUI ui;
        [SerializeField] QuestHud questHud;
        [SerializeField] ScriptedDialogue dialogue;
        [SerializeField] OpeningAudio audioPlayer;
        [Tooltip("Oberste UI der Ankunft (Fade, Erzaehler, Quest-Hud). Wird ausserhalb der Ankunft ausgeschaltet")]
        [SerializeField] GameObject uiRoot;
        [Tooltip("Das normale Level_01-Hud: waehrend der Ankunft aus")]
        [SerializeField] GameObject hudRoot;

        [Header("Spieler")]
        [SerializeField] PlayerInteractor player;
        [SerializeField] Animator playerAnimator;
        [SerializeField] RuntimeAnimatorController womanController;
        [SerializeField] RuntimeAnimatorController manController;

        [Header("Auto")]
        [SerializeField] CarController car;
        [Tooltip("Start im Wald an der Dorfstrasse (Sueden), Fahrtrichtung Norden")]
        [SerializeField] Vector2 carStart = new Vector2(34.5f, -14f);
        [Tooltip("Hier haelt das Auto, auf Hoehe des Friedhofstors")]
        [SerializeField] Vector2 carStop = new Vector2(34.5f, 8.8f);
        [SerializeField] float driveSpeed = 1.7f;
        [Tooltip("Ab dieser Hoehe beginnt die Kamera zum Friedhof zu schwenken und die Erzaehlung")]
        [SerializeField] float cutsceneStartY = -5f;

        [Header("Friedhof")]
        [SerializeField] List<CrowdMember> crowd = new List<CrowdMember>();
        [SerializeField] NpcMover boy;
        [SerializeField] NpcMover mother;
        [Tooltip("Blickpunkt am offenen Grab")]
        [SerializeField] Transform graveFocus;

        [Header("Bulut")]
        [SerializeField] NpcMover bulut;
        [SerializeField] NpcProfile bulutProfile;
        [SerializeField] Vector2 bulutAtGrave = new Vector2(26.8f, 11.8f);
        [Tooltip("Weg zur Station (Dorfstrasse hinauf, dann zur Tuer); der letzte Punkt davor ist die Tuer selbst (Revier_Aussen_Ausgang)")]
        [SerializeField] Vector2[] stationRoute = { new Vector2(33f, 12f), new Vector2(33f, 56.5f), new Vector2(51.5f, 56.5f) };
        [SerializeField] float bulutSpeed = 1.9f;
        [Tooltip("Bulut wartet, wenn der Spieler weiter weg ist")]
        [SerializeField] float waitDistance = 5.5f;

        [Header("Tag-Uhr")]
        [Tooltip("Spaeter Nachmittag, warmes Abendlicht")]
        [SerializeField] DayPhase clockPhase = DayPhase.Tag;
        [SerializeField, Range(0f, 1f)] float clockProgress = 0.75f;

        [Header("Testen")]
        [Tooltip("Ankunft auch ohne Opening starten (Level_01 direkt per Play)")]
        [SerializeField] bool runWithoutOpening;

        bool villageDone;
        bool menuLock;
        int choice;
        Transform cameraPoint;
        Transform roomFocus;

        // Markerorte aus dem Dorfbau (per Name gefunden, Rueckfall: Zahlen passend zum DorfBuilder)
        Vector3 InsideEntry => Marker("Revier_Innen_Eingang", new Vector3(204.5f, 60.7f, 0f));
        Vector3 OutsideDoor => Marker("Revier_Aussen_Ausgang", new Vector3(51.5f, 59.7f, 0f));

        static Vector3 Marker(string markerName, Vector3 fallback)
        {
            var go = GameObject.Find(markerName);
            return go != null ? go.transform.position : fallback;
        }

        void Start()
        {
            bool run = ArrivalState.Pending || runWithoutOpening;
            ArrivalState.Pending = false;
            if (uiRoot != null) uiRoot.SetActive(run);
            if (!run) { enabled = false; return; }
            StartCoroutine(Run());
        }

        void Update()
        {
            if (questHud == null) return;
            questHud.MenusAllowed = !dialogue.IsOpen && !car.HasDriver && playerFree;
            // Menue offen: Spieler sperren, damit F/E nichts ausloesen
            bool onFoot = !car.HasDriver;
            if (questHud.MenuOpen && !menuLock && onFoot) { player.Lock(true); menuLock = true; }
            else if (!questHud.MenuOpen && menuLock) { player.Lock(false); menuLock = false; }
        }

        bool playerFree;

        // ------------------------------------------------------------ Ablauf

        IEnumerator Run()
        {
            var cam = CameraFollow2D.Main;
            SetHud(false);
            SetCombat(false);
            QuestLog.SetMain(null);
            questHud.Show(false);
            questHud.MenusAllowed = false;
            var cycle = DayNightCycle.Instance;
            if (cycle != null) { cycle.SetPhase(clockPhase, clockProgress); cycle.Paused = true; }
            if (PlayerChoice.HasChosen) ApplyProtagonist(PlayerChoice.Current);
            foreach (var c in crowd) if (c != null) c.Watch = car.transform;

            var brain = bulut.GetComponent<NpcBrain>();
            if (brain != null) brain.enabled = false;
            Place(bulut, bulutAtGrave);
            bulut.LookAt(graveFocus != null ? (Vector2)graveFocus.position : bulutAtGrave + Vector2.left);

            car.gameObject.SetActive(true);
            car.Teleport(carStart, 0f);
            car.Enter(player);
            car.EngineOn = true;
            ui.SetFade(1f);
            yield return null;
            yield return null;
            if (cam != null) cam.Snap();
            audioPlayer.StartDriveAmbience(0.5f);
            yield return new WaitForSeconds(0.6f);
            yield return ui.FadeIn();

            // ---------------- Fahrt zum Dorfeingang (Autopilot), dann Cutscene am Friedhof
            car.DriveTo(carStop, driveSpeed);
            while (car.transform.position.y < cutsceneStartY) yield return null;
            villageDone = false;
            StartCoroutine(CutsceneCamera());
            StartCoroutine(GraveNarration());
            while (!villageDone || !car.AutoArrived || Mathf.Abs(car.Speed) > 0.05f) yield return null;
            car.Park();
            ui.HideSubtitle();
            ui.HideBubble();
            yield return new WaitForSeconds(1.0f);
            yield return BulutRunsToCar(3.5f);

            // ---------------- Bulut am Fenster: der Spieler geht mit
            dialogue.Open(bulutProfile);
            var w = ArrivalScript.AtTheWindow;
            for (int i = 0; i < w.Length; i++) yield return dialogue.PlayLine(w[i]);
            dialogue.Close();
            car.EngineOn = false;
            audioPlayer.StopAll(1.2f);
            car.Exit(player, unlock: false);
            if (cam != null) cam.ClearFocus();
            if (cameraPoint != null) Destroy(cameraPoint.gameObject);
            yield return new WaitForSeconds(0.8f);

            // ---------------- Zur Station: Bulut geht voraus, der Spieler folgt
            yield return ui.Narrate(ArrivalScript.WalkToStation[0].text);
            StartCoroutine(LeadToStation());
            yield return ui.Narrate(ArrivalScript.WalkToStation[1].text);
            player.Lock(false);
            playerFree = true;
            QuestLog.SetMain(ArrivalScript.QuestFollow);
            questHud.Show(true);
            StartCoroutine(ui.Narrate(ArrivalScript.WalkToStation[2].text));

            // Der Spieler betritt die Station (Durchgang an der Tuer teleportiert ihn in den Innenraum)
            while (Vector2.Distance(player.transform.position, InsideEntry) > 3f) yield return null;
            while (BildUebergang.Instance != null && BildUebergang.Instance.Laeuft) yield return null;
            playerFree = false;
            player.Lock(true);
            ui.HideSubtitle();
            QuestLog.CompleteMain(null);
            questHud.Show(false);

            // ---------------- Erste Begegnung in der Station
            yield return SheriffScene();

            // ---------------- Danach: Level_01 gehoert dem Spieler
            QuestLog.SetMain(ArrivalScript.QuestBar);
            questHud.Show(true);
            if (cam != null) cam.ClearFocus();
            if (roomFocus != null) Destroy(roomFocus.gameObject);
            SetHud(true);
            SetCombat(true);
            player.Lock(false);
            playerFree = true;
            if (cycle != null) cycle.Paused = false;
            yield return ui.Hint("New Main Quest: " + ArrivalScript.QuestBar, 3.2f);
        }

        void ApplyProtagonist(Protagonist p)
        {
            var ctrl = p == Protagonist.Mann ? manController : womanController;
            if (playerAnimator != null && ctrl != null) playerAnimator.runtimeAnimatorController = ctrl;
        }

        void SetHud(bool on) { if (hudRoot != null) hudRoot.SetActive(on); }

        void SetCombat(bool on)
        {
            var combat = player.GetComponent<PlayerCombat>();
            if (combat != null) combat.enabled = on;
        }

        static void Place(NpcMover npc, Vector2 position)
        {
            npc.Stop();
            npc.transform.position = position;
            var rb = npc.GetComponent<Rigidbody2D>();
            if (rb != null) rb.position = position;
        }

        // ------------------------------------------------------------ Friedhof

        IEnumerator GraveNarration()
        {
            var lines = ArrivalScript.GraveEntry;
            var w = ArrivalScript.Whispers;

            // erzaehlt wird erst, wenn man die Menschen auch sieht (die Kamera schwenkt in CutsceneCamera)
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
                yield return ui.Bubble(mother.transform, ArrivalScript.MotherCall);
            }
            yield return WaitVisible(Speaker(4));
            yield return ui.Bubble(Speaker(4), w[2]);
            yield return ui.Narrate(lines[2].text, thought: true);
            yield return ui.Narrate(lines[3].text, thought: true);
            villageDone = true;
        }

        /// <summary>
        /// Kamera der Cutscene: schwenkt, je naeher das Auto kommt, zur Mitte zwischen Trauergaesten (links) und Auto (rechts).
        /// Am Ende bleibt sie stehen (auch fuer das Gespraech am Fenster).
        /// </summary>
        IEnumerator CutsceneCamera()
        {
            var cam = Camera.main;
            var follow = CameraFollow2D.Main;
            if (cam == null || follow == null) yield break;

            float minY = float.MaxValue, maxY = float.MinValue, sumX = 0f;
            int n = 0;
            void Include(Transform t)
            {
                if (t == null) return;
                minY = Mathf.Min(minY, t.position.y);
                maxY = Mathf.Max(maxY, t.position.y + 1.7f);
                sumX += t.position.x;
                n++;
            }
            foreach (var c in crowd) if (c != null) Include(c.transform);
            if (boy != null) Include(boy.transform);
            if (mother != null) Include(mother.transform);
            float groupX = n > 0 ? sumX / n : graveFocus.position.x;
            // 0,9 hoeher: unten verdeckt die Erzaehlerzeile sonst die vorderen Gaeste
            float centerY = (minY < maxY ? (minY + maxY) * 0.5f : graveFocus.position.y) + 0.9f;
            float halfW = cam.orthographicSize * cam.aspect;
            float targetX = Mathf.Min(carStop.x - 0.3f, Mathf.Max(groupX + 1.5f, carStop.x - halfW * 0.9f));

            cameraPoint = new GameObject("Cutscene_Kamerapunkt").transform;
            float startY = car.transform.position.y;
            cameraPoint.position = player.transform.position;     // dort schaut die Kamera gerade hin: kein Sprung beim Start
            follow.SetFocus(cameraPoint, 1f);
            while (!villageDone || !car.AutoArrived || Mathf.Abs(car.Speed) > 0.05f)
            {
                float progress = Mathf.InverseLerp(startY, carStop.y, car.transform.position.y);
                float k = progress * progress;                  // erst spaet wegschwenken: das Auto bleibt im Bild
                Vector2 start = (Vector2)player.transform.position + follow.Offset;
                Vector2 center = Vector2.Lerp(start, new Vector2(targetX, centerY), k);
                cameraPoint.position = center - follow.Offset;
                yield return null;
            }
            cameraPoint.position = new Vector2(targetX, centerY) - follow.Offset;
        }

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

        IEnumerator BulutRunsToCar(float seconds)
        {
            Vector2 window = car.SidePoint(1.45f, 0.3f);
            float dist = Vector2.Distance(bulut.Position, window);
            var walk = bulut.GetComponent<ScriptedWalker>();
            yield return walk.WalkTo(window, Mathf.Max(0.9f, dist / seconds));
            bulut.LookAt(car.transform.position);
        }

        // ------------------------------------------------------------ Weg zur Station

        IEnumerator LeadToStation()
        {
            var walk = bulut.GetComponent<ScriptedWalker>();
            // Bulut wartet, wenn der Spieler zurueckbleibt
            bool Hold() => Vector2.Distance(player.transform.position, bulut.Position) > waitDistance;
            foreach (var p in stationRoute) yield return walk.WalkTo(p, bulutSpeed, Hold);
            Vector2 door = OutsideDoor;
            yield return walk.WalkTo(door, bulutSpeed, Hold);
            // An der Tuer: wartet, bis der Spieler nah ist, dann geht er voraus hinein
            while (Vector2.Distance(player.transform.position, bulut.Position) > 4.5f) yield return null;
            yield return walk.WalkTo(door + Vector2.up * 1.4f, 1.3f);
            bulut.gameObject.SetActive(false);
        }

        // ------------------------------------------------------------ Station: Scene 1

        IEnumerator SheriffScene()
        {
            var cam = CameraFollow2D.Main;
            Vector3 entry = InsideEntry;
            roomFocus = new GameObject("Raum_Blickpunkt").transform;
            roomFocus.position = entry + new Vector3(0f, 2.2f, 0f);
            if (cam != null) cam.SetFocus(roomFocus, 0.85f);

            // Bulut sitzt hinter seinem Schreibtisch und schaut nicht auf
            bulut.gameObject.SetActive(true);
            Vector2 seat = (Vector2)entry + new Vector2(0f, 3.7f);
            Place(bulut, seat);
            var rb = bulut.GetComponent<Rigidbody2D>();
            if (rb != null) rb.bodyType = RigidbodyType2D.Kinematic;
            bulut.LookAt(seat + Vector2.down);
            player.Controller.FaceTowards(Vector2.up);
            yield return new WaitForSeconds(0.6f);

            dialogue.Open(bulutProfile);
            var intro = ArrivalScript.Arrival;
            for (int i = 0; i < intro.Length - 1; i++) yield return dialogue.PlayLine(intro[i]);
            yield return Ask(intro[intro.Length - 1], ArrivalScript.ChoiceSit, ArrivalScript.ChoiceStayAtDoor, ArrivalScript.ChoiceLookAround);

            // Ablauf wie im Ink: sit_down / stay_at_door / look_around fuehren in bulut_next bzw. wait_and_listen
            const int SitDown = 0, BulutNext = 1, Listen = 2;
            int step;
            if (choice == 0) step = SitDown;
            else if (choice == 1)
            {
                yield return PlayAllButLast(ArrivalScript.StayAtDoor);
                yield return Ask(Last(ArrivalScript.StayAtDoor), ArrivalScript.ChoiceSit, ArrivalScript.ChoiceStayAndListen);
                step = choice == 0 ? SitDown : Listen;
            }
            else
            {
                yield return dialogue.PlayLine(ArrivalScript.LookAround);
                yield return Ask(ArrivalScript.LookAroundBulut, ArrivalScript.ChoiceSit, ArrivalScript.ChoiceAskList);
                if (choice == 0) step = SitDown;
                else
                {
                    yield return dialogue.PlayLine(ArrivalScript.AskAboutList);
                    step = BulutNext;
                }
            }

            if (step == SitDown)
            {
                StartCoroutine(StepToDesk());
                yield return dialogue.Play(ArrivalScript.SitDown);
                step = BulutNext;
            }
            if (step == BulutNext)
            {
                yield return dialogue.Play(ArrivalScript.BulutNext);
                yield return PlayAllButLast(ArrivalScript.BulutAnswers);
                yield return Ask(Last(ArrivalScript.BulutAnswers), ArrivalScript.ChoiceLeave, ArrivalScript.ChoiceStayStill);
                if (choice == 0) yield return dialogue.Play(ArrivalScript.LeaveAttempt);
            }

            yield return dialogue.Play(ArrivalScript.Rules);
            yield return dialogue.Play(ArrivalScript.Reaction);
            dialogue.Close();
            yield return new WaitForSeconds(0.5f);
        }

        IEnumerator PlayAllButLast(Line[] lines)
        {
            for (int i = 0; i < lines.Length - 1; i++) yield return dialogue.PlayLine(lines[i]);
        }

        static Line Last(Line[] lines) => lines[lines.Length - 1];

        /// <summary>Letzte Zeile mit den Antworten darunter; das Ergebnis steht in choice.</summary>
        IEnumerator Ask(Line last, params string[] options)
        {
            yield return dialogue.PlayLine(last, options.Length);
            yield return dialogue.Choose(options);
            choice = dialogue.Chosen;
        }

        /// <summary>Ein Schritt vom Eingang an den Schreibtisch (der Spieler setzt sich "gedanklich" gegenueber).</summary>
        IEnumerator StepToDesk()
        {
            var rb = player.GetComponent<Rigidbody2D>();
            Vector2 from = rb.position, to = from + new Vector2(0f, 0.9f);
            const float seconds = 0.7f;
            for (float t = 0f; t < seconds; t += Time.deltaTime)
            {
                Vector2 p = Vector2.Lerp(from, to, t / seconds);
                rb.position = p;
                player.transform.position = p;
                yield return null;
            }
            player.Controller.FaceTowards(Vector2.up);
        }
    }
}
