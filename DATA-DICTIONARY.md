# Data dictionary

Every number in the manuscript comes from `flymind.brain` (the circuit) or from the per-trial
CSVs in `results/raw/`. This file names every column so the analysis can be re-derived without
reading the code.

## 1. `flymind.brain` — the circuit blob (FLYMIND4)

Flat binary, 21,383,125 bytes, SHA256 `FC6B544C84A082AE25A7AE704A36D0F065010EFFC6E4F4886EA877A5836E0C8A`.
Written by `tools/CircuitBuilder`, read by `CircuitPreview` / `CircuitSchematic`.

| block | type | meaning |
|---|---|---|
| header | magic `FLYMIND4`, int32 version | format tag |
| N | int32 | neurons (12,000) |
| per neuron | int32 bodyId, int8 pop, int8 cxFamily, float x,y,z, float plasticBase | MaleCNS body id; population code; CX subfamily code; soma position (blob units, from the release annotation); plastic base weight |
| S | int32 | synapses (1,615,753) |
| per synapse | int32 pre, int32 post, int16 count, int8 sign, float w | presynaptic index, postsynaptic index, synapse count, sign (+1 excitatory / −1 inhibitory), base weight (count/1000) |
| P | int32 | odour cells |
| … | int32 indices | the odour-context population |

Population codes: 0 sensory, 1 antennal, 2 KC, 3 dopamine, 4 MBON, 5 descending (DN),
6 motor, 7 LPTC, 8 CX, 9 unnamed. CX subfamily codes (only meaningful for pop = 8):
0 not-CX, 1 ring EPG/PEG, 2 columnar (PFN/PFR/hDelta), 3 fan-body (FB), 4 other (LAL/IB/ER/TuBu).

## 2. `results/raw/<family>-trials.csv` — one row per trial

The unit of analysis. `<family>` ∈ {`A-flow`, `A2-flow`, `A3-flow`, `B-heading`, `B2`, `B3`,
`C-dose`, `C2`, `C3-dose`, `D-controls`, `E-conflict`, `F-n20`, `G-k150`, `H-k600`,
`I-heading`, `J-n20`, `K-k150`, `L-k600`, `M-dose`}.

| column | unit | meaning |
|---|---|---|
| `arm` | — | experimental arm id (see §5) |
| `trial` | — | trial index within the arm (independent seed / stimulus stream) |
| `pool_rate_hz` | Hz | mean firing rate of the 2,689-cell visual pool (manipulation check) |
| `injected_events` | count | stimulation events actually delivered to the pool |
| `cx_rate_hz` | Hz | mean firing rate over the 2,074 CX cells |
| `cx_active_fraction` | — | fraction of CX cells above 0.5 Hz |
| `ring_rate_hz` | Hz | mean rate, ring EPG/PEG (68 cells) |
| `columnar_rate_hz` | Hz | mean rate, columnar CX (1,036 cells) |
| `fanbody_rate_hz` | Hz | mean rate, fan-body CX (601 cells) |
| `other_rate_hz` | Hz | mean rate, remaining CX (369 cells) |
| `*_active_fraction` | — | as above, per subfamily |
| `pair_corr` | r | mean pairwise correlation over 300 sampled CX pairs |
| `tau_ms` | ms | integrated autocorrelation time (Σ ACF to 0.05) |
| `dim` | — | participation ratio of the bin-space Gram matrix (effective dimensionality) |
| `pop_rate_sd_hz` | Hz | SD of the population-mean rate across 20 ms bins |
| `bumpR` | — | ring population-vector amplitude in the soma-derived ring plane |
| `patch_drive_fraction` | — | **manipulation check**: share of the total drive that reached the body-patch cells (0 for arms without a patch) |
| `patch_level_ratio` | — | **manipulation check**: mean patch level ÷ mean surround level. A body-locked patch must sit clearly below the natural value (≈1.0) |
| `anat_gain_integral` | — | ring bump angle regressed on the integrated heading (anatomical ring plane) |
| `anat_resid_deg` | ° | residual of that fit |
| `anat_gain_yaw` | — | ring bump angle regressed on the yaw command |
| `turned_deg` | ° | heading actually integrated over the analysis window |
| `ring_pc12_var` | — | fraction of ring-state variance in its own top-2 PCs |
| `ring_loop` | — | 1 = the state circles the PC-plane origin (a ring) |
| `ring_track_gain_yaw` | — | ring rotation per unit yaw at the drive frequency |
| `ring_lag_yaw_deg` | ° | phase lag of the ring state behind the yaw command |
| `ring_track_gain_head` / `ring_lag_head_deg` | —, ° | same against the integrated heading |
| `cx_yaw_modulation_hz` | Hz | mean \|d(rate)/d(yaw)\| over CX cells |
| `cx_tuning_wire_corr` | r | **primary heading readout**: correlation across CX cells between the yaw-tuning slope and the push–pull weight implied by the connectome |
| `ring_tuning_wire_corr` | r | the same restricted to the ring |
| `ring_ang_diffusion_deg` | ° | SD of the ring-state angle about its best linear trend |
| `ring_ang_ac1` | — | lag-1 autocorrelation of that angle |
| `steer_corr_yaw` | r | **behavioural readout**: correlation between the descending left–right asymmetry and the yaw command |
| `steer_asym_sd_hz` | Hz | SD of that asymmetry (steering amplitude) |
| `dn_rate_hz` | Hz | mean descending-neuron rate |

