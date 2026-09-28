"""Throwaway: capture take_buffer call sites for the failing field, printing on error."""
import importlib.util
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":', 'if False:')

patched = src.replace("""        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]""", """        def take_buffer() -> bytes:
            _TRACE.append((sys._getframe(1).f_lineno, buf_i[0], buffers[buf_i[0]]))
            off, ln = buffers[buf_i[0]]""", 1)
patched = patched.replace("""        node_i = [0]
        buf_i = [0]""", """        node_i = [0]
        buf_i = [0]
        _TRACE = []
        """, 1)
patched = patched.replace("import struct\n", "import struct\nimport sys\n", 1)
open(r"D:\projects\science\tools\scratch_instE.py", "w", encoding="utf-8").write(patched)

spec = importlib.util.spec_from_file_location("iE", r"D:\projects\science\tools\scratch_instE.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, b in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))

tr = getattr(mod.FeatherFile._read_batch, "trace", [])
print("last 12 take_buffer calls (line, buf_index, (off,len)):")
for ln, idx, buf in tr[-12:]:
    print("   line %-4d buffers[%d] = %s" % (ln, idx, buf))
