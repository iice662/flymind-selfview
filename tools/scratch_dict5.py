"""Throwaway: walk every frame in the file via the footer's record batch blocks."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, Table

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

print("footer says %d record batch blocks" % len(f.record_batches))
print("first 6 blocks:", f.record_batches[:6])

# every frame between schema (8) and the last record batch end
pos = 8
seen = {}
order = []
guard = 0
while pos < len(data) - 10 and guard < 500:
    guard += 1
    try:
        root_at, meta_len = f._frame(pos)
        msg = Table(data, root_at)
    except Exception as e:
        print("stop at %d: %s" % (pos, e))
        break
    mtype = msg.i8(1, 0)
    body_len = msg.i64(3, 0)
    seen[mtype] = seen.get(mtype, 0) + 1
    if mtype == 2:
        db = Table.at(data, msg._deref(2))
        rb = db.table(1)
        order.append((pos, "dict", "id0=%d" % db.i64(0, -1),
                      "rbpos=%s nodes=%s buffers=%s len=%s bufs=%s" % (
                          None if rb is None else rb.pos,
                          None if rb is None else rb.vector_len(1),
                          None if rb is None else rb.vector_len(2),
                          None if rb is None else rb.i64(0, -1),
                          None if rb is None else [(rb.vector_struct_i64(2, i, 16, 0),
                                                    rb.vector_struct_i64(2, i, 16, 8))
                                                   for i in range(rb.vector_len(2))])))
    else:
        order.append((pos, "type%d" % mtype, "body=%d" % body_len, ""))
    pos = root_at + meta_len + body_len

print("message type histogram:", seen)
print("total frames:", len(order))
print("first 8 frames:")
for row in order[:8]:
    print("   ", row)
print("dict frames:")
for row in order:
    if row[1] == "dict":
        print("   ", row)
