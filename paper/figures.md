# 图表数据规格 + 生成方式

## 投稿图集（4 主图 + 1 方法与对照图 + 4 补充图）

**这是投稿用的那一套。** 脚本 `tools/make_main_figures.py`，只读 `results/raw/*.csv`，
所以图不可能与稿子里的数字脱钩；`manuscript.md` 的 Figure legends 已按这套结构改写。

```powershell
cd D:\projects\science
python tools\make_main_figures.py              # 全部 9 张
python tools\make_main_figures.py main4 supp1  # 单张
```

| 稿件 | 文件 | 尺寸 | 内容 |
|---|---|---|---|
| Fig. 1 | `main1.pdf/.png` | 双栏 7.0 in | 回路普查 / κ 标定 / 头向通路 / D-E 配平后投递事件 / F 被静默的 CX 输入构成 |
| Fig. 2 | `main2.pdf/.png` | 单栏 3.5 in | 信号传播：97.2% 一跳到达；2.5 ms 单突触峰（±body patch / κ=100·300·1000） |
| Fig. 3 | `main3.pdf/.png` | 双栏 7.0 in | 光流：A–G 各臂指标（n=10，95% CI），H rate vs geometry 效应量点图（randmat 复现 rate 不复现 geometry） |
| Fig. 4 | `main4.pdf/.png` | 双栏 7.0 in | 头向核心图：A–B n=20 零结果（BF01 2.8–3.0 / 2.4–2.8），C–H 冲突剂量单调曲线（ρ、P 标注在面板内） |
| Fig. 5 | `main4b.pdf/.png` | 双栏 7.0 in | 对照：A rate 与 drive 双平（ρ=+0.10 / −0.04）、B 三种 κ 下秩序保持、C BF01 柱状 + 设计上限 |
| Fig. S1 | `supp1.pdf/.png` | 双栏 7.0 in | patch 尺寸剂量（无趋势）+ 阳性对照（drive ±50%、同步注射） |
| Fig. S2 | `supp2.pdf/.png` | 单栏 3.5 in | 等效性森林图：8 个读数 × 3 对照，90% CI + \|d\|<0.5 界 |
| Fig. S3 | `supp3.pdf/.png` | 单栏 3.5 in | BF01 设计上限 vs 每臂 trial 数 |
| Fig. S4 | `supp4.pdf/.png` | 单栏 3.5 in | drive-matching trap：配平前后同一对比 |
| Fig. S5 | `supp5.pdf/.png` | 双栏 7.0 in | 切片真实解剖图：12,000 个 MaleCNS 胞体的 x–y 与 x–z 投影（池 1,594 LPTC + 1,095 CX 中继、身体斑块 672、环 EPG/PEG 68）+ 池/斑块的细胞类型构成。数据 `results/raw/slice-census.csv`，脚本 `tools/make_anatomy_figure.py` |

**图注数字全部由脚本从 CSV 现算**（`dose_annot()` 与面板标题里的 BF 都会重算），不再硬编码——
修正三个缺陷时就暴露过这个问题：旧版把 ρ 写死在 `main4` 标题里，数据一改图注立刻说谎。

**当前图对应的实验族**（修正后，见 `results/CORRECTION.md`）：
Fig. 1 ← `A4-flow-matching` + `I2-heading-matching` + 校准 `calibration2-sweep.txt`；
Fig. 2 ← `P2-propagation.stdout.txt`；Fig. 3 ← `A4-flow`；Fig. 4 ← `I2-heading` 剂量 + `J2-n20`；
Fig. 5 ← `I2-heading`（rate/drive 平性）+ `K2-k150`/`L2-k600`（增益复现）+ `J2-n20-equivalence.csv`；
Fig. S1 ← `M2-dose-dose` + `D2-controls`；Fig. S2 ← `J2-n20-equivalence.csv`；
Fig. S4 ← `I2-heading` 对 `B3-heading`（旧的未配平族）。

`main4` 与 `main4b` 是同一结果的两半（结论图 + 对照图），投稿时可合并为一张 5 行大图，
也可按上表拆成 Fig. 4 / Fig. 5——拆开对审稿人更友好，因为 BF 上限那段是方法性论证。

## 归档图集（早期 10 张，不投稿）

`tools/make_figures.py` 出的 `fig1`–`fig7`、`fig5b`、`figS1`、`figS3` 保留作历史记录与快速核查；
其中 `fig4` 的面板 H 与 `fig2` 的面板 D 的标签问题已在 `main3`、`main1` 中重做，不要再用归档版投稿。

