"""Throwaway: prove the exact structure of _read_batch's decode by replacing it wholesale."""
import struct
import sys
sys.path.insert(0, r"D:\projects\science\tools")
import feather_lite as FL

P = r"D:\projects\science\malecns\body-annotations.feather"

def read_batch(self, batch, body_start, dicts, strict=True):
    n_nodes = batch.vector_len(1)
    n_bufs = batch.vector_len(2)
    nodes = [(batch.vector_struct_i64(1, i, 16, 0), batch.vector_struct_i64(1, i, 16, 8))
             for i in range(n_nodes)]
    bufs = [(batch.vector_struct_i64(2, i, 16, 0), batch.vector_struct_i64(2, i, 16, 8))
            for i in range(n_bufs)]
    comp = batch.table(3)
    codec = comp.i8(0) if comp is not None else 0
    st = {"n": 0, "b": 0}

    def get():
        off, ln = bufs[st["b"]]
        st["b"] += 1
        if ln == 0:
            return b""
        raw = bytes(self.data[body_start + off: body_start + off + ln])
        if ln >= 8:
            decl = struct.unpack_from("<q", raw, 0)[0]
            payload = raw[8:]
            if payload[:4] == bytes.fromhex("04224d18"):
                return FL._lz4_frame(payload)
            if payload[:4] == bytes.fromhex("28b52ffd"):
                from compression import zstd
                return zstd.decompress(payload)
        return raw

    def col(field):
        n = nodes[st["n"]][0]
        st["n"] += 1
        get()                       # validity
        t = field.type_id
        if t == FL.T_INT:
            return FL._decode_ints(get(), field.bit_width or 32, n)
        if t == FL.T_FLOATINGPOINT:
            b = get()
            return list(struct.unpack_from("<%dd" % n, b, 0)) if n else []
        if t == FL.T_BOOL:
            b = get()
            return [bool((b[i >> 3] >> (i & 7)) & 1) for i in range(n)]
        if t in (FL.T_UTF8, FL.T_BINARY, FL.T_LARGE_UTF8, FL.T_LARGE_BINARY):
            ob, db = get(), get()
            offs = struct.unpack_from("<%di" % (n + 1), ob, 0)
            raw = [db[offs[i]:offs[i + 1]] for i in range(n)]
            if t in (FL.T_UTF8, FL.T_LARGE_UTF8):
                return [v.decode("utf-8", "replace") for v in raw]
            return raw
        if t in (FL.T_LIST, FL.T_LARGE_LIST):
            ob = get()
            offs = struct.unpack_from("<%di" % (n + 1), ob, 0)
            child = field.children[0] if field.children else None
            if child is None:
                st["n"] += 1
                get(); get()
                return [[] for _ in range(n)]
            cv = col(child)
            return [cv[offs[i]:offs[i + 1]] for i in range(n)]
        if field.dictionary_id is not None:
            pass
        raise ValueError("unsupported %d" % t)

    def col_dict(field):
        n = nodes[st["n"]][0]
        st["n"] += 1
        get()
        idx = get()
        bw = field.bit_width or 32
        idxs = (FL._decode_bitpacked(idx, bw, n) if bw in (1, 2, 4)
                else FL._decode_ints(idx, bw, n))
        table = dicts.get(field.dictionary_id)
        if table is None:
            return idxs
        return [table[i] if 0 <= i < len(table) else None for i in idxs]

    out = {}
    for field in self.fields:
        out[field.name] = col_dict(field) if field.dictionary_id is not None else col(field)
    print("consumed nodes %d/%d buffers %d/%d" % (st["n"], n_nodes, st["b"], n_bufs))
    return out

f = FL.FeatherFile(P)
f._read_batch = lambda b, bs, d, strict=True: read_batch(f, b, bs, d, strict)
for k, batch in enumerate(f.iter_batches()):
    print("batch %d rows=%d" % (k, len(batch["bodyId"])))
    print("   bodyId[:5]    =", batch["bodyId"][:5])
    print("   type[:5]      =", batch["type"][:5])
    print("   class[:5]     =", batch["class"][:5])
    print("   superclass[:5]=", batch["superclass"][:5])
    print("   somaSide[:5]  =", batch["somaSide"][:5])
    print("   somaLocation[:3] =", batch["somaLocation"][:3])
    print("   statusLabel[:5]  =", batch["statusLabel"][:5])
    if k >= 0:
        break
