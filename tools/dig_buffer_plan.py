"""Print the real per-field buffer consumption of the annotations record batch.

The node/buffer counts (38 nodes / 101 buffers) contradict the naive "2 buffers per
scalar, 4 per list" rule, so one or more columns must differ.  This walks the field
list consuming buffers the way the decoder does and prints exactly which buffer lengths
land on which field, which is how the discrepancy gets localised.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\body-annotations.feather"
d = F.FeatherFile(path)

# locate the first record batch frame
pos = 8
for _ in range(40):
    root_at, mlen = d._frame(pos)
    msg = F.Table(d.data, root_at)
    if msg.i8(1, 0) == 3:
        rb = msg.table(2) or msg.table(1)
        body = root_at + mlen
        break
    pos = root_at + mlen + msg.i64(3, 0)

nb = rb.vector_len(2)
lens = [rb.vector_struct_i64(2, i, 16, 8) for i in range(nb)]
nodes = [rb.vector_struct_i64(1, i, 16, 0) for i in range(rb.vector_len(1))]
print("buffers: %d   nodes: %d" % (nb, len(nodes)))
print("buffer lengths:", lens)
print()

# For each field try the two candidate plans and report which one keeps every
# "validity" buffer at the expected bitmap size (ceil(n/8) = 8192 for n=65536).
IDX_NAME = {0: "bool", 1: "int8", 2: "int64", 3: "float64", 4: "float32",
            5: "utf8", 12: "list<int64>"}

for plan in ("strict-2/3", "all-2"):
    bi = 0
    ni = 0
    ok = True
    print("=== plan %s ===" % plan)
    for f in d.fields:
        n = nodes[ni]
        ni += 1
        nbuf = 3 if (f.type_id == 5 and plan == "strict-2/3") else 2
        if f.type_id == 12:
            nbuf = 4
        got = lens[bi:bi + nbuf]
        bi += nbuf
        valid_like = got[0] == (n + 7) // 8
        extra = "" if valid_like else "   <-- first buffer is not a bitmap"
        print("   %-16s %-11s n=%-7d buffers=%s%s" % (f.name, IDX_NAME.get(f.type_id, f.type_id),
                                                     n, got, extra))
        if not valid_like:
            ok = False
        if bi > nb:
            print("   ...ran out of buffers")
            break
    print("   consumed %d of %d buffers; every first-buffer-is-bitmap: %s" % (bi, nb, ok))
    print()
