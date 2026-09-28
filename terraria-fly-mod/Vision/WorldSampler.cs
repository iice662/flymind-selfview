using System;
using Microsoft.Xna.Framework;
using Terraria;

namespace FlyMind.Vision
{
    /// <summary>
    /// What a fly's compound eyes are telling it, compressed into a handful of channels.
    /// The optic lobe holds ~60,000 of the MaleCNS neurons, so the game side keeps only
    /// the functional summary the rest of the circuit consumes - and the same summary is
    /// what the on-screen narrative describes.
    /// </summary>
    public struct FlySight
    {
        public const int Channels = 16;

        /// <summary>Per-channel "something is here": 0..1, index 0 = far left, 15 = far right.</summary>
        public float[] Channel;

        /// <summary>Per-channel light level of the air/open space in that direction.</summary>
        public float[] Brightness;

        public float TotalLight;      // mean brightness across the field
        public float Motion;          // frame-to-frame change (0..1)
        public float Looming;         // 0..1, rising when something is growing fast in view
        public float FoodDirection;   // -1 (left) .. 1 (right), 0 if no food in view
        public float FoodSize;        // 0..1, how much of the view the nearest food occupies
        public float SelfInView;      // 0..1, fraction of the view that is the fly's own body

        // ---- derived scene statistics, filled by WorldSampler
        public float WallFraction;    // how much of the field is blocked by solid geometry
        public float OpenFraction;    // how much of the field is open air
        public float Contrast;        // spread between the darkest and brightest direction
        public float LeftWeight;      // 0..1, mass of "stuff" on the left half
        public float FrontWeight;     // 0..1, mass in the centre of the field
        public float RearWeight;      // 0..1, mass behind the fly
        public float SkyBias;         // -1 all below, +1 all above (brightness asymmetry)
        public float NearestWall;     // tiles to the closest solid thing (0 = none in range)
        public float NearestWallAngle; // radians, where that closest thing is
        public float EdgeCount;       // number of strong channel-to-channel transitions (edges)
        public int BrightestChannel;  // index of the brightest direction
        public int DarkestChannel;    // index of the dimmest direction
    }

    /// <summary>
    /// Samples the world around a fly into a <see cref="FlySight"/>.
    ///
    /// The sampling grid is the fly's visual field: 240 degrees wide, centred on the
    /// fly's heading, walking outward in rays and asking what is in each cell.  That gives
    /// real occlusion (a wall in front of the food hides the food) without rendering
    /// anything, and it is the signal the retina would hand to the optic lobe.
    ///
    /// Beyond the 16 energy channels this now also reports the scene statistics the HUD
    /// narrates: how much is wall vs open air, contrast, where the mass sits relative to
    /// the heading, sky/ground bias and the distance to the nearest solid thing.
    /// </summary>
    public static class WorldSampler
    {
        public const float FovDegrees = 240f;   // flies see almost all the way around
        public const float MaxRange = 26f * 16f;

        private const int RaySamples = 14;      // samples along each ray
        private const float RayStep = MaxRange / RaySamples;

