"""Throwaway: dump RecordBatch 0 node/buffer layout of body-annotations."""
import struct, sys
sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile, _lz4_frame, decompress

P = r"D:\projects\science\malecns\body-annotations.feather"
f = FeatherFile(P)
data = f.data

# first record batch frame
pos = f.record_batches[0][0]
msg, body_start = f._message_at(pos)
rb = msg.table(2)
print("batch frame@%d body_start=%d body_len=%d" % (pos, body_start, msg.i64(3)))
print("length=%d" % rb.i64(0))
n_nodes, n_bufs = rb.vector_len(1), rb.vector_len(2)
print("nodes=%d buffers=%d" % (n_nodes, n_bufs))
comp = rb.table(3)
print("compression=%s" % (None if comp is None else comp.i8(0)))

print("\nschema walk (name, node idx, buffers):")
node_i = 0
buf_i = 0
def walk(field, depth=0):
    global node_i, buf_i
    my_node = node_i
    n = rb.vector_struct_i64(1, node_i, 16, 0)
    nc = rb.vector_struct_i64(1, node_i, 16, 8)
    node_i += 1
    kind = field.kind()
    if field.type_id == 12 and field.children:
        kind = "list<%s>" % field.children[0].kind()
    line = "  %s%-16s node#%d len=%d nulls=%d" % ("  " * depth, field.name, my_node, n, nc)
    owned = []
    if field.dictionary_id is not None:
        owned = [buf_i, buf_i + 1]
    elif field.type_id == 12:
        owned = [buf_i, buf_i + 1]
    else:
        owned = [buf_i]
    print(line + " bufs=%s" % owned)
    for b in owned:
        off, ln = rb.vector_struct_i64(2, b, 16, 0), rb.vector_struct_i64(2, b, 16, 8)
        print("%s     buf#%d off=%d len=%d" % ("  " * depth, b, off, ln))
    buf_i += len(owned)
    for c in field.children:
        walk(c, depth + 1)

for fl in f.fields:
    walk(fl)
print("consumed nodes=%d/%d buffers=%d/%d" % (node_i, n_nodes, buf_i, n_bufs))
