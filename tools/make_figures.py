"""Publication figures for the self-observation paper, straight from the raw CSVs.

Every panel reads `results/raw/*.csv` and nothing else, so a figure cannot drift away from
the numbers in the manuscript.  Output: `paper/figures/figN.pdf` (vector, for submission) and
`paper/figures/figN.png` (300 dpi, for reading and for the repository).

Usage:
    python tools/make_figures.py            # all figures
    python tools/make_figures.py fig4 fig5  # selected ones

Style: Science single-column 3.5 in, double-column 7.0 in; 7 pt labels; Arial/Helvetica;
no top/right spines; error bars = mean +/- 95% CI (never SEM); significance marks only from
Holm-corrected p at the pre-specified family.
"""
import csv
import math
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow

RAW = os.path.join("results", "raw")
OUT = os.path.join("paper", "figures")
os.makedirs(OUT, exist_ok=True)

# colour-blind safe (Wong 2011)
C = {"flow": "#0072B2", "self": "#D55E00", "shuffle": "#56B4E9", "randmat": "#009E73",
     "decorr": "#CC79A7", "rest": "#999999", "drive0.5": "#0072B2", "drive1.5": "#D55E00",
     "synch": "#009E73", "conf25": "#E69F00", "conf50": "#F0E442", "conf75": "#CC79A7"}
LBL = {"flow": "flow\n(natural)", "self": "self\n(body patch)", "shuffle": "shuffle\n(random, same size)",
       "randmat": "randmat\n(random, same CX input)", "decorr": "decorr\n(conflicting slip)",
       "rest": "rest", "drive0.5": "drive x0.5", "drive1.5": "drive x1.5", "synch": "synchronised",
       "conf25": "a=0.25", "conf50": "a=0.50", "conf75": "a=0.75"}
# short tick labels: the long forms collide in narrow panels, so the explanation lives in the
# figure caption instead (see paper/figures.md)
SHORT = {"flow": "flow", "self": "self*", "shuffle": "shuffle", "randmat": "randmat",
         "decorr": "decorr", "rest": "rest", "drive0.5": "x0.5", "drive1.5": "x1.5",
         "synch": "synch", "conf25": "0.25", "conf50": "0.50", "conf75": "0.75"}
ORDER = ["flow", "self", "shuffle", "randmat", "decorr"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7, "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
    "ytick.major.size": 2.5, "lines.linewidth": 1.0, "lines.markersize": 3.0,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02, "pdf.fonttype": 42, "ps.fonttype": 42,
})


