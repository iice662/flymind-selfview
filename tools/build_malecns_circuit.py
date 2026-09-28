"""Extract a real sub-circuit from the MaleCNS v1.0 connectome for the Terraria mod.

The full MaleCNS table is 151,856,684 edges over ~166k neurons (~1 GB of Arrow IPC).
Nothing about that fits a 16 ms frame, so this builds the chemosensory ->
mushroom body -> dopamine -> descending/motor sub-circuit around annotated seed
neurons and exports just that (blob layout documented in Neural/BrainData.cs).

Two streaming passes over the source table, so no multi-GB intermediate is written:
    pass 1  grow the neuron set with a synapse budget, from the seed neurons
    pass 2  keep the edges whose endpoints are both selected, and write the blob

Dynamics constants are copied from Shiu et al. 2024 model.py.  The MaleCNS edges carry
connection strength but no sign; sign is only applied when a transmitter table is
available, otherwise every synapse is excitatory (see --sign).

Usage:
    python build_malecns_circuit.py --stats
    python build_malecns_circuit.py --max-neurons 3000 --rounds 3 --out ..\\flymind.brain
"""
from __future__ import annotations

import array
import csv
import json
import os
import re
import struct
import sys
import time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, ".."))
MCNS = os.path.join(DATA, "malecns")
CONNECTOME = os.path.join(MCNS, "connectome-weights.feather")
ANN = os.path.join(MCNS, "annotations.tsv")
OUT_BLOB = os.path.join(DATA, "flymind.brain")
OUT_REPORT = os.path.join(DATA, "flymind.brain.report.json")

sys.path.insert(0, HERE)
import feather_lite  # noqa: E402

# ---------------------------------------------------------------- model constants
LIF = dict(v_0=-52.0, v_rst=-52.0, v_th=-45.0, t_mbr=20.0, tau=5.0, t_rfc=2.2, t_dly=1.8,
           w_syn=0.275, r_poi=150.0, f_poi=250.0)

POP_UNKNOWN, POP_SENSORY, POP_ANTENNAL, POP_MUSHROOM, POP_DAN = 0, 1, 2, 3, 4
POP_MBON, POP_DESCENDING, POP_MOTOR, POP_INTERNEURON, POP_VNC = 5, 6, 7, 8, 9
POP_NAMES = {POP_UNKNOWN: "unknown", POP_SENSORY: "sensory", POP_ANTENNAL: "antennal_lobe",
             POP_MUSHROOM: "kenyon_cell", POP_DAN: "dopamine", POP_MBON: "mbon",
             POP_DESCENDING: "descending", POP_MOTOR: "motor",
             POP_INTERNEURON: "interneuron", POP_VNC: "vnc"}
N_POP = 10

# cell-type name (MaleCNS `type` column) -> population, checked in order
POP_PATTERNS = [
    (POP_DAN, r"^(PAM|PPL|PAL)\d"),
    (POP_MBON, r"^MBON"),
    (POP_MUSHROOM, r"^KC"),
    (POP_MOTOR, r"^MN|proboscis|CEM|^MNs|feeding"),
    (POP_DESCENDING, r"^DN"),
    (POP_ANTENNAL, r"adPN|vPN|smPN|lvPN|_PN|^ALPN|^PN\d|WEDPN|^M_l|^Z_l|^V_l"),
    (POP_SENSORY, r"GRN|^GR\d|sugar|sweet|tpGRN|ORN|sensill"),
    (POP_VNC, r"^VNC|^Tdc|^Leg|^Wing|^Haltere"),
]

# what the mod's food item stimulates; matched against `type` then `hemibrainType`
SEED_PATTERNS = {
    "sugar": r"GRN|^GR\d|sugar|sweet|tpGRN",
    "odor": r"^ORN|^OR\d|adPN|vPN|smPN|lvPN|WEDPN",
    "reward": r"^(PAM|PPL)\d",
    "motor": r"^MN|proboscis|CEM",
}
LANDMARKS = {
    "sugar_taste_grn": r"GRN|^GR\d|tpGRN",
    "odor_orn": r"^ORN|^OR\d",
    "antennal_pn": r"adPN|vPN|smPN|lvPN|WEDPN",
    "kenyon": r"^KC",
    "pam_dan": r"^PAM\d",
    "ppl_dan": r"^PPL\d",
    "mbon": r"^MBON",
    "descending": r"^DN",
    "motor": r"^MN|proboscis|CEM",
}


