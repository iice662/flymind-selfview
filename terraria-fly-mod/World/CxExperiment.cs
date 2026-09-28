using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using FlyMind.Neural;
using Terraria;
using Terraria.ModLoader;

namespace FlyMind.World
{
    /// <summary>
    /// Which structure the fly's visual input has this block.
    ///
    ///   Natural  - the world sweeps past the eye and there is no "self" term: the fly's own
    ///              body is not part of its visual field.
    ///   SelfView - the fly's own body is rendered into its visual field (third person), so a
    ///              compact part of the visual pool reports no retinal slip: that region of
    ///              the field is covered by something rigidly attached to the head.
    ///   Shuffle  - placebo arm: the visual world is IDENTICAL to Natural (the body is not
    ///              drawn), but the same body-patch drive is applied to a random subset of
    ///              the pool instead of the compact one.  Same total drive, no spatial
    ///              structure - so a difference between SelfView and Shuffle cannot be
    ///              "more input" or "the world looked different".
    /// </summary>
    public enum CxArm { Natural, SelfView, Shuffle }

    /// <summary>
    /// The self-observation experiment, in game.
    ///
    /// The offline harness (tools/CircuitPreview --exp) runs the same design with exact
    /// magnitude matching and permutation tests; this one is what makes it an experiment on
    /// a *behaving* fly: the visual input is the real rendered world, the fly moves, and the
    /// only thing the experiment changes is whether the fly's own body is in its own visual
    /// field.  Arms alternate in blocks, every block contributes one value per metric, and
    /// the report compares the arms with an effect size and a permutation test.
    ///
    /// Everything is appended to Mods\flymind_experiment.txt, so the raw block values can be
    /// re-analysed outside the game.
    /// </summary>
    public sealed class CxExperiment
    {
        public const float BlockSeconds = 20f;
        public const int MinBlocksPerArm = 6;

        public bool Running { get; private set; }
        public CxArm Arm { get; private set; } = CxArm.Natural;
        public int BlocksDone { get; private set; }
        public float BlockProgress { get; private set; }
        public string LastReport { get; private set; } = "";

        private readonly Dictionary<CxArm, List<Block>> _blocks = new()
        {
            [CxArm.Natural] = new List<Block>(),
            [CxArm.SelfView] = new List<Block>(),
            [CxArm.Shuffle] = new List<Block>(),
        };

        private readonly List<float> _cxRateSeries = new();
        private readonly List<float> _bumpSeries = new();
        private float _blockSeconds;
        private int _blockIndex;
        private VisualPatch _patchNatural;
        private VisualPatch _patchShuffle;

        /// <summary>One 20 s block: the metrics that get compared across arms.</summary>
        public sealed class Block
        {
            public CxArm Arm;
            public int Index;
            public float CxRate, CxActive, RingRate, ColumnarRate, FanBodyRate, OtherRate;
            public float BumpR, BumpAngleDrift, RateSd, TauMs, SelfInViewMean, ViewMotionMean;
        }

        public void Configure(BrainData data)
        {
            _patchNatural = VisualPatch.Build(data, false);
            _patchShuffle = VisualPatch.Build(data, true);
        }

        public VisualPatch PatchForArm(CxArm arm) => arm == CxArm.Shuffle ? _patchShuffle : _patchNatural;

        /// <summary>Number of finished blocks for one arm (shown live in the panel).</summary>
        public int BlockCount(CxArm arm) => _blocks[arm].Count;

        public void Toggle()
        {
            Running = !Running;
            if (Running)
            {
                _blocks[CxArm.Natural].Clear();
                _blocks[CxArm.SelfView].Clear();
                _blocks[CxArm.Shuffle].Clear();
                _blockIndex = 0;
                BlocksDone = 0;
                Arm = CxArm.Natural;
                _blockSeconds = 0f;
                LastReport = "running: NAT -> SELF -> SHUF blocks";
                Log($"# experiment started ({DateTime.Now:yyyy-MM-dd HH:mm:ss}) "
                    + $"block={BlockSeconds:0}s arms=NAT,SELF,SHUF");
            }
            else
            {
                LastReport = "stopped";
                Log("# experiment stopped");
            }
        }

