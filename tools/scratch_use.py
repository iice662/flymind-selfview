"""Throwaway: log start/end buf_i for every field in the schema loop."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """        out = {}
        for field in self.fields:
            out[field.name] = decode(field)"""
assert n in src
src = src.replace(n, """        out = {}
        for field in self.fields:
            _b0 = buf_i[0]
            _n0 = node_i[0]
            out[field.name] = decode(field)
            print("USE %-20s bufs[%d..%d] (%d) nodes[%d]" % (
                field.name, _b0, buf_i[0] - 1, buf_i[0] - _b0, _n0))""", 1)
src = src.replace('if __name__ == "__main__":', 'if False:')
open(r"D:\projects\science\tools\scratch_inst9.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("i9", r"D:\projects\science\tools\scratch_inst9.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, b in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
