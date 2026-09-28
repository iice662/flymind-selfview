import sys, os, struct, time
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\sugarR.parquet"
print("== sugarR.parquet ==")
rgs, leaves = P._open_meta(p)
print("leaves:", [l[-1] for l in leaves], "row groups:", len(rgs), "rows:", sum(rg.num_rows for rg in rgs))
col = rgs[0].columns[0]
print("col0:", col.name, "phys", col.physical, "codec", col.codec, "nvals", col.num_values,
      "dict_off", col.dict_page_offset, "data_off", col.data_page_offset)
t0 = time.time()
try:
    for b in P.read_parquet(p, batch_rows=5):
        for k, v in b.items():
            print("   %-16s %s" % (k, v[:5]))
        break
    print("decode OK in %.1fs" % (time.time()-t0))
except Exception as e:
    print("decode FAIL: %s" % e)
