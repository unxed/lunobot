#!/bin/sh
# TV3_STEP_DIR=/absolute/path prepC.sh KEY SPECNAME STEM TEST : build a room in this step directory
set -eu
TOOLS=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ACCOUNTING=$(git -C "$TOOLS" rev-parse --show-toplevel)
D=$(CDPATH= cd -- "${TV3_STEP_DIR:?set TV3_STEP_DIR to the step work directory}" && pwd)
k=$1; sp=$2; st=$3; ts=$4
git -C "$D/base" fetch -q origin && git -C "$D/base" checkout -q -B main origin/main
mkdir -p "$D/$k/spec" "$D/$k/room/repo"; cp "$ACCOUNTING/projects/tv3/specs/$sp.md" "$D/$k/spec/$sp.md"
R="$D/$k/room/repo"
git -C "$D/base" archive HEAD | tar -x -C "$R"
rm -f "$R/src/$st.pas" "$R/tests/$ts.pas" "$R/provenance/src/$st.pas.json" "$R/provenance/tests/$ts.pas.json"
git -C "$R" init -q; git -C "$R" config user.name unxed; git -C "$R" config user.email 1151423+unxed@users.noreply.github.com
git -C "$R" add -A; git -C "$R" commit -q -m "Snapshot"; git -C "$R" checkout -q -b "$k"
cp "$D/$k/spec/$sp.md" "$D/$k/room/spec.md"
cat "$TOOLS/promptC.tmpl" > "$D/$k/room/PROMPT.md"; if [ -f "$D/$k/task.txt" ]; then cat "$D/$k/task.txt" >> "$D/$k/room/PROMPT.md"; fi
echo ready
