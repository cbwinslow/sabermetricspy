## Why

Entry 1 of `docs/LITERATURE.md`: Base-Advance Average (Hardegree, 2005) is fully specified, needs only play-by-play base states already in the canonical schema, and the paper prints a worked half-inning whose totals reconcile (14 bases over 57 opportunities).

## What Changes

- Add `add_base_advance_columns` that derives bases advanced and base-advance opportunities per plate appearance from base states and runs.
- Add the `base_advance_average` metric: total bases advanced over total opportunities.
- Add the paper's sample inning as a golden fixture, a methodology entry and ADR-0031.

## Capabilities

### New Capabilities
- `base-advance-average`: Base-Advance Average from play-by-play base states.

### Modified Capabilities
<!-- none -->

## Impact

- `expectancy/` (helper), `metrics/` (metric), `types/enums.py`, `data/methodology.yaml`, tests, ADR-0031.
