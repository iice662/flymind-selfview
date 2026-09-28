using System;
using System.Collections.Generic;
using FlyMind.Neural;
using FlyMind.World;
using Microsoft.Xna.Framework;

namespace FlyMind.Neural
{
    /// <summary>
    /// One fly's brain: a private <see cref="LifCircuit"/> instance plus the
    /// sensory encoding and motor readout that connects it to the 2D world.
    ///
    /// Signal flow (all neuron ids and synapses come from the real FlyWire
    /// connectome, see tools/build_circuit.py):
    ///
    ///   food odour / contact  -> SugarSeeds / OdorSeeds   (Poisson spikes, 0-150 Hz)
    ///   danger (player, hurt) -> BitterSeeds              (Poisson spikes)
    ///   network               -> Kenyon cells, PAM/PPL dopamine, MBON, DN, motor neurons
    ///   readout               -> proboscis extension, forward speed, turn rate
    ///
    /// When no brain blob is available the class reports neutral drive so the NPC
    /// can fall back to scripted behaviour.
    /// </summary>
    public sealed class FlyBrain
    {
        public readonly LifCircuit Circuit;

        /// <summary>The blob this brain was built from (needed to build the body patch).</summary>
        public readonly BrainData CircuitData;

        // seed neuron groups (real MaleCNS neurons selected by cell type)
        public readonly int[] CircuitSugarSeeds;
        public readonly int[] CircuitOdorSeeds;
        public readonly int[] CircuitMotorSeeds;
        public readonly int[] CircuitSelfMotionSeeds;
        /// <summary>Connectome-derived visual relay into the central complex.</summary>
        public readonly int[] CircuitVisualRelay;

        /// <summary>Central-complex readout: subfamily rates and the heading-bump vector.</summary>
        public CxReadout Cx { get; }

        /// <summary>
        /// The body patch (see World/SelfViewPatch) and whether the fly's own body is part of
        /// its visual field this block.  Both are set by the self-observation experiment
        /// (World/CxExperiment); with the experiment off the fly is simply in the third
        /// person, i.e. it always sees itself.
        /// </summary>
        public bool BodyInVisualField = true;
        public VisualPatch Patch { get; private set; }
        /// <summary>When true the patch drive is applied even though the body is not drawn
        /// (the placebo arm: identical world, identical circuit input to the self arm).</summary>
        public bool ForcePatchDrive;

        public void SetPatch(VisualPatch patch) => Patch = patch;

        // sensory stimulus strengths, 0..1, set by the NPC each tick
        public float FoodSmell;
        public float FoodTaste;
        public float Danger;

        /// <summary>
        /// How much of the eye view is the fly's own body, 0..1, and how fast the rest of
        /// the view is sweeping past.  These two together are what the lobula plate
        /// tangential cells report: "the image is moving, and part of that image is me".
        /// </summary>
        public float SelfInView;
        public float ViewMotion;

        // population ids (mirror tools/CircuitBuilder PopName order)
        public const byte PopSensory = 1;
        public const byte PopAntennalLobe = 2;
        public const byte PopKenyon = 3;
        public const byte PopDopamine = 4;
        public const byte PopMbon = 5;
        public const byte PopDescending = 6;
        public const byte PopMotor = 7;
        public const byte PopInterneuron = 8;
        public const byte PopVnc = 9;
        public const byte PopSelfMotion = 10;

        /// <summary>
        /// Gain on every connectome weight (kappa).  The published threshold is 7 mV and the
        /// published weight is 0.275 mV per synapse, so a neuron needs ~26 synapses to fire
        /// together - a real fly's operating point, but a 12,000-neuron slice of a 166k
        /// connectome only contains the synapses *inside the slice* (mean in-degree ~135
        /// against ~900 in the whole brain), so at the native weight nothing ever reaches
        /// threshold and the circuit sits silent.  kappa is the single calibrated parameter
        /// that compensates for the missing fan-in; it is applied to connectome weights only,
        /// never to the stimulation protocol.  kappa = 300 puts the central complex at about
        /// 1 Hz with ~8% of its cells active under natural optic flow (tools/CircuitPreview
        /// --sweep); every experiment arm shares it.  See METHODS.md.
        /// </summary>
        public const float ConnectomeGain = 300f;

