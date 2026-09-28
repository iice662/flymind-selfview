"""Throwaway: sequence of buffer reads for somaLocation with phase labels."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":', 'if False:')
open(r"D:\projects\science\tools\scratch_inst7.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("i7", r"D:\projects\science\tools\scratch_inst7.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
# reach in: wrap take_buffer behaviour by patching vector_struct_i64 is messy;
# instead re-implement the walk using the library's own Table objects.
msg, body_start = f._message_at(f.record_batches[0][0])
rb = msg.table(2)
n_bufs = rb.vector_len(2)
bufs = [(rb.vector_struct_i64(2, i, 16, 0), rb.vector_struct_i64(2, i, 16, 8)) for i in range(n_bufs)]
print("body_start =", body_start)
print("somaLocation subtree should own buffers:", )
# print owner mapping by simulating the exact field walk
node_i = 0
buf_i = 0
for fl in f.fields:
    if fl.dictionary_id is not None:
        own = 2
    elif fl.type_id == 12:
        own = 2
    else:
        own = 1
    if fl.name in ("receptorType", "somaLocation", "tosomaLocation", "status"):
        print("  %-16s owns buf %d..%d  (%s)" % (fl.name, buf_i, buf_i + own - 1,
              [bufs[b] for b in range(buf_i, buf_i + own)]))
    buf_i += own
    for c in fl.children:
        cown = 1
        if c.name.split(".")[0] in ("somaLocation", "tosomaLocation"):
            print("     %-14s owns buf %d..%d  (%s)" % (c.name, buf_i, buf_i + cown - 1,
                  [bufs[b] for b in range(buf_i, buf_i + cown)]))
        buf_i += cown
print("total consumed:", buf_i, "of", n_bufs)
