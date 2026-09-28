// Build the MaleCNS sub-circuit blob for the Terraria mod.
//
// Why this exists: the MaleCNS flat connectome is 151,856,684 edges and the budgeted
// growth pass is a membership test per edge per round.  Doing that in interpreted
// Python takes tens of minutes; the same loops here run in seconds.  So the pipeline is
// split - Python writes a compact edge stream (tools/export_edges.py), this program
// does the selection and emits the .brain blob the mod loads.
//
// Memory strategy: the edge stream is read once per growth round and only per-candidate
// scores are kept (never all 151M edges), then a final pass keeps just the induced
// subgraph.  Peak RSS stays well under a gigabyte even though the input is 2.4 GB.
//
// Usage:
//   dotnet run --project tools/CircuitBuilder -- <edges.bin> <annotations.tsv> <out.brain> [maxNeurons] [rounds]
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

internal static class CircuitBuilder
{
    private const float WSyn = 0.275f;   // Shiu et al. 2024, the model's only free parameter

    /// <summary>
    /// MaleCNS's `weight` column is a connection strength on its own scale (integers
    /// ~92..2591, modes near 95 plus a long tail), not the paper's `Excitatory x
    /// Connectivity` (1..~20 contacts).  Tested against the offline preview, the value
    /// works directly as a synapse count: with unit = 1000 the strongest connection lands
    /// at 0.71 mV, i.e. ~10 synapses' worth at w_syn = 0.275 mV, which is exactly the
    /// regime the published model was tuned for.  Earlier attempts (no scaling at all, and
    /// a stray /1000) put single synapses at 1e-3 of that and no signal could propagate
    /// past the directly driven seeds.
    /// </summary>
    private const float SourceWeightUnit = 1000f;

    private const int PopUnknown = 0, PopSensory = 1, PopAntennal = 2, PopMushroom = 3,
        PopDan = 4, PopMbon = 5, PopDescending = 6, PopMotor = 7, PopInterneuron = 8, PopVnc = 9,
        PopSelfMotion = 10, PopCentralComplex = 11;
    private const int NPop = 12;

    // Central-complex subfamilies (written into the per-neuron pad byte so the in-game
    // readout and the offline harness can report the same breakdown).
    private const int CxNone = 0, CxRing = 1, CxColumnar = 2, CxFanBody = 3, CxOther = 4;

    private static readonly (int Family, string Pattern)[] CxFamilyRules =
    {
        // Labels are "type | hemibrainType", so these are prefix matches.  Anchoring them
        // (with $ or \b) silently emptied families: the label ends in "| EPG", not in "EPG",
        // and the columnar types append a suffix (PFNp_b, Delta7, hDeltaK).
        (CxRing, @"^(EPG|PEG|EPGt)"),         // ellipsoid-body ring: the heading bump
        (CxColumnar, @"^(PFN|PFR|hDelta|Delta\d|vDelta)"),   // protocerebral bridge <-> fan-shaped body
        (CxFanBody, @"^FB\d"),                 // fan-shaped body columnar (steering)
        (CxOther, @"^(ER\d|ExR\d|PEN|EL\b|LAL\d|IB\d|TuBu|CRE|PFL\d|PLP\d|SpsP)"),  // ring inputs / pre-motor
    };

