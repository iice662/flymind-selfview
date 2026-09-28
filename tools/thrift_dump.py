"""Fully generic thrift-compact dumper: shows every field with its type and value,
so the real byte layout of a parquet page header is visible instead of inferred."""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TYPES = {0: "STOP", 1: "TRUE", 2: "FALSE", 3: "BYTE", 4: "I16", 5: "I32", 6: "I64",
         7: "DOUBLE", 8: "BINARY", 9: "LIST", 10: "SET", 11: "MAP", 12: "STRUCT"}


def dump(buf, pos, indent=0, max_depth=6, label=""):
    pad = "  " * indent
    last = 0
    while pos < len(buf):
        h = buf[pos]
        pos += 1
        ttype = h & 0x0F
        delta = (h >> 4) & 0x0F
        if ttype == 0:
            print("%s%sSTOP @%d" % (pad, label, pos - 1))
            return pos
        if delta:
            fid = last + delta
        else:
            v, pos = varint(buf, pos)
            fid = (v >> 1) ^ -(v & 1)
        last = fid
        info = "f%-3d %-6s" % (fid, TYPES.get(ttype, "?"))
        if ttype in (1, 2):
            print("%s%s = %s" % (pad, info, ttype == 1))
        elif ttype == 3:
            b = buf[pos]; pos += 1
            print("%s%s = %d" % (pad, info, struct.unpack("b", bytes([b]))[0]))
        elif ttype in (4, 5, 6):
            v, pos = varint(buf, pos)
            print("%s%s = %d" % (pad, info, (v >> 1) ^ -(v & 1)))
        elif ttype == 7:
            v = struct.unpack_from("<d", buf, pos)[0]; pos += 8
            print("%s%s = %g" % (pad, info, v))
        elif ttype == 8:
            n, pos = varint(buf, pos)
            s = buf[pos:pos + n]; pos += n
            print("%s%s len=%d %r" % (pad, info, n, s[:24]))
        elif ttype in (9, 10):
            hh = buf[pos]; pos += 1
            size = (hh >> 4) & 0x0F
            etype = hh & 0x0F
            if size == 15:
                size, pos = varint(buf, pos)
            print("%s%s list<%-6s> size=%d" % (pad, info, TYPES.get(etype, "?"), size))
            for i in range(size):
                if etype == 12 and indent < max_depth:
                    pos = dump(buf, pos, indent + 2, max_depth, "elem%d " % i)
                elif etype in (4, 5, 6):
                    v, pos = varint(buf, pos)
                    print("%s  [%d] = %d" % (pad, i, (v >> 1) ^ -(v & 1)))
                elif etype == 8:
                    n, pos = varint(buf, pos)
                    print("%s  [%d] = %r" % (pad, i, buf[pos:pos + n][:16])); pos += n
                else:
                    print("%s  [%d] type %s unhandled" % (pad, i, TYPES.get(etype)))
        elif ttype == 12:
            print("%s%s struct:" % (pad, info))
            if indent < max_depth:
                pos = dump(buf, pos, indent + 1, max_depth)
            else:
                return pos
        elif ttype == 11:
            size, pos = varint(buf, pos)
            print("%s%s map size=%d" % (pad, info, size))
            for _ in range(size):
                if pos < len(buf):
                    hh = buf[pos]; pos += 1
                    kt, vt = (hh >> 4) & 0xF, hh & 0xF
                    _, pos = varint(buf, pos)
                    _, pos = varint(buf, pos)
        else:
            print("%s%s UNHANDLED type %d at %d" % (pad, info, ttype, pos))
            return pos
    return pos


def varint(buf, pos):
    shift = 0
    result = 0
    while True:
        c = buf[pos]; pos += 1
        result |= (c & 0x7F) << shift
        if not (c & 0x80):
            return result, pos
        shift += 7


if __name__ == "__main__":
    path = sys.argv[1]
    offset = int(sys.argv[2])
    length = int(sys.argv[3]) if len(sys.argv) > 3 else 256
    with open(path, "rb") as f:
        f.seek(offset)
        buf = f.read(length)
    print("== %s @%d ==" % (os.path.basename(path), offset))
    print("bytes:", buf[:min(96, len(buf))].hex())
    dump(buf, 0)
