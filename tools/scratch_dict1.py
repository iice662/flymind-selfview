"""Throwaway: dump the leading message frames of body-annotations.feather."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, Table

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

pos = 8
for k in range(12):
    root_at, meta_len = f._frame(pos)
    msg = Table(data, root_at)
    mtype = msg.i8(1, 0)
    blen = msg.i64(3, 0)
    print("frame@%-10d root_at=%-8d meta_len=%-6d mtype=%d body_len=%-10d body_start=%d present=%s vlen=%d"
          % (pos, root_at, meta_len, mtype, blen, root_at + meta_len, msg.present_fields(), msg.vlen))
    if mtype == 3:
        rb0 = msg.table(2)
        print("   RecordBatch pos=%s len=%s nodes=%s buffers=%s"
              % (None if rb0 is None else rb0.pos, None if rb0 is None else rb0.i64(0, -1),
                 None if rb0 is None else rb0.vector_len(1), None if rb0 is None else rb0.vector_len(2)))
    if mtype == 2:
        print("   (record batch -- stopping)")
        break
    pos = root_at + meta_len + blen
