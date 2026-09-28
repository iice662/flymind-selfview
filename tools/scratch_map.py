"""Throwaway: map field -> consumed buffers to find the desync."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n1 = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
assert n1 in src
src = src.replace(n1, """        def decode(field: Field):
            n = nodes[node_i[0]]
            _b0 = buf_i[0]
            node_i[0] += 1
            print("  DECODE %-20s node_i=%d buf_i=%d n=%d type=%d child=%d"
                  % (field.name, node_i[0] - 1, _b0, n, field.type_id, len(field.children)))""")
src = src.replace("""        out = {}
        for field in self.fields:
            out[field.name] = decode(field)
            if hasattr(self, "_on_column"):
                self._on_column(field.name)
        return out""", """        out = {}
        for field in self.fields:
            _b0 = buf_i[0]
            out[field.name] = decode(field)
            print("     -> %-20s used bufs %d..%d" % (field.name, _b0, buf_i[0] - 1))
            if hasattr(self, "_on_column"):
                self._on_column(field.name)
        return out""")
ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
for k, batch in enumerate(f.iter_batches()):
    break
