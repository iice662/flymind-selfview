"""Throwaway: trace _read_dict_values, logging to a file, compact output."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
import feather_lite as FL

P = r"D:\projects\science\malecns\body-annotations.feather"
OUT = open(r"D:\projects\science\tools\scratch_log.txt", "w", encoding="utf-8")

real = FL.FeatherFile._read_dict_values
def probe(self, batch, body_start):
    OUT.write("READ_DICT: pos=%d vtable=%d vlen=%d body_start=%d fields=%d\n"
              % (batch.pos, batch.vtable, batch.vlen, body_start, len(self.fields)))
    return real(self, batch, body_start)
FL.FeatherFile._read_dict_values = probe

orig_table = FL.Table.table
def table_probe(self, fi):
    t = orig_table(self, fi)
    if 6700 < self.pos < 7000:
        OUT.write("Table.table(pos=%d, fi=%d) -> %s\n" % (self.pos, fi, None if t is None else t.pos))
    return t
FL.Table.table = table_probe

f = FL.FeatherFile(P)
try:
    f._collect_dictionaries()
    OUT.write("OK\n")
except Exception as e:
    OUT.write("FAILED: %r\n" % (e,))
OUT.close()

with open(r"D:\projects\science\tools\scratch_log.txt", encoding="utf-8") as fh:
    for line in fh.readlines()[:40]:
        print(line.rstrip())
