"""Scan parquet page payloads for known compression frames, to settle which codec a
file really uses."""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parquet_lite as P

MAGICS = {
    "zstd": bytes.fromhex("28b52ffd"),
    "lz4-frame": bytes.fromhex("04224d18"),
    "snappy-stream": bytes.fromhex("ff060000734e61507059"),
    "gzip": bytes.fromhex("1f8b08"),
    "brotli-stream": bytes.fromhex("ceb2cf81"),
    "lz4-skippable": bytes.fromhex("502a4d18"),
}


def scan(path, max_pages=6):
    rgs, _ = P._open_meta(path)
    f = open(path, "rb")
    print("== %s (%d row groups)" % (os.path.basename(path), len(rgs)))
    for gi in range(min(len(rgs), 3)):
        rg = rgs[gi]
        for col in rg.columns[:3]:
            start = col.dict_page_offset or col.data_page_offset
            if not start:
                continue
            f.seek(start)
            buf = f.read(1 << 20)
            r = P._Reader(buf, 0)
            ph = P._read_struct(r)
            comp = ph.get(3)
            payload = buf[r.i:r.i + comp]
            hits = [name for name, m in MAGICS.items() if m in payload]
            print("   rg%d %-28s codec=%s hdr=%d payload=%d  frames=%s  starts=%s"
                  % (gi, col.name, col.codec, r.i, len(payload), hits or "none",
                     payload[:6].hex()))
            break


for p in sys.argv[1:]:
    scan(p)
