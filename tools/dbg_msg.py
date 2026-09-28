import struct
import sys

for path in sys.argv[1:]:
    data = open(path, "rb").read(1 << 20)
    print("== %s (first MB)" % path.split("\\")[-1])
    print("   head:", data[:24].hex())
    if data[:6] != b"ARROW1":
        print("   not arrow")
        continue
    pos = 8
    first = struct.unpack_from("<I", data, pos)[0]
    if first == 0xFFFFFFFF:
        mlen = struct.unpack_from("<i", data, pos + 4)[0]
        mstart = pos + 8
    else:
        mlen = struct.unpack_from("<i", data, pos)[0]
        mstart = pos + 4
    print("   message meta: start=%d len=%d" % (mstart, mlen))
    u = struct.unpack_from("<I", data, mstart)[0]
    tpos = mstart + u
    soff = struct.unpack_from("<i", data, tpos)[0]
    vt = tpos - soff
    vlen = struct.unpack_from("<H", data, vt)[0]
    nf = (vlen - 4) // 2
    print("   Message table @%d vtable@%d vlen=%d fields=%d" % (tpos, vt, vlen, nf))
    for k in range(nf):
        voff = struct.unpack_from("<H", data, vt + 4 + 2 * k)[0]
        if not voff:
            print("      f%d absent" % k)
            continue
        at = tpos + voff
        raw = data[at:at + 12]
        as_i8 = struct.unpack_from("<b", raw)[0]
        as_i16 = struct.unpack_from("<h", raw)[0]
        as_i32 = struct.unpack_from("<i", raw)[0]
        as_u32 = struct.unpack_from("<I", raw)[0]
        tgt = at + as_u32
        print("      f%d @%d raw=%s i8=%d i16=%d i32=%d u32=%d -> target %d" % (
            k, at, raw[:8].hex(), as_i8, as_i16, as_i32, as_u32, tgt))