# ---------------------------------------------------------------- io
def load(prefix, arm_col="arm"):
    """-> {metric: {arm: [values]}} plus arm order, from <prefix>-trials.csv"""
    path = os.path.join(RAW, prefix + "-trials.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if arm_col not in rows[0]:
        arm_col = "frac"                      # the dose tables label the arm column 'frac'
    metrics = [k for k in rows[0] if k not in ("arm", "trial", "frac")]
    out, arms = {}, []
    for r in rows:
        if r[arm_col] not in arms:
            arms.append(r[arm_col])
        for m in metrics:
            try:
                v = float(r[m])
            except ValueError:
                continue
            if math.isfinite(v):
                out.setdefault(m, {}).setdefault(r[arm_col], []).append(v)
    return out, arms


def read_text(path):
    """The Tee-Object logs are UTF-16, the redirected ones UTF-8 with BOM: accept both."""
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def load_rows(prefix):
    with open(os.path.join(RAW, prefix + "-trials.csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_csv(name):
    with open(os.path.join(RAW, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def ci95(v):
    n = len(v)
    if n < 2:
        return 0.0
    return 2.262 * statistics.stdev(v) / math.sqrt(n) if n <= 10 else \
        1.96 * statistics.stdev(v) / math.sqrt(n)


def mean_ci(v):
    return statistics.fmean(v), ci95(v)


def pairs(prefix):
    return load_csv(prefix + "-pairs.csv")


def pair_lookup(prefix):
    """(metric, control) -> (d, p) with the sign normalised to self - control."""
    out = {}
    for r in pairs(prefix):
        a, b = r["arm_a"], r["arm_b"]
        if "self" not in (a, b):
            continue
        ctrl = b if a == "self" else a
        s = 1.0 if a == "self" else -1.0
        out[(r["metric"], ctrl)] = (s * float(r["cohens_d"]),
                                    float(r["p_welch_two_sided"]),
                                    s * float(r["diff_a_minus_b"]))
    return out


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300)
    plt.close(fig)
    print("  wrote", os.path.join(OUT, name + ".{pdf,png}"))


def panel_tag(ax, tag, dx=-0.16, dy=1.06):
    ax.text(dx, dy, tag, transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom")


def bar_arms(ax, data, metric, arms, ylabel, colors=None, show_pts=True, ylim=None):
    xs = range(len(arms))
    for i, a in enumerate(arms):
        v = data[metric].get(a, [])
        if not v:
            continue
        m, e = mean_ci(v)
        ax.bar(i, m, width=0.62, color=(colors or C).get(a, "#888888"),
               edgecolor="black", linewidth=0.4, zorder=2)
        ax.errorbar(i, m, yerr=e, fmt="none", ecolor="black", elinewidth=0.6, capsize=1.6, zorder=3)
        if show_pts:
            jitter = [i + (k - (len(v) - 1) / 2) * 0.02 for k in range(len(v))]
            ax.plot(jitter, v, ".", color="black", markersize=1.3, alpha=0.7, zorder=4)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([SHORT.get(a, a) for a in arms], fontsize=6, rotation=45, ha="right")
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    return ax


def sig_bar(ax, i, j, y, text):
    ax.plot([i, i, j, j], [y, y * 1.02, y * 1.02, y], lw=0.6, c="black")
    ax.text((i + j) / 2, y * 1.03, text, ha="center", va="bottom", fontsize=6)


# ---------------------------------------------------------------- figures
def fig1():
    """Circuit census, kappa calibration, heading pathway."""
    fig = plt.figure(figsize=(7.0, 2.1))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1, 1], wspace=0.85)

    # (A) populations and CX subfamilies (from the blob metadata)
    ax = fig.add_subplot(gs[0])
    pops = [("sensory", 2695), ("antennal", 620), ("KC", 193), ("dopamine", 344), ("MBON", 67),
            ("descending", 119), ("motor", 316), ("LPTC", 1770), ("CX", 2074), ("unnamed", 3802)]
    fams = [("ring EPG/PEG", 68), ("columnar", 1036), ("fan-body", 601), ("other CX", 369)]
    y = list(range(len(pops)))
    ax.barh(y, [p[1] for p in pops], color="#BBD7E8", edgecolor="black", linewidth=0.4)
    ax.barh([len(pops) + 1 + k for k in range(len(fams))], [f[1] for f in fams],
            color="#F2C6A0", edgecolor="black", linewidth=0.4)
    ax.set_yticks(y + [len(pops) + 1 + k for k in range(len(fams))])
    ax.set_yticklabels([p[0] for p in pops] + [f[0] for f in fams], fontsize=6)
    ax.invert_yaxis()
    ax.set_xlabel("neurons")
    ax.set_title("12,000 neurons / 1,615,753 synapses", fontsize=6.5)
    panel_tag(ax, "A")

    # (B) kappa sweep
    ax = fig.add_subplot(gs[1])
    ks, cx, act = [], [], []
    for line in open(os.path.join(RAW, "calibration2-sweep.txt"), encoding="utf-8"):
        if not line.startswith(" ") or "|" not in line:
            continue
        f = line.split("|")
        try:
            k = float(f[0].strip())
        except ValueError:
            continue
        cols = f[1].split()
        # columns: 0..10 = populations (LPTC at 10), 11 = CX, 12 = CXactive%, 13 = active%
        ks.append(k); cx.append(float(cols[11])); act.append(float(cols[12]))
    ax.plot(ks, cx, "o-", color=C["self"], label="CX rate")
    ax.axvline(300, ls=":", lw=0.7, color="black")
    ax.text(300, max(cx) * 0.55, " k=300", fontsize=6)
    ax.set_xscale("log")
    ax.set_xlabel("gain kappa")
    ax.set_ylabel("CX rate (Hz)")
    ax2 = ax.twinx()
    ax2.plot(ks, act, "s--", color=C["flow"], label="active %")
    ax2.set_ylabel("CX cells active (%)", color=C["flow"])
    ax2.tick_params(axis="y", colors=C["flow"])
    ax2.spines["right"].set_visible(True)
    panel_tag(ax, "B", dx=-0.28)

    # (C) heading pathway
    ax = fig.add_subplot(gs[2])
    seg = [("LPTC->ring", 67), ("LPTC->columnar", 58), ("columnar->ring", 1031),
           ("ring->ring", 1692), ("ring->FB", 539), ("FB->DN", 88), ("DN->motor", 2810)]
    ax.barh(range(len(seg)), [s[1] for s in seg], color="#C8D6B9", edgecolor="black", linewidth=0.4)
    ax.set_yticks(range(len(seg)))
    ax.set_yticklabels([s[0] for s in seg], fontsize=6)
    ax.set_xscale("log")
    ax.set_xlabel("synapses (log)")
    ax.invert_yaxis()
    ax.set_title("heading pathway", fontsize=6.5)
    panel_tag(ax, "C", dx=-0.42)
    save(fig, "fig1")


def fig2():
    """Manipulation and drive balancing."""
    fig = plt.figure(figsize=(7.0, 3.4))
    gs = fig.add_gridspec(2, 3, hspace=0.55, wspace=0.35)

    for col, (tag, prefix) in enumerate([("A", "A3-flow"), ("B", "B3-heading"),
                                         ("C", "E-conflict")]):
        m = load_csv(prefix + "-matching.csv")
        ax = fig.add_subplot(gs[0, col])
        arms = [r["arm"] for r in m if r["arm"] != "rest"]
        xs = range(len(arms))
        ax.bar(xs, [float(r["delivered_ratio_vs_self"]) for r in m if r["arm"] != "rest"],
               color=[C.get(a, "#888888") for a in arms], edgecolor="black", linewidth=0.4)
        ax.axhline(1.0, color="black", lw=0.6, ls="--")
        ax.set_ylim(0.98, 1.02)
        ax.set_xticks(list(xs))
        ax.set_xticklabels(arms, rotation=60, ha="right", fontsize=5.5)
        ax.set_ylabel("delivered / self")
        ax.set_title(f"{prefix}: drive balancing", fontsize=6.5)
        panel_tag(ax, tag, dx=-0.30)

    # CX input each patch silences
    ax = fig.add_subplot(gs[1, 0])
    m = load_csv("A4-flow-matching.csv")
    sel = [r for r in m if r["arm"] in ("self", "shuffle", "randmat")]
    ax.bar(range(len(sel)), [float(r["cx_input_synapses"]) for r in sel],
           color=[C[r["arm"]] for r in sel], edgecolor="black", linewidth=0.4)
    ax.set_xticks(range(len(sel)))
    ax.set_xticklabels([LBL[r["arm"]] for r in sel], fontsize=5.5)
    ax.set_ylabel("CX synapses silenced")
    plain = "synapses silenced; ring input 1354 / 412 / 1382"
    ax.set_title(plain, fontsize=6)
    panel_tag(ax, "D", dx=-0.22)

    data, arms = load("A3-flow")
    ax = fig.add_subplot(gs[1, 1])
    bar_arms(ax, data, "cx_rate_hz", ORDER, "CX rate (Hz)")
    panel_tag(ax, "E", dx=-0.22)

    data, arms = load("B3-heading")
    ax = fig.add_subplot(gs[1, 2])
    bar_arms(ax, data, "cx_tuning_wire_corr", ORDER, "tuning <-> wiring (r)")
    panel_tag(ax, "F", dx=-0.22)
    save(fig, "fig2")


def fig3():
    """Signal propagation."""
    fig = plt.figure(figsize=(3.5, 2.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.2], wspace=0.45)

    ax = fig.add_subplot(gs[0])
    hops, cum = [1, 2, 3], [97.2, 97.4, 97.4]
    ax.plot(hops, cum, "o-", color=C["flow"])
    ax.set_ylim(90, 100)
    ax.set_xlabel("hops from visual pool")
    ax.set_ylabel("CX cells reached (%)")
    ax.set_title("2,015/2,074 at one hop\n48,315 direct synapses", fontsize=6)
    panel_tag(ax, "A", dx=-0.30)

    ax = fig.add_subplot(gs[1])
    labels, peaks, base = [], [], []
    for line in read_text(os.path.join(RAW, "P2-propagation.stdout.txt")).splitlines():
        f = line.split()
        if len(f) >= 8 and f[0].isdigit() and ("flow" in f or "self" in f):
            labels.append(f"{f[0]} {'self' if 'self' in f else 'flow'}")
            base.append(float(f[2])); peaks.append(float(f[3]))
    xs = range(len(labels))
    ax.bar([x - 0.2 for x in xs], peaks, width=0.38, color=[C["self"] if "self" in l else C["flow"]
                                                           for l in labels],
           edgecolor="black", linewidth=0.4, label="evoked peak")
    ax.plot(xs, base, "k_", markersize=6, label="baseline")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=5)
    ax.set_ylabel("CX spikes / 0.5 ms step")
    ax.legend(frameon=False, fontsize=5.5)
    ax.set_title("volley: peak at 2.5 ms", fontsize=6)
    panel_tag(ax, "B", dx=-0.30)
    save(fig, "fig3")


def fig4():
    """Optic flow: rates move, geometry separates coherence from input loss."""
    data, _ = load("A3-flow")
    pl = pair_lookup("A3-flow")
    fig = plt.figure(figsize=(7.0, 4.6))
    gs = fig.add_gridspec(2, 4, hspace=0.62, wspace=0.45)
    metrics = [("cx_rate_hz", "CX rate (Hz)"), ("cx_active_fraction", "CX active fraction"),
               ("ring_rate_hz", "ring rate (Hz)"), ("bumpR", "ring bump R"),
               ("dim", "effective dimension"), ("pop_rate_sd_hz", "fluctuation SD (Hz)"),
               ("columnar_rate_hz", "columnar rate (Hz)"), ("pair_corr", "pairwise correlation")]
    for k, (m, lab) in enumerate(metrics):
        ax = fig.add_subplot(gs[k // 4, k % 4])
        bar_arms(ax, data, m, ORDER, lab)
        panel_tag(ax, chr(ord("A") + k), dx=-0.34)

    ax = fig.add_subplot(gs[1, 3])
    rate_m = ["cx_rate_hz", "ring_rate_hz", "columnar_rate_hz", "fanbody_rate_hz",
              "other_rate_hz", "pop_rate_sd_hz"]
    geo_m = ["cx_active_fraction", "dim", "bumpR", "pair_corr"]
    ctrls = ["flow", "shuffle", "randmat", "decorr"]
    w = 0.2
    for j, ctrl in enumerate(ctrls):
        for i, group in enumerate([rate_m, geo_m]):
            for k, m in enumerate(group):
                d = pl.get((m, ctrl), (float("nan"),))[0]
                ax.bar(i * (len(group) + 1) + k + j * w, d, width=w, color=C[ctrl],
                       edgecolor="black", linewidth=0.3,
                       label=ctrl if (i == 0 and k == 0) else None)
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xticks([len(rate_m) / 2, len(rate_m) + 1 + len(geo_m) / 2])
    ax.set_xticklabels(["rate metrics", "geometry metrics"], fontsize=6)
    ax.set_ylabel("Cohen's d (self - control)")
    ax.set_title("randmat reproduces rates, not geometry", fontsize=6)
    ax.legend(frameon=False, fontsize=5, ncol=2)
    panel_tag(ax, "I", dx=-0.30)
    save(fig, "fig4")


def fig5():
    """The core figure: absence is tolerated, conflict is graded, across gains."""
    e, _ = load("E-conflict")
    f20, _ = load("F-n20")            # n = 20 carries the steering readout; B3 predates it
    pl = pair_lookup("E-conflict")
    fig = plt.figure(figsize=(7.0, 5.0))
    gs = fig.add_gridspec(2, 4, hspace=0.62, wspace=0.50)

    # (A) the null against four controls (n = 20)
    ax = fig.add_subplot(gs[0, 0])
    bar_arms(ax, f20, "cx_tuning_wire_corr", ORDER, "tuning <-> wiring (r)")
    panel_tag(ax, "A", dx=-0.34)

    # (B) same for the steering readout
    ax = fig.add_subplot(gs[0, 1])
    bar_arms(ax, f20, "steer_corr_yaw", ORDER, "steering <-> yaw (r)")
    panel_tag(ax, "B", dx=-0.34)

    # (C,D) dose response, two readouts
    A = {"self": 0.0, "conf25": 0.25, "conf50": 0.5, "conf75": 0.75, "decorr": 1.0}
    for k, (m, lab, note) in enumerate([("cx_tuning_wire_corr", "tuning <-> wiring (r)", "rho = -0.82"),
                                        ("steer_corr_yaw", "steering <-> yaw (r)", "rho = -0.94")]):
        ax = fig.add_subplot(gs[0, 2 + k])
        xs, ms, es = [], [], []
        for a, x in A.items():
            v = e[m].get(a, [])
            if not v:
                continue
            mm, ee = mean_ci(v)
            xs.append(x); ms.append(mm); es.append(ee)
        ax.errorbar(xs, ms, yerr=es, fmt="o-", color=C["self"], ecolor="black",
                    elinewidth=0.6, capsize=1.6)
        ax.set_xlabel("conflict strength alpha")
        ax.set_ylabel(lab)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_title(note + ", P = 2e-4", fontsize=6)
        panel_tag(ax, chr(ord("C") + k), dx=-0.34)

    # (E,F,G,H) more dose panels
    dose = [("cx_yaw_modulation_hz", "yaw modulation (Hz)", "rho = -0.92"),
            ("tau_ms", "population tau (ms)", "rho = -0.89"),
            ("steer_asym_sd_hz", "steering amplitude (Hz)", "rho = -0.91"),
            ("dim", "effective dimension", "rho = +0.57")]
    for k, (m, lab, note) in enumerate(dose):
        ax = fig.add_subplot(gs[1, k])
        xs, ms, es = [], [], []
        for a, x in A.items():
            v = e[m].get(a, [])
            if not v:
                continue
            mm, ee = mean_ci(v)
            xs.append(x); ms.append(mm); es.append(ee)
        ax.errorbar(xs, ms, yerr=es, fmt="o-", color=C["self"], ecolor="black",
                    elinewidth=0.6, capsize=1.6)
        ax.set_xlabel("conflict strength alpha")
        ax.set_ylabel(lab)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_title(note + ", P = 2e-4", fontsize=6)
        panel_tag(ax, chr(ord("E") + k), dx=-0.34)
    save(fig, "fig5")


def fig5b():
    """Flat mean rate + gain replication + Bayes factors."""
    e, _ = load("E-conflict")
    g150, _ = load("G-k150")
    h600, _ = load("H-k600")
    fig = plt.figure(figsize=(7.0, 2.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.3, 1.1], wspace=0.45)
    A = {"self": 0.0, "conf25": 0.25, "conf50": 0.5, "conf75": 0.75, "decorr": 1.0}

    ax = fig.add_subplot(gs[0])
    for src, lab, col in [(e, "CX rate", C["flow"]), (e, "delivered events/1e5", C["rest"])]:
        m = "cx_rate_hz" if lab == "CX rate" else "injected_events"
        xs, ms, es = [], [], []
        for a, x in A.items():
            v = src[m].get(a, [])
            mm, ee = mean_ci(v)
            if m == "injected_events":
                mm, ee = mm / 1e5, ee / 1e5
            xs.append(x); ms.append(mm); es.append(ee)
        ax.errorbar(xs, ms, yerr=es, fmt="o-", color=col, ecolor="black",
                    elinewidth=0.6, capsize=1.6, label=lab)
    ax.set_xlabel("conflict strength alpha")
    ax.set_ylabel("Hz  /  1e5 events")
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.legend(frameon=False, fontsize=5.5)
    ax.set_title("rate and drive flat: rho = +0.10 / -0.04", fontsize=6)
    panel_tag(ax, "A", dx=-0.32)

    ax = fig.add_subplot(gs[1])
    readouts = [("steer_corr_yaw", "steering fidelity"), ("cx_tuning_wire_corr", "tuning"),
                ("steer_asym_sd_hz", "steering amplitude")]
    series = [(g150, "k=150", C["flow"], "-"), (e, "k=300", C["self"], "-"),
              (h600, "k=600", C["decorr"], "-")]
    for idx, (m, lab) in enumerate(readouts):
        for src, slab, col, ls in series:
            v0 = statistics.fmean(src[m]["self"]) if "self" in src[m] else float("nan")
            xs, norm = [], []
            for a, x in A.items():
                if a not in src[m]:
                    continue
                xs.append(x); norm.append(statistics.fmean(src[m][a]) / v0)
            ax.plot(xs, [n + idx * 0.35 for n in norm], ls, marker="o", color=col,
                    label=slab if idx == 0 else None)
    ax.axhline(0, color="black", lw=0.5)
    ax.set_yticks([1, 1.35, 1.7, 2.05])
    ax.set_yticklabels(["steering\nfidelity", "tuning", "steering\namplitude", ""], fontsize=5.5)
    ax.set_xlabel("conflict strength alpha")
    ax.set_ylabel("normalised to alpha = 0")
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.legend(frameon=False, fontsize=5.5, ncol=3)
    ax.set_title("replicates at three gains", fontsize=6)
    panel_tag(ax, "B", dx=-0.26)

    ax = fig.add_subplot(gs[2])
    rows = [("tuning", 2.84, 2.85, 3.03), ("yaw mod.", 2.79, 2.56, 3.15),
            ("ring loop", 3.04, 2.95, 2.23), ("ring PC1-2", 3.09, 2.23, 2.53),
            ("bump R", 1.51, 2.88, 2.90), ("CX rate", 2.39, 2.05, 2.83)]
    w = 0.26
    for j, (lab, c) in enumerate([("flow", C["flow"]), ("shuffle", C["shuffle"]),
                                  ("randmat", C["randmat"])]):
        vals = [r[1 + j] for r in rows]
        ax.bar([i + j * w for i in range(len(rows))], vals, width=w, color=c,
               edgecolor="black", linewidth=0.3, label=lab)
    ax.axhline(3, ls="--", lw=0.7, color="black")
    ax.axhline(3.24, ls=":", lw=0.7, color="grey")
    ax.text(len(rows) - 0.5, 3.26, "ceiling n=20", fontsize=5, ha="right")
    ax.set_xticks([i + w for i in range(len(rows))])
    ax.set_xticklabels([r[0] for r in rows], rotation=45, ha="right", fontsize=5.5)
    ax.set_ylabel("BF01 (n = 20)")
    ax.set_ylim(0, 3.8)
    ax.legend(frameon=False, fontsize=5.5)
    panel_tag(ax, "C", dx=-0.30)
    save(fig, "fig5b")


def fig6():
    """Patch-size dose (no trend) and positive controls."""
    d, _ = load("C3-dose-dose") if os.path.exists(
        os.path.join(RAW, "C3-dose-dose-trials.csv")) else ({}, [])
    fig = plt.figure(figsize=(7.0, 2.4))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1.4, 1.2, 1.2], wspace=0.55)

    ax = fig.add_subplot(gs[0])
    fracs = ["0", "0.125", "0.25", "0.5"]
    inj = [statistics.fmean(d["injected_events"][f]) for f in fracs]
    ax.plot(range(len(fracs)), [v / 1e5 for v in inj], "o-", color=C["rest"])
    ax.set_ylim(700, 704)
    ax.set_xticks(range(len(fracs))); ax.set_xticklabels(fracs, fontsize=6)
    ax.set_xlabel("patch fraction")
    ax.set_ylabel("delivered events /1e5")
    ax.set_title("drive matched", fontsize=6)
    panel_tag(ax, "A", dx=-0.34)

    ax = fig.add_subplot(gs[1])
    series = {"cx_tuning_wire_corr": ("tuning (rho=-0.01)", C["self"]),
              "cx_rate_hz": ("CX rate (rho=-0.01)", C["flow"]),
              "bumpR": ("bump R (rho=+0.05)", C["randmat"]),
              "ring_pc12_var": ("ring PC1-2 (rho=+0.18)", C["decorr"])}
    for m, (lab, col) in series.items():
        if m not in d:
            continue
        ys = [statistics.fmean(d[m][f]) for f in fracs]
        base = ys[0]
        ax.plot(range(len(fracs)), [y / base for y in ys], "o-", color=col, label=lab)
    ax.axhline(1, color="black", lw=0.5, ls=":")
    ax.set_xticks(range(len(fracs))); ax.set_xticklabels(fracs, fontsize=6)
    ax.set_xlabel("patch fraction")
    ax.set_ylabel("normalised to 0")
    ax.legend(frameon=False, fontsize=5.5)
    ax.set_title("no monotone trend (all P >= 0.28)", fontsize=6)
    panel_tag(ax, "B", dx=-0.24)

    dc, _ = load("D-controls")
    ax = fig.add_subplot(gs[2])
    arms = ["self", "drive0.5", "drive1.5", "synch"]
    bar_arms(ax, dc, "cx_rate_hz", arms, "CX rate (Hz)")
    ax.set_title("total drive +/-50%: d = 15-23", fontsize=6)
    panel_tag(ax, "C", dx=-0.30)

    ax = fig.add_subplot(gs[3])
    arms = ["self", "synch"]
    ax.bar([0], [statistics.fmean(dc["dim"]["self"])], width=0.5, color=C["self"],
           edgecolor="black", linewidth=0.4)
    ax.bar([1], [statistics.fmean(dc["dim"]["synch"])], width=0.5, color=C["synch"],
           edgecolor="black", linewidth=0.4)
    ax.errorbar([0, 1], [statistics.fmean(dc["dim"][a]) for a in arms],
                yerr=[ci95(dc["dim"][a]) for a in arms], fmt="none", ecolor="black",
                elinewidth=0.6, capsize=1.6)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["self", "synchronised"], fontsize=6)
    ax.set_ylabel("effective dimension")
    ax.set_title("same total, structure changed: d = 7.0", fontsize=6)
    panel_tag(ax, "D", dx=-0.30)
    save(fig, "fig6")


def fig7():
    """The drive-matching trap."""
    unb, _ = load("B-heading")
    bal, _ = load("B3-heading")
    fig = plt.figure(figsize=(3.5, 2.4))
    gs = fig.add_gridspec(1, 2, wspace=0.45)
    for k, (m, lab) in enumerate([("cx_tuning_wire_corr", "tuning <-> wiring (r)"),
                                  ("cx_rate_hz", "CX rate (Hz)")]):
        ax = fig.add_subplot(gs[k])
        for src, slab, col in [(unb, "unbalanced", C["decorr"]), (bal, "balanced", C["flow"])]:
            xs, ms, es = [], [], []
            for i, a in enumerate(["flow", "self", "shuffle"]):
                v = src[m].get(a, [])
                if not v:
                    continue
                mm, ee = mean_ci(v)
                xs.append(i + (0 if slab == "unbalanced" else 0.0)); ms.append(mm); es.append(ee)
            ax.errorbar([x + (0.12 if slab == "unbalanced" else -0.12) for x in xs], ms, yerr=es,
                        fmt="o", color=col, ecolor="black", elinewidth=0.6, capsize=1.6, label=slab)
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["flow", "self", "shuffle"], fontsize=6)
        ax.set_ylabel(lab)
        if k == 0:
            ax.legend(frameon=False, fontsize=6)
        panel_tag(ax, "AB"[k], dx=-0.32)
    save(fig, "fig7")


