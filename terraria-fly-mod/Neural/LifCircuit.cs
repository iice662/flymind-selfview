using System;

namespace FlyMind.Neural
{
    /// <summary>
    /// Leaky integrate-and-fire network with alpha synapses and conductance-based
    /// coupling. This is a direct port of the model in Shiu et al. 2024
    /// (github.com/philshiu/Drosophila_brain_model, model.py), which itself is
    /// built from published Drosophila membrane constants:
    ///
    ///     dv/dt = (v_0 - v + g) / t_mbr          v_0 = -52 mV, v_th = -45 mV
    ///     dg/dt = -g / tau                       tau = 5 ms
    ///     spike: v = v_rst, g = 0, refractory t_rfc = 2.2 ms
    ///     on_pre: g += w, delayed by t_dly = 1.8 ms
    ///
    /// The only free parameter of the published model is the per-synapse weight
    /// w_syn = 0.275 mV; the synaptic weights loaded from the brain blob are
    /// already scaled by it.
    ///
    /// This class deliberately has no Terraria dependency so it can be unit
    /// tested and benchmarked outside the game.
    /// </summary>
    public sealed class LifCircuit
    {
        // membrane constants, in mV / ms (verbatim from the paper's model.py)
        public const float V0 = -52f;      // resting potential
        public const float VRst = -52f;    // reset potential
        public const float VTh = -45f;     // spike threshold
        public const float Tmbr = 20f;     // membrane time constant
        public const float Tau = 5f;       // synaptic decay
        public const float TRfc = 2.2f;    // refractory period
        public const float TDly = 1.8f;    // synaptic delay
        public const float WSyn = 0.275f;  // weight per synapse

        public const float VMin = -70f;    // numerical guard rail

        public readonly int NeuronCount;
        public readonly int SynapseCount;

        private readonly int[] _offset;      // CSR row starts, length N+1
        private readonly int[] _target;      // CSR column indices
        private readonly float[] _weight;    // CSR weights (already * w_syn)
        private readonly byte[] _pop;        // population id per neuron
        private readonly float[] _soma;      // 3 floats per neuron (waypoint coords)
        private readonly bool[] _kcMbonMask; // synapses that carry dopamine modulation
        private readonly float[] _baseWeight; // anatomical weights, before modulation

        // state
        private readonly float[] _v;
        private readonly float[] _g;
        private readonly float[] _rfc;
        private readonly float[] _spikeRate; // leaky spike counter, spikes per 100 ms
        private readonly float[] _spikeOut;  // spikes emitted this step (0/1)

        // delayed synaptic delivery ring buffer
        private readonly float[][] _pendingG;
        private readonly int[][] _pendingTarget;
        private readonly int[] _pendingCount;
        private readonly int _delaySteps;
        private readonly float _dt;
        private readonly float _decayG;
        private int _slot;

        private int _spikeTotal;

        public float Dt => _dt;
        public float SimulatedMs { get; private set; }
        public int SpikeTotal => _spikeTotal;
        public int LastSpikeCount { get; private set; }

        public LifCircuit(BrainData data, float dt = 0.5f, float gain = 1f)
        {
            NeuronCount = data.NeuronCount;
            SynapseCount = data.SynapseCount;
            _offset = data.Offset;
            _target = data.Target;
            // The gain is applied once, here, to a private copy of the weights: it scales the
            // connectome only, so the stimulation protocol (w_syn * f_poi) keeps the value the
            // published model gives it.  See FlyBrain.ConnectomeGain.
            _weight = new float[data.Weight.Length];
            for (int e = 0; e < _weight.Length; e++) _weight[e] = data.Weight[e] * gain;
            _baseWeight = new float[data.BaseWeight.Length];
            for (int e = 0; e < _baseWeight.Length; e++) _baseWeight[e] = data.BaseWeight[e] * gain;
            _pop = data.Population;
            _soma = data.Soma;
            _kcMbonMask = data.KcMbonMask;

            _dt = dt;
            _decayG = (float)Math.Exp(-dt / Tau);
            _delaySteps = Math.Max(1, (int)Math.Round(TDly / dt));

            _v = new float[NeuronCount];
            _g = new float[NeuronCount];
            _rfc = new float[NeuronCount];
            _spikeRate = new float[NeuronCount];
            _spikeOut = new float[NeuronCount];

            _pendingG = new float[_delaySteps][];
            _pendingTarget = new int[_delaySteps][];
            _pendingCount = new int[_delaySteps];
            for (int i = 0; i < _delaySteps; i++)
            {
                // size for the whole synapse population spread over the delay slots:
                // undersizing these makes Step() call Array.Resize mid-frame, which is
                // exactly the kind of allocation spike a 16 ms budget cannot afford
                int cap = Math.Max(64, SynapseCount / _delaySteps + (SynapseCount / 8));
                _pendingG[i] = new float[cap];
                _pendingTarget[i] = new int[cap];
            }

            Reset();
        }

