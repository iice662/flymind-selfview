import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
for hdr_abs, uncomp in ((16712, 24895), (4, 77504)):
    f.seek(hdr_abs)
    buf = f.read(1 << 16)
    hits = []
    for skip in range(20, 130):
        payload = buf[skip:skip + 40000]
        try:
            out = P._lz4_block_decompress(payload, uncomp)
            hits.append(skip)
        except Exception:
            pass
    print("header at %d: lz4 succeeds when payload starts at rel offset %s" % (hdr_abs, hits[:5]))
