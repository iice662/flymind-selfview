"""Throwaway: find the true body base by decompressing candidate buffers."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import _lz4_frame

P = r"D:\projects\science\malecns\body-annotations.feather"
with open(P, "rb") as fh:
    data = fh.read(8000)

# declared metadata len at 6732
meta_len = struct.unpack_from("<i", data, 6732)[0]
print("declared meta_len =", meta_len, " -> body_start would be", 6736 + meta_len)

for base in (6900, 6908, 6912, 6916, 6918, 6920, 6924):
    print("\n=== candidate body_start = %d" % base)
    for name, off, ln in (("validity", 0, 0), ("offsets", 146, 146), ("data", 152, 348)):
        p = base + off
        raw = bytes(data[p:p + ln])
        if not ln:
            print("   %-8s [%d..%d) empty" % (name, p, p))
            continue
        declared = struct.unpack_from("<q", raw, 0)[0]
        magic = raw[8:12].hex()
        info = "len=%d prefix=%d magic=%s" % (ln, declared, magic)
        if magic == "04224d18":
            try:
                dec = _lz4_frame(raw[8:])
                info += " -> decompressed %d bytes" % len(dec)
                if name == "offsets":
                    ints = struct.unpack_from("<%di" % (len(dec) // 4), dec, 0)
                    info += " first ints=%s" % (ints[:8],)
                else:
                    info += " text=%r" % dec[:40]
            except Exception as e:
                info += " -> lz4 FAILED %s" % e
        print("   %-8s [%d..%d) %s" % (name, p, p + ln, info))
