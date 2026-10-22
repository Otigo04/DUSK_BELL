using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Nightward.NPC
{
    /// <summary>
    /// Begehbarkeits-Raster der Szene (eine Zelle = eine Kachel) plus Warteschlange fuer Pfadanfragen.
    /// Blockiert ist eine Zelle, wenn eine der blockierenden Tilemaps dort ein Tile hat
    /// oder ein statischer Collider (kein Trigger, kein beweglicher Rigidbody) in der Zelle liegt.
    /// Genau eine Instanz pro Szene.
    /// </summary>
    [DefaultExecutionOrder(-100)]
    public class NavGrid : MonoBehaviour
    {
        public static NavGrid Instance { get; private set; }

        [Tooltip("Grid der Tilemaps. Leer = automatisch suchen")]
        [SerializeField] Grid grid;
        [Tooltip("Tilemaps, deren Tiles immer blockieren. Leer = alle Tilemaps mit TilemapCollider2D")]
        [SerializeField] List<Tilemap> blockingTilemaps = new List<Tilemap>();
        [Tooltip("Layer, auf denen statische Collider als Hindernis zaehlen")]
        [SerializeField] LayerMask obstacleLayers = ~0;
        [Tooltip("Groesse der Pruefbox pro Zelle (1 = ganze Kachel). Kleiner = NPCs duerfen naeher an Hindernisse")]
        [SerializeField, Range(0.2f, 1f)] float probeSize = 0.8f;
        [Tooltip("Halbe Koerperbreite der NPCs. Gerade Abkuerzungen muessen in dieser Breite frei sein")]
        [SerializeField] float agentRadius = 0.3f;
        [Tooltip("Rand um die Tilemap-Bounds, der zusaetzlich gerastert wird (in Zellen)")]
        [SerializeField] int padding = 1;

        [Header("Warteschlange")]
        [Tooltip("Maximale Pfadberechnungen pro Frame. Verteilt die Last bei vielen NPCs")]
        [SerializeField] int maxPathsPerFrame = 8;

        [Header("Debug")]
        [SerializeField] bool drawGrid = true;

        bool[] walkable;
        bool[] nearWall; // begehbar, aber direkt neben einem Hindernis: Pfade meiden solche Zellen, wenn es geht
        int[] region; // zusammenhaengende Flaechen, 0 = blockiert
        BoundsInt bounds;
        Pathfinder pathfinder;

        readonly LinkedList<PathRequest> queue = new LinkedList<PathRequest>();
        readonly Dictionary<object, LinkedListNode<PathRequest>> pendingByOwner = new Dictionary<object, LinkedListNode<PathRequest>>();

        struct PathRequest
        {
            public object owner;
            public Vector2 from, to;
            public Action<List<Vector2>> callback;
        }

        public int Width => bounds.size.x;
        public int Height => bounds.size.y;
        public Vector3 CellSize => grid.cellSize;

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Debug.LogWarning("Mehr als ein NavGrid in der Szene, " + name + " wird ignoriert.", this);
                enabled = false;
                return;
            }
            Instance = this;
            Rebuild();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Update()
        {
            int budget = maxPathsPerFrame;
            while (budget-- > 0 && queue.Count > 0)
            {
                var req = queue.First.Value;
                queue.RemoveFirst();
                pendingByOwner.Remove(req.owner);
                req.callback(FindPath(req.from, req.to));
            }
        }

        // ---------- Aufbau ----------

        /// <summary>Rastert die komplette Szene neu. Nach groesseren Aenderungen am Level aufrufen.</summary>
        [ContextMenu("Raster neu bauen")]
        public void Rebuild()
        {
            if (grid == null) grid = FindAnyObjectByType<Grid>();
            if (grid == null)
            {
                Debug.LogError("NavGrid: kein Grid in der Szene gefunden.", this);
                return;
            }
            if (blockingTilemaps.Count == 0)
            {
                foreach (var tm in grid.GetComponentsInChildren<Tilemap>())
                    if (tm.GetComponent<TilemapCollider2D>() != null) blockingTilemaps.Add(tm);
            }

            bounds = CollectBounds();
            walkable = new bool[Width * Height];
            region = new int[Width * Height];
            for (int y = 0; y < Height; y++)
                for (int x = 0; x < Width; x++)
                    walkable[x + y * Width] = ProbeCell(new Vector3Int(bounds.xMin + x, bounds.yMin + y, 0));

            BuildNearWall();
            BuildRegions();
            pathfinder = new Pathfinder(this);
        }

        /// <summary>Rastert nur einen Weltbereich neu, z. B. wenn ein Hindernis gebaut oder entfernt wurde.</summary>
        public void RebuildArea(Bounds worldArea)
        {
            if (walkable == null) return;
            Vector2Int min = WorldToCell(worldArea.min), max = WorldToCell(worldArea.max);
            for (int y = Mathf.Max(0, min.y); y <= Mathf.Min(Height - 1, max.y); y++)
                for (int x = Mathf.Max(0, min.x); x <= Mathf.Min(Width - 1, max.x); x++)
                    walkable[x + y * Width] = ProbeCell(new Vector3Int(bounds.xMin + x, bounds.yMin + y, 0));
            BuildNearWall();
            BuildRegions();
        }

        void BuildNearWall()
        {
            if (nearWall == null || nearWall.Length != walkable.Length) nearWall = new bool[walkable.Length];
            for (int y = 0; y < Height; y++)
                for (int x = 0; x < Width; x++)
                {
                    bool near = false;
                    for (int dy = -1; dy <= 1 && !near; dy++)
                        for (int dx = -1; dx <= 1 && !near; dx++)
                            if ((dx != 0 || dy != 0) && InBounds(x + dx, y + dy) && !walkable[x + dx + (y + dy) * Width]) near = true;
                    nearWall[x + y * Width] = walkable[x + y * Width] && near;
                }
        }

        BoundsInt CollectBounds()
        {
            bool any = false;
            Vector3Int min = Vector3Int.zero, max = Vector3Int.zero;
            foreach (var tm in grid.GetComponentsInChildren<Tilemap>())
            {
                tm.CompressBounds();
                var b = tm.cellBounds;
                if (b.size.x == 0 || b.size.y == 0) continue;
                if (!any) { min = b.min; max = b.max; any = true; }
                else { min = Vector3Int.Min(min, b.min); max = Vector3Int.Max(max, b.max); }
            }
            min -= new Vector3Int(padding, padding, 0);
            max += new Vector3Int(padding, padding, 0);
            return new BoundsInt(min.x, min.y, 0, max.x - min.x, max.y - min.y, 1);
        }

        bool ProbeCell(Vector3Int cell)
        {
            foreach (var tm in blockingTilemaps)
                if (tm != null && tm.HasTile(cell)) return false;

            Vector2 center = grid.GetCellCenterWorld(cell);
            Vector2 size = (Vector2)grid.cellSize * probeSize;
            foreach (var col in Physics2D.OverlapBoxAll(center, size, 0f, obstacleLayers))
                if (IsStaticObstacle(col)) return false;
            return true;
        }

        static bool IsStaticObstacle(Collider2D col)
        {
            if (col.isTrigger) return false;
            if (col is TilemapCollider2D) return false; // wird ueber blockingTilemaps/HasTile erfasst
            var rb = col.attachedRigidbody;
            return rb == null || rb.bodyType == RigidbodyType2D.Static;
        }

        // Flood-Fill: jede zusammenhaengende Flaeche bekommt eine eigene Nummer.
        // Damit erkennt man ohne A*, ob ein Ziel ueberhaupt erreichbar ist.
        void BuildRegions()
        {
            Array.Clear(region, 0, region.Length);
            var stack = new Stack<int>();
            int next = 1;
            for (int i = 0; i < walkable.Length; i++)
            {
                if (!walkable[i] || region[i] != 0) continue;
                region[i] = next;
                stack.Push(i);
                while (stack.Count > 0)
                {
                    int c = stack.Pop();
                    int cx = c % Width, cy = c / Width;
                    TryFill(cx + 1, cy, next, stack);
                    TryFill(cx - 1, cy, next, stack);
                    TryFill(cx, cy + 1, next, stack);
                    TryFill(cx, cy - 1, next, stack);
                }
                next++;
            }
        }

        void TryFill(int x, int y, int id, Stack<int> stack)
        {
            if (!InBounds(x, y)) return;
            int i = x + y * Width;
            if (!walkable[i] || region[i] != 0) return;
            region[i] = id;
            stack.Push(i);
        }

        // ---------- Abfragen ----------

        public bool InBounds(int x, int y) => x >= 0 && y >= 0 && x < Width && y < Height;
        public bool IsWalkable(int x, int y) => InBounds(x, y) && walkable[x + y * Width];
        public bool IsWalkable(Vector2 world) { var c = WorldToCell(world); return IsWalkable(c.x, c.y); }
        public bool IsNearWall(int x, int y) => InBounds(x, y) && nearWall[x + y * Width];
        public int RegionAt(int x, int y) => InBounds(x, y) ? region[x + y * Width] : 0;

        /// <summary>Weltposition in lokale Rasterkoordinaten (0..Width-1, 0..Height-1).</summary>
        public Vector2Int WorldToCell(Vector2 world)
        {
            var c = grid.WorldToCell(world);
            return new Vector2Int(c.x - bounds.xMin, c.y - bounds.yMin);
        }

        public Vector2 CellToWorld(int x, int y) =>
            grid.GetCellCenterWorld(new Vector3Int(x + bounds.xMin, y + bounds.yMin, 0));

        /// <summary>Liegen beide Punkte in derselben zusammenhaengenden Flaeche?</summary>
        public bool IsReachable(Vector2 from, Vector2 to)
        {
            if (!TryGetNearestWalkable(WorldToCell(from), out var a, 3)) return false;
            if (!TryGetNearestWalkable(WorldToCell(to), out var b, 3)) return false;
            return RegionAt(a.x, a.y) == RegionAt(b.x, b.y);
        }

        /// <summary>Naechste begehbare Zelle in Spiralsuche bis maxRadius.</summary>
        public bool TryGetNearestWalkable(Vector2Int cell, out Vector2Int result, int maxRadius = 6)
        {
            if (IsWalkable(cell.x, cell.y)) { result = cell; return true; }
            for (int r = 1; r <= maxRadius; r++)
            {
                float best = float.MaxValue;
                result = cell;
                for (int dy = -r; dy <= r; dy++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        if (Mathf.Abs(dx) != r && Mathf.Abs(dy) != r) continue; // nur der Ring
                        if (!IsWalkable(cell.x + dx, cell.y + dy)) continue;
                        float d = dx * dx + dy * dy;
                        if (d < best) { best = d; result = new Vector2Int(cell.x + dx, cell.y + dy); }
                    }
                if (best < float.MaxValue) return true;
            }
            result = cell;
            return false;
        }

        /// <summary>Zufaelliger begehbarer Punkt im Radius, der von 'center' aus erreichbar ist.</summary>
        public bool TryGetRandomPoint(Vector2 center, float radius, out Vector2 point, int attempts = 20)
        {
            point = center;
            if (!TryGetNearestWalkable(WorldToCell(center), out var start)) return false;
            int startRegion = RegionAt(start.x, start.y);
            for (int i = 0; i < attempts; i++)
            {
                var c = WorldToCell(center + UnityEngine.Random.insideUnitCircle * radius);
                if (IsWalkable(c.x, c.y) && RegionAt(c.x, c.y) == startRegion)
                {
                    point = CellToWorld(c.x, c.y);
                    return true;
                }
            }
            return false;
        }

        /// <summary>
        /// Kann ein NPC gerade von 'from' nach 'to' laufen? Prueft die Mittellinie und zwei um agentRadius
        /// seitlich versetzte Linien, damit der Koerper nicht an Hindernisecken haengen bleibt.
        /// Wird fuer das Glaetten der Pfade und fuer direktes Laufen genutzt.
        /// </summary>
        public bool HasLineOfSight(Vector2 from, Vector2 to)
        {
            if (!HasLineOfSightThin(from, to)) return false;
            Vector2 d = to - from;
            if (agentRadius <= 0f || d.sqrMagnitude < 0.0001f) return true;
            Vector2 side = new Vector2(-d.y, d.x).normalized * agentRadius;
            return HasLineOfSightThin(from + side, to + side) && HasLineOfSightThin(from - side, to - side);
        }

        /// <summary>Gerade Linie ohne Breite, nur durch begehbare Zellen (Supercover: jede beruehrte Zelle zaehlt).</summary>
        public bool HasLineOfSightThin(Vector2 from, Vector2 to)
        {
            Vector2 cs = grid.cellSize;
            Vector2 origin = grid.CellToWorld(new Vector3Int(bounds.xMin, bounds.yMin, 0));
            Vector2 a = (from - origin) / cs, b = (to - origin) / cs;

            int x = Mathf.FloorToInt(a.x), y = Mathf.FloorToInt(a.y);
            int endX = Mathf.FloorToInt(b.x), endY = Mathf.FloorToInt(b.y);
            Vector2 d = b - a;
            int stepX = d.x > 0 ? 1 : -1, stepY = d.y > 0 ? 1 : -1;
            float tDeltaX = d.x != 0 ? Mathf.Abs(1f / d.x) : float.MaxValue;
            float tDeltaY = d.y != 0 ? Mathf.Abs(1f / d.y) : float.MaxValue;
            float tMaxX = d.x != 0 ? ((stepX > 0 ? x + 1 - a.x : a.x - x) * tDeltaX) : float.MaxValue;
            float tMaxY = d.y != 0 ? ((stepY > 0 ? y + 1 - a.y : a.y - y) * tDeltaY) : float.MaxValue;

            int guard = Width + Height + 4;
            while (guard-- > 0)
            {
                if (!IsWalkable(x, y)) return false;
                if (x == endX && y == endY) return true;
                if (Mathf.Abs(tMaxX - tMaxY) < 1e-5f)
                {
                    // Linie geht genau durch eine Ecke: beide Nachbarn muessen frei sein
                    if (!IsWalkable(x + stepX, y) || !IsWalkable(x, y + stepY)) return false;
                    x += stepX; y += stepY;
                    tMaxX += tDeltaX; tMaxY += tDeltaY;
                }
                else if (tMaxX < tMaxY) { x += stepX; tMaxX += tDeltaX; }
                else { y += stepY; tMaxY += tDeltaY; }
            }
            return false;
        }

        // ---------- Pfade ----------

        /// <summary>Sofortige Berechnung. Fuer einzelne Aufrufe ok, bei vielen NPCs lieber RequestPath nutzen.</summary>
        public List<Vector2> FindPath(Vector2 from, Vector2 to) => pathfinder?.FindPath(from, to);

        /// <summary>
        /// Stellt eine Anfrage in die Warteschlange. Eine neuere Anfrage desselben owners ersetzt die alte,
        /// so wird bei schnellem Neuplanen (z. B. Folgen) nicht doppelt gerechnet.
        /// Callback bekommt null, wenn kein Weg existiert.
        /// </summary>
        public void RequestPath(object owner, Vector2 from, Vector2 to, Action<List<Vector2>> callback)
        {
            var req = new PathRequest { owner = owner, from = from, to = to, callback = callback };
            if (pendingByOwner.TryGetValue(owner, out var node))
            {
                node.Value = req; // Platz in der Schlange bleibt erhalten
                return;
            }
            pendingByOwner[owner] = queue.AddLast(req);
        }

        public void CancelRequest(object owner)
        {
            if (!pendingByOwner.TryGetValue(owner, out var node)) return;
            queue.Remove(node);
            pendingByOwner.Remove(owner);
        }

        void OnDrawGizmosSelected()
        {
            if (!drawGrid || walkable == null || grid == null) return;
            Vector3 size = grid.cellSize * 0.9f;
            for (int y = 0; y < Height; y++)
                for (int x = 0; x < Width; x++)
                {
                    Gizmos.color = walkable[x + y * Width] ? new Color(0.3f, 1f, 0.4f, 0.12f) : new Color(1f, 0.2f, 0.3f, 0.35f);
                    Gizmos.DrawCube(CellToWorld(x, y), size);
                }
        }
    }
}
