using System.Collections.Generic;
using UnityEngine;

namespace Nightward.NPC
{
    /// <summary>
    /// Laeuft einen Pfad vom NavGrid ab (freie Bewegung zwischen Wegpunkten), weicht anderen NPCs und dem Spieler aus.
    /// Entscheidet nicht selbst, wohin es geht. Das machen die Behaviors ueber SetDestination.
    ///
    /// Der Koerper ist kinematisch: Der NPC prueft jede Bewegung selbst per Shape-Cast und gleitet an Hindernissen
    /// entlang, statt von der Physik geschoben zu werden. Dadurch kann der Spieler ihn nicht mehr wegdruecken
    /// (und umgekehrt), und es gibt kein Zittern, wenn beide gegeneinander laufen.
    /// Der Spieler wird vorausschauend umlaufen; steht er im Weg, wartet der NPC kurz und geht dann aussen herum.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class NpcMover : MonoBehaviour
    {
        static readonly List<NpcMover> All = new List<NpcMover>();
        const float Skin = 0.02f;

        [Tooltip("Geschwindigkeit in Units (= Kacheln) pro Sekunde")]
        [SerializeField] float moveSpeed = 2.5f;
        [Tooltip("Wie weit vor einem Wegpunkt er als erreicht gilt")]
        [SerializeField] float waypointTolerance = 0.1f;
        [Tooltip("Wie weit vor dem Ziel gestoppt wird")]
        [SerializeField] float arriveDistance = 0.15f;
        [Tooltip("Wie schnell die Geschwindigkeit der Zielrichtung folgt (hoeher = abrupter)")]
        [SerializeField] float acceleration = 20f;
        [Tooltip("Layer, an denen der NPC haengen bleibt (Waende, Baeume, Spieler)")]
        [SerializeField] LayerMask collisionLayers = ~0;

        [Header("Ausweichen")]
        [Tooltip("Ab diesem Abstand schieben sich NPCs voneinander weg")]
        [SerializeField] float separationRadius = 0.6f;
        [SerializeField] float separationStrength = 1.5f;
        [Tooltip("Kommt ein NPC von vorne, wird ab diesem Abstand nach rechts ausgewichen")]
        [SerializeField] float avoidDistance = 1.2f;
        [SerializeField] float avoidStrength = 1.2f;
        [Tooltip("Aus = NPCs gehen durcheinander durch und weichen nur per Steuerung aus. Verhindert Blockaden in engen Gassen")]
        [SerializeField] bool collideWithOtherNpcs = false;

        [Header("Spieler")]
        [Tooltip("Abstand (Mitte zu Mitte), den der NPC beim Vorbeigehen zum Spieler halten will")]
        [SerializeField] float playerClearance = 0.8f;
        [Tooltip("So weit (Sekunden) wird vorausgeschaut, ob man sich in die Quere kommt")]
        [SerializeField] float playerLookAhead = 0.9f;
        [Tooltip("Steht der Spieler im Weg, wartet der NPC so lange, bevor er das Ziel aufgibt")]
        [SerializeField] float blockedGiveUpTime = 2.5f;
        [Tooltip("Drueckt der Spieler so lange gegen den stehenden NPC, macht dieser Platz")]
        [SerializeField] float pushedYieldDelay = 0.3f;

        [Header("Feststecken")]
        [Tooltip("Kommt der NPC so lange nicht voran, wird der Weg neu berechnet")]
        [SerializeField] float stuckTime = 0.6f;
        [Tooltip("So oft hintereinander darf neu geplant werden, danach gibt er das Ziel auf")]
        [SerializeField] int maxRepaths = 3;

        [Header("Debug")]
        [SerializeField] bool drawPath = true;

        Rigidbody2D body;
        Collider2D[] colliders;
        Collider2D mainCollider;
        readonly List<Vector2> path = new List<Vector2>();
        readonly List<RaycastHit2D> hits = new List<RaycastHit2D>();
        ContactFilter2D filter;
        int pathIndex;
        Vector2 destination;
        bool hasDestination;
        bool waitingForPath;
        float speedMultiplier = 1f;
        Vector2 velocity;        // gewollte Geschwindigkeit (nach Beschleunigung)
        Vector2 actualVelocity;  // tatsaechlich zurueckgelegt, fuer Animation
        Vector2 lastProgressPos;
        float stuckTimer;
        int repaths;
        float blockedTimer;
        float pushedTimer;
        float yieldSide;
        float sideSign;          // gemerkte Ausweichseite beim Spieler, damit sie nicht hin und her springt
        Rigidbody2D player;
        Collider2D playerCollider;
        Player.PlayerController playerController;

        public bool IsMoving => actualVelocity.sqrMagnitude > 0.04f;
        public bool HasArrived => !hasDestination && !waitingForPath;
        public bool PathFailed { get; private set; }
        public Vector2 Destination => destination;
        public Vector2 Velocity => actualVelocity;
        public Vector2 Position => body.position;
        /// <summary>Letzte Bewegungs- oder Blickrichtung, fuer Animation.</summary>
        public Vector2 Facing { get; private set; } = Vector2.down;
        public float MoveSpeed { get => moveSpeed; set => moveSpeed = value; }
        /// <summary>Steht still und weicht niemandem aus, z. B. waehrend eines Gespraechs.</summary>
        public bool Frozen { get; set; }

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.gravityScale = 0f;
            body.freezeRotation = true;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            body.useFullKinematicContacts = false;
            colliders = GetComponentsInChildren<Collider2D>();
            foreach (var c in colliders)
                if (!c.isTrigger) { mainCollider = c; break; }
            filter = new ContactFilter2D { useTriggers = false, useLayerMask = true, layerMask = collisionLayers };
        }

