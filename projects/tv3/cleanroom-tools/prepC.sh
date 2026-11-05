#!/bin/sh
# prepC.sh KEY SPECNAME STEM TEST : room = snapshot of fresh main (no history) minus the unit and its test, plus the spec
D=/tmp/lunobot-1/work/tv3-part2-1105-1322; k=$1; sp=$2; st=$3; ts=$4
git -C $D/base fetch -q origin && git -C $D/base checkout -q -B main origin/main
mkdir -p $D/$k/spec $D/$k/room/repo; cp $D/accounting/projects/tv3/specs/$sp.md $D/$k/spec/$sp.md
R=$D/$k/room/repo
git -C $D/base archive HEAD | tar -x -C $R
rm -f $R/src/$st.pas $R/tests/$ts.pas $R/provenance/src/$st.pas.json $R/provenance/tests/$ts.pas.json
git -C $R init -q; git -C $R config user.name unxed; git -C $R config user.email 1151423+unxed@users.noreply.github.com
git -C $R add -A; git -C $R commit -q -m "Snapshot"; git -C $R checkout -q -b $k
cp $D/$k/spec/$sp.md $D/$k/room/spec.md
cat $D/promptC.tmpl > $D/$k/room/PROMPT.md; [ -f $D/$k/task.txt ] && cat $D/$k/task.txt >> $D/$k/room/PROMPT.md
echo ready
