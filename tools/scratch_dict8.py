"""Throwaway: exact values inside _collect_dictionaries' DictionaryBatch branch."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, Table

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

pos = 8
msg, body_start = f._message_at(pos)
mtype = msg.i8(1, 0)
print("schema frame: msg.pos=%d mtype=%d body_start=%d body_len=%d" % (msg.pos, mtype, body_start, msg.i64(3)))
pos = body_start + msg.i64(3)
print("next pos = %d" % pos)

msg, body_start = f._message_at(pos)
mtype = msg.i8(1, 0)
print("frame@%d: msg.pos=%d mtype=%d body_start=%d body_len=%d present=%s slots=%s"
      % (pos, msg.pos, mtype, body_start, msg.i64(3), msg.present_fields(),
         [msg._slot(i) for i in range(msg.field_count())]))

db = msg.table(2) or msg.table(1)
print("db = %r  pos=%s vlen=%s" % (db, None if db is None else db.pos, None if db is None else db.vlen))
if db is not None:
    for fi in range(db.field_count()):
        sl = db._slot(fi)
        if sl is None:
            print("  slot %d absent" % fi)
            continue
        u = struct.unpack_from("<I", data, sl)[0]
        print("  slot %d @%d u32=%d -> %d" % (fi, sl, u, sl + u))
    print("db.table(1) =", db.table(1))
    print("db.table(0) =", db.table(0))
    print("db.i64(0) =", db.i64(0, -1))
    print("--- what does the ORIGINAL code path produce?")
    rb = db.table(1)
    print("rb.pos =", rb.pos if rb else None)
