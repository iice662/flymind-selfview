"""Extract a real FlyWire circuit subset and export it for the Terraria mod.

Why a subset: the full model is 138,639 neurons / ~15 M synapses (Shiu et al. 2024)
and the paper runs it in Brian2 for seconds of biological time per trial.  Terraria
gives us 16 ms per frame, so we export the chemosensory -> mushroom body -> dopamine
-> descending/motor part of the graph and run *that* at 60 Hz.  Everything about the
dynamics stays identical to model.py; only the neuron set is reduced.

Selection is synapse-budgeted importance BFS from real annotated seed neurons, so
the retained circuit is the part of the connectome that is actually wired into the
food/reward pathway rather than an arbitrary slice.

Inputs
    drosophila-brain-model/Connectivity_783.parquet   (FlyWire 783 edge list)
    drosophila-brain-model/Completeness_783.csv       (model neuron order)
    flywire-annotations/.../Supplemental_file1_neuron_annotations.tsv

Output
    flymind.brain (+ flymind.brain.report.json)  <- loaded by the C# mod

Usage
    python build_circuit.py --stats
    python build_circuit.py --max-neurons 4000 --expand 4
    python build_circuit.py --selftest          # extra: run the LIF model in Python
"""
from __future__ import annotations

import argparse
import array
import csv
import json
import math
import os
import re
import struct
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parquet_lite  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, ".."))
CONNECTIVITY = os.path.join(DATA, "drosophila-brain-model", "Connectivity_783.parquet")
COMPLETENESS = os.path.join(DATA, "drosophila-brain-model", "Completeness_783.csv")
ANNOTATIONS = os.path.join(DATA, "flywire-annotations",
                           "Supplemental_file1_neuron_annotations.tsv")
OUT_BLOB = os.path.join(DATA, "flymind.brain")
OUT_REPORT = os.path.join(DATA, "flymind.brain.report.json")

# ---------------------------------------------------------------------------
# model constants - verbatim from Shiu et al. 2024 model.py
# ---------------------------------------------------------------------------
LIF = dict(
    v_0=-52.0, v_rst=-52.0, v_th=-45.0,     # mV
    t_mbr=20.0, tau=5.0, t_rfc=2.2, t_dly=1.8,  # ms
    w_syn=0.275,                             # mV per synapse (the model's only free parameter)
    r_poi=150.0,                             # Hz, Poisson drive used for stimulated neurons
    f_poi=250.0,                             # weight scale factor for Poisson synapses
)

POP_UNKNOWN, POP_SENSORY, POP_ANTENNAL_LOBE, POP_MUSHROOM, POP_DAN = 0, 1, 2, 3, 4
POP_MBON, POP_DESCENDING, POP_MOTOR, POP_INTERNEURON, POP_OPTIC = 5, 6, 7, 8, 9
POP_NAMES = {
    POP_UNKNOWN: "unknown", POP_SENSORY: "sensory", POP_ANTENNAL_LOBE: "antennal_lobe",
    POP_MUSHROOM: "kenyon_cell", POP_DAN: "dopamine", POP_MBON: "mbon",
    POP_DESCENDING: "descending", POP_MOTOR: "motor", POP_INTERNEURON: "interneuron",
    POP_OPTIC: "optic",
}
N_POP = 10

# label -> population (checked in order, against joined annotation columns)
POP_PATTERNS = [
    (POP_DAN, r"^PAM|^PPL|^PAL\d|dopamin|\bDAN\b"),
    (POP_MBON, r"MBON"),
    (POP_MUSHROOM, r"Kenyon|KC[gab]"),
    (POP_MOTOR, r"proboscis_motor|ingestion_motor|brain_motor|crop_motor|pharyngeal"),
    (POP_DESCENDING, r"\bDN[a-z]?\d|\bDNge|\bDNpe|\bDNg|descending"),
    (POP_ANTENNAL_LOBE, r"ALPN|ALLN|LHLN|adPN|vPN|smPN|lvPN|PN\b|uniglomerular|antennal"),
    (POP_SENSORY, r"\bORN|sensory|receptor|ocellar|GRN"),
    (POP_OPTIC, r"^ME|^LO|^LOP|^LA|optic|lamina|medulla|lobula|L1-5|T4|T5"),
]

