# Design: Decorator-Based Telemetry & Benchmark Registry

## 1. Architecture & Type-Safe Decorator Design
- **`@profiled` Signature**:
  - Uses `@overload` with `ParamSpec` (`P`) and `TypeVar` (`R`) so decorating any function or method preserves its exact signature in `pyright` strict mode.
  - Supports both bare decoration (`@profiled`) and parameterized decoration (`@profiled(category="expectancy")` or `@profiled("custom_name", category="pipeline")`).
- **Automatic Frame & Row Inspection**:
  - Before calling the wrapped function, `_inspect_input_frame(args, kwargs)` scans positional and keyword arguments (skipping `self`/`cls` on bound methods) for the first dataframe-like object (`polars`, `pandas`, `pyarrow`, `duckdb`, or `CalculationResult`) to extract `(backend_name, rows_in)`.
  - After calling the wrapped function, `_inspect_output_rows(result, rows_in)` extracts `rows_out` from `CalculationResult.df`, a returned DataFrame/Table, or falls back to `rows_in` for `.fit()` methods returning `self`.
- **`PerformanceTracker` (`sb.telemetry`)**:
  - Stores a list of frozen `SpanRecord` instances when `enabled=True`.
  - `.summary_df()` aggregates spans by `(name, category, backend)` to compute `calls`, `total_rows_in`, `total_ms`, `mean_ms`, `min_ms`, `max_ms`, and `rows_per_sec`.
  - `.format_table()` renders a clean ASCII table of all recorded spans and aggregated statistics.
- **Benchmark Registry (`@register_benchmark`)**:
  - Stores registered benchmark callables in `_BENCHMARK_REGISTRY: dict[str, BenchmarkEntry]`.
  - `run_registered_benchmarks(repeats: int = 3, category: str | None = None)` executes each registered benchmark callable `repeats` times, measures median/mean/min duration (`ms`) and `rows/sec`, and returns a `RegisteredBenchmarkResult` with `.summary_df()` and `.format_table()`.