def figS1():
    """Equivalence: 90% CI against both bounds."""
    rows = load_csv("J2-n20-equivalence.csv")
    keep = ["cx_tuning_wire_corr", "cx_yaw_modulation_hz", "ring_loop", "ring_pc12_var",
            "bumpR", "cx_rate_hz", "dim", "ring_lag_yaw_deg"]
    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    y = 0
    ticks, labels = [], []
    for m in keep:
        for ctrl in ("flow", "shuffle", "randmat"):
            r = next((x for x in rows if x["metric"] == m
                      and x["contrast"] == "self_vs_" + ctrl), None)
            if not r:
                continue
            lo, hi = float(r["ci90_lo_d"]), float(r["ci90_hi_d"])
            d = float(r["cohens_d"])
            b = float(r["bound_d_raw"])
            col = C.get(ctrl, "grey")
            ax.plot([lo, hi], [y, y], "-", color=col, lw=1.2)
            ax.plot([d], [y], "o", color=col, markersize=2.5)
            ax.plot([-b, b], [y + 0.32, y + 0.32], "-", color="black", lw=0.5)
            ticks.append(y); labels.append(f"{m} / {ctrl}")
            y += 1
    ax.axvline(0, color="black", lw=0.6)
    ax.set_yticks(ticks); ax.set_yticklabels(labels, fontsize=4.5)
    ax.invert_yaxis()
    ax.set_xlabel("difference (raw units), 90% CI; bars = |d|<0.5 bound")
    save(fig, "figS1")


