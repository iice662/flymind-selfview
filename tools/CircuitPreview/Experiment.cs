// The self-observation experiment, offline half.
//
// QUESTION
//   The fly in the mod is watched in the third person, so its own eyes look at a world
//   that contains its own body.  No fly ever sees itself.  Does that unnatural input
//   change what the central complex (CX) - the head-direction ring and the columnar
//   steering circuits - is doing, and if it does, is the change a property of the
//   *structure* of the input or just of "more input"?
//
// DESIGN
//   All arms receive the same amount of drive to the self-motion pool (the lobula plate
//   tangential cells H1/H2/VS/V1/HS/JO-EV/LHAV/LHPV) to within a matched total, the same
//   background odour context and the same spontaneous resting tone.  They differ only in
//   HOW the drive is distributed across the pool:
//
//     rest        - no visual drive at all (reference: is the circuit alive?)
//     flow        - natural: every self-motion cell sees the same world optic flow F(t)
//     self        - unnatural: a compact anatomical cluster of the pool ("body patch",
//                   25% of the cells) is modelled as the part of the visual field covered
//                   by the fly's own body, so its retinal slip is ~0 (the body is rigidly
//                   attached to the head) while the surround keeps the full world flow
//     shuffle     - null: identical drive, identical patch SIZE, random patch identity
//                   (destroys the spatial coherence of the patch)
//     decorrelated- null: identical patch, identical drive statistics, but the patch
//                   signal is an independent process instead of being locked to F(t)
//
//   `self`, `shuffle` and `decorrelated` have the same total injected spike count by
//   construction (see DriveProfile), so arm differences cannot be explained by magnitude.
//   `flow` has the same total too, so the primary contrast `self` vs `flow` is
//   magnitude-matched as well: it isolates the presence of a body-locked, slip-free
//   region inside an otherwise natural flow field.
//
// READOUT
//   Per CX subfamily (ring EPG/PEG, columnar PFN/PFR/hDelta, fan-shaped body, other) and
//   for the CX as a whole: mean firing rate, active fraction, mean pairwise correlation,
//   integrated autocorrelation time of the population state, participation ratio
//   (effective dimensionality), and the amplitude of the ring population vector.
//
// STATISTICS
//   Each arm is run N times with different RNG seeds.  Every metric is compared between
//   arms with an effect size (Cohen's d) and a permutation test over the trial values
//   (two-sided, 4000 permutations).  Nothing here is a claim about the real fly: it is a
//   measurement on the MaleCNS connectome under a stated model of the unnatural input.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

internal static class Experiment
{
    // The published stimulation protocol: a Poisson train at up to 150 Hz on a stimulated
    // neuron, each event worth f_poi = 250 synapses (Shiu et al. 2024).
    internal const float MaxStimHz = 150f;
    internal const float Fpoi = 250f;

    /// <summary>Fraction of the self-motion pool treated as covered by the fly's own body.</summary>
    internal const float BodyFieldFraction = 0.25f;

    /// <summary>Retinal slip inside the body region, relative to the world flow (0 = the
    /// body is perfectly locked to the head, so nothing moves across it).</summary>
    internal const float BodySlip = 0.1f;

    internal sealed record Arm(string Id, string Name, string Description,
        bool Driven, int Mode, float Scale = 1f, bool Sync = false, float Alpha = 0f);

    /// <summary>Closed loop (see results/CLOSED-LOOP-PLAN.md): the turn is caused by the circuit's
    /// own descending steering command and the visual drive is the heading error, so the conflict
    /// manipulation can be scored as behaviour.  LoopGain is calibrated ONCE at alpha = 0 and then
    /// frozen for every arm, alpha and kappa - otherwise the comparison would be circular.</summary>
    internal static bool ClosedLoop = false;
    internal static float LoopGain = 0f;

    // patch modes
    private const int ModeUniform = 0;      // natural optic flow over the whole pool
    private const int ModePatchReduced = 1; // body-locked (slip-free) patch
    private const int ModePatchRandom = 2;  // same size, random identity
    private const int ModePatchDecor = 3;   // same patch, signal independent of F(t)
    private const int ModePatchCxMatched = 4; // random identity, matched CX input loss

    /// <summary>Retinal slip in deg/s of a fully driven rotation-sensitive cell at |yaw| = 1.</summary>
    internal const float MaxTurnRateDeg = 200f;

    internal static Arm[] Arms =
    {
        new("rest", "静息(无视觉输入)", "没有视觉驱动，只有背景气味与静息噪声", false, ModeUniform),
        new("flow", "自然:世界光流", "整个世界均匀扫过复眼，视野里没有自己", true, ModeUniform),
        new("self", "非自然:看见自己", "身体占据视野的一块(体锁、几乎无滑移)，周边照旧扫过", true, ModePatchReduced, 1f, false, 0f),
        new("shuffle", "对照:随机斑块", "与 self 同强度同数量，斑块身份随机(破坏空间相干性)", true, ModePatchRandom),
        new("randmat", "对照:随机斑块·匹配CX输入", "随机身份，但大小按\"削掉同样多的 CX 输入\"配平(9.1%)", true, ModePatchCxMatched),
        new("decorr", "对照:斑块信号去相关", "与 self 同斑块同强度，但斑块信号与 F(t) 独立", true, ModePatchDecor, 1f, false, 1f),
    };

    /// <summary>
    /// Conflict dose.  Alpha is the fraction of the body patch's slip that is replaced by a
    /// 100 ms block-shuffled copy of the same waveform: alpha = 0 is the slip-free body patch
    /// (the "missing self-signal" condition), alpha = 1 is the de-correlated patch (the same
    /// marginal distribution with no alignment to the world's rotation).  Intermediate values
    /// give a graded conflict, so the claim "conflict, not absence, perturbs heading" becomes a
    /// dose-response rather than a single contrast.  `self` (alpha = 0) and `decorr`
    /// (alpha = 1) are already in Arms, so a run with --conflict gives the full series.
    /// </summary>
    internal static readonly Arm[] ConflictArms =
    {
        new("conf25", "冲突剂量 25%", "斑块滑移 = 75% 自然 + 25% 打乱", true, ModePatchReduced, 1f, false, 0.25f),
        new("conf50", "冲突剂量 50%", "斑块滑移 = 50% 自然 + 50% 打乱", true, ModePatchReduced, 1f, false, 0.50f),
        new("conf75", "冲突剂量 75%", "斑块滑移 = 25% 自然 + 75% 打乱", true, ModePatchReduced, 1f, false, 0.75f),
    };

    /// <summary>
    /// Positive controls.  A null result is only worth reporting if the same pipeline, on the
    /// same cells, through the same pathway, does move when something that must matter is
    /// changed:
    ///
    ///   drive0.5 / drive1.5 - the whole visual pool, same structure, total drive scaled by
    ///                         0.5 or 1.5.  This is the positive control for "the readouts can
    ///                         see a change in what arrives from the eyes".
    ///   synch               - identical cells and identical EXPECTED total, but the injection
    ///                         draws are common across cells, so all cells fire together
    ///                         instead of independently.  Only the temporal structure of the
    ///                         input changes: the positive control for "structure, not just
    ///                         amount, is detectable through this pathway".
    ///
    /// A body patch that is slip-free is a much smaller change than either of these; if the
    /// positive controls move the readouts and the patch does not, the null is informative.
    /// </summary>
    internal static readonly Arm[] ControlArms =
    {
        new("drive0.5", "阳性对照:总驱动×0.5", "同一池、同一结构，总量减半", true, ModeUniform, 0.5f),
        new("drive1.5", "阳性对照:总驱动×1.5", "同一池、同一结构，总量增半", true, ModeUniform, 1.5f),
        new("synch", "阳性对照:同步发放", "同一池、同期望总量，但所有细胞同相同步", true, ModeUniform, 1f, true),
    };

    internal sealed class Trial
    {
        public string ArmId = "";
        public float Rate, ActiveFraction, PairCorr, TauMs, Dim, PopSd, BumpR;
        public float PoolRate;                 // self-motion pool (manipulation check)
        public float[] FamRate = new float[5];
        public float[] FamActive = new float[5];
        public long InjectedEvents;            // spikes actually delivered to the pool
        /// <summary>Sum of the injection probabilities over the trial: the expected number of
        /// events.  Delivered vs expected is the drive-matching check that does not depend on
        /// Bernoulli noise.</summary>
        public double ExpectedEvents;
        // heading-encoding metrics (only meaningful with the yaw drive)
        public float HeadGain, HeadResidDeg, TurnedDeg, RelayGain;
        /// <summary>Ring state read out from the data itself (top-2 PCs of the ring state
        /// trajectory) rather than from soma geometry.</summary>
        public float RingPc12Var;      // fraction of ring-state variance in the first two PCs
        public float RingLoop;         // 1 = the state circles the PC plane origin (a ring)
        public float TrackGainYaw;     // ring rotation per unit yaw at the drive frequency
        public float TrackLagYawDeg;   // phase lag behind the yaw command
        public float TrackGainHead;    // ring rotation per unit integrated heading
        public float TrackLagHeadDeg;  // phase lag behind the integrated heading
        /// <summary>Does the population's yaw tuning follow the connectome's push-pull wiring?</summary>
        public float YawTuningWireCorr;    // corr(slope_j, w_j) over CX cells
        public float RingYawTuningWireCorr;
        public float YawModulation;        // mean |d(rate)/d(yaw)| in Hz per unit yaw
        // mechanism: is the heading estimate noisier, or merely weaker?
        public float RingAngDiffusionDeg;  // SD of the ring angle around its trend (deg)
        public float RingAngAc1;           // lag-1 autocorrelation of the ring angle
        // behavioural readout: the steering command the brain sends
        public float SteerCorrYaw;         // corr((right-left) descending rate, yaw)
        public float SteerAsymSd;          // SD of the left-right descending asymmetry (Hz)
        public float DnRateL, DnRateR;
        // closed loop only: how well the fly held the commanded course (radians)
        public float LoopErrRms;           // RMS heading error over the analysis window
        public float LoopErrMean;          // mean signed error (drift)
        // ---- manipulation check, computed from the drive levels actually delivered ----
        // Fraction of the total drive that went to the body-patch cells, and their mean level
        // relative to the surround's.  Without these two numbers a drive model can silently
        // fail to implement the manipulation it claims to implement: an earlier version of
        // YawLevel gave the body patch the world's full rotation signal, so the "slip-free
        // body patch" arm was bit-for-bit the natural condition apart from Bernoulli noise,
        // and its null result was vacuous.  Any arm whose PatchLevelRatio is not clearly
        // below the natural ratio is not the arm its name says it is.
        public float PatchDriveFraction;   // sum(level over patch) / sum(level over pool)
        public float PatchLevelRatio;      // mean patch level / mean surround level
    }

    // ------------------------------------------------------------------ drive profile
    /// <summary>
    /// Per-cell drive level d_i(t) in [0,1] for one arm.  The normalisation makes the
    /// expected total injected spike count identical in every driven arm:
    ///
    ///   sum_i d_i = n * F(t) for all arms, solved PER STEP against the signals actually
    ///   delivered, and never clipped: the injected probability is pMax * d_i with
    ///   pMax = 150 Hz * 0.5 ms = 0.075, so d_i can reach ~13 before the Bernoulli draw
    ///   saturates.  Two earlier versions of this file did not balance:
    ///     * they clamped the multiplied level at 1.0, so every step in which the surround
    ///       asked for more was silently truncated (the arms then differed by 0.5-27% in
    ///       total injected events), and
    ///     * the de-correlated patch ran on an independent process with a different mean.
    ///   Both are gone: the de-correlated arm now replays a BLOCK-SHUFFLED copy of the same
    ///   signal (identical marginal distribution, so identical expected drive), and the
    ///   surround is scaled by whatever is needed to make the per-step total come out at
    ///   n * F(t) exactly.
    /// </summary>
    private sealed class DriveProfile
    {
        private readonly bool[] _isPatch;
        private readonly float[] _pref;     // preferred yaw direction per cell (+1 / -1)
        public readonly bool Driven;
        public readonly int Mode;
        private readonly int _n;

        public DriveProfile(Arm arm, int[] pool, bool[] patchOf, CircuitPreview.BrainData d, Random rng)
        {
            Driven = arm.Driven; Mode = arm.Mode;
            _n = pool.Length;
            _isPatch = (bool[])patchOf.Clone();
            // Preferred direction proxy: the two lobula plates are mirror-symmetric, so a
            // rotation about the vertical axis excites the cells on one side of the head and
            // silences the other.  The blob carries no tuning curves, so the side of the
            // midline stands in for the sign of the preferred yaw direction.
            _pref = new float[pool.Length];
            for (int k = 0; k < pool.Length; k++) _pref[k] = IsPositiveSide(d, pool[k]) ? 1f : -1f;
        }

        /// <summary>Per-cell drive level for global optic flow.  <paramref name="flow"/> is the
        /// retinal slip every cell sees; <paramref name="patchFlow"/> is what the body-covered
        /// cells see (their own signal in the de-correlated arm).  The surround level is solved
        /// so that the total equals n * flow exactly.</summary>
        public void Level(float flow, float patchFlow, float[] dst)
        {
            if (Mode == ModeUniform)
            {
                for (int k = 0; k < _n; k++) dst[k] = flow;
                return;
            }
            double patchSum = 0;
            int nPatch = 0;
            for (int k = 0; k < _n; k++)
                if (_isPatch[k]) { patchSum += BodySlip * patchFlow; nPatch++; }
            int nRest = _n - nPatch;
            double budget = _n * (double)flow;
            // the patch may never absorb more than the whole budget (same reason as in
            // YawLevel: the de-correlated signal can spike while the real flow is low)
            float patchCap = patchSum > budget && patchSum > 1e-9
                ? (float)(budget / patchSum) : 1f;
            patchSum *= patchCap;
            float rest = nRest == 0 ? flow : (float)((budget - patchSum) / nRest);
            if (rest < 0f) rest = 0f;
            for (int k = 0; k < _n; k++)
                dst[k] = _isPatch[k] ? BodySlip * patchFlow * patchCap : rest;
        }

        /// <summary>Slip level per cell for a rotation of the world past the fly at rate
        /// <paramref name="yaw"/> (positive = turning right).  Cells whose preferred direction
        /// matches the turn are driven, the others sit at the baseline, and the surround is
        /// solved per step so that the total drive equals the natural total exactly.
        ///
        /// <paramref name="slipPatch"/> is the rotation signal the BODY-COVERED cells carry,
        /// which is not the world's rotation: a body-locked region has no slip of its own
        /// (BodySlip = 0.1 of the world's, the same factor the optic-flow drive uses), and the
        /// conflict-dose arms replace that residual slip with a block-shuffled copy of the
        /// waveform.  This parameter is what makes the manipulation real -- an earlier version
        /// of this method used the world's rotation for the patch as well, so at alpha = 0 the
        /// slip-free arm was numerically identical to the natural arm and its null was
        /// vacuous.  Trial.PatchLevelRatio is reported for every run as the guard.</summary>
        public void YawLevel(float yaw, float slipPatch, float[] dst)
        {
            const float baseline = 0.12f;
            if (Mode == ModeUniform)
            {
                for (int k = 0; k < _n; k++)
                    dst[k] = baseline + (1f - baseline) * Math.Max(0f, _pref[k] * yaw);
                return;
            }
            double aboveRest = 0, target = 0, patchDelivered = 0;
            for (int k = 0; k < _n; k++)
            {
                float natural = baseline + (1f - baseline) * Math.Max(0f, _pref[k] * yaw);
                target += natural - baseline;
                if (_isPatch[k])
                    patchDelivered += (1f - baseline) * Math.Max(0f, _pref[k] * slipPatch);
                else
                    aboveRest += natural - baseline;
            }
            if (aboveRest < 1e-6)
            {
                for (int k = 0; k < _n; k++) dst[k] = baseline;
                return;
            }
            // The patch may not deliver more than the whole target on its own: in the
            // de-correlated arm the shuffled signal can be strong while the real turn is weak,
            // and then no scaling of the surround can bring the total back down (the earlier
            // version simply clamped the surround at zero and the arm delivered 0.6-2.1% MORE
            // than every other arm - a drive difference that produced a spurious "effect" in
            // the heading metrics).  The rectifier is linear in a non-negative factor, so
            // capping the patch by target/patchDelivered is exact.
            float patchCap = patchDelivered > target && patchDelivered > 1e-9
                ? (float)(target / patchDelivered) : 1f;
            patchDelivered *= patchCap;
            float scale = (float)Math.Max(0.0, (target - patchDelivered) / aboveRest);
            for (int k = 0; k < _n; k++)
            {
                if (_isPatch[k])
                    dst[k] = baseline + (1f - baseline) * Math.Max(0f, _pref[k] * slipPatch) * patchCap;
                else
                    dst[k] = baseline + (1f - baseline) * Math.Max(0f, _pref[k] * yaw) * scale;
            }
        }
    }

