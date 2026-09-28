import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
f.seek(4)
buf = f.read(1 << 16)
r = P._Reader(buf, 0)
ph = P._read_struct(r)
print("hdr bytes 0..%d: %s" % (r.i, buf[:r.i].hex()))
print("parsed:", {k: v for k, v in ph.items()})
comp = ph.get(3)
payload = buf[r.i:r.i+comp]
import hashlib
print("payload sha256:", hashlib.sha256(payload).hexdigest()[:24])
# does the payload literally appear inside the file elsewhere (uncompressed copy)?
target = payload[:24]
print("search for payload prefix in first 2MB:", f.seek(0) or open(p,'rb').read(2_000_000).find(target))
# what does the 77504-byte uncompressed dictionary look like if we just take that many bytes?
f.seek(r.i)
raw_guess = f.read(ph.get(2))
print("first 6 int64 of 77504-byte span:", [hex(v) for v in struct.unpack_from("<6q", raw_guess, 0)])
try:
    from compression import zstd
    print("zstd on that span:", len(zstd.decompress(raw_guess)))
except Exception as e:
    print("zstd on that span failed:", str(e)[:60])
try:
    out = P._lz4_block_decompress(payload, None)
    print("lz4 decoded %d bytes (expected %s); first int64: %s" % (len(out), ph.get(2), [hex(v) for v in struct.unpack_from("<3q", out, 0)]))
except Exception as e:
    print("lz4 partial fail:", e)
