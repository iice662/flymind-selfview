"""Throwaway: inspect somaLocation's buffers — uncompressed but sniffed as compressed."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data
pos = f.record_batches[0][0]
msg, body_start = f._message_at(pos)
rb = msg.table(2)
comp = rb.table(3)
print("RecordBatch.codec = %s" % (None if comp is None else comp.i8(0)))
print("body_start=%d" % body_start)
for b in (90, 91, 92):
    off = rb.vector_struct_i64(2, b, 16, 0)
    ln = rb.vector_struct_i64(2, b, 16, 8)
    raw = bytes(data[body_start + off: body_start + off + ln])
    declared = struct.unpack_from("<q", raw, 0)[0] if len(raw) >= 8 else None
    print("buf %d off=%d len=%-8d declared=%-10s payload[:4]=%s  len(payload)=%d"
          % (b, off, ln, declared, raw[8:12].hex(), len(raw) - 8))
    print("     verdict: declared(%s) > 0 AND len(payload)=%d <= declared -> %s"
          % (declared, len(raw) - 8, (declared or 0) > 0 and len(raw) - 8 <= (declared or 0)))
