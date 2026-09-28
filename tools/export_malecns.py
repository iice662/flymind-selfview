"""Read the MaleCNS flat-connectome tables into plain binary files.

Why: the source tables are Arrow IPC (`feather`) with LZ4_FRAME-compressed,
linked blocks; feather_lite decodes them, but re-decoding 1 GB on every analysis
run is wasteful.  This writes the columns out as raw arrays that a later step can
memory-map.

Outputs (in D:\\projects\\science\\malecns):
    connectome.edges    int64 body_pre[n], body_post[n], weight[n]  + 32-byte header
    annotations.tsv     decoded bodyId / type / class / superclass / side / soma columns

Usage:
    python export_malecns.py --edges
    python export_malecns.py --annotations
    python export_malecns.py --info
"""
from __future__ import annotations

import array
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "malecns"))
CONNECTOME = os.path.join(DATA, "connectome-weights.feather")
ANNOTATIONS = os.path.join(DATA, "body-annotations.feather")
OUT_EDGES = os.path.join(DATA, "connectome.edges")
OUT_ANN = os.path.join(DATA, "annotations.tsv")

HEADER = b"MCNSEDG1"


def export_edges():
    t0 = time.time()
    f = F.FeatherFile(CONNECTOME)
    n_total = None
    with open(OUT_EDGES, "wb") as out:
        out.write(HEADER)
        out.write(struct.pack("<QQQ", 0, 0, 0))     # patched later: pre, post, weight offsets
        written = 0
        pre_off = out.tell()
        # three sequential passes would need three files; instead buffer per batch and
        # write column by column into a temporary list of file objects
        import tempfile
        tmp = [tempfile.NamedTemporaryFile(delete=False, dir=DATA) for _ in range(3)]
        try:
            for bi, batch in enumerate(f.iter_batches()):
                for k, tmpf in zip(("body_pre", "body_post", "weight"), tmp):
                    vals = batch[k]
                    arr = array.array("q", vals)
                    tmpf.write(arr.tobytes())
                written += len(batch["body_pre"])
                if bi % 100 == 0:
                    print("    %d edges (%.0fs)" % (written, time.time() - t0), end="\r")
            print()
            offsets = []
            for tmpf in tmp:
                tmpf.flush()
                offsets.append(out.tell())
                with open(tmpf.name, "rb") as src:
                    while True:
                        chunk = src.read(1 << 22)
                        if not chunk:
                            break
                        out.write(chunk)
        finally:
            for tmpf in tmp:
                tmpf.close()
                os.unlink(tmpf.name)
        out.seek(len(HEADER))
        out.write(struct.pack("<QQQ", offsets[0], offsets[1], offsets[2]))
        out.write(struct.pack("<Q", written)) if False else None
    size = os.path.getsize(OUT_EDGES)
    print("wrote %s: %d edges, %.2f GB (%.0fs)" % (OUT_EDGES, written, size / 1e9, time.time() - t0))
    return written


def export_annotations():
    f = F.FeatherFile(ANNOTATIONS)
    cols = ["bodyId", "type", "class", "subclass", "superclass", "supertype",
            "hemibrainType", "somaSide", "somaNeuromere", "receptorType",
            "entryNerve", "exitNerve", "status", "dimorphism", "vfbId", "mancType"]
    keep = [c for c in cols if c in [fl.name for fl in f.fields]]
    with open(OUT_ANN, "w", encoding="utf-8", newline="") as out:
        out.write("\t".join(keep) + "\n")
        rows = 0
        for batch in f.iter_batches():
            for i in range(len(batch["bodyId"])):
                out.write("\t".join(str(batch[c][i]).replace("\t", " ") for c in keep) + "\n")
                rows += 1
    print("wrote %s: %d rows, columns=%s" % (OUT_ANN, rows, keep))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or "--info" in args:
        for p, name in ((CONNECTOME, "connectome"), (ANNOTATIONS, "annotations")):
            f = F.FeatherFile(p)
            print("== %s: %s" % (name, f.schema_summary()))
            print("   batches: %d" % len(f.record_batches))
    if "--edges" in args:
        export_edges()
    if "--annotations" in args:
        export_annotations()
