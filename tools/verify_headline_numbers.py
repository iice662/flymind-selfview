"""Check the paper's headline numbers against the deposited per-trial data.

Every entry is (family, arm, metric, expected value, tolerance).  A failure means the manuscript
and the data disagree - the paper's central failure mode (see results/CORRECTION.md).

Usage: python tools/verify_headline_numbers.py
"""

import csv
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "raw")

# (family, arm, metric, expected, tol)  - values as quoted in results/CORRECTION.md
CHECKS = [
    ("I2-heading", "flow", "cx_rate_hz", 3.952, 5e-3),
    ("I2-heading", "self", "cx_rate_hz", 3.172, 5e-3),
    ("I2-heading", "flow", "cx_tuning_wire_corr", 0.3093, 5e-5),
    ("I2-heading", "self", "cx_tuning_wire_corr", 0.2359, 5e-5),
    ("I2-heading", "randmat", "cx_tuning_wire_corr", 0.310, 5e-4),
    ("I2-heading", "flow", "steer_corr_yaw", 0.786, 5e-4),
    ("I2-heading", "self", "steer_corr_yaw", 0.7405, 5e-4),
    ("I2-heading", "decorr", "steer_corr_yaw", 0.6154, 5e-4),
    ("I2-heading", "self", "dn_rate_hz", 1930, 1.0),
    ("I2-heading", "flow", "cx_yaw_modulation_hz", 1.919, 5e-3),
    ("I2-heading", "self", "cx_yaw_modulation_hz", 1.153, 5e-3),
    ("I2-heading", "self", "bumpR", 0.3585, 5e-5),
    ("I2-heading", "decorr", "bumpR", 0.2742, 5e-5),
    # the manipulation check itself: a body-locked patch must sit below the natural ratio
    ("I2-heading", "flow", "patch_level_ratio", 0.977, 5e-3),
    ("I2-heading", "self", "patch_level_ratio", 0.426, 5e-3),
    ("I2-heading", "decorr", "patch_level_ratio", 0.892, 5e-3),
    # drive matching: every arm delivers the same number of events (within 0.1%)
    ("I2-heading", "self", "injected_events", 6.552e5, 0.1e5),
    ("I2-heading", "decorr", "injected_events", 6.558e5, 0.1e5),
    ("A4-flow", "flow", "cx_rate_hz", 5.93, 5e-3),
    ("A4-flow", "self", "cx_rate_hz", 3.04, 5e-3),
    ("A4-flow", "randmat", "cx_rate_hz", 3.16, 5e-3),
    ("A4-flow", "self", "bumpR", 0.461, 5e-4),
    ("A4-flow", "randmat", "bumpR", 0.353, 5e-4),
    ("J2-n20", "flow", "cx_tuning_wire_corr", 0.312241, 5e-5),
    ("J2-n20", "self", "cx_tuning_wire_corr", 0.245712, 5e-5),
]


def main():
    cache = {}
    bad = 0
    for fam, arm, metric, exp, tol in CHECKS:
        if fam not in cache:
            p = os.path.join(RAW, fam + "-trials.csv")
            if not os.path.exists(p):
                print(f"MISSING  {fam}-trials.csv")
                bad += 1
                continue
            by = {}
            with open(p, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    by.setdefault(row["arm"], []).append(row)
            cache[fam] = by
        rows = cache[fam].get(arm)
        if not rows:
            print(f"MISSING  {fam} / arm {arm}")
            bad += 1
            continue
        got = statistics.fmean(float(r[metric]) for r in rows)
        ok = abs(got - exp) <= tol
        bad += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'} {fam:<11} {arm:<8} {metric:<22} "
              f"data={got:<12.6g} paper={exp:<12.6g} tol={tol:g}")
    print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} checks pass")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
