# Delta Specification: Sabermetrics Calculation Engine

## ADDED Requirements

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
