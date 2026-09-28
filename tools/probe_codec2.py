import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
from compression import zstd
for path, name in ((r"D:\projects\science\drosophila-brain-model\sugarR.parquet", "sugarR"),
                   (r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet", "connectivity")):
    rgs, _ = P._open_meta(path)
    col = rgs[0].columns[0]
    f = open(path, "rb")
    for label, off in (("dict", col.dict_page_offset), ("data", col.data_page_offset)):
        if not off: continue
        f.seek(off)
        buf = f.read(1 << 16)
        r = P._Reader(buf, 0)
        ph = P._read_struct(r)
        comp = ph.get(3); payload = buf[r.i:r.i + comp]
        print("%s %s page: hdrlen=%d type=%s uncomp=%s comp=%s payload[:8]=%s" % (
            name, label, r.i, ph.get(1), ph.get(2), comp, payload[:8].hex()))
        for cname, fn in (("zstd", lambda d: zstd.decompress(d)),
                          ("snappy", P._snappy_decompress),
                          ("lz4", lambda d: P._lz4_block_decompress(d, ph.get(2))),
                          ("brotli?", None)):
            if fn is None: continue
            try:
                out = fn(payload)
                print("     %-7s OK -> %d bytes (expected %s)" % (cname, len(out), ph.get(2)))
            except Exception as e:
                print("     %-7s fail: %s" % (cname, str(e)[:52]))
        # what does the column metadata say?
        md = rgs[0].columns[0]
        print("     codec field =", md.codec, " physical =", md.physical, " total_compressed =", md.total_compressed_size)
