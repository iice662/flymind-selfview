import csv, re, collections
p = r"D:\projects\science\flywire-annotations\Supplemental_file1_neuron_annotations.tsv"
cols = ["super_class","cell_class","cell_sub_class","top_nt","nerve"]
counts = {c: collections.Counter() for c in cols}
n = 0
with open(p, encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        n += 1
        for c in cols:
            counts[c][row.get(c) or "<blank>"] += 1
print("rows:", n)
for c in cols:
    print("\n== %s (%d distinct) ==" % (c, len(counts[c])))
    for k, v in counts[c].most_common(28):
        print("   %-26s %d" % (k[:26], v))
