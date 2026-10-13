#!/usr/bin/env bash
# run_all.sh -- every check outside Lean; outputs go to build/.
#   C:      maxsub.c over all lattices with at most twelve elements (posets from nauty-genposetg), compared
#           line by line with data/counts_upto12_all.txt
#   Python: check_examples.py (the examples of Theorems A, B, C and E), check_minimal.py (a second program:
#           order convexity for all lattices with at most ten elements, Question 2 for all convex geometries
#           with at most eleven), convex_geometries.py (all convex geometries on at most five points),
#           dimension_three.py (convex geometries on six points of convex dimension at most three with at most
#           25 closed sets); the last two need python-sat
# Needs a C compiler, nauty (nauty-genposetg) and Python 3 with python-sat.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
B="$ROOT/build"
PY="$ROOT/verification/python"
mkdir -p "$B"
cc -O2 -o "$B/maxsub" "$ROOT/verification/c/maxsub.c"

echo "== C: all lattices with at most twelve elements"
: > "$B/counts_upto12_all.txt"
for m in $(seq 0 10); do
  printf 'N=%d ' $((m + 2)) >> "$B/counts_upto12_all.txt"
  nauty-genposetg $m t q 2>/dev/null | "$B/maxsub" > "$B/maxsub_$((m + 2)).txt" 2>> "$B/counts_upto12_all.txt"
done
cat "$B/counts_upto12_all.txt"
diff "$B/counts_upto12_all.txt" "$ROOT/data/counts_upto12_all.txt"

echo "== Python: the examples"
python3 -I "$PY/check_examples.py" | tee "$B/check_examples.txt"

echo "== Python: second program"
for m in $(seq 0 8); do nauty-genposetg $m t q 2>/dev/null | python3 -I "$PY/check_minimal.py"; done \
  | tee "$B/check_minimal_all.txt"
test "$(grep -c '^nonconvex' "$B/check_minimal_all.txt")" = 1
for m in $(seq 0 9); do nauty-genposetg $m t q 2>/dev/null | python3 -I "$PY/check_minimal.py" cg; done \
  | tee "$B/check_minimal_cg.txt"
test "$(grep -c '^question2-meet' "$B/check_minimal_cg.txt")" = 1
test "$(grep -c '^question2-join' "$B/check_minimal_cg.txt")" = 0

echo "== Python: all convex geometries on at most five points"
for n in 1 2 3 4 5; do python3 -I "$PY/convex_geometries.py" $n; done | tee "$B/convex_geometries.txt"
grep -q "n = 5: 59386 labeled and 672 unlabeled convex geometries" "$B/convex_geometries.txt"
test "$(grep -c '^  H2 fails' "$B/convex_geometries.txt")" = 3

echo "== Python: convex dimension three on six points"
python3 -I "$PY/dimension_three.py" 4 | tee "$B/dimension_three.txt"
grep -q "56990 labelled families, 8435 isomorphism classes" "$B/dimension_three.txt"
grep -q "classes failing Hypothesis 2: 1$" "$B/dimension_three.txt"
grep -q "25 closed sets:" "$B/dimension_three.txt"
echo "all checks passed"
