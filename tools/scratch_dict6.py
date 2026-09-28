"""Throwaway: reproduce the failure with instrumentation."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
import feather_lite as FL
from feather_lite import FeatherFile, Table, Field, T_UTF8, T_INT, T_FLOATINGPOINT

P = r"D:\projects\science\malecns\body-annotations.feather"

orig_read_batch = FeatherFile._read_batch
def traced(self, batch, body_start, dicts):
    print("  _read_batch: batch.pos=%s batch.vlen=%s present=%s body_start=%s fields=%d"
          % (batch.pos, batch.vlen, batch.present_fields(), body_start, len(self.fields)))
    try:
        print("     vec_len(1)=%s vec_len(2)=%s len0=%s" % (batch.vector_len(1), batch.vector_len(2), batch.i64(0, -1)))
    except Exception as e:
        print("     vec probe failed: %s" % e)
    return orig_read_batch(self, batch, body_start, dicts)
FeatherFile._read_batch = traced

orig = FeatherFile._read_dict_values
def traced_dict(self, batch, body_start):
    print("_read_dict_values: batch.pos=%s present=%s body_start=%s" % (batch.pos, batch.present_fields(), body_start))
    vf = next((f for f in self.fields if f.dictionary_id is not None), None)
    print("   chosen value_field=%r type_id=%s bit_width=%s" % (vf, None if vf is None else vf.type_id,
                                                                None if vf is None else vf.bit_width))
    return orig(self, batch, body_start)
FeatherFile._read_dict_values = traced_dict

f = FeatherFile(P)
print("collecting dictionaries...")
try:
    d = f._collect_dictionaries()
    print("got %d dictionaries" % len(d))
    for k, v in d.items():
        print("   id=%s len=%s first=%s" % (k, len(v), v[:5]))
except Exception as e:
    print("FAILED: %r" % (e,))
