using System;
using System.Globalization;
using System.IO;
using System.Text;
using FlyMind.Neural;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Terraria;
using Terraria.GameContent;
using Terraria.ModLoader;

namespace FlyMind.UI
{
    /// <summary>
    /// "神经实验台" - the panel that tells the player, live, what the fly's eyes are
    /// reporting and what that does to its circuit, and can dump the same readings to a
    /// text file so a session can be read back later.
    ///
    /// Two things it deliberately does:
    ///   * shows the 16 measured visual channels as a bar strip, so the reading can be
    ///     checked against the raw signal instead of taken on faith
    ///   * labels every neural statement with a firing rate, because "the fly is afraid"
    ///     is only meaningful next to "the aversive pathway is at 6.2 Hz"
    ///
    /// F7 toggles the panel, F8 writes a snapshot into the log file.
    /// </summary>
    public class NeuroLabHud : ModSystem
    {
        public static bool Visible = true;

        private const int PanelWidth = 430;
        private const int PanelHeight = 250;
        private const string LogName = "flymind_neurolab.txt";

        private static Texture2D _pixel;
        private static float _logTimer;

        /// <summary>Whatever the last F8 / auto snapshot wrote, for reference in chat.</summary>
        public static string LastDumpPath = "";

        public override void PostDrawInterface(SpriteBatch spriteBatch)
        {
            if (Main.dedServ || Main.gameMenu) return;

            var agent = FoodScentSystem.TheFly;
            if (agent == null || agent.Npc == null || !agent.Npc.active) return;

            // auto-log: a snapshot every few seconds so a session leaves a readable trace
            _logTimer += 1f / 60f;
            bool autoLog = NeuroLabConfig.AutoLog;
            if (autoLog && _logTimer >= NeuroLabConfig.AutoLogInterval)
            {
                _logTimer = 0f;
                WriteSnapshot(agent, "auto");
            }
            if (NeuroLabConfig.DumpRequested)
            {
                NeuroLabConfig.DumpRequested = false;
                WriteSnapshot(agent, "manual");
            }

            if (!Visible) return;

            if (_pixel == null)
            {
                _pixel = new Texture2D(Main.graphics.GraphicsDevice, 1, 1);
                _pixel.SetData(new[] { Color.White });
            }

            float scale = MathHelper.Clamp(Main.UIScale, 0.75f, 1.25f);
            int w = (int)(PanelWidth * scale);
            int h = (int)(PanelHeight * scale);
            // bottom-right, under the brain scan + eye view
            var origin = new Vector2(Main.screenWidth - w - 10f, Main.screenHeight - h - 10f);
            var panel = new Rectangle((int)origin.X, (int)origin.Y, w, h);
            DrawChrome(spriteBatch, panel, new Color(8, 12, 18, 224), new Color(96, 168, 168));

            var font = FontAssets.MouseText.Value;
            float x = origin.X + 10f;
            float y = origin.Y + 7f;

            Utils.DrawBorderString(spriteBatch, "神经实验台 · 它看见什么 → 脑里发生什么",
                new Vector2(x, y), new Color(196, 240, 236), 0.74f);
            y += 20f;

            // ---- measured visual channels
            Utils.DrawBorderString(spriteBatch, "视网膜通道(左→右 240°)", new Vector2(x, y),
                new Color(150, 206, 206), 0.6f);
            y += 15f;
            DrawChannelStrip(spriteBatch, agent.Sight, (int)x, (int)y, w - 20, 20);
            y += 24f;

            var brain = agent.Brain;
            string sightLine = string.Format(
                "空地{0:0}% 遮挡{1:0}% 亮度{2:0.00} 对比{3:0.00} 边缘{4} 最近墙{5:0.0}格",
                agent.Sight.OpenFraction * 100f, agent.Sight.WallFraction * 100f,
                agent.Sight.TotalLight, agent.Sight.Contrast, agent.Sight.EdgeCount,
                agent.Sight.NearestWall);
            Utils.DrawBorderString(spriteBatch, sightLine, new Vector2(x, y),
                new Color(206, 214, 226), 0.6f);
            y += 17f;

            string selfLine = string.Format(
                "自分占视野{0:0}% 画面位移{1:0.00} 自运动池{2:0.00} 主导:{3}",
                agent.SelfView * 100f, agent.ViewMotion,
                brain?.SelfMotionLevel ?? 0f, agent.Narrative.DominantPool());
            Utils.DrawBorderString(spriteBatch, selfLine, new Vector2(x, y),
                new Color(206, 190, 236), 0.6f);
            y += 19f;

            // ---- the three-beat reading
            DrawWrapped(spriteBatch, "看见  " + agent.Narrative.See, x, ref y,
                w - 20, new Color(220, 236, 236));
            DrawWrapped(spriteBatch, "神经  " + agent.Narrative.Fire, x, ref y,
                w - 20, new Color(255, 224, 170));
            DrawWrapped(spriteBatch, "所以  " + agent.Narrative.So, x, ref y,
                w - 20, new Color(190, 236, 190));

            // ---- central complex: the region the self-observation experiment measures
            if (agent.Brain?.Cx != null)
            {
                var cx = agent.Brain.Cx;
                DrawWrapped(spriteBatch, string.Format(CultureInfo.InvariantCulture,
                    "中央复合体 CX {0:0.0} Hz  活跃 {1:0}%  "
                    + "ring {2:0.0} / columnar {3:0.00} / fanbody {4:0.0} / other {5:0.0}",
                    cx.CxRate, cx.CxActiveFraction * 100f, cx.FamilyRate[1], cx.FamilyRate[2],
                    cx.FamilyRate[3], cx.FamilyRate[4]), x, ref y, w - 20,
                    new Color(236, 214, 160));
                DrawWrapped(spriteBatch, string.Format(CultureInfo.InvariantCulture,
                    "朝向环 bump 幅值 {0:0.00}  角度 {1:0}°  ({2} 个 EPG/PEG 细胞)",
                    cx.BumpR, cx.BumpAngle * 180f / MathF.PI, cx.RingCells), x, ref y, w - 20,
                    new Color(200, 226, 250));
            }
            var exp = agent.Experiment;
            if (exp.Running)
            {
                DrawWrapped(spriteBatch, string.Format(CultureInfo.InvariantCulture,
                    "自我观察实验 F9：{0} 臂  第 {1} 块  {2:0}%  (NAT {3} / SELF {4} / SHUF {5})",
                    exp.Arm, exp.BlocksDone + 1, exp.BlockProgress * 100f,
                    exp.BlockCount(World.CxArm.Natural), exp.BlockCount(World.CxArm.SelfView),
                    exp.BlockCount(World.CxArm.Shuffle)), x, ref y, w - 20, new Color(255, 200, 220));
            }
            else
            {
                DrawWrapped(spriteBatch, "自我观察实验：按 F9 开始（NAT/SELF/SHUF 每 20 秒轮换）",
                    x, ref y, w - 20, new Color(160, 170, 190));
            }

            Utils.DrawBorderString(spriteBatch, "F7 显隐 · F8 存档快照 · F9 自我观察实验",
                new Vector2(x, origin.Y + h - 15f), new Color(130, 140, 160), 0.58f);
        }

