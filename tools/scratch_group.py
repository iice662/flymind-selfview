"""Throwaway: group take_buffer calls by field for the library's decode."""
path = r"D:\projects\science\tools\feather_lite.py"
src = open(path, encoding="utf-8").read()

a1 = """        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
assert a1 in src
src = src.replace(a1, """        def take_buffer() -> bytes:
            _ix = buf_i[0]
            off, ln = buffers[_ix]
            buf_i[0] += 1
            _USED.append((_CURF[0], _ix, off, ln))""", 1)

a2 = """        node_i = [0]
        buf_i = [0]"""
assert a2 in src
src = src.replace(a2, """        node_i = [0]
        buf_i = [0]
        _USED = []
        _CURF = ["?"]""", 1)

a3 = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
assert a3 in src
src = src.replace(a3, """        def decode(field: Field):
            _CURF[0] = field.name
            n = nodes[node_i[0]]
            node_i[0] += 1""", 1)

a4 = """        out = {}
        for field in self.fields:
            out[field.name] = decode(field)"""
assert a4 in src
src = src.replace(a4, """        out = {}
        for field in self.fields:
            _USED.clear()
            out[field.name] = decode(field)
            print("FIELD %-18s used: %s" % (field.name,
                  [(u[1], u[3]) for u in _USED]))""", 1)

open(r"D:\projects\science\tools\scratch_instK.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("iK", r"D:\projects\science\tools\scratch_instK.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, b in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