        /// <summary>
        /// Sample the world for one fly. <paramref name="previous"/> holds that fly's
        /// last frame (one entry per channel) so motion can be derived; it is updated
        /// in place. Call once per tick.
        /// </summary>
        public static FlySight Sample(Vector2 eye, float heading, float previousLoom, float[] previous)
        {
            if (previous == null || previous.Length != FlySight.Channels)
                previous = new float[FlySight.Channels];
            var sight = new FlySight
            {
                Channel = new float[FlySight.Channels],
                Brightness = new float[FlySight.Channels],
            };

            float fov = MathHelper.ToRadians(FovDegrees);
            float half = fov * 0.5f;
            float total = 0f;
            float sumLight = 0f;

            float left = 0f, front = 0f, rear = 0f;
            float above = 0f, below = 0f;
            int walls = 0, opens = 0;
            float nearest = float.MaxValue;
            float nearestAngle = 0f;

            for (int c = 0; c < FlySight.Channels; c++)
            {
                float t = FlySight.Channels == 1 ? 0.5f : c / (float)(FlySight.Channels - 1);
                float angle = heading - half + fov * t;
                Vector2 dir = new Vector2((float)Math.Cos(angle), (float)Math.Sin(angle) * 0.35f);
                if (dir.LengthSquared() > 0f) dir.Normalize();

                float energy = 0f;
                float lightHere = 0f;
                bool blocked = false;
                float blockDist = 0f;

                for (int s = 1; s <= RaySamples; s++)
                {
                    Vector2 p = eye + dir * (RayStep * s);
                    int tx = (int)(p.X / 16f);
                    int ty = (int)(p.Y / 16f);
                    if (!WorldGen.InWorld(tx, ty, 2)) break;

                    Tile tile = Main.tile[tx, ty];
                    if (tile != null && tile.HasTile)
                    {
                        // solid geometry blocks sight and counts as "something here", and
                        // the nearer it is the stronger the edge signal
                        energy += 1f - (s / (float)RaySamples) * 0.7f;
                        blocked = true;
                        blockDist = s * RayStep;
                        break;
                    }
                    // light in the air: flies orient by contrast, so bright tiles matter
                    float light = Lighting.Brightness(tx, ty);
                    lightHere = Math.Max(lightHere, light);
                    if (light > 0.75f) energy += 0.08f;
                }

                // which way the world leans relative to the fly's heading
                float angleFromNose = MathHelper.WrapAngle(angle - heading);
                float absFromNose = Math.Abs(angleFromNose);
                if (blocked)
                {
                    if (blockDist < nearest)
                    {
                        nearest = blockDist;
                        nearestAngle = angle;
                    }
                    if (absFromNose > MathHelper.Pi * 0.5f) rear += energy;
                    else if (absFromNose < MathHelper.Pi / 5f) front += energy;
                    else if (angleFromNose < 0f) left += energy;
                }

                // food patches are what the fly actually cares about
                float food = 0f;
                foreach (var patch in FoodScentSystem.Patches)
                {
                    Vector2 toPatch = patch.Position - eye;
                    float d = toPatch.Length();
                    if (d > MaxRange) continue;
                    float patchAngle = (float)Math.Atan2(toPatch.Y, toPatch.X);
                    float delta = Math.Abs(MathHelper.WrapAngle(patchAngle - angle));
                    if (delta < 0.25f)
                    {
                        float near = 1f - d / MaxRange;
                        energy += near * 1.5f;
                        food = Math.Max(food, near);
                    }
                }

                sight.Channel[c] = Math.Min(1f, energy);
                sight.Brightness[c] = lightHere;
                total += sight.Channel[c];
                sumLight += lightHere;
                if (blocked) walls++; else opens++;

                // sky/ground: rays pointing up vs down from the eye
                float vy = Math.Sign(dir.Y);
                if (vy < 0) above += lightHere; else below += lightHere;

                if (food > sight.FoodSize)
                {
                    sight.FoodSize = food;
                    sight.FoodDirection = t * 2f - 1f;
                }
            }

            sight.TotalLight = sumLight / FlySight.Channels;
            sight.WallFraction = walls / (float)FlySight.Channels;
            sight.OpenFraction = opens / (float)FlySight.Channels;
            sight.LeftWeight = MathHelper.Clamp(left / FlySight.Channels, 0f, 1f);
            sight.FrontWeight = MathHelper.Clamp(front / FlySight.Channels, 0f, 1f);
            sight.RearWeight = MathHelper.Clamp(rear / FlySight.Channels, 0f, 1f);
            sight.NearestWall = nearest == float.MaxValue ? 0f : nearest / 16f;
            sight.NearestWallAngle = nearestAngle;

            // contrast + edges + brightest/darkest direction
            float lo = 1f, hi = 0f;
            int loC = 0, hiC = 0;
            for (int c = 0; c < FlySight.Channels; c++)
            {
                if (sight.Channel[c] < lo) { lo = sight.Channel[c]; loC = c; }
                if (sight.Channel[c] > hi) { hi = sight.Channel[c]; hiC = c; }
            }
            sight.DarkestChannel = loC;
            sight.BrightestChannel = hiC;
            sight.Contrast = MathHelper.Clamp(hi - lo, 0f, 1f);
            int edges = 0;
            for (int c = 1; c < FlySight.Channels; c++)
                if (Math.Abs(sight.Channel[c] - sight.Channel[c - 1]) > 0.30f) edges++;
            sight.EdgeCount = edges;
            sight.SkyBias = MathHelper.Clamp((above - below) / Math.Max(0.001f, above + below), -1f, 1f);

            // motion = how much the view changed since last tick
            float change = 0f;
            for (int c = 0; c < FlySight.Channels; c++)
            {
                change += Math.Abs(sight.Channel[c] - previous[c]);
                previous[c] = sight.Channel[c];
            }
            sight.Motion = Math.Min(1f, change / FlySight.Channels * 4f);

            // looming = the view is filling up quickly: something is coming at the fly
            float grow = sight.FoodSize - previousLoom;
            sight.Looming = MathHelper.Clamp(grow * 6f, 0f, 1f);

            return sight;
        }
    }
}
