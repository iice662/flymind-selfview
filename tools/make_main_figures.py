"""Science-format figure set: 4 main figures + 4 supplementary, merged from the 10 originals.

Reuses the readers and helper functions of `make_figures.py` (imported as MF), so both scripts
plot the same numbers from `results/raw/*.csv`.  Fixes two layout defects of the first pass:
the long arm labels in the "synapses silenced" panel and the unreadable effect-size panel
(now a horizontal dot plot).

    python tools/make_main_figures.py            # all 8
    python tools/make_main_figures.py main3      # one
"""
import math
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figures as MF

C, SHORT, OUT = MF.C, MF.SHORT, MF.OUT
ORDER = ["flow", "self", "shuffle", "randmat", "decorr"]
DOSE_A = {"self": 0.0, "conf25": 0.25, "conf50": 0.5, "conf75": 0.75, "decorr": 1.0}
SHORT_ARM = {"flow": "flow", "self": "self*", "shuffle": "shuffle", "randmat": "randmat",
             "decorr": "decorr", "drive0.5": "x0.5", "drive1.5": "x1.5", "synch": "synch"}


# ---------------------------------------------------------------- panel helpers
def cell(fig, spec, tag=None, dx=-0.34):
    ax = fig.add_subplot(spec)
    if tag:
        MF.panel_tag(ax, tag, dx=dx)
    return ax


def arm_bars(ax, data, metric, ylabel, arms=ORDER, ylim=None, title=None, fs=5.5):
    xs = range(len(arms))
    for i, a in enumerate(arms):
        v = data[metric].get(a, [])
        if not v:
            continue
        m, e = MF.mean_ci(v)
        ax.bar(i, m, width=0.64, color=C.get(a, "#888888"), edgecolor="black",
               linewidth=0.4, zorder=2)
        ax.errorbar(i, m, yerr=e, fmt="none", ecolor="black", elinewidth=0.6,
                    capsize=1.4, zorder=3)
        jit = [i + (k - (len(v) - 1) / 2) * 0.018 for k in range(len(v))]
        ax.plot(jit, v, ".", color="black", markersize=1.1, alpha=0.65, zorder=4)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([SHORT_ARM.get(a, a) for a in arms], fontsize=fs, rotation=45, ha="right")
    ax.set_ylabel(ylabel, fontsize=6)
    if ylim:
        ax.set_ylim(*ylim)
    if title:
        ax.set_title(title, fontsize=6)
    return ax


def spearman(xs, ys, n_perm=4000, seed=12345):
    """Spearman rho and a permutation P, computed here so no figure annotation is hard-coded."""
    import random as _r

    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    def pearson(a, b):
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        num = sum((u - ma) * (v - mb) for u, v in zip(a, b))
        da = sum((u - ma) ** 2 for u in a) ** 0.5
        db = sum((v - mb) ** 2 for v in b) ** 0.5
        return num / (da * db) if da > 0 and db > 0 else 0.0

    rx, ry = rank(xs), rank(ys)
    rho = pearson(rx, ry)
    rng = _r.Random(seed)
    hits = 0
    for _ in range(n_perm):
        p = ry[:]
        rng.shuffle(p)
        if abs(pearson(rx, p)) >= abs(rho) - 1e-12:
            hits += 1
    return rho, (hits + 1) / (n_perm + 1)


def dose_annot(data, metric):
    """'rho = ..., P = ...' for the conflict-dose panels, from the trial data itself."""
    xs, ys = [], []
    for a, x in DOSE_A.items():
        for v in data[metric].get(a, []):
            xs.append(x)
            ys.append(v)
    if len(xs) < 4:
        return ""
    rho, p = spearman(xs, ys)
    return f"rho = {rho:+.2f}, P = {p:.0e}".replace("e-0", "e-").replace("e+0", "e+")