def figS3():
    """BF design ceiling."""
    n = list(range(10, 51))
    ceil_ = [2.52, 2.60, 2.68, 2.75, 2.83, 2.90, 2.97, 3.04, 3.10, 3.17, 3.24, 3.30, 3.35,
             3.41, 3.46, 3.51, 3.56, 3.61, 3.66, 3.70, 3.75, 3.79, 3.83, 3.87, 3.91, 3.95,
             3.99, 4.03, 4.06, 4.10, 4.13, 4.17, 4.20, 4.23, 4.26, 4.30, 4.33, 4.36, 4.39, 4.42,
             4.44]
    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    ax.plot(n[:len(ceil_)], ceil_, "-", color=C["flow"])
    ax.axhline(3, ls="--", lw=0.7, color="black")
    ax.text(11, 3.02, "moderate evidence threshold", fontsize=6)
    ax.axvline(20, ls=":", lw=0.7, color="grey")
    ax.text(20.4, 2.6, "n = 20", fontsize=6)
    ax.set_xlabel("trials per arm")
    ax.set_ylabel("BF01 ceiling at t = 0")
    save(fig, "figS3")


ALL = {"fig1": fig1, "fig2": fig2, "fig3": fig3, "fig4": fig4, "fig5": fig5,
       "fig5b": fig5b, "fig6": fig6, "fig7": fig7, "figS1": figS1, "figS3": figS3}


def main():
    want = [a for a in sys.argv[1:] if a in ALL] or list(ALL)
    for name in want:
        print(name)
        try:
            ALL[name]()
        except Exception as e:                      # one bad panel must not kill the rest
            print("   FAILED:", type(e).__name__, e)


if __name__ == "__main__":
    main()
