#!/bin/sh
# mkroom.sh <unit-lower> <test-name> <magiblot path>... : builds $W/room-<unit>/ per CLEANROOM.md п. 2
set -eu
W=${W:?W = the step directory, with clones tv3 and accounting}; T=$W/tv3; M=b4831e2ca16652db327fb7cc964f1c8c2d512524
u=$1; t=$2; shift 2; R=$W/room-$u; mkdir -p $R/magiblot $R/deps $R/out
sed -n '1,/^implementation/p' $T/src/$u.pas | sed '$d' > $R/interface.pas
cp $T/docs/API-NAMES.md $R/; cp $T/src/tvdefs.inc $R/deps/
: > $R/inputs.txt
for p in "$@"; do f=$R/magiblot/$(basename $p); gh api -H 'Accept: application/vnd.github.raw+json' "repos/magiblot/tvision/contents/$p?ref=$M" > $f; echo "$p $(gh api "repos/magiblot/tvision/contents/$p?ref=$M" --jq .sha)" >> $R/inputs.txt; done
# interface sections of the tv3 units it uses
for d in $(tr '\n' ' ' < $T/src/$u.pas | grep -oiE '\buses\b[^;]*;' | sed -E 's/\buses\b//I; s/[;,]/ /g' | tr ' ' '\n' | grep -iE '^tv' | tr 'A-Z' 'a-z' | sort -u); do [ -f $T/src/$d.pas ] && sed -n '1,/^implementation/p' $T/src/$d.pas | sed '$d' > $R/deps/$d.pas; done
{ echo "tests/$t.pas - the checks of the unit, by name:"; grep -oE "Check\([^;]*'[^']+'\)" $T/tests/$t.pas | grep -oE "'[^']+'\)$" | tr -d "')" | sed 's/^/  - /'; } > $R/tests.txt
echo "room $R: $(ls $R/magiblot | tr '\n' ' ') deps: $(ls $R/deps | tr '\n' ' ') checks: $(($(wc -l < $R/tests.txt)-1))"
