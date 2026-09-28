import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read()
msg = F.Table(data, 16)
sch = msg.table(2)
print("schema at", sch.pos, "vtable", sch.vtable, "vlen", sch.vlen, "present", sch.present_fields())
print("fields vector len:", sch.vector_len(1))
for i in range(min(6, sch.vector_len(1))):
    ft = sch.vector_table(1, i)
    print("  raw field %d: %s" % (i, ft))
    if ft is None:
        continue
    print("     pos=%d vtable=%d vlen=%d present=%s" % (ft.pos, ft.vtable, ft.vlen, ft.present_fields()))
    print("     name=%r nullable=%s" % (ft.string(0), ft.bool_(1)))
    tt = ft.table(2)
    print("     type table=%s type_id=%s" % (tt, tt.i8(0) if tt else None))
    print("     children len=%d" % ft.vector_len(3))
