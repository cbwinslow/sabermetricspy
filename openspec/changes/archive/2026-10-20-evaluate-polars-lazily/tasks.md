# Tasks

## 1. Engine

- [x] 1.1 Evaluate stage 2 lazily for Polars frames and collect once; leave other backends unchanged. Verify: the saved 141-metric reference from the previous engine equals the new output exactly, and a grouped (`by=`) case equals its reference.
- [x] 1.2 Add a test that calculates 30 metrics on a 120,000-row, 98-column frame and asserts a generous time bound plus equality with a per-metric immediate evaluation. Verify: `uv run pytest tests/test_engine_speed.py`.

## 2. Records

- [x] 2.1 Register a benchmark for the wide-frame case, record measured numbers in ADR-0057, correct the row-count statement in ADR-0056 with new measurements, update the changelog. Verify: `openspec validate --all`, full test suite, ruff, pyright.
