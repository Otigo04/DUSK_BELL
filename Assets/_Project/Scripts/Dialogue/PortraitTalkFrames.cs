using UnityEngine;

namespace Nightward.Dialogue
{
    /// <summary>
    /// Erzeugt zu einem Ausdrucksbild (z. B. "tense") die Sprech-Frames: das Gesicht des Ausdrucks, aber mit der Mundstellung
    /// aus den normalen Sprech-Frames des NPC. So bewegt sich der Mund auch, wenn ein fester Ausdruck gezeigt wird.
    /// Der Mund ist der Bereich, in dem sich ein Sprech-Frame vom Ruhebild unterscheidet. Laeuft zur Laufzeit,
    /// die Texturen muessen nicht lesbar importiert sein.
    /// </summary>
    public static class PortraitTalkFrames
    {
        const int Threshold = 24;

        public static Sprite[] Build(Sprite idle, Sprite[] talk, Sprite expression)
        {
            if (idle == null || expression == null || talk == null || talk.Length == 0) return new Sprite[0];
            var baseFace = Read(idle, out int w, out int h);
            var face = Read(expression, out int ew, out int eh);
            if (baseFace == null || face == null || ew != w || eh != h) return new Sprite[0];

            var result = new Sprite[talk.Length];
            for (int i = 0; i < talk.Length; i++)
            {
                var mouth = Read(talk[i], out int tw, out int th);
                if (mouth == null || tw != w || th != h) { result[i] = expression; continue; }

                var pixels = (Color32[])face.Clone();
                for (int p = 0; p < pixels.Length; p++)
                    if (Differs(baseFace[p], mouth[p])) pixels[p] = mouth[p];

                var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, name = expression.name + "_talk" + i };
                tex.SetPixels32(pixels);
                tex.Apply();
                var pivot = new Vector2(expression.pivot.x / expression.rect.width, expression.pivot.y / expression.rect.height);
                result[i] = Sprite.Create(tex, new Rect(0, 0, w, h), pivot, expression.pixelsPerUnit);
            }
            return result;
        }

        static bool Differs(Color32 a, Color32 b) =>
            Mathf.Abs(a.r - b.r) + Mathf.Abs(a.g - b.g) + Mathf.Abs(a.b - b.b) + Mathf.Abs(a.a - b.a) > Threshold;

        /// <summary>Liest die Pixel eines Sprites ueber eine RenderTexture, funktioniert auch bei nicht lesbaren Texturen.</summary>
        static Color32[] Read(Sprite s, out int width, out int height)
        {
            width = height = 0;
            if (s == null || s.texture == null) return null;
            var src = s.texture;
            var r = s.textureRect;
            width = Mathf.RoundToInt(r.width);
            height = Mathf.RoundToInt(r.height);

            var rt = RenderTexture.GetTemporary(src.width, src.height, 0, RenderTextureFormat.ARGB32);
            var previous = RenderTexture.active;
            Graphics.Blit(src, rt);
            RenderTexture.active = rt;
            var copy = new Texture2D(width, height, TextureFormat.RGBA32, false);
            copy.ReadPixels(new Rect(r.x, r.y, width, height), 0, 0);
            copy.Apply();
            RenderTexture.active = previous;
            RenderTexture.ReleaseTemporary(rt);
            var pixels = copy.GetPixels32();
            Object.Destroy(copy);
            return pixels;
        }
    }
}
