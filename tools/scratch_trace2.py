"""Throwaway: line trace filtered to the nested decode's own code object."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":', 'if False:')
open(r"D:\projects\science\tools\scratch_inst5.py", "w", encoding="utf-8").write(src)
LINES = src.splitlines()

import importlib.util
spec = importlib.util.spec_from_file_location("i5", r"D:\projects\science\tools\scratch_inst5.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

marker = "FeatherFile._read_batch"

target_code = {}

orig = mod.FeatherFile._read_batch
def wrapper(self, batch, body_start, dicts, strict=True):
    import types
    # find nested 'decode'
    def find(code):
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                if c.co_name == "decode":
                    target_code["decode"] = c
                find(c)
    find(orig.__code__)
    return orig(self, batch, body_start, dicts, strict)
mod.FeatherFile._read_batch = wrapper

log = []
def tracer(frame, event, arg):
    if frame.f_code is target_code.get("decode"):
        if event == "line":
            log.append(("decode", frame.f_lineno))
        elif event == "call":
            log.append((">decode", frame.f_lineno))
        elif event == "return":
            log.append(("<decode", frame.f_lineno))
    if frame.f_code is not None and frame.f_code.co_name == "take_buffer":
        if event == "call":
            log.append(("  take_buffer", frame.f_lineno))
    frame.f_trace_lines = True
    return tracer

f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
gen = f.iter_batches()
sys.settrace(tracer)
try:
    next(gen)
except Exception as e:
    err = repr(e)
sys.settrace(None)

print("decode code object found:", "decode" in target_code)
print("events: %d" % len(log))
for name, ln in log[:80]:
    print("  %-14s line %-4d | %s" % (name, ln, LINES[ln - 1].strip()[:80]))
print("ERR:", err)
