"""Generate one cover letter per venue and the cascade tracker.

Why not "submit everywhere at once": every one of these journals refuses a manuscript that is under
consideration elsewhere, so simultaneous submission is the one route that gets a paper desk-rejected.
The legitimate way to be in several places is (a) a preprint, which all five allow, and (b) a
sequential cascade with a ready-to-send cover letter for each step - which is what this produces.

    python tools/make_cascade.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "submission")
SRC = os.path.join(ROOT, "paper", "cover-letter.md")

VENUES = [
    ("1-science", "Science", "Research Article (or Report, ~2,500 words, 4 display items)",
     "https://www.science.org/author-center/submitting-manuscript",
     "Science's DataSeer check will open the repository and confirm the data and code are there; the "
     "prompt log (Supplementary Note S2) must be uploaded, not summarised."),
    ("2-nature-communications", "Nature Communications", "Article",
     "https://www.nature.com/ncomms/submit",
     "Use Nature's manuscript-transfer service if Science declines: the file moves with any referee "
     "reports. Add ORCID and Nature's own reporting summary."),
    ("3-elife", "eLife", "Research Article (reviewed preprint)",
     "https://submit.elifesciences.org",
     "The paper is posted and reviewed in the open; add a short assessment paragraph. The "
     "methodological half (drive-matching and body-lock traps) is what this venue values most."),
    ("4-plos-compbiol", "PLOS Computational Biology", "Research Article",
     "https://journals.plos.org/ploscompbiol/s/submission-guidelines",
     "PLOS explicitly welcomes negative and methodological results, which is half of this paper; add "
     "the PLOS submission checklist."),
    ("5-pnas-or-current-biology", "PNAS (Direct Submission) or Current Biology", "Research Article / Report",
     "https://www.pnas.org/author-center/submitting-your-manuscript",
     "PNAS Direct Submission needs an NAS member to sponsor it; Current Biology would want the "
     "Report format (4 display items, so merge main4 and main4b)."),
]


def main():
    base = open(SRC, encoding="utf-8").read()
    os.makedirs(os.path.join(OUT, "cover-letters"), exist_ok=True)

    for slug, name, atype, url, note in VENUES:
        t = base
        t = t.replace("**To the Editors of *Science***", f"**To the Editors of *{name}***")
        t = t.replace("We submit for your consideration a Research Article entitled",
                      f"**Article type:** {atype}\n\nWe submit for your consideration a manuscript entitled")
        t += (f"\n\n---\n\n**Venue-specific note ({name}).** {note}\n\n"
              f"Submission URL: {url}\n")
        open(os.path.join(OUT, "cover-letters", f"cover-{slug}.md"), "w", encoding="utf-8").write(t)
        print("wrote cover-letters/cover-%s.md" % slug)

    rows = ["# Cascade tracker: one journal at a time", "",
            "**Rule:** all five refuse a manuscript under consideration elsewhere.  Submit to one, "
            "wait, then move down the list.  To be publicly visible meanwhile, post the preprint "
            "(bioRxiv) - all five allow it and it is not prior publication.", "",
            "| # | venue | article type | submit at | cover letter | status |",
            "|---|---|---|---|---|---|"]
    for slug, name, atype, url, _ in VENUES:
        rows.append(f"| {slug.split('-')[0]} | {name} | {atype} | {url} | "
                    f"`cover-letters/cover-{slug}.md` | not sent |")
    rows += ["", "## Preprint (do this first, it is the only 'many places at once' that is allowed)",
             "",
             "1. https://www.biorxiv.org/submit-a-manuscript — upload `submission/manuscript.pdf`.",
             "2. Metadata to paste: `submission/metadata.txt` (title, abstract, authors).",
             "3. Category: Neuroscience → *Drosophila* / computational; licence: CC BY 4.0 (data and "
             "figures in the repository already use it).",
             "4. Decline the journal's own transfer offers if you intend to run this cascade.",
             "",
             "## What is already prepared for every step", "",
             "- `submission/manuscript.docx` / `.pdf` — main text, double spaced, tables inline",
             "- `submission/figures/` — Fig1–Fig5 and figS1–figS5, PDF and 300 dpi PNG",
             "- `submission/metadata.txt` — every field the forms ask for, paste-ready",
             "- `paper/reporting-summary.md` — Science's form, and the content Nature's form needs",
             "- `paper/supplementary-note-S1.md` (provenance) and `-S2.md` (AI disclosure + prompts)",
             "- repository with the full data, code, per-trial CSVs and a release bundle:",
             "  <https://github.com/iice662/flymind-selfview>", "",
             "## The one thing only you can do", "",
             "Sign in as the corresponding author and tick the declaration that you are the author, "
             "that the work is original, and that it is **not under consideration elsewhere**. "
             "Nobody else can make that statement truthfully, which is why the last click is yours.",
             ""]
    open(os.path.join(OUT, "CASCADE.md"), "w", encoding="utf-8").write("\n".join(rows))
    print("wrote CASCADE.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
