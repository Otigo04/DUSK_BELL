using System.Collections.Generic;
using Nightward.Player;
using UnityEngine;

namespace Nightward.Vision
{
    /// <summary>
    /// Sicht des Spielers in Gebaeuden. Steht er in einem Interior, wird alles ausserhalb schwarz.
    /// Sichtbar bleiben der Raum selbst und ein breites Blickfeld in Blickrichtung, das nur durch offene Fenster
    /// und Tueren (VisionOpening) nach draussen reicht, z. B. um nachts nach Monstern zu sehen.
    /// Wie in echt: Direkt vor dem Fenster sieht man fast die ganze Seite draussen, aus der Raummitte nur einen Ausschnitt.
    /// Draussen gibt es keinen Effekt.
    ///
    /// Aussehen: Die Sichtkanten laufen exakt durch die Fensterraender (gerade Linien, keine Treppen) und sind weich
    /// ausgeblendet (Halbschatten, der mit der Entfernung breiter wird). Nach hinten und zu den Seiten des Sichtfelds
    /// laeuft der Blick sanft ins Dunkel aus.
    ///
    /// Technik: Ein Masken-Mesh (Raum + Blick nach draussen inkl. Halbschatten) setzt ein Stencil-Bit, ein schwarzes
    /// Rechteck deckt alles ohne Bit ab. Ein zweites Mesh legt die weichen Verlaeufe darueber.
    /// Alles liegt ganz oben in der Sortierung, das UI (Overlay-Canvas) bleibt darueber.
    /// </summary>
    [RequireComponent(typeof(PlayerController))]
    public class PlayerVision : MonoBehaviour
    {
        [Header("Blickfeld")]
        [Tooltip("Sichtfeld in Grad (Mensch ca. 150-180)")]
        [SerializeField, Range(20f, 220f)] float coneAngle = 160f;
        [Tooltip("Am Rand des Sichtfelds wird ueber so viele Grad weich abgedunkelt")]
        [SerializeField, Range(1f, 80f)] float edgeSoftness = 35f;
        [Tooltip("Wie weit man aus dem Fenster sieht (Units = Kacheln, ab dem Auge). Dahinter ist es dunkel")]
        [SerializeField] float range = 11f;
        [Tooltip("Sekunden, bis der Blick einer neuen Blickrichtung gefolgt ist")]
        [SerializeField] float turnSmoothTime = 0.15f;
        [Tooltip("Augenhoehe ueber dem Pivot (Fuesse). Klein halten, sonst liegt das Auge vor dem Fenster schon in der Wand")]
        [SerializeField] Vector2 eyeOffset = new Vector2(0f, 0.1f);
        [Tooltip("Draussen blockieren diese Layer zusaetzlich die Sicht (z. B. hohe Mauern). Standard: nichts")]
        [SerializeField] LayerMask outsideBlockers = 0;

        [Header("Weichheit")]
        [Tooltip("Breite des Halbschattens an den Fensterkanten direkt hinter der Wand ...")]
        [SerializeField] float penumbraNear = 0.3f;
        [Tooltip("... und wie viel er pro Unit Entfernung breiter wird")]
        [SerializeField] float penumbraGrowth = 0.2f;
        [Tooltip("Ab welchem Anteil der Sichtweite es dunkler wird (0 = sofort, 1 = erst am Ende)")]
        [SerializeField, Range(0f, 1f)] float fadeStart = 0.25f;
        [Tooltip("Strahlen pro Grad (mehr = rundere Verlaeufe, die Kanten sind unabhaengig davon exakt)")]
        [SerializeField, Range(0.25f, 4f)] float raysPerDegree = 1f;

        [Header("Darstellung")]
        [SerializeField] Material maskMaterial;
        [SerializeField] Material darknessMaterial;
        [SerializeField] Material falloffMaterial;
        [SerializeField, Range(0f, 1f)] float darkness = 1f;
        [SerializeField] float fadeTime = 0.3f;
        [SerializeField] string sortingLayer = "Default";
        [SerializeField] int sortingOrder = 32000;

