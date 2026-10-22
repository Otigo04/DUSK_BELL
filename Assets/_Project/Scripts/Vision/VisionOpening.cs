using UnityEngine;

namespace Nightward.Vision
{
    /// <summary>
    /// Fenster, Tuer oder Durchgang in der Aussenwand eines Innenraums: Hier geht der Blick nach draussen.
    /// Die Box (Trigger) liegt ueber dem Fenster bzw. der Tuer und reicht bis ueber die Aussenkante des Raums.
    /// Geschlossen (z. B. Vorhang zu, Tuer zu, Fensterladen) laesst sie keinen Blick durch.
    ///
    /// Gesehen wird wie durch eine duenne Wand: Die eigentliche Oeffnung (Apertur) liegt dort, wo die Wand auf den Boden trifft.
    /// Sie wird beim Start automatisch gefunden (von der Box aus Richtung Raummitte bis zur ersten Stelle ohne Wand-Collider).
    /// Steht man direkt davor, sieht man daher fast die ganze Seite draussen, weiter weg nur noch einen schmalen Ausschnitt.
    /// </summary>
    [RequireComponent(typeof(BoxCollider2D))]
    public class VisionOpening : MonoBehaviour
    {
        [SerializeField] bool open = true;
        [Tooltip("Aus = Oeffnung an der raumseitigen Kante der Box statt an der automatisch gefundenen Wandkante")]
        [SerializeField] bool findWallBase = true;
        [Tooltip("So weit wird hoechstens Richtung Raummitte nach der Wandkante gesucht")]
        [SerializeField] float maxWallDepth = 4f;

        BoxCollider2D box;
        Vector2 apertureA, apertureB, outward = Vector2.up;
        bool hasAperture;

        public bool Open { get => open; set => open = value; }
        public BoxCollider2D Box => box != null ? box : box = GetComponent<BoxCollider2D>();
        /// <summary>Linie, durch die der Blick muss (Weltkoordinaten).</summary>
        public Vector2 ApertureA => apertureA;
        public Vector2 ApertureB => apertureB;
        /// <summary>Richtung nach draussen (senkrecht zur Wand).</summary>
        public Vector2 Outward => outward;

        void Reset() => GetComponent<BoxCollider2D>().isTrigger = true;

        public bool Contains(Vector2 world) => Box.OverlapPoint(world);

        /// <summary>Die vier Ecken in Weltkoordinaten.</summary>
        public void Corners(Vector2[] into)
        {
            var b = Box;
            Vector2 h = b.size * 0.5f;
            var t = transform;
            into[0] = t.TransformPoint(b.offset + new Vector2(-h.x, -h.y));
            into[1] = t.TransformPoint(b.offset + new Vector2(h.x, -h.y));
            into[2] = t.TransformPoint(b.offset + new Vector2(h.x, h.y));
            into[3] = t.TransformPoint(b.offset + new Vector2(-h.x, h.y));
        }

        /// <summary>Apertur bestimmen. roomCenter: Mitte des Innenraums (gibt die Richtung nach innen vor).</summary>
        public void ComputeAperture(Vector2 roomCenter)
        {
            var b = Box;
            Bounds bounds = b.bounds;
            Vector2 c = bounds.center, ext = bounds.extents;
            Vector2 toRoom = roomCenter - c;
            // Wand liegt waagrecht (Nord/Sued) oder senkrecht (Ost/West): nach innen entlang der groesseren Achse
            bool vertical = Mathf.Abs(toRoom.y) >= Mathf.Abs(toRoom.x);
            Vector2 inward = vertical ? new Vector2(0f, Mathf.Sign(toRoom.y)) : new Vector2(Mathf.Sign(toRoom.x), 0f);
            Vector2 across = vertical ? new Vector2(ext.x, 0f) : new Vector2(0f, ext.y);
            float innerFace = vertical ? ext.y : ext.x;

            float depth = innerFace;
            if (findWallBase)
            {
                // Von der Mitte der Box Richtung Raum: erst in die Wand hinein (die Box kann auch ueber der Mauerkrone beginnen),
                // dann bis zur ersten Stelle ohne Wand-Collider. Tueren haben keine Wand: dann gilt die raumseitige Boxkante
                const float step = 1f / 16f;
                bool inWall = false;
                for (float d = 0f; d <= innerFace + maxWallDepth; d += step)
                {
                    bool wall = IsWall(c + inward * d);
                    if (wall) inWall = true;
                    else if (inWall) { depth = d; break; }
                }
            }
            Vector2 mid = c + inward * depth;
            apertureA = mid - across;
            apertureB = mid + across;
            outward = -inward;
            hasAperture = true;
        }

        static bool IsWall(Vector2 p)
        {
            foreach (var col in Physics2D.OverlapPointAll(p))
            {
                if (col.isTrigger) continue;
                var rb = col.attachedRigidbody;
                if (rb == null || rb.bodyType == RigidbodyType2D.Static) return true;
            }
            return false;
        }

        void OnDrawGizmos()
        {
            var b = Box;
            if (b == null) return;
            Gizmos.color = open ? new Color(0.43f, 0.83f, 0.9f, 0.6f) : new Color(0.84f, 0.29f, 0.42f, 0.6f);
            var m = Gizmos.matrix;
            Gizmos.matrix = transform.localToWorldMatrix;
            Gizmos.DrawWireCube(b.offset, b.size);
            Gizmos.matrix = m;
            if (hasAperture)
            {
                Gizmos.color = new Color(1f, 0.82f, 0.48f, 1f);
                Gizmos.DrawLine(apertureA, apertureB);
            }
        }
    }
}
