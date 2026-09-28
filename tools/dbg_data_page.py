import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
start = 16712
f.seek(start)
buf = f.read(1 << 16)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
print("hdr len", r.i, "parsed:", {k: v for k, v in ph.items() if k != 4})
print("data page header:", ph.get(4))
comp = ph.get(3); payload = buf[r.i:r.i+comp]
print("payload first 12:", payload[:12].hex())
# hypothesis: payload is deflate-wrapped-lz4 = "lz4 hadoop"? try deflate on payload
import zlib
for name, fn in (("deflate", lambda d: zlib.decompress(d, -15)),
                 ("zlib", zlib.decompress),
                 ("gzip", lambda d: zlib.decompress(d, 16+15))):
    try:
        out = fn(payload); print("  %s -> %d bytes" % (name, len(out)))
    except Exception as e:
        print("  %s fail" % name)
# hypothesis: raw uncompressed page (codec mislabeled) -> parse as def levels + RLE dict indices
ln = struct.unpack_from("<I", payload, 0)[0]
print("as RLE level blob, length prefix =", ln, "payload len =", len(payload))
