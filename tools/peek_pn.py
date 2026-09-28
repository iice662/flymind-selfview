import csv, re, collections
p = r"D:\projects\science\flywire-annotations\Supplemental_file1_neuron_annotations.tsv"
# what do the antennal-lobe projection neurons and ascending/sensory neurons look like?
pn = collections.Counter(); al = collections.Counter()
with open(p, encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        cc = row.get("cell_class") or ""
        nt = row.get("nerve") or ""
        if cc in ("ALPN", "ALLN", "LHLN"):
            pn[(row.get("cell_type") or row.get("hemibrain_type") or row.get("supertype"), cc, nt)] += 1
        if nt in ("AN", "PhN", "MxLbN", "ON", "OCN", "CV"):
            al[(nt, row.get("cell_type") or row.get("hemibrain_type") or row.get("supertype"), row.get("super_class"))] += 1
print("== ALPN/ALLN/LHLN: %d neurons, %d combos" % (sum(pn.values()), len(pn)))
for k, v in pn.most_common(12): print("   %s" % (k,), v)
print("== by nerve (AN=antennal, PhN=pharyngeal, MxLbN=labial, ON=optic): %d" % sum(al.values()))
for k, v in al.most_common(12): print("   %s" % (k,), v)
