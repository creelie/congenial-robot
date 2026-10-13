// maxsub.c : reads Hasse diagrams of posets (digraph6, as written by nauty-genposetg) on stdin. For each
// poset P it forms L = P with a new least and greatest element; if L is a lattice, it finds every maximal
// proper sublattice M (by enumerating all subsets) and tests, for the complement C = L \ M, the hypotheses
// of Adaricheva, Mata, Silberger and Zamojska-Dzienio:
//   H1  L semidistributive          => C is an interval              (counter sd-noninterval)
//   H2  L join semidistributive     => C has a least element and is order convex (h2join-fail; dual h2meet-fail)
//   H3  any L                       => C is order convex             (nonconvex)
//   H4  L a convex geometry         => every x in C has a lower cover m in M with [0,m] inside M (H4-fail)
//   Q2  L a convex geometry         => the only join-irreducible in C is its least element and the only
//                                      meet-irreducibles in C are its maximal elements (Q2-join/meet-part-fail)
// It also counts semidistributive lattices that are not both lower and upper bounded (D relation).
// Environment: SDONLY=1 skips lattices that are neither join nor meet semidistributive; DUMPNB=1 prints
// the semidistributive lattices that are not bounded; DUMPCG=1 prints every convex geometry.
// Lattices with at most 22 elements; memory about 2 * 22 * 2^22 * 4 bytes.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAXN 22
static int N;
static unsigned up_[MAXN], dn_[MAXN];       // up_[x] = {y >= x}, dn_[x] = {y <= x}
static int J[MAXN][MAXN], Mt[MAXN][MAXN];
static unsigned *JM, *MM;               // JM[x<<N | S] = {x v y : y in S}
static unsigned char *cl, *h;
static long long ncg, nmaxcg, nh4, nq2, nq2j, nq2m;
static unsigned lowc[MAXN];
static long long nposets, nlat, nmax, nviol, nsd, nsdnonint, nsdj, nsdm, nh2j, nh2m, nsdnb, nmaxnb;
static int sdflag, nbflag;
static int printed;

static int parse(const char *s, unsigned *adj) {   // digraph6
  if (s[0] != '&') return -1;
  int n = s[1] - 63; const char *p = s + 2; int bit = 0, k = 0;
  memset(adj, 0, sizeof(unsigned) * MAXN);
  for (int i = 0; i < n; i++) for (int j = 0; j < n; j++) {
    int c = p[k] - 63; int b = (c >> (5 - bit)) & 1;
    if (b) adj[i] |= 1u << j;
    if (++bit == 6) { bit = 0; k++; }
  }
  return n;
}

static void report(const char *what, unsigned M) {
  if (printed > 40) return;
  printed++;
  printf("%s N=%d M=", what, N);
  for (int x = 0; x < N; x++) if (M >> x & 1) printf("%d ", x);
  printf("| order:");
  for (int x = 0; x < N; x++) for (int y = 0; y < N; y++) if (x != y && (up_[x] >> y & 1)) {
    // print covers only
    int cover = 1; for (int z = 0; z < N; z++) if (z != x && z != y && (up_[x] >> z & 1) && (up_[z] >> y & 1)) cover = 0;
    if (cover) printf(" %d<%d", x, y);
  }
  printf("\n"); fflush(stdout);
}


