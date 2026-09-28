import sys, os
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
meta = P._read_footer(p)
for i, cc in enumerate(meta[4][0][1][:3]):
    md = cc[3]
    print("== col", i)
    for k in sorted(md):
        v = md[k]
        if isinstance(v, bytes):
            v = v[:24].hex()
        if isinstance(v, list) and v and isinstance(v[0], dict):
            v = ["{k=%s v=%s}" % (sorted(d.items())) for d in v][:3]
        print("   field %-3s = %s" % (k, v))
