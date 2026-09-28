"""Throwaway: label every take_buffer call with the current field."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
assert n in src
src = src.replace(n, """        _CUR = ["?"]

        def decode(field: Field):
            _CUR[0] = field.name
            n = nodes[node_i[0]]
            node_i[0] += 1""", 1)
n2 = """            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert n2 in src
src = src.replace(n2, """            off, ln = buffers[buf_i[0]]
            print("   [%s] read buffers[%d] = (%d, %d)" % (_CUR[0], buf_i[0], off, ln))
            buf_i[0] += 1""", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
