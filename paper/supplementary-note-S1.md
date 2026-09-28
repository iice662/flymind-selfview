# Supplementary Note S1 — Provenance, balancing derivation, and analysis self-checks

Companion to `paper/manuscript.md`. Every number in the manuscript is regenerated from one
file, `flymind.brain` (FLYMIND4), by the commands listed here. This note is the reproducibility
half of the paper; `results/PROVENANCE.md` holds the full-length version including file hashes.

---

## S1.1 Source data

| dataset | released file | local file | bytes | SHA256 |
|---|---|---|---|---|
| MaleCNS v1.0 flat connectome | `connectome-weights-male-cns-v1.0-minconf-0.5.feather` | `malecns/connectome-weights.feather` | 1,051,241,946 | `E35DA783D1C686B2B58B3B87CD6A403AE43BFCFBA8BFF28E08EF752C1A56AFC1` |
| MaleCNS v1.0 annotations | `body-annotations-male-cns-v1.0-minconf-0.5.feather` | `malecns/body-annotations.feather` | 14,483,314 | `2177E246113E4CFBF1E7772EC37C6DA1955FF22E8063D0B1F833101F99A9A3B2` |
| MaleCNS v1.0 transmitter predictions | `body-neurotransmitters-male-cns-v1.0.feather` | `malecns/body-neurotransmitters.feather` | 43,282,834 | `95C9289220663ABEB3409F3AD9E5A7F8A53F8093F5139D15502CD08DA8879621` |

Release bucket `gs://flyem-male-cns`; download page `https://male-cns.janelia.org/download`.
Derived intermediates: `malecns/edges.bin` (3,037,133,688 bytes; int64 count + 151,856,684 rows
of 20 bytes, SHA256 `59E43C67…17BD0D`), `malecns/annotations.tsv` (211,577 rows),
`malecns/transmitters.tsv` (164,401 rows). Feather/Parquet were read with purpose-written pure
Python readers (`tools/feather_lite.py`, `tools/parquet_lite.py`); no third-party dependency is
used anywhere in the pipeline.

## S1.2 Pipeline

```
export_edges.py / export_annotations.py / export_transmitters.py      (Python 3.14.7)
        ↓  edges.bin, annotations.tsv, transmitters.tsv
CircuitBuilder            (C#, .NET 8.0.404)  →  flymind.brain  (FLYMIND4, 21,383,125 bytes,
                                                  SHA256 FC6B544C…836E0C8A, ≈140 s)
        ↓
CircuitPreview --exp / --dose / --pp / --asym / --propagate          → per-trial CSV + stdout
        ↓
compare_trials.py         → descriptive stats, pairwise tests, equivalence + Bayes factors
```

Exact commands for every table are in `results/raw/00-commands.txt`.

## S1.3 Circuit blob (FLYMIND4)

```
magic       8s     "FLYMIND4"
uint32       n_neurons, n_synapses, 0
uint32       pop_counts[12]
uint32       seed_count[6]        sugar, motor, odor, selfmotion, centralcomplex, visualrelay
per neuron   24 B   uint64 body id | float32 soma x,y,z (µm) | uint8 population | uint8 cx family | 2 pad
CSR          uint32 offsets[n+1] ; uint32 targets[n_syn] ; float32 weights[n_syn]  (signed)
plasticity   uint8 kc_mbon_mask[n_syn] ; float32 base_weight[n_syn]
seeds        6 × uint32 index arrays
metadata     uint32 json_len + UTF-8 JSON
```

Integrity checks executed on load: `offsets[0] = 0`, `offsets[-1] = n_synapses` (1,615,753),
offsets monotone non-decreasing, all targets inside `[0, n)`. Native weight distribution
(|w| before κ): min 0.000275, p25 0.000275, median 0.000550, p75 0.001650, max 0.530475,
mean 0.001887 mV; 540,052 of 1,615,753 synapses negative (33.42%); 3,206 KC→MBON synapses
flagged plastic.

## S1.4 Eq. S1 — per-step drive balancing

Let the visual pool have *n* cells, split into the body patch *B* (|B| = ρn) and the surround
*S*. The natural condition delivers level d⁰ᵢ = f(t) to every cell, where f(t) is the optic-flow
or rectified-yaw drive. The manipulation replaces the patch's drive by ρ·g(t), where g(t) is the
patch's own signal (identical to f(t) for `self`, a block-shuffled copy for `decorr`, or the
blend (1−α)f + α·g for the conflict-dose arms). The surround level s is solved from the levels
actually delivered in that step:

  Σᵢ dᵢ = Σ_{B} ρ·g + s·Σ_{S} f = Σ_{all} f     ⇒     s = ( Σ_{all} f − Σ_{B} ρ·g ) / Σ_{S} f

