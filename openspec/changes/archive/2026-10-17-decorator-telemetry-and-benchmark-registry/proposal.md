# Proposal: Decorator-Based Telemetry (`@profiled`) & Benchmark Registry (`@register_benchmark`)

## 1. Context & Problem Statement
While `calculate()`, `calculate_suite()`, and `calculate_rolling()` attach an `ExecutionProfile` to `CalculationResult`, other major subsystems in `sabermetricspy`—including `SourceTranslator`, `from_retrosheet`, `from_statcast`, `RunExpectancyMatrix`, `CountExpectancyMatrix`, `WinProbabilityModel`, `WARCalculator`, `MarcelProjector`, and `EmpiricalBayesEstimator`—do not automatically capture execution spans or register with the benchmark runner. Additionally, users building end-to-end pipelines cannot easily decorate their own functions to see a unified timing breakdown alongside `sabermetricspy` internals.

## 2. Proposed Solution
1. **`src/sabermetricspy/telemetry/__init__.py`**:
   - Implement `SpanRecord` (frozen dataclass with `name`, `category`, `backend`, `rows_in`, `rows_out`, `duration_ms`, and `rows_per_sec`).
   - Implement `PerformanceTracker` (`sb.telemetry`) with `.spans`, `.reset()`, `.summary_df()`, `.format_table()`, and context-manager support (`with sb.telemetry.session():`).
   - Implement the `@profiled` decorator (supporting both `@profiled` and `@profiled(name=..., category=...)`) with full `ParamSpec`/`TypeVar` static type preservation, automatic input/output DataFrame row-count and backend inspection, and `time.perf_counter_ns()` timing.
   - Implement `@register_benchmark` and `run_registered_benchmarks()` so subsystem workloads (and user-decorated benchmark functions) can be discovered and executed in one call or via `sabermetrics benchmark --registered`.
2. **Instrument All Core Subsystems**:
   - Apply `@profiled` across `engine`, `presets` (`SourceTranslator`, `from_retrosheet`, `from_statcast`), `expectancy` (`RunExpectancyMatrix`, `CountExpectancyMatrix`, `WinProbabilityModel`), `value` (`WARCalculator`), and `models` (`MarcelProjector`, `EmpiricalBayesEstimator`).
   - Register built-in subsystem benchmark workloads using `@register_benchmark`.
3. **CLI & Demo Integration**:
   - Add `--registered` flag to `sabermetrics benchmark`.
   - Update `examples/05_benchmarking_rolling_physics_and_cli.py` and tests to demonstrate `@profiled`, `sb.telemetry.format_table()`, and `@register_benchmark`.
