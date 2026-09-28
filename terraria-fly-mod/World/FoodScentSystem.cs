using System;
using System.Collections.Generic;
using FlyMind.Neural;
using Microsoft.Xna.Framework;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace FlyMind
{
    /// <summary>A lump of fly food sitting in the world, radiating smell.</summary>
    public sealed class FoodPatch
    {
        public Vector2 Position;
        public float Age;              // seconds
        public float Lifetime = 90f;   // seconds until it dries out
        public float Strength = 1f;    // smell intensity, decays with age

        /// <summary>Smell concentration at a world position: 1 at the patch, 0 beyond Radius.</summary>
        public float ConcentrationAt(Vector2 p, float radius)
        {
            float d = Vector2.Distance(p, Position);
            if (d >= radius) return 0f;
            return Strength * (1f - d / radius);
        }
    }

    public enum FlyStimulus
    {
        None,
        Food,        // smells food: seek it
        Feeding,     // arrived: extend proboscis and feed
        Alarmed      // player swinging nearby / damaged: flee
    }

    /// <summary>
    /// World-level manager: owns the food patches and the brain-driven fly agents.
    /// Runs once per game tick from ModSystem.PostUpdateEverything.
    /// </summary>
    public sealed class FoodScentSystem : ModSystem
    {
        public const float SmellRadius = 40f * 16f;   // 40 tiles
        public const float TasteRadius = 1.5f * 16f;  // proboscis reach

        public static readonly List<FoodPatch> Patches = new List<FoodPatch>();
        public static readonly List<FlyAgent> Flies = new List<FlyAgent>();

        /// <summary>
        /// The one fly the player is watching: its brain is what the scan panel draws
        /// and its eyes are what the fly-cam shows.  Food placement moves it rather
        /// than spawning more, so there is always exactly one.
        /// </summary>
        public static FlyAgent TheFly
        {
            get
            {
                for (int i = Flies.Count - 1; i >= 0; i--)
                {
                    var a = Flies[i];
                    if (a?.Npc != null && a.Npc.active) return a;
                }
                return null;
            }
        }

        private static int _nextSeed = 12345;

        public static FoodPatch PlacePatch(Vector2 worldPos, Player owner)
        {
            var patch = new FoodPatch { Position = worldPos };
            Patches.Add(patch);
            SpawnOrSummonTheFly(worldPos, owner);
            return patch;
        }

        /// <summary>
        /// Ensure exactly one fly exists, and put it near the fresh food so the player
        /// immediately sees the reaction.  Reuses the existing fly instead of spawning
        /// another one.
        /// </summary>
        private static void SpawnOrSummonTheFly(Vector2 worldPos, Player owner)
        {
            if (Main.netMode == NetmodeID.MultiplayerClient) return;

            var existing = TheFly;
            if (existing != null)
            {
                // teleport it in with a little puff of dust, just outside smell range
                float angle = Main.rand.NextFloat(MathHelper.TwoPi);
                var spot = worldPos + new Vector2((float)Math.Cos(angle), (float)Math.Sin(angle) * 0.4f)
                           * (SmellRadius * 0.8f);
                if (IsFreeSpot(spot))
                {
                    existing.Npc.Center = spot;
                    existing.Npc.velocity = Vector2.Zero;
                    existing.Npc.netUpdate = true;
                    for (int i = 0; i < 8; i++)
                        Dust.NewDust(existing.Npc.position, existing.Npc.width, existing.Npc.height, DustID.Smoke);
                }
                return;
            }

            int type = ModContent.NPCType<NPCs.Fly>();
            var spawn = worldPos + new Vector2(Main.rand.NextFloat(-SmellRadius * 0.7f, SmellRadius * 0.7f),
                                               -Main.rand.NextFloat(40f, 160f));
            var idx = NPC.NewNPC(new Terraria.DataStructures.EntitySource_SpawnNPC(),
                (int)spawn.X, (int)spawn.Y, type);
            if (idx >= 0 && idx < Main.maxNPCs)
            {
                var npc = Main.npc[idx];
                npc.velocity = new Vector2(Main.rand.NextFloat(-1f, 1f), Main.rand.NextFloat(-1f, 1f));
                npc.netUpdate = true;
                RegisterFly(npc);
            }
        }

        private static bool IsFreeSpot(Vector2 world)
        {
            int tx = (int)(world.X / 16f), ty = (int)(world.Y / 16f);
            return tx > 10 && tx < Main.maxTilesX - 10 && ty > 10 && ty < Main.maxTilesY - 10;
        }

        public static FlyAgent GetAgent(NPC npc)
        {
            foreach (var a in Flies)
                if (a.Npc == npc) return a;
            return null;
        }

        public static void RegisterFly(NPC npc)
        {
            if (GetAgent(npc) != null) return;
            Flies.Add(new FlyAgent(npc, _nextSeed++));
        }

        public static void UnregisterFly(NPC npc)
        {
            for (int i = Flies.Count - 1; i >= 0; i--)
                if (Flies[i].Npc == npc) Flies.RemoveAt(i);
        }

        public override void PostUpdateEverything()
        {
            if (Main.dedServ) return;

            // age the patches
            for (int i = Patches.Count - 1; i >= 0; i--)
            {
                var p = Patches[i];
                p.Age += 1f / 60f;
                p.Strength = Math.Max(0f, 1f - p.Age / p.Lifetime);
                if (p.Age >= p.Lifetime) Patches.RemoveAt(i);
            }

            // drop agents whose npc slot got reused
            for (int i = Flies.Count - 1; i >= 0; i--)
            {
                var a = Flies[i];
                if (a.Npc == null || !a.Npc.active || a.Npc.type != ModContent.NPCType<NPCs.Fly>())
                    Flies.RemoveAt(i);
            }
        }

        public override void OnWorldUnload()
        {
            Patches.Clear();
            Flies.Clear();
        }
    }
}
