# Maximal sublattices of convex geometries: four counterexamples

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23343145.svg)](https://doi.org/10.5281/zenodo.23343145)

Release v1.0.0: [doi:10.5281/zenodo.23343145](https://doi.org/10.5281/zenodo.23343145) (all versions: [doi:10.5281/zenodo.23343144](https://doi.org/10.5281/zenodo.23343144)).

Adaricheva, Mata, Silberger and Zamojska-Dzienio, *Conjecture on maximal sublattices of finite
semidistributive lattices and beyond*, Discrete Math. Theor. Comput. Sci. 28:2 (2026),
[doi:10.46298/dmtcs.16374](https://doi.org/10.46298/dmtcs.16374)
([arXiv:2507.22682](https://arxiv.org/abs/2507.22682)), put forward four hypotheses and a question
about the complement C = L \ M of a maximal sublattice M of a finite lattice L, and proved them for
convex geometries of convex dimension two. This repository settles all of them except the first.

| Statement | Status | Example |
|---|---|---|
| Hypothesis 1: L semidistributive ⇒ C is an interval (the 1997 question of Adams, Freese, Nation and Schmid) | **open**; true up to 14 elements | — |
| Hypothesis 2: L a convex geometry, or join semidistributive ⇒ C is a union of intervals with a common least element | **false**, already in convex dimension three | 𝒢₁₇ (5 points, convex dimension 4), 𝒢₂₅ (6 points, convex dimension 3) |
| Hypothesis 3: in every finite lattice C is order convex | **false** | the 10-element lattice L₁₀ |
| Hypothesis 4: L a convex geometry ⇒ every x ∈ C covers some m ∈ M with [0, m] ⊆ M | **false** | 𝒢₁₇, 𝒢₂₅ |
| Question 2, join half: the only join-irreducible in C is its minimum | **no** | 𝒢₁₇, 𝒢₂₅ |
| Question 2, meet half: the only meet-irreducibles in C are its maxima | **no** | 𝒢₁₁ (4 points) |

𝒢₁₇ is the convex geometry on {a, b, c, d, e} with the closed sets
∅, a, b, c, d, e, ac, ad, bd, ae, de, abd, acd, ade, abde, acde, abcde; the maximal sublattice
M = {∅, b, c} ∪ {A : e ∈ A} has complement {a, d, ac, ad, bd, abd, acd}, with the two minimal
elements a and d. 𝒢₂₅ is the convex geometry on {a, …, f} realized by the orders
a<b<c<d<e<f, f<c<e<b<d<a and d<e<b<c<a<f; the complement of M = {∅, a, f} ∪ {A : d ∈ A} has the three
minimal elements b, c, e. So the theorem for convex dimension two does not extend.

## What is proved, and how

Every example is proved by hand in the paper and formally in Lean 4 with Mathlib (v4.34.1). The
formal statements are the negations of the hypotheses, quantified over all finite lattices, with
convex geometries described, as in the paper of Adaricheva et al., as the finite lattices that are
join semidistributive and lower semimodular.

| Statement | Lean theorem |
|---|---|
| Hypothesis 2 fails | `MaxSub.not_hypothesis2` |
| Hypothesis 2 fails in convex dimension three (three orders realize 𝒢₂₅ and no one or two orders do; M maximal; C without least element; `bc` without lower cover in M) | `MaxSub.hypothesis2_fails_in_convex_dimension_three` |
| Hypothesis 3 fails | `MaxSub.not_hypothesis3`, `MaxSub.exists_coatom_not_ordConnected` |
| Hypothesis 4 fails | `MaxSub.not_hypothesis4` |
| Question 2, join half | `MaxSub.not_question2_join` |
| Question 2, meet half | `MaxSub.not_question2` |

All proofs are checked by the kernel (`decide +kernel` and explicit derivations, no
`native_decide`); `lean/Check.lean` prints the axioms of twenty theorems, and
`scripts/audit_axioms.py` checks that only `propext`, `Classical.choice` and `Quot.sound` occur.
`lean/MaxSub/*.lean` is generated from the cover relations by `scripts/gen_lean.py`.

Independent checks outside Lean (`scripts/run_all.sh`):

- `verification/c/maxsub.c`: all lattices with at most 12 elements (from `nauty-genposetg`), every
  maximal sublattice, Hypotheses 1–4 and Question 2; the counts are compared with
  `data/counts_upto12_all.txt` (the lattice counts are OEIS A006966). The runs for 13 and 14
  elements (join- or meet-semidistributive lattices; 1,104,891,746 posets for 14) are in
  `data/counts_13_14_sd.txt`.
- `verification/python/check_examples.py`: the four examples from their closed sets, with the
  standard library only.
- `verification/python/check_minimal.py`: a second program, sharing no code with the C one, for
  order convexity (lattices up to 10 elements) and Question 2 (convex geometries up to 11 elements).
- `verification/python/convex_geometries.py`: all convex geometries on at most five points
  (59,386 labelled, 672 unlabelled on five); exactly six violate Hypothesis 2, all of convex
  dimension four, the smallest being 𝒢₁₇.
- `verification/python/dimension_three.py`: all convex geometries on six points of convex dimension
  at most three with at most 25 closed sets (8,435 up to isomorphism); 𝒢₂₅ is the only one that
  violates Hypothesis 2.

## Layout

```
lean/                 Lean 4 + Mathlib (v4.34.1)
  MaxSub/H2.lean      𝒢₁₇: Hypotheses 2 and 4, Question 2 (join half)
  MaxSub/CD3.lean     𝒢₂₅: Hypothesis 2 in convex dimension three, with the convex dimension
  MaxSub/Q2.lean      𝒢₁₁: Question 2 (meet half)
  MaxSub/H3.lean      L₁₀: Hypothesis 3
  Check.lean          axiom audit
verification/         C and Python checks; axioms.txt is the output of Check.lean
data/                 outputs of the exhaustive C runs
preprint/             the paper (amsart) and its TikZ figures
dist/                 PDF, LaTeX source with PNG figures, arXiv tarball
scripts/              gen_lean.py, run_all.sh, build_paper.sh, audit_axioms.py
PRIORITY-CHECK.md     dated check that the hypotheses had not been settled
```

## Reproduce

```
cd lean && lake exe cache get && lake build && lake env lean Check.lean   # Lean, a few minutes
scripts/run_all.sh                                                        # C and Python checks
scripts/build_paper.sh                                                    # the paper into dist/
```

`run_all.sh` needs a C compiler, nauty and Python 3 with `python-sat`.

## Paper

D. Bhattacharjee, *Maximal sublattices of convex geometries: four counterexamples*, 2026
(`dist/maximal-sublattices-cg.pdf`).

## Author

Deep Bhattacharjee, formerly Electro-Gravitational Space Propulsion Laboratory (EGSPL),
Bhubaneswar, Odisha 751030, India. d.bhattacharjee@erl-forschung.de (corresponding),
itsdeep@live.com. ORCID [0000-0003-0466-750X](https://orcid.org/0000-0003-0466-750X).

MIT License.
