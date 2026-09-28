# 果蝇脑模型 → 泰拉瑞亚 tModLoader Mod（MaleCNS 版）

> 更新 2026-09-15 · 工作目录 `D:\projects\science`
> 数据：**MaleCNS v1.0**（Google Research × HHMI Janelia × FlyWire Consortium，Cell 2026-09-03，约 16.6 万神经元，脑 + 腹神经索）
> 动力学：**Shiu et al. 2024, Nature 634:210** LIF 模型
> 状态：**已完成并装进游戏**——真连接组（含抑制性突触）+ 实时脑成像 + 实时解读 + 果蝇第三人称视角 + 标记

---

## 1. 成品

**`C:\Users\Asus\Documents\My Games\Terraria\tModLoader\Mods\`**
- `terraria-fly-mod.tmod`（3.19 MB，已启用）
- `flymind.brain`（16.4 MB，真连接组子回路，必须和 .tmod 放在一起）

玩法：
1. tModLoader → Mods 启用 **FlyMind** → 进世界。
2. 物品栏 3 个 **果蝇食物**：**左键自己吃＝什么都不会发生**；**右键放置**。
3. 屏幕**右侧**从上到下：
   - **实时脑成像**：9000 个点＝9000 个真实神经元，按功能上色（多巴胺橙 / Kenyon 紫 / MBON 黄 / 运动绿 / 下行蓝 / 感觉浅绿），亮 = 当前脉冲率高；
   - 五条读数：多巴胺 / 食物气味 / 前向驱动 / 取食 / 危险；
   - **实时解读**：一句话说它现在想干什么 + 依据的原始数字；
   - **果蝇视角 fly-cam（第三人称）**：从它眼睛位置、按它朝向后上方拍的画面。
4. 世界里的那只果蝇：**脉冲光圈 + 头顶箭头 + 名牌**；跑出屏幕时屏幕边缘显示方向箭头和距离。

---

## 2. 真实数据管线（全部打通）

| 数据 | 大小 | 结果 |
|---|---|---|
| `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | 1002 MB | **成功解码 151,856,684 条突触边**（2318 个 Arrow record batch） |
| `body-annotations-male-cns-v1.0-minconf-0.5.feather` | 13.8 MB | **成功解码 211,577 行**、11,752 种细胞类型 |
| `body-neurotransmitters-male-cns-v1.0.feather` | 43.3 MB | **成功解码 1,835,518 行**递质预测 → 164,401 个神经元有明确递质 |
| 最终子回路 `flymind.brain` | 8.08 MB | **12,000 神经元 / 594,036 突触 / 142,483 条抑制性（24%）** |

子回路的真实构成（blob 头部读出来的）：

```
sensory 2695 · kenyon 1803 · self_motion 1770 · antennal 625 · dopamine 344
motor 316 · descending 169 · mbon 77 · unknown 4201
种子：糖觉 GRN/tpGRN 60 · 嗅觉 ORN/PN 3303 · 运动 MN 312 · 自体运动 LPTC 1770
可塑性突触（Kenyon→MBON）：29,763
```

也就是说：**"食物气味 → 触角叶 → 蘑菇体 Kenyon 细胞 → 多巴胺 → 运动/下行"这条链是真的接上了**，
而且**突触带正负号**——GABA / 谷氨酸 / 组胺按抑制处理（依据每个突触前细胞的 consensus_nt 预测），不再全部当兴奋。

**突触预算**：完整子图是 1,767,641 条突触，LIF 每步要转发每个放电神经元的全部出边，超了 16 ms 帧预算。
所以导出时按突触前细胞比例抽稀到 594,036 条（**优先保留抑制性和 KC→MBON 可塑性突触**，12000 个神经元一个不丢）。

### 2.0 果蝇在第三人称视角里"看到什么"

`FlyEyeView` 每帧把它眼睛正前方（后上方视角）的画面渲染进 RenderTarget2D，然后做两件事：

1. **几何自视**：把果蝇自己的身体投影到画面里，得到一张 16×9 的占据栅格 → `SelfInView`（自己占视野的百分比）。
   这就是"它看见自己"的事实层面。
2. **视网膜位移**：把渲染结果读回 CPU（每 4 帧一次，约 15 Hz，约等于果蝇自身几十毫秒的视觉延迟），
   和上一帧做差 → `ViewMotion`（画面在扫过的速度）。

这两个量一起灌进 **lobula plate tangential cells**（H1/H2/VS/V1 与 JO-EV / LHAV / LHPV 家族，MaleCNS 里真实的 1770 个自运动神经元）。
它们在果蝇身上做的正是"世界在动 + 我自己在动"的登记，**不是**果蝇看见自己的脑——脑里没有能看到脑的感器，
面板上那条 `自体运动 Self-motion` 读数和脑成像里的粉色点就是这群细胞。

### 2.1 摸清的格式难点（都解决了）

1. 本机 **pip 被墙**、没有 pandas/pyarrow → 写了两个纯 Python 读取器：
   - `tools/parquet_lite.py` — Parquet（thrift compact + 字典编码 + LZ4/Snappy/ZSTD）
   - `tools/feather_lite.py` — **Arrow IPC / Feather**（手工 flatbuffer 遍历 + 按位打包字典索引 + **LZ4 帧 linked block** 解压）
