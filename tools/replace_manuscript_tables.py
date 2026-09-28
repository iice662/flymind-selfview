"""Replace the manuscript's three stale tables with the generated, data-checked ones.

The manuscript's Table 1-3 were still the pre-fix versions, marked SUPERSEDED and pointing at
paper/tables.md.  A submitted manuscript cannot carry pointer-stubs where its tables should be, so
this script substitutes the generated tables (which are produced from the deposited CSVs by
tools/make_tables.py) into the region between "## Table 1." and "## Supplementary materials".

    python tools/replace_manuscript_tables.py [--check]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "paper", "manuscript.md")
TABLES = os.path.join(ROOT, "paper", "tables.md")

HEAD = ("| readout |", "| metric |", "| gain |")


def sections(path):
    """-> ordered list of (heading, body-lines) for every '## Table' block."""
    out, cur = [], None
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.startswith("## Table"):
            cur = [line, []]
            out.append(cur)
        elif cur is not None:
            if line.startswith("## ") and not line.startswith("## Table"):
                cur = None
            else:
                cur[1].append(line)
    return out


def main():
    check = "--check" in sys.argv
    text = open(DOC, encoding="utf-8").read()
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("## Table 1."))
        end = next(i for i, l in enumerate(lines) if l.startswith("## Supplementary materials"))
    except StopIteration:
        print("could not locate the table region; nothing changed")
        return 1

    secs = sections(TABLES)
    if len(secs) < 3:
        print(f"expected at least 3 generated tables, found {len(secs)}")
        return 1
    t1, t2, t3 = secs[0], secs[1], secs[2]

    def body(sec, keep_head=False):
        out = []
        for l in sec[1]:
            if l.strip() == "" or l.startswith("Source:"):
                if out and out[-1] == "":
                    continue
                out.append("")
                continue
            out.append(l)
        while out and out[-1] == "":
            out.pop()
        return out

    new = ["## Table 1. Heading readouts per arm (I2-heading, kappa = 300, n = 10 trials per arm)",
           "",
           "Generated from `results/raw/I2-heading-trials.csv` by `python tools\\make_tables.py`; "
           "every value in this table and in Tables 2-3 is recomputed from the deposited per-trial "
           "data, and `python tools\\verify_headline_numbers.py` checks the quoted numbers against it.",
           ""]
    new += body(t1)[1:]                      # skip its heading line
    new += ["", "---", "",
            "## Table 2. Self versus each control manipulation: difference, effect size, "
            "equivalence test and Bayes factor",
            ""]
    new += body(t2)[1:]
    new += ["", "---", "",
            "## Table 3. Conflict dose: every readout against alpha (kappa = 300, n = 10 per level, "
            "6 s per trial)",
            ""]
    new += body(t3)[1:]
    new += ["", "---", ""]

    out = lines[:start] + new + lines[end:]
    print(f"replacing manuscript lines {start + 1}-{end} ({end - start} lines) "
          f"with {len(new)} lines of generated tables")
    if check:
        return 0
    open(DOC + ".bak3", "w", encoding="utf-8").write(text)
    open(DOC, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("wrote", os.path.relpath(DOC, ROOT), "(backup: manuscript.md.bak3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
