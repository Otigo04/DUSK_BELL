using System;
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
using UnityEngine.Rendering.Universal;

namespace Nightward.Opening
{
    /// <summary>
    /// Die erste Story-Szene in Level_01, komplett als Film (Cutscene: keine Eingabe des Spielers, die Kamera schwenkt mit):
    /// 1. Ankunft: der Pickup rollt von Sueden an den Dorfeingang, am Friedhof wird beerdigt (Pastor David, Mara, Doctor Veronica, Can,
    ///    Sheriff Bulut), alle drehen die Koepfe. Bulut kommt zum Autofenster.
    /// 2. Weg zur Sheriff-Station, erste Begegnung nach "Sheriff Bulut: Erste Begegnung (Ink)" (mit den Entscheidungen im Gespraech).
    /// 3. Weg zur Bar, Ilhan, der Tag geht zu Ende.
    /// 4. Erste Nacht: Klopfen am Fenster. Die Entscheidung am Fenster fuehrt in die Station (Flucht, Zellen) oder durch die Nacht im Flur.
    /// 5. Morgen: Bulut wartet. Danach gehoert Level_01 dem Spieler (HUD, Tag/Nacht, Kampf kommen zurueck).
    /// Alle Orte stehen als Zahlen hier oder werden ueber Namen gefunden, damit ein Neubau des Dorfs (DorfBuilder) die Szene nicht zerlegt.
    /// Start: Opening setzt ArrivalState.Pending und laedt Level_01; zum Testen "runWithoutOpening" oder das Menue Nightward/Story.
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
        [Tooltip("Mitte des offenen Grabs")]
        [SerializeField] Vector2 grave = new Vector2(22f, 12f);
        [SerializeField] Vector2 davidAt = new Vector2(22.4f, 14.1f);
        [SerializeField] Vector2 maraAt = new Vector2(19.4f, 9.8f);
        [SerializeField] Vector2 veronicaAt = new Vector2(23.9f, 8.9f);
        [SerializeField] Vector2 canAt = new Vector2(17.6f, 14.0f);
        [SerializeField] Vector2 bulutAtGrave = new Vector2(26.8f, 11.8f);
        [Tooltip("Durch das Tor im Osten zur Strasse")]
        [SerializeField] Vector2 graveGate = new Vector2(28.6f, 10.9f);

        [Header("Bulut")]
        [SerializeField] NpcProfile bulutProfile;
        [SerializeField] NpcProfile ilhanProfile;
        [Tooltip("Weg zur Station (Dorfstrasse hinauf, dann zur Tuer)")]
        [SerializeField] Vector2[] stationRoute = { new Vector2(33f, 12f), new Vector2(33f, 56.5f), new Vector2(51.5f, 56.5f) };
        [Tooltip("Weg von der Station zur Bar: Strasse, Querstrasse, Platz vor der Bar")]
        [SerializeField] Vector2[] barRoute = { new Vector2(51.5f, 56.5f), new Vector2(34f, 56.5f), new Vector2(34f, 86.7f), new Vector2(56f, 86.7f), new Vector2(56f, 94.2f) };
        [SerializeField] float bulutSpeed = 1.9f;
        [Tooltip("Bulut wartet, wenn der Spieler weiter weg ist")]
        [SerializeField] float waitDistance = 4.5f;

        [Header("Station innen (Raum 200..210 x 60..68)")]
        [SerializeField] Vector2 bulutSeat = new Vector2(204.5f, 65.15f);
        [SerializeField] Vector2 visitorSeat = new Vector2(204.5f, 62.6f);
        [SerializeField] Vector2 ilhanInStation = new Vector2(203.1f, 61.7f);

        [Header("Bar innen (Raum 206..240 x 1..21)")]
        [SerializeField] Vector2 ilhanBehindBar = new Vector2(224f, 17.4f);
        [SerializeField] Vector2[] barInnerRoute = { new Vector2(224.5f, 3.2f), new Vector2(225.0f, 13.6f) };
        [Tooltip("Gang zwischen den Tischen, auf dem der Spieler zur Theke geht")]
        [SerializeField] float barAisleX = 224.0f;
        [SerializeField] Vector2 playerAtBar = new Vector2(222.4f, 13.6f);
        [SerializeField] Vector2 playerBackRoom = new Vector2(234.4f, 14.0f);
        [SerializeField] Vector2 ilhanBackRoom = new Vector2(235.8f, 14.0f);

        [Header("Nacht: Fenster und Flucht")]
        [Tooltip("Das Monster der ersten Nacht (NPC_Gast); wird zur Laufzeit erzeugt und vom Skript gefuehrt")]
        [SerializeField] GameObject monsterPrefab;
        [Tooltip("Fenster in der Nordwand des Hinterzimmers")]
        [SerializeField] Vector2 windowAt = new Vector2(236.5f, 19.1f);
        [Tooltip("Hier muss der Spieler stehen, um mit dem Monster am Fenster zu sprechen")]
        [SerializeField] Vector2 playerAtWindow = new Vector2(236.5f, 17.4f);
        [SerializeField] Vector2 monsterOutside = new Vector2(236.5f, 19.7f);
        [Tooltip("Tempo des Monsters als Vielfaches der Gehgeschwindigkeit: schneller als Gehen, langsamer als Sprinten (Umschalt) - es holt den Spieler ein, wenn er geht oder stehen bleibt")]
        [SerializeField] float monsterSpeedFactor = 1.18f;
        [SerializeField] float catchDistance = 0.6f;
        [Tooltip("Ilhan steht hier in der Tuer zum Hinterzimmer, wenn er aufwacht und ruft")]
        [SerializeField] Vector2 ilhanWakes = new Vector2(231.2f, 13.5f);
        [Tooltip("Ilhan rennt voraus: durch die Bar bis zur Ausgangstuer")]
        [SerializeField] Vector2[] ilhanRunRoute = { new Vector2(228f, 12f), new Vector2(224.5f, 6f), new Vector2(223.5f, 1.2f) };

        [Header("Tag-Uhr")]
        [Tooltip("Spaeter Nachmittag, warmes Abendlicht")]
        [SerializeField] DayPhase clockPhase = DayPhase.Tag;
        [SerializeField, Range(0f, 1f)] float clockProgress = 0.75f;

