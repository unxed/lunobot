#!/bin/sh
# diag.sh <sha>: print failures of the push run
S=$1; A=/tmp/lunobot-1/work/tv3-cont2-1028/accounting
R=$(gh run list -R unxed/tv3-new --commit $S --json databaseId,event --jq '.[]|select(.event=="push")|.databaseId')
gh run view $R -R unxed/tv3-new --json jobs --jq '.jobs[]|"\(.name) \(.conclusion)"'
python3 $A/tools/run_log.py unxed/tv3-new $R --job linux --grep 'Error|FAIL|Fatal' --tail 40 | tail -40
gh run view $R -R unxed/tv3-new --log 2>/dev/null | grep -E 'MATCH (raw|ren)' | sed -E 's/.*MATCH (raw|ren) ([^ ]+) lines ([0-9-]+) \(([0-9]+) tokens\).*/\2 \3 \4 \1/' | sort | tr '\n' ';'
