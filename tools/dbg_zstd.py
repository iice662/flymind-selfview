import sys, os
sys.path.insert(0, os.getcwd())
import parquet_lite as P
from compression import zstd
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
f.seek(16712)
buf = f.read(60000)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
payload = buf[r.i:r.i+ph.get(2)]
D = zstd.ZstdDecompressor()
for name, data in (("payload", payload), ("no-head", payload[10:])):
    try:
        out = D.decompress(data, max_length=200000)
        print(name, "stream_reader OK ->", len(out), out[:16].hex())
    except Exception as e:
        print(name, "stream fail:", e)
# check zstd frame header bytes manually
b = payload
print("frame header magic:", b[:4].hex(), "FHD:", hex(b[4]))
print("window descriptor:", hex(b[5]), "dict id flag:", (b[4]>>0)&3)
