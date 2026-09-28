# Correction record: three defects in the simulation, and the results after fixing them

**Status: the results in `paper/manuscript.md` as it stood before this record are superseded.**
Three defects were found in the circuit and drive code while extending the work. Two of them were
fatal to the paper's central claim and one mislabelled a quarter of the input pool. All three are
fixed; every experiment was re-run from the rebuilt circuit; the corrected numbers are below.

Artifacts: rebuilt blob `flymind.brain` (21,383,125 bytes,
SHA256 `FC6B544C68B4C9997987E2BAA788A41ED8E4E91B3B5C60EBC1166947447827AB`), new families
`A4-flow`, `I2-heading`, `J2-n20`, `K2-k150`, `L2-k600`, `M2-dose`, `D2-controls`, `P2-propagation`,
`calibration2-sweep`. The pre-fix families (`A3`, `B3`, `E`, `F`, `G`, `H`, `C3`, `D`) and the
pre-fix blob (`malecns/flymind-before-poolfix.brain`) are kept for comparison.

---

## 1. Defect A — the yaw drive never implemented the body lock (fatal)

**What the paper claimed.** The manipulation is a *body-locked, slip-free* region of the visual
field: the part of the eye covered by the fly's own body sees no rotation, because the body does not
move relative to the head (`BodySlip` = 0.1 of the world's slip; the optic-flow drive implemented
exactly that).

**What the code did.** `DriveProfile.YawLevel` — the only drive path used by every heading
experiment (B3, E, F, G, H, C3) — took the patch signal straight from the caller and applied **no**
`BodySlip` factor. At α = 0 the caller passed `patchSignal = yaw`, i.e. the world's full rotation,
so `YawLevel(yaw, yaw)` reduced algebraically to `patchCap = 1`, `scale = 1`, and
`dst[k] = natural_k` for **every** cell. The "slip-free body patch" arm was therefore *the natural
condition* in every heading run, up to Bernoulli sampling noise.

**Evidence.** (i) `BodySlip` appears only in `Level()` (optic flow) and nowhere in `YawLevel()`.
(ii) The reported self-vs-flow contrast was d = −0.05, P = 0.91 with 95% CI
[−0.0075, 0.0066] — the signature of two identical conditions, not of a null effect.
(iii) After the fix, the harness prints a manipulation check
(`Trial.PatchLevelRatio` = mean patch level ÷ mean surround level) which for a body-locked patch
must sit clearly below the natural value: it is now 0.43 for `self` versus 0.98 for `flow`, and
rises monotonically with α (0.51, 0.64, 0.76, 0.89).

**Consequence.** The paper's headline — "a slip-free self-view is statistically indistinguishable
from the natural condition" (TOST, Bayes factors 2.8–3.2) — was **vacuous**: it compared a condition
with itself. It is not a null result, it is no result.

**Fix.** `YawLevel(yaw, slipPatch, dst)`: the body-covered cells receive `BodySlip × yaw` at α = 0,
and the conflict arms blend *that* residual slip with the block-shuffled copy,
`slipPatch = (1−α)·BodySlip·yaw + α·decor`. The surround is still solved per step so the total
delivered drive is identical in every arm (the end points are now two genuinely different
manipulations instead of one manipulation and one copy of the control).

## 2. Defect B — the "visual pool" was 10% antennal mechanosensory (material)

**What the paper claimed.** The pool is the lobula plate tangential cells: "the whole eye driven by
world optic flow".

**What the code did.** The self-motion pattern was `^(H1|H2|V1|VS|HS|JO-EV\d|LHAV|LHPV)`. The `JO-*`
types are Johnston's-organ neurons — antennal mechanosensory cells, a different modality. They are
identifiable as such in the release itself: `JO-EV1..6` have **no** `hemibrainType` and **no**
`somaLocation` (their somata are in the antenna, outside the imaged CNS volume), unlike every
optic-lobe type, which has both. 176 of the 1,770 pool cells were `JO-EV*`.

**Consequence.** (i) 10% of the "visual" pool was non-visual and was being driven with optic flow and
with a yaw push–pull assigned by *side of the midline*. (ii) Those 176 cells have no annotated soma,
so they all fell on one side of the midline (x = 0) and were all given the same preferred direction.
(iii) The connectome-derived CX relay (1,122 cells) had been computed *from* those cells as if they
were LPTCs.