        void Start()
        {
            var p = GameObject.FindGameObjectWithTag("Player");
            if (p != null)
            {
                player = p.GetComponent<Rigidbody2D>();
                playerCollider = p.GetComponent<Collider2D>();
                playerController = p.GetComponent<Player.PlayerController>();
            }
        }

        void OnEnable()
        {
            if (!collideWithOtherNpcs)
                foreach (var other in All) IgnoreCollisions(other);
            All.Add(this);
        }

        void IgnoreCollisions(NpcMover other)
        {
            foreach (var a in colliders)
                foreach (var b in other.colliders)
                    Physics2D.IgnoreCollision(a, b);
        }

        void OnDisable()
        {
            All.Remove(this);
            if (NavGrid.Instance != null) NavGrid.Instance.CancelRequest(this);
        }

        /// <summary>
        /// Neues Ziel setzen. Bei freier Sichtlinie wird direkt gelaufen, sonst ein Pfad angefragt.
        /// speedMultiplier z. B. 1.5 zum Rennen, 0.5 zum Schlendern.
        /// </summary>
        public void SetDestination(Vector2 target, float speedMultiplier = 1f)
        {
            repaths = 0;
            blockedTimer = 0f;
            SetDestination(target, speedMultiplier, allowDirect: true);
        }

        void SetDestination(Vector2 target, float speedMultiplier, bool allowDirect)
        {
            this.speedMultiplier = speedMultiplier;
            destination = target;
            hasDestination = true;
            PathFailed = false;
            stuckTimer = 0f;
            lastProgressPos = body.position;

            var nav = NavGrid.Instance;
            if (nav == null || (allowDirect && nav.HasLineOfSight(body.position, target)))
            {
                SetPath(new List<Vector2> { target });
                return;
            }
            waitingForPath = true;
            nav.RequestPath(this, body.position, target, OnPathReady);
        }

        public void Stop()
        {
            hasDestination = false;
            waitingForPath = false;
            path.Clear();
            if (NavGrid.Instance != null) NavGrid.Instance.CancelRequest(this);
        }

        /// <summary>Im Stehen in eine Richtung schauen, z. B. zum Spieler.</summary>
        public void LookAt(Vector2 worldPoint)
        {
            Vector2 d = worldPoint - body.position;
            if (d.sqrMagnitude > 0.0001f) Facing = d.normalized;
        }

        public float RemainingDistance()
        {
            if (!hasDestination) return 0f;
            float dist = 0f;
            Vector2 p = body.position;
            for (int i = pathIndex; i < path.Count; i++) { dist += Vector2.Distance(p, path[i]); p = path[i]; }
            return dist;
        }

        void OnPathReady(List<Vector2> result)
        {
            if (!waitingForPath) return; // inzwischen gestoppt
            waitingForPath = false;
            if (result == null || result.Count == 0)
            {
                Fail();
                return;
            }
            SetPath(result);
        }

        void Fail()
        {
            PathFailed = true;
            hasDestination = false;
            path.Clear();
        }

        void SetPath(List<Vector2> newPath)
        {
            path.Clear();
            path.AddRange(newPath);
            pathIndex = 0;
        }

