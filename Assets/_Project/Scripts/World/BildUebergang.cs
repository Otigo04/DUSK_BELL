using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.World
{
    /// <summary>
    /// Bildschirm-Uebergang aus den Sheets in Art/VFX/Transitions (z. B. Transition_Tueren): Frames vorwaerts = Bild zu,
    /// in der Mitte passiert der Wechsel (Teleport, Szene laden ...), Frames rueckwaerts = Bild wieder auf.
    /// Liegt einmal in der Szene, eigenes Overlay-Canvas ueber allem.
    /// </summary>
    public class BildUebergang : MonoBehaviour
    {
        public static BildUebergang Instance { get; private set; }

        [SerializeField] Sprite[] frames = new Sprite[0];
        [SerializeField] float frameZeit = 0.04f;
        [Tooltip("Wie lange das Bild ganz zu bleibt")]
        [SerializeField] float halten = 0.12f;
        [SerializeField] Image bild;

        public bool Laeuft { get; private set; }

        void Awake()
        {
            Instance = this;
            if (bild != null) bild.enabled = false;
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        /// <summary>Bild zu, mitte() ausfuehren, Bild auf. Ohne Frames wird mitte() sofort ausgefuehrt.</summary>
        public void Spielen(Action mitte, Action fertig = null)
        {
            if (Laeuft) return;
            if (frames.Length == 0 || bild == null)
            {
                mitte?.Invoke();
                fertig?.Invoke();
                return;
            }
            StartCoroutine(Ablauf(mitte, fertig));
        }

        IEnumerator Ablauf(Action mitte, Action fertig)
        {
            Laeuft = true;
            bild.enabled = true;
            for (int i = 0; i < frames.Length; i++)
            {
                bild.sprite = frames[i];
                yield return new WaitForSecondsRealtime(frameZeit);
            }
            mitte?.Invoke();
            yield return new WaitForSecondsRealtime(halten);
            for (int i = frames.Length - 1; i >= 0; i--)
            {
                bild.sprite = frames[i];
                yield return new WaitForSecondsRealtime(frameZeit);
            }
            bild.enabled = false;
            Laeuft = false;
            fertig?.Invoke();
        }
    }
}
