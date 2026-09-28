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
    /// Marks the one watched fly so it is never lost in the dark or behind a wall:
    /// a pulsing ring around it, a small arrow above it with its name, and an edge
    /// indicator with a distance readout when it leaves the screen.
    /// </summary>
    public class FlyMarkerLayer : ModSystem
    {
        private static Texture2D _pixel;

        public override void PostDrawTiles()
        {
            if (Main.dedServ || Main.gameMenu) return;
            var agent = FoodScentSystem.TheFly;
            if (agent == null || agent.Npc == null || !agent.Npc.active) return;

            if (_pixel == null)
            {
                _pixel = new Texture2D(Main.graphics.GraphicsDevice, 1, 1);
                _pixel.SetData(new[] { Color.White });
            }

            var sb = Main.spriteBatch;
            Vector2 world = agent.Npc.Center;
            Vector2 screen = world - Main.screenPosition;
            float pulse = 0.5f + 0.5f * (float)Math.Sin(agent.Age * 4.0);

            sb.Begin(SpriteSortMode.Deferred, BlendState.AlphaBlend, SamplerState.PointClamp,
                DepthStencilState.None, RasterizerState.CullNone, null, Main.GameViewMatrix.TransformationMatrix);

            bool onScreen = screen.X > -40 && screen.X < Main.screenWidth + 40
                            && screen.Y > -40 && screen.Y < Main.screenHeight + 40;

            if (onScreen)
            {
                // pulsing ring, drawn as a square outline so it never needs a round texture
                var ring = new Color(120, 220, 255) * (0.55f + 0.35f * pulse);
                int r = (int)(16 + 4 * pulse);
                DrawOutline(sb, new Rectangle((int)screen.X - r, (int)screen.Y - r, r * 2, r * 2), ring, 2);

                // arrow above its head
                int ax = (int)screen.X;
                int ay = (int)screen.Y - 30 - (int)(3 * pulse);
                for (int i = 0; i < 8; i++)
                    sb.Draw(_pixel, new Rectangle(ax - 4 + i / 2, ay + i, 8 - i, 1), new Color(120, 220, 255));

                // name tag
                string tag = string.Format("◄ 观察对象 · 果蝇 {0}{1}",
                    agent.HasBrain ? "· 真连接组" : "· 脚本",
                    agent.Feeding ? " · 取食中" : "");
                var size = FontAssets.MouseText.Value.MeasureString(tag);
                Utils.DrawBorderString(sb, tag,
                    new Vector2(screen.X - size.X * 0.5f, ay - 22f),
                    new Color(180, 235, 255), 0.72f);
            }
            else
            {
                // offscreen indicator pinned to the screen edge, with distance
                Vector2 dir = screen - new Vector2(Main.screenWidth * 0.5f, Main.screenHeight * 0.5f);
                if (dir.LengthSquared() < 1f) dir = Vector2.UnitX;
                dir.Normalize();
                var edge = new Vector2(Main.screenWidth * 0.5f, Main.screenHeight * 0.5f)
                           + dir * new Vector2(Main.screenWidth * 0.42f, Main.screenHeight * 0.42f);
                edge.X = MathHelper.Clamp(edge.X, 60f, Main.screenWidth - 60f);
                edge.Y = MathHelper.Clamp(edge.Y, 60f, Main.screenHeight - 60f);

                float dist = Vector2.Distance(world, Main.LocalPlayer.Center) / 16f;
                string tag = string.Format("果蝇 {0:0} 格 →", dist);
                Utils.DrawBorderString(sb, tag, edge, new Color(160, 225, 255), 0.8f);

                float ang = (float)Math.Atan2(dir.Y, dir.X);
                for (int i = 0; i < 10; i++)
                {
                    float t = i / 10f;
                    var p = edge + new Vector2((float)Math.Cos(ang), (float)Math.Sin(ang)) * (34f + t * 10f);
                    sb.Draw(_pixel, new Rectangle((int)p.X, (int)p.Y, 4, 4), new Color(160, 225, 255) * (1f - t));
                }
            }

            sb.End();
        }

        private static void DrawOutline(SpriteBatch sb, Rectangle r, Color color, int thickness)
        {
            sb.Draw(_pixel, new Rectangle(r.X, r.Y, r.Width, thickness), color);
            sb.Draw(_pixel, new Rectangle(r.X, r.Bottom - thickness, r.Width, thickness), color);
            sb.Draw(_pixel, new Rectangle(r.X, r.Y, thickness, r.Height), color);
            sb.Draw(_pixel, new Rectangle(r.Right - thickness, r.Y, thickness, r.Height), color);
        }
    }
}