def load_annotations(path=ANN):
    """-> (ids, rows) for every annotated body, preserving file order."""
    csv.field_size_limit(1 << 24)
    ids, rows = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            try:
                ids.append(int(row["bodyId"]))
            except (KeyError, ValueError):
                continue
            rows.append(row)
    if not ids:
        raise SystemExit("%s is empty - run export_annotations.py first" % path)
    return ids, rows


def label_of(row):
    """The cell identity we classify on: the type name, falling back to hemibrain."""
    return "%s | %s" % ((row.get("type") or "").strip(), (row.get("hemibrainType") or "").strip())


def classify(label):
    for pop, pat in POP_PATTERNS:
        if re.search(pat, label, re.I):
            return pop
    return POP_UNKNOWN


def batches(path=CONNECTOME):
    return feather_lite.FeatherFile(path).iter_batches()


def grow(seed_ids, max_neurons, rounds, log=print):
    """Synapse-budgeted growth: each round adds the neurons with the most synapses
    onto the currently selected set.  Only counts are kept per candidate, so memory
    stays proportional to the frontier rather than to the 151M edges."""
    sel = set(seed_ids)
    order = list(seed_ids)
    log("    round 0: %d seeds" % len(sel))
    for rnd in range(1, rounds + 1):
        room = max_neurons - len(sel)
        if room <= 0:
            break
        score = defaultdict(float)
        t0 = time.time()
        for b in batches():
            pre = b["body_pre"]
            post = b["body_post"]
            wt = b["weight"]
            for i in range(len(pre)):
                a = pre[i]
                c = post[i]
                ain = a in sel
                cin = c in sel
                if ain == cin:
                    continue
                cand = c if ain else a
                if cand in sel:
                    continue
                score[cand] += wt[i]
        if not score:
            break
        ranked = sorted(score.items(), key=lambda kv: -kv[1])[:room]
        for cand, _ in ranked:
            sel.add(cand)
            order.append(cand)
        log("    round %d: +%d -> %d neurons (%.0fs)" % (rnd, len(ranked), len(sel), time.time() - t0))
    return order, sel


def write_blob(path, ids, pop, soma, offsets, targets, weights, mask, sugar, odor, bitter, meta):
    n = len(ids)
    nsyn = len(targets)
    with open(path, "wb") as f:
        f.write(b"FLYMIND1")
        f.write(struct.pack("<III", n, nsyn, len(meta.get("groups", {}))))
        pops = [0] * N_POP
        for p in pop:
            pops[p] += 1
        f.write(struct.pack("<%dI" % N_POP, *pops))
        f.write(struct.pack("<3I", len(sugar), len(bitter), len(odor)))
        rec = bytearray()
        for i in range(n):
            rec += struct.pack("<Qfff", ids[i], soma[i * 3], soma[i * 3 + 1], soma[i * 3 + 2])
            rec += bytes((pop[i], 0, 0, 0))
        f.write(rec)
        f.write(array.array("I", offsets).tobytes())
        f.write(array.array("I", targets).tobytes())
        f.write(array.array("f", weights).tobytes())
        f.write(bytes(mask))
        f.write(array.array("f", weights).tobytes())
        for lst in (sugar, bitter, odor):
            f.write(array.array("I", lst).tobytes())
        js = json.dumps(meta, ensure_ascii=False).encode("utf-8")
        f.write(struct.pack("<I", len(js)))
        f.write(js)


