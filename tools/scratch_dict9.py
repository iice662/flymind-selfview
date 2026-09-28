"""Throwaway: instrument the real _read_dict_values and the DictionaryBatch branch."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
import feather_lite as FL
from feather_lite import FeatherFile, Table

P = r"D:\projects\science\malecns\body-annotations.feather"

real_read_dict_values = FeatherFile._read_dict_values
def probe(self, batch, body_start):
    print("PROBE: batch.pos=%d batch.vlen=%d batch.vtable=%d present=%s"
          % (batch.pos, batch.vlen, batch.vtable, batch.present_fields()))
    print("       body_start=%d  len0=%s nodes=%s buffers=%s"
          % (body_start, batch.i64(0, -1), batch.vector_len(1), batch.vector_len(2)))
    return real_read_dict_values(self, batch, body_start)
FeatherFile._read_dict_values = probe

real_collect = FeatherFile._collect_dictionaries
def collect(self):
    if self._dictionaries is not None:
        return self._dictionaries
    dicts = {}
    pos = 8
    end = len(self.data) - 10
    while pos < end:
        msg, body_start = self._message_at(pos)
        mtype = msg.i8(1, 0)
        body_len = msg.i64(3, 0)
        print("COLLECT: pos=%d msg.pos=%d mtype=%d body_start=%d body_len=%d"
              % (pos, msg.pos, mtype, body_start, body_len))
        if mtype == 2:
            db = msg.table(2) or msg.table(1)
            print("   db=%r db.pos=%s db.vlen=%s slots=%s"
                  % (db, None if db is None else db.pos, None if db is None else db.vlen,
                     None if db is None else [db._slot(i) for i in range(db.field_count())]))
            if db is not None:
                print("   dict_id=%s" % db.i64(0, None))
                rb = db.table(1)
                print("   rb=%r rb.pos=%s" % (rb, None if rb is None else rb.pos))
                if rb is not None:
                    print("   rb len=%s nodes=%s buffers=%s"
                          % (rb.i64(0, -1), rb.vector_len(1), rb.vector_len(2)))
        if mtype == 3:
            break
        pos = body_start + body_len
    return dicts
FeatherFile._collect_dictionaries = collect

f = FeatherFile(P)
try:
    f._collect_dictionaries()
except Exception as e:
    print("FAILED: %r" % (e,))
