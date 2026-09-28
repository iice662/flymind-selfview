"""Stream the MaleCNS edge table into a compact binary the C# builder reads.

The source is a 1 GB Arrow IPC table holding body_pre / body_post / weight for
151,856,684 synapses.  feather_lite decodes it in batches; this writes each batch
straight out so nothing big is ever held in memory.

Output (malecns/edges.bin):
    int64 count, then count x (int64 body_pre, int64 body_post, int32 milli_weight)
"""
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

SRC = r"D:\projects\science\malecns\connectome-weights.feather"
DST = r"D:\projects\science\malecns\edges.bin"

t0 = time.time()
f = F.FeatherFile(SRC)
written = 0
buf = bytearray()
with open(DST, "wb") as out:
    out.write(struct.pack("<q", -1))          # placeholder count, patched below
    for batch in f.iter_batches():
        pre = batch["body_pre"]
        post = batch["body_post"]
        wt = batch["weight"]
        buf.clear()
        for i in range(len(pre)):
            buf += struct.pack("<qqi", pre[i], post[i], int(wt[i]))
        out.write(buf)
        written += len(pre)
        if written % (1 << 22) < len(pre):
            print("    %d edges (%.0fs)" % (written, time.time() - t0), end="\r")
    out.seek(0)
    out.write(struct.pack("<q", written))
print()
print("wrote %s: %d edges, %.2f GB (%.0fs)"
      % (DST, written, os.path.getsize(DST) / 1e9, time.time() - t0))