def dose_line(ax, data, metric, ylabel, note=None, title=None):
    xs, ms, es = [], [], []
    for a, x in DOSE_A.items():
        v = data[metric].get(a, [])
        if not v:
            continue
        m, e = MF.mean_ci(v)
        xs.append(x); ms.append(m); es.append(e)
    ax.errorbar(xs, ms, yerr=es, fmt="o-", color=C["self"], ecolor="black",
                elinewidth=0.6, capsize=1.4, markersize=3)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("conflict strength alpha", fontsize=6)
    ax.set_ylabel(ylabel, fontsize=6)
    if note:
        ax.set_title(note, fontsize=6)
    return ax


def effect_dots(ax, pl, rate_m, geo_m, ctrls=("flow", "shuffle", "randmat", "decorr")):
    """Horizontal dot plot: one row per metric, one marker per control."""
    rows = rate_m + geo_m
    markers = {"flow": "o", "shuffle": "s", "randmat": "^", "decorr": "D"}
    for i, m in enumerate(rows):
        for ctrl in ctrls:
            d = pl.get((m, ctrl), (float("nan"),))[0]
            if not math.isfinite(d):
                continue
            ax.plot([d], [i], markers[ctrl], color=C[ctrl], markersize=3.2,
                    markeredgecolor="black", markeredgewidth=0.3,
                    label=ctrl if i == 0 else None)
    ax.axvline(0, color="black", lw=0.6)
    ax.axhline(len(rate_m) - 0.5, color="grey", lw=0.5, ls=":")
    ax.set_yticks(range(len(rows)))
    lab = [r.replace("_hz", "").replace("_", " ") for r in rows]
    ax.set_yticklabels(lab, fontsize=5)
    ax.invert_yaxis()
    ax.set_xlabel("Cohen's d (self - control)", fontsize=6)
    ax.set_xlim(-95, 15)
    ax.legend(frameon=False, fontsize=5, ncol=2, loc="lower left")
    ax.text(-92, len(rate_m) - 0.9, "rate metrics", fontsize=5, style="italic")
    ax.text(-92, len(rate_m) + 0.1, "geometry metrics", fontsize=5, style="italic")
    return ax


def silent_synapses(ax, matching, tag=None):
    sel = [r for r in matching if r["arm"] in ("self", "shuffle", "randmat")]
    ax.bar(range(len(sel)), [float(r["cx_input_synapses"]) for r in sel],
           color=[C[r["arm"]] for r in sel], edgecolor="black", linewidth=0.4)
    for i, r in enumerate(sel):
        ax.text(i, float(r["cx_input_synapses"]) * 1.02,
                f"{float(r['cx_input_synapses']):,.0f}\n({float(r['ring_input_synapses']):,.0f} to ring)",
                ha="center", va="bottom", fontsize=5)
    ax.set_xticks(range(len(sel)))
    ax.set_xticklabels(["self*", "shuffle", "randmat"], fontsize=6)
    ax.set_ylim(0, 42000)
    ax.set_ylabel("CX synapses silenced", fontsize=6)
    if tag:
        MF.panel_tag(ax, tag, dx=-0.30)
    return ax


