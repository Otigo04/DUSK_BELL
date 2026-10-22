using UnityEngine;

namespace Nightward.Items
{
    /// <summary>
    /// Aussehen eines Behaelters: zu, offen (mit Inhalt), offen und leer. Eine geleerte Truhe bleibt offen stehen,
    /// so sieht man aus der Ferne, was schon gepluendert ist. Fehlt ein Bild, wird das naechstpassende genommen.
    /// </summary>
    [RequireComponent(typeof(ItemContainer))]
    public class ContainerVisual : MonoBehaviour
    {
        [SerializeField] SpriteRenderer target;
        [SerializeField] Sprite closed;
        [Tooltip("Offen, solange etwas drin liegt (z. B. Gold zu sehen)")]
        [SerializeField] Sprite openFull;
        [Tooltip("Offen und leer. Auch das Bild der gepluenderten Truhe")]
        [SerializeField] Sprite openEmpty;
        [Tooltip("Eine geleerte Truhe bleibt offen")]
        [SerializeField] bool showLooted = true;

        ItemContainer container;

        void Awake()
        {
            container = GetComponent<ItemContainer>();
            if (target == null) target = GetComponentInChildren<SpriteRenderer>();
        }

        void OnEnable()
        {
            container.Changed += Refresh;
            Refresh();
        }

        void OnDisable() => container.Changed -= Refresh;

        void Start() => Refresh();

        void Refresh()
        {
            if (target == null || container.Inv == null) return;
            bool empty = container.IsEmpty;
            Sprite s;
            if (container.IsOpen) s = empty && openEmpty != null ? openEmpty : (openFull != null ? openFull : openEmpty);
            else if (showLooted && container.Searched && empty && openEmpty != null) s = openEmpty;
            else s = closed;
            if (s == null) s = closed;
            if (s != null && target.sprite != s) target.sprite = s;
        }
    }
}
