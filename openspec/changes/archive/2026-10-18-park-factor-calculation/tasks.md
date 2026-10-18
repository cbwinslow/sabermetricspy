## 1. Calculation

- [x] 1.1 Write failing tests from the FanGraphs article examples (raw 1.10 / composite 1.05; regression 1.25 to 1.15, 1.175, 1.20, 1.225) and add `value/park.py` with `raw_park_factor`, `composite_park_factor`, `regress_park_factor`, decorated with `@profiled`. Verify the tests pass.

## 2. Bundled table

- [x] 2.1 Record the Guts! 2024 rows as `tests/golden/park_factors_2024.yaml`, regenerate `park_factors.yaml` from it with provenance, and test equality plus the unknown-park warning. Verify the tests pass.

## 3. Record

- [x] 3.1 Add ADR-0029 and the DECISIONS row; run `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, `uv run pytest`, `openspec validate --all`. Verify all are clean.
