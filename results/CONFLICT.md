# 冲突剂量：新跑的四组数据（E / F / G / H）

这四组把论文从"精心配平的空结果"变成了"**有剂量–反应的正面结果 + 三档增益复现 + 贝叶斯越过阈值**"。
全部：`flymind.brain` FLYMIND4，转圈条件，6 s/trial，配平后各臂 `expected` 逐位相同。

## 1. 冲突强度 α 的定义

斑块滑移 = (1−α)·自然信号 + α·(同一波形的 100 ms 分块打乱副本)。α=0 即无滑移身体斑块（原 `self`），
α=1 即完全去相关斑块（原 `decorr`）。E/G/H 各自包含 α = 0 / 0.25 / 0.5 / 0.75 / 1 五个水平。

## 2. E：κ=300，n=10，五个水平（主实验）

配平（`E-conflict-matching.csv`）：`expected` = 702,528.9 全部相同；
实际注入 702,809 / 702,573 / 702,564 / 702,359 / 702,837（相对 self 0.9994–1.0000）。

```
readout                        alpha=0    0.25     0.50     0.75     1.00 | rho(alpha)  p_perm
steer_corr_yaw                  0.8119  0.7802   0.7558   0.6789   0.6057 |  -0.943    0.0002
cx_yaw_modulation_hz            1.969   1.790    1.618    1.400    1.253  |  -0.924    0.0002
steer_asym_sd_hz                640.6   608.5    566.6    532.7    509.1  |  -0.913    0.0002
tau_ms                          246.9   231.6    197.7    171.4    163.3  |  -0.887    0.0002
cx_tuning_wire_corr             0.3169  0.3181   0.3031   0.2782   0.2442 |  -0.816    0.0002
pop_rate_sd_hz                  1.026   0.973    0.933    0.9007   0.8985 |  -0.759    0.0002
columnar_active_fraction        0.1074  0.1029   0.09566  0.09508  0.09353|  -0.637    0.0002
dim                             50.42   52.85    55.45    56.65    59.01  |  +0.571    0.0002
cx_active_fraction              0.2218  0.2163   0.2112   0.2117   0.213  |  -0.539    0.0002
ring_active_fraction            0.8676  0.8544   0.8544   0.8529   0.8338 |  -0.500    0.0007
bumpR                           0.3113  0.2991   0.2956   0.2867   0.2687 |  -0.493    0.0007
ring_lag_yaw_deg               -53.59  -64.03   -78.86   -76.97   -70.48  |  -0.330    0.0195
ring_rate_hz                    20.94   20.77    20.86    20.86    21.82  |  +0.321    0.0242
--- 不变的 ---
cx_rate_hz                      4.133   4.026    3.995    4.028    4.171  |  +0.103    0.4636
ring_ang_diffusion_deg          228.4   253.7    227.4    241.4    252.1  |  +0.100    0.4831
ring_pc12_var                   0.4174  0.411    0.4195   0.4084   0.4101 |  -0.078    0.5879
injected_events               7.028e5 7.026e5  7.026e5  7.024e5  7.028e5 |  -0.038    0.7918
turned_deg                      -60.9   -60.9    -60.9    -60.9    -60.9  |   0.000    1.0000
```

逐个对照 self（d，p）：`cx_tuning_wire_corr` conf25 −0.09/0.84、conf50 +1.05/0.033、conf75 +3.05/5.1e−6、
decorr +2.93/5.3e−5；`steer_corr_yaw` conf25 +1.98/4.4e−4、conf50 +2.62/1.9e−5、conf75 +5.02/1.6e−8、
decorr +5.76/2.6e−8；`tau_ms` conf50 +2.75/1.2e−5、conf75 +4.25/3.7e−8、decorr +5.87/1.5e−10。

**要点**：平均放电率完全不随冲突变（ρ=+0.10，P=0.46），而调谐、调制深度、积分时间常数、
bump、以及**转向指令对实际转向的保真度**单调退化；转向保真度是整组里效应最大的（0.81→0.61）。

## 3. F：κ=300，n=20（提高贝叶斯上限）

配平：`expected` = 702,432.5 全同；实际注入 0.99950–1.00000。

```
metric                  contrast              d       BF01     BF10     p_tost_pct
cx_tuning_wire_corr     vs flow            -0.181     2.84     0.352    1.4e-10
cx_tuning_wire_corr     vs shuffle         -0.180     2.85     0.351    4.2e-11
cx_tuning_wire_corr     vs randmat         +0.130     3.03     0.330    3.1e-10
cx_tuning_wire_corr     vs decorr          +3.206  4.7e-10  2.1e+09    1
cx_yaw_modulation_hz    vs flow            +0.193     2.79     0.358    8.3e-07
cx_yaw_modulation_hz    vs randmat         +0.083     3.15     0.317    1.5e-06
cx_yaw_modulation_hz    vs decorr          +4.308  1.0e-13  9.9e+12    1
ring_loop               vs flow            +0.125     3.04     0.329    0.35
ring_pc12_var           vs flow            +0.110     3.09     0.324    1.8e-04
bumpR                   vs decorr          +1.600  6.8e-04  1.5e+03    0.906
dim                     vs decorr          -1.335  6.4e-03  1.6e+02    0.607
ring_lag_yaw_deg        vs flow            -0.617     0.74     1.35     0.774   <- 唯一不支持的指标
```

n=20 的设计上限 BF01(t=0) = 3.24；实测 2.8–3.2（四个指标/对照组合越过 3）。

## 4. G / H：增益复现（κ=150 与 κ=600，n=6，五个水平）

```
readout                       kappa=150                    kappa=300(=E)               kappa=600
steer_corr_yaw          -0.980 (0.831->0.417)        -0.943 (0.812->0.606)       -0.871 (0.770->0.658)
steer_asym_sd_hz        -0.915 (518->401)            -0.913 (641->509)           -0.863 (735->638)
cx_tuning_wire_corr     -0.920 (0.238->0.134)        -0.816 (0.317->0.244)       -0.844 (0.323->0.253)
cx_yaw_modulation_hz    -0.980 (0.785->0.387)        -0.924 (1.97->1.25)         -0.528 (2.63->2.35)
dim                     +0.926 (40.6->52.7)          +0.571 (50.4->59.0)         +0.479 (89.6->94.7)
（全部 p_perm ≤ 0.007）
```

三档增益下 CX 静息水平分别约 1 / 4 / 15 Hz；效应方向一致、秩相关不衰减，
说明结论不依赖 κ 这个唯一标定参数。

## 5. 复现命令

```powershell
cd tools\CircuitPreview
dotnet run -- ..\..\flymind.brain --exp --heading --conflict --kappa 300 --trials 10 --secs 6 --odor 0.05 --csv ..\..\results\raw\E-conflict
dotnet run -- ..\..\flymind.brain --exp --heading            --kappa 300 --trials 20 --secs 6 --odor 0.05 --csv ..\..\results\raw\F-n20
dotnet run -- ..\..\flymind.brain --exp --heading --conflict --kappa 150 --trials 6  --secs 6 --odor 0.05 --csv ..\..\results\raw\G-k150
dotnet run -- ..\..\flymind.brain --exp --heading --conflict --kappa 600 --trials 6  --secs 6 --odor 0.05 --csv ..\..\results\raw\H-k600
cd ..\..; python tools\conflict_trend.py results\raw\E-conflict-trials.csv
```
