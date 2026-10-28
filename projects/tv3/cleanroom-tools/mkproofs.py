#!/usr/bin/env python3
"""mkproofs.py <verdict.log> <repo>: prints proofs.txt lines (standard) for MATCH lines on the generated tables."""
import re, sys
log, repo = sys.argv[1:3]
proofs = open(repo + "/tools/audit/proofs.txt", encoding="utf-8").read()
cache = {}
def pages(path):
    if path in cache: return cache[path]
    lines = open(repo + "/" + path, encoding="utf-8").read().split("\n")
    hdr = {}
    for l in lines:
        m = re.match(r"^\{ ((?:Cp|Set)\d+): (.+) \}$", l)
        if m: hdr[m.group(1)] = m.group(2).split(",")[0].strip()
    start = []
    for i, l in enumerate(lines, 1):
        m = re.match(r"^\s+((?:Cp|Set)\d+): array", l)
        if m: start.append((i, hdr[m.group(1)]))
    cache[path] = start
    return start
out = []
seen = set()
for l in open(log, encoding="utf-8", errors="replace"):
    m = re.search(r"MATCH (raw|ren|lit) (src/tv(?:cp|csets)\.inc) lines (\d+)-(\d+) \((\d+) tokens\) id ([0-9a-f]{64})", l)
    if not m: continue
    cmp_, path, a, b, n, mid = m.groups(); a = int(a); b = int(b)
    if mid in proofs or mid in seen: continue
    seen.add(mid)
    st = pages(path)
    fs = []
    for i, (ln, f) in enumerate(st):
        end = st[i + 1][0] - 1 if i + 1 < len(st) else 10**9
        if ln <= b and a <= end and f not in fs: fs.append(f)
    if not fs: print("NOPAGE", l, file=sys.stderr); continue
    fs = ["charsets/" + f for f in fs]
    out.append("%s\t%s\t%s\tstandard %s" % (cmp_, mid, path, ",".join(fs)))
print("\n".join(out))
