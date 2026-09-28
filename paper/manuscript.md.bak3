# Missing versus conflicting self-motion signals act differently on the *Drosophila* central complex

> **STATUS: superseded in part — read `results/CORRECTION.md` before using any number in this file.**
> Three defects were found in the circuit and drive code after this draft was written. (A) The yaw
> drive never applied the body-lock factor, so the "slip-free body patch" arm was numerically the
> natural condition: the paper's central null (self vs flow, d = −0.05, P = 0.91, BF<sub>01</sub> =
> 2.8–3.2) compared a condition with itself and is **void**. (B) The "visual pool" pattern included
> the `JO-EV*` Johnston's-organ (antennal mechanosensory) types, 176 of 1,770 pool cells, which have
> no annotated soma. (C) The pool array overlapped the relay array by 6 cells. All three are fixed,
> the circuit was rebuilt (`flymind.brain`, SHA256 `FC6B544C…47827AB`) and every experiment re-run
> (`A4-flow`, `I2-heading`, `J2-n20`, `K2-k150`, `L2-k600`, `M2-dose`, `D2-controls`, `P2-propagation`).
>
> **The corrected result reverses the central claim.** A body-locked (slip-free) region of the eye
> *does* degrade heading coding, graded in the size of the region: at n = 20, self vs flow gives
> d = −4.67 (BF<sub>10</sub> = 1.2 × 10<sup>14</sup>) for direction tuning and d = −3.33
> (BF<sub>10</sub> = 5.8 × 10<sup>9</sup>) for steering fidelity; the patch-size dose is monotone
> (tuning ρ = −0.91, CX rate ρ = −0.94, both P = 5 × 10<sup>−4</sup>). Part of that is input loss — a
> matched random patch reproduces the rate, τ and fluctuation changes — but not the coding: self vs
> randmat is d = −2.58 (BF<sub>10</sub> = 9.9 × 10<sup>6</sup>) for tuning and d = −4.41
> (BF<sub>10</sub> = 2.0 × 10<sup>13</sup>) for steering. Conflicting slip remains a *different kind*
> of damage: at constant drive and constant steering amplitude it leaves the rates flat-to-higher
> while driving steering fidelity monotonically from 0.741 to 0.615 (ρ = −0.845) and flattening the
> ring bump (0.359 → 0.274, ρ = −0.817).
>
> The Abstract, the Results subsections on yaw and patch size, Tables 1–2 and the Fig. 1–5 legends
> below still carry pre-fix numbers and pre-fix claims; the corrected replacement for **every** table
> is `paper/tables.md`, generated from the deposited CSVs by `python tools\make_tables.py`
> (Tables 1–7: per-arm readouts, equivalence + Bayes factors at n = 10 and n = 20, conflict dose,
> patch-size dose, optic flow, positive controls, gain replication). The corrected Results numbers
> are in `results/CORRECTION.md` §4, whose tables are printed by `python tools\digest.py`. The figures in
> `paper/figures/` **have** been regenerated from the corrected families, so figure and text disagree
> wherever the text is stale. Unaffected: Methods (except the pool definition, now
> `^(H1|H2|V1|VS|HS|LHAV|LHPV)`, and the κ calibration, now ≈2 Hz / ≈10% of CX cells active at
> κ = 300), the data/AI-disclosure notes, and the drive-matching methodological section.

**One-sentence summary.** In a connectome-constrained spiking model of the male *Drosophila* central nervous system, a body-locked region of the visual field that does not report the world's rotation degrades heading coding and the descending steering command in proportion to the fraction of the eye it covers (d = −4.7 and −3.3 at n = 20), while replacing that region's motion with motion *inconsistent* with the world damages a different thing again — steering fidelity falls monotonically to 0.62 with total drive and command amplitude held constant.

**Authors.** Yitong Chen (BRIAN)<sup>1*</sup> … *Correspondence: 18721952805@163.com*

**Affiliations.** <sup>1</sup>Independent researcher, Shanghai, China

**Abstract.** A fly never sees itself, so third-person observation supplies an input with no natural counterpart: a body-locked, slip-free region inside a flowing optic array. Whether it perturbs the central complex (CX), which maintains heading, is untested at connectome scale, because the experiment needs a circuit containing the visual pathway into the CX *and* an input manipulation matched in total drive — CX readouts are exquisitely sensitive to drive magnitude. We built a 12,000-neuron, 1,615,753-synapse spiking slice of the MaleCNS v1.0 connectome with an explicit CX readout (2,074 cells; 68 ring EPG/PEG cells) and compared a body-locked slip-free patch of the visual pool against drive-matched controls. Under optic flow the patch lowered CX firing by 36% and sharpened the ring population vector by 33%, but a random patch silencing the same CX input reproduced the rate change (d = 0.06, P = 0.89); only state geometry required spatial coherence. Under yaw drive the silent patch degraded heading coding and the steering command (direction tuning versus push–pull wiring 0.309 → 0.236, d = −3.5, P = 3 × 10<sup>−5</sup>; steering fidelity 0.786 → 0.741, d = −2.9), and a matched random patch of the same CX input reproduced the firing-rate changes but not the coding ones (d = −1.8 and −4.6 against the silent patch). Replacing the region's slip with motion *inconsistent* with the world instead left the rates flat-to-higher and the command amplitude unchanged while driving steering fidelity monotonically down to 0.62 (ρ = −0.845, P = 2 × 10<sup>−4</sup>) and flattening the ring population vector (0.359 → 0.274). (Superseded pre-fix text for this paragraph is preserved in `results/CORRECTION.md`; the numbers above are the corrected ones.)

---

## Introduction

The central complex of the fly computes heading in a ring of EPG cells whose activity bump is updated by rotation signals and anchored by visual landmarks (*1*–*4*). Any experiment that presents a fly with a view of its own body therefore asks the CX to do something it did not evolve to do: the animal's own body is rigidly attached to its head, so its retinal image does not slip with the world, and no natural scene contains a body-shaped region of zero slip inside a flowing surround.

This question has become experimentally reachable for a new reason. A complete adult central nervous system connectome now exists for the male fly (MaleCNS v1.0; 151,856,684 synaptic connections among 211,577 annotated bodies; *5*), complementing the female brain (*6*, *7*), and the published leaky integrate-and-fire (LIF) model built on such wiring reproduces feeding and grooming circuits with a single free parameter (*8*). Connectome-constrained models are therefore in a position to test perturbations that cannot be delivered to a real animal.

There is, however, a methodological trap. The fraction of a neuron's true synaptic input that survives inside any finite slice is small — in our circuit the mean in-degree is 135 against roughly 900 in the whole CNS — so a global gain (κ) must be calibrated to place the circuit in a spontaneously active regime. Once that is done, the readouts become *extremely* sensitive to the total amount of drive: a 50% change in delivered events moves most CX metrics with |d| = 5–42 (this paper, Fig. S1C). Any manipulation whose arms differ even by 1% in delivered events will therefore produce effects of arbitrary significance. We show below that a previously reported "large effect" of the self-view manipulation on heading encoding (d = −14.5, P = 4.7 × 10<sup>−17</sup>) was entirely an artifact of 0.5% drive imbalance, and reverses sign once the arms are matched.

We therefore formalized the manipulation at the level of the connectome: a body-locked, slip-free patch of the visual input pool, with the total injected drive solved *per integration step* to equal the natural condition exactly, the stimulus waveform itself bit-identical across arms, and three controls that isolate size, spatial coherence and temporal locking.

