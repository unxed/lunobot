#!/bin/sh
# ship.sh <slug> <implementer> "<commit msg>" <prfile>: collapse commits, land, push, PR, wait CI, diagnose
set -u
W=/tmp/lunobot-1/work/tv3-cont2-1028; slug=$1; impl=$2; msg=$3; body=$4
python3 $W/tools/onecommit.py $W/rooms/$slug/repo/out/commits.txt "$msg" || exit 1
python3 $W/tools/land.py $slug "$impl" 2>&1 | tail -4
cd $W/repo && git push -q -f origin tmp/19d3/$slug 2>&1 | grep -v '^remote' | head -2
sha=$(git rev-parse HEAD); echo $sha > $W/$slug.sha; echo sha $sha
if [ ! -f $W/$slug.pr ]; then python3 $W/accounting/tools/gh_post.py pr unxed/tv3-new tmp/19d3/$slug main $W/$body | tail -1 | tee $W/$slug.pr; fi
$W/tools/waitci.sh $sha
$W/tools/diag.sh $sha
