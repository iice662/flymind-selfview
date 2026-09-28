using System;
using System.Collections.Generic;
using FlyMind.Neural;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace FlyMind.UI
{
    /// <summary>
    /// Right-hand brain scan: draws the fly's actual neurons as a live activity map
    /// plus the per-population readouts the behaviour is derived from.
    ///
    /// The neuron map is a real grid of dots, one per neuron, coloured by population and
    /// brightened by that neuron's current firing rate - so what the player watches is
    /// the circuit itself, not an animation.
    /// </summary>
    public class BrainScanHud : ModSystem
    {
        public static bool Visible = true;

        private const int BasePanelWidth = 252;
        private const int PanelHeight = 300;
        private const int Pad = 12;

        private static Texture2D _dot;

        public override void PostDrawInterface(SpriteBatch spriteBatch)
        {
            if (Main.dedServ || Main.gameMenu) return;

            // keep the fly's eye view rendered for whichever panel wants to show it
            var watched = FoodScentSystem.TheFly;
            if (watched != null && global::FlyMind.Vision.FlyEyeView.Enabled)
                global::FlyMind.Vision.FlyEyeView.Render(watched);

            if (!Visible) return;
            var agent = watched;
            if (agent == null || agent.Npc == null || !agent.Npc.active) return;

            if (_dot == null)
            {
                _dot = new Texture2D(Main.graphics.GraphicsDevice, 2, 2);
                _dot.SetData(new[] { Color.White, Color.White, Color.White, Color.White });
            }

            float uiScale = MathHelper.Clamp(Main.UIScale, 0.75f, 1.25f);
            int panelW = (int)(BasePanelWidth * uiScale);
            int panelH = (int)(PanelHeight * uiScale);
            var origin = new Vector2(Main.screenWidth - panelW - 10f, (Main.screenHeight - panelH) * 0.35f);

            var panel = new Rectangle((int)origin.X, (int)origin.Y, panelW, panelH);
            DrawChrome(spriteBatch, panel);

            var font = FontAssets.MouseText.Value;
            float x = origin.X + Pad;
            float y = origin.Y + 8f;

            Utils.DrawBorderString(spriteBatch, "果蝇脑实时成像 · Brain Scan", new Vector2(x, y),
                new Color(226, 232, 250), 0.82f);
            y += 22f;
            Utils.DrawBorderString(spriteBatch, "MaleCNS v1.0 · Shiu 2024 LIF", new Vector2(x, y),
                new Color(150, 158, 185), 0.62f);
            y += 20f;

            var brain = agent.Brain;
            if (brain == null)
            {
                Utils.DrawBorderString(spriteBatch, "未载入 flymind.brain", new Vector2(x, y),
                    new Color(230, 160, 160), 0.72f);
                y += 20f;
                Utils.DrawBorderString(spriteBatch, "当前为脚本行为模式", new Vector2(x, y),
                    new Color(170, 170, 190), 0.66f);
                y += 22f;
                Utils.DrawBorderString(spriteBatch, "神经元：无 · 脉冲率：无", new Vector2(x, y),
                    new Color(150, 150, 170), 0.66f);
                if (agent.Interpretation != null)
                    DrawInterpretation(spriteBatch, x, origin.Y + panelH - 96f * uiScale, agent.Interpretation, uiScale);
                return;
            }

            // ---- neuron activity map
            float mapH = 150f * uiScale;
            var map = new Rectangle((int)x, (int)y, panelW - Pad * 2, (int)mapH);
            DrawChrome(spriteBatch, map, new Color(6, 8, 14, 220), new Color(40, 48, 70));
            DrawNeuronMap(spriteBatch, brain, map);
            y += mapH + 8f;

            // ---- population meters
            Meter(spriteBatch, font, x, y, panelW - Pad * 2, "多巴胺 Dopamine",
                brain.DopamineLevel, new Color(255, 148, 60));
            y += 21f;
            Meter(spriteBatch, font, x, y, panelW - Pad * 2, "食物气味 Odour",
                Math.Max(brain.FoodSmell, brain.FoodTaste), new Color(140, 220, 130));
            y += 21f;
            Meter(spriteBatch, font, x, y, panelW - Pad * 2, "前向驱动 Forward",
                brain.ForwardDrive, new Color(130, 185, 255));
            y += 21f;
            Meter(spriteBatch, font, x, y, panelW - Pad * 2, "取食 Feeding",
                brain.Feeding, new Color(255, 220, 120));
            y += 21f;
            Meter(spriteBatch, font, x, y, panelW - Pad * 2, "危险 Danger",
                brain.Danger, new Color(255, 110, 110));
            y += 21f;
            // the fly's own movement detectors: these fire while it watches the world -
            // and its own body inside it - sweep past
            Meter(spriteBatch, font, x, y, panelW - Pad * 2, "自体运动 Self-motion",
                brain.SelfMotionLevel, new Color(190, 150, 255));
            y += 20f;

            if (global::FlyMind.Vision.FlyEyeView.SelfInView > 0.001f)
            {
                string self = string.Format("视野里自己占 {0:0}% · 画面位移 {1:0.00}",
                    global::FlyMind.Vision.FlyEyeView.SelfInView * 100f,
                    global::FlyMind.Vision.FlyEyeView.ViewMotion);
                Utils.DrawBorderString(spriteBatch, self, new Vector2(x, y),
                    new Color(190, 160, 255), 0.6f);
                y += 17f;
            }

            string stats = string.Format("神经元 {0} · 突触 {1} · 学习增益 x{2:0.00}",
                brain.Circuit.NeuronCount, brain.Circuit.SynapseCount, brain.Attraction);
            Utils.DrawBorderString(spriteBatch, stats, new Vector2(x, y),
                new Color(150, 156, 178), 0.6f);

            if (agent.Interpretation != null)
                DrawInterpretation(spriteBatch, x, origin.Y + panelH - 104f * uiScale,
                    agent.Interpretation, uiScale);
        }

        private static void DrawNeuronMap(SpriteBatch sb, FlyBrain brain, Rectangle map)
        {
            var circuit = brain.Circuit;
            int n = circuit.NeuronCount;
            if (n == 0) return;

            // grid: aim for roughly square cells, one dot per neuron
            int cols = (int)Math.Ceiling(Math.Sqrt(n * (map.Width / (float)Math.Max(1, map.Height))));
            cols = Math.Max(1, cols);
            int rows = (int)Math.Ceiling(n / (float)cols);

            float cw = map.Width / (float)cols;
            float ch = map.Height / (float)rows;
            float size = MathHelper.Clamp(Math.Min(cw, ch), 1.4f, 3.2f);

            var bar = Main.LocalPlayer.Center;
            for (int i = 0; i < n; i++)
            {
                int cx = i % cols;
                int cy = i / cols;
                var at = new Vector2(map.X + cx * cw + cw * 0.5f, map.Y + cy * ch + ch * 0.5f);

                var color = PopulationColor(circuit, i);
                float rate = circuit.Rate(i);
                // 0 spikes/100ms -> dim population tint, ~4 -> near white hot
                float heat = MathHelper.Clamp(rate * 0.25f, 0f, 1f);
                if (heat > 0.01f)
                    color = Color.Lerp(color * 0.55f, Color.White, heat * 0.85f);
                else
                    color *= 0.5f;
                color.A = (byte)(150 + 105 * heat);

                sb.Draw(_dot, at, null, color, 0f, new Vector2(0.5f), size, SpriteEffects.None, 0f);
            }
        }

        private static Color PopulationColor(LifCircuit circuit, int neuron)
        {
            switch (circuit.Population(neuron))
            {
                case FlyBrain.PopDopamine: return new Color(255, 138, 40);
                case FlyBrain.PopMbon: return new Color(255, 206, 90);
                case FlyBrain.PopKenyon: return new Color(150, 120, 255);
                case FlyBrain.PopMotor: return new Color(120, 240, 180);
                case FlyBrain.PopDescending: return new Color(110, 190, 255);
                case FlyBrain.PopSensory: return new Color(130, 230, 140);
                case FlyBrain.PopAntennalLobe: return new Color(90, 200, 230);
                case FlyBrain.PopVnc: return new Color(200, 150, 255);
                case FlyBrain.PopSelfMotion: return new Color(255, 130, 220);
                default: return new Color(150, 150, 165);
            }
        }

        private static void DrawInterpretation(SpriteBatch sb, float x, float y,
            string text, float scale)
        {
            Utils.DrawBorderString(sb, "它在做什么 / What it is doing", new Vector2(x, y),
                new Color(150, 200, 255), 0.62f);
            y += 18f;

            // wrap to the panel width without a measuring API dependency
            const int wrap = 20;
            foreach (var raw in text.Split('\n'))
            {
                var line = raw;
                while (line.Length > wrap)
                {
                    int cut = line.LastIndexOf(' ', Math.Min(wrap, line.Length - 1));
                    if (cut <= 0) cut = Math.Min(wrap, line.Length);
                    Utils.DrawBorderString(sb, line.Substring(0, cut), new Vector2(x, y),
                        new Color(236, 240, 250), 0.7f);
                    line = line.Substring(cut).TrimStart();
                    y += 16f;
                }
                if (line.Length > 0)
                {
                    Utils.DrawBorderString(sb, line, new Vector2(x, y),
                        new Color(236, 240, 250), 0.7f);
                    y += 16f;
                }
            }
        }

        private static void Meter(SpriteBatch sb, ReLogic.Graphics.DynamicSpriteFont font,
            float x, float y, float width, string label, float value, Color color)
        {
            value = MathHelper.Clamp(value, 0f, 1f);
            Utils.DrawBorderString(sb, label, new Vector2(x, y), new Color(198, 204, 224), 0.66f);
            int barX = (int)(x + width * 0.46f);
            int barW = (int)(width * 0.54f);
            var track = new Rectangle(barX, (int)y + 3, barW, 9);
            Fill(sb, track, new Color(34, 36, 50, 220));
            Fill(sb, new Rectangle(track.X, track.Y, (int)(track.Width * value), track.Height), color);
        }

        private static void DrawChrome(SpriteBatch sb, Rectangle r) =>
            DrawChrome(sb, r, new Color(10, 12, 20, 216), new Color(96, 116, 168));

        private static void DrawChrome(SpriteBatch sb, Rectangle r, Color fill, Color border)
        {
            Fill(sb, r, fill);
            Fill(sb, new Rectangle(r.X, r.Y, r.Width, 1), border);
            Fill(sb, new Rectangle(r.X, r.Y + r.Height - 1, r.Width, 1), border);
            Fill(sb, new Rectangle(r.X, r.Y, 1, r.Height), border);
            Fill(sb, new Rectangle(r.X + r.Width - 1, r.Y, 1, r.Height), border);
        }

        private static void Fill(SpriteBatch sb, Rectangle rect, Color color)
        {
            if (rect.Width <= 0 || rect.Height <= 0) return;
            sb.Draw(TextureAssets.MagicPixel.Value, rect, color);
        }
    }
}
