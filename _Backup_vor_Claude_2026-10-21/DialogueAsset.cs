using System;
using System.Collections.Generic;
using UnityEngine;

namespace Nightward.Dialogue
{
    public enum Speaker { Npc, Spieler, Erzaehler }

    /// <summary>Antwortmoeglichkeit des Spielers. Jede Antwort kann die Beziehung zum NPC aendern.</summary>
    [Serializable]
    public class DialogueChoice
    {
        [TextArea(1, 2)] public string text;
        [Tooltip("ID des Knotens, mit dem der NPC reagiert. Leer = Gespraech endet")]
        public string next;
        [Tooltip("Beziehungsaenderung zum NPC, z. B. +1 freundlich, -2 unhoeflich")]
        public int relationship;
        [Tooltip("Optional: Flag, das bei dieser Antwort gesetzt wird")]
        public string setFlag;

        [Header("Nur anzeigen, wenn ...")]
        public int minRelationship = Relationships.Min;
        public string requireFlag;
    }

    [Serializable]
    public class DialogueNode
    {
        public string id;
        public Speaker speaker;
        [TextArea(2, 5)] public string text;
        [Tooltip("Beziehungsaenderung beim Erreichen dieses Knotens (z. B. Reaktion des NPCs)")]
        public int relationship;
        public string setFlag;
        [Tooltip("Kein automatischer Abschied: das Gespraech endet nach diesem Knoten ohne Antwortwahl (z. B. wenn der NPC abbricht)")]
        public bool noFarewell;
        [Tooltip("Folgeknoten ohne Auswahl. Leer und keine Antworten = Gespraech endet")]
        public string next;
        public List<DialogueChoice> choices = new List<DialogueChoice>();
    }

    /// <summary>
    /// Ein Gespraech als Liste von Knoten (Text + optionale Antworten). Knoten verweisen per ID aufeinander.
    /// Im Text wird {name} durch den Namen des NPCs ersetzt.
    /// </summary>
    [CreateAssetMenu(menuName = "Nightward/Dialog", fileName = "Dialog_")]
    public class DialogueAsset : ScriptableObject
    {
        [Tooltip("ID des ersten Knotens. Leer = erster Eintrag der Liste")]
        public string startNode;
        public List<DialogueNode> nodes = new List<DialogueNode>();

        public DialogueNode Start => Find(startNode) ?? (nodes.Count > 0 ? nodes[0] : null);

        public DialogueNode Find(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            foreach (var n in nodes) if (n.id == id) return n;
            Debug.LogWarning($"[Dialog] Knoten '{id}' fehlt in {name}.", this);
            return null;
        }
    }
}
