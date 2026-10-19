using UnityEngine;

namespace Nightward.Core
{
    /// <summary>Weiche Kamera-Verfolgung mit optionaler Begrenzung auf die Levelgrenzen.</summary>
    [RequireComponent(typeof(Camera))]
    public class CameraFollow2D : MonoBehaviour
    {
        [SerializeField] Transform target;
        [SerializeField] Vector2 offset = new Vector2(0f, 0.7f);
        [SerializeField] float smoothTime = 0.12f;
        [Header("Begrenzung (Weltkoordinaten)")]
        [SerializeField] bool clampToBounds = true;
        [SerializeField] Vector2 boundsMin = new Vector2(-6f, -6f);
        [SerializeField] Vector2 boundsMax = new Vector2(54f, 38f);

        Camera cam;
        Vector3 velocity;

        void Awake() => cam = GetComponent<Camera>();

        void Start()
        {
            if (target == null)
            {
                var player = GameObject.FindWithTag("Player");
                if (player != null) target = player.transform;
            }
            if (target != null) transform.position = Clamp(Desired());
        }

        void LateUpdate()
        {
            if (target == null) return;
            transform.position = Clamp(Vector3.SmoothDamp(transform.position, Desired(), ref velocity, smoothTime));
        }

        Vector3 Desired() => new Vector3(target.position.x + offset.x, target.position.y + offset.y, transform.position.z);

        Vector3 Clamp(Vector3 p)
        {
            if (!clampToBounds) return p;
            float halfH = cam.orthographicSize, halfW = halfH * cam.aspect;
            p.x = boundsMax.x - boundsMin.x <= halfW * 2f ? (boundsMin.x + boundsMax.x) * 0.5f : Mathf.Clamp(p.x, boundsMin.x + halfW, boundsMax.x - halfW);
            p.y = boundsMax.y - boundsMin.y <= halfH * 2f ? (boundsMin.y + boundsMax.y) * 0.5f : Mathf.Clamp(p.y, boundsMin.y + halfH, boundsMax.y - halfH);
            return p;
        }
    }
}
