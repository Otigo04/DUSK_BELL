using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Survival
{
    /// <summary>
    /// Bereich (Trigger-Collider), der den Spieler beeinflusst, solange er darin steht: Umwelt-Flags (Feuer, Innenraum, Licht,
    /// Dickicht) und/oder beliebige Effekte, z. B. "Sanity -4 pro Stunde" fuer einen unheimlichen Ort.
    /// Einfach ein leeres Objekt mit Collider2D (Is Trigger) und diesem Skript anlegen.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class SurvivalZone : MonoBehaviour
    {
        [Header("Umwelt")]
        [SerializeField] bool indoors;
        [SerializeField] bool nearFire;
        [SerializeField] bool lightIsland;
        [Tooltip("Dickicht/Unterholz: weite Sprints senken das Maximum der Ausdauer")]
        [SerializeField] bool thicket;

        [Header("Eigene Effekte (gelten, solange der Spieler im Bereich steht)")]
        [SerializeField] List<Effect> effects = new List<Effect>();

        public bool Indoors => indoors;
        public bool NearFire => nearFire;
        public bool LightIsland => lightIsland;
        public bool Thicket => thicket;
        public List<Effect> Effects => effects;

        void Reset()
        {
            var c = GetComponent<Collider2D>();
            if (c != null) c.isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            var p = other.GetComponentInParent<PlayerSurvival>();
            if (p != null) p.EnterZone(this);
        }

        void OnTriggerExit2D(Collider2D other)
        {
            var p = other.GetComponentInParent<PlayerSurvival>();
            if (p != null) p.ExitZone(this);
        }

        void OnDisable()
        {
            if (PlayerSurvival.Instance != null) PlayerSurvival.Instance.ExitZone(this, true);
        }
    }
}
