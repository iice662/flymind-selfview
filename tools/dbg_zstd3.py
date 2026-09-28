import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
from compression import zstd
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
regions = []
f.seek(4); regions.append(("dict", f.read(20000)))
f.seek(16712); regions.append(("data", f.read(30000)))
for name, buf in regions:
    r = P._Reader(buf, 0)
    ph = P._read_struct(r)
    payload = buf[r.i:r.i+ph.get(3)]
    d = zstd.ZstdDecompressor()
    for label, data in (("payload", payload), ("minus1", payload[1:]), ("minus2", payload[2:]), ("minus4", payload[4:])):
        try:
            out = d.decompress(data, max_length=1000000)
            print("%s/%s: OK -> %d bytes %s" % (name, label, len(out), out[:16].hex()))
            break
        except Exception as e:
            print("%s/%s: %s" % (name, label, str(e)[:60]))
