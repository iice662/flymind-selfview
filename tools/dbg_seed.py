import sys, os, csv, re
sys.path.insert(0, os.getcwd())
import build_circuit as B
ids, id2i = B.load_completeness()
ann, _ = B.load_annotations(id2i)
hits = 0
for rid, row in ann.items():
    lab = B.label_of(row)
    if re.search(r"^PAM", lab, re.I) or "PAM" in lab:
        hits += 1
        if hits <= 3:
            print("label:", repr(lab))
            print("  classify ->", B.POP_NAMES[B.classify(row)])
print("labels containing PAM:", hits)
print("classify PAM with pattern:", bool(re.search(r"^PAM|^PPL|^PAL\d|dopamin|\bDAN\b", "PAM06 | PAM06 | 92324 | DAN", re.I)))
