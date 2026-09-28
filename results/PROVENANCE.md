# 数据来源与管线（provenance）

本文件记录 `results/raw/` 里每一个数字是怎么来的：公开数据 → 本地文件（含 SHA256）→ 命令 → 输出。
不含解读，只含可核对的链条。所有 SHA256 为 SHA-256，长度单位为字节。

---

## 1. 公开数据来源

| 数据集 | 文件（发布名） | 本地文件 | 大小 | SHA256 |
|---|---|---|---:|---|
| MaleCNS v1.0 连接组（突触级） | `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | `malecns/connectome-weights.feather` | 1,051,241,946 | `E35DA783D1C686B2B58B3B87CD6A403AE43BFCFBA8BFF28E08EF752C1A56AFC1` |
| MaleCNS v1.0 细胞注释 | `body-annotations-male-cns-v1.0-minconf-0.5.feather` | `malecns/body-annotations.feather` | 14,483,314 | `2177E246113E4CFBF1E7772EC37C6DA1955FF22E8063D0B1F833101F99A9A3B2` |
| MaleCNS v1.0 递质预测 | `body-neurotransmitters-male-cns-v1.0.feather` | `malecns/body-neurotransmitters.feather` | 43,282,834 | `95C9289220663ABEB3409F3AD9E5A7F8A53F8093F5139D15502CD08DA8879621` |

发布桶：`gs://flyem-male-cns`，下载页 `https://male-cns.janelia.org/download`，
桶结构说明保存在本地 `downloads/README_RELEASE_BUCKET.md`（文件内自述版本为 `v0.9`，本地三个文件名为 `v1.0`）。
本机未保存逐文件下载 URL 日志；文件名中的版本号是唯一记录（见 §7）。

动力学模型：Shiu et al. 2024（`philshiu/Drosophila_brain_model`），本地副本
`drosophila-brain-model/model.py`（11,900 字节），常量见 §4。注：本目录下另有该仓库的
`Connectivity_783.parquet` / `sugarR.parquet` 下载尝试，本管线未使用。

## 2. 管线（每一步的命令与产物）

### 步骤 1 — Feather/Parquet → 纯文本 / 紧凑二进制

本机无 pandas / pyarrow / numpy（`pip` 不可用），故手写读取器：
`tools/feather_lite.py`（Arrow IPC/Feather：flatbuffer 遍历、按位打包字典索引、LZ4 frame linked block）
与 `tools/parquet_lite.py`。

| 命令 | 输入 | 输出 | 行数/边数 | SHA256 |
|---|---|---|---:|---|
| `python tools/export_edges.py` | `connectome-weights.feather` | `malecns/edges.bin` | 151,856,684 行 | `59E43C67EDF936B36330B58DAB05131F92D2A272BD8D032CAD026DB84117BD0D` |
| `python tools/export_annotations.py` | `body-annotations.feather` | `malecns/annotations.tsv` | 211,577 行 | `CEBDAADB7EBD88852E9CFFC055C85DE17E2DBE71991C8E951B63B4F7C7BF28B0` |
| `python tools/export_transmitters.py` | `body-neurotransmitters.feather` | `malecns/transmitters.tsv` | 164,401 行 | `8BB94778BFAE4842AB2C76CA8C4B7434B7300212695FF9A20CCDDC81073CBC0C` |

`edges.bin` 格式：`int64 行数` + 每行 `int64 pre, int64 post, int32 weight` = 20 字节
（3,037,133,688 字节 = 8 + 151,856,684 × 20）。
`annotations.tsv` 列：`bodyId  type  hemibrainType  somaLocation`（`somaLocation` = `x,y,z`，8 nm 体素）。
`transmitters.tsv` 列：`bodyId  transmitter`，来自 feather 的 `consensus_nt` 字段（值 `unclear` 的行不写出）。

递质标签分布（`python tools/export_transmitters.py --check`，不写文件）：
```
unclear 1671117 | acetylcholine 104193 | glutamate 29443 | gaba 22196
histamine 8024 | dopamine 396 | octopamine 101 | serotonin 48
```

### 步骤 2 — 回路切片 → `flymind.brain`