        const int Samples = 4; // Punkte je Strahl fuer den Verlauf nach hinten

        struct Sight
        {
            public Vector2 dir, exit;
            public float reach;  // sichtbare Weite hinter der Aussenkante
            public float weight; // 1 = mitten im Sichtfeld, 0 = am Rand
            public bool through;
        }

        PlayerController controller;
        Camera cam;
        Interior current, drawn;
        float visibility;
        float angle = -90f;
        float angleVelocity;
        bool angleKnown;

        Mesh maskMesh, darkMesh, falloffMesh;
        MeshRenderer maskRenderer, darkRenderer, falloffRenderer;
        Transform root;

        readonly List<float> angles = new List<float>();
        readonly List<Sight> rays = new List<Sight>();
        readonly List<Vector3> verts = new List<Vector3>();
        readonly List<int> tris = new List<int>();
        readonly List<Vector3> fVerts = new List<Vector3>();
        readonly List<Color> fColors = new List<Color>();
        readonly List<int> fTris = new List<int>();
        static readonly Color[] QuadColors = { Color.white, Color.white, Color.white, Color.white };
        static readonly int[] QuadTris = { 0, 2, 1, 0, 3, 2 };
        readonly Vector3[] darkVerts = new Vector3[4];

        /// <summary>Innenraum, in dem der Spieler gerade steht (null = draussen).</summary>
        public Interior Current => current;
        /// <summary>0 = kein Effekt, 1 = voll aktiv (blendet beim Betreten/Verlassen weich).</summary>
        public float Visibility => visibility;

        void Awake()
        {
            controller = GetComponent<PlayerController>();
            // Eigene Kopien: die Farbe (Ausblenden) wird zur Laufzeit veraendert, das Asset soll unberuehrt bleiben
            maskMaterial = maskMaterial != null ? new Material(maskMaterial) : new Material(Shader.Find("Nightward/Vision Mask"));
            darknessMaterial = darknessMaterial != null ? new Material(darknessMaterial) : new Material(Shader.Find("Nightward/Vision Darkness"));
            if (falloffMaterial != null) falloffMaterial = new Material(falloffMaterial);
            else
            {
                falloffMaterial = new Material(Shader.Find("Nightward/Vision Darkness"));
                falloffMaterial.SetFloat("_StencilComp", (float)UnityEngine.Rendering.CompareFunction.Always);
            }

            root = new GameObject("Sicht").transform;
            root.SetParent(transform, false);
            maskRenderer = MakeLayer("Maske", maskMaterial, sortingOrder, out maskMesh);
            darkRenderer = MakeLayer("Dunkelheit", darknessMaterial, sortingOrder + 1, out darkMesh);
            falloffRenderer = MakeLayer("Verlauf", falloffMaterial, sortingOrder + 2, out falloffMesh);
            SetVisible(false);
        }

