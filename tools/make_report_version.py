"""Produce the remaining submission files: PDFs of the supplementary material, and a Report-format
condensation of the manuscript.

The condensation is ASSEMBLED FROM THE EXISTING TEXT - it selects and concatenates paragraphs that
are already in paper/manuscript.md and does not write new claims, so nothing in it can drift from the
data.  It is meant as a starting point the author trims, not as a finished Report.

    python tools/make_report_version.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from make_submission_package import CSS, md_to_html  # noqa: E402

MD = os.path.join(ROOT, "paper", "manuscript.md")
OUT = os.path.join(ROOT, "submission")
EXTRA = [("supplementary-note-S1", os.path.join(ROOT, "paper", "supplementary-note-S1.md")),
         ("supplementary-note-S2", os.path.join(ROOT, "paper", "supplementary-note-S2.md")),
         ("reporting-summary", os.path.join(ROOT, "paper", "reporting-summary.md")),
         ("cover-letter", os.path.join(ROOT, "paper", "cover-letter.md")),
         ("submission-plan", os.path.join(ROOT, "paper", "submission-plan.md"))]

KEEP_RESULTS = [
    "### Under optic flow the body patch changes CX state",     # rate vs geometry
    "### Under yaw drive a silent body region degrades",         # the silent patch
    "### Graded temporal conflict degrades the steering command",  # the headline dose
    "### The conflict effect does not depend on how the body",   # robustness
]


def section(md, heading):
    i = md.find(heading)
    if i < 0:
        return ""
    j = md.find("\n### ", i + len(heading))
    k = md.find("\n## ", i + len(heading))
    ends = [x for x in (j, k) if x > 0]
    return md[i:min(ends) if ends else len(md)].strip()


def first_paragraphs(text, n=2):
    out, buf = [], []
    for line in text.splitlines()[1:]:
        if line.startswith(">"):          # skip the correction-note blockquotes
            continue
        if line.strip() == "":
            if buf:
                out.append("\n".join(buf))
                buf = []
                if len(out) >= n:
                    break
        else:
            buf.append(line)
    if buf and len(out) < n:
        out.append("\n".join(buf))
    return "\n\n".join(out)


def main():
    md = open(MD, encoding="utf-8").read()
    title = md.splitlines()[0].lstrip("# ").strip()

    # ---- Report-format condensation -------------------------------------------------
    parts = [f"# {title} (Report-format condensation)", "",
             "> Assembled from `paper/manuscript.md` by `tools/make_report_version.py`: the text is "
             "the published text, cut to a Report's length.  Trim the Results paragraphs below to ~4 "
             "display items (Fig. 1-2 plus a merged Fig. 4/5) before submitting it as a Report.", ""]
    for label, anchor, n in [("One-sentence summary", "**One-sentence summary.**", 1),
                             ("Abstract", "**Abstract.**", 1)]:
        t = section(md, anchor) if anchor.startswith("**O") or anchor.startswith("**A") else ""
        if t:
            parts += [t, ""]
    intro = section(md, "## Introduction")
    if intro:
        parts += ["## Introduction", "", first_paragraphs(intro, 2).replace("## Introduction", "").strip(), ""]
    parts += ["## Results", ""]
    for h in KEEP_RESULTS:
        s = section(md, h)
        if s:
            parts += [h.replace("### ", "**") + "**", "", first_paragraphs(s, 2), ""]
    disc = section(md, "## Discussion")
    if disc:
        parts += ["## Discussion", "", first_paragraphs(disc, 2).replace("## Discussion", "").strip(), ""]
    parts += ["## Methods", "",
              "Materials and Methods are unchanged from the Research Article version: "
              "`paper/manuscript.md`, section *Materials and Methods*.  Every number in this "
              "condensation is regenerated from `results/raw/*.csv` and checked by "
              "`tools/verify_headline_numbers.py`.", ""]
    rv = "\n".join(parts)
    open(os.path.join(OUT, "report-version.md"), "w", encoding="utf-8").write(rv)
    open(os.path.join(OUT, "report-version.html"), "w", encoding="utf-8").write(
        "<html><head><meta charset='utf-8'><style>" + CSS + "</style></head><body>"
        + md_to_html(rv) + "</body></html>")
    words = len(re.findall(r"\S+", rv))
    print(f"wrote submission/report-version.md ({words} words)  and .html")

    # ---- HTML for every supplementary document, for the Word PDF pass ----------------
    for name, path in EXTRA:
        if not os.path.exists(path):
            print("  missing", path)
            continue
        body = md_to_html(open(path, encoding="utf-8").read())
        open(os.path.join(OUT, f"{name}.html"), "w", encoding="utf-8").write(
            "<html><head><meta charset='utf-8'><style>" + CSS + "</style></head><body>"
            + body + "</body></html>")
        print("  wrote submission/%s.html" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
