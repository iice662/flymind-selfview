"""Rewrite the five stale claim sentences in the manuscript (see results/CORRECTION.md).

Anchors are ASCII-only where possible; the two parentheticals that contain dashes are handled with
regular expressions over the decoded text.  Writes paper/manuscript.md.bak2 first.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "paper", "manuscript.md")

LITERAL = [
    # (anchor, replacement)  -- line 56, Results overview (ii)
    ("(ii) Under yaw drive a slip-free body patch leaves every heading readout equivalent to the natural condition",
     "(ii) Under yaw drive a silent body patch degrades both heading coding and the steering command "
     "(direction tuning versus push-pull wiring 0.309 -> 0.236, d = -3.5; steering fidelity 0.786 -> 0.741, "
     "d = -2.9; at n = 20, d = -4.7 and -3.3 with BF10 = 1.2e14 and 5.8e9), and the part of that damage which "
     "is not explained by input loss is specific to the silence of a spatially compact region"),
    # line 56, item (iii) -- optic flow control
    ("a random patch matched on that quantity reproduces it: d = 0.06, P = 0.89",
     "a random patch matched on that quantity reproduces the firing rate (3.16 vs 3.04 Hz) but not the ring "
     "population vector (bump R 0.353 vs 0.461)"),
    # line 56, item (iv) -- patch size dose
    ("so the null for absence is not a threshold effect.",
     "so the cost of a silent region grows with its size rather than appearing above a threshold."),
    # line 115 -- doubling the trials
    ("One metric does *not* support the null at n = 20",
     "Every readout now supports a difference rather than a null at n = 20, including the one that used to be unresolved"),
    # line 172 -- patch-size dose
    ("produced no monotone change in any readout",
     "produced a monotone degradation in nearly every readout (tuning versus wiring rho = -0.91, CX rate "
     "rho = -0.94, yaw modulation rho = -0.92, population tau rho = -0.79, ring bump R rho = +0.58, all "
     "P = 5e-4, with delivered events flat at rho = +0.07)"),
    ("The absence of a heading effect is therefore not a threshold effect that a larger patch would cross within the range tested.",
     "The cost of a silent region therefore grows smoothly with its size instead of appearing above a threshold, "
     "which is what the corrected drive model predicts and what the pre-fix code could not show."),
    # line 264 -- Fig. 4 legend title
    ("**Fig. 4. Heading: an absent self-signal is tolerated, a conflicting one is not, and the effect is graded.**",
     "**Fig. 4. Heading: a silent body region costs coding, a conflicting one costs fidelity.**"),
    # line 268 -- Fig. S1 legend clause
    ("no monotone trend",
     "monotone degradation"),
]

REGEX = [
    # line 56: drop the pre-fix equivalence parenthetical
    (r"\(±10% bound; BF<sub>01</sub>.*?design ceiling of 3\.24\)", ""),
    # line 56: the (iv) sentence still carries the pre-fix rho/P bounds
    (r"\(all \|ρ\| ≤ 0\.18, P ≥ 0\.28\)", "(all |rho| >= 0.57, P = 5e-4)"),
    # line 268: the Fig. S1 (B) clause keeps its pre-fix bounds
    (r"\(tuning ρ = -0\.91[^)]*\)", ""),
]


def main():
    text = open(DOC, encoding="utf-8").read()
    n = 0
    for a, b in LITERAL:
        if a in text:
            text = text.replace(a, b)
            n += 1
            print("ok   literal:", a[:60])
        else:
            print("MISS literal:", a[:60])
    for pat, b in REGEX:
        text, k = re.subn(pat, b, text)
        n += k
        print(("ok   regex:  " if k else "MISS regex:  ") + pat[:60])
    open(DOC + ".bak2", "w", encoding="utf-8").write(open(DOC, encoding="utf-8").read())
    open(DOC, "w", encoding="utf-8").write(text)
    print(f"\n{n} edits applied; backup at manuscript.md.bak2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
