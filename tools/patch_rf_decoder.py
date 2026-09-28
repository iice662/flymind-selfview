"""Point tools/receptive_field.py at the schema-driven decoder (tools/arrow_columns.py)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, "tools", "receptive_field.py")
s = open(p, encoding="utf-8").read()
before = s
s = s.replace("from export_annotations import decode_batch",
              "from arrow_columns import decode_planned")
s = s.replace("cols = decode_batch(d, nodes, bufs, body, fields)",
              "cols, _used, _notes = decode_planned(d, nodes, bufs, body, fields)")
s = s.replace('pp = cols.get("primary_post")',
              'pp = cols.get("primary_post#index", cols.get("primary_post"))')
if s != before:
    open(p, "w", encoding="utf-8").write(s)
print("decode_planned" in s and "receptive_field.py now uses the schema-driven decoder"
      or "PATCH FAILED")
