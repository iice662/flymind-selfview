import sys, os, struct, random
sys.path.insert(0, os.getcwd())
import parquet_lite as P

def lz4_compress_literal_only(data):
    """Emit a valid LZ4 block using only literal runs (never matches)."""
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        run = min(n - i, 0x7FFFFFF0)
        lit = run
        token = 0
        if lit >= 15:
            token = 0xF0
            out.append(token)
            rem = lit - 15
            while rem >= 255:
                out.append(255); rem -= 255
            out.append(rem)
        else:
            out.append(lit << 4)
        out += data[i:i + lit]
        i += lit
    return bytes(out)

rng = random.Random(7)
for size in (1, 14, 15, 16, 300, 70000):
    data = bytes(rng.randrange(256) for _ in range(size))
    packed = lz4_compress_literal_only(data)
    try:
        got = P._lz4_block_decompress(packed, size)
        print("  size %-6d literal-only block roundtrip: %s" % (size, "OK" if got == data else "MISMATCH"))
    except Exception as e:
        print("  size %-6d FAIL %s" % (size, e))

# also verify a match-bearing vector by hand: 3 literals + match(offset 3, len 6) => "abcabcabc"
payload = bytes([0x32]) + b"abc" + struct.pack("<H", 3) + bytes([0x20])
# token 0x32: 3 literals, matchlen nibble 2 -> 2+4=6
print("  handcrafted match vector:", P._lz4_block_decompress(payload, 9))
