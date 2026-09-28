// Offline preview of the on-screen neuro readout.
//
// The in-game panel narrates whatever the fly is doing at that moment, which makes it hard
// to tell a real response from noise.  This replays the SAME blob through the SAME LIF
// step (port of Neural/LifCircuit.cs) under a few representative visual conditions and
// prints what each population does, so the numbers on screen can be checked against a
// reference instead of being taken on faith.
//
// Usage:
//   dotnet run --project tools/CircuitPreview -- <flymind.brain>
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

internal static class CircuitPreview
{
    // ---------------------------------------------------------------- circuit (port of LifCircuit.cs)
    internal sealed class Circuit
    {
        public const float V0 = -52f, VRst = -52f, VTh = -45f, Tmbr = 20f, Tau = 5f,
            TRfc = 2.2f, TDly = 1.8f, WSyn = 0.275f, VMin = -70f;

        public int N, Syn;
        public int[] Offset, Target;
        public float[] Weight, BaseWeight;
        public bool[] KcMbon;
        public byte[] Pop;
        public float[] Soma;        // 3 per neuron
        public byte[] CxFamily;

        private float[] v, g, rfc, rate, outSpike;
        private float[][] pendG;
        private int[][] pendT;
        private int[] pendC;
        private int delaySteps, slot;
        public float Dt = 0.5f;
        private float decayG;

        public int LastSpikes;

        /// <summary>Total spikes emitted per neuron since construction (exact rates).</summary>
        public readonly long[] SpikeTotal;

        public Circuit(BrainData d)
        {
            N = d.N; Syn = d.Syn;
            Offset = d.Offset; Target = d.Target; Weight = d.Weight;
            BaseWeight = d.BaseBase; KcMbon = d.KcMbon; Pop = d.Pop;
            Soma = d.Soma; CxFamily = d.CxFamily;
            SpikeTotal = new long[N];
            decayG = (float)Math.Exp(-Dt / Tau);
            delaySteps = Math.Max(1, (int)Math.Round(TDly / Dt));
            v = new float[N]; g = new float[N]; rfc = new float[N];
            rate = new float[N]; outSpike = new float[N];
            pendG = new float[delaySteps][]; pendT = new int[delaySteps][];
            pendC = new int[delaySteps];
            for (int i = 0; i < delaySteps; i++)
            {
                int cap = Math.Max(64, Syn / delaySteps + Syn / 8);
                pendG[i] = new float[cap];
                pendT[i] = new int[cap];
            }
            for (int i = 0; i < N; i++) { v[i] = V0; }
        }

        public void Inject(int neuron, float weight)
        {
            if ((uint)neuron < (uint)N) g[neuron] += weight;
        }

        public void Step()
        {
            // deliver the events that arrive at this step (full weight: the transmission
            // delay is modelled by the ring buffer, the decay by the PSP below)
            int cnt = pendC[slot];
            if (cnt > 0)
            {
                var gs = pendG[slot]; var tg = pendT[slot];
                for (int k = 0; k < cnt; k++) g[tg[k]] += gs[k];
                pendC[slot] = 0;
            }

            // integrate; the conductance decays with tau (dg/dt = -g/tau) instead of being
            // consumed in a single step, which is what lets PSPs summate over their 5 ms
            int fired = 0;
            for (int i = 0; i < N; i++)
            {
                if (rfc[i] > 0f) { rfc[i] -= Dt; outSpike[i] = 0f; continue; }
                float gi = g[i];
                float vi = v[i] + Dt * (V0 - v[i] + gi) / Tmbr;
                if (vi > VTh)
                {
                    vi = VRst; rfc[i] = TRfc; outSpike[i] = 1f; rate[i] += 1f; fired++;
                    SpikeTotal[i]++;
                    g[i] = 0f;                       // reset rule: v = v_rst, g = 0
                }
                else
                {
                    if (vi < VMin) vi = VMin; outSpike[i] = 0f;
                    g[i] = gi * decayG;
                }
                v[i] = vi;
            }

            int outSlot = (slot + delaySteps) % delaySteps;
            if (fired > 0)
            {
                var gs = pendG[outSlot]; var tg = pendT[outSlot];
                int m = pendC[outSlot]; int cap = gs.Length;
                for (int i = 0; i < N; i++)
                {
                    if (outSpike[i] == 0f) continue;
                    for (int e = Offset[i]; e < Offset[i + 1]; e++)
                    {
                        if (m == cap) { Array.Resize(ref gs, cap * 2); Array.Resize(ref tg, cap * 2); cap *= 2; }
                        tg[m] = Target[e]; gs[m] = Weight[e]; m++;
                    }
                }
                pendG[outSlot] = gs; pendT[outSlot] = tg; pendC[outSlot] = m;
            }

            slot = (slot + 1) % delaySteps;
            LastSpikes = fired;
            float rk = Dt / 100f;
            for (int i = 0; i < N; i++) rate[i] -= rk * rate[i];
        }

