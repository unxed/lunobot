#!/bin/sh
# ship.sh <unit-lower> <Unit> <test> <step> : branch + commit + push + PR + CI.md/BRANCHES + audit with extra
set -eu
W=${W:?W = the step directory, with clones tv3 and accounting}; G=$W/tv3; A=$W/accounting; u=$1; U=$2; t=$3; st=$4
S="${SIGN:?SIGN = id for --sign}"; ID="${ID:?ID = full id with the worker suffix}"
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUTF8=1
sed -n '1,/^implementation/p' $W/room-$u/out/$u.pas | sed '$d' | diff -q - $W/room-$u/interface.pas
cd $A; git stash -q 2>/dev/null || true
python3 tools/acct_line.py add projects/tv3/BRANCHES.md "$(date -u '+%d-%m-%Y %H:%M:%S') $ID, ветка \`lunobot/pr/$u-rw\` для https://github.com/unxed/tv3/issues/12" -m "unxed/tv3#12: ветка $st $U" --sign "$S" | tail -1
git -C $G switch -q main; git -C $G pull -q; OLD=$(git -C $G rev-parse HEAD)
git -C $G switch -q -c lunobot/pr/$u-rw; cp $W/room-$u/out/$u.pas $G/src/$u.pas; git -C $G add src/$u.pas
git -C $G commit -q -m "$U: new implementation

A new implementation section; the interface is unchanged. tests/$t.pas
checks the behaviour.

Part of #12 (step $st).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git -C $G push -q -u origin lunobot/pr/$u-rw 2>&1 | grep -v '^remote' || true
H=$(git -C $G rev-parse HEAD)
printf '%s\n\n%s\n\n%s\n\n%s\n' "$U: new implementation (#12, $st)" "Step $st of #12: a new implementation section of \`$U\`. The interface section is unchanged byte for byte." "Checks: \`ci\` on the exact head; \`tools/audit/run.sh\` on the head in the sandbox CI with the extra checks of the plan, posted here before merging." "*Lunobot-1 (node 19d368003c6c048e43dbec70; LNX; Claude Opus 5.5; subagent)*" > $W/drafts/pr-$u.md
PR=$(python3 tools/gh_post.py pr unxed/tv3 lunobot/pr/$u-rw main $W/drafts/pr-$u.md | tail -1); echo "PR $PR head $H old $OLD"
sed -e "s/<m>/$u/" -e "s/<sha main>/$OLD/" $A/projects/tv3/cleanroom-tools/extra.tmpl > $W/extra-$u.sh
gh workflow run tv3-audit.yml --repo unxed/sandbox --ref main -f repo=unxed/tv3 -f refs="main $H" -f extra="$(cat $W/extra-$u.sh)"
sleep 10
AR=$(gh run list --repo unxed/sandbox --workflow tv3-audit.yml --limit 1 --json databaseId --jq '.[0].databaseId')
CR=$(gh api "repos/unxed/tv3/actions/runs?head_sha=$H&event=pull_request" --jq '.workflow_runs[0]|"\(.id) \(.run_number)"')
set -- $CR; N=${PR##*/}
python3 tools/acct_line.py add projects/tv3/CI.md "$(date -u '+%d-%m-%Y %H:%M:%S') $ID, тикет https://github.com/unxed/tv3/issues/12 ($st), PR [#$N]($PR), коммит \`$(echo $H | cut -c1-7)\`, прогон [#$2](https://github.com/unxed/tv3/actions/runs/$1)" -m "unxed/tv3#$N: $st $U, прогон в CI.md" --sign "$S" | tail -1
git stash pop -q 2>/dev/null || true
echo "CI $1 AUDIT $AR PR $N HEAD $H"
