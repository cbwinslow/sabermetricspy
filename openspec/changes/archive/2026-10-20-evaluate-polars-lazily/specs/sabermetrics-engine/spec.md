# Spec Delta

## ADDED Requirements

### Requirement: Polars evaluation builds one query plan
For a Polars input, the engine SHALL add all requested metric columns to a single deferred query and execute it once, so
the cost of adding a metric does not include a copy or full pass over the existing columns. The returned frame SHALL have
the same type, columns and column order as evaluating each metric immediately, and values equal to it within floating-point
rounding (relative difference below 1e-12).

#### Scenario: Many metrics on a wide frame
- **WHEN** 30 metrics are calculated on an eager Polars frame of 120,000 rows and 98 columns
- **THEN** the call finishes in under one second on a typical developer machine and returns an eager Polars frame

#### Scenario: Results unchanged
- **WHEN** every registered metric is calculated on the same frame before and after this behavior
- **THEN** every column is equal within a relative difference of 1e-12, and nulls and NaN are in the same positions

#### Scenario: Lazy input
- **WHEN** a Polars LazyFrame is calculated
- **THEN** the result is a LazyFrame and nothing is executed until the caller collects it
