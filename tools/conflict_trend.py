"""Conflict-strength dose-response from a per-trial CSV.

Maps arm id -> conflict strength alpha (self = 0, conf25/50/75 = 0.25/0.5/0.75, decorr = 1) and
tests each metric for a monotone trend against alpha, at the trial level, with a permutation p.

Usage:
    python conflict_trend.py results/raw/E-conflict-trials.csv [--arms self,conf25,conf50,conf75,decorr]
"""
import csv
import math
import statistics
import sys

ALPHA = {"self": 0.0, "conf25": 0.25, "conf50": 0.50, "conf75": 0.75, "decorr": 1.0,
         "flow": None, "shuffle": None, "randmat": None, "rest": None}


def spearman(x, y):
    def ranks(v):
        idx = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i0 = 0
        while i0 < len(v):
            j = i0
            while j + 1 < len(v) and v[idx[j + 1]] == v[idx[i0]]:
                j += 1
            avg = (i0 + j) / 2.0 + 1.0
            for k in range(i0, j + 1):
                r[idx[k]] = avg
            i0 = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    sx = sum((a - mx) ** 2 for a in rx)
    sy = sum((b - my) ** 2 for b in ry)
    if sx <= 0 or sy <= 0:
        return 0.0
    return sum((rx[i] - mx) * (ry[i] - my) for i in range(len(x))) / math.sqrt(sx * sy)


def perm_p(x, y, n=4000, seed=12345):
    import random
    obs = abs(spearman(x, y))
    rng = random.Random(seed)
    xs = list(x)
    hit = 0
    for _ in range(n):
        rng.shuffle(xs)
        if abs(spearman(xs, y)) >= obs - 1e-12:
            hit += 1
    return (hit + 1.0) / (n + 1.0)


def main():
    src = sys.argv[1]
    only = None
    if "--arms" in sys.argv:
        only = sys.argv[sys.argv.index("--arms") + 1].split(",")
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    metrics = [k for k in rows[0].keys() if k not in ("arm", "trial")]
    xs, ys = {m: [] for m in metrics}, {m: [] for m in metrics}
    for r in rows:
        a = r["arm"]
        if a not in ALPHA or ALPHA[a] is None:
            continue
        if only and a not in only:
            continue
        for m in metrics:
            try:
                v = float(r[m])
            except ValueError:
                continue
            if not math.isfinite(v):
                continue
            xs[m].append(ALPHA[a])
            ys[m].append(v)
    print(f"{'metric':<28}{'rho(alpha)':>12}{'p_perm':>10}{'n':>6}   alpha=0 -> 1 (mean)")
    out = []
    for m in metrics:
        if len(xs[m]) < 8:
            continue
        rho = spearman(xs[m], ys[m])
        p = perm_p(xs[m], ys[m])
        by = {}
        for a, v in zip(xs[m], ys[m]):
            by.setdefault(a, []).append(v)
        means = "  ".join(f"{statistics.fmean(by[a]):.4g}" for a in sorted(by))
        out.append((m, rho, p, len(xs[m]), means))
    for m, rho, p, n, means in sorted(out, key=lambda t: t[2]):
        print(f"{m:<28}{rho:>12.3f}{p:>10.4f}{n:>6}   {means}")
    print("\n(alpha = fraction of the body patch's slip replaced by a block-shuffled copy of the"
          " same waveform; rho < 0 = the metric degrades as conflict grows)")


if __name__ == "__main__":
    main()
