# ADR-0039: Forecast-Evaluation Utilities

Status: Accepted

## Context
The original design conversation asked for RMSE, MAE, calibration and Brier scoring to be built in from the start. The
audit in `docs/ADR_AUDIT.md` found Brier only inside `ExpectedOutcomeModel` and `PitchQualityModel`, with no general
function a caller could use to check a projection or win-probability model.

## Decision
New package `sabermetricspy.evaluation` with `mse`, `rmse`, `mae`, `bias`, `brier_score`, `brier_skill_score`,
`log_loss` and `calibration_table`. Each takes a dataframe of any narwhals backend plus column names and an optional
weight column. The Brier score is the binary form of Brier (1950); the calibration table reports the Murphy (1973)
decomposition and returns the within-bin remainder instead of forcing the identity, because the decomposition is exact
only when forecasts are constant within a bin. Log loss clips probabilities at 1e-15.

Alternatives considered: (a) leave scoring to scikit-learn, rejected because it adds a heavy dependency for six
one-line reductions and does not take weights the same way across functions; (b) a single `evaluate()` returning
everything, rejected because callers usually want one score and the individual functions compose with `group_by`.

## Consequences
Values are pinned by hand-computed tests (`tests/test_evaluation.py`). The two models' internal Brier calculations are
unchanged. Elo and Bradley-Terry rating systems remain unimplemented.