        MeshRenderer MakeLayer(string name, Material mat, int order, out Mesh mesh)
        {
            var go = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer));
            go.transform.SetParent(root, false);
            mesh = new Mesh { name = "Sicht_" + name };
            mesh.MarkDynamic();
            go.GetComponent<MeshFilter>().sharedMesh = mesh;
            var r = go.GetComponent<MeshRenderer>();
            r.sharedMaterial = mat;
            r.sortingLayerName = sortingLayer;
            r.sortingOrder = order;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
            return r;
        }

        void OnDestroy()
        {
            Destroy(maskMesh);
            Destroy(darkMesh);
            Destroy(falloffMesh);
            Destroy(maskMaterial);
            Destroy(darknessMaterial);
            Destroy(falloffMaterial);
        }

        void SetVisible(bool on)
        {
            maskRenderer.enabled = darkRenderer.enabled = falloffRenderer.enabled = on;
        }

        void LateUpdate()
        {
            Vector2 feet = transform.position;
            var inside = FindInterior(feet);
            if (inside != current)
            {
                if (current != null) current.SetPlayerInside(false);
                if (inside != null) inside.SetPlayerInside(true);
                current = inside;
            }
            // Beim Verlassen wird der alte Raum noch gezeichnet, waehrend die Dunkelheit ausblendet
            if (current != null) drawn = current;

            visibility = Mathf.MoveTowards(visibility, current != null ? 1f : 0f, Time.deltaTime / Mathf.Max(0.01f, fadeTime));
            if (visibility <= 0f || drawn == null)
            {
                if (visibility <= 0f) drawn = null;
                SetVisible(false);
                return;
            }

            UpdateAngle();
            if (cam == null) cam = Camera.main;
            root.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            Build(drawn, feet + eyeOffset);
            SetVisible(true);
        }

        static Interior FindInterior(Vector2 p)
        {
            var all = Interior.All;
            for (int i = 0; i < all.Count; i++)
                if (all[i] != null && all[i].Contains(p)) return all[i];
            return null;
        }

        void UpdateAngle()
        {
            Vector2 f = controller.FacingVector;
            float target = Mathf.Atan2(f.y, f.x) * Mathf.Rad2Deg;
            if (!angleKnown) { angle = target; angleKnown = true; }
            angle = Mathf.SmoothDampAngle(angle, target, ref angleVelocity, turnSmoothTime);
        }

        // ------------------------------------------------------------------ Meshes

        void Build(Interior room, Vector2 eye)
        {
            verts.Clear(); tris.Clear(); fVerts.Clear(); fColors.Clear(); fTris.Clear();

            // 1) Raum komplett sichtbar
            foreach (var p in room.Outline) verts.Add(p);
            tris.AddRange(room.Triangles);

            // 2) Blick nach draussen: Strahlen gleichmaessig plus exakt an jeder Fensterkante, dann zusammenhaengende Faecher
            CollectAngles(room, eye);
            rays.Clear();
            float half = coneAngle * 0.5f;
            foreach (float a in angles)
            {
                float rad = a * Mathf.Deg2Rad;
                var r = new Sight { dir = new Vector2(Mathf.Cos(rad), Mathf.Sin(rad)) };
                r.through = Cast(room, eye, r.dir, out float exitDist, out r.reach, out float grazing);
                r.exit = eye + r.dir * exitDist;
                float off = Mathf.Abs(Mathf.DeltaAngle(angle, a));
                float w = Mathf.Clamp01((half - off) / edgeSoftness);
                r.weight = w * w * (3f - 2f * w) * grazing;
                rays.Add(r);
            }
            for (int i = 0; i < rays.Count; i++)
            {
                if (!rays[i].through) continue;
                int start = i;
                while (i + 1 < rays.Count && rays[i + 1].through) i++;
                AddFan(start, i);
            }

            Apply(maskMesh, verts, null, tris);
            Apply(falloffMesh, fVerts, fColors, fTris);
            BuildDarkness();

            darknessMaterial.color = new Color(0f, 0f, 0f, darkness * visibility);
            falloffMaterial.color = new Color(0f, 0f, 0f, visibility);
        }

        void CollectAngles(Interior room, Vector2 eye)
        {
            angles.Clear();
            float half = coneAngle * 0.5f;
            int n = Mathf.Max(2, Mathf.CeilToInt(coneAngle * raysPerDegree));
            for (int i = 0; i <= n; i++) angles.Add(angle - half + coneAngle * i / n);
            // Exakte Kanten: je Fensterkante ein Strahl knapp davor und knapp dahinter
            foreach (var o in room.Openings)
            {
                if (o == null || !o.Open) continue;
                AddEdgeAngles(eye, o.ApertureA);
                AddEdgeAngles(eye, o.ApertureB);
            }
            float from = angle - half;
            angles.Sort((x, y) => Mathf.DeltaAngle(from, x).CompareTo(Mathf.DeltaAngle(from, y)));
        }

        void AddEdgeAngles(Vector2 eye, Vector2 corner)
        {
            Vector2 d = corner - eye;
            if (d.sqrMagnitude < 0.0001f) return;
            float a = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
            float delta = Mathf.DeltaAngle(angle, a);
            if (Mathf.Abs(delta) > coneAngle * 0.5f) return;
            angles.Add(angle + delta - 0.02f);
            angles.Add(angle + delta + 0.02f);
        }

        /// <summary>Strahl vom Auge. exitDist = Abstand bis zur Aussenkante des Raums, reach = Sichtweite dahinter.
        /// true, wenn er vorher durch eine offene Oeffnung (Apertur an der Wandkante) geht, also nach draussen sieht.</summary>
        bool Cast(Interior room, Vector2 eye, Vector2 dir, out float exitDist, out float reach, out float grazing)
        {
            var outline = room.Outline;
            exitDist = reach = 0f;
            grazing = 1f;
            float best = float.MaxValue;
            for (int i = 0; i < outline.Length; i++)
                if (RaySegment(eye, dir, outline[i], outline[(i + 1) % outline.Length], out float t) && t < best) best = t;
            if (best == float.MaxValue) return false;
            exitDist = best;
            if (best >= range) return false;

            bool through = false;
            foreach (var o in room.Openings)
            {
                if (o == null || !o.Open || !o.isActiveAndEnabled) continue;
                // Auge steht schon in der Oeffnung (z. B. mitten in der Tuer): jede Richtung nach draussen ist frei
                if (o.Contains(eye)) { through = true; break; }
                if (!RaySegment(eye, dir, o.ApertureA, o.ApertureB, out float t) || t > best + 0.01f) continue;
                // Ganz flach durchs Fenster sieht man in echt nicht (die Laibung verdeckt es): weich ausblenden
                float g = Mathf.Clamp01((Vector2.Dot(dir, o.Outward) - 0.2f) / 0.3f);
                g = g * g * (3f - 2f * g);
                if (g <= 0f) continue;
                grazing = g;
                through = true;
                break;
            }
            if (!through) return false;

            reach = range - best;
            if (outsideBlockers != 0)
            {
                var hit = Physics2D.Raycast(eye + dir * (best + 0.02f), dir, reach, outsideBlockers);
                if (hit.collider != null) reach = hit.distance + 0.02f;
            }
            return true;
        }

        static bool RaySegment(Vector2 o, Vector2 d, Vector2 a, Vector2 b, out float t)
        {
            t = 0f;
            Vector2 e = b - a;
            float denom = d.x * e.y - d.y * e.x;
            if (Mathf.Abs(denom) < 1e-6f) return false;
            Vector2 ao = a - o;
            t = (ao.x * e.y - ao.y * e.x) / denom;
            float u = (ao.x * d.y - ao.y * d.x) / denom;
            return t > 1e-4f && u >= 0f && u <= 1f;
        }

        // Punkt k (0..Samples-1) entlang eines Strahls hinter der Aussenkante
        static Vector2 Point(Sight r, int k) => r.exit + r.dir * (r.reach * k / (Samples - 1));

        // Dunkelheit an Punkt k: 0 = klar, 1 = schwarz. Erst klar, dann weich ins Dunkel, am Rand des Sichtfelds dunkler
        float Dark(Sight r, int k)
        {
            float t = (float)k / (Samples - 1);
            float fade = Mathf.Clamp01((t - fadeStart) / Mathf.Max(0.01f, 1f - fadeStart));
            float bright = 1f - fade * fade * (3f - 2f * fade);
            return 1f - r.weight * bright;
        }

        /// <summary>Ein zusammenhaengender Blick durch eine Oeffnung (Strahlen first..last) plus Halbschatten an beiden Seiten.</summary>
        void AddFan(int first, int last)
        {
            for (int i = first; i < last; i++) AddStrip(rays[i], rays[i + 1]);
            AddPenumbra(rays[first], -1f);
            AddPenumbra(rays[last], 1f);
        }

        void AddStrip(Sight a, Sight b)
        {
            int mv = verts.Count, fv = fVerts.Count;
            for (int k = 0; k < Samples; k++)
            {
                Vector2 pa = Point(a, k), pb = Point(b, k);
                verts.Add(pa); verts.Add(pb);
                fVerts.Add(pa); fVerts.Add(pb);
                fColors.Add(new Color(0f, 0f, 0f, Dark(a, k)));
                fColors.Add(new Color(0f, 0f, 0f, Dark(b, k)));
            }
            AddLadder(mv, fv);
        }

        // Halbschatten: aussen neben der Randkante ein Streifen, der von "wie die Kante" nach schwarz verlaeuft.
        // side: -1 = Richtung kleinerer Winkel (im Uhrzeigersinn), +1 = groesserer Winkel
        void AddPenumbra(Sight r, float side)
        {
            Vector2 n = side > 0f ? new Vector2(-r.dir.y, r.dir.x) : new Vector2(r.dir.y, -r.dir.x);
            int mv = verts.Count, fv = fVerts.Count;
            for (int k = 0; k < Samples; k++)
            {
                Vector2 inner = Point(r, k);
                Vector2 outer = inner + n * (penumbraNear + penumbraGrowth * r.reach * k / (Samples - 1));
                verts.Add(inner); verts.Add(outer);
                fVerts.Add(inner); fVerts.Add(outer);
                fColors.Add(new Color(0f, 0f, 0f, Dark(r, k)));
                fColors.Add(new Color(0f, 0f, 0f, 1f));
            }
            AddLadder(mv, fv);
        }

        // Dreiecke fuer eine "Leiter" aus Samples Punktpaaren (in Maske und Verlauf)
        void AddLadder(int mv, int fv)
        {
            for (int k = 0; k < Samples - 1; k++)
            {
                int i0 = 2 * k, i1 = 2 * k + 1, i2 = 2 * k + 2, i3 = 2 * k + 3;
                tris.Add(mv + i0); tris.Add(mv + i2); tris.Add(mv + i1);
                tris.Add(mv + i1); tris.Add(mv + i2); tris.Add(mv + i3);
                fTris.Add(fv + i0); fTris.Add(fv + i2); fTris.Add(fv + i1);
                fTris.Add(fv + i1); fTris.Add(fv + i2); fTris.Add(fv + i3);
            }
        }

        // Schwarzes Rechteck ueber den ganzen Kamerabereich (mit Rand gegen Wackeln der Kamera)
        void BuildDarkness()
        {
            Vector3 c = cam != null ? cam.transform.position : transform.position;
            float h = cam != null && cam.orthographic ? cam.orthographicSize + 2f : 20f;
            float w = cam != null ? h * cam.aspect + 2f : 30f;
            darkVerts[0] = new Vector3(c.x - w, c.y - h);
            darkVerts[1] = new Vector3(c.x + w, c.y - h);
            darkVerts[2] = new Vector3(c.x + w, c.y + h);
            darkVerts[3] = new Vector3(c.x - w, c.y + h);
            darkMesh.Clear();
            darkMesh.vertices = darkVerts;
            darkMesh.colors = QuadColors;
            darkMesh.triangles = QuadTris;
            darkMesh.bounds = new Bounds(new Vector3(c.x, c.y, 0f), new Vector3(w * 2f, h * 2f, 10f));
        }

        static void Apply(Mesh mesh, List<Vector3> v, List<Color> colors, List<int> t)
        {
            mesh.Clear();
            mesh.SetVertices(v);
            if (colors != null) mesh.SetColors(colors);
            mesh.SetTriangles(t, 0);
            mesh.RecalculateBounds();
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(1f, 0.82f, 0.48f, 0.5f);
            Vector2 eye = (Vector2)transform.position + eyeOffset;
            float a = (angleKnown ? angle : -90f) * Mathf.Deg2Rad, half = coneAngle * 0.5f * Mathf.Deg2Rad;
            Gizmos.DrawLine(eye, eye + new Vector2(Mathf.Cos(a - half), Mathf.Sin(a - half)) * range);
            Gizmos.DrawLine(eye, eye + new Vector2(Mathf.Cos(a + half), Mathf.Sin(a + half)) * range);
        }
    }
}
