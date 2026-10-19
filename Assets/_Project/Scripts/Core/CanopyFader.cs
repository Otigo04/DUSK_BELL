using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Nightward.Core
{
    /// <summary>
    /// Blendet Baumkronen, die die Spielfigur verdecken, weich aus.
    /// Eine Krone ist ein hohes Tile (Pivot unten links); sie verdeckt Zellen oberhalb ihrer Basiszelle.
    /// </summary>
    public class CanopyFader : MonoBehaviour
    {
        [SerializeField] Tilemap crowns;
        [SerializeField] Transform target;
        [SerializeField, Range(0f, 1f)] float fadedAlpha = 0.3f;
        [Tooltip("Basiszellen links/rechts der Figur, deren Krone sie noch verdecken kann")]
        [SerializeField] int searchLeft = 2;
        [SerializeField] int searchRight = 1;
        [Tooltip("Wie viele Zellen unterhalb der Figur nach Kronen gesucht wird (Baumhoehe)")]
        [SerializeField] int searchBelow = 4;
        [SerializeField] float fadeSpeed = 4f;

        readonly Dictionary<Vector3Int, float> alpha = new Dictionary<Vector3Int, float>();
        readonly HashSet<Vector3Int> wanted = new HashSet<Vector3Int>();
        readonly List<Vector3Int> keys = new List<Vector3Int>();

        void Awake()
        {
            if (crowns == null) crowns = GetComponent<Tilemap>();
            // Tile-Farben sind standardmaessig gesperrt
            foreach (var pos in crowns.cellBounds.allPositionsWithin)
                if (crowns.HasTile(pos)) crowns.SetTileFlags(pos, TileFlags.None);
        }

        void Update()
        {
            if (target == null)
            {
                var p = GameObject.FindWithTag("Player");
                if (p == null) return;
                target = p.transform;
            }

            var c = crowns.WorldToCell(target.position);
            wanted.Clear();
            for (int dx = -searchLeft; dx <= searchRight; dx++)
                for (int dy = -searchBelow; dy <= 0; dy++)
                {
                    var cell = new Vector3Int(c.x + dx, c.y + dy, 0);
                    if (!crowns.HasTile(cell)) continue;
                    wanted.Add(cell);
                    if (!alpha.ContainsKey(cell)) alpha[cell] = 1f;
                }

            keys.Clear();
            keys.AddRange(alpha.Keys);
            foreach (var cell in keys)
            {
                float goal = wanted.Contains(cell) ? fadedAlpha : 1f;
                float a = Mathf.MoveTowards(alpha[cell], goal, fadeSpeed * Time.deltaTime);
                crowns.SetColor(cell, new Color(1f, 1f, 1f, a));
                if (a >= 1f && !wanted.Contains(cell)) alpha.Remove(cell);
                else alpha[cell] = a;
            }
        }
    }
}
