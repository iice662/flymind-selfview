"""Throwaway: follow the DictionaryBatch -> data -> RecordBatch chain."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, Table

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

def dump_table(t, label):
    print("%s: Table.at pos=%d vtable=%d vlen=%d fields=%d present=%s"
          % (label, t.pos, t.vtable, t.vlen, t.field_count(), t.present_fields()))
    for fi in range(t.field_count()):
        sl = t._slot(fi)
        extra = ""
        if sl is not None:
            u = struct.unpack_from("<I", data, sl)[0]
            extra = " u32=%d -> deref=%d  i64=%d i32=%d i8=%d" % (
                u, sl + u, struct.unpack_from("<q", data, sl)[0],
                struct.unpack_from("<i", data, sl)[0], data[sl])
        print("    slot %d @%s%s" % (fi, sl, extra))

root_at, meta_len = f._frame(6728)
msg = Table(data, root_at)
print("Message header_type=%d bodyLength=%d" % (msg.i8(1), msg.i64(3)))
hdr_addr = msg._deref(2)
print("Message.header deref -> %d" % hdr_addr)
db = Table.at(data, hdr_addr)
dump_table(db, "DictionaryBatch")

# field 0 (id) is absent per vtable; field 1 points at the data table
data_addr = db._deref(1)
print("DictionaryBatch slot1 deref -> %s" % data_addr)
rb = Table.at(data, data_addr)
dump_table(rb, "RecordBatch(raw at slot1 target)")

# compare: Table() ctor indirection
u = struct.unpack_from("<I", data, db._slot(1))[0]
print("slot1 uoffset = %d ; at+u = %d" % (u, db._slot(1) + u))
rb2 = Table(data, db._slot(1))
dump_table(rb2, "RecordBatch(via Table ctor indirection)")

# and the uoffset *at* data_addr
u2 = struct.unpack_from("<I", data, data_addr)[0]
print("uoffset stored at %d = %d -> %d" % (data_addr, u2, data_addr + u2))
rb3 = Table(data, data_addr)
dump_table(rb3, "RecordBatch(ctor from data_addr)")

for cand, name in ((data_addr, "at(data_addr)"), (rb3.pos, "rb3.pos")):
    t = Table.at(data, cand)
    print("%s -> len=%d nodes=%d buffers=%d" % (name, t.i64(0, -1), t.vector_len(1), t.vector_len(2)))
