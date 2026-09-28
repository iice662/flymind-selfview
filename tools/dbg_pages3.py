import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
from compression import zstd
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
for start in (4, 16712):
    f.seek(start)
    buf = f.read(400000)
    r = P._Reader(buf, 0)
    ph = _ = P._read_struct(r)
    print("== at %d: type=%s uncomp=%s comp=%s hdrlen=%d other fields=%s" % (
        start, ph.get(1), ph.get(2), ph.get(3), r.i, sorted(k for k in ph if k not in (1,2,3))))
    comp = ph.get(3) or ph.get(2)
    payload = buf[r.i:r.i+comp]
    print("   payload[:8]:", payload[:8].hex())
    try:
        out = zstd.decompress(payload)
        print("   zstd OK ->", len(out), "bytes; first int64s:", [hex(x) for x in struct.unpack_from("<4q", out, 0)])
    except Exception as e:
        print("   zstd fail:", e)
    if 4 in ph: print("   DATA page header:", ph[4])
    if 7 in ph: print("   DICT page header:", ph[7])
    if 8 in ph: print("   DATA_V2 header:", ph[8])