    // ------------------------------------------------------------------ dose response
    /// <summary>
    /// Dose-response: the same self-view manipulation at several body-patch fractions,
    /// nothing else changed.  A graded manipulation should move the readouts monotonically
    /// with the fraction of the visual pool that stops reporting slip; a step at one size
    /// only would not.  The 0 fraction is the natural condition (no patch) and is the
    /// reference point of the trend test.
    ///
    /// Trend test: Spearman rank correlation between the patch fraction and each readout at
    /// the trial level, with a permutation p over the fraction labels.
    /// </summary>
    internal static int RunDose(CircuitPreview.BrainData d, double kappa, int trials, float seconds,
                                float odor, bool heading, float[] fracs, string csvPrefix)
    {
        ScaleWeights(d, kappa);
        int[] pool = BuildVisualPool(d);
        FindMidline(d, pool);
        var pushPullW = new float[d.Cx.Length];
        PushPullWeights(d, pool, pushPullW);
        var arm = Arms.First(a => a.Id == "self");
        int nBins = Math.Max(20, (int)(seconds * 50f));

        Console.WriteLine($"dose response: {trials} trials per patch fraction, {seconds:0.#} s each, "
                          + $"{(heading ? "yaw push-pull" : "global optic flow")}, kappa = {kappa:0.###}\n");

        var perFrac = new List<(float Frac, List<Trial> Trials)>();
        var patches = new List<(float Frac, bool[] Patch)>();
        int seed = 777;
        foreach (float f in fracs)
        {
            bool[] patch = CompactPatch(d, pool, f);
            patches.Add((f, patch));
            PatchCheck(d, pool, patch, $"patch {f:0.###}");
            var list = new List<Trial>();
            for (int t = 0; t < trials; t++)
            {
                var rng = new Random(seed++);
                list.Add(OneTrial(d, arm, pool, patch, seconds, nBins, odor, rng, heading,
                                  pushPullW, t));
            }
            perFrac.Add((f, list));
            Console.WriteLine($"  frac {f:0.###} done");
        }

        // metric table
        var metrics = new (string Name, Func<Trial, float> Get)[]
        {
            ("cx_rate_hz", t => t.Rate),
            ("cx_active_fraction", t => t.ActiveFraction),
            ("ring_rate_hz", t => t.FamRate[1]),
            ("columnar_rate_hz", t => t.FamRate[2]),
            ("fanbody_rate_hz", t => t.FamRate[3]),
            ("other_rate_hz", t => t.FamRate[4]),
            ("dim", t => t.Dim),
            ("pop_rate_sd_hz", t => t.PopSd),
            ("bumpR", t => t.BumpR),
            ("tau_ms", t => t.TauMs),
            ("injected_events", t => t.InjectedEvents),
            ("pool_rate_hz", t => t.PoolRate),
        };
        if (heading)
            metrics = metrics.Concat(new (string, Func<Trial, float>)[]
            {
                ("ring_pc12_var", t => t.RingPc12Var),
                ("ring_loop", t => t.RingLoop),
                ("ring_lag_yaw_deg", t => t.TrackLagYawDeg),
                ("ring_track_gain_yaw", t => t.TrackGainYaw),
                ("cx_yaw_modulation_hz", t => t.YawModulation),
                ("cx_tuning_wire_corr", t => t.YawTuningWireCorr),
                ("ring_tuning_wire_corr", t => t.RingYawTuningWireCorr),
            }).ToArray();

        Console.WriteLine("\n" + "metric".PadRight(24)
                          + string.Join("", fracs.Select(f => $"frac={f:0.###}".PadLeft(20))));
        foreach (var (name, get) in metrics)
        {
            var line = new StringBuilder($"{name,-24}");
            foreach (var (f, list) in perFrac)
            {
                var v = list.Select(get).Where(x => !float.IsNaN(x) && !float.IsInfinity(x)).ToArray();
                line.Append(v.Length == 0 ? "-".PadLeft(20)
                    : $"{v.Average():F4}".PadLeft(20));
            }
            Console.WriteLine(line.ToString());
        }

        Console.WriteLine("\n" + "metric".PadRight(24) + "rho(frac)".PadLeft(12)
                          + "p_perm".PadLeft(12) + "slope/trial".PadLeft(14));
        var doseRows = new List<(string Metric, string Frac, double Mean, double Sd, double Sem,
                                 double Lo, double Hi, int N)>();
        foreach (var (name, get) in metrics)
        {
            var xs = new List<double>(); var ys = new List<double>();
            foreach (var (f, list) in perFrac)
            {
                var v = list.Select(get).Where(x => !float.IsNaN(x) && !float.IsInfinity(x)).ToArray();
                if (v.Length == 0) continue;
                double m = v.Average();
                double sd = v.Length > 1 ? Math.Sqrt(v.Select(x => (x - m) * (x - m)).Sum() / (v.Length - 1)) : 0;
                double sem = sd / Math.Sqrt(v.Length);
                double half = 2.262 * sem;       // t(0.975, 9)
                doseRows.Add((name, f.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture),
                              m, sd, sem, m - half, m + half, v.Length));
                foreach (double x in v) { xs.Add(f); ys.Add(x); }
            }
            double rho = Spearman(xs, ys);
            double p = PermSpearman(xs, ys);
            double slope = Slope(xs, ys);
            Console.WriteLine($"{name,-24}{rho,12:F3}{p,12:F4}{slope,14:G4}");
        }

