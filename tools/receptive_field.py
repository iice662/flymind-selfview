"""Receptive-field proxy for the visual pool, from syn-partners (6.8 GB, streamed).

Why a dedicated reader: the file is 6.8 GB and this machine has ~3 GB of RAM free, so the table
cannot be loaded; `feather_lite.iter_batches` streams it batch by batch instead.  Only five of the
eleven columns are decoded (`body_post`, `primary_post`, `x_post`, `y_post`, `z_post`).

    python tools/receptive_field.py --verify     # decode the first batch and print a schema check
    python tools/receptive_field.py --full       # stream everything, write results/receptive-field.csv

Output (--full): one row per visual-pool cell with the neuropil distribution of its INPUT synapses
(rows whose `body_post` is that cell) and the centroid of those postsynaptic sites, which is the
receptive-field proxy: the optic-lobe position where the cell reads the world.
"""
import argparse
import collections
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_transmitters as FL
from arrow_columns import decode_planned                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "malecns", "syn-partners.feather")
POOL = os.path.join(ROOT, "results", "raw", "slice-census.csv")
OUT = os.path.join(ROOT, "results", "receptive-field.csv")
WANT = ("body_post", "primary_post", "x_post", "y_post", "z_post")


def pool_bodies():
    """body_id -> (index, is_lptc) for the 2,689 cells of the visual pool."""
    out = {}
    with open(POOL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["in_pool"] == "1":
                out[int(r["body_id"])] = (int(r["index"]), int(r["is_lptc"]))
    return out


def run(verify, full):
    pool = pool_bodies()
    print(f"pool cells to map: {len(pool)}")
    nrows = 0
    agg = collections.defaultdict(collections.Counter)     # body -> neuropil -> count
    pos = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    batches = 0
    for d, nodes, bufs, body, fields in FL.iter_batches(SRC):
        cols, _used, _notes = decode_planned(d, nodes, bufs, body, fields)
        have = [c for c in WANT if c in cols]
        if verify and batches == 0:
            print("  columns present:", sorted(cols)[:12])
            for c in WANT:
                v = cols.get(c)
                print(f"  {c:<14} {'MISSING' if not v else str(v[:3])[:70]}")
            n = len(cols.get("body_post") or [])
            print(f"  rows in batch 0: {n}")
        if not full:
            batches += 1
            if batches >= 1:
                return 0
            continue
        bp = cols.get("body_post")
        pp = cols.get("primary_post#index", cols.get("primary_post"))
        if bp is None or pp is None:
            batches += 1
            continue
        xs, ys, zs = cols.get("x_post"), cols.get("y_post"), cols.get("z_post")
        for i, b in enumerate(bp):
            b = int(b)
            if b not in pool:
                continue
            agg[b][pp[i]] += 1
            if xs:
                p = pos[b]
                p[0] += float(xs[i]); p[1] += float(ys[i]); p[2] += float(zs[i]); p[3] += 1
        nrows += len(bp)
        batches += 1
        if batches % 20 == 0:
            print(f"  {batches} batches, {nrows:,} rows, {len(agg):,} pool cells seen", flush=True)
    if not full:
        return 0
    print(f"streamed {batches} batches, {nrows:,} rows; {len(agg)} pool cells have input rows")
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index", "body_id", "is_lptc", "input_synapses", "top_neuropil",
                    "top_neuropil_n", "n_neuropils", "rf_x", "rf_y", "rf_z"])
        for b, (idx, is_lptc) in sorted(pool.items(), key=lambda kv: kv[1][0]):
            c = agg.get(b)
            if not c:
                w.writerow([idx, b, is_lptc, 0, "", 0, 0, "", "", ""])
                continue
            top, k = c.most_common(1)[0]
            p = pos[b]
            w.writerow([idx, b, is_lptc, sum(c.values()), top, k, len(c),
                        round(p[0] / p[3], 1) if p[3] else "", round(p[1] / p[3], 1) if p[3] else "",
                        round(p[2] / p[3], 1) if p[3] else ""])
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    raise SystemExit(run(a.verify or not a.full, a.full))

