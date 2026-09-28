import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

for path in sys.argv[1:]:
    print("==", os.path.basename(path))
    data = open(path, "rb").read()
    f = F.FB.__new__(F.FB)
    f.buf = data
    f.pos = 0
    try:
        ff = F.FeatherFile.__new__(F.FeatherFile)
        ff.path = path
        ff.data = data
        footer_len = struct.unpack_from("<i", data, len(data) - 10)[0]
        ff.footer = F.FB(data, len(data) - 10 - footer_len)
        ff.schema_msg = ff._message_at(0)
        msg = ff.schema_msg[0]
        print("   message fields present:", [i for i in range(6) if msg.field(i) is not None])
        for fi in (2, 1):
            off = msg.field(fi)
            print("   msg.field(%d) = %s" % (fi, off))
            if off is None:
                continue
            target = off + struct.unpack_from("<I", data, off)[0]
            print("      target =", target, "of", len(data))
            if 0 <= target < len(data) - 8:
                sch = F.FB.at(data, target)
                print("      schema table ok, fields vec len =", sch.vector_len(1))
                break
    except Exception as e:
        import traceback
        traceback.print_exc()
