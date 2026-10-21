# sabermetrics-engine Specification

## Purpose
Provide a strongly-typed, dataframe-agnostic sabermetrics calculation engine, declarative YAML source/nomenclature translator, metric registry, empirical expectancy matrix builder, and forecasting model suite across Polars, DuckDB, PyArrow, and pandas.

## Requirements

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

### Requirement: Empirical Expectancy and Forecasting Models
The library SHALL provide `scikit-learn`-style estimators (`RunExpectancyMatrix`, `CountExpectancyMatrix`, `LinearWeightsEstimator`, `MarcelProjector`, `Log5Model`, `MarkovChainModel`, `MonteCarloSimulator`) that expose frozen `.results` objects with statistical diagnostics and uncertainty intervals.

#### Scenario: Fitting RE24 Run Expectancy Matrix and valuing plays
- **WHEN** `RunExpectancyMatrix().fit(events_df)` is called on play-by-play records and `.transform(events_df)` is executed
- **THEN** `.results` contains the 24 base-out state expectancy matrix and the transformed table contains `re_before`, `re_after`, and `run_value = runs_on_play + re_after - re_before`

### Requirement: Declarative YAML Column Alias and Nomenclature Registry
The library SHALL load default column aliases from a bundled YAML file (`data/presets/aliases.yaml`) and SHALL provide `register_column_aliases()` and `register_column_aliases_yaml()` so users can register custom column nomenclatures at runtime without modifying library source code.

#### Scenario: Registering a custom YAML nomenclature alias
- **WHEN** a user registers a custom YAML nomenclature mapping `{"dinger_ct": "hr", "free_passes": "bb", "whiff_outs": "so"}` and calls `calculate(df, [Metric.FIP])`
- **THEN** the engine automatically translates `dinger_ct`, `free_passes`, and `whiff_outs` into canonical `hr`, `bb`, and `so` columns and computes `FIP`

### Requirement: Generic YAML SourceTranslator for Provider Schemas
The library SHALL provide a `SourceTranslator` class that loads declarative YAML translation rules (`column_map`, `value_rules`, `range_rules`) from built-in presets (`retrosheetpy_events`, `statcast`, `lahman`) or user-supplied `.yaml` files and executes them as vectorized Narwhals expressions.

#### Scenario: Translating a custom provider dataset via YAML SourceTranslator
- **WHEN** a user defines a custom provider translator in YAML with `column_map` and `value_rules` and passes `preset=translator` to `calculate()`
- **THEN** `SourceTranslator` translates the raw provider columns and event codes into canonical Tier 2 additive counts and computes the requested metrics across Polars, pandas, PyArrow, or DuckDB

### Requirement: 288-State Count Expectancy Matrix (RE288)
The library SHALL provide `CountExpectancyMatrix` supporting `.fit(df)`, `.transform(df)`, and frozen `.results` (`RE288Results`) across the 288 `(balls, strikes, outs, base_state)` states (fitted from data with one count per plate appearance; there is no built-in table, and unfitted states are null), computing `re288_before`, `re288_after`, `pitch_run_value`, and `count_leverage`.

#### Scenario: Valuing non-terminal and terminal pitches with RE288
- **WHEN** a `CountExpectancyMatrix` fitted on pitch records with a `pa_id` column calls `.transform(pitches_df)`
- **THEN** pitches whose before and after states were fitted get `re288_before`, `re288_after` and `pitch_run_value`, pitches in unfitted states get null, and `count_run_value(balls, strikes)` returns Walsh's published run value for each of the 12 live counts

### Requirement: Markov Win Expectancy
The library SHALL provide `MarkovWinExpectancy` supporting `.fit(df)` on batting plays (`outs_before`, `base_state_before`, `outs_after`, `base_state_after`, `runs_on_play`), frozen `.results`, and `.win_expectancy(inning, half_inning, outs, base_state, home_score_diff)`, solving the home team's win probability by backward induction over observed base-out transitions (Tango's `we.html` construction). The removed `WinProbabilityModel` (ADR-0064) is not provided.

#### Scenario: Hand-solvable chain
- **WHEN** every state hits a solo home run with probability p and otherwise makes an out
- **THEN** the bottom of the 9th, tied, with no outs is worth `q + (1 - q) / 2` with `q = 1 - (1 - p)^3`

### Requirement: Built-In Execution Telemetry and Multi-Backend Benchmarking
The calculation engine SHALL record stage-by-stage nanosecond timing telemetry in a frozen `ExecutionProfile` attached to `CalculationResult.profile` and provide a `benchmark()` function for comparing throughput across Polars, DuckDB, PyArrow, and pandas.

#### Scenario: Inspecting `.profile` on a calculation result and running `benchmark()`
- **WHEN** a user calls `res = sb.calculate(df, [Metric.WRC_PLUS], by="player_id")` or `bench = sb.benchmark(rows=10_000, repeats=2)`
- **THEN** `res.profile.total_ms > 0`, `res.profile.rows_per_sec > 0`, `res.profile.backend == "polars"`, and `bench.summary_df` reports timing and throughput across all 4 dataframe backends.

