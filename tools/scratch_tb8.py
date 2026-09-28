"""Throwaway: print the exact caller line for each take_buffer read of somaLocation."""
import sys, traceback
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
src = src.replace(n, """        _CUR = ["?"]

        def decode(field: Field):
            _CUR[0] = field.name
            n = nodes[node_i[0]]
            node_i[0] += 1""", 1)
n2 = """            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert n2 in src
src = src.replace(n2, """            off, ln = buffers[buf_i[0]]
            if _CUR[0] == "somaLocation":
                _st = traceback.extract_stack()
                print("   [%s] buffers[%d]=(%d,%d) callers=%s"
                      % (_CUR[0], buf_i[0], off, ln,
                         [(f.name, f.lineno) for f in _st[-4:-1]]))
            buf_i[0] += 1""", 1)
src = src.replace("import struct\n", "import struct\nimport traceback\n", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
