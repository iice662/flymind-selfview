"""Throwaway: definitive per-field buffer consumption map."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()

n1 = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
assert n1 in src
src = src.replace(n1, """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1
            print("DECODE %-22s type=%-3d child=%d n=%-7d buf_i=%-4d node_i=%d"
                  % (field.name, field.type_id, len(field.children), n, buf_i[0], node_i[0] - 1))""", 1)

n2 = """        out = {}
        for field in self.fields:
            out[field.name] = decode(field)"""
assert n2 in src
src = src.replace(n2, """        out = {}
        for field in self.fields:
            _b = buf_i[0]
            _nn = node_i[0]
            out[field.name] = decode(field)
            print("   => %-22s bufs %d..%d (%d)  nodes %d..%d"
                  % (field.name, _b, buf_i[0] - 1, buf_i[0] - _b, _nn, node_i[0] - 1))""", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
