## Why

The original design conversation (Perplexity blueprint, forecasting section) asked for forecast-evaluation scoring (RMSE, MAE, calibration, Brier score) to be built in from the start so projections and win-probability models can be checked against outcomes. `docs/ADR_AUDIT.md` (Vision alignment) found that Brier appears only inside two models and nothing general exists.

## What Changes

- Add a `sabermetricspy.evaluation` package with provider-agnostic scoring functions over a dataframe and column names: `mse`, `rmse`, `mae`, `bias`, `brier_score`, `log_loss`, `brier_skill_score`, and `calibration_table` with the Murphy (1973) Brier decomposition.
- Optional weight column (projection evaluations weight by playing time).
- Add ADR-0039 and a `docs/DECISIONS.md` row.

## Capabilities

### New Capabilities
- `forecast-evaluation`: scoring of point and probability forecasts against outcomes.

### Modified Capabilities
<!-- none -->

## Impact

- New `src/sabermetricspy/evaluation/`, top-level exports, `tests/test_evaluation.py`, ADR-0039.
- No change to existing metrics or models.
