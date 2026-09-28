using System.Collections.Generic;
using Terraria;
using Terraria.ModLoader;

namespace FlyMind.Players
{
    /// <summary>
    /// Gives the player the fly food from the start (the item the whole mod hangs off:
    /// left click = eat it yourself, right click = put it down) and routes the mod's
    /// hotkeys.
    ///
    /// Notes on the 1.4.4 API, both verified against tModLoader.dll:
    ///   * ModPlayer.AddStartingItems returns IEnumerable&lt;Item&gt;, so items are yielded
    ///   * hotkeys are polled in ModPlayer.ProcessTriggers(TriggersSet); the Mod class has
    ///     no hotkey hook
    /// </summary>
    public class StarterPlayer : ModPlayer
    {
        public override IEnumerable<Item> AddStartingItems(bool mediumCoreDeath)
        {
            yield return new Item(ModContent.ItemType<Items.FlyFood>(), 3);
        }

        public override void ProcessTriggers(Terraria.GameInput.TriggersSet triggersSet)
        {
            if (FlyMind.ToggleLab?.JustPressed == true)
            {
                UI.NeuroLabHud.Visible = !UI.NeuroLabHud.Visible;
                UI.NeuroLabConfig.AutoLog = UI.NeuroLabHud.Visible;
                Main.NewText(UI.NeuroLabHud.Visible
                    ? "神经实验台：开（每 5 秒把读数写进 flymind_neurolab.txt）"
                    : "神经实验台：关");
            }

            if (FlyMind.DumpSnapshot?.JustPressed == true)
            {
                UI.NeuroLabConfig.DumpRequested = true;
                Main.NewText("神经实验台：快照已写入 Mods\\flymind_neurolab.txt");
            }

            // F9 - the self-observation experiment: NAT -> SELF -> SHUF blocks, 20 s each,
            // logged to Mods\flymind_experiment.txt
            if (FlyMind.ToggleExperiment?.JustPressed == true)
            {
                var agent = FoodScentSystem.TheFly;
                if (agent?.Brain == null)
                {
                    Main.NewText("还没有果蝇，先召唤一只（左键喂食 / 右键放置食物）");
                }
                else
                {
                    bool wasRunning = agent.Experiment.Running;
                    agent.Experiment.Toggle();
                    if (!wasRunning)
                    {
                        agent.Experiment.Configure(agent.Brain.CircuitData);
                        agent.Brain.BodyInVisualField = true;
                        agent.Brain.SetPatch(agent.Experiment.PatchForArm(World.CxArm.SelfView));
                    }
                    else
                    {
                        Vision.FlyEyeView.RenderOwnBody = true;
                        agent.Brain.BodyInVisualField = true;
                        agent.Brain.ForcePatchDrive = false;
                    }
                    Main.NewText(agent.Experiment.Running
                        ? "自我观察实验：开始。NAT(看不见自己) → SELF(看见自己) → SHUF(安慰剂) 每 20 秒轮换，"
                          + "结果写入 Mods\\flymind_experiment.txt"
                        : "自我观察实验：停止");
                }
            }
        }
    }
}
