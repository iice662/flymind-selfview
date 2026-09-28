import struct
import sys
import os

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read()
print("size:", len(data), "tail:", data[-10:].hex())
footer_len = struct.unpack_from("<i", data, len(data) - 10)[0]
print("footer_len:", footer_len)
for cand_name, cand in (("end-10-len", len(data) - 10 - footer_len),
                        ("at 8", 8),
                        ("end-10", len(data) - 10)):
    if 0 <= cand <= len(data) - 4:
        head = struct.unpack_from("<I", data, cand)[0]
        print("  candidate %-12s @%d first u32=%d (as table rel: %d)" % (cand_name, cand, head, cand + head))
# brute force: find a uoffset position p where table@p+u32 is inside the file and
# the vtable looks sane (soff>0, vlen in 4..64)
best = []
for p in range(max(0, len(data) - 20000), len(data) - 4, 4):
    u = struct.unpack_from("<I", data, p)[0]
    tp = p + u
    if tp + 4 >= len(data) or u == 0:
        continue
    soff = struct.unpack_from("<i", data, tp)[0]
    vt = tp - soff
    if vt < 0 or vt + 4 >= len(data) or soff <= 0:
        continue
    vlen = struct.unpack_from("<H", data, vt)[0]
    if 4 <= vlen <= 64 and vlen % 2 == 0:
        nfields = (vlen - 4) // 2
        offs = [struct.unpack_from("<H", data, vt + 4 + 2 * k)[0] for k in range(nfields)]
        if nfields == 4 and all(o > 0 for o in offs):
            best.append((p, u, tp, vlen, offs))
print("footer root candidates (nfields=4):")
for b in best[:6]:
    print("   p=%d uoff=%d table@%d vlen=%d fieldoffs=%s" % b)
    tp = b[2]
    for k, o in enumerate(b[4]):
        raw = data[tp + o:tp + o + 8]
        print("      field %d raw=%s as u32=%s" % (k, raw.hex(), struct.unpack_from("<I", data, tp + o)[0]))