# Seed groups.  NOTE: the FlyWire FAFB dataset covers the brain only - the
# gustatory receptor neurons that sense sugar sit in the subesophageal zone and
# pharynx and are *not* part of it, so the sugar input is injected at the
# dopaminergic PAM cluster (the first sugar-reward stage that does exist here).
SEED_PATTERNS = {
    "odor": r"\badPN\b|\bvPN\b|\bsmPN\b|\blvPN\b|\bALPN\b|\bORN\b",  # antennal lobe PNs
    "sugar": r"\bPAM\d*",     # sugar-reward dopaminergic cluster (PAM)
    "bitter": r"\bPPL\d*|\bPAL\d*",  # aversive / punishment dopaminergic clusters
}
LANDMARKS = {
    "projection_neurons": r"\badPN\b|\bvPN\b|\bsmPN\b|\blvPN\b|\bALPN\b",
    "kenyon_cells": r"Kenyon|KC[gab]",
    "pam_dan": r"\bPAM\d*",
    "ppl_dan": r"\bPPL\d*",
    "pal_dan": r"\bPAL\d*",
    "mbon": r"MBON",
    "descending": r"\bDN[a-z]?\d|\bDNge|\bDNpe|\bDNg",
    "motor_ingestion": r"ingestion_motor",
    "motor_proboscis": r"proboscis_motor",
}

LZ4_CODEC_BYTES = 2.9  # informational only


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def load_completeness(path=COMPLETENESS):
    ids = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if row:
                ids.append(int(row[0]))
    return ids, {v: i for i, v in enumerate(ids)}


def load_annotations(id2i, path=ANNOTATIONS):
    out = {}
    total = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            total += 1
            try:
                rid = int(row["root_id"])
            except (KeyError, ValueError):
                continue
            if rid in id2i:
                out[rid] = row
    return out, total


LABEL_KEYS = ("cell_class", "cell_sub_class", "supertype", "cell_type",
              "hemibrain_type", "nerve", "super_class")


def label_of(row):
    return " | ".join((row.get(k) or "").strip() for k in LABEL_KEYS)


def match_any(label, pattern):
    return re.search(pattern, label, re.I) is not None


def classify(row):
    label = label_of(row)
    for pop, pat in POP_PATTERNS:
        if match_any(label, pat):
            return pop
    sc = row.get("super_class") or ""
    if sc in ("optic", "visual_projection", "visual_centrifugal"):
        return POP_OPTIC
    return {"sensory": POP_SENSORY, "descending": POP_DESCENDING,
            "motor": POP_MOTOR, "central": POP_INTERNEURON}.get(sc, POP_UNKNOWN)


def load_connectivity(path, batch=4_000_000):
    """Stream the edge list into compact typed arrays (12 bytes per edge)."""
    pre = array.array("i")
    post = array.array("i")
    wts = array.array("f")
    t0 = time.time()
    for chunk in parquet_lite.read_parquet(
            path, columns=["Presynaptic_Index", "Postsynaptic_Index",
                           "Excitatory x Connectivity"], batch_rows=batch):
        a_l = chunk["Presynaptic_Index"]
        b_l = chunk["Postsynaptic_Index"]
        w_l = chunk["Excitatory x Connectivity"]
        pre.extend(a_l)
        post.extend(b_l)
        wts.extend(w_l)
        print("    %d edges (%.0fs)" % (len(pre), time.time() - t0), end="\r")
    print()
    return pre, post, wts


