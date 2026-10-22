using UnityEngine;
using UnityEngine.UI;

namespace Nightward.Dialogue
{
    /// <summary>
    /// Grosses Portraet in der Dialogbox: Mund bewegt sich, solange der NPC spricht (Text wird getippt),
    /// sonst Ruhebild mit gelegentlichem Blinzeln. Frames kommen aus dem NpcProfile.
    /// Mit SetExpression zeigt es statt dessen ein festes Ausdrucksbild (z. B. "tense"), ohne Mund- und Blinzelwechsel.
    /// </summary>
    [RequireComponent(typeof(Image))]
    public class PortraitAnimator : MonoBehaviour
    {
        [SerializeField] Vector2 blinkInterval = new Vector2(2f, 5f);
        [SerializeField] float blinkDuration = 0.12f;

        Image image;
        NpcProfile profile;
        float frameTimer;
        float blinkTimer;
        float blinkLeft;
        int lastTalkFrame = -1;
        Sprite expression;
        Sprite[] expressionTalk;

        public bool Talking { get; set; }

        void Awake() => image = GetComponent<Image>();

        public void SetProfile(NpcProfile p)
        {
            profile = p;
            expression = null;
            expressionTalk = null;
            Talking = false;
            blinkLeft = 0f;
            blinkTimer = Random.Range(blinkInterval.x, blinkInterval.y);
            image.sprite = p != null ? p.portraitIdle : null;
            image.enabled = image.sprite != null;
        }

        /// <summary>Festes Ausdrucksbild statt Ruhebild/Mund. null = wieder normal animieren.
        /// talkFrames: dasselbe Gesicht mit offenem Mund (siehe PortraitTalkFrames), damit der Ausdruck auch beim Sprechen "spricht".</summary>
        public void SetExpression(Sprite sprite, Sprite[] talkFrames = null)
        {
            expression = sprite;
            expressionTalk = sprite != null ? talkFrames : null;
            lastTalkFrame = -1;
            if (sprite != null) { image.sprite = sprite; image.enabled = true; }
            else if (profile != null) image.sprite = profile.portraitIdle;
        }

        void Update()
        {
            if (expression != null)
            {
                if (Talking && expressionTalk != null && expressionTalk.Length > 0) AnimateMouth(expression, expressionTalk);
                else { lastTalkFrame = -1; image.sprite = expression; }
                return;
            }
            if (profile == null || profile.portraitIdle == null) return;
            float dt = Time.unscaledDeltaTime;

            if (Talking && profile.portraitTalk.Length > 0)
            {
                AnimateMouth(profile.portraitIdle, profile.portraitTalk);
                return;
            }

            lastTalkFrame = -1;
            if (blinkLeft > 0f)
            {
                blinkLeft -= dt;
                if (blinkLeft <= 0f) image.sprite = profile.portraitIdle;
                return;
            }
            image.sprite = profile.portraitIdle;
            blinkTimer -= dt;
            if (blinkTimer <= 0f && profile.portraitBlink != null)
            {
                image.sprite = profile.portraitBlink;
                blinkLeft = blinkDuration;
                blinkTimer = Random.Range(blinkInterval.x, blinkInterval.y);
            }
        }

        /// <summary>Zufaellige Mundstellung (inkl. geschlossen = closed), nie zweimal dieselbe: wirkt wie echtes Sprechen.</summary>
        void AnimateMouth(Sprite closed, Sprite[] open)
        {
            frameTimer -= Time.unscaledDeltaTime;
            if (frameTimer > 0f) return;
            frameTimer = 1f / Mathf.Max(1f, profile != null ? profile.talkFps : 10f);
            int count = open.Length + 1;
            int next = Random.Range(0, count - 1);
            if (next >= lastTalkFrame) next++;
            lastTalkFrame = next;
            image.sprite = next == 0 ? closed : open[next - 1];
        }
    }
}
