// Where does the fly's own rotation actually reach the heading ring?
//
// The extracted circuit showed only 67 synapses from the self-motion pool (LPTC) into the
// EPG/PEG heading ring, and a redistribution of the LPTC drive changed nothing in the
// central complex.  Before blaming the experiment, check the connectome: this tool scans
// the full flat edge list once and answers three questions.
//
//   1. which cell types project onto the heading ring (all presynaptic partners of EPG/PEG)
//   2. which cell types the rotation-sensitive cells project onto
//   3. which single cells sit on BOTH lists - the actual angular-velocity relay, i.e. cells
//      that receive from LPTC and send to the ring.  If the circuit never selected those,
//      the manipulation cannot reach the ring no matter how it is scaled.
//
// Usage:
//   PathProbe <edges.bin> <annotations.tsv> [epgRegex] [lptcRegex]
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.Error.WriteLine("usage: PathProbe <edges.bin> <annotations.tsv> [epgRegex] [lptcRegex]");
            return 2;
        }
        string edgePath = args[0], annPath = args[1];
        string epgPat = args.Length > 2 ? args[2] : @"^(EPG|PEG|EPGt)$";
        string lptcPat = args.Length > 3 ? args[3] : @"^(H1|H2|H3|HS|VS\d+|V1|LHAV|LHPV|JO-EV\d+).*";

        var epgRx = new System.Text.RegularExpressions.Regex(epgPat,
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        var lptcRx = new System.Text.RegularExpressions.Regex(lptcPat,
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);

        var type = new Dictionary<long, string>();
        foreach (var line in File.ReadLines(annPath).Skip(1))
        {
            var f = line.Split('\t');
            if (f.Length < 2) continue;
            if (long.TryParse(f[0], out long id)) type[id] = f[1];
        }

        var epg = new HashSet<long>(type.Where(kv => epgRx.IsMatch(kv.Value)).Select(kv => kv.Key));
        var lptc = new HashSet<long>(type.Where(kv => lptcRx.IsMatch(kv.Value)).Select(kv => kv.Key));
        Console.WriteLine($"EPG/PEG set: {epg.Count} bodies   LPTC set: {lptc.Count} bodies");
        Console.WriteLine("  epg examples: " + string.Join(", ", epg.Take(5).Select(x => type[x])));
        Console.WriteLine("  lptc examples: " + string.Join(", ", lptc.Take(8).Select(x => type[x])));
        Console.WriteLine("  lptc types: " + string.Join(", ",
            lptc.Select(x => type[x]).Distinct().Take(20)) + "\n");

        // one pass over the whole connectome
        var toEpgByType = new Dictionary<string, long>();
        var fromLptcByType = new Dictionary<string, long>();
        var toEpgByCell = new Dictionary<long, long>();       // X -> synapses X -> EPG
        var fromLptcByCell = new Dictionary<long, long>();    // X -> synapses LPTC -> X
        var epgIn = new Dictionary<long, long>();
        var lptcOut = new Dictionary<long, long>();

        using (var fs = new FileStream(edgePath, FileMode.Open, FileAccess.Read, FileShare.Read, 1 << 20))
        using (var br = new BinaryReader(fs))
        {
            long count = br.ReadInt64();
            var buf = new byte[20 * 4096];
            long done = 0;
            while (done < count)
            {
                int batch = (int)Math.Min(4096, count - done);
                int got = 0, need = batch * 20;
                while (got < need)
                {
                    int r = br.Read(buf, got, need - got);
                    if (r <= 0) break;
                    got += r;
                }
                if (got < need) break;
                for (int k = 0; k < batch; k++)
                {
                    int o = k * 20;
                    long pre = BitConverter.ToInt64(buf, o);
                    long post = BitConverter.ToInt64(buf, o + 8);
                    bool preEpg = epg.Contains(pre), postEpg = epg.Contains(post);
                    bool preLp = lptc.Contains(pre), postLp = lptc.Contains(post);
                    if (postEpg && !preEpg)
                    {
                        To(toEpgByCell, pre);
                        Bump(toEpgByType, type.TryGetValue(pre, out string t) ? t : "?");
                    }
                    if (preEpg && postEpg) { To(epgIn, pre); }
                    if (preLp && !postLp)
                    {
                        To(fromLptcByCell, post);
                        Bump(fromLptcByType, type.TryGetValue(post, out string t) ? t : "?");
                    }
                    if (postLp && preLp) { To(lptcOut, pre); }
                }
                done += batch;
            }
            Console.WriteLine($"scanned {done} edges\n");
        }

        Console.WriteLine("=== 1. who projects onto the heading ring (EPG/PEG) - top partner types ===");
        foreach (var kv in toEpgByType.OrderByDescending(kv => kv.Value).Take(25))
            Console.WriteLine($"   {kv.Key,-28} {kv.Value,9} synapses");

        Console.WriteLine("\n=== 2. where the rotation-sensitive cells (LPTC) project - top target types ===");
        foreach (var kv in fromLptcByType.OrderByDescending(kv => kv.Value).Take(25))
            Console.WriteLine($"   {kv.Key,-28} {kv.Value,9} synapses");

        Console.WriteLine("\n=== 3. the actual relay: cells that receive from LPTC AND project to EPG/PEG ===");
        var relays = fromLptcByCell.Keys.Where(toEpgByCell.ContainsKey)
            .Select(x => (Cell: x, FromLp: fromLptcByCell[x], ToEpg: toEpgByCell[x]))
            .OrderByDescending(r => Math.Min(r.FromLp, r.ToEpg)).Take(40).ToList();
        if (relays.Count == 0)
            Console.WriteLine("   none - the connectome has no 2-hop LPTC -> X -> EPG path in these tables");
        foreach (var r in relays)
        {
            string tn = type.TryGetValue(r.Cell, out string t) ? t : "?";
            Console.WriteLine($"   {r.Cell,12}  {tn,-24} LPTC->X {r.FromLp,7}   X->EPG {r.ToEpg,7}");
        }

        Console.WriteLine($"\nEPG/PEG internal recurrence (EPG->EPG presyn counts): {epgIn.Count} sources, "
                          + $"{epgIn.Values.Sum()} synapses");
        Console.WriteLine($"LPTC internal: {lptcOut.Count} sources, {lptcOut.Values.Sum()} synapses");
        return 0;
    }

    private static void To(Dictionary<long, long> d, long key)
    {
        d.TryGetValue(key, out long v);
        d[key] = v + 1;
    }

    private static void Bump(Dictionary<string, long> d, string key)
    {
        d.TryGetValue(key, out long v);
        d[key] = v + 1;
    }
}
