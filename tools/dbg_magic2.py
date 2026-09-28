p = r"D:\projects\science\drosophila-brain-model\Connectivity_783.parquet"
f = open(p, "rb")
data = f.read(300000)
for name, hexmagic in (("snappy-stream", "ff060000734e61507059"), ("lz4-frame", "04224d18"),
                       ("gzip", "1f8b"), ("zlib", "789c"), ("brotli-ish", "ceb2cf81"),
                       ("zstd-skippable", "50 2a 4d 18".replace(" ","")), ("zstd", "28b52ffd")):
    m = bytes.fromhex(hexmagic)
    print("%-16s %s -> idx %s" % (name, hexmagic, data.find(m)))
print("brotli first 16 payload bytes of dict page:", data[24:40].hex())
