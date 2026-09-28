# 你还要做的事（我做完的都列在最后）

> 更新：本轮已完成 **冲突剂量–反应（E）**、**n=20（F）**、**两档增益复现（G/H）**。
> 论文的正面结论现在是"缺失可容忍、矛盾按剂量退化"，见 `results/CONFLICT.md` 与 `paper/manuscript.md`。

## 0. 先说一件必须你判断的事

你之前说"不让 AI 写图表和总结"；这一轮你要的是成稿。我按 Science 格式写出了
`paper/manuscript.md`（含摘要、结果、讨论、方法、参考文献、图注、三张表）。
**投稿/交作业前请确认你所在场合对 AI 代笔的规定。** 若禁止 AI 生成正文文字：
把这份当"结构与数字的骨架"，正文用你自己的话重写（数字不必改，全部可追溯到 CSV）；
图可以照用（它们是从你的数据算出来的数据图，不是 AI 生成图像），或按 `paper/figures.md` 自己重画。
所有原始数据、命令、SHA256 都在 `results/`；三种披露方案与现成文本在 `paper/AI-DISCLOSURE.md`。

## 1. 必须你做的（我做不了）

1. **图已经画好了**——投稿图集 9 张（`main1`–`main4`、`main4b`、`supp1`–`supp4`，PDF + PNG）在
   `paper/figures/`，重跑 `python tools\make_main_figures.py` 即可；每格取哪个 CSV 的哪一列、
   误差棒与显著性约定写在 `paper/figures.md`。你要做的是**看一眼配色/排版是否合你意**，
   以及决定 Fig. 4 与 Fig. 5（`main4` + `main4b`）拆开投还是合并成一张。
2. **核对参考文献**：`manuscript.md` 中标 `[VERIFY]` 的条目（MaleCNS v1.0 的 Cell 卷/页/DOI、
   Schlegel 2024、Lin 2023）必须查证；Seelig 2015 / Kim 2017 / Webb 2004 的 DOI 本轮已核实。
3. **作者信息、单位、通讯、基金、致谢、利益冲突、CRediT 贡献声明**——稿里是占位符。
4. **仓库与数据可用性**：建仓库（或 Zenodo/figshare）上传 `flymind.brain`、`results/`、`tools/`、
   `paper/`。`edges.bin` 3.04 GB 不要上传，写"可由 `tools/export_edges.py` 从公开 feather 重建"。
5. **投稿信定稿**：`paper/cover-letter.md` 已写好，只差推荐审稿人（需你定，建议：CX/朝向回路 1 人、
   连接组约束建模 1 人、等效性/贝叶斯方法 1 人）。
6. **Reporting summary**（Science 要求）。**Note S1 / S2 已按期刊格式写好**：
   `paper/supplementary-note-S1.md`（来源、平衡公式、贝叶斯自校验、文件索引）、
   `paper/supplementary-note-S2.md`（AI 披露 + 提示词全文日志）——S2 里 S2.3.1 与 S2.4.3 两条
   标了 `[recorded form]`，你手上有会话记录，可换成逐字原文。
7. **决定投哪**：现在有了剂量–反应 + 行为读出 + 三档增益复现，
   现实顺序建议 **Nature Communications / eLife / PLoS Computational Biology**（命中率高）；
   若坚持 Science，走 **Report** 短格式，把"缺失 vs 矛盾 + drive-matching 陷阱"双卖点压到 4 图。

## 2. 审稿人可能还要的（我能做，但需要你点头）

| 优先级 | 实验 | 成本 | 说明 |
|---|---|---|---|
| 高 | **感受野映射替代 soma 代理** | 需下载 ~7 GB（`syn-partners` + `rois/fullbrain-roi-v4`） | 现在"身体斑块"是 soma 空间簇；用突触位置映射到视叶神经毡才是真正的视野区域。这是最容易被质疑的一点 |
| 中 | **行为闭环**：把转向保真度的下降接到飞行轨迹 | 需改 mod 侧 | 现在"转向指令"是下行神经元读出；若能让 fly agent 用这个指令飞，可给出"看见错误的自画像 → 飞得更差"的闭环证据 |
| 中 | **对称 vs 单侧斑块** | 约 30 min 机时 | 第三人称下身体在画面中央：对称遮挡与单侧遮挡预测不同 |
| 低 | 多组 trial 种子重跑 | 约 1 h | 报告 d 的跨种子散布 |
| 低 | 加可塑性（STDP/增益控制） | 新机制 | 回答"看见自己会不会被学会" |

## 3. 三条最容易被抓住的点，先想好怎么答

1. **"12,000 神经元只占 CNS 的 1.1% 突触、平均入度 135 vs 全脑 ~900，凭什么谈生物学？"**
   答：所有结论都是同回路内部的条件对照；κ 的标定与扫描、以及"未配平就会出假阳性"的实证都在方法里；
   并且冲突效应在 κ=150/300/600 三档复现（`results/CONFLICT.md` §4）。
2. **"切片里 CX 占 17.3%，真脑约 0.9%——放大了 20 倍还测不出'缺失'的效应？"**
   答：正因为放大，零结果更强；这确实是选择偏差，已写进 Limitations。
3. **"n=10 的贝叶斯因子上限只有 2.52，凭什么说'无差异'？"**
   答：现在有三条并列证据——n=20 把 BF01 抬到 2.8–3.2（设计上限 3.24）、
   ±10% 原始界的 TOST 全部通过、同一读出对冲突剂量给出 ρ = −0.94（P = 2e−4）的阳性对照；
   且诚实承认 |d|<0.5 的标准化界未全部通过、`ring_lag_yaw_deg` 在 n=20 时 BF01 = 0.74（不支持的唯一指标）。

## 4. 我已经做完的（不用你再做）

| 产出 | 文件 |
|---|---|
| Science 格式稿件（三张表、四张主图 + 一张对照图 + 四张补充图的图注、十七条参考文献、AI 声明） | `paper/manuscript.md` |
| 投稿信（含 AI 使用声明）+ 投稿检查表 | `paper/cover-letter.md` |
| 补充材料 Note S1（来源、平衡公式、贝叶斯自校验、文件索引） | `paper/supplementary-note-S1.md` |
| 补充材料 Note S2（AI 披露 + 提示词全文日志，按阶段分组） | `paper/supplementary-note-S2.md` |
| AI 使用政策核查 + 三处披露文本 + A/B/C 三个方案 | `paper/AI-DISCLOSURE.md` |
| 投稿图集 9 张（PDF + PNG 300 dpi）与绘图脚本 | `paper/figures/main*,supp*`、`tools/make_main_figures.py` |
| 图表数据规格 | `paper/figures.md` |
| 冲突剂量（E）、n=20（F）、增益复现（G/H） | `results/CONFLICT.md` + `results/raw/E,F,G,H-*` |
| 配平后的主数据与新旧对照 | `results/BALANCED.md` |
| 三项方法学验证（阳性对照 / 传播 / 等效性+贝叶斯） | `results/VALIDATION.md` |
| 来源与可复现性（SHA256、命令、环境） | `results/PROVENANCE.md` |
| 电路简图（blob 现算，含 Mermaid 与矩阵） | `circuit-schematic.md` |
| 逐 trial 原始数据 + 全部统计表 | `results/raw/*-trials.csv`、`*-compare.csv`、`*-pairs.csv`、`*-equivalence.csv`、`*-matching.csv` |
| 分析代码（含贝叶斯自校验与剂量趋势） | `tools/compare_trials.py`、`tools/conflict_trend.py` |
| 可交互实现（Terraria mod，F9 跑同一实验，已安装） | `terraria-fly-mod/` |