    private static readonly (int Pop, string Pattern)[] PopRules =
    {
        // Central complex first: the head-direction and columnar families are where a
        // self-referential signal would have to land, and they are also easy to catch by
        // accident with broader patterns.
        //   EPG / PEG  - head-direction cells of the ellipsoid body
        //   PFN / PFR  - protocerebral-bridge <-> fan-shaped-body columnar cells (hDelta)
        //   FB*        - fan-shaped body columnar cells
        //   ER / ExR   - ellipsoid-body ring neurons and their extrinsic (landmark) input.
        //                Probing the full connectome (tools/PathProbe) showed that the ring's
        //                actual presynaptic partners are ER4d/ER2/ER3/ExR1-6/PEN/Delta7, NOT
        //                the lobula plate cells: a body-occluded patch of the visual field
        //                reaches the ring through this visual relay, and the relay has to be
        //                inside the circuit for the experiment to have a route at all.
        (PopCentralComplex, @"^(EPG|PEG|EPGt|PFN|PFR|FB\d|hDelta|Delta\d|vDelta|LAL\d|IB\d|ER\d|ExR\d|PEN\b|EL\b|TuBu|CRE\b|PFL\d|PLP\d|SpsP)"),
        // Self-motion / gaze-stabilisation cells: the lobula plate tangential cells.
        // An earlier version of this pattern also carried "JO-EV\d".  Those are Johnston's-organ
        // neurons -- antennal mechanosensory cells, a different sensory modality entirely --
        // and they are recognisable as such in the release: the JO-* types have neither a
        // hemibrainType nor a somaLocation, because their somata sit in the antenna, outside
        // the imaged CNS volume.  Including them made 176 of the 1,770 "visual" pool cells
        // non-visual and gave those 176 cells a preferred direction from a missing coordinate
        // (all of them fell on one side of the midline).  They remain in the circuit as part
        // of the antennal population; they are no longer part of the visual pool.
        (PopSelfMotion, @"^(H1|H2|V1|VS|HS|LHAV|LHPV)"),
        (PopDan, @"^(PAM|PPL|PAL)\d"),
        (PopMbon, @"^MBON"),
        (PopMushroom, @"^KC"),
        (PopMotor, @"^MN|proboscis|CEM|feeding"),
        (PopDescending, @"^DN"),
        (PopAntennal, @"adPN|vPN|smPN|lvPN|_PN|^ALPN|^PN\d|WEDPN"),
        (PopSensory, @"GRN|^GR\d|sugar|sweet|tpGRN|^ORN"),
        (PopVnc, @"^VNC|^Leg|^Wing|^Haltere"),
    };

    private static readonly (string Name, string Pattern)[] SeedRules =
    {
        // Cell-type names only.  Matching loosely here is expensive: a pattern like
        // "_PN" also catches optic-lobe cells (Mi1, L1, ...) and eats the whole neuron
        // budget before the growth rounds can pull in the mushroom body.
        //
        // "odor" is deliberately broad (every antennal-lobe cell, not just olfactory
        // receptor neurons): the Kenyon cells only receive ~2.7 synapses per seeded PN,
        // so a thin seed set leaves the mushroom body unable to reach threshold - measured
        // with tools/CircuitPreview --reach.  Matching the population the classifier
        // already assigns (antennal_lobe) is both broader and safer than extending a regex.
        ("sugar", @"GRN|^GR\d|sugar|sweet|tpGRN"),
        ("odor", @"^(H1|H2|V1|VS|HS|JO-EV\d|LHAV|LHPV)|^ORN|^OR\d|[a-z]PN\d*$|_adPN|_vPN|_lPN|WEDPN|^lLN|^LN|^ALPN|^LHLN"),
        ("reward", @"^(PAM|PPL|PAL)\d"),
        ("motor", @"^MN[a-z]|proboscis|^CEM"),
        // the pool that lights up when the fly watches itself move (lobula plate tangential
        // cells only: see the note on PopSelfMotion above for why JO-* is excluded)
        ("selfmotion", @"^(H1|H2|V1|VS|HS|LHAV|LHPV)"),
        // the readout region: head-direction / columnar cells of the central complex.
        // These are not an input - they are what the experiment measures.
        ("centralcomplex", @"^(EPG|PEG|EPGt|PFN|PFR|FB\d|hDelta|Delta\d)"),
    };

