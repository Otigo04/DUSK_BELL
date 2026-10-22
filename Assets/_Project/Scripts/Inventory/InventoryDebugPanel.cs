using UnityEngine;
using UnityEngine.InputSystem;

namespace Nightward.Items
{
    /// <summary>
    /// Test-Panel fuers Inventar (nur Editor/Development-Build): F9 oeffnet eine Liste aller Gegenstaende zum Geben
    /// (Klick = 1, Umschalt = ganzer Stapel), als Pickup vor die Fuesse werfen, Rucksack leeren, Speichern/Laden testen.
    /// </summary>
    public class InventoryDebugPanel : MonoBehaviour
    {
        [SerializeField] Key toggleKey = Key.F9;

        PlayerInventory inv;
        bool open;
        Vector2 scroll;
        bool asPickup;
        string saved;

        void Awake() => inv = GetComponent<PlayerInventory>();

#if UNITY_EDITOR || DEVELOPMENT_BUILD
        void Update()
        {
            if (Keyboard.current != null && Keyboard.current[toggleKey].wasPressedThisFrame) open = !open;
        }

        void OnGUI()
        {
            if (!open || inv == null || inv.Database == null) return;
            float k = Mathf.Max(1f, Screen.height / 720f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(k, k, 1f));
            float h = Screen.height / k;
            GUILayout.BeginArea(new Rect(Screen.width / k - 330, 8, 322, h - 16), GUI.skin.box);
            GUILayout.Label("INVENTAR  (Klick = 1, Umschalt = Stapel)");
            GUILayout.BeginHorizontal();
            asPickup = GUILayout.Toggle(asPickup, "Als Pickup werfen");
            if (GUILayout.Button("Rucksack leeren")) { inv.Main.Clear(); inv.Equipment.Clear(); }
            if (GUILayout.Button("Speichern")) saved = inv.SaveJson();
            if (GUILayout.Button("Laden") && saved != null) inv.LoadJson(saved);
            GUILayout.EndHorizontal();

            scroll = GUILayout.BeginScrollView(scroll);
            ItemCategory last = (ItemCategory)(-1);
            int col = 0;
            var items = new System.Collections.Generic.List<ItemDef>(inv.Database.items);
            items.Sort((a, b) => a.category != b.category ? a.category.CompareTo(b.category) : string.CompareOrdinal(a.displayName, b.displayName));
            foreach (var d in items)
            {
                if (d == null) continue;
                if (d.category != last)
                {
                    if (col != 0) GUILayout.EndHorizontal();
                    GUILayout.Label("-- " + d.category);
                    GUILayout.BeginHorizontal();
                    col = 0;
                    last = d.category;
                }
                if (GUILayout.Button(d.displayName, GUILayout.Width(100)))
                {
                    bool shift = Keyboard.current != null && Keyboard.current.leftShiftKey.isPressed;
                    int n = shift ? d.maxStack : 1;
                    if (asPickup) ItemPickup.Spawn(new ItemStack(d, n), inv.transform.position + (Vector3)(inv.GetComponent<Nightward.Player.PlayerController>().FacingVector * 1.5f), Vector2.zero, inv);
                    else inv.Give(d, n);
                }
                if (++col % 3 == 0) { GUILayout.EndHorizontal(); GUILayout.BeginHorizontal(); }
            }
            GUILayout.EndHorizontal();
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }
#endif
    }
}