        /// <summary>Did this neuron emit a spike in the step that just ran?</summary>
        public bool Spiked(int neuron) => outSpike != null && (uint)neuron < (uint)N && outSpike[neuron] != 0f;

        public float PopRate(byte p)
        {
            float sum = 0; int c = 0;
            for (int i = 0; i < N; i++) if (Pop[i] == p) { sum += rate[i]; c++; }
            return c == 0 ? 0f : sum / c * 10f;   // Hz
        }

        /// <summary>Resting tone: an independent Poisson train on every neuron.</summary>
        public void Spontaneous(float probabilityPerStep, Random rng)
        {
            if (probabilityPerStep <= 0f) return;
            for (int i = 0; i < N; i++)
                if (rng.NextDouble() < probabilityPerStep) g[i] += WSyn;
        }

        public float PlasticityGain
        {
            set
            {
                for (int i = 0; i < Syn; i++)
                    if (KcMbon[i]) Weight[i] = BaseWeight[i] * value;
            }
        }
    }

    internal sealed class BrainData
    {
        public int N, Syn;
        public int[] Offset, Target;
        public float[] Weight, BaseBase;
        public bool[] KcMbon;
        public byte[] Pop;
        public float[] Soma;        // 3 per neuron (mm/1000, same as the blob)
        /// <summary>Central-complex subfamily per neuron (0 = not CX): 1 EPG/PEG ring,
        /// 2 PFN/PFR/hDelta/Delta, 3 fan-shaped-body columnar, 4 other CX.</summary>
        public byte[] CxFamily;
        public int[] Sugar, Motor, Odor, SelfMotion, Cx;
        /// <summary>Cells that receive from the self-motion pool and project onto the CX:
        /// the connectome-derived visual route into the central complex.</summary>
        public int[] VisualRelay;

        public static BrainData Load(string path)
        {
            using var br = new BinaryReader(File.OpenRead(path));
            var tag = System.Text.Encoding.ASCII.GetString(br.ReadBytes(8));
            bool v4 = tag == "FLYMIND4";
            bool v3 = v4 || tag == "FLYMIND3";
            var d = new BrainData();
            d.N = (int)br.ReadUInt32(); d.Syn = (int)br.ReadUInt32(); br.ReadUInt32();
            for (int i = 0; i < (v3 ? 12 : 11); i++) br.ReadUInt32();
            int nSugar = (int)br.ReadUInt32(), nMotor = (int)br.ReadUInt32(),
                nOdor = (int)br.ReadUInt32();
            int nSelf = tag == "FLYMIND1" ? 0 : (int)br.ReadUInt32();
            int nCx = v3 ? (int)br.ReadUInt32() : 0;
            int nRelay = v4 ? (int)br.ReadUInt32() : 0;
            d.Pop = new byte[d.N];
            d.CxFamily = new byte[d.N];
            d.Soma = new float[d.N * 3];
            var buf = new byte[24];
            for (int i = 0; i < d.N; i++)
            {
                br.Read(buf, 0, 24);
                d.Soma[i * 3] = BitConverter.ToSingle(buf, 8);
                d.Soma[i * 3 + 1] = BitConverter.ToSingle(buf, 12);
                d.Soma[i * 3 + 2] = BitConverter.ToSingle(buf, 16);
                d.Pop[i] = buf[20];
                d.CxFamily[i] = buf[21];
            }
            d.Offset = ReadInts(br, d.N + 1);
            d.Target = ReadInts(br, d.Syn);
            d.Weight = ReadFloats(br, d.Syn);
            var mask = br.ReadBytes(d.Syn);
            d.KcMbon = new bool[d.Syn];
            for (int i = 0; i < d.Syn; i++) d.KcMbon[i] = mask[i] != 0;
            d.BaseBase = ReadFloats(br, d.Syn);
            d.Sugar = ReadInts(br, nSugar);
            d.Motor = ReadInts(br, nMotor);
            d.Odor = ReadInts(br, nOdor);
            d.SelfMotion = ReadInts(br, nSelf);
            d.Cx = ReadInts(br, nCx);
            d.VisualRelay = ReadInts(br, nRelay);
            return d;
        }

