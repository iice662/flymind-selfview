"""Read the circuit blob's per-neuron records without the C# tools.

The blob (FLYMIND4) is the single source of truth for every number in the paper; this reader
exists so the slice can be inspected and plotted from plain Python.  Layout, mirroring
BrainData.Load in tools/CircuitPreview/Program.cs:

    char[8]  "FLYMIND4"
    u32      N, Syn, <reserved>
    u32[12]  reserved counters
    u32      nSugar, nMotor, nOdor, nSelf, nCx, nRelay
    N x 24B  i64 bodyId | f32 x | f32 y | f32 z | u8 pop | u8 cxFamily | 2B pad
    (N+1) i32 connectome offsets          (not read here)
    Syn  i32 targets, Syn f32 weights, Syn u8 mask, Syn f32 base weights
    nSugar i32, nMotor i32, nOdor i32, nSelf i32, nCx i32, nRelay i32

Usage:
    python tools/dump_slice.py [--blob PATH] [--annotations PATH] [--out CSV]
"""

import argparse
import os
import struct
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Codes as written by tools/CircuitBuilder/Program.cs.  They are NOT 0-based by population:
# 0 is "no rule matched", 8 (interneuron) and 9 (VNC) are empty in this slice because the
# growth round filled the budget with the named populations.
POP_NAMES = {0: "unnamed", 1: "sensory", 2: "antennal", 3: "KC", 4: "dopamine", 5: "MBON",
             6: "descending", 7: "motor", 8: "interneuron", 9: "VNC",
             10: "LPTC (self-motion)", 11: "CX"}
CX_NAMES = {0: "not-CX", 1: "ring EPG/PEG", 2: "columnar", 3: "fan-body", 4: "other CX"}


def read_slice(blob):
    """Return (body_id, pop, cx_family, soma_xyz) for the 12,000 neurons of the slice."""
    with open(blob, "rb") as f:
        tag = f.read(8)
        if tag != b"FLYMIND4":
            raise ValueError(f"not a FLYMIND4 blob: {tag!r}")
        n, syn, _ = struct.unpack("<III", f.read(12))
        f.read(4 * 12)
        n_sugar, n_motor, n_odor, n_self, n_cx, n_relay = struct.unpack("<IIIIII", f.read(24))
        rec = np.frombuffer(f.read(n * 24), dtype=np.uint8).reshape(n, 24)
    body_id = rec[:, 0:8].copy().view("<i8").ravel()
    pop = rec[:, 20].copy()
    cx_family = rec[:, 21].copy()
    soma = rec[:, 8:20].copy().view("<f4").reshape(n, 3)
    counts = dict(n=n, syn=syn, n_sugar=n_sugar, n_motor=n_motor, n_odor=n_odor,
                  n_self=n_self, n_cx=n_cx, n_relay=n_relay)
    return body_id, pop, cx_family, soma, counts


def _separation(v):
    """Best 1-D 2-means split of a coordinate (variance-explained) - the midline rule."""
    c = np.sort(np.asarray(v, dtype=float))
    total = ((c - c.mean()) ** 2).sum()
    run = np.cumsum(c)
    k = np.arange(1, len(c))
    m1 = run[:-1] / k
    m2 = (run[-1] - run[:-1]) / (len(c) - k)
    between = k * (m1 - c.mean()) ** 2 + (len(c) - k) * (m2 - c.mean()) ** 2
    j = int(np.argmax(between))
    return (between[j] / total if total > 0 else 0.0), 0.5 * (c[j] + c[j + 1])


def read_annotations(path):
    """bodyId -> (type, hemibrainType), so a slice cell can be named."""
    types = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
        cols = header.rstrip("\n").split("\t")
        i_type = cols.index("type")
        i_hemi = cols.index("hemibrainType") if "hemibrainType" in cols else None
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) <= i_type:
                continue
            types[int(p[0])] = (p[i_type], p[i_hemi] if i_hemi is not None else "")
    return types


