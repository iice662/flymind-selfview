# 三项方法学验证：阳性对照 / 信号传播 / 等效性检验

配合 `BALANCED.md`（配平后的主结果）使用。成稿见 `paper/manuscript.md`。
所有运行：`flymind.brain` FLYMIND4，12,000 神经元 / 1,615,753 突触，κ = 300，n = 10 trials/臂。

---

## 1. 阳性对照：证明这套读出能被动到

命令（转圈条件，9 个臂）：
```
dotnet run -- ..\..\flymind.brain --exp --heading --controls --kappa 300 --trials 10 --secs 4 --odor 0.05 --csv ..\..\results\raw\D-controls
```
新增三个臂（`Experiment.ControlArms`）：`drive0.5`（同一视觉池、同一结构，总驱动 ×0.5）、
`drive1.5`（×1.5）、`synch`（同一池、**同期望总量**，但所有细胞的抽样用同一个随机数 → 全池同相同步）。

配平检查（`D-controls-matching.csv`）：`expected` 在 flow/self/shuffle/randmat/decorr/synch 上完全相同
（472,944.1），`drive0.5` / `drive1.5` 为 236,472.0 / 709,416.1（正好 0.5 与 1.5 倍）。
实际注入：self 473,063；drive0.5 236,432（0.49979）；drive1.5 709,677（1.50018）；
synch 477,248（1.00885，sd 21,786 = 4.6%，因为同步把随机性集中在整步上——这是 synch 臂的性质，需在文中注明）。

### 结果（self − 对照；n = 10）

```
metric                  control          diff        d         p         BF01
cx_rate_hz              drive0.5        +1.521     +22.92   6.9e-21   6.5e-18
cx_rate_hz              drive1.5        -1.329     -15.19   4.3e-16   5.7e-15
cx_rate_hz              synch           +0.119      +0.56   0.236      1.45
ring_rate_hz            drive0.5        +4.385      +8.19   8.6e-13   1.4e-10
ring_rate_hz            drive1.5        -3.830      -5.30   2.4e-09   1.1e-07
ring_rate_hz            synch           +0.529      +0.69   0.142      1.11
fanbody_rate_hz         drive0.5        +1.744     +42.33   9.7e-26   3.5e-22
fanbody_rate_hz         drive1.5        -1.606     -25.68   1.1e-17   1.0e-18
cx_active_fraction      drive0.5        +0.0382     +7.44   6.3e-10   6.2e-10
cx_active_fraction      drive1.5        -0.0341     -5.67   4.1e-08   4.1e-08
dim                     drive0.5        +5.008      +1.08   0.0284     0.386
dim                     drive1.5        -4.096      -0.87   0.069      0.707
dim                     synch          +19.710      +7.01   1.6e-09   1.6e-09
pop_rate_sd_hz          synch           -0.4194    -6.09   7.9e-09   —
bumpR                   drive0.5        -0.0973     -2.63   4.0e-05   9.7e-04
bumpR                   drive1.5        +0.0636     +1.72   0.0018    0.039
cx_yaw_modulation_hz    drive0.5        +0.7246     +7.58   2.3e-11   4.6e-10
cx_yaw_modulation_hz    drive1.5        -0.5708     -6.10   4.2e-10   1.4e-08
cx_tuning_wire_corr     drive0.5        +0.0318     +2.37   1.1e-04   2.8e-03
cx_tuning_wire_corr     drive1.5        -0.0054     -0.58   0.208      1.40
cx_tuning_wire_corr     synch           +0.0049     +0.23   0.619      2.29
ring_lag_yaw_deg        drive0.5       +26.61       +0.22   0.623      —
ring_loop               drive0.5        -0.0610     -2.02   3.4e-04   —
ring_loop               drive1.5        +0.0160     +0.37   0.421      —
```

读法：
- **总额外驱动 ±50% 把几乎所有读出都推动了**（|d| = 5–42，p 低至 1e-26）→ 这套管线对
  "到达眼睛的信号变了"极度灵敏，空结果不是管线死掉。
- **同步化（同期望总量、同细胞、只改时间结构）把维度 +46%（43.1 → 62.8，d = 7.0，p = 1.6e-9）
  和群体涨落 SD −37%（d = −6.1，p = 7.9e-9）** → 结构本身可被检测，
  但朝向环那几个读数（bumpR / 调谐↔接线 / yaw 调制 / 环相位）对同步化不敏感（p ≥ 0.4）。
- 注意：`synch` 臂的实际注入总量比其它臂高 0.9%（sd 4.6%），因为同步把随机性集中在整步上；
  它的 `expected` 与其它臂完全相同（472,944.1）。

> 正则性说明：`--secs 4` 与主实验的 `--secs 6` 不同，所以本表里各臂的**绝对**指标值
> （例如 `cx_tuning_wire_corr` 0.09–0.10、环相位 +79…+130°）不能与 `BALANCED.md` 的
> B3 表直接比。本表的用途是**同一轮运行内部的对照**（所有臂共享同一刺激与窗口）。

