"""Exhaustive check: does ANY codec at ANY reasonable page-payload offset turn the
first parquet dictionary page into the expected bytes? Settles whether the file's
page bodies are readable at all."""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parquet_lite as P

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
rgs, _ = P._open_meta(path)
col = rgs[0].columns[0]
f = open(path, "rb")
f.seek(col.dict_page_offset)
buf = f.read(1 << 20)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
target = ph.get(2)
comp = ph.get(3)
print("page: header=%d compressed=%d uncompressed=%d" % (r.i, comp, target))

from compression import zstd

def snappy_raw(d):
    out = bytearray(); pos = 0
    while pos < len(d) and len(out) < target:
        tag = d[pos]; pos += 1
        kind = tag & 3; ln = tag >> 2
        if kind == 0:
            if ln >= 60:
                extra = ln - 59; ln = int.from_bytes(d[pos:pos+extra], "little"); pos += extra
            ln += 1; out += d[pos:pos+ln]; pos += ln
        else:
            if kind == 1:
                ln = ((tag >> 2) & 7) + 4; offset = ((tag >> 5) << 8) | d[pos]; pos += 1
            elif kind == 2:
                ln = (tag >> 2) + 1; offset = int.from_bytes(d[pos:pos+2], "little"); pos += 2
            else:
                ln = (tag >> 2) + 1; offset = int.from_bytes(d[pos:pos+4], "little"); pos += 4
            if offset == 0 or offset > len(out):
                raise ValueError("offset")
            start = len(out) - offset
            out += out[start:start+ln] if ln <= offset else bytes(out[start+k] for k in range(ln))
    return bytes(out)

hits = []
for skip in range(r.i, r.i + 12):
    payload = buf[skip:skip + comp]
    for name, fn in (("lz4", lambda d: P._lz4_block_decompress(d, target)),
                     ("snappy", snappy_raw),
                     ("zstd", zstd.decompress),
                     ("plain", lambda d: d[:target])):
        try:
            out = fn(payload)
            if len(out) != target:
                continue
            vals = struct.unpack_from("<4q", out, 0)
            plausible = all(7.2e16 < v < 7.3e16 for v in vals if v > 0)
            hits.append((skip, name, len(out), plausible, [hex(v) for v in vals[:2]]))
        except Exception:
            pass

if hits:
    for h in hits:
        print("  HIT skip=%d %s out=%d plausible_ids=%s first=%s" % h)
else:
    print("  no codec/offset combination yields %d plausible bytes -> page bodies are not readable" % target)

# also: do the two independent downloads differ anywhere in this region?
other = path.replace(".parquet", ".http.parquet")
if os.path.exists(other):
    a = open(path, "rb").read(4 << 20)
    b = open(other, "rb").read(4 << 20)
    print("  first 4MB identical between the two downloads:", a == b)