// lower bounded test: D relation on join-irreducibles, p D q iff q lies in a minimal nontrivial join cover of p
static int joinOf(unsigned A) { int r = 0; for (unsigned R = A; R; R &= R - 1) r = J[r][__builtin_ctz(R)]; return r; }
static int meetOf(unsigned A) { int r = N - 1; for (unsigned R = A; R; R &= R - 1) r = Mt[r][__builtin_ctz(R)]; return r; }
static int acyclic(unsigned *D, unsigned V) {   // D[p] = successors; Kahn-style removal of sinks
  unsigned left = V; int changed = 1;
  while (changed) { changed = 0;
    for (unsigned R = left; R; R &= R - 1) { int p = __builtin_ctz(R); if (!(D[p] & left)) { left &= ~(1u << p); changed = 1; } } }
  return left == 0;
}
static int lowerBounded(int dual) {
  unsigned JI = 0; unsigned D[MAXN]; memset(D, 0, sizeof D);
  for (int p = 0; p < N; p++) {           // join irreducible: exactly one lower cover (dual: one upper cover)
    unsigned below = dual ? (up_[p] & ~(1u << p)) : (dn_[p] & ~(1u << p));
    if (!below) continue;
    int top = dual ? meetOf(below) : joinOf(below);
    if (top != p) JI |= 1u << p;
  }
  for (unsigned R = JI; R; R &= R - 1) { int p = __builtin_ctz(R);
    unsigned le = dual ? up_[p] : dn_[p];     // elements a with p <= a are trivial covers (dual: a <= p)
    unsigned cand = JI & ~(dual ? dn_[p] : up_[p]);   // a with p not<= a  (dual: a not>= p)
    // enumerate subsets A of cand
    for (unsigned A = cand; A; A = (A - 1) & cand) {
      int jn = dual ? meetOf(A) : joinOf(A);
      int cover = dual ? (dn_[p] >> jn & 1) : (up_[p] >> jn & 1);
      if (!cover) continue;
      int minimal = 1;
      for (unsigned T = A; T && minimal; T &= T - 1) { int a = __builtin_ctz(T);
        unsigned B = A & ~(1u << a);
        if (B) { int j2 = dual ? meetOf(B) : joinOf(B); if (dual ? (dn_[p] >> j2 & 1) : (up_[p] >> j2 & 1)) minimal = 0; }
        // replace a by its unique lower cover a_* (dual: upper cover)
        unsigned strict = (dual ? up_[a] : dn_[a]) & ~(1u << a);
        int as = dual ? meetOf(strict) : joinOf(strict);
        int j3 = dual ? Mt[as][meetOf(B | (1u << as))] : J[as][joinOf(B | (1u << as))];
        if (dual ? (dn_[p] >> j3 & 1) : (up_[p] >> j3 & 1)) minimal = 0;
      }
      if (minimal) D[p] |= A;
    }
    (void)le;
  }
  return acyclic(D, JI);
}

