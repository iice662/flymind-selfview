"""Update the pool census in the documents and in the Figure 1A census block.

Pre-fix pool: 2,892 = self_motion 1,770 (which wrongly included 176 JO-EV) + visualrelay 1,122.
Post-fix pool: 2,689 = self_motion 1,594 + visualrelay 1,095.  See results/CORRECTION.md.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBS = [
    ("the 1,770 rotation-sensitive lobula plate tangential cells (H1, H2, V1, VS, HS, JO-EV, LHAV, LHPV) plus the 1,122 cells",
     "the 1,594 rotation-sensitive lobula plate tangential cells (H1, H2, V1, VS, HS, LHAV, LHPV) plus the 1,095 cells"),
    ("LPTC 1,770, CX 1,400", "LPTC 1,594, CX 1,400"),
    ("2,892-cell visual pool", "2,689-cell visual pool"),
    ("2,892 | `self_motion`(1,770)", "2,689 | `self_motion`(1,594)"),
    ("visualrelay 1,122", "visualrelay 1,095"),
    ('("LPTC", 1770)', '("LPTC", 1594), ("CX relay", 1095)'),
    ("1,122 cells that form the connectome-defined relay", "1,095 cells that form the connectome-defined relay"),
]
FILES = ["paper/manuscript.md", "DATA-DICTIONARY.md", "results/PROVENANCE.md",
         "paper/supplementary-note-S1.md", "tools/make_main_figures.py"]


def main():
    for rel in FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        o = s
        for a, b in SUBS:
            s = s.replace(a, b)
        if s != o:
            open(p, "w", encoding="utf-8").write(s)
            print("patched", rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
