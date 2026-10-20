# Tasks

## 1. Engine

- [x] 1.1 Convert DuckDB input to Polars at the start of `calculate` and return a relation at the end; document the trade-off in the docstring. Verify: `tests/test_backend_matrix.py` compares every registered metric on DuckDB with Polars and asserts a 10 s bound for 60 rows.
- [x] 1.2 Confirm `calculate_suite`, `calculate_available`, `calculate_rolling` and `benchmark` still work on DuckDB. Verify: the backend matrix suite tests plus `uv run pytest tests/test_benchmarks.py`.

## 2. Records

- [x] 2.1 Mark ADR-0056 Accepted and record the measured result, update README and changelog, remove the DuckDB metric limit from the backend test. Verify: `openspec validate --all`, full test suite, ruff, pyright.
