"""Work out the DictionaryBatch layout in the MaleCNS annotations feather.

Prints, for the first dictionary batch: the header table, its record-batch table,
the node/buffer structs, and — decisively — decoded UTF-8 strings from the candidate
data buffer.  Used to fix feather_lite's dictionary handling.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\body-annotations.feather"
d = F.FeatherFile(path)
data = d.data

# frame 0 = schema (starts at 8), its body is empty -> frame 1 at 6728
root_at, mlen = d._frame(8)
msg = F.Table(data, root_at)
print("schema frame: root_at=%d mlen=%d bodyLen=%d" % (root_at, mlen, msg.i64(3, 0)))
pos2 = root_at + mlen
root2, ml2 = d._frame(pos2)
msg2 = F.Table(data, root2)
print("frame2 @%d: root_at=%d mlen=%d present=%s bodyLen=%d"
      % (pos2, root2, ml2, msg2.present_fields(), msg2.i64(3, 0)))

for fi in msg2.present_fields():
    slot = msg2._slot(fi)
    raw = bytes(data[slot:slot + 8])
    print("   f%d @%d %s i8=%d i32=%d i64=%d"
          % (fi, slot, raw.hex(), struct.unpack_from("<b", raw)[0],
             struct.unpack_from("<i", raw)[0], struct.unpack_from("<q", raw)[0]))

hdr = msg2.table(2) or msg2.table(1)
print("header table @%d vlen=%d present=%s" % (hdr.pos, hdr.vlen, hdr.present_fields()))
for fi in hdr.present_fields():
    slot = hdr._slot(fi)
    raw = bytes(data[slot:slot + 8])
    t = hdr.table(fi)
    print("   f%d @%d %s i64=%d table=%s" % (
        fi, slot, raw.hex(), struct.unpack_from("<q", raw)[0],
        ("@%d vlen=%d present=%s" % (t.pos, t.vlen, t.present_fields())) if t else None))

# the record batch is whichever header field resolves to a table with a nodes vector
body_len = msg2.i64(3, 0)
body_start = root2 + ml2
for fi in hdr.present_fields():
    rb = hdr.table(fi)
    if rb is None:
        continue
    nn = rb.vector_len(1)
    nb = rb.vector_len(2)
    print("rb candidate f%d @%d: length=%d nodes=%d buffers=%d present=%s"
          % (fi, rb.pos, rb.i64(0), nn, nb, rb.present_fields()))
    if nn == 0 and nb == 0:
        continue
    nodes = [rb.vector_struct_i64(1, i, 16, 0) for i in range(nn)]
    bufs = [(rb.vector_struct_i64(2, i, 16, 0), rb.vector_struct_i64(2, i, 16, 8))
            for i in range(nb)]
    print("   nodes:", nodes)
    print("   buffers:", bufs)
    for bi, (off, ln) in enumerate(bufs):
        if ln > 16:
            raw = bytes(data[body_start + off: body_start + off + ln])
            print("   buffer %d raw[:16]=%s" % (bi, raw[:16].hex()))
            # try: uncompressed utf8 buffer (offsets + data) or lz4 frame
            if raw[:4] == bytes.fromhex("04224d18"):
                try:
                    out = F._lz4_frame(raw)
                    print("      lz4 -> %d bytes, first 80: %r" % (len(out), out[:80]))
                except Exception as e:
                    print("      lz4 failed:", e)
            elif len(raw) > 16:
                # offsets buffer? print first few int32
                offs = struct.unpack_from("<8i", raw, 0)
                print("      as int32 offsets:", offs)
    break
