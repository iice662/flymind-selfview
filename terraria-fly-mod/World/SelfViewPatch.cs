using System;
using System.Collections.Generic;
using System.Linq;
using FlyMind.Neural;

namespace FlyMind.World
{
    /// <summary>
    /// The body patch: the part of the fly's visual input pool that its own body covers.
    ///
    /// The pool is every cell the visual field can act through - the rotation-sensitive
    /// cells themselves plus the connectome-derived relay that carries visual information
    /// into the central complex (cells receiving from the rotation pool and projecting onto
    /// the CX; tools/CircuitBuilder writes that list into the blob).  The patch is the
    /// fraction of the pool closest to the pool's own soma centroid: the lobula plate and
    /// its relays are retinotopically organised, so a compact cluster of somas stands in for
    /// a compact region of the visual field.  The blob carries no receptive-field map, so
    /// this is a proxy and is described as one wherever the result is reported.
    ///
    /// The rule (nearest 25% to the centroid, fixed permutation seed for the shuffled
    /// control) is identical to the offline harness in tools/CircuitPreview/Experiment.cs,
    /// so the game and the offline experiment manipulate the same cells.
    /// </summary>
    public sealed class VisualPatch
    {
        public const float BodyFieldFraction = 0.25f;

        /// <summary>Parallel to <see cref="BrainData.SelfMotionSeeds"/>.</summary>
        public bool[] SelfMotion = Array.Empty<bool>();
        /// <summary>Parallel to <see cref="BrainData.VisualRelay"/>.</summary>
        public bool[] Relay = Array.Empty<bool>();
        public int PoolSize;
        public int PatchSize;

        public static VisualPatch Build(BrainData data, bool shuffled)
        {
            var pool = new List<int>(data.SelfMotionSeeds.Length + data.VisualRelay.Length);
            pool.AddRange(data.SelfMotionSeeds);
            foreach (int i in data.VisualRelay) if (!data.SelfMotionSeeds.Contains(i)) pool.Add(i);

            var chosen = CompactPatch(data, pool, BodyFieldFraction);
            if (shuffled)
            {
                // a random subset of exactly the same size: destroys the spatial coherence of
                // the patch while keeping the amount of input identical
                var rng = new Random(20260903);
                var arr = pool.Select(i => chosen.Contains(i)).ToArray();
                for (int i = arr.Length - 1; i > 0; i--)
                {
                    int j = rng.Next(i + 1);
                    (arr[i], arr[j]) = (arr[j], arr[i]);
                }
                chosen = pool.Where((_, k) => arr[k]).ToHashSet();
            }

            var patch = new VisualPatch { PoolSize = pool.Count, PatchSize = chosen.Count };
            patch.SelfMotion = data.SelfMotionSeeds.Select(i => chosen.Contains(i)).ToArray();
            patch.Relay = data.VisualRelay.Select(i => chosen.Contains(i)).ToArray();
            return patch;
        }

        /// <summary>Neurons within the pool closest to the pool's soma centroid.</summary>
        private static HashSet<int> CompactPatch(BrainData data, List<int> pool, float fraction)
        {
            if (pool.Count == 0) return new HashSet<int>();
            double cx = 0, cy = 0, cz = 0;
            foreach (int i in pool)
            {
                cx += data.Soma[i * 3];
                cy += data.Soma[i * 3 + 1];
                cz += data.Soma[i * 3 + 2];
            }
            cx /= pool.Count; cy /= pool.Count; cz /= pool.Count;
            int n = Math.Max(1, (int)Math.Round(pool.Count * fraction));
            return pool
                .Select(i =>
                {
                    double dx = data.Soma[i * 3] - cx, dy = data.Soma[i * 3 + 1] - cy,
                           dz = data.Soma[i * 3 + 2] - cz;
                    return (i, d: dx * dx + dy * dy + dz * dz);
                })
                .OrderBy(t => t.d)
                .Take(n)
                .Select(t => t.i)
                .ToHashSet();
        }
    }
}
