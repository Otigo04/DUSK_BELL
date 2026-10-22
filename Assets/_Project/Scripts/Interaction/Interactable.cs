using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Interaction
{
    /// <summary>Taste zum Ausloesen. Steuerung laut Opening-Spec: E spricht mit Dorfbewohnern, F benutzt Objekte.</summary>
    public enum InteractKey { E, F }

    /// <summary>
    /// Alles, was der Spieler mit E oder F benutzen kann (NPC ansprechen, Tuer, Truhe ...).
    /// Unterklassen entscheiden in CanInteract, ob es gerade geht, und loesen in Interact die Aktion aus.
    /// </summary>
    public abstract class Interactable : MonoBehaviour
    {
        public static readonly List<Interactable> All = new List<Interactable>();

        [Tooltip("Kurzer Hinweis, was passiert, z. B. 'Reden'")]
        [SerializeField] string prompt = "Reden";
        [Tooltip("Hoehe des Hinweis-Symbols ueber dem Pivot (bei Figuren: ueber dem Kopf)")]
        [SerializeField] float indicatorHeight = 1.7f;
        [Tooltip("E = mit Personen sprechen, F = Objekte benutzen")]
        [SerializeField] protected InteractKey key = InteractKey.E;

        [Tooltip("Eigene Reichweite in Units. 0 = Standardreichweite des Spielers")]
        [SerializeField] float reach = 0f;

        public float Reach => reach;
        public string Prompt { get => prompt; set => prompt = value; }
        public InteractKey Key => key;
        public virtual Vector3 IndicatorPosition => transform.position + Vector3.up * indicatorHeight;

        /// <summary>Text des Hinweises ("F - Pick up Bread"). Standard ist der feste Hinweis, Unterklassen koennen ihn je nach Zustand aendern.</summary>
        public virtual string PromptLabel => prompt;

        /// <summary>Farbe des Hinweistextes (z. B. Seltenheit). Color.clear = Standardfarbe.</summary>
        public virtual Color PromptTint => Color.clear;

        /// <summary>Zeigt der Hinweis-Kasten im Spiel (InteractHintUI) diesen Hinweis an? Standard nein: NPCs und Tueren haben ihre eigenen Symbole.</summary>
        public virtual bool ShowsPromptBox => false;

        protected virtual void OnEnable() => All.Add(this);
        protected virtual void OnDisable() => All.Remove(this);

        public virtual bool CanInteract(PlayerInteractor who) => isActiveAndEnabled;

        /// <summary>Ob das Hinweis-Symbol ueber dem Objekt erscheinen soll. Benutzbar bleibt es auch ohne Symbol (z. B. NPC ohne Neuigkeiten).</summary>
        public virtual bool ShowsIndicator(PlayerInteractor who) => true;
        public abstract void Interact(PlayerInteractor who);
    }
}
