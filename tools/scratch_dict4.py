"""Throwaway: enumerate all leading DictionaryBatch frames + schema fields."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, Table, TYPE_NAMES

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

print("== schema fields (%d)" % len(f.fields))
for fl in f.fields:
    print("   %-28s type=%-12s dict_id=%s bit_width=%s children=%s"
          % (fl.name, fl.kind(), fl.dictionary_id, fl.bit_width,
             [c.kind() for c in fl.children]))

print("== leading frames")
pos = 8
n_dict = 0
while pos < len(data) - 10:
    root_at, meta_len = f._frame(pos)
    msg = Table(data, root_at)
    mtype = msg.i8(1, 0)
    body_len = msg.i64(3, 0)
    if mtype == 3:
        rb = msg.table(2)
        print("frame@%d mtype=3 (RecordBatch) len=%s nodes=%s buffers=%s"
              % (pos, rb.i64(0, -1), rb.vector_len(1), rb.vector_len(2)))
        break
    if mtype == 2:
        db = Table.at(data, msg._deref(2))
        rb = db.table(1)
        line = "frame@%d mtype=2 id=%s" % (pos, db.i64(0, None))
        if rb is not None:
            line += " rb_len=%s nodes=%s buffers=%s len0=%s buf_lens=%s" % (
                rb.pos, rb.vector_len(1), rb.vector_len(2), rb.i64(0, -1),
                [rb.vector_struct_i64(2, i, 16, 8) for i in range(rb.vector_len(2))])
        print(line)
        n_dict += 1
    else:
        print("frame@%d mtype=%d" % (pos, mtype))
    pos = root_at + meta_len + body_len
    if n_dict > 45:
        break
print("total dict batches seen:", n_dict)
