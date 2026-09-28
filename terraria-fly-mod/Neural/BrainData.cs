using System;
using System.IO;

namespace FlyMind.Neural
{
    /// <summary>
    /// Loads the compact circuit blob produced by tools/CircuitBuilder.
    ///
    /// Layout (little endian; the writer is tools/CircuitBuilder/Program.cs):
    ///
    ///   magic       8s    "FLYMIND3"   (v1/v2 files with three/four seed groups still load)
    ///   uint32      n_neurons
    ///   uint32      n_synapses
    ///   uint32      n_groups
    ///   uint32      pop_counts[12]        (10 = self-motion / lobula plate, 11 = central complex)
    ///   uint32      seed_count[5]         sugar, motor, odor, selfmotion, centralcomplex
    ///   per neuron  uint64 body id
    ///               float32 soma_x, soma_y, soma_z   (micrometre/1000)
    ///               uint8   population, uint8 pad[3]      -> 24 bytes per neuron
    ///   CSR         uint32 offsets[n_neurons+1]
    ///               uint32 targets[n_synapses]
    ///               float32 weights[n_synapses]       (signed, already scaled by w_syn)
    ///   plasticity  uint8  kc_mbon_mask[n_synapses] (1 = Kenyon cell -> MBON)
    ///               float32 base_weight[n_synapses]
    ///   seeds       uint32 sugar[n], motor[n], odor[n], selfmotion[n], centralcomplex[n]
    ///   metadata    uint32 json_len + utf8 json
    /// </summary>
    public sealed class BrainData
    {
        /// <summary>Population ids, matching the builder's PopName order.</summary>
        public const int PopulationCount = 12;

        public int NeuronCount;
        public int SynapseCount;
        public int GroupCount;
        public uint[] PopulationCounts;
        public ulong[] BodyIds;
        public float[] Soma;            // 3 per neuron
        public byte[] Population;
        public byte[] CxFamily;         // 0 none, 1 ring, 2 columnar, 3 fanbody, 4 other
        public int[] Offset;            // N+1
        public int[] Target;            // synapses
        public float[] Weight;          // synapses (signed; plasticity applied on top)
        public bool[] KcMbonMask;       // synapses
        public float[] BaseWeight;      // synapses
        public int[] SugarSeeds;
        public int[] MotorSeeds;
        public int[] OdorSeeds;

        /// <summary>
        /// Lobula plate tangential cells (H1/H2/VS/V1 and the JO-EV / LHAV / LHPV
        /// families): the fly's own movement detectors.  The eye view drives these while
        /// the fly watches the world - and its own body in it - sweep past.
        /// </summary>
        public int[] SelfMotionSeeds;

        /// <summary>
        /// Central-complex neurons (EPG/PEG/PFN/PFR/FB columnar/hDelta/Delta families).
        /// This is the readout region of the self-observation experiment: the ring
        /// attractor and head-direction system that computes the fly's own orientation,
        /// and therefore the structure most likely to be perturbed by a view in which the
        /// fly can see its own body.
        /// </summary>
        public int[] CentralComplexSeeds;

        /// <summary>
        /// The visual relay into the central complex: cells that receive from the
        /// self-motion pool and project onto the CX (connectome-derived, computed by
        /// tools/CircuitBuilder).  This is the route a body-occluded patch of the visual
        /// field actually has into the heading system.
        /// </summary>
        public int[] VisualRelay;

        public string MetadataJson;

