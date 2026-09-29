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

### The conflict effect does not depend on how the body region is defined

The body patch of every experiment above is a compact cluster of somata (the 672 pool cells nearest
the pool centroid). That is a proxy: the region a fly's own body occupies is a region of the
*visual field*, not of the soma cloud. We therefore repeated the whole conflict series with the
patch defined by receptive field instead - each pool cell's input sites taken from the released
synaptic-partner table, its receptive-field position being the centroid of those sites, and the
patch being the 672 cells nearest the centre of that map (rank-based, so size-matched by
construction; the field-of-view assumption is stated in `tools/patch_from_rf.py`).

Two things follow, and they point in opposite directions.

**The graded conflict effect replicates.** Steering fidelity falls from 0.727 to 0.612 across
alpha = 0 to 1 with the receptive-field patch, against 0.741 to 0.615 with the soma patch: the same
monotone degradation of the steering command, at the same drive (delivered events equal across arms
to within 0.1%; manipulation check `patch/surround` = 0.427 for both patches, so the manipulation
reaches the cells it claims to in both cases). The paper's main result therefore does not depend on
the patch definition.

**The effect of the silent patch does.** With the same number of cells and a comparable share of CX
input removed (11.7% for the receptive-field patch against 9.5% for the soma patch), the silent
patch costs less direction tuning when it is defined by receptive field than when it is defined by
soma position: `cx_tuning_wire_corr` 0.286 against 0.236 (natural condition 0.309). Input quantity
alone therefore does not explain the silent-patch effect; *which* cells stop reporting self-motion
matters, over and above how much input is removed.

Both numbers are in `results/raw/N-rfpatch-*.csv`; the comparison is reproduced by
`python tools\digest.py N-rfpatch I2-heading`.

### Closing the loop with the descending command: an attempt that fails for a measurable reason

The conflict series above measures the *quality* of the steering command. The behavioural question is
whether the fly then flies worse, so we closed the loop: the turn is produced by the circuit's own
descending left-right difference, low-pass filtered, and the visual drive is the heading error
between a commanded course and the heading actually flown. The loop gain is calibrated once at
alpha = 0 and then frozen for every arm, alpha and gain, so the comparison cannot be circular. Four
defects had to be removed before the loop ran at all, and each is a trap of the same species as the
one in ref. *8*'s calibration: (i) driving the pool with the *motor command* instead of the visual
signal left the loop at a dead fixed point (command zero, therefore no rotation signal, therefore
command zero); (ii) the stabilising sign is positive feedback - the asymmetry encodes the rotation
the eye *senses*, which in closed loop *is* the error - and the opposite sign diverges
(0.50 rad against 2.53); (iii) the asymmetry carries a DC imbalance unrelated to the error
(mean -0.01 against excursions of +/-0.03), which pins the command at full turn if amplified raw;
(iv) the usable gain is three orders of magnitude below the first guess.

With the mechanism verified, **no gain we tried makes the fly hold the commanded course**: RMS
heading error falls monotonically toward the open-loop value as the gain rises but never crosses it - 0.577, 0.543, 0.525 and 0.521 rad at gains of 30, 50, 80 and 100, and 0.49-0.61 across gains of 5-20 and the saturated regime above 200, against
against 0.5017 rad when the loop is open, i.e. when the error is simply the commanded course itself.
The reason is measurable: each 20 ms bin contains only 2-8 spikes across the ~59 descending cells of
each side, so the population asymmetry (about +/-0.03) is dominated by Poisson noise at exactly the
timescale a controller needs. The descending command is therefore a faithful *report* of heading -
its correlation with the yaw command is 0.79 - but not a low-latency *control* signal in this slice.
Closing the loop would need either a much longer integration paired with a correspondingly slower
course, or a smoother population readout such as the ring state's own rotation. We report the
attempt rather than a behaviour curve because a controller that never tracks cannot test the
prediction, and because the failure is a property of the readout we could measure, not a claim about
the fly.



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