        /// <summary>The 16 sampled directions, drawn as bars: heights are the raw signal.</summary>
        private static void DrawChannelStrip(SpriteBatch sb, Vision.FlySight sight,
            int x, int y, int width, int height)
        {
            Fill(sb, new Rectangle(x, y, width, height), new Color(14, 18, 26, 230));
            if (sight.Channel == null) return;
            int n = sight.Channel.Length;
            float bw = width / (float)n;
            for (int c = 0; c < n; c++)
            {
                float v = MathHelper.Clamp(sight.Channel[c], 0f, 1f);
                float bv = MathHelper.Clamp(sight.Brightness != null && c < sight.Brightness.Length
                    ? sight.Brightness[c] : 0f, 0f, 1f);
                int bh = (int)((height - 4) * v);
                var bar = new Rectangle((int)(x + c * bw) + 1, y + height - 2 - bh,
                    Math.Max(1, (int)bw - 2), bh);
                // colour by brightness so a dark direction reads differently from a lit wall
                var col = Color.Lerp(new Color(220, 140, 90), new Color(150, 230, 240), bv);
                Fill(sb, bar, col * 0.95f);
            }
            // food direction marker
            if (sight.FoodSize > 0.05f)
            {
                int fx = (int)(x + (sight.FoodDirection * 0.5f + 0.5f) * width);
                Fill(sb, new Rectangle(fx - 1, y, 2, height), new Color(140, 255, 140));
            }
            // brightest direction marker
            int bx = (int)(x + (sight.BrightestChannel + 0.5f) * bw);
            Fill(sb, new Rectangle(bx - 1, y, 1, height), new Color(255, 255, 255) * 0.5f);
        }

        private static void DrawWrapped(SpriteBatch sb, string text, float x, ref float y,
            float width, Color color)
        {
            const float glyphWidth = 7.4f;      // MouseText at scale 0.62
            int perLine = Math.Max(12, (int)(width / glyphWidth));
            foreach (var raw in text.Split('\n'))
            {
                var line = raw;
                while (line.Length > perLine)
                {
                    int cut = line.LastIndexOf(' ', Math.Min(perLine, line.Length - 1));
                    if (cut <= 0) cut = Math.Min(perLine, line.Length);
                    Utils.DrawBorderString(sb, line.Substring(0, cut), new Vector2(x, y), color, 0.62f);
                    line = line.Substring(cut).TrimStart();
                    y += 15f;
                }
                if (line.Length > 0)
                {
                    Utils.DrawBorderString(sb, line, new Vector2(x, y), color, 0.62f);
                    y += 15f;
                }
            }
        }