**Fix.** The pattern is now `^(H1|H2|V1|VS|HS|LHAV|LHPV)`. The JO-* cells stay in the circuit as part
of the antennal population (the odour-background seed pattern is unchanged) but are no longer part of
the visual pool. Rebuilt pool: **2,689 cells** (1,594 LPTC + 1,095 relay, no overlap, relay
recomputed), of which only **5** lack an annotated soma (was 181). Midline: axis x at 385.7
(splits 1,379 / 1,310). The body patch at fraction 0.25 contains 672 cells and **no** cell without a
soma.

## 3. Defect C — the pool array overlapped the relay array (minor)

The pre-fix blob's visual relay contained 6 cells that were already LPTCs, so the harness pool
(1,770 + 1,122 = 2,892) injected 6 cells twice. The rebuilt blob has no overlap (`np.intersect1d` = 0).

## 4. What the corrected experiment shows

All numbers below are from the new families, drive-matched to ±0.1% (delivered events identical
across arms: e.g. 6.551–6.558 × 10<sup>5</sup> per trial in I2), n = 10 per arm, 6 s per trial,
κ = 300 unless stated.

### 4.1 κ = 300 calibration is unchanged in character

`calibration2-sweep`: CX 1.95 Hz with 9.9% of CX cells active at κ = 300 under the natural
condition, against 0.22 Hz / 1.4% at κ = 200 and 68.9 Hz / 45.5% at κ = 100 in the resting
condition. The paper's calibration sentence becomes "≈2 Hz with ≈10% of CX cells active".

### 4.2 A body-locked patch is *not* tolerated (replaces the old null)

Means per arm (I2), and the self-vs-control contrasts:

| metric | flow | **self** | shuffle | randmat | decorr | self vs flow (d, P) | self vs randmat (d, P) |
|---|---|---|---|---|---|---|---|
| CX rate (Hz) | 3.95 | **3.17** | 3.82 | 3.24 | 3.96 | −9.77, 1 × 10<sup>−4</sup> | −0.92, 5 × 10<sup>−8</sup> |
| CX active fraction | 0.215 | **0.170** | 0.208 | 0.176 | 0.201 | −10.1 | −1.25 |
| yaw modulation (Hz) | 1.919 | **1.153** | 1.542 | 0.953 | 0.937 | −7.12, 1 × 10<sup>−4</sup> | +1.34, P = 0.16 |
| tuning ↔ wiring *r* | 0.309 | **0.236** | 0.342 | 0.310 | 0.252 | −3.52, 3 × 10<sup>−5</sup> | −1.81, P = 0.027 |
| steering fidelity | 0.786 | **0.741** | 0.770 | 0.814 | 0.615 | −2.87, 1 × 10<sup>−4</sup> | −4.64, 8 × 10<sup>−7</sup> |
| steering amplitude (Hz) | 502 | **424** | 489 | 526 | 431 | −6.36 | −8.27 |
| descending rate (Hz) | 2,072 | **1,930** | 2,093 | 2,072 | 2,076 | −11.9 | −12.6 |
| population τ (ms) | 223 | **150** | 197 | 146 | 131 | −2.87 | +0.15, P = 0.21 |
| bump *R* | 0.327 | **0.359** | 0.332 | 0.336 | 0.274 | +1.44, P = 0.31 | +0.86, P = 0.46 |
| effective dimension | 51.0 | **52.8** | 54.0 | 53.9 | 59.9 | +0.52 | −0.18 |

Two things are separable here, and they are the corrected paper's structure:

1. **The rate/firing consequences are input loss.** A *random* patch that removes the same number of
   CX input synapses (375 cells, 9.6% of CX input) reproduces the CX rate (3.24 vs self 3.17,
   d = −0.92), the active fraction, the fan-body rate (d = +1.44), τ (d = +0.15) and the fluctuation
   SD (d = −0.27).
2. **The coding and behavioural consequences are not.** The same random patch does *not* reproduce
   the drop in tuning (self 0.236 vs randmat 0.310, d = −1.81, P = 0.027), the drop in steering
   fidelity (0.741 vs 0.814, d = −4.64, BF<sub>10</sub> = 1.3 × 10<sup>6</sup>), the yaw modulation
   (1.15 vs 0.95 Hz) or the descending rate (Δ = −142 Hz, d = −12.6). Keeping a spatially compact,
   body-shaped region silent costs more than silencing a random set of the same size.

### 4.3 Conflict is worse than silence for the steering command, better for the rates

As α rises from 0 to 1 (I2 conflict dose, 5 levels × 10 trials):