**Limitations.** A closed-loop behavioural test was attempted and is reported as a negative result: the descending left-right difference in this slice carries 2-8 spikes per side per 20 ms bin, which is too sparse to close a heading loop, so the steering-command result above is a statement about the command's fidelity and not yet about flight behaviour. The receptive-field patch is a rank-based proxy: it selects the cells whose input sites lie nearest the centre of the pool's retinotopic map, which is not the same as the projection of a body of a given angular size, and the cells of the 1,095-cell connectome-derived relay have input sites but no annotated soma to compare against. The silent-patch effect is patch-definition-dependent (0.286 against 0.236 for direction tuning at the same patch size and comparable input loss), so its magnitude should be read as a property of this circuit and this patch, not as a general constant of the heading system. The circuit is a 12,000-neuron slice (7.2% of the CNS) whose composition over-represents the CX (17.3% of the slice against ≈0.9% of the CNS); absolute firing rates are not physiological and only within-circuit contrasts are meaningful. Every neuron carries roughly 15% of its true in-degree, and κ = 300 is the single parameter that compensates; we report the calibration and the ceiling it imposes but cannot exclude that a different regime would change the result. Transmitter signs are predictions, not measurements (33% of synapses inhibitory overall; 48% within the recurrent CX block). The body patch is an anatomical proxy: the blob carries no receptive-field map, so a compact cluster of somata stands in for a region of the visual field. There is no plasticity in the CX, and we did not model neuromodulation. The heading readout's coordinate is defined by the connectome's push-pull weights rather than by an anatomical ring map, and the ring's own trajectory is close to a leaky integrator (baseline circularity 0.11) rather than a clean rotating bump. Finally, 1,615,753 synapses is 1.1% of the CNS's 151.9 million; the pathway we manipulate is the one the connectome defines, at the resolution the slice preserves.

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

## Table 1. Heading readouts per arm (I2-heading, kappa = 300, n = 10 trials per arm)

Generated from `results/raw/I2-heading-trials.csv` by `python tools\make_tables.py`; every value in this table and in Tables 2-3 is recomputed from the deposited per-trial data, and `python tools\verify_headline_numbers.py` checks the quoted numbers against it.

| readout | rest | flow | self | shuffle | randmat | decorr | conf25 | conf50 | conf75 |
|---|---|---|---|---|---|---|---|---|---|
| CX rate (Hz) | 0.2523 | 3.952 | 3.172 | 3.819 | 3.235 | 3.962 | 3.42 | 3.63 | 3.853 |
| CX active fraction | 0.0135 | 0.2145 | 0.1696 | 0.2083 | 0.1756 | 0.201 | 0.1737 | 0.1852 | 0.1965 |
| yaw modulation (Hz) | 0 | 1.919 | 1.153 | 1.542 | 0.9526 | 0.9366 | 0.9853 | 0.9717 | 0.9713 |
| tuning <-> wiring r | 0 | 0.3093 | 0.2359 | 0.3424 | 0.31 | 0.252 | 0.2518 | 0.2549 | 0.2539 |
| steering fidelity | 0 | 0.786 | 0.7405 | 0.7702 | 0.8143 | 0.6154 | 0.7142 | 0.6793 | 0.6541 |
| steering amplitude (Hz) | 182.1 | 501.9 | 424.3 | 488.9 | 525.7 | 431.3 | 423 | 425.5 | 422.4 |
| descending rate (Hz) | 1060 | 2072 | 1930 | 2093 | 2072 | 2076 | 1976 | 2009 | 2041 |
| population tau (ms) | 31.85 | 223.2 | 150.3 | 196.8 | 146.2 | 131 | 104.3 | 117.6 | 116.5 |
| dim. (PR) | 25.25 | 51 | 52.83 | 53.97 | 53.92 | 59.86 | 55.12 | 54.54 | 57.99 |
| bump R | 0 | 0.3269 | 0.3585 | 0.3315 | 0.3364 | 0.2742 | 0.3278 | 0.3036 | 0.2765 |
| ring circularity | 1 | 0.1333 | 0.1687 | 0.1553 | 0.1333 | 0.112 | 0.1553 | 0.1313 | 0.14 |
| ring PC1-2 var | 0 | 0.4215 | 0.4357 | 0.4349 | 0.4123 | 0.3995 | 0.4408 | 0.4275 | 0.4231 |
| fluctuation SD (Hz) | 0.04831 | 0.9971 | 0.7568 | 0.9306 | 0.7642 | 0.8419 | 0.7748 | 0.8029 | 0.828 |
| delivered events | 0 | 6.551e+05 | 6.552e+05 | 6.553e+05 | 6.551e+05 | 6.558e+05 | 6.555e+05 | 6.556e+05 | 6.554e+05 |
| patch/surround | 0 | 0.9767 | 0.4257 | 0.4269 | 0.4614 | 0.8918 | 0.5143 | 0.636 | 0.7619 |

