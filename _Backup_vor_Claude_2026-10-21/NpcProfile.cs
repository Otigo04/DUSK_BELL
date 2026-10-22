using UnityEngine;

namespace Nightward.Dialogue
{
    public enum NpcGender { Maennlich, Weiblich, Divers }

    /// <summary>
    /// Wer ein NPC ist: ID fuer Beziehung/Flags, Anzeigename, eigene Namensfarbe (UI-Cheatsheet: nie Monsterfarbe)
    /// und die Portraet-Frames fuer die Dialogbox. Ein Asset pro NPC.
    /// </summary>
    [CreateAssetMenu(menuName = "Nightward/NPC-Profil", fileName = "NpcProfile_")]
    public class NpcProfile : ScriptableObject
    {
        [Tooltip("Eindeutig und unveraenderlich, z. B. 'ilhan'. Schluessel fuer Beziehung und Flags")]
        public string id;
        public string displayName;
        public Color nameColor = new Color32(0xff, 0xd2, 0x7a, 0xff);

        [Header("Beziehung")]
        [Tooltip("Fuer die Stufennamen (Guter Freund / Gute Freundin)")]
        public NpcGender gender = NpcGender.Maennlich;
        [Tooltip("Kann eine Romanze werden (z. B. Date ab dem Mindestwert in RelationshipTiers)")]
        public bool romanceable;
        [Tooltip("Startwert der Beziehung zum Spieler, falls man sich schon kennt")]
        [Range(Relationships.Min, Relationships.Max)] public int startRelationship;

        [Header("Portraet (Kopf und Oberkoerper)")]
        public Sprite portraitIdle;
        [Tooltip("Mundstellungen beim Sprechen, z. B. halb offen, offen")]
        public Sprite[] portraitTalk = new Sprite[0];
        public Sprite portraitBlink;
        [Tooltip("Mundwechsel pro Sekunde")]
        public float talkFps = 10f;
    }
}
