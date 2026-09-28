"""Print the headline numbers of every family as a compact digest (one screen per family).

Usage: python tools/digest.py [family ...]      (default: the families reported in the paper)
"""

import csv
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "raw")

FAMILIES = ["I2-heading", "J2-n20", "K2-k150", "L2-k600", "M2-dose", "A4-flow", "D2-controls"]

KEY = ["cx_rate_hz", "cx_active_fraction", "ring_rate_hz", "fanbody_rate_hz", "tau_ms", "dim",
       "pop_rate_sd_hz", "bumpR", "cx_yaw_modulation_hz", "cx_tuning_wire_corr",
       "ring_tuning_wire_corr", "ring_lag_yaw_deg", "ring_loop", "ring_pc12_var",
       "steer_corr_yaw", "steer_asym_sd_hz", "dn_rate_hz"]

ORDER = ["rest", "flow", "self", "shuffle", "randmat", "decorr",
         "conf25", "conf50", "conf75", "drive0.5", "drive1.5", "synch"]


def load(path):
    by = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by.setdefault(row["arm"], {}).setdefault(row["metric"], []).append(float(row["value"]))
    return by


def read_trials(path):
    by = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by.setdefault(row["arm"], []).append(row)
    return by


def ci(v):
    if len(v) < 2:
        return 0.0
    sd = statistics.stdev(v)
    return 1.96 * sd / (len(v) ** 0.5)


def main():
    fams = sys.argv[1:] or FAMILIES
    for fam in fams:
        tp = os.path.join(RAW, fam + "-trials.csv")
        if not os.path.exists(tp):
            print(f"\n### {fam}: MISSING")
            continue
        trials = read_trials(tp)
        arms = [a for a in ORDER if a in trials] + [a for a in trials if a not in ORDER]
        n = {a: len(trials[a]) for a in arms}
        print(f"\n### {fam}  (n per arm: {n})")
        hdr = "metric".ljust(22) + "".join(a[:9].rjust(10) for a in arms)
        print(hdr)
        for m in KEY:
            if m not in trials[arms[0]][0]:
                continue
            line = m.ljust(22)
            for a in arms:
                v = [float(r[m]) for r in trials[a]]
                line += f"{statistics.fmean(v):10.4g}"
            print(line)
        # manipulation check + drive
        for m in ("patch_level_ratio", "injected_events"):
            if m in trials[arms[0]][0]:
                line = m.ljust(22)
                for a in arms:
                    v = [float(r[m]) for r in trials[a]]
                    line += f"{statistics.fmean(v):10.4g}"
                print(line)
        # key contrasts with CI
        eq = os.path.join(RAW, fam + "-equivalence.csv")
        if os.path.exists(eq):
            print("  --- self vs control (diff, d, P, BF01) ---")
            with open(eq, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if not row["contrast"].startswith("self_vs_") or row["metric"] not in KEY:
                        continue
                    print("   %-22s %-18s %10.4g %8.3f %9.3g %9.3g" % (
                        row["metric"], row["contrast"], float(row["diff"]),
                        float(row["cohens_d"]), float(row["p_tost_pct"]), float(row["bf01"])))
        tr = os.path.join(RAW, fam + "-dose-trend.csv")
        if not os.path.exists(tr):
            tr = os.path.join(RAW, fam + "-trend.csv")
        if os.path.exists(tr):
            print("  --- trend vs dose (rho, P) ---")
            with open(tr, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row["metric"] in KEY:
                        print("   %-22s rho=%8.3f  P=%9.3g" % (
                            row["metric"], float(row["spearman_rho_vs_fraction"]),
                            float(row["p_perm_two_sided"])))


if __name__ == "__main__":
    main()
