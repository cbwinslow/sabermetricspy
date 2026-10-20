# ADR-0056: DuckDB Input Is Evaluated on Polars

Status: Accepted (2026-10-20; implemented by OpenSpec change `evaluate-duckdb-on-polars`)

## Context
A backend sweep (ADR-0055 follow-up) ran every registered metric on Polars, LazyFrame, pandas, PyArrow and DuckDB. All 137
runnable metrics gave identical results on all five (Shutdown and Meltdown refuse `by=` on purpose, ADR-0043). It also
found that DuckDB takes far longer to execute the engine's result as the metric count grows. With 60 rows and 98 input
columns, materializing the result took: 10 metrics 0.75 s, 20 metrics 2.6 s, 30 metrics 7.0 s, 40 metrics 14.0 s;
`calculate_available` with 141 metrics took more than two minutes, against 0.3 s on Polars and 2.3 s on pandas. The engine
adds metrics one at a time with `with_columns`; DuckDB expands each earlier expression inside the later columns that use
it, so the work grows faster than the number of metrics. Measured with 30 metrics: 6.2 s on 60 rows and 11.6 s on 120,000 rows (Polars: 0.05 s and 0.32 s
after ADR-0057), so the cost is mostly a fixed price per metric that rows add to. The first version of this finding came
from a prototype that is not in the code: materializing the DuckDB frame every 8 metrics cut 40 metrics from 14.9 s to
5.4 s but 141 metrics still took 34 s to build.

## Decision
For DuckDB input, evaluate the metric DAG on a Polars frame converted from Arrow and return a DuckDB relation built from
the result, as the rolling calculation and the expectancy models already do (`to_polars_df`). On the 60-row frame that
makes 141 metrics take about 0.5 s (measured: Arrow in, Polars engine, relation out, materialized). This gives up DuckDB's ability to stream a table larger than memory through the
engine; callers with such tables should aggregate in DuckDB first and pass the aggregate.

Measured after the change (60 rows, 98 columns, all 141 metrics): 0.3 s to build and 0.2 s to materialize on DuckDB, the same as
Polars (0.3 s); before, the same call took minutes. `tests/test_backend_matrix.py` runs every metric on DuckDB with a 10 s bound.
The result relation is created on DuckDB's default connection, because a relation does not expose its own.

Alternatives considered: (a) keep evaluating inside DuckDB and flatten every N metrics, not chosen now because the
prototype still took 34 s for 141 metrics; revisit if DuckDB's optimizer stops inlining projections. (b) Build all metrics
as one `SELECT` with common subexpressions factored out, not chosen now because narwhals does not expose that and
replacing it is a large change; revisit if narwhals adds common-subexpression support for DuckDB. (c) Leave as is and
document, not chosen now because a user asking for the full suite on DuckDB waits minutes; revisit if no DuckDB user
asks for more than a few dozen metrics.

## Consequences
DuckDB calls return in about the time Polars takes for any metric count,. The cost is that a DuckDB table is pulled into memory as Arrow for the calculation.
