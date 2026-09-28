"""Inspect a .tmod: read its header, hashes, and the embedded file list.

The tModLoader container is `TMOD` + version string + deflate(FILE_* / INFO...) with a
hashes and signature trailer, so the useful part (which files got packed) is inside the
deflate stream.  Written to confirm the installed .tmod really contains the build that
was just made, rather than trusting timestamps.
"""
import os
import re
import struct
import sys
import zlib


def read_string(d, i):
    n = d[i]
    i += 1
    s = d[i:i + n].decode("utf-8", "replace")
    return s, i + n


def main(path):
    d = open(path, "rb").read()
    print("file: %s (%d bytes)" % (os.path.basename(path), len(d)))
    if d[:4] != b"TMOD":
        raise SystemExit("not a .tmod")
    i = 4
    version, i = read_string(d, i)
    print("format version:", version)

    # the deflate stream starts right after the version string; find both zlib raw and
    # zlib-wrapped starts because tModLoader has used different prefix bytes
    body = d[i:]
    for label, wbits in (("raw deflate", -15), ("zlib", 15)):
        for skip in range(0, 6):
            try:
                out = zlib.decompress(body[skip:], wbits)
                print("decompressed %s (skip=%d) -> %d bytes" % (label, skip, len(out)))
                return report(out)
            except Exception:
                continue
    print("could not decompress the container body (encrypted or different layout)")
    return None


def report(txt: bytes):
    text = txt.decode("utf-8", "replace")
    names = re.findall(r"[\w\-./]+\.(?:dll|png|hjson|txt|brain|rawimg|xnb|json|md)", text)
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    print("packed files (%d):" % len(seen))
    for n in seen:
        print("   ", n)
    for want in ("FlyMind.dll", "build.txt", "flymind.brain", "Fly.png", "FlyFood.png",
                 "en-US_Mods.FlyMind.hjson"):
        print("  contains %-28s %s" % (want, want in seen))
    return seen


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else
         r"C:\Users\Asus\Documents\My Games\Terraria\tModLoader\Mods\terraria-fly-mod.tmod")
