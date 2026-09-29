# Cover letter

**To the Editors of *PLOS Computational Biology***

Dear Editors,

**Article type:** Research Article

We submit for your consideration a manuscript entitled **"Missing versus conflicting self-motion signals act differently on the *Drosophila* central complex."**

**The question.** Every animal that is observed from the outside — in a video, in a virtual-reality rig, in a game — receives a visual input that no animal has ever received in its own life: a body-locked, slip-free region inside an otherwise flowing optic array. The fly's central complex (CX) maintains heading in a ring of EPG cells, and whether such a self-referential input perturbs that computation is an old question that has never been answerable, because it requires (i) a circuit containing the visual pathway into the CX at connectome scale and (ii) an input manipulation whose total drive is matched to the natural condition.

**What we did.** We built a 12,000-neuron, 1,615,753-synapse spiking slice of the MaleCNS v1.0 connectome (151,856,684 edges; no pruning) with an explicit, per-subfamily CX readout, calibrated to a spontaneously active regime with a single global gain, and ran the self-observation manipulation as a controlled experiment: a body-locked slip-free patch of the visual pool versus drive-matched controls that isolate patch size, spatial coherence and temporal locking. We verified the substrate two ways — 97.2% of CX cells are one synapse from the visual pool, and a synchronous volley evokes a monosynaptic CX response at 2.5 ms — and we used equivalence testing and Bayes factors rather than null-hypothesis non-rejection.

**What we found.**

1. **The CX distinguishes absent from inconsistent self-motion, and the distinction is graded.** A slip-free body patch leaves every heading metric statistically equivalent to the natural condition (TOST within ±10%; Bayes factors 2.8–3.2 at n = 20 against a design ceiling of 3.24). Replacing a *fraction* α of that patch's slip with motion that is not aligned to the world's rotation degrades, monotonically in α, how well CX cells' tuning follows the connectome's own push–pull wiring (0.317 → 0.244), their yaw modulation depth (1.97 → 1.25 Hz), the population's integration time constant (247 → 163 ms), the ring's bump amplitude — and, largest of all, the fidelity with which the descending pre-motor command follows the animal's actual turn (r = 0.81 → 0.61, amplitude −21%) — while the mean firing rate of the CX is unchanged (ρ = +0.10, P = 0.46). The pattern replicates at two other circuit gains (κ = 150 and 600; ρ = −0.87…−0.98 for steering fidelity), over a fourfold range.
2. **Under global optic flow the same manipulation does change CX state** — 36% lower firing, 33% sharper ring population vector — but the firing-rate component is quantitatively reproduced by a *random* patch that silences the same 9.1% of CX input, so the rate effect is input loss and only the state geometry requires spatial coherence.
3. **Method.** In connectome-derived circuits normalized by a global gain, the delivered event total is a stronger determinant of every readout than the structure of the input under study. An earlier, unbalanced version of this same experiment reported the self-view as perturbing heading at P = 4.7 × 10⁻¹⁷ (d = −14.5); after per-step drive matching the same contrast is d = −0.05 (P = 0.91). We give the balancing scheme, the controls it requires, and the equivalence/Bayes analysis appropriate to a null.

**Why it belongs in *Science*.** The result is a boundary statement about a computation, not a simulation report: the heading system tolerates a missing self-signal and is progressively degraded by a contradictory one, with the behavioural readout — steering fidelity — showing the largest effect. That predicts a specific and cheap experiment in intact flies (a body-locked occluder should be behaviourally silent; a body-locked *moving* pattern should bias heading and degrade turn fidelity in proportion to how much it moves), and it connects to the forward-model/efference-copy literature that has long argued insect sensory systems must discount self-generated change. The methodological half — that structure-free drive matching and equivalence testing are prerequisites for any perturbation of a connectome-constrained circuit — applies to every model of this kind now being built.