| readout | α = 0 | 0.25 | 0.50 | 0.75 | 1.00 | ρ vs α | P |
|---|---|---|---|---|---|---|---|
| **steering fidelity** | **0.7405** | 0.7142 | 0.6793 | 0.6541 | **0.6154** | **−0.845** | 2 × 10<sup>−4</sup> |
| bump *R* | 0.3585 | 0.3278 | 0.3036 | 0.2765 | 0.2742 | −0.817 | 2 × 10<sup>−4</sup> |
| effective dimension | 52.83 | 55.12 | 54.54 | 57.99 | 59.86 | +0.503 | 5 × 10<sup>−4</sup> |
| ring trajectory circularity | 0.1687 | 0.1553 | 0.1313 | 0.1400 | 0.1120 | −0.444 | 7 × 10<sup>−4</sup> |
| ring state top-2 variance | 0.4357 | 0.4408 | 0.4275 | 0.4231 | 0.3995 | −0.363 | 0.0085 |
| yaw modulation (Hz) | 1.153 | 0.985 | 0.972 | 0.971 | 0.937 | −0.335 | 0.021 |
| CX rate (Hz) | 3.172 | 3.420 | 3.630 | 3.853 | 3.962 | +0.952 | 2 × 10<sup>−4</sup> |
| descending rate (Hz) | 1,930 | 1,976 | 2,009 | 2,041 | 2,076 | +0.958 | 2 × 10<sup>−4</sup> |
| tuning ↔ wiring *r* | 0.2359 | 0.2518 | 0.2549 | 0.2539 | 0.2520 | +0.246 | 0.093 |
| delivered events | 6.552 × 10<sup>5</sup> | 6.555 | 6.556 | 6.554 | 6.558 | +0.134 | 0.36 |
| steering amplitude (Hz) | 424.3 | 423.0 | 425.5 | 422.4 | 431.3 | +0.119 | 0.41 |

The conflict dose is a pure *signal-quality* manipulation: total drive is flat (ρ = +0.13), the
steering command's amplitude is flat (ρ = +0.12), and yet the **fidelity** with which that command
follows the actual turn falls monotonically, 0.741 → 0.615, together with the ring's bump
(0.359 → 0.274) and its trajectory circularity. Firing rates *rise* with α, because a fully
conflicting patch delivers rotation drive where a body-locked one delivers almost none.

### 4.4 Patch-size dose: monotone degradation (was reported as no trend)

M2 (`--dose`, fractions 0 / 0.125 / 0.25 / 0.5 of the pool, drive matched to 0.07%):

| readout | ρ vs fraction | P |
|---|---|---|
| fan-body rate | −0.969 | 5 × 10<sup>−4</sup> |
| pool rate | −0.969 | 5 × 10<sup>−4</sup> |
| CX rate | −0.941 | 5 × 10<sup>−4</sup> |
| yaw modulation | −0.916 | 5 × 10<sup>−4</sup> |
| tuning ↔ wiring *r* | −0.914 | 5 × 10<sup>−4</sup> |
| fluctuation SD | −0.899 | 5 × 10<sup>−4</sup> |
| population τ | −0.792 | 5 × 10<sup>−4</sup> |
| bump *R* | +0.575 | 5 × 10<sup>−4</sup> |
| CX active fraction | −0.574 | 5 × 10<sup>−4</sup> |
| effective dimension | −0.046 | 0.77 |
| delivered events | +0.070 | 0.68 |

The bigger the silent region, the worse the heading system — the opposite of the pre-fix result
(|ρ| ≤ 0.18, P ≥ 0.28) and exactly what the corrected drive model predicts. This is the paper's
positive control that the manipulation *is* a manipulation.

### 4.5 Gain replication of the conflict effect

Steering fidelity versus α at three gains (n = 6 per level at the replication gains):

| gain | α = 0 | 0.25 | 0.50 | 0.75 | 1.00 | ρ | P |
|---|---|---|---|---|---|---|---|
| κ = 150 | 0.6791 | 0.6481 | 0.5775 | 0.5322 | 0.4622 | −0.931 | 2 × 10<sup>−4</sup> |
| κ = 300 | 0.7405 | 0.7142 | 0.6793 | 0.6541 | 0.6154 | −0.845 | 2 × 10<sup>−4</sup> |
| κ = 600 | 0.7571 | 0.7485 | 0.7325 | 0.7232 | 0.6910 | −0.673 | 2 × 10<sup>−4</sup> |

The dose effect is present at every gain and attenuates as the circuit is driven harder, which is the
expected direction (a higher-gain circuit has more recurrent amplification to compensate).

### 4.6 Optic flow: rate change is input loss, geometry change is not