```powershell
python tools\make_figures.py                 # 全部
python tools\make_figures.py fig5 fig5b      # 单张
```

产物每张两种格式（投稿图集与归档图集同规则）：

| 格式 | 用途 |
|---|---|
| `figN.pdf` | **矢量、字体嵌入为 TrueType（`pdf.fonttype=42`）**，Science 接受 PDF/EPS 作为线图格式 |
| `figN.png` | 300 dpi，用于阅读、审阅、仓库展示 |

归档 10 张：`fig1`–`fig7`、`fig5b`（贝叶斯）、`figS1`（等效性）、`figS3`（贝叶斯设计上限）。
尺寸按期刊约定：单栏 3.5 in（`fig3`、`fig7`、`figS1`、`figS3`、`main2`、`supp2`–`supp4`），双栏 7.0 in（其余）；
字号 6–8 pt，去顶/右边框，误差棒一律 mean ± 95% CI，逐 trial 点用小黑点叠加。

**微调怎么做**（三种，按需要选）：
1. **改脚本再跑**——配色/面板/坐标轴都集中在 `tools/make_figures.py`（投稿图集另见 `tools/make_main_figures.py`，
   它 `import make_figures as MF` 复用同一套 `C`、`SHORT`、`save`）顶部的 `C`（Wong 色盲友好配色）、
   `SHORT`（刻度短标签）、`plt.rcParams`（字号/线宽）。改完重跑同一条命令即可。
2. **在矢量软件里改**——PDF 里的文字是真字体、可编辑；装 Inkscape（本机没装）即可打开 PDF/PNG 手调，
   再导 EPS/PDF 投稿。
3. **换数据**——把箭头指向别的 metric 名即可（脚本里每个面板只写 metric 名，列名见 `results/raw/*-trials.csv`）。

**必须写进图注的两件事**：① 刻度里的 `self*` 中的星号 = 该臂是操纵臂（无滑移身体斑块）；
② 误差棒 = 95% CI，n 见各图注，分析窗口 = 每 trial 后半段。

---

## 每个面板的数据来源（脚本已按此实现）

所有数据文件在 `results/raw/`。下面给出"每一格取哪一列、哪些臂、误差棒定义"，
便于你核对脚本输出，或自己换工具重画。

---

## Fig. 1 电路与读出

| 面板 | 数据 | 说明 |
|---|---|---|
| 1A | `circuit-schematic.md` §1 表 | 人群普查 + CX 亚family（ring 68 / columnar 1036 / fanbody 601 / other 369） |
| 1B | `circuit-schematic.md` §2 矩阵 | 人群间突触数（+兴奋/−抑制），用热图或气泡图 |
| 1C | `calibration-kappa-sweep.txt` | x = κ ∈ {100,200,300,500,1000}，左轴 CX 平均放电率、CXact%（同表最后一列），箭头指 κ=300 |
| 1D | `circuit-schematic.md` §4 | 朝向通路逐段计数：LPTC→ring 67、LPTC→columnar 58、columnar→ring 1031、ring→ring 1692、ring→fb 539、fb→DN 88、DN→motor 2810 |

## Fig. 2 操作与配平

| 面板 | 数据 | 说明 |
|---|---|---|
| 2A | `A3-flow-matching.csv`、`B3-heading-matching.csv` | 柱：`patch_cells`（0 / 723 / 723 / 353 / 723）；文字标注 `cx_input_synapses`（0 / 30919 / 13053 / 30958 / 30919）与 `ring_input_synapses` |
| 2B | 同两个 matching.csv | y = `delivered_ratio_vs_self`，x = 臂；加一条 y=1 参考线，并标 `expected`（A: 590096.5；B: 702528.9，所有臂相同） |
| 2C | `A3-flow-compare.csv` | 六个指标 × 五个臂的 `mean` ± `ci95_hi/lo`（cx_rate_hz, cx_active_fraction, ring_rate_hz, dim, pop_rate_sd_hz, bumpR） |
| 2D | `B3-heading-compare.csv` | 同上，换 B3 |

## Fig. 3 信号传播

| 面板 | 数据 | 说明 |
|---|---|---|
| 3A | `propagation.stdout.txt` 前 8 行 | x = hop（1,2,3），y = 累计 CX 到达比例（97.2 / 97.4 / 97.4 %）；标注 direct pool→CX = 48315 |
| 3B | `propagation.stdout.txt` 表 | 每行是一个 (κ, patch) 条件；画峰潜伏期 vs 峰值，或画 6 个条件的分组柱（peak/step 与 responsive_CX%） |

