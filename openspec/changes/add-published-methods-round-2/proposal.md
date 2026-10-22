## Why

The research round of 2026-10-22 (evidence library `sabermetricspy_research`, dossiers and specs for each method) found published methods whose formulas were read in a primary source and whose printed values reproduce. This change adds the ones that pass `CLAUDE.md` rule 7 and records the evidence level of each.

## What Changes

- Add `power_speed_number`, `xr` and `xrr` metrics (ADR-0070, ADR-0071).
- Add a `closed` option, default right-closed, to `calibration_table`; add `expected_calibration_error`, `maximum_calibration_error`, `ranked_probability_score` and `diebold_mariano_test` to `evaluation` (ADR-0072, ADR-0073, ADR-0075, ADR-0076).
- Add `JamesSteinShrinker` (ADR-0074) and the scalar Glicko-2 update (ADR-0077).
- Add methodology entries, golden fixtures and tests for each; correct the `EmpiricalBayesShrinker` citation.
- Not added: XRB, the Harvey-Leybourne-Newbold correction, Brown (2008) shrinkage, calibration slope and Hosmer-Lemeshow, Shin de-vig, Bradley-Terry (evidence or papers missing; see the research notes).

## Capabilities

### New Capabilities
- `power-speed-number`: harmonic mean of home runs and stolen bases.
- `extrapolated-runs`: Furtado's XR and XRR run estimators.
- `calibration-bin-convention`: right-closed default bins for `calibration_table`.
- `calibration-error`: expected and maximum calibration error.
- `ranked-probability-score`: score for ordered-category forecasts.
- `diebold-mariano-test`: test of equal forecast accuracy.
- `arcsine-james-stein`: Efron-Morris shrinkage of equal-trial hit rates.
- `glicko2-rating`: Glicko-2 rating update for one period.

### Modified Capabilities
<!-- none -->

## Impact

- `types/enums.py`, `metrics/specialized.py`, `metrics/weighted.py`, `evaluation/__init__.py`, `uncertainty/__init__.py`, `models/glicko2.py`, `telemetry/__init__.py`, `data/methodology.yaml`, `docs/METHODOLOGY.md`, `docs/DECISIONS.md`, ADR-0070 to ADR-0077, `CHANGELOG.md`, new golden fixtures and tests.