def build_csr(pre, post, wts, n_neurons):
    """Build outgoing and incoming CSR adjacency (array based, low memory)."""
    t0 = time.time()
    out_deg = array.array("i", bytes(4 * (n_neurons + 1)))
    in_deg = array.array("i", bytes(4 * (n_neurons + 1)))
    for a in pre:
        out_deg[a + 1] += 1
    for b in post:
        in_deg[b + 1] += 1
    for i in range(n_neurons):
        out_deg[i + 1] += out_deg[i]
        in_deg[i + 1] += in_deg[i]
    out_start = array.array("i", out_deg)
    in_start = array.array("i", in_deg)
    out_nb = array.array("i", bytes(4 * len(pre)))
    out_w = array.array("f", bytes(4 * len(pre)))
    in_nb = array.array("i", bytes(4 * len(pre)))
    in_w = array.array("f", bytes(4 * len(pre)))
    cursor_o = array.array("i", out_start)
    cursor_i = array.array("i", in_start)
    for k in range(len(pre)):
        a = pre[k]
        b = post[k]
        ww = wts[k]
        p = cursor_o[a]
        out_nb[p] = b
        out_w[p] = ww
        cursor_o[a] = p + 1
        q = cursor_i[b]
        in_nb[q] = a
        in_w[q] = ww
        cursor_i[b] = q + 1
    print("    CSR built in %.0fs (%d edges)" % (time.time() - t0, len(pre)))
    return dict(out_start=out_start, out_nb=out_nb, out_w=out_w,
                in_start=in_start, in_nb=in_nb, in_w=in_w)


# ---------------------------------------------------------------------------
# synapse-budgeted importance BFS
# ---------------------------------------------------------------------------
def extract_subgraph(csr, seeds, max_neurons=4000, rounds=4, log=print, batch=400_000):
    """Grow a connected, weighted-importance subgraph around the seed neurons.

    Round 0 takes the seeds.  Each further round scores every unselected neuron by
    the total |weight| of its synapses onto the selected set (both directions) and
    takes the strongest candidates until the neuron budget is used up.  This keeps
    the part of the connectome that is actually wired into the seed pathway rather
    than an arbitrary topological neighbourhood.
    """
    out_start, out_nb, out_w = csr["out_start"], csr["out_nb"], csr["out_w"]
    in_start, in_nb, in_w = csr["in_start"], csr["in_nb"], csr["in_w"]

    sel = set(seeds)
    order = list(seeds)
    log("    round 0: %d seed neurons" % len(sel))

    for rnd in range(1, rounds + 1):
        room = max_neurons - len(sel)
        if room <= 0:
            break
        frontier = list(sel)
        picked = []
        batch_count = 0
        # walk the frontier in batches so peak memory stays bounded
        for i in range(0, len(frontier), batch):
            part = frontier[i:i + batch]
            score = {}
            for node in part:
                for k in range(out_start[node], out_start[node + 1]):
                    t = out_nb[k]
                    if t in sel:
                        continue
                    aw = out_w[k]
                    score[t] = score.get(t, 0.0) + (aw if aw >= 0 else -aw)
                for k in range(in_start[node], in_start[node + 1]):
                    t = in_nb[k]
                    if t in sel:
                        continue
                    aw = in_w[k]
                    score[t] = score.get(t, 0.0) + (aw if aw >= 0 else -aw)
            if not score:
                continue
            ranked = sorted(score.items(), key=lambda kv: -kv[1])
            for cand, _ in ranked:
                if len(picked) >= room:
                    break
                if cand in sel:
                    continue
                sel.add(cand)
                picked.append(cand)
            batch_count += len(score)
            if len(picked) >= room:
                break
        order.extend(picked)
        log("    round %d: +%d -> %d neurons (%d candidates scored)"
            % (rnd, len(picked), len(sel), batch_count))
        if not picked:
            break
    return order, sel


