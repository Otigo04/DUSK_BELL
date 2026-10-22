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
        [SerializeField] Vector2 veronicaAt = new Vector2(22.6f, 9.1f);
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
        [SerializeField] Vector2[] barInnerRoute = { new Vector2(224.5f, 3.2f), new Vector2(224.6f, 13.6f) };
        [SerializeField] Vector2 playerAtBar = new Vector2(222.4f, 13.6f);
        [SerializeField] Vector2 playerBackRoom = new Vector2(234.4f, 14.0f);
        [SerializeField] Vector2 ilhanBackRoom = new Vector2(235.8f, 14.0f);

        [Header("Tag-Uhr")]
        [Tooltip("Spaeter Nachmittag, warmes Abendlicht")]
        [SerializeField] DayPhase clockPhase = DayPhase.Tag;
        [SerializeField, Range(0f, 1f)] float clockProgress = 0.75f;

        [Header("Testen")]
        [Tooltip("Ankunft auch ohne Opening starten (Level_01 direkt per Play)")]
        [SerializeField] bool runWithoutOpening;

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
        }

        readonly List<Actor> actors = new List<Actor>();
        readonly List<(Light2D light, float intensity)> barLights = new List<(Light2D, float)>();
        Actor bulut, mara, veronica, david, can, ilhan;
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
                yield return ArrivalAtGraveyard();
                yield return WalkToStation();
                yield return StationScene();
                yield return WalkToBar();
                yield return BarByDay();
                bool windowOpened = false;
                yield return FirstNight(result => windowOpened = result);
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

        void BeginFilm()
        {
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
            mover.Stop();
            actors.Add(a);
            return a;
        }

        /// <summary>Die Figur geht wieder in ihren Alltag: an den Heimatort, Verhalten an.</summary>
        void Release(Actor a)
        {
            if (a == null || a.go == null) return;
            a.go.SetActive(true);
            if (a.crowd != null) { Destroy(a.crowd); a.crowd = null; }
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
            // 0,9 hoeher: unten verdeckt die Erzaehlerzeile sonst die vorderen Gaeste
            float centerY = (n > 0 ? (minY + maxY) * 0.5f : grave.y) + 0.9f;
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
            yield return Escort(bulut, route, bulutSpeed);
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
            roomFocus.position = entry + new Vector3(0f, 2.2f, 0f);

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
            var rb = bulut.go.GetComponent<Rigidbody2D>();
            if (rb != null) rb.bodyType = RigidbodyType2D.Dynamic;
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
            var rb = bulut.go.GetComponent<Rigidbody2D>();
            if (rb != null) rb.bodyType = RigidbodyType2D.Kinematic;
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
            yield return Escort(bulut, barRoute, bulutSpeed);
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
            StartCoroutine(Flag(WalkRoute(bulut, barInnerRoute, 1.7f), () => { }));
            yield return PlayerWalkTo(inside + new Vector2(0f, 1.0f), 1.5f);
            yield return PlayerWalkTo(barInnerRoute[0] + new Vector2(0f, 0.3f), 1.6f);
            yield return PlayerWalkTo(playerAtBar, 1.6f);
            yield return WaitWalking(bulut);
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

        IEnumerator WaitWalking(Actor a)
        {
            while (a.walker.Walking) yield return null;
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
            Place(ilhan, ilhanBackRoom);
            ilhan.mover.LookAt(ilhanBackRoom + Vector2.up);
            if (cam != null) cam.Snap();
            yield return new WaitForSeconds(0.8f);
            yield return ui.FadeIn();
            yield return new WaitForSeconds(0.4f);

            dialogue.Open(ilhanProfile);
            var k = ArrivalScript.NightKnock;
            for (int i = 0; i < k.Length - 1; i++) yield return dialogue.PlayLine(k[i]);
            yield return Ask(Last(k), ArrivalScript.ChoiceOpenWindow, ArrivalScript.ChoiceRefuse);
            bool opened = choice == 0;
            windowOpened(opened);

            if (opened)
            {
                yield return dialogue.Play(ArrivalScript.WindowOpened);
                dialogue.Close();
                yield return RunToStation();
            }
            else
            {
                yield return dialogue.Play(ArrivalScript.WindowRefused);
                dialogue.Close();
                yield return ui.FadeOut();
            }
        }

        /// <summary>Flucht in die Station (Bulut wartet schon), Gespraech, danach die Zellen.</summary>
        IEnumerator RunToStation()
        {
            var cam = CameraFollow2D.Main;
            Vector3 entry = InsideEntry;
            var roomFocus = new GameObject("Raum_Blickpunkt").transform;
            roomFocus.position = entry + new Vector3(0f, 2.2f, 0f);

            ui.SetFade(1f);
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
            var rb = bulut.go.GetComponent<Rigidbody2D>();
            if (rb != null) rb.bodyType = RigidbodyType2D.Dynamic;
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
