"""Sync the documents with the rebuilt circuit blob (see results/CORRECTION.md).

The blob was rebuilt after the pool-definition fix: 21,383,937 -> 21,383,125 bytes and
E6829B51... -> FC6B544C..., with the visual pool 2,892 -> 2,689 cells (LPTC 1,770 -> 1,594,
relay 1,122 -> 1,095).  results/CORRECTION.md is a historical record and is NOT touched.

Usage: python tools/sync_docs.py [--check]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_HASH, NEW_HASH = "E6829B51", "FC6B544C"
OLD_LEN, NEW_LEN = "21,383,937", "21,383,125"
FILES = [
    os.path.join(ROOT, "results", "PROVENANCE.md"),
    os.path.join(ROOT, "paper", "supplementary-note-S1.md"),
    os.path.join(ROOT, "paper", "supplementary-note-S2.md"),
    os.path.join(ROOT, "paper", "manuscript.md"),
    os.path.join(ROOT, "DATA-DICTIONARY.md"),
    os.path.join(ROOT, "README.md"),
    os.path.join(ROOT, "paper", "figures.md"),
]
NOTE = """
> **Circuit rebuilt (see `results/CORRECTION.md`).** After the pool-definition fix the blob was
> rebuilt from the same released files and every experiment re-run: `flymind.brain` is now
> **21,383,125 bytes**, SHA256 `FC6B544C68B4C9997987E2BAA788A41ED8E4E91B3B5C60EBC1166947447827AB`
> (pre-fix blob kept as `malecns/flymind-before-poolfix.brain`). The visual pool is now
> **2,689 cells** = 1,594 lobula-plate tangential cells + 1,095 connectome-derived CX relay cells
> (previously 2,892 = 1,770 + 1,122, where the 1,770 wrongly included 176 Johnston's-organ
> `JO-EV*` cells). The reported families are `A4-flow`, `I2-heading`, `J2-n20`, `K2-k150`,
> `L600`-equivalents `L2-k600`, `M2-dose`, `D2-controls`, `P2-propagation`.
"""


def main():
    check = "--check" in sys.argv
    changed = 0
    for p in FILES:
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        o = s
        s = s.replace(OLD_HASH, NEW_HASH).replace(OLD_LEN, NEW_LEN)
        if s != o and not check:
            if "Circuit rebuilt" not in s and p.endswith(("PROVENANCE.md", "DATA-DICTIONARY.md")):
                s = s.rstrip() + "\n" + NOTE
            open(p, "w", encoding="utf-8").write(s)
        if s != o:
            changed += 1
            print(("would update " if check else "updated ") + os.path.relpath(p, ROOT))
            for m in re.finditer(r".{0,60}(?:2,892|1,770|1,122).{0,60}", o):
                print("    pool-count line to review:", m.group(0).replace("\n", " ")[:120])
    print(f"\n{changed} files {'need' if check else ''} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
