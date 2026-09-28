"""Numeric comparison of per-trial experiment output.

Reads a *-trials.csv written by tools/CircuitPreview --csv and writes two tables:

  <prefix>-compare.csv   per metric x arm: n, mean, sd, sem, min, max, median
  <prefix>-pairs.csv     per metric x arm pair: diff, ratio, Cohen's d, Welch t, df,
                         p (two-sided, Student t), p (two-sided, permutation)

Only arithmetic and hypothesis-test statistics go in here; nothing is interpreted.
All pairs of arms are compared, not only those against one reference arm, so the
choice of reference stays with the reader.

Usage:
    python compare_trials.py results/raw/A-flow-trials.csv
"""
import csv
import math
import os
import random
import statistics
import sys

NP = 4000           # permutations (only computed for pairs that involve 'self')
SEED = 12345


# ---------------------------------------------------------------- t distribution
def _betacf(a, b, x):
    tiny, eps = 1e-300, 1e-12
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betai(a, b, x):
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbeta) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta) * _betacf(b, a, 1.0 - x) / b


def t_sf_two_sided(t, df):
    """Two-sided p for Student t."""
    if df <= 0 or math.isnan(t):
        return float("nan")
    x = df / (df + t * t)
    return _betai(df / 2.0, 0.5, x)


def t_ppf_two_sided(p, df):
    """t such that the two-sided p equals `p` (bisection; enough for 95% intervals)."""
    lo, hi = 0.0, 1e4
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_sf_two_sided(mid, df) > p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def mean_ci(v, conf=0.95):
    """(lo, hi) confidence interval of the mean."""
    n = len(v)
    if n < 2:
        return (float("nan"), float("nan"))
    m = statistics.fmean(v)
    se = statistics.stdev(v) / math.sqrt(n)
    t = t_ppf_two_sided(1.0 - conf, n - 1)
    return (m - t * se, m + t * se)


def welch_diff_ci(a, b, conf=0.95):
    """(diff, lo, hi, se, df) for mean(a) - mean(b), Welch."""
    na, nb = len(a), len(b)
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va = statistics.variance(a) if na > 1 else 0.0
    vb = statistics.variance(b) if nb > 1 else 0.0
    se2 = va / na + vb / nb
    if se2 <= 0:
        return (ma - mb, float("nan"), float("nan"), 0.0, float("nan"))
    se = math.sqrt(se2)
    df = se2 ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    t = t_ppf_two_sided(1.0 - conf, df)
    return (ma - mb, ma - mb - t * se, ma - mb + t * se, se, df)


