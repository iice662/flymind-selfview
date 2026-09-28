"""Throwaway: log what take_buffer RETURNS (not just the buffer entry)."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()

n = """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert n in src
src = src.replace(n, """        def take_buffer() -> bytes:
            _idx = buf_i[0]
            off, ln = buffers[_idx]
            _res = _take_buffer_impl(off, ln)
            print("      TB #%-3d off=%-9d ln=%-8d -> returned %d bytes" % (_idx, off, ln, len(_res)))
            buf_i[0] += 1
            return _res
        def _take_buffer_impl(off, ln):""", 1)

# indent the remainder of the original take_buffer body
start = src.index("        def _take_buffer_impl(off, ln):") + len("        def _take_buffer_impl(off, ln):\n")
end = src.index("        def _decode_values(fld: Field, count: int):")
body = src[start:end]
body_indented = "".join(("    " + line if line.strip() else line) for line in body.splitlines(keepends=True))
src = src[:start] + body_indented + src[end:]

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        print("OK batch %d" % k)
        break
except Exception as e:
    print("ERR %r" % (e,))
