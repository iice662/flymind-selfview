"""Read the MaleCNS neurotransmitter table and write bodyId -> transmitter.

The Arrow schema is now parsed exactly (tools/feather_lite.py), and for this table the
buffer plan is unambiguous: each field contributes one FieldNode, and each column's
buffers are [validity?, values] for fixed width or [validity?, offsets, data] for text.
The validity slot is *present but empty* when a column has no nulls, so a fixed-width
plan is used for all 10 columns and the resulting count (25) matches the batch exactly.

Usage:
    python export_transmitters.py            # writes malecns/transmitters.tsv
    python export_transmitters.py --check    # prints value distributions only
"""
import collections
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

SRC = r"D:\projects\science\malecns\body-neurotransmitters.feather"
DST = r"D:\projects\science\malecns\transmitters.tsv"


def plan(fields):
    """-> list of (field, [buffer indices]) using the fixed-width Arrow plan."""
    out = []
    i = 0
    for f in fields:
        n = 3 if f.type_id == 5 else 2
        out.append((f, list(range(i, i + n))))
        i += n
    return out, i


def load_buffer(d, body, off, ln, expect=None):
    """Read one Arrow buffer.

    Fixed-width columns are an int64 uncompressed-size prefix followed by an LZ4 frame.
    Text columns keep their *offsets* buffer without a prefix (its compressed length is
    not smaller than the stored bytes), so the prefix is stripped only when the declared
    size is smaller than the stored bytes.  `expect` lets callers document the size they
    need, but the unwrapping itself must stay size-agnostic: an earlier attempt to drive
    it by `expect` corrupted the string columns.
    """
    raw = bytes(d.data[body + off: body + off + ln])
    if ln == 0:
        return b""
    declared = struct.unpack_from("<q", raw, 0)[0]
    if raw[8:12] == bytes.fromhex("04224d18"):
        return F._lz4_frame(raw[8:])
    if 0 < declared < ln:
        return raw[8:]
    return raw


def iter_batches(path):
    """Walk every record batch: yields (nodes, buffers, body_start, fields)."""
    d = F.FeatherFile(path)
    pos = 8
    while pos < len(d.data) - 10:
        root_at, mlen = d._frame(pos)
        msg = F.Table(d.data, root_at)
        mtype = msg.i8(1, 0)
        body_len = msg.i64(3, 0)
        if mtype == 3:
            rb = msg.table(2) or msg.table(1)
            nodes = [rb.vector_struct_i64(1, i, 16, 0) for i in range(rb.vector_len(1))]
            bufs = [(rb.vector_struct_i64(2, i, 16, 0), rb.vector_struct_i64(2, i, 16, 8))
                    for i in range(rb.vector_len(2))]
            yield d, nodes, bufs, root_at + mlen, d.fields
        pos = root_at + mlen + body_len


def main():
    check_only = "--check" in sys.argv
    total = 0
    written = 0
    hist = collections.Counter()
    # --check must not touch the destination: it used to open DST for writing anyway,
    # which truncated an already-generated transmitters.tsv down to its header line.
    out = open(DST, "w", encoding="utf-8", newline="") if not check_only else None
    try:
        if out:
            out.write("bodyId\ttransmitter\n")
        for d, nodes, bufs, body, fields in iter_batches(SRC):
            assigned, consumed = plan(fields)
            if consumed != len(bufs):
                print("  skip batch: plan %d != buffers %d" % (consumed, len(bufs)))
                continue
            ids = None
            cols = {}
            for f, idxs in assigned:
                n = nodes[0]
                if f.type_id == 2:
                    width = "q" if f.bit_width == 64 else "i"
                    raw = load_buffer(d, body, *bufs[idxs[-1]],
                                      expect=n * (8 if f.bit_width == 64 else 4))
                    vals = list(struct.unpack_from("<%d%s" % (n, width), raw, 0))
                elif f.type_id == 5:
                    off_raw = load_buffer(d, body, *bufs[idxs[1]], expect=4 * (n + 1))
                    data_raw = load_buffer(d, body, *bufs[idxs[2]])
                    offsets = struct.unpack_from("<%di" % (n + 1), off_raw, 0)
                    if offsets[-1] > len(data_raw):
                        cols[f.name] = None
                        continue
                    vals = [data_raw[offsets[i]:offsets[i + 1]].decode("utf-8", "replace")
                            for i in range(n)]
                else:
                    continue
                if f.name == "body":
                    ids = vals
                cols[f.name] = vals
            if ids is None or cols.get("consensus_nt") is None:
                continue
            nts = cols["consensus_nt"]
            total += len(ids)
            for bid, nt in zip(ids, nts):
                hist[nt] += 1
                if not nt or nt == "unclear":
                    continue
                if out:
                    out.write("%d\t%s\n" % (bid, nt))
                written += 1
            print("   %d rows so far" % total, end="\r")
    finally:
        if out:
            out.close()
    print()
    print("transmitter distribution:", dict(hist.most_common(8)))
    print(("checked only; %s left untouched" % DST) if check_only
          else "wrote %s: %d of %d bodies labelled" % (DST, written, total))


if __name__ == "__main__":
    main()
