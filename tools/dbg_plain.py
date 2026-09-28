import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
f.seek(16712)
buf = f.read(60000)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
print("header:", {k: v for k, v in ph.items() if k != 5})
print("data page header:", ph.get(5))
payload = buf[r.i:r.i+ph.get(2)]
# hypothesis A: payload = def levels(RLE, 4-byte len) + dictionary indices (bit-packed RLE)
ln = struct.unpack_from("<I", payload, 0)[0]
print("A: level blob len =", ln)
# hypothesis B: payload is plain INT64 values (codec effectively none)
vals = struct.unpack_from("<8q", payload, 0)
print("B: first int64s:", [hex(v) for v in vals])
print("   plausible flywire ids?", all(7.2e16 < v < 7.3e16 for v in vals if v > 0))
# hypothesis C: plain after skipping some bytes
for skip in (0, 4, 8, 16):
    v = struct.unpack_from("<4q", payload, skip)
    print("C skip=%d:" % skip, [hex(x) for x in v])
