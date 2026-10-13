"""Convex geometries on six points of convex dimension at most three and Hypothesis 2.

Every such geometry is the family of intersections of the initial segments of three linear orders of
{0, ..., 5} (repetitions allowed), and after relabelling the points the first order is 0 < 1 < ... < 5.
The script runs through all pairs of further orders, keeps the families with at most 25 closed sets,
reduces them to isomorphism classes, and tests Hypothesis 2 on every maximal sublattice of each class
(with the SAT search of convex_geometries.py). Expected output: 8435 classes, exactly one of which
fails Hypothesis 2; it has 25 closed sets and is the geometry of Theorem E.

Usage: python3 dimension_three.py [workers]      (about a quarter of an hour on three cores)
"""
import itertools
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convex_geometries import canonical, lattice, maximal_complements, tests  # noqa: E402

n, NMAX = 6, 25


def family(orders):
    fam = {0}
    for o in orders:
        m = 0
        for x in o:
            m |= 1 << x
            fam.add(m)
    changed = True
    while changed:
        changed = False
        for a in list(fam):
            for b in list(fam):
                if a & b not in fam:
                    fam.add(a & b)
                    changed = True
    return tuple(sorted(fam, key=lambda s: (bin(s).count("1"), s)))


def canon(sets):
    return canonical(sets, n)


def fails_h2(sets):
    sets = list(sets)
    N, join, meet, le, lower, upper = lattice(sets)
    return sets, any(not tests(N, meet, le, lower, upper, C)[0] for C in maximal_complements(N, join, meet))


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    perms = list(itertools.permutations(range(n)))
    fams = set()
    for i, o2 in enumerate(perms):
        for o3 in perms[i:]:
            f = family((perms[0], o2, o3))
            if len(f) <= NMAX:
                fams.add(f)
    with Pool(workers) as p:
        classes = sorted(set(p.map(canon, fams, chunksize=200)))
        by_size = {}
        for c in classes:
            by_size[len(c)] = by_size.get(len(c), 0) + 1
        print(f"{len(fams)} labelled families, {len(classes)} isomorphism classes with at most {NMAX} closed sets")
        print("classes by number of closed sets:", sorted(by_size.items()))
        bad = [s for s, f in p.map(fails_h2, classes, chunksize=20) if f]
    names = "abcdef"
    print(f"classes failing Hypothesis 2: {len(bad)}")
    for s in bad:
        print(f"  {len(s)} closed sets:", [("".join(names[x] for x in range(n) if t >> x & 1) or "0") for t in s])


if __name__ == "__main__":
    main()
