"""Throwaway: patch feather_lite.py's list branch with debug prints via literal anchors."""
import re

path = r"D:\projects\science\tools\feather_lite.py"
src = open(path, encoding="utf-8").read()

# find the T_LIST branch's offsets read via a literal anchor
anchor = """                take_buffer()          # validity bitmap
                offsets_buf = take_buffer()"""
assert anchor in src, "anchor missing"
dbg = """                _b_before = buf_i[0]
                take_buffer()          # validity bitmap
                offsets_buf = take_buffer()
                print("LIST %s: validity=buffers[%d], offsets=buffers[%d]=%s, len=%d, node_i=%d"
                      % (field.name, _b_before, _b_before + 1,
                         buffers[_b_before + 1], len(offsets_buf), node_i[0]))"""
src2 = src.replace(anchor, dbg, 1)

# also print every take_buffer return length
anchor2 = """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert anchor2 in src2
src2 = src2.replace(anchor2, """        def take_buffer() -> bytes:
            _ix = buf_i[0]
            off, ln = buffers[_ix]
            buf_i[0] += 1
            print("   TB[%d]=(%d,%d)" % (_ix, off, ln))""", 1)

out = r"D:\projects\science\tools\scratch_instJ.py"
open(out, "w", encoding="utf-8").write(src2)

import importlib.util
spec = importlib.util.spec_from_file_location("iJ", out)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, b in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
