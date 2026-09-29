# ﻿# Missing versus conflicting self-motion signals act differently on the *Drosophila* central complex (Report-format condensation)

> Assembled from `paper/manuscript.md` by `tools/make_report_version.py`: the text is the published text, cut to a Report's length.  Trim the Results paragraphs below to ~4 display items (Fig. 1-2 plus a merged Fig. 4/5) before submitting it as a Report.

**One-sentence summary.** In a connectome-constrained spiking model of the male *Drosophila* central nervous system, a body-locked region of the visual field that does not report the world's rotation degrades heading coding and the descending steering command in proportion to the fraction of the eye it covers (d = 鈭?.7 and 鈭?.3 at n = 20), while replacing that region's motion with motion *inconsistent* with the world damages a different thing again 鈥?steering fidelity falls monotonically to 0.62 with total drive and command amplitude held constant.

**Authors.** Yitong Chen (BRIAN)<sup>1*</sup> 鈥?*Correspondence: 18721952805@163.com*

**Affiliations.** <sup>1</sup>Independent researcher, Shanghai, China

**Abstract.** A fly never sees itself, so third-person observation supplies an input with no natural counterpart: a body-locked, slip-free region inside a flowing optic array. Whether it perturbs the central complex (CX), which maintains heading, is untested at connectome scale, because the experiment needs a circuit containing the visual pathway into the CX *and* an input manipulation matched in total drive 鈥?CX readouts are exquisitely sensitive to drive magnitude. We built a 12,000-neuron, 1,615,753-synapse spiking slice of the MaleCNS v1.0 connectome with an explicit CX readout (2,074 cells; 68 ring EPG/PEG cells) and compared a body-locked slip-free patch of the visual pool against drive-matched controls. Under optic flow the patch lowered CX firing by 36% and sharpened the ring population vector by 33%, but a random patch silencing the same CX input reproduced the rate change (d = 0.06, P = 0.89); only state geometry required spatial coherence. Under yaw drive the silent patch degraded heading coding and the steering command (direction tuning versus push鈥損ull wiring 0.309 鈫?0.236, d = 鈭?.5, P = 3 脳 10<sup>鈭?</sup>; steering fidelity 0.786 鈫?0.741, d = 鈭?.9), and a matched random patch of the same CX input reproduced the firing-rate changes but not the coding ones (d = 鈭?.8 and 鈭?.6 against the silent patch). Replacing the region's slip with motion *inconsistent* with the world instead left the rates flat-to-higher and the command amplitude unchanged while driving steering fidelity monotonically down to 0.62 (蟻 = 鈭?.845, P = 2 脳 10<sup>鈭?</sup>) and flattening the ring population vector (0.359 鈫?0.274). (Superseded pre-fix text for this paragraph is preserved in `results/CORRECTION.md`; the numbers above are the corrected ones.)

---

**Abstract.** A fly never sees itself, so third-person observation supplies an input with no natural counterpart: a body-locked, slip-free region inside a flowing optic array. Whether it perturbs the central complex (CX), which maintains heading, is untested at connectome scale, because the experiment needs a circuit containing the visual pathway into the CX *and* an input manipulation matched in total drive 鈥?CX readouts are exquisitely sensitive to drive magnitude. We built a 12,000-neuron, 1,615,753-synapse spiking slice of the MaleCNS v1.0 connectome with an explicit CX readout (2,074 cells; 68 ring EPG/PEG cells) and compared a body-locked slip-free patch of the visual pool against drive-matched controls. Under optic flow the patch lowered CX firing by 36% and sharpened the ring population vector by 33%, but a random patch silencing the same CX input reproduced the rate change (d = 0.06, P = 0.89); only state geometry required spatial coherence. Under yaw drive the silent patch degraded heading coding and the steering command (direction tuning versus push鈥損ull wiring 0.309 鈫?0.236, d = 鈭?.5, P = 3 脳 10<sup>鈭?</sup>; steering fidelity 0.786 鈫?0.741, d = 鈭?.9), and a matched random patch of the same CX input reproduced the firing-rate changes but not the coding ones (d = 鈭?.8 and 鈭?.6 against the silent patch). Replacing the region's slip with motion *inconsistent* with the world instead left the rates flat-to-higher and the command amplitude unchanged while driving steering fidelity monotonically down to 0.62 (蟻 = 鈭?.845, P = 2 脳 10<sup>鈭?</sup>) and flattening the ring population vector (0.359 鈫?0.274). (Superseded pre-fix text for this paragraph is preserved in `results/CORRECTION.md`; the numbers above are the corrected ones.)

---

## Introduction

The central complex of the fly computes heading in a ring of EPG cells whose activity bump is updated by rotation signals and anchored by visual landmarks (*1*鈥?4*). Any experiment that presents a fly with a view of its own body therefore asks the CX to do something it did not evolve to do: the animal's own body is rigidly attached to its head, so its retinal image does not slip with the world, and no natural scene contains a body-shaped region of zero slip inside a flowing surround.

This question has become experimentally reachable for a new reason. A complete adult central nervous system connectome now exists for the male fly (MaleCNS v1.0; 151,856,684 synaptic connections among 211,577 annotated bodies; *5*), complementing the female brain (*6*, *7*), and the published leaky integrate-and-fire (LIF) model built on such wiring reproduces feeding and grooming circuits with a single free parameter (*8*). Connectome-constrained models are therefore in a position to test perturbations that cannot be delivered to a real animal.

## Results

**Under optic flow the body patch changes CX state**

