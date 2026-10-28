#!/bin/sh
# prepC.sh KEY SPECNAME : room from fresh main + spec
D=/tmp/lunobot-1/work/tv3-cont-10271905; k=$1; sp=$2
git -C $D/base fetch -q origin && git -C $D/base checkout -q -B main origin/main
mkdir -p $D/$k/spec $D/$k/room; cp $D/accounting/projects/tv3/specs/$sp.md $D/$k/spec/$sp.md
rm -rf $D/$k/room/repo; git clone -q $D/base $D/$k/room/repo; git -C $D/$k/room/repo remote remove origin
git -C $D/$k/room/repo config user.name unxed; git -C $D/$k/room/repo config user.email 1151423+unxed@users.noreply.github.com
git -C $D/$k/room/repo checkout -q -b $k
cp $D/$k/spec/$sp.md $D/$k/room/spec.md
cat $D/promptC.tmpl > $D/$k/room/PROMPT.md; [ -f $D/$k/task.txt ] && cat $D/$k/task.txt >> $D/$k/room/PROMPT.md
echo ready