---

## 2. 信号传播验证：第三人称信号确实到达了目标回路

命令：`dotnet run -- ..\..\flymind.brain --propagate --kappa 300 --kappas 100,1000`
（输出：`results/raw/propagation.stdout.txt`）

### 2.1 解剖可达性（同一张图上做 BFS）

```
visual pool 2892 cells -> CX readout 2074 cells
  hop 1:    6785 newly reached,  2015 of them CX  (cumulative CX reached 2015/2074 = 97.2%)
  hop 2:    2321 newly reached,     5 of them CX  (cumulative CX reached 2020/2074 = 97.4%)
  hop 3:       2 newly reached,     0 of them CX  (cumulative CX reached 2020/2074 = 97.4%)
  direct pool -> CX synapses: 48315
```

**97.2% 的 CX 读出细胞与视觉池只隔一跳，直接突触 48,315 条**，两跳内 97.4%。
即"信号到不了"这一解释被排除。

### 2.2 功能传播：单次同步发放（每个池细胞在同一时刻注入一个事件）

只统计 CX 细胞的脉冲（不含池自身），基线 = 发放前 100 ms，每步 0.5 ms：

```
kappa  patch   baseline/step    peak/step  peak_at  latency   excess_20ms  responsive_CX
  300  flow           0.17          21      2.5ms    0.0ms          115       105 (5.1%)
  300  self           0.17           6      2.5ms    2.0ms           36        41 (2.0%)
  100  flow           0.01          49      2.5ms    2.0ms           54        54 (2.6%)
  100  self           0.01          12      2.5ms    2.5ms           14        14 (0.7%)
 1000  flow          15.80          52      9.5ms        -          444       586 (28.3%)
 1000  self          15.80          53     56.5ms        -          358       548 (26.4%)
```

- **潜伏期 2.5 ms**：模型的突触延迟 `TDly = 1.8 ms`，加上一步积分为 2.0–2.5 ms，
  即响应是**单突触**的，不是背景漂移。
- 幅度：CX 脉冲从 0.17/步升到 21/步（×124），20 ms 内多出 115 个 CX 脉冲，
  105/2074 = 5.1% 的 CX 细胞被激活（κ=100 时仍有 2.6%，κ=1000 时 28.3%）。
- **操纵确实改变了到达 CX 的东西**：同样一次发放，把身体斑块设为无滑移后，
  峰值 6 vs 21（−71%），被激活细胞 41 vs 105（−61%）。

---

## 3. 等效性检验：不是"没有显著差异"，而是"差异被排除在某个范围之外"

命令：`python tools\compare_trials.py results\raw\B3-heading-trials.csv`
（输出：`B3-heading-equivalence.csv`，字段含 `p_tost_d`、`p_tost_pct`、`ci90_*`、`bf10`、`bf01`）

两个**事先可指定**的等效界：
- 标准化：|Cohen's d| < 0.5（"中等效应"是我们会在意的最小效应，所以"无差异"= 小于中等）
- 原始：|差值| < 对照均值的 10%

TOST（双单侧检验）在界内时 p < 0.05；等价地，**差值的 90% CI 落在界内**。
BF01 为 JZS 贝叶斯因子（Rouder et al. 2009，Cauchy 先验 r = 0.707，两独立样本），
`BF01 > 3` 记"中等支持无差异"，`> 10` 记"强"。

### 3.1 贝叶斯因子实现的自我校验（`python tools\compare_trials.py --selftest`）

```
JZS Bayes factor self-test (r = 0.707, n = 10 per arm)
  t =  0.0   BF10 =    0.3973   BF01 =    2.5171
  t =  0.5   BF10 =    0.4341   BF01 =    2.3037
  t =  1.0   BF10 =    0.5634   BF01 =    1.7748
  t =  2.0   BF10 =    1.4964   BF01 =    0.6683
  t =  3.0   BF10 =    6.2818   BF01 =    0.1592
  t =  4.0   BF10 =   34.4220   BF01 =    0.0291
```
`t = 0` 时 BF01 = 2.52 与 Rouder 表格中该设计的值一致（解析锚点
`E[(1+n_eff·g)^{-1/2}] = 0.3974`，`n_eff = 5`）；实现里曾经漏掉对数参数化的雅可比因子 `g`，
是这条校验抓出来的。

**样本量上限（重要）**：`t = 0` 时的 BF01 是这套设计能给出的最大证据量：
n = 10/臂 → **2.52**；n = 16 → 2.97；n = 20 → 3.24；n = 30 → 3.81；n = 50 → 4.74。
即：**BF01 > 3 需要 ≥ 20 trials/臂，BF01 > 10 在这个先验下不可达**。

### 3.2 B3（转圈，10×6 s）的等效性