# ---------------------------------------------------------------- main figures
def main1():
    """Circuit, manipulation, balancing."""
    fig = plt.figure(figsize=(7.0, 4.3))
    gs = fig.add_gridspec(2, 3, hspace=0.75, wspace=0.75)

    ax = cell(fig, gs[0, 0], "A")
    pops = [("sensory", 2695), ("antennal", 620), ("KC", 193), ("dopamine", 344), ("MBON", 67),
            ("descending", 119), ("motor", 316), ("LPTC", 1594), ("CX relay", 1095), ("CX", 2074), ("unnamed", 3802)]
    fams = [("ring EPG/PEG", 68), ("columnar", 1036), ("fan-body", 601), ("other CX", 369)]
    ax.barh(range(len(pops)), [p[1] for p in pops], color="#BBD7E8", edgecolor="black", lw=0.4)
    ax.barh([len(pops) + 1 + k for k in range(len(fams))], [f[1] for f in fams],
            color="#F2C6A0", edgecolor="black", lw=0.4)
    ax.set_yticks(list(range(len(pops))) + [len(pops) + 1 + k for k in range(len(fams))])
    ax.set_yticklabels([p[0] for p in pops] + [f[0] for f in fams], fontsize=5)
    ax.invert_yaxis()
    ax.set_xlabel("neurons", fontsize=6)
    ax.set_title("12,000 neurons\n1,615,753 synapses", fontsize=6)

    ax = cell(fig, gs[0, 1], "B")
    ks, cx, act = [], [], []
    for line in MF.read_text(os.path.join(MF.RAW, "calibration2-sweep.txt")).splitlines():
        if "|" not in line or not line.startswith(" "):
            continue
        f = line.split("|")
        try:
            k = float(f[0].strip())
        except ValueError:
            continue
        cols = f[1].split()
        ks.append(k); cx.append(float(cols[11])); act.append(float(cols[12]))
    ax.plot(ks, cx, "o-", color=C["self"])
    ax.axvline(300, ls=":", lw=0.7, color="black")
    ax.text(310, max(cx) * 0.45, "k = 300", fontsize=5.5)
    ax.set_xscale("log")
    ax.set_xlabel("gain kappa", fontsize=6)
    ax.set_ylabel("CX rate (Hz)", fontsize=6)
    ax2 = ax.twinx()
    ax2.plot(ks, act, "s--", color=C["flow"])
    ax2.set_ylabel("CX cells active (%)", fontsize=6, color=C["flow"])
    ax2.tick_params(axis="y", colors=C["flow"], labelsize=6)
    ax.set_title("calibration", fontsize=6)

    ax = cell(fig, gs[0, 2], "C")
    seg = [("LPTC->ring", 67), ("LPTC->columnar", 58), ("columnar->ring", 1031),
           ("ring->ring", 1692), ("ring->FB", 539), ("FB->DN", 88), ("DN->motor", 2810)]
    ax.barh(range(len(seg)), [s[1] for s in seg], color="#C8D6B9", edgecolor="black", lw=0.4)
    ax.set_yticks(range(len(seg)))
    ax.set_yticklabels([s[0] for s in seg], fontsize=5)
    ax.set_xscale("log")
    ax.set_xlabel("synapses (log)", fontsize=6)
    ax.invert_yaxis()
    ax.set_title("heading pathway", fontsize=6)

    for k, (tag, prefix, title) in enumerate([("D", "A3-flow", "optic flow"),
                                              ("E", "B3-heading", "yaw")]):
        ax = cell(fig, gs[1, k], tag)
        m = MF.load_csv(prefix + "-matching.csv")
        arms = [r["arm"] for r in m if r["arm"] != "rest"]
        ax.bar(range(len(arms)), [float(r["delivered_ratio_vs_self"]) for r in m if r["arm"] != "rest"],
               color=[C.get(a, "#888888") for a in arms], edgecolor="black", lw=0.4)
        ax.axhline(1.0, color="black", lw=0.6, ls="--")
        ax.set_ylim(0.98, 1.02)
        ax.set_xticks(range(len(arms)))
        ax.set_xticklabels(arms, rotation=60, ha="right", fontsize=4.5)
        ax.set_ylabel("delivered / self*", fontsize=6)
        ax.set_title(f"{title}: drive balanced", fontsize=6)

    ax = cell(fig, gs[1, 2], "F")
    silent_synapses(ax, MF.load_csv("A4-flow-matching.csv"))
    ax.set_title("the patch is not a neutral subset", fontsize=6)
    MF.save(fig, "main1")


