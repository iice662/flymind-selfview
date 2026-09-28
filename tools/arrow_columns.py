"""Deterministic Arrow IPC column decoding (replaces the size-based heuristic).

The heuristic in export_annotations.decode_batch guessed each column's buffer width from the size
of the following buffer; one wrong guess shifted every later column, which is why `primary_post`,
`type`, `somaSide` and `somaLocation` all decoded as empty strings (results/CORRECTION.md).

Arrow's record-batch layout is deterministic per column *type*, so it is read from the schema
instead of guessed (see export_transmitters.plan):

    Int (2), FloatingPoint (3), Bool (1)   -> [validity, data]          2 buffers
    Utf8 (5), Binary (4)                   -> [validity, offsets, data] 3 buffers
    anything else (e.g. Dictionary, 23)    -> skipped, reported

    from arrow_columns import decode_planned
    cols, consumed, skipped = decode_planned(d, nodes, bufs, body, fields)

Usage (self-test on the first batch of a file):
    python tools/arrow_columns.py malecns/syn-partners.feather
"""
import csv
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_transmitters as T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT, FLOAT, UTF8 = 2, 3, 5


def decode_planned(d, nodes, bufs, body, fields):
    """-> ({column: values}, buffers consumed, [notes]).

    Buffer width comes from the schema type (Int/Float 2, plain Utf8 3).  A text column that is
    *dictionary-encoded* has only [validity, indices] in the record batch and its values live in a
    separate DictionaryBatch, so when the schema plan would overrun the batch we fall back to 2
    buffers and decode the column as integer dictionary indices: the index is a stable identifier
    of the compartment, and it is enough to group sites (the names are only labels).
    """
    n = nodes[0]
    plan, total = T.plan(fields)
    overrun = total > len(bufs)
    cols, notes = {}, []
    i = 0
    for f in plan:
        f, idx = f
        fid = getattr(f, "type_id", None)
        want = len(idx)
        if i + want > len(bufs):
            want = 2                                   # dictionary-encoded: [validity, indices]
        idx = list(range(i, i + want))
        i += want
        try:
            if fid == INT:
                raw = T.load_buffer(d, body, *bufs[idx[1]])
                fmt = "<%dq" % n if len(raw) >= 8 * n else "<%di" % n
                cols[f.name] = list(struct.unpack_from(fmt, raw, 0))
            elif fid == FLOAT:
                raw = T.load_buffer(d, body, *bufs[idx[1]])
                fmt = "<%dd" % n if len(raw) >= 8 * n else "<%df" % n
                cols[f.name] = list(struct.unpack_from(fmt, raw, 0))
            elif fid == UTF8 and want == 3:
                off_raw = T.load_buffer(d, body, *bufs[idx[1]], expect=4 * (n + 1))
                data_raw = T.load_buffer(d, body, *bufs[idx[2]])
                offs = struct.unpack_from("<%di" % (n + 1), off_raw, 0)
                cols[f.name] = [data_raw[offs[k]:offs[k + 1]].decode("utf-8", "replace")
                                for k in range(n)]
            elif fid == UTF8:                          # dictionary indices
                raw = T.load_buffer(d, body, *bufs[idx[1]])
                fi = "<%dd" % n if len(raw) >= 8 * n else "<%di" % n
                cols[f.name + "#index"] = list(struct.unpack_from(fi, raw, 0))
                notes.append("%s: dictionary-encoded, decoded as indices" % f.name)
            else:
                notes.append("%s: type %s skipped" % (getattr(f, "name", "?"), fid))
        except Exception as e:                                  # keep the rest decodable
            notes.append("%s(type %s: %s)" % (getattr(f, "name", "?"), fid, str(e)[:40]))
    if overrun:
        notes.append("plan %d > buffers %d: dictionary fallback applied" % (total, len(bufs)))
    return cols, i, notes


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "malecns", "syn-partners.feather")
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    for d, nodes, bufs, body, fields in T.iter_batches(path):
        cols, consumed, skipped = decode_planned(d, nodes, bufs, body, fields)
        print(f"rows in batch 0: {nodes[0]}; buffers {len(bufs)}, plan consumed {consumed}")
        if skipped:
            print("skipped:", skipped)
        for name in cols:
            v = cols[name][:3]
            print(f"  {name:<16} {str(v)[:78]}")
        return 0
    print("no batches")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