        private static int[] ReadInts(BinaryReader br, int n)
        {
            if (n <= 0) return Array.Empty<int>();
            var b = br.ReadBytes(n * 4); var a = new int[n];
            Buffer.BlockCopy(b, 0, a, 0, b.Length); return a;
        }

        private static float[] ReadFloats(BinaryReader br, int n)
        {
            if (n <= 0) return Array.Empty<float>();
            var b = br.ReadBytes(n * 4); var a = new float[n];
            Buffer.BlockCopy(b, 0, a, 0, b.Length); return a;
        }
    }

    // ---------------------------------------------------------------- scenarios
    private sealed record Scenario(string Name, string Description,
        float Odor, float Taste, float Danger, float ViewMotion, float SelfInView);

    private static int Main(string[] args)
    {
        string path = args.Length > 0 ? args[0] : @"D:\projects\science\flymind.brain";
        var data = BrainData.Load(path);
        Console.WriteLine($"circuit: {data.N} neurons, {data.Syn} synapses");
        Console.WriteLine($"seeds: sugar={data.Sugar.Length} motor={data.Motor.Length} " +
                          $"odor={data.Odor.Length} selfmotion={data.SelfMotion.Length} " +
                          $"centralcomplex={data.Cx.Length}\n");

        if (args.Contains("--sweep"))
        {
            var ks = args.SkipWhile(a => a != "--sweep").Skip(1).TakeWhile(a => !a.StartsWith("--"))
                         .Select(s => double.Parse(s, System.Globalization.CultureInfo.InvariantCulture))
                         .ToArray();
            if (ks.Length == 0) ks = new double[] { 1, 3, 10, 30, 100 };
            return Experiment.RunSweep(data, ks, (float)ArgF(args, "--secs", 2.0),
                                       (float)ArgF(args, "--odor", 0.30));
        }

        if (args.Contains("--dose"))
        {
            int di = Array.IndexOf(args, "--fracs");
            var fracs = di >= 0 && di + 1 < args.Length
                ? args[di + 1].Split(',').Select(s => float.Parse(s,
                      System.Globalization.CultureInfo.InvariantCulture)).ToArray()
                : new[] { 0f, 0.125f, 0.25f, 0.5f };
            int ci2 = Array.IndexOf(args, "--csv");
            string csv2 = ci2 >= 0 && ci2 + 1 < args.Length ? args[ci2 + 1] : null;
            return Experiment.RunDose(data, ArgF(args, "--kappa", 300.0),
                                      (int)ArgF(args, "--trials", 10),
                                      (float)ArgF(args, "--secs", 6.0),
                                      (float)ArgF(args, "--odor", 0.05),
                                      args.Contains("--heading"), fracs, csv2);
        }

        if (args.Contains("--propagate"))
        {
            int ki = Array.IndexOf(args, "--kappas");
            var ks = ki >= 0 && ki + 1 < args.Length
                ? args[ki + 1].Split(',').Select(s => double.Parse(s,
                      System.Globalization.CultureInfo.InvariantCulture)).ToArray()
                : Array.Empty<double>();
            return Experiment.RunPropagation(data, ArgF(args, "--kappa", 300.0),
                                            (float)ArgF(args, "--odor", 0.05), ks);
        }

        if (args.Contains("--pp"))
            return Experiment.RunPushPull(data, ArgF(args, "--kappa", 1.0));

        if (args.Contains("--asym"))
            return Experiment.RunAsymmetry(data, ArgF(args, "--kappa", 300.0),
                                           (float)ArgF(args, "--secs", 4.0),
                                           (float)ArgF(args, "--odor", 0.05),
                                           (float)ArgF(args, "--yaw", 0.6),
                                           args.Contains("--patch"));

        if (args.Contains("--exp"))
        {
            double kappa = ArgF(args, "--kappa", 1.0);
            int trials = (int)ArgF(args, "--trials", 12);
            float secs = (float)ArgF(args, "--secs", 3.0);
            float odor = (float)ArgF(args, "--odor", 0.30);
            int nPerm = (int)ArgF(args, "--perm", 4000);
            int ci = Array.IndexOf(args, "--csv");
            string csv = ci >= 0 && ci + 1 < args.Length ? args[ci + 1] : null;
            // closed loop (results/CLOSED-LOOP-PLAN.md): the turn is caused by the circuit's own
            // descending steering command; --loopgain is calibrated once at alpha = 0 and frozen
            Experiment.ClosedLoop = args.Contains("--closedloop");
            Experiment.LoopGain = (float)ArgF(args, "--loopgain", 0.0);
            if (Experiment.ClosedLoop)
                Console.WriteLine($"[closedloop] enabled, LoopGain = {Experiment.LoopGain}");
            return Experiment.Run(data, kappa, trials, secs, odor, nPerm, args.Contains("--heading"),
                                  csv, args.Contains("--controls"), args.Contains("--conflict"));
        }

        if (args.Contains("--diag")) return Diagnose(data, args.Contains("--run"));

        var scenarios = new[]
        {
            new Scenario("静息(黑暗/无输入)", "没有任何线索，只有基线噪声",
                0f, 0f, 0f, 0f, 0f),
            new Scenario("闻到食物·静止", "气味进入触角叶，但没有移动",
                0.5f, 0f, 0f, 0f, 0.08f),
            new Scenario("闻到食物·飞行中", "边飞边闻到，画面在扫过",
                0.6f, 0f, 0f, 0.5f, 0.08f),
            new Scenario("正在取食", "喙接触食物，糖觉 + 气味同时到",
                0.6f, 0.8f, 0f, 0.15f, 0.08f),
            new Scenario("受惊逃跑", "威胁输入 + 高风险画面位移",
                0.2f, 0f, 0.9f, 0.8f, 0.08f),
        };

        Console.WriteLine("运行每个场景 2000 步（0.5 ms/步 = 1 秒生物时间），取后半段稳态：\n");

        foreach (var s in scenarios)
        {
            var c = new Circuit(data);
            var rng = new Random(1234);
            float pPerStep = 150f * c.Dt / 1000f;
            float poiW = Circuit.WSyn * 250f;
            float viewDrive = Math.Clamp(0.75f * s.ViewMotion + 0.5f * s.SelfInView, 0f, 1f);

            for (int step = 0; step < 2000; step++)
            {
                Fire(c, data.Odor, pPerStep * s.Odor, poiW, rng);
                Fire(c, data.Sugar, pPerStep * s.Taste, poiW, rng);
                Fire(c, data.Motor, pPerStep * s.Danger, poiW, rng);
                if (viewDrive > 0.02f)
                    Fire(c, data.SelfMotion, pPerStep * 0.6f * viewDrive, poiW, rng);
                // resting tone: same as FlyBrain.SpontaneousRateHz, one synapse per spike
                c.Spontaneous(6f * c.Dt / 1000f, rng);
                c.Step();
            }

            Console.WriteLine($"── {s.Name}");
            Console.WriteLine($"   场景: {s.Description}");
            Console.WriteLine($"   脉冲/步 {c.LastSpikes}");
            Console.WriteLine(string.Format(
                "   sensory {0,5:0.0}  antennal {1,5:0.0}  kenyon {2,5:0.0}  dopamine {3,5:0.0} Hz",
                c.PopRate(1), c.PopRate(2), c.PopRate(3), c.PopRate(4)));
            Console.WriteLine(string.Format(
                "   mbon    {0,5:0.0}  descending {1,3:0.0}  motor {2,5:0.0}  selfmotion {3,4:0.0} Hz\n",
                c.PopRate(5), c.PopRate(6), c.PopRate(7), c.PopRate(10)));
        }

        return 0;
    }