### Requirement: Additive Rolling-Window Calculation Engine
The library SHALL provide `calculate_rolling()` that sums additive counting columns over rolling windows of size `window` ordered by `order_by` (optionally partitioned by `by`) before evaluating rate and ratio metric expressions.

#### Scenario: Computing a 3-game rolling OBP and wOBA
- **WHEN** a user calls `sb.calculate_rolling(game_logs_df, [Metric.AVG, Metric.OBP, Metric.WOBA], window=3, by="player_id", order_by="game_seq")`
- **THEN** the engine sums `ab`, `h`, `bb`, `hbp`, `sf`, `pa`, `b1`, `b2`, `b3`, `hr`, `ibb` over each 3-game window per player prior to dividing, matching exact multi-game cumulative rates.

### Requirement: Pitch-Tracking Physics and Statcast Expected Metrics
The registry and `statcast` YAML translator SHALL support Statcast expected metrics (`XBA`, `XSLG`, `XWOBA`, `WOBA_MINUS_XWOBA`, `BA_MINUS_XBA` in `MetricSuite.STATCAST_EXPECTED`) and pitch-tracking kinematics (`AVG_VELO`, `AVG_SPIN`, `AVG_EXTENSION`, `IVB`, `HB`, `TOTAL_BREAK`, `EFFECTIVE_VELO`, `VAA` in `MetricSuite.PITCH_PHYSICS`).

#### Scenario: Computing VAA, IVB, HB, and xwOBA from Statcast pitch records
- **WHEN** a user passes Statcast pitch data with `release_speed`, `release_spin_rate`, `release_extension`, `pfx_x`, `pfx_z`, `vy0`, `vz0`, `ay`, `az`, and `estimated_woba_using_speedangle` to `sb.calculate_suite(df, [MetricSuite.PITCH_PHYSICS, MetricSuite.STATCAST_EXPECTED], preset="statcast", by="pitcher_id")`
- **THEN** the engine computes accurate `avg_velo`, `avg_spin`, `ivb`, `hb`, `total_break`, `vaa`, and `xwoba`.

### Requirement: Command-Line Interface (`sabermetrics`)
The package SHALL expose a `sabermetrics` CLI supporting `list`, `info`, `suites`, and `benchmark` subcommands.

#### Scenario: Running CLI commands
- **WHEN** a user invokes `sabermetrics info wrc_plus`, `sabermetrics list --category batting`, `sabermetrics suites`, or `sabermetrics benchmark --rows 10000 --repeats 2`
- **THEN** the CLI exits with status code `0` and prints structured output.

### Requirement: Decorator-Based Telemetry (`@profiled`) and PerformanceTracker (`sb.telemetry`)
The library SHALL provide a `@profiled` decorator and a `PerformanceTracker` singleton (`sb.telemetry`) that automatically capture execution timing (`duration_ms`, `rows_per_sec`), backend type, and row counts across decorated library functions, estimator methods, and user functions.

#### Scenario: Decorating and tracking multi-step pipeline execution
- **GIVEN** a pipeline that calls `from_statcast`, `calculate_suite`, `WinExpectancyMatrix.fit`, and a user function decorated with `@sb.profiled`
- **WHEN** executed inside `with sb.telemetry.session():` (or after `sb.telemetry.reset()`)
- **THEN** `sb.telemetry.spans` SHALL record a `SpanRecord` for each decorated call with positive `duration_ms`, accurate `rows_in`/`rows_out`, and `sb.telemetry.format_table()` SHALL render the aggregated breakdown.

### Requirement: Decorator-Based Benchmark Registry (`@register_benchmark`)
The library SHALL provide a `@register_benchmark` decorator and `run_registered_benchmarks()` runner to register and benchmark subsystem workloads (`engine`, `translator`, `expectancy`, `valuation`, `forecasting`) and custom user benchmarks from Python or via `sabermetrics benchmark --registered`.

#### Scenario: Running registered subsystem benchmarks
- **GIVEN** built-in or user-defined benchmark workloads decorated with `@register_benchmark`
- **WHEN** `sb.run_registered_benchmarks(repeats=2)` or `sabermetrics benchmark --registered` is called
- **THEN** it SHALL execute each registered benchmark and return a `RegisteredBenchmarkResult` containing `median_ms`, `mean_ms`, `min_ms`, and `rows_per_sec` for every workload.

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

### Requirement: DuckDB input is read once
For a DuckDB relation the engine SHALL read the relation into memory once as Arrow. A table larger than memory SHALL be aggregated in DuckDB by the caller before it is passed, and the documentation SHALL say so.

#### Scenario: Documented limit
- **WHEN** the README and the `calculate` docstring are read
- **THEN** both state that DuckDB input is read into memory as Arrow and the result is returned on DuckDB's default connection
