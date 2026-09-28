"""Throwaway: use sys.settrace to log every take_buffer call with its line number."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":', 'if False:')
open(r"D:\projects\science\tools\scratch_inst4.py", "w", encoding="utf-8").write(src)

import importlib.util
spec = importlib.util.spec_from_file_location("i4", r"D:\projects\science\tools\scratch_inst4.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

log = []
def tracer(frame, event, arg):
    if frame.f_code.co_name in ("decode", "take_buffer", "_decode_values", "_read_batch"):
        if event == "call":
            log.append(("CALL", frame.f_code.co_name, frame.f_lineno))
        elif event == "line" and frame.f_code.co_name == "decode":
            log.append(("LINE", "decode", frame.f_lineno))
    return tracer

f = mod.FeatherFile(r"D:\projects\science\malecns\body-annotations.feather")
gen = f.iter_batches()
sys.settrace(tracer)
try:
    next(gen)
except Exception:
    import traceback
    err = traceback.format_exc().strip().splitlines()[-1]
sys.settrace(None)

# print the last 60 events
for e in log[-60:]:
    print("%-5s %-16s line %d" % e)
print("ERR:", err)
lines = src.splitlines()
print("\n--- source lines 620-706 (1-based) for reference on interesting lines:")
seen = sorted({e[2] for e in log[-60:] if e[0] in ("CALL",)})
for ln in seen:
    if 600 <= ln <= 720:
        print("%4d| %s" % (ln, lines[ln - 1]))
