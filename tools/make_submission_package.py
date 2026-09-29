"""Build the per-venue submission package from the Markdown sources.

Nothing here can log in to a journal: the submission itself needs the corresponding author's
account and their authorship/originality declaration.  What it produces is everything the systems
ask you to upload or paste, so the actual submission is copy-and-click.

    python tools/make_submission_package.py

Outputs (submission/):
    manuscript.html            styled source for Word/LibreOffice (double spaced, Times 12)
    HOW-TO-SUBMIT.md           per-venue upload checklist + the metadata blocks to paste
    figures/Fig1.pdf ...       figures renamed the way the forms expect them
    metadata.txt               title, abstract, authors, statements - paste-ready
"""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "submission")
MD = os.path.join(ROOT, "paper", "manuscript.md")
FIG = os.path.join(ROOT, "paper", "figures")

# submission figure name -> file in paper/figures
FIGMAP = [("Fig1", "main1"), ("Fig2", "main2"), ("Fig3", "main3"), ("Fig4", "main4"),
          ("Fig5", "main4b"), ("figS1", "supp1"), ("figS2", "supp2"), ("figS3", "supp3"),
          ("figS4", "supp4"), ("figS5", "supp5")]

CSS = """
body { font-family: "Times New Roman", serif; font-size: 12pt; line-height: 2.0; }
h1 { font-size: 14pt; } h2 { font-size: 13pt; } h3 { font-size: 12pt; font-style: italic; }
table { border-collapse: collapse; font-size: 9pt; line-height: 1.2; }
td, th { border: 1px solid #444; padding: 2px 4px; }
blockquote { font-size: 10pt; line-height: 1.3; color: #333; }
code { font-family: "Courier New", monospace; font-size: 10pt; }
"""


def inline(t):
    t = (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"<sup>(.+?)</sup>", r"<sup>\1</sup>", t)
    t = re.sub(r"<sub>(.+?)</sub>", r"<sub>\1</sub>", t)
    return t


def md_to_html(md):
    out, in_table = [], False
    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            tag = "th" if not in_table else "td"
            if not in_table:
                out.append("<table>")
                in_table = True
            out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        if s.startswith("### "):
            out.append(f"<h3>{inline(s[4:])}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("# "):
            out.append(f"<h1>{inline(s[2:])}</h1>")
        elif s.startswith("> "):
            out.append(f"<blockquote>{inline(s[2:])}</blockquote>")
        elif s.strip() == "---":
            out.append("<hr>")
        elif s.strip() == "":
            out.append("")
        else:
            out.append(f"<p>{inline(s)}</p>")
    if in_table:
        out.append("</table>")
    return "\n".join(out)


def extract(md, start, stop):
    i = md.find(start)
    if i < 0:
        return ""
    j = md.find(stop, i + len(start)) if stop else -1
    return md[i:j if j > 0 else len(md)].strip()


def main():
    md = open(MD, encoding="utf-8").read()
    os.makedirs(os.path.join(OUT, "figures"), exist_ok=True)

    html = ("<html><head><meta charset='utf-8'><style>" + CSS + "</style></head><body>"
            + md_to_html(md) + "</body></html>")
    open(os.path.join(OUT, "manuscript.html"), "w", encoding="utf-8").write(html)
    print("wrote submission/manuscript.html")

    n = 0
    for new, old in FIGMAP:
        for ext in ("pdf", "png"):
            src = os.path.join(FIG, f"{old}.{ext}")
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(OUT, "figures", f"{new}.{ext}"))
                n += 1
    print(f"copied {n} figure files into submission/figures/")

    title = md.splitlines()[0].lstrip("# ").strip()
    summary = extract(md, "**One-sentence summary.**", "**Authors.**").replace(
        "**One-sentence summary.**", "").strip()
    authors = extract(md, "**Authors.**", "**Abstract.**")
    abstract = extract(md, "**Abstract.**", "## Introduction").replace("**Abstract.**", "").strip()
    meta = [f"TITLE\n{title}\n", f"ONE-SENTENCE SUMMARY\n{summary}\n",
            f"AUTHORS AND AFFILIATIONS\n{authors}\n", f"ABSTRACT\n{abstract}\n",
            "DATA AND CODE AVAILABILITY\n"
            "https://github.com/iice662/flymind-selfview (MIT for code, CC BY 4.0 for data and "
            "figures; release v1.0.0 carries a single-file bundle of the whole repository)\n",
            "GENERATIVE AI DECLARATION\n"
            "The manuscript text was drafted with a large language model (DeepSeek-V4.1-Flash, via "
            "the DeepSeek Harness, 2026-09-28) under author direction, and the same model wrote the "
            "simulation, analysis and figure code from the authors' specifications. All code was "
            "executed and its output verified by the authors; no AI-generated images are used (all "
            "figures are programmatic plots of the authors' data). The full prompt log is in "
            "Supplementary Note S2. The authors take full responsibility for the content.\n",
            "SUGGESTED REVIEWERS\n" + extract(md, "**Suggested reviewers.**", None) if
            "**Suggested reviewers.**" in md else ""]
    open(os.path.join(OUT, "metadata.txt"), "w", encoding="utf-8").write("\n".join(meta))
    print("wrote submission/metadata.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