static void doLattice(void) {
  unsigned full = (1u << N) - 1, S;
  // semidistributivity
  int sd = 1;
  for (int x = 0; x < N && sd; x++) for (int y = 0; y < N && sd; y++) for (int z = 0; z < N && sd; z++) {
    if (J[x][y] == J[x][z] && J[x][y] != J[x][Mt[y][z]]) sd = 0;
    if (Mt[x][y] == Mt[x][z] && Mt[x][y] != Mt[x][J[y][z]]) sd = 0;
  }
  int sdj = 1, sdm = 1;
  for (int x = 0; x < N && (sdj || sdm); x++) for (int y = 0; y < N; y++) for (int z = 0; z < N; z++) {
    if (J[x][y] == J[x][z] && J[x][y] != J[x][Mt[y][z]]) sdj = 0;
    if (Mt[x][y] == Mt[x][z] && Mt[x][y] != Mt[x][J[y][z]]) sdm = 0;
  }
  nsd += sd; nsdj += sdj; nsdm += sdm;
  if (getenv("SDONLY") && !sdj && !sdm) return;
  for (int x = 0; x < N; x++) { lowc[x] = 0;
    for (unsigned R = dn_[x] & ~(1u << x); R; R &= R - 1) { int y = __builtin_ctz(R);
      if ((up_[y] & dn_[x]) == ((1u << y) | (1u << x))) lowc[x] |= 1u << y; } }
  int cg = sdj;   // convex geometry: SD-join and every [meet of lower covers of x, x] Boolean
  for (int x = 0; x < N && cg; x++) {
    int lc[MAXN], k = 0; for (unsigned R = lowc[x]; R; R &= R - 1) lc[k++] = __builtin_ctz(R);
    unsigned seen = 0; int cnt = 0;
    for (int T = 0; T < (1 << k); T++) { int m = x; for (int i = 0; i < k; i++) if (T >> i & 1) m = Mt[m][lc[i]];
      if (seen >> m & 1) { cg = 0; break; } seen |= 1u << m; cnt++; }
    if (cg) { int mx = x; for (int i = 0; i < k; i++) mx = Mt[mx][lc[i]];
      if ((up_[mx] & dn_[x]) != seen) cg = 0; }
  }
  ncg += cg;
  if (cg && getenv("DUMPCG")) { printf("CG %d", N); for (int x = 0; x < N; x++) for (unsigned R = lowc[x]; R; R &= R - 1) printf(" %d<%d", __builtin_ctz(R), x); printf("\n"); }
  sdflag = sd; nbflag = 0;
  if (sd && !(lowerBounded(0) && lowerBounded(1))) { nsdnb++; nbflag = 1;
    if (getenv("DUMPNB")) { printf("NB %d", N); for (int x = 0; x < N; x++) for (int y = 0; y < N; y++) if (x != y && (up_[x] >> y & 1)) {
      int cover = 1; for (int z = 0; z < N; z++) if (z != x && z != y && (up_[x] >> z & 1) && (up_[z] >> y & 1)) cover = 0;
      if (cover) printf(" %d<%d", x, y); } printf("\n"); } }

  for (int x = 0; x < N; x++) {
    unsigned *jm = JM + ((size_t)x << N), *mm = MM + ((size_t)x << N);
    jm[0] = mm[0] = 0;
    for (S = 1; S <= full; S++) { int y = __builtin_ctz(S); unsigned T = S & (S - 1);
      jm[S] = jm[T] | (1u << J[x][y]); mm[S] = mm[T] | (1u << Mt[x][y]); }
  }
  for (S = 0; S <= full; S++) {
    int ok = S != 0;
    for (unsigned R = S; R && ok; R &= R - 1) { int x = __builtin_ctz(R);
      if ((JM[((size_t)x << N) | S] | MM[((size_t)x << N) | S]) & ~S) ok = 0; }
    cl[S] = ok && S != full;
  }
  // h[S] = some proper closed T with T ⊇ S
  for (S = 0; S <= full; S++) h[S] = cl[S];
  for (int b = 0; b < N; b++) for (S = 0; S <= full; S++) if (!(S >> b & 1)) h[S] |= h[S | 1u << b];
  for (S = 1; S < full; S++) if (cl[S]) {
    int maxl = 1;
    for (int b = 0; b < N && maxl; b++) if (!(S >> b & 1) && h[S | 1u << b]) maxl = 0;
    if (!maxl) continue;
    nmax++; if (nbflag) nmaxnb++;
    unsigned C = full & ~S;
    int viol = 0;
    for (unsigned R = S; R; R &= R - 1) { int d = __builtin_ctz(R);
      if ((dn_[d] & C) && (up_[d] & C)) { viol = 1; break; } }
    if (viol) { nviol++; report("NONCONVEX", S); }
    { // Hypothesis 2: SD-join => C has a least element and is convex; dually for SD-meet
      int lo, hi; unsigned R = C; lo = hi = __builtin_ctz(R);
      for (R &= R - 1; R; R &= R - 1) { int x = __builtin_ctz(R); lo = Mt[lo][x]; hi = J[hi][x]; }
      if (sdj && (viol || !(C >> lo & 1))) { nh2j++; report("H2-JOIN-FAILS", S); }
      if (sdm && (viol || !(C >> hi & 1))) { nh2m++; report("H2-MEET-FAILS", S); }
    }
    if (cg && !(C & 1u) && !(C >> (N - 1) & 1)) { nmaxcg++;
      int h4 = 1;
      for (unsigned R = C; R && h4; R &= R - 1) { int x = __builtin_ctz(R); int ok = 0;
        for (unsigned Q = lowc[x]; Q; Q &= Q - 1) { int m = __builtin_ctz(Q); if ((S >> m & 1) && !(dn_[m] & C)) { ok = 1; break; } }
        if (!ok) h4 = 0; }
      if (!h4) { nh4++; report("H4-FAILS", S); }
      int lo = __builtin_ctz(C); for (unsigned R = C; R; R &= R - 1) lo = Mt[lo][__builtin_ctz(R)];
      int q2 = 1, q2j = 1, q2m = 1;
      for (unsigned R = C; R; R &= R - 1) { int x = __builtin_ctz(R);
        int ji = __builtin_popcount(lowc[x]) == 1;
        unsigned upc = 0; for (int y = 0; y < N; y++) if (lowc[y] >> x & 1) upc |= 1u << y;
        int mi = __builtin_popcount(upc) == 1;
        if (ji && x != lo) q2 = q2j = 0;
        if (mi && (up_[x] & C & ~(1u << x))) q2 = q2m = 0; }
      if (!q2) { nq2++; report("Q2-FAILS", S); }
      nq2j += !q2j; nq2m += !q2m;
    }
    if (sd) { // interval test: C = [meet C, join C]
      int lo = -1, hi = -1;
      unsigned R = C; int f = __builtin_ctz(R); lo = hi = f;
      for (R &= R - 1; R; R &= R - 1) { int x = __builtin_ctz(R); lo = Mt[lo][x]; hi = J[hi][x]; }
      unsigned I = up_[lo] & dn_[hi];
      if (I != C) { nsdnonint++; report("SD-NONINTERVAL", S); }
    }
  }
}