def d_ci(a, b, d, conf=0.95):
    """Approximate CI for Cohen's d (Hedges & Olkin standard error)."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2 or math.isnan(d):
        return (float("nan"), float("nan"))
    se = math.sqrt((na + nb) / (na * nb) + d * d / (2 * (na + nb)))
    z = 1.959963985 if conf == 0.95 else 1.959963985
    return (d - z * se, d + z * se)


def hedges_g(a, b, d):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2 or math.isnan(d):
        return float("nan")
    return d * (1.0 - 3.0 / (4.0 * (na + nb) - 9.0))


def mannwhitney(a, b):
    """Mann-Whitney U with tie correction -> (U, z, p_two_sided, rank_biserial)."""
    na, nb = len(a), len(b)
    if na < 1 or nb < 1:
        return (float("nan"),) * 4
    pool = [(x, 0) for x in a] + [(x, 1) for x in b]
    pool.sort(key=lambda t: t[0])
    N = na + nb
    ranks = [0.0] * N
    ties = []
    i = 0
    while i < N:
        j = i
        while j + 1 < N and pool[j + 1][0] == pool[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        ties.append(j - i + 1)
        i = j + 1
    r1 = sum(ranks[k] for k in range(N) if pool[k][1] == 0)
    u1 = r1 - na * (na + 1) / 2.0
    mu = na * nb / 2.0
    tie_term = sum(t ** 3 - t for t in ties)
    var = na * nb / 12.0 * ((N + 1) - tie_term / (N * (N - 1))) if N > 1 else 0.0
    if var <= 0:
        return (u1, float("nan"), float("nan"), 1.0 - 2.0 * u1 / (na * nb))
    z = (u1 - mu - math.copysign(0.5, u1 - mu)) / math.sqrt(var)
    p = math.erfc(abs(z) / math.sqrt(2.0))
    rb = 1.0 - 2.0 * u1 / (na * nb)
    return (u1, z, p, rb)


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, order preserved, monotonicity enforced."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [1.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * pvals[i])
        running = max(running, val)
        adj[i] = running
    return adj


# ---------------------------------------------------------------- equivalence
def t_cdf(t, df):
    """CDF of Student t."""
    two = t_sf_two_sided(abs(t), df)
    return 1.0 - two / 2.0 if t >= 0 else two / 2.0


def tost(a, b, bound):
    """Two one-sided tests for equivalence within +/- bound (raw units).

    Returns (p_tost, lo90, hi90, df, se, diff).  Equivalence is supported when
    p_tost < 0.05, which is exactly the condition that the 90% CI of the difference
    lies inside [-bound, +bound]."""
    na, nb = len(a), len(b)
    va = statistics.variance(a) if na > 1 else 0.0
    vb = statistics.variance(b) if nb > 1 else 0.0
    diff = statistics.fmean(a) - statistics.fmean(b)
    se2 = va / na + vb / nb
    if se2 <= 0:
        return (0.0, diff, diff, float("nan"), 0.0, diff)
    se = math.sqrt(se2)
    df = se2 ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    p1 = 1.0 - t_cdf((diff + bound) / se, df)      # H0: diff <= -bound
    p2 = t_cdf((diff - bound) / se, df)            # H0: diff >= +bound
    t90 = t_ppf_two_sided(0.10, df)
    return (max(p1, p2), diff - t90 * se, diff + t90 * se, df, se, diff)


def bf10_jzs(a, b, r=0.707, ngrid=4001):
    """JZS Bayes factor for two independent samples (Rouder et al. 2009), Cauchy
    prior of scale r on the standardised effect.  BF01 = 1 / BF10."""
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    va = statistics.variance(a)
    vb = statistics.variance(b)
    sp2 = ((na - 1) * va + (nb - 1) * vb) / (na + nb - 2)
    if sp2 <= 0:
        return float("nan")
    se = math.sqrt(sp2 * (1.0 / na + 1.0 / nb))
    t = (statistics.fmean(a) - statistics.fmean(b)) / se
    nu = na + nb - 2
    neff = na * nb / (na + nb)
    denom = (1.0 + t * t / nu) ** (-(nu + 1) / 2.0)

    def integrand(logg):
        g = math.exp(logg)
        prior = r / math.sqrt(2 * math.pi) * g ** -1.5 * math.exp(-r * r / (2 * g))
        # the integration variable is log g, so the Jacobian g must be carried
        return g * prior * (1 + neff * g) ** -0.5 \
            * (1 + t * t / ((1 + neff * g) * nu)) ** (-(nu + 1) / 2.0)

    lo, hi = math.log(1e-8), math.log(1e3)
    h = (hi - lo) / (ngrid - 1)
    total = 0.0
    for i in range(ngrid):
        w = 1.0 if i in (0, ngrid - 1) else (4.0 if i % 2 else 2.0)
        total += w * integrand(lo + i * h)
    total *= h / 3.0
    return total / denom if denom > 0 else float("nan")


def bf_selftest():
    """Anchor points for the Bayes-factor implementation.

    With the default Cauchy scale r = 0.707 and n = 10 per arm, the JZS Bayes factor at
    t = 0 is BF01 = 1 / E[(1 + n_eff g)^(-1/2)] = 2.52 (n_eff = 5), which is the value the
    Rouder et al. 2009 tables give for this design; BF10 must increase monotonically in |t|
    and BF01 must be its reciprocal.  These are printed by --selftest so the number in a
    manuscript can be traced to a check rather than to trust."""
    print("JZS Bayes factor self-test (r = 0.707, n = 10 per arm)")
    for t in (0.0, 0.5, 1.0, 2.0, 3.0, 4.0):
        bf = bf10_jzs([0.0] * 10, [0.0] * 10, 0.707) if False else bf10_from_t(t, 10, 10)
        print(f"  t = {t:4.1f}   BF10 = {bf:9.4f}   BF01 = {1 / bf:9.4f}")


def bf10_from_t(t, n1, n2, r=0.707, ngrid=20001):
    """Same integral driven by t directly (used by the self-test)."""
    nu = n1 + n2 - 2
    neff = n1 * n2 / (n1 + n2)
    denom = (1.0 + t * t / nu) ** (-(nu + 1) / 2.0)

    def integrand(logg):
        g = math.exp(logg)
        prior = r / math.sqrt(2 * math.pi) * g ** -1.5 * math.exp(-r * r / (2 * g))
        return g * prior * (1 + neff * g) ** -0.5 \
            * (1 + t * t / ((1 + neff * g) * nu)) ** (-(nu + 1) / 2.0)

    lo, hi = math.log(1e-8), math.log(1e3)
    h = (hi - lo) / (ngrid - 1)
    total = 0.0
    for i in range(ngrid):
        w = 1.0 if i in (0, ngrid - 1) else (4.0 if i % 2 else 2.0)
        total += w * integrand(lo + i * h)
    return (total * h / 3.0) / denom


def equivalence_rows(rows_out, vals, metrics, sesoi_d=0.5, sesoi_pct=10.0):
    """Equivalence evidence for every self-vs-control contrast of every metric.

    Two bounds, both pre-specifiable before the data are seen:
      * standardised: |Cohen's d| < 0.5 (a medium effect is the smallest one worth
        caring about, so "no difference" means "smaller than medium")
      * raw: |difference| < 10% of the control mean
    p_tost < 0.05 is the equivalence test at those bounds; BF01 > 3 is the
    conventional "moderate evidence for the null", BF01 > 10 "strong"."""
    out = []
    for m in metrics:
        for r in rows_out:
            if r["metric"] != m:
                continue
            a, b = r["a"], r["b"]
            if "self" not in (a, b):
                continue
            ctrl = b if a == "self" else a
            if ctrl not in ("flow", "shuffle", "randmat", "decorr",
                            "drive0.5", "drive1.5", "synch"):
                continue
            va, vb = vals[(m, "self")], vals[(m, ctrl)]
            sign = 1.0 if a == "self" else -1.0
            na, nb = len(va), len(vb)
            sp = math.sqrt(((na - 1) * statistics.variance(va)
                            + (nb - 1) * statistics.variance(vb)) / (na + nb - 2))
            mean_ctrl = statistics.fmean(vb)
            bound_d = sesoi_d * sp
            bound_pct = abs(mean_ctrl) * sesoi_pct / 100.0
            p_d, lo_d, hi_d, df, se, diff = tost(va, vb, bound_d)
            p_pc, lo_p, hi_p, _, _, _ = tost(va, vb, bound_pct)
            bf = bf10_jzs(va, vb)
            out.append({
                "metric": m, "contrast": "self_vs_" + ctrl, "n": na,
                "mean_self": statistics.fmean(va), "mean_ctrl": mean_ctrl,
                "diff": diff, "se": se, "df": df, "cohens_d": sign * r["d"],
                "sesoi_d": sesoi_d, "bound_d_raw": bound_d,
                "p_tost_d": p_d, "ci90_lo_d": lo_d, "ci90_hi_d": hi_d,
                "sesoi_pct": sesoi_pct, "bound_pct_raw": bound_pct,
                "p_tost_pct": p_pc, "ci90_lo_pct": lo_p, "ci90_hi_pct": hi_p,
                "bf10": bf, "bf01": (1.0 / bf if bf and bf > 0 else float("nan")),
            })
    return out


# ---------------------------------------------------------------- statistics
def welch(a, b):
    na, nb = len(a), len(b)
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va = statistics.variance(a) if na > 1 else 0.0
    vb = statistics.variance(b) if nb > 1 else 0.0
    se2 = va / na + vb / nb
    if se2 <= 0:
        return float("nan"), float("nan"), 0.0
    t = (ma - mb) / math.sqrt(se2)
    df = se2 ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)) \
        if na > 1 and nb > 1 and (va > 0 or vb > 0) else 0.0
    return t, df, t_sf_two_sided(t, df)


def cohens_d(a, b):
    na, nb = len(a), len(b)
    va = statistics.variance(a) if na > 1 else 0.0
    vb = statistics.variance(b) if nb > 1 else 0.0
    sp = math.sqrt(((na - 1) * va + (nb - 1) * vb) / max(1, na + nb - 2))
    if sp <= 0:
        return float("nan")
    return (statistics.fmean(a) - statistics.fmean(b)) / sp


def perm_test(a, b, n=NP, seed=SEED):
    obs = abs(statistics.fmean(a) - statistics.fmean(b))
    pool = list(a) + list(b)
    na = len(a)
    rng = random.Random(seed)
    hit = 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(statistics.fmean(pool[:na]) - statistics.fmean(pool[na:])) >= obs - 1e-12:
            hit += 1
    return (hit + 1.0) / (n + 1.0)


# ---------------------------------------------------------------- main
def main():
    if "--selftest" in sys.argv:
        bf_selftest()
        return 0
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src = sys.argv[1]
    prefix = os.path.splitext(src)[0]
    if prefix.endswith("-trials"):
        prefix = prefix[:-len("-trials")]        # A-flow-trials.csv -> A-flow-compare.csv

    rows = []
    with open(src, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(row)
    if not rows:
        print("no rows in", src)
        return 1
    metrics = [k for k in rows[0].keys() if k not in ("arm", "trial")]
    arms = []
    for r in rows:
        if r["arm"] not in arms:
            arms.append(r["arm"])
    vals = {}
    dropped = {}
    for m in metrics:
        for a in arms:
            keep, bad = [], 0
            for r in rows:
                if r["arm"] != a:
                    continue
                x = float(r[m])
                if math.isfinite(x):
                    keep.append(x)
                else:
                    bad += 1          # NaN/inf written by the tool when a fit did not converge
            vals[(m, a)] = keep
            dropped[(m, a)] = bad

    cmp_path = prefix + "-compare.csv"
    with open(cmp_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "arm", "n", "mean", "sd", "sem", "ci95_lo", "ci95_hi",
                    "min", "q1", "median", "q3", "max", "n_excluded_nonfinite"])
        for m in metrics:
            for a in arms:
                v = sorted(vals[(m, a)])
                if not v:
                    w.writerow([m, a, 0, "", "", "", "", "", "", "", "", "", "", dropped[(m, a)]])
                    continue
                lo, hi = mean_ci(v)
                q = statistics.quantiles(v, n=4) if len(v) > 1 else [v[0], v[0], v[0]]
                w.writerow([m, a, len(v), f"{statistics.fmean(v):.6g}",
                            f"{statistics.stdev(v):.6g}" if len(v) > 1 else "0",
                            f"{statistics.stdev(v) / math.sqrt(len(v)):.6g}" if len(v) > 1 else "0",
                            f"{lo:.6g}", f"{hi:.6g}", f"{min(v):.6g}", f"{q[0]:.6g}",
                            f"{statistics.median(v):.6g}", f"{q[2]:.6g}", f"{max(v):.6g}",
                            dropped[(m, a)]])

    pair_path = prefix + "-pairs.csv"
    rows_out = []
    for m in metrics:
        for i in range(len(arms)):
            for j in range(i + 1, len(arms)):
                a, b = arms[i], arms[j]
                va, vb = vals[(m, a)], vals[(m, b)]
                if len(va) < 2 or len(vb) < 2:
                    continue
                ma, mb = statistics.fmean(va), statistics.fmean(vb)
                diff, dlo, dhi, se, df = welch_diff_ci(va, vb)
                t = diff / se if se > 0 else float("nan")
                p = t_sf_two_sided(t, df)
                dd = cohens_d(va, vb)
                glo, ghi = d_ci(va, vb, dd)
                u, z, pmw, rb = mannwhitney(va, vb)
                ratio = (ma / mb) if mb != 0 else float("nan")
                pperm = perm_test(va, vb) if "self" in (a, b) else float("nan")
                rows_out.append({
                    "metric": m, "a": a, "b": b, "mean_a": ma, "mean_b": mb,
                    "diff": diff, "dlo": dlo, "dhi": dhi, "se": se, "df": df,
                    "ratio": ratio, "d": dd, "d_lo": glo, "d_hi": ghi,
                    "g": hedges_g(va, vb, dd), "t": t, "p": p,
                    "U": u, "z": z, "p_mw": pmw, "rb": rb, "p_perm": pperm,
                    "n": len(va)})
    # Holm-Bonferroni inside the primary contrast family of each metric: the three
    # self-vs-control contrasts (self/flow, self/shuffle, self/decorr) regardless of the
    # order the pair was enumerated in.  Raw p is reported for every other pair.
    primary = ("flow", "shuffle", "decorr")
    def is_primary(r):
        s = {r["a"], r["b"]}
        return "self" in s and len(s & set(primary)) == 1
    for m in metrics:
        fam = [r for r in rows_out if r["metric"] == m and is_primary(r)]
        if fam:
            adj = holm([r["p"] for r in fam])
            for r, q in zip(fam, adj):
                r["p_holm"] = q
    with open(pair_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "arm_a", "arm_b", "n_per_arm", "mean_a", "mean_b",
                    "diff_a_minus_b", "diff_ci95_lo", "diff_ci95_hi", "ratio_a_over_b",
                    "cohens_d", "d_ci95_lo", "d_ci95_hi", "hedges_g",
                    "welch_t", "welch_df", "p_welch_two_sided", "p_holm_self_family",
                    "mannwhitney_U", "mw_z", "p_mannwhitney_two_sided", "rank_biserial",
                    "p_perm_two_sided"])
        for r in rows_out:
            holm_s = "" if math.isnan(r.get("p_holm", float("nan"))) else f"{r['p_holm']:.6g}"
            perm_s = "" if math.isnan(r["p_perm"]) else f"{r['p_perm']:.6g}"
            w.writerow([r["metric"], r["a"], r["b"], r["n"],
                        f"{r['mean_a']:.6g}", f"{r['mean_b']:.6g}",
                        f"{r['diff']:.6g}", f"{r['dlo']:.6g}", f"{r['dhi']:.6g}",
                        f"{r['ratio']:.6g}", f"{r['d']:.6g}", f"{r['d_lo']:.6g}",
                        f"{r['d_hi']:.6g}", f"{r['g']:.6g}", f"{r['t']:.6g}",
                        f"{r['df']:.6g}", f"{r['p']:.6g}", holm_s,
                        f"{r['U']:.6g}", f"{r['z']:.6g}", f"{r['p_mw']:.6g}",
                        f"{r['rb']:.6g}", perm_s])

    print(cmp_path)
    print(pair_path)
    eq_path = prefix + "-equivalence.csv"
    eq = equivalence_rows(rows_out, vals, metrics)
    with open(eq_path, "w", newline="", encoding="utf-8") as fh:
        if eq:
            w = csv.DictWriter(fh, fieldnames=list(eq[0].keys()))
            w.writeheader()
            for row in eq:
                w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v)
                            for k, v in row.items()})
    print(eq_path)
    with open(prefix + "-columns.txt", "w", encoding="utf-8") as fh:
        fh.write(
            "columns of %s-compare.csv\n"
            "  metric, arm, n, mean, sd, sem, ci95_lo, ci95_hi (CI of the mean, Student t),\n"
            "  min, q1, median, q3, max, n_excluded_nonfinite (NaN/inf dropped, never imputed)\n\n"
            "columns of %s-pairs.csv  (unpaired: each trial is an independent RNG seed)\n"
            "  metric, arm_a, arm_b, n_per_arm\n"
            "  mean_a, mean_b, diff_a_minus_b = mean_a - mean_b\n"
            "  diff_ci95_lo/hi  Welch CI of the difference, t quantile at df_welch\n"
            "  ratio_a_over_b   mean_a / mean_b\n"
            "  cohens_d         (mean_a - mean_b) / pooled sd (sample sd, n-1)\n"
            "  d_ci95_lo/hi     Hedges & Olkin standard-error approximation\n"
            "  hedges_g         d * (1 - 3/(4*(na+nb)-9))\n"
            "  welch_t, welch_df, p_welch_two_sided   Welch t test, two-sided\n"
            "  p_holm_self_family  Holm-Bonferroni over the three self-vs-control contrasts of\n"
            "                      that metric (self/flow, self/shuffle, self/decorr); blank for\n"
            "                      pairs outside that family\n"
            "  mannwhitney_U    U from arm_a ranks, tie-corrected average ranks\n"
            "  mw_z             normal approximation with continuity correction\n"
            "  p_mannwhitney_two_sided\n"
            "  rank_biserial    = 1 - 2U/(n_a*n_b); +1 = every arm_a value below every arm_b\n"
            "                     value, -1 = every arm_a value above every arm_b value\n"
            "  p_perm_two_sided permutation test, 4000 relabellings, seed 12345; only computed\n"
            "                     for pairs involving 'self'; resolution limit 1/4001 = 0.0002499\n"
            "  (blank field = not computed, e.g. permutation p outside the self family)\n"
            % (os.path.basename(prefix), os.path.basename(prefix)))

    # compact numeric view of the headline pairs, no interpretation
    show = ["cx_rate_hz", "cx_active_fraction", "ring_rate_hz", "columnar_rate_hz",
            "fanbody_rate_hz", "other_rate_hz", "dim", "pop_rate_sd_hz", "bumpR",
            "pair_corr", "tau_ms", "cx_yaw_modulation_hz", "cx_tuning_wire_corr",
            "ring_lag_yaw_deg", "ring_loop", "ring_pc12_var", "injected_events",
            "pool_rate_hz"]
    print()
    hdr = f"{'metric':<24}" + "".join(f"{a:>12}" for a in arms)
    print(hdr)
    for m in [s for s in show if s in metrics]:
        line = f"{m:<24}"
        for a in arms:
            v = vals[(m, a)]
            line += f"{statistics.fmean(v):>12.4g}" if v else f"{'-':>12}"
        print(line)
    print()
    print(f"{'metric':<24}{'contrast':<18}{'self mean [95% CI]':<26}"
          f"{'diff [95% CI] (self - control)':<32}{'d':>8}{'p':>11}{'p_holm':>10}{'p_MW':>11}{'rb':>7}")
    for m in [s for s in show if s in metrics]:
        va = vals[(m, "self")]
        if len(va) < 2:
            continue
        lo, hi = mean_ci(va)
        for ctrl in ("flow", "shuffle", "decorr"):
            r = next((x for x in rows_out if x["metric"] == m
                      and {x["a"], x["b"]} == {"self", ctrl}), None)
            if r is None:
                continue
            # normalise to self - control regardless of the canonical pair order
            if r["a"] == "self":
                diff, dlo, dhi, d, rb = r["diff"], r["dlo"], r["dhi"], r["d"], r["rb"]
                self_mean = r["mean_a"]
            else:
                diff, dlo, dhi, d, rb = -r["diff"], -r["dhi"], -r["dlo"], -r["d"], -r["rb"]
                self_mean = r["mean_b"]
            holm_s = "-" if math.isnan(r.get("p_holm", float("nan"))) else f"{r['p_holm']:.3g}"
            print(f"{m:<24}{('self vs ' + ctrl):<18}"
                  + f"{self_mean:.4g} [{lo:.4g}, {hi:.4g}]".ljust(26)
                  + f"{diff:.4g} [{dlo:.4g}, {dhi:.4g}]".ljust(32)
                  + f"{d:>8.3f}{r['p']:>11.3g}{holm_s:>10}{r['p_mw']:>11.3g}{rb:>7.3f}")
    print()
    print("=== equivalence (self vs control): TOST at |d| < 0.5 and at |diff| < 10% of the"
          " control mean, plus JZS BF01 (BF01 > 3 = moderate evidence for no difference) ===")
    print(f"{'metric':<24}{'contrast':<17}{'diff':>11}{'d':>8}{'p_tost_d':>10}{'p_tost_pct':>11}"
          f"{'BF01':>10}{'BF10':>10}{'90% CI (d-bound)':>26}")
    for row in eq:
        ci = "[" + format(row["ci90_lo_d"], ".4g") + ", " + format(row["ci90_hi_d"], ".4g") + "]"
        print(f"{row['metric']:<24}{row['contrast']:<17}{row['diff']:>11.4g}"
              f"{row['cohens_d']:>8.3f}{row['p_tost_d']:>10.3g}{row['p_tost_pct']:>11.3g}"
              f"{row['bf01']:>10.3g}{row['bf10']:>10.3g}{ci:>26}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
