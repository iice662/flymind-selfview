import time, sys, os
sys.path.insert(0, os.getcwd())
import parquet_lite as P
t0 = time.time()
rgs, leaves = P._open_meta(r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet")
print("leaves:", [l[-1] for l in leaves])
print("row groups:", len(rgs), "rows:", sum(rg.num_rows for rg in rgs))
for rg in rgs[:3]:
    for c in rg.columns:
        print("  col=%-32s phys=%s codec=%s nvals=%s" % (c.name, c.physical, c.codec, c.num_values))
    break