        void FixedUpdate()
        {
            float dt = Time.fixedDeltaTime;
            if (Frozen)
            {
                velocity = actualVelocity = Vector2.zero;
                return;
            }

            Vector2 desired = Vector2.zero;
            bool following = hasDestination && !waitingForPath && pathIndex < path.Count;
            if (following) desired = FollowPath();

            desired += Separation() + Avoidance(desired);
            float max = moveSpeed * speedMultiplier;
            desired = AvoidPlayer(desired, following);

            Vector2 yield = YieldWhenPushed(dt);
            if (yield != Vector2.zero)
            {
                desired = yield;
                max = Mathf.Max(max, moveSpeed);
            }
            if (desired.sqrMagnitude > max * max) desired = desired.normalized * max;

            velocity = Vector2.MoveTowards(velocity, desired, acceleration * dt);
            Vector2 start = body.position;
            Vector2 end = Slide(start, velocity * dt);
            body.MovePosition(end);
            actualVelocity = (end - start) / dt;
            if (actualVelocity.sqrMagnitude > 0.04f) Facing = actualVelocity.normalized;
            if (following) CheckStuck(end, dt);
        }

        Vector2 FollowPath()
        {
            Vector2 pos = body.position;
            Vector2 target = path[pathIndex];
            bool last = pathIndex == path.Count - 1;
            float tolerance = last ? arriveDistance : waypointTolerance;

            if ((target - pos).sqrMagnitude <= tolerance * tolerance)
            {
                if (last) { Stop(); return Vector2.zero; }
                pathIndex++;
                target = path[pathIndex];
                last = pathIndex == path.Count - 1;
            }

            Vector2 dir = (target - pos).normalized;
            float speed = moveSpeed * speedMultiplier;
            // Kurz vor dem Ziel abbremsen statt drueberzuschiessen
            if (last) speed = Mathf.Min(speed, (target - pos).magnitude / Time.fixedDeltaTime);
            return dir * speed;
        }

        void CheckStuck(Vector2 pos, float dt)
        {
            if ((pos - lastProgressPos).sqrMagnitude > 0.04f)
            {
                lastProgressPos = pos;
                stuckTimer = 0f;
                return;
            }
            stuckTimer += dt;
            if (stuckTimer < stuckTime) return;
            stuckTimer = 0f;

            // Der Spieler steht im Weg: nicht sinnlos neu planen (der Weg bleibt derselbe), sondern kurz warten
            if (PlayerNear(1.3f))
            {
                blockedTimer += stuckTime;
                if (blockedTimer >= blockedGiveUpTime) { Stop(); PathFailed = true; }
                return;
            }
            // Direkter Weg klappt offenbar nicht (z. B. Collider ragt ueber die Zelle): echten A*-Pfad erzwingen
            if (++repaths > maxRepaths) { Fail(); return; }
            SetDestination(destination, speedMultiplier, allowDirect: false);
        }

        // Gewollte statt tatsaechlicher Geschwindigkeit: laeuft der Spieler gegen den NPC, ist seine echte Geschwindigkeit 0
        Vector2 PlayerVelocity() =>
            playerController != null && playerController.isActiveAndEnabled ? playerController.DesiredVelocity : player.linearVelocity;

        bool PlayerNear(float radius) => player != null && (player.position - body.position).sqrMagnitude < radius * radius;

        // ---------- Bewegung mit Kollision ----------

        /// <summary>Bewegt per Shape-Cast bis zum naechsten Hindernis und gleitet an dessen Kante weiter (max. 3 Schritte).</summary>
        Vector2 Slide(Vector2 pos, Vector2 delta)
        {
            if (mainCollider == null) return pos + delta;
            for (int iteration = 0; iteration < 3; iteration++)
            {
                float dist = delta.magnitude;
                if (dist < 0.0001f) break;
                Vector2 dir = delta / dist;
                if (!CastClosest(pos, dir, dist + Skin, out var hit))
                {
                    pos += delta;
                    break;
                }
                float move = Mathf.Max(0f, hit.distance - Skin);
                pos += dir * move;
                Vector2 rest = delta - dir * move;
                // Anteil in die Wand hinein entfernen, der Rest gleitet an ihr entlang
                float into = Vector2.Dot(rest, hit.normal);
                if (into < 0f) rest -= hit.normal * into;
                float vInto = Vector2.Dot(velocity, hit.normal);
                if (vInto < 0f) velocity -= hit.normal * vInto;
                delta = rest;
            }
            return pos;
        }