```powershell
cd tools\CircuitBuilder
dotnet run -- ..\..\malecns\edges.bin ..\..\malecns\annotations.tsv ..\..\flymind.brain 12000 1 ..\..\malecns\transmitters.tsv
```
输入：`edges.bin`、`annotations.tsv`、`transmitters.tsv`
输出：`flymind.brain`，21,383,125 字节，
SHA256 `FC6B544C84A082AE25A7AE704A36D0F065010EFFC6E4F4886EA877A5836E0C8A`
运行时间：约 130–145 s（打印在 stdout 末行）。

切片过程（源码 `tools/CircuitBuilder/Program.cs`）：
1. 按细胞类型正则选种子（`PopRules` / `SeedRules`），得 7,378 个种子；
2. 按"与已选集合的连接强度"迭代 1 轮补到 12,000 个神经元（62,923 个候选，打印于 stdout）；
3. 取两端都在集合内的边 = **1,615,753 条**（`maxSynapses = 2_000_000`，本回路未触发剪枝）；
4. 突触符号：突触前细胞 `consensus_nt` ∈ {gaba, glutamate, histamine} → 负；
5. 权重：`w_blob = (source_weight / 1000) × 0.275 mV`（`SourceWeightUnit = 1000`）；
6. 写入 FLYMIND4 blob（布局见 §5）。

### 步骤 3 — 三组数值实验

```powershell
cd tools\CircuitPreview
dotnet run -- ..\..\flymind.brain --sweep 100 200 300 500 1000 --secs 2 --odor 0.05
dotnet run -- ..\..\flymind.brain --pp
dotnet run -- ..\..\flymind.brain --asym --kappa 300 --secs 5 --yaw 0.6
dotnet run -- ..\..\flymind.brain --asym --kappa 300 --secs 5 --yaw 0.6 --patch
dotnet run -- ..\..\flymind.brain --exp            --kappa 300 --trials 10 --secs 3 --odor 0.05 --csv ..\..\results\raw\A-flow
dotnet run -- ..\..\flymind.brain --exp --heading  --kappa 300 --trials 10 --secs 6 --odor 0.05 --csv ..\..\results\raw\B-heading
```
输出：`results/raw/*.stdout.txt`（完整 stdout）、`A-flow-trials.csv`、`B-heading-trials.csv`
（每 trial 一行；列见下）、`A-flow-summary.csv`、`B-heading-summary.csv`。
每步生物学时间 0.5 ms；一次 trial 的步数 = `secs × 2000`；分析窗口 = 后半段；分箱 20 ms。

`*-trials.csv` 的列即第 3 步直接记录的每个量：`cx_rate_hz`（CX 平均放电率）、`cx_active_fraction`
（率 > 0.5 Hz 的 CX 细胞比例）、`ring_rate_hz` / `columnar_rate_hz` / `fanbody_rate_hz` / `other_rate_hz`
（四个 CX 亚family）、`pair_corr`（CX 内随机抽 300 对的平均 Pearson r，20 ms 分箱）、
`tau_ms`（群体态自相关时间，20 ms/bin 积分至 ACF < 0.05）、`dim`（参与率，由 bin 空间 Gram 矩阵特征值）、
`pop_rate_sd_hz`（群体平均率的时间标准差）、`bumpR`（EPG/PEG 活动加权群体向量长度）、
`injected_events`（该 trial 注入池的实际事件总数）、`pool_rate_hz`（视觉池放电率）。

heading 专用列：`ring_pc12_var`（环状态前两个主成分占的方差比例）、`ring_loop`（环状态轨迹角度的
合矢量长度）、`ring_track_gain_yaw` / `ring_lag_yaw_deg`（环状态角对 0.25 Hz yaw 分量的增益与相位差）、
`ring_track_gain_head` / `ring_lag_head_deg`（对积分朝向）、`cx_yaw_modulation_hz`（各细胞放电率对 yaw
回归斜率的平均绝对值）、`cx_tuning_wire_corr` / `ring_tuning_wire_corr`（各细胞 yaw 回归斜率与其推挽
权重 w 的 Pearson r）。`anat_gain_integral` / `anat_resid_deg` / `anat_gain_yaw` 是基于 soma 主轴环坐标的
旧读出，部分 trial 拟合不收敛（写出 NaN，比较脚本里剔除并计数）。