**What we do not claim.** We do not claim that a fly perceives itself; we do not claim that a 12,000-neuron slice is a brain (it carries 1.1% of the connectome's synapses, over-represents the CX about twentyfold, and uses a single calibrated gain); and we do not claim that the manipulation's effect on the CX is large in absolute terms. We do claim that within this circuit, with the input matched to 0.09%, the difference between *missing* and *conflicting* self-motion is measurable, reproducible across gains, and graded in dose. All raw per-trial data, the circuit blob, the balancing code and the analysis code are provided.

**Suggested reviewers.** We suggest the following, none of whom is a co-author, collaborator or
current colleague of ours. Contact addresses are as published in the corresponding authors'
papers; please verify each on the journal's form before sending.

*Central complex / heading coding in Drosophila*
1. Vivek Jayaraman, Janelia Research Campus (HHMI) — ring-attractor dynamics of the ellipsoid body, EPG heading cells, calcium imaging in behaving flies. `jayaramav@janelia.hhmi.org`
2. Gaby Maimon, The Rockefeller University — heading computation and steering in the central complex, PFL neurons, tethered-flight physiology. `maimon@rockefeller.edu`

*Connectome-constrained modelling*
3. Jakob H. Macke, University of Tübingen — connectome-constrained mechanistic networks of the fly visual system; the same modelling philosophy this paper tests. `macke@tuebingen.mpg.de`
4. Srinivas C. Turaga, Janelia Research Campus (HHMI) — training networks on connectome-derived circuits, including motion vision. `turagas@janelia.hhmi.org`

*Equivalence testing and Bayesian evidence for the null*
5. Daniël Lakens, Eindhoven University of Technology — equivalence testing and the TOST procedure (ref. 13 in this manuscript). `D.Lakens@tue.nl`
6. Jeffrey N. Rouder, University of California, Irvine — Bayes factors for accepting and rejecting the null (ref. 10 in this manuscript). `jrouder@uci.edu`

Two further names, should any of the above be unavailable: Johannes Seelig (University of
Washington) for central-complex physiology, and Jan Funke (Janelia Research Campus) for
connectome analysis. We have deliberately not suggested the authors of the MaleCNS v1.0 dataset,
since this manuscript both relies on their release and criticises a modelling practice that has
grown up around connectome-derived circuits.

**Declaration of generative AI use.** In accordance with the Science journals' policy, we declare that the manuscript text was drafted with the assistance of a large language model (`DeepSeek-V4.1-Flash`, via the DeepSeek Harness, `2026-09-28`); the model was used to draft and edit the text and, under the authors' direction, to write the simulation, analysis and plotting code. All research data were generated by our own simulations; all code was executed, inspected and validated by the authors; every numerical value in the manuscript, tables and figures was regenerated from the deposited raw per-trial data by the authors. No AI-generated images are included: all figures are direct plots of the authors' data produced with matplotlib from the deposited scripts. The full prompt log is provided in Supplementary Note S2. The authors take full responsibility for the content.

Sincerely,

Yitong Chen (BRIAN)
Independent researcher, Shanghai, China
18721952805@163.com

---

## Submission checklist (Science Research Article)

| item | status |
|---|---|
| Main text ≤ ~4,500 words | manuscript.md main text ≈ 2,900 words (excluding Methods) |
| Abstract ≤ 125 words | 148 words — **trim before submission** |
| One-sentence summary | present |
| Figures ≤ 4 in main text | we have 7 main + 3 supplementary — **merge to 4 before submission** (see `figures.md` for a suggested merge) |
| Methods | present, self-contained |
| References ≤ 60 | 15 present; add the CX/ring-attractor primary literature |
| Data and code availability | require a repository DOI (**author action**) |
| Author contributions / competing interests | **author action** |
| Reporting summary | Science requires one — **author action** |


---

**Venue-specific note (PLOS Computational Biology).** PLOS explicitly welcomes negative and methodological results, which is half of this paper; add the PLOS submission checklist.

Submission URL: https://journals.plos.org/ploscompbiol/s/submission-guidelines
