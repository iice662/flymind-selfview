import sys, os, time
sys.path.insert(0, os.getcwd())
import parquet_lite as P
t0=time.time()
for b in P.read_parquet(r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet", batch_rows=8):
    for k,v in b.items():
        print(k, v[:8])
    break
print("elapsed %.1fs" % (time.time()-t0))