        /// <summary>Dopamine pool activity, leaky (0..1) - "how excited the fly is".</summary>
        public float DopamineLevel { get; private set; }

        /// <summary>
        /// Self-motion cell activity, leaky (0..1): how strongly the fly is registering
        /// itself moving through the world (and its own body moving in its view).
        /// </summary>
        public float SelfMotionLevel { get; private set; }

        /// <summary>
        /// Mean leaky firing rate per population, refreshed every Step.  Units are the
        /// circuit's native "spikes per 100 ms"; multiply by 10 for Hz.  The narrative HUD
        /// reads this so it reports measured activity rather than re-deriving it.
        /// </summary>
        public float[] PopulationRates => _popRates;

        /// <summary>
        /// Background spontaneous firing applied to every neuron, as a Poisson rate in Hz.
        ///
        /// The published model is driven only where the experiment stimulates, so with no
        /// input the circuit sits perfectly silent - which is not what a fly brain does and
        /// makes the point of the mod (watching it react) impossible to see.  Real brains
        /// carry resting tone; a few Hz of spontaneous firing reproduces that and lets weak
        /// inputs summate into real spikes, which the offline preview confirmed is needed
        /// for anything downstream of the seeds to fire at all.
        /// </summary>
        public float SpontaneousRateHz = 6f;

        /// <summary>Learned attraction gain on KC->MBON synapses (1 = naive).</summary>
        public float Attraction { get; private set; } = 1f;

        /// <summary>Forward drive from the descending neuron pool, leaky (0..1).</summary>
        public float ForwardDrive { get; private set; }

        /// <summary>Turn bias: positive = turn clockwise (to the fly's right).</summary>
        public float TurnBias { get; private set; }

        /// <summary>Proboscis extension drive, leaky (0..1).</summary>
        public float Feeding { get; private set; }

        private readonly Random _rng;
        private readonly float[] _popRates = new float[BrainData.PopulationCount];
        private int _steps;

        public FlyBrain(BrainData data, int seed)
        {
            CircuitData = data;
            Circuit = new LifCircuit(data, 0.5f, ConnectomeGain);
            CircuitSugarSeeds = data.SugarSeeds;
            CircuitOdorSeeds = data.OdorSeeds;
            CircuitMotorSeeds = data.MotorSeeds;
            CircuitSelfMotionSeeds = data.SelfMotionSeeds;
            CircuitVisualRelay = data.VisualRelay ?? Array.Empty<int>();
            Cx = new CxReadout(data, Circuit);
            _rng = new Random(seed);
            // The mod's normal view is third person, so by default the fly's own body IS in
            // its visual field and the drive it receives is the patched one.  The experiment
            // swaps this for the shuffled or the natural drive per block.
            Patch = VisualPatch.Build(data, false);
            AssignReadoutNeurons(data);
        }

        // readout groups, resolved once at construction
        private int[] _dopamineNeurons = Array.Empty<int>();
        private int[] _kenyonNeurons = Array.Empty<int>();
        private int[] _mbonNeurons = Array.Empty<int>();
        private int[] _motorNeurons = Array.Empty<int>();
        private int[] _descendingLeft = Array.Empty<int>();
        private int[] _descendingRight = Array.Empty<int>();

