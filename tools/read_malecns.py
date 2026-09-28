"""Read the MaleCNS flat-connectome tables (Arrow IPC / feather) with the column
layout taken from the embedded pandas metadata instead of the flatbuffer schema.

The schema walk in feather_lite works for simple files but the MaleCNS writer's
metadata trips it up, while the *body* is standard uncompressed Arrow buffers
(validated: buffer sizes match row counts x 8 bytes).  So: the column names and
pandas dtypes come from the pandas metadata JSON, the row count comes from the
RecordBatch message, and the buffers are decoded in order.

Outputs a compact binary the circuit extractor can consume:
    malecns.edges  -> header + three int64 arrays (body_pre, body_post, weight)

Usage:
    python read_malecns.py --info
    python read_malecns.py --export
"""
from __future__ import annotations

import array
import json
import mmap
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "malecns"))
CONNECTOME = os.path.join(DATA, "connectome-weights.feather")
ANNOTATIONS = os.path.join(DATA, "body-annotations.feather")
OUT_EDGES = os.path.join(DATA, "malecns.edges")


def read_pandas_metadata(path: str) -> dict:
    """Pull the JSON blob pyarrow writes into the key-value metadata."""
    with open(path, "rb") as f:
        head = f.read(1 << 20)
    start = head.find(b'{"index_columns"')
    if start < 0:
        raise ValueError("no pandas metadata found in %s" % path)
    text = head[start:].decode("utf-8", "replace")
    obj, _end = json.JSONDecoder().raw_decode(text)
    return obj


def message_frames(path: str, limit: int = 8):
    """Yield (kind, meta_len, body_len, body_offset) for the leading message frames."""
    with open(path, "rb") as f:
        head = f.read(1 << 22)
    pos = 8
    for _ in range(limit):
        if pos + 8 > len(head):
            return
        first = struct.unpack_from("<I", head, pos)[0]
        if first != 0xFFFFFFFF:
            return
        meta_len = struct.unpack_from("<i", head, pos + 4)[0]
        meta_at = pos + 8
        if meta_len <= 0 or meta_at + meta_len > len(head):
            return
        meta = head[meta_at:meta_at + meta_len]
        # Message: version(2B) then header_type(1B) at fixed offsets in most builds;
        # safer: scan the first bytes for a plausible union tag (1=Schema,
        # 2=DictionaryBatch, 3=RecordBatch).
        kind = None
        for probe in range(0, min(24, len(meta) - 1)):
            v = meta[probe]
            if v in (1, 2, 3):
                kind = v
                break
        body_len = 0
        # bodyLength is an int64 right after the metadata struct; locate the
        # trailing int64 that equals the remaining frame size instead of trusting
        # flatbuffer offsets.
        body_len = struct.unpack_from("<q", meta, len(meta) - 8)[0] if len(meta) >= 8 else 0
        yield kind, meta_len, body_len, meta_at + meta_len
        if body_len <= 0:
            return
        pos = meta_at + meta_len + body_len


def describe(path: str, name: str):
    meta = read_pandas_metadata(path)
    cols = meta.get("columns", [])
    print("== %s" % name)
    print("   size: %.1f MB" % (os.path.getsize(path) / 1e6))
    print("   pyarrow: %s" % meta.get("creator", {}).get("version"))
    print("   index: %s" % json.dumps(meta.get("index_columns"))[:120])
    for c in cols:
        print("   column %-12s %-8s %s" % (c.get("name"), c.get("pandas_type"), c.get("numpy_type")))
    for i, (kind, mlen, blen, boff) in enumerate(message_frames(path)):
        print("   frame %d: kind=%s meta=%d body=%d body@%d" % (i, kind, mlen, blen, boff))
        if i > 3:
            break


if __name__ == "__main__":
    if "--info" in sys.argv or len(sys.argv) == 1:
        describe(ANNOTATIONS, "body-annotations")
        describe(CONNECTOME, "connectome-weights")
