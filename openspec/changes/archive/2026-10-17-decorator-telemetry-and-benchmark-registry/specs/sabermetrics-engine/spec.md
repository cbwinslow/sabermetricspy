# Delta Spec: Sabermetrics Engine (`sabermetrics-engine`)

## ADDED Requirements

### Requirement: Decorator-Based Telemetry (`@profiled`) and PerformanceTracker (`sb.telemetry`)
The library SHALL provide a `@profiled` decorator and a `PerformanceTracker` singleton (`sb.telemetry`) that automatically capture execution timing (`duration_ms`, `rows_per_sec`), backend type, and row counts across decorated library functions, estimator methods, and user functions.

#### Scenario: Decorating and tracking multi-step pipeline execution
- **GIVEN** a pipeline that calls `from_statcast`, `calculate_suite`, `WinProbabilityModel.transform`, and a user function decorated with `@sb.profiled`
- **WHEN** executed inside `with sb.telemetry.session():` (or after `sb.telemetry.reset()`)
- **THEN** `sb.telemetry.spans` SHALL record a `SpanRecord` for each decorated call with positive `duration_ms`, accurate `rows_in`/`rows_out`, and `sb.telemetry.format_table()` SHALL render the aggregated breakdown.

### Requirement: Decorator-Based Benchmark Registry (`@register_benchmark`)
The library SHALL provide a `@register_benchmark` decorator and `run_registered_benchmarks()` runner to register and benchmark subsystem workloads (`engine`, `translator`, `expectancy`, `valuation`, `forecasting`) and custom user benchmarks from Python or via `sabermetrics benchmark --registered`.

#### Scenario: Running registered subsystem benchmarks
- **GIVEN** built-in or user-defined benchmark workloads decorated with `@register_benchmark`
- **WHEN** `sb.run_registered_benchmarks(repeats=2)` or `sabermetrics benchmark --registered` is called
- **THEN** it SHALL execute each registered benchmark and return a `RegisteredBenchmarkResult` containing `median_ms`, `mean_ms`, `min_ms`, and `rows_per_sec` for every workload.
