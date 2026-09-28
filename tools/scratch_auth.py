"""Throwaway: authoritative per-field buffer/nodes usage from the library's own loop."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":', 'if False:')
old = """        out = {}
        for field in self.fields:
            out[field.name] = decode(field)"""
assert old in src, "anchor not found"
new = """        out = {}
        print("FIELDLIST len=%d: %s" % (len(self.fields), [f.name for f in self.fields]))
        for field in self.fields:
            _b0, _n0 = buf_i[0], node_i[0]
            out[field.name] = decode(field)
            print("USE %-20s input_buf=%-3d input_node=%-3d -> used bufs %d..%d (%d)"
                  % (field.name, _b0, _n0, _b0, buf_i[0] - 1, buf_i[0] - _b0))"""
src = src.replace(old, new, 1)
open(r"D:\projects\science\tools\scratch_instH.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("iH", r"D:\projects\science\tools\scratch_instH.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, b in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
