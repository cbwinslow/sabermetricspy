# ADR-0074: Arcsine James-Stein Shrinker (Efron and Morris 1975)

Status: Accepted (adopted by default from the research specs; owner to confirm the defaults listed below)

## Context
`EmpiricalBayesShrinker` is a Beta-binomial estimator. Its docstring cited Efron and Morris (1975) and its methodology note said that paper "was not retrievable". The paper is in the research library and its method is different: a normal-theory James-Stein rule applied after an arcsine variance-stabilising transform, on 18 players with 45 at bats each. A Beta prior fitted to the printed estimates still misses them by up to 0.00103, so the existing class cannot reproduce the paper.

## Decision
Add `JamesSteinShrinker` (and frozen `JamesSteinResults`) to `sabermetricspy.uncertainty`: `x = sqrt(n) * arcsin(2y - 1)`, `delta_i = xbar + (1 - (k - 3)/V)(x_i - xbar)`, back-transformed with `(sin(delta/sqrt(n)) + 1)/2`. All players must have the same trials. `fit` raises `ValueError` for fewer than 4 players, unequal or non-positive trials, successes outside `[0, n]`, nulls, zero dispersion, and `V <= k - 3` (no source defines a positive-part rule). It reproduces all 18 printed estimates, the constants .791 and .209 and the errors 17.56 and 5.01 (`tests/golden/efron_morris_james_stein.yaml`). The paper's printed Xbar (-3.275) contradicts its own Table 1 (-3.317) and is not used. The `EmpiricalBayesShrinker` docstring and methodology note are corrected. Methodology status `matches`, evidence `golden`; one benchmark `uncertainty.james_stein`.

Defaults adopted without an owner answer (research spec `efron_morris_james_stein`, O-EM-1 to O-EM-4): class in `uncertainty/`, equal trials enforced, raise when `V <= k - 3`, corrected docstring and note.

## Alternatives
- Clip the factor at 0 (positive-part rule), not chosen now because the paper prints none and a clipped result silently shrinks everything to the mean; revisit if a source defines one (Brown 2008 uses a positive part, but for a heteroscedastic variant whose printed tables do not all reproduce).
- Extend `EmpiricalBayesShrinker` with an arcsine mode, not chosen now because the two estimators have different inputs and assumptions (equal versus unequal trials) and mixing them would blur a documented tie-out; revisit if a unified shrinkage interface is wanted.
- Support unequal trials with Brown (2008) heteroscedastic formulas, not chosen now because only 35 of 59 printed cells reproduce (research dossier `brown_2008_batting_shrinkage`); revisit when the mismatches are explained.

## Consequences
New public classes `JamesSteinShrinker` and `JamesSteinResults`; one benchmark; docstring and methodology corrections for `EmpiricalBayesShrinker`; `docs/METHODOLOGY.md` regenerated.
