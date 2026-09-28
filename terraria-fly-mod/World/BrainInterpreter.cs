using System;
using System.Text;
using FlyMind.Neural;
using Microsoft.Xna.Framework;

namespace FlyMind
{
    /// <summary>
    /// Turns the fly's circuit state into a sentence a human can read.
    ///
    /// This is a *decoder*, not a mind reader: it maps measurable things (which
    /// populations are firing, how hard, and in what combination) onto the behavioural
    /// state those populations are known to drive - sensing, orienting, approaching,
    /// feeding, escaping, or idling.  A second line always shows the raw numbers the
    /// reading came from, so the player can judge it instead of trusting it.
    /// </summary>
    public sealed class BrainInterpreter
    {
        public string Headline = "静止";
        public string Mood = "平静";
        public string Detail = "";
        public string Evidence = "";

        private float _lastFoodSmell;
        private bool _wasFeeding;

        public void Update(FlyAgent agent, float dt)
        {
            var brain = agent.Brain;
            if (brain == null)
            {
                Headline = "脚本行为模式";
                Mood = "—";
                Detail = "没有加载连接组数据，行为由规则驱动。";
                Evidence = "脑活动：无";
                return;
            }

            bool feeding = agent.Feeding;
            bool moving = agent.Speed > 12f;
            float smell = Math.Max(brain.FoodSmell, brain.FoodTaste);
            bool justStartedFeeding = feeding && !_wasFeeding;
            _wasFeeding = feeding;
            _lastFoodSmell = brain.FoodSmell;

            var sb = new StringBuilder();
            string prefix = "";

            if (brain.Danger > 0.25f)
            {
                Headline = "受惊 · 逃跑";
                Mood = "恐惧";
                prefix = "危险通路被点亮。";
                sb.Append("苦味/威胁输入到了（Danger ");
                sb.Append(brain.Danger.ToString("0.00"));
                sb.Append("），下行神经元池在把它往外推。");
            }
            else if (justStartedFeeding)
            {
                Headline = "找到食物 · 伸喙取食";
                Mood = "满足";
                prefix = "它认出了这堆东西可以吃。";
                sb.Append("喙运动神经元开始放电（Feeding ");
                sb.Append(brain.Feeding.ToString("0.00"));
                sb.Append("），取食回路闭合。");
            }
            else if (feeding)
            {
                Headline = "正在取食";
                Mood = "满足";
                prefix = "它正在吃。";
                sb.Append("取食运动神经元持续放电（Feeding ");
                sb.Append(brain.Feeding.ToString("0.00"));
                sb.Append("），多巴胺池 ");
                sb.Append(brain.DopamineLevel.ToString("0.00"));
                sb.Append("。");
            }
            else if (brain.FoodTaste > 0.05f)
            {
                Headline = "尝到了食物";
                Mood = "兴奋";
                prefix = "喙碰到了能吃的东西。";
                sb.Append("味觉输入到达（Taste ");
                sb.Append(brain.FoodTaste.ToString("0.00"));
                sb.Append("），取食回路马上要启动。");
            }
            else if (smell > 0.06f && moving)
            {
                Headline = "闻到食物 · 正在靠近";
                Mood = brain.DopamineLevel > 0.4f ? "渴望" : "好奇";
                prefix = "它闻到吃的了，正在往那边走。";
                sb.Append("嗅觉通路在跟踪浓度梯度（Odour ");
                sb.Append(brain.FoodSmell.ToString("0.00"));
                sb.Append("），多巴胺池 ");
                sb.Append(brain.DopamineLevel.ToString("0.00"));
                sb.Append("，学到的偏好增益 x");
                sb.Append(brain.Attraction.ToString("0.00"));
                sb.Append("。");
            }
            else if (smell > 0.06f)
            {
                Headline = "闻到食物 · 正在定向";
                Mood = "好奇";
                prefix = "有味道，但还没决定往哪走。";
                sb.Append("气味已经进了触角叶，它正在把朝向调向浓度更高的方向。");
            }
            else if (moving)
            {
                Headline = "随意游走";
                Mood = "平静";
                prefix = "没闻到什么，它在乱逛。";
                sb.Append("没有食物线索，下行神经元维持一个低速探索步态。");
            }
            else
            {
                Headline = "静止";
                Mood = "平静";
                prefix = "它停着不动。";
                sb.Append("脑活动接近基线，可能在休息或理毛。");
            }

            if (brain.DopamineLevel > 0.55f && brain.Danger < 0.2f) Mood = "上头";
            else if (brain.DopamineLevel > 0.3f && brain.Danger < 0.2f && Mood == "平静") Mood = "有点兴奋";

            Detail = prefix + sb.ToString();
            Evidence = string.Format(
                "脉冲 {0} · 多巴胺 {1:0.00} · 气味 {2:0.00} · 取食 {3:0.00} · 危险 {4:0.00} · 速度 {5}",
                brain.Circuit.LastSpikeCount, brain.DopamineLevel, smell,
                brain.Feeding, brain.Danger, (int)agent.Speed);
        }

        /// <summary>Compact multi-line text for the brain scan panel.</summary>
        public string PanelText()
        {
            return "现在：" + Headline + "\n心情：" + Mood + "\n" + Evidence;
        }
    }
}
