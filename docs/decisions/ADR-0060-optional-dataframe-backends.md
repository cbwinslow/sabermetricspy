# ADR-0060: Only Polars Is Required; pandas, PyArrow and DuckDB Are Optional Extras

Status: Accepted (records commit 46cd50f, GitHub issue 10)

## Context
Callers bring frames from different libraries. The engine runs on Polars through narwhals, and `rich` was installed but unused.

## Decision
Core dependencies are narwhals, pydantic, pyyaml, numpy, scipy and polars. `pandas`, `pyarrow` and `duckdb` are extras (`pip install sabermetricspy[pandas]`); the dev dependency group installs all of them so every backend is tested (ADR-0056, the backend matrix test). `rich` was removed.

## Alternatives
- Require every backend, not chosen now because most users need one and the install is much larger; revisit if optional-import errors become a common support issue.
- Make Polars optional too, not chosen now because the engine, ids and models use it internally; revisit if a second evaluation backend is added.

## Consequences
A missing backend fails on first use of that backend, naming the extra to install.