        [Header("Testen")]
        [Tooltip("Ankunft auch ohne Opening starten (Level_01 direkt per Play)")]
        [SerializeField] bool runWithoutOpening;

        /// <summary>Nur zum Testen: mit Schritt n beginnen (0 Friedhof, 1 Weg zur Station, 2 Station, 3 Weg zur Bar, 4 Bar, 5 Nacht, 6 Morgen).</summary>
        public static int DebugStartStep
        {
            get => PlayerPrefs.GetInt("nw_arrival_debug_step", 0);
            set => PlayerPrefs.SetInt("nw_arrival_debug_step", value);
        }

        /// <summary>Figur, die der Film uebernimmt: Verhalten aus, Heimatort merken, laeuft per ScriptedWalker.</summary>
        class Actor
        {
            public GameObject go;
            public NpcMover mover;
            public NpcBrain brain;
            public ScriptedWalker walker;
            public Vector2 home;
            public CrowdMember crowd;
            /// <summary>true = beim Freigeben nicht nach Hause setzen (die Figur bleibt, wo sie steht)</summary>
            public bool keepPlace;
            /// <summary>"E zum Reden" ist im Film aus (sonst koennte der Spieler Figuren mitten in der Szene ansprechen)</summary>
            public Interactable[] talks;
        }

        readonly List<Actor> actors = new List<Actor>();
        readonly List<(Light2D light, float intensity)> barLights = new List<(Light2D, float)>();
        Actor bulut, mara, veronica, david, can, ilhan, monster;
        Rigidbody2D playerBody;
        Collider2D[] playerColliders;
        Transform graveFocus;
        Transform cameraPoint;
        int choice;
        bool villageDone;

        // Markerorte aus dem Dorfbau (per Name gefunden, Rueckfall: Zahlen passend zum DorfBuilder)
        Vector3 InsideEntry => Marker("Revier_Innen_Eingang", new Vector3(204.5f, 60.7f, 0f));
        Vector3 OutsideDoor => Marker("Revier_Aussen_Ausgang", new Vector3(51.5f, 59.7f, 0f));

        static Vector3 Marker(string markerName, Vector3 fallback)
        {
            var go = GameObject.Find(markerName);
            return go != null ? go.transform.position : fallback;
        }

        /// <summary>Marker innerhalb der Bar (Spawn_Innen / Spawn_Aussen), sonst Rueckfall.</summary>
        static Vector3 BarMarker(string path, Vector3 fallback)
        {
            var bar = GameObject.Find("Ilhans_Bar");
            var t = bar != null ? bar.transform.Find(path) : null;
            return t != null ? t.position : fallback;
        }

        void Start()
        {
            bool run = ArrivalState.Pending || runWithoutOpening;
            ArrivalState.Pending = false;
            if (uiRoot != null) uiRoot.SetActive(run);
            if (!run)
            {
                if (car != null) car.gameObject.SetActive(false);
                enabled = false;
                return;
            }
            StartCoroutine(Run());
        }

        void Update()
        {
            if (questHud == null) return;
            // Waehrend des Films gibt es keine Menues (Quest-Uebersicht, Pause)
            questHud.MenusAllowed = !Cutscene.Active && !dialogue.IsOpen;
        }

        void OnDestroy()
        {
            // Szenenwechsel mitten im Film: nichts gesperrt zuruecklassen
            Cutscene.Reset();
        }

        // ------------------------------------------------------------ Ablauf

        IEnumerator Run()
        {
            Cutscene.Begin();
            try
            {
                BeginFilm();
                int from = DebugStartStep;
                DebugStartStep = 0;     // gilt nur fuer diesen einen Start, sonst beginnt ein normaler Durchlauf spaeter mitten im Ablauf
                if (from > 0) PrepareDebugStart(from);
                if (from <= 0) yield return ArrivalAtGraveyard();
                if (from <= 1) yield return WalkToStation();
                if (from <= 2) yield return StationScene();
                if (from <= 3) yield return WalkToBar();
                if (from <= 4) yield return BarByDay();
                bool windowOpened = false;
                if (from <= 5) yield return FirstNight(result => windowOpened = result);
                yield return Morning(windowOpened);
            }
            finally
            {
                EndFilm();
            }
            // Danach: Level_01 gehoert dem Spieler
            QuestLog.SetMain(ArrivalScript.QuestVillagers);
            questHud.Show(true);
            yield return ui.Hint("New Main Quest: " + ArrivalScript.QuestVillagers, 3.2f);
        }

        /// <summary>Teststart mitten im Ablauf: Figuren dorthin, wo der vorige Schritt sie hinterlassen haette.</summary>
        void PrepareDebugStart(int step)
        {
            var cam = CameraFollow2D.Main;
            Vector2 door = OutsideDoor;
            if (step == 1)
            {
                // Direkt nach dem Gespraech am Autofenster
                SetPlayerAt(carStop + new Vector2(-1.05f, -0.04f));
                Place(bulut, carStop + new Vector2(-1.5f, 0.2f));
                bulut.mover.LookAt(player.transform.position);
            }
            else if (step <= 3)
            {
                SetPlayerAt(door + new Vector2(0f, -0.5f));
                Place(bulut, door + new Vector2(0.9f, -0.3f));
            }
            else
            {
                Vector2 bar = new Vector2(56f, 94.2f);
                SetPlayerAt(bar + new Vector2(-0.4f, -0.4f));
                Place(bulut, bar);
            }
            if (cam != null) cam.Snap();
        }

        void BeginFilm()
        {
            ui.SetFade(0f);       // die UI startet mit schwarzem Bild; wer mitten im Ablauf beginnt, braucht es klar
            playerBody = player.GetComponent<Rigidbody2D>();
            playerColliders = player.GetComponentsInChildren<Collider2D>();
            if (PlayerChoice.HasChosen) ApplyProtagonist(PlayerChoice.Current);

            // Hud, Kampf und Eingabe aus; der Spieler ist nur noch Darsteller (ohne Kollision, damit er nirgends haengen bleibt)
            if (hudRoot != null) hudRoot.SetActive(false);
            var combat = player.GetComponent<PlayerCombat>();
            if (combat != null) combat.enabled = false;
            player.Lock(true);
            foreach (var c in playerColliders) c.enabled = false;
            QuestLog.SetMain(null);
            questHud.Show(false);
            questHud.MenusAllowed = false;

            var cycle = DayNightCycle.Instance;
            if (cycle != null) { cycle.SetPhase(clockPhase, clockProgress); cycle.Paused = true; }

            graveFocus = new GameObject("Grab_Blickpunkt").transform;
            graveFocus.position = grave;

            // Die Besetzung: echte Dorfbewohner (keine Platzhalter)
            bulut = Take("NPC_Bulut_Sheriff");
            mara = Take("NPC_Mara_Baker");
            veronica = Take("NPC_Veronica_Doctor");
            david = Take("NPC_David_Pastor");
            can = Take("NPC_Can");
            ilhan = Take("NPC_Ilhan_Bartender");
            CollectBarLights();
        }

