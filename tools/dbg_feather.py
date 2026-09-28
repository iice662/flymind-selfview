import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read()
print("file size:", len(data))
print("head:", data[:16].hex(), " tail:", data[-16:].hex())
footer_len = struct.unpack_from("<i", data, len(data) - 10)[0]
print("footer_len:", footer_len, " footer_off:", len(data) - 10 - footer_len)
footer = F.FB(data, len(data) - 10 - footer_len)
print("footer fields present:", [i for i in range(8) if footer.field(i) is not None])
n = footer.vector_len(3)
print("block vector len(field3):", n)
for i in range(min(n, 3)):
    blk = footer.vector_table(3, i)
    print("  block", i, "fields:", [j for j in range(5) if blk.field(j) is not None],
          "offset:", blk.int64(0), "metaLen:", blk.int32(1), "bodyLen:", blk.int64(2))
# also try field 2 and 4 in case my footer field numbering is off
for fi in (2, 3, 4, 5):
    try:
        print("  field %d vector len = %s" % (fi, footer.vector_len(fi)))
    except Exception as e:
        print("  field %d err %s" % (fi, e))
print("schema field present:", footer.field(1) is not None)
sch = footer.table(1)
if sch is not None:
    print("schema fields:", [i for i in range(6) if sch.field(i) is not None])
    print("schema endianness:", sch.int16(0), "num fields:", sch.vector_len(1))
