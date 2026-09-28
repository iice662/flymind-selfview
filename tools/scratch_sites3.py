"""Throwaway: capture take_buffer call sites via a module-level trace list."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":', 'if False:')
src = src.replace("""        def take_buffer() -> bytes:
            off, ln = buffers[buf_i[0]]""", """        def take_buffer() -> bytes:
            TRACE.append((sys._getframe(1).f_lineno, buf_i[0], buffers[buf_i[0]]))
            off, ln = buffers[buf_i[0]]""", 1)
src = src.replace("import struct\n", "import struct\nimport sys\nTRACE = []\n", 1)
open(r"D:\projects\science\tools\scratch_instG.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("iG", r"D:\projects\science\tools\scratch_instG.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
try:
    for k, b in enumerate(f.iter_batches()):
        break
except Exception as e:
    print("ERR %r" % (e,))

print("last 14 take_buffer calls (line, buf_index, (off,len)):")
src_lines = src.splitlines()
for ln, idx, buf in mod.TRACE[-14:]:
    print("   line %-4d buffers[%-3d] = %-22s | %s" % (ln, idx, buf, src_lines[ln - 1].strip()[:60]))
