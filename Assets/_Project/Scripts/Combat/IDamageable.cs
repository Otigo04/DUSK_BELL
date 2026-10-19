using UnityEngine;

namespace Nightward.Combat
{
    /// <summary>Alles, was Schaden von Schlaegen und Angriffen nehmen kann.</summary>
    public interface IDamageable
    {
        void TakeDamage(int amount, Vector2 hitDirection);
    }
}
