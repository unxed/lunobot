#!/bin/sh
# results.sh <audit run> <ci run> : summary; downloads the sheet to art-<run>, deletes the artifact
W=${W:?W = the step directory, with clones tv3 and accounting}; A=$W/accounting
gh api repos/unxed/tv3/actions/runs/$2 --jq '"ci: \(.conclusion)"'
python3 $A/run_log.py unxed/sandbox $1 --job audit > $W/audit-$1.log 2>&1
grep -E '^## |AUDIT (PASS|FAIL)|keys of the 2nd revision missing from the 1st: [0-9]|known matches not counted|^(raw|ren|lit) |lowered exit|prev exit|^== |^/tmp/low' $W/audit-$1.log | grep -v 'echo ' 
mkdir -p $W/art-$1; gh run download $1 --repo unxed/sandbox -n tv3-audit -D $W/art-$1 >/dev/null 2>&1
for a in $(gh api repos/unxed/sandbox/actions/runs/$1/artifacts --jq '.artifacts[].id'); do gh api -X DELETE repos/unxed/sandbox/actions/artifacts/$a >/dev/null && echo "artifact $a deleted"; done