### 步骤 4 — 比较表

```powershell
python tools\compare_trials.py results\raw\A-flow-trials.csv
python tools\compare_trials.py results\raw\B-heading-trials.csv
```
输出：`*-compare.csv`（每 metric × 每 arm：n, mean, sd, sem, min, max, median, n_excluded_nonfinite）、
`*-pairs.csv`（每 metric × 每对 arm：mean_a, mean_b, diff, ratio, Cohen's d, Welch t, Welch df,
p_welch 双侧, p_perm 双侧）。Cohen's d 用合并标准差；Welch t 的 p 由正则化不完全 Beta 函数给出；
置换检验 `NP = 4000`，`SEED = 12345`，仅对含 `self` 的配对计算，分辨率下限 1/4001 = 0.0002499。
脚本不做任何取舍或筛选，非有限值只计数不插补。

### 步骤 5 — 电路简图

```powershell
cd tools\CircuitSchematic
dotnet run -- ..\..\flymind.brain ..\..\malecns\annotations.tsv ..\..\circuit-schematic.md
```
输出 `circuit-schematic.md`（17 KB）：人群普查、人群间连接矩阵、最强通路、朝向通路逐段计数、
扇入/扇出、以及每个细胞类型的 FlyWire Codex 检索链接。所有计数由 blob 现算。

### 步骤 6 — 全连接组通路追踪

```powershell
cd tools\PathProbe
dotnet run -- ..\..\malecns\edges.bin ..\..\malecns\annotations.tsv
```
单遍扫描全部 151,856,684 条边，输出：EPG/PEG 的突触前伙伴类型排名、LPTC 的突触后目标类型排名、
以及"既接收 LPTC 又投射到 EPG/PEG"的两跳中继细胞列表。默认正则 `^(EPG|PEG|EPGt)$` 与
`^(H1|H2|H3|HS|VS\d+|V1|LHAV|LHPV|JO-EV\d+).*`。

---

## 3. 每个量从哪来（source of truth）

| 量 | 来源 | 备注 |
|---|---|---|
| 神经元数 12,000 | 切片器参数（命令行第 4 个参数，下限 12,000） | `maxNeurons = Math.Max(maxNeurons, 12_000)` |
| 突触数 1,615,753 | 诱导子图计数 | blob `offsets[-1] = 1,615,753`（校验通过） |
| 抑制性突触 540,052（33.42%） | blob 中 `w < 0` 的计数 | 由突触前细胞 `consensus_nt` 决定 |
| 可塑性突触 3,206 | blob 的 KC→MBON 掩码求和 | `pop(KC) × pop(MBON)` 的边 |
| 每个突触的重量 | `(source_weight / 1000) × 0.275 mV` | 见 §5 的分布 |
| soma 坐标 | `annotations.tsv` 的 `somaLocation`（8 nm 体素）× 8 / 1000 → **µm** | 体素坐标全为正 |
| 细胞类型 | `annotations.tsv` 的 `type`（MaleCNS 命名）与 `hemibrainType` | 正则匹配的是 `type + " \| " + hemibrainType` |
| CX 亚family | 类型名正则（`CxFamilyRules`）：ring=`^(EPG\|PEG\|EPGt)`、columnar=`^(PFN\|PFR\|hDelta\|Delta\d\|vDelta)`、fanbody=`^FB\d`、其余 CX 归 other | 每个 CX 神经元必有 family，无空洞 |
| 左右侧（半球） | 对视觉池的 soma 坐标沿 x/y/z 各做一维 2-means，取组间方差占比最大的轴与其分界 | 打印：x 0.814 @365.9、y 0.561 @179.2、z 0.587 @194.8 → 取 x |
| 视觉池 2,689 | `self_motion`(1,594) ∪ `visualrelay`(1,122) | visualrelay 由连接组定义（见下） |
| visualrelay 1,095 | 回路内：`LPTC→x ≥ 3` 且（`x→ring ≥ 3` 或 `x→CX ≥ 3`） | 切片器计算并写入 blob |
| 身体斑块 723 | 视觉池中 soma 距池质心最近的 25%（`BodyFieldFraction = 0.25`） | 离线与游戏内同一规则 |
| 斑块削掉的 CX 输入 | 斑块细胞的出边中指向 CX 的计数 | 30,919（9.1%）/ 随机同大小 13,053（3.8%） |
| 推挽权重 w | 对每个 CX 细胞：`(A 侧兴奋 + B 侧抑制) − (B 侧兴奋 + A 侧抑制)` | A/B = 中线两侧 |
| 驱动脉冲 | 每步对池细胞做伯努利抽样，概率 = `150 Hz × 0.5 ms × level`；单次事件权重 `0.275 × 250 mV` | 论文的刺激协议 |
| κ = 300 | 连接组权重的全局倍数（不含刺激项） | 标定目标见 §4；扫描输出见 `calibration-kappa-sweep.txt` |

