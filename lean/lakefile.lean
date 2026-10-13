import Lake
open Lake DSL

package MaxSub where
  leanOptions := #[⟨`autoImplicit, false⟩]

require mathlib from git "https://github.com/leanprover-community/mathlib4" @ "v4.34.1"

/-- the two counterexamples: Hypothesis 3 and Question 2 of Adaricheva, Mata, Silberger and
Zamojska-Dzienio -/
@[default_target]
lean_lib MaxSub
