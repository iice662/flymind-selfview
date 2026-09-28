import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read()
footer_len = struct.unpack_from("<i", data, len(data) - 10)[0]
foff = len(data) - 10 - footer_len
footer = F.FB(data, foff)
print("footer@%d len=%d" % (foff, footer_len))
print("footer.pos =", footer.pos, " fields:", [i for i in range(8) if footer.field(i) is not None])

off = footer.field(3)
print("field3 value offset:", off)
start = off + struct.unpack_from("<I", data, off)[0]
n = struct.unpack_from("<I", data, start)[0]
print("block vector: start=%d len=%d" % (start, n))
for i in range(n):
    elem = start + 4 + i * 4
    uoff = struct.unpack_from("<I", data, elem)[0]
    print("  block %d: elem@%d uoff=%d (as struct:) %s" % (
        i, elem, uoff, [struct.unpack_from("<q", data, elem + 8 * k)[0] for k in range(3)]))
    tp = elem + uoff
    print("     interpreted as table@%d %s" % (tp, "in range" if tp + 4 <= len(data) else "OUT OF RANGE"))
    soff = struct.unpack_from("<i", data, tp)[0]
    vt = tp - soff
    vlen = struct.unpack_from("<H", data, vt)[0]
    print("     soff=%d vtable@%d vlen=%d entries=%s" % (soff, vt, vlen,
          [struct.unpack_from("<H", data, vt + 4 + 2 * k)[0] for k in range((vlen - 4) // 2)]))
    vals = []
    for k in range((vlen - 4) // 2):
        voff = struct.unpack_from("<H", data, vt + 4 + 2 * k)[0]
        if voff:
            vals.append((k, data[tp + voff:tp + voff + 8].hex()))
    print("     field bytes:", vals)
    blk = F.FB.at(data, tp)
    print("     offset=%d metaLen=%d bodyLen=%d" % (blk.int64(0), blk.int32(1), blk.int64(2)))