and the patch is capped so that it can never absorb more than the whole budget,
ρ·g ← ρ·g·min(1, Σ_{all} f / Σ_{B} ρ·g), which is exact because the rectifier is linear in a
non-negative factor. Injection is then Bernoulli per cell with pᵢ = 150 Hz·Δt·dᵢ (p clamped at 1,
levels are not; p_max = 0.075 so levels up to ≈13 are representable). Three consequences, all
verified in the matching tables: the *expected* event total is identical in every arm, the
realised totals differ only by Bernoulli noise, and no arm can deliver more than the natural
condition. The stimulus waveform, its shuffled copy, the odour background and the sampled CX
pairs are drawn from one shared stream per trial index (`Random(90000 + trial)`); arm-specific
streams are used only for the pool draws.

## S1.5 Bayes-factor self-check

`python tools/compare_trials.py --selftest` prints the JZS two-sample Bayes factor
(Cauchy prior scale r = 0.707) against the analytic anchor at t = 0:

```
t = 0.0  BF10 = 0.3973  BF01 = 2.5171     (analytic: 1/E[(1+n_eff g)^(-1/2)] = 1/0.3974, n_eff = 5)
t = 1.0  BF10 = 0.5634  BF01 = 1.7748
t = 2.0  BF10 = 1.4964  BF01 = 0.6683
t = 4.0  BF10 = 34.4220 BF01 = 0.0291
```

Design ceiling (BF01 at t = 0 against trials per arm): n = 10 → 2.52; 16 → 2.97; 20 → 3.24;
30 → 3.81; 50 → 4.74. This is the maximum evidence for the null that this design can produce,
and it is why the manuscript reports the Bayes factor together with the equivalence tests rather
than either alone.

## S1.6 File index for the reported numbers

| manuscript element | file |
|---|---|
| Fig. 1A–1C, circuit census / calibration / pathways | `circuit-schematic.md`, `results/raw/calibration-kappa-sweep.txt` |
| Fig. 1D–1F, manipulation and balancing | `results/raw/A3-flow-matching.csv`, `B3-heading-matching.csv` |
| Fig. 2, propagation | `results/raw/propagation.stdout.txt` |
| Fig. 3, optic flow | `results/raw/A3-flow-{compare,pairs,trials,summary}.csv` |
| Fig. 4, yaw null + conflict dose | `results/raw/B3-heading-*`, `E-conflict-*`, `F-n20-*` |
| Fig. 5A, flat rate and drive | `results/raw/E-conflict-{trials,summary}.csv` |
| Fig. 5B, gain replication | `results/raw/G-k150-*`, `H-k600-*` |
| Fig. 5C, Bayes factors at n = 20 | `results/raw/F-n20-equivalence.csv` |
| Fig. S1, patch-size dose and positive controls | `results/raw/C3-dose-dose-*`, `D-controls-*` |
| Fig. S2, equivalence bounds | `results/raw/F-n20-equivalence.csv` |
| Fig. S3, Bayes-factor design ceiling | `tools/make_main_figures.py` (`supp3`), analytic anchor in §S1.5 |
| Fig. S4, the drive-matching trap | `results/raw/B-heading-trials.csv` (unbalanced) vs `B3-heading-trials.csv` |
| Table 1 (n = 10 equivalence) | `results/raw/B3-heading-equivalence.csv` |
| Table 2 (n = 20 Bayes factors) | `results/raw/F-n20-equivalence.csv` |
| Table 3 (conflict dose) | `results/raw/E-conflict-trials.csv` analysed by `tools/conflict_trend.py` |
| table S4 (gain replication) | `G-k150-trials.csv`, `H-k600-trials.csv` likewise |

## S1.7 Conflict-dose trend analysis

`python tools/conflict_trend.py results/raw/E-conflict-trials.csv` maps arm id → α
(`self` 0, `conf25` 0.25, `conf50` 0.5, `conf75` 0.75, `decorr` 1), ranks the trial-level values
of every metric, and reports Spearman ρ against α with a permutation P (4,000 relabellings,
seed 12345). The same command run on `G-k150-trials.csv` and `H-k600-trials.csv` gives the two
extra gains. Metrics whose ρ is not reported had fewer than eight finite trial values (the two
legacy anatomical-gain readouts, which do not converge on every trial).
