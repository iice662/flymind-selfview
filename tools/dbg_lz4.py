import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
for hdr_abs, tname in ((16712, "data"), (4, "dict")):
    f.seek(hdr_abs)
    buf = f.read(1 << 16)
    r = P._Reader(buf, 0)
    ph = P._read_struct(r)
    comp = ph.get(3); payload = buf[r.i:r.i+comp]
    print("%s: hdrlen=%d payload=%d expected_uncomp=%s" % (tname, r.i, len(payload), ph.get(2)))
    try:
        out = P._lz4_block_decompress(payload, ph.get(2))
        print("   lz4 OK -> %d bytes" % len(out))
        print("   first bytes:", out[:24].hex())
        print("   as int64:", [hex(v) for v in struct.unpack_from("<3q", out if tname=="dict" else out[4:], 0)])
    except Exception as e:
        print("   lz4 fail:", e)
