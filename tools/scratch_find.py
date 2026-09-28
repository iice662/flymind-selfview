"""Throwaway: minimal, surgical state print at the T_LIST offsets read."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

path = r"D:\projects\science\tools\feather_lite.py"
lines = open(path, encoding="utf-8").read().splitlines()

# find the T_LIST branch and the line that reads the offsets buffer
idx = next(i for i, l in enumerate(lines) if "if t in (T_LIST, T_LARGE_LIST):" in l)
print("T_LIST branch at line %d" % (idx + 1))
for j in range(idx, idx + 12):
    print("%4d| %s" % (j + 1, lines[j]))
