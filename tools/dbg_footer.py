import sys, os
sys.path.insert(0, os.getcwd())
import parquet_lite as P
meta = P._read_footer(r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet")
print("version field(1):", meta.get(1), "num_rows(3):", meta.get(3))
se = meta[2]
print("schema field type:", type(se), "len:", len(se))
if isinstance(se, list):
    print("first elem:", {k: (v.decode() if isinstance(v, bytes) else v) for k, v in se[0].items()})
    print("second elem:", {k: (v.decode() if isinstance(v, bytes) else v) for k, v in se[1].items()})
    for el in se:
        nm = el.get(3)
        print("   children=%s name=%s type=%s" % (el.get(2), nm.decode() if isinstance(nm, bytes) else nm, el.get(1)))
else:
    print("schema dict keys:", sorted(se.keys()))