        public void Reset()
        {
            for (int i = 0; i < NeuronCount; i++)
            {
                _v[i] = V0;
                _g[i] = 0f;
                _rfc[i] = 0f;
                _spikeRate[i] = 0f;
                _spikeOut[i] = 0f;
            }
            for (int i = 0; i < _delaySteps; i++)
                _pendingCount[i] = 0;
            _slot = 0;
            _spikeTotal = 0;
            SimulatedMs = 0f;
        }

        /// <summary>Inject a synaptic conductance directly into one neuron (sensory input).</summary>
        public void InjectConductance(int neuron, float g)
        {
            if ((uint)neuron >= (uint)NeuronCount) return;
            _g[neuron] += g;
        }

        /// <summary>
        /// Feed an external spike into a neuron. Poisson sensory drive from the
        /// paper uses weight = w_syn * 250, i.e. "one sensory spike = 250 synapses'.
        /// </summary>
        public void InjectSpike(int neuron, float weightInMv)
        {
            if ((uint)neuron >= (uint)NeuronCount) return;
            _g[neuron] += weightInMv;
        }

        /// <summary>Advance the network by one step of <see cref="Dt"/> ms.</summary>
        public void Step()
        {
            // 1. deliver delayed synaptic events for this slot.
            //
            // The delay is modelled explicitly by the ring buffer, so an arriving event is
            // added at full weight and then decays through the PSP time constant below -
            // it must NOT be pre-decayed here.  (This used to multiply by _decayG, which
            // double-counted the decay the integration step already applies.)
            int slot = _slot;
            int cnt = _pendingCount[slot];
            if (cnt > 0)
            {
                float[] gs = _pendingG[slot];
                int[] tg = _pendingTarget[slot];
                for (int k = 0; k < cnt; k++)
                    _g[tg[k]] += gs[k];
                _pendingCount[slot] = 0;
            }

            // 2. integrate.  The synaptic conductance DECAYS with tau (the model's
            //    dg/dt = -g/tau) instead of being consumed in one step.  Zeroing it made
            //    every synapse a single 0.5 ms impulse: no summation over the 5 ms PSP
            //    window, so a sensory spike could never combine with anything, the
            //    cascade died after one synapse and the whole circuit needed a 1000x
            //    gain to move at all.
            int n = NeuronCount;
            int fired = 0;
            float dt = _dt;
            for (int i = 0; i < n; i++)
            {
                float rfc = _rfc[i];
                if (rfc > 0f)
                {
                    _rfc[i] = rfc - dt;
                    _spikeOut[i] = 0f;
                    continue;
                }
                float g = _g[i];
                float v = _v[i] + dt * (V0 - _v[i] + g) / Tmbr;
                if (v > VTh)
                {
                    v = VRst;
                    _rfc[i] = TRfc;
                    _spikeOut[i] = 1f;
                    _spikeRate[i] += 1f;
                    _g[i] = 0f;      // reset rule: 'v = v_rst; w = 0; g = 0 * mV'
                    fired++;
                }
                else
                {
                    if (v < VMin) v = VMin;
                    _spikeOut[i] = 0f;
                    _g[i] = g * _decayG;
                }
                _v[i] = v;
            }

            // 3. queue outgoing events into the slot that is delaySteps ahead
            int outSlot = (slot + _delaySteps) % _delaySteps;
            if (fired > 0)
            {
                float[] gs = _pendingG[outSlot];
                int[] tg = _pendingTarget[outSlot];
                int m = _pendingCount[outSlot];
                int cap = gs.Length;
                for (int i = 0; i < n; i++)
                {
                    if (_spikeOut[i] == 0f) continue;
                    int end = _offset[i + 1];
                    for (int e = _offset[i]; e < end; e++)
                    {
                        if (m == cap)
                        {
                            Array.Resize(ref gs, cap * 2);
                            Array.Resize(ref tg, cap * 2);
                            cap *= 2;
                        }
                        tg[m] = _target[e];
                        gs[m] = _weight[e];
                        m++;
                    }
                }
                _pendingG[outSlot] = gs;
                _pendingTarget[outSlot] = tg;
                _pendingCount[outSlot] = m;
            }

            _slot = (slot + 1) % _delaySteps;
            _spikeTotal += fired;
            LastSpikeCount = fired;
            SimulatedMs += dt;

            // leaky spike-rate readout, time constant 100 ms
            float rk = dt / 100f;
            for (int i = 0; i < n; i++)
                _spikeRate[i] -= rk * _spikeRate[i];
        }

