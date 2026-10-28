#!/usr/bin/env python3
"""addgen.py <file.inc> <src dest e.g. src/tvcp.inc> <implementer>: copy generated table and write its standard record."""
import json, re, sys, shutil, hashlib, subprocess, os
R = "/tmp/lunobot-1/work/tv3-cont2-1028/repo"
src, dest, impl = sys.argv[1:4]
shutil.copyfile(src, os.path.join(R, dest))
text = open(src, encoding="utf-8").read()
files = []
for m in re.finditer(r"^\{ \w+: ([^}]+?) \}$", text, re.M):
    for f in m.group(1).split(","):
        f = f.strip()
        if f and f not in files: files.append(f)
srcs = []
for f in files:
    rp = "%s/provenance/tools/audit/facts/charsets/%s.json" % (R, f)
    rec = json.load(open(rp, encoding="utf-8"))
    for s in rec["sources"]:
        if s not in srcs: srcs.append(s)
g = hashlib.sha256(open(R + "/tools/gen_tables.py", "rb").read()).hexdigest()
bl = subprocess.run(["git", "hash-object", dest], cwd=R, stdout=subprocess.PIPE).stdout.decode().strip()
rec = {"path": dest, "kind": "standard", "sources": srcs,
       "inputs": [{"origin": "repository:tools/gen_tables.py", "sha256": g}],
       "implementer": impl, "proofs": [], "versions": [{"blob": bl, "commit": None, "pr": None, "audit_run": None}]}
rp = "%s/provenance/%s.json" % (R, dest)
os.makedirs(os.path.dirname(rp), exist_ok=True)
json.dump(rec, open(rp, "w", encoding="utf-8", newline="\n"), indent=2, ensure_ascii=False); open(rp, "a").write("\n")
print(len(files), "files", len(srcs), "sources")
