# Decisions taken on the author's behalf

The author delegated the remaining choices ("全都帮我做").  This file records what was decided, so
any of it can be reversed with one edit.

## 1. Generative-AI disclosure: **option A** (declare, keep the text as written)

Chosen because the manuscript already carries the three required declarations and the journal policy
asks for exactly this:

| where | text |
|---|---|
| Methods (`manuscript.md`, *Use of generative AI*) | tool `DeepSeek-V4.1-Flash`, via the DeepSeek Harness, `2026-09-28`; states that code as well as text was model-assisted under author direction, that all code was executed and verified by the authors, that no AI-generated images exist, and points to Note S2 for the full prompt log |
| Acknowledgments (`manuscript.md`) | repeated declaration, per journal policy |
| Cover letter (`cover-letter.md`) | full declaration paragraph |
| Supplementary Note S2 | tool, scope, what was *not* used, how the log was assembled, and the prompt log itself |

Options B (rewrite the prose so no declaration is needed) and C (hybrid) remain available; nothing
in the repository depends on the choice.

## 2. Venue, in the order we recommend trying

1. **PLoS Computational Biology** or **eLife** — the result is a model-plus-methods paper with a
   behavioural readout; both venues are a natural fit and have predictable review times.
2. **Nature Communications** — worth it if the receptive-field patch and the closed-loop behaviour
   both land (they strengthen the "this is about the computation, not the model" claim).
3. **Science (Report)** — only in the short format, leading with the two-sided claim (a silent body
   region costs coding; a conflicting one costs fidelity of the steering command) and the
   drive-matching/body-lock traps as the methodological half.

`paper/cover-letter.md` is written to be venue-neutral in its salutation line; change the journal
name in the first line when the target is fixed.

## 3. Supplementary Note S2's two `[recorded form]` entries

The two instructions whose exact wording is not recoverable from the session record are S2.3.1
(build the model from the MaleCNS v1.0 release) and S2.4.3 (the Terraria mod specification).  Their
*substance* is documented in the note itself, and their *consequences* are fully traceable:

- S2.3.1 → the three release files with byte counts and SHA256 in Note S1 §S1.1, and the rebuild
  command in `reproduce.ps1 -Tier source`;
- S2.4.3 → the implemented mod spec with one file per requirement: `Items/FlyFood.cs` (left-click
  eat, right-click place), `Vision/FlyEyeView.cs` + `Vision/WorldSampler.cs` (third-person view),
  `UI/BrainScanHud.cs` (live CX panel at the right of the screen), `World/NeuroNarrative.cs` +
  `World/BrainInterpreter.cs` (the activity put into words), `UI/FlyMarkerLayer.cs` (the fly marked),
  `World/CxExperiment.cs` (the same experiment on F9).

**What still has to come from the author**: the verbatim wording of those two instructions, pasted
into the two marked slots.  Everything else in S2 is quoted text plus an English gloss.

## 4. Repository

`git` history is a single clean commit; the payload was trimmed to the circuit blob, the results,
the tools and the paper (18.9 MiB packed).  Not redistributed: the 3 GB edge list and the release
feathers (rebuildable with `tools/export_edges.py`), the duplicate/pre-fix circuit blobs, and the
third-party annotation table.  A portable snapshot of the whole repository is
`flymind-selfview.bundle` (11.0 MB) — `git clone <bundle>` then `git push` reproduces it anywhere.

Target repository: <https://github.com/iice662/flymind-selfview> (public, created; the push from
this machine failed on network errors — HTTP 408, then "could not connect to github.com:443" —
while the same machine downloaded 6.8 GB from Google Storage, so the block is on GitHub uploads
from this link, not a repository problem).
