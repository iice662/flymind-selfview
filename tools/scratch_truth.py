"""Throwaway: ground-truth byte walk of the DictionaryBatch frame, log to file."""
import struct

P = r"D:\projects\science\malecns\body-annotations.feather"
dev = open(P, "rb")
data = dev.read(8000)
log = open(r"D:\projects\science\tools\scratch_log.txt", "w", encoding="utf-8")

def w(s):
    log.write(s + "\n")

def u32(p): return struct.unpack_from("<I", data, p)[0]
def i32(p): return struct.unpack_from("<i", data, p)[0]
def i64(p): return struct.unpack_from("<q", data, p)[0]
def i16(p): return struct.unpack_from("<h", data, p)[0]

def dump_table(addr, label):
    vt = addr - i32(addr)
    vlen = struct.unpack_from("<H", data, vt)[0]
    w("%s Table.at(%d): vtable=%d vlen=%d fields=%d" % (label, addr, vt, vlen, max(0, (vlen - 4) // 2)))
    for fi in range(max(0, (vlen - 4) // 2)):
        e = vt + 4 + fi * 2
        if vt + vlen > len(data) or e + 2 > len(data):
            w("   field %d: vtable out of range" % fi)
            continue
        voff = struct.unpack_from("<H", data, e)[0]
        if voff == 0 or addr + voff + 4 > len(data):
            w("   field %d: absent" % fi)
            continue
        at = addr + voff
        w("   field %d: voff=%d at=%d u32=%d deref=%d i64=%d" % (fi, voff, at, u32(at), at + u32(at), i64(at) if at + 8 <= len(data) else -1))
    return vt, vlen

# --- frame at 6728
w("=== frame at 6728")
w("first u32 = 0x%08X  next i32 = %d" % (u32(6728), i32(6732)))
root_at, meta_len = 6736, i32(6732)
w("root uoffset pos=%d meta_len=%d body_start=%d" % (root_at, meta_len, root_at + meta_len))
msg_addr, msg_len = root_at, i32(6728)      # message flatbuffer
msg = root_at + u32(root_at)
w("Message table addr=%d" % msg)
dump_table(msg, "Message")
w("version=%d header_type=%d bodyLength=%d" % (i16(msg + 4), data[msg + 6], i64(msg + 16)))

hdr_addr = i32(msg + 8) + msg + 8
w("Message.header -> %d" % hdr_addr)
dump_table(hdr_addr, "DictionaryBatch")
w("DictionaryBatch.isDelta(byte at +10)=%d" % data[hdr_addr + 10])

# DictionaryBatch.data is field 1 -> uoffset at hdr_addr+4
d_slot = hdr_addr + 4
d_target = d_slot + u32(d_slot)
w("DictionaryBatch.data uoffset slot=%d value=%d -> %d" % (d_slot, u32(d_slot), d_target))
rb = d_target
dump_table(rb, "RecordBatch")

# RecordBatch fields via its vtable
vt = rb - i32(rb)
def slot(fi):
    e = vt + 4 + fi * 2
    voff = struct.unpack_from("<H", data, e)[0]
    return None if voff == 0 else rb + voff

s_len, s_nodes, s_bufs, s_comp = slot(0), slot(1), slot(2), slot(3)
w("RecordBatch.length slot=%s value=%s" % (s_len, None if s_len is None else i64(s_len)))
w("RecordBatch.nodes slot=%s uoffset=%s -> %s" % (s_nodes, None if s_nodes is None else u32(s_nodes), None if s_nodes is None else s_nodes + u32(s_nodes)))
w("RecordBatch.buffers slot=%s uoffset=%s -> %s" % (s_bufs, None if s_bufs is None else u32(s_bufs), None if s_bufs is None else s_bufs + u32(s_bufs)))
w("RecordBatch.compression slot=%s" % s_comp)

nv = s_nodes + u32(s_nodes)
nnodes = u32(nv - 4)
w("nodes vector: count=%d at %d" % (nnodes, nv))
for i in range(nnodes):
    w("   node %d: length=%d null_count=%d" % (i, i64(nv + i * 16), i64(nv + i * 16 + 8)))
bv = s_bufs + u32(s_bufs)
nbufs = u32(bv - 4)
w("buffers vector: count=%d at %d" % (nbufs, bv))
for i in range(nbufs):
    w("   buffer %d: offset=%d length=%d" % (i, i64(bv + i * 16), i64(bv + i * 16 + 8)))

log.close()
with open(r"D:\projects\science\tools\scratch_log.txt", encoding="utf-8") as fh:
    print(fh.read())