        if (!string.IsNullOrEmpty(csvPrefix))
        {
            using (var w = new StreamWriter(csvPrefix + "-dose-trials.csv"))
            {
                w.Write("frac,trial");
                foreach (var (name, _) in metrics) w.Write("," + name);
                w.WriteLine();
                foreach (var (f, list) in perFrac)
                    for (int t = 0; t < list.Count; t++)
                    {
                        w.Write($"{f.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture)},{t}");
                        foreach (var (_, get) in metrics)
                            w.Write("," + get(list[t]).ToString("G6",
                                System.Globalization.CultureInfo.InvariantCulture));
                        w.WriteLine();
                    }
            }
            using (var w = new StreamWriter(csvPrefix + "-dose-summary.csv"))
            {
                w.WriteLine($"# kappa,{kappa}");
                w.WriteLine($"# trials_per_fraction,{trials}");
                w.WriteLine($"# seconds_per_trial,{seconds}");
                w.WriteLine($"# drive,{(heading ? "yaw_push_pull" : "global_optic_flow")}");
                w.WriteLine("metric,frac,n,mean,sd,sem,ci95_lo,ci95_hi");
                foreach (var r in doseRows)
                    w.WriteLine($"{r.Metric},{r.Frac},{r.N},{r.Mean:G6},{r.Sd:G6},{r.Sem:G6},{r.Lo:G6},{r.Hi:G6}");
            }
            using (var w = new StreamWriter(csvPrefix + "-dose-trend.csv"))
            {
                w.WriteLine("metric,spearman_rho_vs_fraction,p_perm_two_sided,ols_slope_per_unit_fraction,permutations");
                foreach (var (name, get) in metrics)
                {
                    var xs = new List<double>(); var ys = new List<double>();
                    foreach (var (f, list) in perFrac)
                        foreach (var tr in list)
                        {
                            float y = get(tr);
                            if (float.IsNaN(y) || float.IsInfinity(y)) continue;
                            xs.Add(f); ys.Add(y);
                        }
                    w.WriteLine($"{name},{Spearman(xs, ys):G6},{PermSpearman(xs, ys):G6},"
                                + $"{Slope(xs, ys):G6},2000");
                }
            }
            Console.WriteLine($"\nwrote {csvPrefix}-dose-trials.csv / -dose-summary.csv / -dose-trend.csv");
        }
        return 0;
    }

    /// <summary>Spearman rank correlation with average ranks for ties.</summary>
    private static double Spearman(List<double> x, List<double> y)
    {
        var rx = Ranks(x); var ry = Ranks(y);
        return Pearson(rx, ry);
    }

    private static double[] Ranks(List<double> v)
    {
        int n = v.Count;
        var idx = Enumerable.Range(0, n).OrderBy(i => v[i]).ToArray();
        var r = new double[n];
        int i0 = 0;
        while (i0 < n)
        {
            int j = i0;
            while (j + 1 < n && v[idx[j + 1]] == v[idx[i0]]) j++;
            double avg = (i0 + j) / 2.0 + 1.0;
            for (int k = i0; k <= j; k++) r[idx[k]] = avg;
            i0 = j + 1;
        }
        return r;
    }

    private static double Pearson(double[] a, double[] b)
    {
        int n = a.Length;
        double ma = a.Average(), mb = b.Average();
        double sa = 0, sb = 0, sab = 0;
        for (int i = 0; i < n; i++)
        {
            double da = a[i] - ma, db = b[i] - mb;
            sa += da * da; sb += db * db; sab += da * db;
        }
        return (sa > 1e-12 && sb > 1e-12) ? sab / Math.Sqrt(sa * sb) : 0.0;
    }

    private static double Slope(List<double> x, List<double> y)
    {
        double mx = x.Average(), my = y.Average();
        double sxx = 0, sxy = 0;
        for (int i = 0; i < x.Count; i++) { sxx += (x[i] - mx) * (x[i] - mx); sxy += (x[i] - mx) * (y[i] - my); }
        return sxx > 1e-12 ? sxy / sxx : 0.0;
    }

    /// <summary>Permutation p for the Spearman rho (fraction labels relabelled).</summary>
    private static double PermSpearman(List<double> x, List<double> y, int nPerm = 2000)
    {
        double obs = Math.Abs(Spearman(x, y));
        var rng = new Random(31337);
        var xs = new List<double>(x);
        int hit = 0;
        for (int it = 0; it < nPerm; it++)
        {
            for (int i = xs.Count - 1; i > 0; i--)
            {
                int j = rng.Next(i + 1);
                (xs[i], xs[j]) = (xs[j], xs[i]);
            }
            if (Math.Abs(Spearman(xs, y)) >= obs - 1e-12) hit++;
        }
        return (hit + 1.0) / (nPerm + 1.0);
    }

    // ------------------------------------------------------------------ calibration
    /// <summary>
    /// Calibrate the single free gain kappa.
    ///
    /// The connectome's native weight is w_syn = 0.275 mV per synapse and the threshold is
    /// 7 mV, so a neuron needs ~26 synapses to fire together inside one 5 ms window.  That
    /// is a real fly's operating point, but a 12000-neuron slice of a 166k-neuron CNS only
    /// carries the synapses *inside the slice* - every neuron is missing most of its real
    /// inputs (mean in-degree here is ~135, not ~900) - so with the native weight the
    /// circuit is silent and measures nothing.  kappa is the one free parameter that sets
    /// where the slice sits relative to threshold; it is chosen once, on the unstimulated
    /// circuit, to put the network in a spontaneously active, fluctuation-driven regime,
    /// and then held fixed for every arm of the experiment.  It scales weights,
    /// stimulation and resting tone together, so it is equivalent to expressing the
    /// threshold in the connectome's own weight units.
    /// </summary>
    internal static int RunSweep(CircuitPreview.BrainData d, double[] kappas, float seconds,
                                 float odor)
    {
        var baseline = (float[])d.Weight.Clone();
        var basePlast = (float[])d.BaseBase.Clone();
        Console.WriteLine($"{seconds:0.#} s per kappa, odour context {odor:0.##}, no resting tone.");
        Console.WriteLine("kappa scales CONNECTOME weights only - the stimulation event stays at the");
        Console.WriteLine("published w_syn * f_poi, so a stimulated cell fires at its Poisson rate and the");
        Console.WriteLine("only thing kappa changes is how far a spike travels through the connectome.\n");
        Console.WriteLine("kappa |" + string.Join("", SweepPops.Select(p => PopShort(p).PadLeft(8)))
                          + "   CXact%  active%");
        foreach (double k in kappas)
        {
            for (int e = 0; e < d.Syn; e++)
            {
                d.Weight[e] = baseline[e] * (float)k;
                d.BaseBase[e] = basePlast[e] * (float)k;
            }
            var c = new CircuitPreview.Circuit(d);
            var rng = new Random(4242);
            int steps = (int)(seconds * 1000f / c.Dt);
            float pMax = MaxStimHz * c.Dt / 1000f;
            float stimW = CircuitPreview.Circuit.WSyn * Fpoi;      // native: the paper's protocol
            // the visual drive is present in the calibration too, so the operating point is
            // the one the experiment actually runs in (natural optic flow, no self in view)
            float pVis = pMax * 0.5f;
            for (int s = 0; s < steps; s++)
            {
                for (int i = 0; i < d.Odor.Length; i++)
                    if (rng.NextDouble() < pMax * odor) c.Inject(d.Odor[i], stimW);
                for (int i = 0; i < d.SelfMotion.Length; i++)
                    if (rng.NextDouble() < pVis) c.Inject(d.SelfMotion[i], stimW);
                c.Step();
            }
            float windowSec = steps * c.Dt / 1000f;
            var line = new StringBuilder();
            int cxActive = 0, anyActive = 0;
            foreach (int p in SweepPops)
            {
                int n = 0; long sp = 0;
                for (int i = 0; i < d.N; i++) if (d.Pop[i] == p) { n++; sp += c.SpikeTotal[i]; }
                if (p == 11)
                    foreach (int i in d.Cx) if (c.SpikeTotal[i] > 0) cxActive++;
                line.Append((n == 0 ? 0f : sp / (float)n / windowSec).ToString("F2").PadLeft(8));
            }
            for (int i = 0; i < d.N; i++) if (c.SpikeTotal[i] > 0) anyActive++;
            Console.WriteLine($"{k,5:0.##} |{line}   {100.0 * cxActive / Math.Max(1, d.Cx.Length),6:F1}  "
                              + $"{100.0 * anyActive / d.N,6:F1}");

            // Mean synaptic conductance each pool is actually receiving: sum over incoming
            // synapses of weight x presynaptic rate x tau.  A neuron fires when this reaches
            // ~7 mV, so this number says which pools are starved and by how much - guessing
            // from population rates alone cannot distinguish "starved" from "inhibited".
            var rate = new float[d.N];
            for (int i = 0; i < d.N; i++) rate[i] = c.SpikeTotal[i] / windowSec;
            const int NPopulations = 12;
            var drive = new float[NPopulations];
            var driveExc = new float[NPopulations];
            var driveInh = new float[NPopulations];
            var cells = new int[NPopulations];
            for (int i = 0; i < d.N; i++) cells[d.Pop[i]]++;
            for (int i = 0; i < d.N; i++)
                for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
                {
                    int q = d.Pop[d.Target[e]];
                    float g = d.Weight[e] * rate[i] * CircuitPreview.Circuit.Tau;   // mV
                    drive[q] += g;
                    if (d.Weight[e] >= 0) driveExc[q] += g; else driveInh[q] += g;
                }
            var dl = new StringBuilder();
            foreach (int p in new[] { 3, 4, 5, 6, 7, 11 })
                if (cells[p] > 0)
                    dl.Append($"  {PopShort(p)}={drive[p] / cells[p]:F1}({driveExc[p] / cells[p]:F1}/{driveInh[p] / cells[p]:F1})");
            Console.WriteLine($"        mean input conductance mV (exc/inh):{dl}");
        }
        return 0;
    }

    /// <summary>Every population, including the unnamed bulk: the first sweep watched only
    /// the named pools and concluded the circuit was silent while the activity was sitting
    /// in the 4248 unlabelled neurons.</summary>
    private static readonly int[] SweepPops = { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 };

    private static string PopShort(int p) => p switch
    {
        1 => "sensory", 2 => "AL", 3 => "KC", 4 => "dopam", 5 => "MBON", 6 => "DN",
        7 => "motor", 10 => "LPTC", 11 => "CX", _ => "int",
    };

    internal static void ScaleWeights(CircuitPreview.BrainData d, double kappa)
    {
        if (Math.Abs(kappa - 1.0) < 1e-9) return;
        for (int e = 0; e < d.Syn; e++)
        {
            d.Weight[e] *= (float)kappa;
            d.BaseBase[e] *= (float)kappa;
        }
    }
    // ------------------------------------------------------------------ entry point
    internal static int Run(CircuitPreview.BrainData d, double kappa, int trials, float seconds,
                            float odor, int nPerm, bool heading, string csvPrefix = null,
                            bool withControls = false, bool withConflict = false)
    {
        if (withControls) Arms = Arms.Concat(ControlArms).ToArray();
        if (withConflict) Arms = Arms.Concat(ConflictArms).ToArray();
        ScaleWeights(d, kappa);
        Console.WriteLine($"kappa (connectome gain, calibrated) = {kappa:0.###}");
        Console.WriteLine($"circuit: {d.N} neurons, {d.Syn} synapses, CX readout {d.Cx.Length} "
                          + $"({SubfamilyCensus(d)})");
        Console.WriteLine($"drive model: {(heading
            ? "yaw push-pull - the fly turns, rotation-sensitive cells report the turn"
            : "global optic flow - the world sweeps past the whole eye")}");
        FindMidline(d, BuildVisualPool(d));

        // ---- the visual input pool and the body patch.
        // The pool is the set of cells a body-occluded region of the visual field can act
        // through: the rotation-sensitive cells themselves PLUS the connectome-derived relay
        // that carries visual information into the central complex (cells receiving from the
        // rotation pool and projecting onto the CX).  The patch is a compact anatomical
        // cluster of that pool (25%, standing in for the fraction of the field the body
        // covers); the lobula plate and its relays are retinotopically organised, so a
        // spatial cluster is a stand-in for a visual-field region.  Same rule in the mod
        // (World/SelfViewPatch).
        int[] pool = BuildVisualPool(d);
        if (pool.Length == 0) { Console.WriteLine("no visual pool in this blob"); return 1; }
        bool[] selfPatch = CompactPatch(d, pool, BodyFieldFraction);
        var shuffled = (bool[])selfPatch.Clone();
        Shuffle(shuffled, new Random(20260903));
        var randMatched = CxMatchedRandomPatch(d, pool, selfPatch, 20260904);
        Console.WriteLine($"visual pool {pool.Length} cells = self-motion {d.SelfMotion.Length} "
                          + $"+ CX relay {d.VisualRelay.Length}; body patch {selfPatch.Count(b => b)} cells "
                          + $"({100f * selfPatch.Count(b => b) / pool.Length:F0}%)\n");
        var patchCx = new Dictionary<string, (int Cells, long CxSyn, long RingSyn)>
        {
            ["self"] = PatchCheck(d, pool, selfPatch, "body patch (compact)"),
            ["shuffle"] = PatchCheck(d, pool, shuffled, "control patch (same size, random)"),
            ["randmat"] = PatchCheck(d, pool, randMatched, "control patch (CX-input matched)"),
            ["decorr"] = PatchCheck(d, pool, selfPatch, "decorr patch (= body patch)"),
            ["flow"] = (0, 0, 0),
            ["rest"] = (0, 0, 0),
        };
        // the conflict-dose arms use the same body patch, only their slip differs
        foreach (var a in ConflictArms)
            patchCx[a.Id] = patchCx["self"];
        Console.WriteLine();
        var byArm = new Dictionary<string, List<Trial>>();
        int seed = 12345;
        int nBins = Math.Max(20, (int)(seconds * 50f));   // 20 ms bins
        var pushPullW = new float[d.Cx.Length];
        PushPullWeights(d, pool, pushPullW);

        foreach (var arm in Arms)
        {
            var list = new List<Trial>();
            for (int t = 0; t < trials; t++)
            {
                bool[] patchOf = arm.Id switch
                {
                    "self" => selfPatch,
                    "decorr" => selfPatch,
                    "shuffle" => shuffled,
                    "randmat" => randMatched,
                    _ => selfPatch,
                };
                var rng = new Random(seed++);
                list.Add(OneTrial(d, arm, pool, patchOf, seconds, nBins, odor, rng, heading,
                                  pushPullW, t));
                Console.Write($"\r  {arm.Name,-24} trial {t + 1}/{trials}   ");
            }
            Console.WriteLine($"\r  {arm.Name,-24} done ({trials} trials)          ");
            byArm[arm.Id] = list;
        }

        Report(d, byArm, trials, seconds, nPerm, heading);
        WriteMatching(d, byArm, patchCx, csvPrefix);
        if (!string.IsNullOrEmpty(csvPrefix)) WriteCsv(csvPrefix, byArm, trials, seconds, odor,
                                                      kappa, heading, nPerm, d);
        return 0;
    }

    /// <summary>
    /// The manipulation check, in one table: how many cells each arm silences, how much CX
    /// input that removes, and how many events it actually delivered.  Every arm must land on
    /// the same delivered total (the surround is solved per step to force it); the CX-input
    /// column is the one the arms are ALLOWED to differ on, because that difference is the
    /// manipulation.  Written to &lt;prefix&gt;-matching.csv.
    /// </summary>
    private static void WriteMatching(CircuitPreview.BrainData d,
                                      Dictionary<string, List<Trial>> byArm,
                                      Dictionary<string, (int Cells, long CxSyn, long RingSyn)> patchCx,
                                      string csvPrefix)
    {
        if (byArm.Count == 0) return;
        double selfInj = byArm["self"].Average(t => (double)t.InjectedEvents);
        // denominator for the input-loss column: every synapse onto a CX cell in the circuit
        var isCx = new bool[d.N];
        foreach (int i in d.Cx) isCx[i] = true;
        long totalCx = 0;
        for (int i = 0; i < d.N; i++)
            for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
                if (isCx[d.Target[e]]) totalCx++;
        Console.WriteLine("\n=== 配平检查 (delivered = 实际注入事件/trial, ratio = /self) ===");
        Console.WriteLine("arm          patch_cells  cx_input_syn   ring_syn   delivered_mean"
                          + "   ratio_vs_self      expected      sd");
        var rows = new List<string>();
        foreach (var arm in Arms)
        {
            var list = byArm[arm.Id];
            var pc = patchCx.TryGetValue(arm.Id, out var v) ? v : (Cells: 0, CxSyn: 0L, RingSyn: 0L);
            double mean = list.Average(t => (double)t.InjectedEvents);
            double exp = list.Average(t => t.ExpectedEvents);
            double sd = list.Count > 1
                ? Math.Sqrt(list.Sum(t => (t.InjectedEvents - mean) * (t.InjectedEvents - mean))
                            / (list.Count - 1)) : 0;
            Console.WriteLine($"{arm.Id,-12} {pc.Cells,11} {pc.CxSyn,13} {pc.RingSyn,9} "
                              + $"{mean,16:F1} {mean / selfInj,15:F5} {exp,14:F1} {sd,7:F0}");
            rows.Add($"{arm.Id},{pc.Cells},{pc.CxSyn},{pc.RingSyn},{mean:G6},{mean / selfInj:F6},"
                     + $"{exp:G8},{sd:G6}");
        }
        if (!string.IsNullOrEmpty(csvPrefix))
        {
            using var w = new StreamWriter(csvPrefix + "-matching.csv");
            w.WriteLine("arm,patch_cells,cx_input_synapses,ring_input_synapses,delivered_events_mean,"
                        + "delivered_ratio_vs_self,delivered_sd");
            foreach (string r in rows) w.WriteLine(r);
            Console.WriteLine($"wrote {csvPrefix}-matching.csv");
        }
    }

    /// <summary>
    /// Raw numbers, no interpretation: one row per trial (so the reader can draw their own
    /// figures and run their own statistics) plus one row per arm x metric.
    /// </summary>
    private static void WriteCsv(string prefix, Dictionary<string, List<Trial>> byArm, int trials,
                                 float seconds, float odor, double kappa, bool heading, int nPerm,
                                 CircuitPreview.BrainData d)
    {
        var cols = new List<(string Name, Func<Trial, float> Get)>
        {
            ("pool_rate_hz", t => t.PoolRate),
            ("injected_events", t => t.InjectedEvents),
            ("cx_rate_hz", t => t.Rate),
            ("cx_active_fraction", t => t.ActiveFraction),
            ("ring_rate_hz", t => t.FamRate[1]),
            ("columnar_rate_hz", t => t.FamRate[2]),
            ("fanbody_rate_hz", t => t.FamRate[3]),
            ("other_rate_hz", t => t.FamRate[4]),
            ("ring_active_fraction", t => t.FamActive[1]),
            ("columnar_active_fraction", t => t.FamActive[2]),
            ("fanbody_active_fraction", t => t.FamActive[3]),
            ("other_active_fraction", t => t.FamActive[4]),
            ("pair_corr", t => t.PairCorr),
            ("tau_ms", t => t.TauMs),
            ("dim", t => t.Dim),
            ("pop_rate_sd_hz", t => t.PopSd),
            ("bumpR", t => t.BumpR),
            // manipulation check: 0 for arms with no body patch
            ("patch_drive_fraction", t => t.PatchDriveFraction),
            ("patch_level_ratio", t => t.PatchLevelRatio),
        };
        if (heading)
            cols.AddRange(new (string, Func<Trial, float>)[]
            {
                ("anat_gain_integral", t => t.HeadGain),
                ("anat_resid_deg", t => t.HeadResidDeg),
                ("anat_gain_yaw", t => t.RelayGain),
                ("turned_deg", t => t.TurnedDeg),
                ("ring_pc12_var", t => t.RingPc12Var),
                ("ring_loop", t => t.RingLoop),
                ("ring_track_gain_yaw", t => t.TrackGainYaw),
                ("ring_lag_yaw_deg", t => t.TrackLagYawDeg),
                ("ring_track_gain_head", t => t.TrackGainHead),
                ("ring_lag_head_deg", t => t.TrackLagHeadDeg),
                ("cx_yaw_modulation_hz", t => t.YawModulation),
                ("cx_tuning_wire_corr", t => t.YawTuningWireCorr),
                ("ring_tuning_wire_corr", t => t.RingYawTuningWireCorr),
                ("ring_ang_diffusion_deg", t => t.RingAngDiffusionDeg),
                ("ring_ang_ac1", t => t.RingAngAc1),
                ("steer_corr_yaw", t => t.SteerCorrYaw),
                ("steer_asym_sd_hz", t => t.SteerAsymSd),
                ("dn_rate_hz", t => t.DnRateL + t.DnRateR),
                ("loop_err_rms", t => t.LoopErrRms),
                ("loop_err_mean", t => t.LoopErrMean),
            });

        string trialPath = prefix + "-trials.csv";
        using (var w = new StreamWriter(trialPath))
        {
            w.Write("arm,trial");
            foreach (var (name, _) in cols) w.Write("," + name);
            w.WriteLine();
            foreach (var arm in Arms)
            {
                var list = byArm[arm.Id];
                for (int t = 0; t < list.Count; t++)
                {
                    w.Write($"{arm.Id},{t}");
                    foreach (var (_, get) in cols)
                        w.Write("," + get(list[t]).ToString("G6", System.Globalization.CultureInfo.InvariantCulture));
                    w.WriteLine();
                }
            }
        }

        string sumPath = prefix + "-summary.csv";
        using (var w = new StreamWriter(sumPath))
        {
            w.WriteLine($"# circuit_neurons,{d.N}");
            w.WriteLine($"# circuit_synapses,{d.Syn}");
            w.WriteLine($"# cx_readout_cells,{d.Cx.Length}");
            w.WriteLine($"# kappa,{kappa.ToString(System.Globalization.CultureInfo.InvariantCulture)}");
            w.WriteLine($"# trials_per_arm,{trials}");
            w.WriteLine($"# seconds_per_trial,{seconds.ToString(System.Globalization.CultureInfo.InvariantCulture)}");
            w.WriteLine($"# odour_context,{odor.ToString(System.Globalization.CultureInfo.InvariantCulture)}");
            w.WriteLine($"# drive,{(heading ? "yaw_push_pull" : "global_optic_flow")}");
            w.WriteLine($"# permutations,{nPerm}");
            w.Write("metric,arm,mean,sd,sem,n,d_vs_self,p_vs_self");
            w.WriteLine();
            foreach (var (name, get) in cols.Select(c => (c.Name, c.Get)))
            {
                var self = byArm["self"].Select(get).ToArray();
                foreach (var arm in Arms)
                {
                    var v = byArm[arm.Id].Select(get).ToArray();
                    double mean = v.Average();
                    double sd = v.Length > 1
                        ? Math.Sqrt(v.Select(x => (x - mean) * (x - mean)).Sum() / (v.Length - 1)) : 0;
                    string eff = arm.Id == "self" ? "" : CohensD(self, v).ToString("G4",
                        System.Globalization.CultureInfo.InvariantCulture);
                    string pv = arm.Id == "self" ? "" : PermTest(self, v, nPerm).ToString("G4",
                        System.Globalization.CultureInfo.InvariantCulture);
                    w.WriteLine($"{name},{arm.Id},{mean.ToString("G6", System.Globalization.CultureInfo.InvariantCulture)},"
                                + $"{sd.ToString("G6", System.Globalization.CultureInfo.InvariantCulture)},"
                                + $"{(sd / Math.Sqrt(v.Length)).ToString("G6", System.Globalization.CultureInfo.InvariantCulture)},"
                                + $"{v.Length},{eff},{pv}");
                }
            }
        }
        Console.WriteLine($"\nwrote {trialPath} and {sumPath}");
    }

    // ------------------------------------------------------------------ controls
    /// <summary>
    /// Positive controls and the signal-propagation check.  A null result is only
    /// interpretable if (a) the pipeline can detect a perturbation at all and (b) the
    /// manipulation demonstrably reaches the circuit being measured.  Both are measured here.
    ///
    /// PROPAGATION (anatomical): breadth-first hop counts from the driven visual pool into the
    /// central complex on the same graph the simulation runs.
    ///
    /// PROPAGATION (functional): a single synchronous volley - one event into every pool cell
    /// in the same step - and the CX spike histogram for the next 100 ms.  A route that exists
    /// anatomically but carries nothing would show no evoked response; this measures the
    /// latency, the peak and how many CX cells answer, at three values of kappa so a null
    /// cannot be blamed on the gain.
    ///
    /// POSITIVE CONTROLS (run with --controls, as extra arms):
    ///   drive0.5 / drive1.5  - the same visual pool, same structure, total drive scaled by
    ///                          0.5 / 1.5.  If the readouts do not move under this, the
    ///                          pipeline is dead and no null means anything.
    ///   synch                - identical expected total and identical cells, but the draws are
    ///                          common across cells (all cells in phase).  This changes only
    ///                          the temporal structure of the input, so it is the positive
    ///                          control for "structure is detectable through this pathway".
    /// </summary>
    internal static int RunPropagation(CircuitPreview.BrainData d, double kappa, float odor,
                                       double[] extraKappas)
    {
        int[] pool = BuildVisualPool(d);
        FindMidline(d, pool);
        var patch = CompactPatch(d, pool, BodyFieldFraction);

        // ---- anatomical reachability
        Console.WriteLine($"visual pool {pool.Length} cells -> CX readout {d.Cx.Length} cells");
        var isPool = new bool[d.N];
        foreach (int i in pool) isPool[i] = true;
        var isCx = new bool[d.N];
        foreach (int i in d.Cx) isCx[i] = true;

        var hop = new int[d.N];
        for (int i = 0; i < d.N; i++) hop[i] = -1;
        var frontier = new List<int>();
        foreach (int i in pool) { hop[i] = 0; frontier.Add(i); }
        var hist = new int[8];
        long cxAtHop = 0;
        for (int h = 1; h <= 6 && frontier.Count > 0; h++)
        {
            var next = new List<int>();
            foreach (int i in frontier)
                for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
                {
                    int j = d.Target[e];
                    if (hop[j] != -1) continue;
                    hop[j] = h;
                    next.Add(j);
                    if (isCx[j]) { hist[h]++; cxAtHop++; }
                }
            Console.WriteLine($"  hop {h}: {next.Count,7} newly reached, "
                              + $"{hist[h],5} of them CX  (cumulative CX reached {cxAtHop}/{d.Cx.Length} "
                              + $"= {100.0 * cxAtHop / d.Cx.Length:F1}%)");
            frontier = next;
        }
        long poolCxDirect = 0;
        for (int k = 0; k < pool.Length; k++)
        {
            int i = pool[k];
            for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
                if (isCx[d.Target[e]]) poolCxDirect++;
        }
        Console.WriteLine($"  direct pool -> CX synapses: {poolCxDirect}\n");

        // ---- functional: evoked volley.  Weights are rescaled from the native blob for each
        // kappa, so the three rows differ only in gain.
        var nativeW = (float[])d.Weight.Clone();
        var nativeP = (float[])d.BaseBase.Clone();
        Console.WriteLine("evoked volley (one event into every pool cell in the same step);"
                          + " counts are CX cells only, per model step (0.5 ms);"
                          + " latency = first step above baseline+3sd");
        Console.WriteLine("kappa  patch   baseline/step    peak/step  peak_at  latency   excess_20ms"
                          + "  responsive_CX");
        foreach (double k in new[] { kappa }.Concat(extraKappas ?? Array.Empty<double>()))
        {
            Array.Copy(nativeW, d.Weight, nativeW.Length);
            Array.Copy(nativeP, d.BaseBase, nativeP.Length);
            ScaleWeights(d, k);
            Volley(d, pool, null, k, odor, "flow");
            Volley(d, pool, patch, k, odor, "self");
        }
        Array.Copy(nativeW, d.Weight, nativeW.Length);
        Array.Copy(nativeP, d.BaseBase, nativeP.Length);
        return 0;
    }

    private static void Volley(CircuitPreview.BrainData d, int[] pool, bool[] patch, double kappa,
                               float odor, string label)
    {
        var c = new CircuitPreview.Circuit(d);
        var rng = new Random(4242);
        float pMax = MaxStimHz * c.Dt / 1000f;
        float stimW = CircuitPreview.Circuit.WSyn * Fpoi;
        const int pre = 200, post = 200;      // 100 ms each at 0.5 ms per step
        var preCx = new int[pre];             // CX spikes per step before the volley
        var postCx = new int[post];           // and after (CX cells only: the volley's own
                                              // spikes in the pool are not counted)
        var cellsFired = new HashSet<int>();
        var inPatch = new bool[pool.Length];
        if (patch != null)
            for (int k = 0; k < pool.Length; k++) inPatch[k] = patch[k];

        for (int s = 0; s < pre + post; s++)
        {
            if (odor > 0f)
                for (int k = 0; k < d.Odor.Length; k++)
                    if (rng.NextDouble() < pMax * odor) c.Inject(d.Odor[k], stimW);
            if (s == pre)
                for (int k = 0; k < pool.Length; k++)
                    if (!inPatch[k]) c.Inject(pool[k], stimW);
            c.Step();
            int cxSpikes = 0;
            foreach (int i in d.Cx) if (c.Spiked(i)) cxSpikes++;
            if (s < pre) preCx[s] = cxSpikes;
            else
            {
                postCx[s - pre] = cxSpikes;
                if (s - pre <= 40) foreach (int i in d.Cx) if (c.Spiked(i)) cellsFired.Add(i);
            }
        }
        double baseMean = preCx.Average();
        double baseSd = Math.Sqrt(preCx.Select(x => (x - baseMean) * (x - baseMean)).Sum() / (pre - 1));
        int peak = 0, peakStep = 0;
        for (int s = 0; s < post; s++) if (postCx[s] > peak) { peak = postCx[s]; peakStep = s; }
        int latency = -1;
        for (int s = 0; s < post; s++)
            if (postCx[s] > baseMean + 3 * baseSd) { latency = s; break; }
        double excess = postCx.Take(40).Sum() - baseMean * 40;
        Console.WriteLine($"{kappa,5:0}  {label,-7}{baseMean,12:F2}{peak,12}"
                          + $"{peakStep * 0.5,9:F1}ms{(latency < 0 ? "-" : (latency * 0.5).ToString("F1") + "ms"),9}"
                          + $"{excess,13:F0}{cellsFired.Count,10} ({100.0 * cellsFired.Count / d.Cx.Length:F1}%)");
    }

    // ------------------------------------------------------------------ one trial
    private static Trial OneTrial(CircuitPreview.BrainData d, Arm arm, int[] pool, bool[] patchOf,
                                  float seconds, int nBins, float odor, Random rng, bool heading,
                                  float[] pushPullW, int trialIndex)
    {
        var c = new CircuitPreview.Circuit(d);
        var profile = new DriveProfile(arm, pool, patchOf, d, rng);
        // Everything that is not the pool-injection structure is drawn from a SHARED
        // per-trial stream, so the stimulus itself is bit-identical in every arm: the
        // optic-flow / yaw series, its block-shuffled copy, the odour background and the
        // sampled CX pairs.  Only the pool Bernoulli draws use the arm-specific stream.
        // Without this the arms differed by ~0.1% purely because their noise realisations
        // differed, which is the same order as the effects being measured.
        var shared = new Random(90000 + trialIndex);
        var level = new float[pool.Length];
        float pMax = MaxStimHz * c.Dt / 1000f;
        float stimW = CircuitPreview.Circuit.WSyn * Fpoi;

        int steps = (int)(seconds * 1000f / c.Dt);      // 0.5 ms per step
        int warmup = steps / 2;                         // analyse the second half only
        int binSteps = Math.Max(1, (steps - warmup) / nBins);

        var cx = d.Cx;
        var state = new float[nBins][];
        for (int b = 0; b < nBins; b++) state[b] = new float[cx.Length];
        var prev = new long[cx.Length];

        // pairwise-correlation sample inside the CX
        var pairA = new List<int>(); var pairB = new List<int>();
        int nPairs = Math.Min(300, cx.Length * (cx.Length - 1) / 2);
        var seen = new HashSet<long>();
        while (pairA.Count < nPairs)
        {
            int a = shared.Next(cx.Length), b = shared.Next(cx.Length);
            if (a == b) continue;
            if (a > b) (a, b) = (b, a);
            if (!seen.Add((long)a * 100000 + b)) continue;
            pairA.Add(a); pairB.Add(b);
        }

        long injected = 0;
        double expected = 0;
        long poolSpikesAtWarmup = 0;
        double levelSum = 0, patchLevelSum = 0;
        int nPatchCells = 0, patchCellsSeen = 0;
        for (int k = 0; k < pool.Length; k++) if (patchOf[k]) nPatchCells++;
        // descending neurons split by side of the midline: their left-right difference is the
        // steering command the brain sends, so it is the behavioural readout of the same
        // heading computation the CX metrics describe
        var dnL = new List<int>();
        var dnR = new List<int>();
        for (int i = 0; i < d.N; i++)
            if (d.Pop[i] == 6)
            {
                if (IsPositiveSide(d, i)) dnR.Add(i); else dnL.Add(i);
            }
        var dnPrev = new long[dnL.Count + dnR.Count];
        var dnBinL = new float[nBins];
        var dnBinR = new float[nBins];
        var familyIdx = new List<int>[5];
        for (int f = 0; f < 5; f++) familyIdx[f] = new List<int>();
        for (int k = 0; k < cx.Length; k++) familyIdx[d.CxFamily[cx[k]]].Add(k);

        // heading bookkeeping: the turn command, the heading it integrates to, and the ring
        // readout per bin
        var bumpAng = new float[nBins];
        var trueHeading = new float[nBins];
        var yawAtBin = new float[nBins];
        float yaw = 0f, headingRad = 0f;
        float loopLp = 0f, yawCommand = 0f, loopDc = 0f;   // closed-loop controller state (per bin)
        double loopErr2 = 0, loopErrSum = 0;     // closed-loop tracking error accumulation
        int loopErrN = 0;
        var yawDecor = new float[1];
        for (int b = 0; b < nBins; b++) bumpAng[b] = float.NaN;

        // ---- the drive series are built up front, so the de-correlated arm can replay a
        // block-shuffled copy of the SAME series: identical marginal distribution (hence the
        // same expected drive, and an exact total once the surround is solved against it),
        // but no temporal alignment with the world.
        var driveSeries = new float[steps];
        var decorSeries = new float[steps];
        {
            float dtS = c.Dt / 1000f;
            for (int s = 0; s < steps; s++)
            {
                float tSec = s * dtS;
                driveSeries[s] = heading
                    ? Math.Clamp(0.5f * (float)Math.Sin(2 * Math.PI * ProbeHz * tSec)
                                 + 0.3f * (float)Math.Sin(2 * Math.PI * 0.6f * tSec + 0.7f)
                                 + 0.12f * (float)(shared.NextDouble() - 0.5), -1f, 1f)
                    : Math.Clamp(0.45f + 0.30f * (float)Math.Sin(2 * Math.PI * 0.7f * tSec)
                                 + 0.10f * (float)Math.Sin(2 * Math.PI * 2.3f * tSec + 1.1f)
                                 + 0.08f * (float)(shared.NextDouble() - 0.5), 0.05f, 1f);
            }
            const int block = 200;                 // 100 ms blocks
            int nBlocks = Math.Max(1, steps / block);
            var perm = Enumerable.Range(0, nBlocks).ToArray();
            for (int i = perm.Length - 1; i > 0; i--)
            {
                int j = shared.Next(i + 1);
                (perm[i], perm[j]) = (perm[j], perm[i]);
            }
            for (int b = 0; b < nBlocks; b++)
                for (int k = 0; k < block; k++)
                {
                    int src = perm[b] * block + k, dstIdx = b * block + k;
                    if (dstIdx < steps && src < steps) decorSeries[dstIdx] = driveSeries[src];
                }
        }

        for (int s = 0; s < steps; s++)
        {
            if (arm.Driven)
            {
                float signal = driveSeries[s];
                // closed loop: the retina carries the slip of a fly trying to hold the commanded
                // course.  Units matter: `signal` is a command level in [-1, 1] and the commanded
                // heading is taken as signal * 90 deg, while headingRad accumulates in RADIANS;
                // subtracting the two directly saturates the retina and the fly stops turning
                // (measured: turned_deg = 0.0 with steering fidelity at chance, 0.33).
                if (ClosedLoop && heading)
                {
                    signal = Math.Clamp(signal - headingRad / 1.5708f, -1f, 1f);
                    double e = driveSeries[s] * 1.5708 - headingRad;   // tracking error, radians
                    loopErr2 += e * e; loopErrSum += e; loopErrN++;
                }
                // The BODY-COVERED cells do not see the world's rotation: a body-locked region
                // has almost no slip (BodySlip, the same factor the optic-flow drive uses).
                // alpha replaces that residual slip with a block-shuffled copy of the same
                // waveform: alpha = 0 is "the body region reports no self-motion" (missing),
                // alpha = 1 is "the body region reports motion uncorrelated with the world"
                // (conflicting).  Blending the residual slip, not the world signal, is what
                // makes the two endpoints two different manipulations.
                float bodySlip = BodySlip * signal;
                float patchSignal = arm.Alpha > 0f
                    ? bodySlip + arm.Alpha * (decorSeries[s] - bodySlip)
                    : bodySlip;
                if (heading)
                {
                    yaw = ClosedLoop ? yawCommand : signal;
                    headingRad += (float)(yaw * MaxTurnRateDeg * c.Dt / 1000f * Math.PI / 180.0);
                    // The pool must be driven by the VISUAL signal, not by the motor command.
                    // Open loop they are the same variable (yaw = signal), which is why this call
                    // used to pass `yaw`.  In closed loop they differ, and passing the command here
                    // creates a dead fixed point: yawCommand starts at 0, so the surround receives
                    // no rotation drive, so the descending asymmetry stays 0, so the command stays
                    // 0 (measured before the fix: turned_deg = 0.0 and identical metrics for
                    // LoopGain = 500, 2000 and 8000).
                    profile.YawLevel(ClosedLoop ? signal : yaw, patchSignal, level);
                }
                else
                {
                    profile.Level(signal, patchSignal, level);
                }
                if (arm.Scale != 1f)
                    for (int k = 0; k < pool.Length; k++) level[k] *= arm.Scale;
                if (arm.Sync)
                {
                    // one common draw per step: all cells in phase, same expected total
                    double u = rng.NextDouble();
                    for (int k = 0; k < pool.Length; k++)
                    {
                        float p = pMax * level[k];
                        if (p <= 0f) continue;
                        if (p > 1f) p = 1f;
                        expected += p;
                        if (u < p) { c.Inject(pool[k], stimW); injected++; }
                    }
                }
                else
                {
                    for (int k = 0; k < pool.Length; k++)
                    {
                        float p = pMax * level[k];
                        if (p <= 0f) continue;
                        if (p > 1f) p = 1f;               // the draw saturates, never the level
                        expected += p;
                        if (rng.NextDouble() < p) { c.Inject(pool[k], stimW); injected++; }
                    }
                }
                // manipulation check: how much of the drive actually reached the body patch
                for (int k = 0; k < pool.Length; k++)
                {
                    levelSum += level[k];
                    if (patchOf[k]) patchLevelSum += level[k];
                }
                patchCellsSeen++;
            }
            // identical background in every arm: weak food odour context
            if (odor > 0f)
                for (int k = 0; k < d.Odor.Length; k++)
                    if (shared.NextDouble() < pMax * odor) c.Inject(d.Odor[k], stimW);

            c.Step();

            if (s == warmup)
            {
                for (int k = 0; k < cx.Length; k++) prev[k] = c.SpikeTotal[cx[k]];
                for (int k = 0; k < pool.Length; k++) poolSpikesAtWarmup += c.SpikeTotal[pool[k]];
                for (int k = 0; k < dnL.Count; k++) dnPrev[k] = c.SpikeTotal[dnL[k]];
                for (int k = 0; k < dnR.Count; k++) dnPrev[dnL.Count + k] = c.SpikeTotal[dnR[k]];
            }
            else if (s > warmup && (s - warmup) % binSteps == 0)
            {
                int b = (s - warmup) / binSteps - 1;
                if (b >= 0 && b < nBins)
                {
                    for (int k = 0; k < cx.Length; k++)
                    {
                        long now = c.SpikeTotal[cx[k]];
                        state[b][k] = now - prev[k];
                        prev[k] = now;
                    }
                    for (int k = 0; k < dnL.Count; k++)
                    {
                        long now = c.SpikeTotal[dnL[k]];
                        dnBinL[b] += now - dnPrev[k];
                        dnPrev[k] = now;
                    }
                    for (int k = 0; k < dnR.Count; k++)
                    {
                        long now = c.SpikeTotal[dnR[k]];
                        dnBinR[b] += now - dnPrev[dnL.Count + k];
                        dnPrev[dnL.Count + k] = now;
                    }
                    trueHeading[b] = headingRad;
                    yawAtBin[b] = yaw;
                    // closed-loop controller: the previous bin's descending left-right asymmetry
                    // (already counted above) becomes the turn command for the next bin
                    if (ClosedLoop && heading)
                    {
                        float steer = (dnBinR[b] - dnBinL[b]) / Math.Max(1, dnL.Count + dnR.Count);
                        // POSITIVE feedback, with a slow filter.  The descending asymmetry encodes
                        // the rotation the eye senses, which in closed loop IS the heading error, so
                        // `yaw = +k * error` is the stabilising sign: with -k the fly turns away
                        // from the commanded course and diverges (measured loop_err_rms = 2.53 rad
                        // against 0.50 for +k).  But at alpha = 0.5 per 20 ms bin the loop updates
                        // faster than the DN asymmetry is informative, so the command flips sign
                        // every bin and the fly only jitters around zero heading -- measured RMS
                        // 0.50 rad for every k tried, which is exactly the RMS of the commanded
                        // heading itself, i.e. no tracking.  Hence alpha = 0.1 (tau ~ 200 ms):
                        // integrate the asymmetry over many bins before turning it into a command.
                        // The DN asymmetry is sparse (2-8 spikes per 20 ms bin across ~59 cells per
                        // side) and has a small DC imbalance between the two sides that has nothing
                        // to do with the heading error.  Amplifying it directly pins the command at
                        // full turn (measured: steer ~ +/-0.03 with alternating sign around a mean
                        // of -0.01, so k = 2000 gives yaw = -1.000 for every bin -- the fly holds a
                        // constant turn instead of tracking).  A slow estimate of that bias is
                        // therefore subtracted before the gain: the controller drives the DEVIATION
                        // of the asymmetry from its own operating point, not its absolute value.
                        loopDc += (steer - loopDc) * 0.03f;
                        float dev = steer - loopDc;
                        loopLp += (dev - loopLp) * 0.1f;
                        yawCommand = Math.Clamp(LoopGain * loopLp, -1f, 1f);
                        // diagnostic (results/CLOSED-LOOP-PLAN.md): is the asymmetry informative
                        // at all?  |steer| ~ 1e-3 means it is buried in Bernoulli noise; a healthy
                        // mean with sign flips means the left/right split disagrees with the pool's
                        if (b % 10 == 0)
                            Console.WriteLine($"  cl b={b,3} dnL={dnBinL[b],6:F1} dnR={dnBinR[b],6:F1} "
                                              + $"steer={steer,9:E2} dc={loopDc,9:E2} lp={loopLp,9:E2} yaw={yawCommand,6:F3}");
                    }
                }
            }
        }

        // ---- metrics over the analysis window
        var tr = new Trial { ArmId = arm.Id, InjectedEvents = injected, ExpectedEvents = expected };
        if (patchCellsSeen > 0 && levelSum > 0)
        {
            tr.PatchDriveFraction = (float)(patchLevelSum / levelSum);
            double meanPatch = patchLevelSum / nPatchCells;
            double meanRest = (levelSum - patchLevelSum) / Math.Max(1, pool.Length - nPatchCells);
            tr.PatchLevelRatio = meanRest > 1e-12 ? (float)(meanPatch / meanRest) : 0f;
        }
        float windowSec = (steps - warmup) * c.Dt / 1000f;
        float windowSecPerBin = windowSec / nBins;
        long poolSpikes = 0;
        for (int k = 0; k < pool.Length; k++) poolSpikes += c.SpikeTotal[pool[k]];
        tr.PoolRate = (poolSpikes - poolSpikesAtWarmup) / (float)pool.Length / windowSec;

        var rates = new float[cx.Length];
        for (int k = 0; k < cx.Length; k++)
        {
            long total = 0;
            for (int b = 0; b < nBins; b++) total += (long)state[b][k];
            rates[k] = total / windowSec;
        }
        tr.Rate = rates.Average();
        tr.ActiveFraction = rates.Count(r => r > 0.5f) / (float)cx.Length;

        for (int f = 0; f < 5; f++)
        {
            var idx = familyIdx[f];
            if (idx.Count == 0) continue;
            float sum = 0; int act = 0;
            foreach (int k in idx) { sum += rates[k]; if (rates[k] > 0.5f) act++; }
            tr.FamRate[f] = sum / idx.Count;
            tr.FamActive[f] = act / (float)idx.Count;
        }

        // population state metrics
        ComputeStateMetrics(state, nBins, cx.Length, tr, pairA, pairB);

        // ring population vector (only meaningful if the EPG/PEG somas really form a ring)
        tr.BumpR = RingReadout(d, state, nBins, bumpAng);
        if (heading)
        {
            // (a) anatomical angle from the soma-derived ring plane - kept for comparison
            FitHeading(bumpAng, trueHeading, out float gainI, out float residI);
            FitHeading(bumpAng, yawAtBin, out float gainY, out _);
            tr.HeadGain = gainI;
            tr.HeadResidDeg = residI * 180f / (float)Math.PI;
            tr.RelayGain = gainY;
            tr.TurnedDeg = (trueHeading[nBins - 1] - trueHeading[0]) * 180f / (float)Math.PI;
            if (loopErrN > 0)
            {
                tr.LoopErrRms = (float)Math.Sqrt(loopErr2 / loopErrN);
                tr.LoopErrMean = (float)(loopErrSum / loopErrN);
            }

            // (b) the ring read out of its own state trajectory (top-2 PCs), which is the
            // measurement that does not depend on guessing the ring's anatomy
            var ringPos = new List<int>();
            for (int k = 0; k < cx.Length; k++) if (d.CxFamily[cx[k]] == 1) ringPos.Add(k);
            RingStateAnalysis(state, nBins, ringPos.ToArray(), yawAtBin, trueHeading, tr);

            // (c) the connectome's own direction readout: how each cell's yaw tuning relates
            // to the push-pull weight its wiring gives it.  This is the metric that can see a
            // change in direction coding; a raw rate comparison cannot.
            YawTuningAnalysis(state, nBins, yawAtBin, pushPullW, ringPos.ToArray(), tr);

            // (d) mechanism and behaviour: is the ring angle noisier (diffusion) and does the
            // steering command still follow the turn?
            RingAngleStability(bumpAng, yawAtBin, tr);
            SteeringReadout(dnBinL, dnBinR, yawAtBin, windowSecPerBin, tr);
        }
        return tr;
    }

    private static void ComputeStateMetrics(float[][] state, int nBins, int nCell, Trial tr,
                                            List<int> pairA, List<int> pairB)
    {
        // z-score each cell over bins
        var mean = new float[nCell]; var sd = new float[nCell];
        for (int k = 0; k < nCell; k++)
        {
            float m = 0; for (int b = 0; b < nBins; b++) m += state[b][k];
            m /= nBins; mean[k] = m;
            float v = 0; for (int b = 0; b < nBins; b++) { float dv = state[b][k] - m; v += dv * dv; }
            sd[k] = (float)Math.Sqrt(v / Math.Max(1, nBins - 1)) + 1e-6f;
        }

        // population mean rate per bin: mean and SD (fluctuation amplitude)
        var popRateBin = new float[nBins];
        for (int b = 0; b < nBins; b++)
        {
            float s = 0; for (int k = 0; k < nCell; k++) s += state[b][k];
            popRateBin[b] = s / nCell * 50f;    // bins are 20 ms -> Hz
        }
        float pm = popRateBin.Average();
        tr.PopSd = (float)Math.Sqrt(popRateBin.Select(x => (x - pm) * (x - pm)).Average());

        // mean pairwise correlation over the sampled pairs
        double rSum = 0;
        for (int p = 0; p < pairA.Count; p++)
        {
            int i = pairA[p], j = pairB[p];
            double num = 0;
            for (int b = 0; b < nBins; b++)
                num += ((state[b][i] - mean[i]) / sd[i]) * ((state[b][j] - mean[j]) / sd[j]);
            rSum += num / Math.Max(1, nBins - 1);
        }
        tr.PairCorr = pairA.Count == 0 ? 0f : (float)(rSum / pairA.Count);

        // integrated autocorrelation time of the mean z-scored population state
        var z = new float[nBins];
        for (int b = 0; b < nBins; b++)
        {
            float s = 0;
            for (int k = 0; k < nCell; k++) s += (state[b][k] - mean[k]) / sd[k];
            z[b] = s / nCell;
        }
        float zVar = 0; for (int b = 0; b < nBins; b++) zVar += z[b] * z[b];
        if (zVar > 1e-9f)
        {
            float tau = 0;
            for (int lag = 0; lag < Math.Min(30, nBins / 2); lag++)
            {
                double ac = 0;
                for (int b = 0; b + lag < nBins; b++) ac += z[b] * z[b + lag];
                ac /= zVar;
                tau += (float)Math.Max(0, ac) * 20f;      // 20 ms per bin
            }
            tr.TauMs = tau;
        }

        // participation ratio from the bin-space Gram matrix (same non-zero spectrum as the
        // cell-space covariance, and nBins << nCell keeps it cheap)
        int nb = nBins;
        var g = new float[nb, nb];
        for (int a = 0; a < nb; a++)
            for (int b = a; b < nb; b++)
            {
                double s = 0;
                for (int k = 0; k < nCell; k++)
                    s += ((state[a][k] - mean[k]) / sd[k]) * ((state[b][k] - mean[k]) / sd[k]);
                g[a, b] = g[b, a] = (float)(s / nb);
            }
        var ev = JacobiEigen(g, nb);
        double sum = 0, sum2 = 0;
        foreach (var l in ev) { if (l > 1e-6) { sum += l; sum2 += l * l; } }
        tr.Dim = sum2 > 0 ? (float)(sum * sum / sum2) : 0f;
    }

    /// <summary>
    /// Amplitude (resultant length) of the activity-weighted population vector over the
    /// EPG/PEG ring cells, using the ring plane recovered from the somas themselves
    /// (the two dominant axes of the soma point cloud).  0 = no bump.
    /// </summary>
    private static float RingVector(CircuitPreview.BrainData d, float[][] state, int nBins)
    {
        var tmp = new float[nBins];
        return RingReadout(d, state, nBins, tmp);
    }

    /// <summary>
    /// Ring population vector per 20 ms bin.  Returns the mean amplitude R and writes the
    /// circular-mean angle of each bin into <paramref name="angOut"/> (NaN for empty bins).
    /// The plane of the ring is recovered from the somas themselves (two leading principal
    /// axes of the EPG/PEG point cloud), so no anatomical atlas is baked in: if these cells
    /// really sit around the ellipsoid body, the recovered plane is the plane of the ring.
    /// </summary>
    private static float RingReadout(CircuitPreview.BrainData d, float[][] state, int nBins,
                                     float[] angOut)
    {
        var ring = new List<int>();
        for (int k = 0; k < d.Cx.Length; k++)
            if (d.CxFamily[d.Cx[k]] == 1) ring.Add(d.Cx[k]);
        if (ring.Count < 12) return 0f;

        var pos = new Dictionary<int, int>(d.Cx.Length);
        for (int k = 0; k < d.Cx.Length; k++) pos[d.Cx[k]] = k;

        // centre and the two principal axes of the soma cloud
        double cx = 0, cy = 0, cz = 0;
        foreach (int i in ring) { cx += d.Soma[i * 3]; cy += d.Soma[i * 3 + 1]; cz += d.Soma[i * 3 + 2]; }
        cx /= ring.Count; cy /= ring.Count; cz /= ring.Count;
        var cov = new float[3, 3];
        foreach (int i in ring)
        {
            float[] p = { d.Soma[i * 3] - (float)cx, d.Soma[i * 3 + 1] - (float)cy, d.Soma[i * 3 + 2] - (float)cz };
            for (int a = 0; a < 3; a++) for (int b = 0; b < 3; b++) cov[a, b] += p[a] * p[b];
        }
        var ev = JacobiEigen(cov, 3);
        // the two leading eigenvectors by power iteration (plane of the ring)
        float[] v1 = PowerVector(cov, null), v2 = PowerVector(cov, v1);

        var ang = new float[ring.Count];
        for (int k = 0; k < ring.Count; k++)
        {
            int i = ring[k];
            float[] p = { d.Soma[i * 3] - (float)cx, d.Soma[i * 3 + 1] - (float)cy, d.Soma[i * 3 + 2] - (float)cz };
            float a = p[0] * v1[0] + p[1] * v1[1] + p[2] * v1[2];
            float b = p[0] * v2[0] + p[1] * v2[1] + p[2] * v2[2];
            ang[k] = (float)Math.Atan2(b, a);
        }

        // activity-weighted resultant length, averaged over bins
        float rSum = 0; int used = 0;
        for (int bin = 0; bin < nBins; bin++)
        {
            double sx = 0, sy = 0, sw = 0;
            for (int k = 0; k < ring.Count; k++)
            {
                float w = state[bin][pos[ring[k]]];
                sw += w; sx += w * Math.Cos(ang[k]); sy += w * Math.Sin(ang[k]);
            }
            if (sw <= 1e-6) { angOut[bin] = float.NaN; continue; }
            angOut[bin] = (float)Math.Atan2(sy, sx);
            rSum += (float)Math.Sqrt(sx * sx + sy * sy) / (float)sw;
            used++;
        }
        return used == 0 ? 0f : rSum / used;
    }

    /// <summary>
    /// Fit the ring's heading estimate against the true heading the fly has turned through.
    ///
    /// The map from a position on the ring to a heading is not in the connectome, and the
    /// plane recovered from the somas has an arbitrary origin and handedness, so the two
    /// series are compared up to an affine map: the slope is the path-integration GAIN
    /// (1 = the bump tracks the turn exactly, &lt;1 = the estimate under-integrates, which
    /// is what a blind spot in the rotation input should produce) and the residual RMS is
    /// how noisy the tracking is after the best affine fit.  Reported as |gain| with the
    /// sign convention left open.
    /// </summary>
    private static void FitHeading(float[] bumpedAng, float[] trueHeading, out float gain,
                                   out float residRms)
    {
        var es = new List<double>(); var ts = new List<double>();
        double prevE = 0, prevT = 0; bool first = true;
        for (int b = 0; b < bumpedAng.Length; b++)
        {
            if (float.IsNaN(bumpedAng[b])) continue;
            double e = bumpedAng[b], t = trueHeading[b];
            if (!first)
            {
                // unwrap both series so an accumulated turn is not aliased by the 2*pi wrap
                e = prevE + Wrap(e - prevE);
                t = prevT + Wrap(t - prevT);
            }
            es.Add(e); ts.Add(t); prevE = e; prevT = t; first = false;
        }
        gain = 0; residRms = float.NaN;
        if (es.Count < 8) return;
        double mt = ts.Average(), me = es.Average();
        double sxy = 0, sxx = 0;
        for (int i = 0; i < es.Count; i++) { sxy += (ts[i] - mt) * (es[i] - me); sxx += (ts[i] - mt) * (ts[i] - mt); }
        if (sxx < 1e-9) return;
        double g = sxy / sxx;
        double ss = 0;
        for (int i = 0; i < es.Count; i++)
        {
            double r = es[i] - me - g * (ts[i] - mt);
            ss += r * r;
        }
        gain = (float)Math.Abs(g);
        residRms = (float)Math.Sqrt(ss / es.Count);
    }

    private static double Wrap(double a)
    {
        while (a > Math.PI) a -= 2 * Math.PI;
        while (a < -Math.PI) a += 2 * Math.PI;
        return a;
    }

    // ------------------------------------------------------------------ midline
    private static int _midAxis = -1;
    private static double _midValue;

    /// <summary>
    /// Which axis is the fly's left-right (mirror) axis, and where is its midline?
    ///
    /// This matters more than it looks.  The rotation drive is push-pull: turning right
    /// excites the cells on one side of the head and silences the other, and the two lobula
    /// plates are mirror images.  The first version of this experiment used "soma_x >= 0" as
    /// the side proxy - but MaleCNS soma coordinates are voxel coordinates from the image
    /// volume, i.e. ALL POSITIVE, so every cell was assigned to the same side, the push-pull
    /// collapsed into a uniform rate change, and the direction test dutifully reported
    /// corr(right, left) = +0.86: the CX "responding the same way to both turn directions".
    /// That was an artefact of the drive, not a property of the circuit.
    ///
    /// The axis is found from the data instead: the CNS is bilaterally symmetric, so the
    /// mirror axis is the one about whose median the soma distribution is most symmetric
    /// (compared by a two-sample KS statistic between the deviations on either side).
    /// </summary>
    internal static void FindMidline(CircuitPreview.BrainData d, int[] pool)
    {
        if (_midAxis >= 0) return;
        // Which axis separates the fly's two eyes?  Split the visual pool in two along each
        // axis (best 1-D 2-means) and keep the axis with the largest between-group variance:
        // the two lobula plates are the most lateral structures in the head, so the
        // left-right axis is the one that pulls the pool apart most cleanly.  Point-cloud
        // mirror symmetry was tried first and was not decisive (all three axes scored
        // similarly - a fly CNS is roughly ellipsoidal), which is exactly why the choice is
        // made on the cells the experiment drives.
        int bestAxis = 0;
        double bestScore = -1, bestMid = 0;
        var coords = new double[pool.Length];
        for (int a = 0; a < 3; a++)
        {
            for (int k = 0; k < pool.Length; k++) coords[k] = d.Soma[pool[k] * 3 + a];
            Array.Sort(coords);
            double total = 0, mean = coords.Average();
            for (int k = 0; k < coords.Length; k++) total += (coords[k] - mean) * (coords[k] - mean);
            double bestBetween = -1, bestSplit = coords[0];
            double runSum = 0;
            for (int k = 0; k < coords.Length - 1; k++)
            {
                runSum += coords[k];
                int n1 = k + 1, n2 = coords.Length - n1;
                double m1 = runSum / n1, m2 = (runSum2(coords) - runSum) / n2;
                double between = n1 * (m1 - mean) * (m1 - mean) + n2 * (m2 - mean) * (m2 - mean);
                if (between > bestBetween)
                {
                    bestBetween = between;
                    bestSplit = 0.5 * (coords[k] + coords[k + 1]);
                }
            }
            double score = total > 0 ? bestBetween / total : 0;
            Console.WriteLine($"   axis {("xyz")[a]}: 2-means separation {score:F3} (split at {bestSplit:F1})");
            if (score > bestScore) { bestScore = score; bestAxis = a; bestMid = bestSplit; }
        }
        _midAxis = bestAxis;
        _midValue = bestMid;
        int l = 0, r = 0;
        foreach (int i in pool)
        {
            if (d.Soma[i * 3 + bestAxis] > bestMid) r++; else l++;
        }
        Console.WriteLine($"   -> left-right axis = {("xyz")[bestAxis]} at {bestMid:F1}; "
                          + $"visual pool splits {l} / {r}\n");

        static double runSum2(double[] v)
        {
            double s = 0;
            foreach (double x in v) s += x;
            return s;
        }
    }

    /// <summary>True if the neuron sits on the positive side of the midline.</summary>
    internal static bool IsPositiveSide(CircuitPreview.BrainData d, int neuron)
    {
        return d.Soma[neuron * 3 + _midAxis] > _midValue;
    }

    // ------------------------------------------------------------------ push-pull wiring
    /// <summary>
    /// Can this circuit represent the SIGN of rotation at all?
    ///
    /// The direction test showed the visual pool itself flipping with the turn
    /// (corr(right,left) = -0.23, as it must) while the central complex did not (+0.81): the
    /// CX responded to "the world is moving" without encoding which way.  There are two very
    /// different reasons for that, and they call for opposite conclusions:
    ///
    ///   (a) the wiring cannot do it - both sides of the head project onto the same CX cells
    ///       with the SAME sign, so the mirror-symmetric input simply sums and only its
    ///       magnitude survives.  Then no experiment on this slice can perturb direction
    ///       coding, and the slice needs the missing pathway.
    ///   (b) the wiring can do it - some CX cells receive excitation from one side and
    ///       inhibition from the other (true push-pull), and the loss is a matter of regime
    ///       (gain, thresholds, competing input), which is fixable.
    ///
    /// This counts, for every CX cell, the excitatory and inhibitory synapses it receives from
    /// each side of the midline and reports how many cells have opposite-sign drive from the
    /// two sides.
    /// </summary>
    internal static int RunPushPull(CircuitPreview.BrainData d, double kappa)
    {
        ScaleWeights(d, kappa);
        int[] pool = BuildVisualPool(d);
        FindMidline(d, pool);
        var inPool = new bool[d.N];
        foreach (int i in pool) inPool[i] = true;
        var side = new bool[d.N];
        foreach (int i in pool) side[i] = IsPositiveSide(d, i);

        int nCx = 0, bothSides = 0, pushPull = 0, sameExc = 0, sameInh = 0;
        int ringN = 0, ringBoth = 0, ringPushPull = 0;
        double sumAbsImbalance = 0;
        for (int k = 0; k < d.Cx.Length; k++)
        {
            int j = d.Cx[k];
            double eA = 0, iA = 0, eB = 0, iB = 0;
            for (int i = 0; i < d.N; i++)
            {
                if (!inPool[i]) continue;
                for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
                {
                    if (d.Target[e] != j) continue;
                    bool pos = d.Weight[e] >= 0;
                    if (side[i]) { if (pos) eA += 1; else iA += 1; }
                    else { if (pos) eB += 1; else iB += 1; }
                }
            }
            nCx++;
            double netA = eA - iA, netB = eB - iB;
            double absA = eA + iA, absB = eB + iB;
            if (absA >= 3 && absB >= 3)
            {
                bothSides++;
                sumAbsImbalance += Math.Abs(netA) + Math.Abs(netB);
                if (netA * netB < 0) pushPull++;                    // opposite sign: real push-pull
                else if (netA > 0 && netB > 0) sameExc++;
                else if (netA < 0 && netB < 0) sameInh++;
            }
            if (d.CxFamily[j] == 1)
            {
                ringN++;
                if (absA >= 3 && absB >= 3)
                {
                    ringBoth++;
                    if (netA * netB < 0) ringPushPull++;
                }
            }
        }

        Console.WriteLine($"CX cells: {nCx};  receiving >=3 synapses from BOTH sides: {bothSides} "
                          + $"({100.0 * bothSides / Math.Max(1, nCx):F0}%)");
        Console.WriteLine($"  of those: push-pull (opposite net sign) {pushPull} "
                          + $"({100.0 * pushPull / Math.Max(1, bothSides):F0}%), "
                          + $"same sign excitatory {sameExc}, same sign inhibitory {sameInh}");
        Console.WriteLine($"  mean |net drive| summed over the two sides: "
                          + $"{sumAbsImbalance / Math.Max(1, bothSides):F1} synapses");
        Console.WriteLine($"ring EPG/PEG cells: {ringN}; both sides {ringBoth}; push-pull {ringPushPull} "
                          + $"({100.0 * ringPushPull / Math.Max(1, ringBoth):F0}%)");
        Console.WriteLine("\n(push-pull fraction near 0 => the two sides sum instead of opposing, so only"
                          + " |rotation| can reach the CX, whatever the experiment does)");
        return 0;
    }

    /// <summary>
    /// The push-pull weight of every CX cell: (excitation from one side + inhibition from the
    /// other) minus the mirror image of that.  A cell with w &gt; 0 is driven when the fly
    /// turns one way and suppressed when it turns the other, so projecting the population
    /// onto w is the readout the connectome itself defines for "which way am I turning" -
    /// no anatomical guess about the ring's coordinate is needed.
    /// </summary>
    private static void PushPullWeights(CircuitPreview.BrainData d, int[] pool, float[] w)
    {
        var inPool = new bool[d.N];
        foreach (int i in pool) inPool[i] = true;
        var side = new bool[d.N];
        foreach (int i in pool) side[i] = IsPositiveSide(d, i);
        for (int k = 0; k < d.Cx.Length; k++)
        {
            int j = d.Cx[k];
            double eA = 0, iA = 0, eB = 0, iB = 0;
            for (int i = 0; i < d.N; i++)
            {
                if (!inPool[i]) continue;
                for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
                {
                    if (d.Target[e] != j) continue;
                    bool pos = d.Weight[e] >= 0;
                    if (side[i]) { if (pos) eA++; else iA++; }
                    else { if (pos) eB++; else iB++; }
                }
            }
            w[k] = (float)((eA - iA) - (eB - iB));
        }
    }

    // ------------------------------------------------------------------ direction test
    /// <summary>
    /// Does the central complex carry the SIGN of rotation at all?
    ///
    /// Coordinate-free and cheap: drive a steady rightward turn, record each neuron's firing
    /// rate over the steady state; drive a steady leftward turn, record again.  A circuit that
    /// represents angular velocity must be antisymmetric - the right-turn state should be the
    /// mirror of the left-turn state, i.e. corr(right, left) clearly negative over the CX
    /// cells.  corr ~ 0 means the CX responds to "the world is moving" without encoding which
    /// way, which would explain why no heading-gain effect could be measured.
    ///
    /// Printed per population and for the ring alone.  If the sign is encoded, the self-view
    /// manipulation can be asked a sharp question: does the body-in-view patch bias it?
    /// </summary>
    internal static int RunAsymmetry(CircuitPreview.BrainData d, double kappa, float seconds,
                                     float odor, float yawMag, bool withPatch)
    {
        ScaleWeights(d, kappa);
        int[] pool = BuildVisualPool(d);
        FindMidline(d, pool);
        bool[] patch = withPatch ? CompactPatch(d, pool, BodyFieldFraction) : null;
        Console.WriteLine($"circuit {d.N} neurons; visual pool {pool.Length}; "
                          + $"patch {(patch == null ? "off (natural)" : patch.Count(b => b) + " cells")}; "
                          + $"|yaw| = {yawMag:0.##}, {seconds:0.#} s per direction\n");

        var right = RunSteady(d, pool, patch, +yawMag, seconds, odor, 11);
        var left = RunSteady(d, pool, patch, -yawMag, seconds, odor, 22);

        // (1) the connectome's own direction readout: project the CX state onto the push-pull
        // weights.  A circuit that encodes the sign of rotation must give opposite signs here
        // for the two directions, even if the raw rate vectors look similar.
        var w = new float[d.Cx.Length];
        PushPullWeights(d, pool, w);
        Console.WriteLine("readout                       D(right)   D(left)   index   corr(dr,w)");
        Projection("CX (push-pull projection)", d.Cx, w);
        Projection("  ring EPG/PEG only", d.Cx.Where(i => d.CxFamily[i] == 1).ToArray(), w);
        Projection("  non-ring CX", d.Cx.Where(i => d.CxFamily[i] != 1).ToArray(), w);

        void Projection(string name, int[] cells, float[] weights)
        {
            var pos = new Dictionary<int, int>(d.Cx.Length);
            for (int k = 0; k < d.Cx.Length; k++) pos[d.Cx[k]] = k;
            double dr = 0, dl = 0;
            var dw = new List<(double Dr, double W)>();
            foreach (int i in cells)
            {
                double wr = weights[pos[i]];
                double a = right[i], b = left[i];
                dr += wr * a; dl += wr * b;
                if (a + b > 0.5) dw.Add((a - b, wr));
            }
            double index = (Math.Abs(dr) + Math.Abs(dl)) > 1e-9
                ? (dr - dl) / (Math.Abs(dr) + Math.Abs(dl)) : 0;
            // does the observed direction selectivity of each cell follow its wiring?
            double mw = dw.Count == 0 ? 0 : dw.Average(t => t.W);
            double md = dw.Count == 0 ? 0 : dw.Average(t => t.Dr);
            double sww = 0, sdd = 0, swd = 0;
            foreach (var (Dr, W) in dw)
            {
                sww += (W - mw) * (W - mw); sdd += (Dr - md) * (Dr - md); swd += (W - mw) * (Dr - md);
            }
            double corr = (sww > 1e-12 && sdd > 1e-12) ? swd / Math.Sqrt(sww * sdd) : 0;
            Console.WriteLine($"{name,-28} {dr,9:F1} {dl,9:F1} {index,8:F3} {corr,10:F3}");
        }
        Console.WriteLine("(index > 0 = the CX state flips with the turn direction;"
                          + " corr > 0 = single cells are selective the way their wiring predicts)\n");

        Console.WriteLine("population            corr(R,L)   DSI      n(active)");
        Report2("all CX", d.Cx);
        for (int f = 1; f <= 4; f++)
        {
            var idx = d.Cx.Where(i => d.CxFamily[i] == f).ToArray();
            Report2(f switch { 1 => "ring EPG/PEG", 2 => "columnar", 3 => "fanbody", _ => "other" }, idx);
        }
        Report2("LPTC (input pool)", d.SelfMotion);
        Report2("whole circuit", Enumerable.Range(0, d.N).ToArray());

        void Report2(string name, int[] cells)
        {
            double mr = 0, ml = 0;
            foreach (int i in cells) { mr += right[i]; ml += left[i]; }
            mr /= cells.Length; ml /= cells.Length;
            double srr = 0, sll = 0, srl = 0;
            int active = 0;
            foreach (int i in cells)
            {
                double a = right[i] - mr, b = left[i] - ml;
                srr += a * a; sll += b * b; srl += a * b;
                if (right[i] + left[i] > 0.5f) active++;
            }
            double corr = srl / Math.Sqrt(Math.Max(1e-12, srr * sll));
            // direction selectivity over cells that fire at all: +1 = only right, -1 = only left
            double dsi = 0; int n = 0;
            foreach (int i in cells)
            {
                double s = right[i] + left[i];
                if (s < 0.5) continue;
                dsi += (right[i] - left[i]) / s; n++;
            }
            Console.WriteLine($"{name,-22} {corr,8:F3} {(n == 0 ? 0 : dsi / n),8:F3} {active,8}");
        }
        Console.WriteLine("\n(corr(R,L) < 0 = the steady-state pattern flips with the turn direction;"
                          + " |DSI| >> 0 = single cells are direction selective)");
        return 0;
    }

    /// <summary>One steady turn: returns the per-neuron firing rate over the second half.</summary>
    private static float[] RunSteady(CircuitPreview.BrainData d, int[] pool, bool[] patch,
                                     float yaw, float seconds, float odor, int seed)
    {
        var c = new CircuitPreview.Circuit(d);
        var rng = new Random(seed);
        var level = new float[pool.Length];
        float pMax = MaxStimHz * c.Dt / 1000f;
        float stimW = CircuitPreview.Circuit.WSyn * Fpoi;
        const float baseline = 0.12f;
        // exact per-step balancing, as in DriveProfile: the surround is solved so the delivered
        // total equals the natural total, and the level is never clipped (the Bernoulli draw is)
        int nPatchCells = patch?.Count(b => b) ?? 0;
        var pref = new float[pool.Length];
        for (int k = 0; k < pool.Length; k++)
            pref[k] = IsPositiveSide(d, pool[k]) ? 1f : -1f;
        for (int k = 0; k < pool.Length; k++)
            level[k] = baseline + (1f - baseline) * Math.Max(0f, pref[k] * yaw);
        if (patch != null)
        {
            double aboveRest = 0, target = 0;
            for (int k = 0; k < pool.Length; k++)
            {
                double above = level[k] - baseline;
                target += above;
                if (!patch[k]) aboveRest += above;
            }
            float scale = aboveRest > 1e-6 ? (float)(target / aboveRest) : 1f;
            for (int k = 0; k < pool.Length; k++)
                level[k] = patch[k] ? baseline : baseline + (level[k] - baseline) * scale;
        }
        int steps = (int)(seconds * 1000f / c.Dt);
        int warm = steps / 2;
        var prev = new long[d.N];
        for (int s = 0; s < steps; s++)
        {
            for (int k = 0; k < pool.Length; k++)
            {
                float p = pMax * level[k];
                if (p > 1f) p = 1f;
                if (rng.NextDouble() < p) c.Inject(pool[k], stimW);
            }
            for (int k = 0; k < d.Odor.Length; k++)
                if (rng.NextDouble() < pMax * odor) c.Inject(d.Odor[k], stimW);
            c.Step();
            if (s == warm) for (int i = 0; i < d.N; i++) prev[i] = c.SpikeTotal[i];
        }
        float window = (steps - warm) * c.Dt / 1000f;
        var rate = new float[d.N];
        for (int i = 0; i < d.N; i++) rate[i] = (c.SpikeTotal[i] - prev[i]) / window;
        return rate;
    }

    // ------------------------------------------------------------------ yaw tuning
    /// <summary>
    /// Per-cell yaw tuning vs the cell's push-pull wiring.
    ///
    /// For every CX cell, regress its binned firing rate on the yaw command and take the
    /// slope; then correlate those slopes with the weights the connectome implies (a cell that
    /// is excited from one side and inhibited from the other MUST have a large slope of a
    /// definite sign).  corr = 1 means the population's direction selectivity is exactly what
    /// its wiring says it should be; corr = 0 means the direction information is not reaching
    /// the cells, whatever the raw rates do.  Reported per trial, so arms can be compared.
    /// </summary>
    private static void YawTuningAnalysis(float[][] state, int nBins, float[] yawSeries,
                                          float[] w, int[] ringPos, Trial tr)
    {
        int n = state[0].Length;
        if (n == 0 || nBins < 8) return;
        double meanYaw = 0;
        for (int b = 0; b < nBins; b++) meanYaw += yawSeries[b];
        meanYaw /= nBins;
        double varYaw = 0;
        for (int b = 0; b < nBins; b++) varYaw += (yawSeries[b] - meanYaw) * (yawSeries[b] - meanYaw);
        if (varYaw < 1e-9) return;

        var slope = new float[n];
        double sumAbs = 0; int used = 0;
        for (int k = 0; k < n; k++)
        {
            double m = 0;
            for (int b = 0; b < nBins; b++) m += state[b][k];
            m /= nBins;
            double cov = 0;
            for (int b = 0; b < nBins; b++) cov += (yawSeries[b] - meanYaw) * (state[b][k] - m);
            slope[k] = (float)(cov / varYaw * 50.0);      // Hz per unit yaw (bins are 20 ms)
            sumAbs += Math.Abs(slope[k]);
            used++;
        }
        tr.YawModulation = used == 0 ? 0f : (float)(sumAbs / used);
        tr.YawTuningWireCorr = CorrWithWeights(slope, w, null, 0);
        tr.RingYawTuningWireCorr = CorrWithWeights(slope, w, ringPos, ringPos.Length);
    }

    /// <summary>Pearson correlation between per-cell slopes and per-cell push-pull weights,
    /// optionally restricted to the cells listed in <paramref name="subset"/>.</summary>
    private static float CorrWithWeights(float[] slope, float[] w, int[] subset, int count)
    {
        int n = subset == null ? slope.Length : count;
        if (n < 8) return 0f;
        double ms = 0, mw = 0;
        for (int i = 0; i < n; i++) { int k = subset == null ? i : subset[i]; ms += slope[k]; mw += w[k]; }
        ms /= n; mw /= n;
        double vss = 0, vww = 0, vsw = 0;
        for (int i = 0; i < n; i++)
        {
            int k = subset == null ? i : subset[i];
            double a = slope[k] - ms, b = w[k] - mw;
            vss += a * a; vww += b * b; vsw += a * b;
        }
        if (vss < 1e-12 || vww < 1e-12) return 0f;
        return (float)(vsw / Math.Sqrt(vss * vww));
    }

    // ------------------------------------------------------------------ mechanism
    /// <summary>
    /// Is the heading estimate noisier or merely weaker?  Two numbers on the ring's own state
    /// angle: the SD of the angle about its best linear trend over the window (angular
    /// diffusion, in degrees) and the lag-1 autocorrelation of that angle.  A circuit that
    /// integrates a conflicting rotation estimate should show more diffusion at unchanged mean
    /// rate; a circuit that simply receives less input should show neither.
    /// </summary>
    private static void RingAngleStability(float[] ang, float[] yawSeries, Trial tr)
    {
        var xs = new List<double>(); var ts = new List<double>();
        double prev = 0; bool first = true;
        for (int b = 0; b < ang.Length; b++)
        {
            if (float.IsNaN(ang[b])) continue;
            double a = ang[b];
            if (!first) a = prev + Wrap(a - prev);
            xs.Add(a); ts.Add(b * 0.02); prev = a; first = false;
        }
        if (xs.Count < 8) return;
        double mt = ts.Average(), ma = xs.Average();
        double stt = 0, sta = 0;
        for (int i = 0; i < xs.Count; i++) { stt += (ts[i] - mt) * (ts[i] - mt); sta += (ts[i] - mt) * (xs[i] - ma); }
        double slope = stt > 1e-12 ? sta / stt : 0;
        double ss = 0;
        var resid = new double[xs.Count];
        for (int i = 0; i < xs.Count; i++)
        {
            resid[i] = xs[i] - ma - slope * (ts[i] - mt);
            ss += resid[i] * resid[i];
        }
        tr.RingAngDiffusionDeg = (float)(Math.Sqrt(ss / xs.Count) * 180.0 / Math.PI);
        double num = 0, den = 0;
        for (int i = 1; i < resid.Length; i++) num += resid[i] * resid[i - 1];
        for (int i = 0; i < resid.Length; i++) den += resid[i] * resid[i];
        tr.RingAngAc1 = den > 1e-12 ? (float)(num / den) : 0f;
    }

    /// <summary>
    /// Steering readout: the descending neurons are the brain's motor command, so the
    /// left-right difference of their firing over time is what the fly would steer with.
    /// Reported as its SD (how much steering is being commanded at all) and its correlation
    /// with the yaw command (how faithfully the command follows the turn).
    /// </summary>
    private static void SteeringReadout(float[] dnL, float[] dnR, float[] yawSeries,
                                        float binSeconds, Trial tr)
    {
        int n = dnL.Length;
        if (n < 8) return;
        double meanL = dnL.Average(), meanR = dnR.Average();
        tr.DnRateL = (float)(meanL / binSeconds);
        tr.DnRateR = (float)(meanR / binSeconds);
        var asym = new double[n];
        for (int b = 0; b < n; b++) asym[b] = dnR[b] - dnL[b];
        double ma = asym.Average();
        tr.SteerAsymSd = (float)(Math.Sqrt(asym.Select(x => (x - ma) * (x - ma)).Sum() / Math.Max(1, n - 1))
                                 / binSeconds);
        double my = yawSeries.Average();
        double sa = 0, sy = 0, say = 0;
        for (int b = 0; b < n; b++)
        {
            double da = asym[b] - ma, dy = yawSeries[b] - my;
            sa += da * da; sy += dy * dy; say += da * dy;
        }
        tr.SteerCorrYaw = (sa > 1e-12 && sy > 1e-12) ? (float)(say / Math.Sqrt(sa * sy)) : 0f;
    }

    // ------------------------------------------------------------------ ring state
    /// <summary>Drive frequency used for the phase analysis (the yaw command carries a
    /// strong component here, so the ring's response can be read as a transfer function).</summary>
    internal const float ProbeHz = 0.25f;

    /// <summary>
    /// Read the ring out of its OWN dynamics instead of out of an anatomical guess.
    ///
    /// The soma-derived ring angle produced gains far above 1 and ~200 deg residuals in every
    /// arm, which means it was not a heading coordinate at all - so "no significant change in
    /// heading encoding" was not a result, it was an unmeasurable.  This does it properly:
    /// take the activity of the 68 ring cells per 20 ms bin, keep the two leading principal
    /// components of that state trajectory, and use the angle in that plane.  A ring attractor
    /// MUST show up here as a state that loops around the plane's origin, whatever the cells'
    /// anatomy; if it does not loop, the slice has no bump to perturb.
    ///
    /// Then the angle is projected onto the drive frequency as a complex coefficient, and
    /// compared with the same projection of the yaw command and of the integrated heading:
    ///
    ///     lag ~ 0 deg    -> the ring follows angular velocity (a relay)
    ///     lag ~ -90 deg  -> the ring follows the integral (path integration)
    /// </summary>
    private static void RingStateAnalysis(float[][] state, int nBins, int[] ringPos,
                                          float[] yawSeries, float[] headingSeries, Trial tr)
    {
        int nr = ringPos.Length;
        if (nr < 8 || nBins < 16) return;

        // z-score every ring cell across bins
        var mean = new float[nr];
        var sd = new float[nr];
        for (int k = 0; k < nr; k++)
        {
            double m = 0;
            for (int b = 0; b < nBins; b++) m += state[b][ringPos[k]];
            m /= nBins; mean[k] = (float)m;
            double v = 0;
            for (int b = 0; b < nBins; b++) { double dv = state[b][ringPos[k]] - m; v += dv * dv; }
            sd[k] = (float)Math.Sqrt(v / Math.Max(1, nBins - 1)) + 1e-6f;
        }

        // top two principal components of the ring state, by power iteration with deflation
        var cov = new float[nr, nr];
        for (int a = 0; a < nr; a++)
            for (int b = a; b < nr; b++)
            {
                double s = 0;
                for (int t = 0; t < nBins; t++)
                    s += ((state[t][ringPos[a]] - mean[a]) / sd[a])
                       * ((state[t][ringPos[b]] - mean[b]) / sd[b]);
                cov[a, b] = cov[b, a] = (float)(s / nBins);
            }
        float[] v1 = PowerVector(cov, null);
        float l1 = Rayleigh(cov, v1);
        float[] v2 = PowerVector(cov, v1);
        float l2 = Rayleigh(cov, v2);
        tr.RingPc12Var = (l1 + l2) / nr;          // total variance is nr after z-scoring

        // trajectory angle in the PC plane
        var ang = new float[nBins];
        double sx = 0, sy = 0;
        for (int t = 0; t < nBins; t++)
        {
            double p1 = 0, p2 = 0;
            for (int k = 0; k < nr; k++)
            {
                double z = (state[t][ringPos[k]] - mean[k]) / sd[k];
                p1 += z * v1[k];
                p2 += z * v2[k];
            }
            ang[t] = (float)Math.Atan2(p2, p1);
            sx += Math.Cos(ang[t]);
            sy += Math.Sin(ang[t]);
        }
        tr.RingLoop = (float)Math.Sqrt(sx * sx + sy * sy) / nBins;

        // complex projection at the drive frequency: amplitude and phase of the ring angle,
        // of the yaw command and of the integrated heading
        ComplexAtFrequency(ang, nBins, out double ringAmp, out double ringPhase);
        ComplexAtFrequency(yawSeries, nBins, out double yawAmp, out double yawPhase);
        ComplexAtFrequency(headingSeries, nBins, out double headAmp, out double headPhase);
        if (yawAmp > 1e-9)
        {
            tr.TrackGainYaw = (float)(ringAmp / yawAmp);
            tr.TrackLagYawDeg = (float)((ringPhase - yawPhase) * 180.0 / Math.PI);
        }
        if (headAmp > 1e-9)
        {
            tr.TrackGainHead = (float)(ringAmp / headAmp);
            tr.TrackLagHeadDeg = (float)((ringPhase - headPhase) * 180.0 / Math.PI);
        }
    }

    /// <summary>Amplitude and phase of a series at <see cref="ProbeHz"/> (least-squares fit
    /// of one sinusoid; the series are read at 20 ms bins).</summary>
    private static void ComplexAtFrequency(float[] series, int nBins, out double amp, out double phase)
    {
        double re = 0, im = 0;
        for (int b = 0; b < nBins; b++)
        {
            double t = b * 0.02;                       // bins are 20 ms
            double w = 2 * Math.PI * ProbeHz * t;
            re += series[b] * Math.Cos(w);
            im += series[b] * Math.Sin(w);
        }
        re *= 2.0 / nBins; im *= 2.0 / nBins;
        amp = Math.Sqrt(re * re + im * im);
        phase = Math.Atan2(im, re);
    }

    private static float Rayleigh(float[,] a, float[] v)
    {
        int n = v.Length;
        double s = 0;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++) s += v[i] * a[i, j] * v[j];
        return (float)s;
    }

    // ------------------------------------------------------------------ helpers
    /// <summary>
    /// What the patch actually removes from the central complex, in synapses.  Without this
    /// number "the body patch changed the CX" cannot be told apart from "the patch happened
    /// to contain the cells that feed the CX": the compact cluster and the random
    /// same-size control are compared on equal footing here.
    /// </summary>
    private static (int Cells, long CxSyn, long RingSyn) PatchCheck(CircuitPreview.BrainData d,
            int[] pool, bool[] patch, string name)
    {
        var isCx = new bool[d.N];
        var isRing = new bool[d.N];
        foreach (int i in d.Cx) isCx[i] = true;
        foreach (int i in d.Cx) if (d.CxFamily[i] == 1) isRing[i] = true;

        long toCx = 0, toRing = 0, cxIn = 0;
        for (int k = 0; k < pool.Length; k++)
        {
            if (!patch[k]) continue;
            int i = pool[k];
            for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
            {
                int j = d.Target[e];
                if (!isCx[j]) continue;
                toCx++;
                if (isRing[j]) toRing++;
            }
        }
        for (int i = 0; i < d.N; i++)
            for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
                if (isCx[d.Target[e]]) cxIn++;

        Console.WriteLine($"   {name,-32} {patch.Count(b => b),5} cells, "
                          + $"{toCx,7} synapses into the CX ({toRing} into the heading ring), "
                          + $"= {100.0 * toCx / Math.Max(1, cxIn):F1}% of all CX input");
        return (patch.Count(b => b), toCx, toRing);
    }

    private static int[] BuildVisualPool(CircuitPreview.BrainData d)
    {
        var set = new HashSet<int>(d.SelfMotion);
        foreach (int i in d.VisualRelay) set.Add(i);
        return set.OrderBy(x => x).ToArray();
    }

    /// <summary>
    /// A random subset of the pool sized so that it silences the SAME number of synapses into
    /// the central complex as the compact body patch does.
    ///
    /// Matching the injected spike count is not enough: a compact cluster of somas carries
    /// 2.4x more CX input than a random subset of the same size (30,919 vs 13,053 synapses in
    /// this circuit).  An earlier version tried to close that gap by taking a plain random
    /// subset and simply growing it until the target was reached - which never happens, because
    /// the remaining cells are mostly lobula-plate cells with almost no direct CX projection;
    /// the arm saturated at 5.1% instead of 9.1%, and (with the old clipped drive) it also
    /// delivered 27-42% less input than the other arms, so it could not be used at all.
    ///
    /// This draws cells by probability-proportional-to-CX-input (Efraimidis-Spirakis weighted
    /// sampling without replacement) and stops when the silenced CX input reaches the target.
    /// Cell identity is still random - no anatomical clustering, no spatial coherence - but the
    /// sampling is biased so that the control is attainable.
    /// </summary>
    private static bool[] CxMatchedRandomPatch(CircuitPreview.BrainData d, int[] pool,
                                              bool[] compactPatch, int seed)
    {
        var isCx = new bool[d.N];
        foreach (int i in d.Cx) isCx[i] = true;
        var cxIn = new int[pool.Length];
        long target = 0;
        for (int k = 0; k < pool.Length; k++)
        {
            int i = pool[k];
            for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
                if (isCx[d.Target[e]]) cxIn[k]++;
            if (compactPatch[k]) target += cxIn[k];
        }
        var rng = new Random(seed);
        // weighted random order: key = U^(1/w), largest keys first
        var keys = new double[pool.Length];
        for (int k = 0; k < pool.Length; k++)
        {
            double u = Math.Max(1e-12, rng.NextDouble());
            keys[k] = cxIn[k] > 0 ? Math.Pow(u, 1.0 / cxIn[k]) : 0.0;
        }
        var order = Enumerable.Range(0, pool.Length).OrderByDescending(k => keys[k]).ToArray();
        var mask = new bool[pool.Length];
        long acc = 0;
        foreach (int k in order)
        {
            if (acc >= target) break;
            mask[k] = true;
            acc += cxIn[k];
        }
        return mask;
    }

    /// <summary>
    /// The body patch: the fraction of the pool closest to the pool's own centroid.
    /// Deterministic, so the offline harness and the mod pick the identical cells.
    /// </summary>
    private static bool[] CompactPatch(CircuitPreview.BrainData d, int[] pool, float fraction)
    {
        double cx = 0, cy = 0, cz = 0;
        foreach (int i in pool) { cx += d.Soma[i * 3]; cy += d.Soma[i * 3 + 1]; cz += d.Soma[i * 3 + 2]; }
        cx /= pool.Length; cy /= pool.Length; cz /= pool.Length;
        var d2 = pool.Select(i =>
        {
            double dx = d.Soma[i * 3] - cx, dy = d.Soma[i * 3 + 1] - cy, dz = d.Soma[i * 3 + 2] - cz;
            return (i, v: dx * dx + dy * dy + dz * dz);
        }).OrderBy(t => t.v).ToArray();        int n = Math.Max(1, (int)Math.Round(pool.Length * fraction));
        var set = new HashSet<int>(d2.Take(n).Select(t => t.i));
        return pool.Select(i => set.Contains(i)).ToArray();
    }

    private static void Shuffle(bool[] a, Random rng)
    {
        for (int i = a.Length - 1; i > 0; i--)
        {
            int j = rng.Next(i + 1);
            (a[i], a[j]) = (a[j], a[i]);
        }
    }

    private static float[] PowerVector(float[,] a, float[] deflate)
    {
        int n = a.GetLength(0);
        var v = new float[n];
        for (int i = 0; i < n; i++) v[i] = 1f / (float)Math.Sqrt(n);
        for (int it = 0; it < 200; it++)
        {
            var w = new float[n];
            for (int i = 0; i < n; i++)
            {
                float s = 0;
                for (int j = 0; j < n; j++) s += a[i, j] * v[j];
                if (deflate != null)
                {
                    float proj = 0;
                    for (int j = 0; j < n; j++) proj += deflate[j] * v[j];
                    s -= proj * deflate[i] * 1.0f;
                }
                w[i] = s;
            }
            float norm = (float)Math.Sqrt(w.Sum(x => x * x));
            if (norm < 1e-12f) break;
            for (int i = 0; i < n; i++) v[i] = w[i] / norm;
        }
        return v;
    }

    /// <summary>Eigenvalues of a symmetric matrix (cyclic Jacobi).</summary>
    internal static float[] JacobiEigen(float[,] aIn, int n)
    {
        var a = (float[,])aIn.Clone();
        for (int sweep = 0; sweep < 60; sweep++)
        {
            double off = 0;
            for (int p = 0; p < n; p++)
                for (int q = p + 1; q < n; q++) off += a[p, q] * a[p, q];
            if (off < 1e-12) break;
            for (int p = 0; p < n; p++)
                for (int q = p + 1; q < n; q++)
                {
                    if (Math.Abs(a[p, q]) < 1e-15f) continue;
                    float theta = (a[q, q] - a[p, p]) / (2f * a[p, q]);
                    float t = Math.Sign(theta) / (Math.Abs(theta) + (float)Math.Sqrt(theta * theta + 1));
                    if (theta == 0) t = 1;
                    float c = 1f / (float)Math.Sqrt(t * t + 1), s = t * c;
                    for (int k = 0; k < n; k++)
                    {
                        float akp = a[k, p], akq = a[k, q];
                        a[k, p] = c * akp - s * akq;
                        a[k, q] = s * akp + c * akq;
                    }
                    for (int k = 0; k < n; k++)
                    {
                        float apk = a[p, k], aqk = a[q, k];
                        a[p, k] = c * apk - s * aqk;
                        a[q, k] = s * apk + c * aqk;
                    }
                }
        }
        var ev = new float[n];
        for (int i = 0; i < n; i++) ev[i] = a[i, i];
        return ev;
    }

    private static string SubfamilyCensus(CircuitPreview.BrainData d)
    {
        var c = new int[5];
        foreach (int i in d.Cx) c[d.CxFamily[i]]++;
        return $"ring={c[1]} columnar={c[2]} fanbody={c[3]} other={c[4]}";
    }

    // ------------------------------------------------------------------ report
    private static void Report(CircuitPreview.BrainData d, Dictionary<string, List<Trial>> byArm,
                               int trials, float seconds, int nPerm, bool heading)
    {
        Console.WriteLine($"\n=== 结果 ({trials} trials/arm, {seconds:0.#} s/生物时间 per trial, 分析后半段) ===\n");
        Console.WriteLine("arm         pool-Hz  inj/step |  CX-Hz  active  corr   tau(ms)  dim   bumpR"
                          + (heading ? "  PC12   loop  lagYaw  lagHead" : ""));
        foreach (var arm in Arms)
        {
            var l = byArm[arm.Id];
            Console.WriteLine($"{arm.Id,-11} {Avg(l, t => t.PoolRate),7:F1} {Avg(l, t => t.InjectedEvents) / (seconds * 2000f),7:F2} | "
                              + $"{Avg(l, t => t.Rate),6:F2} {Avg(l, t => t.ActiveFraction),7:F3} "
                              + $"{Avg(l, t => t.PairCorr),6:F3} {Avg(l, t => t.TauMs),8:F0} "
                              + $"{Avg(l, t => t.Dim),5:F2} {Avg(l, t => t.BumpR),6:F3}"
                              + (heading ? $" {Avg(l, t => t.RingPc12Var),6:F3} {Avg(l, t => t.RingLoop),6:F3} "
                                         + $"{Avg(l, t => t.TrackLagYawDeg),7:F0} {Avg(l, t => t.TrackLagHeadDeg),8:F0}" : ""));
        }

        string[] famNames = { "-", "ring(EPG/PEG)", "columnar(PFN/PFR/hDelta)", "fanbody(FB)", "other(LAL/IB/ER/TuBu)" };

        // ---- manipulation check: is the body patch actually the body patch? -------------
        // A drive model can silently fail to implement the manipulation it is named after.
        // For a body-locked region the patch level must sit clearly BELOW the surround level
        // (BodySlip = 0.1 relative to the world), and for the conflict arms it must approach
        // the surround level again (the shuffled copy has the world's marginal distribution).
        // A slip-free arm whose ratio is ~1.0 is the natural condition wearing the arm's name
        // and its null result means nothing.
        Console.WriteLine("\n=== 操纵检查: 斑块实际拿到的驱动 (patch level / surround level) ===");
        Console.WriteLine("arm          patch_drive_frac  patch/surround   verdict");
        foreach (var arm in Arms)
        {
            var l = byArm[arm.Id];
            float frac = Avg(l, t => t.PatchDriveFraction);
            float ratio = l.Where(t => t.PatchLevelRatio > 0f).Select(t => t.PatchLevelRatio).DefaultIfEmpty(0f).Average();
            string verdict = arm.Mode == ModeUniform ? "no patch (natural)"
                : ratio <= 0f ? "no patch cells"
                : ratio < 0.5f ? "body-locked: below natural"
                : ratio < 0.9f ? "partially body-locked"
                : "NOT BELOW NATURAL -- check the drive model";
            Console.WriteLine($"{arm.Id,-12} {frac,15:F4} {ratio,15:F3}   {verdict}");
        }
        Console.WriteLine("\nper subfamily   " + string.Join("  ", Arms.Select(a => a.Id.PadLeft(9))));
        for (int f = 1; f <= 4; f++)
        {
            if (byArm["self"].All(t => t.FamRate[f] == 0f)) continue;
            Console.WriteLine($"{famNames[f],-26}" + string.Join("  ",
                Arms.Select(a => Avg(byArm[a.Id], t => t.FamRate[f]).ToString("F2").PadLeft(9))));
            Console.WriteLine($"{"  active fraction",-26}" + string.Join("  ",
                Arms.Select(a => Avg(byArm[a.Id], t => t.FamActive[f]).ToString("F3").PadLeft(9))));
        }

        Console.WriteLine("\n=== 关键对比: self(看见自己) vs 各对照 (效应量 d, 置换检验 p, 两侧) ===");
        Console.WriteLine("metric                      self      flow   shuffle   randmat    decorr |"
                          + "  d(flow) p(flow)  d(shuf) p(shuf)  d(rndm) p(rndm)  d(dec)  p(dec)");
        var metrics = new (string Name, Func<Trial, float> Get)[]
        {
            ("CX 平均放电率 (Hz)", t => t.Rate),
            ("CX 活跃细胞比例", t => t.ActiveFraction),
            ("ring 放电率 (Hz)", t => t.FamRate[1]),
            ("columnar 放电率 (Hz)", t => t.FamRate[2]),
            ("fanbody 放电率 (Hz)", t => t.FamRate[3]),
            ("other 放电率 (Hz)", t => t.FamRate[4]),
            ("CX 成对相关", t => t.PairCorr),
            ("CX 自相关时间 (ms)", t => t.TauMs),
            ("CX 有效维度", t => t.Dim),
            ("CX 群体涨落 SD (Hz)", t => t.PopSd),
            ("ring 群体向量幅值", t => t.BumpR),
        };
        if (heading)
            metrics = metrics.Concat(new (string, Func<Trial, float>)[]
            {
                ("heading 积分增益 |g|", t => t.HeadGain),
                ("heading 残差 (度)", t => t.HeadResidDeg),
                ("yaw 中继增益 |g|", t => t.RelayGain),
                ("ring 状态 PC1+2 方差", t => t.RingPc12Var),
                ("ring 轨迹环绕度", t => t.RingLoop),
                ("ring 跟随增益(对yaw)", t => t.TrackGainYaw),
                ("ring 相位滞后(对yaw)°", t => t.TrackLagYawDeg),
                ("ring 相位滞后(对积分朝向)°", t => t.TrackLagHeadDeg),
                ("CX yaw 调制幅度 (Hz)", t => t.YawModulation),
                ("CX 调谐↔推挽接线 r", t => t.YawTuningWireCorr),
                ("ring 调谐↔推挽接线 r", t => t.RingYawTuningWireCorr),
                ("ring 角度扩散 (度)", t => t.RingAngDiffusionDeg),
                ("ring 角度 lag-1 自相关", t => t.RingAngAc1),
                ("转向指令↔yaw 相关", t => t.SteerCorrYaw),
                ("转向指令 SD (Hz)", t => t.SteerAsymSd),
                ("DN 左/右 放电率 (Hz)", t => t.DnRateL + t.DnRateR),
            }).ToArray();
        var selfVals = byArm["self"];
        var controlIds = new[] { "flow", "shuffle", "randmat", "decorr" };
        foreach (var (name, get) in metrics)
        {
            var sv = selfVals.Select(get).ToArray();
            var cells = new List<string> { $"{sv.Average(),8:F3}" };
            foreach (string id in controlIds)
                cells.Add($"{byArm[id].Select(get).Average(),8:F3}");
            var stat = new List<string>();
            foreach (string id in controlIds)
            {
                var ov = byArm[id].Select(get).ToArray();
                double eff = CohensD(sv, ov);
                double pv = PermTest(sv, ov, nPerm);
                stat.Add($"{eff,7:F2} {pv,7:F4}");
            }
            Console.WriteLine($"{name,-24}" + string.Join(" ", cells) + " |" + string.Join(" ", stat));
        }
        Console.WriteLine("\n(d>0 = self 更大; p<0.05 表示该指标在 self 与对照之间可分)");
    }

    private static float Avg(List<Trial> l, Func<Trial, float> get) => l.Select(get).Average();

    private static double CohensD(float[] a, float[] b)
    {
        double ma = a.Average(), mb = b.Average();
        double va = a.Select(x => (x - ma) * (x - ma)).Sum() / Math.Max(1, a.Length - 1);
        double vb = b.Select(x => (x - mb) * (x - mb)).Sum() / Math.Max(1, b.Length - 1);
        double sp = Math.Sqrt((va + vb) / 2);
        return sp < 1e-12 ? 0 : (ma - mb) / sp;
    }

    /// <summary>Two-sided permutation test on the difference of means.</summary>
    private static double PermTest(float[] a, float[] b, int nPerm)
    {
        var all = a.Concat(b).ToArray();
        double obs = Math.Abs(a.Average() - b.Average());
        if (obs < 1e-12) return 1.0;
        var rng = new Random(99991);
        int hit = 0;
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
}
