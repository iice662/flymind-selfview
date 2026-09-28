import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
from compression import zstd
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
f.seek(4)
buf = f.read(1 << 16)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
print("header len =", r.i, "bytes:", buf[:r.i].hex())
comp = ph.get(3); target = ph.get(2)
payload = buf[r.i:r.i + comp]
print("payload:", len(payload), "expected out:", target)
try:
    out = zstd.decompress(payload)
    print("*** ZSTD OK ->", len(out), "bytes")
    vals = struct.unpack_from("<8q", out, 0)
    print("    first int64:", [hex(v) for v in vals[:4]])
    print("    plausible FlyWire ids:", all(7.2e16 < v < 7.3e16 for v in vals))
except Exception as e:
    print("zstd fail:", e)
