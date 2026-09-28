import mmap, os, struct
p = r"D:\projects\science\malecns\connectome-weights.feather"
size = os.path.getsize(p)
f = open(p, "rb")
mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
magics = {"zstd": bytes.fromhex("28b52ffd"), "lz4-frame": bytes.fromhex("04224d18"),
          "snappy-stream": bytes.fromhex("ff060000734e61507059")}
# scan the first 20 MB for frame magics
window = mm[:20 << 20]
for name, m in magics.items():
    idx = window.find(m)
    print("%-14s first at %s" % (name, idx))
    if idx >= 0:
        print("   context:", window[max(0,idx-8):idx+24].hex())
# also: where does the first record batch body start?
mlen = struct.unpack_from("<i", window, 12)[0]
body = 8 + 8 + mlen
print("first body offset:", body, "first 32 bytes:", window[body:body+32].hex())
mm.close(); f.close()