## 4. 模型常量

LIF（`tools/CircuitPreview/Program.cs` 与 `terraria-fly-mod/Neural/LifCircuit.cs`，逐字取自
`drosophila-brain-model/model.py` 第 22–52 行）：

```
V0 = VRst = -52 mV   VTh = -45 mV   Tmbr = 20 ms   Tau = 5 ms
TRfc = 2.2 ms        TDly = 1.8 ms  WSyn = 0.275 mV
r_poi = 150 Hz       f_poi = 250    r_poi2 = 0 Hz
dv/dt = (v0 - v + g)/t_mbr ;  dg/dt = -g/tau ;  发放时 v = v_rst, g = 0
```

数值积分：显式欧拉，`dt = 0.5 ms`；突触延迟用 `round(1.8/0.5) = 4` 步的环形缓冲；
`VMin = -70 mV` 为数值下限。

刺激协议（论文）：被刺激神经元的每个 Poisson 事件注入 `w_syn × f_poi = 68.75 mV`。
静息噪声：本实验关闭（`SpontaneousRateHz = 0`）；原生权重下 6 Hz × 0.275 mV 的背景
在 5 ms 内只累到约 0.008 mV（阈值 7 mV）。

κ 标定：扫描 κ ∈ {100, 200, 300, 500, 1000}，2 s/点，气味背景 0.05，无静息噪声，
有自然光流（每个 LPTC 以 150 Hz × 0.5 的概率被驱动）；
选取 κ = 300（CX 1.35 Hz、CX 活跃细胞 8.2%、全回路 57.5% 细胞有放电）。κ 只乘连接组权重，
不乘刺激事件权重，也不乘静息噪声。

实验参数：`--trials 10`，`--secs 3`（A）/ `--secs 6`（B），`--odor 0.05`，`--perm 4000`；
heading 模式的转圈指令为 `yaw(t) = 0.5·sin(2π·0.25t) + 0.3·sin(2π·0.6t + 0.7) + 0.12·U(−0.5,0.5)`，
`MaxTurnRateDeg = 200 °/s`，相位分析频率 `ProbeHz = 0.25 Hz`；
推挽：`level = 0.12 + 0.88·max(0, pref·yaw)`，斑块细胞 `level = 0.12`，其余按
`(n − 0.1·n_patch)/(n − n_patch)` 放大（`BodySlip = 0.1`）。

## 5. blob（FLYMIND4）二进制布局与一致性检查

```
magic       8s     "FLYMIND4"
uint32       n_neurons, n_synapses, 0
uint32       pop_counts[12]
uint32       seed_count[6]            sugar, motor, odor, selfmotion, centralcomplex, visualrelay
per neuron   24 B   uint64 body id | float32 soma x,y,z | uint8 population | uint8 cx family | 2 pad
CSR          uint32 offsets[n+1] ; uint32 targets[n_syn] ; float32 weights[n_syn]（带符号）
plasticity   uint8 kc_mbon_mask[n_syn] ; float32 base_weight[n_syn]
seeds        6 × uint32 索引数组
metadata     uint32 json_len + UTF-8 JSON
```

读取校验（直接读 `flymind.brain`）：

