#!/bin/sh
# land.sh BRANCH BODYFILE : PR, wait checks, merge commit
D=/tmp/lunobot-1/work/tv3-cont-10271905; b=$1
(cd $D/accounting && python3 tools/gh_post.py pr unxed/tv3-new $b main $2 | tail -1) || exit 1
N=$(gh pr list -R unxed/tv3-new --head $b --json number --jq '.[0].number')
sleep 30
timeout 900 sh -c "until [ -z \"\$(gh pr checks $N -R unxed/tv3-new --json bucket --jq '.[]|select(.bucket==\"pending\")' 2>/dev/null)\" ] && [ -n \"\$(gh pr checks $N -R unxed/tv3-new --json bucket --jq '.[0]' 2>/dev/null)\" ]; do sleep 20; done"
gh pr checks $N -R unxed/tv3-new --json name,bucket --jq '.[]|.name+" "+.bucket'
if gh pr checks $N -R unxed/tv3-new --json bucket --jq '.[].bucket' | grep -qv pass; then echo NOTGREEN; exit 1; fi
gh pr merge $N -R unxed/tv3-new --merge 2>&1 | tail -1
gh pr view $N -R unxed/tv3-new --json state,mergeCommit --jq '"\(.state) #'$N' \(.mergeCommit.oid)"'
