# Specification: Sabermetrics Core Engine, Registry, Metrics, and Estimators

## ADDED Requirements

### Requirement: Three-Tier Sabermetric Naming and Enum Vocabulary
The library SHALL expose `StrEnum` classes (`Stat`, `Metric`, `MetricSuite`, `Category`, `ImplKind`, `Direction`, `Handedness`, `PitchOutcome`, `PlayOutcome`, `BattedBallType`, `BaseState`) where enum member names use `UPPER_SNAKE_CASE`, enum string values use canonical `lower_snake_case`, and `MetricSpec.display_name` preserves official baseball typography (`"wOBA"`, `"wRC+"`, `"xFIP"`, `"CSW%"`, `"K-BB%"`).

#### Scenario: Resolving metrics by StrEnum or string
- **WHEN** a caller passes `Metric.WRC_PLUS` or `"wrc_plus"` or `"wRC+"` to the registry or `calculate()`
- **THEN** the registry resolves the exact `MetricSpec` for `Metric.WRC_PLUS` with `name="wrc_plus"` and `display_name="wRC+"`

### Requirement: Two-Stage Additive Calculation and DAG Dependency Resolution
The calculation engine SHALL aggregate additive counting columns across any requested `by` grouping before evaluating ratio or weighted formulas, and SHALL automatically resolve dependent metrics in topological order without duplicate computation.

#### Scenario: Computing ratio metrics across multi-game rows
- **WHEN** a player has two games (`3-for-4` and `1-for-5`) and `calculate(df, [Metric.AVG, Metric.OPS], by=["player_id"])` is called
- **THEN** the engine sums `h=4` and `ab=9` first to produce `avg = 4/9` (`0.4444...`), NOT the average of `0.750` and `0.200`, and automatically computes `OBP` and `SLG` to derive `OPS`

### Requirement: Zero-Denominator Safety and Innings-to-Outs Conversion
The library SHALL store innings pitched as integer `outs` (`1 IP = 3 outs`), convert baseball fractional notation (`6.1` -> `19`, `6.2` -> `20`) at ingestion boundaries, and return `NaN`/`null` whenever any metric denominator is zero.

#### Scenario: Zero at-bats or zero outs recorded
- **WHEN** a row has `ab = 0` or `outs = 0`
- **THEN** `AVG`, `SLG`, `ERA`, `WHIP`, and `FIP` evaluate to `NaN`/`null` without raising `ZeroDivisionError` or returning `inf`

### Requirement: Multi-Backend Dataframe Interoperability
All metric calculations SHALL execute natively on Polars `DataFrame`/`LazyFrame`, pandas `DataFrame`, PyArrow `Table`, and DuckDB relations via `narwhals`, returning a frozen `CalculationResult` whose `.df` matches the input dataframe family.

#### Scenario: Polars, pandas, and PyArrow round-trip calculation
- **WHEN** `calculate()` is invoked with a Polars `DataFrame`, pandas `DataFrame`, or PyArrow `Table`
- **THEN** `result.df` is returned in the matching backend type with identical numerical values within floating-point tolerance (`1e-9`)

### Requirement: Empirical Expectancy and Forecasting Models
The library SHALL provide `scikit-learn`-style estimators (`RunExpectancyMatrix`, `CountExpectancyMatrix`, `LinearWeightsEstimator`, `MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`) that expose frozen `.results` objects with statistical diagnostics and uncertainty intervals.

#### Scenario: Fitting RE24 Run Expectancy Matrix and valuing plays
- **WHEN** `RunExpectancyMatrix().fit(events_df)` is called on play-by-play records and `.transform(events_df)` is executed
- **THEN** `.results` contains the 24 base-out state expectancy matrix and the transformed table contains `re_before`, `re_after`, and `run_value = runs_on_play + re_after - re_before`