```
neurons 12000   synapses 1615753
pop_counts      (unknown 3802, sensory 2695, antennal_lobe 620, kenyon_cell 193,
                 dopamine 344, mbon 67, descending 119, motor 316, interneuron 0, vnc 0,
                 self_motion 1770, central_complex 2074)
seed_counts     sugar 60, motor 312, odor 5262, selfmotion 1770, centralcomplex 2074, visualrelay 1122
offsets[0] = 0, offsets[-1] = 1615753（= n_synapses），offsets 单调不减：True
targets 全部落在 [0, n)：True
|w| mV（未乘 κ）：min 0.000275  p25 0.000275  median 0.000550  p75 0.001650
                  max 0.530475  mean 0.001887
w < 0 的突触：540052 / 1615753 = 0.3342
可塑性掩码求和：3206
json: {"source":"MaleCNS v1.0 (Berg et al. 2026)","model":"Shiu et al. 2024 LIF, w_syn=0.275",
       "n_neurons":12000,"n_edges":1615753,"n_inhibitory_synapses":540052,
       "n_plastic_synapses":3206,"sign_source":"consensus_nt per presynaptic cell (GABA/glutamate/histamine negative)",
       "source_weight_unit":1000,"cx_subfamilies":{"ring":68,"columnar":1036,"fanbody":601,"other":369}}
```

## 6. 软件与运行环境

| 项 | 值 | 取得方式 |
|---|---|---|
| .NET SDK | 8.0.404 | `dotnet --version` |
| Python | 3.14.7 | `python --version` |
| tModLoader | 1.4.4.9+2026.07.3.0（stable） | 前序环境检查；本次未复核 |
| 依赖 | 无第三方包（纯标准库 / BCL） | 无 pip、无 NuGet 包引用 |
| 硬件 | 单机（Windows），单线程 | 未记录 CPU 型号 |

各步运行时间（stdout 自报）：回路切片 130–145 s（其中扫描 1.5 亿条边约 85 s）；
`--exp` A（6 臂 × 10 trials × 3 s）约 12 min；`--exp --heading` B（× 6 s）约 24 min；
`--pp` 约 40 s；`--asym` 每次约 30 s。

## 7. 无法从现有记录核实的项（引用时请勿当作已核实）

1. 三个 feather 的**逐文件下载 URL 与下载时刻**：本机只保留了文件名中的版本号（v1.0）与本地时间戳，
   没有 URL 日志。桶结构见 `downloads/README_RELEASE_BUCKET.md`（其正文自述版本为 v0.9）。
2. **下载完整性**：只有本地 SHA256（§1），没有发布方公布的校验和可比对。
3. `edges.bin` 中 `weight` 列的**语义**（连接强度、接触数、还是别的量纲）来自 MaleCNS 表的列定义，
   本管线只按 `weight / 1000 × w_syn` 使用，未做进一步核实。
4. **递质阈值**：`consensus_nt` 为 `unclear` 的 1,671,117 行未写出，视为无符号信息（按兴奋处理）；
   该阈值是发布方的 consensus 判定，不是本管线选的。
5. **tModLoader 构建**：`.tmod` 由 `dotnet build` 调用 tModLoader 构建；本次未复核其版本号。
6. 中途被修正的两次实现缺陷（会造成假结果，已修）：LIF 的 `g` 每步清零（应为 `dg/dt = −g/τ`），
   以及早前的突触预算剪枝（600k）。修正前后同一命令的输出不同，`results/raw/` 里保存的是修正后的输出。

> **Circuit rebuilt (see `results/CORRECTION.md`).** After the pool-definition fix the blob was
> rebuilt from the same released files and every experiment re-run: `flymind.brain` is now
> **21,383,125 bytes**, SHA256 `FC6B544C68B4C9997987E2BAA788A41ED8E4E91B3B5C60EBC1166947447827AB`
> (pre-fix blob kept as `malecns/flymind-before-poolfix.brain`). The visual pool is now
> **2,689 cells** = 1,594 lobula-plate tangential cells + 1,095 connectome-derived CX relay cells
> (previously 2,892 = 1,770 + 1,122, where the 1,770 wrongly included 176 Johnston's-organ
> `JO-EV*` cells). The reported families are `A4-flow`, `I2-heading`, `J2-n20`, `K2-k150`,
> `L600`-equivalents `L2-k600`, `M2-dose`, `D2-controls`, `P2-propagation`.
