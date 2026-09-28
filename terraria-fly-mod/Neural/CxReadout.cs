using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using FlyMind.Neural;

namespace FlyMind.Neural
{
    /// <summary>
    /// Central-complex readout: what the fly's heading system is doing right now.
    ///
    /// The CX is read out per subfamily, not as one number, because a shift that only moves
    /// the heading ring would be invisible in a whole-CX average:
    ///
    ///   ring     EPG/PEG            the heading bump (ellipsoid body ring)
    ///   columnar PFN/PFR/hDelta     the angular-velocity input and the bump update
    ///   fanbody  FB columnar        heading -> steering
    ///   other    LAL/IB/ER/TuBu     CX-adjacent pre-motor
    ///
    /// The bump is the activity-weighted population vector over the ring cells in the plane
    /// recovered from their somas (two leading principal axes of the point cloud - the
    /// connectome carries no receptive-field or ring-coordinate map).  Its length R says how
    /// concentrated the ring's activity is: a bump, or nothing in particular.
    /// </summary>
    public sealed class CxReadout
    {
        private readonly LifCircuit _circuit;
        private readonly int[] _cx;
        private readonly byte[] _familyOf;      // parallel to _cx
        private readonly int[][] _byFamily = new int[5][];
        private readonly int[] _ring;
        private readonly float[] _ringCos;
        private readonly float[] _ringSin;

        public readonly float[] FamilyRate = new float[5];
        public readonly float[] FamilyActive = new float[5];

        public float CxRate;
        public float CxActiveFraction;
        public float BumpR;          // 0..1 population-vector length over the ring
        public float BumpAngle;      // radians, in the soma-derived ring plane

        public int RingCells => _ring.Length;
        public int CxCells => _cx.Length;

        public CxReadout(BrainData data, LifCircuit circuit)
        {
            _circuit = circuit;
            _cx = data.CentralComplexSeeds ?? Array.Empty<int>();
            _familyOf = new byte[_cx.Length];
            for (int f = 0; f < 5; f++) _byFamily[f] = Array.Empty<int>();
            var lists = new List<int>[5];
            for (int f = 0; f < 5; f++) lists[f] = new List<int>();
            for (int k = 0; k < _cx.Length; k++)
            {
                byte fam = data.CxFamily != null && _cx[k] < data.CxFamily.Length
                    ? data.CxFamily[_cx[k]] : (byte)0;
                _familyOf[k] = fam;
                lists[fam < 5 ? fam : 0].Add(_cx[k]);
            }
            for (int f = 0; f < 5; f++) _byFamily[f] = lists[f].ToArray();

            _ring = _byFamily[1];
            _ringCos = new float[_ring.Length];
            _ringSin = new float[_ring.Length];
            BuildRingPlane(data);
        }

        /// <summary>
        /// Recover the plane of the ring from the EPG/PEG somas (centroid + two leading
        /// principal axes) and store each cell's angle as a unit vector.  If these cells do
        /// sit around the ellipsoid body, this is the ring's own coordinate system; if they
        /// do not, the bump amplitude stays low and the readout says so instead of inventing
        /// a heading.
        /// </summary>
        private void BuildRingPlane(BrainData data)
        {
            if (_ring.Length < 4) return;
            var c = Vector3.Zero;
            foreach (int i in _ring)
                c += new Vector3(_circuit.SomaX(i), _circuit.SomaY(i), _circuit.SomaZ(i));
            c /= _ring.Length;
            var cov = new float[3, 3];
            foreach (int i in _ring)
            {
                var p = new Vector3(_circuit.SomaX(i), _circuit.SomaY(i), _circuit.SomaZ(i)) - c;
                float[] a = { p.X, p.Y, p.Z };
                for (int u = 0; u < 3; u++) for (int v = 0; v < 3; v++) cov[u, v] += a[u] * a[v];
            }
            float[] v1 = PowerVector(cov, null), v2 = PowerVector(cov, v1);
            for (int k = 0; k < _ring.Length; k++)
            {
                int i = _ring[k];
                var p = new Vector3(_circuit.SomaX(i), _circuit.SomaY(i), _circuit.SomaZ(i)) - c;
                float a = p.X * v1[0] + p.Y * v1[1] + p.Z * v1[2];
                float b = p.X * v2[0] + p.Y * v2[1] + p.Z * v2[2];
                float norm = MathF.Sqrt(a * a + b * b) + 1e-6f;
                _ringCos[k] = a / norm;
                _ringSin[k] = b / norm;
            }
        }

        private static float[] PowerVector(float[,] a, float[] deflate)
        {
            var v = new float[3];
            for (int i = 0; i < 3; i++) v[i] = 1f / MathF.Sqrt(3f);
            for (int it = 0; it < 120; it++)
            {
                var w = new float[3];
                for (int i = 0; i < 3; i++)
                {
                    float s = 0;
                    for (int j = 0; j < 3; j++) s += a[i, j] * v[j];
                    if (deflate != null)
                    {
                        float proj = 0;
                        for (int j = 0; j < 3; j++) proj += deflate[j] * v[j];
                        s -= proj * deflate[i];
                    }
                    w[i] = s;
                }
                float norm = MathF.Sqrt(w[0] * w[0] + w[1] * w[1] + w[2] * w[2]);
                if (norm < 1e-9f) break;
                for (int i = 0; i < 3; i++) v[i] = w[i] / norm;
            }
            return v;
        }

        /// <summary>Refresh every CX statistic from the circuit's current firing rates.</summary>
        public void Update()
        {
            float sum = 0;
            int active = 0;
            for (int f = 0; f < 5; f++)
            {
                var idx = _byFamily[f];
                if (idx.Length == 0) { FamilyRate[f] = 0f; FamilyActive[f] = 0f; continue; }
                float s = 0; int act = 0;
                for (int k = 0; k < idx.Length; k++)
                {
                    float r = _circuit.Rate(idx[k]);
                    s += r;
                    if (r > 0.05f) act++;          // rates are spikes per 100 ms: 0.05 = 0.5 Hz
                }
                FamilyRate[f] = s / idx.Length * 10f;      // Hz
                FamilyActive[f] = act / (float)idx.Length;
                if (f != 0) { sum += s; active += act; }
            }
            int named = 0;
            for (int f = 1; f < 5; f++) named += _byFamily[f].Length;
            CxRate = named == 0 ? 0f : sum / named * 10f;
            CxActiveFraction = named == 0 ? 0f : active / (float)named;

            if (_ring.Length < 4) { BumpR = 0f; return; }
            float sx = 0, sy = 0, sw = 0;
            for (int k = 0; k < _ring.Length; k++)
            {
                float w = _circuit.Rate(_ring[k]);
                sw += w;
                sx += w * _ringCos[k];
                sy += w * _ringSin[k];
            }
            if (sw <= 1e-5f) { BumpR = 0f; return; }
            float vx = sx / sw, vy = sy / sw;
            BumpR = MathF.Sqrt(vx * vx + vy * vy);
            BumpAngle = MathF.Atan2(vy, vx);
        }
    }
}
