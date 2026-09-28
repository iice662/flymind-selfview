import sys, os
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
rgs, leaves = P._open_meta(p)
print("row groups:", len(rgs))
ok = bad = 0
samples = []
f = open(p, "rb")
for gi in (0, 1, 3, 7, 11, 14):
    if gi >= len(rgs): continue
    rg = rgs[gi]
    for ci in (0, 4):          # Presynaptic_ID and the weight column
        col = rg.columns[ci]
        start = col.dict_page_offset or col.data_page_offset
        f.seek(start)
        buf = f.read(1 << 16)
        r = P._Reader(buf, 0)
        ph = P._read_struct(r)
        payload = buf[r.i:r.i + ph.get(3)]
        try:
            out = P._lz4_block_decompress(payload, ph.get(2))
            ok += 1
            samples.append("rg%d col%d LZ4 OK -> %d bytes" % (gi, ci, len(out)))
        except Exception as e:
            bad += 1
            samples.append("rg%d col%d LZ4 FAIL (%s)" % (gi, ci, str(e)[:40]))
for s in samples: print("  ", s)
print("decodable pages: %d, undecodable: %d" % (ok, bad))
