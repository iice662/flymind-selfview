"""Throwaway: inspect statusLabel's DictionaryEncoding table."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data
sch = f.schema_msg.table(2)
ft = sch.vector_table(1, 7)
dt = ft.table(4)
print("DictionaryEncoding at %d vlen=%d present=%s" % (dt.pos, dt.vlen, dt.present_fields()))
for fi in range(dt.field_count()):
    at = dt._slot(fi)
    print("   slot %d at=%s %s" % (fi, at, "" if at is None else "u32=%d i64=%d i8=%d"
          % (struct.unpack_from("<I", data, at)[0],
             struct.unpack_from("<q", data, at)[0], data[at])))
print("id =", dt.i64(0, None))
it = dt.table(1)
if it is not None:
    print("indexType (Int) table at %d vlen=%d present=%s" % (it.pos, it.vlen, it.present_fields()))
    print("   bitWidth =", it.i32(0, None), " (probing i32 at slots)")
    for fi in range(it.field_count()):
        at = it._slot(fi)
        print("   slot %d at=%s i32=%s i8=%s is_signed=%s" % (fi, at,
              None if at is None else struct.unpack_from("<i", data, at)[0],
              None if at is None else data[at],
              None if at is None else data[at + 4]))