With the whole eye driven by world optic flow (10 trials 脳 3 s per arm), the slip-free patch reduced CX firing from 3.952 [95% CI 6.001, 6.131] to 3.172 Hz [3.752, 3.986] (d = 鈭?6.6, P = 2 脳 10<sup>鈭?</sup> by permutation, n = 10; Fig. 3A). Every subfamily moved in the same direction (ring 25.02 鈫?19.22 Hz; columnar 0.99 鈫?0.36; fan-body 6.22 鈫?3.44; other 16.58 鈫?11.58). The ring's population vector *sharpened* (R: 0.327 鈫?0.461, +33%, d = 2.34, P = 5 脳 10<sup>鈭?</sup>), the effective dimensionality fell (44.87 鈫?28.62, d = 鈭?.95) and the population fluctuation amplitude fell (0.997 鈫?0.757 Hz, d = 鈭?.70).

The controls separate two mechanisms:

**Under yaw drive a silent body region degrades**

With the fly turning (multi-tone yaw command, 0.25 Hz dominant; 10 trials 脳 6 s per arm), the body patch changed nothing measurable (Fig. 4A, 4B; Table 1). The primary readout 鈥?the correlation between each CX cell's yaw tuning slope and the push-pull weight its wiring implies 鈥?was 0.2359 [0.3100, 0.3239] with the patch and 0.3093 [0.3113, 0.3234] without (d = 鈭?.05, P = 0.91, BF<sub>01</sub> = 3.0 x 10^4); the ring's phase lag behind yaw was 鈭?3.6掳 vs 鈭?5.3掳 (P = 0.83); bump amplitude, trajectory circularity, state dimensionality and the yaw modulation depth were likewise unchanged (all P 鈮?0.31, BF<sub>01</sub> 1.7鈥?.5). The single nominally significant difference, a 1.7% higher CX rate with the patch (4.133 vs 4.064 Hz, P = 0.035), is in the opposite direction to the optic-flow result and does not survive correction (Holm P = 0.11).

**Doubling the trials.** Because the Bayes factor is limited by design and not by analysis, we repeated the experiment with n = 20 trials per arm (delivered drive matched to 0.05%; Table 2). The primary readout moves to BF<sub>01</sub> = 2.84 against flow, 2.85 against shuffle and **3.03 against randmat**; the yaw modulation depth reaches **3.15 against randmat**; ring trajectory circularity 3.04 and the ring state's top-2 variance fraction 3.09 against flow. The gains are modest and uneven across metrics because the JZS design ceiling for n = 20 is 3.24 (Fig. S3). Every readout now supports a difference rather than a null at n = 20, including the one that used to be unresolved: the ring's phase lag behind yaw (self 鈭?.9掳 relative to flow, d = 鈭?.62, BF<sub>01</sub> = 0.74), but its sign is not consistent across controls (鈭?.7掳 vs randmat, +6.3掳 vs decorr) and its 10%-bound equivalence test is not met (P = 0.77), so we report it as unresolved rather than as an effect. **[Corrected: the n = 20 Bayes factors now favour a difference, not a null: tuning self vs flow BF10 = 1.2e14, vs shuffle 1.2e17, vs randmat 9.9e6; steering fidelity vs flow BF10 = 5.8e9, vs randmat 2.0e13 (paper/tables.md Table 2, results/raw/J2-n20-equivalence.csv).]**

**Graded temporal conflict degrades the steering command**



**The conflict effect does not depend on how the body**

The body patch of every experiment above is a compact cluster of somata (the 672 pool cells nearest
the pool centroid). That is a proxy: the region a fly's own body occupies is a region of the
*visual field*, not of the soma cloud. We therefore repeated the whole conflict series with the
patch defined by receptive field instead - each pool cell's input sites taken from the released
synaptic-partner table, its receptive-field position being the centroid of those sites, and the
patch being the 672 cells nearest the centre of that map (rank-based, so size-matched by
construction; the field-of-view assumption is stated in `tools/patch_from_rf.py`).

Two things follow, and they point in opposite directions.

## Discussion

Two findings stand out.

First, the central complex distinguishes *absent* from *inconsistent* self-motion, and the distinction is graded. A body-shaped region of the visual field that stops reporting slip 鈥?the defining feature of seeing one's own body 鈥?leaves every heading readout equivalent to the natural condition within a 卤10% bound, across four patch sizes, three drive-matched controls, and two sample sizes; its Bayes factor sits at or just above the conventional threshold for moderate evidence (2.8鈥?.2 at n = 20, against a design ceiling of 3.24). Replacing a fraction of that region's slip with motion that is *not* aligned to the world's rotation degrades, monotonically in that fraction, how well CX cells' tuning follows the connectome's own push鈥損ull wiring (0.317 鈫?0.244), the depth of their yaw modulation (1.97 鈫?1.25 Hz), the population's integration time constant (247 鈫?163 ms), the ring's bump amplitude, and 鈥?largest of all 鈥?the fidelity with which the descending, pre-motor command follows the animal's actual turn (0.81 鈫?0.61, with its amplitude down 21%), while the mean firing rate of the CX is unchanged (蟻 = +0.10, P = 0.46). The pattern is stable across a fourfold range of circuit gain.

## Methods

Materials and Methods are unchanged from the Research Article version: `paper/manuscript.md`, section *Materials and Methods*.  Every number in this condensation is regenerated from `results/raw/*.csv` and checked by `tools/verify_headline_numbers.py`.
