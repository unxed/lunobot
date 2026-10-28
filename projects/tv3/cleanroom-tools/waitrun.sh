#!/bin/sh
# waitrun.sh <sha> [secs]: block up to secs (default 115) until all runs of sha completed; print them
S=$1; T=${2:-115}
timeout $T sh -c "until [ \"\$(gh run list -R unxed/tv3-new --commit $S --json status --jq 'length')\" -ge 1 ] && [ \"\$(gh run list -R unxed/tv3-new --commit $S --json status --jq '[.[]|select(.status!=\"completed\")]|length')\" = 0 ]; do sleep 5; done"
gh run list -R unxed/tv3-new --commit $S --json databaseId,status,conclusion,event