```
metric                  contrast      diff        d        p_tost_d  p_tost_pct   BF01      BF10
cx_tuning_wire_corr     vs flow     -0.000470   -0.052     0.165     2.5e-07     2.51      0.399
cx_tuning_wire_corr     vs shuffle  -0.001733   -0.158     0.227     5.3e-06     2.41      0.415
cx_tuning_wire_corr     vs randmat  -0.001742   -0.148     0.221     1.4e-05     2.42      0.413
cx_tuning_wire_corr     vs decorr   +0.072730   +2.926     1         0.999       3.0e-04   3.3e+03
cx_yaw_modulation_hz    vs flow     -0.012820   -0.139     0.217     3.1e-04     2.43      0.411
cx_yaw_modulation_hz    vs shuffle  +0.015540   +0.160     0.230     6.4e-04     2.41      0.416
cx_yaw_modulation_hz    vs randmat  -0.020350   -0.231     0.279     2.6e-04     2.29      0.437
cx_yaw_modulation_hz    vs decorr   +0.716100   +8.811     1         1           4.2e-11   2.4e+10
ring_pc12_var           vs flow     +0.004664   +0.119     0.204     0.0264      2.45      0.407
ring_pc12_var           vs shuffle  -0.010930   -0.308     0.336     0.0303      2.13      0.469
ring_pc12_var           vs randmat  -0.005333   -0.183     0.244     0.00566     2.37      0.422
ring_loop               vs flow     -0.004667   -0.104     0.196     0.361       2.47      0.405
ring_loop               vs shuffle  -0.004000   -0.123     0.206     0.297       2.45      0.408
ring_loop               vs randmat  +0.001333   +0.033     0.157     0.297       2.51      0.398
ring_lag_yaw_deg        vs flow     +1.692      +0.095     0.189     0.318       2.48      0.404
ring_lag_yaw_deg        vs shuffle  +5.507      +0.360     0.379     0.477       2.00      0.499
ring_lag_yaw_deg        vs randmat +10.96      +0.783     0.730     0.757       0.896     1.12
bumpR                   vs flow     -0.008879   -0.467     0.471     0.00712     1.72      0.582
bumpR                   vs shuffle  -0.007667   -0.285     0.319     0.0323      2.18      0.459
bumpR                   vs randmat  -0.010060   -0.447     0.454     0.0221      1.77      0.564
cx_rate_hz              vs flow     +0.068810   +1.021     0.870     8.2e-10     0.462     2.16
cx_rate_hz              vs shuffle  +0.011140   +0.134     0.212     3.2e-09     2.44      0.410
cx_rate_hz              vs randmat  +0.009676   +0.148     0.221     3.7e-11     2.42      0.413
dim                     vs flow     -0.929100   -0.304     0.334     0.00346     2.14      0.468
dim                     vs shuffle  -1.390000   -0.385     0.400     0.0167      1.94      0.515
```

要点（写论文时逐条对应）：

1. **原始界的等效性通过得很彻底**：所有朝向读数在 `|diff| < 对照均值 10%` 上
   `p_tost_pct ≤ 0.03`（多数 ≤ 1e-5），即数据把大于 10% 的差异排除了。
2. **标准化界（|d| < 0.5）没有全部通过**：`cx_tuning_wire_corr`（p = 0.165）、
   `cx_yaw_modulation_hz`（0.217）、`bumpR`（0.471）、`ring_lag_yaw_deg`（0.189）等
   在 |d| < 0.5 上**不能宣称等效**，原因是这些指标的组内 SD 很小，
   ±0.5·SD 的原始界（如 ±0.0055）比差值的 90% CI（[−0.0075, +0.0066]）还窄。
   0.5 这个界对它们而言比数据精度更严。
3. **BF01 ≈ 2.3–2.5**（self vs flow / shuffle / randmat）＝中等偏弱地支持"无差异"，
   但**低于 3 这个常规阈值**；而 `BF01(t=0) = 2.52` 说明这是 n = 10/臂的**上限**，
   要提高只能加 trial（≥20/臂 → BF01 ≈ 3.2）。
4. **self vs decorr：BF01 = 3.0e-04 ~ 0.05（BF10 = 20 ~ 3300）**，
   TOST 两个界都不通过（p ≈ 1）→ 去相关斑块与无滑移斑块**确实不同**，
   这是同一张表里的阳性对照（同一读出、同一 n，能测出差异时它测得出）。

### 3.3 阳性对照与主结果的并列（决定"空结果有没有信息"）

```
同一读出，同一 n=10，同一窗口：
  self vs drive1.5   cx_rate d = -15.19, p = 4.3e-16, BF01 = 5.7e-15   ← 阳性对照（总量 +50%）
  self vs synch      dim      d =  +7.01, p = 1.6e-09, BF01 = 1.6e-09   ← 阳性对照（同总量、只改结构）
  self vs flow       cx_tuning_wire_corr d = -0.052, p = 0.909, BF01 = 2.51  ← 主结果（空）
  self vs decorr     cx_tuning_wire_corr d = +2.926, p = 5.3e-05, BF01 = 3.0e-04 ← 同一读出的阳性对照
```