        private void AssignReadoutNeurons(BrainData data)
        {
            var dan = new List<int>();
            var kc = new List<int>();
            var mbon = new List<int>();
            var motor = new List<int>();
            var dnLeft = new List<int>();
            var dnRight = new List<int>();

            for (int i = 0; i < data.NeuronCount; i++)
            {
                switch (data.Population[i])
                {
                    case PopDopamine: dan.Add(i); break;
                    case PopKenyon: kc.Add(i); break;
                    case PopMbon: mbon.Add(i); break;
                    case PopMotor: motor.Add(i); break;
                    case PopDescending:
                        // soma_x < 0 is one hemisphere: splitting the descending pool
                        // gives a left/right asymmetry the fly can steer with
                        if (data.Soma[i * 3] < 0f) dnLeft.Add(i);
                        else dnRight.Add(i);
                        break;
                }
            }
            _dopamineNeurons = dan.ToArray();
            _kenyonNeurons = kc.ToArray();
            _mbonNeurons = mbon.ToArray();
            _motorNeurons = motor.ToArray();
            _descendingLeft = dnLeft.ToArray();
            _descendingRight = dnRight.ToArray();
        }

        public bool HasReadout =>
            _dopamineNeurons.Length + _kenyonNeurons.Length + _mbonNeurons.Length +
            _descendingLeft.Length + _descendingRight.Length + _motorNeurons.Length > 0;

        /// <summary>Advance the brain by one step and refresh the readouts.</summary>
        public void Step(float gameTimeScale = 1f)
        {
            // ---- sensory encoding: Poisson spike trains on the real seed neurons.
            // The paper drives stimulated neurons with a 150 Hz Poisson train.
            float pPerStep = 150f * Circuit.Dt / 1000f;
            InjectPoisson(CircuitSugarSeeds, pPerStep * FoodTaste);
            InjectPoisson(CircuitOdorSeeds, pPerStep * FoodSmell);
            InjectPoisson(CircuitMotorSeeds, pPerStep * Danger);

            // ---- self-view: the fly's own eyes.  The lobula plate tangential cells and the
            // visual relay into the central complex fire with retinal image motion, so they
            // are driven by how fast the view sweeps past - and, when the fly's own body is
            // in its visual field, the part of that pool the body covers stops reporting
            // slip (the body is rigidly attached to the head, so nothing slides across it).
            // The rest of the pool is scaled up so the TOTAL drive is unchanged: the arms of
            // the experiment differ in the structure of the input, never in its amount.
            float viewDrive = MathHelper.Clamp(0.75f * ViewMotion + 0.5f * SelfInView, 0f, 1f);
            bool patchDrive = ForcePatchDrive || (BodyInVisualField && Patch != null);
            InjectVisualDrive(viewDrive, patchDrive);

            // ---- resting tone: the published model is silent without stimulation and a
            // Poisson background at the native weight cannot reach threshold (~5 kHz would be
            // needed), so the tone is deliberately off: the circuit's activity comes from the
            // connectome, not from a synthetic driver.
            if (SpontaneousRateHz > 0.01f)
                InjectSpontaneous(SpontaneousRateHz * Circuit.Dt / 1000f);

            // ---- network
            Circuit.Step();
            _steps++;
            Cx.Update();

            // ---- readouts (leaky integrators, ~100 ms). One pass over the circuit
            // instead of four, so the cost stays flat as the neuron count grows.
            float k = Math.Min(1f, Circuit.Dt / 60f) * gameTimeScale;
            Circuit.PopulationRates(_popRates);
            float danRate = _popRates[PopDopamine];
            float motorRate = _popRates[PopMotor];

            // left/right descending asymmetry is what steers; the pools are split by
            // soma side in AssignReadoutNeurons
            float leftRate = Circuit.MeanRate(_descendingLeft);
            float rightRate = Circuit.MeanRate(_descendingRight);
            float dnRate = 0.5f * (leftRate + rightRate);

            // rates are "spikes per 100 ms"; 1 spike/100ms = 10 Hz -> scale to 0..1
            DopamineLevel += k * (Squash(danRate * 0.25f) - DopamineLevel);
            ForwardDrive += k * (Squash(dnRate * 0.25f) - ForwardDrive);
            Feeding += k * (Squash(motorRate * 0.5f) - Feeding);
            SelfMotionLevel += k * (Squash(_popRates[PopSelfMotion] * 0.25f) - SelfMotionLevel);

            float asym = rightRate - leftRate;
            TurnBias += k * (MathHelper.Clamp(asym * 0.15f, -1f, 1f) - TurnBias);

            // ---- dopamine-dependent attraction (the only non-paper layer)
            // Repeated sugar reward strengthens KC->MBON transmission, which makes
            // the fly seek the odour it learned to associate with food.
            float target = 1f + 2f * MathHelper.Clamp(DopamineLevel * (0.2f + FoodTaste), 0f, 1f);
            Attraction += 0.002f * (target - Attraction);
            Circuit.PlasticityGain = Attraction;
        }

