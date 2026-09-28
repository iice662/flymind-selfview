using System;
using System.IO;
using System.Linq;

internal static class Probe
{
    private static void Main2(string[] args)
    {
        string path = args.Length > 0 ? args[0] : @"D:\projects\science\flymind.brain";
        using var br = new BinaryReader(File.OpenRead(path));
        string tag = System.Text.Encoding.ASCII.GetString(br.ReadBytes(8));
        int n = (int)br.ReadUInt32(), syn = (int)br.ReadUInt32(), ng = (int)br.ReadUInt32();
        Console.WriteLine($"tag={tag} n={n} syn={syn} ng={ng}");
        var pops = new uint[11];
        for (int i = 0; i < 11; i++) pops[i] = br.ReadUInt32();
        Console.WriteLine("pops: " + string.Join(",", pops));
        int ns = (int)br.ReadUInt32(), nm = (int)br.ReadUInt32(), no = (int)br.ReadUInt32(), nse = (int)br.ReadUInt32();
        Console.WriteLine($"seeds sugar={ns} motor={nm} odor={no} self={nse}");
        Console.WriteLine($"position after header: {br.BaseStream.Position} (expected 80)");

        var buf = new byte[24];
        br.Read(buf, 0, 24);
        ulong id = BitConverter.ToUInt64(buf, 0);
        Console.WriteLine($"neuron0 id={id} x={BitConverter.ToSingle(buf,8):F2} pop={buf[20]}");
        Console.WriteLine($"position after 1 neuron: {br.BaseStream.Position} (expected 104)");

        br.BaseStream.Position = 80 + (long)n * 24;
        var offs = new int[n + 1];
        var ob = br.ReadBytes((n + 1) * 4);
        Buffer.BlockCopy(ob, 0, offs, 0, ob.Length);
        Console.WriteLine($"offsets[0..4]={string.Join(",", offs.Take(5))} last={offs[n]} == syn? {offs[n] == syn}");
        br.BaseStream.Position = 80 + (long)n * 24 + (long)(n + 1) * 4 + (long)syn * 4;
        var wb = br.ReadBytes(16);
        Console.WriteLine($"first 4 weights = {BitConverter.ToSingle(wb,0):E3}, {BitConverter.ToSingle(wb,4):E3}, {BitConverter.ToSingle(wb,8):E3}, {BitConverter.ToSingle(wb,12):E3}");
    }
}
