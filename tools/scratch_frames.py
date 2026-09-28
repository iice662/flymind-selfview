"""Throwaway: scan the metadata/body region for LZ4 frames and identify them."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import _lz4_frame

P = r"D:\projects\science\malecns\body-annotations.feather"
with open(P, "rb") as fh:
    data = fh.read(16000)

MAGIC = bytes.fromhex("04224d18")
pos = 6728
while pos < 16000:
    k = data.find(MAGIC, pos, 16000)
    if k < 0:
        break
    # the 8 bytes before it are the uncompressed-size prefix
    prefix = struct.unpack_from("<q", data, k - 8)[0] if k >= 8 else None
    # find the end of this frame: scan block sizes
    p = k + 4
    flg = data[p]; p += 1
    bd = data[p]; p += 1
    if flg & 0x08:
        p += 8
    if flg & 0x01:
        p += 4
    p += 1
    total = 0
    while p + 4 <= len(data):
        blk = struct.unpack_from("<I", data, p)[0]
        p += 4
        if blk == 0:
            break
        size = blk & 0x7FFFFFFF
        p += size
        total += size
        if flg & 0x10:
            p += 4
    end = p
    try:
        dec = _lz4_frame(bytes(data[k:end]))
        info = "dec=%d text=%r" % (len(dec), dec[:32])
        if len(dec) % 4 == 0 and len(dec) > 8:
            ints = struct.unpack_from("<%di" % min(8, len(dec) // 4), dec, 0)
            info += " ints=%s" % (ints,)
    except Exception as e:
        info = "FAILED %s" % e
    print("frame magic at %d  prefix@%d=%s  frame_len=%d  %s" % (k, k - 8, prefix, end - k, info))
    pos = end
