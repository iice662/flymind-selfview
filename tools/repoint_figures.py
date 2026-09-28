"""One-off: repoint the figure scripts at the corrected families (see results/CORRECTION.md)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SUBS = [
    ('MF.load("A3-flow")', 'MF.load("A4-flow")'),
    ('MF.pair_lookup("A3-flow")', 'MF.pair_lookup("A4-flow")'),
    ('"A3-flow-matching.csv"', '"A4-flow-matching.csv"'),
    ('MF.load("E-conflict")', 'MF.load("I2-heading")'),
    ('MF.load("F-n20")', 'MF.load("J2-n20")'),
    ('MF.load("G-k150")', 'MF.load("K2-k150")'),
    ('MF.load("H-k600")', 'MF.load("L2-k600")'),
    ('MF.load("C3-dose-dose")', 'MF.load("M2-dose-dose")'),
    ('MF.load("C-dose-dose")', 'MF.load("M2-dose-dose")'),
    ('MF.load("D-controls")', 'MF.load("D2-controls")'),
    ('MF.load("B3-heading")', 'MF.load("I2-heading")'),
    ('MF.load("B-heading")', 'MF.load("B3-heading")'),
    ('"B3-heading-matching.csv"', '"I2-heading-matching.csv"'),
    ('"F-n20-equivalence.csv"', '"J2-n20-equivalence.csv"'),
    ('"propagation.stdout.txt"', '"P2-propagation.stdout.txt"'),
    ('"calibration-kappa-sweep.txt"', '"calibration2-sweep.txt"'),
    ('fig5b', 'fig5b'),
]

for name in ("make_main_figures.py", "make_figures.py"):
    p = os.path.join(HERE, name)
    s = open(p, encoding="utf-8").read()
    before = s
    for a, b in SUBS:
        s = s.replace(a, b)
    if s != before:
        open(p, "w", encoding="utf-8").write(s)
        print("patched", name)
for name in ("make_main_figures.py", "make_figures.py"):
    print("---", name)
    for line in open(os.path.join(HERE, name), encoding="utf-8").read().splitlines():
        t = line.strip()
        if t.startswith("MF.load(") or "load_csv(" in t or "stdout.txt" in t or "sweep" in t:
            print("   ", t[:110])
