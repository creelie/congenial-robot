"""Second implementation of the small-lattice search, in Python with the standard library only.

Reads the Hasse diagrams of all posets on m points (digraph6, from `nauty-genposetg m t q`) on
standard input, adds a least and a greatest element, keeps the lattices, and reports

  * the number of lattices (to compare with OEIS A006966),
  * the maximal proper sublattices whose complement is not order convex (Hypothesis 3), and
  * for convex geometries (meet-distributive lattices), the maximal proper sublattices whose
    complement contains a meet-irreducible element that is not maximal in the complement, or a
    join-irreducible element that is not its least element (Question 2).

It shares no code with verification/c/maxsub.c. Usage:
    nauty-genposetg 8 t q | python3 check_minimal.py
    nauty-genposetg 9 t q | python3 check_minimal.py cg     (sublattices of convex geometries only)
"""
import sys


def parse_digraph6(line):
    n = ord(line[1]) - 63
    bits = []
    for ch in line[2:]:
        v = ord(ch) - 63
        bits.extend((v >> (5 - i)) & 1 for i in range(6))
    return n, [[bits[i * n + j] for j in range(n)] for i in range(n)]


def lattice_from_poset(m, adj):
    n = m + 2
    up = [1 << x for x in range(n)]          # up[x] = {y : x <= y} as a bit mask
    for i in range(m):
        for j in range(m):
            if adj[i][j]:
                up[i + 1] |= 1 << (j + 1)
    up[0] = (1 << n) - 1
    for x in range(1, n - 1):
        up[x] |= 1 << (n - 1)
    changed = True
    while changed:
        changed = False
        for x in range(n):
            u = up[x]
            for y in range(n):
                if u >> y & 1 and up[y] | u != u:
                    u |= up[y]
            if u != up[x]:
                up[x] = u
                changed = True
    down = [sum(1 << y for y in range(n) if up[y] >> x & 1) for x in range(n)]
    join = [[0] * n for _ in range(n)]
    meet = [[0] * n for _ in range(n)]
    for x in range(n):
        for y in range(x, n):
            u, d = up[x] & up[y], down[x] & down[y]
            j = [z for z in range(n) if u >> z & 1 and up[z] & u == u]
            k = [z for z in range(n) if d >> z & 1 and down[z] & d == d]
            if not j or not k:
                return None
            join[x][y] = join[y][x] = j[0]
            meet[x][y] = meet[y][x] = k[0]
    return n, up, down, join, meet


def maximal_sublattices(n, join, meet):
    full = (1 << n) - 1
    closed = []
    for s in range(1, full):
        el = [x for x in range(n) if s >> x & 1]
        if all(s >> join[a][b] & 1 and s >> meet[a][b] & 1 for i, a in enumerate(el) for b in el[i + 1:]):
            closed.append(s)
    return [s for s in closed if not any(t != s and t & s == s for t in closed)]


def is_convex_geometry(n, up, down, join, meet):
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if join[x][y] == join[x][z] and join[x][y] != join[x][meet[y][z]]:
                    return False
    for x in range(n):
        lc = [y for y in range(n) if y != x and down[x] >> y & 1
              and (up[y] & down[x]) == (1 << y) | (1 << x)]
        meets = set()
        for t in range(1 << len(lc)):
            v = x
            for i, y in enumerate(lc):
                if t >> i & 1:
                    v = meet[v][y]
            meets.add(v)
        if len(meets) != 1 << len(lc):
            return False
        bottom = x
        for y in lc:
            bottom = meet[bottom][y]
        if {z for z in range(n) if up[bottom] >> z & 1 and down[x] >> z & 1} != meets:
            return False
    return True


def main():
    cg_only = sys.argv[1:] == ["cg"]
    stats = dict(posets=0, lattices=0, nonconvex=0, cg=0, q2_meet=0, q2_join=0)
    for line in sys.stdin:
        if not line.startswith("&"):
            continue
        stats["posets"] += 1
        m, adj = parse_digraph6(line.strip())
        lat = lattice_from_poset(m, adj)
        if lat is None:
            continue
        n, up, down, join, meet = lat
        stats["lattices"] += 1
        cg = is_convex_geometry(n, up, down, join, meet)
        stats["cg"] += cg
        if cg_only and not cg:
            continue
        for s in maximal_sublattices(n, join, meet):
            comp = ((1 << n) - 1) & ~s
            if any(down[d] & comp and up[d] & comp for d in range(n) if s >> d & 1):
                stats["nonconvex"] += 1
                print("nonconvex", n, line.strip(), [x for x in range(n) if s >> x & 1])
            if cg and not comp & 1 and not comp >> (n - 1) & 1:
                cs = [x for x in range(n) if comp >> x & 1]
                lo = cs[0]
                for x in cs:
                    lo = meet[lo][x]
                for x in cs:
                    ucov = [y for y in range(n) if y != x and up[x] >> y & 1
                            and (up[x] & down[y]) == (1 << x) | (1 << y)]
                    lcov = [y for y in range(n) if y != x and down[x] >> y & 1
                            and (up[y] & down[x]) == (1 << y) | (1 << x)]
                    if len(ucov) == 1 and any(y != x and up[x] >> y & 1 for y in cs):
                        stats["q2_meet"] += 1
                        print("question2-meet", n, line.strip(), cs)
                        break
                for x in cs:
                    lcov = [y for y in range(n) if y != x and down[x] >> y & 1
                            and (up[y] & down[x]) == (1 << y) | (1 << x)]
                    if len(lcov) == 1 and x != lo:
                        stats["q2_join"] += 1
                        print("question2-join", n, line.strip(), cs)
                        break
    print(" ".join(f"{k} {v}" for k, v in stats.items()))


if __name__ == "__main__":
    main()
