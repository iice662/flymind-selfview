"""Throwaway baseline: connectome-weights.feather first two batches."""
import sys, time
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\connectome-weights.feather"
t0 = time.time()
f = FeatherFile(P)
print("open %.1fs" % (time.time() - t0))
print("fields:", f.schema_summary())
print("batches:", len(f.record_batches))
t0 = time.time()
for k, batch in enumerate(f.iter_batches()):
    print("batch %d: %s" % (k, {n: (len(v), v[:5]) for n, v in batch.items()}))
    if k >= 1:
        break
print("decode %.1fs" % (time.time() - t0))
