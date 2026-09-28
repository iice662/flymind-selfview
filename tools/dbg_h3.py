import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P
p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb"); f.seek(16712)
buf = f.read(60000)
r = P._Reader(buf, 0); ph = P._read_struct(r)
comp = ph.get(3); payload = buf[r.i:r.i+comp]
# treat as PLAIN float32: is it a plausible Excitatory/Connectivity style value?
print("as float32:", struct.unpack_from("<8f", payload, 0))
# treat payload as def-level RLE blob: 4-byte LE length prefix
ln = struct.unpack_from("<I", payload, 0)[0]
print("as RLE length prefix:", ln, "vs payload", len(payload))
# try: RLE blob at [4:4+ln], then bit-packed dictionary indices
if 0 < ln < len(payload):
    body = payload[4+ln:]
    print("body bytes:", len(body), "-> first 8:", body[:8].hex())
    try:
        idx = P._decode_rle_hybrid(body, 14, 20)
        print("first 20 dict indices (bw=14):", idx)
    except Exception as e:
        print("rle decode failed:", e)
# is the whole thing maybe two concatenated lz4 blocks? check for lz4 frame magic
print("contains lz4 frame magic:", payload.find(bytes.fromhex("04224d18")))
print("contains zstd magic:", payload.find(bytes.fromhex("28b52ffd")))
print("contains snappy stream magic:", payload.find(bytes.fromhex("ff060000734e61507059")))
