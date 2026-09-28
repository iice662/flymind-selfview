"""Anatomical figure: the 12,000-neuron slice in MaleCNS coordinates (supp5).

Reads only results/raw/slice-census.csv (produced by tools/dump_slice.py from the blob and the
released annotation table).  Usage: python tools/make_anatomy_figure.py
"""
import csv
import collections
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_figures as MF  # colours + save()

C = MF.C
S = os.path.join(ROOT, "results", "raw", "slice-census.csv")


def load():
    with open(S, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f)]


def main():
    rows = load()
    fig = plt.figure(figsize=(7.0, 2.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.25, 0.9], wspace=0.42)
    px = [(float(r["x"]), float(r["y"]), float(r["z"])) for r in rows]

    for k, (i, j, ax_lab, ylab, xlab) in enumerate(
            [(0, 1, "A", "y (um)", "x (um)"), (0, 2, "B", "z (um)", "x (um)")]):
        ax = fig.add_subplot(gs[k])
        ax.plot([p[i] for p in px], [p[j] for p in px], ".", color="#CCCCCC",
                markersize=0.6, zorder=1)
        for key, col, size, z in (("is_relay", C["flow"], 1.2, 2), ("is_lptc", C["self"], 1.6, 3),
                                  ("in_body_patch", "#D62728", 2.4, 4)):
            sel = [p for r, p in zip(rows, px) if r[key] == "1"]
            if sel:
                ax.plot([p[i] for p in sel], [p[j] for p in sel], ".", color=col,
                        markersize=size, zorder=z,
                        label={"is_relay": "CX relay (1,095)", "is_lptc": "LPTC pool (1,594)",
                               "in_body_patch": "body patch (672)"}[key])
        ring = [p for r, p in zip(rows, px) if r["cx_family"] == "1"]
        ax.plot([p[i] for p in ring], [p[j] for p in ring], "o", mfc="none", mec="#7B3294",
                markersize=4, mew=0.5, zorder=5, label="ring EPG/PEG (68)")
        ax.set_xlabel(xlab, fontsize=6)
        ax.set_ylabel(ylab, fontsize=6)
        ax.tick_params(labelsize=5)
        MF.panel_tag(ax, ax_lab, dx=-0.30)
        if k == 0:
            ax.legend(frameon=False, fontsize=4.5, loc="upper right", handletextpad=0.2,
                      borderpad=0.2, labelspacing=0.25)

    ax = fig.add_subplot(gs[2])
    pool = [r for r in rows if r["in_pool"] == "1"]
    patch = [r for r in rows if r["in_body_patch"] == "1"]
    for lab, sel, col in (("pool", pool, C["flow"]), ("body patch", patch, "#D62728")):
        c = collections.Counter((r["cell_type"] or "(unnamed)") for r in sel)
        top = c.most_common(6)
        ys = [i + (0.0 if lab == "pool" else 0.42) for i in range(len(top))]
        ax.barh(ys, [v for _, v in top], height=0.38, color=col, edgecolor="black", lw=0.3,
                label=f"{lab} (n = {len(sel)})")
    types = collections.Counter((r["cell_type"] or "(unnamed)") for r in pool).most_common(6)
    ax.set_yticks([i + 0.21 for i in range(len(types))])
    ax.set_yticklabels([t for t, _ in types], fontsize=5)
    ax.invert_yaxis()
    ax.set_xlabel("cells", fontsize=6)
    ax.legend(frameon=False, fontsize=4.5)
    MF.panel_tag(ax, "C", dx=-0.34)
    MF.save(fig, "supp5")
    print("cells with a soma:", sum(1 for p in px if p != (0.0, 0.0, 0.0)),
          "pool", len(pool), "patch", len(patch))


if __name__ == "__main__":
    main()
