"""Instrument feather_lite's own batch decoder and dump the buffer each field consumes.

Guessing the Arrow buffer plan from lengths has failed twice, so this records what the
decoder actually does, field by field, which makes the structural rule visible.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

TARGET = sys.argv[1] if len(sys.argv) > 1 else r"D:\projects\science\malecns\body-neurotransmitters.feather"

orig_read_batch = F.FeatherFile._read_batch


def traced(self, batch, body_start, dicts, strict=True):
    n_nodes = batch.vector_len(1)
    n_buffers = batch.vector_len(2)
    nodes = [batch.vector_struct_i64(1, i, 16, 0) for i in range(n_nodes)]
    buffers = [(batch.vector_struct_i64(2, i, 16, 0), batch.vector_struct_i64(2, i, 16, 8))
               for i in range(n_buffers)]
    comp = batch.table(3)
    codec = comp.i8(0) if comp is not None else 0
    print("batch: nodes=%d buffers=%d codec=%s fields=%d"
          % (n_nodes, n_buffers, codec, len(self.fields)))

    node_i = [0]
    buf_i = [0]
    log = []
    current = [None]

    def take_buffer():
        off, ln = buffers[buf_i[0]]
        idx = buf_i[0]
        buf_i[0] += 1
        raw = bytes(self.data[body_start + off: body_start + off + ln])
        declared = None
        if ln >= 8:
            declared = struct.unpack_from("<q", raw, 0)[0]
        log.append((current[0], idx, ln, declared))
        if ln == 0:
            return b""
        if codec != 0 and ln >= 8:
            return F.decompress(codec, raw[8:], declared or 0)
        if ln >= 8 and declared and 0 < declared and raw[8:12] == bytes.fromhex("04224d18"):
            return F._lz4_frame(raw[8:])
        return raw

    for field in self.fields:
        current[0] = field.name
        n = nodes[node_i[0]]
        node_i[0] += 1
        try:
            take_buffer()  # validity
            t = field.type_id
            if t == 2:
                take_buffer()
            elif t == 3:
                take_buffer()
            elif t == 5:
                take_buffer()
                take_buffer()
            elif t == 12:
                take_buffer()
                node_i[0] += 1
                take_buffer()
                take_buffer()
        except Exception as e:
            log.append((field.name, -1, -1, str(e)))
            break

    print("%-18s %-6s %-8s %s" % ("field", "type", "nodeN", "buffers (idx,len,declared)"))
    for name, idx, ln, declared in log:
        print("  %-18s %-6s %-8s idx=%-3s len=%-8s declared=%s"
              % (name, "", "", idx, ln, declared))
    print("consumed %d of %d buffers, %d of %d nodes"
          % (buf_i[0], n_buffers, node_i[0], n_nodes))


F.FeatherFile._read_batch = traced
try:
    d = F.FeatherFile(TARGET)
    next(d.iter_batches())
except StopIteration:
    pass
except Exception as e:
    import traceback
    traceback.print_exc()
