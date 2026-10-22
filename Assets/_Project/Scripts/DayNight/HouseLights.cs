using System;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Nightward.DayNight
{
    /// <summary>
    /// Macht abends in einem Haus Licht: tauscht dunkle Fenster-Tiles gegen beleuchtete und schaltet die
    /// Fensterlichter (NightLight mit autoSwitch aus) ein. Jedes Haus hat einen eigenen zufaelligen Zeitpunkt.
    /// Gehoert an das Haus-Objekt (z. B. Grid/Haus_01), durchsucht alle Tilemaps darunter.
    /// </summary>
    public class HouseLights : MonoBehaviour
    {
        [Serializable]
        public struct TileSwap
        {
            public TileBase dark;
            public TileBase lit;
        }

        [SerializeField] TileSwap[] swaps = new TileSwap[0];
        [SerializeField] NightLight[] windowLights = new NightLight[0];
        [Tooltip("Bei welchem Nachtanteil (0..1) im Haus Licht gemacht wird, zufaellig in diesem Bereich")]
        [SerializeField] Vector2 switchOnRange = new Vector2(0.2f, 0.7f);
        [Tooltip("Aus = Haus bleibt dunkel (z. B. unbewohnt oder Bewohner tot)")]
        [SerializeField] bool inhabited = true;

        Tilemap[] maps;
        float threshold;
        bool lit;
        bool first = true;

        public bool Inhabited { get => inhabited; set => inhabited = value; }

        void Awake()
        {
            maps = GetComponentsInChildren<Tilemap>();
            threshold = UnityEngine.Random.Range(switchOnRange.x, switchOnRange.y);
        }

        void Update()
        {
            float night = DayNightCycle.Instance != null ? DayNightCycle.Instance.NightFactor : 1f;
            bool want = inhabited && (lit ? night >= threshold - 0.05f : night >= threshold);
            if (want == lit && !first) return;
            Apply(want, instant: first);
            first = false;
        }

        void Apply(bool on, bool instant)
        {
            lit = on;
            foreach (var tm in maps)
            {
                foreach (var pos in tm.cellBounds.allPositionsWithin)
                {
                    var t = tm.GetTile(pos);
                    if (t == null) continue;
                    foreach (var s in swaps)
                    {
                        var from = on ? s.dark : s.lit;
                        if (t != from) continue;
                        tm.SetTile(pos, on ? s.lit : s.dark);
                        break;
                    }
                }
            }
            foreach (var l in windowLights)
                if (l != null) l.SwitchOn(on, instant);
        }
    }
}
