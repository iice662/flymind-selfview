import sys, os, struct, zlib
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
f.seek(16712)
buf = f.read(60000)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
comp = ph.get(2); payload = buf[r.i:r.i+comp]
print("compressed_page_size =", comp, " first bytes:", payload[:16].hex())
# try gzip/zlib/deflate
for name, fn in (("zlib", lambda d: zlib.decompress(d)),
                 ("raw-deflate", lambda d: zlib.decompress(d, -15)),
                 ("gzip", lambda d: zlib.decompress(d, 16+15))):
    try:
        out = fn(payload); print("  %s OK -> %d bytes" % (name, len(out)))
    except Exception as e:
        print("  %s fail: %s" % (name, e))
# thrift-compact plausibility of the payload as a definition-level blob:
# first 4 bytes little-endian length prefix
ln = struct.unpack_from("<I", payload, 0)[0]
print("  first uint32 as RLE length prefix:", ln, "(plausible if <= %d)" % comp)
# LZ4 raw block check: first 4 bytes as token
print("  lz4? token byte:", payload[0], "literal len:", payload[0] >> 4)
