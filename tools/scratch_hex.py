"""Throwaway: hexdump 6728..7420 with int64 annotations."""
import struct

P = r"D:\projects\science\malecns\body-annotations.feather"
with open(P, "rb") as fh:
    data = fh.read(7600)

out = open(r"D:\projects\science\tools\scratch_log.txt", "w", encoding="utf-8")
for row in range(6728, 7424, 8):
    chunk = bytes(data[row:row + 8])
    hexs = " ".join("%02x" % b for b in chunk)
    q = struct.unpack_from("<q", data, row)[0]
    i = struct.unpack_from("<i", data, row)[0]
    txt = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    out.write("%6d  %-23s  q=%-22d i=%-12d %s\n" % (row, hexs, q, i, txt))

# search for the dictionary values ascii near here
out.write("\n--- looking for printable runs around the body\n")
body = bytes(data[6920:7368])
out.write("body bytes: %s\n" % " ".join("%02x" % b for b in body[:64]))
out.write("as text: %r\n" % body[:200])
out.close()
with open(r"D:\projects\science\tools\scratch_log.txt", encoding="utf-8") as fh:
    print(fh.read())
