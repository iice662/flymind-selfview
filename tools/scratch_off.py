"""Throwaway: print offsets_buf length at the list branch and the traceback line of the error."""
import sys, traceback
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n1 = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
src = src.replace(n1, """        _CUR = ["?"]

        def decode(field: Field):
            _CUR[0] = field.name
            n = nodes[node_i[0]]
            node_i[0] += 1""", 1)
n2 = """                offsets_buf = take_buffer()
                if len(offsets_buf) < struct.calcsize("<%d%s" % (n + 1, "q" if wide else "i")):"""
assert n2 in src
src = src.replace(n2, """                offsets_buf = take_buffer()
                print("   [%s] offsets_buf=%d bytes buf_i=%d" % (_CUR[0], len(offsets_buf), buf_i[0]))
                if len(offsets_buf) < struct.calcsize("<%d%s" % (n + 1, "q" if wide else "i")):""", 1)
open(r"D:\projects\science\tools\scratch_inst2.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("feather_inst2",
                                              r"D:\projects\science\tools\scratch_inst2.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        print("OK batch %d" % k)
        break
except Exception:
    tb = traceback.format_exc()
    print(tb)