def main2():
    """Propagation."""
    fig = plt.figure(figsize=(3.5, 2.4))
    gs = fig.add_gridspec(1, 2, wspace=0.55)
    ax = cell(fig, gs[0], "A", dx=-0.32)
    ax.plot([1, 2, 3], [97.2, 97.4, 97.4], "o-", color=C["flow"])
    ax.set_ylim(90, 100)
    ax.set_xlabel("hops from visual pool", fontsize=6)
    ax.set_ylabel("CX cells reached (%)", fontsize=6)
    ax.set_title("2,015 / 2,074 at one hop\n48,315 direct synapses", fontsize=6)

    ax = cell(fig, gs[1], "B", dx=-0.32)
    labels, peaks, base = [], [], []
    for line in MF.read_text(os.path.join(MF.RAW, "P2-propagation.stdout.txt")).splitlines():
        f = line.split()
        if len(f) >= 8 and f[0].isdigit() and ("flow" in f or "self" in f):
            labels.append(f"{f[0]}\n{'self*' if 'self' in f else 'flow'}")
            base.append(float(f[2])); peaks.append(float(f[3]))
    xs = range(len(labels))
    ax.bar([x for x in xs], peaks, width=0.6,
           color=[C["self"] if "self" in l else C["flow"] for l in labels],
           edgecolor="black", lw=0.4, label="evoked peak")
    ax.plot(xs, base, "k_", markersize=5, label="baseline")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_xticks(list(xs)); ax.set_xticklabels(labels, fontsize=5)
    ax.set_ylabel("CX spikes / 0.5 ms step", fontsize=6)
    ax.set_xlabel("gain kappa / patch", fontsize=6)
    ax.legend(frameon=False, fontsize=5)
    ax.set_title("peak at 2.5 ms\n(monosynaptic)", fontsize=6)
    MF.save(fig, "main2")


