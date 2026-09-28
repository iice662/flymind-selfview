using FlyMind.Neural;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.ID;
using Terraria.ModLoader;

namespace FlyMind.NPCs
{
    /// <summary>
    /// A fruit fly. Its movement comes from <see cref="FlyAgent"/>: a heading angle
    /// it can turn freely plus a speed driven by the descending-neuron readout of a
    /// FlyWire-derived LIF circuit (see FlyMind.Neural).
    /// </summary>
    public class Fly : ModNPC
    {
        public override void SetStaticDefaults()
        {
            Main.npcFrameCount[Type] = 4;   // idle / walk / groom / feed
            NPCID.Sets.CountsAsCritter[Type] = true;
            NPCID.Sets.TakesDamageFromHostilesWithoutBeingFriendly[Type] = false;
            NPCID.Sets.NPCBestiaryDrawOffset.Add(Type, new NPCID.Sets.NPCBestiaryDrawModifiers
            {
                Velocity = 0.5f,
            });
        }

        public override void SetDefaults()
        {
            NPC.width = 10;
            NPC.height = 8;
            NPC.aiStyle = -1;              // we drive the body ourselves
            NPC.damage = 0;
            NPC.defense = 0;
            NPC.lifeMax = 8;
            NPC.HitSound = SoundID.NPCHit1;
            NPC.DeathSound = SoundID.NPCDeath1;
            NPC.noGravity = true;          // flies walk on surfaces, not on gravity
            NPC.noTileCollide = false;     // but still bump into walls
            NPC.friendly = false;
            NPC.catchItem = 0;             // not catchable (yet)
            NPC.knockBackResist = 1.4f;
            NPC.alpha = 0;
        }

        public override void AI()
        {
            FoodScentSystem.RegisterFly(NPC);
            var agent = FoodScentSystem.GetAgent(NPC);
            if (agent == null) return;

            // The agent owns the body: heading, speed and the brain step.  Running it
            // here (rather than from a ModSystem) keeps the fly in lockstep with the
            // NPC update, which vanilla expects.
            agent.Tick();

            NPC.direction = NPC.spriteDirection;
        }

        public override void FindFrame(int frameHeight)
        {
            var agent = FoodScentSystem.GetAgent(NPC);
            if (agent == null)
            {
                NPC.frame.Y = 0;
                return;
            }

            if (agent.Feeding) NPC.frame.Y = frameHeight * 3;
            else if (agent.Speed > 8f) NPC.frame.Y = frameHeight * 1;
            else NPC.frame.Y = 0;
        }

        public override bool PreDraw(SpriteBatch spriteBatch, Vector2 screenPos, Color drawColor)
        {
            var agent = FoodScentSystem.GetAgent(NPC);
            if (agent == null) return false;

            // Draw the fly rotated to its heading instead of a left/right flip: the
            // heading is the fly's real state, the sprite just visualises it.
            var texture = Terraria.GameContent.TextureAssets.Npc[Type].Value;
            int frameH = texture.Height / Main.npcFrameCount[Type];
            var source = new Rectangle(0, NPC.frame.Y, texture.Width, frameH);
            Vector2 origin = new Vector2(texture.Width / 2f, frameH / 2f);
            float rot = NPC.rotation + (NPC.spriteDirection < 0 ? MathHelper.Pi : 0f);
            var effects = NPC.spriteDirection < 0 ? SpriteEffects.FlipVertically : SpriteEffects.None;

            if (agent.HasBrain)
                drawColor = Color.Lerp(drawColor, new Color(170, 205, 255), 0.30f);

            spriteBatch.Draw(texture, NPC.Center - screenPos, source, drawColor, rot,
                origin, NPC.scale, effects, 0f);
            return false;   // we drew it ourselves
        }

        public override void OnKill()
        {
            FoodScentSystem.UnregisterFly(NPC);
            for (int i = 0; i < 4; i++)
                Dust.NewDust(NPC.position, NPC.width, NPC.height, DustID.Blood);
        }

        public override bool CheckActive() => false;   // do not despawn when offscreen
    }
}