        /// <summary>Write the current reading to disk so the session can be reviewed later.</summary>
        public static void WriteSnapshot(FlyAgent agent, string reason)
        {
            try
            {
                string dir = Path.Combine(ModLoader.ModPath);
                if (!Directory.Exists(dir))
                    dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                        "My Games", "Terraria", "tModLoader", "Mods");
                string path = Path.Combine(dir, LogName);
                LastDumpPath = path;

                var brain = agent.Brain;
                var sight = agent.Sight;
                var sb = new StringBuilder();
                sb.Append("=== ").Append(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"))
                  .Append("  [").Append(reason).Append("] ===\n");
                sb.Append("世界: ").Append(Main.worldName)
                  .Append("  果蝇位置 ").Append((int)(agent.Npc.Center.X / 16f)).Append(',')
                  .Append((int)(agent.Npc.Center.Y / 16f)).Append(" 格\n");
                sb.Append("朝向 ").Append((agent.Heading * 180f / Math.PI).ToString("0"))
                  .Append("°  速度 ").Append(agent.Speed.ToString("0")).Append(" px/s\n");
                sb.Append("通道: ");
                for (int c = 0; c < sight.Channel.Length; c++)
                    sb.Append(sight.Channel[c].ToString("0.00", CultureInfo.InvariantCulture)).Append(' ');
                sb.Append('\n');
                sb.Append("场景: 空地 ").Append((sight.OpenFraction * 100f).ToString("0"))
                  .Append("%  遮挡 ").Append((sight.WallFraction * 100f).ToString("0"))
                  .Append("%  亮度 ").Append(sight.TotalLight.ToString("0.00"))
                  .Append("  对比 ").Append(sight.Contrast.ToString("0.00"))
                  .Append("  边缘 ").Append(sight.EdgeCount)
                  .Append("  最近墙 ").Append(sight.NearestWall.ToString("0.0")).Append(" 格\n");
                sb.Append("自身: 占视野 ").Append((agent.SelfView * 100f).ToString("0"))
                  .Append("%  画面位移 ").Append(agent.ViewMotion.ToString("0.00")).Append('\n');
                if (brain != null)
                {
                    var r = brain.PopulationRates;
                    sb.Append("种群(Hz): ");
                    AppendPool(sb, "sensory", r[FlyBrain.PopSensory]);
                    AppendPool(sb, "antennal", r[FlyBrain.PopAntennalLobe]);
                    AppendPool(sb, "kenyon", r[FlyBrain.PopKenyon]);
                    AppendPool(sb, "dopamine", r[FlyBrain.PopDopamine]);
                    AppendPool(sb, "mbon", r[FlyBrain.PopMbon]);
                    AppendPool(sb, "descending", r[FlyBrain.PopDescending]);
                    AppendPool(sb, "motor", r[FlyBrain.PopMotor]);
                    AppendPool(sb, "selfmotion", r[FlyBrain.PopSelfMotion]);
                    sb.Append('\n');
                    sb.Append("读出: 多巴胺 ").Append(brain.DopamineLevel.ToString("0.00"))
                      .Append("  前向 ").Append(brain.ForwardDrive.ToString("0.00"))
                      .Append("  取食 ").Append(brain.Feeding.ToString("0.00"))
                      .Append("  危险 ").Append(brain.Danger.ToString("0.00"))
                      .Append("  自运动 ").Append(brain.SelfMotionLevel.ToString("0.00"))
                      .Append("  增益 x").Append(brain.Attraction.ToString("0.00"))
                      .Append("  本步脉冲 ").Append(brain.Circuit.LastSpikeCount).Append('\n');
                }
                sb.Append("看见  ").Append(agent.Narrative.See).Append('\n');
                sb.Append("神经  ").Append(agent.Narrative.Fire).Append('\n');
                sb.Append("所以  ").Append(agent.Narrative.So).Append("\n\n");
                File.AppendAllText(path, sb.ToString(), Encoding.UTF8);
            }
            catch (Exception e)
            {
                ModContent.GetInstance<FlyMind>()?.Logger.Warn("NeuroLab snapshot failed: " + e.Message);
            }
        }

        private static void AppendPool(StringBuilder sb, string name, float ratePerStep)
        {
            float hz = ratePerStep * 10f;
            if (hz < 0.1f) return;
            sb.Append(name).Append('=').Append(hz.ToString("0.0")).Append(' ');
        }

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
            sb.Draw(_pixel, rect, color);
        }
    }

    /// <summary>Runtime switches for the neuro lab, toggled from the keyboard.</summary>
    public static class NeuroLabConfig
    {
        /// <summary>Write a snapshot every <see cref="AutoLogInterval"/> seconds.</summary>
        public static bool AutoLog = true;
        public static float AutoLogInterval = 5f;

        /// <summary>Set by the keybind; the HUD consumes it on the next frame.</summary>
        public static bool DumpRequested;
    }
}
