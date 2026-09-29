# Cascade tracker: one journal at a time

**Rule:** all five refuse a manuscript under consideration elsewhere.  Submit to one, wait, then move down the list.  To be publicly visible meanwhile, post the preprint (bioRxiv) - all five allow it and it is not prior publication.

| # | venue | article type | submit at | cover letter | status |
|---|---|---|---|---|---|
| 1 | Science | Research Article (or Report, ~2,500 words, 4 display items) | https://www.science.org/author-center/submitting-manuscript | `cover-letters/cover-1-science.md` | not sent |
| 2 | Nature Communications | Article | https://www.nature.com/ncomms/submit | `cover-letters/cover-2-nature-communications.md` | not sent |
| 3 | eLife | Research Article (reviewed preprint) | https://submit.elifesciences.org | `cover-letters/cover-3-elife.md` | not sent |
| 4 | PLOS Computational Biology | Research Article | https://journals.plos.org/ploscompbiol/s/submission-guidelines | `cover-letters/cover-4-plos-compbiol.md` | not sent |
| 5 | PNAS (Direct Submission) or Current Biology | Research Article / Report | https://www.pnas.org/author-center/submitting-your-manuscript | `cover-letters/cover-5-pnas-or-current-biology.md` | not sent |

## Preprint (do this first, it is the only 'many places at once' that is allowed)

1. https://www.biorxiv.org/submit-a-manuscript — upload `submission/manuscript.pdf`.
2. Metadata to paste: `submission/metadata.txt` (title, abstract, authors).
3. Category: Neuroscience → *Drosophila* / computational; licence: CC BY 4.0 (data and figures in the repository already use it).
4. Decline the journal's own transfer offers if you intend to run this cascade.

## What is already prepared for every step

- `submission/manuscript.docx` / `.pdf` — main text, double spaced, tables inline
- `submission/figures/` — Fig1–Fig5 and figS1–figS5, PDF and 300 dpi PNG
- `submission/metadata.txt` — every field the forms ask for, paste-ready
- `paper/reporting-summary.md` — Science's form, and the content Nature's form needs
- `paper/supplementary-note-S1.md` (provenance) and `-S2.md` (AI disclosure + prompts)
- repository with the full data, code, per-trial CSVs and a release bundle:
  <https://github.com/iice662/flymind-selfview>

## The one thing only you can do

Sign in as the corresponding author and tick the declaration that you are the author, that the work is original, and that it is **not under consideration elsewhere**. Nobody else can make that statement truthfully, which is why the last click is yours.
