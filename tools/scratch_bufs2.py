"""Throwaway: print the full buffer tuple list as _read_batch builds it."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """        comp = batch.table(3)"""
assert n in src
src = src.replace(n, """        if _WANT.get("dump") and batch.vector_len(2) > 50:
            for _i in range(len(buffers)):
                print("BUF %3d = %s" % (_i, buffers[_i]))
            _WANT["dump"] = False
        comp = batch.table(3)""", 1)
ns = {"__name__": "dbg", "_WANT": {"dump": True}}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