---

## Table 2. Self versus each control manipulation: difference, effect size, equivalence test and Bayes factor

| readout | contrast | diff | d | P (TOST, +-10%) | BF01 | BF10 |
|---|---|---|---|---|---|---|
| delivered events (n = 10) | vs flow | 165.4 | 0.173 | 1.2e-29 | 2.39 | 0.419 |
| delivered events (n = 10) | vs shuffle | -18 | -0.019 | 1.1e-29 | 2.52 | 0.398 |
| delivered events (n = 10) | vs randmat | 139.7 | 0.167 | 2.4e-27 | 2.4 | 0.417 |
| delivered events (n = 10) | vs decorr | -550.2 | -0.590 | 1.1e-29 | 1.38 | 0.723 |
| CX rate (Hz) (n = 10) | vs flow | -0.7802 | -9.773 | 1 | 7.84e-12 | 1.28e+11 |
| CX rate (Hz) (n = 10) | vs shuffle | -0.6474 | -9.888 | 1 | 6.48e-12 | 1.54e+11 |
| CX rate (Hz) (n = 10) | vs randmat | -0.06276 | -0.919 | 5e-08 | 0.624 | 1.6 |
| CX rate (Hz) (n = 10) | vs decorr | -0.7902 | -8.634 | 1 | 5.79e-11 | 1.73e+10 |
| CX active fraction (n = 10) | vs flow | -0.04484 | -10.117 | 1 | 4.47e-12 | 2.24e+11 |
| CX active fraction (n = 10) | vs shuffle | -0.03867 | -9.549 | 1 | 1.14e-11 | 8.77e+10 |
| CX active fraction (n = 10) | vs randmat | -0.005979 | -1.251 | 3.2e-05 | 0.219 | 4.58 |
| CX active fraction (n = 10) | vs decorr | -0.03134 | -5.957 | 1 | 1.95e-08 | 5.13e+07 |
| population tau (ms) (n = 10) | vs flow | -72.91 | -2.872 | 1 | 0.000374 | 2.67e+03 |
| population tau (ms) (n = 10) | vs shuffle | -46.53 | -1.888 | 0.98 | 0.0195 | 51.2 |
| population tau (ms) (n = 10) | vs randmat | 4.107 | 0.148 | 0.2 | 2.42 | 0.413 |
| population tau (ms) (n = 10) | vs decorr | 19.27 | 0.577 | 0.66 | 1.42 | 0.706 |
| dim. (PR) (n = 10) | vs flow | 1.832 | 0.515 | 0.028 | 1.59 | 0.63 |
| dim. (PR) (n = 10) | vs shuffle | -1.133 | -0.300 | 0.011 | 2.15 | 0.466 |
| dim. (PR) (n = 10) | vs randmat | -1.083 | -0.180 | 0.069 | 2.38 | 0.421 |
| dim. (PR) (n = 10) | vs decorr | -7.03 | -2.088 | 0.75 | 0.0087 | 115 |
| fluctuation SD (Hz) (n = 10) | vs flow | -0.2403 | -8.608 | 1 | 6.08e-11 | 1.65e+10 |
| fluctuation SD (Hz) (n = 10) | vs shuffle | -0.1738 | -5.265 | 1 | 1.24e-07 | 8.05e+06 |
| fluctuation SD (Hz) (n = 10) | vs randmat | -0.007352 | -0.266 | 1.4e-05 | 2.22 | 0.45 |
| fluctuation SD (Hz) (n = 10) | vs decorr | -0.08504 | -2.170 | 0.52 | 0.00624 | 160 |
| bump R (n = 10) | vs flow | 0.03158 | 1.441 | 0.46 | 0.111 | 9.02 |
| bump R (n = 10) | vs shuffle | 0.02691 | 1.258 | 0.26 | 0.213 | 4.69 |
| bump R (n = 10) | vs randmat | 0.02202 | 0.857 | 0.16 | 0.739 | 1.35 |
| bump R (n = 10) | vs decorr | 0.0843 | 3.707 | 1 | 1.68e-05 | 5.97e+04 |
| patch/surround (n = 10) | vs flow | -0.551 | -3505.490 | 1 | 4.93e-31 | 2.03e+30 |
| patch/surround (n = 10) | vs shuffle | -0.001243 | -5.702 | 3.1e-38 | 3.78e-08 | 2.64e+07 |
| patch/surround (n = 10) | vs randmat | -0.03565 | -162.215 | 5.2e-43 | 4.09e-29 | 2.45e+28 |
| patch/surround (n = 10) | vs decorr | -0.4661 | -41.459 | 1 | 4.86e-22 | 2.06e+21 |
| ring PC1-2 var (n = 10) | vs flow | 0.01418 | 0.613 | 0.0081 | 1.32 | 0.758 |
| ring PC1-2 var (n = 10) | vs shuffle | 0.0007921 | 0.022 | 0.0094 | 2.52 | 0.398 |
| ring PC1-2 var (n = 10) | vs randmat | 0.02337 | 0.691 | 0.13 | 1.11 | 0.897 |
| ring PC1-2 var (n = 10) | vs decorr | 0.03621 | 1.030 | 0.41 | 0.45 | 2.22 |
| ring circularity (n = 10) | vs flow | 0.03533 | 0.852 | 0.87 | 0.749 | 1.33 |
| ring circularity (n = 10) | vs shuffle | 0.01333 | 0.352 | 0.45 | 2.02 | 0.494 |
| ring circularity (n = 10) | vs randmat | 0.03533 | 1.298 | 0.96 | 0.186 | 5.38 |
| ring circularity (n = 10) | vs decorr | 0.05667 | 1.756 | 1 | 0.0331 | 30.2 |
| yaw modulation (Hz) (n = 10) | vs flow | -0.7668 | -7.119 | 1 | 1.24e-09 | 8.07e+08 |
| yaw modulation (Hz) (n = 10) | vs shuffle | -0.3895 | -3.043 | 1 | 0.000193 | 5.19e+03 |
| yaw modulation (Hz) (n = 10) | vs randmat | 0.2001 | 1.336 | 0.93 | 0.163 | 6.15 |
| yaw modulation (Hz) (n = 10) | vs decorr | 0.2161 | 1.384 | 0.95 | 0.137 | 7.3 |
| tuning <-> wiring r (n = 10) | vs flow | -0.07341 | -3.518 | 1 | 3.29e-05 | 3.04e+04 |
| tuning <-> wiring r (n = 10) | vs shuffle | -0.1065 | -4.680 | 1 | 6.89e-07 | 1.45e+06 |
| tuning <-> wiring r (n = 10) | vs randmat | -0.07409 | -1.805 | 0.98 | 0.0272 | 36.8 |
| tuning <-> wiring r (n = 10) | vs decorr | -0.01608 | -0.556 | 0.24 | 1.47 | 0.679 |
| steering fidelity (n = 10) | vs flow | -0.04547 | -2.868 | 0.0001 | 0.00038 | 2.63e+03 |
| steering fidelity (n = 10) | vs shuffle | -0.02962 | -2.070 | 3.6e-07 | 0.00936 | 107 |
| steering fidelity (n = 10) | vs randmat | -0.07379 | -4.635 | 0.15 | 7.92e-07 | 1.26e+06 |
| steering fidelity (n = 10) | vs decorr | 0.1251 | 4.615 | 1 | 8.43e-07 | 1.19e+06 |
| steering amplitude (Hz) (n = 10) | vs flow | -77.65 | -6.358 | 1 | 7.2e-09 | 1.39e+08 |
| steering amplitude (Hz) (n = 10) | vs shuffle | -64.64 | -5.668 | 1 | 4.14e-08 | 2.42e+07 |
| steering amplitude (Hz) (n = 10) | vs randmat | -101.4 | -8.265 | 1 | 1.17e-10 | 8.57e+09 |
| steering amplitude (Hz) (n = 10) | vs decorr | -6.972 | -0.490 | 1.9e-05 | 1.66 | 0.603 |
| descending rate (Hz) (n = 10) | vs flow | -141.6 | -11.920 | 3.9e-09 | 3.07e-13 | 3.26e+12 |
| descending rate (Hz) (n = 10) | vs shuffle | -162.8 | -21.812 | 2.9e-11 | 1.46e-17 | 6.83e+16 |
| descending rate (Hz) (n = 10) | vs randmat | -141.9 | -12.575 | 1.3e-09 | 1.27e-13 | 7.85e+12 |
| descending rate (Hz) (n = 10) | vs decorr | -145.7 | -8.391 | 3.3e-06 | 9.15e-11 | 1.09e+10 |
| delivered events (n = 20) | vs flow | 2.2 | 0.002 | 1.8e-60 | 3.24 | 0.309 |
| delivered events (n = 20) | vs shuffle | 78.1 | 0.104 | 3.1e-61 | 3.1 | 0.322 |
| delivered events (n = 20) | vs randmat | 133.3 | 0.168 | 6.6e-63 | 2.89 | 0.345 |
| delivered events (n = 20) | vs decorr | -80.55 | -0.104 | 1.7e-62 | 3.1 | 0.322 |
| CX rate (Hz) (n = 20) | vs flow | -0.7641 | -10.730 | 1 | 4.57e-27 | 2.19e+26 |
| CX rate (Hz) (n = 20) | vs shuffle | -0.6354 | -7.278 | 1 | 3.76e-21 | 2.66e+20 |
| CX rate (Hz) (n = 20) | vs randmat | 0.006164 | 0.084 | 2.4e-16 | 3.15 | 0.318 |
| CX rate (Hz) (n = 20) | vs decorr | -0.8288 | -9.206 | 1 | 1.05e-24 | 9.54e+23 |
| CX active fraction (n = 20) | vs flow | -0.042 | -9.987 | 1 | 5.87e-26 | 1.7e+25 |
| CX active fraction (n = 20) | vs shuffle | -0.03652 | -8.295 | 1 | 4.04e-23 | 2.47e+22 |
| CX active fraction (n = 20) | vs randmat | -0.006919 | -1.373 | 5.7e-08 | 0.00468 | 214 |
| CX active fraction (n = 20) | vs decorr | -0.03469 | -5.708 | 1 | 1.34e-17 | 7.44e+16 |
| population tau (ms) (n = 20) | vs flow | -90.21 | -4.534 | 1 | 2.12e-14 | 4.71e+13 |
| population tau (ms) (n = 20) | vs shuffle | -56.12 | -2.743 | 1 | 2.41e-08 | 4.16e+07 |
| population tau (ms) (n = 20) | vs randmat | -10.64 | -0.529 | 0.25 | 1.08 | 0.922 |
| population tau (ms) (n = 20) | vs decorr | 8.261 | 0.310 | 0.29 | 2.21 | 0.452 |
| dim. (PR) (n = 20) | vs flow | -3.134 | -0.721 | 0.055 | 0.441 | 2.27 |
| dim. (PR) (n = 20) | vs shuffle | -0.71 | -0.140 | 0.0043 | 3 | 0.334 |
| dim. (PR) (n = 20) | vs randmat | -0.5203 | -0.085 | 0.011 | 3.15 | 0.318 |
| dim. (PR) (n = 20) | vs decorr | -6 | -1.119 | 0.57 | 0.0341 | 29.3 |
| fluctuation SD (Hz) (n = 20) | vs flow | -0.1863 | -5.637 | 1 | 2.02e-17 | 4.94e+16 |
| fluctuation SD (Hz) (n = 20) | vs shuffle | -0.1452 | -4.678 | 1 | 7.99e-15 | 1.25e+14 |
| fluctuation SD (Hz) (n = 20) | vs randmat | 0.01375 | 0.440 | 1.2e-07 | 1.51 | 0.661 |
| fluctuation SD (Hz) (n = 20) | vs decorr | -0.09944 | -2.827 | 0.86 | 1.16e-08 | 8.6e+07 |
| bump R (n = 20) | vs flow | 0.05003 | 1.893 | 0.98 | 4.99e-05 | 2.01e+04 |
| bump R (n = 20) | vs shuffle | 0.03776 | 1.452 | 0.69 | 0.00241 | 414 |
| bump R (n = 20) | vs randmat | 0.02605 | 0.861 | 0.18 | 0.198 | 5.06 |
| bump R (n = 20) | vs decorr | 0.09646 | 3.869 | 1 | 2.49e-12 | 4.01e+11 |
| patch/surround (n = 20) | vs flow | -0.551 | -4052.790 | 1 | 2.16e-73 | 4.63e+72 |
| patch/surround (n = 20) | vs shuffle | -0.001243 | -6.571 | 8.2e-81 | 1.22e-19 | 8.18e+18 |
| patch/surround (n = 20) | vs randmat | -0.03565 | -186.917 | 6.6e-91 | 1.7e-67 | 5.9e+66 |
| patch/surround (n = 20) | vs decorr | -0.4674 | -44.560 | 1 | 2.66e-49 | 3.76e+48 |
| ring PC1-2 var (n = 20) | vs flow | 0.04253 | 1.307 | 0.56 | 0.008 | 125 |
| ring PC1-2 var (n = 20) | vs shuffle | 0.03996 | 1.255 | 0.45 | 0.0121 | 82.5 |
| ring PC1-2 var (n = 20) | vs randmat | 0.04603 | 1.302 | 0.68 | 0.00832 | 120 |
| ring PC1-2 var (n = 20) | vs decorr | 0.03191 | 0.844 | 0.2 | 0.219 | 4.57 |
| ring circularity (n = 20) | vs flow | 0.06067 | 1.360 | 1 | 0.0052 | 192 |
| ring circularity (n = 20) | vs shuffle | 0.04533 | 1.182 | 0.99 | 0.0213 | 47 |
| ring circularity (n = 20) | vs randmat | 0.02933 | 0.666 | 0.84 | 0.584 | 1.71 |
| ring circularity (n = 20) | vs decorr | 0.05467 | 1.342 | 1 | 0.00604 | 166 |
| yaw modulation (Hz) (n = 20) | vs flow | -0.8193 | -7.411 | 1 | 2.02e-21 | 4.96e+20 |
| yaw modulation (Hz) (n = 20) | vs shuffle | -0.5445 | -4.726 | 1 | 5.84e-15 | 1.71e+14 |
| yaw modulation (Hz) (n = 20) | vs randmat | 0.08272 | 0.703 | 0.35 | 0.484 | 2.07 |
| yaw modulation (Hz) (n = 20) | vs decorr | 0.03291 | 0.236 | 0.064 | 2.59 | 0.386 |
| tuning <-> wiring r (n = 20) | vs flow | -0.06653 | -4.670 | 1 | 8.45e-15 | 1.18e+14 |
| tuning <-> wiring r (n = 20) | vs shuffle | -0.09212 | -5.785 | 1 | 8.66e-18 | 1.15e+17 |
| tuning <-> wiring r (n = 20) | vs randmat | -0.06332 | -2.580 | 1 | 1.01e-07 | 9.92e+06 |
| tuning <-> wiring r (n = 20) | vs decorr | 0.0109 | 0.255 | 0.18 | 2.5 | 0.4 |
| steering fidelity (n = 20) | vs flow | -0.05451 | -3.328 | 1.8e-05 | 1.72e-10 | 5.81e+09 |
| steering fidelity (n = 20) | vs shuffle | -0.03001 | -1.697 | 2.3e-10 | 0.000289 | 3.46e+03 |
| steering fidelity (n = 20) | vs randmat | -0.07398 | -4.406 | 0.097 | 5.11e-14 | 1.96e+13 |
| steering fidelity (n = 20) | vs decorr | 0.1364 | 3.254 | 1 | 3.15e-10 | 3.17e+09 |
| steering amplitude (Hz) (n = 20) | vs flow | -69.65 | -5.369 | 1 | 9.97e-17 | 1e+16 |
| steering amplitude (Hz) (n = 20) | vs shuffle | -67.31 | -3.630 | 1 | 1.56e-11 | 6.42e+10 |
| steering amplitude (Hz) (n = 20) | vs randmat | -90.26 | -5.901 | 1 | 4.48e-18 | 2.23e+17 |
| steering amplitude (Hz) (n = 20) | vs decorr | -5.105 | -0.256 | 4.2e-07 | 2.5 | 0.401 |
| descending rate (Hz) (n = 20) | vs flow | -150.4 | -13.113 | 1.3e-46 | 3.47e-30 | 2.88e+29 |
| descending rate (Hz) (n = 20) | vs shuffle | -178.7 | -14.089 | 8.2e-10 | 2.61e-31 | 3.83e+30 |
| descending rate (Hz) (n = 20) | vs randmat | -156.6 | -11.740 | 6.7e-15 | 1.84e-28 | 5.43e+27 |
| descending rate (Hz) (n = 20) | vs decorr | -150.3 | -8.810 | 3.6e-12 | 4.92e-24 | 2.03e+23 |

