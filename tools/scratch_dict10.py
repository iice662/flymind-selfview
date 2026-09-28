"""Throwaway: precise instrumentation with object identity."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
import feather_lite as FL

P = r"D:\projects\science\malecns\body-annotations.feather"

real = FL.FeatherFile._read_dict_values
def probe(self, batch, body_start):
    print("READ_DICT: batch=%r pos=%d vtable=%d vlen=%d body_start=%d fields=%d"
          % (batch, batch.pos, batch.vtable, batch.vlen, body_start, len(self.fields)))
    print("   i64(0)=%s vec_len(1)=%s vec_len(2)=%s" % (batch.i64(0, -1), batch.vector_len(1), batch.vector_len(2)))
    print("   slots=%s" % [batch._slot(i) for i in range(batch.field_count())])
    return real(self, batch, body_start)
FL.FeatherFile._read_dict_values = probe

f = FL.FeatherFile(P)
# replicate the exact original loop body, but print
msg, body_start = f._message_at(6728)
print("msg.pos=%d mtype=%d" % (msg.pos, msg.i8(1, 0)))
db = msg.table(2) or msg.table(1)
print("db.pos=%d" % db.pos)
batch = db.table(1)
print("directly: db.table(1).pos = %d" % batch.pos)
print("now call via the real loop path:")
try:
    f._collect_dictionaries()
except Exception as e:
    print("FAILED %r" % (e,))
