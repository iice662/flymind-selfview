import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parquet_lite as P

for path, name in ((r"D:\projects\science\drosophila-brain-model\sugarR.parquet", "sugarR"),
                   (r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet", "connectivity")):
    rgs, _ = P._open_meta(path)
    col = rgs[0].columns[0]
    f = open(path, "rb")
    f.seek(col.data_page_offset)
    buf = f.read(1 << 20)
    r = P._Reader(buf, 0)
    ph = P._read_struct(r)
    comp = ph.get(3)
    payload = buf[r.i:r.i + comp]
    print("== %s: hdrlen=%d uncomp=%s comp=%s  (codec field=%s)" % (name, r.i, ph.get(2), comp, col.codec))
    ln = struct.unpack_from("<I", payload, 0)[0]
    print("   level blob len:", ln, " -> body bytes:", len(payload) - 4 - ln)
    body = payload[4 + ln:]
    n_int = min(6, len(body) // 8)
    vals = struct.unpack_from("<%dq" % n_int, body, 0)
    print("   first int64s:", [hex(v) for v in vals])
    print("   plausible FlyWire ids:", all(7.2e16 < v < 7.3e16 for v in vals if v > 0))
    print("   as float64:", ["%.3f" % v for v in struct.unpack_from("<%dd" % n_int, body, 0)])
