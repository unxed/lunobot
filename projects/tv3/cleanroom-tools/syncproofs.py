#!/usr/bin/env python3
"""syncproofs.py <repo>: set the proofs of every provenance record to the ids of its lines in tools/audit/proofs.txt."""
import json, sys, os
R = sys.argv[1]
by = {}
for l in open(R + "/tools/audit/proofs.txt", encoding="utf-8"):
    p = l.rstrip("\n").split("\t")
    if len(p) >= 4: by.setdefault(p[2], []).append(p[1])
for path, ids in by.items():
    rp = "%s/provenance/%s.json" % (R, path)
    if not os.path.exists(rp): continue
    r = json.load(open(rp, encoding="utf-8"))
    if set(r["proofs"]) != set(ids):
        r["proofs"] = ids
        json.dump(r, open(rp, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False); open(rp, "a").write("\n")
        print("updated", path, len(ids))
