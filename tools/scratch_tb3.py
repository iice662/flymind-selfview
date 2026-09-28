"""Throwaway: log each take_buffer request with stack context for the list branch."""
import sys, traceback
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()

n = """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert n in src
src = src.replace(n, """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            _st = traceback.extract_stack()
            _who = " <- ".join("%s:%d" % (f.name, f.lineno) for f in _st[-3:-1])
            print("      TB #%-3d off=%-9d ln=%-8d via %s" % (buf_i[0], off, ln, _who))
            buf_i[0] += 1""", 1)
src = src.replace("import struct\n", "import struct\nimport traceback\n", 1)

n2 = """        def _decode_values(fld: Field, count: int):"""
assert n2 in src
src = src.replace(n2, """        def _decode_values(fld: Field, count: int):
            print("      _decode_values(%s, %d) buf_i=%d" % (fld.name, count, buf_i[0]))""", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