## Fig. 4 光流条件

| 面板 | 数据 | 说明 |
|---|---|---|
| 4A | `A3-flow-compare.csv` | 六指标 × 五臂 mean ± 95% CI（同 2C，可合并） |
| 4B | `A3-flow-pairs.csv` | y = `cohens_d`（self 为 arm_a 的行直接取；arm_b=self 的行取负），x = 对照臂；**按读数分两组**：率类（cx_rate_hz, ring_rate_hz, columnar_rate_hz, fanbody_rate_hz, other_rate_hz, pop_rate_sd_hz）与几何类（cx_active_fraction, dim, bumpR, pair_corr）；`randmat` 柱分别用不同填充表示"同 CX 输入损失" |

## Fig. 5 转圈条件

| 面板 | 数据 | 说明 |
|---|---|---|
| 5A | `B3-heading-compare.csv` | `cx_tuning_wire_corr` × 五臂 mean ± 95% CI |
| 5B | 同 | `ring_lag_yaw_deg` × 五臂（注意负号） |
| 5C | 同 | `ring_loop` 与 `ring_pc12_var` × 五臂 |
| 5D | `B3-heading-pairs.csv` | self vs 四个对照的 `cohens_d` + `p_welch_two_sided`，指标取 heading 六项；把 `decorr` 显著标出 |

## Fig. 6 剂量–反应

| 面板 | 数据 | 说明 |
|---|---|---|
| 6 上 | `C3-dose-dose-summary.csv` | `injected_events` vs `frac`（0, 0.125, 0.25, 0.5），证明配平 |
| 6 下 | 同 | 六个指标 vs `frac`，每个点标 `ci95_lo/hi` 与 n=10；面板内写 `spearman_rho` 与 `p_perm`（`C3-dose-dose-trend.csv`） |

## Fig. 7 阳性对照

| 面板 | 数据 | 说明 |
|---|---|---|
| 7A | `D-controls-compare.csv` | 臂 = self / drive0.5 / drive1.5，六指标 mean ± 95% CI |
| 7B | 同 | 臂 = self / synch，指标 = dim 与 pop_rate_sd_hz（这两个动），旁边并列 bumpR / cx_tuning_wire_corr（这两个不动） |
| 7C | `D-controls-pairs.csv` + `B3-heading-pairs.csv` | 同一读出（cx_tuning_wire_corr）三个对比条形：self−flow（d≈0，BF01 2.51）、self−decorr（d=2.93，BF10 3.3e3）、以及 drive1.5 的 cx_rate（d=−15.2，BF10 1.8e14） |

## Fig. 8（方法，可选）

| 面板 | 数据 | 说明 |
|---|---|---|
| 8 | `B-heading-trials.csv`（未配平）vs `B3-heading-trials.csv`（配平） | 同一对比的前后：cx_tuning_wire_corr 与 cx_rate 的 d 与 P；标注两轮的实际注入比值 0.99459 / 0.99751 / 0.89527 vs 0.99956 / 0.99971 / 1.00004 |

## 补充图

| 图 | 数据 |
|---|---|
| S1 | `circuit-schematic.md` 全文（简图 + Mermaid + 矩阵 + 通路） |
| S2 | `PathProbe` 输出（EPG 突触前伙伴排名、LPTC 目标排名、两跳中继） |
| S3 | `B3-heading-equivalence.csv`：每指标一行，画 Δ 的 90% CI 与两个等效界（`bound_d_raw` 与 `bound_pct_raw`），落在界内 = 支持等效 |
| S4 | 逐 trial 散点：`A3-flow-trials.csv`、`B3-heading-trials.csv` 的 `cx_rate_hz` / `cx_tuning_wire_corr` 按臂分色 |

---

## 误差棒与显著性标注的统一约定

- 误差棒一律 **mean ± 95% CI**（`compare.csv` 的 `ci95_lo/ci95_hi`），不用 SEM。
- 星号只用于 **Holm 校正后** 的 p：`*` < 0.05，`**` < 0.01，`***` < 0.001；原始 p 与置换 p 写进图注。
- 每个面板标注 n（10 trials/臂）与"analysis window = second half of each trial"。
- 贝叶斯因子只在表 1 与 Fig. 7C 出现，标 `BF01`（支持无差异）与 `BF10`（支持有差异），不要混用。
- 色盲友好：率类用一套蓝-橙，几何类用绿-紫；`randmat` 永不用与 `self` 同色（它是"同输入损失"的正对照）。
