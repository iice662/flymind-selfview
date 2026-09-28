import sys, os
sys.path.insert(0, os.getcwd())
import parquet_lite as P
from compression import zstd
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
rgs, leaves = P._open_meta(p)
col = rgs[0].columns[0]
print("col:", col.name, "phys", col.physical, "codec", col.codec, "nvals", col.num_values,
      "data_off", col.data_page_offset, "dict_off", col.dict_page_offset)
f = open(p, "rb")
for off in (col.dict_page_offset, col.data_page_offset, 4):
    if not off: continue
    f.seek(off)
    head = f.read(24)
    print("offset %d: %s" % (off, head.hex()))
# try parsing a page header at data_page_offset
f.seek(col.data_page_offset)
buf = f.read(4 << 20)
r = P._Reader(buf, 0)
try:
    ph = P._read_struct(r)
    print("page header:", {k: (v if not isinstance(v, bytes) else v[:20]) for k, v in ph.items()})
    print("consumed bytes:", r.i)
except Exception as e:
    print("header parse failed:", e)
