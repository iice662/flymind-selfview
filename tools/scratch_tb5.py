"""Throwaway: log tb #85..#95 in return order (fix misattribution) + list branch state."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()

n = """            if t in (T_LIST, T_LARGE_LIST):
                wide = t == T_LARGE_LIST"""
assert n in src
src = src.replace(n, """            if t in (T_LIST, T_LARGE_LIST):
                wide = t == T_LARGE_LIST
                print("   LIST %s n=%d buf_i=%d node_i=%d" % (field.name, n, buf_i[0], node_i[0]))""", 1)

n2 = """                offsets = struct.unpack_from(fmt, offsets_buf, 0)
                child = field.children[0] if field.children else None"""
assert n2 in src
src = src.replace(n2, """                print("      %s offsets_buf=%d bytes" % (field.name, len(offsets_buf)))
                offsets = struct.unpack_from(fmt, offsets_buf, 0)
                child = field.children[0] if field.children else None""", 1)

n3 = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
assert n3 in src
src = src.replace(n3, """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1
            print("DECODE %-22s type=%-3d child=%d n=%-7d buf_i=%d" % (field.name, field.type_id, len(field.children), n, buf_i[0]))""", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        print("OK batch %d" % k)
        break
except Exception as e:
    print("ERR %r" % (e,))
