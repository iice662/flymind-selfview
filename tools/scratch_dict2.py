"""Throwaway: dump the DictionaryBatch at frame 6728 byte by byte."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, Table

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

def hexdump(base, length, label):
    print("--- %s: [%d..%d)" % (label, base, base + length))
    for row in range(base, base + length, 16):
        chunk = bytes(data[row:row + 16])
        print("  %8d  %-47s  %s" % (row, " ".join("%02x" % b for b in chunk),
                                    "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)))

# frame 6728
root_at, meta_len = f._frame(6728)
print("frame 6728: root uoffset pos=%d meta_len=%d body_start=%d" % (root_at, meta_len, root_at + meta_len))
print("uoffset at %d = %d" % (root_at, struct.unpack_from("<I", data, root_at)[0]))
msg = Table(data, root_at)
print("Message table pos=%d vtable=%d vlen=%d present=%s" % (msg.pos, msg.vtable, msg.vlen, msg.present_fields()))
for fi in range(msg.field_count()):
    sl = msg._slot(fi)
    print("   msg slot %d -> %s" % (fi, sl))
print("version=%d header_type=%d bodyLength=%d" % (msg.i16(0), msg.i8(1), msg.i64(3)))
hexdump(msg.pos, 32, "Message table")
print("header field 2 slot -> %s" % msg._slot(2))
print("header field 1 slot -> %s" % msg._slot(1))
d2 = msg._deref(2)
d1 = msg._deref(1)
print("deref(2)=%s deref(1)=%s" % (d2, d1))
for addr in (d2, d1):
    if addr is None:
        continue
    try:
        t = Table.at(data, addr)
    except ValueError as e:
        print("  Table.at(%d) -> %s" % (addr, e))
        continue
    print("  Table.at(%d) pos=%d vtable=%d vlen=%d present=%s" % (addr, t.pos, t.vtable, t.vlen, t.present_fields()))
    hexdump(t.vtable, min(48, t.vlen), "vtable@%d" % t.vtable)
    hexdump(t.pos, 40, "table@%d" % t.pos)
    for fi in range(t.field_count()):
        sl = t._slot(fi)
        print("     slot %d -> %s  i64=%s i32=%s" % (fi, sl,
              None if sl is None else struct.unpack_from("<q", data, sl)[0],
              None if sl is None else struct.unpack_from("<i", data, sl)[0]))
