"""Independent checks of the two examples, in Python with the standard library only.

1. The ten-element lattice L10: M = {0, 1, 4, 6, 9} is a maximal proper sublattice and its
   complement {2, 3, 5, 7, 8} is not order convex (2 < 6 < 7).
2. The eleven-element lattice L11 is the lattice of closed sets of the convex geometry on {a, b, c, d}
   whose closed sets are listed below: the sets are closed under intersection, the closure operator
   has the anti-exchange property, and the lattice is join semidistributive and lower semimodular.
   M = {0, 2, 3, 6, 7, 9, 10} is a maximal proper sublattice, the complement is the interval
   [a, abc] = {a, ab, ac, abc}, and ac is meet-irreducible but lies below abc.
3. The seventeen-element lattice L17 is the lattice of closed sets of a convex geometry on
   {a, b, c, d, e}; M = {0, b, c, e, ae, de, ade, abde, acde, abcde} is a maximal proper sublattice and its
   complement {a, d, ac, ad, bd, abd, acd} has two minimal elements a and d (Hypothesis 2 fails), the
   element ad has no lower cover in M (Hypothesis 4 fails), and a and d are join-irreducible.
4. The twenty-five-element lattice L25 is the lattice of closed sets of a convex geometry on
   {a, b, c, d, e, f} realized by three linear orders and by no two (its meet-irreducibles have width
   three); M = {0, a, f} together with the closed sets containing d is a maximal proper sublattice, its
   complement has the three minimal elements b, c and e, and bc has no lower cover in M.
5. All maximal proper sublattices of L10, L11 and L17 are listed, so the reader can compare them with
   the paper.
"""
import itertools


def from_covers(n, covers):
    le = [[i == j for j in range(n)] for i in range(n)]
    for c in covers.split():
        a, b = map(int, c.split("<"))
        le[a][b] = True
    for k in range(n):
        for i in range(n):
            for j in range(n):
                le[i][j] = le[i][j] or (le[i][k] and le[k][j])
    join = [[None] * n for _ in range(n)]
    meet = [[None] * n for _ in range(n)]
    for a in range(n):
        for b in range(n):
            ub = [z for z in range(n) if le[a][z] and le[b][z]]
            lb = [z for z in range(n) if le[z][a] and le[z][b]]
            least = [z for z in ub if all(le[z][w] for w in ub)]
            great = [z for z in lb if all(le[w][z] for w in lb)]
            assert len(least) == 1 and len(great) == 1, "not a lattice"
            join[a][b], meet[a][b] = least[0], great[0]
    return le, join, meet


def generated(n, join, meet, gens):
    s = set(gens)
    while True:
        new = {op[a][b] for a in s for b in s for op in (join, meet)} - s
        if not new:
            return s
        s |= new


def is_sublattice(s, join, meet):
    return all(join[a][b] in s and meet[a][b] in s for a in s for b in s)


def maximal_sublattices(n, join, meet):
    subs = [frozenset(x for x in range(n) if m >> x & 1) for m in range(1, (1 << n) - 1)]
    subs = [s for s in subs if is_sublattice(s, join, meet)]
    return [s for s in subs if not any(s < t for t in subs)]


def covers_of(n, le):
    return {(a, b) for a in range(n) for b in range(n) if a != b and le[a][b]
            and not any(le[a][z] and le[z][b] and z not in (a, b) for z in range(n))}


def check_l10():
    n = 10
    le, join, meet = from_covers(n, "0<1 0<2 0<3 1<8 2<5 2<6 3<4 3<5 4<9 5<7 5<8 6<7 7<9 8<9")
    M = {0, 1, 4, 6, 9}
    C = set(range(n)) - M
    assert is_sublattice(M, join, meet)
    for c in C:
        assert generated(n, join, meet, M | {c}) == set(range(n))
    assert le[2][6] and le[6][7] and 2 in C and 7 in C and 6 in M
    maxs = maximal_sublattices(n, join, meet)
    assert frozenset(M) in maxs
    print("1. L10: M = {0,1,4,6,9} is a maximal sublattice; its complement {2,3,5,7,8} contains 2 < 7 "
          "but not 6, with 2 < 6 < 7: ok")
    print("   complements of all maximal sublattices of L10:",
          sorted(sorted(set(range(n)) - s) for s in maxs))


