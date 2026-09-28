"""Decode a parquet page payload as a raw Snappy block (no preamble) and check that
the result looks like real column data."""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parquet_lite as P


def snappy_block(data, limit=None):
    out = bytearray()
    pos = 0
    n = len(data)
    while pos < n and (limit is None or len(out) < limit):
        tag = data[pos]
        pos += 1
        kind = tag & 0x03
        ln = tag >> 2
        if kind == 0:
            if ln >= 60:
                extra = ln - 59
                ln = int.from_bytes(data[pos:pos + extra], "little")
                pos += extra
            ln += 1
            out += data[pos:pos + ln]
            pos += ln
        else:
            if kind == 1:
                ln = ((tag >> 2) & 0x07) + 4
                offset = ((tag >> 5) << 8) | data[pos]
                pos += 1
            elif kind == 2:
                ln = (tag >> 2) + 1
                offset = int.from_bytes(data[pos:pos + 2], "little")
                pos += 2
            else:
                ln = (tag >> 2) + 1
                offset = int.from_bytes(data[pos:pos + 4], "little")
                pos += 4
            if offset == 0 or offset > len(out):
                raise ValueError("bad offset %d at out=%d (pos=%d)" % (offset, len(out), pos))
            start = len(out) - offset
            if ln <= offset:
                out += out[start:start + ln]
            else:
                for k in range(ln):
                    out.append(out[start + k])
    return bytes(out)


def try_file(path, col_index=0, row_group=0):
    rgs, _ = P._open_meta(path)
    col = rgs[row_group].columns[col_index]
    f = open(path, "rb")
    start = col.dict_page_offset or col.data_page_offset
    f.seek(start)
    buf = f.read(1 << 20)
    r = P._Reader(buf, 0)
    ph = P._read_struct(r)
    expected = ph.get(2)
    payload = buf[r.i:r.i + ph.get(3)]
    print("== %s: %s (phys %s, expected %d bytes)" % (
        os.path.basename(path), col.name, col.physical, expected))
    try:
        out = snappy_block(payload, expected)
        print("   decoded %d bytes (expected %d) %s" % (
            len(out), expected, "OK" if len(out) == expected else "SIZE MISMATCH"))
        if col.physical == 2:      # INT64
            vals = struct.unpack_from("<6q", out, 0)
            print("   first int64:", [hex(v) for v in vals])
            print("   flywire-id-looking:", all(7.2e16 < v < 7.3e16 for v in vals if v > 0))
        elif col.physical == 5:    # DOUBLE
            print("   first doubles:", ["%.4f" % v for v in struct.unpack_from("<6d", out, 0)])
        elif col.physical == 1:    # INT32
            print("   first int32:", struct.unpack_from("<8i", out, 0))
        return True
    except Exception as e:
        print("   snappy block decode failed: %s" % e)
        return False


if __name__ == "__main__":
    okc = 0
    for p in sys.argv[1:]:
        for ci in (0, 3, 4):
            try:
                if try_file(p, ci):
                    okc += 1
            except Exception as e:
                print("   (column %d skipped: %s)" % (ci, e))
    print("decodable: %d" % okc)
