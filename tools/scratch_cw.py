"""Throwaway: connectome-weights schema field tags."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\connectome-weights.feather"
f = FeatherFile(P)
data = f.data
print("footer batches:", len(f.record_batches))
sch = f.schema_msg.table(2)
print("Schema vlen=%d present=%s fields=%d" % (sch.vlen, sch.present_fields(), sch.vector_len(1)))
for i in range(sch.vector_len(1)):
    ft = sch.vector_table(1, i)
    name = ft.string(0)
    tag_at = ft._slot(2)
    tag = data[tag_at] if tag_at is not None else None
    print("field[%d] %-12s vlen=%d present=%s type_tag=%s" % (i, name, ft.vlen, ft.present_fields(), tag))
    for fi in range(ft.field_count()):
        at = ft._slot(fi)
        if at is None:
            print("     slot %d absent" % fi)
            continue
        u = struct.unpack_from("<I", data, at)[0]
        deref = at + u
        extra = ""
        if 0 <= deref < len(data) - 4:
            try:
                vt = deref - struct.unpack_from("<i", data, deref)[0]
                vlen = struct.unpack_from("<H", data, vt)[0]
                extra = " (valid table? vlen=%d)" % vlen
            except Exception:
                pass
        print("     slot %d at=%d u32=%d deref=%d i8=%d%s" % (fi, at, u, deref, data[at], extra))
