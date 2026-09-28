"""Dump the complete cell-type vocabulary so pathway seeds can be chosen from
real annotation values instead of guessed regexes.

Outputs:
    celltype_vocab.txt     every distinct (cell_type, hemibrain_type, supertype) value with counts
    pathway_candidates.txt lines matching sugar / bitter / odor / DAN / MBON / motor / descending
"""
import csv
import os
import re
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "..", "flywire-annotations",
                   "Supplemental_file1_neuron_annotations.tsv")

KEYS = ("cell_type", "hemibrain_type", "supertype", "cell_class", "cell_sub_class")
label_ct = collections.Counter()
per_key = {k: collections.Counter() for k in KEYS}
n = 0
with open(TSV, encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        n += 1
        for k in KEYS:
            v = (row.get(k) or "").strip()
            if v:
                per_key[k][v] += 1
        lab = " | ".join((row.get(k) or "").strip() for k in KEYS if (row.get(k) or "").strip())
        if lab:
            label_ct[lab] += 1

with open(os.path.join(HERE, "celltype_vocab.txt"), "w", encoding="utf-8") as out:
    out.write("# %d annotation rows\n" % n)
    for k in KEYS:
        out.write("\n===== %s : %d distinct values =====\n" % (k, len(per_key[k])))
        for v, c in per_key[k].most_common():
            out.write("%8d  %s\n" % (c, v))
    out.write("\n===== joined labels : %d distinct =====\n" % len(label_ct))
    for v, c in label_ct.most_common():
        out.write("%8d  %s\n" % (c, v))

PATTERNS = {
    "SUGAR": r"GRN|GR\d|sugar|sweet|SER|gustat|pharyngeal.*sens|labell",
    "BITTER": r"bitter|aversive|GR\d+a|GRN.*bitt",
    "ODOR": r"ORN|OR\d|odor|olfact|antennal.*receptor",
    "DAN": r"^PAM|^PPL|^PAL|dopamin|DAN",
    "MBON": r"MBON",
    "KC": r"Kenyon|KC[a-z]",
    "MOTOR_PROBOSCIS": r"proboscis|ingestion|crop_motor|pharyngeal",
    "DESCENDING": r"^DN|descending",
}
with open(os.path.join(HERE, "pathway_candidates.txt"), "w", encoding="utf-8") as out:
    for name, pat in PATTERNS.items():
        rx = re.compile(pat)
        hits = collections.Counter()
        for lab, c in label_ct.items():
            if rx.search(lab):
                hits[lab] += c
        out.write("\n########## %s : %d distinct labels, %d neurons ##########\n"
                  % (name, len(hits), sum(hits.values())))
        for v, c in hits.most_common(120):
            out.write("%6d  %s\n" % (c, v))

print("rows:", n)
print("wrote celltype_vocab.txt and pathway_candidates.txt")
