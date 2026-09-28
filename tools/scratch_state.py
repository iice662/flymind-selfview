"""Throwaway: dump precise state for the somaLocation decode in batch 0."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
assert n in src
src = src.replace(n, """        def decode(field: Field):
            _nm = field.name
            n = nodes[node_i[0]]
            node_i[0] += 1""", 1)
n2 = """                offsets_buf = take_buffer()
                if len(offsets_buf) < struct.calcsize"""
assert n2 in src
src = src.replace(n2, """                _oi = buf_i[0]
                offsets_buf = take_buffer()
                print("STATE %s: n=%d wide=%s off_idx=%d off_len=%d node_i=%d buf_i=%d"
                      % (_nm, n, wide, _oi, len(offsets_buf), node_i[0], buf_i[0]))
                if len(offsets_buf) < struct.calcsize""", 1)
src = src.replace('if __name__ == "__main__":', 'if False:')
open(r"D:\projects\science\tools\scratch_inst8.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("i8", r"D:\projects\science\tools\scratch_inst8.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, b in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
