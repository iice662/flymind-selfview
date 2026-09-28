import struct
import sys

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read()

def dump_table(pos, label, depth=0):
    pad = "  " * depth
    if pos + 4 > len(data):
        print("%s%s @%d OUT OF RANGE" % (pad, label, pos))
        return
    soff = struct.unpack_from("<i", data, pos)[0]
    vt = pos - soff
    ok = 0 <= vt < len(data) - 2
    vlen = struct.unpack_from("<H", data, vt)[0] if ok else -1
    print("%s%s @%d soff=%d vtable@%d vlen=%s %s" % (
        pad, label, pos, soff, vt, vlen, "" if (ok and 4 <= vlen <= 64) else "<-- not a table?"))
    if not ok or not (4 <= vlen <= 64):
        print("%s   bytes: %s" % (pad, data[pos - 8:pos + 24].hex()))
        return
    nf = (vlen - 4) // 2
    for k in range(nf):
        voff = struct.unpack_from("<H", data, vt + 4 + 2 * k)[0]
        if voff == 0:
            continue
        raw = data[pos + voff:pos + voff + 8]
        u = struct.unpack_from("<I", raw, 0)[0]
        i64 = struct.unpack_from("<q", raw, 0)[0]
        print("%s   f%d voff=%-4d raw=%s u32=%-12d i64=%-20d target=%d" % (
            pad, k, voff, raw[:6].hex(), u, i64, pos + voff + u))

print("== frame byte layout ==")
print("  [0:8]  ", data[0:8])
print("  [8:12] ", data[8:12].hex(), "= continuation marker" if data[8:12] == b"\xff\xff\xff\xff" else "")
mlen = struct.unpack_from("<i", data, 12)[0]
print("  [12:16]", data[12:16].hex(), "= metadata length", mlen)
msg_pos = 16
print("== root message table @%d ==" % msg_pos)
dump_table(msg_pos, "Message", 1)
# interpret as if it were a flatbuffer whose uoffset is at msg_pos
u = struct.unpack_from("<I", data, msg_pos)[0]
print("== as uoffset: %d -> table @%d ==" % (u, msg_pos + u))
dump_table(msg_pos + u, "Message(root)", 1)
