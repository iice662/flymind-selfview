"""Throwaway: build a fresh instrumented module file (scratch_inst3.py) with clear markers."""
import sys
sys.path.insert(0, r"D:\projects\science\tools")

src = open(r"D:\projects\science\tools\feather_lite.py", encoding="utf-8").read()

# mark each take_buffer call site uniquely
src = src.replace("""            off, ln = buffers[buf_i[0]]
            buf_i[0] += 1""", """            off, ln = buffers[buf_i[0]]
            _MARK.append((buf_i[0], off, ln))
            print("TB#%d (off=%d len=%d)" % (buf_i[0], off, ln))
            buf_i[0] += 1""", 1)
src = src.replace("""        node_i = [0]
        buf_i = [0]""", """        node_i = [0]
        buf_i = [0]
        _MARK = []""", 1)
src = src.replace("""        def decode(field: Field):
            n = nodes[node_i[0]]
            node_i[0] += 1""", """        def decode(field: Field):
            _name = field.name
            n = nodes[node_i[0]]
            node_i[0] += 1
            print("== BEGIN %s type=%d child=%d n=%d buf_i=%d" % (_name, field.type_id, len(field.children), n, buf_i[0]))
            _MARK.clear()""", 1)
src = src.replace("""        out = {}
        for field in self.fields:
            out[field.name] = decode(field)""", """        out = {}
        for field in self.fields:
            out[field.name] = decode(field)
            print("== END   %-20s used %d buffers" % (field.name, len(_MARK)))""", 1)
src = src.replace('if __name__ == "__main__":', 'if False:')

open(r"D:\projects\science\tools\scratch_inst3.py", "w", encoding="utf-8").write(src)
lines = src.splitlines()
for i in range(676, 706):
    print("%4d| %s" % (i + 1, lines[i]))
