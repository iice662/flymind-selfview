import struct
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read()
msg_pos = 16
u = struct.unpack_from("<I", data, msg_pos)[0]
msg = msg_pos + u
print("Message table @%d" % msg)
soff = struct.unpack_from("<i", data, msg)[0]
vt = msg - soff
n = struct.unpack_from("<H", data, vt)[0]
nf = (n - 4) // 2
print("  soff=%d vtable@%d vlen=%d fields=%d" % (soff, vt, n, nf))
for k in range(nf):
    voff = struct.unpack_from("<H", data, vt + 4 + 2 * k)[0]
    if not voff:
        print("   f%d absent" % k)
        continue
    at = msg + voff
    raw = data[at:at + 8]
    print("   f%d @%d raw=%s u32=%d i16=%d i8=%d" % (
        k, at, raw[:6].hex(), struct.unpack_from("<I", raw)[0],
        struct.unpack_from("<h", raw)[0], struct.unpack_from("<b", raw)[0]))
    if k in (1, 2):
        tgt = at + struct.unpack_from("<I", raw)[0]
        print("        -> uoffset target %d" % tgt)
        if 0 <= tgt < len(data) - 8:
            s2 = struct.unpack_from("<i", data, tgt)[0]
            vt2 = tgt - s2
            if 0 <= vt2 < len(data) - 4:
                n2 = struct.unpack_from("<H", data, vt2)[0]
                print("        target table: soff=%d vtable@%d vlen=%d fields=%d" % (
                    s2, vt2, n2, (n2 - 4) // 2))
                for k2 in range((n2 - 4) // 2):
                    v2 = struct.unpack_from("<H", data, vt2 + 4 + 2 * k2)[0]
                    if not v2:
                        print("         f%d absent" % k2)
                        continue
                    at2 = tgt + v2
                    raw2 = data[at2:at2 + 8]
                    print("         f%d @%d raw=%s u32=%d i8=%d" % (
                        k2, at2, raw2[:6].hex(), struct.unpack_from("<I", raw2)[0],
                        struct.unpack_from("<b", raw2)[0]))