def lif_selftest(n, offsets, targets, weights, seeds, steps=600, dt=0.1, log=print):
    """Same LIF equations as model.py, in pure Python, to sanity-check the export."""
    import random
    p = LIF
    v = [p["v_0"]] * n
    g = [0.0] * n
    rfc = [0.0] * n
    spikes = [0] * n
    seed_set = set(seeds)
    exp_g = math.exp(-dt / p["tau"])
    delay_steps = max(1, int(round(p["t_dly"] / dt)))
    p_poi = p["r_poi"] * dt / 1000.0
    rng = random.Random(12345)
    pending = [[] for _ in range(delay_steps)]

    for step in range(steps):
        for s in seed_set:
            if rng.random() < p_poi:
                g[s] += p["w_syn"] * p["f_poi"]
        for (b, ww) in pending[step % delay_steps]:
            g[b] += ww
        pending[step % delay_steps] = []
        fired = []
        for i in range(n):
            if rfc[i] > 0.0:
                rfc[i] -= dt
                g[i] *= exp_g
                continue
            v[i] += dt * ((p["v_0"] - v[i]) + g[i]) / p["t_mbr"]
            g[i] *= exp_g
            if v[i] > p["v_th"]:
                v[i] = p["v_rst"]
                g[i] = 0.0
                rfc[i] = p["t_rfc"]
                spikes[i] += 1
                fired.append(i)
        slot = pending[(step + delay_steps) % delay_steps]
        for i in fired:
            for k in range(offsets[i], offsets[i + 1]):
                slot.append((targets[k], weights[k]))
    return spikes


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------
def write_blob(path, ids, pop, soma_xyz, offsets, targets, weights, kc_mbon_mask,
               sugar, bitter, odor, meta):
    n, nsyn = len(ids), len(targets)
    assert len(weights) == nsyn and len(kc_mbon_mask) == nsyn and len(soma_xyz) == n * 3
    with open(path, "wb") as f:
        f.write(b"FLYMIND1")
        f.write(struct.pack("<III", n, nsyn, len(meta.get("groups", {}))))
        pops = [0] * N_POP
        for pp in pop:
            pops[pp] += 1
        f.write(struct.pack("<%dI" % N_POP, *pops))
        f.write(struct.pack("<3I", len(sugar), len(bitter), len(odor)))
        rec = bytearray()
        for i in range(n):
            rec += struct.pack("<Qfff", ids[i], soma_xyz[i * 3], soma_xyz[i * 3 + 1],
                               soma_xyz[i * 3 + 2])
            rec += bytes((pop[i], 0, 0, 0))
        f.write(rec)
        f.write(array.array("I", offsets).tobytes())
        f.write(array.array("I", targets).tobytes())
        f.write(array.array("f", weights).tobytes())
        f.write(bytes(kc_mbon_mask))
        f.write(array.array("f", weights).tobytes())     # base weights (plasticity reference)
        for lst in (sugar, bitter, odor):
            f.write(array.array("I", lst).tobytes())
        js = json.dumps(meta, ensure_ascii=False).encode("utf-8")
        f.write(struct.pack("<I", len(js)))
        f.write(js)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--max-neurons", type=int, default=4000)
    ap.add_argument("--expand", type=int, default=4)
    ap.add_argument("--out", default=OUT_BLOB)
    args = ap.parse_args()

    t0 = time.time()
    print("== completeness ==")
    ids, id2i = load_completeness()
    print("    %d neurons in the model index" % len(ids))

    print("== annotations ==")
    ann, total = load_annotations(id2i)
    print("    %d annotation rows, %d join to the model" % (total, len(ann)))

    pop = [POP_UNKNOWN] * len(ids)
    labels = {}
    for rid, row in ann.items():
        i = id2i[rid]
        pop[i] = classify(row)
        labels[i] = label_of(row)
    print("    populations:", dict(Counter(POP_NAMES[p] for p in pop)))

    groups = {name: sum(1 for lab in labels.values() if match_any(lab, pat))
              for name, pat in LANDMARKS.items()}
    print("    landmarks:", groups)

    seeds = {name: [id2i[rid] for rid, row in ann.items()
                    if match_any(label_of(row), pat)]
             for name, pat in SEED_PATTERNS.items()}
    print("    seeds:", {k: len(v) for k, v in seeds.items()})

    if args.stats:
        return

    print("== connectivity (%s) ==" % os.path.basename(CONNECTIVITY))
    pre, post, w = load_connectivity(CONNECTIVITY)
    print("    %d edges" % len(pre))
    csr = build_csr(pre, post, w, len(ids))

    seed_all = sorted(set(seeds["odor"]) | set(seeds["sugar"]) | set(seeds["bitter"]))
    print("== extraction (budget %d neurons, %d rounds) ==" % (args.max_neurons, args.expand))
    selected, sel = extract_subgraph(csr, seed_all,
                                     max_neurons=args.max_neurons, rounds=args.expand)
    reindex = {old: new for new, old in enumerate(selected)}

    edges = [(reindex[a], reindex[b], ww)
             for a, b, ww in zip(pre, post, w) if a in sel and b in sel]
    print("    %d neurons, %d synapses" % (len(selected), len(edges)))

    deg = [0] * len(selected)
    for a, b, ww in edges:
        deg[a] += 1
    offsets = [0] * (len(selected) + 1)
    for i in range(len(selected)):
        offsets[i + 1] = offsets[i] + deg[i]
    cursor = offsets[:]
    targets = [0] * len(edges)
    weights = [0.0] * len(edges)
    for a, b, ww in edges:
        k = cursor[a]
        targets[k] = b
        weights[k] = ww * LIF["w_syn"]
        cursor[a] = k + 1

    soma = []
    for old in selected:
        row = ann.get(ids[old], {})

        def fl(key):
            try:
                return float(row.get(key) or 0.0)
            except ValueError:
                return 0.0
        soma.extend([fl("soma_x") / 1000.0, fl("soma_y") / 1000.0, fl("soma_z") / 1000.0])

    out_ids = [ids[o] for o in selected]
    out_pop = [pop[o] for o in selected]
    out_sugar = [reindex[i] for i in seeds["sugar"] if i in sel]
    out_bitter = [reindex[i] for i in seeds["bitter"] if i in sel]
    out_odor = [reindex[i] for i in seeds["odor"] if i in sel]

    kc_mbon_mask = bytearray(len(edges))
    for k, (a, b, ww) in enumerate(edges):
        if out_pop[a] == POP_MUSHROOM and out_pop[b] == POP_MBON:
            kc_mbon_mask[k] = 1

    stats = {}
    if args.selftest:
        print("== python LIF self test ==")
        spk = lif_selftest(len(selected), offsets, targets, weights, out_odor, steps=600)
        by_pop = Counter()
        for i, s in enumerate(spk):
            if s:
                by_pop[POP_NAMES[out_pop[i]]] += s
        stats = {"selftest_spikes_by_population": dict(by_pop),
                 "selftest_active_neurons": sum(1 for s in spk if s)}
        print("    spiking populations:", dict(by_pop))

    meta = dict(
        source="FlyWire FAFB v783 (Dorkenwald et al. 2024) + annotations "
               "(Schlegel et al. 2024 / Berg et al. 2025)",
        model="Shiu et al. 2024 leaky integrate-and-fire, w_syn=%.3f mV" % LIF["w_syn"],
        lif=LIF, pop_names=POP_NAMES, groups=groups,
        counts=dict(Counter(POP_NAMES[p] for p in out_pop)),
        n_neurons=len(selected), n_edges=len(edges),
        n_plastic_synapses=sum(kc_mbon_mask),
        seeds=dict(sugar=len(out_sugar), bitter=len(out_bitter), odor=len(out_odor)),
        note="FlyWire covers the brain only; sugar-sensing GRNs live in the SEZ/pharynx "
             "and are not part of this dataset, so the sugar input is injected at the "
             "PAM dopaminergic cluster.",
        built=time.strftime("%Y-%m-%d %H:%M:%S"), **stats)
    write_blob(args.out, out_ids, out_pop, soma, offsets, targets, weights,
               kc_mbon_mask, out_sugar, out_bitter, out_odor, meta)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("== wrote %s (%.2f MB) ==" % (args.out, os.path.getsize(args.out) / 1e6))
    print("    elapsed %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
