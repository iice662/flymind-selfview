import csv, re, collections, json
p = r"D:\projects\science\flywire-annotations\Supplemental_file1_neuron_annotations.tsv"
pats = {
 "GRN_sugar": re.compile(r"GRN|gustat|sugar|sweet", re.I),
 "DA": re.compile(r"^PAM|^PPL|^PAL|dopamin|\bDAN\b", re.I),
 "MBON": re.compile(r"MBON", re.I),
 "proboscis/ingest": re.compile(r"proboscis|ingest|feeding|pharyngeal", re.I),
 "PN_AL": re.compile(r"ALPN|uniglomerular|PN", re.I),
 "descending": re.compile(r"^DN", re.I),
}
hits = {k: collections.Counter() for k in pats}
nt = collections.Counter()
with open(p, encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        nt[row["top_nt"]] += 1
        hay = " | ".join(row.get(c,"") or "" for c in ("cell_class","cell_sub_class","supertype","cell_type","hemibrain_type","nerve"))
        for k, rx in pats.items():
            if rx.search(hay):
                hits[k][ (row.get("cell_type") or row.get("hemibrain_type") or row.get("supertype"), row.get("cell_class"), row.get("top_nt")) ] += 1
print("== top_nt ==")
for k,v in nt.most_common(15): print("   %-16s %d" % (k if k else "<blank>", v))
for k in pats:
    print("\n==", k, "== distinct:", len(hits[k]))
    for (ct, cc, tn), v in hits[k].most_common(25):
        print("   %-22s %-14s %-14s %d" % (str(ct)[:22], str(cc)[:14], str(tn)[:14], v))
