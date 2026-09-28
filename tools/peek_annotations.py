import csv, sys, collections
p = r"D:\projects\science\flywire-annotations\Supplemental_file1_neuron_annotations.tsv"
cols = ["super_class","cell_class","cell_sub_class","supertype","cell_type","hemibrain_type","top_nt","known_nt","nerve","flow"]
counts = {c: collections.Counter() for c in cols}
n = 0
with open(p, encoding="utf-8", newline="") as f:
    r = csv.DictReader(f, delimiter="\t")
    for row in r:
        n += 1
        for c in cols:
            counts[c][row.get(c, "")] += 1
print("rows parsed:", n)
for c in cols:
    print("\n==", c, "== distinct:", len(counts[c]))
    for k, v in counts[c].most_common(30):
        print("   %-28s %d" % (k if k else "<blank>", v))
