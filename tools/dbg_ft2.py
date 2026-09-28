import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import feather_lite as F

path = r"D:\projects\science\malecns\body-annotations.feather"
data = open(path, "rb").read()

for label, construct in (("Table(data, 16)", lambda: F.Table(data, 16)),
                         ("Table.at(data, 32)", lambda: F.Table(data, 32))):
    try:
        msg = construct()
        print("%s -> pos=%d vtable=%d vlen=%d" % (label, msg.pos, msg.vtable, msg.vlen))
        for fi in range(msg.field_count()):
            print("   f%d slot=%s" % (fi, msg._slot(fi)))
        t2 = msg.table(2)
        print("   msg.table(2) =", t2)
        if t2 is not None:
            print("   fields vector len =", t2.vector_len(1))
            ft = t2.vector_table(1, 0) if t2.vector_len(1) else None
            print("   field 0 =", ft)
            if ft is not None:
                print("      name=%r" % ft.string(0))
    except Exception as e:
        import traceback
        traceback.print_exc()
    print()
