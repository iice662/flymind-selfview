using System;
using FlyMind.Neural;
using FlyMind.World;
using Microsoft.Xna.Framework;
using Terraria;

namespace FlyMind
{
    /// <summary>
    /// Couples one in-world fly NPC to one brain.
    ///
    /// The fly's body is holonomic-ish: it has a heading angle (0..2pi) it can turn
    /// freely, and it moves along that heading.  In a side-view world this reads as
    /// walking left or right while facing wherever it likes, exactly like a fly on a
    /// wall - the horizontal component of the heading drives X, the vertical
    /// component drives a compressed Y (flies walk up and down surfaces too).
    ///
    /// Without a brain blob the agent falls back to scripted chemotaxis so the mod
    /// is still playable, and the HUD labels the fly as "scripted".
    /// </summary>
    public sealed class FlyAgent
    {
        public NPC Npc;
        public FlyBrain Brain;
        public bool HasBrain => Brain != null;

        public float Heading;        // radians, 0 = facing +X
        public float TurnRate;       // rad/s, changed by the brain
        public float Speed;          // px/s along the heading

        public float FoodSmell;
        public float FoodTaste;
        public float Alarm;
        public float WingPhase;
        public bool Feeding;

        /// <summary>Latest sampled visual field (see FlyMind.Vision.WorldSampler).</summary>
        public Vision.FlySight Sight;

        /// <summary>Human-readable reading of the brain state (see BrainInterpreter).</summary>
        public readonly BrainInterpreter Interpreter = new BrainInterpreter();

        /// <summary>
        /// The scene-plus-circuit narration: what the eyes report, which populations fire,
        /// and what that implies.  Refreshed every tick from the same data the behaviour
        /// uses, so it describes this fly and not a generic one.
        /// </summary>
        public readonly NeuroNarrative Narrative = new NeuroNarrative();

        /// <summary>Short line shown in the brain scan panel.</summary>
        public string Interpretation => Interpreter.PanelText();

        /// <summary>Fraction of the eye view taken up by the fly's own body (0..1).</summary>
        public float SelfView => Vision.FlyEyeView.SelfInView;

        /// <summary>How fast the view is sweeping past (0..1), measured from the eye view.</summary>
        public float ViewMotion => Vision.FlyEyeView.ViewMotion;

        /// <summary>Seconds this fly has existed, used for the marker pulse.</summary>
        public float Age;

        /// <summary>
        /// The self-observation experiment this fly is part of (see World/CxExperiment).
        /// It only changes the structure of the fly's visual input; the fly keeps behaving
        /// with the same brain either way, which is what makes it a within-subject design.
        /// </summary>
        public readonly CxExperiment Experiment = new CxExperiment();

        private readonly float[] _previousChannels = new float[Vision.FlySight.Channels];
        private float _previousFoodSize;

        private float _wanderTimer;
        private float _wanderTarget;
        private readonly Random _rng;

        public FlyAgent(NPC npc, int seed)
        {
            Npc = npc;
            _rng = new Random(seed);
            Heading = NextFloat() * MathHelper.TwoPi;
            if (FlyMind.Instance?.CircuitData != null)
                Brain = new FlyBrain(FlyMind.Instance.CircuitData, seed);
        }

