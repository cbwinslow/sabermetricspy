# Design

## Context

ADR-0056 has the measurements and the options. A DuckDB relation does not expose its connection (checked with duckdb
1.5.6: no connection attribute), so a result relation can only be created on the default connection with
`duckdb.from_arrow`.

## Goals / Non-Goals

**Goals:** DuckDB calls cost about what Polars calls cost for any metric count; return type stays a relation.
**Non-Goals:** streaming tables larger than memory through the engine; keeping the result on the caller's own connection.

## Decisions

1. **Convert right after `nw.from_native(df)`** when the implementation is DuckDB: `pl.from_arrow(relation.to_arrow_table())`,
   then wrap with narwhals and continue on the existing Polars path (which ADR-0057 made one lazy plan). At the end the
   Polars result becomes `duckdb.from_arrow(result.to_arrow())`. Preset translation and column normalization then also
   run on Polars, which is faster and already tested.
2. **No new dependency:** duckdb and pyarrow are already imported where DuckDB input is handled.
3. **Alternatives** are in ADR-0056 (flatten every N metrics: still 34 s for 141 metrics; one SELECT with shared
   subexpressions: not available in narwhals).

## Risks / Trade-offs

- [Large DuckDB tables are pulled into memory] -> documented; the caller aggregates first.
- [The result relation is on the default connection, so it cannot be joined with tables on a caller-created connection
  without registering it there] -> documented; `result.to_polars()` or `.df.to_arrow_table()` give data to register.
