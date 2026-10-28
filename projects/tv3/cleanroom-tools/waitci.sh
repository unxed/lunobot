#!/bin/sh
# waitci.sh <sha>: wait until push and PR runs are complete, print result
S=$1
sleep 60
until [ "$(gh run list -R unxed/tv3-new --commit $S --json status --jq 'length')" -ge 2 ] && [ "$(gh run list -R unxed/tv3-new --commit $S --json status --jq '[.[]|select(.status!="completed")]|length')" = 0 ]; do sleep 30; done
gh run list -R unxed/tv3-new --commit $S --json databaseId,conclusion,event