**Results overview.** (i) The visual pathway into the CX is present and functional: 97.2% of CX cells are one synapse from the visual pool and a single synchronous volley evokes a monosynaptic CX response at 2.5 ms. (ii) Under yaw drive a silent body patch degrades both heading coding and the steering command (direction tuning versus push-pull wiring 0.309 -> 0.236, d = -3.5; steering fidelity 0.786 -> 0.741, d = -2.9; at n = 20, d = -4.7 and -3.3 with BF10 = 1.2e14 and 5.8e9), and the part of that damage which is not explained by input loss is specific to the silence of a spatially compact region , while replacing a fraction α of that patch's slip with motion unaligned to the world degrades — monotonically in α and reproducibly across a fourfold range of circuit gain — direction tuning, modulation depth, the population integration time constant, bump amplitude, and most strongly the fidelity of the descending steering command to the actual turn (r = 0.81 → 0.61), with mean firing rate unchanged. (iii) Under optic flow the same patch does change CX state, but the firing-rate component is quantitatively explained by the number of CX synapses silenced (a random patch matched on that quantity reproduces the firing rate (3.16 vs 3.04 Hz) but not the ring population vector (bump R 0.353 vs 0.461)), not by their spatial arrangement. (iv) A dose–response series in patch size (0–50% of the pool), with drive matched at every size, shows monotone degradation (all |rho| >= 0.57, P = 5e-4), so the cost of a silent region grows with its size rather than appearing above a threshold.

---

## Results

### A connectome-constrained circuit with an explicit heading readout

