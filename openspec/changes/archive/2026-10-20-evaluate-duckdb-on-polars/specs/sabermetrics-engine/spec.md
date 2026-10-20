# Spec Delta

## MODIFIED Requirements

### Requirement: Multi-Backend Dataframe Interoperability
All metric calculations SHALL accept Polars `DataFrame`/`LazyFrame`, pandas `DataFrame`, PyArrow `Table`, and DuckDB relations, returning a frozen `CalculationResult` whose `.df` matches the input dataframe family. Polars, pandas and PyArrow inputs are evaluated through `narwhals` on their own backend; a DuckDB relation is converted to Arrow, evaluated on Polars, and returned as a DuckDB relation on DuckDB's default connection, so that the time for many metrics does not grow faster than their number.

#### Scenario: Polars, pandas, and PyArrow round-trip calculation
- **WHEN** `calculate()` is invoked with a Polars `DataFrame`, pandas `DataFrame`, or PyArrow `Table`
- **THEN** `result.df` is returned in the matching backend type with identical numerical values within floating-point tolerance (`1e-9`)

#### Scenario: DuckDB relation
- **WHEN** `calculate()` is invoked with a DuckDB relation
- **THEN** `result.df` is a DuckDB relation holding the input columns and the metric columns, with values equal to the Polars result within `1e-9`

#### Scenario: Many metrics on DuckDB
- **WHEN** every registered metric is calculated on a DuckDB relation of 60 rows
- **THEN** the call and its materialization finish in under 10 seconds

## ADDED Requirements

### Requirement: DuckDB input is read once
For a DuckDB relation the engine SHALL read the relation into memory once as Arrow. A table larger than memory SHALL be aggregated in DuckDB by the caller before it is passed, and the documentation SHALL say so.

#### Scenario: Documented limit
- **WHEN** the README and the `calculate` docstring are read
- **THEN** both state that DuckDB input is read into memory as Arrow and the result is returned on DuckDB's default connection