    /// <summary>Read a numeric command-line option (<c>--name value</c>).</summary>
    private static double ArgF(string[] args, string name, double fallback)
    {
        int i = Array.IndexOf(args, name);
        if (i < 0 || i + 1 >= args.Length) return fallback;
        return double.TryParse(args[i + 1], System.Globalization.NumberStyles.Float,
                               System.Globalization.CultureInfo.InvariantCulture, out double v)
            ? v : fallback;
    }

    private static void Fire(Circuit c, int[] neurons, float probability, float weight, Random rng)
    {
        if (neurons.Length == 0 || probability <= 0f) return;
        if (probability > 1f) probability = 1f;
        for (int i = 0; i < neurons.Length; i++)
            if (rng.NextDouble() < probability) c.Inject(neurons[i], weight);
    }

    /// <summary>
    /// Wiring sanity check.  The first preview run showed sensory and antennal activity but
    /// nothing in Kenyon cells / dopamine / MBON, which is either a real property of the
    /// extracted path or a broken cascade - this prints degrees and the strongest single
    /// input per population so the difference is visible, and optionally runs the network.
    /// </summary>
    private static int Diagnose(BrainData d, bool run)
    {
        string PopName(int p) => p switch
        {
            1 => "sensory", 2 => "antennal", 3 => "kenyon", 4 => "dopamine", 5 => "mbon",
            6 => "descending", 7 => "motor", 8 => "interneuron", 9 => "vnc", 10 => "selfmotion",
            _ => "unknown",
        };

        var counts = new int[11];
        var outDeg = new long[11];
        var inDeg = new long[11];
        var outPos = new long[11];
        var outNeg = new long[11];
        var strongest = new float[11];
        for (int i = 0; i < d.N; i++)
        {
            counts[d.Pop[i]]++;
            outDeg[d.Pop[i]] += d.Offset[i + 1] - d.Offset[i];
            for (int e = d.Offset[i]; e < d.Offset[i + 1]; e++)
            {
                int tp = d.Pop[d.Target[e]];
                inDeg[tp]++;
                if (d.Weight[e] >= 0) outPos[d.Pop[i]]++; else outNeg[d.Pop[i]]++;
                float w = Math.Abs(d.Weight[e]);   // blob already carries the w_syn factor
                if (w > strongest[tp]) strongest[tp] = w;
            }
        }

        Console.WriteLine("pop            neurons   out-syn    in-syn    out(+)   out(-)   strongest-in");
        for (int p = 1; p <= 10; p++)
            if (counts[p] > 0)
                Console.WriteLine($"{PopName(p),-14} {counts[p],7} {outDeg[p],9} {inDeg[p],9} " +
                                  $"{outPos[p],9} {outNeg[p],9} {strongest[p],10:F3} mV");
        Console.WriteLine($"\n(a neuron needs {(Circuit.VTh - Circuit.V0):F1} mV of conductance to reach threshold)");

        if (!run) return 0;

        // drive the odour seeds and watch where activity actually goes
        var c = new Circuit(d);
        var rng = new Random(7);
        float pStep = 150f * c.Dt / 1000f, poiW = Circuit.WSyn * 250f;
        var byPop = new long[11];
        for (int step = 0; step < 4000; step++)
        {
            Fire(c, d.Odor, pStep, poiW, rng);
            int before = 0;
            c.Step();
            before = c.LastSpikes;
            if (before > 0) { /* counted inside via PopRate below */ }
        }
        Console.WriteLine("\n4000 steps driven on odour seeds only - mean rate per population:");
        for (int p = 1; p <= 10; p++)
            if (counts[p] > 0)
                Console.WriteLine($"   {PopName(p),-14} {c.PopRate((byte)p),8:F2} Hz");
        Console.WriteLine($"   spikes in last step: {c.LastSpikes}");
        return 0;
    }
}