int main(int argc, char **argv) {
  char line[256]; unsigned adj[MAXN];
  JM = malloc(sizeof(unsigned) * MAXN << MAXN); MM = malloc(sizeof(unsigned) * MAXN << MAXN);
  cl = malloc(1u << MAXN); h = malloc(1u << MAXN);
  while (fgets(line, sizeof line, stdin)) {
    if (line[0] != '&') continue;
    int m = parse(line, adj); nposets++;
    N = m + 2; int top = N - 1;
    // element i+1 for poset point i; edge i->j means i < j
    unsigned lt[MAXN]; memset(lt, 0, sizeof lt);   // lt[x] = {y > x}
    for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) if (adj[i] >> j & 1) lt[i + 1] |= 1u << (j + 1);
    for (int k = 0; k < N; k++) for (int i = 0; i < N; i++) if (lt[i] >> k & 1) lt[i] |= lt[k];
    for (int i = 1; i < N - 1; i++) lt[i] |= 1u << top;
    lt[0] = ((1u << N) - 1) & ~1u;
    for (int i = 0; i < N; i++) { up_[i] = lt[i] | 1u << i; dn_[i] = 0; }
    for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) if (up_[j] >> i & 1) dn_[i] |= 1u << j;
    int lat = 1;
    for (int x = 0; x < N && lat; x++) for (int y = x; y < N && lat; y++) {
      unsigned U = up_[x] & up_[y], D = dn_[x] & dn_[y]; int j = -1, mt = -1;
      for (unsigned R = U; R; R &= R - 1) { int u = __builtin_ctz(R); if ((up_[u] & U) == U) { j = u; break; } }
      for (unsigned R = D; R; R &= R - 1) { int u = __builtin_ctz(R); if ((dn_[u] & D) == D) { mt = u; break; } }
      if (j < 0 || mt < 0) lat = 0; else { J[x][y] = J[y][x] = j; Mt[x][y] = Mt[y][x] = mt; }
    }
    if (!lat) continue;
    nlat++;
    doLattice();
  }
  fprintf(stderr, "posets %lld lattices %lld SD %lld SDjoin %lld SDmeet %lld maximal-sublattices %lld nonconvex %lld sd-noninterval %lld h2join-fail %lld h2meet-fail %lld SD-not-bounded %lld nb-maxsubs %lld CG %lld CG-maxsubs %lld H4-fail %lld Q2-fail %lld Q2-join-part-fail %lld Q2-meet-part-fail %lld\n",
          nposets, nlat, nsd, nsdj, nsdm, nmax, nviol, nsdnonint, nh2j, nh2m, nsdnb, nmaxnb, ncg, nmaxcg, nh4, nq2, nq2j, nq2m);
  return 0;
}