        /// <summary>Leaky spike rate estimate in "spikes per 100 ms" (0..~20).</summary>
        public float Rate(int neuron)
        {
            return (uint)neuron < (uint)NeuronCount ? _spikeRate[neuron] : 0f;
        }

        public bool Spiked(int neuron)
        {
            return (uint)neuron < (uint)NeuronCount && _spikeOut[neuron] != 0f;
        }

        public float Potential(int neuron)
        {
            return (uint)neuron < (uint)NeuronCount ? _v[neuron] : V0;
        }

        public byte Population(int neuron)
        {
            return (uint)neuron < (uint)NeuronCount ? _pop[neuron] : (byte)0;
        }

        public float SomaX(int neuron) { return _soma[neuron * 3]; }
        public float SomaY(int neuron) { return _soma[neuron * 3 + 1]; }
        public float SomaZ(int neuron) { return _soma[neuron * 3 + 2]; }

        /// <summary>Mean leaky rate over a list of neurons - the "readout" used to drive behaviour.</summary>
        public float MeanRate(int[] neurons)
        {
            if (neurons == null || neurons.Length == 0) return 0f;
            float sum = 0f;
            for (int i = 0; i < neurons.Length; i++)
                sum += _spikeRate[neurons[i]];
            return sum / neurons.Length;
        }

        /// <summary>Sum of leaky rates over a population id.</summary>
        public float PopulationRate(byte pop)
        {
            float sum = 0f;
            for (int i = 0; i < NeuronCount; i++)
                if (_pop[i] == pop) sum += _spikeRate[i];
            return sum;
        }

        /// <summary>Normalised population activity (mean rate / neuron) for HUD meters.</summary>
        public float PopulationMeter(byte pop)
        {
            int c = 0;
            float sum = 0f;
            for (int i = 0; i < NeuronCount; i++)
                if (_pop[i] == pop) { sum += _spikeRate[i]; c++; }
            return c == 0 ? 0f : sum / c;
        }

        /// <summary>
        /// Mean leaky rate of every population in one pass.  The behavioural readout
        /// needs several populations at once (dopamine, motor, descending, MBON), and
        /// walking the neuron array once instead of once per population keeps the
        /// per-tick readout cost flat while the circuit grows to thousands of neurons.
        /// </summary>
        public void PopulationRates(float[] destination)
        {
            if (destination == null || destination.Length == 0) return;
            Array.Clear(destination, 0, destination.Length);
            _popCounts ??= CountPopulations();
            for (int i = 0; i < NeuronCount; i++)
            {
                byte p = _pop[i];
                if (p < destination.Length) destination[p] += _spikeRate[i];
            }
            for (int p = 0; p < destination.Length; p++)
                if (_popCounts[p] > 0) destination[p] /= _popCounts[p];
        }

        private int[] _popCounts;

        private int[] CountPopulations()
        {
            var counts = new int[BrainData.PopulationCount];
            for (int i = 0; i < NeuronCount; i++) counts[_pop[i]]++;
            return counts;
        }

        /// <summary>
        /// Dopamine-modulated gain on Kenyon-cell -> mushroom-body-output synapses.
        /// The published model has no plasticity; this is a deliberately simple,
        /// biologically motivated modulation layer kept in one place so it can be
        /// disabled (gain = 1) for faithful replay of the paper's model.
        /// </summary>
        public float PlasticityGain
        {
            get => _plasticityGain;
            set
            {
                if (Math.Abs(value - _plasticityGain) < 1e-4f) return;
                _plasticityGain = value;
                for (int i = 0; i < SynapseCount; i++)
                    if (_kcMbonMask[i])
                        _weight[i] = _baseWeight[i] * value;
            }
        }
        private float _plasticityGain = 1f;

        /// <summary>Histogram of neurons per population id.</summary>
        public int[] PopulationHistogram()
        {
            var h = new int[BrainData.PopulationCount];
            for (int i = 0; i < NeuronCount; i++)
                h[_pop[i]]++;
            return h;
        }
    }
}
