using UnityEngine;

namespace Nightward.DayNight
{
    /// <summary>
    /// Regelt die Emission eines Partikelsystems ueber den NightFactor (Gluehwuermchen, Motten).
    /// Mit 'invert' nur tagsueber (z. B. Pollen).
    /// </summary>
    [RequireComponent(typeof(ParticleSystem))]
    public class NightParticles : MonoBehaviour
    {
        [Tooltip("Partikel pro Sekunde bei voller Nacht")]
        [SerializeField] float maxRate = 10f;
        [Tooltip("Ab diesem NightFactor beginnt die Emission")]
        [SerializeField, Range(0f, 1f)] float startAt = 0.4f;
        [SerializeField] bool invert;

        ParticleSystem.EmissionModule emission;

        void Awake() => emission = GetComponent<ParticleSystem>().emission;

        void Update()
        {
            float night = DayNightCycle.Instance != null ? DayNightCycle.Instance.NightFactor : 1f;
            if (invert) night = 1f - night;
            emission.rateOverTimeMultiplier = maxRate * Mathf.InverseLerp(startAt, 1f, night);
        }
    }
}