## 3. `-compare.csv` — descriptive statistics per metric per arm

`metric, arm, n, mean, sd, sem, ci95_lo, ci95_hi, min, q1, median, q3, max, n_excluded_nonfinite`.
`sem` is reported for completeness; every figure and table uses the 95% CI.

## 4. `-pairs.csv` — every pairwise contrast

`metric, arm_a, arm_b, n_per_arm, mean_a, mean_b, diff_a_minus_b, diff_ci95_lo, diff_ci95_hi,
ratio_a_over_b, cohens_d, d_ci95_lo, d_ci95_hi, hedges_g, welch_t, welch_df, p_welch_two_sided,
p_holm_self_family, mannwhitney_U, mw_z, p_mannwhitney_two_sided, rank_biserial,
p_perm_two_sided`. `p_holm_self_family` Holm-corrects within each metric's family of
self-vs-control contrasts.

## 5. `-equivalence.csv` — TOST and Bayes factors

`metric, contrast, n, mean_self, mean_ctrl, diff, se, df, cohens_d, sesoi_d, bound_d_raw,
p_tost_d, ci90_lo_d, ci90_hi_d, sesoi_pct, bound_pct_raw, p_tost_pct, ci90_lo_pct, ci90_hi_pct,
bf10, bf01`. Two pre-specified equivalence bounds: standardised (\|d\| < 0.5) and relative
(±10% of the control mean). Bayes factors are JZS two-sample with a Cauchy prior of scale
r = 0.707, validated against the analytic anchor at t = 0 (`python tools/compare_trials.py
--selftest`).

## 6. `-matching.csv` — the drive-matching audit

`arm, patch_cells, cx_input_synapses, ring_input_synapses, delivered_events_mean,
delivered_ratio_vs_self, delivered_sd`. `delivered_ratio_vs_self` must be 1.000 ± 0.001 for
every arm: this is the file that exposed the drive-matching artefact (Fig. S4).

## 7. `-summary.csv`, `-trend.csv`, `-report.txt`, `*.stdout.txt`

- `-summary.csv`: per-metric mean/sd/sem per arm plus the self-vs-control d and permutation P in
  one row per metric.
- `-trend.csv` (`C*`, `M-dose`): Spearman ρ of each metric against the patch fraction, with a
  permutation P (4,000 relabellings, seed 12345).
- `-report.txt`: the full human-readable report of one run (all contrasts, all metrics).
- `*.stdout.txt`: the complete console output of the run that produced the family, including the
  manipulation check of §2.

## 8. Arm ids

| id | drive mode |
|---|---|
| `rest` | no visual drive (background odour only) |
| `flow` | natural: the whole eye sees world optic flow |
| `self` | body-locked patch: the body region carries `BodySlip` = 10% of the world's slip (α = 0) |
| `shuffle` | same patch size and drive, random identity (breaks spatial coherence) |
| `randmat` | random identity, resized to remove the same number of CX input synapses (3.8% vs 9.1%) |
| `decorr` | same patch, signal replaced by a 100 ms block-shuffled copy of the waveform (α = 1) |
| `conf25` / `conf50` / `conf75` | patch slip = (1−α)·body slip + α·shuffled copy, α = 0.25 / 0.5 / 0.75 |
| `drive0.5` / `drive1.5` | positive control: total drive ×0.5 / ×1.5 |
| `synch` | positive control: same expected total, all cells in phase |
| `frac0` / `frac0.125` / `frac0.25` / `frac0.5` | patch-size dose (`--dose`) |

> **Circuit rebuilt (see `results/CORRECTION.md`).** After the pool-definition fix the blob was
> rebuilt from the same released files and every experiment re-run: `flymind.brain` is now
> **21,383,125 bytes**, SHA256 `FC6B544C68B4C9997987E2BAA788A41ED8E4E91B3B5C60EBC1166947447827AB`
> (pre-fix blob kept as `malecns/flymind-before-poolfix.brain`). The visual pool is now
> **2,689 cells** = 1,594 lobula-plate tangential cells + 1,095 connectome-derived CX relay cells
> (previously 2,892 = 1,770 + 1,122, where the 1,770 wrongly included 176 Johnston's-organ
> `JO-EV*` cells). The reported families are `A4-flow`, `I2-heading`, `J2-n20`, `K2-k150`,
> `L600`-equivalents `L2-k600`, `M2-dose`, `D2-controls`, `P2-propagation`.
