"""Throwaway: log the exact tuple consumed at each take_buffer call in buffer-index order."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert n in src
src = src.replace(n, """            _i = buf_i[0]
            off, ln = buffers[_i]
            print("   read buffers[%d] = (%d, %d)" % (_i, off, ln))
            buf_i[0] += 1""", 1)
n2 = """            if t in (T_LIST, T_LARGE_LIST):
                wide = t == T_LARGE_LIST"""
src = src.replace(n2, """            if t in (T_LIST, T_LARGE_LIST):
                print("   ==> LIST branch %s buf_i=%d" % (field.name, buf_i[0]))
                wide = t == T_LARGE_LIST""", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        print("OK batch %d" % k)
        break
except Exception as e:
    print("ERR %r" % (e,))