        public static BrainData Load(string path)
        {
            using FileStream fs = File.OpenRead(path);
            using var br = new BinaryReader(fs);
            var magic = br.ReadBytes(8);
            string tag = System.Text.Encoding.ASCII.GetString(magic);
            if (tag != "FLYMIND1" && tag != "FLYMIND2" && tag != "FLYMIND3" && tag != "FLYMIND4")
                throw new InvalidDataException("not a FlyMind brain blob: " + tag);
            bool v3 = tag == "FLYMIND3" || tag == "FLYMIND4";
            bool v4 = tag == "FLYMIND4";

            var d = new BrainData();
            d.NeuronCount = (int)br.ReadUInt32();
            d.SynapseCount = (int)br.ReadUInt32();
            d.GroupCount = (int)br.ReadUInt32();

            d.PopulationCounts = new uint[PopulationCount];
            for (int i = 0; i < PopulationCount; i++)
                d.PopulationCounts[i] = br.ReadUInt32();

            int nSugar = (int)br.ReadUInt32();
            int nMotor = (int)br.ReadUInt32();
            int nOdor = (int)br.ReadUInt32();
            // the self-motion group only exists from v2 on, the central complex from v3
            int nSelf = tag == "FLYMIND1" ? 0 : (int)br.ReadUInt32();
            int nCx = v3 ? (int)br.ReadUInt32() : 0;
            int nRelay = v4 ? (int)br.ReadUInt32() : 0;

            int n = d.NeuronCount;
            d.BodyIds = new ulong[n];
            d.Soma = new float[n * 3];
            d.Population = new byte[n];
            d.CxFamily = new byte[n];
            var buf = new byte[24];
            for (int i = 0; i < n; i++)
            {
                ReadExactly(br, buf, 0, 24);
                d.BodyIds[i] = BitConverter.ToUInt64(buf, 0);
                d.Soma[i * 3 + 0] = BitConverter.ToSingle(buf, 8);
                d.Soma[i * 3 + 1] = BitConverter.ToSingle(buf, 12);
                d.Soma[i * 3 + 2] = BitConverter.ToSingle(buf, 16);
                d.Population[i] = buf[20];
                d.CxFamily[i] = buf[21];
            }

            d.Offset = new int[n + 1];
            ReadInts(br, d.Offset, n + 1);
            d.Target = new int[d.SynapseCount];
            ReadInts(br, d.Target, d.SynapseCount);
            d.Weight = new float[d.SynapseCount];
            ReadFloats(br, d.Weight, d.SynapseCount);

            var mask = br.ReadBytes(d.SynapseCount);
            d.KcMbonMask = new bool[d.SynapseCount];
            for (int i = 0; i < d.SynapseCount; i++)
                d.KcMbonMask[i] = mask[i] != 0;
            d.BaseWeight = new float[d.SynapseCount];
            ReadFloats(br, d.BaseWeight, d.SynapseCount);

            d.SugarSeeds = new int[nSugar];
            ReadInts(br, d.SugarSeeds, nSugar);
            d.MotorSeeds = new int[nMotor];
            ReadInts(br, d.MotorSeeds, nMotor);
            d.OdorSeeds = new int[nOdor];
            ReadInts(br, d.OdorSeeds, nOdor);
            d.SelfMotionSeeds = new int[nSelf];
            ReadInts(br, d.SelfMotionSeeds, nSelf);
            d.CentralComplexSeeds = new int[nCx];
            ReadInts(br, d.CentralComplexSeeds, nCx);
            d.VisualRelay = new int[nRelay];
            ReadInts(br, d.VisualRelay, nRelay);

            int jsonLen = (int)br.ReadUInt32();
            d.MetadataJson = System.Text.Encoding.UTF8.GetString(br.ReadBytes(jsonLen));
            return d;
        }

        private static void ReadExactly(BinaryReader br, byte[] buf, int off, int len)
        {
            int got = 0;
            while (got < len)
            {
                int r = br.Read(buf, off + got, len - got);
                if (r <= 0) throw new EndOfStreamException("truncated brain blob");
                got += r;
            }
        }

        private static void ReadInts(BinaryReader br, int[] dst, int count)
        {
            if (count <= 0) return;
            var tmp = new byte[count * 4];
            ReadExactly(br, tmp, 0, tmp.Length);
            Buffer.BlockCopy(tmp, 0, dst, 0, tmp.Length);
        }

        private static void ReadFloats(BinaryReader br, float[] dst, int count)
        {
            if (count <= 0) return;
            var tmp = new byte[count * 4];
            ReadExactly(br, tmp, 0, tmp.Length);
            Buffer.BlockCopy(tmp, 0, dst, 0, tmp.Length);
        }
    }
}
