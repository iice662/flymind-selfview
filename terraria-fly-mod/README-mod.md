# FlyMind — 用果蝇脑模型驱动的 Terraria mod

> 数据：**MaleCNS v1.0**（Google Research × HHMI Janelia × FlyWire Consortium，Cell 2026-09-03，约 16.6 万神经元，脑 + 腹神经索）
> 动力学：**Shiu et al. 2024, Nature 634:210** 的 leaky integrate-and-fire 模型（`w_syn = 0.275 mV`，唯一自由参数）
> 状态：**已编译、已打包、已安装**到 `Documents\My Games\Terraria\tModLoader\Mods\terraria-fly-mod.tmod`

---

## 玩法

1. 启动 tModLoader → **Mods** 里启用 **FlyMind** → Reload Mods → 进世界。
2. 物品栏自带 3 个 **果蝇食物**：
   - **左键 = 自己吃**：什么都不会发生（只有一句吐槽文本）。
   - **右键 = 放置**：放在地上，会召来**唯一那只被观察的果蝇**。
3. 屏幕**右侧**是它的脑：
   - 上半部分 **实时脑成像**：每一个点就是一个真实神经元，按功能上色（多巴胺=橙、蘑菇体 Kenyon 细胞=紫、MBON=黄、运动=绿、下行=蓝、感觉=浅绿），越亮 = 当前脉冲率越高。
   - 中间是四条读数条：多巴胺 / 食物气味 / 前向驱动 / 取食 / 危险。
   - 下面是**实时解读**：用人话告诉你它现在想干什么，以及这个判断依据的原始数字。
   - 最下面 **果蝇视角 fly-cam（第三人称）**：从它眼睛位置、按它的朝向后上方拍的画面。
4. 世界里的那只果蝇有**脉冲光圈 + 头顶箭头 + 名字标签**；跑出屏幕时屏幕边缘会显示方向箭头和距离。

## 目录

| 文件 | 作用 |
|---|---|
| `FlyMind.cs` | mod 主类，按 `FLYMIND_BRAIN` 环境变量 → `ModSources/FlyMind/Assets/flymind.brain` → `D:\projects\science\flymind.brain` 找脑数据 |
| `Neural/LifCircuit.cs` | LIF 内核（参数逐字照抄论文；CSR 稀疏突触、1.8 ms 延迟环缓冲、KC→MBON 多巴胺增益） |
| `Neural/BrainData.cs` | `flymind.brain` 读取器 |
| `Neural/FlyBrain.cs` | 一只果蝇的脑：Poisson 感觉编码 + 多巴胺/前向/转向/取食读出 + 学习增益 |
| `Items/FlyFood.cs` | 左键吃（无效果）/ 右键放置 |
| `Players/StarterPlayer.cs` | 开局自带 3 个 |
| `NPCs/Fly.cs` | 果蝇 NPC：自定义 AI、按朝向旋转绘制、4 帧动画 |
| `World/FoodScentSystem.cs` | 食物堆、气味场、**唯一那只果蝇**的管理 |
| `World/FlyAgent.cs` | 身体：朝向角 + 角速度 + 速度（侧向压缩 0.35）、避墙、逃跑、趋味 |
| `World/BrainInterpreter.cs` | 把脑状态翻译成"它在想什么"的文字 + 依据数字 |
| `Vision/WorldSampler.cs` | 神经侧视觉：沿视野射线采样 → 16 通道 + 运动 + 迫近 |
| `Vision/FlyEyeView.cs` | 果蝇视角：渲染到 RenderTarget2D 的第三人称画面 |
| `UI/BrainScanHud.cs` | 右侧脑成像面板 |
| `UI/FlyMarkerLayer.cs` | 果蝇的标记（光圈/箭头/名牌/屏幕外指示） |

## 重建

```powershell
# 编译 + 打包（需要 .NET 8 SDK）
cd D:\projects\science\terraria-fly-mod
dotnet build
# 产物 .tmod 交给 tModLoader 由它自己安装到 Mods 目录
```

### 脑数据管线（离线）

```
malecns/connectome-weights.feather (1 GB, 151,856,684 条边)
malecns/body-annotations.feather   (13.8 MB, 211,577 行)
        │  tools/feather_lite.py    纯 Python Arrow IPC/Feather 读取器
        │  tools/export_annotations.py  → annotations.tsv
        │  tools/export_edges.py        → edges.bin (2.4 GB 紧凑流)
        ▼  tools/CircuitBuilder (C#) 预算式重要性生长 + 导出
   flymind.brain  →  放进 Assets/  →  重新 dotnet build
```

`tools/` 里还有：`parquet_lite.py`（纯 Python Parquet 读取器）、`fetch_file.ps1`（断点续传）、
`dump_api.ps1`（用 Mono.Cecil 从 `tModLoader.dll` 导出真实 API 签名，写代码前先查证）、
`gen_sprites.ps1`（占位贴图）。

## 诚实边界

- 这是**连接组约束的近似模型**：无神经调质扩散、无可塑性（KC→MBON 增益是我们加的规则层）、2D 身体是近似。
- MaleCNS 的平坦边表**只有强度没有正负号**，所以当前所有突触都按兴奋处理——这不是生物学上完整的（GABA/谷氨酸抑制缺失）。
- 视觉是功能性压缩，不是视叶数万神经元的仿真；fly-cam 是自绘的第三人称窗口，不是原版渲染管线。
- "记忆/想法"的解读是**行为状态解码**（哪群神经元在放电 → 对应的行为倾向），不是读心。
- 引用：Berg et al. 2026（MaleCNS 数据）；Shiu et al. 2024（LIF 模型）；Schlegel et al. 2024 / Dorkenwald et al. 2024（FlyWire 对照）。
