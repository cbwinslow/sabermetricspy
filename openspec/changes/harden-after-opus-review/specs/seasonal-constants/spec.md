# Spec Delta

## ADDED Requirements

### Requirement: Season detection is backend-independent
Reading the season from a frame SHALL work for Polars, pandas, PyArrow and DuckDB inputs, eager or lazy, and SHALL NOT
fail a calculation of metrics that read no season constants. A `season` column that does not hold years (text that is
not an integer, dates, or all nulls) SHALL be treated as absent for inference, and a calculation of a metric that reads
season constants SHALL then follow the no-season rule and warn accurately.

#### Scenario: DuckDB relation with a season column
- **WHEN** a DuckDB relation holding season 2001 is calculated for AVG, or for wRC+ with no context
- **THEN** the calculation succeeds and wRC+ uses 2001 constants

#### Scenario: Season column that is not a year
- **WHEN** the season column holds text such as "2016-reg" and AVG is calculated
- **THEN** the calculation succeeds without a warning

#### Scenario: Season column that is all null
- **WHEN** wRC+ is calculated on a frame whose season column is entirely null, with no season or context
- **THEN** the warning says the data holds no usable season value

### Requirement: Stateful valuation does not default silently
Valuation objects that take a season (`WARFramework`) SHALL warn when constructed with neither a context nor a season,
naming the default season they will use.

#### Scenario: WAR framework with no season
- **WHEN** a WAR framework is constructed with no context and no season
- **THEN** a `UserWarning` names the default season; passing a season or a context emits none
