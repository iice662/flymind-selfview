import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\connectome-weights.feather"
f = F.FeatherFile(path)
off, ml = f.record_batches[0]
root_at, mlen = f._frame(off)
rb = F.Table(f.data, root_at).table(2)
body = root_at + mlen
o = rb.vector_struct_i64(2, 1, 16, 0)
ln = rb.vector_struct_i64(2, 1, 16, 8)
raw = bytes(f.data[body + o: body + o + ln])
declared = struct.unpack_from("<q", raw, 0)[0]
frame = raw[8:]
print("buffer len", ln, "declared uncompressed", declared)
print("frame magic", frame[:4].hex())
pos = 4
flg = frame[pos]; pos += 1
bd = frame[pos]; pos += 1
print("FLG=%02x (version=%d blockIndep=%d contentSize=%d contentChecksum=%d dictId=%d blockChecksum=%d)"
      % (flg, flg >> 6, (flg >> 5) & 1, (flg >> 3) & 1, (flg >> 2) & 1, flg & 1, (flg >> 4) & 1))
print("BD=%02x (blockMaxSize=%d)" % (bd, (bd >> 4) & 7))
content = None
if flg & 0x08:
    content = struct.unpack_from("<q", frame, pos)[0]
    pos += 8
    print("content size", content)
if flg & 0x01:
    pos += 4
pos += 1  # header checksum
print("first block header:", frame[pos:pos + 4].hex())
n = 0
while pos + 4 <= len(frame):
    block = struct.unpack_from("<I", frame, pos)[0]
    pos += 4
    if block == 0:
        print("end mark")
        break
    uncompressed = bool(block & 0x80000000)
    size = block & 0x7FFFFFFF
    chunk = frame[pos:pos + size]
    pos += size
    n += 1
    try:
        out = chunk if uncompressed else F._lz4_block(chunk)
        print("  block %d: comp=%d uncompressed_flag=%s -> %d bytes (first %s)"
              % (n, size, uncompressed, len(out), out[:8].hex()))
    except Exception as e:
        print("  block %d: comp=%d FAILED: %s" % (n, size, e))
        print("     first bytes:", chunk[:16].hex())
        break
    if flg & 0x10:
        pos += 4
    if n > 4:
        break
