# Science Reporting Summary — item-by-item answers

Fill the journal's online form from this sheet. Values are from `paper/tables.md` (generated) and
`results/CORRECTION.md` (the corrected experiment). Anything marked **[you]** is author-side.

## Study design

| item | answer |
|---|---|
| Study type | Computational experiment on a connectome-constrained spiking model. No animals, no human participants, no clinical data. |
| Unit of analysis | One simulated trial (independent stimulus stream and injection draws). |
| n per group | 10 trials per arm (I2-heading, M2-dose, A4-flow, D2-controls); 20 per arm in the replication (J2-n20); 6 per level at the two extra gains (K2-k150, L2-k600). |
| Randomisation | Arm order is fixed by design; every arm draws its injections from its own `Random` stream, and all arms in a trial share one stimulus stream (`Random(90000 + trial)`), so the stimulus is bit-identical across arms. |
| Blinding | Not applicable — no subjective measurement. Every readout is computed by code from spike counts. |
| Inclusion / exclusion | No trials excluded. `n_excluded_nonfinite` is reported per metric in `results/raw/*-compare.csv` (0 for every reported metric). |
| Replication | Internal: the whole experiment was re-run after the circuit was rebuilt (see `results/CORRECTION.md`), and the conflict dose was replicated at κ = 150 and κ = 600. |
| Sample-size justification | The Bayes-factor ceiling of the design is set by n, not by the analysis: BF₀₁(t = 0) = 2.52 at n = 10 and 3.24 at n = 20 (`tools/make_main_figures.py: supp3`). n = 20 was chosen to cross BF = 3 for the primary readouts. |

## Data and materials

| item | answer |
|---|---|
| Source data | MaleCNS v1.0 flat connectome (Google × Janelia / FlyWire Consortium; male CNS, brain + VNC). Exact files, byte counts and SHA256 in `paper/supplementary-note-S1.md` §S1.1. |
| Derived data | `flymind.brain` (FLYMIND4), SHA256 `FC6B544C68B4C9997987E2BAA788A41ED8E4E91B3B5C60EBC1166947447827AB`; reconstruction command in `reproduce.ps1 -Tier source`. |
| New reagents | None. This is a computational study. |
| Materials availability | Not applicable. |

## Statistics

| item | answer |
|---|---|
| Tests | Welch t with 95% CI; Cohen's d with Hedges–Olkin CI; Mann–Whitney U with tie correction and rank-biserial correlation; permutation tests (4,000 relabellings, seed 12345); Holm–Bonferroni within each metric's self-vs-control family. |
| Equivalence | TOST at two pre-specified bounds: standardised (\|d\| < 0.5) and relative (±10% of the control mean), with 90% CIs. |
| Bayes factors | JZS two-sample, Cauchy prior scale r = 0.707; validated against the analytic anchor BF₀₁(t = 0, n = 10/arm) = 2.52 (`python tools/compare_trials.py --selftest`). |
| Multiplicity | Reported per contrast as raw P plus Holm-corrected P, and read against Bayes factors; no metric is claimed on corrected P alone. |
| Error bars in figures | Mean ± 95% CI everywhere; individual trial values are overlaid as points. |
| Analysis software | Python 3.14.7 (standard library + numpy/matplotlib for figures), .NET 8.0.404 for the simulator. No statistical package is used: every test is implemented in `tools/compare_trials.py`. |

## Reproducibility

| item | answer |
|---|---|
| One-command reproduction | `pwsh -File reproduce.ps1 -Tier sims\|stats\|figures` |
| Blob check | `python tools\verify_headline_numbers.py` — 25 checks, all passing against the deposited CSVs |
| Environment | Windows, .NET 8.0.404, Python 3.14.7; software versions in `results/PROVENANCE.md` |
| Compute | One workstation, single-threaded simulator, 0.81× real time; the full family set is ~25 min wall-clock with 8 processes in parallel |

## Data, code and AI

| item | answer |
|---|---|
| Data availability | Repository URL: **[you — fill after pushing]**; the blob, every raw per-trial CSV and every stdout log are included. The 3 GB edge list and the 1 GB source feathers are *not* redistributed; they are rebuilt from the released MaleCNS v1.0 files by `tools/export_edges.py` (see `paper/supplementary-note-S1.md`). |
| Code availability | Same repository; MIT for code, CC BY 4.0 for data and figures (see `LICENSE`). |
| Generative AI — text | Disclosed: Methods (*Use of generative AI*), Acknowledgments, cover letter, and the full prompt log in Supplementary Note S2. |
| Generative AI — images | None. Every figure is a programmatic plot of the authors' own numerical output (matplotlib scripts in `tools/`); no AI image tool was used. |
| Generative AI — code | The model, analysis and figure code was written with a large language model under author direction; all of it was executed and its output verified by the authors (Note S2). |
| Dual use / biosafety | None. |
| Third-party material | None; no previously published figure or image is reproduced. |
