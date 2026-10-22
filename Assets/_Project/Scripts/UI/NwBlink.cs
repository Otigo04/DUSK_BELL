using UnityEngine;
using UnityEngine.UI;

namespace Nightward.UI
{
    /// <summary>Schaltet eine Grafik im festen Takt an/aus (Weiterpfeil: alle 0,5 s). Laeuft auch bei Time.timeScale = 0.</summary>
    [RequireComponent(typeof(Graphic))]
    public class NwBlink : MonoBehaviour
    {
        [SerializeField] float interval = NwTheme.ArrowBlink;
        Graphic graphic;
        float timer;

        void Awake() => graphic = GetComponent<Graphic>();

        void OnEnable()
        {
            timer = 0f;
            if (graphic != null) graphic.enabled = true;
        }

        void Update()
        {
            timer += Time.unscaledDeltaTime;
            if (timer < interval) return;
            timer -= interval;
            graphic.enabled = !graphic.enabled;
        }
    }
}
