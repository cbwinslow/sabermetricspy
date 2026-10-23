# ADR-0078: Closed-Form Offensive Metrics: Isolated Discipline, Batter's Run Average, and Estimated Runs Produced

- **Status**: Accepted
- **Date**: 2026-10-23
- **OpenSpec change**: `add-closed-form-offensive-metrics`

## Context
Standard sabermetric literature contains several widely referenced, closed-form offensive metrics that add clear diagnostic and predictive value for player evaluation and machine learning models:
1. **Isolated Discipline (`isod`)**: Non-hit plate discipline rate ($\text{OBP} - \text{AVG}$), separating walks/HBP from batting average fluctuations.
2. **Batter's Run Average (`bra`)**: Multiplicative on-base and slugging interaction ($\text{OBP} \times \text{SLG}$) formulated by Dick Cramer and Pete Palmer in the 1974 Baseball Research Journal.
3. **Estimated Runs Produced (`erp`)**: Linear weights run estimator developed by Paul Johnson (1985 Bill James Baseball Abstract) and documented by Furtado (1999) and the Tango Tiger wiki.

## Decision
- Add `Metric.ISOD` (`"isod"`, "IsoD") to category `batting`. Evaluates $\text{OBP} - \text{AVG}$, requiring `h`, `ab`, `bb` and evaluated safely with `safe_div`. Zero denominators return `null`.
- Add `Metric.BRA` (`"bra"`, "BRA") to category `weighted_offense`. Evaluates $\text{OBP} \times \text{SLG}$, returning `null` when either component is `null`.
- Add `Metric.ERP` (`"erp"`, "ERP") to category `weighted_offense`. Evaluates $(2(\text{TB} + \text{BB} + \text{HBP}) + \text{H} + \text{SB} - 0.605(\text{AB} + \text{CS} + \text{GIDP} - \text{H})) \times 0.16$, defaulting absent optional columns (`cs`, `gidp`, `hbp`, `sb`) to 0. Algebraically identical to Furtado's linear expansion ($0.48 \times 1\text{B} + 0.80 \times 2\text{B} + 1.12 \times 3\text{B} + 1.44 \times \text{HR} + 0.32(\text{BB}+\text{HBP}) + 0.16 \times \text{SB} - 0.0968 \times \text{outs}$).
- All three metrics are pure vectorized `narwhals` expressions tested against golden fixtures (`tests/golden/closed_form_batting.yaml`), property-based tests in `tests/test_golden_closed_form_batting.py`, and verified across Polars, DuckDB, PyArrow, and pandas backends.

## Consequences
- Three new canonical metrics in `Metric` enum and registry.
- `methodology.yaml` and `docs/METHODOLOGY.md` updated.
- Zero network I/O; clean compatibility across all backends.
