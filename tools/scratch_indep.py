"""Throwaway: independent sequential decoder for body-annotations batch 0."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, _lz4_frame

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

msg, body_start = f._message_at(f.record_batches[0][0])
rb = msg.table(2)
n_nodes, n_bufs = rb.vector_len(1), rb.vector_len(2)
nodes = [(rb.vector_struct_i64(1, i, 16, 0), rb.vector_struct_i64(1, i, 16, 8)) for i in range(n_nodes)]
bufs = [(rb.vector_struct_i64(2, i, 16, 0), rb.vector_struct_i64(2, i, 16, 8)) for i in range(n_bufs)]
print("nodes=%d buffers=%d body_start=%d" % (n_nodes, n_bufs, body_start))

def get(b):
    off, ln = bufs[b]
    if ln == 0:
        return b""
    raw = bytes(data[body_start + off: body_start + off + ln])
    decl = struct.unpack_from("<q", raw, 0)[0]
    payload = raw[8:]
    if payload[:4] == bytes.fromhex("04224d18"):
        out = _lz4_frame(payload)
        assert len(out) == decl, (len(out), decl)
        return out
    return raw

def decomp_check():
    bad = []
    for i, (off, ln) in enumerate(bufs):
        if ln == 0:
            continue
        raw = bytes(data[body_start + off: body_start + off + ln])
        if raw[8:12] != bytes.fromhex("04224d18"):
            bad.append((i, ln))
    return bad

print("buffers whose payload is NOT an lz4 frame:", decomp_check())

# sequential decode of the flat schema order (Arrow's documented order)
node_i = 0
buf_i = 0

def dec(field, depth=0):
    global node_i, buf_i
    n, nulls = nodes[node_i]
    node_i += 1
    t = field.type_id
    v = get(buf_i); buf_i += 1          # validity
    pad = "  " * depth
    if field.dictionary_id is not None:
        idx = get(buf_i); buf_i += 1
        return ("dict", n, len(idx))
    if t == 2:      # Int
        b = get(buf_i); buf_i += 1
        return ("int%d" % field.bit_width, n, len(b))
    if t == 3:      # Float
        b = get(buf_i); buf_i += 1
        return ("float", n, len(b))
    if t in (4, 5):  # Binary/Utf8
        ob = get(buf_i); buf_i += 1
        db = get(buf_i); buf_i += 1
        offs = struct.unpack_from("<%di" % (n + 1), ob, 0)
        ok = all(offs[i] <= offs[i + 1] for i in range(n))
        return ("utf8", n, "offs[0]=%d offs[-1]=%d data=%d monotone=%s"
                % (offs[0], offs[-1], len(db), ok))
    if t == 12:     # List
        ob = get(buf_i); buf_i += 1
        offs = struct.unpack_from("<%di" % (n + 1), ob, 0)
        out = [("list", n, "offs[-1]=%d" % offs[-1], len(ob))]
        for c in field.children:
            out.append(dec(c, depth + 1))
        return out
    return ("type%d" % t, n, "?")

for fl in f.fields:
    try:
        print("%-20s %s" % (fl.name, dec(fl)))
    except Exception as e:
        print("%-20s FAILED at node_i=%d buf_i=%d: %r" % (fl.name, node_i, buf_i, e))
        break
print("consumed nodes=%d/%d buffers=%d/%d" % (node_i, n_nodes, buf_i, n_bufs))
