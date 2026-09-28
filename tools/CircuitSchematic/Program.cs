// Circuit schematic of the fly that runs in the mod.
//
// Reads the same FLYMIND3 blob the game loads (so the diagram cannot drift away from the
// circuit that actually runs) plus the MaleCNS annotation table (for cell-type names) and
// writes a Markdown schematic: population census, the inter-population connection matrix,
// the top pathways, the heading pathway of the central complex link by link, and the
// cell types behind every box - each one linked to its counterpart in the FlyWire
// resources (codex.flywire.ai / flywire.ai), because MaleCNS and FlyWire are the male and
// female halves of the same animal and the two nomenclatures have to be cross-walked to
// talk about "the fly's heading circuit" at all.
//
// Usage:
//   dotnet run --project tools/CircuitSchematic -- <flymind.brain> <annotations.tsv> <out.md>
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;

internal static class Program
{
    private const int NPop = 12;
    private static readonly string[] PopNames =
    {
        "unknown", "sensory", "antennal_lobe", "kenyon_cell", "dopamine", "mbon",
        "descending", "motor", "interneuron", "vnc", "self_motion", "central_complex",
    };
    private static readonly string[] CxNames = { "-", "ring (EPG/PEG)", "columnar (PFN/PFR/hDelta)", "fanbody (FB)", "other (LAL/IB/ER/TuBu)" };

