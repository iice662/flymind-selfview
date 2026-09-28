import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
from compression import zstd
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
rgs, leaves = P._open_meta(p)
col = rgs[0].columns[0]
f = open(p, "rb")
for page_offset in sorted({col.data_page_offset, col.dict_page_offset or col.data_page_offset}):
    f.seek(page_offset)
    buf = f.read(3 << 20)
    r = P._Reader(buf, 0)
    ph = P._read_struct(r)
    print("offset=%d ptype=%s uncomp=%s comp=%s hdrlen=%d" % (page_offset, ph.get(1), ph.get(2), ph.get(2), r.i))
    comp_size = ph.get(2)
    raw = buf[r.i:r.i+comp_size]
    print("  first 8 payload bytes:", raw[:8].hex())
    try:
        out = zstd.decompress(raw)
        print("  zstd OK ->", len(out), "bytes")
    except Exception as e:
        print("  zstd FAIL:", e)
        # maybe the payload is uncompressed despite codec flag
        print("  (raw len %d) header of payload as thrift? first bytes %s" % (len(raw), raw[:16].hex()))
