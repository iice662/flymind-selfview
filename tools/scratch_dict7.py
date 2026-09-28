"""Throwaway: compact trace of _collect_dictionaries."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, Table

P = r"D:\projects\science\malecns\body-annotations.feather"

orig_msg_at = FeatherFile._message_at
def traced_msg_at(self, offset):
    msg, body_start = orig_msg_at(self, offset)
    if offset > 7000:
        return msg, body_start
    mtype = msg.i8(1, 0)
    print("message_at(%d): root=%d mtype=%d body_start=%d" % (offset, msg.pos, mtype, body_start))
    if mtype == 2:
        hdr = msg._deref(2)
        db = Table.at(self.data, hdr)
        print("    header deref=%d db.pos=%d db.vtable=%d db.vlen=%d present=%s"
              % (hdr, db.pos, db.vtable, db.vlen, db.present_fields()))
        print("    db.i64(0)=%d  db.i64(1)=%d" % (db.i64(0, -1), db.i64(1, -1)))
        for fi in range(db.field_count()):
            sl = db._slot(fi)
            if sl is None:
                print("      slot %d absent" % fi)
                continue
            u = struct.unpack_from("<I", self.data, sl)[0]
            print("      slot %d @%d u32=%d -> target %d" % (fi, sl, u, sl + u))
            try:
                t = Table.at(self.data, sl + u)
                print("         -> Table.at(%d) pos=%d vlen=%d present=%s len0=%d nodes=%d buffers=%d"
                      % (sl + u, t.pos, t.vlen, t.present_fields(), t.i64(0, -1),
                         t.vector_len(1), t.vector_len(2)))
            except ValueError as e:
                print("         -> invalid table: %s" % e)
    return msg, body_start
FeatherFile._message_at = traced_msg_at

orig_dict = FeatherFile._read_dict_values
def traced_dict(self, batch, body_start):
    print("_read_dict_values(batch.pos=%d, body_start=%d) fields=%d"
          % (batch.pos, body_start, len(self.fields)))
    return orig_dict(self, batch, body_start)
FeatherFile._read_dict_values = traced_dict

f = FeatherFile(P)
try:
    d = f._collect_dictionaries()
    print("OK %d dicts" % len(d))
except Exception as e:
    print("FAILED: %r" % (e,))
