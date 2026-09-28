using System;
using System.Text;
using FlyMind.Neural;
using Microsoft.Xna.Framework;

namespace FlyMind
{
    /// <summary>
    /// Reads the fly's visual scene together with its circuit activity and writes the
    /// result out as sentences.
    ///
    /// The structure of every reading is the same three beats, so the player can check it:
    ///   看见 SEE   - what the retina is actually reporting (geometry: walls, open air,
    ///               contrast, where the mass sits, what is looming)
    ///   神经 FIRE  - which populations that light up, named with their real cell groups
    ///               and the firing rates, not adjectives
    ///   所以 SO    - the behavioural tendency that follows, phrased as a tendency
    ///
    /// Nothing here reads the fly's "mind": it maps measurable population activity plus
    /// measured scene geometry onto a description, and always shows the numbers behind it.
    /// </summary>
    public sealed class NeuroNarrative
    {
        public string See = "";
        public string Fire = "";
        public string So = "";
        public string Dominant = "";

        private readonly StringBuilder _sb = new StringBuilder(256);

        public void Update(FlyAgent agent, float dt)
        {
            var brain = agent.Brain;
            var sight = agent.Sight;

            var see = new StringBuilder();
            var fire = new StringBuilder();
            var so = new StringBuilder();

            // ---------------------------------------------------------------- SEE
            string openWord = sight.OpenFraction > 0.8f ? "开阔"
                            : sight.OpenFraction > 0.5f ? "半开阔"
                            : sight.OpenFraction > 0.2f ? "被挡了一半" : "几乎贴脸";
            see.Append("视野").Append(openWord);
            see.Append("（空地 ").Append((int)(sight.OpenFraction * 100)).Append("%");
            see.Append(" · 遮挡 ").Append((int)(sight.WallFraction * 100)).Append("%）");

            if (sight.NearestWall > 0.1f && sight.NearestWall < 12f)
                see.Append("，最近的墙 ").Append(sight.NearestWall.ToString("0.0")).Append(" 格");

            see.Append("；亮度 ").Append(sight.TotalLight.ToString("0.00"));
            if (sight.Contrast > 0.35f)
                see.Append("，明暗差大(").Append(sight.Contrast.ToString("0.00")).Append(")");
            if (sight.EdgeCount >= 3)
                see.Append("，").Append(sight.EdgeCount).Append(" 处强边缘");

            // where the mass sits relative to the nose
            float f = sight.FrontWeight, l = sight.LeftWeight, r = sight.RearWeight;
            if (f > l && f > r && f > 0.03f) see.Append("；正前方有东西");
            else if (r > l && r > f && r > 0.03f) see.Append("；东西在身后");
            else if (l > 0.03f) see.Append("；东西偏向一侧");

            if (sight.FoodSize > 0.05f)
            {
                string side = sight.FoodDirection < -0.25f ? "左" : sight.FoodDirection > 0.25f ? "右" : "正对";
                see.Append("；食物在").Append(side).Append("侧、占比 ").Append((int)(sight.FoodSize * 100)).Append("%");
            }
            if (sight.Looming > 0.25f) see.Append("；有东西正在快速放大");
            if (agent.SelfView > 0.02f)
                see.Append("；自己的身子占了画面的 ").Append((int)(agent.SelfView * 100)).Append("%");
            if (agent.ViewMotion > 0.05f)
                see.Append("；画面在扫过(位移 ").Append(agent.ViewMotion.ToString("0.00")).Append(")");
            see.Append("。");

            // ---------------------------------------------------------------- FIRE
            if (brain == null)
            {
                Fire = "没有载入连接组数据，这一帧没有可读的神经活动。";
                So = "当前行为由规则驱动，不是从脑活动推出来的。";
                See = see.ToString();
                Dominant = "无脑数据";
                return;
            }

            var circuit = brain.Circuit;
            bool anyFire = false;

            AppendPool(fire, ref anyFire, "自运动细胞 LPTC", _selfMotionRate,
                "视网膜位移 + 自身占视野 → H1/H2/VS/V1 群");
            AppendPool(fire, ref anyFire, "嗅觉投射神经元", _odorRate,
                "气味输入进触角叶");
            AppendPool(fire, ref anyFire, "糖觉 GRN", _sugarRate,
                "味觉接触");
            AppendPool(fire, ref anyFire, "Kenyon 细胞(蘑菇体)", _kenyonRate,
                "气味在这张图里被表征");
            AppendPool(fire, ref anyFire, "多巴胺 PAM/PPL", _danRate,
                "奖赏/厌恶标签");
            AppendPool(fire, ref anyFire, "MBON 蘑菇体输出", _mbonRate,
                "蘑菇体往外说的一句话");
            AppendPool(fire, ref anyFire, "下行神经元 DN", _dnRate,
                "把指令送出去");
            AppendPool(fire, ref anyFire, "取食运动神经元", _motorRate,
                "喙/取食动作");

            if (!anyFire)
                fire.Append("所有种群都在基线附近(脉冲 ").Append(circuit.LastSpikeCount).Append(")，没有明显反应。");

            // the dominant channel of activity, named
            Dominant = DominantPool();

            // ---------------------------------------------------------------- SO
            if (brain.Danger > 0.25f)
                so.Append("厌恶性输入占优 → 逃跑/拉开距离的倾向。");
            else if (agent.Feeding)
                so.Append("取食回路闭合 → 停在原地吃。");
            else if (brain.FoodTaste > 0.05f)
                so.Append("味觉已确认 → 下一步是伸喙。");
            else if (brain.FoodSmell > 0.06f && agent.Speed > 12f)
                so.Append("嗅觉梯度在上升 → 朝气味源移动。");
            else if (brain.FoodSmell > 0.06f)
                so.Append("闻到但还没定方向 → 转头扫描。");
            else if (agent.Speed > 12f)
                so.Append("没有化学线索 → 低速随机探索。");
            else
                so.Append("没有驱动性输入 → 停驻/理毛。");

            if (brain.SelfMotionLevel > 0.25f)
                so.Append(" 自运动信号强，它在登记「我在动、世界在退」——这是稳定视线用的，不是它在看自己的脑。");

            See = see.ToString();
            Fire = fire.ToString();
            So = so.ToString();
        }

