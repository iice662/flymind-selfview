"""Throwaway: dump the exact source text around the failing lines of the exec'd module."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()
n1 = """        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1"""
src = src.replace(n1, """        _CUR = ["?"]

        def decode(field: Field):
            _CUR[0] = field.name
            n = nodes[node_i[0]]
            node_i[0] += 1""", 1)
n2 = """            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1"""
src = src.replace(n2, """            off, ln = buffers[buf_i[0]]
            if _CUR[0] == "somaLocation":
                print("   [%s] TAKE buffers[%d]=(%d,%d)" % (_CUR[0], buf_i[0], off, ln))
            buf_i[0] += 1""", 1)

lines = src.splitlines()
open(r"D:\projects\science\tools\scratch_log.txt", "w", encoding="utf-8").write(
    "\n".join("%4d| %s" % (i + 1, lines[i]) for i in range(668, 700)))
print("\n".join("%4d| %s" % (i + 1, lines[i]) for i in range(668, 700)))