        bool CastClosest(Vector2 pos, Vector2 dir, float distance, out RaycastHit2D closest)
        {
            closest = default;
            hits.Clear();
            Vector2 offset = pos - body.position; // der Koerper selbst bewegt sich erst nach dem Cast
            int count = CastShape(offset, dir, distance);
            float best = float.MaxValue;
            for (int i = 0; i < count; i++)
            {
                var h = hits[i];
                if (h.collider == null || IsOwn(h.collider)) continue;
                if (Vector2.Dot(dir, h.normal) >= 0f) continue; // laeuft vom Hindernis weg: nicht blockieren
                var rb = h.rigidbody;
                if (rb != null && rb != player && rb.bodyType != RigidbodyType2D.Static)
                {
                    var other = rb.GetComponent<NpcMover>();
                    if (other != null && !collideWithOtherNpcs) continue;
                }
                if (h.distance < best) { best = h.distance; closest = h; }
            }
            return best < float.MaxValue;
        }

        // Cast der eigenen Form an einer verschobenen Stelle (der Koerper steht noch an der alten Position)
        int CastShape(Vector2 offset, Vector2 dir, float distance)
        {
            Vector2 center = (Vector2)mainCollider.bounds.center + offset;
            switch (mainCollider)
            {
                case CapsuleCollider2D cap:
                    return Physics2D.CapsuleCast(center, Vector2.Scale(cap.size, (Vector2)transform.lossyScale), cap.direction, 0f, dir, filter, hits, distance);
                case CircleCollider2D circle:
                    return Physics2D.CircleCast(center, circle.radius * Mathf.Abs(transform.lossyScale.x), dir, filter, hits, distance);
                case BoxCollider2D box:
                    return Physics2D.BoxCast(center, Vector2.Scale(box.size, (Vector2)transform.lossyScale), 0f, dir, filter, hits, distance);
                default:
                    return offset.sqrMagnitude < 0.000001f ? mainCollider.Cast(dir, filter, hits, distance) : 0;
            }
        }

        bool IsOwn(Collider2D c)
        {
            foreach (var own in colliders) if (own == c) return true;
            return false;
        }

        // ---------- Ausweichen ----------

        // Jeder NPC schiebt sich von zu nahen Nachbarn weg. Reicht fuer hunderte NPCs,
        // bei deutlich mehr waere ein Raumraster fuer die Nachbarsuche sinnvoll.
        Vector2 Separation()
        {
            Vector2 push = Vector2.zero;
            Vector2 pos = body.position;
            float r2 = separationRadius * separationRadius;
            foreach (var other in All)
            {
                if (other == this) continue;
                Vector2 d = pos - other.body.position;
                float dist2 = d.sqrMagnitude;
                if (dist2 >= r2) continue;
                if (dist2 < 0.0001f) d = Random.insideUnitCircle * 0.01f; // exakt gleiche Position
                float dist = Mathf.Sqrt(dist2);
                push += d.normalized * (1f - dist / separationRadius);
            }
            return push * separationStrength;
        }

        // Steht oder kommt jemand direkt im Weg, nach rechts ausweichen. Weil alle nach rechts gehen,
        // laufen sich zwei NPCs auf Gegenkurs nicht gegenseitig in die Arme.
        Vector2 Avoidance(Vector2 desired)
        {
            if (desired.sqrMagnitude < 0.01f) return Vector2.zero;
            Vector2 pos = body.position;
            Vector2 forward = desired.normalized;
            Vector2 right = new Vector2(forward.y, -forward.x);
            Vector2 steer = Vector2.zero;
            foreach (var other in All)
            {
                if (other == this) continue;
                Vector2 toOther = other.body.position - pos;
                float ahead = Vector2.Dot(toOther, forward);
                if (ahead <= 0f || ahead > avoidDistance) continue;
                float lateral = Vector2.Dot(toOther, right);
                if (Mathf.Abs(lateral) > separationRadius) continue; // steht nicht im Weg
                // Steht der andere schon rechts, weicht man nach links aus
                float side = lateral > 0.05f ? -1f : 1f;
                steer += right * side * (1f - ahead / avoidDistance);
            }
            return steer * avoidStrength * moveSpeed * speedMultiplier;
        }

