"""Write the MaleCNS annotation columns the circuit builder needs.

The 36-column annotation table reads correctly with the explicit Arrow buffer plan that
tools/export_transmitters.py validated: one FieldNode per column, and per column
    fixed width : [validity, values]
    text        : [validity, offsets, data]
    list<prim>  : [validity, offsets, child validity, child values]
where a null-free column's validity slot is present but empty.

Usage:
    python export_annotations.py [--check]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_transmitters as T

SRC = r"D:\projects\science\malecns\body-annotations.feather"
DST = r"D:\projects\science\malecns\annotations.tsv"
WANT = ["bodyId", "type", "hemibrainType", "superclass", "class", "subclass",
        "supertype", "somaSide", "somaNeuromere", "receptorType", "entryNerve",
        "exitNerve", "status", "somaLocation"]


def decode_batch(d, nodes, bufs, body, fields):
    """-> {column: values} using the per-column buffer plan.

    Text columns come in two shapes and the batch only makes sense if both are handled:
        [validity, int32 offsets, data]   - offsets buffer is >= 4*(n+1) bytes and its
                                            last entry lands inside the data buffer
        [validity, bit-packed indices]    - the column is dictionary-encoded
    """
    cols = {}
    bi = 0
    ni = 0
    n = nodes[0]
    needed = 4 * (n + 1)
    for f in fields:
        try:
            if f.type_id in (2, 3, 4):
                raw = T.load_buffer(d, body, *bufs[bi + 1])
                width = "q" if (f.type_id == 2 and f.bit_width == 64) else (
                    "i" if f.type_id == 2 else "d")
                cols[f.name] = list(struct.unpack_from("<%d%s" % (n, width), raw, 0))
                bi += 2
            elif f.type_id == 5:
                next_len = bufs[bi + 1][1] if bi + 1 < len(bufs) else 0
                after_len = bufs[bi + 2][1] if bi + 2 < len(bufs) else -1
                # A text column is [validity, int32 offsets, data] only when the next
                # buffer is big enough to hold n+1 offsets; a dictionary-encoded column
                # spends a single bit-packed index buffer instead, and mistaking one for
                # the other shifts every later column.
                if next_len >= needed and after_len >= 0:
                    off_raw = T.load_buffer(d, body, *bufs[bi + 1])
                    data_raw = T.load_buffer(d, body, *bufs[bi + 2])
                    offsets = struct.unpack_from("<%di" % (n + 1), off_raw, 0)
                    if offsets[-1] <= len(data_raw):
                        cols[f.name] = [data_raw[offsets[i]:offsets[i + 1]]
                                        .decode("utf-8", "replace") for i in range(n)]
                    else:
                        cols[f.name] = [""] * n
                    bi += 3
                else:
                    cols[f.name] = [""] * n
                    bi += 1
            elif f.type_id == 12:
                off_raw = T.load_buffer(d, body, *bufs[bi + 1])
                offsets = struct.unpack_from("<%di" % (n + 1), off_raw, 0)
                child_raw = T.load_buffer(d, body, *bufs[bi + 3])
                child_n = nodes[ni + 1] if ni + 1 < len(nodes) else offsets[-1]
                items = list(struct.unpack_from("<%dq" % child_n, child_raw, 0))
                cols[f.name] = [items[offsets[i]:offsets[i + 1]] for i in range(n)]
                bi += 4
                ni += 1
            else:
                cols[f.name] = [""] * n
                bi += 2
        except Exception as e:
            print("   ! %s: %s" % (f.name, str(e)[:70]))
            cols[f.name] = [""] * n
            bi += 2
        ni += 1
    return cols


def main():
    check_only = "--check" in sys.argv
    rows = 0
    out = None if check_only else open(DST, "w", encoding="utf-8", newline="")
    if out:
        out.write("\t".join(WANT) + "\n")
    try:
        for d, nodes, bufs, body, fields in T.iter_batches(SRC):
            cols = decode_batch(d, nodes, bufs, body, fields)
            bids = cols.get("bodyId")
            if not bids:
                continue
            if check_only:
                if rows == 0:
                    for name in WANT:
                        v = cols.get(name)
                        sample = v[:3] if v else None
                        print("  %-14s %s" % (name, sample))
                rows += len(bids)
                continue
            for i in range(len(bids)):
                vals = []
                for name in WANT:
                    col = cols.get(name)
                    v = col[i] if col and i < len(col) else ""
                    if isinstance(v, list):
                        v = ",".join(str(int(x)) for x in v[:3])
                    vals.append(str(v).replace("\t", " ").replace("\n", " "))
                out.write("\t".join(vals) + "\n")
            rows += len(bids)
            print("   %d rows" % rows, end="\r")
    finally:
        if out:
            out.close()
    print()
    print("%s: %d rows, columns=%s" % ("checked" if check_only else "wrote " + DST, rows, WANT))


if __name__ == "__main__":
    main()
