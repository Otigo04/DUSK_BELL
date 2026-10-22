using System.Collections.Generic;
using System.IO;
using Nightward.Opening;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Nightward.EditorTools
{
    /// <summary>
    /// Pickup-Grafik (Art/Vehicles/Auto_Pickup.png, erzeugt von _Quelle_Generator/gen_pickup.py): Blatt schneiden und
    /// ein Auto-GameObject damit ausstatten (Opening und Level_01 nutzen dasselbe Auto).
    /// </summary>
    public static class CarArt
    {
        public const string SheetPath = "Assets/_Project/Art/Vehicles/Auto_Pickup.png";
        public const string SmokePath = "Assets/_Project/Art/Vehicles/Auto_Rauch.png";
        const string LitMaterial = "Packages/com.unity.render-pipelines.universal/Runtime/Materials/Sprite-Lit-Default.mat";
        const int CellW = 112, CellH = 80, Dirs = 8, Frames = 8;
        // Pivot: Bodenmitte des Autos (Pixel 56, 52 von 112x80)
        static readonly Vector2 Pivot = new Vector2(56f / CellW, 1f - 52f / CellH);

        /// <summary>Schneidet das Blatt (8 Richtungen x 8 Bilder, Name Auto_Pickup_RICHTUNG*8+BILD) und liefert die Sprites in dieser Reihenfolge.</summary>
        public static Sprite[] SliceSheet()
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(SheetPath);
            if (ti == null) { Debug.LogError("[Auto] fehlt: " + SheetPath); return new Sprite[0]; }
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Multiple;
            ti.spritePixelsPerUnit = 32;
            ti.filterMode = FilterMode.Point;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            var metas = new List<SpriteMetaData>();
            int th = CellH * Dirs;
            for (int d = 0; d < Dirs; d++)
                for (int f = 0; f < Frames; f++)
                    metas.Add(new SpriteMetaData
                    {
                        name = "Auto_Pickup_" + (d * Frames + f),
                        rect = new Rect(f * CellW, th - (d + 1) * CellH, CellW, CellH),
                        alignment = (int)SpriteAlignment.Custom,
                        pivot = Pivot,
                    });
#pragma warning disable CS0618
            ti.spritesheet = metas.ToArray();
#pragma warning restore CS0618
            ti.SaveAndReimport();
            return Load(SheetPath);
        }

        public static Sprite[] Load(string path)
        {
            var list = new List<Sprite>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(path)) if (o is Sprite sp) list.Add(sp);
            list.Sort((a, b) => Index(a.name).CompareTo(Index(b.name)));
            return list.ToArray();
        }

        static int Index(string n) { int i = n.LastIndexOf('_'); return i >= 0 && int.TryParse(n.Substring(i + 1), out int v) ? v : 0; }

        static void SetSprites(SerializedObject so, string prop, Sprite[] sprites)
        {
            var p = so.FindProperty(prop);
            p.arraySize = sprites.Length;
            for (int i = 0; i < sprites.Length; i++) p.GetArrayElementAtIndex(i).objectReferenceValue = sprites[i];
        }

        /// <summary>
        /// Legt ein komplettes Auto an: Rigidbody, Kollision, CarController, Visual (CarVisual) und zwei Scheinwerfer.
        /// Kein Interactable (das setzen Opening bzw. die Ankunft selbst).
        /// </summary>
        public static GameObject Create(Transform parent, Vector3 position, int sortingOrder)
        {
            var carGo = new GameObject("Auto");
            if (parent != null) carGo.transform.SetParent(parent, false);
            carGo.transform.position = position;
            var body = carGo.AddComponent<Rigidbody2D>();
            body.gravityScale = 0f;
            body.mass = 50f;
            body.freezeRotation = true;
            body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            carGo.AddComponent<BoxCollider2D>();
            var car = carGo.AddComponent<CarController>();

            var visGo = new GameObject("Visual");
            visGo.transform.SetParent(carGo.transform, false);
            var sr = visGo.AddComponent<SpriteRenderer>();
            sr.sortingOrder = sortingOrder;
            visGo.AddComponent<CarVisual>();

            foreach (var (name, x) in new[] { ("Scheinwerfer_L", -0.5f), ("Scheinwerfer_R", 0.5f) })
            {
                var pivot = new GameObject(name + "_Dreh").transform;
                pivot.SetParent(carGo.transform, false);
                var go = new GameObject(name);
                go.transform.SetParent(pivot, false);
                var l = go.AddComponent<Light2D>();
                l.lightType = Light2D.LightType.Point;
                l.color = new Color(1f, 0.86f, 0.55f);
                l.intensity = 0.5f;
                l.pointLightOuterRadius = 2.6f;
                l.pointLightInnerRadius = 0.5f;
                l.pointLightInnerAngle = 40f;
                l.pointLightOuterAngle = 70f;
                go.transform.localPosition = new Vector3(x, 1.6f, 0f);
            }
            Apply(carGo);
            return carGo;
        }

        /// <summary>
        /// Stattet ein bestehendes Auto (Opening oder neu angelegt) mit dem Pickup aus: Sprites, Kollision, Scheinwerfer-Sitz.
        /// </summary>
        public static void Apply(GameObject carGo)
        {
            var sheet = SliceSheet();
            var smoke = SliceSmoke();
            var vis = carGo.GetComponentInChildren<CarVisual>(true);
            if (vis == null) { Debug.LogError("[Auto] kein CarVisual an " + carGo.name); return; }

            var vso = new SerializedObject(vis);
            SetSprites(vso, "sheet", sheet);
            SetSprites(vso, "smoke", smoke);
            var hl = vso.FindProperty("headlights");
            var heads = new List<Transform>();
            foreach (Transform c in carGo.transform) if (c.name.EndsWith("_Dreh")) heads.Add(c);
            hl.arraySize = heads.Count;
            for (int i = 0; i < heads.Count; i++) hl.GetArrayElementAtIndex(i).objectReferenceValue = heads[i];
            vso.FindProperty("car").objectReferenceValue = carGo.GetComponent<CarController>();
            vso.ApplyModifiedPropertiesWithoutUndo();

            var lit = AssetDatabase.LoadAssetAtPath<Material>(LitMaterial);
            var sr = vis.GetComponent<SpriteRenderer>();
            if (lit != null) sr.sharedMaterial = lit;
            if (sheet.Length > 16) sr.sprite = sheet[2 * Frames];          // steht nach Norden

            // Kollision: das Auto dreht nicht, die Box ist ein Kompromiss aus Laenge (3,2) und Breite (1,1)
            var box = carGo.GetComponent<BoxCollider2D>();
            if (box != null) { box.size = new Vector2(1.5f, 1.5f); box.offset = Vector2.zero; }
            foreach (var pivot in heads)
                foreach (Transform l in pivot) l.localPosition = new Vector3(Mathf.Sign(l.localPosition.x) * 0.5f, 1.6f, 0f);
            EditorUtility.SetDirty(carGo);
        }

        static Sprite[] SliceSmoke()
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath(SmokePath);
            if (ti != null && ti.spriteImportMode != SpriteImportMode.Multiple)
            {
                ti.textureType = TextureImporterType.Sprite;
                ti.spriteImportMode = SpriteImportMode.Multiple;
                ti.spritePixelsPerUnit = 32;
                ti.filterMode = FilterMode.Point;
                ti.SaveAndReimport();
            }
            return Load(SmokePath);
        }

        [MenuItem("Nightward/Auto/Pickup-Blatt schneiden")]
        public static void SliceMenu()
        {
            AssetDatabase.Refresh();
            Debug.Log("[Auto] Pickup-Blatt geschnitten: " + SliceSheet().Length + " Sprites");
        }

        [MenuItem("Nightward/Auto/Pickup in der geoeffneten Szene anwenden")]
        public static void ApplyToOpenScene()
        {
            int n = 0;
            foreach (var vis in Object.FindObjectsByType<CarVisual>(FindObjectsInactive.Include))
            {
                var car = vis.GetComponentInParent<CarController>();
                if (car != null) { Apply(car.gameObject); n++; }
            }
            Debug.Log("[Auto] Pickup auf " + n + " Auto(s) angewendet");
        }
    }
}