2. pyarrow 的 LZ4 帧默认 `blockIndep=0`：后续块会引用前面块的已解压数据 → 第一版按独立块处理，第二块就报 "bad offset"。
3. Arrow Field 的真实布局：`0 name / 1 nullable / 2 type_tag / 3 type / 5 dictionary`——type tag 和 type 表是分开的两个槽，猜错就把 int64 当未知类型。
4. **每列的缓冲布局有两条分支**：文本列可能是 `[validity, int32 offsets, data]`，也可能是字典编码的 `[validity, 按位打包索引]`（只占 1 个缓冲）。判据是"下一个缓冲是否 ≥ 4×(行数+1) 字节"。这一个判断决定了后续每一列是否错位——之前 `class`/`superclass` 解出拼接串就是栽在这里。
5. 固定宽度列的缓冲是 `int64 原始长度 + LZ4 帧`，而文本列的 offsets 缓冲**没有**长度前缀；只有 `原始长度 < 存储字节数` 才剥前缀。曾试图用"期望字节数"驱动解包，把字符串列全解坏了——已回退并加了注释说明原因。
6. 递质表用同一套判据一次解通（10 列 / 10 节点 / 25 缓冲，计划数与实际完全一致），这反过来验证了第 4 条的规则。
7. `enabled.json` 里已经有 `terraria-fly-mod`。

### 2.2 性能：为什么要换语言

Python 扫 1.518 亿条边做每轮预算式生长**太慢**（跑了几分钟还在第一轮）。改成：
- `tools/export_edges.py` 把边表导成紧凑流 `edges.bin`（3.04 GB，int64+int64+int32）；
- `tools/CircuitBuilder/`（C#）做生长 + 加符号 + 抽稀 + 导出 blob — **82 秒**完成 12000 神经元。

mod 侧也做了针对性优化（突触量比原计划大一个数量级）：
- 延迟环缓冲按突触总量预分配，避免帧内 `Array.Resize`；
- 读出改成 `PopulationRates()` 单次遍历，而不是每个种群走一遍全数组；
- 视口回读节流到 15 Hz（`GetData` 不便宜，而且果蝇视觉本来就有几十毫秒延迟）。

---

## 3. 代码结构

```
terraria-fly-mod/
  FlyMind.cs                 加载 flymind.brain（环境变量 → Mods 目录 → ModSources → 仓库）
  Neural/LifCircuit.cs       LIF 内核（参数逐字照抄论文）+ 种群单遍读出
  Neural/BrainData.cs        blob 读取器
  Neural/FlyBrain.cs         Poisson 感觉编码 + 多巴胺/前向/转向/取食读出 + 学习增益
  Items/FlyFood.cs           左键吃（无效果）/ 右键放置
  Players/StarterPlayer.cs   开局自带 3 个
  NPCs/Fly.cs                果蝇 NPC（自定义 AI、按朝向旋转绘制）
  World/FoodScentSystem.cs   食物堆 + 气味场 + 唯一那只果蝇
  World/FlyAgent.cs          朝向角 + 角速度 + 速度（侧向压缩）、避墙、逃跑、趋味
  World/BrainInterpreter.cs  脑状态 → "它在想什么" + 依据数字
  Vision/WorldSampler.cs     神经侧视觉（16 通道 + 运动 + 迫近）
  Vision/FlyEyeView.cs       果蝇视角 RenderTarget2D 第三人称画面
  UI/BrainScanHud.cs         右侧脑成像面板
  UI/FlyMarkerLayer.cs       光圈 / 箭头 / 名牌 / 屏幕外指示
  Localization/*.hjson       中英文
  Assets/flymind.brain       回路数据
```

---

## 4. 诚实边界

- 连接组约束的**近似**模型：无神经调质扩散、无可塑性（KC→MBON 增益是我们加的规则层）、2D 身体是近似。
- **突触符号来自递质预测**，不是电生理实测：GABA / 谷氨酸 / 组胺按抑制处理，乙酰胆碱等按兴奋，标为 `unclear` 的按兴奋（不猜）。164,401 / 1,835,518 个 body 有明确标签，所以子回路里仍有部分突触的符号是默认值。
- **突触抽稀**：594,036 / 1,767,641 条（34%），按突触前细胞比例保留并偏向抑制性与可塑性突触。抽稀会改变网络动力学，只是把代价压进帧预算。
- **"看见自己"的准确含义**：果蝇看见的是**周围环境 + 画面里的自己**，不是自己的脑。驱动的是自运动细胞（LPTC），输入是"自己占视野多少 + 画面扫过多快"。脑里没有能看到脑的感器，所以"看自己的神经反应"这件事在这个模型里**不存在**，面板里给的是自运动反应。
- **视野占据是几何计算，不是像素识别**：`SelfInView` 来自把身体投影到视锥的几何，`ViewMotion` 才是真的读回渲染帧做的差分。所以"看见自己"这一半是几何事实，不是神经网络识别出来的。
- 视觉是功能性压缩，不是视叶数万神经元的仿真；fly-cam 是自绘的第三人称窗口，不是原版渲染管线。
- **解读是行为状态解码**（哪群神经元在放电 → 对应行为倾向），不是读心；面板里始终带上原始数字供自行判断。
- 引用：Berg et al. 2026（MaleCNS）；Shiu et al. 2024（LIF 模型）；Schlegel et al. 2024 / Dorkenwald et al. 2024（FlyWire 对照）。

---

## 5. 复现一步到位

```powershell
cd D:\projects\science\tools
python export_annotations.py                 # 211,577 行细胞标注
python export_transmitters.py                # 164,401 个神经元的递质
python export_edges.py                       # 151,856,684 条边 -> edges.bin（约 15 分钟）
cd CircuitBuilder
dotnet run -- ..\..\malecns\edges.bin ..\..\malecns\annotations.tsv ..\..\flymind.brain 9000 2 ..\..\malecns\transmitters.tsv
copy ..\..\flymind.brain ..\..\terraria-fly-mod\Assets\flymind.brain
cd ..\..\terraria-fly-mod; dotnet build      # 打包 .tmod
```