        void EndFilm()
        {
            StopPlayerWalk();
            foreach (var c in playerColliders) if (c != null) c.enabled = true;
            if (car != null && car.HasDriver) car.Exit(player, unlock: false);
            var cam = CameraFollow2D.Main;
            if (cam != null) cam.ClearFocus();
            if (cameraPoint != null) Destroy(cameraPoint.gameObject);
            if (graveFocus != null) Destroy(graveFocus.gameObject);
            ui.Backdrop(false);
            ui.SetFade(0f);
            ui.HideSubtitle();
            ui.HideBubble();
            if (dialogue.IsOpen) dialogue.Close();
            SetBarLights(1f);
            foreach (var a in actors) Release(a);
            actors.Clear();
            if (hudRoot != null) hudRoot.SetActive(true);
            var combat = player.GetComponent<PlayerCombat>();
            if (combat != null) combat.enabled = true;
            var cycle = DayNightCycle.Instance;
            if (cycle != null) cycle.Paused = false;
            player.Lock(false);
            Cutscene.End();
        }

        void ApplyProtagonist(Protagonist p)
        {
            var ctrl = p == Protagonist.Mann ? manController : womanController;
            if (playerAnimator != null && ctrl != null) playerAnimator.runtimeAnimatorController = ctrl;
        }

        // ------------------------------------------------------------ Figuren

        Actor Take(string objectName)
        {
            var go = GameObject.Find(objectName);
            if (go == null) { Debug.LogWarning("[Ankunft] Figur fehlt in der Szene: " + objectName); return null; }
            var mover = go.GetComponent<NpcMover>();
            if (mover == null) return null;
            var a = new Actor
            {
                go = go,
                mover = mover,
                brain = go.GetComponent<NpcBrain>(),
                home = go.transform.position,
            };
            a.walker = go.GetComponent<ScriptedWalker>();
            if (a.walker == null) a.walker = go.AddComponent<ScriptedWalker>();
            if (a.brain != null) a.brain.enabled = false;
            a.talks = go.GetComponentsInChildren<Interactable>(true);
            foreach (var t in a.talks) t.enabled = false;
            mover.Stop();
            // Im Film wird die Figur direkt gesetzt (ScriptedWalker): kein Physik-Anstossen an Moebeln und Tueren
            var rb = go.GetComponent<Rigidbody2D>();
            if (rb != null) { rb.linearVelocity = Vector2.zero; rb.bodyType = RigidbodyType2D.Kinematic; }
            actors.Add(a);
            return a;
        }

        /// <summary>Die Figur geht wieder in ihren Alltag: an den Heimatort, Verhalten an.</summary>
        void Release(Actor a)
        {
            if (a == null || a.go == null) return;
            a.go.SetActive(true);
            if (a.crowd != null) { Destroy(a.crowd); a.crowd = null; }
            if (a.talks != null) foreach (var t in a.talks) if (t != null) t.enabled = true;
            if (!a.keepPlace) Place(a, a.home);
            var rb = a.go.GetComponent<Rigidbody2D>();
            if (rb != null) rb.bodyType = RigidbodyType2D.Dynamic;
            if (a.brain != null) a.brain.enabled = true;
        }

        static void Place(Actor a, Vector2 position)
        {
            if (a == null) return;
            a.mover.Stop();
            a.go.transform.position = position;
            var rb = a.go.GetComponent<Rigidbody2D>();
            if (rb != null) rb.position = position;
        }

        void Mourner(Actor a, Vector2 at)
        {
            if (a == null) return;
            Place(a, at);
            a.crowd = a.go.GetComponent<CrowdMember>();
            if (a.crowd == null) a.crowd = a.go.AddComponent<CrowdMember>();
            a.crowd.SetRest(graveFocus);
            a.crowd.Watch = car.transform;
            a.mover.LookAt(grave);
        }

        static IEnumerator Flag(IEnumerator inner, Action done)
        {
            yield return inner;
            done();
        }

        IEnumerator WalkRoute(Actor a, IList<Vector2> route, float speed, Func<bool> hold = null)
        {
            for (int i = 0; i < route.Count; i++) yield return a.walker.WalkTo(route[i], speed, hold, stand: i == route.Count - 1);
        }

        // ------------------------------------------------------------ Spieler als Darsteller

        void SetPlayerAt(Vector2 p)
        {
            player.transform.position = p;
            if (playerBody != null) { playerBody.position = p; playerBody.linearVelocity = Vector2.zero; }
            Physics2D.SyncTransforms();
        }

        void StopPlayerWalk()
        {
            if (player == null) return;
            var pc = player.Controller;
            pc.ScriptedInput = Vector2.zero;
            pc.ScriptedSpeed = 0f;
        }

        /// <summary>Der Spieler geht (ohne Kollision) zu einem Punkt. Steckt er fest oder dauert es zu lange, wird er hingesetzt.</summary>
        IEnumerator PlayerWalkTo(Vector2 target, float speed, float timeout = 14f)
        {
            var pc = player.Controller;
            for (float t = 0f; t < timeout; t += Time.deltaTime)
            {
                Vector2 to = target - playerBody.position;
                if (to.magnitude < 0.12f) break;
                pc.ScriptedSpeed = speed;
                pc.ScriptedInput = to.normalized;
                yield return null;
            }
            StopPlayerWalk();
            SetPlayerAt(target);
        }

