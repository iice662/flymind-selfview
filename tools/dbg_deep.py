import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
from compression import zstd
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
data = open(p, "rb").read()
print("file bytes:", len(data))
for name, magic in (("zstd", "28b52ffd"), ("lz4-frame", "04224d18"), ("lz4-skippable", "502a4d18"),
                    ("snappy-stream", "ff060000734e61507059"), ("gzip", "1f8b")):
    m = bytes.fromhex(magic)
    idx = data.find(m)
    cnt = 0
    pos = 0
    while pos != -1 and cnt < 3:
        pos = data.find(m, pos)
        if pos == -1: break
        cnt += 1; pos += 1
    print("  %-15s first at %s (total scanned hits shown: %d)" % (name, idx, cnt))
# try lz4 decompression at every plausible header length for the first dict page
f = open(p, "rb"); f.seek(4)
buf = f.read(1 << 16)
r = P._Reader(buf, 0); ph = P._read_struct(r)
print("page:", {k: v for k, v in ph.items()})
target = ph.get(2); comp = ph.get(3)
found = []
for skip in range(r.i, r.i + 8):
    for endextra in (0, -0):
        payload = buf[skip:skip + comp + endextra]
        try:
            out = P._lz4_block_decompress(payload, target)
            found.append((skip, len(out)))
        except Exception:
            pass
print("lz4 hits:", found)
# zstd with unknown-content-size streaming
try:
    d = zstd.ZstdDecompressor()
    for skip in range(r.i, r.i + 8):
        try:
            with d.stream_reader(buf[skip:skip + comp]) as sr:
                out = sr.read()
            print("  zstd stream from skip=%d -> %d bytes" % (skip, len(out)))
            break
        except Exception as e:
            pass
except Exception as e:
    print("zstd reader err", e)
