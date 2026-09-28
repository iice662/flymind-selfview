import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
f.seek(4); buf = f.read(20000)
r = P._Reader(buf, 0); ph = P._read_struct(r)
payload = buf[r.i:r.i+ph.get(3)]
try:
    out = P._snappy_decompress(payload)
    print("snappy OK -> %d bytes" % len(out))
    vals = struct.unpack_from("<6q", out, 0)
    print("first int64s:", [hex(v) for v in vals])
    print("plausible ids:", all(7.2e16 < v < 7.3e16 for v in vals))
except Exception as e:
    print("snappy fail:", e)
