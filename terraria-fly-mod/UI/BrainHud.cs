using System;
using FlyMind.Neural;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace FlyMind.UI
{
    /// <summary>
    /// Small "fly mind" readout: when the player stands near a fly, a panel shows what
    /// that fly's brain is doing right now - dopamine pool activity, learned
    /// attraction, forward drive, and whether the proboscis is out.
    ///
    /// This is deliberately a HUD overlay rather than an embedded view of the world:
    /// rendering the world into a RenderTarget2D mid-frame is possible but needs its
    /// own verification pass on tModLoader 1.4.4 (see fly-mod-feasibility.md).
    /// </summary>
    public class BrainHud : ModSystem
    {
        public static bool Visible = true;

        private const float MaxDistance = 220f;

        public override void PostDrawInterface(SpriteBatch spriteBatch)
        {
            if (!Visible || Main.dedServ || Main.gameMenu) return;

            var agent = NearestAgent(out float dist);
            if (agent == null) return;

            Vector2 origin = new Vector2(24f, Main.screenHeight - 160f);
            DrawPanel(spriteBatch, origin, 268f, 136f);

            var brain = agent.Brain;
            string title = brain != null ? "果蝇脑 · FlyWire v783 · LIF" : "果蝇 · 脚本行为";
            Utils.DrawBorderString(spriteBatch, title, origin + new Vector2(10f, 6f),
                new Color(232, 232, 248), 0.85f);

            if (brain == null)
            {
                Utils.DrawBorderString(spriteBatch, "（未找到 flymind.brain）",
                    origin + new Vector2(10f, 34f), new Color(210, 170, 170), 0.75f);
                Utils.DrawBorderString(spriteBatch, "运行 tools/build_circuit.py 生成",
                    origin + new Vector2(10f, 56f), new Color(175, 175, 195), 0.7f);
                return;
            }

            float y = 32f;
            Meter(spriteBatch, origin + new Vector2(10f, y), "多巴胺 Dopamine", brain.DopamineLevel, new Color(255, 150, 60));
            y += 22f;
            Meter(spriteBatch, origin + new Vector2(10f, y), "食物气味 Odour", brain.FoodSmell, new Color(150, 220, 140));
            y += 22f;
            Meter(spriteBatch, origin + new Vector2(10f, y), "前向驱动 Forward", brain.ForwardDrive, new Color(140, 190, 255));
            y += 22f;
            Meter(spriteBatch, origin + new Vector2(10f, y), "取食 Feeding", brain.Feeding, new Color(255, 220, 120));

            string line = string.Format("学习增益 x{0:0.00}   距离 {1}", brain.Attraction, (int)dist);
            Utils.DrawBorderString(spriteBatch, line, origin + new Vector2(10f, 116f),
                new Color(205, 205, 220), 0.7f);
        }

        private static FlyAgent NearestAgent(out float distance)
        {
            FlyAgent best = null;
            distance = float.MaxValue;
            Vector2 me = Main.LocalPlayer.Center;
            foreach (var a in FoodScentSystem.Flies)
            {
                if (a?.Npc == null || !a.Npc.active) continue;
                float d = Vector2.Distance(me, a.Npc.Center);
                if (d < distance)
                {
                    distance = d;
                    best = a;
                }
            }
            return distance <= MaxDistance ? best : null;
        }

        private static void Meter(SpriteBatch sb, Vector2 pos, string label, float value, Color color)
        {
            value = MathHelper.Clamp(value, 0f, 1f);
            Utils.DrawBorderString(sb, label, pos, new Color(210, 210, 228), 0.7f);
            var track = new Rectangle((int)pos.X + 124, (int)pos.Y + 3, 120, 9);
            FillRect(sb, track, new Color(40, 40, 58, 210));
            FillRect(sb, new Rectangle(track.X, track.Y, (int)(track.Width * value), track.Height), color);
        }

        private static void DrawPanel(SpriteBatch sb, Vector2 pos, float w, float h)
        {
            var border = new Color(92, 112, 164);
            FillRect(sb, new Rectangle((int)pos.X, (int)pos.Y, (int)w, (int)h), new Color(12, 14, 22, 208));
            FillRect(sb, new Rectangle((int)pos.X, (int)pos.Y, (int)w, 1), border);
            FillRect(sb, new Rectangle((int)pos.X, (int)pos.Y + (int)h - 1, (int)w, 1), border);
            FillRect(sb, new Rectangle((int)pos.X, (int)pos.Y, 1, (int)h), border);
            FillRect(sb, new Rectangle((int)pos.X + (int)w - 1, (int)pos.Y, 1, (int)h), border);
        }

        private static void FillRect(SpriteBatch sb, Rectangle rect, Color color)
        {
            sb.Draw(TextureAssets.MagicPixel.Value, rect, color);
        }
    }
}
