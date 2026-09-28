"""Throwaway: instrument take_buffer directly to find the desync."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
import feather_lite as FL

P = r"D:\projects\science\malecns\body-annotations.feather"

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
# insert a print inside take_buffer
needle = """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert needle in src
patched = src.replace(needle, """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            print("      take_buffer #%d off=%d len=%d node_i=%d" % (buf_i[0], off, ln, node_i[0]))
            buf_i[0] += 1""")
ns = {"__name__": "feather_dbg"}
exec(compile(patched, "feather_lite_dbg", "exec"), ns)
FeatherFile = ns["FeatherFile"]

f = FeatherFile(P)
for k, batch in enumerate(f.iter_batches()):
    print("batch %d ok: %s" % (k, {n: len(v) for n, v in batch.items()}))
    break