        public void Tick()
        {
            var npc = Npc;
            if (npc == null || !npc.active) return;

            Vector2 pos = npc.Center;

            // ---------- 1. sensory field sampling (smell / taste / alarm)
            FoodSmell = 0f;
            FoodTaste = 0f;
            Vector2 bestDir = Vector2.Zero;
            float bestConc = 0f;
            foreach (var patch in FoodScentSystem.Patches)
            {
                float c = patch.ConcentrationAt(pos, FoodScentSystem.SmellRadius);
                if (c > bestConc)
                {
                    bestConc = c;
                    bestDir = patch.Position - pos;
                }
                float d = Vector2.Distance(pos, patch.Position);
                if (d < FoodScentSystem.TasteRadius) FoodTaste = Math.Max(FoodTaste, c);
            }
            FoodSmell = bestConc;

            // danger: a player swinging a weapon right next to the fly
            Alarm = 0f;
            for (int i = 0; i < Main.maxPlayers; i++)
            {
                var p = Main.player[i];
                if (p == null || !p.active) continue;
                float d = Vector2.Distance(p.Center, pos);
                if (d < 96f && (p.itemAnimation > 0 || p.velocity.Length() > 3f))
                    Alarm = Math.Max(Alarm, 1f - d / 96f);
            }

            // ---------- 1b. eyes: sample the visual field for this tick
            Sight = Vision.WorldSampler.Sample(pos, Heading, _previousFoodSize, _previousChannels);
            _previousFoodSize = Sight.FoodSize;
            if (Sight.Looming > 0.4f)
                Alarm = Math.Max(Alarm, Sight.Looming);   // something is rushing at the fly

            // ---------- 2. brain step
            if (HasBrain)
            {
                // ---- the experiment decides what the fly's visual field contains this block
                if (Experiment.Running)
                {
                    Brain.BodyInVisualField = Experiment.Arm == CxArm.SelfView;
                    Brain.ForcePatchDrive = Experiment.Arm == CxArm.Shuffle;
                    Brain.SetPatch(Experiment.PatchForArm(Experiment.Arm));
                    Vision.FlyEyeView.RenderOwnBody = Brain.BodyInVisualField;
                }

                Brain.FoodSmell = FoodSmell;
                Brain.FoodTaste = FoodTaste;
                Brain.Danger = Alarm;
                // what the fly's own eyes are reporting: its body inside the view, and how
                // fast the rest of the view sweeps past (both measured by the eye view)
                Brain.SelfInView = Vision.FlyEyeView.SelfInView;
                Brain.ViewMotion = Vision.FlyEyeView.ViewMotion;
                Brain.Step();
                Experiment.Update(Brain, Brain.Cx, Brain.SelfInView, Brain.ViewMotion, 1f);

                // motor readout -> locomotion
                float targetSpeed = MathHelper.Clamp(Brain.ForwardDrive * 90f, 0f, 90f);
                Speed += 0.15f * (targetSpeed - Speed);

                // steering: combine the brain's turn bias with odour gradient taxis
                float taxis = 0f;
                if (bestDir != Vector2.Zero)
                {
                    float desired = (float)Math.Atan2(bestDir.Y * 0.35f, bestDir.X);
                    taxis = MathHelper.Clamp(MathHelper.WrapAngle(desired - Heading) * 2.5f, -3.5f, 3.5f);
                }
                float flee = 0f;
                if (Alarm > 0.05f)
                {
                    // run away from the nearest threatening player
                    Vector2 away = Vector2.Zero;
                    for (int i = 0; i < Main.maxPlayers; i++)
                    {
                        var p = Main.player[i];
                        if (p == null || !p.active) continue;
                        if (Vector2.Distance(p.Center, pos) < 160f)
                            away += pos - p.Center;
                    }
                    if (away != Vector2.Zero)
                    {
                        float desired = (float)Math.Atan2(away.Y * 0.35f, away.X);
                        flee = MathHelper.Clamp(MathHelper.WrapAngle(desired - Heading) * 3f, -4f, 4f);
                    }
                    Speed = Math.Max(Speed, 120f * Alarm);
                }

                TurnRate = Brain.TurnBias * 2.2f + taxis + flee;
                Feeding = Brain.Feeding > 0.35f && FoodTaste > 0.05f;
            }
            else
            {
                // ---------- scripted fallback (no brain blob): simple chemotaxis
                _wanderTimer -= 1f / 60f;
                if (_wanderTimer <= 0f)
                {
                    _wanderTimer = NextFloat(0.6f, 2.4f);
                    _wanderTarget = NextFloat(-2.4f, 2.4f);
                }
                float taxis = 0f;
                if (bestDir != Vector2.Zero)
                {
                    float desired = (float)Math.Atan2(bestDir.Y * 0.35f, bestDir.X);
                    taxis = MathHelper.Clamp(MathHelper.WrapAngle(desired - Heading) * 2.5f, -3.5f, 3.5f);
                }
                TurnRate = _wanderTarget * (1f - FoodSmell) + taxis * (0.4f + FoodSmell);
                float targetSpeed = 20f + 70f * FoodSmell + 120f * Alarm;
                Speed += 0.15f * (targetSpeed - Speed);
                Feeding = FoodTaste > 0.05f;
            }

            // ---------- 3. integrate the body
            Heading = MathHelper.WrapAngle(Heading + TurnRate * (1f / 60f));
            Vector2 dir = new Vector2((float)Math.Cos(Heading), (float)Math.Sin(Heading) * 0.35f);
            npc.velocity = dir * (Speed / 60f);

            // keep the fly out of solid tiles instead of phasing through the world
            if (npc.velocity.X != 0f && Collision.SolidCollision(npc.position + npc.velocity, npc.width, npc.height))
            {
                Heading = MathHelper.WrapAngle(Heading + MathHelper.Pi * 0.5f * (_rng.Next(2) == 0 ? 1f : -1f));
                npc.velocity = new Vector2((float)Math.Cos(Heading), (float)Math.Sin(Heading) * 0.35f) * (Speed / 60f);
            }

            // face along the heading (sprite flip only; the draw code rotates the sprite)
            npc.spriteDirection = Math.Cos(Heading) >= 0f ? 1 : -1;
            npc.rotation = Heading * 0.35f;   // partial tilt: top-down heading on a side view

            WingPhase += (0.25f + Speed / 60f) * (1f / 60f) * 40f;
            Age += 1f / 60f;
            Interpreter.Update(this, 1f / 60f);
            Narrative.SampleRates(Brain);
            Narrative.Update(this, 1f / 60f);
        }

        /// <summary>Uniform random float (System.Random has no such helper).</summary>
        private float NextFloat()
        {
            return (float)_rng.NextDouble();
        }

        private float NextFloat(float min, float max)
        {
            return min + (float)_rng.NextDouble() * (max - min);
        }
    }
}