def check_l11():
    n = 11
    le, join, meet = from_covers(n, "0<1 0<2 0<3 1<4 1<5 1<6 2<4 2<7 3<5 3<7 4<8 4<9 5<8 6<9 7<8 8<10 9<10")
    names = ["", "a", "b", "c", "ab", "ac", "ad", "bc", "abc", "abd", "abcd"]
    sets = [frozenset(s) for s in names]
    # the order of L11 is inclusion of these sets, and they are closed under intersection
    for i in range(n):
        for j in range(n):
            assert le[i][j] == (sets[i] <= sets[j])
            assert sets[meet[i][j]] == sets[i] & sets[j]
    closed = set(sets)

    def phi(a):
        return min((c for c in closed if a <= c), key=len)

    pts = "abcd"
    anti = all(not (q in phi(a | {p}) and p in phi(a | {q}))
               for a in closed for p in pts for q in pts if p != q and p not in a and q not in a)
    assert phi(frozenset()) == frozenset() and anti
    sd_join = all(join[x][y] != join[x][z] or join[x][y] == join[x][meet[y][z]]
                  for x in range(n) for y in range(n) for z in range(n))
    cov = covers_of(n, le)
    lsm = all(((x, join[x][y]) not in cov) or ((meet[x][y], y) in cov) for x in range(n) for y in range(n))
    sd_meet = all(meet[x][y] != meet[x][z] or meet[x][y] == meet[x][join[y][z]]
                  for x in range(n) for y in range(n) for z in range(n))
    assert sd_join and lsm and not sd_meet
    M = {0, 2, 3, 6, 7, 9, 10}
    C = set(range(n)) - M
    assert is_sublattice(M, join, meet)
    for c in C:
        assert generated(n, join, meet, M | {c}) == set(range(n))
    assert C == {x for x in range(n) if le[1][x] and le[x][8]}
    upper = {x: [y for (z, y) in cov if z == x] for x in range(n)}
    lower = {x: [z for (z, y) in cov if y == x] for x in range(n)}
    mi = sorted(x for x in range(n) if len(upper[x]) == 1)
    ji = sorted(x for x in range(n) if len(lower[x]) == 1)
    assert 5 in mi and le[5][8] and 5 in C and 8 in C
    # the meet-irreducible 5 = ac is not maximal in C, while the only join-irreducible in C is its least element a
    assert [x for x in C if x in ji] == [1]
    print("2. L11 is the lattice of closed sets of a convex geometry on {a,b,c,d} (anti-exchange), "
          "join semidistributive, lower semimodular, not meet semidistributive: ok")
    print("   M = {0,2,3,6,7,9,10} is maximal; C = [a, abc] = {a, ab, ac, abc}; ac is meet-irreducible "
          "and ac < abc: ok")
    maxs = maximal_sublattices(n, join, meet)
    assert frozenset(M) in maxs
    print("   complements of all maximal sublattices of L11:",
          [[names[x] or "0" for x in sorted(set(range(n)) - s)] for s in maxs])
    # the closed sets are generated by three maximal chains (convex dimension 3): the meet-irreducibles
    # form a poset of width 3
    width = max(r for r in range(1, len(mi) + 1) for A in itertools.combinations(mi, r)
                if all(not le[p][q] and not le[q][p] for p, q in itertools.combinations(A, 2)))
    assert width == 3
    print("   meet-irreducibles", [names[x] for x in mi], "form a poset of width 3 (convex dimension 3): ok")


