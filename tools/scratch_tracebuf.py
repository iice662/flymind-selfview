"""Throwaway: trace buffer consumption in _read_batch for batch 0."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
import feather_lite as FL
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\body-annotations.feather"

orig = FeatherFile._read_batch
def traced(self, batch, body_start, dicts, strict=True):
    print("=== _read_batch body_start=%d nodes=%d buffers=%d"
          % (body_start, batch.vector_len(1), batch.vector_len(2)))
    global N
    return orig(self, batch, body_start, dicts, strict)
FeatherFile._read_batch = traced

f = FeatherFile(P)
# monkeypatch take_buffer indirectly: wrap vector_struct_i64 to log buffer reads
orig_vs = FL.Table.vector_struct_i64
count = {"n": 0}
def vs(self, fi, index, size, field_offset):
    v = orig_vs(self, fi, index, size, field_offset)
    if fi == 2 and field_offset == 8:
        print("   buffer[%d].length = %d" % (index, v))
    return v
FL.Table.vector_struct_i64 = vs

for k, batch in enumerate(f.iter_batches()):
    print("batch %d: %s" % (k, {n: len(v) for n, v in batch.items()}))
    break
