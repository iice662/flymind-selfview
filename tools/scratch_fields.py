"""Throwaway: raw dump of the schema's Field tables (esp. statusLabel and a utf8 one)."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

msg = f.schema_msg
sch = msg.table(2)
print("Schema table pos=%d vlen=%d present=%s" % (sch.pos, sch.vlen, sch.present_fields()))
print("fields vector len=%d endianness field? %s" % (sch.vector_len(1), sch._slot(0)))
out = open(r"D:\projects\science\tools\scratch_log.txt", "w", encoding="utf-8")

def dump(addr, label, n=48):
    vt = addr - struct.unpack_from("<i", data, addr)[0]
    vlen = struct.unpack_from("<H", data, vt)[0]
    nf = max(0, (vlen - 4) // 2)
    out.write("%s addr=%d vtable=%d vlen=%d fields=%d present=%s\n"
              % (label, addr, vt, vlen, nf, [i for i in range(nf)
                 if struct.unpack_from("<H", data, vt + 4 + i * 2)[0] != 0]))
    for i in range(nf):
        voff = struct.unpack_from("<H", data, vt + 4 + i * 2)[0]
        if voff == 0:
            continue
        at = addr + voff
        u = struct.unpack_from("<I", data, at)[0]
        out.write("    f%d voff=%-3d at=%-6d u32=%-12d deref=%-6d i8=%d i32=%d i64=%d\n"
                  % (i, voff, at, u, at + u, data[at],
                     struct.unpack_from("<i", data, at)[0],
                     struct.unpack_from("<q", data, at)[0]))
    return vt

for i in range(len(f.fields)):
    ft = sch.vector_table(1, i)
    if ft is None:
        continue
    name = ft.string(0)
    if i < 2 or name in ("statusLabel", "somaLocation", "type", "class", "superclass",
                         "somaSide", "bodyId", "flywireType"):
        dump(ft.pos, "field[%d] name=%r" % (i, name))
out.close()
print(open(r"D:\projects\science\tools\scratch_log.txt", encoding="utf-8").read())
