using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>
    /// Wecklevel-Einblendung oben Mitte, nur kurz (Tagesbeginn), danach aus. Fuenf Balken: 1-2 gelb, 3 orange, 4-5 rot,
    /// darueber leer, Stufe 0 = alle leer. Steigt der Wert, leuchtet der neue Balken kurz auf.
    /// </summary>
    [RequireComponent(typeof(CanvasGroup))]
    public class NwWakeLevel : MonoBehaviour
    {
        [SerializeField] Image[] bars;
        [SerializeField] Image pulse;
        [SerializeField] Text valueText;
        [SerializeField] Sprite barEmpty;
        [SerializeField] Sprite barYellow;
        [SerializeField] Sprite barOrange;
        [SerializeField] Sprite barRed;
        [SerializeField] float showTime = 3.5f;
        [SerializeField] float fadeTime = 0.4f;
        [SerializeField] float pulseTime = 0.6f;

        CanvasGroup group;
        Coroutine routine;
        int lastLevel;

        void Awake()
        {
            group = GetComponent<CanvasGroup>();
            group.alpha = 0f;
            pulse.enabled = false;
        }

        Sprite BarSprite(int index) => index < 2 ? barYellow : index < 3 ? barOrange : barRed;

        /// <summary>Zeigt das Wecklevel (0-5) kurz an.</summary>
        public void Show(int level)
        {
            level = Mathf.Clamp(level, 0, bars.Length);
            for (int i = 0; i < bars.Length; i++) bars[i].sprite = i < level ? BarSprite(i) : barEmpty;
            valueText.text = level + " / " + bars.Length;
            valueText.color = level >= 4 ? NwTheme.Loss : level == 3 ? NwTheme.Warning : level >= 1 ? NwTheme.Title : NwTheme.TextDefault;

            bool raised = level > lastLevel;
            lastLevel = level;
            if (routine != null) StopCoroutine(routine);
            routine = StartCoroutine(Run(raised ? level - 1 : -1));
        }

        IEnumerator Run(int pulseIndex)
        {
            gameObject.SetActive(true);
            yield return Fade(0f, 1f);
            if (pulseIndex >= 0)
            {
                pulse.rectTransform.anchoredPosition = bars[pulseIndex].rectTransform.anchoredPosition + new Vector2(-1f, 1f);
                pulse.enabled = true;
                yield return new WaitForSecondsRealtime(pulseTime);
                pulse.enabled = false;
            }
            yield return new WaitForSecondsRealtime(showTime);
            yield return Fade(1f, 0f);
            routine = null;
        }

        IEnumerator Fade(float from, float to)
        {
            for (float t = 0f; t < fadeTime; t += Time.unscaledDeltaTime)
            {
                group.alpha = Mathf.Lerp(from, to, t / fadeTime);
                yield return null;
            }
            group.alpha = to;
        }
    }
}
