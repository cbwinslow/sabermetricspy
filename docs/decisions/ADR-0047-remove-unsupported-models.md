# ADR-0047: Remove Models and Metrics With No Public Method

Status: Accepted

## Context
The library ships only methods that are publicly documented and reproduce outside reference values (CLAUDE.md rule 7).
Five pieces failed that test, and two failed outright on real data (recorded Skubal 2024 sample, 2,868 pitches):
- `PitchQualityModel` (open Stuff+/Location+/Pitching+): no vendor publishes the model or its training data; fitting it on
  the sample raised "exog contains inf or nans" because spin rate is null on some pitches.
- `ExpectedOutcomeModel` (open k-NN xBA/xSLG/xwOBA): Savant's model is unpublished; the class scores itself on its own
  training batted balls (478 of them), reporting a Brier score of 0.0000.
- `CatcherFramingModel` and `OutsAboveAverageModel`: generic logistic regressions, not Savant's framing or OAA models; only
  the run-value constants (0.125 per strike, 0.75 per out) were sourced.
- `xera`: Savant publishes no xERA formula, and the library's translation ran 0.06 runs low (2.62 against 2.68).

## Decision
Delete them, with their result types, audit entries, benchmark, tests and example sections. Remove `Metric.XERA`. Drop
`scikit-learn` and `statsmodels` from the core dependencies, since nothing else imports them. `xba`, `xslg` and `xwoba`
stay: they sum Savant's own per-pitch estimates and reproduce its pitch-arsenal values.

Alternatives considered: (a) move them to an `experimental` package, not chosen now because unvalidated results would stay
one import away and the code is in git history; revisit if a method with a public definition appears (for example a
published Stuff+ implementation); (b) fix the crash and the in-sample scoring and keep them, not chosen now because that
would not give them a public method to reproduce; (c) keep `xera` as a documented approximation, not chosen now because the
owner's rule is to remove rather than approximate. `WinProbabilityModel` and `CountExpectancyMatrix` are not part of this
decision; they have a possible published-table replacement and are handled separately.

## Consequences
Callers of the removed names get an import or attribute error (the package is at 0.1.0). Anyone needing these quantities
should read Savant's published fields and leaderboards. The OpenSpec change is `remove-unsupported-models`.
