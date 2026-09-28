import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.http.parquet"
try:
    rgs, leaves = P._open_meta(p)
    print("footer OK; leaves:", [l[-1] for l in leaves][:8])
except Exception as e:
    print("footer not readable yet:", e); sys.exit()
col = rgs[0].columns[0]
f = open(p, "rb")
f.seek(col.dict_page_offset or col.data_page_offset)
buf = f.read(1 << 16)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
comp = ph.get(3)
payload = buf[r.i:r.i+comp]
print("page type=%s uncomp=%s comp=%s payload=%d" % (ph.get(1), ph.get(2), comp, len(payload)))
for label, fn in (("lz4", P._lz4_block_decompress), ("snappy", P._snappy_decompress)):
    try:
        out = fn(payload, ph.get(2)) if label == "lz4" else fn(payload)
        ids = struct.unpack_from("<4q", out, 0)
        print("  %s OK -> %d bytes, first ids %s" % (label, len(out), [hex(v) for v in ids]))
    except Exception as e:
        print("  %s fail: %s" % (label, str(e)[:60]))