def check_l17():
    names = ["", "a", "b", "c", "d", "e", "ac", "ad", "bd", "ae", "de", "abd", "acd", "ade", "abde", "acde",
             "abcde"]
    K = [frozenset(s) for s in names]
    n = len(K)
    X = K[-1]
    assert all(A & B in K for A in K for B in K)

    def phi(Y):
        return min((A for A in K if Y <= A), key=len)

    assert all(not (q in phi(A | {p}) and p in phi(A | {q}))
               for A in K for p in X - A for q in X - A if p != q)
    le = [[K[i] <= K[j] for j in range(n)] for i in range(n)]
    join = [[K.index(phi(K[i] | K[j])) for j in range(n)] for i in range(n)]
    meet = [[K.index(K[i] & K[j]) for j in range(n)] for i in range(n)]
    sd_join = all(join[x][y] != join[x][z] or join[x][y] == join[x][meet[y][z]]
                  for x in range(n) for y in range(n) for z in range(n))
    cov = covers_of(n, le)
    lsm = all(((x, join[x][y]) not in cov) or ((meet[x][y], y) in cov) for x in range(n) for y in range(n))
    assert sd_join and lsm
    M = {names.index(s) for s in ["", "b", "c", "e", "ae", "de", "ade", "abde", "acde", "abcde"]}
    C = set(range(n)) - M
    assert is_sublattice(M, join, meet)
    for c in C:
        assert generated(n, join, meet, M | {c}) == set(range(n))
    minimal = sorted(names[c] for c in C if not any(d != c and le[d][c] for d in C))
    assert minimal == ["a", "d"]
    ad = names.index("ad")
    assert all(z in C for (z, y) in cov if y == ad)
    lower = {x: [z for (z, y) in cov if y == x] for x in range(n)}
    assert [names[x] for x in sorted(C) if len(lower[x]) == 1] == ["a", "d"]
    print("3. L17 is the lattice of closed sets of a convex geometry on {a,b,c,d,e}, join semidistributive "
          "and lower semimodular: ok")
    print("   M = {0,b,c,e,ae,de,ade,abde,acde,abcde} is maximal; the complement", sorted(names[c] for c in C),
          "has the two minimal elements a, d; both lower covers of ad lie outside M: ok")
    maxs = maximal_sublattices(n, join, meet)
    assert frozenset(M) in maxs
    print("   complements of all maximal sublattices of L17:",
          [[names[x] or "0" for x in sorted(set(range(n)) - s)] for s in maxs])


def check_l25():
    names = ["", "a", "b", "c", "d", "e", "f", "ab", "bc", "bd", "be", "ce", "de", "cf", "abc", "bcd", "bce",
             "bde", "cef", "abcd", "bcde", "bcef", "abcde", "bcdef", "abcdef"]
    K = [frozenset(s) for s in names]
    n = len(K)
    X = K[-1]
    # the intersections of initial segments of three orders are exactly the closed sets
    orders = ["abcdef", "fcebda", "debcaf"]
    segs = {frozenset(o[:k]) for o in orders for k in range(7)}
    inters = set()
    for Y in (frozenset(t) for k in range(7) for t in itertools.combinations("abcdef", k)):
        if Y == X.intersection(*[S for S in segs if Y <= S]):
            inters.add(Y)
    assert inters == set(K)
    assert all(A & B in K for A in K for B in K)

    def phi(Y):
        return min((A for A in K if Y <= A), key=len)

    assert all(not (q in phi(A | {p}) and p in phi(A | {q}))
               for A in K for p in X - A for q in X - A if p != q)
    le = [[K[i] <= K[j] for j in range(n)] for i in range(n)]
    join = [[K.index(phi(K[i] | K[j])) for j in range(n)] for i in range(n)]
    meet = [[K.index(K[i] & K[j]) for j in range(n)] for i in range(n)]
    sd_join = all(join[x][y] != join[x][z] or join[x][y] == join[x][meet[y][z]]
                  for x in range(n) for y in range(n) for z in range(n))
    cov = covers_of(n, le)
    lsm = all(((x, join[x][y]) not in cov) or ((meet[x][y], y) in cov) for x in range(n) for y in range(n))
    assert sd_join and lsm
    # convex dimension: the meet-irreducibles have width three, so no two orders realize the closed sets
    upper = {x: [y for (z, y) in cov if z == x] for x in range(n)}
    mi = [x for x in range(n) if len(upper[x]) == 1]
    width = max(r for r in range(1, 5) for A in itertools.combinations(mi, r)
                if all(not le[p][q] and not le[q][p] for p, q in itertools.combinations(A, 2)))
    assert width == 3
    M = {i for i in range(n) if names[i] in ("", "a", "f") or "d" in names[i]}
    C = set(range(n)) - M
    assert is_sublattice(M, join, meet)
    for c in C:
        assert generated(n, join, meet, M | {c}) == set(range(n))
    minimal = sorted(names[c] for c in C if not any(d != c and le[d][c] for d in C))
    assert minimal == ["b", "c", "e"]
    bc = names.index("bc")
    assert all(z in C for (z, y) in cov if y == bc)
    print("4. L25 is the lattice of closed sets of a convex geometry on {a,...,f} realized by the orders",
          orders, "and of convex dimension 3 (meet-irreducibles of width 3); join semidistributive and "
          "lower semimodular: ok")
    print("   M = {0,a,f} + {closed sets containing d} is maximal; the complement", sorted(names[c] for c in C),
          "has the minimal elements b, c, e; both lower covers of bc lie outside M: ok")


if __name__ == "__main__":
    check_l10()
    check_l11()
    check_l17()
    check_l25()