        public void Update(FlyBrain brain, CxReadout cx, float selfInView, float viewMotion,
                           float gameTimeScale)
        {
            if (!Running || brain == null || cx == null) return;
            _cxRateSeries.Add(cx.CxRate);
            _bumpSeries.Add(cx.BumpAngle);
            _blockSeconds += brain.Circuit.Dt / 1000f * gameTimeScale;
            BlockProgress = Math.Min(1f, _blockSeconds / BlockSeconds);
            if (_blockSeconds < BlockSeconds) return;

            var b = new Block
            {
                Arm = Arm,
                Index = _blockIndex++,
                CxRate = cx.CxRate,
                CxActive = cx.CxActiveFraction,
                RingRate = cx.FamilyRate[1],
                ColumnarRate = cx.FamilyRate[2],
                FanBodyRate = cx.FamilyRate[3],
                OtherRate = cx.FamilyRate[4],
                BumpR = Mean(_bumpSeries),
                RateSd = Sd(_cxRateSeries),
                TauMs = AutocorrTime(_cxRateSeries),
                SelfInViewMean = selfInView,
                ViewMotionMean = viewMotion,
            };
            _cxRateSeries.Clear();
            _bumpSeries.Clear();
            _blockSeconds = 0f;
            _blocks[Arm].Add(b);
            BlocksDone++;

            Log(string.Format(CultureInfo.InvariantCulture,
                "block {0} arm={1} cxHz={2:F3} active={3:F3} ring={4:F2} col={5:F2} fb={6:F2} "
                + "other={7:F2} bumpR={8:F3} sd={9:F3} tau={10:F0} selfInView={11:F3} viewMotion={12:F3}",
                b.Index, Arm, b.CxRate, b.CxActive, b.RingRate, b.ColumnarRate, b.FanBodyRate,
                b.OtherRate, b.BumpR, b.RateSd, b.TauMs, b.SelfInViewMean, b.ViewMotionMean));

            // next arm: keep the block counts balanced
            var counts = _blocks.ToDictionary(kv => kv.Key, kv => kv.Value.Count);
            Arm = counts.OrderBy(kv => kv.Value).ThenBy(kv => kv.Key).First().Key;
            if (counts.Values.All(c => c >= MinBlocksPerArm) && counts.Values.Min() % 2 == 0)
                LastReport = Report();
        }

        /// <summary>Effect size and permutation test of SelfView against each control arm.</summary>
        public string Report()
        {
            var sb = new StringBuilder();
            sb.AppendLine($"== {DateTime.Now:HH:mm:ss} blocks NAT={_blocks[CxArm.Natural].Count} "
                          + $"SELF={_blocks[CxArm.SelfView].Count} SHUF={_blocks[CxArm.Shuffle].Count}");
            sb.AppendLine("metric                     NAT     SELF     SHUF |  d(NAT)  p(NAT)  d(SHUF)  p(SHUF)");
            var metrics = new (string Name, Func<Block, float> Get)[]
            {
                ("CX rate (Hz)", b => b.CxRate),
                ("CX active fraction", b => b.CxActive),
                ("ring rate (Hz)", b => b.RingRate),
                ("columnar rate (Hz)", b => b.ColumnarRate),
                ("fanbody rate (Hz)", b => b.FanBodyRate),
                ("other rate (Hz)", b => b.OtherRate),
                ("ring bump R", b => b.BumpR),
                ("CX rate SD (Hz)", b => b.RateSd),
                ("CX autocorr (ms)", b => b.TauMs),
                ("self in view", b => b.SelfInViewMean),
            };
            var self = _blocks[CxArm.SelfView].Select(b => b).ToList();
            if (self.Count < 3) return "not enough SELF blocks yet";
            foreach (var (name, get) in metrics)
            {
                var sv = self.Select(get).ToArray();
                var nv = _blocks[CxArm.Natural].Select(get).ToArray();
                var hv = _blocks[CxArm.Shuffle].Select(get).ToArray();
                sb.AppendLine($"{name,-26} {nv.Average(),7:F3} {sv.Average(),8:F3} {hv.Average(),8:F3} |"
                              + (nv.Length >= 3 ? $" {CohensD(sv, nv),7:F2} {PermTest(sv, nv),7:F4}" : "       -       -")
                              + (hv.Length >= 3 ? $" {CohensD(sv, hv),8:F2} {PermTest(sv, hv),8:F4}" : "       -       -"));
            }
            sb.AppendLine("(d>0 = SELF larger; p from a two-sided permutation test over blocks)");
            string text = sb.ToString();
            Log(text);
            return text;
        }

