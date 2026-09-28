import sys, os
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb"); f.seek(16712)
raw = f.read(120)
print("bytes:", raw.hex())
pos = 0
def rd_varint(b, i):
    shift=0; val=0
    while True:
        c=b[i]; i+=1; val |= (c & 0x7f) << shift
        if not (c & 0x80): return val, i
        shift += 7
last = 0
while pos < len(raw):
    h = raw[pos]; pos += 1
    ttype = h & 0x0f; delta = (h & 0xf0) >> 4
    if ttype == 0:
        print("STOP at", pos-1); break
    fid = last + delta if delta else None
    if fid is None:
        fid, pos = rd_varint(raw, pos)
    last = fid
    if ttype in (5, 6):
        v, pos = rd_varint(raw, pos)
        print("  field %d type=%d zigzag->%d" % (fid, ttype, (v >> 1) ^ -(v & 1)))
    elif ttype == 12:
        print("  field %d STRUCT begins at %d" % (fid, pos))
    elif ttype == 8:
        ln, pos = rd_varint(raw, pos)
        print("  field %d BINARY len=%d" % (fid, ln)); pos += ln
    elif ttype in (1, 2):
        print("  field %d BOOL %s" % (fid, ttype == 1))
    else:
        print("  field %d type=%d (unhandled)" % (fid, ttype)); break
