# How to submit: the package is built, the final click is yours

**Why the last step cannot be automated.** Every one of these systems requires the corresponding
author to sign in with their own account, and to tick a declaration that *they* are the author,
that the work is original, and that it is **not under consideration anywhere else**. Nobody else can
truthfully make that statement, and submitting on someone's behalf with their credentials is exactly
what those declarations forbid. What is done here is everything up to that click.

**And the one rule that shapes the whole plan:** all five venues refuse manuscripts that are under
consideration elsewhere.  Submit to **one**, wait for the decision, then send the same package to the
next.  To have the work visible meanwhile, post it to **bioRxiv** — all five allow preprints and
treat them as prior *disclosure*, not prior *publication*.

---

## The package (in `submission/`)

| file | use |
|---|---|
| `manuscript.docx` | main text for every system, double-spaced, Times 12, tables inline |
| `manuscript.pdf` | the same, for systems that want a single review PDF |
| `manuscript.html` | source of both; edit this and re-run the converter if the text changes |
| `metadata.txt` | title, one-sentence summary, authors, abstract, statements — paste-ready |
| `figures/Fig1..Fig5.pdf` + `.png` | main figures, already 3.5 in / 7.0 in, 300 dpi, fonts embedded |
| `figures/figS1..figS5.pdf` + `.png` | supplementary figures |
| two supplementary notes | `../paper/supplementary-note-S1.md` (provenance) and `-S2.md` (AI disclosure + prompt log) — convert with the same script if the system wants PDFs |
| reporting summary | `../paper/reporting-summary.md` |
| cover letter | `../paper/cover-letter.md` (already addressed to the Editors of *Science*) |

Rebuild after any edit: `python tools\make_submission_package.py`, then Word → `SaveAs` HTML to
`.docx` (format 16) and `.pdf` (format 17) — the commands are in the repository history.

---

## 1. *Science* — https://www.science.org/author-center/submitting-manuscript

1. Article type: **Research Article** (or **Report** if you cut to ~2,500 words and 4 display items;
   merge `main4` + `main4b` into one figure for that).
2. Upload `manuscript.docx` as the main document; figures can go inside it or as separate files —
   the system builds the review PDF either way.
3. Paste from `metadata.txt`: title, one-sentence summary (Science asks for one), abstract, author
   list with affiliations and the corresponding author's email, funding, competing interests,
   author contributions, data and code availability.
4. Paste the **generative-AI declaration** (in `metadata.txt`) into the designated field, and upload
   Supplementary Note S2 (the prompt log) as supplementary material — Science requires the full
   prompt, not a summary.
5. Suggested reviewers: six names are in the cover letter, grouped by expertise; the form takes up to
   five, so drop the two alternates.
6. Cover letter: paste `../paper/cover-letter.md`.
7. The repository URL is already in the manuscript; DataSeer will check that it resolves and that the
   data and code are actually there. It does: <https://github.com/iice662/flymind-selfview>.

## 2. *Nature Communications* — https://www.nature.com/ncomms/submit

Same package.  Add: ORCID for the corresponding author, the Nature **reporting summary** (content is
in `../paper/reporting-summary.md`), and separate *Data availability* / *Code availability*
statements.  If *Science* declines, use Nature's **manuscript transfer service** — the file moves
with any referee reports, which is the fastest legitimate route.

## 3. *eLife* — https://submit.elifesciences.org

Reviewed-preprint model: the paper is posted and reviewed in the open.  No reformatting beyond a
short summary paragraph for the eLife assessment.  The methodological half of this paper (the
drive-matching and body-lock traps) is the part this venue is most likely to value.

## 4. *PLoS Computational Biology* — https://journals.plos.org/ploscompbiol/s/submission-guidelines

Same package plus the PLOS submission checklist.  PLOS explicitly welcomes negative and
methodological results, which is half of this paper.

## 5. *PNAS* (Direct Submission) or *Current Biology*

*PNAS* needs an NAS member to sponsor a Direct Submission; *Current Biology* would want the Report
format (4 display items).  Both reuse the same files.

---

## What is already true for all five (no rework)

- every number regenerates from the deposited per-trial CSVs; `tools\verify_headline_numbers.py`
  reports **25/25**;
- the AI disclosure is written to *Science*'s standard, the strictest of the five, so it satisfies
  the others by construction;
- figures meet every venue's technical requirements (vector PDF, 300 dpi PNG, embedded fonts,
  single/double column widths);
- the repository is public, has a README, one-command reproduction and a release bundle of the whole
  project.

## Still author-side (nothing else)

1. Sign in to the target system and tick the authorship/originality/not-elsewhere declaration.
2. Confirm the six suggested reviewers' addresses on the form (they are as published; two minutes to
   check).
3. Pay any page charge the venue asks for, if applicable.