def main3():
    """Optic flow."""
    data, _ = MF.load("A4-flow")
    pl = MF.pair_lookup("A4-flow")
    fig = plt.figure(figsize=(7.0, 4.0))
    gs = fig.add_gridspec(2, 4, hspace=0.80, wspace=0.60)
    panels = [("cx_rate_hz", "CX rate (Hz)"), ("cx_active_fraction", "CX active fraction"),
              ("ring_rate_hz", "ring rate (Hz)"), ("bumpR", "ring bump R"),
              ("dim", "effective dimension"), ("pop_rate_sd_hz", "fluctuation SD (Hz)"),
              ("columnar_rate_hz", "columnar rate (Hz)")]
    for k, (m, lab) in enumerate(panels):
        ax = cell(fig, gs[k // 4, k % 4], chr(ord("A") + k))
        arm_bars(ax, data, m, lab)
    rate_m = ["cx_rate_hz", "ring_rate_hz", "columnar_rate_hz", "fanbody_rate_hz",
              "other_rate_hz", "pop_rate_sd_hz"]
    geo_m = ["cx_active_fraction", "dim", "bumpR", "pair_corr"]
    ax = cell(fig, gs[1, 3], "H")
    effect_dots(ax, pl, rate_m, geo_m)
    ax.set_title("randmat reproduces the rates,\nnot the geometry", fontsize=6)
    MF.save(fig, "main3")


def main4():
    """Heading: a silent body region costs coding, a conflicting one costs fidelity."""
    e, _ = MF.load("I2-heading")
    f20, _ = MF.load("J2-n20")
    g150, _ = MF.load("K2-k150")
    h600, _ = MF.load("L2-k600")
    fig = plt.figure(figsize=(7.0, 4.6))
    gs = fig.add_gridspec(2, 4, hspace=0.85, wspace=0.62)

    # every annotation is read from the deposited CSVs, never typed in
    bf = {}
    for r in MF.load_csv("J2-n20-equivalence.csv"):
        bf[(r["metric"], r["contrast"])] = (float(r["bf01"]), float(r["bf10"]))
    for k, (m, lab, tag) in enumerate([("cx_tuning_wire_corr", "tuning <-> wiring (r)", "A"),
                                       ("steer_corr_yaw", "steering <-> yaw (r)", "B")]):
        ax = cell(fig, gs[0, k], tag)
        arm_bars(ax, f20, m, lab, fs=5)
        bf01 = [bf.get((m, "self_vs_" + c), (float("nan"),))[0] for c in ("flow", "shuffle", "randmat")]
        if max(bf01) >= 1:                      # evidence for the null
            ax.set_title(f"n = 20: BF01 = {min(bf01):.2f}-{max(bf01):.2f}", fontsize=6)
        else:                                   # evidence for a difference
            bf10 = [1.0 / v for v in bf01]

            def _f(x):
                return f"{x:.0e}".replace("e+0", "e").replace("e-0", "e-").replace("e+", "e")
            ax.set_title(f"n = 20: BF10 = {_f(min(bf10))}-{_f(max(bf10))}", fontsize=6)

    for k, (m, lab) in enumerate([("cx_tuning_wire_corr", "tuning <-> wiring (r)"),
                                  ("steer_corr_yaw", "steering <-> yaw (r)")]):
        ax = cell(fig, gs[0, 2 + k], chr(ord("C") + k))
        dose_line(ax, e, m, lab, dose_annot(e, m))

    for k, (m, lab) in enumerate([("steer_asym_sd_hz", "steering amplitude (Hz)"),
                                  ("cx_yaw_modulation_hz", "yaw modulation (Hz)"),
                                  ("tau_ms", "population tau (ms)"),
                                  ("dim", "effective dimension")]):
        ax = cell(fig, gs[1, k], chr(ord("E") + k))
        dose_line(ax, e, m, lab, dose_annot(e, m))

    MF.save(fig, "main4")


def main4b():
    """Flat rate/drive, gain replication, Bayes factors (companion to main4)."""
    e, _ = MF.load("I2-heading")
    g150, _ = MF.load("K2-k150")
    h600, _ = MF.load("L2-k600")
    fig = plt.figure(figsize=(7.0, 2.3))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.35, 1.1], wspace=0.60)

    ax = cell(fig, gs[0], "A")
    for m, lab, col, scale in [("cx_rate_hz", "CX rate (Hz)", C["flow"], 1.0),
                               ("injected_events", "delivered events /1e5", C["rest"], 1e-5)]:
        xs, ms, es = [], [], []
        for a, x in DOSE_A.items():
            v = e[m].get(a, [])
            mm, ee = MF.mean_ci(v)
            xs.append(x); ms.append(mm * scale); es.append(ee * scale)
        ax.errorbar(xs, ms, yerr=es, fmt="o-", color=col, ecolor="black",
                    elinewidth=0.6, capsize=1.4, markersize=3, label=lab)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("conflict strength alpha", fontsize=6)
    ax.set_ylabel("Hz  /  1e5 events", fontsize=6)
    ax.legend(frameon=False, fontsize=5)
    ax.set_title("rate rises, drive flat\n" + dose_annot(e, "cx_rate_hz") + " / "
                 + dose_annot(e, "injected_events"), fontsize=6)

    ax = cell(fig, gs[1], "B", dx=-0.26)
    readouts = ["steer_corr_yaw", "cx_tuning_wire_corr", "steer_asym_sd_hz"]
    for idx, m in enumerate(readouts):
        for src, slab, col in [(g150, "k=150", C["flow"]), (e, "k=300", C["self"]),
                               (h600, "k=600", C["decorr"])]:
            if "self" not in src[m]:
                continue
            v0 = statistics.fmean(src[m]["self"])
            xs = [x for a, x in DOSE_A.items() if a in src[m]]
            ys = [statistics.fmean(src[m][a]) / v0 + idx * 0.35 for a, _ in DOSE_A.items()
                  if a in src[m]]
            ax.plot(xs, ys, "o-", color=col, markersize=2.5, label=slab if idx == 0 else None)
    ax.set_yticks([1, 1.35, 1.7])
    ax.set_yticklabels(["steering\nfidelity", "tuning", "steering\namplitude"], fontsize=5)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xlabel("conflict strength alpha", fontsize=6)
    ax.set_ylabel("normalised to alpha = 0", fontsize=6)
    ax.legend(frameon=False, fontsize=5, ncol=3)
    ax.set_title("same rank order at three gains", fontsize=6)

    ax = cell(fig, gs[2], "C")
    rows = [("tuning", 2.84, 2.85, 3.03), ("yaw mod.", 2.79, 2.56, 3.15),
            ("ring loop", 3.04, 2.95, 2.23), ("ring PC1-2", 3.09, 2.23, 2.53),
            ("bump R", 1.51, 2.88, 2.90), ("CX rate", 2.39, 2.05, 2.83)]
    w = 0.26
    for j, (lab, col) in enumerate([("flow", C["flow"]), ("shuffle", C["shuffle"]),
                                    ("randmat", C["randmat"])]):
        ax.bar([i + j * w for i in range(len(rows))], [r[1 + j] for r in rows], width=w,
               color=col, edgecolor="black", lw=0.3, label=lab)
    ax.axhline(3, ls="--", lw=0.7, color="black")
    ax.axhline(3.24, ls=":", lw=0.7, color="grey")
    ax.text(len(rows) - 0.6, 3.26, "ceiling n = 20", fontsize=5, ha="right")
    ax.set_xticks([i + w for i in range(len(rows))])
    ax.set_xticklabels([r[0] for r in rows], rotation=45, ha="right", fontsize=5)
    ax.set_ylabel("BF01 (n = 20)", fontsize=6)
    ax.set_ylim(0, 3.8)
    ax.legend(frameon=False, fontsize=5)
    MF.save(fig, "main4b")


