"""Throwaway: pandas metadata + per-field arrow type tag ground truth."""
import json, struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

head = bytes(data[:1 << 20])
start = head.find(b'{"index_columns"')
meta, end = json.JSONDecoder().raw_decode(head[start:].decode("utf-8", "replace"))
print("pandas columns: %d" % len(meta.get("columns", [])))
for i, c in enumerate(meta.get("columns", [])):
    print("  meta[%d] %-20s pandas_type=%-22s numpy_type=%s"
          % (i, c.get("name"), c.get("pandas_type"), c.get("numpy_type")))

print("\n== arrow schema Field tables ==")
sch = f.schema_msg.table(2)
for i in range(sch.vector_len(1)):
    ft = sch.vector_table(1, i)
    name = ft.string(0)
    tag_at = ft._slot(2)
    tag = data[tag_at] if tag_at is not None else None
    typ_addr = ft._deref(3)
    dict_slot = ft._slot(4)
    line = "field[%2d] %-18s type_tag=%-4s type_table=%s" % (i, name, tag, typ_addr)
    if typ_addr is not None:
        t = ft.table(3)
        if t is not None:
            line += " (i8=%d)" % t.i8(0)
    if dict_slot is not None:
        dt = ft.table(4)
        line += " DICT id=%s indexType=%s" % (None if dt is None else dt.i64(0),
                                              None if dt is None else dt.table(0))
    print(line)
