#!/usr/bin/env python3
"""land.py <slug> <implementer-name> [--base origin/main]: builds branch tmp/19d3/<slug> in W/repo from the room."""
import json, os, re, subprocess, sys, shutil, hashlib
W = "/tmp/lunobot-1/work/tv3-cont2-1028"
PIN = "b4831e2ca16652db327fb7cc964f1c8c2d512524"
PINT = "210eb23564da06c358d2623388939bb02f7f3419"
def srcinfo(i):
    if i.startswith("tvterm/"): return "magiblot/tvterm", PINT, i[7:]
    return "magiblot/tvision", PIN, i
slug, impl = sys.argv[1], sys.argv[2]
branch = "tmp/19d3/" + slug
room = "%s/rooms/%s/repo" % (W, slug)
repo = W + "/repo"
def git(*a, cwd=repo, check=True):
    return subprocess.run(["git"] + list(a), cwd=cwd, check=check, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()
inputs = {}
for line in open("%s/rooms/%s.inputs.tsv" % (W, slug), encoding="utf-8"):
    p, blob, sha, n = line.rstrip("\n").split("\t")
    inputs[p] = (sha, int(n))
prov = {}
for line in open(room + "/out/provenance.tsv", encoding="utf-8"):
    line = line.rstrip("\n")
    if not line.strip(): continue
    p, _, rest = line.partition("\t")
    prov[p.strip()] = [x.strip() for x in rest.split(",") if x.strip()]
blocks, cur = [], None
for line in open(room + "/out/commits.txt", encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith("commit:"):
        cur = {"msg": line[7:].strip(), "files": []}; blocks.append(cur)
    elif line.strip() and cur is not None:
        cur["files"].append(line.strip().lstrip("-* ").strip("`"))
allowed = re.compile(r"^(src/[^/]+|tests/[^/]+|docs/API-NAMES\.md|tools/gen_tables\.py|tools/tests/test_gen_tables\.py|\.github/workflows/ci\.yml)$")
git("fetch", "-q", "origin", "main")
git("checkout", "-q", "main"); git("merge", "-q", "--ff-only", "origin/main")
git("checkout", "-q", "-B", branch, "origin/main")
def blob(p): return git("hash-object", p).strip()
for b in blocks:
    for f in b["files"]:
        assert allowed.match(f), "path not allowed: " + f
        src = room + "/" + f
        if os.path.exists(src):
            shutil.copyfile(src, repo + "/" + f)
        else:
            os.remove(repo + "/" + f)
    for f in b["files"]:
        if not os.path.exists(repo + "/" + f): continue
        rp = "%s/provenance/%s.json" % (repo, f)
        if os.path.exists(rp):
            rec = json.load(open(rp, encoding="utf-8"))
        else:
            k = "new" if f.startswith(("tools/", ".github/")) else "translation"
            rec = {"path": f, "kind": k, "sources": [], "inputs": [], "implementer": impl, "proofs": [], "versions": []}
        if f in prov and any(i.startswith("far2l/") for i in prov[f]):
            rec["kind"] = "standard"
            rec["sources"] = [{"document": "VTExts.md of unxed/far2l", "url": "https://github.com/unxed/far2l/blob/8030902caf42498e1612e5a393ab7fc489048f51/VTExts.md"}]
            rec["inputs"] = [{"origin": "unxed/far2l@8030902caf42498e1612e5a393ab7fc489048f51:VTExts.md", "sha256": inputs["far2l/VTExts.md"][0]}]
            if impl not in rec["implementer"]:
                rec["implementer"] = rec["implementer"] + ", " + impl
        elif f in prov and rec["kind"] == "translation":
            have = {s["file"] for s in rec["sources"]} | {"tvterm/"+s["file"] for s in rec["sources"] if s["source"]=="magiblot/tvterm"}
            for i in prov[f]:
                if i not in inputs:
                    if i in have: continue
                    raise SystemExit("unknown input " + i)
                sha, n = inputs[i]
                sname, scommit, sfile = srcinfo(i)
                if sfile not in have:
                    rec["sources"].append({"source": sname, "commit": scommit, "file": sfile, "lines": "1-%d" % n})
                o = "%s@%s:%s" % (sname, scommit, sfile)
                if not any(x["origin"] == o for x in rec["inputs"]):
                    rec["inputs"].append({"origin": o, "sha256": sha})
            if impl not in rec["implementer"]:
                rec["implementer"] = rec["implementer"] + ", " + impl
        elif f in prov:
            print("WARN: record of", f, "is kind", rec["kind"], "- inputs not added")
        bl = blob(f)
        if not any(v["blob"] == bl for v in rec["versions"]):
            rec["versions"].append({"blob": bl, "commit": None, "pr": None, "audit_run": None})
        os.makedirs(os.path.dirname(rp), exist_ok=True)
        with open(rp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rec, fh, indent=2, ensure_ascii=False); fh.write("\n")
    out = subprocess.run(["python3", "tools/audit/provenance_lint.py", "--write-index"], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()
    git("add", "-A", "src", "tests", "docs", "provenance")
    msg = b["msg"] + "\n\nAssisted-by: Claude Sonnet 5.5\n"
    git("commit", "-q", "-m", msg)
    print("commit", git("rev-parse", "--short", "HEAD").strip(), b["msg"])
print(subprocess.run(["python3", "tools/audit/provenance_lint.py"], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()[-600:])
print(subprocess.run(["python3", "tools/text_lint.py"], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode()[-800:])