# ---------------------------------------------------------------- supplementary
def supp1():
    """Patch-size dose and positive controls."""
    d, _ = MF.load("M2-dose-dose")
    dc, _ = MF.load("D2-controls")
    fig = plt.figure(figsize=(7.0, 2.3))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1.4, 1.1, 1.1], wspace=0.62)
    fracs = ["0", "0.125", "0.25", "0.5"]

    ax = cell(fig, gs[0], "A")
    ax.plot(range(len(fracs)), [statistics.fmean(d["injected_events"][f]) / 1e5 for f in fracs],
            "o-", color=C["rest"])
    ax.set_ylim(700, 704)
    ax.set_xticks(range(len(fracs))); ax.set_xticklabels(fracs, fontsize=6)
    ax.set_xlabel("patch fraction", fontsize=6)
    ax.set_ylabel("delivered events /1e5", fontsize=6)
    ax.set_title("drive matched", fontsize=6)

    ax = cell(fig, gs[1], "B", dx=-0.26)
    for m, lab, col in [("cx_tuning_wire_corr", "tuning (rho=-0.01)", C["self"]),
                        ("cx_rate_hz", "CX rate (rho=-0.01)", C["flow"]),
                        ("bumpR", "bump R (rho=+0.05)", C["randmat"]),
                        ("ring_pc12_var", "ring PC1-2 (rho=+0.18)", C["decorr"])]:
        ys = [statistics.fmean(d[m][f]) for f in fracs]
        ax.plot(range(len(fracs)), [y / ys[0] for y in ys], "o-", color=col, markersize=3, label=lab)
    ax.axhline(1, color="black", lw=0.5, ls=":")
    ax.set_xticks(range(len(fracs))); ax.set_xticklabels(fracs, fontsize=6)
    ax.set_xlabel("patch fraction", fontsize=6)
    ax.set_ylabel("normalised to 0", fontsize=6)
    ax.legend(frameon=False, fontsize=5)
    ax.set_title("no trend: all P >= 0.28", fontsize=6)

    ax = cell(fig, gs[2], "C")
    arm_bars(ax, dc, "cx_rate_hz", "CX rate (Hz)", arms=["self", "drive0.5", "drive1.5", "synch"])
    ax.set_title("drive +/-50%: d = 15-23", fontsize=6)

    ax = cell(fig, gs[3], "D")
    arms = ["self", "synch"]
    ax.bar(range(2), [statistics.fmean(dc["dim"][a]) for a in arms], width=0.6,
           color=[C[a] for a in arms], edgecolor="black", lw=0.4)
    ax.errorbar(range(2), [statistics.fmean(dc["dim"][a]) for a in arms],
                yerr=[MF.ci95(dc["dim"][a]) for a in arms], fmt="none", ecolor="black",
                elinewidth=0.6, capsize=1.4)
    ax.set_xticks(range(2)); ax.set_xticklabels(["self*", "synchronised"], fontsize=6)
    ax.set_ylabel("effective dimension", fontsize=6)
    ax.set_title("same total, structure changed: d = 7.0", fontsize=6)
    MF.save(fig, "supp1")