        private static float Mean(List<float> xs) => xs.Count == 0 ? 0f : xs.Average();
        private static float Sd(List<float> xs)
        {
            if (xs.Count < 2) return 0f;
            float m = xs.Average();
            return MathF.Sqrt(xs.Sum(x => (x - m) * (x - m)) / (xs.Count - 1));
        }

        /// <summary>Integrated autocorrelation time of the CX rate series, in ms (ticks are 0.5 ms of model time).</summary>
        private static float AutocorrTime(List<float> xs)
        {
            if (xs.Count < 20) return 0f;
            float m = xs.Average();
            var z = xs.Select(x => x - m).ToArray();
            float v = z.Sum(x => x * x);
            if (v < 1e-9f) return 0f;
            float tau = 0;
            int maxLag = Math.Min(20, z.Length / 3);
            for (int lag = 1; lag <= maxLag; lag++)
            {
                float ac = 0;
                for (int i = 0; i + lag < z.Length; i++) ac += z[i] * z[i + lag];
                ac /= v;
                if (ac < 0.05f) break;
                tau += ac * 0.5f;      // one tick = 0.5 ms of model time
            }
            return tau;
        }

        private static double CohensD(float[] a, float[] b)
        {
            if (a.Length < 2 || b.Length < 2) return 0;
            double ma = a.Average(), mb = b.Average();
            double va = a.Select(x => (x - ma) * (x - ma)).Sum() / (a.Length - 1);
            double vb = b.Select(x => (x - mb) * (x - mb)).Sum() / (b.Length - 1);
            double sp = Math.Sqrt((va + vb) / 2);
            return sp < 1e-12 ? 0 : (ma - mb) / sp;
        }

        private static double PermTest(float[] a, float[] b)
        {
            if (a.Length < 3 || b.Length < 3) return 1.0;
            var all = a.Concat(b).ToArray();
            double obs = Math.Abs(a.Average() - b.Average());
            if (obs < 1e-12) return 1.0;
            var rng = new Random(4242);
            int hit = 0, nPerm = 2000;
            var idx = Enumerable.Range(0, all.Length).ToArray();
            for (int it = 0; it < nPerm; it++)
            {
                for (int i = all.Length - 1; i > 0; i--)
                {
                    int j = rng.Next(i + 1);
                    (idx[i], idx[j]) = (idx[j], idx[i]);
                }
                double sa = 0, sb = 0;
                for (int i = 0; i < a.Length; i++) sa += all[idx[i]];
                for (int i = a.Length; i < all.Length; i++) sb += all[idx[i]];
                if (Math.Abs(sa / a.Length - sb / b.Length) >= obs - 1e-12) hit++;
            }
            return (hit + 1.0) / (nPerm + 1.0);
        }

        private static void Log(string line)
        {
            try
            {
                string path = Path.Combine(ModLoader.ModPath, "flymind_experiment.txt");
                File.AppendAllText(path, line + Environment.NewLine);
            }
            catch (Exception e)
            {
                ModContent.GetInstance<FlyMind>()?.Logger.Warn("experiment log failed: " + e.Message);
            }
        }
    }
}