    private static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.Error.WriteLine("usage: CircuitSchematic <flymind.brain> <annotations.tsv> [out.md]");
            return 2;
        }
        string blobPath = args[0], annPath = args[1];
        string outPath = args.Length > 2 ? args[2] : "circuit-schematic.md";

        var b = Load(blobPath);
        var types = LoadTypes(annPath);
        Console.WriteLine($"blob: {b.N} neurons, {b.Syn} synapses ({b.Inhibitory} inhibitory)");
        Console.WriteLine($"annotations: {types.Count} bodies");

        var sb = new StringBuilder();
        WriteHeader(sb, b, blobPath, annPath, types);
        WriteDiagram(sb, b, types);
        WriteCensus(sb, b, types);
        WriteMatrix(sb, b);
        WritePathways(sb, b);
        WriteHeadingChain(sb, b);
        WriteFanIn(sb, b);
        WriteLinks(sb);
        File.WriteAllText(outPath, sb.ToString(), new UTF8Encoding(false));
        Console.WriteLine($"wrote {outPath} ({new FileInfo(outPath).Length / 1024} KB)");
        return 0;
    }

    // ---------------------------------------------------------------- blob
    private sealed class Blob
    {
        public int N, Syn, Inhibitory;
        public int[] Offset, Target;
        public float[] Weight;
        public byte[] Pop, Cx;
        public ulong[] Body;
        public int[] CxIdx;
        /// <summary>Visual relay onto the CX (receives from the rotation pool, projects onto CX).</summary>
        public int[] Relay;
        public string Json;
    }

    private static Blob Load(string path)
    {
        using var br = new BinaryReader(File.OpenRead(path));
        var tag = Encoding.ASCII.GetString(br.ReadBytes(8));
        if (tag != "FLYMIND4")
            throw new InvalidDataException("expected FLYMIND4, got " + tag);
        var b = new Blob();
        b.N = (int)br.ReadUInt32(); b.Syn = (int)br.ReadUInt32(); br.ReadUInt32();
        for (int i = 0; i < NPop; i++) br.ReadUInt32();
        int nSugar = (int)br.ReadUInt32(), nMotor = (int)br.ReadUInt32(),
            nOdor = (int)br.ReadUInt32(), nSelf = (int)br.ReadUInt32(), nCx = (int)br.ReadUInt32(),
            nRelay = (int)br.ReadUInt32();
        b.Body = new ulong[b.N]; b.Pop = new byte[b.N]; b.Cx = new byte[b.N];
        var buf = new byte[24];
        for (int i = 0; i < b.N; i++)
        {
            br.Read(buf, 0, 24);
            b.Body[i] = BitConverter.ToUInt64(buf, 0);
            b.Pop[i] = buf[20];
            b.Cx[i] = buf[21];
        }
        b.Offset = ReadInts(br, b.N + 1);
        b.Target = ReadInts(br, b.Syn);
        b.Weight = ReadFloats(br, b.Syn);
        br.ReadBytes(b.Syn);                       // kc->mbon mask
        ReadFloats(br, b.Syn);                     // base weights
        ReadInts(br, nSugar); ReadInts(br, nMotor); ReadInts(br, nOdor); ReadInts(br, nSelf);
        b.CxIdx = ReadInts(br, nCx);
        b.Relay = ReadInts(br, nRelay);
        int jsonLen = (int)br.ReadUInt32();
        b.Json = Encoding.UTF8.GetString(br.ReadBytes(jsonLen));
        b.Inhibitory = b.Weight.Count(w => w < 0);
        return b;
    }

    private static int[] ReadInts(BinaryReader br, int n)
    {
        if (n <= 0) return Array.Empty<int>();
        var raw = br.ReadBytes(n * 4); var a = new int[n];
        Buffer.BlockCopy(raw, 0, a, 0, raw.Length); return a;
    }

    private static float[] ReadFloats(BinaryReader br, int n)
    {
        if (n <= 0) return Array.Empty<float>();
        var raw = br.ReadBytes(n * 4); var a = new float[n];
        Buffer.BlockCopy(raw, 0, a, 0, raw.Length); return a;
    }

    private static Dictionary<ulong, (string Type, string Hemi)> LoadTypes(string path)
    {
        var d = new Dictionary<ulong, (string, string)>();
        foreach (var line in File.ReadLines(path).Skip(1))
        {
            var f = line.Split('\t');
            if (f.Length < 3) continue;
            if (ulong.TryParse(f[0], out ulong id)) d[id] = (f[1], f[2]);
        }
        return d;
    }

    // ---------------------------------------------------------------- sections
    private static void WriteHeader(StringBuilder sb, Blob b, string blobPath, string annPath,
                                    Dictionary<ulong, (string Type, string Hemi)> types)
    {
        sb.AppendLine("# 果蝇神经电路简图 (MaleCNS v1.0 → 模组实际运行的回路)");
        sb.AppendLine();
        sb.AppendLine("这份简图不是手绘的示意图，而是从游戏实际加载的那个 blob 里算出来的：每个人群、每条通路、");
        sb.AppendLine("每个 CX 亚family 的突触数都是回路里的真实计数。细胞类型名来自 MaleCNS v1.0 注释表，");
        sb.AppendLine("并给出它在 FlyWire（雌性脑，v783）体系里的对应检索——MaleCNS 与 FlyWire 是同一物种的雄/雌两半，");
        sb.AppendLine("两套命名必须互相索引，才能把\"果蝇的朝向回路\"当作同一件事来讨论。");
        sb.AppendLine();
        sb.AppendLine($"- blob: `{Path.GetFileName(blobPath)}` — {b.N} 神经元 / {b.Syn} 突触 / {b.Inhibitory} 抑制性 ({100.0 * b.Inhibitory / b.Syn:F0}%)");
        sb.AppendLine($"- 注释: `{Path.GetFileName(annPath)}` — {types.Count} 个 body，覆盖回路内 {b.Body.Count(x => types.ContainsKey(x))}/{b.N} 个神经元");
        sb.AppendLine($"- 视觉中继 (LPTC → X → CX): {b.Relay.Length} 个细胞，其中 "
                      + $"{b.Relay.Count(i => b.Cx[i] != 0)} 个属于 CX 环的输入类型；"
                      + $"{b.Relay.Count(i => !types.ContainsKey(b.Body[i]))} 个尚未命名");
        sb.AppendLine($"- 元数据: `{b.Json}`");
        sb.AppendLine();
    }

    /// <summary>
    /// The diagram itself.  The boxes and arrows are hand laid out, the numbers in them are
    /// counted from the blob, so the picture can never drift away from the circuit that runs.
    /// </summary>
    private static void WriteDiagram(StringBuilder sb, Blob b,
                                     Dictionary<ulong, (string Type, string Hemi)> types)
    {
        int N(int fromPop, int toPop)
        {
            int c = 0;
            for (int i = 0; i < b.N; i++)
            {
                if (b.Pop[i] != fromPop) continue;
                for (int e = b.Offset[i]; e < b.Offset[i + 1]; e++)
                    if (b.Pop[b.Target[e]] == toPop) c++;
            }
            return c;
        }
        int NFam(int fromPop, int family)
        {
            int c = 0;
            for (int i = 0; i < b.N; i++)
            {
                if (b.Pop[i] != fromPop) continue;
                for (int e = b.Offset[i]; e < b.Offset[i + 1]; e++)
                    if (b.Cx[b.Target[e]] == family) c++;
            }
            return c;
        }
        int cnt(int pop) => Enumerable.Range(0, b.N).Count(i => b.Pop[i] == pop);
        var fam = new int[5];
        foreach (int i in b.CxIdx) fam[b.Cx[i]]++;

        sb.AppendLine("## 0. 简图 (数字全部由 blob 现算)");
        sb.AppendLine();
        sb.AppendLine("```");
        sb.AppendLine("        嗅觉 (食物)                           视觉 (复眼 → 视叶)");
        sb.AppendLine($"   ┌───────────────────┐                ┌──────────────────────────┐");
        sb.AppendLine($"   │ ORN/味觉  sensory │                │ 旋转光流细胞 LPTC        │");
        sb.AppendLine($"   │        {cnt(1),6}      │                │ (H1/H2/VS/V1/HS/JO-EV)   │");
        sb.AppendLine($"   └─────┬─────────────┘                │        {cnt(10),6}            │");
        sb.AppendLine($"         │ {N(1, 2),6}                       └───┬──────────────────┬───┘");
        sb.AppendLine($"   ┌─────▼─────────────┐                    │ {NFam(10, 1),6} → ring      │ {N(10, 11),6} → CX");
        sb.AppendLine($"   │ 触角叶     AL     │                    │ {NFam(10, 2),6} → columnar  │ {N(10, 2),5} → AL");
        sb.AppendLine($"   │        {cnt(2),6}      │                    │                          │");
        sb.AppendLine($"   └──┬──────────────┬──┘                    │                          │");
        sb.AppendLine($"      │ {N(2, 3),5} → KC   │                          │                          │");
        sb.AppendLine($"   ┌──▼───────────┐  │   ┌──────────────────────▼──────────────────────┐");
        sb.AppendLine($"   │ 蘑菇体 KC    │  │   │            中央复合体 CX  {cnt(11),5}              │");
        sb.AppendLine($"   │     {cnt(3),6}     │  │   │  ring(EPG/PEG) {fam[1],4}  ← 朝向 bump       │");
        sb.AppendLine($"   └──┬───────────┘  │   │  columnar      {fam[2],4}  (PFN/PFR/hDelta)   │");
        sb.AppendLine($"      │ {N(3, 5),5}      │   │  fanbody(FB)   {fam[3],4}  (转向)            │");
        sb.AppendLine($"   ┌──▼───────────┐  │   │  other         {fam[4],4}  (LAL/IB/ER/TuBu)   │");
        sb.AppendLine($"   │ MBON   {cnt(5),5}   │  │   └───────┬───────────────────────┬───────────┘");
        sb.AppendLine($"   └──────────────┘  │           │ {NFam(11, 3),6} → fanbody      │ {N(11, 2),5} → AL");
        sb.AppendLine($"                     │   ┌───────▼────────┐              │");
        sb.AppendLine($"                     └──▶│ 下行神经元 DN  │              │");
        sb.AppendLine($"                         │      {cnt(6),5}     │              │");
        sb.AppendLine($"                         └───────┬────────┘              │");
        sb.AppendLine($"                                 │ {N(6, 7),6} → motor");
        sb.AppendLine($"                         ┌───────▼────────┐");
        sb.AppendLine($"                         │ 运动神经元 MN  │   → 飞行肌 / 腿");
        sb.AppendLine($"                         │      {cnt(7),5}     │");
        sb.AppendLine($"                         └────────────────┘");
        sb.AppendLine("```");
        sb.AppendLine();
        sb.AppendLine("```mermaid");
        sb.AppendLine("flowchart LR");
        sb.AppendLine($"  ORN[\"ORN/味觉 sensory<br/>{cnt(1)}\"] -->|{N(1, 2)}| AL[\"触角叶 AL<br/>{cnt(2)}\"]");
        sb.AppendLine($"  AL -->|{N(2, 3)}| KC[\"蘑菇体 KC<br/>{cnt(3)}\"]");
        sb.AppendLine($"  AL -->|{N(2, 4)}| DAN[\"多巴胺 PAM/PPL<br/>{cnt(4)}\"]");
        sb.AppendLine($"  KC -->|{N(3, 5)}| MBON[\"MBON<br/>{cnt(5)}\"]");
        sb.AppendLine($"  DAN -->|{N(4, 3)}| KC");
        sb.AppendLine($"  LPTC[\"旋转光流 LPTC<br/>{cnt(10)}\"] -->|{NFam(10, 2)}| COL[\"CX columnar PFN/PFR/hDelta<br/>{fam[2]}\"]");
        sb.AppendLine($"  LPTC -->|{NFam(10, 1)}| RING[\"CX ring EPG/PEG 朝向 bump<br/>{fam[1]}\"]");
        sb.AppendLine($"  COL -->|{NFam(2, 1)}| RING");
        sb.AppendLine($"  RING -->|{NFam(1, 1)}| RING");
        sb.AppendLine($"  RING -->|{NFam(1, 3)}| FB[\"CX fanbody FB 柱状<br/>{fam[3]}\"]");
        sb.AppendLine($"  MBON -->|{N(5, 11)}| CX[\"CX 其余<br/>{fam[4]}\"]");
        sb.AppendLine($"  FB -->|{NFam(3, 6)}| DN[\"下行 DN<br/>{cnt(6)}\"]");
        sb.AppendLine($"  DN -->|{N(6, 7)}| MN[\"运动神经元 MN<br/>{cnt(7)}\"]");
        sb.AppendLine($"  CX --> DN");
        sb.AppendLine("```");
        sb.AppendLine();
        sb.AppendLine("> 视觉一侧是这份工作真正关心的通路：`LPTC → ring`、`columnar → ring`、`ring → ring`、");
        sb.AppendLine("> `ring → fanbody → DN → motor` 就是\"看见 → 朝向 → 转向\"的完整链。第三人称视角下，");
        sb.AppendLine("> 这条链的**输入端**（LPTC 所在的那部分视野）被果蝇自己的身体遮住，这正是要检验的扰动。");
        sb.AppendLine();
    }

    private static void WriteCensus(StringBuilder sb, Blob b, Dictionary<ulong, (string Type, string Hemi)> types)    {
        sb.AppendLine("## 1. 人群与 CX 亚family");
        sb.AppendLine();
        var counts = new int[NPop];
        for (int i = 0; i < b.N; i++) counts[b.Pop[i]]++;
        sb.AppendLine("| 人群 | 神经元 | 占回路 | 主要细胞类型 (MaleCNS `type`) |");
        sb.AppendLine("|---|---:|---:|---|");
        for (int p = 1; p < NPop; p++)
        {
            if (counts[p] == 0) continue;
            var top = TopTypes(b, types, i => b.Pop[i] == p, 6);
            sb.AppendLine($"| `{PopNames[p]}` | {counts[p]} | {100.0 * counts[p] / b.N:F1}% | {top} |");
        }
        sb.AppendLine();
        var cxCounts = new int[5];
        foreach (int i in b.CxIdx) cxCounts[b.Cx[i]]++;
        sb.AppendLine("| CX 亚family | 神经元 | 主要细胞类型 |");
        sb.AppendLine("|---|---:|---|");
        for (int f = 1; f <= 4; f++)
        {
            var top = TopTypes(b, types, i => b.Cx[i] == f, 8);
            sb.AppendLine($"| {CxNames[f]} | {cxCounts[f]} | {top} |");
        }
        sb.AppendLine();
    }

    private static string TopTypes(Blob b, Dictionary<ulong, (string Type, string Hemi)> types,
                                   Func<int, bool> pred, int k)
    {
        var t = new Dictionary<string, int>();
        for (int i = 0; i < b.N; i++)
        {
            if (!pred(i)) continue;
            if (!types.TryGetValue(b.Body[i], out var v)) continue;
            string key = v.Type;
            t.TryGetValue(key, out int c);
            t[key] = c + 1;
        }
        var top = t.OrderByDescending(kv => kv.Value).Take(k).ToList();
        if (top.Count == 0) return "_(未命名)_";
        return string.Join(", ", top.Select(kv => $"[{kv.Key}]({Codex(kv.Key)})×{kv.Value}"));
    }

    private static void WriteMatrix(StringBuilder sb, Blob b)
    {
        sb.AppendLine("## 2. 人群间连接矩阵 (突触数, 上=兴奋 / 下=抑制)");
        sb.AppendLine();
        var syn = new int[NPop, NPop]; var exc = new int[NPop, NPop];
        for (int i = 0; i < b.N; i++)
            for (int e = b.Offset[i]; e < b.Offset[i + 1]; e++)
            {
                int j = b.Target[e];
                syn[b.Pop[i], b.Pop[j]]++;
                if (b.Weight[e] >= 0) exc[b.Pop[i], b.Pop[j]]++;
            }
        var present = Enumerable.Range(1, NPop - 1).Where(p => Enumerable.Range(0, b.N).Any(i => b.Pop[i] == p)).ToArray();
        sb.Append("| pre \\ post |");
        foreach (int q in present) sb.Append($" {Short(PopNames[q])} |");
        sb.AppendLine();
        sb.Append("|---|" + string.Concat(present.Select(_ => "---:|")));
        sb.AppendLine();
        for (int p = 1; p < NPop; p++)
        {
            if (!present.Contains(p)) continue;
            sb.Append($"| **{Short(PopNames[p])}** |");
            foreach (int q in present)
            {
                if (syn[p, q] == 0) { sb.Append(" · |"); continue; }
                sb.Append($" {syn[p, q]}<br><sub>{exc[p, q]}+/{syn[p, q] - exc[p, q]}−</sub> |");
            }
            sb.AppendLine();
        }
        sb.AppendLine();
        sb.AppendLine("_斜体说明_: `+` 兴奋性突触, `−` 抑制性突触 (抑制性来自 presynaptic 细胞的递质预测)。");
        sb.AppendLine();
    }

    private static void WritePathways(StringBuilder sb, Blob b)
    {
        sb.AppendLine("## 3. 最强通路 (人群 → 人群)");
        sb.AppendLine();
        var syn = new Dictionary<(int, int), int>();
        for (int i = 0; i < b.N; i++)
            for (int e = b.Offset[i]; e < b.Offset[i + 1]; e++)
            {
                var key = (b.Pop[i], b.Pop[b.Target[e]]);
                syn.TryGetValue(key, out int c);
                syn[key] = c + 1;
            }
        sb.AppendLine("| # | 通路 | 突触 |");
        sb.AppendLine("|---:|---|---:|");
        int rank = 1;
        foreach (var kv in syn.OrderByDescending(kv => kv.Value).Take(24))
            sb.AppendLine($"| {rank++} | `{PopNames[kv.Key.Item1]}` → `{PopNames[kv.Key.Item2]}` | {kv.Value} |");
        sb.AppendLine();
    }

    /// <summary>
    /// The heading pathway, link by link.  This is the part of the circuit the
    /// self-observation experiment measures and (if the wiring is there) perturbs:
    /// rotation-sensitive optic-flow cells -> central-complex columnar/nodulus cells ->
    /// the EPG/PEG ring that holds the heading bump -> fan-shaped-body steering ->
    /// descending -> motor.
    /// </summary>
    private static void WriteHeadingChain(StringBuilder sb, Blob b)
    {
        sb.AppendLine("## 4. 朝向通路 (heading pathway) 逐段核对");
        sb.AppendLine();
        var syn = new int[NPop, NPop]; var exc = new int[NPop, NPop]; var inh = new int[NPop, NPop];
        for (int i = 0; i < b.N; i++)
            for (int e = b.Offset[i]; e < b.Offset[i + 1]; e++)
            {
                int j = b.Target[e];
                syn[b.Pop[i], b.Pop[j]]++;
                if (b.Weight[e] >= 0) exc[b.Pop[i], b.Pop[j]]++; else inh[b.Pop[i], b.Pop[j]]++;
            }
        int lp = 10, ring = 11;
        int lpRing = 0, ringRing = 0, lpCol = 0, colRing = 0, ringFb = 0, fbDn = 0, dnMotor = 0, ringOut = 0;
        bool[] isRing = new bool[b.N], isCol = new bool[b.N], isFb = new bool[b.N];
        foreach (int i in b.CxIdx)
        {
            if (b.Cx[i] == 1) isRing[i] = true;
            else if (b.Cx[i] == 2) isCol[i] = true;
            else if (b.Cx[i] == 3) isFb[i] = true;
        }
        for (int i = 0; i < b.N; i++)
            for (int e = b.Offset[i]; e < b.Offset[i + 1]; e++)
            {
                int j = b.Target[e];
                if (b.Pop[i] == lp && isRing[j]) lpRing++;
                if (b.Pop[i] == lp && isCol[j]) lpCol++;
                if (isCol[i] && isRing[j]) colRing++;
                if (isRing[i] && isRing[j]) ringRing++;
                if (isRing[i] && isFb[j]) ringFb++;
                if (isRing[i]) ringOut++;
                if (isFb[i] && b.Pop[j] == 6) fbDn++;
                if (b.Pop[i] == 6 && b.Pop[j] == 7) dnMotor++;
            }

        sb.AppendLine("| 段 | 含义 | 突触 | 判定 |");
        sb.AppendLine("|---|---|---:|---|");
        Row("self_motion → ring", "旋转光流细胞 → 朝向环 (角速度输入)", lpRing);
        Row("self_motion → columnar", "旋转光流细胞 → 小脑桥/扇形体柱状细胞", lpCol);
        Row("columnar → ring", "柱状细胞 → 朝向环 (attractor 更新)", colRing);
        Row("ring → ring", "朝向环内部递归 (attractor 自持)", ringRing);
        Row("ring → fanbody", "朝向环 → 扇形体 (朝向→转向)", ringFb);
        Row("fanbody → descending", "扇形体 → 下行神经元 (转向指令出脑)", fbDn);
        Row("descending → motor", "下行 → 运动神经元", dnMotor);
        sb.AppendLine();
        sb.AppendLine($"ring 细胞总输出突触: {ringOut}；ring←全体输入占比见矩阵。");
        sb.AppendLine();
        void Row(string seg, string meaning, int n) =>
            sb.AppendLine($"| `{seg}` | {meaning} | {n} | {(n == 0 ? "**断链**" : n < 50 ? "稀疏" : "存在")} |");
    }

    private static void WriteFanIn(StringBuilder sb, Blob b)
    {
        sb.AppendLine("## 5. 扇入/扇出 (为什么这个回路没有被剪枝)");
        sb.AppendLine();
        var inDeg = new int[NPop]; var outDeg = new long[NPop]; var cells = new int[NPop];
        var strongest = new float[NPop];
        for (int i = 0; i < b.N; i++)
        {
            cells[b.Pop[i]]++;
            outDeg[b.Pop[i]] += b.Offset[i + 1] - b.Offset[i];
            for (int e = b.Offset[i]; e < b.Offset[i + 1]; e++)
            {
                inDeg[b.Pop[b.Target[e]]]++;
                strongest[b.Pop[b.Target[e]]] = Math.Max(strongest[b.Pop[b.Target[e]]], Math.Abs(b.Weight[e]));
            }
        }
        sb.AppendLine("| 人群 | 神经元 | 平均入度 | 平均出度 | 最强单突触 (mV) |");
        sb.AppendLine("|---|---:|---:|---:|---:|");
        for (int p = 1; p < NPop; p++)
        {
            if (cells[p] == 0) continue;
            sb.AppendLine($"| `{PopNames[p]}` | {cells[p]} | {(double)inDeg[p] / cells[p]:F1} | "
                          + $"{(double)outDeg[p] / cells[p]:F1} | {strongest[p]:F3} |");
        }
        sb.AppendLine();
    }

    /// <summary>
    /// How this circuit is tied back to the public atlases.  MaleCNS is the male CNS; FlyWire
    /// (codex.flywire.ai / flywire.ai) is the female brain; the Janelia release even ships
    /// FlyWire meshes transformed into MaleCNS space, which is the official bridge between
    /// the two nomenclatures.
    /// </summary>
    private static void WriteLinks(StringBuilder sb)
    {
        sb.AppendLine("## 6. 与 FlyWire / flywire.ai 的对接");
        sb.AppendLine();
        sb.AppendLine("| 资源 | 用途 | 链接 |");
        sb.AppendLine("|---|---|---|");
        sb.AppendLine("| MaleCNS 下载页 | 本回路的数据来源 (v1.0 / v0.9 发布桶) | https://male-cns.janelia.org/download |");
        sb.AppendLine("| MaleCNS neuroglancer | 在 EM 里直接看这些神经元 | https://neuroglancer-demo.appspot.com/#!gs://flyem-male-cns/v0.9/male-cns-v0.9.json |");
        sb.AppendLine("| neuprint male-cns | 按细胞类型查询连接 (Cypher) | https://neuprint.janelia.org/?dataset=male-cns%3Av0.9 |");
        sb.AppendLine("| FlyWire Codex | 雌性脑的同类细胞类型 / 形态 / 连接 | https://codex.flywire.ai |");
        sb.AppendLine("| flywire.ai | FlyWire 项目主页与全脑数据入口 | https://flywire.ai |");
        sb.AppendLine("| flywire_annotations | FlyWire 细胞类型注释 (跨数据集命名的权威来源) | https://github.com/flyconnectome/flywire_annotations |");
        sb.AppendLine("| flywire2mcns_meshes | **官方桥**: FlyWire v783 网格已变换到 MaleCNS 坐标空间 | https://storage.googleapis.com/flyem-male-cns/flywire2mcns_meshes/ |");
        sb.AppendLine("| hemibrain2mcns_meshes | Hemibrain v1.2 网格 → MaleCNS 空间 | https://storage.googleapis.com/flyem-male-cns/hemibrain2mcns_meshes/v1.2 |");
        sb.AppendLine();
        sb.AppendLine("本简图里每个细胞类型都带一个 Codex 检索链接：MaleCNS 的 `type` 名与 FlyWire 的命名");
        sb.AppendLine("大多同源 (EPG / PEG / PFN / PFR / FB* / KC / MBON / PAM 等)，可以直接用同一个名字在");
        sb.AppendLine("FlyWire Codex 里找到对应细胞并对比形态与连接；MaleCNS 注释表里的 `hemibrainType` 列则是");
        sb.AppendLine("通往 Hemibrain 命名体系的桥。");
        sb.AppendLine();
    }

    private static string Short(string pop) => pop switch
    {
        "self_motion" => "LPTC",
        "central_complex" => "CX",
        "antennal_lobe" => "AL",
        "kenyon_cell" => "KC",
        "descending" => "DN",
        _ => pop,
    };

    private static string Codex(string type) =>
        "https://codex.flywire.ai/app/search?search=" + Uri.EscapeDataString(type);
}
