using UnityEditor;
using UnityEditor.SceneManagement;

namespace Nightward.EditorTools
{
    /// <summary>Schnellzugriff auf die wichtigsten Szenen. Fragt vorher nach, ob ungespeicherte Aenderungen gesichert werden sollen.</summary>
    public static class SceneShortcuts
    {
        const string Level01 = "Assets/_Project/Scenes/Game/Level_01.unity";

        [MenuItem("Nightward/Szenen/Level 01 oeffnen %#1")] // Strg+Umschalt+1
        static void OpenLevel01() => Open(Level01);

        static void Open(string path)
        {
            if (EditorApplication.isPlaying) EditorApplication.isPlaying = false;
            if (EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
                EditorSceneManager.OpenScene(path);
        }
    }
}
