"""Throwaway: decompress somaLocation's two buffers directly."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, _lz4_frame

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data
msg, body_start = f._message_at(f.record_batches[0][0])
rb = msg.table(2)

for b in (90, 91, 92):
    off = rb.vector_struct_i64(2, b, 16, 0)
    ln = rb.vector_struct_i64(2, b, 16, 8)
    raw = bytes(data[body_start + off: body_start + off + ln])
    print("=== buf %d len=%d" % (b, ln))
    if ln < 8:
        print("   too short")
        continue
    declared = struct.unpack_from("<q", raw, 0)[0]
    print("   declared=%d magic=%s" % (declared, raw[8:12].hex()))
    try:
        dec = _lz4_frame(raw[8:])
        print("   decompressed %d bytes (expected %d) %s" % (len(dec), declared,
              "OK" if len(dec) == declared else "MISMATCH"))
        if len(dec) >= 8:
            print("   first ints: %s" % (struct.unpack_from("<4i", dec, 0),))
            print("   last ints : %s" % (struct.unpack_from("<4i", dec, len(dec) - 16),))
    except Exception as e:
        print("   lz4 FAILED: %r" % (e,))
