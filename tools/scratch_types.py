"""Throwaway: dump every field's Type table raw, in both files."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, TYPE_NAMES

for path, label in ((r"D:\projects\science\malecns\body-annotations.feather", "annotations"),
                    (r"D:\projects\science\malecns\connectome-weights.feather", "weights")):
    f = FeatherFile(path)
    data = f.data
    sch = f.schema_msg.table(2)
    print("=" * 70)
    print(label)
    for i in range(sch.vector_len(1)):
        ft = sch.vector_table(1, i)
        name = ft.string(0)
        tag_at = ft._slot(2)
        tag = data[tag_at] if tag_at is not None else None
        addr = ft._deref(3)
        t = ft.table(3)
        line = "  %-16s tag=%-3s addr=%-6s" % (name, tag, addr)
        if t is None:
            line += " no table"
        else:
            nf = t.field_count()
            line += " pos=%d vt=%d vlen=%d present=%s" % (t.pos, t.vtable, t.vlen, t.present_fields())
            if nf:
                a0 = t._slot(0)
                a1 = t._slot(1)
                line += " slot0=%s(%s) slot1=%s(%s)" % (
                    a0, None if a0 is None else struct.unpack_from("<i", data, a0)[0],
                    a1, None if a1 is None else struct.unpack_from("<i", data, a1)[0])
            line += " i8(0)=%s -> %s" % (t.i8(0), TYPE_NAMES.get(t.i8(0), "?"))
        print(line)
        if i < 3 or label == "weights":
            base = (addr or 0) - 24
            print("      bytes@%d: %s" % (base, " ".join("%02x" % b for b in data[base:base + 48])))