    private static int Main(string[] args)
    {
        if (args.Length < 3)
        {
            Console.Error.WriteLine("usage: CircuitBuilder <edges.bin> <annotations.tsv> <out.brain> [maxNeurons] [rounds]");
            return 2;
        }
        string edgesPath = args[0], annPath = args[1], outPath = args[2];
        int maxNeurons = args.Length > 3 ? int.Parse(args[3]) : 3000;
        int rounds = args.Length > 4 ? int.Parse(args[4]) : 3;
        string ntPath = args.Length > 5 ? args[5] : null;
        // The seeds alone can exceed the budget (sensory + reward + motor + self-motion
        // is ~5800 cells), in which case no growth round runs and the mushroom body never
        // joins the circuit.  Keep a floor so at least one growth round always happens.
        maxNeurons = Math.Max(maxNeurons, 12_000);
        var sw = System.Diagnostics.Stopwatch.StartNew();

        // ---------------------------------------------------------------- transmitters
        // The flat connectome edge table has no sign, so inhibition comes from the
        // presynaptic cell's predicted transmitter (GABA / glutamate are inhibitory in
        // the fly brain; histamine is inhibitory in the optic lobe).
        var ntByBody = new Dictionary<long, string>();
        if (!string.IsNullOrEmpty(ntPath) && File.Exists(ntPath))
        {
            foreach (var line in File.ReadLines(ntPath).Skip(1))
            {
                int tab = line.IndexOf('\t');
                if (tab <= 0) continue;
                if (long.TryParse(line.AsSpan(0, tab), out long bid))
                    ntByBody[bid] = line.Substring(tab + 1).Trim();
            }
        }
        Console.WriteLine($"transmitters: {ntByBody.Count} labelled bodies"
                          + (ntByBody.Count == 0 ? "  (no sign data - all synapses excitatory)" : ""));

        // ---------------------------------------------------------------- annotations
        var ids = new List<long>(220_000);
        var labels = new List<string>(220_000);
        var soma = new List<float>(660_000);
        foreach (var line in File.ReadLines(annPath).Skip(1))
        {
            var f = line.Split('\t');
            if (f.Length < 4) continue;
            if (!long.TryParse(f[0], out long bid)) continue;
            ids.Add(bid);
            labels.Add(f[1] + " | " + f[2]);
            var xyz = f[3].Split(',');
            for (int k = 0; k < 3; k++)
                soma.Add(k < xyz.Length && float.TryParse(xyz[k], NumberStyles.Float,
                    CultureInfo.InvariantCulture, out float v) ? v * 8f / 1000f : 0f);
        }
        var indexByBody = new Dictionary<long, int>(ids.Count);
        for (int i = 0; i < ids.Count; i++) indexByBody[ids[i]] = i;
        Console.WriteLine($"annotations: {ids.Count} bodies  ({sw.Elapsed.TotalSeconds:F1}s)");

        var compiled = PopRules.Select(r => (r.Pop, Rx: new Regex(r.Pattern, RegexOptions.IgnoreCase))).ToArray();
        var cxRules = CxFamilyRules.Select(r => (r.Family, Rx: new Regex(r.Pattern, RegexOptions.IgnoreCase))).ToArray();
        var popOf = new byte[ids.Count];
        var cxFamOf = new byte[ids.Count];
        var popCountsAll = new int[NPop];
        for (int i = 0; i < ids.Count; i++)
        {
            byte pop = PopUnknown;
            foreach (var (p, rx) in compiled)
                if (rx.IsMatch(labels[i])) { pop = (byte)p; break; }
            popOf[i] = pop;
            popCountsAll[pop]++;

            // The central complex is not one structure: the ring attractor measures the
            // fly's heading (EPG/PEG), the protocerebral bridge and fan-shaped body turn
            // that heading into steering (PFN/PFR, FB columnar), and the rest is
            // pre-motor.  A whole-CX average would blur a shift that only moves one of
            // these, so every neuron carries its subfamily to the experiment.  Anything in
            // the CX population without a matching family falls into `other` rather than
            // being left at 0, so no CX neuron can silently vanish from the readout.
            if (pop == PopCentralComplex)
            {
                cxFamOf[i] = (byte)CxOther;
                foreach (var (fam, rx) in cxRules)
                    if (rx.IsMatch(labels[i])) { cxFamOf[i] = (byte)fam; break; }
            }
        }
        Console.WriteLine("annotation populations: " + string.Join(", ",
            Enumerable.Range(0, NPop).Where(p => popCountsAll[p] > 0).Select(p => $"{PopName(p)}={popCountsAll[p]}")));

        var seeds = new Dictionary<string, List<long>>();
        foreach (var (name, pat) in SeedRules)
        {
            var rx = new Regex(pat, RegexOptions.IgnoreCase);
            seeds[name] = Enumerable.Range(0, ids.Count).Where(i => rx.IsMatch(labels[i]))
                                    .Select(i => ids[i]).ToList();
        }
        Console.WriteLine("seeds: " + string.Join(", ", seeds.Select(kv => $"{kv.Key}={kv.Value.Count}")));

        // ---------------------------------------------------------------- selection
        var sel = new bool[ids.Count];
        var chosen = new List<long>();
        var chosenSet = new HashSet<long>();
        // Order matters: the growth budget is filled from the seeds first, so the
        // chemosensory afferents (the only cells the food item can drive directly) go in
        // before the reward and motor pools, and the self-motion cells are included
        // because the fly's eye view drives them.
        // centralcomplex is seeded last but is not an input: it guarantees the readout
        // region of the self-observation experiment is present in the induced circuit and
        // is not crowded out by the growth budget.
        foreach (string group in new[] { "sugar", "odor", "reward", "motor", "selfmotion", "centralcomplex" })
            foreach (long bid in seeds[group])
                if (chosenSet.Add(bid)) chosen.Add(bid);
        foreach (long bid in chosen)
            if (indexByBody.TryGetValue(bid, out int idx)) sel[idx] = true;
        Console.WriteLine($"round 0: {chosen.Count} seeds");

        for (int rnd = 1; rnd <= rounds && chosen.Count < maxNeurons; rnd++)
        {
            var score = new Dictionary<int, double>();
            foreach (var (pre, post, w) in ReadEdges(edgesPath))
            {
                if (!indexByBody.TryGetValue(pre, out int a)) continue;
                if (!indexByBody.TryGetValue(post, out int b)) continue;
                bool ain = sel[a], bin = sel[b];
                if (ain == bin) continue;
                int cand = ain ? b : a;
                if (sel[cand]) continue;
                score.TryGetValue(cand, out double s);
                score[cand] = s + w;
            }
            var ranked = score.OrderByDescending(kv => kv.Value).Take(maxNeurons - chosen.Count).ToList();
            foreach (var kv in ranked)
            {
                sel[kv.Key] = true;
                chosen.Add(ids[kv.Key]);
                chosenSet.Add(ids[kv.Key]);
            }
            Console.WriteLine($"round {rnd}: +{ranked.Count} -> {chosen.Count} neurons "
                              + $"({score.Count} candidates, {sw.Elapsed.TotalSeconds:F0}s)");
            if (ranked.Count == 0) break;
        }

        // ---------------------------------------------------------------- induced edges
        var index = new Dictionary<long, int>(chosen.Count);
        for (int i = 0; i < chosen.Count; i++) index[chosen[i]] = i;
        var edgeList = new List<(int A, int B, float W)>();
        int inhibitory = 0;
        foreach (var (pre, post, w) in ReadEdges(edgesPath))
        {
            if (!index.TryGetValue(pre, out int a)) continue;
            if (!index.TryGetValue(post, out int b)) continue;
            float signed = w;
            if (ntByBody.TryGetValue(pre, out string nt) && IsInhibitory(nt))
            {
                signed = -w;
                inhibitory++;
            }
            edgeList.Add((a, b, signed));
        }
        int n = chosen.Count;
        var popOut = new byte[n];
        var cxFamily = new byte[n];
        var popCounts = new int[NPop];
        var cxFamCounts = new int[5];
        for (int i = 0; i < n; i++)
        {
            int ai = indexByBody[chosen[i]];
            popOut[i] = popOf[ai];
            popCounts[popOut[i]]++;
            cxFamily[i] = cxFamOf[ai];
            cxFamCounts[cxFamily[i]]++;
        }
        Console.WriteLine($"cx subfamilies: ring={cxFamCounts[CxRing]} columnar={cxFamCounts[CxColumnar]} "
                          + $"fanbody={cxFamCounts[CxFanBody]} other={cxFamCounts[CxOther]}");

        Console.WriteLine($"sub-circuit: {n} neurons, {edgeList.Count} synapses "
                          + $"({inhibitory} inhibitory = {100.0 * inhibitory / Math.Max(1, edgeList.Count):F0}%)  "
                          + $"({sw.Elapsed.TotalSeconds:F0}s)");

        // The LIF step forwards every outgoing synapse of every neuron that spikes, so the
        // per-tick cost scales with the total synapse count.  Terraria gives 16 ms per
        // frame for the whole game.
        //
        // The budget is set above the induced sub-graph (12000 neurons of a 166k-neuron
        // connectome induce ~1.6M synapses) so that NOTHING is pruned.  Decimating to
        // 600k - a third of the wiring - was silently destroying the experiment: a Kenyon
        // cell keeps only ~5 of its ~13 antennal inputs, 5 x 0.275 mV never reaches the
        // 7 mV threshold, and the mushroom body read flat 0 Hz in every scenario.  A
        // connectome experiment that reports a dynamical shift has to run the connectome
        // it was given; the budget is a backstop for a bigger circuit, not a lever.
        const int maxSynapses = 2_000_000;
        if (edgeList.Count > maxSynapses)
        {
            var byPre = new Dictionary<int, List<(int B, float AbsW, bool Inhib, bool Plast)>>();
            foreach (var e in edgeList)
            {
                bool plast = popOut[e.A] == PopMushroom && popOut[e.B] == PopMbon;
                if (!byPre.TryGetValue(e.A, out var list))
                    byPre[e.A] = list = new List<(int, float, bool, bool)>();
                list.Add((e.B, Math.Abs(e.W), e.W < 0, plast));
            }
            double total = 0;
            foreach (var kv in byPre) total += kv.Value.Count;
            var keep = new List<(int A, int B, float W)>(maxSynapses);
            foreach (var kv in byPre)
            {
                // proportional share so no single hub eats the whole budget
                int share = Math.Max(1, (int)(maxSynapses * kv.Value.Count / total));
                foreach (var x in kv.Value
                             .OrderByDescending(x => (x.Inhib ? 4f : 0f) + (x.Plast ? 2f : 0f) + x.AbsW)
                             .Take(share))
                    keep.Add((kv.Key, x.B, (x.Inhib ? -1f : 1f) * x.AbsW));
            }
            Console.WriteLine($"decimated to {keep.Count} synapses (budget {maxSynapses})");
            edgeList = keep;
        }

        int nsyn = edgeList.Count;
        // recomputed here, not carried over: the decimation above changes the total, so a
        // pre-decimation counter would overstate inhibition (it briefly read as 423,913
        // inhibitory out of 594,036 synapses, which is impossible).
        inhibitory = edgeList.Count(e => e.W < 0);
        var offsets = new int[n + 1];
        foreach (var e in edgeList) offsets[e.A + 1]++;
        for (int i = 0; i < n; i++) offsets[i + 1] += offsets[i];
        var cursor = (int[])offsets.Clone();
        var targets = new int[nsyn];
        var weights = new float[nsyn];
        var preOf = new int[nsyn];
        foreach (var e in edgeList)
        {
            int k = cursor[e.A]++;
            targets[k] = e.B;
            weights[k] = e.W * WSyn;
            preOf[k] = e.A;
        }
        var mask = new byte[nsyn];
        for (int k = 0; k < nsyn; k++)
        {
            int ai = indexByBody[chosen[preOf[k]]];
            int bi = indexByBody[chosen[targets[k]]];
            if (popOf[ai] == PopMushroom && popOf[bi] == PopMbon) mask[k] = 1;
        }

        int[] SeedIdx(string name) => seeds[name].Where(chosenSet.Contains).Select(b => index[b]).ToArray();
        var sugar = SeedIdx("sugar");
        var motor = SeedIdx("motor");
        var odor = SeedIdx("odor");
        var selfmotion = SeedIdx("selfmotion");
        // The readout region is the whole central-complex population, not just the cells
        // matched by the seed regex: the CX-adjacent pre-motor families (LAL/IB/ER/TuBu)
        // are part of the same block and the experiment must see them.  Using the seed
        // regex here silently dropped 228 of 1628 CX neurons from the readout.
        var centralComplex = Enumerable.Range(0, n)
            .Where(i => popOut[i] == PopCentralComplex).ToArray();

        // The visual relay into the central complex, derived from the connectome rather than
        // from names: cells that receive from the rotation-sensitive pool AND project into
        // the CX.  In the fly the ring is fed by visual landmark cells (the AOTU -> TuBu ->
        // ExR route) and by the noduli; whatever the annotations call them, the cells that
        // sit on this 2-hop path are the ones a body-occluded patch of the visual field has
        // to travel through.  They are written to the blob so the experiment drives the
        // route that actually exists instead of a name-based guess.
        var intoRelay = new int[n];
        var toCx = new int[n];
        var toRing = new int[n];
        foreach (var e in edgeList)
        {
            if (popOut[e.A] == PopSelfMotion && popOut[e.B] != PopSelfMotion) intoRelay[e.B]++;
            if (popOut[e.B] == PopCentralComplex && popOut[e.A] != PopCentralComplex) toCx[e.A]++;
            if (cxFamily[e.B] == CxRing && popOut[e.A] != PopSelfMotion) toRing[e.A]++;
        }
        bool IsRelay(int i) => popOut[i] != PopSelfMotion && intoRelay[i] >= 3
                               && (toRing[i] >= 3 || toCx[i] >= 3);
        var visualRelay = Enumerable.Range(0, n).Where(IsRelay).ToArray();
        Console.WriteLine($"visual relay into the CX: {visualRelay.Length} cells "
                          + $"({visualRelay.Count(i => toRing[i] >= 3)} of them project onto the heading ring, "
                          + $"{visualRelay.Count(i => cxFamOf[i] != 0)} are ring-input cell types, "
                          + $"{visualRelay.Count(i => popOut[i] == PopUnknown)} unlabelled)");

        // ---------------------------------------------------------------- blob
        using (var fs = File.Create(outPath))
        using (var bw = new BinaryWriter(fs))
        {
            // FLYMIND4 adds a sixth index array: the visual relay into the CX (cells that
            // receive from the rotation-sensitive pool and project onto the central
            // complex).  It is what the experiment applies the body-patch manipulation to
            // when it is not driving the self-motion pool itself.
            bw.Write(System.Text.Encoding.ASCII.GetBytes("FLYMIND4"));
            bw.Write(n);
            bw.Write(nsyn);
            bw.Write(0);
            for (int p = 0; p < NPop; p++) bw.Write(popCounts[p]);
            bw.Write(sugar.Length);
            bw.Write(motor.Length);
            bw.Write(odor.Length);
            bw.Write(selfmotion.Length);
            bw.Write(centralComplex.Length);
            bw.Write(visualRelay.Length);
            for (int i = 0; i < n; i++)
            {
                int ai = indexByBody[chosen[i]];
                bw.Write((ulong)chosen[i]);
                bw.Write(soma[ai * 3]);
                bw.Write(soma[ai * 3 + 1]);
                bw.Write(soma[ai * 3 + 2]);
                bw.Write(popOut[i]);
                bw.Write(cxFamily[i]);
                bw.Write((byte)0);
                bw.Write((byte)0);
            }
            foreach (int v in offsets) bw.Write(v);
            foreach (int v in targets) bw.Write(v);
            foreach (float v in weights) bw.Write(v);
            bw.Write(mask);
            foreach (float v in weights) bw.Write(v);
            foreach (int v in sugar) bw.Write(v);
            foreach (int v in motor) bw.Write(v);
            foreach (int v in odor) bw.Write(v);
            foreach (int v in selfmotion) bw.Write(v);
            foreach (int v in centralComplex) bw.Write(v);
            foreach (int v in visualRelay) bw.Write(v);
            var json = System.Text.Encoding.UTF8.GetBytes(
                $"{{\"source\":\"MaleCNS v1.0 (Berg et al. 2026)\"," +
                $"\"model\":\"Shiu et al. 2024 LIF, w_syn={WSyn}\"," +
                $"\"n_neurons\":{n},\"n_edges\":{nsyn}," +
                $"\"n_inhibitory_synapses\":{inhibitory}," +
                $"\"n_plastic_synapses\":{mask.Count(b => b != 0)}," +
                $"\"sign_source\":\"consensus_nt per presynaptic cell (GABA/glutamate/histamine negative)\"," +
                $"\"seeds\":{{\"sugar\":{sugar.Length},\"motor\":{motor.Length}," +
                $"\"odor\":{odor.Length},\"selfmotion\":{selfmotion.Length}," +
                $"\"centralcomplex\":{centralComplex.Length}," +
                $"\"visualrelay\":{visualRelay.Length}}}," +
                $"\"populations\":{{{string.Join(",", Enumerable.Range(0, NPop).Where(p => popCounts[p] > 0)
                    .Select(p => $"\"{PopName(p)}\":{popCounts[p]}"))}}}," +
                // conductance written per edge is (source weight / source_weight_unit) * w_syn;
                // the model applies an extra global gain kappa on top, calibrated so the
                // unstimulated circuit sits in a spontaneously active regime (see METHODS.md)
                $"\"source_weight_unit\":{SourceWeightUnit}," +
                $"\"cx_subfamilies\":{{\"ring\":{cxFamCounts[CxRing]}," +
                $"\"columnar\":{cxFamCounts[CxColumnar]},\"fanbody\":{cxFamCounts[CxFanBody]}," +
                $"\"other\":{cxFamCounts[CxOther]}}}}}");
            bw.Write(json.Length);
            bw.Write(json);
        }
        Console.WriteLine($"wrote {outPath} ({new FileInfo(outPath).Length / 1e6:F2} MB) in {sw.Elapsed.TotalSeconds:F0}s");
        return 0;
    }

    /// <summary>
    /// Stream the compact edge file: int64 count, then count x (int64 pre, int64 post,
    /// int32 strength).
    ///
    /// The int32 carries the source table's `weight` value exactly as written by
    /// tools/export_edges.py (it is an integer in the source, range ~92..2591), NOT a
    /// scaled fixed-point number.  Dividing it here as well as by SourceWeightUnit was a
    /// silent x1000 error: every synapse in the blob came out at 1e-3 of its intended
    /// conductance, the strongest single input reached 0.0025 mV, and nothing except the
    /// directly driven seeds could ever fire.
    /// </summary>
    private static IEnumerable<(long Pre, long Post, float W)> ReadEdges(string path)
    {
        using var fs = File.OpenRead(path);
        using var br = new BinaryReader(fs);
        long count = br.ReadInt64();
        for (long i = 0; i < count; i++)
            yield return (br.ReadInt64(), br.ReadInt64(),
                          br.ReadInt32() / SourceWeightUnit);
    }

    /// <summary>
    /// Transmitters that hyperpolarise the postsynaptic cell in Drosophila.  Acetylcholine,
    /// dopamine, serotonin and octopamine are treated as excitatory/modulatory here; the
    /// "unclear" label is left excitatory on purpose rather than guessing.
    /// </summary>
    private static bool IsInhibitory(string nt) =>
        nt == "gaba" || nt == "glutamate" || nt == "glycine" || nt == "histamine";

    private static string PopName(int p) => p switch
    {
        1 => "sensory", 2 => "antennal_lobe", 3 => "kenyon_cell", 4 => "dopamine",
        5 => "mbon", 6 => "descending", 7 => "motor", 8 => "interneuron", 9 => "vnc",
        10 => "self_motion", 11 => "central_complex",
        _ => "unknown",
    };
}