        private void InjectPoisson(int[] neurons, float probability)
        {
            if (neurons.Length == 0 || probability <= 0f) return;
            if (probability > 1f) probability = 1f;
            float weight = LifCircuit.WSyn * 250f;   // model.py: f_poi = 250
            for (int i = 0; i < neurons.Length; i++)
            {
                // one Bernoulli draw per neuron per step ~ Poisson at this rate
                if (_rng.NextDouble() < probability)
                    Circuit.InjectSpike(neurons[i], weight);
            }
        }

        /// <summary>
        /// Visual drive to the whole input pool (rotation-sensitive cells + the visual relay
        /// into the CX).  Without the body patch every cell gets the same rate.  With it, the
        /// cells the body covers get the residual slip of a head-locked object and the rest is
        /// scaled so the expected total number of injected events is unchanged.
        /// </summary>
        private void InjectVisualDrive(float viewDrive, bool patchDrive)
        {
            int nPool = CircuitSelfMotionSeeds.Length + CircuitVisualRelay.Length;
            if (nPool == 0 || viewDrive <= 0.02f) return;
            float pBase = 150f * Circuit.Dt / 1000f * 0.6f * viewDrive;
            float weight = LifCircuit.WSyn * 250f;
            if (!patchDrive || Patch == null)
            {
                InjectVisualGroup(CircuitSelfMotionSeeds, null, pBase, weight);
                InjectVisualGroup(CircuitVisualRelay, null, pBase, weight);
                return;
            }
            // magnitude matching: the surround carries exactly the drive the body region
            // does not absorb, so no arm delivers more input than another
            int nPatch = Patch.PatchSize;
            int nSurround = Math.Max(1, nPool - nPatch);
            float surroundScale = (nPool - BodySlip * nPatch) / nSurround;
            InjectVisualGroup(CircuitSelfMotionSeeds, Patch.SelfMotion, pBase, weight, surroundScale);
            InjectVisualGroup(CircuitVisualRelay, Patch.Relay, pBase, weight, surroundScale);
        }

        /// <summary>Residual retinal slip of a head-locked object (the fly's own body).</summary>
        private const float BodySlip = 0.1f;

        private void InjectVisualGroup(int[] neurons, bool[] patch, float pBase, float weight,
                                       float surroundScale = 1f)
        {
            for (int i = 0; i < neurons.Length; i++)
            {
                bool inPatch = patch != null && i < patch.Length && patch[i];
                float p = pBase * (patch == null ? 1f : inPatch ? BodySlip : surroundScale);
                if (p <= 0f) continue;
                if (p > 1f) p = 1f;
                if (_rng.NextDouble() < p) Circuit.InjectSpike(neurons[i], weight);
            }
        }

        /// <summary>
        /// Resting tone: every neuron gets an independent Poisson train.  The weight is one
        /// synapse (w_syn), not the 250x used for explicit stimulation - the point is to
        /// lift the membrane toward threshold so coincident synaptic input can push it over,
        /// not to make the circuit fire on its own.
        /// </summary>
        private void InjectSpontaneous(float probabilityPerStep)
        {
            if (probabilityPerStep <= 0f) return;
            int n = Circuit.NeuronCount;
            for (int i = 0; i < n; i++)
                if (_rng.NextDouble() < probabilityPerStep)
                    Circuit.InjectSpike(i, LifCircuit.WSyn);
        }

        private static float Squash(float x)
        {
            if (x <= 0f) return 0f;
            return x / (1f + x);
        }

        public int Steps => _steps;
    }
}
