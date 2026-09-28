"""Throwaway: depth-aware trace of _read_batch (proper indentation)."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()

n1 = """    def _read_batch(self, batch: Table, body_start: int, dicts: dict,
                    strict: bool = True) -> dict:
"""
assert n1 in src
prologue = """        global _DEPTH
        _DEPTH = globals().get("_DEPTH", 0) + 1
        _P = "  " * _DEPTH
        print("%s>> _read_batch depth=%d strict=%s fields=%d nodes=%d buffers=%d"
              % (_P, _DEPTH, strict, len(self.fields), batch.vector_len(1), batch.vector_len(2)))
"""
src = src.replace(n1, n1 + prologue, 1)

n2 = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
assert n2 in src
src = src.replace(n2, """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1
            if _DEPTH == 1:
                print("%s   FIELD %-20s type=%d child=%d n=%d"
                      % (_P, field.name, field.type_id, len(field.children), n))""", 1)

n3 = """        out = {}
        for field in self.fields:
            out[field.name] = decode(field)
            if hasattr(self, "_on_column"):
                self._on_column(field.name)
        return out"""
assert n3 in src
src = src.replace(n3, """        out = {}
        for field in self.fields:
            _b0 = buf_i[0]
            out[field.name] = decode(field)
            print("%s   %-20s bufs %d..%d" % (_P, field.name, _b0, buf_i[0] - 1))
            if hasattr(self, "_on_column"):
                self._on_column(field.name)
        _DEPTH -= 1
        return out""", 1)

ns = {"__name__": "dbg"}
exec(compile(src, "feather_dbg", "exec"), ns)
f = ns["FeatherFile"](r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, batch in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
