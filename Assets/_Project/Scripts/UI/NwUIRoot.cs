using UnityEngine;

namespace Nightward.UI
{
    /// <summary>
    /// Auf das Canvas legen. Haelt die Pixelschrift scharf: die dynamische Font-Textur wird
    /// bei jedem Neuaufbau auf Point-Filter gesetzt (keine glatten Kanten).
    /// </summary>
    [ExecuteAlways]
    public class NwUIRoot : MonoBehaviour
    {
        [SerializeField] Font pixelFont;
        static bool hooked;

        public Font PixelFont => pixelFont;

        void OnEnable()
        {
            if (!hooked)
            {
                Font.textureRebuilt += OnTextureRebuilt;
                hooked = true;
            }
            Apply(pixelFont);
        }

        static void OnTextureRebuilt(Font f) => Apply(f);

        static void Apply(Font f)
        {
            if (f == null || f.material == null || f.material.mainTexture == null) return;
            f.material.mainTexture.filterMode = FilterMode.Point;
        }
    }
}