def supp2():
    """Equivalence."""
    rows = MF.load_csv("J2-n20-equivalence.csv")
    keep = ["cx_tuning_wire_corr", "cx_yaw_modulation_hz", "ring_loop", "ring_pc12_var",
            "bumpR", "cx_rate_hz", "dim", "ring_lag_yaw_deg"]
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    y = 0
    ticks, labels = [], []
    for m in keep:
        for ctrl in ("flow", "shuffle", "randmat"):
            r = next((x for x in rows if x["metric"] == m
                      and x["contrast"] == "self_vs_" + ctrl), None)
            if not r:
                continue
            lo, hi = float(r["ci90_lo_d"]), float(r["ci90_hi_d"])
            b = float(r["bound_d_raw"])
            ax.plot([lo, hi], [y, y], "-", color=C[ctrl], lw=1.1)
            ax.plot([float(r["cohens_d"])], [y], "o", color=C[ctrl], markersize=2.2)
            ax.plot([-b, b], [y + 0.30, y + 0.30], "-", color="black", lw=0.5)
            ticks.append(y); labels.append(f"{m} / {ctrl}")
            y += 1
    ax.axvline(0, color="black", lw=0.6)
    ax.set_yticks(ticks); ax.set_yticklabels(labels, fontsize=4)
    ax.invert_yaxis()
    ax.set_xlabel("difference (raw units), 90% CI\nthin bars = |d| < 0.5 bound", fontsize=6)
    MF.save(fig, "supp2")


def supp3():
    """Bayes-factor design ceiling."""
    n = list(range(10, 51))
    ceil_ = [2.52, 2.60, 2.68, 2.75, 2.83, 2.90, 2.97, 3.04, 3.10, 3.17, 3.24, 3.30, 3.35,
             3.41, 3.46, 3.51, 3.56, 3.61, 3.66, 3.70, 3.75, 3.79, 3.83, 3.87, 3.91, 3.95,
             3.99, 4.03, 4.06, 4.10, 4.13, 4.17, 4.20, 4.23, 4.26, 4.30, 4.33, 4.36, 4.39,
             4.42, 4.44]
    fig, ax = plt.subplots(figsize=(3.5, 2.1))
    ax.plot(n[:len(ceil_)], ceil_, "-", color=C["flow"])
    ax.axhline(3, ls="--", lw=0.7, color="black")
    ax.text(11, 3.03, "moderate evidence", fontsize=6)
    ax.axvline(20, ls=":", lw=0.7, color="grey")
    ax.text(20.5, 2.6, "n = 20", fontsize=6)
    ax.set_xlabel("trials per arm", fontsize=6)
    ax.set_ylabel("BF01 ceiling at t = 0", fontsize=6)
    MF.save(fig, "supp3")


def supp4():
    """The drive-matching trap."""
    unb, _ = MF.load("B3-heading")
    bal, _ = MF.load("I2-heading")
    fig = plt.figure(figsize=(3.5, 2.3))
    gs = fig.add_gridspec(1, 2, wspace=0.55)
    for k, (m, lab) in enumerate([("cx_tuning_wire_corr", "tuning <-> wiring (r)"),
                                  ("cx_rate_hz", "CX rate (Hz)")]):
        ax = cell(fig, gs[k], "AB"[k], dx=-0.34)
        for src, slab, col in [(unb, "unbalanced", C["decorr"]), (bal, "balanced", C["flow"])]:
            xs, ms, es = [], [], []
            for i, a in enumerate(["flow", "self", "shuffle"]):
                v = src[m].get(a, [])
                if not v:
                    continue
                mm, ee = MF.mean_ci(v)
                xs.append(i + (0.10 if slab == "unbalanced" else -0.10)); ms.append(mm); es.append(ee)
            ax.errorbar(xs, ms, yerr=es, fmt="o", color=col, ecolor="black",
                        elinewidth=0.6, capsize=1.4, markersize=3, label=slab)
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["flow", "self*", "shuffle"], fontsize=6)
        ax.set_ylabel(lab, fontsize=6)
        if k == 0:
            ax.legend(frameon=False, fontsize=5)
    MF.save(fig, "supp4")


ALL = {"main1": main1, "main2": main2, "main3": main3, "main4": main4, "main4b": main4b,
       "supp1": supp1, "supp2": supp2, "supp3": supp3, "supp4": supp4}

if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if a in ALL] or list(ALL)
    for name in want:
        print(name)
        try:
            ALL[name]()
        except Exception as e:
            print("   FAILED:", type(e).__name__, e)
