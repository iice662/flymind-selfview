"""Throwaway: log the buffers[] tuple list with indices (after assignment)."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """        buffers = [(batch.vector_struct_i64(2, i, 16, 0), batch.vector_struct_i64(2, i, 16, 8))
                   for i in range(n_buffers)]"""
assert n in src
src = src.replace(n, n + """
        if n_buffers > 50:
            print("BUFFERS LIST (len=%d):" % len(buffers))
            for _i, _b in enumerate(buffers):
                print("   [%d] = %s" % (_i, _b))""", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
