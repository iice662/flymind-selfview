import struct
import sys

path = sys.argv[1]
data = open(path, "rb").read(4096)
print("bytes 32..96:", data[32:96].hex())
print("bytes 32..96 as chars:", "".join(chr(b) if 32 <= b < 127 else "." for b in data[32:96]))

def show(p, label):
    soff = struct.unpack_from("<i", data, p)[0]
    vt = p - soff
    if not (0 <= vt < len(data) - 4):
        print("  %s @%d: vtable out of range (soff=%d)" % (label, p, soff))
        return
    vlen = struct.unpack_from("<H", data, vt)[0]
    nf = (vlen - 4) // 2
    print("  %s @%d: soff=%d vtable@%d vlen=%d fields=%d" % (label, p, soff, vt, vlen, nf))
    if not (4 <= vlen <= 40):
        print("     raw @%d: %s" % (p, data[p:p+32].hex()))
        return
    for k in range(nf):
        voff = struct.unpack_from("<H", data, vt + 4 + 2 * k)[0]
        if not voff:
            print("     f%d absent" % k)
            continue
        at = p + voff
        raw = data[at:at + 12]
        u32 = struct.unpack_from("<I", raw)[0]
        i8 = struct.unpack_from("<b", raw)[0]
        print("     f%d @%d raw=%s u32=%d i8=%d -> target %d" % (k, at, raw[:8].hex(), u32, i8, at + u32))

show(56, "candidate schema")
# search for a plausible table in the first 4KB: soff in 4..64, vlen even 4..32
print("plausible tables in first 4KB:")
found = 0
for p in range(4, 4000, 2):
    soff = struct.unpack_from("<i", data, p)[0]
    if not (4 <= soff <= 200):
        continue
    vt = p - soff
    if vt < 0:
        continue
    vlen = struct.unpack_from("<H", data, vt)[0]
    if vlen in (4, 6, 8, 10, 12, 14, 16, 18, 20):
        print("   @%d soff=%d vlen=%d fields=%d" % (p, soff, vlen, (vlen - 4) // 2))
        found += 1
        if found > 12:
            break
