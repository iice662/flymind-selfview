import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read(1 << 20)

# schema frame at 8
msg = F.Table(data, 8)
print("schema message: pos=%d vtable=%d vlen=%d present=%s" % (msg.pos, msg.vtable, msg.vlen, msg.present_fields()))
for fi in msg.present_fields():
    slot = msg._slot(fi)
    print("   f%d slot=%d raw=%s i8=%d i16=%d i64=%d" % (
        fi, slot, data[slot:slot + 8].hex(), struct.unpack_from("<b", data, slot)[0],
        struct.unpack_from("<h", data, slot)[0], struct.unpack_from("<q", data, slot)[0]))

mlen = struct.unpack_from("<i", data, 12)[0]
# walk to the first record batch frame
pos = 8 + 8 + mlen
first = struct.unpack_from("<I", data, pos)[0]
print("\nnext frame @%d first=%s" % (pos, hex(first)))
if first == 0xFFFFFFFF:
    mlen2 = struct.unpack_from("<i", data, pos + 4)[0]
    root = pos + 8
else:
    mlen2 = struct.unpack_from("<i", data, pos)[0]
    root = pos + 4
print("   meta len =", mlen2)
rb_msg = F.Table(data, root)
print("   msg pos=%d vtable=%d vlen=%d present=%s" % (rb_msg.pos, rb_msg.vtable, rb_msg.vlen, rb_msg.present_fields()))
for fi in rb_msg.present_fields():
    slot = rb_msg._slot(fi)
    raw = data[slot:slot + 8]
    print("      f%d @%d raw=%s u32=%d i8=%d i16=%d i64=%d" % (
        fi, slot, raw.hex(), struct.unpack_from("<I", raw)[0],
        struct.unpack_from("<b", raw)[0], struct.unpack_from("<h", raw)[0],
        struct.unpack_from("<q", raw)[0]))
for fi in range(rb_msg.field_count()):
    t = rb_msg.table(fi)
    if t is not None:
        print("   field %d -> table @%d vtable=%d vlen=%d present=%s" % (
            fi, t.pos, t.vtable, t.vlen, t.present_fields()))
        if t.vector_len(1):
            print("      nodes:", t.vector_len(1), " buffers:", t.vector_len(2))
            for i in range(min(3, t.vector_len(1))):
                n = t.vector_table(1, i)
                print("         node %d: length=%d nulls=%d" % (i, n.i64(0), n.i64(1)))
            for i in range(min(3, t.vector_len(2))):
                b = t.vector_table(2, i)
                print("         buffer %d: offset=%d len=%d" % (i, b.i64(0), b.i64(1)))
