# Submission plan: *Science* first, then a cascade

**One rule governs everything below: these journals do not consider a manuscript that is under
consideration elsewhere.**  Submitting to many journals at once is not a faster route — it is the
one thing that gets a paper administratively rejected (and, at *Science*, can bar the authors).  The
compliant way to "submit widely" is a **cascade**: submit to one, and the moment it is declined,
send the same paper to the next, with the venue-specific adaptations already prepared here.

Preprint servers (bioRxiv) are the exception: posting a preprint before or during submission is
allowed by *Science*, Nature Portfolio, eLife, PLoS and Cell Press, and it does not count as
prior publication.  That is the legitimate way to have the work publicly visible while the cascade
runs.

## Target 1 — *Science* (Research Article or Report)

| item | what it needs | status |
|---|---|---|
| Cover letter | `paper/cover-letter.md` — already addressed to the Editors of *Science* | ✅ ready |
| Format | Research Article ~15,000 words / 4-6 display items, or Report ~2,500 words / 4 display items | ✅ the manuscript fits; `main4` + `main4b` can merge for a 4-figure Report |
| Reporting Summary | `paper/reporting-summary.md` — every item answered | ✅ ready |
| AI disclosure | Methods + Acknowledgments + cover letter + Supplementary Note S2 with the prompt log | ✅ in place (option A, `paper/DECISIONS.md`) |
| Data/code | DataSeer audits the repository: public, with README, one-command reproduction, per-trial data | ✅ published at https://github.com/iice662/flymind-selfview |
| Author fields | authors, affiliation, correspondence, funding, competing interests, contributions | ✅ filled |
| **Only open item** | the two verbatim prompts in `paper/supplementary-note-S2.md` (S2.3.1, S2.4.3) | ⬜ author |
| Suggested reviewers | three names: one CX/heading physiologist, one connectome-constrained modeller, one on equivalence/Bayes methods | ⬜ author |

**If *Science* declines** (likely at the editor's desk, since the paper is a model study), the
rejection is usually fast (days to ~2 weeks) and does not prejudice the next venue.

## Target 2 — *Nature Communications*

Adaptations: **Reporting Summary** (Nature's own form; `paper/reporting-summary.md` covers the
content), ORCID for the corresponding author, a *Data availability* statement naming the repository
and a *Code availability* statement, and the manuscript split so the Methods come after the
discussion.  Figures stay at 4-6 main.  Transfer service: if *Science* declines, Nature's
manuscript-transfer service can move the file to *Nature Communications* with the referee reports
intact, which is the fastest legitimate path.

## Target 3 — *eLife*

Adaptations: eLife's model is "reviewed preprint" — the paper is posted as a preprint and reviewed
publicly; no reformatting is needed beyond a short *eLife* summary paragraph.  This venue is the
best fit for the paper's methodological half (the drive-matching and body-lock traps) and it is
where the equivalence-testing argument will be appreciated most.

## Target 4 — *PLoS Computational Biology*

Adaptations: PLOS's own submission checklist (similar to the reporting summary), a *Data
Availability* statement with the repository URL, and author contributions in CRediT taxonomy
(already drafted in the Acknowledgments).  The journal explicitly welcomes negative and
methodological results, which is what half of this paper is.

## Target 5 — *PNAS* (Direct Submission) or *Current Biology*

*PNAS* needs an NAS member sponsor for Direct Submission (or a Contributed submission through a
member); *Current Biology* is a good fit for the *Report* format if the closed-loop behaviour
result lands.  Both would need the paper cut to ~4 display items.

## What is already true for every venue (no rework needed)

- the repository and its bundle are public, citable and complete;
- every number in the manuscript is regenerated from the deposited per-trial CSVs and checked by
  `tools/verify_headline_numbers.py` (25/25);
- the AI disclosure follows the strictest of the five policies (*Science*'s), so it satisfies the
  others by construction;
- the figures are already single-column 3.5 in / double-column 7.0 in at 300 dpi with embedded
  TrueType fonts, which every one of these venues accepts.

## The real bottleneck is not the venue list

Four scientific items are still open (see `results/RECEPTIVE-FIELD-STATUS.md` and
`results/CLOSED-LOOP-PLAN.md`): the receptive-field patch experiment (`N-rfpatch`), the closed-loop
gain calibration and dose series, the DictionaryBatch decoding that would name the neuropils, and
the final consistency sweep.  The first two materially strengthen the paper at *any* of the five
venues — the receptive-field patch answers the strongest reviewer objection, and the closed loop
turns the steering-command result into a behavioural one.
