using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Items
{
    /// <summary>
    /// Marker in der Welt, an dem beim Start per Zufall Beute erscheint (Roguelike: jeder Durchgang liegt etwas anderes).
    /// Mit Wahrscheinlichkeit spawnChance entsteht entweder ein Behaelter (zufaellig gewaehlt aus den Optionen, nach Gewicht)
    /// oder lose Gegenstaende aus einer Beute-Tabelle, die um den Punkt verstreut liegen.
    /// </summary>
    public class LootSpawner : MonoBehaviour
    {
        public enum Kind { Container, GroundItems }

        [Serializable]
        public class Option
        {
            public GameObject prefab;
            [Min(0f)] public float weight = 1f;
        }

        [SerializeField] Kind kind = Kind.Container;
        [Range(0f, 1f)] [SerializeField] float spawnChance = 0.6f;
        [Tooltip("Gewuerfelt beim Start der Szene. Aus = nur per Spawn() von Hand")]
        [SerializeField] bool spawnOnStart = true;

        [Header("Behaelter")]
        [SerializeField] List<Option> containers = new List<Option>();

        [Header("Lose Gegenstaende")]
        [SerializeField] LootTable groundTable;
        [SerializeField, Range(0f, 2f)] float groundLuck;
        [Tooltip("Streuung der Gegenstaende um den Punkt in Units")]
        [SerializeField] float scatterRadius = 0.7f;

        /// <summary>Was zuletzt erschienen ist (null = nichts gewuerfelt oder nichts gefallen).</summary>
        public GameObject Spawned { get; private set; }

        void Start()
        {
            if (spawnOnStart) Spawn();
        }

        /// <summary>Wuerfelt jetzt. Gibt den neuen Behaelter zurueck (bei losen Gegenstaenden einen Sammelknoten) oder null.</summary>
        public GameObject Spawn()
        {
            if (Spawned != null) return Spawned;
            var rng = LootTable.NewRng();
            if (rng.NextDouble() > spawnChance) return null;

            Spawned = kind == Kind.Container ? SpawnContainer(rng) : SpawnGround(rng);
            return Spawned;
        }

        GameObject SpawnContainer(System.Random rng)
        {
            float total = 0f;
            foreach (var o in containers) if (o.prefab != null) total += o.weight;
            if (total <= 0f) return null;
            float r = (float)rng.NextDouble() * total;
            foreach (var o in containers)
            {
                if (o.prefab == null) continue;
                r -= o.weight;
                if (r < 0f) return Instantiate(o.prefab, transform.position, Quaternion.identity, transform.parent);
            }
            return null;
        }

        GameObject SpawnGround(System.Random rng)
        {
            if (groundTable == null) return null;
            var root = new GameObject(name + "_Funde");
            root.transform.SetParent(transform.parent, false);
            root.transform.position = transform.position;
            var player = PlayerInventory.Instance;
            foreach (var stack in groundTable.Roll(rng, groundLuck))
            {
                double angle = rng.NextDouble() * Math.PI * 2.0;
                float dist = scatterRadius * Mathf.Sqrt((float)rng.NextDouble());
                Vector3 at = transform.position + new Vector3(Mathf.Cos((float)angle), Mathf.Sin((float)angle) * 0.6f, 0f) * dist;
                var p = ItemPickup.Spawn(stack, at, Vector2.zero, player);
                p.transform.SetParent(root.transform, true);
            }
            return root;
        }

        void OnDrawGizmos()
        {
            Gizmos.color = kind == Kind.Container ? new Color(1f, 0.75f, 0.2f, 0.9f) : new Color(0.5f, 0.9f, 1f, 0.9f);
            Gizmos.DrawWireCube(transform.position + Vector3.up * 0.4f, new Vector3(0.8f, 0.8f, 0f));
            if (kind == Kind.GroundItems) Gizmos.DrawWireSphere(transform.position, scatterRadius);
        }
    }
}