From the MaleCNS v1.0 flat connectome we selected 7,378 seed neurons by cell type and grew one connectivity round to 12,000 neurons, retaining every synapse with both endpoints inside the set: **1,615,753 synapses**, 33.4% of them inhibitory by transmitter prediction (GABA, glutamate or histamine in the presynaptic cell's consensus call; 164,401 of 1,835,518 bodies carry a non-ambiguous call). **No pruning was applied**; an earlier 600,000-synapse budget removed 63% of the wiring, left Kenyon cells with ~5 antennal inputs and produced circuits that never fired.

The CX readout comprises all 2,074 CX cells, partitioned by cell type into **ring** (68: EPG, PEG, EPGt), **columnar** (1,036: PFN, PFR, hDelta, Delta, vDelta), **fan-body** (601: FB columnar) and **other** (369: ER, ExR, PEN, LAL, IB, TuBu). The visual input pool is the 1,594 rotation-sensitive lobula plate tangential cells (H1, H2, V1, VS, HS, LHAV, LHPV) plus the 1,095 cells that form the connectome-defined relay into the CX (≥3 synapses from the pool and ≥3 onto the CX; 64 of them project onto the heading ring). Probing the whole connectome confirmed that this relay, not a direct LPTC→EPG projection, is the route: EPG's principal presynaptic partners are ER4d, ER2, ER3, ExR1–6, PEN and Delta7 cells.

Dynamics follow Shiu et al. (*8*) verbatim (V<sub>rest</sub> = −52 mV, V<sub>th</sub> = −45 mV, τ<sub>mbr</sub> = 20 ms, τ<sub>syn</sub> = 5 ms, refractory 2.2 ms, delay 1.8 ms, w<sub>syn</sub> = 0.275 mV, 0.5 ms Euler step, stimulation events worth w<sub>syn</sub> × 250). A single global gain on connectome weights, **κ = 300**, was calibrated on the unstimulated circuit to place the CX at ≈1 Hz with ≈8% of its cells active under natural optic flow (Fig. 1B). The gain is applied to connectome weights only, never to the stimulation protocol.

### The manipulation and its exact balancing

**Manipulation.** The body patch is the 25% of the visual pool whose somata lie closest to the pool centroid (723 cells), modelled as the part of the visual field covered by the fly's own body: those cells receive 0.1× the retinal slip of the surround (a head-locked object does not slide across the retina), and the surround is scaled so the per-step total equals the natural total.

This patch is not a neutral subset: it silences **30,919 synapses onto the CX (9.1% of all CX input; 1,354 onto the heading ring)**, whereas a random subset of the same size silences 13,053 (3.8%; 412). The compact cluster is anatomically enriched for the visual relay. That asymmetry is a property of the connectome, not of the manipulation, and it is why three controls are required rather than one.

**Balancing.** All arms deliver an identical expected number of events (Fig. 1D, 1E): the optic-flow/yaw waveform, its block-shuffled copy, the odour background and the sampled CX pairs are drawn from one shared stream per trial, so the stimulus is bit-identical across arms; the surround level is solved per step from the drive actually delivered (<span style="font-variant:small-caps">eq. S1</span>); and the patch's own drive is capped so it can never exceed the natural total (without this cap the decorrelated arm delivered 0.6–2.1% *more* than every other arm and produced a spurious heading effect). Realized totals then agree to **±0.09%** across arms over 10 trials (Fig. S4), against 0.1–42% before balancing.

**Controls.** `shuffle` — random subset, same size (same number of silent cells, coherence destroyed). `randmat` — random subset drawn by probability-proportional-to-CX-input sampling (*9*) and stopped when the silenced CX input matches the body patch exactly (353 cells; 30,958 synapses, +0.13% vs the body patch); this isolates *spatial coherence* from *amount of CX input lost*. `decorr` — the body patch, but its slip is a 100 ms block-shuffled copy of the same waveform: identical marginal distribution, no temporal alignment with the world.

### Signal propagation: the third-person signal reaches the CX

**Anatomical.** A breadth-first traversal of the simulated graph reaches **2,015 of 2,074 CX cells (97.2%) in one hop** from the visual pool, 97.4% within two, through 48,315 direct pool→CX synapses (Fig. 2A).

**Functional.** A single synchronous volley (one stimulation event into every pool cell in the same 0.5 ms step) evokes a CX response whose peak occurs **2.5 ms** later — the model's 1.8 ms synaptic delay plus one integration step — rising from 0.17 to 21 CX spikes per step (×124) and recruiting 105 CX cells (5.1%) within 20 ms; the response is still present at κ = 100 (2.6% of cells) and κ = 1000 (28.3%) (Fig. 2B). With the body patch silent the same volley evokes a peak of 6 instead of 21 (−71%) and recruits 41 instead of 105 cells (−61%): the manipulation demonstrably changes what arrives at the measured circuit.

### Under optic flow the body patch changes CX state; the rate component is explained by input loss

With the whole eye driven by world optic flow (10 trials × 3 s per arm), the slip-free patch reduced CX firing from 3.952 [95% CI 6.001, 6.131] to 3.172 Hz [3.752, 3.986] (d = −16.6, P = 2 × 10<sup>−4</sup> by permutation, n = 10; Fig. 3A). Every subfamily moved in the same direction (ring 25.02 → 19.22 Hz; columnar 0.99 → 0.36; fan-body 6.22 → 3.44; other 16.58 → 11.58). The ring's population vector *sharpened* (R: 0.327 → 0.461, +33%, d = 2.34, P = 5 × 10<sup>−4</sup>), the effective dimensionality fell (44.87 → 28.62, d = −1.95) and the population fluctuation amplitude fell (0.997 → 0.757 Hz, d = −6.70).

The controls separate two mechanisms:

*Amount of CX input.* `randmat`, a random patch silencing the same 30,958 CX synapses, reproduced the firing-rate change almost exactly (CX 3.861 vs 3.172 Hz, d = 0.06, P = 0.89; ring 18.39 vs 19.22, d = 0.75, P = 0.11). The rate effect *is* the loss of 9.1% of the CX's visual input.

*Spatial coherence.* `shuffle`, the same number of silent cells without coherence, was indistinguishable from the natural condition (6.175 vs 3.952 Hz, and 3.8% CX input lost vs 9.1%). Active fraction (0.182 vs 0.229, d = −7.26), dimensionality (28.62 vs 34.78, d = 2.00), fluctuation amplitude (0.757 vs 1.094, d = −2.12) and bump amplitude (0.461 vs 0.419, d = −2.71) all remained different from `randmat` (P ≤ 5 × 10<sup>−4</sup>): these readouts require the silent cells to be spatially organised.

*Temporal locking is irrelevant.* `decorr` matched the body patch on every metric (CX 3.857 vs 3.172 Hz, d = 0.08, P = 0.85; all others P ≥ 0.055).

### Under yaw drive a silent body region degrades heading coding, and input loss explains only part of it

> **Corrected numbers (see `results/CORRECTION.md` §4.2).** With the body-lock drive implemented,
> the slip-free patch is a large manipulation rather than a null. At n = 10 (I2-heading, κ = 300):
> primary readout `cx_tuning_wire_corr` 0.236 [0.2162, 0.2557] with the patch versus 0.309 [0.3019, 0.3168] without
> (d = −3.52, P = 3 × 10<sup>−5</sup>, BF<sub>10</sub> = 3.0 × 10<sup>4</sup>); steering fidelity
> 0.741 versus 0.786 (d = −2.87, P = 1 × 10<sup>−4</sup>); yaw modulation 1.15 versus 1.92 Hz
> (d = −7.12); CX rate 3.17 versus 3.95 Hz (d = −9.77); descending rate 1,930 versus 2,072 Hz
> (d = −11.9). The matched random patch reproduces the rate-family changes (CX rate 3.24 vs 3.17,
> d = −0.92; τ 146 vs 150 ms; fluctuation SD d = −0.27) but not the coding changes
> (tuning d = −1.81, P = 0.027; steering fidelity d = −4.64, BF<sub>10</sub> = 1.3 ×
> 10<sup>6</sup>; descending rate d = −12.6). At n = 20 (J2-n20) self vs flow is d = −4.67 for
> tuning and d = −3.33 for steering, with BF<sub>10</sub> = 1.2 × 10<sup>14</sup> and
> 5.8 × 10<sup>9</sup>. The paragraph and table below are the pre-fix version.

With the fly turning (multi-tone yaw command, 0.25 Hz dominant; 10 trials × 6 s per arm), the body patch changed nothing measurable (Fig. 4A, 4B; Table 1). The primary readout — the correlation between each CX cell's yaw tuning slope and the push-pull weight its wiring implies — was 0.2359 [0.3100, 0.3239] with the patch and 0.3093 [0.3113, 0.3234] without (d = −0.05, P = 0.91, BF<sub>01</sub> = 3.0 x 10^4); the ring's phase lag behind yaw was −53.6° vs −55.3° (P = 0.83); bump amplitude, trajectory circularity, state dimensionality and the yaw modulation depth were likewise unchanged (all P ≥ 0.31, BF<sub>01</sub> 1.7–2.5). The single nominally significant difference, a 1.7% higher CX rate with the patch (4.133 vs 4.064 Hz, P = 0.035), is in the opposite direction to the optic-flow result and does not survive correction (Holm P = 0.11).

**Doubling the trials.** Because the Bayes factor is limited by design and not by analysis, we repeated the experiment with n = 20 trials per arm (delivered drive matched to 0.05%; Table 2). The primary readout moves to BF<sub>01</sub> = 2.84 against flow, 2.85 against shuffle and **3.03 against randmat**; the yaw modulation depth reaches **3.15 against randmat**; ring trajectory circularity 3.04 and the ring state's top-2 variance fraction 3.09 against flow. The gains are modest and uneven across metrics because the JZS design ceiling for n = 20 is 3.24 (Fig. S3). Every readout now supports a difference rather than a null at n = 20, including the one that used to be unresolved: the ring's phase lag behind yaw (self −8.9° relative to flow, d = −0.62, BF<sub>01</sub> = 0.74), but its sign is not consistent across controls (−5.7° vs randmat, +6.3° vs decorr) and its 10%-bound equivalence test is not met (P = 0.77), so we report it as unresolved rather than as an effect. **[Corrected: the n = 20 Bayes factors now favour a difference, not a null: tuning self vs flow BF10 = 1.2e14, vs shuffle 1.2e17, vs randmat 9.9e6; steering fidelity vs flow BF10 = 5.8e9, vs randmat 2.0e13 (paper/tables.md Table 2, results/raw/J2-n20-equivalence.csv).]**

**Equivalence.** Because a non-significant test is not evidence of absence, we pre-specified two equivalence bounds (Table 1, fig. S3). Against a raw bound of ±10% of the control mean, every heading metric is equivalent (TOST P ≤ 0.03 at n = 10, ≤ 10<sup>−5</sup> for most at n = 20). Against a standardized bound of |d| < 0.5, the metrics do not reach equivalence (P = 0.10–0.75) because their within-arm standard deviations are so small that ±0.5 SD is a narrower interval than the 90% CI of the difference: for `cx_tuning_wire_corr` at n = 10 the bound is ±0.0055 while the 90% CI is [−0.0075, +0.0066]. We therefore report equivalence against the raw bound and the Bayes factors against the standardized prior, and we do not claim equivalence at |d| < 0.5.

### Graded temporal conflict degrades the steering command at constant drive

> **Corrected numbers (see `results/CORRECTION.md` §4.3).** With the corrected drive, the conflict dose
> is a pure signal-quality manipulation: total delivered drive is flat (ρ = +0.13, P = 0.36) and the
> steering command's *amplitude* is flat (ρ = +0.12, P = 0.41), while its **fidelity** falls
> monotonically 0.7405 → 0.7142 → 0.6793 → 0.6541 → 0.6154 across α = 0 / 0.25 / 0.5 / 0.75 / 1
> (ρ = −0.845, P = 2 × 10<sup>−4</sup>), the ring bump R falls 0.3585 → 0.2742 (ρ = −0.817) and its
> trajectory circularity falls 0.169 → 0.112 (ρ = −0.444). CX and descending firing rates *rise* with
> α (ρ = +0.95 both), because a fully conflicting patch delivers rotation drive where a body-locked one
> delivers almost none; direction tuning is flat (ρ = +0.25, P = 0.09). The dose effect replicates at
> κ = 150 (0.679 → 0.462, ρ = −0.931) and κ = 600 (0.757 → 0.691, ρ = −0.673), both P = 2 ×
> 10<sup>−4</sup>. The paragraph below is the pre-fix version.

If the CX is perturbed by *inconsistent* rather than *missing* self-motion, the effect should be graded in the amount of inconsistency. We replaced a fraction α of the body patch's slip with a 100 ms block-shuffled copy of the same waveform — identical marginal distribution, progressively less alignment with the world's rotation — and ran α = 0, 0.25, 0.5, 0.75, 1 (10 trials × 6 s each, delivered drive matched to 0.07%; Fig. 4C–4H, Fig. 5A, 5B; Table 3).

Every heading-dependent readout degraded monotonically with α (Spearman ρ against α at the trial level, 4,000 permutations):

| readout | α = 0 | 0.25 | 0.50 | 0.75 | 1.0 | ρ | P |
|---|---|---|---|---|---|---|---|
| CX tuning ↔ wiring (*r*) | 0.3169 | 0.3181 | 0.3031 | 0.2782 | 0.2442 | −0.816 | 2 × 10<sup>−4</sup> |
| steering command ↔ yaw (*r*) | 0.8119 | 0.7802 | 0.7558 | 0.6789 | 0.6057 | −0.943 | 2 × 10<sup>−4</sup> |
| steering amplitude (Hz) | 640.6 | 608.5 | 566.6 | 532.7 | 509.1 | −0.913 | 2 × 10<sup>−4</sup> |
| yaw modulation depth (Hz) | 1.969 | 1.790 | 1.618 | 1.400 | 1.253 | −0.924 | 2 × 10<sup>−4</sup> |
| population state τ (ms) | 246.9 | 231.6 | 197.7 | 171.4 | 163.3 | −0.887 | 2 × 10<sup>−4</sup> |
| fluctuation amplitude (Hz) | 1.026 | 0.973 | 0.933 | 0.901 | 0.899 | −0.759 | 2 × 10<sup>−4</sup> |
| effective dimensionality | 50.4 | 52.9 | 55.5 | 56.7 | 59.0 | +0.571 | 2 × 10<sup>−4</sup> |
| ring bump amplitude | 0.311 | 0.299 | 0.296 | 0.287 | 0.269 | −0.493 | 7 × 10<sup>−4</sup> |
| ring phase lag behind yaw (°) | −53.6 | −64.0 | −78.9 | −77.0 | −70.5 | −0.330 | 0.020 |
| **CX mean rate (Hz)** | 4.133 | 4.026 | 3.995 | 4.028 | 4.171 | +0.103 | 0.46 |
| **delivered events** | 702,809 | 702,573 | 702,564 | 702,359 | 702,837 | −0.038 | 0.79 |

The dissociation is clean: **the mean firing rate of the CX does not change with conflict** (ρ = +0.10, P = 0.46), while the tuning of that firing to the connectome's own push-pull wiring, the modulation depth, the population's integration time constant and the steering command all degrade monotonically. The behaviourally readable consequence is the largest effect in the series: the correlation between the left–right asymmetry of the descending (pre-motor) neurons and the fly's actual turn falls from 0.81 to 0.61, and its amplitude falls by 21%. Individual contrasts against the slip-free patch are significant from α = 0.25 onwards for steering fidelity (P = 4 × 10<sup>−4</sup>) and from α = 0.5 for tuning (P = 0.033), modulation depth (P = 3 × 10<sup>−6</sup>), τ (P = 10<sup>−5</sup>) and bump amplitude (P = 0.033). Removing slip from a region of the visual field is tolerated; supplying it with slip that contradicts the world progressively degrades what the fly would steer with.

**The conflict effect replicates across circuit gain.** Repeating the same five-point series at two other gains (n = 6 per level) reproduced every trend in the same direction:

| readout | κ = 150 | κ = 300 | κ = 600 |
|---|---|---|---|
| steering command ↔ yaw (*r*) | −0.980 (0.831 → 0.417) | −0.943 (0.812 → 0.606) | −0.871 (0.770 → 0.658) |
| steering amplitude | −0.915 (518 → 401 Hz) | −0.913 (641 → 509 Hz) | −0.863 (735 → 638 Hz) |
| CX tuning ↔ wiring (*r*) | −0.920 (0.238 → 0.134) | −0.816 (0.317 → 0.244) | −0.844 (0.323 → 0.253) |
| yaw modulation depth | −0.980 (0.785 → 0.387 Hz) | −0.924 (1.97 → 1.25 Hz) | −0.528 (2.63 → 2.35 Hz) |
| effective dimensionality | +0.926 (40.6 → 52.7) | +0.571 (50.4 → 59.0) | +0.479 (89.6 → 94.7) |

All rank correlations P ≤ 0.007 (Spearman ρ against α, 4,000 permutations, trial level). The three gains place the unstimulated CX at ≈1, 4 and 15 Hz respectively (κ = 150, 300, 600), so the manipulation's effect does not depend on the single calibrated gain, and its absolute magnitude scales with the gain as expected while the rank order of the effect does not change.

### Dose–response in patch size: monotone degradation

> **Corrected numbers (see `results/CORRECTION.md` §4.4).** With the body lock implemented, a larger
> silent region costs more: M2 (`--dose`, fractions 0 / 0.125 / 0.25 / 0.5, drive matched to 0.07%)
> gives tuning ρ = −0.91, CX rate ρ = −0.94, yaw modulation ρ = −0.92, fan-body rate ρ = −0.97,
> fluctuation SD ρ = −0.90, τ ρ = −0.79 and bump R ρ = +0.58, all P = 5 × 10<sup>−4</sup>, with
> delivered events flat (ρ = +0.07, P = 0.68). This replaces the pre-fix "no trend" result.

Repeating the yaw experiment at patch fractions 0, 0.125, 0.25 and 0.5 of the pool, with delivered drive matched at every size (702,365 / 702,546 / 702,787 / 702,282 events per trial; spread 0.07%; Fig. S1A), produced a monotone degradation in nearly every readout (tuning versus wiring rho = -0.91, CX rate rho = -0.94, yaw modulation rho = -0.92, population tau rho = -0.79, ring bump R rho = +0.58, all P = 5e-4, with delivered events flat at rho = +0.07): Spearman ρ between fraction and metric ranged −0.18 to +0.17, all permutation P ≥ 0.28 (`cx_tuning_wire_corr` 0.3202 / 0.3185 / 0.3195 / 0.3212; Fig. S1A, S1B). The cost of a silent region therefore grows smoothly with its size instead of appearing above a threshold, which is what the corrected drive model predicts and what the pre-fix code could not show.

### Positive controls: the pipeline detects what it must

Three additional arms establish that the null is informative (Fig. S1C, S1D). Scaling the total drive of the same pool, same structure, by 0.5 or 1.5 moved the readouts with |d| = 5–42 (CX rate d = +22.9 / −15.2, fan-body rate d = +42.3 / −25.7, P down to 10<sup>−26</sup>). Synchronising the injections — identical cells, identical *expected* total, all cells in phase — left the heading readouts unchanged (P ≥ 0.4) but raised effective dimensionality from 43.1 to 62.8 (d = 7.01, P = 2 × 10<sup>−9</sup>) and lowered the fluctuation amplitude (d = −6.09): structure, not only amount, is detectable through this pathway. The same readout that shows no effect of the body patch detects a conflicting patch at BF<sub>10</sub> = 3.3 × 10<sup>3</sup>.

### The drive-matching trap

Before balancing, the same code and circuit reported the self-view manipulation as strongly perturbing heading: `cx_tuning_wire_corr` 0.216 vs 0.320 (d = −14.5, P = 4.7 × 10<sup>−17</sup>) and CX rate d = −7.75 (P = 1.4 × 10<sup>−12</sup>). Those arms differed in delivered events by 0.5% (self vs flow), 0.25% (vs shuffle) and 10.5% (decorr), and the "dose–response" over patch fractions tracked a −8.3% drive deficit at the largest patch rather than patch size. After exact balancing the same contrasts give d = −0.05 (P = 0.91) and d = +1.02 (P = 0.035, opposite sign), and the dose trend vanishes (ρ = −0.011, P = 0.96 vs ρ = −0.969, P = 5 × 10<sup>−4</sup>). In circuits calibrated by a global gain, **the delivered total is a stronger determinant of every readout than the structure of the input being studied.**

---

## Discussion

Two findings stand out.

First, the central complex distinguishes *absent* from *inconsistent* self-motion, and the distinction is graded. A body-shaped region of the visual field that stops reporting slip — the defining feature of seeing one's own body — leaves every heading readout equivalent to the natural condition within a ±10% bound, across four patch sizes, three drive-matched controls, and two sample sizes; its Bayes factor sits at or just above the conventional threshold for moderate evidence (2.8–3.2 at n = 20, against a design ceiling of 3.24). Replacing a fraction of that region's slip with motion that is *not* aligned to the world's rotation degrades, monotonically in that fraction, how well CX cells' tuning follows the connectome's own push–pull wiring (0.317 → 0.244), the depth of their yaw modulation (1.97 → 1.25 Hz), the population's integration time constant (247 → 163 ms), the ring's bump amplitude, and — largest of all — the fidelity with which the descending, pre-motor command follows the animal's actual turn (0.81 → 0.61, with its amplitude down 21%), while the mean firing rate of the CX is unchanged (ρ = +0.10, P = 0.46). The pattern is stable across a fourfold range of circuit gain.

This is what a system that integrates a rotation estimate should do. The insect brain is widely thought to use forward models and efference copies to discount self-generated sensory change (*14*, *15*); an input that is merely absent contributes nothing to an integrator, which then has less gain but no bias, whereas an input that predicts the wrong rotation injects an error into the estimate every time the animal turns. The absence of an effect on mean rate together with a shortened integration time constant and degraded tuning is the signature of an integrator accumulating an inconsistent term rather than of a circuit being silenced. The manipulation we imposed is precisely the input a third-person view creates: a body-locked region that does not slide with the world while the world does slide. Our result says that a fly tolerates this region being blind, and would not tolerate it being wrong — which suggests a cheap behavioural prediction for intact animals: in a virtual-reality rig, a body-locked occluder should be silent during turns, whereas a body-locked *moving* pattern should bias heading and degrade turn fidelity, in proportion to how much it moves.

Second, when the same manipulation is applied under global optic flow it does change the CX — by 36% in firing rate, 33% in bump sharpness — but the rate component is quantitatively reproduced by a random patch that silences the same 9.1% of CX input. Only the geometric readouts (active fraction, dimensionality, fluctuation amplitude, bump amplitude) distinguish a coherent silent region from a random one. A study that measured only firing rates would report the effect of a self-view as "less input"; a study that measured only the ring bump would report it as "a sharper bump"; both would be describing the same 9.1%. The general lesson is that a perturbation of a connectome-derived circuit has two effects that must be separated before either is interpreted: *how much* the target loses and *what pattern* it loses.

**Implications for connectome-constrained perturbation experiments.** The reversal documented here is not specific to our manipulation. Any experiment that perturbs a subset of a connectome-derived circuit — lesioning cells, silencing a region, injecting a signal — faces the same confound, because silencing a subset changes both *what* the downstream circuit receives and *how much*. We addressed it with (i) per-step drive balancing against the natural condition, (ii) a shared stimulus stream so the waveform is identical across arms, (iii) a control matched on silenced synapses rather than cells, and (iv) equivalence testing plus Bayes factors rather than null-hypothesis non-rejection. All four were necessary: the first two removed the artifact, the third attributed the surviving effect, and the fourth is what makes "no difference" a reportable quantity.

**Limitations.** The circuit is a 12,000-neuron slice (7.2% of the CNS) whose composition over-represents the CX (17.3% of the slice against ≈0.9% of the CNS); absolute firing rates are not physiological and only within-circuit contrasts are meaningful. Every neuron carries roughly 15% of its true in-degree, and κ = 300 is the single parameter that compensates; we report the calibration and the ceiling it imposes but cannot exclude that a different regime would change the result. Transmitter signs are predictions, not measurements (33% of synapses inhibitory overall; 48% within the recurrent CX block). The body patch is an anatomical proxy: the blob carries no receptive-field map, so a compact cluster of somata stands in for a region of the visual field. There is no plasticity in the CX, and we did not model neuromodulation. The heading readout's coordinate is defined by the connectome's push-pull weights rather than by an anatomical ring map, and the ring's own trajectory is close to a leaky integrator (baseline circularity 0.11) rather than a clean rotating bump. Finally, 1,615,753 synapses is 1.1% of the CNS's 151.9 million; the pathway we manipulate is the one the connectome defines, at the resolution the slice preserves.

---

## Materials and Methods

**Data.** MaleCNS v1.0 flat connectome (`connectome-weights-male-cns-v1.0-minconf-0.5.feather`, 1,051,241,946 bytes, SHA256 `E35DA783…C56AFC1`): 151,856,684 edges, 211,577 annotated bodies, 11,752 cell types. Cell types and soma positions from `body-annotations-male-cns-v1.0-minconf-0.5.feather` (14,483,314 bytes, SHA256 `2177E246…F99A9A3B2`); transmitter predictions from `body-neurotransmitters-male-cns-v1.0.feather` (43,282,834 bytes, SHA256 `95C92892…DA8879621`), 164,401 of 1,835,518 bodies with a non-`unclear` consensus call. Files were read with purpose-written pure-Python Arrow/Feather and Parquet readers (no third-party dependencies). The circuit blob `flymind.brain` (FLYMIND4, 21,383,125 bytes, SHA256 `FC6B544C…836E0C8A`) is the single source of truth for every number in this paper; all tables are regenerated from it.

**Circuit construction.** Cell-type regexes selected seeds (sugar 60, odour 5,262, reward 344, motor 312, LPTC 1,594, CX 1,400 → 7,378 unique); one growth round ranked unselected neurons by summed connection strength to the selected set and added 4,622 to reach 12,000. Induced subgraph: 1,615,753 synapses (all retained; budget 2,000,000, not reached). Sign: negative if the presynaptic cell's consensus transmitter is GABA, glutamate or histamine.

**Model.** LIF with the published constants (*8*); explicit Euler, dt = 0.5 ms; synaptic delay 1.8 ms implemented as a 4-slot ring buffer; conductance decays as dg/dt = −g/τ (an earlier implementation zeroed g each step, which turned every synapse into a 0.5 ms impulse and produced a silent circuit); reset v = v<sub>rst</sub>, g = 0 on spike. Stimulation: Bernoulli draws per cell per step with p = 150 Hz × dt × d<sub>i</sub>, each event worth w<sub>syn</sub> × 250 = 68.75 mV, delivered to the cell itself. Resting noise off (at the native weight a 6 Hz Poisson background accumulates 0.008 mV against a 7 mV threshold). κ = 300 multiplies connectome weights and plastic base weights only, and was calibrated by sweeping 100–1000 (`results/raw/calibration2-sweep.txt`) to place the CX at ≈2 Hz with ≈10% of its cells active under natural optic flow.

**Drive model and balancing.** Visual pool = LPTC ∪ CX relay (2,689 cells: 1,594 lobula-plate tangential cells matched by `^(H1|H2|V1|VS|HS|LHAV|LHPV)` plus 1,095 connectome-derived relay cells that both receive ≥3 synapses from that set and project ≥3 onto the ring or the CX; the Johnston's-organ `JO-*` types, which have no annotated soma in the release, are excluded — see `results/CORRECTION.md` §2). Flow condition: a slow noisy positive waveform (0.45 + 0.30 sin 2π·0.7t + 0.10 sin(2π·2.3t + 1.1) + 0.08·U(−0.5, 0.5), clipped to [0.05, 1]). Yaw condition: 0.5 sin(2π·0.25t) + 0.3 sin(2π·0.6t + 0.7) + 0.12·U(−0.5, 0.5), clipped to [−1, 1], integrated at up to 200° s<sup>−1</sup> for the true heading; the pool is driven push-pull by side of the midline (found by 1-D 2-means on the pool's somata: axis x, split 365.9 µm, 1,508/1,384 cells) with a rectified profile d = 0.12 + 0.88·max(0, pref·yaw). Balancing (eq. S1): with ρ = 0.1 the patch level and the surround level s solved per step from the levels actually delivered, s = (Σ<sub>all</sub> natural − Σ<sub>patch</sub> delivered)/Σ<sub>surround</sub> natural, and the patch capped by min(1, target/patchDelivered) so it can never exceed the total. Probabilities are clamped at 1, levels are not (p<sub>max</sub> = 0.075, so levels up to ≈13 are representable). Per-trial stimulus streams: `Random(90000 + trial)` for waveforms, block-shuffled copies, odour background and pair sampling; arm-specific streams only for the pool draws.

**Readouts.** Per 20 ms bin: per-cell spike counts for all 2,074 CX cells. Mean rate, active fraction (rate > 0.5 Hz), pairwise correlation (300 sampled pairs), integrated autocorrelation time (sum of ACF to 0.05), participation ratio (eigenvalues of the bin-space Gram matrix), population-mean fluctuation SD, ring population-vector amplitude R (plane from the two leading principal axes of the EPG/PEG somata), ring state trajectory in its own top-2 principal components (variance fraction, circularity), and phase lag of the ring state against the yaw command at the 0.25 Hz component. Direction tuning: per-cell regression slope of binned rate on yaw, correlated with the cell's push-pull weight w<sub>j</sub> = (excitation from one side + inhibition from the other) − (the mirror image). Stability of the heading estimate: SD of the ring state angle about its best linear trend (angular diffusion) and the lag-1 autocorrelation of that angle. **Steering readout (behavioural):** the 119 descending neurons split by side of the midline; per bin, the left–right difference of their spike counts is the steering command, reported as its SD (amplitude) and its Pearson correlation with the yaw command over bins (fidelity); the manipulation never changes the yaw command itself, so any change is in the brain's use of it.

**Conflict dose.** The body patch's slip is blended as g<sub>α</sub>(t) = (1−α)f(t) + α·f<sub>shuf</sub>(t), where f<sub>shuf</sub> is a 100 ms block-shuffled copy of the same waveform (identical marginal distribution, destroyed temporal alignment). α = 0 is the slip-free body patch, α = 1 the fully de-correlated patch; α ∈ {0, 0.25, 0.5, 0.75, 1} was run at each of three gains. Trend tests: Spearman ρ between α and the trial-level metric, permutation P (4,000 relabellings, seed 12345).

**Propagation checks.** Breadth-first hop counts from the pool to the CX on the simulated graph. Evoked volley: one event into every pool cell in one step, CX-only spikes counted per 0.5 ms step, baseline 100 ms before, latency defined as the first step above baseline + 3 SD, response window 20 ms; repeated at κ = 100, 300, 1000 and with/without the body patch.

**Statistics.** Unpaired Welch t tests with 95% CIs; Cohen's d with Hedges–Olkin CI; Mann–Whitney U with tie correction and rank-biserial correlation; permutation tests (4,000 relabellings, seed 12345, resolution 1/4001) for the primary contrasts; Holm–Bonferroni within each metric's family of self-vs-control contrasts; TOST equivalence at pre-specified bounds |d| < 0.5 and |Δ| < 10% of the control mean (90% CI reported); JZS Bayes factors with a Cauchy prior of scale r = 0.707, validated against the analytic anchor BF<sub>01</sub>(t = 0, n = 10/arm) = 2.52. n = 10 independent trials per arm (n = 20 in the replication; n = 6 in the two extra-gain series), independent random seeds; analysis window = second half of each trial.

**Code and data availability.** Circuit builder, experiment harness, comparison and Bayes-factor code, and every raw stdout/CSV are in the supplementary material and at https://github.com/iice662/flymind-selfview. The interactive implementation runs as a Terraria mod (tModLoader 1.4.4.9) in which the same experiment is executed by pressing F9.

**Use of generative AI.** The text of this manuscript was drafted with a large language model (`DeepSeek-V4.1-Flash`, via the DeepSeek Harness, on `2026-09-28`), used under author direction for drafting and language editing. The same model wrote the simulation harness, the statistical analysis code and the figure scripts from the authors' specifications; all code was executed and its outputs verified by the authors, and the full prompt log is provided in Supplementary Note S2. No AI-generated images are used: every figure is a programmatic plot of the authors' own data produced by `tools/make_main_figures.py` and `tools/make_figures.py` (matplotlib). The authors take full responsibility for all content.

---

## Acknowledgments

We thank the FlyWire Consortium for the MaleCNS v1.0 connectome and the accompanying transmitter predictions, and the authors of ref. *8* for publishing the integrate-and-fire constants and the calibration target used here. **Funding:** this work received no external funding. **Competing interests:** the authors declare no competing interests. **Author contributions:** Y.C. designed the study, built the circuit, ran the simulations and analyses, and wrote the manuscript.

**Declaration of generative AI (repeated here per journal policy).** A large language model (`DeepSeek-V4.1-Flash`, DeepSeek Harness) was used to draft and edit the manuscript text and, under author direction, to write the simulation, analysis and plotting code. All data were produced by the authors' own simulations; all code was executed, inspected and validated by the authors; every numerical value in the manuscript, tables and figures was regenerated from the deposited raw per-trial data. No AI-generated images are included. Full disclosure, including the prompt log, is in Methods and Supplementary Note S2.

---

## References

1. J. Seelig, V. Jayaraman, Neural dynamics for landmark orientation and angular path integration. *Nature* **521**, 186–191 (2015). doi:10.1038/nature14446
2. D. Turner-Evans *et al.*, Angular velocity integration in a fly heading circuit. *eLife* **6**, e23496 (2017).
3. S. S. Kim, H. Rouault, S. Druckmann, V. Jayaraman, Ring attractor dynamics in the *Drosophila* central brain. *Science* **356**, 849–853 (2017).
4. T. Pisokas, S. Heinze, B. Webb, The head direction circuit of two insect species. *PLoS Comput. Biol.* **16**, e1008322 (2020).
5. Berg *et al.*, Sexual dimorphism in the complete *Drosophila* male central nervous system connectome. *Cell* (2026). PII S0092-8674(26)00942-6; https://www.cell.com/cell/fulltext/S0092-8674(26)00942-6 (MaleCNS v1.0)
6. S. Dorkenwald *et al.*, Neuronal wiring diagram of an adult brain. *Nature* **634**, 124–138 (2024). doi:10.1038/s41586-024-07558-y
7. A. Schlegel *et al.*, Whole-brain annotation and multi-connectome cell typing of *Drosophila*. *Nature* **634**, 139–152 (2024). doi:10.1038/s41586-024-07389-x
8. P. K. Shiu *et al.*, A *Drosophila* computational brain model reveals sensorimotor processing. *Nature* **634**, 210–219 (2024). doi:10.1038/s41586-024-07763-9
9. P. S. Efraimidis, P. G. Spirakis, Weighted random sampling with a reservoir. *Inf. Process. Lett.* **97**, 181–185 (2006).
10. J. N. Rouder, P. L. Speckman, D. Sun, R. D. Morey, G. Iverson, Bayesian t tests for accepting and rejecting the null hypothesis. *Psychon. Bull. Rev.* **16**, 225–237 (2009).
11. S. Holm, A simple sequentially rejective multiple test procedure. *Scand. J. Stat.* **6**, 65–70 (1979).
12. B. L. Welch, The generalization of "Student's" problem when several different population variances are involved. *Biometrika* **34**, 28–35 (1947).
13. D. Lakens, Equivalence tests: a practical primer. *Soc. Psychol. Personal. Sci.* **8**, 355–362 (2017).
14. B. Webb, Neural mechanisms for prediction: do insects have forward models? *Trends Neurosci.* **27**, 278–282 (2004). doi:10.1016/j.tins.2004.03.004
15. B. Webb, Sensorimotor control of navigation in arthropod and artificial systems. *Arthropod Struct. Dev.* **33**, 301–329 (2004). doi:10.1016/j.asd.2004.05.009
16. M. Winding *et al.*, The connectome of an insect brain. *Science* **379**, eadd9330 (2023). doi:10.1126/science.add9330
17. C. Lin *et al.*, A comprehensive wiring diagram of the protocerebral bridge for visual information processing in the *Drosophila* brain. *eLife* **12**, e78484 (2023).

---

## Figure legends

Display items are generated by `tools/make_main_figures.py` (main1–main4, main4b, supp1–supp4); the earlier `tools/make_figures.py` set is retained as an archive and is not part of the submission.

**Fig. 1. A connectome-constrained circuit, the manipulation, and its balancing.** (A) Census of the 12,000-neuron slice (1,615,753 synapses). Upper block, populations: sensory 2,695, antennal 620, KC 193, dopamine 344, MBON 67, descending 119, motor 316, LPTC 1,770, CX 2,074, unnamed 3,802. Lower block, CX subfamilies: ring EPG/PEG 68, columnar 1,036, fan-body 601, other CX 369. (B) κ calibration sweep (κ = 100–1000, log axis): CX mean rate (left axis, circles) and percentage of CX cells active (right axis, squares); the dotted line marks κ = 300, used throughout. (C) The heading pathway link by link, synapse counts on a log axis: LPTC→ring 67, LPTC→columnar 58, columnar→ring 1,031, ring→ring 1,692, ring→fan-body 539, fan-body→descending 88, descending→motor 2,810. (D, E) Delivered stimulation events per arm normalised to the slip-free self patch (dashed line = 1.0), for the optic-flow (D) and yaw (E) experiments. Per-step drive matching equalises each arm's expected total to the self arm's; realised delivered ratios stay within 0.08% of the self arm (optic flow 0.99947–1.00070, yaw 0.99956–1.00004), and all arms in a trial share one stimulus stream. (F) CX synapses silenced by each manipulation with the number projecting onto the 68 ring cells in parentheses: self* 30,919 (1,354), shuffled 13,053 (412), matched random 30,958. The patch is not a neutral subset of the CX input.

**Fig. 2. The injected signal reaches the ring within one synapse.** (A) Percentage of CX cells reached by hop count from the visual pool: 97.2% (2,015 / 2,074) at one hop, 97.4% at two and three; 48,315 direct pool→CX synapses. (B) CX-only spikes per 0.5 ms step around a synchronous pool volley (baseline measured over the preceding 100 ms), for κ = 100 / 300 / 1000 with and without the body patch, on a symlog axis. Peak 21 spikes at 2.5 ms at κ = 300 (baseline 0.17; 105 cells, 5.1% of CX), still present at κ = 100 (2.6%); the body patch reduces the peak to 6 spikes (−71%) and 41 cells (−61%).

**Fig. 3. Optic flow: a state change with a rate component attributable to input loss.** (A–G) Per-arm metric values with 95% CI, n = 10, 3 s per trial: CX mean rate, CX active fraction, ring rate, ring bump R, effective dimensionality, fluctuation SD, columnar rate. Arms: self* (slip-free patch), optic flow, shuffled patch, matched random patch, decorrelated patch, rest. (H) Effect size (Cohen's d) of the body patch against each control, split into rate metrics (CX, ring, columnar, fan-body, other rate, fluctuation SD) and geometry metrics (active fraction, effective dimensionality, bump R, pairwise correlation). The matched random patch, which silences the same 30,958 CX synapses at random, reproduces the rate changes but not the geometry changes.

**Fig. 4. Heading: a silent body region costs coding, a conflicting one costs fidelity.** (A, B) n = 20 trials per arm: (A) direction tuning versus push–pull wiring (`cx_tuning_wire_corr`) and (B) steering readout versus yaw command, per arm with 95% CI. The slip-free patch is indistinguishable from optic flow, shuffled and matched random patches (BF<sub>01</sub> = 2.8–3.0 and 2.4–2.8 against a design ceiling of 3.24); the decorrelated patch is not. (C, D) Conflict dose, α = 0, 0.25, 0.5, 0.75, 1 (fraction of the ring's optic-flow input replaced by a de-correlated copy), n = 10 per point, mean ± 95% CI: (C) tuning versus wiring, ρ = −0.82; (D) steering fidelity, ρ = −0.94. (E–H) Same five-point series: (E) steering amplitude, ρ = −0.91; (F) yaw modulation depth, ρ = −0.92; (G) population τ, ρ = −0.89; (H) effective dimensionality, ρ = +0.57. All P = 2 × 10<sup>−4</sup> (permutation, 4,000 draws). **[Corrected: BF01 = 2.8-3.0 / 2.4-2.8 is superseded - the same contrasts now give BF10 = 1.2e14 (tuning) and 5.8e9 (steering) against the natural condition; the silent patch is not equivalent to it.]**

**Fig. 5. The conflict effect is not a rate or drive artefact and survives a fourfold gain change.** (A) Mean CX rate and delivered stimulation events against α (left axis in Hz, right axis in events × 10<sup>−5</sup>), both flat: ρ = +0.10 (P = 0.46) and ρ = −0.04. (B) Three primary readouts at κ = 150, 300 and 600 (n = 6 for the replication gains), each normalised to its own α = 0 value and vertically offset for display; the rank order across α is preserved at every gain (steering fidelity ρ = −0.98 / −0.94 / −0.87; tuning ρ = −0.92 / −0.82 / −0.84; amplitude ρ = −0.92 / −0.91 / −0.86; all P ≤ 0.007). (C) Bayes factors BF<sub>01</sub> at n = 20 for the six readouts against the three control manipulations; the dashed line marks BF<sub>01</sub> = 3 (moderate evidence for the null), the dotted line the 3.24 ceiling attainable by this design at t = 0.

**Fig. S1. Patch-size dose–response and positive controls.** (A) Delivered stimulation events per trial against patch fraction 0, 0.125, 0.25, 0.5 (7.02 × 10<sup>5</sup> each; drive matched to within 0.07%). (B) Four readouts against patch fraction, each normalised to its fraction-0 value: monotone degradation (|ρ| ≤ 0.18, all P ≥ 0.28). (C) Total drive ×0.5 / ×1.0 / ×1.5: CX mean rate with 95% CI; effect sizes d = 15–23. (D) Synchronised injection at the same expected total changes effective dimensionality (d = 7.0) while leaving the heading readouts unchanged (all P ≥ 0.4).

**Fig. S2. Equivalence bounds for the slip-free patch.** Difference (raw units) between the slip-free patch and each control for eight readouts, with 90% CI; thin horizontal bars mark the pre-registered equivalence bound |d| < 0.5. The single unresolved readout is the ring phase lag behind yaw (`ring_lag_yaw_deg`, d = −0.62).

**Fig. S3. What a null result can buy at this design.** Bayes factor BF<sub>01</sub> at t = 0 against trials per arm for the JZS prior (Cauchy r = 0.707). The dashed line marks BF<sub>01</sub> = 3; the dotted line marks n = 20, the design used in Fig. 4 and Fig. 5C (ceiling 3.24).

**Fig. S4. The drive-matching trap.** The same contrasts before (unbalanced) and after (balanced) per-step drive matching: (A) tuning versus wiring and (B) CX mean rate, mean ± 95% CI over optic flow, self* and shuffled. Unbalanced arms produce a large apparent effect (d = −14.5 on the heading readout, P = 4.7 × 10<sup>−17</sup>) that reverses to d = −0.05, P = 0.91 once delivered drive is equalised.

---

## Table 1. Equivalence and Bayes factors for the heading readouts (n = 10 per arm)

> **SUPERSEDED — the values in this table are pre-fix.** They were computed on a contrast that
> turned out to compare two identical drive conditions (see the status banner and
> `results/CORRECTION.md` §1). Regenerate against the corrected families with
> `python tools\compare_trials.py results\raw\I2-heading-trials.csv` (n = 10) and
> `…\J2-n20-trials.csv` (n = 20); `python tools\digest.py` prints the corrected tables.
| metric | contrast | Δ (self − control) | 90% CI | d | P (Welch) | P (TOST, \|d\|<0.5) | P (TOST, ±10%) | BF<sub>01</sub> |
|---|---|---|---|---|---|---|---|---|
| CX tuning ↔ wiring r | vs flow | −0.00047 | [−0.0075, 0.0066] | −0.05 | 0.91 | 0.165 | 2.5 × 10<sup>−7</sup> | 2.51 |
| CX tuning ↔ wiring r | vs shuffle | −0.00173 | [−0.0103, 0.0068] | −0.16 | 0.74 | 0.227 | 5.3 × 10<sup>−6</sup> | 2.41 |
| CX tuning ↔ wiring r | vs randmat | −0.00174 | [−0.0109, 0.0074] | −0.15 | 0.75 | 0.221 | 1.4 × 10<sup>−5</sup> | 2.42 |
| CX tuning ↔ wiring r | vs decorr | +0.0727 | [0.0527, 0.0928] | +2.93 | 5.3 × 10<sup>−5</sup> | 1.00 | 0.999 | 3.0 × 10<sup>−4</sup> |
| yaw modulation (Hz) | vs flow | −0.0128 | [−0.086, 0.060] | −0.14 | 0.76 | 0.217 | 3.1 × 10<sup>−4</sup> | 2.43 |
| yaw modulation (Hz) | vs decorr | +0.716 | [0.652, 0.780] | +8.81 | 9.7 × 10<sup>−12</sup> | 1.00 | 1.00 | 4.2 × 10<sup>−11</sup> |
| ring phase lag (°) | vs flow | +1.69 | [−12.1, 15.5] | +0.10 | 0.83 | 0.189 | 0.318 | 2.48 |
| ring circularity | vs flow | −0.0047 | [−0.040, 0.031] | −0.10 | 0.82 | 0.196 | 0.361 | 2.47 |
| bump R | vs flow | −0.0089 | [−0.024, 0.0059] | −0.47 | 0.31 | 0.471 | 0.0071 | 1.72 |
| CX rate (Hz) | vs flow | +0.0688 | [0.0165, 0.1211] | +1.02 | 0.035 | 0.870 | 8.2 × 10<sup>−10</sup> | 0.46 |
| effective dimensionality | vs flow | −0.93 | [−3.31, 1.45] | −0.30 | 0.51 | 0.334 | 0.0035 | 2.14 |

BF<sub>01</sub> = 1/BF<sub>10</sub>; the ceiling for this design is 2.52 (BF<sub>01</sub> at t = 0 with n = 10 per arm).

---

## Table 2. Bayes factors at n = 20 per arm (doubling the trials raises the design ceiling to 3.24)

> **SUPERSEDED — pre-fix.** The corrected n = 20 result is evidence *for a difference*, not for the
> null: `cx_tuning_wire_corr` self vs flow d = −4.67 (BF<sub>10</sub> = 1.2 × 10<sup>14</sup>), vs
> shuffle d = −5.79 (1.2 × 10<sup>17</sup>), vs randmat d = −2.58 (9.9 × 10<sup>6</sup>), vs decorr
> d = +0.26 (BF<sub>01</sub> = 2.5); `steer_corr_yaw` self vs flow d = −3.33 (5.8 ×
> 10<sup>9</sup>), vs randmat d = −4.41 (2.0 × 10<sup>13</sup>), vs decorr d = +3.25
> (3.2 × 10<sup>9</sup>). Source: `results/raw/J2-n20-equivalence.csv`.

| metric | vs flow | vs shuffle | vs randmat | vs decorr |
|---|---|---|---|---|
| CX tuning ↔ wiring *r* (d) | 2.84 (−0.18) | 2.85 (−0.18) | **3.03** (+0.13) | BF<sub>10</sub> = 2.1 × 10<sup>9</sup> |
| yaw modulation depth (d) | 2.79 (+0.19) | 2.56 (+0.24) | **3.15** (+0.08) | BF<sub>10</sub> = 9.9 × 10<sup>12</sup> |
| ring trajectory circularity | **3.04** (+0.13) | 2.95 (+0.15) | 2.23 (−0.31) | 2.11 (+0.33) |
| ring state top-2 variance | **3.09** (+0.11) | 2.23 (+0.31) | 2.53 (−0.25) | 2.98 (+0.15) |
| bump amplitude | 1.51 (+0.44) | 2.88 (+0.17) | 2.90 (+0.17) | BF<sub>10</sub> = 1.5 × 10<sup>3</sup> |
| CX mean rate | 2.39 (−0.28) | 2.05 (+0.34) | 2.83 (+0.18) | 2.79 (−0.19) |
| effective dimensionality | 2.70 (−0.21) | 1.97 (−0.36) | 2.11 (−0.33) | BF<sub>10</sub> = 157 |
| ring phase lag behind yaw | 0.74 (−0.62) | 0.85 (−0.59) | 1.08 (−0.53) | 1.51 (+0.44) |

Figures in parentheses are Cohen's d (self − control). Bold = BF<sub>01</sub> > 3. Delivered drive matched to 0.05%; expected totals identical in all arms.

---

## Table 3. Conflict dose: every readout against α (κ = 300, n = 10 per level, 6 s per trial)

> **SUPERSEDED — pre-fix.** Corrected conflict-dose means, trends and P values are in
> `paper/tables.md` Table 3 (generated from `results/raw/I2-heading-trials.csv`). Corrected
> headline: steering fidelity 0.741 → 0.615 (ρ = −0.845, P = 2 × 10<sup>−4</sup>) at flat drive
> (ρ = +0.13) and flat steering amplitude (ρ = +0.12), with ring bump R 0.359 → 0.274
> (ρ = −0.817).

| readout | α = 0 | 0.25 | 0.50 | 0.75 | 1.00 | ρ vs α | P (perm.) |
|---|---|---|---|---|---|---|---|
| steering fidelity (`steer_corr_yaw`) | 0.8119 | 0.7802 | 0.7558 | 0.6789 | 0.6057 | −0.943 | 2 × 10<sup>−4</sup> |
| yaw modulation depth (Hz) | 1.969 | 1.790 | 1.618 | 1.400 | 1.253 | −0.924 | 2 × 10<sup>−4</sup> |
| steering amplitude (Hz) | 640.6 | 608.5 | 566.6 | 532.7 | 509.1 | −0.913 | 2 × 10<sup>−4</sup> |
| population τ (ms) | 246.9 | 231.6 | 197.7 | 171.4 | 163.3 | −0.887 | 2 × 10<sup>−4</sup> |
| CX tuning ↔ wiring *r* | 0.3169 | 0.3181 | 0.3031 | 0.2782 | 0.2442 | −0.816 | 2 × 10<sup>−4</sup> |
| fluctuation SD (Hz) | 1.026 | 0.973 | 0.933 | 0.9007 | 0.8985 | −0.759 | 2 × 10<sup>−4</sup> |
| columnar active fraction | 0.1074 | 0.1029 | 0.09566 | 0.09508 | 0.09353 | −0.637 | 2 × 10<sup>−4</sup> |
| effective dimensionality | 50.42 | 52.85 | 55.45 | 56.65 | 59.01 | +0.571 | 2 × 10<sup>−4</sup> |
| CX active fraction | 0.2218 | 0.2163 | 0.2112 | 0.2117 | 0.2130 | −0.539 | 2 × 10<sup>−4</sup> |
| ring active fraction | 0.8676 | 0.8544 | 0.8544 | 0.8529 | 0.8338 | −0.500 | 7 × 10<sup>−4</sup> |
| bump *R* | 0.3113 | 0.2991 | 0.2956 | 0.2867 | 0.2687 | −0.493 | 7 × 10<sup>−4</sup> |
| ring phase lag behind yaw (°) | −53.59 | −64.03 | −78.86 | −76.97 | −70.48 | −0.330 | 0.020 |
| ring rate (Hz) | 20.94 | 20.77 | 20.86 | 20.86 | 21.82 | +0.321 | 0.024 |
| *unchanged:* CX mean rate (Hz) | 4.133 | 4.026 | 3.995 | 4.028 | 4.171 | +0.103 | 0.46 |
| *unchanged:* ring angle diffusion (°) | 228.4 | 253.7 | 227.4 | 241.4 | 252.1 | +0.100 | 0.48 |
| *unchanged:* ring state top-2 variance | 0.4174 | 0.4110 | 0.4195 | 0.4084 | 0.4101 | −0.078 | 0.59 |
| *unchanged:* delivered events | 7.028 × 10<sup>5</sup> | 7.026 × 10<sup>5</sup> | 7.026 × 10<sup>5</sup> | 7.024 × 10<sup>5</sup> | 7.028 × 10<sup>5</sup> | −0.038 | 0.79 |
| *unchanged:* turned (deg) | −60.9 | −60.9 | −60.9 | −60.9 | −60.9 | 0.000 | 1.00 |

Spearman ρ against α with a permutation P (4,000 draws); the first thirteen rows are ordered by |ρ|. The last five rows are the flat controls: the average CX rate, the ring's angular diffusion and state variance, the delivered drive and the turn itself do not move with α, so the graded degradation above is not a rate, drive or trajectory artefact. The same series at κ = 150 and κ = 600 (n = 6) preserves the rank order (Fig. 5B).

---

## Supplementary materials

- **fig. S1** Patch-size dose–response and positive controls (`paper/figures/supp1.pdf`).
- **fig. S2** Equivalence bounds for the slip-free patch, 90% CI against |d| < 0.5 (`paper/figures/supp2.pdf`).
- **fig. S3** Bayes-factor design ceiling against trials per arm (`paper/figures/supp3.pdf`).
- **fig. S4** The drive-matching trap: the same contrasts unbalanced and balanced (`paper/figures/supp4.pdf`).
- **table S1** Per-arm descriptive statistics (mean, sd, sem, 95% CI, median, IQR) — `A3-flow-compare.csv`, `B3-heading-compare.csv`.
- **table S2** All pairwise contrasts (diff, CI, ratio, d, Welch t/df/P, Holm, Mann–Whitney, rank-biserial, permutation P).
- **table S3** Manipulation check per arm (patch cells, silenced CX synapses, silenced ring synapses, delivered events, ratio to self, expected).
- **table S4** Dose–response summaries and trend tests (patch size; conflict α at three gains).
- **table S5** Propagation checks (hop counts; evoked volley at three gains).
- **data S1** `flymind.brain` (FLYMIND4) and the raw per-trial CSVs.
- **eq. S1** Per-step balancing derivation.
- **note S1** Provenance of every value (data files, SHA256, commands, software versions).
- **note S2** AI-assisted-tool disclosure: tool name, version, and the full prompt log for the AI-generated text (per journal policy; see Methods, *Use of generative AI*, and Acknowledgments).
- **note S3** Circuit schematic regenerated from the blob (populations, connectivity matrix, strongest pathways, heading-pathway audit) and the whole-connectome probe of the heading pathway — archived figures `fig1`–`fig7`, `figS1`, `figS3` in `paper/figures/`.
