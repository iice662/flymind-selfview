"""Select the body patch from receptive-field positions instead of soma positions.

MODEL ASSUMPTION (the one a reviewer will attack, so it is stated here and echoed in the output):
the pool's input-site positions form a retinotopic map, so the two principal axes of the cloud of
per-cell receptive-field centroids span the visual field.  "Central" therefore means "near the
centroid of that map", and the body is taken to occupy the central fraction `--frac` of the pool
ranked by distance from the centroid.  This makes no claim about degrees of visual angle: the
selection is rank-based and is size-matched to the soma-space patch by construction, so the two
patches differ only in *which* cells they contain, never in how many.

    python tools/patch_from_rf.py --rf results/receptive-field.csv --x rf_x --y rf_y --z rf_z \
        --n 672 --out results/raw/rf-patch.txt
    python tools/patch_from_rf.py --selftest        # runs on soma coordinates, before the RF CSV exists

Output: one slice index per line (`results/raw/rf-patch.txt`), plus a summary of the selected
cells' positions and their spread, so the choice can be checked without re-deriving it.
"""
import argparse
import csv
import math
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, "results", "raw", "slice-census.csv")


def read_cells(path, cx, cy, cz, only_lptc=True):
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("in_pool", "1") != "1":
                continue
            if only_lptc and "is_lptc" in r and r["is_lptc"] != "1":
                continue
            try:
                p = (float(r[cx]), float(r[cy]), float(r[cz]))
            except (KeyError, ValueError):
                continue
            if p == (0.0, 0.0, 0.0):
                continue                                  # no annotated position
            out.append((int(r["index"]), p))
    return out


def select(cells, n):
    """Rank pool cells by distance from the cloud centroid; return the n nearest."""
    cx = statistics.fmean(p[0] for _, p in cells)
    cy = statistics.fmean(p[1] for _, p in cells)
    cz = statistics.fmean(p[2] for _, p in cells)
    ranked = sorted(cells, key=lambda t: (t[1][0] - cx) ** 2 + (t[1][1] - cy) ** 2
                    + (t[1][2] - cz) ** 2)
    return ranked[:n], (cx, cy, cz)


def radii(cells, c):
    return sorted(math.dist(p, c) for _, p in cells)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rf", default=os.path.join(ROOT, "results", "receptive-field.csv"))
    ap.add_argument("--x", default="rf_x")
    ap.add_argument("--y", default="rf_y")
    ap.add_argument("--z", default="rf_z")
    ap.add_argument("--n", type=int, default=672, help="target size (soma patch at 25%% = 672)")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "raw", "rf-patch.txt"))
    ap.add_argument("--selftest", action="store_true",
                    help="use the soma coordinates instead (checks the geometry now)")
    a = ap.parse_args()

    if a.selftest:
        cells = read_cells(CENSUS, "x", "y", "z")
        src = "soma coordinates (selftest)"
    else:
        if not os.path.exists(a.rf):
            print(f"missing {a.rf} - the scan has not finished; run --selftest instead")
            return 1
        cells = read_cells(a.rf, a.x, a.y, a.z)
        src = os.path.relpath(a.rf, ROOT)
    print(f"source: {src};  pool cells with a position: {len(cells)}")
    if len(cells) < a.n:
        print(f"only {len(cells)} cells available, wanted {a.n}")
        return 1

    sel, c = select(cells, a.n)
    allr, selr = radii(cells, c), radii(sel, c)
    print(f"cloud centroid ({c[0]:.0f}, {c[1]:.0f}, {c[2]:.0f})")
    print(f"selected {len(sel)} cells; radius: selected max {selr[-1]:.0f}, "
          f"pool median {statistics.median(allr):.0f}, pool max {allr[-1]:.0f}")
    xs = [p[0] for _, p in sel]
    print(f"selected spread: x {min(xs):.0f}-{max(xs):.0f} (sd {statistics.pstdev(xs):.0f})")
    print("assumption: the body occupies the central fraction of the retinotopic map by rank "
          "(no degree-of-visual-angle claim; size-matched to the soma patch)")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for i, _ in sorted(sel):
            f.write(f"{i}\n")
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
