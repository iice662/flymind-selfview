"""Inspect the first arrow DictionaryBatch directly: buffer layout + decoded strings."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\body-annotations.feather"
f = F.FeatherFile(path)

# walk frames from the start of the file
pos = 8
for step in range(6):
    root_at, mlen = f._frame(pos)
    msg = F.Table(f.data, root_at)
    hdr = msg.table(2)
    hdr_type = -1
    for fi in range(msg.field_count()):
        slot = msg._slot(fi)
        if slot is not None and msg.buf[slot] in (1, 2, 3):
            hdr_type = msg.buf[slot]
            break
    body_len = msg.i64(3, 0)
    print("frame@%d hdr_type=%s body_len=%d hdr=%s" % (pos, hdr_type, body_len, hdr))
    if hdr is None:
        break
    print("   hdr pos=%d vlen=%d present=%s" % (hdr.pos, hdr.vlen, hdr.present_fields()))
    for fi in hdr.present_fields():
        slot = hdr._slot(fi)
        raw = bytes(f.data[slot:slot + 8])
        print("      f%d @%d raw=%s u32=%d i8=%d i64=%d" % (
            fi, slot, raw.hex(), struct.unpack_from("<I", raw)[0],
            struct.unpack_from("<b", raw)[0], struct.unpack_from("<q", raw)[0]))
        t = hdr.table(fi)
        if t is not None:
            print("         -> table pos=%d vlen=%d present=%s" % (t.pos, t.vlen, t.present_fields()))
    if hdr_type == 2:
        body = root_at + mlen
        # try the two candidate record-batch tables
        for fi in hdr.present_fields():
            rb = hdr.table(fi)
            if rb is None:
                continue
            nodes = [rb.vector_struct_i64(1, i, 16, 0) for i in range(rb.vector_len(1))]
            bufs = [(rb.vector_struct_i64(2, i, 16, 0), rb.vector_struct_i64(2, i, 16, 8))
                    for i in range(rb.vector_len(2))]
            print("   candidate rb field %d: nodes=%s buffers=%s" % (fi, nodes, bufs))
            for (o, l) in bufs:
                if l and l > 16:
                    raw = bytes(f.data[body + o: body + o + min(l, 400)])
                    if l > 8:
                        raw = raw[8:]
                    n = struct.unpack_from("<i", raw, 0)[0]
                    s = raw[4:4 + n]
                    if 0 < n < 64:
                        print("      -> first string: %r" % s.decode("utf-8", "replace"))
        break
    pos = root_at + mlen + body_len

