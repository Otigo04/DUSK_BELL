using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Vision
{
    /// <summary>
    /// Ein Innenraum (Haus, Bar, Keller ...). Steht der Spieler darin, ist draussen alles schwarz,
    /// nur durch Fenster und Tueren (VisionOpening als Kinder) sieht er in Blickrichtung hinaus (PlayerVision).
    /// Die Flaeche ist ein BoxCollider2D oder PolygonCollider2D (Trigger) inklusive der Waende.
    /// Optional werden beim Betreten Objekte aus- bzw. eingeblendet, z. B. Dach und Fassade gegen den Innenraum.
    /// </summary>
    public class Interior : MonoBehaviour
    {
        static readonly List<Interior> all = new List<Interior>();
        public static IReadOnlyList<Interior> All => all;

        [Tooltip("Raumflaeche inkl. Waende. Leer = Collider an diesem Objekt")]
        [SerializeField] Collider2D area;
        [Tooltip("Beim Betreten ausblenden, z. B. Dach")]
        [SerializeField] GameObject[] hideWhenInside = new GameObject[0];
        [Tooltip("Nur sichtbar, solange der Spieler drin ist, z. B. Innenraum-Tilemaps")]
        [SerializeField] GameObject[] showWhenInside = new GameObject[0];

        VisionOpening[] openings;
        Vector2[] outline;
        int[] triangles;
        bool playerInside;
        bool started;

        public IReadOnlyList<VisionOpening> Openings => openings;
        /// <summary>Umriss in Weltkoordinaten (geschlossen, ohne doppelten Endpunkt).</summary>
        public Vector2[] Outline => outline;
        /// <summary>Dreiecke ueber Outline (Indizes), fuer die Maske des Raums.</summary>
        public int[] Triangles => triangles;

        public event Action<bool> PlayerInsideChanged;

        void Awake()
        {
            if (area == null) area = GetComponent<Collider2D>();
            openings = GetComponentsInChildren<VisionOpening>(true);
            Rebuild();
            Apply(false);
        }

        // Erst in Start: dann sind die Tilemap-Collider der Waende sicher aufgebaut (die Apertur sucht die Wandkante per Physik)
        void Start()
        {
            started = true;
            ComputeApertures();
        }

        void ComputeApertures()
        {
            Physics2D.SyncTransforms();
            Vector2 center = area.bounds.center;
            foreach (var o in openings) if (o != null) o.ComputeAperture(center);
        }

        void OnEnable() => all.Add(this);
        void OnDisable() => all.Remove(this);

        /// <summary>Umriss neu lesen, z. B. nachdem der Raum verschoben wurde.</summary>
        public void Rebuild()
        {
            outline = ReadOutline(area);
            triangles = Triangulate(outline);
            if (started) ComputeApertures();
        }

        public bool Contains(Vector2 world) => area != null && area.OverlapPoint(world);

        /// <summary>Liegt der Punkt (auf der Aussenkante) in einem offenen Fenster / einer offenen Tuer?</summary>
        public bool IsOpening(Vector2 world)
        {
            foreach (var o in openings)
                if (o != null && o.Open && o.isActiveAndEnabled && o.Contains(world)) return true;
            return false;
        }

        /// <summary>Wird von PlayerVision gesetzt.</summary>
        public void SetPlayerInside(bool inside)
        {
            if (inside == playerInside) return;
            playerInside = inside;
            Apply(inside);
            PlayerInsideChanged?.Invoke(inside);
        }

        void Apply(bool inside)
        {
            foreach (var go in hideWhenInside) if (go != null) go.SetActive(!inside);
            foreach (var go in showWhenInside) if (go != null) go.SetActive(inside);
        }

        static Vector2[] ReadOutline(Collider2D c)
        {
            var t = c.transform;
            switch (c)
            {
                case BoxCollider2D box:
                    Vector2 h = box.size * 0.5f;
                    return new Vector2[]
                    {
                        t.TransformPoint(box.offset + new Vector2(-h.x, -h.y)),
                        t.TransformPoint(box.offset + new Vector2(h.x, -h.y)),
                        t.TransformPoint(box.offset + new Vector2(h.x, h.y)),
                        t.TransformPoint(box.offset + new Vector2(-h.x, h.y)),
                    };
                case PolygonCollider2D poly:
                    var pts = poly.GetPath(0);
                    var world = new Vector2[pts.Length];
                    for (int i = 0; i < pts.Length; i++) world[i] = t.TransformPoint(pts[i] + poly.offset);
                    return world;
                default:
                    var b = c.bounds;
                    return new Vector2[] { b.min, new Vector2(b.max.x, b.min.y), b.max, new Vector2(b.min.x, b.max.y) };
            }
        }

        // Ear Clipping fuer einfache Polygone (Raeume sind klein, das reicht voellig)
        static int[] Triangulate(Vector2[] pts)
        {
            int n = pts.Length;
            var result = new List<int>();
            if (n < 3) return result.ToArray();
            var idx = new List<int>(n);
            float area = 0f;
            for (int i = 0; i < n; i++)
            {
                Vector2 a = pts[i], b = pts[(i + 1) % n];
                area += a.x * b.y - b.x * a.y;
            }
            // gegen den Uhrzeigersinn ordnen
            for (int i = 0; i < n; i++) idx.Add(area > 0f ? i : n - 1 - i);

            int guard = n * n;
            while (idx.Count > 3 && guard-- > 0)
            {
                bool clipped = false;
                for (int i = 0; i < idx.Count; i++)
                {
                    int ia = idx[(i + idx.Count - 1) % idx.Count], ib = idx[i], ic = idx[(i + 1) % idx.Count];
                    Vector2 a = pts[ia], b = pts[ib], c = pts[ic];
                    if (Cross(b - a, c - b) <= 0f) continue; // Spiegelecke
                    bool inside = false;
                    foreach (int j in idx)
                    {
                        if (j == ia || j == ib || j == ic) continue;
                        if (InTriangle(pts[j], a, b, c)) { inside = true; break; }
                    }
                    if (inside) continue;
                    result.Add(ia); result.Add(ib); result.Add(ic);
                    idx.RemoveAt(i);
                    clipped = true;
                    break;
                }
                if (!clipped) break;
            }
            if (idx.Count == 3) { result.Add(idx[0]); result.Add(idx[1]); result.Add(idx[2]); }
            return result.ToArray();
        }

        static float Cross(Vector2 a, Vector2 b) => a.x * b.y - a.y * b.x;

        static bool InTriangle(Vector2 p, Vector2 a, Vector2 b, Vector2 c) =>
            Cross(b - a, p - a) >= 0f && Cross(c - b, p - b) >= 0f && Cross(a - c, p - c) >= 0f;

        void OnDrawGizmosSelected()
        {
            var c = area != null ? area : GetComponent<Collider2D>();
            if (c == null) return;
            var pts = ReadOutline(c);
            Gizmos.color = new Color(1f, 0.82f, 0.48f, 0.8f);
            for (int i = 0; i < pts.Length; i++) Gizmos.DrawLine(pts[i], pts[(i + 1) % pts.Length]);
        }
    }
}
