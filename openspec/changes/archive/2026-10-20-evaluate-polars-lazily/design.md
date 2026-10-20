# Design

## Context

Stage 2 of `engine.calculate` loops over the metric DAG and calls `nw_df.with_columns(expr)` once per metric on the
frame it holds. For an eager Polars frame each call executes immediately. Measured on 120,000 rows and 98 columns:
eager 8.7 s, lazy 0.12 s for 30 metrics; lazy and eager results were equal.

## Goals / Non-Goals

**Goals:** make Polars evaluation cost proportional to the work the metrics do; keep types, values and column order.
**Non-Goals:** the DuckDB evaluation cost (ADR-0056), pandas or PyArrow speed, changing metric expressions.

## Decisions

1. **Switch eager Polars frames to lazy for stage 2 and collect at the end.** narwhals `DataFrame.lazy()` on a Polars
   frame returns a Polars-backed lazy frame without copying; `.collect()` returns an eager frame of the same
   implementation. The `_ContextProbe` and season checks run before and are unaffected. Alternative: build all
   expressions and call `with_columns` once with the list, not chosen now because later metrics read earlier metric
   columns, so one call would need dependency waves; revisit if lazy evaluation shows a plan-size problem.
2. **Only for Polars.** For pandas, `.lazy()` would convert to another backend; PyArrow and DuckDB have their own costs
   (ADR-0056). The check is on `nw_df.implementation`.
3. **Equality guard.** A saved reference of all 141 metrics from the previous implementation on a 4,800-row frame is
   compared before and after (done once during the change; the permanent guard is the backend matrix test plus the
   golden fixtures).

## Risks / Trade-offs

- [Lazy plans can reorder or fuse floating-point operations] -> measured: all 141 metrics on the reference frame were
  bit-for-bit identical; a grouped weighted-offense case differed by up to 1e-16 relative (last-bit rounding), so the spec
  states a 1e-12 tolerance instead of exact equality.
- [A very deep plan of 140 metrics could be slow to optimize] -> measured below one second for 141 metrics.
