# Tasks: Decorator-Based Telemetry & Benchmark Registry

- [x] 1. Create `src/sabermetricspy/telemetry/__init__.py` with `SpanRecord`, `PerformanceTracker`, `telemetry`, `@profiled`, `@register_benchmark`, `RegisteredBenchmarkResult`, and `run_registered_benchmarks`.
- [x] 2. Decorate core functions and estimator methods across `engine`, `presets`, `expectancy`, `value`, and `models` with `@profiled`, and register built-in subsystem benchmarks with `@register_benchmark`.
- [x] 3. Export `profiled`, `register_benchmark`, `run_registered_benchmarks`, `telemetry`, `PerformanceTracker`, `SpanRecord`, and `RegisteredBenchmarkResult` in `src/sabermetricspy/__init__.py` and add `--registered` to `sabermetrics benchmark` in `src/sabermetricspy/cli/__init__.py`.
- [x] 4. Record `ADR-0025` in `docs/DECISIONS.md`, update `examples/05_benchmarking_rolling_physics_and_cli.py`, and add unit and benchmark tests in `tests/test_sabermetricspy.py` and `tests/test_benchmarks.py`.
- [x] 5. Run `openspec validate --all`, `uv run ruff check .`, `uv run pyright`, and `uv run pytest`, then archive the change.