        private static void AppendPool(StringBuilder sb, ref bool any, string name, float rate,
            string meaning, float threshold = 0.35f)
        {
            if (rate < threshold) return;
            if (any) sb.Append("；");
            sb.Append(name).Append(' ').Append(rate.ToString("0.0")).Append(" Hz");
            if (!string.IsNullOrEmpty(meaning)) sb.Append("（").Append(meaning).Append('）');
            any = true;
        }

        // population rates sampled once per update, in Hz (spikes per 100 ms x 10)
        private float _selfMotionRate, _odorRate, _sugarRate, _kenyonRate;
        private float _danRate, _mbonRate, _dnRate, _motorRate;

        /// <summary>Populations that were firing, biggest first - the "what dominated" line.</summary>
        public string DominantPool()
        {
            var best = "";
            float top = 0f;
            void Consider(string name, float v)
            {
                if (v > top) { top = v; best = name; }
            }
            Consider("自运动 LPTC", _selfMotionRate);
            Consider("Kenyon 细胞", _kenyonRate);
            Consider("多巴胺", _danRate);
            Consider("MBON", _mbonRate);
            Consider("下行 DN", _dnRate);
            Consider("取食运动", _motorRate);
            Consider("嗅觉输入", _odorRate);
            Consider("糖觉输入", _sugarRate);
            return top <= 0f ? "无" : string.Format("{0}（{1:0.0} Hz）", best, top);
        }

        /// <summary>Refresh the per-population rates this narrative reports.</summary>
        public void SampleRates(FlyBrain brain)
        {
            if (brain == null) return;
            var r = brain.PopulationRates;
            _selfMotionRate = r[FlyBrain.PopSelfMotion] * 10f;
            _odorRate = r[FlyBrain.PopAntennalLobe] * 10f;
            _sugarRate = r[FlyBrain.PopSensory] * 10f;
            _kenyonRate = r[FlyBrain.PopKenyon] * 10f;
            _danRate = r[FlyBrain.PopDopamine] * 10f;
            _mbonRate = r[FlyBrain.PopMbon] * 10f;
            _dnRate = r[FlyBrain.PopDescending] * 10f;
            _motorRate = r[FlyBrain.PopMotor] * 10f;
        }

        /// <summary>Three labelled lines for the HUD / the log.</summary>
        public string PanelText()
        {
            _sb.Clear();
            _sb.Append("看见  ").Append(See).Append('\n');
            _sb.Append("神经  ").Append(Fire).Append('\n');
            _sb.Append("所以  ").Append(So);
            return _sb.ToString();
        }
    }
}
