import sys, os
sys.path.insert(0, os.getcwd())
import parquet_lite as P
meta = P._read_footer(r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet")
rg0 = meta[4][0]
print("rg0 num_rows:", rg0.get(3))
for i, cc in enumerate(rg0[1][:2]):
    print("== column chunk", i, "keys:", sorted(cc.keys()))
    for k, v in cc.items():
        if k == 1 and isinstance(v, dict):
            print("   meta keys:", sorted(v.keys()))
            for kk, vv in v.items():
                if isinstance(vv, bytes):
                    print("      %s = %s" % (kk, vv[:40]))
                elif isinstance(vv, list) and vv and isinstance(vv[0], dict):
                    print("      %s = <list of %d structs>" % (kk, len(vv)))
                else:
                    print("      %s = %s" % (kk, vv))
        else:
            print("   %s = %s" % (k, v if not isinstance(v, bytes) else v[:40]))
