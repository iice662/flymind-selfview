"""Throwaway: write the instrumented source to disk so I can read the real line numbers."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n = """            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
src = src.replace(n, """            off, ln = buffers[buf_i[0]]
            print("TB buf_i=%d -> (%d,%d)" % (buf_i[0], off, ln))
            buf_i[0] += 1""", 1)
src = src.replace("if __name__ == \"__main__\":", "if False:", 1)
open(r"D:\projects\science\tools\scratch_instrumented.py", "w", encoding="utf-8").write(src)
print("written")
