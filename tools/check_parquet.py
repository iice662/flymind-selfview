"""Brute-force check: which codec turns the parquet page payloads into something
that decodes as parquet page data?  Also validates the downloaded file against the
size reported by the GitHub API.
"""
import hashlib
import json
import os
import struct
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parquet_lite as P

P_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                      "drosophila-brain-model", "Connectivity_783.parquet")

size = os.path.getsize(P_PATH)
h = hashlib.sha256()
with open(P_PATH, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
print("local size :", size)
print("local sha256:", h.hexdigest()[:32], "...")

try:
    req = urllib.request.Request(
        "https://api.github.com/repos/philshiu/Drosophila_brain_model/contents/Connectivity_783.parquet",
        headers={"User-Agent": "dsh", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        info = json.load(r)
    print("remote size:", info.get("size"), " sha:", info.get("sha"))
except Exception as e:  # network is flaky on this box
    print("remote check failed:", e)

# walk the pages of the first column chunk and try every codec we can reach
meta = P._read_footer(P_PATH)
rgs, leaves = P._open_meta(P_PATH)
col = rgs[0].columns[0]
print("column:", col.name, "codec field:", col.codec, "phys:", col.physical,
      "dict_off:", col.dict_page_offset, "data_off:", col.data_page_offset,
      "chunk_bytes:", col.total_compressed_size)

f = open(P_PATH, "rb")
start = col.dict_page_offset or col.data_page_offset
f.seek(start)
buf = f.read(1 << 16)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
comp = ph.get(3)
payload = buf[r.i:r.i + comp]
print("page type=%s uncomp=%s comp=%s payload=%d bytes" % (ph.get(1), ph.get(2), comp, len(payload)))

candidates = {}
try:
    from compression import zstd
    candidates["zstd"] = zstd.decompress
except Exception as e:
    print("no zstd:", e)
import zlib
candidates["gzip"] = lambda d: zlib.decompress(d, 16 + 15)
candidates["zlib"] = zlib.decompress
candidates["deflate"] = lambda d: zlib.decompress(d, -15)
candidates["snappy"] = P._snappy_decompress

for name, fn in candidates.items():
    try:
        out = fn(payload)
        ids = struct.unpack_from("<6q", out, 0)
        ok = all(7.2e16 < v < 7.3e16 for v in ids if v > 0)
        print("  %-8s OK -> %d bytes (expected %s) plausible_ids=%s first=%s"
              % (name, len(out), ph.get(2), ok, [hex(v) for v in ids[:2]]))
    except Exception as e:
        print("  %-8s fail: %s" % (name, str(e)[:70]))
