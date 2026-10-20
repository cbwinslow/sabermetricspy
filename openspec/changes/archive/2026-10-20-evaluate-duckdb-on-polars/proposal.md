# Proposal

## Why

ADR-0056 (accepted 2026-10-20): the engine's stacked column expressions make DuckDB's execution time grow faster than the
number of metrics (30 metrics: 6.2 s on 60 rows and 11.6 s on 120,000 rows; all 141 metrics: minutes), while Polars takes
0.05 s and 0.32 s after ADR-0057. Results are correct, only slow. The rolling calculation and the expectancy models
already convert DuckDB input to Polars; the engine is the outlier.

## What Changes

- `calculate` reads a DuckDB relation into Arrow once, evaluates on Polars, and returns a DuckDB relation built from the
  result (same family as the input, as the spec requires).
- The DuckDB case of `tests/test_backend_matrix.py` runs every metric instead of the first 25.
- Documentation states the trade-off: DuckDB input is read into memory, the result lives on DuckDB's default connection.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `sabermetrics-engine`: the interoperability requirement no longer says metrics execute natively on DuckDB; adds the
  read-once requirement.

## Impact

`engine.calculate` only (rolling and models already convert). `benchmark()` already materializes with `.pl()`, which still
works on a relation. README, ADR-0056 (accepted by this change).
