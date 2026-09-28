"""Diagnostic for the MaleCNS connectome feather: confirm the column names and the
record-batch body layout, so the data can be parsed even if the footer flatbuffer
metadata is hard to walk."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\connectome-weights.feather"
size = os.path.getsize(path)
print("size:", size)
with open(path, "rb") as f:
    head = f.read(1024)
print("head:", head[:64].hex())
print("strings in header:", [s.decode() for s in
      __import__("re").findall(rb"[ -~]{4,}", head[:960])])

# footer: last 10 bytes
with open(path, "rb") as f:
    f.seek(size - 10)
    tail = f.read(10)
print("tail:", tail.hex())
footer_len = struct.unpack_from("<i", tail, 0)[0]
print("footer_len:", footer_len, "footer_off:", size - 10 - footer_len)

# message frame
mlen = struct.unpack_from("<i", head, 12)[0]
print("first message meta len:", mlen)
try:
    f = F.FeatherFile(path)
    print("schema:", f.schema_summary())
    print("record batches:", len(f.record_batches), f.record_batches[:3])
except Exception as e:
    print("reader failed:", type(e).__name__, e)

# row count sanity: look at the first record batch message we can find
try:
    with open(path, "rb") as fh:
        fh.seek(8)
        blob = fh.read(1 << 20)
    # scan for the RecordBatch message: search for 0xFFFFFFFF + plausible length after the schema
    pos = 8
    for _ in range(6):
        first = struct.unpack_from("<I", blob, pos)[0]
        if first != 0xFFFFFFFF:
            break
        mlen = struct.unpack_from("<i", blob, pos + 4)[0]
        msg = F.Table(blob, pos + 8)
        mtype = msg.i8(1, -1)
        body_len = msg.i64(3, 0)
        print("frame@%d meta=%d type=%s body_len=%d" % (pos, mlen, mtype, body_len))
        if body_len == 0:
            break
        pos = pos + 8 + mlen + body_len
except Exception as e:
    print("frame walk failed:", e)
