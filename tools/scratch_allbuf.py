"""Throwaway: full buffer table of batch 0 + schema field list."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
msg, body_start = f._message_at(f.record_batches[0][0])
rb = msg.table(2)
n = rb.vector_len(2)
print("buffers=%d nodes=%d" % (n, rb.vector_len(1)))
print("--- schema fields that own buffers (in order):")
def walk(field, depth=0):
    kind = field.kind()
    if field.dictionary_id is not None:
        own = 2
    elif field.type_id == 12:
        own = 2
    else:
        own = 1
    print("   %s%-22s type=%-6s owns=%d buf" % ("  " * depth, field.name, kind, own))
    for c in field.children:
        walk(c, depth + 1)
for fl in f.fields:
    walk(fl)
print("--- buffers:")
b = 0
for i in range(n):
    off = rb.vector_struct_i64(2, i, 16, 0)
    ln = rb.vector_struct_i64(2, i, 16, 8)
    print("   buf %3d off=%-9d len=%-9d" % (i, off, ln))
