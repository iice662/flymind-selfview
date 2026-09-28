"""Throwaway: wrap the nested take_buffer to capture exact call sites in somaLocation's decode."""
import sys, types
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":', 'if False:')
open(r"D:\projects\science\tools\scratch_instC.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("iC", r"D:\projects\science\tools\scratch_instC.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Patch the module source: record (line, buf index) for every take_buffer call.
# We do this by re-exec'ing with an inserted recorder that uses sys._getframe.
patched = src.replace("""        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]""", """        def take_buffer() -> bytes:
            _fr = sys._getframe(1)
            _TRACE.append((_fr.f_lineno, buf_i[0], buffers[buf_i[0]]))
            off, ln = buffers[buf_i[0]]""", 1)
patched = patched.replace("""        node_i = [0]
        buf_i = [0]""", """        node_i = [0]
        buf_i = [0]
        _TRACE = []""", 1)
patched = patched.replace("""        out = {}
        for field in self.fields:
            out[field.name] = decode(field)""", """        out = {}
        for field in self.fields:
            _TRACE.clear()
            out[field.name] = decode(field)
            if field.name == "somaLocation":
                print("TRACE for somaLocation:")
                for _ln, _idx, _b in _TRACE:
                    print("   call at line %d -> buffers[%d] = %s" % (_ln, _idx, _b))""", 1)
patched = patched.replace("import struct\n", "import struct\nimport sys\n", 1)
open(r"D:\projects\science\tools\scratch_instD.py", "w", encoding="utf-8").write(patched)

spec2 = importlib.util.spec_from_file_location("iD", r"D:\projects\science\tools\scratch_instD.py")
mod2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(mod2)
f = mod2.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, b in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))
src_lines = patched.splitlines()
print("(somaLocation branch lines 680-700 in patched source)")
for j in range(679, 700):
    print("%4d| %s" % (j + 1, src_lines[j]))
