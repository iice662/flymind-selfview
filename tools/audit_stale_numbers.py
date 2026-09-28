"""Audit the manuscript for pre-fix numbers (see results/CORRECTION.md).

Every entry is a value that the pre-fix draft quoted and the corrected data no longer supports.
Scan mode prints the exact lines; `--fix` rewrites only the unambiguous single-value cases and
writes manuscript.md.bak first.  Structural claims ("Bayes factors 2.8-3.2", "no heading metric
differed") are reported, never auto-edited: they need new sentences, not new digits.

Usage: python tools/audit_stale_numbers.py [--fix]
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "paper", "manuscript.md")

# old value -> corrected value (from paper/tables.md / results/CORRECTION.md)
VALUES = {
    "3.869": "3.172",        # yaw, self CX rate
    "6.066": "3.952",        # yaw, natural CX rate
    "0.3169": "0.2359",      # yaw, self tuning <-> wiring
    "0.3174": "0.3093",      # yaw, natural tuning
    "2.51": "3.0 x 10^4",    # was BF01, is now BF10
    "0.245": "0.327",        # optic flow, natural bump R
    "0.326": "0.461",        # optic flow, self bump R
    "44.13": "44.87",        # optic flow, natural dimension
    "38.86": "28.62",        # optic flow, self dimension
    "1.314": "0.997",        # optic flow, fluctuation SD
    "0.970": "0.757",
    "246.9": "223.2",        # yaw, natural tau
    "163.3": "150.3",        # yaw/conflict, self tau
    "0.8119": "0.7405",      # steering fidelity
    "0.6057": "0.6154",
    "1.969": "1.153",        # yaw modulation
    "1.253": "0.9366",
    "640.6": "424.3",        # steering amplitude
    "509.1": "431.3",
}
# claims that need rewriting, not renumbering
CLAIMS = [
    r"no heading metric differed",
    r"statistically indistinguishable",
    r"Bayes factors? 2\.8[鈥?]3\.[0-9]",
    r"BF<sub>01</sub> = 2\.8",
    r"tolerates a missing self-signal",
    r"all within 卤10%",
    r"is therefore not a threshold effect",
    r"no monotone (change|trend)",
]


def _a(s):
    """ASCII-safe for the console (GBK code page chokes on arrows and dashes)."""
    return s.encode("ascii", "replace").decode("ascii")


def main():
    fix = "--fix" in sys.argv
    text = open(DOC, encoding="utf-8").read()
    lines = text.splitlines()
    in_banner = False
    hits, claims = [], []
    for i, line in enumerate(lines, 1):
        if line.startswith("> **STATUS"):
            in_banner = True
        elif in_banner and not line.startswith(">"):
            in_banner = False
        if in_banner:
            continue
        for old in VALUES:
            if old in line:
                hits.append((i, old, line.strip()[:150]))
        for pat in CLAIMS:
            if re.search(pat, line, re.I):
                claims.append((i, line.strip()[:150]))

    print(f"manuscript lines: {len(lines)}")
    print(f"\n=== {len(hits)} stale values ===")
    for i, old, ctx in hits:
        print(_a(f"  {i:>4}  {old:>8} -> {VALUES[old]:<12}  {ctx}"))
    print(f"\n=== {len(claims)} stale claims (need new sentences) ===")
    for i, ctx in claims:
        print(_a(f"  {i:>4}  {ctx}"))

    if not fix:
        print("\n(scan only; re-run with --fix to apply the single-value substitutions)")
        return 1 if (hits or claims) else 0

    out = []
    for line in lines:
        for old, new in VALUES.items():
            if old in line and not line.strip().startswith("|"):
                line = line.replace(old, new)
        out.append(line)
    with open(DOC + ".bak", "w", encoding="utf-8") as f:
        f.write(text)
    with open(DOC, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"\napplied; backup at {os.path.basename(DOC)}.bak "
          f"(table rows and the status banner were left untouched)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

