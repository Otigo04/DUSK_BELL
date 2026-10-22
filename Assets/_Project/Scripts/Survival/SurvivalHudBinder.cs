using System;
using Nightward.UI;
using UnityEngine;

namespace Nightward.Survival
{
    /// <summary>
    /// Schreibt die Werte des Ueberlebens-Systems ins HUD (NwGameHud): Leben, Ausdauer samt gesperrtem Maximum, Sanity
    /// und die Zustands-Kacheln. Jede Stimmung zeigt auf eine Kachel ueber MoodDef.hudTile (Name aus NeedKind).
    /// </summary>
    [DefaultExecutionOrder(50)]
    public class SurvivalHudBinder : MonoBehaviour
    {
        [Tooltip("Aus = HUD wird nicht angefasst (z. B. wenn ein Test es von Hand steuert)")]
        [SerializeField] bool driveHud = true;

        SurvivalSystem system;
        NeedKind[] tiles;
        bool[] hasTile;
        bool warned;

        void Awake() => system = GetComponent<SurvivalSystem>();

        void Start()
        {
            var moods = (MoodId[])Enum.GetValues(typeof(MoodId));
            tiles = new NeedKind[moods.Length];
            hasTile = new bool[moods.Length];
            foreach (var id in moods)
            {
                var def = system.Config.Mood(id);
                if (def == null || string.IsNullOrEmpty(def.hudTile)) continue;
                if (Enum.TryParse(def.hudTile, out NeedKind kind)) { tiles[(int)id] = kind; hasTile[(int)id] = true; }
                else Debug.LogWarning($"[Survival] Stimmung {id}: HUD-Kachel '{def.hudTile}' gibt es nicht (NeedKind).", this);
            }
        }

        void LateUpdate()
        {
            var hud = NwGameHud.Instance;
            var sim = system != null ? system.Sim : null;
            if (!driveHud || hud == null || sim == null) return;

            hud.SetHealth(sim.Value(StatId.Health), sim.Def(StatId.Health).max);
            hud.SetStamina(sim.Value(StatId.Stamina), sim.Def(StatId.Stamina).max, sim.Max(StatId.Stamina));
            hud.SetSanity(sim.Value(StatId.Sanity), sim.Def(StatId.Sanity).max);

            for (int i = 0; i < hasTile.Length; i++)
            {
                if (!hasTile[i]) continue;
                var m = sim.Mood((MoodId)i);
                if (hud.FindTile(tiles[i]) == null)
                {
                    if (!warned && m.IsActive)
                    {
                        warned = true;
                        Debug.LogWarning($"[Survival] Im HUD fehlt die Kachel {tiles[i]}. Menue Nightward/UI/HUD Neu/2 Prefabs bauen, dann 3 In offene Szene einbauen.", this);
                    }
                    continue;
                }
                hud.SetNeed(tiles[i], m.Stage, m.IsPositive);
            }
        }
    }
}
