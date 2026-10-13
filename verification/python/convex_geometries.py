"""All convex geometries on n <= 5 points, and the complements of their maximal sublattices.

A convex geometry on X = {0, ..., n-1} is a family K of subsets that contains the empty set and X, is
closed under intersection, and in which every member other than X has a one-point extension in K (this
is equivalent to the anti-exchange property). The script enumerates all such families, keeps one per
isomorphism class (the counts 1, 1, 3, 22, 485, 59386 labeled and 1, 1, 2, 6, 34, 672 unlabeled for
n = 0, ..., 5 are the known ones), and for each lattice K finds every maximal proper sublattice that
contains the least and the greatest element with a SAT solver (python-sat). For each complement C it
tests

  H2  C has a least element and is order convex,
  H4  every x in C has a lower cover m outside C with no element of C below m,
  Q2  C contains exactly one join-irreducible element (the join half of Question 2), and every
      meet-irreducible element of C is maximal in C (the meet half).

With --digraph6 FILE it also writes, for every geometry with at most 22 closed sets, the Hasse diagram
of the closed sets other than the empty set and X in digraph6, so that verification/c/maxsub.c can
repeat the tests by exhaustive enumeration of subsets.

Usage: python3 convex_geometries.py 5 [--digraph6 cg5.d6]
"""
import itertools
import sys

from pysat.solvers import Cadical153


def geometries(n):
    full = (1 << n) - 1
    order = sorted(range(1 << n), key=lambda s: (-bin(s).count("1"), s))
    out = []

    def rec(i, fam, forced):
        if i == len(order):
            out.append(sorted(fam, key=lambda s: (bin(s).count("1"), s)))
            return
        s = order[i]
        accessible = s == full or any((s | 1 << x) in fam for x in range(n) if not s >> x & 1)
        must = s in forced or s == 0 or s == full
        if not must:
            rec(i + 1, fam, forced)
        if accessible:
            new = {s & t for t in fam} - fam - {s}
            fam.add(s)
            rec(i + 1, fam, forced | new)
            fam.discard(s)

    rec(0, set(), frozenset())
    return out


def canonical(fam, n):
    best = None
    for p in itertools.permutations(range(n)):
        img = tuple(sorted(sum(1 << p[x] for x in range(n) if s >> x & 1) for s in fam))
        if best is None or img < best:
            best = img
    return best


def lattice(sets):
    N = len(sets)
    idx = {s: i for i, s in enumerate(sets)}

    def closure(m):
        return min((s for s in sets if s & m == m), key=lambda s: bin(s).count("1"))

    join = [[idx[closure(a | b)] for b in sets] for a in sets]
    meet = [[idx[a & b] for b in sets] for a in sets]
    le = [[sets[i] & sets[j] == sets[i] for j in range(N)] for i in range(N)]
    lower = [[j for j in range(N) if j != i and le[j][i]
              and not any(k not in (i, j) and le[j][k] and le[k][i] for k in range(N))] for i in range(N)]
    upper = [[j for j in range(N) if i in lower[j]] for i in range(N)]
    return N, join, meet, le, lower, upper


def maximal_complements(N, join, meet):
    def gen(S):
        S = set(S)
        while True:
            new = {join[a][b] for a in S for b in S} | {meet[a][b] for a in S for b in S}
            if new <= S:
                return S
            S |= new

    solver = Cadical153()
    for a in range(N):
        for b in range(a + 1, N):
            solver.add_clause([-(a + 1), -(b + 1), join[a][b] + 1])
            solver.add_clause([-(a + 1), -(b + 1), meet[a][b] + 1])
    solver.add_clause([1])
    solver.add_clause([N])
    solver.add_clause([-(i + 1) for i in range(N)])
    comps = []
    while solver.solve():
        model = solver.get_model()
        S = gen({i for i in range(N) if model[i] > 0})
        for c in range(N):
            if c not in S:
                T = gen(S | {c})
                if len(T) < N:
                    S = T
        C = [i for i in range(N) if i not in S]
        comps.append(C)
        solver.add_clause([c + 1 for c in C])   # the next sublattice is not contained in this one
    solver.delete()
    return comps


def tests(N, meet, le, lower, upper, C):
    Cs = set(C)
    lo = C[0]
    for x in C:
        lo = meet[lo][x]
    convex = all(not (le[a][b] and le[b][c]) or b in Cs for a in C for c in C for b in range(N))
    h2 = lo in Cs and convex
    h4 = all(any(m not in Cs and not any(le[z][m] for z in C) for m in lower[x]) for x in C)
    q2_join = sum(1 for x in C if len(lower[x]) == 1) == 1
    q2_meet = not any(len(upper[x]) == 1 and any(y != x and le[x][y] for y in C) for x in C)
    return h2, h4, q2_join, q2_meet


def digraph6(sets, le):
    inner = list(range(1, len(sets) - 1))
    m = len(inner)
    bits = []
    for i in inner:
        for j in inner:
            cover = i != j and le[i][j] and not any(k not in (i, j) and le[i][k] and le[k][j] for k in inner)
            bits.append(1 if cover else 0)
    bits += [0] * (-len(bits) % 6)
    return "&" + chr(63 + m) + "".join(chr(63 + int("".join(map(str, bits[k:k + 6])), 2))
                                       for k in range(0, len(bits), 6))


def main():
    n = int(sys.argv[1])
    d6 = sys.argv[sys.argv.index("--digraph6") + 1] if "--digraph6" in sys.argv else None
    labeled = geometries(n)
    classes = {}
    for fam in labeled:
        classes.setdefault(canonical(fam, n), fam)
    print(f"n = {n}: {len(labeled)} labeled and {len(classes)} unlabeled convex geometries")
    names = "abcdefgh"
    by_size = {}
    fails = []
    lines = []
    for key in sorted(classes, key=lambda k: (len(k), k)):
        sets = sorted(key, key=lambda s: (bin(s).count("1"), s))
        N, join, meet, le, lower, upper = lattice(sets)
        if d6 and N <= 22 and N >= 3:
            lines.append(digraph6(sets, le))
        row = by_size.setdefault(N, [0, 0, 0, 0, 0])
        row[0] += 1
        bad = [False] * 4
        for C in maximal_complements(N, join, meet):
            for i, ok in enumerate(tests(N, meet, le, lower, upper, C)):
                if not ok:
                    bad[i] = True
            h2, h4, qj, qm = tests(N, meet, le, lower, upper, C)
            if not h2:
                fails.append((N, [("".join(names[x] for x in range(n) if s >> x & 1) or "0") for s in sets],
                              [("".join(names[x] for x in range(n) if sets[c] >> x & 1)) for c in C]))
        for i in range(4):
            row[i + 1] += bad[i]
    print("closed sets: geometries, failing H2, failing H4, failing Q2 join half, failing Q2 meet half")
    for N in sorted(by_size):
        print(f"  {N:3d}: {by_size[N]}")
    for N, sets, C in sorted(fails)[:3]:
        print(f"  H2 fails with {N} closed sets {sets}: complement {C}")
    if d6:
        open(d6, "w").write("\n".join(lines) + "\n")
        print(f"wrote {len(lines)} Hasse diagrams to {d6}")


if __name__ == "__main__":
    main()