A4 (new pool, 3 s, n = 10): CX rate 5.93 (flow) → 3.04 (self), −49%; `shuffle` (random identity, same
size, same reduced slip) 5.58; `randmat` (matched CX input loss) 3.16. Ring bump *R* 0.237 (flow) →
0.461 (self) → 0.318 (shuffle) → 0.353 (randmat); effective dimension 44.9 → 28.6 → 40.8 → 33.3. The
rate falls as far with a random patch as with the body patch, while the sharpening of the ring
population vector is much larger for the body patch than for either control.

### 4.7 Propagation and positive controls still hold

P2: 2,015 / 2,074 CX cells (97.2%) are one hop from the pool, 48,064 direct pool→CX synapses; a
synchronous volley peaks at 2.5 ms with 21 CX spikes/step (baseline 0.17) and 101 responsive cells
(4.9%), falling to 5 spikes and 36 cells (−76%, −64%) with the body patch silent; still present at
κ = 100 and κ = 1000 (54 spikes at 9.5 ms).

D2 positive controls: drive ×0.5 / ×1.5 moves the CX rate 2.54 / 5.17 Hz against self 3.17;
synchronised injection at the same expected total collapses the effective dimension to 29.4 (vs 52.8)
and raises the fluctuation SD to 1.35 Hz (vs 0.76) while leaving tuning (0.311 vs 0.236) and steering
(0.653 vs 0.741) far smaller than the patch effect.

## 5. What the paper now says, and what it can no longer say

| | pre-fix claim | post-fix result |
|---|---|---|
| Absent self-motion (slip-free body patch) | statistically indistinguishable from natural (BF<sub>01</sub> = 2.8–3.2) | **large, significant degradation**: tuning d = −3.52, steering fidelity d = −2.87, yaw modulation d = −7.12, CX rate d = −9.77 |
| Is the effect just input loss? | (not asked) | rate/τ/SD **yes** (randmat reproduces them); tuning and steering **no** (d = −1.81 and −4.64) |
| Conflicting self-motion | degrades heading coding (tuning ρ = −0.82) | degrades the **steering command** (ρ = −0.845) and the ring bump (ρ = −0.817) at **constant drive and constant command amplitude**; tuning is flat (ρ = +0.25) |
| Patch size | no trend (|ρ| ≤ 0.18) | monotone degradation (tuning ρ = −0.91, CX rate ρ = −0.94) |
| Gain replication | tuning ρ = −0.92 / −0.82 / −0.84 | steering fidelity ρ = −0.93 / −0.85 / −0.67 |

The unifying statement the corrected data support: **a body-shaped region of the eye that does not
report the world's rotation degrades heading coding and the steering command in proportion to its
size, and the damage is not merely the loss of input — replacing that region's motion with motion
that contradicts the world leaves the firing rates intact while destroying the fidelity of the
steering command.** The "missing versus conflicting" contrast survives, but as *different kinds* of
damage rather than as "tolerated versus not tolerated".

## 6. Reproduce

```powershell
cd D:\projects\science
pwsh -File reproduce.ps1 -Tier sims     # rebuild-free: re-run every family (~25 min, 8 processes)
pwsh -File reproduce.ps1 -Tier stats    # every statistic, equivalence test and Bayes factor
pwsh -File reproduce.ps1 -Tier figures  # redraw the figures from the deposited CSVs
python tools\digest.py                  # the tables in this record, from the CSVs
```

The blob is rebuilt from the released feather files with
`dotnet run -c Release -- <edges.bin> <annotations.tsv> ..\flymind.brain 12000 1 <transmitters.tsv>`
(75 s) — see `reproduce.ps1 -Tier source`.

## 7. Lesson for the paper's methodological half

The drive-matching trap the paper already reports (an unmatched 0.5% drive difference produced
d = −14.5 at P = 4.7 × 10<sup>−17</sup>) now has two companions, and both are the same species of
error: *a manipulation that is not implemented is indistinguishable from a manipulation with no
effect*, and *a pool that is not what its name says is a different experiment*.

- Defect A produced a **false null** — the most dangerous possible outcome, because a null is
  reported as evidence of tolerance.
- Defect B changed what the input population *is* by 10% while every name in the code said
  "visual pool".

Both were invisible in the outputs and both are caught by one-line checks that are now permanent
parts of the harness: `patch_level_ratio` (does the manipulation reach the cells it claims to?) and
`pop_name` in `results/raw/slice-census.csv` (is the population what the pattern says it is?). Any
connectome-constrained perturbation study needs both.