        /// <summary>Der Spieler folgt der Figur im Abstand; Tempo passt sich an (hinterher = schneller, nah dran = langsamer).</summary>
        void FollowStep(Actor lead, ref Vector2 prev, ref Vector2 dir, float behind, float leadSpeed)
        {
            var pc = player.Controller;
            Vector2 p = lead.mover.Position;
            if ((p - prev).sqrMagnitude > 1e-6f) dir = (p - prev).normalized;
            prev = p;
            Vector2 target = p - dir * behind;
            Vector2 to = target - playerBody.position;
            float d = to.magnitude;
            if (d < 0.12f)
            {
                pc.ScriptedInput = Vector2.zero;
                pc.ScriptedSpeed = 0f;
                pc.FaceTowards(dir);
                return;
            }
            pc.ScriptedSpeed = Mathf.Clamp(leadSpeed * (0.55f + d * 0.9f), 0.5f, leadSpeed * 1.7f);
            pc.ScriptedInput = to.normalized;
        }

        /// <summary>Die Figur geht die Route entlang, der Spieler folgt. Endet, wenn die Figur angekommen ist.</summary>
        IEnumerator Escort(Actor lead, IList<Vector2> route, float speed, float behind = 1.2f)
        {
            bool done = false;
            Func<bool> hold = () => Vector2.Distance(playerBody.position, lead.mover.Position) > waitDistance;
            StartCoroutine(Flag(WalkRoute(lead, route, speed, hold), () => done = true));
            Vector2 prev = lead.mover.Position, dir = Vector2.up;
            while (!done)
            {
                FollowStep(lead, ref prev, ref dir, behind, speed);
                yield return null;
            }
            // Spieler schliesst noch auf
            for (float t = 0f; t < 1.5f; t += Time.deltaTime)
            {
                FollowStep(lead, ref prev, ref dir, behind, speed);
                if (Vector2.Distance(playerBody.position, lead.mover.Position - dir * behind) < 0.15f) break;
                yield return null;
            }
            StopPlayerWalk();
        }

        // ------------------------------------------------------------ Kamera und Uebergaenge

        Vector2 CamPoint(Vector2 center) => center - CameraFollow2D.Main.Offset;

        /// <summary>Weicher Wechsel der Blende: Bild zu, mitte() ausfuehren (Teleport), Bild auf.</summary>
        IEnumerator DoorTransition(Action middle)
        {
            var tr = BildUebergang.Instance;
            if (tr == null)
            {
                yield return ui.FadeOut();
                middle();
                yield return null;
                yield return ui.FadeIn();
                yield break;
            }
            bool finished = false;
            tr.Spielen(() =>
            {
                middle();
                var cam = CameraFollow2D.Main;
                if (cam != null) cam.Snap();
            }, () => finished = true);
            while (!finished) yield return null;
        }

        IEnumerator Cut(Action middle, float hold = 0.3f)
        {
            yield return ui.FadeOut();
            middle();
            var cam = CameraFollow2D.Main;
            if (cam != null) cam.Snap();
            yield return new WaitForSeconds(hold);
            yield return ui.FadeIn();
        }

        // ------------------------------------------------------------ 1. Ankunft am Friedhof

        IEnumerator ArrivalAtGraveyard()
        {
            var cam = CameraFollow2D.Main;
            Mourner(david, davidAt);
            Mourner(mara, maraAt);
            Mourner(veronica, veronicaAt);
            Mourner(can, canAt);
            if (bulut != null)
            {
                Place(bulut, bulutAtGrave);
                bulut.mover.LookAt(grave);
            }

            car.gameObject.SetActive(true);
            car.Teleport(carStart, 0f);
            car.Enter(player);
            car.EngineOn = true;
            ui.SetFade(1f);
            yield return null;
            yield return null;
            ClearLootOnArrivalRoad();
            if (cam != null) cam.Snap();
            audioPlayer.StartDriveAmbience(0.5f);
            yield return new WaitForSeconds(0.6f);
            yield return ui.FadeIn();

            // Fahrt zum Dorfeingang (Autopilot), dann die Cutscene am Friedhof
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

            // Bulut kommt durch das Tor zum Autofenster
            if (bulut != null)
            {
                Vector2 window = car.SidePoint(1.45f, 0.3f);
                yield return bulut.walker.WalkTo(graveGate, 1.9f);
                // Die Dialogbox deckt die untere Haelfte: die Kamera rueckt zu Auto und Bulut, so dass beide darueber stehen
                if (cameraPoint != null) StartCoroutine(GlideCamera(new Vector2(carStop.x - 2.4f, carStop.y - 1.4f), 1.6f));
                yield return bulut.walker.WalkTo(window, 2.3f);
                bulut.mover.LookAt(car.transform.position);
            }

            dialogue.Open(bulutProfile);
            var w = ArrivalScript.AtTheWindow;
            for (int i = 0; i < w.Length; i++) yield return dialogue.PlayLine(w[i]);
            dialogue.Close();
            car.EngineOn = false;
            audioPlayer.StopAll(1.2f);
            car.Exit(player, unlock: false);
            foreach (var c in playerColliders) c.enabled = false;      // Exit schaltet sie wieder ein, im Film bleibt der Spieler ohne Kollision
            if (cam != null) cam.ClearFocus();
            if (cameraPoint != null) { Destroy(cameraPoint.gameObject); cameraPoint = null; }
            yield return new WaitForSeconds(0.8f);
        }

        /// <summary>
        /// Der LootSpawner wuerfelt beim Szenenstart Kisten und Gegenstaende, auch auf der Ankunftsstrasse und im Friedhof:
        /// eine Kiste auf der Fahrspur laesst das Auto steckenbleiben. Im Bereich der Startsequenz bleibt die Beute weg.
        /// </summary>
        void ClearLootOnArrivalRoad()
        {
            var area = Rect.MinMaxRect(10f, carStart.y - 1f, 39f, 18f);
            foreach (var s in FindObjectsByType<Nightward.Items.LootSpawner>())
            {
                if (!area.Contains(s.transform.position)) continue;
                if (s.Spawned != null) Destroy(s.Spawned);
                s.enabled = false;
            }
        }