def read_index_arrays(blob):
    """Return the six index arrays (sugar, motor, odour, self-motion, CX, visual relay)."""
    with open(blob, "rb") as f:
        f.read(8)
        n, syn, _ = struct.unpack("<III", f.read(12))
        f.read(48)
        counts = struct.unpack("<IIIIII", f.read(24))
        f.read(n * 24)              # neurons
        f.read((n + 1) * 4)         # offsets
        f.read(syn * 4)             # targets
        f.read(syn * 4)             # weights
        f.read(syn)                 # kc/mbon mask
        f.read(syn * 4)             # plastic base weights
        return [np.frombuffer(f.read(c * 4), dtype="<i4") for c in counts]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blob", default=os.path.join(ROOT, "flymind.brain"))
    ap.add_argument("--annotations", default=os.path.join(ROOT, "malecns", "annotations.tsv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "raw", "slice-census.csv"))
    a = ap.parse_args()

    body_id, pop, cx_family, soma, counts = read_slice(a.blob)
    types = read_annotations(a.annotations) if os.path.exists(a.annotations) else {}
    print(f"{counts['n']} neurons, {counts['syn']} synapses; "
          f"pool {counts['n_self']} + relay {counts['n_relay']}, CX {counts['n_cx']}, "
          f"annotations {'joined' if types else 'MISSING'}")

    # ---- pool membership, midline and body patch, recomputed exactly as the harness does
    sugar, motor, odor, selfmotion, cx, relay = read_index_arrays(a.blob)
    pool = np.union1d(selfmotion, relay)
    in_pool = np.zeros(len(body_id), dtype=int)
    in_pool[pool] = 1
    pool_is_lptc = np.isin(np.arange(len(body_id)), selfmotion).astype(int)
    pool_is_relay = np.isin(np.arange(len(body_id)), relay).astype(int)

    p = soma[pool]
    axis = int(np.argmax([_separation(p[:, k])[0] for k in range(3)]))
    mid = _separation(p[:, axis])[1]
    positive_side = (soma[:, axis] > mid).astype(int)
    centroid = p.mean(axis=0)
    order = np.argsort(((p - centroid) ** 2).sum(axis=1))
    patch = np.zeros(len(body_id), dtype=int)
    patch[pool[order[:int(round(len(pool) * 0.25))]]] = 1
    zero_coord = (np.abs(soma).sum(axis=1) == 0).astype(int)
    print(f"pool {len(pool)} cells; midline axis {'xyz'[axis]} at {mid:.1f} "
          f"({int((~positive_side[pool].astype(bool)).sum())} / {int(positive_side[pool].sum())}); "
          f"body patch {int(patch.sum())} cells, "
          f"{int(zero_coord[pool].sum())} pool cells without an annotated soma")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as w:
        w.write("index,body_id,pop,pop_name,cx_family,cx_name,x,y,z,cell_type,"
                "in_pool,is_lptc,is_relay,in_body_patch,positive_side,no_soma\n")
        for i in range(len(body_id)):
            t, _ = types.get(int(body_id[i]), ("", ""))
            w.write(f"{i},{body_id[i]},{pop[i]},{POP_NAMES.get(int(pop[i]), '?')},"
                    f"{cx_family[i]},{CX_NAMES.get(int(cx_family[i]), '?')},"
                    f"{soma[i, 0]:.1f},{soma[i, 1]:.1f},{soma[i, 2]:.1f},{t},"
                    f"{in_pool[i]},{pool_is_lptc[i]},{pool_is_relay[i]},{patch[i]},"
                    f"{positive_side[i]},{zero_coord[i]}\n")
    print("wrote", a.out)

    # sanity: the population census must match the manuscript
    print("  population census (blob codes):")
    for code in sorted(POP_NAMES):
        c = int((pop == code).sum())
        if c:
            print(f"    {code:>2} {POP_NAMES[code]:<18} {c:>6}")
    total = 0
    for code in sorted(CX_NAMES):
        if code == 0:
            continue
        c = int((cx_family == code).sum())
        total += c
        print(f"    CX{code} {CX_NAMES[code]:<17} {c:>6}")
    print(f"    CX total {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
