import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read()
msg = F.Table(data, 16)
sch = msg.table(2)
ft = sch.vector_table(1, 2)          # bodyId
print("field table @%d vtable@%d vlen=%d" % (ft.pos, ft.vtable, ft.vlen))
print("vtable bytes:", data[ft.vtable:ft.vtable + ft.vlen].hex())
for k in range(ft.field_count()):
    slot = ft._slot(k)
    if slot is None:
        print("  f%d absent" % k)
        continue
    raw = data[slot:slot + 16]
    print("  f%d slot=%d raw=%s u32=%d i8=%d i64=%d" % (
        k, slot, raw[:12].hex(), struct.unpack_from("<I", raw)[0],
        struct.unpack_from("<b", raw)[0], struct.unpack_from("<q", raw)[0]))
print()
print("field table raw bytes @%d:" % ft.pos, data[ft.pos:ft.pos + 24].hex())
# what does the region around the table look like? names stored as strings nearby
print("region @%d:" % (ft.pos - 40), data[ft.pos - 40:ft.pos + 40].hex())
