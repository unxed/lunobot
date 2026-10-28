#!/bin/sh
# cycle.sh KEY STEM TEST "implementer N" What BRANCH : rebuild commits on fresh main, push -f, wait CI, collect results to KEY/cycle.out and KEY/room/ci.txt
D=/tmp/lunobot-1/work/tv3-cont-10271905
k=$1; s=$2; t=$3; impl=$4; what=$5; br=$6; R=$D/$k/room/repo; O=$D/$k/cycle.out
: > $O
n=$(ls $D/$k | grep -c '^save'); sv=$D/$k/save$n; mkdir -p $sv
cp $R/src/$s.pas $R/tests/$t.pas $R/docs/API-NAMES.md $sv/
git -C $R fetch -q origin 2>/dev/null || git -C $R remote add origin https://github.com/unxed/tv3-new.git && git -C $R fetch -q origin
git -C $R reset -q --hard origin/main && git -C $R clean -fdq
cp $sv/$s.pas $R/src/; cp $sv/$t.pas $R/tests/; cp $sv/API-NAMES.md $R/docs/
[ -d $D/$k/orig ] && mv $D/$k/orig $D/$k/orig.$n
(cd $D && python3 finish.py $k $s $t "$impl" $what) > $D/$k/finish.out 2>&1 || { cat $D/$k/finish.out > $O; echo "done FINISH-FAILED" >> $O; exit 1; }
git -C $R push -q -f origin HEAD:refs/heads/$br 2>$D/$k/push.err || { echo "done PUSH-FAILED" >> $O; exit 1; }
H=$(git -C $R rev-parse HEAD); echo "pushed $H" >> $O
RID=""
for i in $(seq 1 40); do
  RID=$(gh run list -R unxed/tv3-new --branch $br --event push --limit 5 --json databaseId,headSha --jq ".[]|select(.headSha==\"$H\")|.databaseId" | head -1)
  [ -n "$RID" ] && break; sleep 5
done
[ -n "$RID" ] || { echo "done NORUN" >> $O; exit 1; }
until [ "$(gh run view $RID -R unxed/tv3-new --json status --jq .status)" = completed ]; do sleep 20; done
gh run view $RID -R unxed/tv3-new --json conclusion,jobs --jq '.conclusion+" "+([.jobs[]|.name+"="+.conclusion]|join(","))' >> $O
echo "run $RID" >> $O
for j in linux verdict; do
  jid=$(gh run view $RID -R unxed/tv3-new --json jobs --jq ".jobs[]|select(.name==\"$j\")|.databaseId")
  gh run view $RID -R unxed/tv3-new --log --job $jid > $D/$k/$j.log 2>&1
done
{
echo "Result of the checks on the last version of your files."; echo
echo "Failing checks of the test program and compile errors:"
grep -E "FAIL |BUILD FAILED|Error:|Fatal:|^TEXT:" $D/$k/linux.log | sed 's/^linux\t[^\t]*\t[0-9TZ:.-]* //' | cut -c1-300 | head -60
echo
echo "Audit: stretches of your files identical to other published code; each must be removed by writing the routine differently (same behaviour):"
grep "MATCH" $D/$k/verdict.log | sed -E 's/.*MATCH (raw|ren|lit) ([^ ]+) lines ([0-9-]+) \(([0-9]+) tokens\).*/\2 lines \3: \4 tokens (\1)/' | sort -t' ' -k1,1 -k3,3n
} > $D/$k/room/ci.txt
grep -c "tokens" $D/$k/room/ci.txt >> $O
echo "done $H" >> $O
