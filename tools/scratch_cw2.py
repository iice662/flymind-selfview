"""Throwaway: connectome pandas metadata + type table structure."""
import json, struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\connectome-weights.feather"
f = FeatherFile(P)
data = f.data

head = bytes(data[:1 << 20])
s = head.find(b'{"index_columns"')
if s < 0:
    print("no pandas metadata found in first 1MB")
else:
    meta, _ = json.JSONDecoder().raw_decode(head[s:].decode("utf-8", "replace"))
    for c in meta.get("columns", []):
        print("  pandas %-12s pandas_type=%-10s numpy_type=%s" % (c.get("name"), c.get("pandas_type"), c.get("numpy_type")))

sch = f.schema_msg.table(2)
for i in range(sch.vector_len(1)):
    ft = sch.vector_table(1, i)
    print("\nfield[%d] %s" % (i, ft.string(0)))
    addr = ft._deref(3)
    print("   type union value -> %d" % addr)
    t = ft.table(3)
    if t is None:
        print("   not a table")
        continue
    print("   type table pos=%d vtable=%d vlen=%d present=%s" % (t.pos, t.vtable, t.vlen, t.present_fields()))
    for fi in range(t.field_count()):
        at = t._slot(fi)
        print("      slot %d at=%s i8=%s i16=%s i32=%s" % (
            fi, at, None if at is None else data[at],
            None if at is None else struct.unpack_from("<h", data, at)[0],
            None if at is None else struct.unpack_from("<i", data, at)[0]))
