## Why

Classic sabermetric literature contains several widely cited, closed-form offensive metrics that provide direct, orthogonal signals for player evaluation and machine learning models (e.g. pure non-hit plate discipline, multiplicative on-base x slugging run interaction, and linear run estimation). This change adds Isolated Discipline (`isod`), Batter's Run Average (`bra`), and Estimated Runs Produced (`erp`), each backed by verified literature citations and outside validation tie-outs.

## What Changes

- Add `Metric.ISOD` (`"isod"`, "IsoD"): Isolated Discipline, defined as `OBP - AVG`, measuring non-hit on-base ability.
- Add `Metric.BRA` (`"bra"`, "BRA"): Batter's Run Average (Cramer & Palmer 1974), the multiplicative interaction `OBP * SLG`.
- Add `Metric.ERP` (`"erp"`, "ERP"): Estimated Runs Produced (Johnson 1985; Tango; Furtado), linear weights run estimation.
- Add golden fixtures, unit tests, property identity tests (`isod == obp - avg`, `bra == obp * slg`), multi-backend tests, methodology entries, and ADR-0078.

## Capabilities

### New Capabilities
- `isolated-discipline`: Isolated Discipline (`OBP - AVG`) batting metric.
- `batters-run-average`: Cramer and Palmer's Batter's Run Average (`OBP * SLG`).
- `estimated-runs-produced`: Paul Johnson's Estimated Runs Produced linear estimator.

### Modified Capabilities
<!-- none -->

## Impact

- `src/sabermetricspy/types/enums.py`: Add `ISOD`, `BRA`, `ERP` enum values.
- `src/sabermetricspy/metrics/batting.py`: Implement `calc_isod`.
- `src/sabermetricspy/metrics/weighted.py`: Implement `calc_bra` and `calc_erp`.
- `src/sabermetricspy/data/methodology.yaml`: Add methodology metadata.
- `docs/METHODOLOGY.md`, `docs/DECISIONS.md`, `CHANGELOG.md`, `docs/decisions/ADR-0078-closed-form-offensive-metrics.md`.
- `tests/golden/closed_form_batting.yaml`, `tests/test_golden_closed_form_batting.py`.
