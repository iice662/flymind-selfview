import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

for path in sys.argv[1:]:
    print("==", os.path.basename(path))
    data = open(path, "rb").read(1 << 20)
    msg, body = F.Table(data, 8 + 8), 8 + 8
    print("   msg table pos=%d vtable=%d vlen=%d fields=%s" % (
        msg.pos, msg.vtable, msg.vlen, msg.present_fields()))
    for fi in range(msg.field_count()):
        slot = msg._slot(fi)
        if slot is None:
            print("   f%d absent" % fi)
            continue
        u = struct.unpack_from("<I", data, slot)[0]
        print("   f%d slot=%d uoffset=%d -> target=%d  i8=%d i16=%d i32=%d i64=%d" % (
            fi, slot, u, slot + u, struct.unpack_from("<b", data, slot)[0],
            struct.unpack_from("<h", data, slot)[0], struct.unpack_from("<i", data, slot)[0],
            struct.unpack_from("<q", data, slot)[0]))
    hdr = msg.table(2)
    print("   msg.table(2) =", hdr)
    if hdr is None:
        hdr = msg.table(1)
        print("   fallback msg.table(1) =", hdr)
    if hdr is not None:
        print("   header fields=%s  vector(1) len=%d" % (hdr.present_fields(), hdr.vector_len(1)))
        for i in range(min(4, hdr.vector_len(1))):
            ft = hdr.vector_table(1, i)
            if ft is None:
                print("     field %d: None" % i)
                continue
            print("     field %d: name=%r type_id=%s nullable=%s dict=%s children=%d" % (
                i, ft.string(0), (ft.table(2).i8(0) if ft.table(2) else None),
                ft.bool_(1), (ft.table(4).i64(0) if ft.table(4) else None), ft.vector_len(3)))