def main():
    args = sys.argv[1:]
    max_neurons = 3000
    rounds = 3
    out = OUT_BLOB
    for i, a in enumerate(args):
        if a == "--max-neurons" and i + 1 < len(args):
            max_neurons = int(args[i + 1])
        if a == "--rounds" and i + 1 < len(args):
            rounds = int(args[i + 1])
        if a == "--out" and i + 1 < len(args):
            out = args[i + 1]

    t0 = time.time()
    ids, rows = load_annotations()
    labels = [label_of(r) for r in rows]
    pops = [classify(l) for l in labels]
    print("== annotations: %d bodies (%.0fs)" % (len(ids), time.time() - t0))
    print("   populations:", dict(Counter(POP_NAMES[p] for p in pops)))
    print("   landmarks:", {k: sum(1 for l in labels if re.search(p, l, re.I))
                            for k, p in LANDMARKS.items()})
    seeds = {}
    for k, pat in SEED_PATTERNS.items():
        seeds[k] = [ids[i] for i, l in enumerate(labels) if re.search(pat, l, re.I)]
    print("   seeds:", {k: len(v) for k, v in seeds.items()})

    if "--stats" in args:
        return

    seed_all = sorted(set(seeds["sugar"]) | set(seeds["odor"]) | set(seeds["reward"])
                      | set(seeds["motor"]))
    print("== growing (budget %d, %d rounds) ==" % (max_neurons, rounds))
    selected, sel = grow(seed_all, max_neurons, rounds)
    reindex = {old: new for new, old in enumerate(selected)}
    print("    selected %d neurons" % len(selected))

    # soma coordinates come from the annotation table, converted to the units the mod
    # uses (voxels * 8nm -> micrometre/1000)
    soma = []
    coord_of = {}
    for i, bid in enumerate(ids):
        loc = (rows[i].get("somaLocation") or "").strip()
        xyz = [0.0, 0.0, 0.0]
        if loc:
            parts = loc.split(",")
            for k in range(min(3, len(parts))):
                try:
                    xyz[k] = float(parts[k])
                except ValueError:
                    pass
        coord_of[bid] = xyz
    for bid in selected:
        xyz = coord_of.get(bid, [0.0, 0.0, 0.0])
        soma.extend([xyz[0] * 8.0 / 1000.0, xyz[1] * 8.0 / 1000.0, xyz[2] * 8.0 / 1000.0])

    pop_of = dict(zip(ids, pops))
    out_pop = [pop_of.get(b, POP_UNKNOWN) for b in selected]

    print("== collecting edges (pass 2) ==")
    edges = []
    t1 = time.time()
    for b in batches():
        pre = b["body_pre"]
        post = b["body_post"]
        wt = b["weight"]
        for i in range(len(pre)):
            a = pre[i]
            if a not in sel:
                continue
            c = post[i]
            if c not in sel:
                continue
            edges.append((reindex[a], reindex[c], wt[i]))
    print("    %d edges among %d neurons (%.0fs)" % (len(edges), len(selected), time.time() - t1))

    deg = [0] * len(selected)
    for a, c, _ in edges:
        deg[a] += 1
    offsets = [0] * (len(selected) + 1)
    for i in range(len(selected)):
        offsets[i + 1] = offsets[i] + deg[i]
    cursor = offsets[:]
    targets = [0] * len(edges)
    weights = [0.0] * len(edges)
    for a, c, w in edges:
        k = cursor[a]
        targets[k] = c
        weights[k] = w * LIF["w_syn"]
        cursor[a] = k + 1

    mask = bytearray(len(edges))
    for k, (a, c, _) in enumerate(edges):
        if out_pop[a] == POP_MUSHROOM and out_pop[c] == POP_MBON:
            mask[k] = 1

    out_sugar = [reindex[i] for i in seeds["sugar"] if i in sel]
    out_odor = [reindex[i] for i in seeds["odor"] if i in sel]
    out_bitter = [reindex[i] for i in seeds["motor"] if i in sel]

    meta = dict(
        source="MaleCNS v1.0 (Berg et al. 2026, Cell) - Google Research x HHMI Janelia x FlyWire Consortium",
        model="Shiu et al. 2024 leaky integrate-and-fire, w_syn=%.3f mV" % LIF["w_syn"],
        lif=LIF, pop_names=POP_NAMES,
        groups={k: sum(1 for l in labels if re.search(p, l, re.I))
                for k, p in LANDMARKS.items()},
        counts=dict(Counter(POP_NAMES[p] for p in out_pop)),
        n_neurons=len(selected), n_edges=len(edges),
        n_plastic_synapses=sum(mask),
        seeds=dict(sugar=len(out_sugar), odor=len(out_odor), motor=len(out_bitter)),
        note="signs are excitatory-only: the flat-connectome edge table has no "
             "transmitter column, so inhibition is not modelled",
        built=time.strftime("%Y-%m-%d %H:%M:%S"))

    write_blob(out, [int(b) for b in selected], out_pop, soma, offsets, targets, weights,
               mask, out_sugar, out_bitter, out_odor, meta)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print("== wrote %s (%.2f MB) ==" % (out, os.path.getsize(out) / 1e6))
    print("   %.0fs total" % (time.time() - t0))


if __name__ == "__main__":
    main()