        IEnumerator GraveNarration()
        {
            var lines = ArrivalScript.GraveEntry;
            var w = ArrivalScript.Whispers;
            Transform T(Actor a) => a != null ? a.go.transform : transform;

            // erzaehlt wird erst, wenn man die Menschen auch sieht (die Kamera schwenkt in CutsceneCamera)
            yield return WaitVisible(T(david), T(mara));
            yield return ui.Narrate(lines[0].text);
            yield return WaitVisible(T(mara));
            yield return ui.Bubble(T(mara), w[0]);
            yield return WaitVisible(T(veronica));
            yield return ui.Bubble(T(veronica), w[1]);

            yield return WaitVisible(T(can), T(veronica));
            yield return ui.Narrate(lines[1].text);
            yield return WaitVisible(T(david));
            yield return ui.Bubble(T(david), w[2]);
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
            foreach (var a in new[] { david, mara, veronica, can })
            {
                if (a == null) continue;
                Vector3 p = a.go.transform.position;
                minY = Mathf.Min(minY, p.y);
                maxY = Mathf.Max(maxY, p.y + 1.7f);
                sumX += p.x;
                n++;
            }
            float groupX = n > 0 ? sumX / n : grave.x;
            // Knapp unter der Mitte: die vorderen Gaeste stehen ueber dem Erzaehlerkasten (zwei Zeilen), die Sprechblase des Pastors passt oben noch ins Bild
            float centerY = (n > 0 ? (minY + maxY) * 0.5f : grave.y) - 0.2f;
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

        /// <summary>Der Kamerapunkt der Cutscene gleitet weich zu einer neuen Bildmitte.</summary>
        IEnumerator GlideCamera(Vector2 center, float time)
        {
            var follow = CameraFollow2D.Main;
            if (cameraPoint == null || follow == null) yield break;
            Vector2 from = cameraPoint.position;
            Vector2 to = center - follow.Offset;
            for (float t = 0f; t < time && cameraPoint != null; t += Time.deltaTime)
            {
                cameraPoint.position = Vector2.Lerp(from, to, Mathf.SmoothStep(0f, 1f, t / time));
                yield return null;
            }
            if (cameraPoint != null) cameraPoint.position = to;
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

        static bool InView(Transform t)
        {
            var cam = Camera.main;
            if (cam == null || t == null) return true;
            Vector3 v = cam.WorldToViewportPoint(t.position + Vector3.up * 0.5f);
            return v.x > 0.04f && v.x < 0.96f && v.y > 0.06f && v.y < 0.94f;
        }

        // ------------------------------------------------------------ 2. Weg zur Station

        IEnumerator WalkToStation()
        {
            yield return ui.Narrate(ArrivalScript.WalkToStation[0].text);
            StartCoroutine(ui.Narrate(ArrivalScript.WalkToStation[1].text));
            var route = new List<Vector2>(stationRoute) { OutsideDoor + new Vector3(0f, -1.0f, 0f) };
            yield return FollowBulut(route, bulutSpeed, ArrivalScript.ObjectiveFollowStation);
            StartCoroutine(ui.Narrate(ArrivalScript.WalkToStation[2].text));
            // An der Tuer: Bulut geht voraus hinein
            yield return bulut.walker.WalkTo((Vector2)OutsideDoor + Vector2.up * 1.1f, 1.3f);
            bulut.go.SetActive(false);
            yield return PlayerWalkTo((Vector2)OutsideDoor + Vector2.up * 0.5f, 1.4f);
        }

        // ------------------------------------------------------------ 2b. Station: Scene 1

        IEnumerator StationScene()
        {
            var cam = CameraFollow2D.Main;
            Vector3 entry = InsideEntry;
            var roomFocus = new GameObject("Raum_Blickpunkt").transform;
            roomFocus.position = entry + new Vector3(0f, 1.2f, 0f);   // tiefer als die Raummitte: Bulut am Schreibtisch steht ueber der Dialogbox

            // Die Trauergaeste sind inzwischen heimgegangen (waehrend die Tuer zu ist)
            yield return DoorTransition(() =>
            {
                foreach (var a in new[] { david, mara, veronica, can }) Release(a);
                bulut.go.SetActive(true);
                SeatBulut();
                SetPlayerAt(entry);
                player.Controller.FaceTowards(Vector2.up);
                if (cam != null) cam.SetFocus(roomFocus, 0.85f);
            });
            ui.HideSubtitle();
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
                StartCoroutine(PlayerWalkTo(visitorSeat, 1.3f));
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
            yield return dialogue.Play(ArrivalScript.LeaveStation);
            dialogue.Close();
            yield return new WaitForSeconds(0.3f);

            // Bulut steht auf und geht zur Tuer, der Spieler mit
            Vector2 door = (Vector2)entry + new Vector2(0.5f, 0.1f);
            bool bulutDone = false;
            StartCoroutine(Flag(WalkRoute(bulut, new[] { new Vector2(203.1f, 65.0f), new Vector2(203.1f, 61.9f), door }, 1.6f), () => bulutDone = true));
            yield return PlayerWalkTo((Vector2)entry + new Vector2(-0.4f, 0.1f), 1.5f);
            while (!bulutDone) yield return null;

            // Hinaus: vor der Station
            yield return DoorTransition(() =>
            {
                if (cam != null) cam.ClearFocus();
                Destroy(roomFocus.gameObject);
                Place(bulut, (Vector2)OutsideDoor + new Vector2(0.9f, -0.3f));
                SetPlayerAt(OutsideDoor);
                player.Controller.FaceTowards(Vector2.down);
            });
        }

        void SeatBulut()
        {
            Place(bulut, bulutSeat);
            bulut.mover.LookAt(bulutSeat + Vector2.down);      // schaut nicht auf, sondern auf seine Unterlagen
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

        // ------------------------------------------------------------ 3. Weg zur Bar, Bar am Tag

        IEnumerator WalkToBar()
        {
            StartCoroutine(PlayWalkTalk());
            yield return FollowBulut(barRoute, bulutSpeed, ArrivalScript.ObjectiveFollowBar);
        }

        IEnumerator PlayWalkTalk()
        {
            var l = ArrivalScript.WalkToBar;
            yield return ui.Narrate(l[0].text);
            yield return ui.Bubble(bulut.go.transform, l[1].text);
        }

        void CollectBarLights()
        {
            barLights.Clear();
            var bar = GameObject.Find("Ilhans_Bar");
            var inner = bar != null ? bar.transform.Find("Innen_IlhansBar") : null;
            if (inner == null) return;
            foreach (var l in inner.GetComponentsInChildren<Light2D>(true)) barLights.Add((l, l.intensity));
        }

        void SetBarLights(float factor)
        {
            foreach (var (light, intensity) in barLights) if (light != null) light.intensity = intensity * factor;
        }

        IEnumerator BarByDay()
        {
            var cam = CameraFollow2D.Main;
            Vector2 inside = BarMarker("Innen_IlhansBar/Spawn_Innen", new Vector3(223.5f, 1.6f, 0f));
            // Ilhan steht hinter der Theke (sein Platz in der Bar)
            Place(ilhan, ilhanBehindBar);
            ilhan.mover.LookAt(ilhanBehindBar + Vector2.down);

            yield return DoorTransition(() =>
            {
                Place(bulut, inside + new Vector2(0.4f, 0.3f));
                bulut.go.SetActive(true);
                SetPlayerAt(inside + new Vector2(-0.4f, 0.1f));
                player.Controller.FaceTowards(Vector2.up);
            });
            ui.HideSubtitle();

            // Beide gehen zur Theke
            bool bulutArrived = false;
            StartCoroutine(Flag(WalkRoute(bulut, barInnerRoute, 1.7f), () => bulutArrived = true));
            yield return PlayerWalkTo(inside + new Vector2(0f, 1.0f), 1.5f);
            yield return PlayerWalkTo(new Vector2(barAisleX, barInnerRoute[0].y + 0.3f), 1.6f);
            yield return PlayerWalkTo(new Vector2(barAisleX, playerAtBar.y), 1.6f);
            yield return PlayerWalkTo(playerAtBar, 1.4f);
            while (!bulutArrived) yield return null;
            player.Controller.FaceTowards(Vector2.up);
            bulut.mover.LookAt(ilhanBehindBar);
            yield return new WaitForSeconds(0.3f);

            dialogue.Open(bulutProfile);
            var l = ArrivalScript.BarEntrance;
            for (int i = 0; i < l.Length - 1; i++) yield return dialogue.PlayLine(l[i]);
            // "Bulut leaves without looking back."
            StartCoroutine(BulutLeavesBar(inside));
            yield return dialogue.PlayLine(l[l.Length - 1]);
            yield return dialogue.Play(ArrivalScript.BarTalk);
            // Es wird dunkel: Ilhan bringt den Spieler nach hinten
            yield return dialogue.Play(ArrivalScript.BarBackRoom);
            dialogue.Close();
        }

        IEnumerator BulutLeavesBar(Vector2 inside)
        {
            yield return bulut.walker.WalkTo(barInnerRoute[0], 2.0f);
            yield return bulut.walker.WalkTo(inside + new Vector2(0.2f, 0.4f), 2.0f);
            bulut.go.SetActive(false);
        }

        // ------------------------------------------------------------ 4. Die erste Nacht

        IEnumerator FirstNight(Action<bool> windowOpened)
        {
            var cam = CameraFollow2D.Main;
            var cycle = DayNightCycle.Instance;

            // Dammerung: die Glocke laeutet, Ilhan loescht das Licht
            yield return ui.FadeOut();
            ui.Backdrop(true);
            ui.SetFade(0f);
            if (cycle != null) cycle.SetPhase(DayPhase.Daemmerung, 0.8f);
            audioPlayer.Bell(3);
            SetBarLights(0.25f);
            dialogue.Open(ilhanProfile);
            yield return dialogue.Play(ArrivalScript.FirstNight);
            dialogue.Close();

            // Nacht: Hinterzimmer
            ui.SetFade(1f);
            ui.Backdrop(false);
            if (cycle != null) cycle.SetPhase(DayPhase.Nacht, 0.2f);
            SetBarLights(0.18f);
            SetPlayerAt(playerBackRoom);
            player.Controller.FaceTowards(Vector2.up);
            Place(ilhan, ilhanBehindBar);
            ilhan.mover.LookAt(ilhanBehindBar + Vector2.down);
            monster = SpawnMonster(monsterOutside);
            if (cam != null) cam.Snap();
            yield return new WaitForSeconds(0.8f);
            yield return ui.FadeIn();
            yield return new WaitForSeconds(0.4f);

            // Das Klopfen weckt den Spieler (ohne Portrait: es spricht niemand, Ilhan schlaeft)
            dialogue.Open(null);
            yield return dialogue.Play(ArrivalScript.NightWake);
            dialogue.Close();

            // Ab hier spielt der Spieler selbst: zum Fenster gehen
            BeginPlay();
            StartCoroutine(ui.Hint(ArrivalScript.ObjectiveWindow, 3f));
            yield return WaitUntilNear(playerAtWindow, 1.1f, ArrivalScript.ObjectiveWindow);
            EndPlay();
            player.Controller.FaceTowards(Vector2.up);

            // Der Spieler selbst spricht mit dem Monster am Fenster (Portrait nur bei den Zeilen des Monsters)
            dialogue.Open(null);
            var k = ArrivalScript.NightKnock;
            for (int i = 0; i < k.Length - 1; i++) yield return dialogue.PlayLine(k[i]);
            yield return Ask(Last(k), ArrivalScript.ChoiceOpenWindow, ArrivalScript.ChoiceRefuse);
            bool opened = choice == 0;
            windowOpened(opened);

            if (opened)
            {
                var w = ArrivalScript.WindowOpened;
                yield return dialogue.PlayLine(w[0]);
                yield return dialogue.PlayLine(w[1]);
                dialogue.Close();
                yield return MonsterClimbsIn();
                // Ilhan wacht auf, ruft von der Tuer und rennt voraus zur Station
                Place(ilhan, ilhanWakes);
                ilhan.mover.LookAt(playerBody.position);
                OpenDoorNear(ilhanWakes);
                StartCoroutine(ui.Bubble(ilhan.go.transform, w[2].text, 0.2f));
                StartCoroutine(Flag(WalkRoute(ilhan, ilhanRunRoute, 4.2f), () => ilhan.go.SetActive(false)));
                yield return RunFromMonster();
                yield return RunToStation();
            }
            else
            {
                yield return dialogue.Play(ArrivalScript.WindowRefused);
                dialogue.Close();
                yield return ui.FadeOut();
            }
            DestroyMonster();
        }

        // ------------------------------------------------------------ Spielphasen im Film

        /// <summary>Freies Spielen mitten im Film: Eingabe und Kollision an (der Kampf bleibt aus).</summary>
        void BeginPlay(bool hideSubtitle = true)
        {
            Cutscene.End();
            foreach (var c in playerColliders) c.enabled = true;
            player.Lock(false);
            if (hideSubtitle) ui.HideSubtitle();
        }

        /// <summary>
        /// Bulut geht voraus, der Spieler laeuft selbst hinterher (mit Kollision, frei in alle Richtungen).
        /// Faellt der Spieler zurueck, bleibt Bulut stehen und wartet; am Ziel muss der Spieler aufschliessen.
        /// </summary>
        IEnumerator FollowBulut(IList<Vector2> route, float speed, string objective)
        {
            BeginPlay(hideSubtitle: false);
            StartCoroutine(ui.Hint(objective, 3f));
            bool arrived = false;
            Func<bool> hold = () => Vector2.Distance(playerBody.position, bulut.mover.Position) > waitDistance;
            StartCoroutine(Flag(WalkRoute(bulut, route, speed, hold), () => arrived = true));
            float remind = 0f;
            while (!arrived)
            {
                // Bulut wartet: nach einer Weile ein Hinweis
                remind = hold() ? remind + Time.deltaTime : 0f;
                if (remind > 12f) { remind = 0f; StartCoroutine(ui.Hint(objective, 3f)); }
                yield return null;
            }
            // Am Ziel angekommen: warten, bis der Spieler da ist
            float wait = 0f;
            while (Vector2.Distance(playerBody.position, bulut.mover.Position) > 2.4f)
            {
                wait += Time.deltaTime;
                if (wait > 12f) { wait = 0f; StartCoroutine(ui.Hint(objective, 3f)); }
                yield return null;
            }
            EndPlay();
        }

        /// <summary>Zurueck in den Film: Eingabe weg, Spieler ohne Kollision.</summary>
        void EndPlay()
        {
            StopPlayerWalk();
            player.Lock(true);
            foreach (var c in playerColliders) c.enabled = false;
            Cutscene.Begin();
        }

        IEnumerator WaitUntilNear(Vector2 spot, float radius, string objective)
        {
            float t = 0f;
            while (Vector2.Distance(playerBody.position, spot) > radius)
            {
                t += Time.deltaTime;
                if (t > 18f) { t = 0f; StartCoroutine(ui.Hint(objective, 3f)); }
                yield return null;
            }
        }

        // ------------------------------------------------------------ Das Monster am Fenster

        Actor SpawnMonster(Vector2 at)
        {
            if (monsterPrefab == null) { Debug.LogWarning("[Ankunft] monsterPrefab fehlt"); return null; }
            var go = Instantiate(monsterPrefab, at, Quaternion.identity);
            go.name = "Nacht_Monster";
            // Das Skript fuehrt das Monster: Verhalten, Dialog, Antippen und Kollision aus
            var brain = go.GetComponent<NpcBrain>();
            if (brain != null) brain.enabled = false;
            foreach (var b in go.GetComponents<NpcBehavior>()) b.enabled = false;
            var monsterNpc = go.GetComponent<MonsterNpc>();
            if (monsterNpc != null) monsterNpc.enabled = false;
            var talk = go.GetComponent<NpcDialogue>();
            if (talk != null) talk.enabled = false;
            foreach (var it in go.GetComponentsInChildren<Interactable>(true)) it.enabled = false;
            foreach (var c in go.GetComponentsInChildren<Collider2D>(true)) c.enabled = false;
            var rb = go.GetComponent<Rigidbody2D>();
            if (rb != null) { rb.linearVelocity = Vector2.zero; rb.bodyType = RigidbodyType2D.Kinematic; rb.position = at; }
            var a = new Actor { go = go, mover = go.GetComponent<NpcMover>(), brain = brain, home = at };
            a.walker = go.GetComponent<ScriptedWalker>();
            if (a.walker == null) a.walker = go.AddComponent<ScriptedWalker>();
            a.mover.Stop();
            a.mover.LookAt(at + Vector2.down);
            return a;
        }

        /// <summary>Ilhan reisst die Klapptuer auf (sonst muesste der Spieler mitten in der Flucht E druecken).</summary>
        void OpenDoorNear(Vector2 at)
        {
            KlappTuer best = null;
            float bestDist = 3f;
            foreach (var door in FindObjectsByType<KlappTuer>())
            {
                float d = Vector2.Distance(door.transform.position, at);
                if (d < bestDist) { bestDist = d; best = door; }
            }
            if (best != null && !best.Offen) best.Interact(player);
        }

        void DestroyMonster()
        {
            if (monster != null && monster.go != null) Destroy(monster.go);
            monster = null;
        }

        /// <summary>Das Fenster geht auf, das Monster klettert herein.</summary>
        IEnumerator MonsterClimbsIn()
        {
            if (monster == null) yield break;
            yield return monster.walker.WalkTo(windowAt, 1.1f, null, false);
            var m = monster.go.GetComponent<MonsterNpc>();
            if (m != null) m.ShowRevealedLook();
            yield return monster.walker.WalkTo(windowAt + Vector2.down * 0.6f, 1.3f);
        }

        /// <summary>
        /// Die Flucht aus der Bar zur Station, vom Spieler selbst gelaufen. Das Monster folgt seiner Spur und ist langsamer:
        /// es holt den Spieler nur ein, wenn er stehen bleibt. Tueren (Durchgang) versetzen den Spieler, das Monster kommt kurz danach.
        /// Wird er gefangen, beginnt es ab der letzten Tuer von vorn.
        /// </summary>
        IEnumerator RunFromMonster()
        {
            if (monster == null) yield break;
            var pc = player.Controller;
            Vector2 stationDoor = OutsideDoor;
            float monsterSpeed = pc.MoveSpeed * monsterSpeedFactor;

            var trail = new Queue<Vector2>();
            Vector2 cpPlayer = playerBackRoom, cpMonster = monster.mover.Position;
            bool cpAfterDoor = false;
            Vector2 lastPos = playerBody.position, lastRecord = lastPos, hopTarget = lastPos;
            float grace = 1.0f, hopWait = 0f, remind = 0f;

            BeginPlay();
            monster.walker.BeginManual();
            StartCoroutine(ui.Hint(ArrivalScript.ObjectiveRun, 3.5f));

            while (true)
            {
                Vector2 pp = playerBody.position;

                // Spieler wurde versetzt (Tuer): das Monster kommt etwas spaeter dort an
                if ((pp - lastPos).sqrMagnitude > 36f)
                {
                    trail.Clear();
                    monster.go.SetActive(false);
                    hopWait = 1.8f;
                    hopTarget = pp;
                    cpPlayer = pp;
                    cpAfterDoor = true;
                    lastRecord = pp;
                }
                lastPos = pp;

                if (hopWait > 0f)
                {
                    hopWait -= Time.deltaTime;
                    if (hopWait <= 0f)
                    {
                        monster.go.SetActive(true);
                        Place(monster, hopTarget);
                        monster.walker.BeginManual();
                        grace = 0.3f;
                    }
                }
                else
                {
                    if ((pp - lastRecord).sqrMagnitude > 0.0625f) { trail.Enqueue(pp); lastRecord = pp; }
                    if (grace > 0f) grace -= Time.deltaTime;
                    else
                    {
                        Vector2 mp = monster.mover.Position;
                        while (trail.Count > 0 && (trail.Peek() - mp).sqrMagnitude < 0.04f) trail.Dequeue();
                        monster.walker.Step(trail.Count > 0 ? trail.Peek() : pp, monsterSpeed);
                        if (Vector2.Distance(monster.mover.Position, pp) < catchDistance)
                        {
                            // Gefangen: zurueck zum letzten Haltepunkt, das Monster ein Stueck dahinter
                            player.Lock(true);
                            StopPlayerWalk();
                            yield return ui.FadeOut();
                            SetPlayerAt(cpPlayer);
                            lastPos = lastRecord = cpPlayer;
                            trail.Clear();
                            if (cpAfterDoor)
                            {
                                monster.go.SetActive(false);
                                hopWait = 1.8f;
                                hopTarget = cpPlayer;
                            }
                            else
                            {
                                Place(monster, cpMonster);
                                monster.walker.BeginManual();
                                grace = 1.2f;
                            }
                            var cam = CameraFollow2D.Main;
                            if (cam != null) cam.Snap();
                            StartCoroutine(ui.Hint(ArrivalScript.CaughtHint, 2.5f));
                            yield return ui.FadeIn();
                            player.Lock(false);
                        }
                    }
                }

                if (Vector2.Distance(pp, stationDoor) < 1.6f) break;
                remind += Time.deltaTime;
                if (remind > 25f) { remind = 0f; StartCoroutine(ui.Hint(ArrivalScript.ObjectiveRun, 3f)); }
                yield return null;
            }

            // Geschafft: das Monster kommt noch bis zur Schwelle und bleibt stehen
            EndPlay();
            player.Controller.FaceTowards(Vector2.up);
            if (monster.go.activeSelf)
            {
                for (float t = 0f; t < 1.2f && Vector2.Distance(monster.mover.Position, playerBody.position) > 2.2f; t += Time.deltaTime)
                {
                    monster.walker.Step(playerBody.position, monsterSpeed);
                    yield return null;
                }
                monster.walker.EndManual(playerBody.position);
            }
            yield return new WaitForSeconds(0.4f);
        }

        /// <summary>Flucht in die Station (Bulut wartet schon), Gespraech, danach die Zellen.</summary>
        IEnumerator RunToStation()
        {
            var cam = CameraFollow2D.Main;
            Vector3 entry = InsideEntry;
            var roomFocus = new GameObject("Raum_Blickpunkt").transform;
            roomFocus.position = entry + new Vector3(0f, 1.2f, 0f);   // tiefer als die Raummitte: Bulut am Schreibtisch steht ueber der Dialogbox

            yield return ui.FadeOut();
            DestroyMonster();
            SetBarLights(1f);
            bulut.go.SetActive(true);
            SeatBulut();
            Place(ilhan, ilhanInStation);
            ilhan.mover.LookAt(ilhanInStation + Vector2.up);
            SetPlayerAt(entry);
            player.Controller.FaceTowards(Vector2.up);
            if (cam != null) { cam.SetFocus(roomFocus, 0.85f); cam.Snap(); }
            yield return new WaitForSeconds(0.6f);
            yield return ui.FadeIn();

            dialogue.Open(bulutProfile);
            yield return dialogue.Play(ArrivalScript.RunToStation);
            dialogue.Close();

            // Zellen: schwarz, der Spieler schlaeft
            yield return ui.FadeOut();
            ui.Backdrop(true);
            ui.SetFade(0f);
            dialogue.Open(bulutProfile);
            yield return dialogue.Play(ArrivalScript.CellsNight);
            dialogue.Close();
            ui.SetFade(1f);
            ui.Backdrop(false);
            if (cam != null) cam.ClearFocus();
            Destroy(roomFocus.gameObject);
        }

        // ------------------------------------------------------------ 5. Morgen

        IEnumerator Morning(bool fromStation)
        {
            var cam = CameraFollow2D.Main;
            var cycle = DayNightCycle.Instance;
            if (cycle != null) cycle.SetPhase(DayPhase.Morgen, 0.3f);
            SetBarLights(1f);

            Vector2 playerAt, bulutAt;
            if (fromStation)
            {
                playerAt = OutsideDoor;
                bulutAt = (Vector2)OutsideDoor + new Vector2(1.5f, -0.4f);
            }
            else
            {
                playerAt = BarMarker("Aussen/Spawn_Aussen", new Vector3(56f, 93.6f, 0f));
                bulutAt = playerAt + new Vector2(1.6f, -0.2f);
            }
            // Ilhan ist wieder hinter der Theke, Bulut wartet draussen
            Place(ilhan, ilhanBehindBar);
            bulut.go.SetActive(true);
            Place(bulut, bulutAt);
            bulut.mover.LookAt(playerAt);
            bulut.keepPlace = true;       // bleibt nach dem Film dort, wo er steht (Heimweg uebernimmt sein Verhalten)
            SetPlayerAt(playerAt);
            player.Controller.FaceTowards(Vector2.right);
            ui.SetFade(1f);
            ui.HideSubtitle();
            if (cam != null) cam.Snap();
            yield return new WaitForSeconds(0.8f);
            yield return ui.FadeIn();

            dialogue.Open(bulutProfile);
            yield return dialogue.Play(fromStation ? ArrivalScript.MorningStation : ArrivalScript.MorningBar);
            yield return dialogue.Play(ArrivalScript.MorningReport);
            dialogue.Close();
            yield return new WaitForSeconds(0.4f);
        }
    }
}
