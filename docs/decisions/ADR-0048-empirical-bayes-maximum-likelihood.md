# ADR-0048: Empirical Bayes Prior Is Fit by Maximum Likelihood

Status: Accepted

## Context
`EmpiricalBayesShrinker` estimated the Beta prior by method of moments, then forced the prior strength into the range
25 to 2000 and floored the true variance at 1e-5. On simulated data with a known prior, a true strength of 10 came back as
25 and a true strength of 3000 as 2000. The clamps were arbitrary numbers with no source.

## Decision
When `stabilization_trials` is not given, the prior mean and strength are the beta-binomial maximum-likelihood estimates
(scipy `betabinom.logpmf`, minimised over log alpha and log beta). There are no clamps. A caller-supplied
`stabilization_trials` still fixes the strength. The posterior formula is unchanged.

Alternatives considered: (a) keep method of moments with the clamps, not chosen now because the clamps bias the answer at
both ends; revisit if a fit ever needs to be guaranteed fast on millions of rows; (b) a hierarchical-model library such as
PyMC, not chosen now because two parameters do not need one; revisit if we model covariates such as age or park.

## Consequences
Fitted priors change slightly for existing data. Very strong priors (strength in the thousands) are weakly identified by
the data, so their estimates are noisy; this is a property of the data, not a clamp. Tests: `tests/test_empirical_bayes_fit.py`.
