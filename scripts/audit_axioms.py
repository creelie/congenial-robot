"""Reads the output of `lake env lean Check.lean` and checks that every main theorem rests only on the
three standard axioms (no sorry, no native_decide)."""
import re
import sys

ALLOWED = {"propext", "Classical.choice", "Quot.sound"}
EXPECTED = 20

text = open(sys.argv[1]).read()
if "sorryAx" in text or "error" in text:
    sys.exit("audit: sorry or error in the output")
found = re.findall(r"^'(\S+)' depends on axioms: \[([^\]]*)\]", text, re.M)
bad = 0
for name, axioms in found:
    used = {a.strip() for a in axioms.split(",") if a.strip()}
    extra = used - ALLOWED
    print(f"{name}: {'standard axioms only' if not extra else 'not allowed: ' + ', '.join(sorted(extra))}")
    bad += bool(extra)
if len(found) != EXPECTED:
    sys.exit(f"audit: expected {EXPECTED} theorems, found {len(found)}")
if bad:
    sys.exit("audit: unexpected axioms")
print(f"axiom audit: {len(found)} theorems, standard axioms only")
