#!/usr/bin/env python3
"""finish.py KEY STEM TESTSTEM IMPLEMENTER WHAT : three commits (interface, implementation, tests+names) in KEY/room/repo.
Env SPEC=<id>: unit made from a specification (spec in KEY/spec/<id>.md), else translation with KEY/inputs.tsv."""
import sys, os, json, re, subprocess, hashlib, shutil
D = "/tmp/lunobot-1/work/tv3-cont-10271905"
key, stem, tstem, impl, what = sys.argv[1:6]
R = f"{D}/{key}/room/repo"
COMMIT = "b4831e2ca16652db327fb7cc964f1c8c2d512524"
TRAILER = "Assisted-by: Claude Sonnet 5.5"
SPEC = os.environ.get("SPEC")
def run(*a):
    return subprocess.run(a, cwd=R, check=True, stdout=subprocess.PIPE).stdout
def sh(*a): return run(*a).decode()
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def blob(p): return sh("git", "hash-object", p).strip()
def commit(msg):
    sh("git", "add", "-A"); sh("git", "commit", "-q", "-m", msg, "--trailer", TRAILER)
src = f"src/{stem}.pas"; tst = f"tests/{tstem}.pas"; api = "docs/API-NAMES.md"
os.makedirs(f"{D}/{key}/orig", exist_ok=True)
for f in (src, tst, api):
    shutil.copy(f"{R}/{f}", f"{D}/{key}/orig/{os.path.basename(f)}")
st = sh("git", "status", "--porcelain").split("\n")
bad = [l for l in st if l.strip() and l[3:] not in (src, tst, api)]
if bad: sys.exit("unexpected changes: %r" % bad)
rows = [] if SPEC else [l.split() for l in open(f"{D}/{key}/inputs.tsv") if l.strip()]
if SPEC:
    base_inputs = [{"origin": f"specification:{SPEC}", "sha256": sha(f"{D}/{key}/spec/{SPEC}.md")}]
    sources = [{"specification": SPEC}]
else:
    base_inputs = [{"origin": f"magiblot/tvision@{COMMIT}:{r[0]}", "sha256": r[2]} for r in rows]
    sources = [{"source": "magiblot/tvision", "commit": COMMIT, "file": r[0], "lines": f"1-{r[3]}"} for r in rows]
def deps(path, seen):
    txt = open(f"{R}/{path}").read()
    names = set()
    for m in re.finditer(r"(?im)^uses\b(.*?);", txt, re.S):
        names |= set(re.findall(r"\bTv\w+", m.group(1)))
    for n in sorted(names):
        p = f"src/{n.lower()}.pas"
        if p not in seen and os.path.exists(f"{R}/{p}"):
            seen.append(p); deps(p, seen)
    return seen
def repo_inputs(extra):
    out = []
    for p in ["docs/API-NAMES.md", "docs/ASYNC.md"] + extra:
        h = hashlib.sha256(run("git", "show", f"HEAD:{p}")).hexdigest()
        out.append({"origin": f"repository:{p}", "sha256": h})
    return out
def write_rec(path, inputs, blobs):
    rec = {"path": path, "kind": "specification" if SPEC else "translation", "sources": sources, "inputs": inputs,
           "implementer": impl, "proofs": [],
           "versions": [{"blob": b, "commit": None, "pr": None, "audit_run": None} for b in blobs]}
    p = f"{R}/provenance/{path}.json"; os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(rec, open(p, "w"), indent=2); open(p, "a").write("\n")
def index():
    subprocess.run(["python3", "tools/audit/provenance_lint.py", "--write-index"], cwd=R, stdout=subprocess.PIPE)
full = open(f"{R}/{src}").read()
iface = full[:full.index("\nimplementation\n")] + "\nimplementation\n\nend.\n"
d = deps(src, [])
inputs_src = base_inputs + repo_inputs(d)
testtxt = open(f"{R}/{tst}").read(); apitxt = open(f"{R}/{api}").read(); apiblob = blob(api)
os.remove(f"{R}/{tst}"); sh("git", "checkout", "HEAD", "--", api)
open(f"{R}/{src}", "w").write(iface); A = blob(src)
write_rec(src, inputs_src, [A]); index()
commit(f"Add the interface of {what}\n\nThe declarations of {what}; the bodies follow in the next commit.")
open(f"{R}/{src}", "w").write(full); B = blob(src)
write_rec(src, inputs_src, [A, B]); index()
commit(f"Implement {what}\n\nThe routines of {what}.")
open(f"{R}/{tst}", "w").write(testtxt); open(f"{R}/{api}", "w").write(apitxt)
T = blob(tst)
write_rec(tst, base_inputs + repo_inputs(d) + [{"origin": f"repository:{src}", "sha256": sha(f"{R}/{src}")}], [T])
arec = f"{R}/provenance/{api}.json"; ar = json.load(open(arec))
if apiblob not in [v["blob"] for v in ar["versions"]]:
    ar["versions"].append({"blob": apiblob, "commit": None, "pr": None, "audit_run": None})
json.dump(ar, open(arec, "w"), indent=2); open(arec, "a").write("\n")
index()
commit(f"Add the test program of {what} and list its added names\n\nChecks of the routines of {what}; the names with no counterpart in the sources are listed in docs/API-NAMES.md.")
print(sh("git", "log", "--oneline", "-4"))
