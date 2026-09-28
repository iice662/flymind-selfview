import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = sys.argv[1]
data = open(path, "rb").read()

# locate and parse each message frame from the front of the file
pos = 8
end = len(data) - 10
frames = []
while pos < end:
    first = struct.unpack_from("<I", data, pos)[0]
    if first == 0xFFFFFFFF:
        meta_len = struct.unpack_from("<i", data, pos + 4)[0]
        msg_pos = pos + 8
    else:
        meta_len = struct.unpack_from("<i", data, pos)[0]
        msg_pos = pos + 4
    if meta_len <= 0 or msg_pos + meta_len > end:
        break
    body_len = struct.unpack_from("<i", data, msg_pos + meta_len - 4)[0] if False else 0
    msg = F.FB(data, msg_pos)
    mtype = msg.int8(0)
    frames.append((pos, msg_pos, meta_len, mtype, msg))
    # body length lives in Message.bodyLength (field 3)
    body_len = msg.int64(3)
    if body_len <= 0:
        break
    pos = msg_pos + meta_len + body_len

print("messages found: %d" % len(frames))
for pos, msg_pos, meta_len, mtype, msg in frames[:6]:
    print("  frame@%d msg@%d meta_len=%d type=%s fields=%s" % (
        pos, msg_pos, meta_len, {0: "Schema", 1: "DictionaryBatch", 2: "RecordBatch"}.get(mtype, mtype), [i for i in range(5) if msg.field(i) is not None]))
    if mtype == 0:
        sch = msg.table(2)
        print("     schema fields present:", [i for i in range(9) if sch.field(i) is not None])
        print("     endianness:", sch.int16(0), " n fields:", sch.vector_len(1))
        for i in range(sch.vector_len(1)):
            ft = sch.vector_table(1, i)
            t = ft.table(2)
            print("       field %d: name=%r type_id=%s nullable=%s dict=%s" % (
                i, ft.string(0), (t.int8(0) if t else None), ft.bool_(1),
                (ft.table(4).int32(0) if ft.table(4) else None)))
