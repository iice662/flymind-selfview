import sys, os, struct
sys.path.insert(0, os.getcwd())
import parquet_lite as P

# --- LZ4 block decoder unit tests (hand-built vectors) ---
cases = [
    # literals only: token 0x40 -> 4 literals "abcd", no match
    (bytes([0x40]) + b"abcd", b"abcd", "literals only"),
    # 4 literals then a 4-byte match at offset 4: "abcdabcd"
    (bytes([0x40]) + b"abcd" + struct.pack("<H", 4) + bytes([0x00]), b"abcdabcd", "one match"),
    # overlapping match: "aaaa" + offset1 len5 -> "aaaaaaaaa"
    (bytes([0x40]) + b"aaaa" + struct.pack("<H", 1) + bytes([0x40]), b"a" * 9, "overlapping"),
    # extended literal length: token 0xF0 + 0x02 -> 15+2 = 17 literals
    (bytes([0xF0, 0x02]) + b"0123456789abcdefg", b"0123456789abcdefg", "long literals"),
]
for payload, expect, name in cases:
    try:
        got = P._lz4_block_decompress(payload, len(expect))
        print("  %-16s OK" % name if got == expect else "  %-16s MISMATCH %r" % (name, got))
    except Exception as e:
        print("  %-16s FAIL %s" % (name, e))
