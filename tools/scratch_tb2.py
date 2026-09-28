"""Throwaway: instrument take_buffer with field names via source patch."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert n in src
src = src.replace(n, """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            print("      TB #%d off=%-9d len=%-8d n_i=%d" % (buf_i[0], off, ln, node_i[0]))
            buf_i[0] += 1""", 1)

n2 = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
assert n2 in src
src = src.replace(n2, """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1
            print("  >>-- DECODE %s (type=%d child=%d n=%d) buf_i=%d node_i=%d"
                  % (field.name, field.type_id, len(field.children), n, buf_i[0], node_i[0] - 1))""", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