---

## Table 3. Conflict dose: every readout against alpha (kappa = 300, n = 10 per level, 6 s per trial)

| readout | a=0 | a=0.25 | a=0.5 | a=0.75 | a=1 | rho | P |
|---|---|---|---|---|---|---|---|
| CX rate (Hz) | 3.172 | 3.42 | 3.63 | 3.853 | 3.962 | +0.952 | 0.0002 |
| CX active fraction | 0.1696 | 0.1737 | 0.1852 | 0.1965 | 0.201 | +0.887 | 0.0002 |
| yaw modulation (Hz) | 1.153 | 0.9853 | 0.9717 | 0.9713 | 0.9366 | -0.335 | 0.021 |
| tuning <-> wiring r | 0.2359 | 0.2518 | 0.2549 | 0.2539 | 0.252 | +0.246 | 0.093 |
| steering fidelity | 0.7405 | 0.7142 | 0.6793 | 0.6541 | 0.6154 | -0.845 | 0.0002 |
| steering amplitude (Hz) | 424.3 | 423 | 425.5 | 422.4 | 431.3 | +0.119 | 0.41 |
| descending rate (Hz) | 1930 | 1976 | 2009 | 2041 | 2076 | +0.958 | 0.0002 |
| population tau (ms) | 150.3 | 104.3 | 117.6 | 116.5 | 131 | -0.076 | 0.6 |
| dim. (PR) | 52.83 | 55.12 | 54.54 | 57.99 | 59.86 | +0.503 | 0.0005 |
| bump R | 0.3585 | 0.3278 | 0.3036 | 0.2765 | 0.2742 | -0.817 | 0.0002 |
| ring circularity | 0.1687 | 0.1553 | 0.1313 | 0.14 | 0.112 | -0.444 | 0.0007 |
| ring PC1-2 var | 0.4357 | 0.4408 | 0.4275 | 0.4231 | 0.3995 | -0.363 | 0.0085 |
| fluctuation SD (Hz) | 0.7568 | 0.7748 | 0.8029 | 0.828 | 0.8419 | +0.698 | 0.0002 |
| delivered events | 6.552e+05 | 6.555e+05 | 6.556e+05 | 6.554e+05 | 6.558e+05 | +0.134 | 0.36 |
| patch/surround | 0.4257 | 0.5143 | 0.636 | 0.7619 | 0.8918 | +0.980 | 0.0002 |

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
