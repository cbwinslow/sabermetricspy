# ADR-0057: Polars Evaluation Builds One Query Plan

Status: Accepted

## Context
The backend sweep found that `calculate` on an eager Polars frame was about 70 times slower than the same call on a lazy
frame, with the same results. The engine added each metric with its own eager `with_columns`, and each call cost a pass
over every column. Measured on 120,000 rows and 98 columns, 30 metrics: 8.7 s eager, 0.12 s lazy; with only the 14 needed
columns, 2.4 s eager. The library promises speed on millions of rows and most callers pass eager Polars frames.

## Decision
For a Polars eager input the engine converts to a lazy frame for stage 2, adds all metric columns, and collects once.
Output type, columns and order are unchanged; other backends are unchanged. Measured after the change: 30 metrics on
120,000 x 98: 0.44 s eager input (0.09 s lazy input); 30 metrics on the 14-column frame: 0.09 s. All 141 metrics on a
4,800-row reference frame were identical to the previous implementation bit for bit; a grouped weighted-offense case
differed by at most 1e-16 relative (last-bit rounding from the optimized plan), so the specification states a 1e-12
tolerance. `tests/test_engine_speed.py` guards the speed (3 s bound) and compares the all-at-once result with one metric at
a time.

Alternatives considered: (a) build all expressions and call one `with_columns`, not chosen now because later metrics read
earlier metric columns and would need dependency waves; revisit if lazy plans show an optimization-time problem at
thousands of metrics. (b) Document the slowness and tell callers to pass lazy frames, not chosen now because most callers
pass eager frames and would not know; revisit never for the default path. (c) Also defer pandas and PyArrow, not chosen now
because narwhals would convert them to another backend and the cost there was not shown to matter; revisit if a benchmark
on those backends shows the same per-metric pass.

## Consequences
Eager Polars calls are 20 times faster for 30 metrics on a wide frame and the gap grows with the number of columns. DuckDB
evaluation remains slow for many metrics (ADR-0056, proposed).