        /// <summary>
        /// Vorausschauend am Spieler vorbei: Wo stehen beide in Kuerze am naechsten zueinander? Ist das zu nah,
        /// wird seitlich (auf die freie Seite) ausgewichen und vor dem Spieler abgebremst, statt in ihn hineinzulaufen.
        /// </summary>
        Vector2 AvoidPlayer(Vector2 desired, bool following)
        {
            if (player == null || !following || desired.sqrMagnitude < 0.01f) { sideSign = 0f; return desired; }
            Vector2 pos = body.position;
            Vector2 rp = player.position - pos;
            float dist = rp.magnitude;
            if (dist > 3f) { sideSign = 0f; return desired; }

            Vector2 rv = PlayerVelocity() - desired;
            float t = 0f;
            if (rv.sqrMagnitude > 0.01f) t = Mathf.Clamp(-Vector2.Dot(rp, rv) / rv.sqrMagnitude, 0f, playerLookAhead);
            Vector2 closest = rp + rv * t;
            float miss = closest.magnitude;
            if (miss >= playerClearance) { sideSign = 0f; return desired; }

            float speed = desired.magnitude;
            Vector2 forward = desired / speed;
            Vector2 side = new Vector2(-forward.y, forward.x);
            if (sideSign == 0f)
            {
                // Auf die Seite, auf der der Spieler nicht sein wird; gibt es dort keinen Platz, auf die andere
                float lateral = Vector2.Dot(closest, side);
                sideSign = Mathf.Abs(lateral) > 0.05f ? -Mathf.Sign(lateral) : 1f;
                if (!IsFree(pos + side * sideSign * 0.8f)) sideSign = -sideSign;
            }
            bool sideFree = IsFree(pos + side * sideSign * 0.8f);

            float urgency = (1f - miss / playerClearance) * (1f - t / (playerLookAhead + 0.01f) * 0.5f);
            Vector2 result = desired;
            if (sideFree) result += side * sideSign * speed * 1.6f * urgency;

            // Spieler direkt vor einem und nah: bremsen. Ohne freie Seite ganz stehen bleiben (warten)
            float ahead = Vector2.Dot(rp, forward);
            if (ahead > 0f && dist < playerClearance + 0.4f)
                result -= forward * Mathf.Min(speed, Vector2.Dot(result, forward)) * (sideFree ? 0.6f : 1f);
            return result;
        }

        /// <summary>Stehender NPC: drueckt der Spieler eine Weile gegen ihn, tritt er zur Seite (wie in einer Tuer).
        /// Wer nur auf ihn zugeht, um ihn anzusprechen, verscheucht ihn dadurch nicht.</summary>
        Vector2 YieldWhenPushed(float dt)
        {
            if (player == null || playerCollider == null || mainCollider == null) { pushedTimer = 0f; return Vector2.zero; }
            Vector2 pos = body.position;
            Vector2 toMe = pos - player.position;
            Vector2 pv = PlayerVelocity();
            float gap = mainCollider.Distance(playerCollider).distance;
            bool pushing = gap < 0.08f && pv.sqrMagnitude > 0.1f && Vector2.Dot(pv.normalized, toMe.normalized) > 0.5f;
            bool yielding = pushedTimer >= pushedYieldDelay;
            if (pushing) pushedTimer += dt;
            // Einmal am Ausweichen: nur so weit, bis etwas Luft zwischen beiden ist, dann stehen bleiben
            else if (!yielding || gap > 0.3f) { pushedTimer = 0f; yieldSide = 0f; return Vector2.zero; }
            if (pushedTimer < pushedYieldDelay) return Vector2.zero;

            Vector2 heading = pv.sqrMagnitude > 0.1f ? pv.normalized : -toMe.normalized;
            Vector2 side = new Vector2(-heading.y, heading.x);
            if (yieldSide == 0f)
            {
                float lateral = Vector2.Dot(toMe, side);
                yieldSide = Mathf.Abs(lateral) > 0.05f ? Mathf.Sign(lateral) : (Random.value < 0.5f ? 1f : -1f);
                if (!IsFree(pos + side * yieldSide * 0.7f)) yieldSide = -yieldSide;
            }
            Vector2 dir = side * yieldSide;
            if (!IsFree(pos + dir * 0.7f)) dir = toMe.normalized; // beide Seiten zu: zuruecktreten
            if (!IsFree(pos + dir * 0.7f)) return Vector2.zero;
            return (dir + toMe.normalized * 0.3f).normalized * moveSpeed * 0.8f;
        }

        static bool IsFree(Vector2 world) => NavGrid.Instance == null || NavGrid.Instance.IsWalkable(world);

        void OnDrawGizmosSelected()
        {
            if (!drawPath || path.Count == 0 || !hasDestination) return;
            Gizmos.color = Color.cyan;
            Vector3 p = transform.position;
            for (int i = pathIndex; i < path.Count; i++)
            {
                Gizmos.DrawLine(p, path[i]);
                Gizmos.DrawWireSphere(path[i], 0.08f);
                p = path[i];
            }
        }
    }
}
