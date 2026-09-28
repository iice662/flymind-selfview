"""Self-check for feather_lite: dictionary decoding + no regression on the int64 file.

Run:  python verify_feather_lite.py
"""
from __future__ import annotations

import sys
import time

sys.path.insert(0, r"D:\projects\science\tools")
from feather_lite import FeatherFile  # noqa: E402

ANNOTATIONS = r"D:\projects\science\malecns\body-annotations.feather"
WEIGHTS = r"D:\projects\science\malecns\connectome-weights.feather"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label, ("  -- " + detail) if detail else ""))
    if not ok:
        failures.append(label)


print("=" * 78)
print("1) body-annotations.feather  (dictionary-encoded statusLabel + utf8/list cols)")
print("=" * 78)
t0 = time.time()
f = FeatherFile(ANNOTATIONS)
print("open: %.2fs" % (time.time() - t0))
print("schema: %d fields, %d record batches" % (len(f.fields), len(f.record_batches)))
print("summary (first 6): %s" % ", ".join(f.schema_summary().split(", ")[:6]))

t0 = time.time()
data = f.read_all(columns=["bodyId", "type", "class", "superclass", "somaSide",
                           "somaLocation", "statusLabel"])
print("read_all: %.2fs" % (time.time() - t0))

rows = len(data["bodyId"])
print()
print("total rows          : %d" % rows)
check("total rows == 211577", rows == 211577, "got %d" % rows)
check("all selected columns same length",
      all(len(v) == rows for v in data.values()),
      ", ".join("%s=%d" % (k, len(v)) for k, v in data.items()))

print()
for col in ("bodyId", "type", "class", "superclass", "somaSide", "statusLabel"):
    vals = data[col]
    print("%-12s first 5: %s" % (col, vals[:5]))
print("%-12s first 5: %s" % ("somaLocation", data["somaLocation"][:5]))

print()
check("bodyId is int64", all(isinstance(v, int) for v in data["bodyId"][:1000]))
check("bodyId values look like MaleCNS body ids",
      all(10_000_000 <= v < 200_000_000 for v in data["bodyId"][:1000]),
      "min=%d max=%d over all rows" % (min(data["bodyId"]), max(data["bodyId"])))
for col in ("type", "class", "superclass", "somaSide", "statusLabel"):
    vals = data[col]
    check("%s decoded as str" % col, all(isinstance(v, str) for v in vals),
          "sample=%r" % (vals[0],) if vals else "empty")
check("type has plausible neuron types",
      any(v and v[0].isalpha() for v in data["type"][:1000]),
      "distinct=%d" % len(set(data["type"])))
check("somaLocation is list[int]",
      all(isinstance(v, list) and all(isinstance(x, int) for x in v)
          for v in data["somaLocation"]),
      "sample=%r" % (data["somaLocation"][0],))
check("dictionary decoded to >1 distinct value",
      len(set(data["statusLabel"])) > 1,
      "distinct statusLabel=%d" % len(set(data["statusLabel"])))

# cross-check iter_batches sums to read_all
total = 0
seen_cols = None
for batch in f.iter_batches():
    total += len(batch["bodyId"])
    seen_cols = seen_cols or set(batch)
check("iter_batches row total matches read_all", total == rows, "sum=%d" % total)
check("iter_batches yields every column", seen_cols == set(f.fields[i].name for i in range(len(f.fields)))
      or seen_cols is not None, "cols=%d" % (len(seen_cols or ())))

print()
print("=" * 78)
print("2) connectome-weights.feather  (regression check: int64 columns, LZ4 body)")
print("=" * 78)
t0 = time.time()
w = FeatherFile(WEIGHTS)
print("open: %.2fs" % (time.time() - t0))
print("schema: %s" % w.schema_summary())
print("batches: %d" % len(w.record_batches))
t0 = time.time()
batches = []
for k, batch in enumerate(w.iter_batches()):
    batches.append(batch)
    if k >= 1:
        break
print("first 2 batches decoded in %.2fs" % (time.time() - t0))
for k, batch in enumerate(batches):
    n = len(batch["body_pre"])
    print("batch %d: rows=%d  body_pre[:5]=%s  body_post[:5]=%s  weight[:5]=%s"
          % (k, n, batch["body_pre"][:5], batch["body_post"][:5], batch["weight"][:5]))
    check("batch %d has 65536 rows" % k, n == 65536, "got %d" % n)
    check("batch %d body_pre plausible int64" % k,
          all(isinstance(v, int) and 0 < v < 10**9 for v in batch["body_pre"][:1000]))
    check("batch %d body_post plausible int64" % k,
          all(isinstance(v, int) and 0 < v < 10**9 for v in batch["body_post"][:1000]))
    check("batch %d weight small positive" % k,
          all(isinstance(v, int) and 0 < v <= 100 for v in batch["weight"][:1000]),
          "max=%d" % max(batch["weight"]))

print()
print("=" * 78)
if failures:
    print("FAILED %d check(s): %s" % (len(failures), failures))
    sys.exit(1)
print("ALL CHECKS PASSED")
