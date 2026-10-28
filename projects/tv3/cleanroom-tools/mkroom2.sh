#!/bin/sh
# usage: mkroom.sh <slug> <task-file> <input path>...   (input paths relative to magiblot root; "-" = none)
set -eu
W=/tmp/lunobot-1/work/tv3-cont2-1028
slug=$1; task=$2; shift 2
room=$W/rooms/$slug
[ -e "$room" ] && { echo "room exists"; exit 1; }
mkdir -p "$W/rooms"
git -C "$W/repo" fetch -q origin main
git -C "$W/repo" checkout -q main && git -C "$W/repo" merge -q --ff-only origin/main
git clone -q --no-hardlinks "$W/repo" "$room/repo"
git -C "$room/repo" remote remove origin
git -C "$room/repo" config user.name unxed
git -C "$room/repo" config user.email 1151423+unxed@users.noreply.github.com
git -C "$room/repo" checkout -q -b work
mkdir -p "$room/repo/inputs" "$room/repo/out"
: > "$W/rooms/$slug.inputs.tsv"
for p in "$@"; do
  [ "$p" = "-" ] && continue
  mkdir -p "$room/repo/inputs/$(dirname "$p")"
  cp "$W/mb/$p" "$room/repo/inputs/$p"
  printf '%s\t%s\t%s\t%s\n' "$p" "$(git hash-object "$W/mb/$p")" "$(sha256sum "$W/mb/$p" | cut -d' ' -f1)" "$(wc -l < "$W/mb/$p")" >> "$W/rooms/$slug.inputs.tsv"
done
sed "s/@SLUG@/$slug/" "$W/tools/prompt.tmpl" > "$room/repo/PROMPT.md"
cat "$task" >> "$room/repo/PROMPT.md"
echo "$room/repo"
